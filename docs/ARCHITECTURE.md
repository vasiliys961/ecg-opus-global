# Архитектура doctor-opus-ecg-engine

Три пути не смешиваются.

### EXISTING VALIDATED PATH

```text
531 CSV → существующий ансамбль MLP + CNN + ResNet1D → 24 score
```

Этот путь сверен с `ecg_web_up`: четыре вектора, абсолютная разница 0. Вход — готовые 531 колонки в порядке `ecg_engine/feature_columns.py`. Сеть, среднее, `mean/std` и индексы 24 выходов не меняются.

### FUTURE RAW PATH

```text
raw 12-lead → exact extractor → те же 531 → существующий ансамбль
```

Статус: `RAW_TO_531_STATUS = NOT_PROVEN`. Опубликованная таблица PTB-XL+ `ecgdeli_features.csv` совпала со схемой и со строкой `ecg_id=513`, но повторный расчёт из сигнала не сделан. `RawECGExtractor` возвращает отказ и не подставляет числа. Подробности: `docs/FEATURE_531_PROVENANCE.md`, `docs/RAW_TO_531_BLOCKERS.md`.

### FUTURE RAW MODEL

```text
raw 12-lead → новая сеть
```

Это другой вход и другие веса. Размерность 531 у нового экстрактора не делает его входом нынешнего ансамбля. Этот путь не начат.

```text
ECG image → разбор изображения, отдельно от обоих числовых путей
```

Картинка не считается 12-lead raw и не превращается в 531 признак.

## Каталоги сейчас

```text
ecg_engine/          инференс, схема, коды SCP, CLI, RawECGExtractor со статусом NOT_PROVEN
models/ecg_ensemble/ веса и mean/std, копия ecg_web_up
tests/fixtures/      публичный CSV ecg_id=513
tests/regression/    сверка с оригинальным скриптом
docs/                аудит и контракты
frontend/            страница с режимами Image, 531 CSV и заглушкой raw
backend/             POST /api/ecg/predict, /api/ecg/image, /api/ecg/raw
```

Движок не импортирует `doctor-opus-global`. Production-репозиторий не менялся.

## Контракт результата CLI

```bash
python -m ecg_engine.predict tests/fixtures/another_ecg_features.csv
```

`predictions` — среднее трёх сигмоид, ключи в порядке индексов модели. `heads` хранит MLP, CNN и ResNet по отдельности. Порога нет: число — model score, не калиброванная вероятность.

Модели грузятся на CPU и в процессе держатся в кэше. Отдельного сервера на этом шаге нет, поэтому «один раз на процесс» относится к повторным вызовам `predict_csv` внутри одного интерпретатора.

## Что уже отделено от числового пути

Канал изображения описан в `docs/DOCTOR_OPUS_ECG_AUDIT.md`. Он не производит 531 признак. PDF и одноканальный USB-снимок в raw 12-lead не входят. Вторая сеть на сыром сигнале не создавалась.
