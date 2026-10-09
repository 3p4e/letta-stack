<!--HEADERDATA
mk_title: Запис за извршување на PQ пратка — PQ-1 = Т1 (пример)
en_title: PQ Shipment Execution Record — PQ-1 = T1 (example)
code: QASOP_0XX_A04
version: 01
doctype: FORM
parent: QASOP_0XX
orient: portrait
-->

ПРИМЕР / СИМУЛАЦИЈА — пополнето со податоците што ги имаме и со пресметките од листот за калкулација; не е запис. Мерењата, потписите, броевите на пломби и логери и податоците што се дознаваат на денот се оставени празни. ||| EXAMPLE / SIMULATION — filled with the data we hold and the calculations on the calculation sheet; not a record. Measurements, signatures, seal and logger numbers and data known only on the day are left blank.

# 1 Идентификација | Identification
[[FORM:grid]]
Код на рутата ||| Lane code ||| L01
Протокол бр. ||| Protocol No. ||| TVP-L01-26
PQ пратка ||| PQ shipment ||| ☒ 1   ☐ 2   ☐ 3
UTID (WHSOP_003) ||| UTID (WHSOP_003) ||| TR-20261020-001
Датум ||| Date ||| 20.10.2026
Сезона ||| Season ||| есен (октомври) | autumn (October)
Амбиент мин./макс. (°C) ||| Ambient min./max. (°C) ||| _
Палети G / M ||| Pallets L / S ||| 20 / 0
Превозник / возило ||| Carrier / vehicle ||| Kuehne + Nagel (предвиден, да се потврди) / ______
Контрола на температура ||| Temperature control ||| ☐ Активна | Active   ☐ Пасивна | Passive
Полициско придружување потврдено (МВР бр.) ||| Police escort confirmed (MoIA No.) ||| _
[[/FORM]]
[[FORM]]
Товар ||| Load ||| ☒ Реален производ | Real product   ☐ Симулиран товар (иста маса и конфигурација на палети) | Simulated load (same mass and pallet configuration)
[[/FORM]]

# 2 Логери | Loggers
## 2.1 USB логери | USB loggers
[[TABLE]]
Позиција~~Position ||| Сериски број~~Serial No. ||| Калибрација важи до~~Calibration due ||| Мин. (°C) ||| Макс. (°C) ||| MKT (°C) ||| Макс. RH (%) ||| Време надвор (мин)~~Time out (min)
Жешка точка од OQ~~OQ hot spot |||  |||  |||  |||  |||  |||  ||| 
Студена точка од OQ~~OQ cold spot |||  |||  |||  |||  |||  |||  ||| 
Амбиент (надвор)~~Ambient (outside) |||  |||  |||  |||  |||  |||  ||| 
[[/TABLE]]

## 2.2 Логери за еднократна употреба во палетите | Single-use loggers in the pallets
[[TABLE]]
ID на палета~~Pallet ID ||| Тип G/M~~Type L/S ||| Е1 сер. бр.~~E1 serial ||| Е1 мин./макс. (°C)~~E1 min./max. (°C) ||| Е2 сер. бр.~~E2 serial ||| Е2 мин./макс. (°C)~~E2 min./max. (°C) ||| Аларм~~Alarm ||| MKT (°C)
TR-20261020-001-P01 ||| G |||  |||  |||  |||  |||  ||| 
TR-20261020-001-P02 ||| G |||  |||  |||  |||  |||  ||| 
TR-20261020-001-P03 ||| G |||  |||  |||  |||  |||  ||| 
TR-20261020-001-P04 ||| G |||  |||  |||  |||  |||  ||| 
TR-20261020-001-P05 ||| G |||  |||  |||  |||  |||  ||| 
TR-20261020-001-P06 ||| G |||  |||  |||  |||  |||  ||| 
TR-20261020-001-P07 ||| G |||  |||  |||  |||  |||  ||| 
TR-20261020-001-P08 ||| G |||  |||  |||  |||  |||  ||| 
TR-20261020-001-P09 ||| G |||  |||  |||  |||  |||  ||| 
TR-20261020-001-P10 ||| G |||  |||  |||  |||  |||  ||| 
TR-20261020-001-P11 ||| G |||  |||  |||  |||  |||  ||| 
TR-20261020-001-P12 ||| G |||  |||  |||  |||  |||  ||| 
TR-20261020-001-P13 ||| G |||  |||  |||  |||  |||  ||| 
TR-20261020-001-P14 ||| G |||  |||  |||  |||  |||  ||| 
TR-20261020-001-P15 ||| G |||  |||  |||  |||  |||  ||| 
TR-20261020-001-P16 ||| G |||  |||  |||  |||  |||  ||| 
TR-20261020-001-P17 ||| G |||  |||  |||  |||  |||  ||| 
TR-20261020-001-P18 ||| G |||  |||  |||  |||  |||  ||| 
TR-20261020-001-P19 ||| G |||  |||  |||  |||  |||  ||| 
TR-20261020-001-P20 ||| G |||  |||  |||  |||  |||  ||| 
[[/TABLE]]

# 3 Тек на пратката | Shipment timeline
[[TABLE]]
Настан~~Event ||| Време~~Time ||| Забелешка~~Remark
Предкондиционирање почнато (само активна)~~Pre-conditioning started (active only) |||  ||| 
Палетите завиткани, логерите активирани~~Pallets wrapped, loggers started |||  ||| 
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
1 ||| Сите логери во палетите во опсег во текот на целото патување~~All pallet loggers within range throughout the journey |||  |||  ||| 
2 ||| MKT во опсег~~MKT within range |||  |||  ||| 
3 ||| Макс. RH ≤ 60 % (каде е применливо)~~Max. RH ≤ 60 % (where applicable) |||  |||  ||| 
4 ||| Времетраење ≤ квалификуваното максимално~~Duration ≤ qualified maximum |||  |||  ||| 
5 ||| Пломбите, лентите и завиткувањето цели~~Seals, tapes and wrapping intact |||  |||  ||| 
6 ||| Ланецот на надзор (WHSOP_003_A04) комплетен~~Chain of custody (WHSOP_003_A04) complete |||  |||  ||| 
7 ||| Пакувањето без оштетување~~Packaging undamaged |||  |||  ||| 
8 ||| Контролните јавувања ја потврдуваат одобрената рута; придружувањето присутно~~Check-in calls confirm the approved route; escort present |||  |||  ||| 
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
