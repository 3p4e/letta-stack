<!--HEADERDATA
mk_title: Запис за извршување на PQ пратка
en_title: PQ Shipment Execution Record
code: QASOP_0XX_A04
version: 01
doctype: FORM
parent: QASOP_0XX
orient: portrait
-->

# 1 Идентификација | Identification
[[FORM:grid]]
Код на рутата ||| Lane code ||| L__
Протокол бр. ||| Protocol No. ||| _
PQ пратка ||| PQ shipment ||| ☐ 1   ☐ 2   ☐ 3
UTID (WHSOP_003) ||| UTID (WHSOP_003) ||| TR-________-___
Датум ||| Date ||| _
Сезона ||| Season ||| _
Амбиент мин./макс. (°C) ||| Ambient min./max. (°C) ||| _
[[/FORM]]
[[FORM]]
Товар ||| Load ||| ☐ Реален производ | Real product   ☐ Симулиран товар (иста термичка маса и конфигурација) | Simulated load (same thermal mass and configuration)
[[/FORM]]

# 2 Логери | Loggers
[[TABLE]]
Позиција~~Position ||| Сериски број~~Serial No. ||| Калибрација важи до~~Calibration due ||| Мин. (°C) ||| Макс. (°C) ||| MKT (°C) ||| Макс. RH (%) ||| Време надвор (мин)~~Time out (min)
Рутинска (жешка/студена точка од OQ)~~Routine (OQ hot/cold spot) |||  |||  |||  |||  |||  |||  ||| 
Центар на товарот~~Load centre |||  |||  |||  |||  |||  |||  ||| 
Кај вратата~~At the door |||  |||  |||  |||  |||  |||  ||| 
Амбиент~~Ambient |||  |||  |||  |||  |||  |||  ||| 
[[/TABLE]]

# 3 Тек на пратката | Shipment timeline
[[TABLE]]
Настан~~Event ||| Време~~Time ||| Забелешка~~Remark
Предкондиционирање почнато~~Pre-conditioning started |||  ||| 
Товарање завршено, вратата затворена~~Loading complete, door closed |||  ||| 
Поаѓање~~Departure |||  ||| 
Застанувања (место, траење)~~Stops (place, duration) |||  ||| 
Пристигнување~~Arrival |||  ||| 
Отворање и истовар~~Opening and unloading |||  ||| 
Вкупно времетраење (h:min)~~Total duration (h:min) |||  ||| 
[[/TABLE]]

# 4 Критериуми за прифаќање | Acceptance criteria
[[TABLE]]
№ ||| Критериум~~Criterion ||| Резултат~~Result ||| Да~~Yes ||| Не~~No
1 ||| Сите логери во опсег во текот на целото патување~~All loggers within range throughout the journey |||  |||  ||| 
2 ||| MKT во опсег~~MKT within range |||  |||  ||| 
3 ||| Макс. RH ≤ 60 % (каде е применливо)~~Max. RH ≤ 60 % (where applicable) |||  |||  ||| 
4 ||| Времетраење ≤ квалификуваното максимално~~Duration ≤ qualified maximum |||  |||  ||| 
5 ||| Пломбите цели, броевите одговараат~~Seals intact, numbers match |||  |||  ||| 
6 ||| Ланецот на надзор (WHSOP_003_A04) комплетен~~Chain of custody (WHSOP_003_A04) complete |||  |||  ||| 
7 ||| Пакувањето без оштетување~~Packaging undamaged |||  |||  ||| 
8 ||| GPS ја потврдува одобрената рута~~GPS confirms approved route |||  |||  ||| 
[[/TABLE]]
[[FORM]]
Отстапувања (број и опис) ||| Deviations (No. and description) ||| _
[[/FORM]]
[[FORM]]
Резултат на пратката ||| Shipment result ||| ☐ Ги исполнува критериумите | Meets the criteria   ☐ Не ги исполнува | Does not meet the criteria
[[/FORM]]

# 5 Потписи | Signatures
[[TABLE]]
Улога~~Role ||| Име~~Name ||| Датум~~Date ||| Потпис~~Signature
Извршил и внел податоци (тим за валидација)~~Executed and entered data (validation team) |||  |||  ||| 
Проверил податоците (второ лице)~~Verified the data (second person) |||  |||  ||| 
Прегледал (QA)~~Reviewed (QA) |||  |||  ||| 
[[/TABLE]]
