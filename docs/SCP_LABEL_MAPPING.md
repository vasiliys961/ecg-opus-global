# Подписи 24 выходов

Индекс и код SCP совпадают с обученной сетью. Менять их нельзя.

`canonical label` — описание из `scp_statements.csv` PTB-XL 1.0.3. `Russian label` — строка из `ecg_web_up`, поле `DIAGNOSIS_TRANSLATION`. В API оба поля возвращаются вместе: `label_en` и `label_ru`.

| index | SCP code | canonical label | Russian label |
| ---: | --- | --- | --- |
| 0 | SR | sinus rhythm | Синусовый ритм |
| 1 | NORM | normal ECG | Нормальная ЭКГ |
| 2 | ABQRS | abnormal QRS | Аберрантный QRS комплекс |
| 3 | IMI | inferior myocardial infarction | Инфаркт миокарда (нижняя стенка) |
| 4 | ASMI | anteroseptal myocardial infarction | Инфаркт миокарда (переднеперегородочная стенка) |
| 5 | LVH | left ventricular hypertrophy | Гипертрофия левого желудочка |
| 6 | NDT | non-diagnostic T abnormalities | Неспецифические изменения ST-T |
| 7 | LAFB | left anterior fascicular block | Блокада передней ветви левой ножки пучка Гиса |
| 8 | AFIB | atrial fibrillation | Фибрилляция предсердий |
| 9 | PVC | ventricular premature complex | Преждевременное желудочковое сокращение |
| 10 | IRBBB | incomplete right bundle branch block | Неполная блокада правой ножки пучка Гиса |
| 11 | VCLVH | voltage criteria (QRS) for left ventricular hypertrophy | Гипертрофия желудочков или левого желудочка |
| 12 | STACH | sinus tachycardia | Синусовая тахикардия |
| 13 | IVCD | non-specific intraventricular conduction disturbance (block) | Внутрижелудочковая блокада |
| 14 | SARRH | sinus arrhythmia | Синусовый ритм с аберрантным проведением |
| 15 | ISCAL | ischemic in anterolateral leads | Ишемия миокарда (нижняя стенка) |
| 16 | SBRAD | sinus bradycardia | Синусовая брадикардия |
| 17 | QWAVE | Q waves present | Патологический Q-волновой комплекс |
| 18 | CRBBB | complete right bundle branch block | Полная блокада правой ножки пучка Гиса |
| 19 | CLBBB | complete left bundle branch block | Полная блокада левой ножки пучка Гиса |
| 20 | ILMI | inferolateral myocardial infarction | Инфаркт миокарда (нижнебоковая стенка) |
| 21 | LOWT | low amplitude T-waves | Низкий T-волновой комплекс |
| 22 | PAC | atrial premature complex | Преждевременное предсердное сокращение |
| 23 | AMI | anterior myocardial infarction | Острый инфаркт миокарда (передняя стенка) |

## Compatibility mapping

Русская подпись сохранена как в старом проекте. Где она расходится с каноническим SCP, в ответе модели код остаётся прежним, а отличие видно по паре подписей.

| SCP code | canonical label | Russian label из ecg_web_up | В чём расхождение |
| --- | --- | --- | --- |
| NDT | non-diagnostic T abnormalities | Неспецифические изменения ST-T | каноническое описание про зубец T |
| VCLVH | voltage criteria (QRS) for left ventricular hypertrophy | Гипертрофия желудочков или левого желудочка | это вольтажный критерий QRS, не общий диагноз гипертрофии |
| SARRH | sinus arrhythmia | Синусовый ритм с аберрантным проведением | канонически синусовая аритмия |
| ISCAL | ischemic in anterolateral leads | Ишемия миокарда (нижняя стенка) | нижняя стенка в SCP — код ISCI |
| AMI | anterior myocardial infarction | Острый инфаркт миокарда (передняя стенка) | в каноническом описании нет слова «острый» |

Машинный список: `ecg_engine/scp.py`.
