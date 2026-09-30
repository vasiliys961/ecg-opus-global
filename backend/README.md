# Backend

`app.py` serves the page and the API. There is no separate frontend build.

`GET /` is the desktop page. `GET /phone` is the phone page. `GET /i18n.js` is the language list and the cookie `opus-ui-locale`.

`POST /api/ecg/intake` opens an uploaded file. A waveform is scored by ECGFounder and delineated with NeuroKit. A sheet goes to `POST /api/ecg/analyze` (Gemini, then Opus). `POST /api/ecg/protocol` and `POST /api/ecg/signal/conclusion` ask Gemini for the description form. The 531 ensemble is not called. `POST /api/ecg/raw` returns 501.

`POST /api/bridge/session` creates the phone code. The upload is stored until the desktop polls it. Nothing is sent to the model from that store by itself.

---

# Сервер

`app.py` отдаёт страницу и API. Отдельной сборки фронтенда нет.

`GET /` — страница компьютера. `GET /phone` — страница телефона. `GET /i18n.js` — список языков и cookie `opus-ui-locale`.

`POST /api/ecg/intake` открывает загруженный файл. Кривая считается ECGFounder и размечается NeuroKit. Лист уходит в `POST /api/ecg/analyze` (Gemini, затем Opus). `POST /api/ecg/protocol` и `POST /api/ecg/signal/conclusion` просят у Gemini бланк описания. Ансамбль 531 не вызывается. `POST /api/ecg/raw` отвечает 501.

`POST /api/bridge/session` создаёт код для телефона. Загрузка хранится, пока компьютер её не заберёт. Сама по себе в модель она не отправляется.
