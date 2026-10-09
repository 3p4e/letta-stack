<!--HEADERDATA
mk_title: Запис за извршување на OQ — температурно мапирање — L01 (пример)
en_title: OQ Execution Record — Temperature Mapping — L01 (example)
code: QASOP_0XX_A03
version: 01
doctype: FORM
parent: QASOP_0XX
orient: landscape
-->

ПРИМЕР / СИМУЛАЦИЈА — не е запис. Сите внесени податоци се во загради: сино — од нашите записи или пресметани; виолетово — пример, да се потврди; портокалово — се внесува на денот. ||| EXAMPLE / SIMULATION — not a record. Every entry is in brackets: blue — from our records or calculated; purple — example, to be confirmed; orange — entered on the day.

# 1 Идентификација | Identification
[[FORM:grid]]
Код на рутата ||| Lane code ||| [L01]
Протокол (QASOP_0XX_A02) бр. ||| Protocol (QASOP_0XX_A02) No. ||| [TVP-L01-26]
Превозник / возило (регистарски број) ||| Carrier / vehicle (registration) ||| [Kuehne + Nagel (предвиден) | Kuehne + Nagel (provisional)] · [ ]
Контрола на температура ||| Temperature control ||| ☐ Активна | Active   ☐ Пасивна | Passive
Палети G / M ||| Pallets L / S ||| [29 / 0 (симулиран товар) | 29 / 0 (simulated load)]
Сезона ||| Season ||| [есен (октомври) | autumn (October)]
Опсег ||| Range ||| [15–25 °C, RH ≤ 60 %]
Датум на извршување ||| Execution date ||| [13.10.2026 – 15.10.2026]
[[/FORM]]

# 2 Логери и позиции | Loggers and positions
## 2.1 USB логери во товарниот простор (10) | USB loggers in the load space (10)
[[TABLE]]
Позиција~~Position ||| Опис~~Description ||| Сериски број~~Serial No. ||| Калибрација важи до~~Calibration due ||| Проверка пред (Δ °C)~~Check before (Δ °C) ||| Проверка после (Δ °C)~~Check after (Δ °C)
P1 ||| Горе напред лево (кон кабината)~~Top front left (cab side) ||| [ ] ||| [ ] ||| [ ] ||| [ ]
P2 ||| Горе напред десно~~Top front right ||| [ ] ||| [ ] ||| [ ] ||| [ ]
P3 ||| Горе назад лево (кон вратите)~~Top rear left (door side) ||| [ ] ||| [ ] ||| [ ] ||| [ ]
P4 ||| Горе назад десно (кон вратите)~~Top rear right (door side) ||| [ ] ||| [ ] ||| [ ] ||| [ ]
P5 ||| Долу напред лево~~Bottom front left ||| [ ] ||| [ ] ||| [ ] ||| [ ]
P6 ||| Долу напред десно~~Bottom front right ||| [ ] ||| [ ] ||| [ ] ||| [ ]
P7 ||| Долу назад лево (кон вратите)~~Bottom rear left (door side) ||| [ ] ||| [ ] ||| [ ] ||| [ ]
P8 ||| Долу назад десно (кон вратите)~~Bottom rear right (door side) ||| [ ] ||| [ ] ||| [ ] ||| [ ]
P9 ||| Геометриски центар~~Geometric centre ||| [ ] ||| [ ] ||| [ ] ||| [ ]
P10 ||| Амбиент (надвор, во сенка)~~Ambient (outside, shaded) ||| [ ] ||| [ ] ||| [ ] ||| [ ]
[[/TABLE]]

## 2.2 Логери за еднократна употреба во палетите (тестови со товар) | Single-use loggers in the pallets (loaded tests)
[[TABLE]]
ID на палета~~Pallet ID ||| Тип G/M~~Type L/S ||| Позиција во возилото~~Position in the vehicle ||| Е1 — горен слој, кон вратите (сер. бр.)~~E1 — top layer, door side (serial) ||| Е2 — долен слој, центар (сер. бр.)~~E2 — bottom layer, centre (serial) ||| Сертификат на серијата~~Lot certificate
[OQ-P01] ||| [G] ||| [ред 1, лево | row 1, left] ||| [ ] ||| [ ] ||| [ ]
[OQ-P02] ||| [G] ||| [ред 1, десно | row 1, right] ||| [ ] ||| [ ] ||| [ ]
[OQ-P03] ||| [G] ||| [ред 2, лево | row 2, left] ||| [ ] ||| [ ] ||| [ ]
[OQ-P04] ||| [G] ||| [ред 2, десно | row 2, right] ||| [ ] ||| [ ] ||| [ ]
[OQ-P05] ||| [G] ||| [ред 3, лево | row 3, left] ||| [ ] ||| [ ] ||| [ ]
[OQ-P06] ||| [G] ||| [ред 3, десно | row 3, right] ||| [ ] ||| [ ] ||| [ ]
[OQ-P07] ||| [G] ||| [ред 4, лево | row 4, left] ||| [ ] ||| [ ] ||| [ ]
[OQ-P08] ||| [G] ||| [ред 4, десно | row 4, right] ||| [ ] ||| [ ] ||| [ ]
[OQ-P09] ||| [G] ||| [ред 5, лево | row 5, left] ||| [ ] ||| [ ] ||| [ ]
[OQ-P10] ||| [G] ||| [ред 5, десно | row 5, right] ||| [ ] ||| [ ] ||| [ ]
[OQ-P11] ||| [G] ||| [ред 6, лево | row 6, left] ||| [ ] ||| [ ] ||| [ ]
[OQ-P12] ||| [G] ||| [ред 6, десно | row 6, right] ||| [ ] ||| [ ] ||| [ ]
[OQ-P13] ||| [G] ||| [ред 7, лево | row 7, left] ||| [ ] ||| [ ] ||| [ ]
[OQ-P14] ||| [G] ||| [ред 7, десно | row 7, right] ||| [ ] ||| [ ] ||| [ ]
[OQ-P15] ||| [G] ||| [ред 8, лево | row 8, left] ||| [ ] ||| [ ] ||| [ ]
[OQ-P16] ||| [G] ||| [ред 8, десно | row 8, right] ||| [ ] ||| [ ] ||| [ ]
[OQ-P17] ||| [G] ||| [ред 9, лево | row 9, left] ||| [ ] ||| [ ] ||| [ ]
[OQ-P18] ||| [G] ||| [ред 9, десно | row 9, right] ||| [ ] ||| [ ] ||| [ ]
[OQ-P19] ||| [G] ||| [ред 10, лево | row 10, left] ||| [ ] ||| [ ] ||| [ ]
[OQ-P20] ||| [G] ||| [ред 10, десно | row 10, right] ||| [ ] ||| [ ] ||| [ ]
[OQ-P21] ||| [G] ||| [ред 11, лево | row 11, left] ||| [ ] ||| [ ] ||| [ ]
[OQ-P22] ||| [G] ||| [ред 11, десно | row 11, right] ||| [ ] ||| [ ] ||| [ ]
[OQ-P23] ||| [G] ||| [ред 12, лево | row 12, left] ||| [ ] ||| [ ] ||| [ ]
[OQ-P24] ||| [G] ||| [ред 12, десно | row 12, right] ||| [ ] ||| [ ] ||| [ ]
[OQ-P25] ||| [G] ||| [ред 13, лево | row 13, left] ||| [ ] ||| [ ] ||| [ ]
[OQ-P26] ||| [G] ||| [ред 13, десно | row 13, right] ||| [ ] ||| [ ] ||| [ ]
[OQ-P27] ||| [G] ||| [ред 14, лево | row 14, left] ||| [ ] ||| [ ] ||| [ ]
[OQ-P28] ||| [G] ||| [ред 14, десно | row 14, right] ||| [ ] ||| [ ] ||| [ ]
[OQ-P29] ||| [G] ||| [ред 15, лево | row 15, left] ||| [ ] ||| [ ] ||| [ ]
[[/TABLE]]

# 3 Резултати по тест | Results per test
[[TABLE]]
Тест~~Test ||| Почеток~~Start ||| Крај~~End ||| Амбиент мин./макс. (°C)~~Ambient min./max. (°C) ||| Воздух мин./макс. (°C) / позиција~~Air min./max. (°C) / position ||| Палети мин./макс. (°C) / логер~~Pallets min./max. (°C) / logger ||| MKT (°C) ||| Време надвор (мин)~~Time out (min) ||| Критериум исполнет~~Criterion met
OQ-1 Празно возило~~Empty vehicle ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| — ||| [ ] ||| [ ] ||| [ ]
OQ-2 Полно ≥ 125 % времетраење~~Loaded ≥ 125 % duration ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ]
OQ-3 Врата 2 × 5 мин~~Door 2 × 5 min ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ]
OQ-4 Прекин на напојување (само активна; ☐ N/A)~~Power interruption (active only; ☐ N/A) ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ]
OQ-5 Летно мапирање со товар~~Summer mapping, loaded ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ]
OQ-6 Зимско мапирање со товар~~Winter mapping, loaded ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ]
[[/TABLE]]
[[FORM:grid]]
Време до опсег по вклучување (мин; само активна) ||| Time to range after start (min; active only) ||| [ ]
Враќање во опсег по врата 1 / врата 2 (мин) ||| Return to range after door 1 / door 2 (min) ||| [ ]
Време на задржување (мин) ||| Hold time (min) ||| [ ]
Жешка точка (воздух / палета) ||| Hot spot (air / pallet) ||| [ ]
Студена точка (воздух / палета) ||| Cold spot (air / pallet) ||| [ ]
Рутинска позиција: USB логер ||| Routine position: USB logger ||| [ ]
Рутинска позиција: логер во палета (Е1 / Е2) ||| Routine position: pallet logger (E1 / E2) ||| [ ]
[[/FORM]]
Необработените податоци (изворна датотека од секој USB логер со SHA-256 и PDF-извештај од секој логер за еднократна употреба, со сериски број и временски печат) се прилагаат и се чуваат со овој запис; печатените вредности мора да се пресметаат од нив. ||| The raw data (original file of each USB logger with SHA-256 and the PDF report of each single-use logger, with serial number and timestamps) are attached and retained with this record; the printed values must be calculated from them.

# 4 Отстапувања | Deviations
[[TABLE]]
Тест~~Test ||| Опис~~Description ||| Отстапување бр.~~Deviation No. ||| Решение~~Resolution ||| Тест повторен~~Test repeated
[ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ]
[[/TABLE]]

# 5 Потписи по тест | Sign-off per test
[[TABLE]]
Тест~~Test ||| Извршил~~Executed by ||| Датум~~Date ||| Проверил (второ лице)~~Verified by (second person) ||| Датум~~Date
OQ-1 ||| [ ] ||| [ ] ||| [ ] ||| [ ]
OQ-2 ||| [ ] ||| [ ] ||| [ ] ||| [ ]
OQ-3 ||| [ ] ||| [ ] ||| [ ] ||| [ ]
OQ-4 ||| [ ] ||| [ ] ||| [ ] ||| [ ]
OQ-5 ||| [ ] ||| [ ] ||| [ ] ||| [ ]
OQ-6 ||| [ ] ||| [ ] ||| [ ] ||| [ ]
[[/TABLE]]
[[FORM]]
Заклучок за OQ ||| OQ conclusion ||| ☐ Сите критериуми исполнети — продолжи кон PQ | All criteria met — proceed to PQ   ☐ Не се исполнети — отстапување | Not met — deviation
[[/FORM]]
[[TABLE]]
Улога~~Role ||| Име~~Name ||| Датум~~Date ||| Потпис~~Signature
Одобрил продолжување кон PQ (QA)~~Released to PQ (QA) ||| [ ] ||| [ ] ||| [ ]
[[/TABLE]]
