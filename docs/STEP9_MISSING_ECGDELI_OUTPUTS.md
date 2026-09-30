# Шаг 9. Поиск недостающих выходов ECGDeli

Дерево: ECGDeli tag `v1.1`, commit `3c13b1b2ff55152360f3cee992c1d1d66099aa14` (2022-10-12, «Add P-wave morphology estimator»). Просмотрены все 26 файлов `.m`: 25 функций верхнего уровня и вложенная `search_p`. Скрипт `Example/Annotate_ExampleECG.m` функцией не является.

`RAW_TO_531_STATUS` остаётся `NOT_PROVEN`. Экстрактор не писался. Сеть не запускалась. Считалась только уже известная запись `00513`, новый прогон ECGDeli не делался.

## Короткий ответ по 291

| Группа | Колонок | Есть ли функция в v1.1 | Есть ли её выход в архиве 00513 |
| --- | ---: | --- | --- |
| `P_Amp`, `Q_Amp`, `R_Amp`, `S_Amp`, `T_Amp` | 180 | да, `ExtractAmplitudeFeaturesFromFPT` | нет, в `.atr` только номера сэмплов |
| `P_Morph` | 36 | да, `Get_P_Morphology` | нет, кодов морфологии в `.atr` нет |
| `QT_IntCorr` | 36 | нет отдельной per-lead коррекции | нет |
| `ST_Elev` | 36 | нет; есть только индекс L/J point | индекс L point в `.atr` есть, милливольт нет |
| `HA__Global` | 3 | нет | нет |

216 колонок имеют публичную функцию, чей результат в PTB-XL+ не выложен отдельно от итоговой таблицы. 75 колонок эта версия не производит. Словарь `feature_description.csv` называет их `QTci_X`, `STc_X` и `elHA`. Этих имён в исходниках нет.

## Что публичный ECGDeli реально возвращает

`Annotate_ECG_Multi(signal, samplerate, wave_flag)` возвращает две таблицы точек, не 531 число.

`FPT_Cell{lead}` и `FPT_MultiChannel`, столбцы в сэмплах:

| Столбец | Поле |
| ---: | --- |
| 1 | P onset |
| 2 | P peak |
| 3 | P offset |
| 4 | QRS onset |
| 5 | Q peak |
| 6 | R peak |
| 7 | S peak |
| 8 | QRS offset |
| 9 | L point, в синхронизации он же назван J point |
| 10 | T onset |
| 11 | T peak |
| 12 | T offset |

Флаг волны по умолчанию `'all'`. Допустимые значения: `all`, `PQRST`, `PQRS`, `QRST`, `QRS`, `P`, `T`, `PT`. Какой флаг был у прогона PTB-XL+, по-прежнему неизвестно.

Поверх этих таблиц лежат две функции признаков. Обе датированы 12.10.2022, тем же днём, что и тег v1.1. `Annotate_ECG_Multi` их сам не вызывает. Их вызывает пример.

`ExtractIntervalFeaturesFromFPT(FPT, FPT_MultiChannel)` не принимает частоту дискретизации. Разности сэмплов умножаются на 2, то есть миллисекунды заложены как 500 Гц.

- Lead-wise, матрица leads × beats × 7: длительность P, QRS, T, PQ, PR, QT, RR. RR здесь тоже lead-wise, и последний интервал копируется.
- Sync, beats × 8: те же шесть интервалов правилом второго порядка, затем QTc Фрамингема, затем RR. Единственная строка коррекции QT во всём дереве:

```text
features_sync(:,7) = 1000.*(QT/1000 + 0.154*(1 - 0.001*RR))
```

Это глобальный столбец, который в словаре назван `QTci_max` и в таблице — `QT_IntFramingham_Global`. Per-lead `QTci_X` / `QT_IntCorr` эта функция не пишет. Lead-wise QT и lead-wise RR в матрице есть, формулы, которая сводит их в per-lead QTc, в файле нет. Такая свёртка здесь не считалась.

`ExtractAmplitudeFeaturesFromFPT(FPT, signal)` возвращает leads × beats × 5: сэмпл сигнала в P peak, Q peak, R peak, S peak, T peak. Перевода единиц внутри нет: единица равна единице переданной матрицы. Индексы меньше 1 поднимаются до 1, индексы длиннее сигнала обрезаются. Первый размер массива зашит как 12. В примере аргумент — `ecg_filtered_isoline`, подпись оси — mV. Это настройки примера на чужой записи PTB Diagnostic с `Fs = 1000`, не журнал прогона 00513.

`Get_P_Morphology(signal, samplerate, FPT)` возвращает `PMorph` размера beats × leads. Коды в присваиваниях: −3, −2, −1, 1, 2, 3 и 0, если форма не определилась. Комментарий предупреждает, что код не проверялся на устойчивость. Пример передаёт исходный `ecg`, не фильтрованный. Внутри функция сама снимает baseline (окно 0,3 с, перекрытие 0,3) и изолинию. Два вызова `designfilt` держат `SampleRate` 1000 независимо от аргумента `samplerate`. Для записи 00513, размеченной на 500 Гц, это отдельное расхождение, и функция на ней не запускалась.

## L point не является ST_Elev

`T_Detection` и `Check_T_Wave` пишут столбец 9 как середину между QRS offset и T onset (`k = 0.5`, либо 0.55 от S, либо 0.6 от R). Комментарий говорит, что точка нужна для диагноза ST elevation или depression. Амплитуда, базовая линия сегмента ST и гауссовы коэффициенты не возвращаются.

`Sync_Beats` и `Sync_Channels` читают столбец 9 как время J point и используют его, чтобы выровнять комплексы. Наружу они отдают снова FPT, не милливольты.

Слово `gaussian` в v1.1 встречается в notch, high/low фильтре и детекторе P. Это ядро фильтра, не «multiple Gaussian fits» из описания `STc_X`.

`Create_Template` возвращает `ampRpeak` одного шаблона одного отведения. Это не ряд `R_Amp` по 12 отведениям и по комплексам.

Локальные переменные с именем `amplitude` в `QRS_Detection`, `Check_R_Peaks_Multi` и `Check_T_Wave` выбирают пик внутри детектора и в таблицу признаков не пишутся.

Поиск по всему дереву v1.1 не дал совпадений: `Bazett`, `Fridericia`, `Hodges`, `elHA`, `STc`, `QTci`, `heart axis`, `electrical axis`, `frontal axis`.

## Инвентарь функций

Commit у всех строк один: `3c13b1b2`. «291» — может ли выход стать одной из недостающих колонок.

| Функция | Файл | Вход | Выход | Единицы | Охват | 291 |
| --- | --- | --- | --- | --- | --- | --- |
| `Annotate_ECG_Multi` | `ECG_Processing/Annotate_ECG_Multi.m` | signal, samplerate, wave flag | `FPT_MultiChannel`, `FPT_Cell` | сэмплы | lead и sync | нет, это точки, уже использованные для 240 |
| `QRS_Detection` | `QRS_Detection.m` | signal, samplerate, optional `peaksQRS` | FPT, R в столбце 6 | сэмплы | одно отведение | нет |
| `P_Detection` | `P_Detection.m` | signal, samplerate, FPT | FPT со столбцами P | сэмплы | одно отведение | нет |
| `search_p` | внутри `P_Detection.m` | filtered signal, wt max, samplerate, flag | позиция P | сэмплы | одно отведение | нет |
| `T_Detection` | `T_Detection.m` | signal, samplerate, FPT | FPT, столбцы 9–12 | сэмплы | одно отведение | столбец 9 — индекс, не `ST_Elev` |
| `Check_T_Wave` | `Check_T_Wave.m` | signal, samplerate, FPT | уточнённый FPT | сэмплы | одно отведение | то же про столбец 9 |
| `Check_R_Peaks_Multi` | `Check_R_Peaks_Multi.m` | signal, samplerate, FPT | уточнённые R | сэмплы | одно отведение | нет |
| `Check_Position_ECG_Waves` | `Check_Position_ECG_Waves.m` | FPT | FPT без сбитых волн | сэмплы | таблица точек | нет |
| `Check_Small_RR` | `Check_Small_RR.m` | FPT, samplerate | FPT без коротких RR | сэмплы | таблица точек | нет |
| `Sync_Beats` | `Sync_Beats.m` | FPT cell, samplerate | выровненные FPT | сэмплы | lead и sync | нет |
| `Sync_Channels` | `Sync_Channels.m` | FPT cell, samplerate | выровненные FPT | сэмплы | lead и sync | нет |
| `Sync_R_Peaks` | `Sync_R_Peaks.m` | FPT cell, samplerate | выровненные R | сэмплы | sync | нет |
| `ExtractIntervalFeaturesFromFPT` | `ExtractIntervalFeaturesFromFPT.m` | FPT cell, FPT sync | lead-wise 7 интервалов и sync 8, включая один QTc | мс при множителе 2 | lead и один глобальный QTc | per-lead `QT_IntCorr` не выходит |
| `ExtractAmplitudeFeaturesFromFPT` | `ExtractAmplitudeFeaturesFromFPT.m` | FPT cell, signal | P, Q, R, S, T | единица матрицы signal | lead-wise | да, 180 колонок, если матрица та же |
| `Get_P_Morphology` | `Get_P_Morphology.m` | signal, samplerate, FPT cell | `PMorph`, `Peaks` | целые коды; пики в сэмплах | lead-wise | да, 36 колонок, если функцию запустить |
| `Create_Template` | `Create_Template.m` | один вектор signal, samplerate, FPT, `ECG` или `QRS` | шаблон, позиция R, одна амплитуда R | амплитуда как у signal | одно отведение | нет |
| `Isoline_Correction` | `Filtering/Isoline_Correction.m` | signal, optional bins | сигнал без моды, offset | как у signal | по каналам | нет, это подготовка |
| `ECG_Baseline_Removal` | `ECG_Baseline_Removal.m` | signal, samplerate, window, overlap | сигнал и baseline | как у signal | по каналам | нет, это подготовка |
| `ECG_High_Low_Filter` | `ECG_High_Low_Filter.m` | signal, samplerate, high, low, тип | фильтрованный сигнал | как у signal | по каналам | нет |
| `ECG_High_Filter` | `ECG_High_Filter.m` | signal, samplerate, high, тип | фильтрованный сигнал | как у signal | по каналам | нет |
| `ECG_Low_Filter` | `ECG_Low_Filter.m` | signal, samplerate, low, тип | фильтрованный сигнал | как у signal | по каналам | нет |
| `Notch_Filter` | `Notch_Filter.m` | signal, samplerate, f0, width | сигнал без частоты f0 | как у signal | по каналам | нет |
| `Remove_QRST` | `Remove_QRST.m` | signal, samplerate, FPT | сигнал с вырезанным QRST | как у signal | одно отведение | служебный вход морфологии |
| `Remove_PQRS` | `Remove_PQRS.m` | signal, samplerate, FPT | сигнал с вырезанным PQRS | как у signal | одно отведение | нет |
| `Remove_QRS_single` | `Remove_QRS_single.m` | signal, samplerate, FPT | сигнал с вырезанным QRS | как у signal | одно отведение | нет |
| `l_operator` | `l_operator.m` | x, y | оператор для детектора | безразмерный промежуточный | не признак | нет |

## Пример не равен прогону PTB-XL+

`Annotate_ExampleECG.m` задаёт `Fs = 1000`. Baseline removal считается и рисуется, а в частотный фильтр уходит исходный `ecg`: highpass 1 Гц, lowpass 40 Гц, затем notch 50 Гц шириной 1, затем `Isoline_Correction`. Амплитуды читаются из `ecg_filtered_isoline`. Морфология читается из исходного `ecg`. Интервалы читаются только из FPT.

Комментарий над фильтром упоминает lowpass 120 Гц и highpass 0,3 Гц, а вызов стоит `ECG_High_Low_Filter(ecg, Fs, 1, 40)`. Для детекторов внутри дерева другие числа: QRS и проверка R фильтруются аргументами функции, T и проверка T — 0,3 и 20 Гц, Butterworth. Какая из этих веток была у авторов таблицы, исходник v1.1 не говорит.

## Соседние деревья

Master ECGDeli `c3738612771264e4d6c4686898ef7b2d6a700ad3` (2025-05-27) содержит те же 34 blob-пути, что и v1.1. Отличаются пять файлов: `CITATION.md`, `CITATION.cff`, `README.md`, приведение `samplerate` к double в `Annotate_ECG_Multi` и правка аргументов `findpeaks` в `Get_P_Morphology`. `ExtractIntervalFeaturesFromFPT.m` и `ExtractAmplitudeFeaturesFromFPT.m` по blob совпадают с v1.1. Функций `elHA`, `STc` и per-lead QTc на master не появилось.

`ECGfeat` — другой набор, 18 признаков на комплекс. Там есть имя `ST elevation` как разность высот двух гауссовых кривых на зубце T (`featureMatrix(16) = curve2.h - curve1.h`). Это не столбец `STc_X` и не таблица из 36 колонок. К воспроизведению `ST_Elev` эта функция не подключалась.

В fiducial-файлах `00513` по-прежнему 12 имён точек плюс строка `time resolution: 500`. Амплитуд, кодов `PMorph` и класса оси там нет.

## Что авторы добавили поверх v1.1

Для 216 колонок добавление — не новая формула внутри ECGDeli, а вызов уже существующих `ExtractAmplitudeFeaturesFromFPT` и `Get_P_Morphology` и запись агрегатов в CSV. Сам вызов в открытом журнале PTB-XL+ не найден, промежуточные матрицы не опубликованы, поэтому числа этих 216 из артефактов 00513 всё ещё не доказаны.

Для 75 колонок добавление лежит вне открытого ECGDeli. На master `c373861` от 2025-05-27 этих функций по-прежнему нет. Словарь даёт имена и текстовые определения. Реализации `QTci_X`, `STc_X` и `elHA` в просмотренных исходниках нет.

Полного вектора 531 из открытого ECGDeli 1.1 не получается. Статус сырого пути не меняется.
