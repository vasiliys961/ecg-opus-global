# ECG Opus

Research decision support for an ECG. This is not a medical device and not an autonomous diagnosis.

The page language is English until another language is chosen. The switcher uses the cookie `opus-ui-locale` (one year). The list is English, Spanish, French, Arabic, Hindi, Portuguese (Brazil), Indonesian, Malay, Turkish, Simplified Chinese, and Russian. Arabic is laid out right to left. The same cookie is read by the phone page. Dictation and the model reply follow that language. The long format guide on the page stays in English.

## Two readings

A picture, a PDF, or a sheet of text goes to Gemini 3.8 Flash, then to Opus 5.5 for the first reading. **Write the protocol** asks Gemini for a Minnesota description form. Opus is not called on that step.

A digital tracing of about 10 seconds and 12 leads goes to ECGFounder (150 sigmoid scores) and to a NeuroKit delineation: rate, intervals, ST displacement, and premature beats. **Write the conclusion** asks Gemini for the same kind of form. The raw samples are not sent to the model. The model sees the delineation text and the scores. Opus is not called on this path. A language model does not change the ECGFounder scores.

ECGFounder publishes AUROC, not a percent correct. This repository has not run the authors' `ptbxl_eval.py`. A score is not a calibrated probability. Important ratios on a CSV are in the file's own units, not millimetres, so a textbook millimetre cutoff is not applied.

The name, year of birth, and sex stay on the computer. They are not sent into the model. They reach the computer from the phone only when **Send to computer** is pressed.

## Phone

Start the server on `0.0.0.0`. A phone on the same Wi-Fi opens the code under the patient fields. **Review** on the phone stays on the phone. **Send to computer** is a separate press. A file lands in **File**, a clip in **Strip video**. The desktop does not start the review by itself.

## Run

Python 3.11. ECGFounder weights stay local at `models/ecgfounder/12_lead_ECGFounder.pth` and are not in git. Override with `ECGFOUNDER_WEIGHTS`.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn backend.app:app --host 0.0.0.0 --port 8765
```

Page: [http://127.0.0.1:8765](http://127.0.0.1:8765).

Picture and text reading needs `LLM_API_KEY` or `OPENROUTER_API_KEY`. Without a key that channel returns 503. The digital score still needs the weights file.

```bash
PYTHONPATH=. pytest
```

## Files the page opens

CSV (eight leads I, II, V1–V6 are completed to twelve when the other four are absent), EDF, a WFDB pair in one zip (format 16 only), MATLAB 5 `.mat` (not v7.3), HL7 aECG and Philips PageWriter XML, SCP-ECG when it is uncompressed or uses the standard Huffman table 19999, a DICOM waveform, a zip of one known file, and PDF, PNG, JPEG, GIF, or WEBP. A phone HEIC or HEIF picture is converted to JPEG in the browser.

These stop: ZQECG, Contec `.ECG` and a Contec CSV with `None` cells, Healforce samples that are 3 leads and under a second, SCP-ECG with a private Huffman table, bimodal compression, or reference-beat subtraction, GE MUSE, Mindray, and Mortara XML, and a lone `.hea` or `.dat`.

If the file has no sampling rate, type it beside **File**. 25 mm/s paper speed is not that rate. A tracing outside about 8–12 seconds is not scored by ECGFounder.

## What this repository does not do

`POST /api/ecg/raw` returns 501. The 531-feature ensemble is not called by the page. Reconstructing those 531 features from a raw tracing is not proven (`RAW_TO_531_STATUS`). The research notes under `docs/` record that limit. They are not a claim that the page runs the ensemble.

---

# ЭКГ Opus

Исследовательская поддержка решения по ЭКГ. Это не медицинское изделие и не самостоятельный диагноз.

Язык страницы английский, пока не выбран другой. Переключатель пишет cookie `opus-ui-locale` на год. В списке английский, испанский, французский, арабский, хинди, португальский (Бразилия), индонезийский, малайский, турецкий, упрощённый китайский и русский. Для арабского включается письмо справа налево. Ту же cookie читает страница телефона. Диктовка и ответ модели идут на выбранном языке. Длинная инструкция по форматам на странице остаётся на английском.

## Два разбора

Снимок, PDF или текст листа идут в Gemini 3.8 Flash, затем в Opus 5.5 для первого разбора. **Write the protocol** просит у Gemini бланк описания по Миннесоте. На этом шаге Opus не вызывается.

Цифровая кривая около 10 секунд и 12 отведений идёт в ECGFounder (150 сигмоид) и в разметку NeuroKit: ЧСС, интервалы, смещение ST и внеочередные комплексы. **Write the conclusion** просит у Gemini такой же бланк. Сами отсчёты модели не отправляются. Модель видит текст разметки и оценки. На этом пути Opus не вызывается. Языковая модель не меняет оценки ECGFounder.

ECGFounder публикует AUROC, а не процент верных ответов. В этом репозитории авторский `ptbxl_eval.py` не запускался. Оценка — не калиброванная вероятность. Важные соотношения в CSV записаны в единицах файла, не в миллиметрах, поэтому учебный порог в миллиметрах к ним не применяется.

ФИО, год рождения и пол остаются на компьютере и в модель не уходят. С телефона они попадают на компьютер только по кнопке **Send to computer**.

## Телефон

Сервер слушает `0.0.0.0`. Телефон в той же сети Wi-Fi открывает код под полями карточки. **Review** на телефоне остаётся на телефоне. **Send to computer** нажимают отдельно. Файл встаёт в **File**, ролик в **Strip video**. На компьютере разбор сам не начинается.

## Запуск

Нужен Python 3.11. Веса ECGFounder лежат локально в `models/ecgfounder/12_lead_ECGFounder.pth` и в git не входят. Путь можно заменить через `ECGFOUNDER_WEIGHTS`.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn backend.app:app --host 0.0.0.0 --port 8765
```

Страница: [http://127.0.0.1:8765](http://127.0.0.1:8765).

Разбор снимка и текста требует `LLM_API_KEY` или `OPENROUTER_API_KEY`. Без ключа этот канал отвечает 503. Цифровой расчёт по-прежнему требует файл весов.

```bash
PYTHONPATH=. pytest
```

## Какие файлы открываются

CSV (если есть только I, II и V1–V6, остальные четыре отведения собираются из них), EDF, пара WFDB в одном zip (только формат 16), MATLAB 5 `.mat` (не v7.3), XML HL7 aECG и Philips PageWriter, SCP-ECG без сжатия или со стандартной таблицей Хаффмана 19999, волна DICOM, zip с одним известным файлом, а также PDF, PNG, JPEG, GIF и WEBP. Снимок телефона HEIC или HEIF в браузере переводится в JPEG.

Не открываются: ZQECG, собственный файл Contec `.ECG` и CSV Contec с ячейками `None`, проверенные записи Healforce (3 отведения и меньше секунды), SCP-ECG со своей таблицей Хаффмана, со сдвоенным сжатием или с вычитанием опорного комплекса, XML GE MUSE, Mindray и Mortara, а также один файл `.hea` или `.dat` без пары.

Если в файле нет частоты, её указывают рядом с **File**. Скорость бумаги 25 мм/с — это не частота. Кривая вне примерно 8–12 секунд в ECGFounder не считается.

## Чего этот репозиторий не делает

`POST /api/ecg/raw` отвечает 501. Ансамбль на 531 признаке страница не вызывает. Собрать эти 531 признака из сырой кривой не доказано (`RAW_TO_531_STATUS`). Заметки в `docs/` фиксируют этот предел. Это не утверждение, что страница запускает ансамбль.
