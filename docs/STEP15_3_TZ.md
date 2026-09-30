# STEP 15.3 — ИНТЕРВАЛЫ ИЗ УЖЕ ЛЕЖАЩИХ FIDUCIALS

Без обучения. Без GPU. Без скачивания PTB-XL. Без ансамбля.

Этот шаг написан по результатам STEP 15, 15.1, аудита Google Drive и STEP 15.2. Он не возвращает проект к идее «median beat → 531 → сеть».

## 0. Что проверки уже установили

Эти факты не переоткрывать и не оспаривать новым кодом.

```text
RAW_TO_531_STATUS = NOT_PROVEN
FULL_531_VECTOR_AVAILABLE = NO
ENSEMBLE_INFERENCE_ON_INCOMPLETE_VECTOR = ЗАПРЕЩЕНО
```

На Google Drive нет:

```text
records500 / *_hr.hea / *_hr.dat
ptbxl_database.csv
ecgdeli_features.csv
```

12SL median beat — это не raw ECG:

```text
12 отведений
500 Гц
600 отсчётов
1.2 с
WFDB format 32
mV
порядок I II III aVR aVL aVF V1 V2 V3 V4 V5 V6
```

Полных пар 12SL: 7979. Размер `.dat` у них 28800 байт.

Fiducials PTB-XL+ лежат отдельно. Полный набор из 13 файлов есть у 2991 id. Одновременно полная пара 12SL и 13 fiducials есть у 1996 id. Первые десять: 2000–2009.

Интервальные 240 колонок считаются из номеров отсчётов в `.atr`, не из median waveform. У записи 00513 того же издателя точки доходят до отсчёта 5000. В median beat таких позиций нет. Индекс fiducial в median beat не подставлять.

Граница 531, уже посчитанная:

| Статус | Колонок | Семейства |
| --- | ---: | --- |
| REQUIRES_FIDUCIALS | 240 | PQ, PR, QRS, QT, P/T duration, RR, Framingham |
| REQUIRES_RAW_10SEC | 180 | P/Q/R/S/T амплитуды |
| UNKNOWN | 111 | P_Morph 36, QT_IntCorr 36, ST_Elev 36, HA__Global 3 |

`000513_medians.*` и `005000_medians.*` — другая семья файлов (`.dat` 10800 байт). Это не пара 12SL и не вход этого шага.

## 1. Цель

Прочитать уже лежащие fiducial `.atr` для id 2000–2009 и посчитать только 240 интервальных колонок существующей формулой `ExtractIntervalFeaturesFromFPT`.

Показать, что расчёт на этих десяти записях либо проходит, либо упирается в запрет чтения файлов. Не доказывать официальное совпадение с PTB-XL+: таблицы `ecgdeli_features.csv` на диске нет.

## 2. Запрещено

```text
обучать RawECGCNN и любые другие модели
запускать benchmark STEP 15
скачивать PTB-XL или любые 10+ GB
читать все median .dat
менять doctor-opus-global
менять веса и inference существующего ансамбля
передавать вектор в MLP, 1D CNN или ResNet1D
подставлять 0, среднее, медиану или случайное число вместо неизвестного признака
считать амплитуды, P_Morph, QT_IntCorr, ST_Elev, HA__Global
переставлять отведения aVF/aVL
объявлять RAW_TO_531_STATUS = PROVEN
делать commit
```

Наблюдение про обмен aVF/aVL относится только к forensic-записи 00513. На id 2000–2009 имена файлов не менять и отведения не переставлять.

## 3. Вход

Только эти десять id: 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009.

Для каждого id нужны 13 файлов:

```text
{id5}_points_global.atr
{id5}_points_lead_I.atr
{id5}_points_lead_II.atr
{id5}_points_lead_III.atr
{id5}_points_lead_aVR.atr
{id5}_points_lead_aVL.atr
{id5}_points_lead_aVF.atr
{id5}_points_lead_V1.atr
{id5}_points_lead_V2.atr
{id5}_points_lead_V3.atr
{id5}_points_lead_V4.atr
{id5}_points_lead_V5.atr
{id5}_points_lead_V6.atr
```

`{id5}` — пять цифр, как в PTB-XL: `02000`, не `2000`.

Корень:

```text
/Users/maxmobiles.ru/Google Drive/Мой диск/ptb-xl-a-comprehensive-electrocardiographic-feature-dataset-1.0.1/fiducial_points/ecgdeli/
```

Корзина id 2000–2009: `02000/`.

Median `.hea` и `.dat` для расчёта не читать. Они уже описаны в STEP 15.2 и в формулу интервала не входят.

## 4. Если файл не читается

macOS уже возвращал `Operation not permitted` на чтение Google Drive.

Если хотя бы один из 13 × 10 файлов не открывается:

```text
не обходить запрет скачиванием
не подставлять точки записи 00513
не выдумывать номера отсчётов
записать, какой путь не открылся
закончить со статусом BLOCKED_BY_OS_READ
```

Метаданные Drive (имя и размер) содержимым `.atr` не являются.

## 5. Разбор одной аннотации

Использовать уже существующий разбор WFDB annotation из `experiments/raw_to_531/reconstruct_from_fiducials.py`: функция `parse_atr` и список полей `FIELDS`.

Новый медицинский смысл полей не вводить.

В каждом файле должно быть ровно одно примечание:

```text
## time resolution: 500
```

Если его нет или оно не одно — запись пропускается с явной ошибкой, расчёт по ней не публикуется.

Ожидаемые подписи точек:

```text
p-wave onset
p-wave peak
p-wave offset
QRS onset
Q peak
R peak
S peak
QRS offset
L point (for STEMI)
t-wave onset
t-wave peak
t-wave offset
```

`L point (for STEMI)` только фиксируется как присутствующая точка. В ST amplitude она не превращается.

Для каждого id записать:

```text
число комплексов
минимальный и максимальный номер отсчёта
есть ли номер отсчёта > 599
```

Если максимум больше 599, в отчёте прямо написать: эти координаты не являются индексами median beat из 600 отсчётов.

## 6. Какие колонки считать

Только 240 колонок со статусом `REQUIRES_FIDUCIALS` из `docs/step15_2_feature_coverage.csv`.

Формулы комплексов не менять. Они уже зафиксированы:

| Колонка | Конец | Начало |
| --- | --- | --- |
| P_DurFull | p-wave offset | p-wave onset |
| T_DurFull | t-wave offset | t-wave onset |
| PQ_Int | QRS onset | p-wave onset |
| PR_Int | R peak | p-wave onset |
| QRS_Dur | QRS offset | QRS onset |
| QT_Int | t-wave offset | QRS onset |

Разность отсчётов умножается на 2, как в `ExtractIntervalFeaturesFromFPT`.

`P_Dur` и `T_Dur`, а также Global-версии PQ, PR, QRS, QT, P_Dur и T_Dur — правило второй крайней границы из того же модуля. Max по отведениям вместо этого правила не использовать.

`RR_Mean_Global` — последовательные R пики global-файла.

`QT_IntFramingham_Global` — Framingham по комплексному QT и этому RR, затем медиана, IQR и count тем же способом, что уже есть в коде агрегации.

Не считать:

```text
P_Amp Q_Amp R_Amp S_Amp T_Amp
P_Morph
QT_IntCorr
ST_Elev
HA__Global
```

В выходной таблице этих колонок нет. Пустых 531-векторов нет.

## 7. Выход

Не перезаписывать результаты STEP 13–15.2.

Создать:

```text
benchmark/results/step15_3/interval_features.csv
benchmark/results/step15_3/fiducial_span.csv
docs/STEP15_3_INTERVALS.md
```

`interval_features.csv`, одна строка на id:

```text
ecg_id
затем 240 интервальных колонок в порядке canonical schema
```

Порядок колонок брать из `ecg_engine.feature_columns.FEATURE_COLUMNS`, оставляя только семейства из раздела 6. Сортировку имён не делать.

`fiducial_span.csv`:

```text
ecg_id
n_beats
sample_min
sample_max
exceeds_median_length
atr_files_read
```

`exceeds_median_length` равен true, если `sample_max > 599`.

В markdown-отчёте:

1. Сколько файлов открыто.
2. Сколько id посчитано.
3. Диапазон номеров отсчётов.
4. Являются ли эти номера индексами median beat.
5. Какие 240 колонок посчитаны.
6. Какие 291 колонка сознательно не считались.
7. Ансамбль не вызывался.
8. Официальная строка PTB-XL+ для сравнения отсутствует.

Если чтение блокировано, `interval_features.csv` не создавать. В отчёте статус `BLOCKED_BY_OS_READ` и список непрочитанных путей.

## 8. Чего этот шаг не делает

Он не оценивает диагностическое качество сети.

Он не отвечает, лучше ли raw-модель ансамбля 531.

Он не восстанавливает официальные 531 признака.

Совпадение формулы с ECGDeli на записи 00513 остаётся прежним forensic-результатом. На id 2000–2009 published row для сверки нет, поэтому слова «exact», «официальное значение» и «признак PTB-XL+» к новым числам не применять. Это расчёт по опубликованным точкам и уже принятой формуле.

## 9. Приёмка

Шаг принят, если выполняется одно из двух.

### A. Расчёт прошёл

```text
10 id
13 atr на каждый id
240 колонок на каждый id
нет амплитуд и UNKNOWN-семейств
нет вызова ансамбля
sample span записан
RAW_TO_531_STATUS остаётся NOT_PROVEN
doctor-opus-global не изменён
```

### B. Чтение закрыто

```text
BLOCKED_BY_OS_READ
числа признаков не выдуманы
ансамбль не вызывался
скачивания нет
```

Оба исхода технически честные. Выдуманная таблица интервалов приёмкой не является.

## 10. Отчёт

После выполнения вернуть только это и остановиться. Следующий шаг не начинать.

```text
STEP 15.3 RESULT

Status:
CALCULATED / BLOCKED_BY_OS_READ

ECG ids:
<список>

ATR files read:
<N> / 130

Interval columns:
<N>

Amplitude columns filled:
0

Unknown families filled:
0

Ensemble called:
NO

Sample max:
<число или NOT_READ>

Exceeds median length 599:
YES / NO / NOT_READ

Official 531 row compared:
NO

RAW_TO_531_STATUS:
NOT_PROVEN

doctor-opus-global:
UNCHANGED

Git commit:
NO
```
