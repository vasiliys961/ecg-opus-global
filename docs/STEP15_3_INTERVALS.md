# STEP 15.3 — интервалы из fiducials

Статус: `BLOCKED_BY_OS_READ`.

Чтение байтов `.atr` закрыто macOS (`PermissionError`, errno 1, `Operation not permitted`). Повтор вне песочницы дал ту же ошибку. Скачивание, подстановка точек записи 00513 и выдуманные номера отсчётов не использовались.

`interval_features.csv` и `fiducial_span.csv` не созданы: без содержимого аннотаций интервалы считать нельзя.

## Что открыто

| Проверка | Результат |
| --- | --- |
| Ожидаемых файлов | 130 (10 id × 13 аннотаций) |
| Файлы есть на диске (`exists` + `stat`) | 130 |
| Размер, байт | 2304–4776, нулевых нет |
| Байты прочитаны | 0 / 130 |
| Id посчитано | 0 |
| Диапазон номеров отсчётов | не прочитан |
| Индекс median beat | не проверялся по содержимому |
| Ансамбль | не вызывался |
| Официальная строка PTB-XL+ | отсутствует, сравнение не делалось |

Метаданные Drive (имя и размер) содержимым `.atr` не являются.

Корень:

```text
/Users/maxmobiles.ru/Google Drive/Мой диск/ptb-xl-a-comprehensive-electrocardiographic-feature-dataset-1.0.1/fiducial_points/ecgdeli/02000/
```

Id: 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009.

## Непрочитанные пути

Все 130 файлов вернули `PermissionError` при `read_bytes()`.

```text
02000_points_global.atr
02000_points_lead_I.atr
02000_points_lead_II.atr
02000_points_lead_III.atr
02000_points_lead_aVR.atr
02000_points_lead_aVL.atr
02000_points_lead_aVF.atr
02000_points_lead_V1.atr
02000_points_lead_V2.atr
02000_points_lead_V3.atr
02000_points_lead_V4.atr
02000_points_lead_V5.atr
02000_points_lead_V6.atr
02001_points_global.atr
02001_points_lead_I.atr
02001_points_lead_II.atr
02001_points_lead_III.atr
02001_points_lead_aVR.atr
02001_points_lead_aVL.atr
02001_points_lead_aVF.atr
02001_points_lead_V1.atr
02001_points_lead_V2.atr
02001_points_lead_V3.atr
02001_points_lead_V4.atr
02001_points_lead_V5.atr
02001_points_lead_V6.atr
02002_points_global.atr
02002_points_lead_I.atr
02002_points_lead_II.atr
02002_points_lead_III.atr
02002_points_lead_aVR.atr
02002_points_lead_aVL.atr
02002_points_lead_aVF.atr
02002_points_lead_V1.atr
02002_points_lead_V2.atr
02002_points_lead_V3.atr
02002_points_lead_V4.atr
02002_points_lead_V5.atr
02002_points_lead_V6.atr
02003_points_global.atr
02003_points_lead_I.atr
02003_points_lead_II.atr
02003_points_lead_III.atr
02003_points_lead_aVR.atr
02003_points_lead_aVL.atr
02003_points_lead_aVF.atr
02003_points_lead_V1.atr
02003_points_lead_V2.atr
02003_points_lead_V3.atr
02003_points_lead_V4.atr
02003_points_lead_V5.atr
02003_points_lead_V6.atr
02004_points_global.atr
02004_points_lead_I.atr
02004_points_lead_II.atr
02004_points_lead_III.atr
02004_points_lead_aVR.atr
02004_points_lead_aVL.atr
02004_points_lead_aVF.atr
02004_points_lead_V1.atr
02004_points_lead_V2.atr
02004_points_lead_V3.atr
02004_points_lead_V4.atr
02004_points_lead_V5.atr
02004_points_lead_V6.atr
02005_points_global.atr
02005_points_lead_I.atr
02005_points_lead_II.atr
02005_points_lead_III.atr
02005_points_lead_aVR.atr
02005_points_lead_aVL.atr
02005_points_lead_aVF.atr
02005_points_lead_V1.atr
02005_points_lead_V2.atr
02005_points_lead_V3.atr
02005_points_lead_V4.atr
02005_points_lead_V5.atr
02005_points_lead_V6.atr
02006_points_global.atr
02006_points_lead_I.atr
02006_points_lead_II.atr
02006_points_lead_III.atr
02006_points_lead_aVR.atr
02006_points_lead_aVL.atr
02006_points_lead_aVF.atr
02006_points_lead_V1.atr
02006_points_lead_V2.atr
02006_points_lead_V3.atr
02006_points_lead_V4.atr
02006_points_lead_V5.atr
02006_points_lead_V6.atr
02007_points_global.atr
02007_points_lead_I.atr
02007_points_lead_II.atr
02007_points_lead_III.atr
02007_points_lead_aVR.atr
02007_points_lead_aVL.atr
02007_points_lead_aVF.atr
02007_points_lead_V1.atr
02007_points_lead_V2.atr
02007_points_lead_V3.atr
02007_points_lead_V4.atr
02007_points_lead_V5.atr
02007_points_lead_V6.atr
02008_points_global.atr
02008_points_lead_I.atr
02008_points_lead_II.atr
02008_points_lead_III.atr
02008_points_lead_aVR.atr
02008_points_lead_aVL.atr
02008_points_lead_aVF.atr
02008_points_lead_V1.atr
02008_points_lead_V2.atr
02008_points_lead_V3.atr
02008_points_lead_V4.atr
02008_points_lead_V5.atr
02008_points_lead_V6.atr
02009_points_global.atr
02009_points_lead_I.atr
02009_points_lead_II.atr
02009_points_lead_III.atr
02009_points_lead_aVR.atr
02009_points_lead_aVL.atr
02009_points_lead_aVF.atr
02009_points_lead_V1.atr
02009_points_lead_V2.atr
02009_points_lead_V3.atr
02009_points_lead_V4.atr
02009_points_lead_V5.atr
02009_points_lead_V6.atr
```

## Колонки

Посчитано интервальных колонок: 0.

Сознательно не считались 291 колонка из 531: 180 амплитуд (`REQUIRES_RAW_10SEC`) и 111 неизвестных (`P_Morph` 36, `QT_IntCorr` 36, `ST_Elev` 36, `HA__Global` 3). Амплитуды и эти семейства нулями не заполнялись.

240 интервальных колонок (`REQUIRES_FIDUCIALS`) тоже не заполнены: формула есть, входных точек нет.

## Чего этот шаг не сделал

Обучение не запускалось. Benchmark STEP 15 не запускался. PTB-XL не скачивался. Веса и `doctor-opus-global` не менялись. `RAW_TO_531_STATUS` остаётся `NOT_PROVEN`. Коммита нет.
