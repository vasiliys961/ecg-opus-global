# STEP 4. Воспроизведение ECGDeli на записи 00513

## Objective

Проверить, даёт ли цепочка

```text
PTB-XL raw 00513 → ECGDeli 1.1 → агрегация авторов PTB-XL+ → 531 колонка
```

опубликованную строку `ecg_id=513`.

Это не продукт и не клиническая проверка. Экстрактор в API не добавлялся. Сеть и веса не менялись.

## Sources

- PTB-XL 1.0.3, запись `00513`, оба файла 500 Гц и 100 Гц. Скачаны в `research/ecgdeli_reproduction/data/ptbxl/`.
- PTB-XL+ 1.0.1, `features/ecgdeli_features.csv`, строка `ecg_id=513`, взята из байтов 0–2999999 официального файла.
- ECGDeli tag `v1.1`, commit `3c13b1b2ff55152360f3cee992c1d1d66099aa14`, checkout `/tmp/ECGdeli`.
- Код, который статья и Zenodo называют сопутствующим: https://github.com/tmehari/ptbxl_feature_benchmark/tree/v1.0.0 , commit `e79c58e4fe962bb0e67be8ef878aa629a3177e56`.

Доступ 2026-09-28.

## Exact versions

Смотри `research/ecgdeli_reproduction/README.md`.

Python 3.11.9, macOS 26.6.2 arm64. MATLAB нет. Octave нет.

## Raw ECG specification

12 отведений, 10 секунд.

- 500 Гц: 5000 отсчётов, `.dat` 120000 байт, SHA-256 `a496d78ceb895ca9a81bdde32d62876d17022004a17d9e52bf9cd8318b6403e0`.
- 100 Гц: 1000 отсчётов, `.dat` 24000 байт, SHA-256 `ebafc313aacf8280a8cbd4f106b346128e8eee8e15465500e1808b4b42fbb604`.
- Единицы заголовка: `1000 ADC/mV`, format 16. Baseline в `.hea` задан поотводно.
- Порядок WFDB: `I, II, III, aVR, aVL, aVF, V1–V6`.
- Порядок колонок таблицы: `I, II, III, V1–V6, aVF, aVL, aVR`, затем Global.

Перестановка не выполнялась.

## ECGDeli configuration

Запуск на 00513 не состоялся.

```text
matlab -batch "disp('ecgdeli')"
stderr: command not found: matlab
```

`octave --version`: `command not found: octave`.

`output/raw_ecgdeli_00513/` без результатов делинеации. Другой библиотекой ECGDeli не заменялся.

Параметры, которыми авторы PTB-XL+ вызывали ECGDeli: `UNKNOWN`.

Параметры примера в теге `v1.1` записаны в research README и к записи 00513 не применялись. Пример фильтрует highpass 1 Гц и lowpass 40 Гц, notch 50 Гц, затем isoline, и аннотирует уже этот сигнал. Baseline removal в примере считается, но в аннотацию не идёт. Частота примера 1000 Гц.

## PTB-XL+ aggregation

Скрипт авторов не найден. Официальный репозиторий читает готовый `ecgdeli_features.csv` и не строит его. Своя агрегация не написана. `reproduced_ecgdeli_features_513.csv` не создавался.

## 531-feature comparison

Файл `research/ecgdeli_reproduction/comparison_513.json`.

Сравнение воспроизведённого вектора с опубликованным не выполнялось: воспроизведённого вектора нет.

| поле | значение |
| --- | --- |
| record_id | 513 |
| feature_count | 531 |
| comparison_executed | false |
| exact_match | false |
| max_abs_difference | null |
| mean_abs_difference | null |
| matching_features | null |
| missing_features | 531 |
| tolerance | 1e-6, порог был задан заранее и ни к чему не применялся |

`comparison_513.csv`: у всех 531 строк `published_value` из официальной строки, `reproduced_value` пустой, статус `MISSING`.

Опубликованная строка при этом ещё раз совпала с фикстурой проекта: 532/532.

## 500 Hz vs 100 Hz experiment

Оба эксперимента `NOT_RUN`. Ни max, ни mean, ни число совпавших признаков по частотам нет. Победитель не выбран.

## Preprocessing

Для пайплайна PTB-XL+ все пункты `UNKNOWN`: filtering, baseline, powerline, инверсия, clipping, пропуски, нормализация отведений, масштаб амплитуды, масштаб времени.

Что видно в примере ECGDeli, перечислено выше и не переносилось на 00513.

## Derived features

Где PTB-XL+ считает QT correction относительно медианы: `UNKNOWN`.

В ECGDeli `v1.1` функция `ExtractIntervalFeaturesFromFPT` считает Framingham на уровне комплекса в синхронной ветке, до какой-либо медианы по записи. Применяет ли таблица PTB-XL+ медиану к этим величинам, из найденного кода не следует.

Проверка «Framingham от уже сохранённых медиан» на строке 513 не равна ячейке `QT_IntFramingham_Global`. Это не даёт права дописать коррекцию после агрегации.

## Model prediction comparison

Не выполнялось. Воспроизведённого 531-вектора нет, ансамбль на нём не вызывался. Совпадения предсказаний нет, потому что второго входа нет.

## What is proven

- Checkout ECGDeli, на котором остановились, — тег `v1.1`, commit `3c13b1b2`.
- Официальный код PTB-XL+ по ссылке из статьи не содержит сборку `ecgdeli_features.csv`.
- Сигнал 00513 скачан в двух частотах, заголовки прочитаны.
- Опубликованная строка 513 по-прежнему равна фикстуре проекта.
- На этой машине ECGDeli не стартует.

## What remains unknown

Версия архива, которой пользовались авторы, частота, фильтр, порядок каналов на входе ECGDeli, формула IQR, шаг коррекции QT, равенство `mean/std` сети всей таблице PTB-XL+.

## Conclusion

Полный пайплайн `raw → ECGDeli → агрегация PTB-XL+ → 531` на записи 00513 не воспроизведён. Названия колонок по-прежнему не считаются доказательством, что ECGDeli сам пишет эти 531 числа.

```text
RAW_TO_531_STATUS = NOT_PROVEN
```

`clinically validated` и `production ready` не заявляются. Экстрактор в API не входил.
