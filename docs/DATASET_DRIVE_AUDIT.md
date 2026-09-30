# Аудит датасета на Google Drive

Только инвентаризация. Файлы не скачивались, не удалялись и не перемещались. Модели не обучались. Код ансамбля, benchmark и `doctor-opus-global` не менялись.

Живой каталог Drive macOS не отдал на чтение (`Operation not permitted` на `CloudStorage`). Имена, размеры и дерево взяты из локальной базы метаданных DriveFS, без копирования содержимого. Текст заголовков взят только из уже лежащих в локальном кэше Drive небольших `.hea` (8 штук). Полные `.dat` в память не читались.

## 1. Корень

Аккаунт смонтирован как:

```text
/Users/maxmobiles.ru/Google Drive/Мой диск
```

Настоящее содержимое лежит здесь:

```text
/Users/maxmobiles.ru/Google Drive/Мой диск/ptb-xl-a-comprehensive-electrocardiographic-feature-dataset-1.0.1
```

Это имя пакета PhysioNet PTB-XL+ 1.0.1. Внутри только два непустых каталога: `fiducial_points` и `median_beats`. Сумма известных размеров файлов: **347 884 890 байт (~332 МиБ)**, не ~10 ГБ.

Рядом есть пустой каркас официального дерева, без файлов:

```text
/Users/maxmobiles.ru/Google Drive/Мой диск/ptb-xl-plus/physionet.org/files/ptb-xl-plus/1.0.1/
├── features/        пусто
└── median_beats/    пусто
```

По всему Drive нет имён `records500`, `records100`, `*_hr.hea`, `*_hr.dat`, `*_lr.hea`, `ptbxl_database.csv`, `ecgdeli_features.csv`, `scp_statements.csv`.

## 2. Структура без копирования

```text
ptb-xl-a-comprehensive-electrocardiographic-feature-dataset-1.0.1/
├── fiducial_points/
│   └── ecgdeli/
│       ├── 00000/ … 21000/     каталоги тысяч, большинство пустые
│       ├── 02000/   12972 × .atr
│       ├── 03000/   12935 × .atr
│       ├── 04000/   13000 × .atr
│       └── 19000/    1617 × .atr
└── median_beats/
    ├── 12sl/
    │   ├── 00000/   987 .hea + 987 .dat
    │   ├── 01000/  1000 .hea + 999 .dat
    │   ├── 02000/   998 .hea + 998 .dat
    │   ├── 04000/  1000 .hea + 1000 .dat
    │   ├── 06000/  1000 .hea + 1000 .dat
    │   ├── 09000/   997 .hea + 997 .dat, 2 файла с размером 0
    │   ├── 10000/  1000 .hea + 1000 .dat
    │   ├── 16000/   150 .hea + 159 .dat, пар нет, 33 файла с размером 0
    │   ├── 17000/  1000 .hea + 1000 .dat
    │   └── остальные тысячи (03000, 05000, 07000, 08000, 11000–15000, 18000–20000) пустые
    └── unig/
        └── 18000/   24 .hea + 19 .dat, общих id нет
```

Итого по дереву с данными:

| Что | Файлы | Известный размер |
| --- | ---: | ---: |
| `fiducial_points/ecgdeli` | 40 524 `.atr` | 103 339 756 байт |
| `median_beats/12sl` | 8 132 `.hea` + 8 140 `.dat` | 244 315 175 байт |
| `median_beats/unig` | 24 `.hea` + 19 `.dat` | 229 959 байт |

Примеры имён:

```text
median_beats/12sl/00000/00001_medians.hea
median_beats/12sl/00000/00001_medians.dat
median_beats/12sl/00000/00513_medians.hea
median_beats/12sl/00000/00513_medians.dat
median_beats/12sl/16000/16047_medians.hea
fiducial_points/ecgdeli/19000/19421_points_lead_V1.atr
fiducial_points/ecgdeli/19000/19649_points_global.atr
```

35 файлов имеют размер 0 и локальный идентификатор вида `local-…`. Это незавершённые записи синхронизации, в основном в `median_beats/12sl/16000`. Их содержимого нет.

## 3. `*_medians.hea` / `*_medians.dat`

Это не исходные 10-секундные ЭКГ PTB-XL.

Каталог `median_beats/12sl` — median beats GE 12SL. Кэш восьми заголовков из той же папки начинается так:

```text
ge_median_beats_wfdb/16853_medians 12 500 600
```

Одинаково для всех 8 прочитанных заголовков: `16079`, `16130`, `16671`, `16686`, `16853` и ещё трёх с той же первой строкой `12 500 600`.

| Поле | Значение |
| --- | --- |
| Формат WFDB | 32 (float32, не format 16 сырого PTB-XL) |
| Каналы | 12 |
| Частота | 500 Гц |
| Отсчёты | 600 |
| Длительность | 1,2 с |
| Единицы | mV |
| Имена каналов | I, II, III, aVR, aVL, aVF, V1, V2, V3, V4, V5, V6 |
| Размер `.dat` | 28 800 байт = 600 × 12 × 4 |

Сырой `records500` был бы 5 000 отсчётов и около 120 000 байт на format 16. Здесь 600 отсчётов и format 32. В модель `[12, 5000]` этот сигнал не ложится.

Пары 12SL:

| | Число |
| --- | ---: |
| ECG с `.hea` | 8 132 |
| ECG с `.dat` | 8 140 |
| Полная пара `.hea`+`.dat` | 7 981 |
| Только `.hea` | 151 |
| Только `.dat` | 159 |
| Диапазон id по `.hea` | 1 … 17 999 |

`median_beats/unig/18000` — другой набор, 6-значные имена (`018647_medians.dat`, 10 800 байт). Среди 24 заголовков и 19 `.dat` нет ни одной пары с одним и тем же id. Для inference этот кусок не собран.

## 4. Заголовки 16047, 16823, 16843

Сам текст этих трёх `.hea` не прочитан.

| Файл | Путь | Размер в метаданных | Пара `.dat` | Заголовок |
| --- | --- | ---: | --- | --- |
| `16047_medians.hea` | `.../median_beats/12sl/16000/16047_medians.hea` | 1 265 байт, id Drive есть | нет | в локальном кэше нет, каталог Drive не читается |
| `16823_medians.hea` | `.../median_beats/12sl/16000/16823_medians.hea` | 0, id `local-417320` | нет | нет содержимого |
| `16843_medians.hea` | `.../median_beats/12sl/16000/16843_medians.hea` | 0, id `local-417316` | нет | нет содержимого |

Вся корзина `16000` битая: 150 заголовков и 159 `.dat`, пересечение id пустое. `16047`, `16823` и `16843` входят в заголовки без `.dat`.

Формат корзины виден по соседу, который в кэше есть, `16079_medians.hea`:

```text
ge_median_beats_wfdb/16079_medians 12 500 600
```

Дальше 12 строк format 32, единицы mV, порядок I … V6. Полный пример того же вида, `16853`:

```text
ge_median_beats_wfdb/16853_medians 12 500 600
ge_median_beats_wfdb/16853_medians.dat 32 …/mV 32 0 … 0 I
… II, III, aVR, aVL, aVF, V1, V2, V3, V4, V5, V6
```

## 5. Что есть одновременно

| Сущность | На Drive |
| --- | --- |
| Raw ECG `records500` / `*_hr` | нет |
| Median ECG 12SL | да, 7 981 полная пара; корзина 16000 без пар |
| Median ECG Uni-G | обрывок, пар нет |
| Fiducial points ECGDeli | да, 40 524 `.atr`, не во всех тысячах |
| Отдельные файлы признаков ECGDeli | нет |
| `ecgdeli_features.csv` | нет |
| PTB-XL metadata `ptbxl_database.csv` | нет |
| SCP labels отдельным файлом | нет |

Fiducials названы `{ecg_id}_points_lead_{lead}.atr` и `{ecg_id}_points_global.atr`. Уникальных id: 3 691, диапазон 2 000…19 999. Полный набор из 13 файлов (12 отведений + global) есть у 2 991 id. Заполнены только корзины `02000`, `03000`, `04000`, `19000`. `fiducial_points/ecgdeli/16000` существует и пуст.

Вне этой папки, в корне «Мой диск», лежат маленькие CSV одной строки, не таблица на ~21 тысячу записей:

```text
another_ecg_features.csv          10 629 байт
single_ecg_features.csv           10 336 байт
single_ecg_features_REAL.csv      10 486 байт
ecg_predictions.csv            6 421 081 байт
```

Их содержимое не читалось. Это не `ecgdeli_features.csv`.

## 6. Соответствие id 16047

Локальная копия метаданных, не с Drive: `/tmp/ptbxl_database.csv`. Строка:

```text
ecg_id=16047
patient_id=5231.0
filename_lr=records100/16000/16047_lr
filename_hr=records500/16000/16047_hr
scp_codes={'ASMI': 50.0, 'NT_': 0.0, 'LVOLT': 0.0, 'AFIB': 0.0}
```

Файл Drive лежит в `median_beats/12sl/16000/16047_medians.hea`. Тысяча `16000` совпадает с путём PTB-XL для этого id. Соседний заголовок в той же схеме буквально называется `16079_medians`. Соответствие имени файла и `ecg_id` подтверждается. Сам сигнал 16047 на Drive неполный: есть только `.hea`, нет `.dat`, нет fiducials, нет raw, нет 531.

## 7. Связка сущностей

Полная цепочка «raw + median pair + 13 fiducials + 531 CSV» на Drive не собрана ни для одной записи: raw и CSV отсутствуют.

Пересечение полной пары 12SL и хотя бы одного fiducial: **1 998** id. Это не 16047.

Запись `00513` на Drive имеет пару `00000/00513_medians.hea` и `.dat` (1 279 и 28 800 байт). Fiducials для 513 нет: atr начинаются с id 2000. Raw `00513_hr` в этом дереве нет. Это не замена forensic-записи и не вектор 531.

## 8. Цепочка 16047

```text
ecg_id 16047
   в /tmp/ptbxl_database.csv есть
   на Drive metadata нет
      ↓
raw ECG records500/16000/16047_hr
   NOT FOUND
      ↓
median ECG 12sl/16000/16047_medians.hea
   FOUND, 1265 байт
   16047_medians.dat NOT FOUND
      ↓
fiducial points
   NOT FOUND (корзина ecgdeli/16000 пустая, id 16047 среди .atr нет)
      ↓
ECGDeli feature files
   NOT FOUND
      ↓
531-feature vector
   NOT FOUND
```

531 признаки не восстанавливались.

## 9. Можно ли снять benchmark с этих medians

Нет.

Существующий ансамбль ест опубликованные 531 числа, не waveform. `*_medians` этими числами не являются. Докачивать 10 ГБ волн, чтобы подать их в уже обученный ансамбль, не нужно: ему нужен официальный `ecgdeli_features.csv`, а его на Drive нет.

Raw-benchmark ждёт `[12, 5000]` при 500 Гц и 10 с. Эти файлы — median beat `[12, 600]`, 1,2 с, WFDB format 32. Даже полная пара не является входом текущей raw-модели. Для 16047 пары нет.

Скачивание найденных ~332 МиБ не заменяет ни raw-корпус, ни таблицу 531.

```text
DATASET_AUDIT_RESULT

Raw ECG:
NOT FOUND

Median ECG:
FOUND

Fiducial points:
FOUND

ECGDeli features:
NOT FOUND

PTB-XL metadata:
NOT FOUND

531 feature CSV:
NOT FOUND

ECG ID correspondence:
CONFIRMED

Raw ECG usable for inference:
NO

Full 10 GB download required:
NO

Training required for current 531 ensemble:
NO
```
