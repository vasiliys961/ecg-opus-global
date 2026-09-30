/* Тот же приём, что в Doctor Opus: cookie opus-ui-locale и язык диктовки от выбранного языка.
   Английский по умолчанию, как в глобальной версии. Русский в списке есть. */
(function () {
  const COOKIE = "opus-ui-locale";
  const DEFAULT_LOCALE = "en";
  const LOCALES = ["en", "es", "fr", "ar", "hi", "pt-BR", "id", "ms", "tr", "zh-CN", "ru"];
  const LABELS = {
    ru: "Русский",
    en: "English",
    es: "Español",
    fr: "Français",
    ar: "العربية",
    hi: "हिन्दी",
    "pt-BR": "Português (BR)",
    id: "Bahasa Indonesia",
    ms: "Bahasa Melayu",
    tr: "Türkçe",
    "zh-CN": "简体中文",
  };
  const SPEECH = {
    ru: "ru-RU",
    en: "en-US",
    es: "es-ES",
    fr: "fr-FR",
    ar: "ar-SA",
    hi: "hi-IN",
    "pt-BR": "pt-BR",
    id: "id-ID",
    ms: "ms-MY",
    tr: "tr-TR",
    "zh-CN": "zh-CN",
  };
  const TEXT = {
    ru: {
      language: "Язык", support: "Поддержка решения, не диагноз.", patient: "Пациент",
      fioStays: "ФИО остаётся на этом компьютере и в разбор не уходит.",
      fio: "ФИО", birthYear: "Год рождения", sex: "Пол", sexUnset: "не указан", sexMale: "муж.", sexFemale: "жен.",
      studyDate: "Дата снятия ЭКГ", qrCaption: "Код для телефона в той же сети Wi-Fi.",
      pair: "Сопряжение с телефоном", ecg: "ЭКГ",
      ecgHint: "Загрузите файл и нажмите «Разобрать». Если формат не открывается, сообщение появится под кнопкой.",
      file: "Файл", rate: "Частота, если в файле её нет", video: "Видео ленты", review: "Разобрать",
      videoHint: "Ролик вдоль ленты — отдельная кнопка: из видео берутся кадры одной записи.",
      formats: "Инструкция и форматы", context: "Клинический контекст без фамилии и контактов",
      voice: "Голос", voiceOn: "Слушаю", voiceNo: "Нет",
      years: "лет", age: "Возраст", intervalWord: "Интервал", amplitudeWord: "Амплитуда", ms: "мс", mv: "мВ",
      protocolTitle: "Протокол описания ЭКГ",
      makeProtocol: "Сформировать протокол", print: "Печать", download: "Скачать Word", share: "Поделиться",
      ruler: "Линейка", caliperNote: "Калибровка вручную: сколько пикселей в 1 мм сетки. Скорость меняет время, усиление меняет напряжение. Сетка сама не распознаётся.",
      px: "Пикселей на 1 мм", gainLabel: "Усиление, мм/мВ",
      conclude: "Сформировать заключение", trace: "Кривая", delineation: "Разметка",
      gridNote: "Сетка условная. Это не калибр 25 мм/с.", param: "Параметр", value: "Значение",
      waitingPhone: "Жду смартфонную версию.", phoneCard: "Карточка пришла со смартфона.",
      fileLanded: "Файл встал в «Файл». Нажмите «Разобрать».", videoLanded: "Ролик встал в «Видео ленты».",
      phoneLost: "Связь со смартфоном прервалась.", phoneCodeFail: "Код для смартфона не создался.",
      refreshCode: "Код телефона обновите, обновив страницу.",
      fileChosen: "Файл выбран. Нажмите «Разобрать».", opening: "Определяю файл и открываю его поток.",
      needFile: "Нужен файл или ролик.", reviewFail: "Разбор прервался. Нажмите «Разобрать» ещё раз.",
      fileFail: "Файл не открылся. Нажмите «Разобрать» ещё раз.", photoFail: "Снимок не открылся.",
      phonePhotoFail: "Снимок с телефона не открылся.", stripFail: "Ролик не открылся. Снимите ленту ещё раз коротким видео.",
      stripBusy: "Беру кадры вдоль ленты.", concludeNeed: "Сначала посчитайте запись.", concluding: "Собираю заключение.",
      concludeFail: "Заключение не собралось. Нажмите кнопку ещё раз.",
      protocolNeed: "Сначала дождитесь заключения по кнопке «Разобрать».",
      protocolBusy: "Собираю протокол. Это отдельный шаг и тоже занимает время.",
      protocolEmpty: "Протокол пришёл пустым.", protocolFail: "Протокол не собрался. Нажмите кнопку ещё раз.",
      copied: "Текст протокола скопирован.",
      photo: "Снимок листа", recordFile: "Файл записи", sendNote: "Кнопка отправки появляется, если страница открыта кодом с компьютера.",
      result: "Разбор", photoPicked: "Снимок выбран. Нажмите «Разобрать».", videoPicked: "Ролик выбран. Нажмите «Разобрать».",
      reviewing: "Разбираю на этом телефоне.", reviewReady: "Разбор готов на этом телефоне.",
      reviewFailPhone: "Разбор не выполнился. Нажмите «Разобрать» ещё раз.",
      needAny: "Нужен снимок, файл или ролик.", stripReview: "Беру кадры ленты и разбираю.",
      pairWhy: "Зачем", pairWhyText: "Телефон снимает лист или открывает файл там, где компьютера нет. Карточка и приём файла остаются здесь. Разбор на телефоне сам сюда не приходит.",
      pairHow: "Как связать",
      pair1: "Телефон и этот компьютер в одной сети Wi-Fi.",
      pair2: "Камера телефона на код под полями карточки.",
      pair3: "На телефоне «Разобрать» считает запись на телефоне и никуда её не отправляет.",
      pair4: "«Отправить на компьютер» нажимают отдельно. Файл встаёт в «Файл», ролик в «Видео ленты». Здесь «Разобрать» нажимаете сами.",
      pairEnd: "ФИО попадает на компьютер только по кнопке «Отправить». В разбор модели оно не уходит.",
      phoneTitle: "ЭКГ", phoneNote: "Разбор идёт здесь. На компьютер ничего не уходит, пока не нажмёте «Отправить на компьютер». ФИО в разбор модели не уходит.",
      send: "Отправить на компьютер",
    },
    en: {
      language: "Language", support: "Decision support, not a diagnosis.", patient: "Patient",
      fioStays: "The name stays on this computer and is not sent into the reading.",
      fio: "Name", birthYear: "Year of birth", sex: "Sex", sexUnset: "not stated", sexMale: "male", sexFemale: "female",
      studyDate: "ECG date", qrCaption: "Phone code, same Wi-Fi.",
      pair: "Pair the phone", ecg: "ECG",
      ecgHint: "Choose a file and press Review. If the format does not open, the reason appears under the button.",
      file: "File", rate: "Rate, if the file has none", video: "Strip video", review: "Review",
      videoHint: "A clip along the strip is a separate button: frames of one recording are taken from the video.",
      formats: "Guide and formats", context: "Clinical context, no name or contact details",
      voice: "Voice", voiceOn: "Listening", voiceNo: "None",
      years: "years", age: "Age", intervalWord: "Interval", amplitudeWord: "Amplitude", ms: "ms", mv: "mV",
      protocolTitle: "ECG description form",
      makeProtocol: "Write the protocol", print: "Print", download: "Download Word", share: "Share",
      ruler: "Caliper", caliperNote: "Set it by hand: how many pixels are in 1 mm of the grid. Speed changes time, gain changes voltage. The grid is not detected.",
      px: "Pixels per 1 mm", gainLabel: "Gain, mm/mV",
      conclude: "Write the conclusion", trace: "Tracing", delineation: "Measurements",
      gridNote: "The grid is only a guide. It is not a 25 mm/s calibration.", param: "Item", value: "Value",
      waitingPhone: "Waiting for the phone.", phoneCard: "The card arrived from the phone.",
      fileLanded: "The file is in File. Press Review.", videoLanded: "The clip is in Strip video.",
      phoneLost: "The phone link stopped.", phoneCodeFail: "The phone code was not created.",
      refreshCode: "Refresh the page to renew the phone code.",
      fileChosen: "File selected. Press Review.", opening: "Identifying the file and opening its stream.",
      needFile: "A file or a clip is needed.", reviewFail: "The review stopped. Press Review again.",
      fileFail: "The file did not open. Press Review again.", photoFail: "The picture did not open.",
      phonePhotoFail: "The phone picture did not open.", stripFail: "The clip did not open. Record the strip again, briefly.",
      stripBusy: "Taking frames along the strip.", concludeNeed: "Score the recording first.", concluding: "Writing the conclusion.",
      concludeFail: "The conclusion was not written. Press the button again.",
      protocolNeed: "Wait for the reading from Review first.",
      protocolBusy: "Writing the protocol. This is a separate step and it takes time.",
      protocolEmpty: "The protocol came back empty.", protocolFail: "The protocol was not written. Press the button again.",
      copied: "The protocol text was copied.",
      photo: "Sheet photo", recordFile: "Recording file", sendNote: "Send appears when this page was opened from the computer code.",
      result: "Reading", photoPicked: "Photo selected. Press Review.", videoPicked: "Clip selected. Press Review.",
      reviewing: "Reviewing on this phone.", reviewReady: "The reading is ready on this phone.",
      reviewFailPhone: "The review did not finish. Press Review again.",
      needAny: "A photo, a file, or a clip is needed.", stripReview: "Taking strip frames and reviewing.",
      pairWhy: "Why", pairWhyText: "The phone photographs a sheet or opens a file where there is no computer. The card and the file intake stay here. A reading on the phone does not arrive by itself.",
      pairHow: "How to link",
      pair1: "The phone and this computer are on the same Wi-Fi.",
      pair2: "Point the phone camera at the code under the card fields.",
      pair3: "Review on the phone scores the recording on the phone and does not send it.",
      pair4: "Send to computer is a separate press. A file lands in File, a clip in Strip video. Press Review here yourself.",
      pairEnd: "The name reaches this computer only through Send. It is not sent into the model.",
      phoneTitle: "ECG", phoneNote: "The review stays on this phone until you press Send to computer. The name is not sent into the model.",
      send: "Send to computer",
    },
    es: {
      language: "Idioma", support: "Apoyo a la decisión, no un diagnóstico.", patient: "Paciente",
      fioStays: "El nombre se queda en este ordenador y no entra en la lectura.",
      fio: "Nombre", birthYear: "Año de nacimiento", sex: "Sexo", sexUnset: "no indicado", sexMale: "hombre", sexFemale: "mujer",
      studyDate: "Fecha del ECG", qrCaption: "Código del teléfono, misma Wi-Fi.",
      pair: "Vincular el teléfono", ecg: "ECG",
      ecgHint: "Elija un archivo y pulse Revisar. Si el formato no se abre, el motivo aparece bajo el botón.",
      file: "Archivo", rate: "Frecuencia, si el archivo no la trae", video: "Vídeo de la tira", review: "Revisar",
      videoHint: "El vídeo a lo largo de la tira es un botón aparte: de él se toman los fotogramas.",
      formats: "Guía y formatos", context: "Contexto clínico, sin nombre ni contactos",
      voice: "Voz", voiceOn: "Escucho", voiceNo: "No",
      phoneTitle: "ECG", phoneNote: "La revisión se queda en el teléfono hasta que pulse Enviar al ordenador. El nombre no entra en el modelo.",
      send: "Enviar al ordenador",
    },
    fr: {
      language: "Langue", support: "Aide à la décision, pas un diagnostic.", patient: "Patient",
      fioStays: "Le nom reste sur cet ordinateur et n’entre pas dans la lecture.",
      fio: "Nom", birthYear: "Année de naissance", sex: "Sexe", sexUnset: "non indiqué", sexMale: "homme", sexFemale: "femme",
      studyDate: "Date de l’ECG", qrCaption: "Code du téléphone, même Wi-Fi.",
      pair: "Relier le téléphone", ecg: "ECG",
      ecgHint: "Choisissez un fichier et appuyez sur Lire. Si le format ne s’ouvre pas, la raison s’affiche sous le bouton.",
      file: "Fichier", rate: "Fréquence, si le fichier ne l’a pas", video: "Vidéo de la bande", review: "Lire",
      videoHint: "La vidéo le long de la bande est un bouton à part : les images en sont extraites.",
      formats: "Guide et formats", context: "Contexte clinique, sans nom ni coordonnées",
      voice: "Voix", voiceOn: "J’écoute", voiceNo: "Non",
      phoneTitle: "ECG", phoneNote: "La lecture reste sur le téléphone tant que vous n’appuyez pas sur Envoyer à l’ordinateur. Le nom n’entre pas dans le modèle.",
      send: "Envoyer à l’ordinateur",
    },
    ar: {
      language: "اللغة", support: "دعم للقرار، وليس تشخيصًا.", patient: "المريض",
      fioStays: "يبقى الاسم على هذا الحاسوب ولا يدخل في القراءة.",
      fio: "الاسم", birthYear: "سنة الميلاد", sex: "الجنس", sexUnset: "غير مذكور", sexMale: "ذكر", sexFemale: "أنثى",
      studyDate: "تاريخ التخطيط", qrCaption: "رمز الهاتف، نفس شبكة الواي فاي.",
      pair: "ربط الهاتف", ecg: "تخطيط القلب",
      ecgHint: "اختر ملفًا ثم اضغط مراجعة. إذا لم يُفتح التنسيق، يظهر السبب تحت الزر.",
      file: "ملف", rate: "التردد، إن لم يكن في الملف", video: "فيديو الشريط", review: "مراجعة",
      videoHint: "فيديو الشريط زر مستقل: تُؤخذ منه لقطات التسجيل.",
      formats: "الدليل والتنسيقات", context: "سياق سريري بلا اسم ولا وسيلة اتصال",
      voice: "صوت", voiceOn: "أستمع", voiceNo: "لا",
      phoneTitle: "تخطيط القلب", phoneNote: "تبقى المراجعة على الهاتف حتى تضغط إرسال إلى الحاسوب. الاسم لا يدخل النموذج.",
      send: "إرسال إلى الحاسوب",
    },
    hi: {
      language: "भाषा", support: "निर्णय में सहायता, निदान नहीं.", patient: "रोगी",
      fioStays: "नाम इस कंप्यूटर पर रहता है और पढ़ने में नहीं जाता.",
      fio: "नाम", birthYear: "जन्म वर्ष", sex: "लिंग", sexUnset: "नहीं बताया", sexMale: "पुरुष", sexFemale: "स्त्री",
      studyDate: "ईसीजी की तारीख", qrCaption: "फ़ोन का कोड, वही वाई-फाई.",
      pair: "फ़ोन जोड़ना", ecg: "ईसीजी",
      ecgHint: "फ़ाइल चुनें और समीक्षा दबाएँ. प्रारूप न खुले तो कारण बटन के नीचे आएगा.",
      file: "फ़ाइल", rate: "आवृत्ति, अगर फ़ाइल में नहीं है", video: "पट्टी का वीडियो", review: "समीक्षा",
      videoHint: "पट्टी का वीडियो अलग बटन है: उसी से फ़्रेम लिए जाते हैं.",
      formats: "मार्गदर्शिका और प्रारूप", context: "नैदानिक प्रसंग, नाम और संपर्क नहीं",
      voice: "आवाज़", voiceOn: "सुन रहा हूँ", voiceNo: "नहीं",
      phoneTitle: "ईसीजी", phoneNote: "समीक्षा फ़ोन पर रहती है जब तक कंप्यूटर पर भेजें नहीं दबाते. नाम मॉडल में नहीं जाता.",
      send: "कंप्यूटर पर भेजें",
    },
    "pt-BR": {
      language: "Idioma", support: "Apoio à decisão, não um diagnóstico.", patient: "Paciente",
      fioStays: "O nome fica neste computador e não entra na leitura.",
      fio: "Nome", birthYear: "Ano de nascimento", sex: "Sexo", sexUnset: "não informado", sexMale: "masculino", sexFemale: "feminino",
      studyDate: "Data do ECG", qrCaption: "Código do telefone, mesma Wi-Fi.",
      pair: "Parear o telefone", ecg: "ECG",
      ecgHint: "Escolha um arquivo e pressione Revisar. Se o formato não abrir, o motivo aparece sob o botão.",
      file: "Arquivo", rate: "Frequência, se o arquivo não tiver", video: "Vídeo da tira", review: "Revisar",
      videoHint: "O vídeo ao longo da tira é um botão à parte: os quadros saem dele.",
      formats: "Guia e formatos", context: "Contexto clínico, sem nome nem contato",
      voice: "Voz", voiceOn: "Ouvindo", voiceNo: "Não",
      phoneTitle: "ECG", phoneNote: "A revisão fica no telefone até você pressionar Enviar ao computador. O nome não entra no modelo.",
      send: "Enviar ao computador",
    },
    id: {
      language: "Bahasa", support: "Dukungan keputusan, bukan diagnosis.", patient: "Pasien",
      fioStays: "Nama tetap di komputer ini dan tidak masuk ke pembacaan.",
      fio: "Nama", birthYear: "Tahun lahir", sex: "Jenis kelamin", sexUnset: "tidak diisi", sexMale: "laki-laki", sexFemale: "perempuan",
      studyDate: "Tanggal EKG", qrCaption: "Kode ponsel, Wi-Fi yang sama.",
      pair: "Hubungkan ponsel", ecg: "EKG",
      ecgHint: "Pilih berkas lalu tekan Tinjau. Jika format tidak terbuka, alasan muncul di bawah tombol.",
      file: "Berkas", rate: "Frekuensi, jika tidak ada di berkas", video: "Video pita", review: "Tinjau",
      videoHint: "Video sepanjang pita adalah tombol sendiri: bingkai diambil dari situ.",
      formats: "Panduan dan format", context: "Konteks klinis, tanpa nama atau kontak",
      voice: "Suara", voiceOn: "Mendengar", voiceNo: "Tidak",
      phoneTitle: "EKG", phoneNote: "Tinjauan tetap di ponsel sampai Anda menekan Kirim ke komputer. Nama tidak masuk ke model.",
      send: "Kirim ke komputer",
    },
    ms: {
      language: "Bahasa", support: "Sokongan keputusan, bukan diagnosis.", patient: "Pesakit",
      fioStays: "Nama kekal di komputer ini dan tidak dihantar ke bacaan.",
      fio: "Nama", birthYear: "Tahun lahir", sex: "Jantina", sexUnset: "tidak dinyatakan", sexMale: "lelaki", sexFemale: "perempuan",
      studyDate: "Tarikh ECG", qrCaption: "Kod telefon, Wi-Fi yang sama.",
      pair: "Pasangkan telefon", ecg: "ECG",
      ecgHint: "Pilih fail dan tekan Semak. Jika format tidak terbuka, sebabnya muncul di bawah butang.",
      file: "Fail", rate: "Kadar, jika tiada dalam fail", video: "Video jalur", review: "Semak",
      videoHint: "Video sepanjang jalur ialah butang berasingan: bingkai diambil daripadanya.",
      formats: "Panduan dan format", context: "Konteks klinikal, tanpa nama atau hubungan",
      voice: "Suara", voiceOn: "Mendengar", voiceNo: "Tiada",
      phoneTitle: "ECG", phoneNote: "Semakan kekal di telefon sehingga anda menekan Hantar ke komputer. Nama tidak masuk ke model.",
      send: "Hantar ke komputer",
    },
    tr: {
      language: "Dil", support: "Karar desteği, tanı değil.", patient: "Hasta",
      fioStays: "Ad bu bilgisayarda kalır ve okumaya girmez.",
      fio: "Ad", birthYear: "Doğum yılı", sex: "Cinsiyet", sexUnset: "belirtilmedi", sexMale: "erkek", sexFemale: "kadın",
      studyDate: "EKG tarihi", qrCaption: "Telefon kodu, aynı Wi-Fi.",
      pair: "Telefonu eşle", ecg: "EKG",
      ecgHint: "Dosyayı seçin ve İncele’ye basın. Biçim açılmazsa neden düğmenin altında yazar.",
      file: "Dosya", rate: "Hız, dosyada yoksa", video: "Şerit videosu", review: "İncele",
      videoHint: "Şerit boyunca video ayrı bir düğmedir: kareler oradan alınır.",
      formats: "Kılavuz ve biçimler", context: "Klinik bağlam, ad ve iletişim yok",
      voice: "Ses", voiceOn: "Dinliyorum", voiceNo: "Yok",
      phoneTitle: "EKG", phoneNote: "İnceleme, Bilgisayara gönder’e basılana kadar telefonda kalır. Ad modele gitmez.",
      send: "Bilgisayara gönder",
    },
    "zh-CN": {
      language: "语言", support: "决策支持，不是诊断。", patient: "患者",
      fioStays: "姓名留在这台电脑上，不进入判读。",
      fio: "姓名", birthYear: "出生年份", sex: "性别", sexUnset: "未填", sexMale: "男", sexFemale: "女",
      studyDate: "心电图日期", qrCaption: "手机码，同一 Wi-Fi。",
      pair: "配对手机", ecg: "心电图",
      ecgHint: "选择文件后按判读。格式打不开时，原因显示在按钮下方。",
      file: "文件", rate: "采样率，文件里没有时填写", video: "条带视频", review: "判读",
      videoHint: "沿条带的视频是单独按钮：从中取帧。",
      formats: "说明与格式", context: "临床情况，不要姓名和联系方式",
      voice: "语音", voiceOn: "正在听", voiceNo: "无",
      phoneTitle: "心电图", phoneNote: "在按下发到电脑之前，判读留在手机上。姓名不进入模型。",
      send: "发到电脑",
    },
  };

  function readCookie() {
    const raw = document.cookie.split(";").map((item) => item.trim()).find((item) => item.startsWith(COOKIE + "="));
    const value = raw ? decodeURIComponent(raw.split("=").slice(1).join("=")) : "";
    return LOCALES.indexOf(value) >= 0 ? value : DEFAULT_LOCALE;
  }

  const locale = readCookie();
  const pack = TEXT[locale] || TEXT[DEFAULT_LOCALE];

  function text(key) {
    return pack[key] || TEXT[DEFAULT_LOCALE][key] || "";
  }

  function apply() {
    document.documentElement.lang = locale;
    document.documentElement.dir = locale === "ar" ? "rtl" : "ltr";
    document.querySelectorAll("[data-i18n]").forEach((node) => {
      const value = text(node.getAttribute("data-i18n"));
      if (value) node.textContent = value;
    });
    const select = document.getElementById("locale-select");
    if (!select) return;
    select.replaceChildren();
    LOCALES.forEach((item) => {
      const option = document.createElement("option");
      option.value = item;
      option.textContent = LABELS[item];
      if (item === locale) option.selected = true;
      select.appendChild(option);
    });
    select.onchange = () => {
      document.cookie = COOKIE + "=" + encodeURIComponent(select.value) + "; path=/; max-age=31536000; samesite=lax";
      window.location.reload();
    };
  }

  globalThis.ECG_I18N = {
    locale: locale,
    text: text,
    speechCode: function () { return SPEECH[locale] || SPEECH[DEFAULT_LOCALE]; },
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", apply);
  else apply();
})();
