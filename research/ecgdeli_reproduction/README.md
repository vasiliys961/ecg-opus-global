# Воспроизведение ECGDeli для записи 00513

Контур отдельный от продукта. GPL-код ECGDeli в этот репозиторий не копировался. Большие сигналы лежат в `data/` и в Git не входят.

Дата: 2026-09-28.

## Зафиксированные версии

| Параметр | Значение |
| --- | --- |
| PTB-XL | 1.0.3, https://physionet.org/content/ptb-xl/1.0.3/ , DOI 10.13026/kfzx-aw45 |
| PTB-XL+ | 1.0.1, https://physionet.org/content/ptb-xl-plus/1.0.1/ , DOI 10.13026/nqsf-pc74 |
| ECGDeli tag | `v1.1` |
| ECGDeli commit | `3c13b1b2ff55152360f3cee992c1d1d66099aa14` |
| Где лежит checkout | `/tmp/ECGdeli`, вне дерева исходников продукта. `git rev-parse HEAD` и `git describe --tags --exact-match` дали `v1.1`. Клон shallow, в `git log` есть пометка `grafted`. Хеш тега совпал. |
| Лицензия ECGDeli | GPL-3.0. В `ecg_engine`, `backend` и `frontend` не копировался. |
| Python | 3.11.9 |
| OS | macOS 26.6.2, Darwin 25.6.0 arm64 |
| MATLAB | нет в `PATH`. Команда `matlab -batch "disp('ecgdeli')"` завершилась `command not found: matlab`. Лог: `logs/matlab_stderr.txt`. |
| Octave | нет в `PATH`. `command not found: octave`. Лог: `logs/octave_stderr.txt`. |
| Зависимости ECGDeli по его README | MATLAB Image Processing Toolbox, Signal Processing Toolbox, Statistics and Machine Learning Toolbox, Wavelet Toolbox. Установлены ли они: `UNKNOWN`, интерпретатора нет. |

## Сигнал 00513

Оба файла скачаны с PhysioNet в `data/ptbxl/`. В Git не добавляются.

| Файл | SHA-256 | Что в заголовке |
| --- | --- | --- |
| `records500/00000/00513_hr.hea` | `1db362e1df09f47b413abdc6080ec9ae59cbd9b5a15970f79504e032a3499368` | 12 отведений, 500 Гц, 5000 отсчётов |
| `records500/00000/00513_hr.dat` | `a496d78ceb895ca9a81bdde32d62876d17022004a17d9e52bf9cd8318b6403e0` | 120000 байт, format 16 |
| `records100/00000/00513_lr.hea` | `dc6094131bcc354e6421daef54e73b50c5108da6df8f22f45cbaeec3fe8ce8c1` | 12 отведений, 100 Гц, 1000 отсчётов |
| `records100/00000/00513_lr.dat` | `ebafc313aacf8280a8cbd4f106b346128e8eee8e15465500e1808b4b42fbb604` | 24000 байт, format 16 |

Длительность обеих записей: 10 с. Усиление в заголовке: `1000.0(0)/mV`, формат 16. Baseline в заголовке разный у отведений, это ADC baseline, не фильтр isoline.

Порядок отведений в WFDB, как записан в `.hea`:

`I, II, III, aVR, aVL, aVF, V1, V2, V3, V4, V5, V6`

Порядок колонок опубликованных 531 признаков другой:

`I, II, III, V1, V2, V3, V4, V5, V6, aVF, aVL, aVR`, затем `Global`, где он есть.

Перестановка под ECGDeli не делалась: программа не запускалась. Молча порядок не менялся.

В примере `Example/Annotate_ExampleECG.m` тега `v1.1` канал 2 назван lead II, канал 7 назван lead V1. Это совпадает с порядком WFDB, если первый канал — I. Полный список из 12 имён сам скрипт не печатает. Ожидаемый ECGDeli порядок для записи PTB-XL+: `UNKNOWN`.

## Параметры ECGDeli, которыми PTB-XL+ считал таблицу

`UNKNOWN`. Статья говорит только «publicly available version 1.1». Журнала запуска для записи 00513 нет.

Ниже параметры примера из того же тега. Это не конфигурация PTB-XL+.

| Вызов в примере | Аргументы | Куда пошёл сигнал |
| --- | --- | --- |
| `ECG_Baseline_Removal` | `Fs`, окно `1`, overlap `0.5` | Результат нарисован и дальше не подан в аннотацию |
| `ECG_High_Low_Filter` | highpass `1` Гц, lowpass `40` Гц, тип по умолчанию `Butterworth` | На исходный `ecg`, не на сигнал после baseline removal |
| `Notch_Filter` | `50` Гц, width `1` | После high/low |
| `Isoline_Correction` | без дополнительных аргументов | Его выход подаётся в `Annotate_ECG_Multi` |
| `Annotate_ECG_Multi` | только сигнал и `Fs` | Значит `process_flag` по умолчанию `'all'` |
| `Fs` в примере | `1000` | Это другая запись PTB Diagnostic, не 00513 |

Частота, фильтр, notch, baseline и флаг волн для PTB-XL+: `UNKNOWN`.

## Агрегация PTB-XL+

Оригинальный скрипт, который из комплексов делает `value + IQR + count` и пишет `ecgdeli_features.csv`, не найден.

Проверено:

- Zenodo https://doi.org/10.5281/zenodo.7817567 . Страница открывается. Файл на ней: `ptbxl_feature_benchmark-v1.0.0.zip`, заявленный md5 `5aa66a7934d7856fbc9435a0de7b66cf`. Прямая загрузка zip вернула HTTP 403.
- Тот же репозиторий, на который страница ссылается: https://github.com/tmehari/ptbxl_feature_benchmark/tree/v1.0.0 , commit `e79c58e4fe962bb0e67be8ef878aa629a3177e56` (2022-11-15, «add LICENSE»). История с первого коммита просмотрена. Скрипта агрегации ECGDeli нет. `code/feature_utils/utils.py` читает уже готовый `features/ecgdeli_features.csv`. Комментарий в коде: `kit_features_final.csv`.
- ECGDeli `v1.1` отдаёт матрицы по комплексам (`ExtractIntervalFeaturesFromFPT`, `ExtractAmplitudeFeaturesFromFPT`, `Get_P_Morphology`), не 531 колонку.
- https://github.com/KIT-IBT/ECGfeat — другой набор признаков F1–F18, не эта таблица.

Своя агрегация не писалась.

## Запуск

ECGDeli не запускался. `output/raw_ecgdeli_00513/` пуст по этой причине.

Команда, которая была выполнена:

```text
matlab -batch "disp('ecgdeli')"
```

stderr: `command not found: matlab`.

Замена на NeuroKit, BioSPPy или собственный экстрактор не делалась.
