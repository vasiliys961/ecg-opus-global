# STEP 14 — независимый аудит STEP 13

Проверен репозиторий `/Users/maxmobiles.ru/Desktop/ECG-opus`, ветка `experimental/step13-compatibility-layer`, commit `093ebb1deef1bb4de815ddf78120b9e1a1b92036`. Исходный inference — снимок `_audit/ecg_web_up` на `bfe7c17`. Код, веса и `RAW_TO_531_STATUS` этим аудитом не менялись. Merge не выполнялся.

Итог: архитектурная граница в рабочем дереве соблюдена, но commit `093ebb1` сам по себе не запускается. STEP 13 технически завершённым считать нельзя.

## Сводка

| Раздел | Вердикт |
| --- | --- |
| 1. Git | FAIL |
| 2. Canonical schema | PASS |
| 3. Model regression | PASS |
| 4. Feature provenance | PASS |
| 5. Unknown values | PASS |
| 6. API | PASS |
| 7. Existing endpoints | PASS |
| 8. Frontend | PASS |
| 9. Tests | FAIL |
| 10. Документация | FAIL |

Риск коммита как воспроизводимого артефакта: высокий. Риск численного сдвига reference CSV inference: низкий.

## 1. Git — FAIL

Ветка и commit совпали с заявленными. `git merge-base main HEAD` — `dbb1801`. Diff `main...HEAD`: 22 файла, `+3210/−28`. В этом diff нет `models/`, `ecg_engine/networks.py`, `ecg_engine/feature_columns.py`, `ecg_engine/ensemble.py`, `ecg_engine/scp.py`.

`_audit/doctor-opus-global` в diff не входит. Его рабочее дерево чистое, ветка `main`.

Незакоммиченные изменения есть. Среди них правки `ecg_engine/ensemble.py` и `ecg_engine/schema.py`, без которых новый API не импортируется. В commit `093ebb1` `backend/app.py` импортирует `predict_features` и `service_payload`. В `ecg_engine/ensemble.py` этого commit этих имён нет. `read_feature_mapping` в committed `schema.py` тоже нет.

Проверка чистого дерева:

```text
git archive 093ebb1
PYTHONPATH=/tmp/step14-clean .venv/bin/python -c 'import backend.app'
```

Результат: `ImportError: cannot import name 'predict_features'`. То же дерево с незакоммиченными правками импортируется.

## 2. Canonical schema — PASS

`FEATURE_COLUMNS_531` — это тот же объект, что `FEATURE_COLUMNS`. Длина 531, уникальных имён 531. Список не отсортирован. Первый индекс `PQ_Int_I` = 0, последний `HA__Global_count` = 530. Файл `feature_columns.py` между `main` и `093ebb1` не менялся. Порядок задан схемой, экстрактор его не переставляет.

## 3. Model regression — PASS

Допуск проекта в committed regression-тесте: max absolute difference `< 1e-5`.

Один и тот же CSV `tests/fixtures/another_ecg_features.csv` прогнан через `_audit/ecg_web_up/analysis_scripts/predict_csv.py` и через `predict_csv` из чистого archive commit `093ebb1` (`models/ecg_ensemble`).

| Голова | max absolute difference |
| --- | ---: |
| MLP | 0.0 |
| CNN | 0.0 |
| ResNet | 0.0 |
| ensemble, 24 выхода | 0.0 |

Исходный inference был доступен. Тест не объявлен пройденным по отсутствию оригинала. В рабочем дереве `predict_features` против `predict_csv` на той же строке тоже даёт max absolute difference `0.0`. Незакоммиченная правка `ensemble.py` добавляет отказ при NaN после той же формулы среднего трёх сигмоид и на конечных выходах число не меняет.

Это сравнение reference CSV. Оно не проверяет 531 сырых значения: слой их не вычисляет.

## 4. Feature provenance — PASS

Файла `feature_registry.csv` нет. Сверены `ecg_engine/feature_registry.py` и `experiments/raw_to_531/step13_feature_status.csv`. В CSV 531 строка, порядок колонок совпадает со схемой. У каждой строки есть provenance в ответе движка. `exact_proven` везде `false`. Статуса `EXACT_PROVEN` нет.

| Семья | Колонок | Статус | Confidence | exact_proven | value_00513 заполнен |
| --- | ---: | --- | --- | --- | ---: |
| Intervals/RR/Framingham | 240 | RECONSTRUCTED | HIGH | false | 240 |
| Amplitudes | 180 | RECONSTRUCTED | MEDIUM | false | 180 |
| P_Morph | 36 | NOT_EXECUTED | UNKNOWN | false | 0 |
| QT_IntCorr | 36 | RECONSTRUCTED | HIGH | false | 36 |
| ST_Elev | 36 | UNKNOWN | UNKNOWN | false | 0 |
| HA__Global | 3 | UNKNOWN | UNKNOWN | false | 0 |

Статусы не подняты до точного тождества с PTB-XL+. Заметки интервалов говорят о 238 ячейках `<= 1e-6` на одной записи и не объявляют все 240 доказанными. `QT_IntCorr` прямо пишет, что порог `1e-6` не взят. `P_Morph` не назван reconstructed. Для `ST_Elev` и `HA__Global` алгоритм не подставлен.

Числа в `value_00513` — forensic-кандидаты из step 12, не выход `FeatureCompatibilityEngine`. Живой разбор возвращает 531 пустое значение и маску из нулей.

## 5. Unknown values — PASS

На синтетическом сигнале 12×20 и на контракте записи 00513 движок кладёт `None` в каждую ячейку. Нуля, среднего и оценки нет. `feature_mask` — 531 нулей. `UNKNOWN` и `NOT_EXECUTED` в status CSV не имеют `value_00513` и `absolute_error_00513`.

`POST /api/ecg/raw/features` не вызывает ансамбль. `ensemble_allowed` для этого вектора ложен: нет статуса `EXACT_PROVEN` и нет конечных чисел. `POST /api/ecg/predict` с `null` в признаке отвечает 400. Сырой ответ поэтому нельзя передать в существующий контракт без подмены пустых ячеек.

Отдельное наблюдение, не дыра сырого пути: reference endpoint примет любой конечный вектор 531, в том числе вектор из нулей, собранный вручную. Сам compatibility layer такой вектор не создаёт.

## 6. API — PASS

Проверен рабочий процесс, потому что чистый commit не импортирует приложение.

| Запрос | Код | Наблюдение |
| --- | ---: | --- |
| 12 отведений, 500 Гц, конечный сигнал | 200 | `RECONSTRUCTED_RAW_MODE`, `NOT_PROVEN`, 531 null, маска 0, provenance 531 |
| нет обязательного отведения | 400 | `FAIL: нет отведений` |
| частота 0 и отрицательная | 400 | отказ |
| частота не число | 422 | отказ разбора JSON |
| частота 100 Гц | 200 | принята и записана, передискретизации нет |
| сигнал не матрица отведений | 400 | отказ |
| NaN и Infinity в сигнале | 400 | отказ |
| отведения в обратном порядке, имена полные | 200 | приведены к каноническому порядку |
| сломанный JSON | 422 | отказ |
| поле прогноза | — | ключ `prediction` есть и равен `null`; ключа `predictions` и 24 вероятностей нет |

## 7. Existing endpoints — PASS

На рабочем дереве:

- `POST /api/ecg/predict` по готовому CSV-объекту отвечает 200 и 24 объектами с полем `probability`.
- `POST /api/ecg/raw` отвечает 501, `features: null`, `prediction: null`, `status: NOT_PROVEN`.
- Reference CSV numerical path совпадает с исходным inference, раздел 3.
- `POST /api/ecg/raw/features` не вызывает `predict_features`.

На чистом commit эти маршруты не стартуют из-за дефекта раздела 1. Контракт predict в blob `ensemble.py` commit совпадает с `main`.

## 8. Frontend — PASS

Панель raw называется `RAW ECG → FEATURE COMPATIBILITY`. Текст: `Reconstructed 531-feature representation` и «Это не опубликованные признаки PTB-XL+». Видно `Exact PTB-XL+ compatibility: NOT PROVEN`. Кнопка проверки контракта не рисует SCP-коды и не вызывает `/api/ecg/predict`. Счётчик `features reconstructed` — это число статусов реестра, не число вычисленных значений. Рядом сказано, что ансамбль не запускается и неизвестные колонки остаются пустыми.

## 9. Tests — FAIL

Рабочее дерево, весь каталог `tests`:

```text
PYTHONPATH=. .venv/bin/python -m pytest tests -q --tb=no
29 passed, 0 failed, 4 warnings
```

Это не доказательство 531 вычисленных значений. Матрица `step13_test_matrix.csv` сравнивает только статус семьи со статусом реестра. В рантайме вычислено 0 из 531.

Чистый commit:

```text
git archive 093ebb1 | tar -x -C /tmp/step14-clean
PYTHONPATH=/tmp/step14-clean .venv/bin/python -m pytest tests -q --tb=line
```

Сбор прерван: `tests/test_feature_compatibility_00513.py` и `tests/test_service.py` падают с `ImportError` на `predict_features`. Набор commit сам себя не прогоняет.

## 10. Документация — FAIL

`experiments/raw_to_531/step13_summary.json` согласован с кодом по статусу и составу семей: `NOT_PROVEN`, 531, `raw_inference.supported = false`, суммы 240+180+36+36+36+3. `docs/STEP13_COMPATIBILITY_LAYER.md` повторяет те же статусы и запрет отдавать сырой вектор в ансамбль. `RAW_TO_531_STATUS` ни в одном из этих файлов не переведён в `PROVEN`.

Противоречие: начало `docs/RAW_TO_531_STATUS.md` по-прежнему говорит, что путь raw → 531 не реализован и что сырой HTTP-ответ — только 501. Ниже абзац шага 13 и `docs/STEP13_COMPATIBILITY_LAYER.md` описывают слой совместимости и `POST /api/ecg/raw/features`. Статус при этом один и тот же, `NOT_PROVEN`.

`step13_feature_status.csv` не помечен как forensic-таблица. Колонка `value_00513` заполнена для 456 reconstructed-строк, хотя API на тех же именах возвращает null.

`step13_test_matrix.csv` честно пишет `values are not claimed exact`, но зелёный `passed` относится только к статусу семьи.

## Дефекты

1. Высокий. Commit `093ebb1` несамодостаточен: API и новые тесты импортируют функции, которые лежат только в незакоммиченном `ensemble.py` и `schema.py`.
2. Высокий для приёмки ветки. Рабочее дерево грязное. В нём же незакоммиченные правки inference-модуля. В merge это нельзя брать молча.
3. Средний. `value_00513` в status CSV легко прочитать как выход нового слоя. Это числа forensic-разбора, не runtime.
4. Низкий. `docs/RAW_TO_531_STATUS.md` в начале не упоминает новый endpoint, хотя дальше описывает шаг 13.
5. Низкий. Ответ raw features содержит `"prediction": null`. Вектора из 24 вероятностей там нет.
6. Низкий, объём commit. В commit попал `backend/vision.py`. Сырой маршрут его не вызывает. При заданном ключе этот модуль умеет внешний вызов; к compatibility layer он не относится.

## Что исправить

Код в этом аудите не исправлялся.

1. Собрать в один commit `backend/app.py` и те определения `predict_features`, `service_payload`, `read_feature_mapping`, без которых он не импортируется. Повторить `import backend.app` и `pytest` на чистом checkout.
2. Отделить этот commit от остальных незакоммиченных forensic-файлов и от правок `ensemble.py`, которые не входят в формулу среднего. Перед любым новым commit просмотреть diff `ensemble.py`: там только отказ на NaN и обёртка входа, но файл inference всё равно должен быть просмотрен явно.
3. В `RAW_TO_531_STATUS.md` согласовать вступительные пункты с наличием compatibility endpoint. Константу `NOT_PROVEN` не менять.
4. Подписать `value_00513` как forensic-значение, чтобы его не путали с null-вектором API.
5. Не сливать ветку в `main`, пока чистый commit не проходит свой набор тестов.

## Можно ли считать STEP 13 технически завершённым

Нет.

В рабочем дереве граница на месте: reference CSV идёт в прежний ансамбль и совпадает с исходным inference с max absolute difference `0.0`; raw ECG остаётся в compatibility layer; пустые признаки не заменяются и в ансамбль не уходят; `RAW_TO_531_STATUS = NOT_PROVEN`.

Заявленный commit `093ebb1` эту реализацию не содержит целиком и не проходит собственные тесты. Пока чистый checkout не воспроизводит шаг, завершение относится к незакоммиченному дереву, а не к ветке.
