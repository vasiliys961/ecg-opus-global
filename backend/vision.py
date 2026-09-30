"""ECG image channel, адаптированный из doctor-opus-global.

Источник промптов: lib/prompts.ts (SPECIALIST_CRITERIA.ecg, getDescriptionPrompt)
и lib/diagnostic-report.ts (DIAGNOSTIC_ECG_SYSTEM_PROMPT), коммит 9221b37a.
Радиологический system prompt production-пути сюда не входит.
Изображение не маскируется и не перекодируется.
"""

from __future__ import annotations

import base64
import json
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path

import certifi


def _load_local_env() -> None:
    path = Path(__file__).resolve().parents[1] / ".env"
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        if name and name not in os.environ:
            os.environ[name] = value


_load_local_env()

EYES_MODEL = os.environ.get("ECG_OBSERVER_MODEL", "google/gemini-3.8-flash")
ANALYZER_MODEL = os.environ.get("ECG_INTERPRETER_MODEL", "anthropic/claude-opus-5.5")
OBSERVER_MODEL = EYES_MODEL
INTERPRETER_MODEL = ANALYZER_MODEL

ECG_DOCTOR = (
    "You have the competence of a physician who reports routine ECGs. "
    "You use the ordinary protocol wording and you keep standard abbreviations: "
    "ЧСС, уд/мин, ЭОС, PQ, QRS, ST, QT, QTc, БПНПГ, БЛНПГ, ГЛЖ, ФП. "
    "Do not expand an abbreviation into a textbook phrase such as «блокада ножки пучка Гиса» "
    "or «частота сердечных сокращений составляет … ударов в минуту». "
    "Do not list mutually exclusive statements as if all of them were present. "
    "Weigh each classifier score against the measured intervals and keep the statement that fits. "
    "Do not write treatment, resuscitation, drugs, or a differential essay."
)

ECG_REQUIREMENTS = (
    "EXTRACT ALL METRICS WITH MAXIMUM PRECISION: 1. Technical parameters (Voltage, Speed mm/s). "
    "2. Rhythm (regularity, source), HR. 3. Electrical axis (alpha angle in degrees). "
    "4. Intervals in ms: P-wave (amplitude, duration), PR (interval), QRS (complex), QT/QTc (corrected). "
    "5. Segments: ST (elevation/depression in mm relative to TP baseline, morphology). "
    "6. Waves: Q, R progression V1–V6, T. 7. Hypertrophy voltage criteria. "
    "8. Conduction: bundle branch blocks, AV blocks."
)

OBSERVER_PROMPT = f"""You read this ECG image with the competence of an ECG diagnostician.
Describe only what is visible. Do not invent a measurement that is not readable.
If a value is not visible, use null.
Name findings with the usual abbreviations when the picture shows them: БПНПГ, БЛНПГ, ГЛЖ, ФП.
{ECG_DOCTOR}

Technical requirements: {ECG_REQUIREMENTS}

Return JSON only:
{{
  "schema_version": "ecg.vision.v1",
  "image_quality": "good",
  "quality_issues": [],
  "measurements": {{
    "heart_rate": null,
    "rhythm": null,
    "pr_ms": null,
    "qrs_ms": null,
    "qt_ms": null,
    "qtc_ms": null,
    "axis": null,
    "paper_speed_mm_s": null,
    "gain_mm_per_mv": null
  }},
  "findings": []
}}
"""

MINNESOTA_CODES = (
    "The description standard is the Minnesota Code: classify the tracing, do not narrate it. "
    "Lead groups, when a site is needed: переднебоковые I, aVL, V6; нижние II, III, aVF; передние V1–V5. "
    "After Заключение print the title Миннесота and one short line. "
    "You may emit only these codes, and only when the stated measurement matches: "
    "2-1 if the QRS axis is from −30° through −90°; "
    "2-2 if the QRS axis is from +120° through +180°; "
    "an axis from −29° through +119° has no axis code; "
    "7-1-1 complete LBBB with QRS at least 120 ms; "
    "7-2-1 complete RBBB with QRS at least 120 ms; "
    "7-3 incomplete RBBB with QRS under 120 ms; "
    "7-6 incomplete LBBB with QRS under 120 ms; "
    "7-4 if QRS is at least 120 ms and there is no bundle-branch label; "
    "8-3-1 atrial fibrillation when P is unstable and RR is uneven; "
    "8-1-2 only when a wide premature beat is counted; "
    "8-7 sinus rhythm under 50 per minute. "
    "Separate codes with a comma. If none apply, write «кодов нет». Do not invent any other number. "
    "Do not emit a code that depends on wave height."
)

MINNESOTA_READING = (
    MINNESOTA_CODES
    + " Use only rhythm, axis, and durations written in the source. Do not invent a millimetre amplitude."
)

MINNESOTA = (
    MINNESOTA_CODES
    + " A classifier score is not a code. CSV amplitudes are not millimetres."
)

INTERPRETER_PROMPT = """You convert an existing ECG extraction into a short report for a clinician.
Use only facts present in the extraction. Do not invent grid values, calibration, or diagnoses.
Write in Russian. No JSON. No Markdown. No asterisks. No English headings.
Omit every measurement that is missing. Do not write "не указано" or "not specified".

Put each of these titles on its own line, and only if that section has something to say:
Запись
Что видно
С чем сравнивать
Что проверить у пациента
Заключение
Что делать

Under a title, one fact per line, each line starting with "- ".
In Заключение, say once that this is decision support and not an autonomous diagnosis.
"""

PROTOCOL_FIELDS = (
    "Ритм",
    "ЧСС",
    "Интервалы",
    "Зубцы",
    "Важные соотношения",
    "Депрессии и элевации",
    "Патологические зубцы",
    "Заключение",
    "Миннесота",
)

BLANK_GUIDE = """Print these titles, each on its own line, in this order:
Ритм
ЧСС
Интервалы
Зубцы
Важные соотношения
Депрессии и элевации
Патологические зубцы
Заключение
Миннесота

Everything before Заключение is a short preamble. One line under each title. No leading dash.
Do not write the patient's name, age, or sex.
Ритм is like "синусовый". ЧСС is like "64 уд/мин".
Интервалы is one line, like "P 126 мс, PQ 132 мс, QRS 118 мс, QT 396 мс, QTc 463 мс".
Зубцы is one line on shape, like "P есть, QRS узкий, T положительный".
Важные соотношения is one line of the usual indices the source already has: ЭОС, Соколов–Лайон, Корнелл, Льюис, Губнер, R/S V1, R/S V5, угол QRS–T. Example: "ЭОС 3°, Соколов–Лайон +1.209, Корнелл +0.840, Льюис +0.350, Губнер +0.900, R/S V1 0.13, R/S V5 2.40, QRS–T 21°". Skip an index that was not calculated. These values are not millimetres, so do not compare them with a textbook cutoff and do not add hypertrophy from the index alone.
Депрессии и элевации is one line of ST, like "II +0.020, J+80 мс". If the source shows none, write "нет".
Патологические зубцы is one line for a pathological Q, QS, or another abnormal wave the source describes. If none, write "нет".
Do not invent a number to fill a line. Omit a missing number, and write "нет" when the whole line has no finding.
Заключение comes after the preamble. It is the line a doctor would sign, not a repeat of the preamble.
"""

PROTOCOL_PROMPT = f"""Rewrite the shown ECG reading as a standard ECG description form.
{ECG_DOCTOR}
The source is already written. Do not look at an image. Do not invent numbers or findings.
Write in Russian. No JSON. No Markdown. No asterisks. No English headings.
This is a description blank, not a consultation and not a treatment plan.

{BLANK_GUIDE}
{MINNESOTA_READING}
Do not write differential diagnosis, artifact discussion, comparison with other recordings, clinical correlation, recommendations, resuscitation, defibrillation, drugs, or calls for a team.
"""


_LOCALE_LABELS = {
    "en": "English",
    "ru": "Russian",
    "es": "Spanish",
    "fr": "French",
    "ar": "Arabic",
    "hi": "Hindi",
    "pt-BR": "Portuguese (Brazil)",
    "id": "Indonesian",
    "ms": "Malay",
    "tr": "Turkish",
    "zh-CN": "Chinese",
}

_BLANK_TITLES = {
    "en": ("Rhythm", "Rate", "Intervals", "Waves", "Important ratios", "ST depression and elevation", "Abnormal waves", "Conclusion", "Minnesota"),
    "ru": PROTOCOL_FIELDS,
    "es": ("Ritmo", "FC", "Intervalos", "Ondas", "Cocientes importantes", "Depresiones y elevaciones", "Ondas patológicas", "Conclusión", "Minnesota"),
    "fr": ("Rythme", "FC", "Intervalles", "Ondes", "Rapports importants", "Dépressions et sus-décalages", "Ondes pathologiques", "Conclusion", "Minnesota"),
    "ar": ("النظم", "معدل القلب", "الفترات", "الموجات", "النسب المهمة", "الانخفاضات والارتفاعات", "الموجات المرضية", "الخلاصة", "مينيسوتا"),
    "hi": ("लय", "हृदय दर", "अंतराल", "तरंगें", "महत्वपूर्ण अनुपात", "अवनमन और उन्नयन", "रोगात्मक तरंगें", "निष्कर्ष", "मिनेसोटा"),
    "pt-BR": ("Ritmo", "FC", "Intervalos", "Ondas", "Relações importantes", "Depressões e elevações", "Ondas patológicas", "Conclusão", "Minnesota"),
    "id": ("Irama", "Laju", "Interval", "Gelombang", "Rasio penting", "Depresi dan elevasi", "Gelombang abnormal", "Kesimpulan", "Minnesota"),
    "ms": ("Irama", "Kadar", "Selang", "Gelombang", "Nisbah penting", "Depresi dan elevasi", "Gelombang abnormal", "Kesimpulan", "Minnesota"),
    "tr": ("Ritim", "Hız", "Aralıklar", "Dalgalar", "Önemli oranlar", "Depresyon ve elevasyon", "Patolojik dalgalar", "Sonuç", "Minnesota"),
    "zh-CN": ("节律", "心率", "间期", "波", "重要比值", "压低与抬高", "异常波", "结论", "明尼苏达"),
}

_READING_TITLES = {
    "en": ("Recording", "What is visible", "What to compare", "What to check with the patient", "Conclusion", "What to do"),
    "es": ("Registro", "Qué se ve", "Con qué comparar", "Qué comprobar en el paciente", "Conclusión", "Qué hacer"),
    "fr": ("Enregistrement", "Ce qui se voit", "À quoi comparer", "À vérifier chez le patient", "Conclusion", "Que faire"),
    "ar": ("التسجيل", "ما يظهر", "بماذا يُقارن", "ما يُفحص عند المريض", "الخلاصة", "ماذا يُفعل"),
    "hi": ("रिकॉर्ड", "क्या दिखता है", "किससे तुलना करें", "रोगी में क्या जाँचें", "निष्कर्ष", "क्या करें"),
    "pt-BR": ("Registro", "O que se vê", "Com o que comparar", "O que verificar no paciente", "Conclusão", "O que fazer"),
    "id": ("Rekaman", "Yang terlihat", "Pembanding", "Yang diperiksa pada pasien", "Kesimpulan", "Yang dilakukan"),
    "ms": ("Rakaman", "Yang kelihatan", "Perbandingan", "Yang diperiksa pada pesakit", "Kesimpulan", "Tindakan"),
    "tr": ("Kayıt", "Ne görünüyor", "Neyle karşılaştırmalı", "Hastada ne kontrol edilmeli", "Sonuç", "Ne yapılmalı"),
    "zh-CN": ("记录", "可见内容", "对照", "需向患者核实", "结论", "处理"),
}

_NONE_WORD = {
    "en": "none", "ru": "нет", "es": "no", "fr": "non", "ar": "لا", "hi": "नहीं",
    "pt-BR": "não", "id": "tidak", "ms": "tiada", "tr": "yok", "zh-CN": "无",
}
_NO_CODES = {
    "en": "no codes", "ru": "кодов нет", "es": "sin códigos", "fr": "aucun code", "ar": "لا رموز",
    "hi": "कोई कोड नहीं", "pt-BR": "sem códigos", "id": "tidak ada kode", "ms": "tiada kod",
    "tr": "kod yok", "zh-CN": "无编码",
}


def response_locale(locale: str) -> str:
    raw = (locale or "").strip()
    folded = {"pt-br": "pt-BR", "pt_br": "pt-BR", "zh-cn": "zh-CN", "zh_cn": "zh-CN", "zh": "zh-CN"}
    if raw in _LOCALE_LABELS:
        return raw
    return folded.get(raw.lower(), "en")


def forced_response_language(locale: str) -> str:
    """Та же формулировка, что buildForcedResponseLanguageInstruction в Doctor Opus."""
    code = response_locale(locale)
    label = _LOCALE_LABELS[code]
    return (
        "RESPONSE LANGUAGE:\n"
        f"- Reply strictly in {label}.\n"
        "- If the user asks for another language, still keep the final answer in "
        f"{label} unless they explicitly change the response language setting.\n"
        "- Keep wording professional, clinically precise, and sufficiently detailed for medical decision support.\n"
        "- Preserve standard international medical terminology where appropriate.\n"
        "- Print the section titles exactly as listed in this prompt. Do not translate those titles."
    )


def _reading_prompt(locale: str) -> str:
    if response_locale(locale) == "ru":
        return INTERPRETER_PROMPT
    titles = _READING_TITLES[response_locale(locale)]
    listed = "\n".join(titles)
    return (
        "You convert an existing ECG extraction into a short report for a clinician.\n"
        "Use only facts present in the extraction. Do not invent grid values, calibration, or diagnoses.\n"
        "No JSON. No Markdown. No asterisks.\n"
        'Omit every measurement that is missing. Do not write "не указано" or "not specified".\n\n'
        "Put each of these titles on its own line, and only if that section has something to say:\n"
        f"{listed}\n\n"
        'Under a title, one fact per line, each line starting with "- ".\n'
        f"In {titles[4]}, say once that this is decision support and not an autonomous diagnosis.\n\n"
        f"{forced_response_language(locale)}"
    )


def _blank_guide(locale: str) -> str:
    if response_locale(locale) == "ru":
        return BLANK_GUIDE
    titles = _BLANK_TITLES[response_locale(locale)]
    none = _NONE_WORD[response_locale(locale)]
    phrase = _NO_CODES[response_locale(locale)]
    listed = "\n".join(titles)
    return f"""Print these titles, each on its own line, in this order:
{listed}

Everything before {titles[7]} is a short preamble. One line under each title. No leading dash.
Do not write the patient's name, age, or sex.
{titles[0]} is like "sinus". {titles[1]} is like "64/min".
{titles[2]} is one line, like "P 126 ms, PQ 132 ms, QRS 118 ms, QT 396 ms, QTc 463 ms".
{titles[3]} is one line on shape, like "P present, QRS narrow, T positive".
{titles[4]} is one line of the usual indices the source already has: axis, Sokolow–Lyon, Cornell, Lewis, Gubner, R/S V1, R/S V5, QRS–T angle. Example: "axis 3°, Sokolow–Lyon +1.209, Cornell +0.840, Lewis +0.350, Gubner +0.900, R/S V1 0.13, R/S V5 2.40, QRS–T 21°". Skip an index that was not calculated. These values are not millimetres, so do not compare them with a textbook cutoff and do not add hypertrophy from the index alone.
{titles[5]} is one line of ST, like "II +0.020, J+80 ms". If the source shows none, write "{none}".
{titles[6]} is one line for a pathological Q, QS, or another abnormal wave the source describes. If none, write "{none}".
Do not invent a number to fill a line. Omit a missing number, and write "{none}" when the whole line has no finding.
{titles[7]} comes after the preamble. It is the line a doctor would sign, not a repeat of the preamble.
On {titles[8]}, if none of the allowed codes apply, write exactly "{phrase}".
"""


def _minnesota_block(locale: str, extra: str) -> str:
    if response_locale(locale) == "ru":
        return extra
    code = response_locale(locale)
    conclusion = _BLANK_TITLES[code][7]
    minnesota = _BLANK_TITLES[code][8]
    phrase = _NO_CODES[code]
    return (
        "The description standard is the Minnesota Code: classify the tracing, do not narrate it. "
        "Lead groups, when a site is needed: anterolateral I, aVL, V6; inferior II, III, aVF; anterior V1–V5. "
        f"After {conclusion} print the title {minnesota} and one short line. "
        "You may emit only these codes, and only when the stated measurement matches: "
        "2-1 if the QRS axis is from −30° through −90°; "
        "2-2 if the QRS axis is from +120° through +180°; "
        "an axis from −29° through +119° has no axis code; "
        "7-1-1 complete LBBB with QRS at least 120 ms; "
        "7-2-1 complete RBBB with QRS at least 120 ms; "
        "7-3 incomplete RBBB with QRS under 120 ms; "
        "7-6 incomplete LBBB with QRS under 120 ms; "
        "7-4 if QRS is at least 120 ms and there is no bundle-branch label; "
        "8-3-1 atrial fibrillation when P is unstable and RR is uneven; "
        "8-1-2 only when a wide premature beat is counted; "
        "8-7 sinus rhythm under 50 per minute. "
        f'Separate codes with a comma. If none apply, write "{phrase}". Do not invent any other number. '
        "Do not emit a code that depends on wave height. "
        + extra
    )


def _protocol_prompt(locale: str) -> str:
    if response_locale(locale) == "ru":
        return PROTOCOL_PROMPT
    return (
        "Rewrite the shown ECG reading as a standard ECG description form.\n"
        f"{ECG_DOCTOR}\n"
        "The source is already written. Do not look at an image. Do not invent numbers or findings.\n"
        "No JSON. No Markdown. No asterisks.\n"
        "This is a description blank, not a consultation and not a treatment plan.\n\n"
        f"{_blank_guide(locale)}\n"
        f"{_minnesota_block(locale, 'Use only rhythm, axis, and durations written in the source. Do not invent a millimetre amplitude.')}\n"
        "Do not write differential diagnosis, artifact discussion, comparison with other recordings, clinical correlation, recommendations, resuscitation, defibrillation, drugs, or calls for a team.\n\n"
        f"{forced_response_language(locale)}"
    )


def _signal_prompt(locale: str) -> str:
    if response_locale(locale) == "ru":
        return SIGNAL_CONCLUSION_PROMPT
    titles = _BLANK_TITLES[response_locale(locale)]
    return (
        "Fill a standard ECG description form from two prepared blocks about one digital recording.\n"
        f"{ECG_DOCTOR}\n"
        "MEASUREMENTS are intervals and amplitudes already calculated. Put those numbers in the matching fields. Do not replace them.\n"
        "ECGFOUNDER lines are sigmoid scores of a research classifier. They are not a calibrated diagnosis and not a percent of accuracy.\n"
        "You decide which scores belong in the conclusion the way an ECG diagnostician would.\n"
        "No JSON. No Markdown. No asterisks.\n"
        "This is a formal ECG protocol, not a consultation and not a treatment plan.\n\n"
        f"{_blank_guide(locale)}\n"
        "Do not pad a number into a long sentence.\n"
        "Keep abbreviations as written: HR, /min, PQ, QRS, ST, QT, QTc, LBBB, RBBB, LVH, AF.\n"
        f"{titles[7]} is one short line, not a catalogue of every score.\n"
        "Ignore scores below 0.5.\n"
        "If two scores exclude each other, keep the one that matches the measurements.\n"
        "Sinus rhythm and atrial fibrillation: unstable P and uneven RR means AF.\n"
        "Incomplete and complete bundle branch block: keep the one that matches the QRS duration.\n"
        "Normal ECG and abnormal ECG: do not write both.\n"
        f"{_minnesota_block(locale, 'A classifier score is not a code. CSV amplitudes are not millimetres.')}\n"
        "Do not write differential diagnosis, artifact discussion, comparison with other recordings, clinical correlation, recommendations, resuscitation, defibrillation, drugs, or calls for a team.\n\n"
        f"{forced_response_language(locale)}"
    )


class VisionUnavailable(RuntimeError):
    """Канал изображения не вызвал модель."""


class UnsupportedImage(ValueError):
    """Формат изображения для этого этапа не принимается."""


class EmptyCase(ValueError):
    """Нет ни снимка, ни текста."""


def _api_key() -> str:
    return os.environ.get("LLM_API_KEY") or os.environ.get("OPENROUTER_API_KEY") or ""


def _endpoint() -> str:
    return os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")


def _looks_like_pdf(payload: bytes, filename: str, mime_type: str) -> bool:
    name = (filename or "").lower()
    mime = (mime_type or "").split(";")[0].strip().lower()
    return name.endswith(".pdf") or mime == "application/pdf" or payload.startswith(b"%PDF")


def prepare_image(payload: bytes, filename: str, mime_type: str) -> tuple[bytes, str]:
    """Проверяет формат и возвращает исходные байты без перекодирования и без маски краёв."""
    name = (filename or "").lower()
    mime = (mime_type or "").split(";")[0].strip().lower()
    if _looks_like_pdf(payload, filename, mime_type):
        if not payload.startswith(b"%PDF"):
            raise UnsupportedImage("Файл не похож на PDF. Байты не менялись.")
        return payload, "application/pdf"
    if mime not in {"image/jpeg", "image/png", "image/gif", "image/webp"}:
        raise UnsupportedImage("Нужен JPG, PNG, GIF или WEBP. Файл не изменялся.")
    if not payload:
        raise UnsupportedImage("Пустой файл изображения.")
    return payload, mime


def _completion(model: str, content: list | str) -> str:
    key = _api_key()
    if not key:
        raise VisionUnavailable(
            "LLM_API_KEY не задан. Изображение не отправлялось, заключение не создано."
        )
    message_content = content if isinstance(content, list) else content
    body = json.dumps(
        {
            "model": model,
            "temperature": 0.1,
            "messages": [{"role": "user", "content": message_content}],
        }
    ).encode()
    request = urllib.request.Request(
        _endpoint(),
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        context = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(request, timeout=120, context=context) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.URLError as exc:
        raise VisionUnavailable(f"Модель изображения недоступна: {exc}") from exc
    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise VisionUnavailable("Ответ модели не содержит текста.") from exc


def _parse_json(text: str) -> tuple[dict | None, str | None]:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None, "Наблюдатель не вернул JSON."
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None, "JSON наблюдателя не разобран."
    if not isinstance(parsed, dict):
        return None, "JSON наблюдателя не является объектом."
    return parsed, None


TEXT_EYES_PROMPT = f"""You read an ECG note with the competence of an ECG diagnostician. You have no image.
Copy only measurements and findings that are explicitly written.
Do not invent numbers. If a value is absent, use null.
Keep the note's abbreviations; do not expand БПНПГ, БЛНПГ, ГЛЖ, ФП, ЧСС, QRS, ST, QT.
{ECG_DOCTOR}

Technical requirements, only when the note states them: {ECG_REQUIREMENTS}

Return JSON only:
{{
  "schema_version": "ecg.vision.v1",
  "image_quality": null,
  "quality_issues": [],
  "measurements": {{
    "heart_rate": null,
    "rhythm": null,
    "pr_ms": null,
    "qrs_ms": null,
    "qt_ms": null,
    "qtc_ms": null,
    "axis": null,
    "paper_speed_mm_s": null,
    "gain_mm_per_mv": null
  }},
  "findings": []
}}
"""


STRIP_EYES_NOTE = (
    "These pictures are ordered frames of one paper ECG strip. "
    "The camera moved along the paper. Neighbouring frames overlap. "
    "Read them as one recording. "
    "Do not treat the frames as separate patients or separate ECGs. "
    "The time between frames is camera time, not ECG time. "
    "Do not invent a measurement that is readable on none of the frames."
)

MAX_STRIP_FRAMES = 6
MAX_FRAME_BYTES = 1_500_000
MAX_PHOTO_BYTES = 4_000_000
MAX_PDF_BYTES = 20_000_000
PDF_EYES_NOTE = (
    "The attachment is the original PDF, every page, without blur, crop, mask, or recompression. "
    "Read the printed ECG and the measurements on the sheet."
)


def _eyes_content(image_urls: list[str], notes: str) -> list | str:
    if image_urls:
        text = OBSERVER_PROMPT
        if any(url.startswith("data:application/pdf;") for url in image_urls):
            text = f"{PDF_EYES_NOTE}\n\n{text}"
        elif len(image_urls) > 1:
            text = f"{STRIP_EYES_NOTE}\n\n{text}"
        if notes:
            text += (
                "\n\nSUPPLIED TEXT is not the picture. "
                "Do not copy it into measurements unless the same value is visible on the image.\n"
                f"SUPPLIED TEXT:\n{notes}"
            )
        content: list = [{"type": "text", "text": text}]
        content.extend({"type": "image_url", "image_url": {"url": url}} for url in image_urls)
        return content
    return f"{TEXT_EYES_PROMPT}\n\nNOTE:\n{notes}"


def _analyzer_input(observer_text: str, notes: str, clinical_context: str, locale: str = "en") -> str:
    parts = [
        _reading_prompt(locale),
        "The extraction comes from the eyes model. Use it. Do not repeat the JSON.",
        "SUPPLIED TEXT, when present, is what the user typed. It is not a measurement you saw.",
        f"\nEXTRACTION:\n{observer_text}",
    ]
    if notes:
        parts.append(f"\nSUPPLIED TEXT:\n{notes}")
    if clinical_context:
        parts.append(f"\nCLINICAL CONTEXT:\n{clinical_context}")
    return "\n".join(parts)


def analyze_case(
    *,
    image: bytes | None = None,
    filename: str = "",
    mime_type: str = "",
    images: list[tuple[bytes, str, str]] | None = None,
    notes: str = "",
    clinical_context: str = "",
    locale: str = "en",
) -> dict:
    """Глаза — Gemini, анализатор — Opus. Ансамбль 531 не вызывается."""
    supplied = notes.strip()
    context = clinical_context.strip()
    payloads = [(payload, name, mime) for payload, name, mime in (images or []) if payload]
    if not payloads and image:
        payloads = [(image, filename, mime_type)]
    if len(payloads) > MAX_STRIP_FRAMES:
        raise UnsupportedImage("Для ленты нужно не больше шести кадров.")
    image_urls: list[str] = []
    pdf_count = 0
    for payload, name, mime in payloads:
        raw, ready = prepare_image(payload, name, mime)
        if ready == "application/pdf":
            pdf_count += 1
            limit = MAX_PDF_BYTES
            too_big = "PDF слишком большой."
        elif len(payloads) == 1:
            limit = MAX_PHOTO_BYTES
            too_big = "Снимок слишком большой."
        else:
            limit = MAX_FRAME_BYTES
            too_big = "Кадр ленты слишком большой."
        if len(raw) > limit:
            raise UnsupportedImage(too_big)
        image_urls.append(f"data:{ready};base64,{base64.b64encode(raw).decode('ascii')}")
    if pdf_count and pdf_count != len(image_urls):
        raise UnsupportedImage("PDF принимается одним файлом, без кадров ленты.")
    if pdf_count > 1:
        raise UnsupportedImage("Нужен один PDF.")
    image_preserved = bool(image_urls)
    if not image_urls and not supplied:
        raise EmptyCase("Нужно изображение ЭКГ или текст: измерения, описание, заключение аппарата.")
    if len(image_urls) > 1 and supplied:
        kind = "strip+text"
    elif len(image_urls) > 1:
        kind = "strip"
    elif pdf_count and supplied:
        kind = "pdf+text"
    elif pdf_count:
        kind = "pdf"
    elif image_urls and supplied:
        kind = "image+text"
    elif image_urls:
        kind = "image"
    else:
        kind = "text"
    observer_text = _completion(EYES_MODEL, _eyes_content(image_urls, supplied))
    extraction, parse_warning = _parse_json(observer_text)
    interpretation = _completion(ANALYZER_MODEL, _analyzer_input(observer_text, supplied, context, locale))
    return {
        "input_kind": kind,
        "ensemble_used": False,
        "image_preserved": image_preserved,
        "edge_mask_applied": False,
        "reencoded": False,
        "eyes_model": EYES_MODEL,
        "analyzer_model": ANALYZER_MODEL,
        "observer_model": EYES_MODEL,
        "interpreter_model": ANALYZER_MODEL,
        "extraction": extraction,
        "extraction_warning": parse_warning,
        "observer_text": observer_text,
        "interpretation": interpretation,
    }


def _protocol_form(text: str, locale: str = "en") -> str:
    """Оставляет только поля бланка. Заголовки приводит к языку страницы."""
    titles = _BLANK_TITLES[response_locale(locale)]
    names = sorted(
        ((title.casefold(), index) for group in _BLANK_TITLES.values() for index, title in enumerate(group)),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    kept: list[str] = []
    accept = False
    for raw in text.replace("**", "").replace("*", "").splitlines():
        line = raw.strip()
        bare = line[1:].strip() if line.startswith("-") else line
        key = bare.casefold()
        matched = next((index for name, index in names if key == name or key.startswith(name + ":")), None)
        if matched is not None:
            accept = True
            kept.append(titles[matched])
            same_line = bare.split(":", 1)[1].strip() if ":" in bare else ""
            if same_line:
                kept.append(same_line)
                accept = False
            continue
        if accept and bare:
            kept.append(bare)
            accept = False
    return "\n".join(kept)


SIGNAL_CONCLUSION_PROMPT = f"""Fill a standard ECG description form from two prepared blocks about one digital recording.
{ECG_DOCTOR}
MEASUREMENTS are intervals and amplitudes already calculated. Put those numbers in the matching fields. Do not replace them.
ECGFOUNDER lines are sigmoid scores of a research classifier. They are not a calibrated diagnosis and not a percent of accuracy.
You decide which scores belong in the conclusion the way an ECG diagnostician would.
Write in Russian. No JSON. No Markdown. No asterisks. No English headings.
This is a formal ECG protocol, not a consultation and not a treatment plan.

{BLANK_GUIDE}
Do not write "составляет", "равен", "регистрируется", "продолжительность", "частота сердечных сокращений" or "ударов в минуту".
Keep abbreviations as written: ЧСС, уд/мин, PQ, QRS, ST, QT, QTc, БПНПГ, БЛНПГ, ГЛЖ, ФП. Do not expand them into "пучок Гиса" or a full phrase.
Заключение is one short line, not a catalogue of every score.
Ignore scores below 0.5.
If two scores exclude each other, keep the one that matches the measurements.
Sinus rhythm and atrial fibrillation: unstable P and uneven RR means ФП.
Incomplete and complete bundle branch block: keep the one that matches the QRS duration.
Normal ECG and abnormal ECG: do not write both.
Use Russian abbreviations: неполная БПНПГ, БПНПГ, БЛНПГ, ГЛЖ, ФП, перегородочный инфаркт.
{MINNESOTA}
Do not write differential diagnosis, artifact discussion, comparison with other recordings, clinical correlation, recommendations, resuscitation, defibrillation, drugs, or calls for a team.
"""


def _signal_brief(measurements: dict, scores: list) -> str:
    text_lines = [
        f"{item.get('name')}: {item.get('value')}"
        for item in measurements.get("lines") or []
        if item.get("name") and item.get("value")
    ]
    lead_lines = []
    for row in measurements.get("leads") or []:
        lead_lines.append(
            f"{row.get('lead')}: ST {row.get('st')}, Q {row.get('q_ms')} мс, QT {row.get('qt_ms')} мс, качество {row.get('quality')}"
        )
    height_lines = []
    for row in measurements.get("amplitudes") or []:
        height_lines.append(
            f"{row.get('lead')}: P {row.get('p')}, Q {row.get('q')}, R {row.get('r')}, S {row.get('s')}, T {row.get('t')}"
        )
    ranked = []
    for item in scores:
        label = item.get("label")
        score = item.get("score")
        if not label or score is None:
            continue
        ranked.append(f"{label}: {float(score):.3f}")
    parts = [
        "MEASUREMENTS",
        str(measurements.get("description") or ""),
        "\n".join(text_lines),
        "LEADS",
        "\n".join(lead_lines),
        "AMPLITUDES",
        "\n".join(height_lines),
        "ECGFOUNDER",
        "\n".join(ranked[:20]),
    ]
    return "\n".join(part for part in parts if part.strip())


def form_signal_conclusion(measurements: dict | None, scores: list | None, locale: str = "en") -> dict:
    """Формальный бланк по цифровой кривой пишет Gemini, как протокол первого модуля."""
    if not measurements or not measurements.get("available"):
        raise EmptyCase("Сначала нужна разметка кривой.")
    if not scores:
        raise EmptyCase("Сначала нужны оценки ECGFounder.")
    brief = _signal_brief(measurements, scores)
    drafted = _completion(EYES_MODEL, f"{_signal_prompt(locale)}\n\n{brief}")
    return {"protocol": _protocol_form(drafted, locale), "protocol_model": EYES_MODEL}


def form_protocol(interpretation: str, extraction: dict | None = None, locale: str = "en") -> dict:
    """Второй шаг: бланк протокола пишет дешёвая модель. Снимок повторно не отправляется."""
    shown = interpretation.strip()
    if not shown:
        raise EmptyCase("Сначала нужно заключение на экране.")
    source = shown
    if extraction:
        source += "\n\nEXTRACTION:\n" + json.dumps(extraction, ensure_ascii=False)
    drafted = _completion(EYES_MODEL, f"{_protocol_prompt(locale)}\n\nSHOWN CONCLUSION:\n{source}")
    return {"protocol": _protocol_form(drafted, locale), "protocol_model": EYES_MODEL}


def analyze_ecg_image(payload: bytes, filename: str, mime_type: str, clinical_context: str = "") -> dict:
    return analyze_case(
        image=payload,
        filename=filename,
        mime_type=mime_type,
        clinical_context=clinical_context,
    )
