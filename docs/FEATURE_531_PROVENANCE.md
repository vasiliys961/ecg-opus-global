# Происхождение 531 признаков

Дата доступа к публичным источникам: 2026-09-28.

Вердикт по вопросу «можно ли сейчас превратить новый raw 12-lead в точно эти 531 числа»:

```text
PARTIALLY PROVEN
```

Идентичность таблицы доказана. Повторный запуск экстрактора на raw не делался, поэтому

```text
RAW_TO_531_STATUS = NOT_PROVEN
```

Экстрактор в этот репозиторий не добавлялся.

## PRIMARY SOURCE

Это сведения, которые проверены по файлу, коммиту или странице источника. Они не выведены из похожести имён.

### Обучающий контракт в `ecg_web_up`

Репозиторий: https://github.com/vasiliys961/ecg_web_up

Полная история на 2026-09-28 — 10 коммитов, с `65ea3503111f514a2bc293732cae314bf3ed76e6` (2025-07-29, «Initial commit: Flask ECG Analyzer») по `bfe7c1738baca97f9f501ede25f1716f2aa94cf6` (2026-09-25, «Add README describing the ECG ensemble and CSV input»).

В истории нет удалённых файлов. Нет notebooks, training scripts, preprocessing scripts и кода экстрактора. Файл `templates/ЭКГ.` пустой. `requirements.txt` содержит Flask, torch, pandas, numpy, scikit-learn и gunicorn. Пакетов ECGDeli, WFDB, NeuroKit и MATLAB там нет. `scikit-learn` в инференсе не вызывается.

Уже первый коммит содержит веса, `ecg_train_mean.npy`, `ecg_train_std.npy` и `templates/another_ecg_features.csv`. README, добавленный последним коммитом, называет формат «ecgdeli». Страница загрузки пишет `ecgdeli_features`. Это имя файла, не версия программы.

### Публичная таблица, с которой совпал наш CSV

Проект: PTB-XL+, a comprehensive electrocardiographic feature dataset, версия 1.0.1.

- Страница: https://physionet.org/content/ptb-xl-plus/1.0.1/
- DOI: https://doi.org/10.13026/nqsf-pc74
- Статья: Strodthoff et al., Scientific Data, 13 May 2023, https://doi.org/10.1038/s41597-023-02153-8
- Файл: https://physionet.org/files/ptb-xl-plus/1.0.1/features/ecgdeli_features.csv
- Заявленный SHA-256 в `SHA256SUMS.txt` той же версии: `84143735682f727201cc7f2825c047f98898f9756c6a21729af993b516221556`
- Размер по HTTP: 62 235 868 байт. Дата файла на сервере: 2023-02-28.
- Словарь колонок: https://physionet.org/files/ptb-xl-plus/1.0.1/features/feature_description.csv
- Лицензия файлов: Creative Commons Attribution 4.0 International, https://physionet.org/content/ptb-xl-plus/view-license/1.0.1/

Заголовок `ecgdeli_features.csv` совпал с заголовком `tests/fixtures/another_ecg_features.csv`: 532 имени, тот же порядок, включая `ecg_id`. Строка `ecg_id=513` совпала по всем 532 ячейкам. Максимальная абсолютная разница 0, средняя 0. Это не пересчёт из сигнала. Это сравнение двух CSV.

В `features/old/ecgdeli_features.csv` другой SHA-256 (`1f84f6a7b6e83045bbb8417edd03b85415dfca7743171a0a9ab0a7ffd510371c`). Release notes v1.0.1 говорят только о расширении списка авторов и описания. Старый файл с нашим CSV не сравнивался.

### Чем посчитаны числа, по словам авторов датасета

Статья и страница PhysioNet говорят одно и то же: признаки ECGDeli посчитаны публичной версией 1.1, отдельно на каждый комплекс. В таблицу попали медиана по комплексам, межквартильный размах (0.25, 0.75) и число комплексов, по которым значение получено. Единицы после гармонизации: милливольты и миллисекунды. Имена колонок — общая схема PTB-XL+, не внутренние имена MATLAB.

Код тулбокса:

- https://github.com/KIT-IBT/ECGdeli
- Тег `v1.1`, commit `3c13b1b2ff55152360f3cee992c1d1d66099aa14`, дата коммита 2022-10-12, сообщение «Add P-wave morphology estimator».
- Архив, на который ссылается статья: Pilia et al., Zenodo, https://doi.org/10.5281/zenodo.7191379 . В статье это «version 1.1» (2020). Побайтовое равенство этого архива и git-тега `v1.1` от 2022-10-12 здесь не проверялось: Zenodo на запрос API ответил 403.
- Лицензия клонированного репозитория: GNU GPL 3.0.
- Статья о тулбоксе: Pilia et al., SoftwareX 13:100639 (2021), https://doi.org/10.1016/j.softx.2020.100639

Функции тега `v1.1`, которые относятся к признакам:

- `ECG_Processing/ExtractIntervalFeaturesFromFPT.m` — по каждому комплексу и отведению: длительность P, QRS, T, интервалы PQ, PR, QT, RR. Синхронные по 12 отведениям величины считаются как разность второй самой поздней и второй самой ранней границы. QTc в синхронной ветке — Framingham: `QT + 154 * (1 - RR/1000)` при QT и RR в миллисекундах. Код умножает разности отсчётов на 2, то есть предполагает шаг 2 мс, частоту 500 Гц.
- `ECG_Processing/ExtractAmplitudeFeaturesFromFPT.m` — амплитуды P, Q, R, S, T по комплексам. Это не готовые 531 колонка.
- `ECG_Processing/Get_P_Morphology.m` — морфология P. В заголовке файла есть предупреждение, что код не проверен на широком наборе сигналов.

Эти функции не пишут CSV с медианой, IQR и count. Агрегацию сделали авторы PTB-XL+. Код этой агрегации статья относит к Zenodo https://doi.org/10.5281/zenodo.7817567 . Этот архив здесь не скачивался.

### Парный raw для строки 513

PTB-XL 1.0.3, https://physionet.org/content/ptb-xl/1.0.3/ , DOI https://doi.org/10.13026/kfzx-aw45 , лицензия CC BY 4.0.

Заголовок записи 513 существует в двух частотах:

- https://physionet.org/files/ptb-xl/1.0.3/records500/00000/00513_hr.hea — 12 отведений, 500 Гц, 5000 отсчётов, 10 с, масштаб `1000 ADC/mV`.
- https://physionet.org/files/ptb-xl/1.0.3/records100/00000/00513_lr.hea — те же 12 отведений, 100 Гц, 1000 отсчётов, 10 с.

Порядок отведений в WFDB: I, II, III, aVR, aVL, aVF, V1–V6. Порядок в 531 колонках другой: I, II, III, V1–V6, aVF, aVL, aVR, затем Global. Сам сигнал `.dat` не скачивался и в экстрактор не подавался.

## SECONDARY / INFERRED INFORMATION

Это не доказано сверкой «raw → программа → CSV».

- Какая из двух частот PTB-XL подавалась в ECGDeli, в статье не названа. Множитель 2 в `ExtractIntervalFeaturesFromFPT.m` согласован с 500 Гц, но это свойство функции, а не журнал того запуска, которым собрали PTB-XL+.
- Колонка без суффикса — медиана по комплексам, `_iqr` — один межквартильный размах, `_count` — число комплексов. Так написано в статье и на странице PhysioNet. Метод процентиля (линейная интерполяция или иной) в скачанном коде не зафиксирован.
- `QT_IntCorr_*` словарь описывает как коррекцию Framingham по отведению. `QT_IntFramingham_Global` — та же формула для глобального QT. На строке 513 формула Framingham от уже сохранённых медиан не равна сохранённому числу: QT Global 499 мс и RR 862 мс дают 520.252, в ячейке 522.01. Bazett от тех же медиан даёт 537.46. Значит, коррекция не применялась к паре медиан. Согласуется с порядком «сначала QTc каждого комплекса, потом медиана», но этот порядок на raw не пересчитан.
- `HA__Global` в словаре: целочисленная ось, 1 — левое отклонение, 2 — горизонтальная, 3 — нормальная, 4 — вертикальная, 5 — правая, 6 — крайняя правая. Два подчёркивания стоят в официальном имени колонки. На строке 513 значение 2, IQR 0, count 1.
- `P_Morph` в словаре: −3…3 для KIT, для Glasgow и GE диапазон уже. Наш столбец относится к ветке ECGDeli.
- Внутренние имена ECGDeli из словаря (`PQi_X`, `PWa_X`, `QTci_X`, `elHA` и остальные) — карта имён, не лог вызова.
- Фильтр, isoline и точные аргументы `Annotate_ECG_Multi`, которыми пользовались авторы PTB-XL+, в просмотренных страницах не указаны.
- Совпадение одной строки и схемы не доказывает, что `ecg_train_mean.npy` посчитан по всей таблице PTB-XL+. Полный файл с сервера имеет длину 62 235 868 байт и SHA-256 `84143735682f727201cc7f2825c047f98898f9756c6a21729af993b516221556`. Локальная копия после докачки получилась длиной 62 534 876 байт и с другим SHA-256, поэтому к сравнению `mean/std` она не использовалась. Сверка заголовка и строки 513 сделана раньше, на непрерывном начале того же ответа сервера.
- README `ecg_web_up` сам по себе источником не считается. Он совпал с файлом, который уже лежал в первом коммите.

## Что искалось и не нашлось в `ecg_web_up`

Marquette 12SL и Glasgow Uni-G в истории репозитория не упомянуты. В PTB-XL+ это другие таблицы: `12sl_features.csv` и `unig_features.csv`. У признаков, которые есть только у ECGDeli (`PQ_Int`, `QT_IntCorr`, `ST_Elev`, `HA__Global`), колонки Uni-G и 12SL в `feature_description.csv` пустые. Наш заголовок совпал с `ecgdeli_features.csv`, не с этими двумя файлами.

61 колонка в `templates/ECG.csv` и `templates/sample_ecg_features.csv` — границы зубцов, не 531 признак.

## Структура 531

Она посчитана по официальному заголовку, который совпал с `ecg_engine/feature_columns.py`. Не из README.

19 семейств. У каждого признака три статистики: значение, `_iqr`, `_count`. Четыре семейства идут по 13 осям (12 отведений и Global) и дают 39 колонок. Десять семейств идут только по 12 отведениям и дают 36 колонок. Пять семейств только Global и дают 3 колонки.

`4×39 + 10×36 + 5×3 = 531`.

Порядок отведений внутри семейства: I, II, III, V1, V2, V3, V4, V5, V6, aVF, aVL, aVR, и Global, если он у семейства есть. Исключение в написании: `HA__Global`, не `HA_Global`.

| family | columns | leads | declared unit of value and IQR | ECGDeli name in feature_description |
| --- | ---: | --- | --- | --- |
| PQ_Int | 39 | 12 + Global | ms | PQi |
| PR_Int | 39 | 12 + Global | ms | PRi |
| QRS_Dur | 39 | 12 + Global | ms | QRSd |
| QT_Int | 39 | 12 + Global | ms | QTi |
| P_Amp | 36 | 12 | mV | PWa |
| P_DurFull | 36 | 12 | ms | PWd |
| P_Morph | 36 | 12 | integer | PWm |
| Q_Amp | 36 | 12 | mV | QPa |
| QT_IntCorr | 36 | 12 | ms | QTci |
| R_Amp | 36 | 12 | mV | RPa |
| S_Amp | 36 | 12 | mV | SPa |
| ST_Elev | 36 | 12 | mV | STc |
| T_Amp | 36 | 12 | mV | TWa |
| T_DurFull | 36 | 12 | ms | TWd |
| P_Dur | 3 | Global | ms | PWd_max |
| QT_IntFramingham | 3 | Global | ms | QTci_max |
| RR_Mean | 3 | Global | ms | RRi_max |
| T_Dur | 3 | Global | ms | TWd_max |
| HA | 3 | Global | integer | elHA |

`_count` — число комплексов, безразмерное. Единица IQR заявлена той же, что у значения.

## Сверка чисел

Кандидат-экстрактор на raw не запускался. Сравнивались готовые таблицы.

| сравнение | max abs | mean abs | совпало ячеек |
| --- | ---: | ---: | ---: |
| заголовки, 532 имени | 0 различий порядка | — | 532/532 |
| строка ecg_id 513, все ячейки | 0 | 0 | 532/532 |

Порог «существенного» расхождения не понадобился: расхождений нет.

Не проверено этим тестом: частота дискретизации, полярность, фильтр, baseline, длина записи, обработка NaN при обучении, формула процентиля. Сеть на новом векторе не запускалась.

## Карта колонок

Индекс 0 — первая колонка после `ecg_id`. `source` для всех строк: PTB-XL+ 1.0.1 `ecgdeli_features.csv`. `confidence`: идентичность колонки доказана совпадением заголовка; единица и смысл статистики заявлены датасетом и из raw заново не пересчитаны.

Полная таблица ниже сгенерирована из `ecg_engine/feature_columns.py` и `feature_description.csv`.

| index | feature_name | family | value/IQR/count | unit | lead dependence | source | confidence |
| ----: | --- | --- | --- | --- | --- | --- | --- |
| 0 | PQ_Int_I | PQ_Int | value | ms | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 1 | PQ_Int_I_iqr | PQ_Int | iqr | ms | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 2 | PQ_Int_I_count | PQ_Int | count | count | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 3 | PQ_Int_II | PQ_Int | value | ms | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 4 | PQ_Int_II_iqr | PQ_Int | iqr | ms | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 5 | PQ_Int_II_count | PQ_Int | count | count | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 6 | PQ_Int_III | PQ_Int | value | ms | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 7 | PQ_Int_III_iqr | PQ_Int | iqr | ms | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 8 | PQ_Int_III_count | PQ_Int | count | count | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 9 | PQ_Int_V1 | PQ_Int | value | ms | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 10 | PQ_Int_V1_iqr | PQ_Int | iqr | ms | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 11 | PQ_Int_V1_count | PQ_Int | count | count | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 12 | PQ_Int_V2 | PQ_Int | value | ms | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 13 | PQ_Int_V2_iqr | PQ_Int | iqr | ms | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 14 | PQ_Int_V2_count | PQ_Int | count | count | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 15 | PQ_Int_V3 | PQ_Int | value | ms | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 16 | PQ_Int_V3_iqr | PQ_Int | iqr | ms | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 17 | PQ_Int_V3_count | PQ_Int | count | count | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 18 | PQ_Int_V4 | PQ_Int | value | ms | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 19 | PQ_Int_V4_iqr | PQ_Int | iqr | ms | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 20 | PQ_Int_V4_count | PQ_Int | count | count | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 21 | PQ_Int_V5 | PQ_Int | value | ms | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 22 | PQ_Int_V5_iqr | PQ_Int | iqr | ms | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 23 | PQ_Int_V5_count | PQ_Int | count | count | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 24 | PQ_Int_V6 | PQ_Int | value | ms | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 25 | PQ_Int_V6_iqr | PQ_Int | iqr | ms | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 26 | PQ_Int_V6_count | PQ_Int | count | count | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 27 | PQ_Int_aVF | PQ_Int | value | ms | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 28 | PQ_Int_aVF_iqr | PQ_Int | iqr | ms | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 29 | PQ_Int_aVF_count | PQ_Int | count | count | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 30 | PQ_Int_aVL | PQ_Int | value | ms | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 31 | PQ_Int_aVL_iqr | PQ_Int | iqr | ms | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 32 | PQ_Int_aVL_count | PQ_Int | count | count | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 33 | PQ_Int_aVR | PQ_Int | value | ms | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 34 | PQ_Int_aVR_iqr | PQ_Int | iqr | ms | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 35 | PQ_Int_aVR_count | PQ_Int | count | count | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 36 | PQ_Int_Global | PQ_Int | value | ms | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 37 | PQ_Int_Global_iqr | PQ_Int | iqr | ms | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 38 | PQ_Int_Global_count | PQ_Int | count | count | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 39 | PR_Int_I | PR_Int | value | ms | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 40 | PR_Int_I_iqr | PR_Int | iqr | ms | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 41 | PR_Int_I_count | PR_Int | count | count | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 42 | PR_Int_II | PR_Int | value | ms | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 43 | PR_Int_II_iqr | PR_Int | iqr | ms | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 44 | PR_Int_II_count | PR_Int | count | count | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 45 | PR_Int_III | PR_Int | value | ms | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 46 | PR_Int_III_iqr | PR_Int | iqr | ms | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 47 | PR_Int_III_count | PR_Int | count | count | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 48 | PR_Int_V1 | PR_Int | value | ms | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 49 | PR_Int_V1_iqr | PR_Int | iqr | ms | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 50 | PR_Int_V1_count | PR_Int | count | count | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 51 | PR_Int_V2 | PR_Int | value | ms | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 52 | PR_Int_V2_iqr | PR_Int | iqr | ms | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 53 | PR_Int_V2_count | PR_Int | count | count | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 54 | PR_Int_V3 | PR_Int | value | ms | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 55 | PR_Int_V3_iqr | PR_Int | iqr | ms | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 56 | PR_Int_V3_count | PR_Int | count | count | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 57 | PR_Int_V4 | PR_Int | value | ms | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 58 | PR_Int_V4_iqr | PR_Int | iqr | ms | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 59 | PR_Int_V4_count | PR_Int | count | count | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 60 | PR_Int_V5 | PR_Int | value | ms | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 61 | PR_Int_V5_iqr | PR_Int | iqr | ms | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 62 | PR_Int_V5_count | PR_Int | count | count | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 63 | PR_Int_V6 | PR_Int | value | ms | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 64 | PR_Int_V6_iqr | PR_Int | iqr | ms | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 65 | PR_Int_V6_count | PR_Int | count | count | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 66 | PR_Int_aVF | PR_Int | value | ms | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 67 | PR_Int_aVF_iqr | PR_Int | iqr | ms | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 68 | PR_Int_aVF_count | PR_Int | count | count | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 69 | PR_Int_aVL | PR_Int | value | ms | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 70 | PR_Int_aVL_iqr | PR_Int | iqr | ms | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 71 | PR_Int_aVL_count | PR_Int | count | count | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 72 | PR_Int_aVR | PR_Int | value | ms | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 73 | PR_Int_aVR_iqr | PR_Int | iqr | ms | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 74 | PR_Int_aVR_count | PR_Int | count | count | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 75 | PR_Int_Global | PR_Int | value | ms | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 76 | PR_Int_Global_iqr | PR_Int | iqr | ms | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 77 | PR_Int_Global_count | PR_Int | count | count | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 78 | P_Amp_I | P_Amp | value | mV | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 79 | P_Amp_I_iqr | P_Amp | iqr | mV | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 80 | P_Amp_I_count | P_Amp | count | count | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 81 | P_Amp_II | P_Amp | value | mV | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 82 | P_Amp_II_iqr | P_Amp | iqr | mV | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 83 | P_Amp_II_count | P_Amp | count | count | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 84 | P_Amp_III | P_Amp | value | mV | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 85 | P_Amp_III_iqr | P_Amp | iqr | mV | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 86 | P_Amp_III_count | P_Amp | count | count | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 87 | P_Amp_V1 | P_Amp | value | mV | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 88 | P_Amp_V1_iqr | P_Amp | iqr | mV | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 89 | P_Amp_V1_count | P_Amp | count | count | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 90 | P_Amp_V2 | P_Amp | value | mV | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 91 | P_Amp_V2_iqr | P_Amp | iqr | mV | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 92 | P_Amp_V2_count | P_Amp | count | count | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 93 | P_Amp_V3 | P_Amp | value | mV | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 94 | P_Amp_V3_iqr | P_Amp | iqr | mV | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 95 | P_Amp_V3_count | P_Amp | count | count | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 96 | P_Amp_V4 | P_Amp | value | mV | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 97 | P_Amp_V4_iqr | P_Amp | iqr | mV | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 98 | P_Amp_V4_count | P_Amp | count | count | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 99 | P_Amp_V5 | P_Amp | value | mV | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 100 | P_Amp_V5_iqr | P_Amp | iqr | mV | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 101 | P_Amp_V5_count | P_Amp | count | count | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 102 | P_Amp_V6 | P_Amp | value | mV | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 103 | P_Amp_V6_iqr | P_Amp | iqr | mV | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 104 | P_Amp_V6_count | P_Amp | count | count | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 105 | P_Amp_aVF | P_Amp | value | mV | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 106 | P_Amp_aVF_iqr | P_Amp | iqr | mV | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 107 | P_Amp_aVF_count | P_Amp | count | count | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 108 | P_Amp_aVL | P_Amp | value | mV | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 109 | P_Amp_aVL_iqr | P_Amp | iqr | mV | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 110 | P_Amp_aVL_count | P_Amp | count | count | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 111 | P_Amp_aVR | P_Amp | value | mV | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 112 | P_Amp_aVR_iqr | P_Amp | iqr | mV | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 113 | P_Amp_aVR_count | P_Amp | count | count | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 114 | P_DurFull_I | P_DurFull | value | ms | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 115 | P_DurFull_I_iqr | P_DurFull | iqr | ms | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 116 | P_DurFull_I_count | P_DurFull | count | count | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 117 | P_DurFull_II | P_DurFull | value | ms | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 118 | P_DurFull_II_iqr | P_DurFull | iqr | ms | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 119 | P_DurFull_II_count | P_DurFull | count | count | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 120 | P_DurFull_III | P_DurFull | value | ms | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 121 | P_DurFull_III_iqr | P_DurFull | iqr | ms | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 122 | P_DurFull_III_count | P_DurFull | count | count | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 123 | P_DurFull_V1 | P_DurFull | value | ms | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 124 | P_DurFull_V1_iqr | P_DurFull | iqr | ms | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 125 | P_DurFull_V1_count | P_DurFull | count | count | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 126 | P_DurFull_V2 | P_DurFull | value | ms | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 127 | P_DurFull_V2_iqr | P_DurFull | iqr | ms | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 128 | P_DurFull_V2_count | P_DurFull | count | count | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 129 | P_DurFull_V3 | P_DurFull | value | ms | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 130 | P_DurFull_V3_iqr | P_DurFull | iqr | ms | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 131 | P_DurFull_V3_count | P_DurFull | count | count | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 132 | P_DurFull_V4 | P_DurFull | value | ms | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 133 | P_DurFull_V4_iqr | P_DurFull | iqr | ms | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 134 | P_DurFull_V4_count | P_DurFull | count | count | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 135 | P_DurFull_V5 | P_DurFull | value | ms | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 136 | P_DurFull_V5_iqr | P_DurFull | iqr | ms | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 137 | P_DurFull_V5_count | P_DurFull | count | count | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 138 | P_DurFull_V6 | P_DurFull | value | ms | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 139 | P_DurFull_V6_iqr | P_DurFull | iqr | ms | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 140 | P_DurFull_V6_count | P_DurFull | count | count | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 141 | P_DurFull_aVF | P_DurFull | value | ms | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 142 | P_DurFull_aVF_iqr | P_DurFull | iqr | ms | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 143 | P_DurFull_aVF_count | P_DurFull | count | count | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 144 | P_DurFull_aVL | P_DurFull | value | ms | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 145 | P_DurFull_aVL_iqr | P_DurFull | iqr | ms | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 146 | P_DurFull_aVL_count | P_DurFull | count | count | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 147 | P_DurFull_aVR | P_DurFull | value | ms | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 148 | P_DurFull_aVR_iqr | P_DurFull | iqr | ms | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 149 | P_DurFull_aVR_count | P_DurFull | count | count | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 150 | P_Dur_Global | P_Dur | value | ms | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 151 | P_Dur_Global_iqr | P_Dur | iqr | ms | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 152 | P_Dur_Global_count | P_Dur | count | count | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 153 | P_Morph_I | P_Morph | value | integer | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 154 | P_Morph_I_iqr | P_Morph | iqr | integer | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 155 | P_Morph_I_count | P_Morph | count | count | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 156 | P_Morph_II | P_Morph | value | integer | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 157 | P_Morph_II_iqr | P_Morph | iqr | integer | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 158 | P_Morph_II_count | P_Morph | count | count | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 159 | P_Morph_III | P_Morph | value | integer | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 160 | P_Morph_III_iqr | P_Morph | iqr | integer | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 161 | P_Morph_III_count | P_Morph | count | count | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 162 | P_Morph_V1 | P_Morph | value | integer | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 163 | P_Morph_V1_iqr | P_Morph | iqr | integer | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 164 | P_Morph_V1_count | P_Morph | count | count | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 165 | P_Morph_V2 | P_Morph | value | integer | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 166 | P_Morph_V2_iqr | P_Morph | iqr | integer | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 167 | P_Morph_V2_count | P_Morph | count | count | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 168 | P_Morph_V3 | P_Morph | value | integer | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 169 | P_Morph_V3_iqr | P_Morph | iqr | integer | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 170 | P_Morph_V3_count | P_Morph | count | count | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 171 | P_Morph_V4 | P_Morph | value | integer | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 172 | P_Morph_V4_iqr | P_Morph | iqr | integer | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 173 | P_Morph_V4_count | P_Morph | count | count | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 174 | P_Morph_V5 | P_Morph | value | integer | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 175 | P_Morph_V5_iqr | P_Morph | iqr | integer | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 176 | P_Morph_V5_count | P_Morph | count | count | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 177 | P_Morph_V6 | P_Morph | value | integer | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 178 | P_Morph_V6_iqr | P_Morph | iqr | integer | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 179 | P_Morph_V6_count | P_Morph | count | count | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 180 | P_Morph_aVF | P_Morph | value | integer | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 181 | P_Morph_aVF_iqr | P_Morph | iqr | integer | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 182 | P_Morph_aVF_count | P_Morph | count | count | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 183 | P_Morph_aVL | P_Morph | value | integer | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 184 | P_Morph_aVL_iqr | P_Morph | iqr | integer | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 185 | P_Morph_aVL_count | P_Morph | count | count | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 186 | P_Morph_aVR | P_Morph | value | integer | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 187 | P_Morph_aVR_iqr | P_Morph | iqr | integer | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 188 | P_Morph_aVR_count | P_Morph | count | count | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 189 | Q_Amp_I | Q_Amp | value | mV | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 190 | Q_Amp_I_iqr | Q_Amp | iqr | mV | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 191 | Q_Amp_I_count | Q_Amp | count | count | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 192 | Q_Amp_II | Q_Amp | value | mV | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 193 | Q_Amp_II_iqr | Q_Amp | iqr | mV | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 194 | Q_Amp_II_count | Q_Amp | count | count | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 195 | Q_Amp_III | Q_Amp | value | mV | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 196 | Q_Amp_III_iqr | Q_Amp | iqr | mV | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 197 | Q_Amp_III_count | Q_Amp | count | count | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 198 | Q_Amp_V1 | Q_Amp | value | mV | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 199 | Q_Amp_V1_iqr | Q_Amp | iqr | mV | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 200 | Q_Amp_V1_count | Q_Amp | count | count | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 201 | Q_Amp_V2 | Q_Amp | value | mV | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 202 | Q_Amp_V2_iqr | Q_Amp | iqr | mV | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 203 | Q_Amp_V2_count | Q_Amp | count | count | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 204 | Q_Amp_V3 | Q_Amp | value | mV | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 205 | Q_Amp_V3_iqr | Q_Amp | iqr | mV | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 206 | Q_Amp_V3_count | Q_Amp | count | count | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 207 | Q_Amp_V4 | Q_Amp | value | mV | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 208 | Q_Amp_V4_iqr | Q_Amp | iqr | mV | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 209 | Q_Amp_V4_count | Q_Amp | count | count | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 210 | Q_Amp_V5 | Q_Amp | value | mV | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 211 | Q_Amp_V5_iqr | Q_Amp | iqr | mV | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 212 | Q_Amp_V5_count | Q_Amp | count | count | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 213 | Q_Amp_V6 | Q_Amp | value | mV | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 214 | Q_Amp_V6_iqr | Q_Amp | iqr | mV | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 215 | Q_Amp_V6_count | Q_Amp | count | count | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 216 | Q_Amp_aVF | Q_Amp | value | mV | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 217 | Q_Amp_aVF_iqr | Q_Amp | iqr | mV | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 218 | Q_Amp_aVF_count | Q_Amp | count | count | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 219 | Q_Amp_aVL | Q_Amp | value | mV | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 220 | Q_Amp_aVL_iqr | Q_Amp | iqr | mV | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 221 | Q_Amp_aVL_count | Q_Amp | count | count | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 222 | Q_Amp_aVR | Q_Amp | value | mV | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 223 | Q_Amp_aVR_iqr | Q_Amp | iqr | mV | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 224 | Q_Amp_aVR_count | Q_Amp | count | count | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 225 | QRS_Dur_I | QRS_Dur | value | ms | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 226 | QRS_Dur_I_iqr | QRS_Dur | iqr | ms | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 227 | QRS_Dur_I_count | QRS_Dur | count | count | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 228 | QRS_Dur_II | QRS_Dur | value | ms | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 229 | QRS_Dur_II_iqr | QRS_Dur | iqr | ms | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 230 | QRS_Dur_II_count | QRS_Dur | count | count | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 231 | QRS_Dur_III | QRS_Dur | value | ms | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 232 | QRS_Dur_III_iqr | QRS_Dur | iqr | ms | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 233 | QRS_Dur_III_count | QRS_Dur | count | count | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 234 | QRS_Dur_V1 | QRS_Dur | value | ms | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 235 | QRS_Dur_V1_iqr | QRS_Dur | iqr | ms | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 236 | QRS_Dur_V1_count | QRS_Dur | count | count | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 237 | QRS_Dur_V2 | QRS_Dur | value | ms | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 238 | QRS_Dur_V2_iqr | QRS_Dur | iqr | ms | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 239 | QRS_Dur_V2_count | QRS_Dur | count | count | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 240 | QRS_Dur_V3 | QRS_Dur | value | ms | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 241 | QRS_Dur_V3_iqr | QRS_Dur | iqr | ms | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 242 | QRS_Dur_V3_count | QRS_Dur | count | count | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 243 | QRS_Dur_V4 | QRS_Dur | value | ms | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 244 | QRS_Dur_V4_iqr | QRS_Dur | iqr | ms | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 245 | QRS_Dur_V4_count | QRS_Dur | count | count | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 246 | QRS_Dur_V5 | QRS_Dur | value | ms | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 247 | QRS_Dur_V5_iqr | QRS_Dur | iqr | ms | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 248 | QRS_Dur_V5_count | QRS_Dur | count | count | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 249 | QRS_Dur_V6 | QRS_Dur | value | ms | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 250 | QRS_Dur_V6_iqr | QRS_Dur | iqr | ms | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 251 | QRS_Dur_V6_count | QRS_Dur | count | count | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 252 | QRS_Dur_aVF | QRS_Dur | value | ms | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 253 | QRS_Dur_aVF_iqr | QRS_Dur | iqr | ms | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 254 | QRS_Dur_aVF_count | QRS_Dur | count | count | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 255 | QRS_Dur_aVL | QRS_Dur | value | ms | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 256 | QRS_Dur_aVL_iqr | QRS_Dur | iqr | ms | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 257 | QRS_Dur_aVL_count | QRS_Dur | count | count | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 258 | QRS_Dur_aVR | QRS_Dur | value | ms | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 259 | QRS_Dur_aVR_iqr | QRS_Dur | iqr | ms | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 260 | QRS_Dur_aVR_count | QRS_Dur | count | count | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 261 | QRS_Dur_Global | QRS_Dur | value | ms | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 262 | QRS_Dur_Global_iqr | QRS_Dur | iqr | ms | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 263 | QRS_Dur_Global_count | QRS_Dur | count | count | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 264 | QT_IntCorr_I | QT_IntCorr | value | ms | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 265 | QT_IntCorr_I_iqr | QT_IntCorr | iqr | ms | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 266 | QT_IntCorr_I_count | QT_IntCorr | count | count | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 267 | QT_IntCorr_II | QT_IntCorr | value | ms | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 268 | QT_IntCorr_II_iqr | QT_IntCorr | iqr | ms | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 269 | QT_IntCorr_II_count | QT_IntCorr | count | count | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 270 | QT_IntCorr_III | QT_IntCorr | value | ms | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 271 | QT_IntCorr_III_iqr | QT_IntCorr | iqr | ms | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 272 | QT_IntCorr_III_count | QT_IntCorr | count | count | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 273 | QT_IntCorr_V1 | QT_IntCorr | value | ms | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 274 | QT_IntCorr_V1_iqr | QT_IntCorr | iqr | ms | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 275 | QT_IntCorr_V1_count | QT_IntCorr | count | count | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 276 | QT_IntCorr_V2 | QT_IntCorr | value | ms | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 277 | QT_IntCorr_V2_iqr | QT_IntCorr | iqr | ms | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 278 | QT_IntCorr_V2_count | QT_IntCorr | count | count | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 279 | QT_IntCorr_V3 | QT_IntCorr | value | ms | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 280 | QT_IntCorr_V3_iqr | QT_IntCorr | iqr | ms | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 281 | QT_IntCorr_V3_count | QT_IntCorr | count | count | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 282 | QT_IntCorr_V4 | QT_IntCorr | value | ms | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 283 | QT_IntCorr_V4_iqr | QT_IntCorr | iqr | ms | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 284 | QT_IntCorr_V4_count | QT_IntCorr | count | count | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 285 | QT_IntCorr_V5 | QT_IntCorr | value | ms | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 286 | QT_IntCorr_V5_iqr | QT_IntCorr | iqr | ms | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 287 | QT_IntCorr_V5_count | QT_IntCorr | count | count | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 288 | QT_IntCorr_V6 | QT_IntCorr | value | ms | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 289 | QT_IntCorr_V6_iqr | QT_IntCorr | iqr | ms | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 290 | QT_IntCorr_V6_count | QT_IntCorr | count | count | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 291 | QT_IntCorr_aVF | QT_IntCorr | value | ms | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 292 | QT_IntCorr_aVF_iqr | QT_IntCorr | iqr | ms | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 293 | QT_IntCorr_aVF_count | QT_IntCorr | count | count | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 294 | QT_IntCorr_aVL | QT_IntCorr | value | ms | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 295 | QT_IntCorr_aVL_iqr | QT_IntCorr | iqr | ms | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 296 | QT_IntCorr_aVL_count | QT_IntCorr | count | count | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 297 | QT_IntCorr_aVR | QT_IntCorr | value | ms | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 298 | QT_IntCorr_aVR_iqr | QT_IntCorr | iqr | ms | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 299 | QT_IntCorr_aVR_count | QT_IntCorr | count | count | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 300 | QT_IntFramingham_Global | QT_IntFramingham | value | ms | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 301 | QT_IntFramingham_Global_iqr | QT_IntFramingham | iqr | ms | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 302 | QT_IntFramingham_Global_count | QT_IntFramingham | count | count | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 303 | QT_Int_I | QT_Int | value | ms | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 304 | QT_Int_I_iqr | QT_Int | iqr | ms | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 305 | QT_Int_I_count | QT_Int | count | count | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 306 | QT_Int_II | QT_Int | value | ms | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 307 | QT_Int_II_iqr | QT_Int | iqr | ms | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 308 | QT_Int_II_count | QT_Int | count | count | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 309 | QT_Int_III | QT_Int | value | ms | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 310 | QT_Int_III_iqr | QT_Int | iqr | ms | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 311 | QT_Int_III_count | QT_Int | count | count | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 312 | QT_Int_V1 | QT_Int | value | ms | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 313 | QT_Int_V1_iqr | QT_Int | iqr | ms | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 314 | QT_Int_V1_count | QT_Int | count | count | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 315 | QT_Int_V2 | QT_Int | value | ms | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 316 | QT_Int_V2_iqr | QT_Int | iqr | ms | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 317 | QT_Int_V2_count | QT_Int | count | count | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 318 | QT_Int_V3 | QT_Int | value | ms | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 319 | QT_Int_V3_iqr | QT_Int | iqr | ms | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 320 | QT_Int_V3_count | QT_Int | count | count | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 321 | QT_Int_V4 | QT_Int | value | ms | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 322 | QT_Int_V4_iqr | QT_Int | iqr | ms | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 323 | QT_Int_V4_count | QT_Int | count | count | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 324 | QT_Int_V5 | QT_Int | value | ms | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 325 | QT_Int_V5_iqr | QT_Int | iqr | ms | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 326 | QT_Int_V5_count | QT_Int | count | count | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 327 | QT_Int_V6 | QT_Int | value | ms | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 328 | QT_Int_V6_iqr | QT_Int | iqr | ms | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 329 | QT_Int_V6_count | QT_Int | count | count | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 330 | QT_Int_aVF | QT_Int | value | ms | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 331 | QT_Int_aVF_iqr | QT_Int | iqr | ms | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 332 | QT_Int_aVF_count | QT_Int | count | count | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 333 | QT_Int_aVL | QT_Int | value | ms | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 334 | QT_Int_aVL_iqr | QT_Int | iqr | ms | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 335 | QT_Int_aVL_count | QT_Int | count | count | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 336 | QT_Int_aVR | QT_Int | value | ms | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 337 | QT_Int_aVR_iqr | QT_Int | iqr | ms | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 338 | QT_Int_aVR_count | QT_Int | count | count | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 339 | QT_Int_Global | QT_Int | value | ms | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 340 | QT_Int_Global_iqr | QT_Int | iqr | ms | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 341 | QT_Int_Global_count | QT_Int | count | count | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 342 | R_Amp_I | R_Amp | value | mV | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 343 | R_Amp_I_iqr | R_Amp | iqr | mV | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 344 | R_Amp_I_count | R_Amp | count | count | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 345 | R_Amp_II | R_Amp | value | mV | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 346 | R_Amp_II_iqr | R_Amp | iqr | mV | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 347 | R_Amp_II_count | R_Amp | count | count | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 348 | R_Amp_III | R_Amp | value | mV | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 349 | R_Amp_III_iqr | R_Amp | iqr | mV | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 350 | R_Amp_III_count | R_Amp | count | count | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 351 | R_Amp_V1 | R_Amp | value | mV | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 352 | R_Amp_V1_iqr | R_Amp | iqr | mV | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 353 | R_Amp_V1_count | R_Amp | count | count | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 354 | R_Amp_V2 | R_Amp | value | mV | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 355 | R_Amp_V2_iqr | R_Amp | iqr | mV | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 356 | R_Amp_V2_count | R_Amp | count | count | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 357 | R_Amp_V3 | R_Amp | value | mV | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 358 | R_Amp_V3_iqr | R_Amp | iqr | mV | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 359 | R_Amp_V3_count | R_Amp | count | count | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 360 | R_Amp_V4 | R_Amp | value | mV | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 361 | R_Amp_V4_iqr | R_Amp | iqr | mV | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 362 | R_Amp_V4_count | R_Amp | count | count | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 363 | R_Amp_V5 | R_Amp | value | mV | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 364 | R_Amp_V5_iqr | R_Amp | iqr | mV | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 365 | R_Amp_V5_count | R_Amp | count | count | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 366 | R_Amp_V6 | R_Amp | value | mV | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 367 | R_Amp_V6_iqr | R_Amp | iqr | mV | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 368 | R_Amp_V6_count | R_Amp | count | count | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 369 | R_Amp_aVF | R_Amp | value | mV | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 370 | R_Amp_aVF_iqr | R_Amp | iqr | mV | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 371 | R_Amp_aVF_count | R_Amp | count | count | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 372 | R_Amp_aVL | R_Amp | value | mV | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 373 | R_Amp_aVL_iqr | R_Amp | iqr | mV | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 374 | R_Amp_aVL_count | R_Amp | count | count | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 375 | R_Amp_aVR | R_Amp | value | mV | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 376 | R_Amp_aVR_iqr | R_Amp | iqr | mV | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 377 | R_Amp_aVR_count | R_Amp | count | count | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 378 | RR_Mean_Global | RR_Mean | value | ms | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 379 | RR_Mean_Global_iqr | RR_Mean | iqr | ms | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 380 | RR_Mean_Global_count | RR_Mean | count | count | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 381 | S_Amp_I | S_Amp | value | mV | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 382 | S_Amp_I_iqr | S_Amp | iqr | mV | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 383 | S_Amp_I_count | S_Amp | count | count | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 384 | S_Amp_II | S_Amp | value | mV | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 385 | S_Amp_II_iqr | S_Amp | iqr | mV | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 386 | S_Amp_II_count | S_Amp | count | count | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 387 | S_Amp_III | S_Amp | value | mV | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 388 | S_Amp_III_iqr | S_Amp | iqr | mV | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 389 | S_Amp_III_count | S_Amp | count | count | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 390 | S_Amp_V1 | S_Amp | value | mV | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 391 | S_Amp_V1_iqr | S_Amp | iqr | mV | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 392 | S_Amp_V1_count | S_Amp | count | count | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 393 | S_Amp_V2 | S_Amp | value | mV | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 394 | S_Amp_V2_iqr | S_Amp | iqr | mV | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 395 | S_Amp_V2_count | S_Amp | count | count | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 396 | S_Amp_V3 | S_Amp | value | mV | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 397 | S_Amp_V3_iqr | S_Amp | iqr | mV | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 398 | S_Amp_V3_count | S_Amp | count | count | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 399 | S_Amp_V4 | S_Amp | value | mV | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 400 | S_Amp_V4_iqr | S_Amp | iqr | mV | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 401 | S_Amp_V4_count | S_Amp | count | count | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 402 | S_Amp_V5 | S_Amp | value | mV | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 403 | S_Amp_V5_iqr | S_Amp | iqr | mV | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 404 | S_Amp_V5_count | S_Amp | count | count | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 405 | S_Amp_V6 | S_Amp | value | mV | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 406 | S_Amp_V6_iqr | S_Amp | iqr | mV | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 407 | S_Amp_V6_count | S_Amp | count | count | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 408 | S_Amp_aVF | S_Amp | value | mV | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 409 | S_Amp_aVF_iqr | S_Amp | iqr | mV | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 410 | S_Amp_aVF_count | S_Amp | count | count | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 411 | S_Amp_aVL | S_Amp | value | mV | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 412 | S_Amp_aVL_iqr | S_Amp | iqr | mV | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 413 | S_Amp_aVL_count | S_Amp | count | count | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 414 | S_Amp_aVR | S_Amp | value | mV | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 415 | S_Amp_aVR_iqr | S_Amp | iqr | mV | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 416 | S_Amp_aVR_count | S_Amp | count | count | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 417 | ST_Elev_I | ST_Elev | value | mV | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 418 | ST_Elev_I_iqr | ST_Elev | iqr | mV | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 419 | ST_Elev_I_count | ST_Elev | count | count | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 420 | ST_Elev_II | ST_Elev | value | mV | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 421 | ST_Elev_II_iqr | ST_Elev | iqr | mV | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 422 | ST_Elev_II_count | ST_Elev | count | count | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 423 | ST_Elev_III | ST_Elev | value | mV | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 424 | ST_Elev_III_iqr | ST_Elev | iqr | mV | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 425 | ST_Elev_III_count | ST_Elev | count | count | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 426 | ST_Elev_V1 | ST_Elev | value | mV | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 427 | ST_Elev_V1_iqr | ST_Elev | iqr | mV | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 428 | ST_Elev_V1_count | ST_Elev | count | count | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 429 | ST_Elev_V2 | ST_Elev | value | mV | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 430 | ST_Elev_V2_iqr | ST_Elev | iqr | mV | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 431 | ST_Elev_V2_count | ST_Elev | count | count | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 432 | ST_Elev_V3 | ST_Elev | value | mV | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 433 | ST_Elev_V3_iqr | ST_Elev | iqr | mV | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 434 | ST_Elev_V3_count | ST_Elev | count | count | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 435 | ST_Elev_V4 | ST_Elev | value | mV | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 436 | ST_Elev_V4_iqr | ST_Elev | iqr | mV | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 437 | ST_Elev_V4_count | ST_Elev | count | count | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 438 | ST_Elev_V5 | ST_Elev | value | mV | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 439 | ST_Elev_V5_iqr | ST_Elev | iqr | mV | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 440 | ST_Elev_V5_count | ST_Elev | count | count | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 441 | ST_Elev_V6 | ST_Elev | value | mV | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 442 | ST_Elev_V6_iqr | ST_Elev | iqr | mV | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 443 | ST_Elev_V6_count | ST_Elev | count | count | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 444 | ST_Elev_aVF | ST_Elev | value | mV | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 445 | ST_Elev_aVF_iqr | ST_Elev | iqr | mV | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 446 | ST_Elev_aVF_count | ST_Elev | count | count | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 447 | ST_Elev_aVL | ST_Elev | value | mV | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 448 | ST_Elev_aVL_iqr | ST_Elev | iqr | mV | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 449 | ST_Elev_aVL_count | ST_Elev | count | count | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 450 | ST_Elev_aVR | ST_Elev | value | mV | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 451 | ST_Elev_aVR_iqr | ST_Elev | iqr | mV | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 452 | ST_Elev_aVR_count | ST_Elev | count | count | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 453 | T_Amp_I | T_Amp | value | mV | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 454 | T_Amp_I_iqr | T_Amp | iqr | mV | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 455 | T_Amp_I_count | T_Amp | count | count | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 456 | T_Amp_II | T_Amp | value | mV | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 457 | T_Amp_II_iqr | T_Amp | iqr | mV | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 458 | T_Amp_II_count | T_Amp | count | count | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 459 | T_Amp_III | T_Amp | value | mV | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 460 | T_Amp_III_iqr | T_Amp | iqr | mV | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 461 | T_Amp_III_count | T_Amp | count | count | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 462 | T_Amp_V1 | T_Amp | value | mV | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 463 | T_Amp_V1_iqr | T_Amp | iqr | mV | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 464 | T_Amp_V1_count | T_Amp | count | count | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 465 | T_Amp_V2 | T_Amp | value | mV | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 466 | T_Amp_V2_iqr | T_Amp | iqr | mV | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 467 | T_Amp_V2_count | T_Amp | count | count | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 468 | T_Amp_V3 | T_Amp | value | mV | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 469 | T_Amp_V3_iqr | T_Amp | iqr | mV | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 470 | T_Amp_V3_count | T_Amp | count | count | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 471 | T_Amp_V4 | T_Amp | value | mV | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 472 | T_Amp_V4_iqr | T_Amp | iqr | mV | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 473 | T_Amp_V4_count | T_Amp | count | count | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 474 | T_Amp_V5 | T_Amp | value | mV | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 475 | T_Amp_V5_iqr | T_Amp | iqr | mV | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 476 | T_Amp_V5_count | T_Amp | count | count | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 477 | T_Amp_V6 | T_Amp | value | mV | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 478 | T_Amp_V6_iqr | T_Amp | iqr | mV | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 479 | T_Amp_V6_count | T_Amp | count | count | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 480 | T_Amp_aVF | T_Amp | value | mV | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 481 | T_Amp_aVF_iqr | T_Amp | iqr | mV | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 482 | T_Amp_aVF_count | T_Amp | count | count | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 483 | T_Amp_aVL | T_Amp | value | mV | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 484 | T_Amp_aVL_iqr | T_Amp | iqr | mV | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 485 | T_Amp_aVL_count | T_Amp | count | count | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 486 | T_Amp_aVR | T_Amp | value | mV | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 487 | T_Amp_aVR_iqr | T_Amp | iqr | mV | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 488 | T_Amp_aVR_count | T_Amp | count | count | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 489 | T_DurFull_I | T_DurFull | value | ms | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 490 | T_DurFull_I_iqr | T_DurFull | iqr | ms | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 491 | T_DurFull_I_count | T_DurFull | count | count | I | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 492 | T_DurFull_II | T_DurFull | value | ms | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 493 | T_DurFull_II_iqr | T_DurFull | iqr | ms | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 494 | T_DurFull_II_count | T_DurFull | count | count | II | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 495 | T_DurFull_III | T_DurFull | value | ms | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 496 | T_DurFull_III_iqr | T_DurFull | iqr | ms | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 497 | T_DurFull_III_count | T_DurFull | count | count | III | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 498 | T_DurFull_V1 | T_DurFull | value | ms | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 499 | T_DurFull_V1_iqr | T_DurFull | iqr | ms | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 500 | T_DurFull_V1_count | T_DurFull | count | count | V1 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 501 | T_DurFull_V2 | T_DurFull | value | ms | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 502 | T_DurFull_V2_iqr | T_DurFull | iqr | ms | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 503 | T_DurFull_V2_count | T_DurFull | count | count | V2 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 504 | T_DurFull_V3 | T_DurFull | value | ms | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 505 | T_DurFull_V3_iqr | T_DurFull | iqr | ms | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 506 | T_DurFull_V3_count | T_DurFull | count | count | V3 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 507 | T_DurFull_V4 | T_DurFull | value | ms | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 508 | T_DurFull_V4_iqr | T_DurFull | iqr | ms | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 509 | T_DurFull_V4_count | T_DurFull | count | count | V4 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 510 | T_DurFull_V5 | T_DurFull | value | ms | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 511 | T_DurFull_V5_iqr | T_DurFull | iqr | ms | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 512 | T_DurFull_V5_count | T_DurFull | count | count | V5 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 513 | T_DurFull_V6 | T_DurFull | value | ms | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 514 | T_DurFull_V6_iqr | T_DurFull | iqr | ms | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 515 | T_DurFull_V6_count | T_DurFull | count | count | V6 | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 516 | T_DurFull_aVF | T_DurFull | value | ms | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 517 | T_DurFull_aVF_iqr | T_DurFull | iqr | ms | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 518 | T_DurFull_aVF_count | T_DurFull | count | count | aVF | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 519 | T_DurFull_aVL | T_DurFull | value | ms | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 520 | T_DurFull_aVL_iqr | T_DurFull | iqr | ms | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 521 | T_DurFull_aVL_count | T_DurFull | count | count | aVL | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 522 | T_DurFull_aVR | T_DurFull | value | ms | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 523 | T_DurFull_aVR_iqr | T_DurFull | iqr | ms | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 524 | T_DurFull_aVR_count | T_DurFull | count | count | aVR | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 525 | T_Dur_Global | T_Dur | value | ms | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 526 | T_Dur_Global_iqr | T_Dur | iqr | ms | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 527 | T_Dur_Global_count | T_Dur | count | count | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 528 | HA__Global | HA | value | integer | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 529 | HA__Global_iqr | HA | iqr | integer | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
| 530 | HA__Global_count | HA | count | count | Global | PTB-XL+ 1.0.1 ecgdeli_features.csv | identity proven; semantics declared |
