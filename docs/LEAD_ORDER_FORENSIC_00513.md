# Порядок отведений, запись 00513

Опубликованная таблица признаков не изменялась. Ниже сверка четырёх порядков и численное соответствие файлов колонкам CSV.

## Четыре порядка

| Source | Position | Lead |
| --- | ---: | --- |
| PTB-XL raw | 1 | I |
| PTB-XL raw | 2 | II |
| PTB-XL raw | 3 | III |
| PTB-XL raw | 4 | AVR |
| PTB-XL raw | 5 | AVL |
| PTB-XL raw | 6 | AVF |
| PTB-XL raw | 7 | V1 |
| PTB-XL raw | 8 | V2 |
| PTB-XL raw | 9 | V3 |
| PTB-XL raw | 10 | V4 |
| PTB-XL raw | 11 | V5 |
| PTB-XL raw | 12 | V6 |
| fiducial | file `00513_points_lead_I.atr` | I |
| fiducial | file `00513_points_lead_II.atr` | II |
| fiducial | file `00513_points_lead_III.atr` | III |
| fiducial | file `00513_points_lead_aVR.atr` | aVR |
| fiducial | file `00513_points_lead_aVL.atr` | aVL |
| fiducial | file `00513_points_lead_aVF.atr` | aVF |
| fiducial | file `00513_points_lead_V1.atr` | V1 |
| fiducial | file `00513_points_lead_V2.atr` | V2 |
| fiducial | file `00513_points_lead_V3.atr` | V3 |
| fiducial | file `00513_points_lead_V4.atr` | V4 |
| fiducial | file `00513_points_lead_V5.atr` | V5 |
| fiducial | file `00513_points_lead_V6.atr` | V6 |
| ECGDeli | 1 | I, если в `signal(:,i)` передан WFDB-порядок |
| ECGDeli | 2 | II; комментарий примера к амплитуде прямо называет entry 2 отведением II |
| ECGDeli | 3 | III |
| ECGDeli | 4 | aVR |
| ECGDeli | 5 | aVL |
| ECGDeli | 6 | aVF |
| ECGDeli | 7 | V1; комментарий примера к амплитуде прямо называет entry 7 отведением V1 |
| ECGDeli | 8 | V2 |
| ECGDeli | 9 | V3 |
| ECGDeli | 10 | V4 |
| ECGDeli | 11 | V5 |
| ECGDeli | 12 | V6 |
| PTB-XL+ feature CSV | 1 | I |
| PTB-XL+ feature CSV | 2 | II |
| PTB-XL+ feature CSV | 3 | III |
| PTB-XL+ feature CSV | 4 | V1 |
| PTB-XL+ feature CSV | 5 | V2 |
| PTB-XL+ feature CSV | 6 | V3 |
| PTB-XL+ feature CSV | 7 | V4 |
| PTB-XL+ feature CSV | 8 | V5 |
| PTB-XL+ feature CSV | 9 | V6 |
| PTB-XL+ feature CSV | 10 | aVF |
| PTB-XL+ feature CSV | 11 | aVL |
| PTB-XL+ feature CSV | 12 | aVR |

Позиции CSV — это порядок внутри семейства из 12 отведений (`PQ_Int` и остальные). У части семейств следом идёт `Global`. Это не тринадцатое отведение.

Заголовок `00513_hr.hea`: `I, II, III, AVR, AVL, AVF, V1, V2, V3, V4, V5, V6`. Тот же порядок в `00513_lr.hea`.

## Что делает ECGDeli с номером канала

`Annotate_ECG_Multi` кладёт `FPT_Cell{i}` из `signal(:,i)`. Внутри v1.1 нет перестановки aVL и aVF.

В `Example/Annotate_ExampleECG.m` два комментария согласованы с WFDB: амплитуда entry 2 подписана как lead II, entry 7 как lead V1. Другой комментарий в том же файле называет `FPT_Cell{3,1}` «Channel 1 (Lead I)» и тут же рисует столбец 3. Этот комментарий противоречит двум амплитудным подписям и коду, который индексирует столбец 3. Он не задаёт обмен aVL и aVF.

Параметры вызова ECGDeli авторами PTB-XL+ по-прежнему неизвестны. Таблица канала ECGDeli выше — это порядок, который следует из комментариев примера, если на вход подан WFDB-сигнал. Это не лог прогона записи 00513.

## Численное соответствие на записи 00513

Интервалы шести семейств (`PQ_Int`, `PR_Int`, `QRS_Dur`, `QT_Int`, `P_DurFull`, `T_DurFull`) сравнивались по value и IQR.

| CSV column | Файл, чьи интервалы совпали с этой колонкой | Имя совпадает |
| --- | --- | --- |
| I | `00513_points_lead_I.atr` | да |
| II | `00513_points_lead_II.atr` | да |
| III | `00513_points_lead_III.atr` | да |
| V1 | `00513_points_lead_V1.atr` | да |
| V2 | `00513_points_lead_V2.atr` | да |
| V3 | `00513_points_lead_V3.atr` | да |
| V4 | `00513_points_lead_V4.atr` | да |
| V5 | `00513_points_lead_V5.atr` | да |
| V6 | `00513_points_lead_V6.atr` | да |
| aVF | `00513_points_lead_aVL.atr` | нет |
| aVL | `00513_points_lead_aVF.atr` | нет |
| aVR | `00513_points_lead_aVR.atr` | да |

Это обмен пары aVF/aVL, а не сдвиг всех отведений: aVR и девять остальных имён совпали. Count у этой пары совпадал и до обмена, потому что в каждом файле 12 комплексов.

Глобальные интервалы от обмена не зависят: правило второго порядка берёт набор из 12 рядов, и набор тот же.

## Что изменено в реконструкторе

В v2 колонка CSV `aVF` читает файл `lead_aVL`, колонка `aVL` читает файл `lead_aVF`. Остальные десять колонок читают файл своего имени. Опубликованный CSV не редактировался. Соответствие записано в `experiments/raw_to_531/lead_mapping_v2.json`.
