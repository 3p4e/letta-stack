<!--HEADERDATA
mk_title: Запис за извршување на OQ — температурно мапирање
en_title: OQ Execution Record — Temperature Mapping
code: QASOP_0XX_A03
version: 01
doctype: FORM
parent: QASOP_0XX
orient: landscape
-->

# 1 Идентификација | Identification
[[FORM:grid]]
Код на рутата ||| Lane code ||| L__
Протокол (QASOP_0XX_A02) бр. ||| Protocol (QASOP_0XX_A02) No. ||| _
Возило (регистарски број) ||| Vehicle (registration) ||| _
Контрола на температура ||| Temperature control ||| ☐ Активна | Active   ☐ Пасивна | Passive
Палети G / M ||| Pallets L / S ||| _
Сезона ||| Season ||| _
Опсег ||| Range ||| _
Датум на извршување ||| Execution date ||| _
[[/FORM]]

# 2 Логери и позиции | Loggers and positions
## 2.1 USB логери во товарниот простор (10) | USB loggers in the load space (10)
[[TABLE]]
Позиција~~Position ||| Опис~~Description ||| Сериски број~~Serial No. ||| Калибрација важи до~~Calibration due ||| Проверка пред (Δ °C)~~Check before (Δ °C) ||| Проверка после (Δ °C)~~Check after (Δ °C)
P1 ||| Горе напред лево (кон кабината)~~Top front left (cab side) |||  |||  |||  ||| 
P2 ||| Горе напред десно~~Top front right |||  |||  |||  ||| 
P3 ||| Горе назад лево (кон вратите)~~Top rear left (door side) |||  |||  |||  ||| 
P4 ||| Горе назад десно (кон вратите)~~Top rear right (door side) |||  |||  |||  ||| 
P5 ||| Долу напред лево~~Bottom front left |||  |||  |||  ||| 
P6 ||| Долу напред десно~~Bottom front right |||  |||  |||  ||| 
P7 ||| Долу назад лево (кон вратите)~~Bottom rear left (door side) |||  |||  |||  ||| 
P8 ||| Долу назад десно (кон вратите)~~Bottom rear right (door side) |||  |||  |||  ||| 
P9 ||| Геометриски центар~~Geometric centre |||  |||  |||  ||| 
P10 ||| Амбиент (надвор, во сенка)~~Ambient (outside, shaded) |||  |||  |||  ||| 
[[/TABLE]]

## 2.2 Логери за еднократна употреба во палетите (тестови со товар) | Single-use loggers in the pallets (loaded tests)
[[TABLE]]
ID на палета~~Pallet ID ||| Тип G/M~~Type L/S ||| Позиција во возилото~~Position in the vehicle ||| Е1 — горен слој, кон вратите (сер. бр.)~~E1 — top layer, door side (serial) ||| Е2 — долен слој, центар (сер. бр.)~~E2 — bottom layer, centre (serial) ||| Сертификат на серијата~~Lot certificate
 |||  |||  |||  |||  ||| 
 |||  |||  |||  |||  ||| 
 |||  |||  |||  |||  ||| 
 |||  |||  |||  |||  ||| 
 |||  |||  |||  |||  ||| 
 |||  |||  |||  |||  ||| 
[[/TABLE]]

# 3 Резултати по тест | Results per test
[[TABLE]]
Тест~~Test ||| Почеток~~Start ||| Крај~~End ||| Амбиент мин./макс. (°C)~~Ambient min./max. (°C) ||| Воздух мин./макс. (°C) / позиција~~Air min./max. (°C) / position ||| Палети мин./макс. (°C) / логер~~Pallets min./max. (°C) / logger ||| MKT (°C) ||| Време надвор (мин)~~Time out (min) ||| Критериум исполнет~~Criterion met
OQ-1 Празно возило~~Empty vehicle |||  |||  |||  |||  ||| — |||  |||  ||| 
OQ-2 Полно ≥ 125 % времетраење~~Loaded ≥ 125 % duration |||  |||  |||  |||  |||  |||  |||  ||| 
OQ-3 Врата 2 × 5 мин~~Door 2 × 5 min |||  |||  |||  |||  |||  |||  |||  ||| 
OQ-4 Прекин на напојување (само активна; ☐ N/A)~~Power interruption (active only; ☐ N/A) |||  |||  |||  |||  |||  |||  |||  ||| 
OQ-5 Летно мапирање со товар~~Summer mapping, loaded |||  |||  |||  |||  |||  |||  |||  ||| 
OQ-6 Зимско мапирање со товар~~Winter mapping, loaded |||  |||  |||  |||  |||  |||  |||  ||| 
[[/TABLE]]
[[FORM:grid]]
Време до опсег по вклучување (мин; само активна) ||| Time to range after start (min; active only) ||| _
Враќање во опсег по врата 1 / врата 2 (мин) ||| Return to range after door 1 / door 2 (min) ||| _
Време на задржување (мин) ||| Hold time (min) ||| _
Жешка точка (воздух / палета) ||| Hot spot (air / pallet) ||| _
Студена точка (воздух / палета) ||| Cold spot (air / pallet) ||| _
Рутинска позиција: USB логер ||| Routine position: USB logger ||| _
Рутинска позиција: логер во палета (Е1 / Е2) ||| Routine position: pallet logger (E1 / E2) ||| _
[[/FORM]]
Необработените податоци (изворна датотека од секој USB логер со SHA-256 и PDF-извештај од секој логер за еднократна употреба, со сериски број и временски печат) се прилагаат и се чуваат со овој запис; печатените вредности мора да се пресметаат од нив. ||| The raw data (original file of each USB logger with SHA-256 and the PDF report of each single-use logger, with serial number and timestamps) are attached and retained with this record; the printed values must be calculated from them.

# 4 Отстапувања | Deviations
[[TABLE]]
Тест~~Test ||| Опис~~Description ||| Отстапување бр.~~Deviation No. ||| Решение~~Resolution ||| Тест повторен~~Test repeated
 |||  |||  |||  ||| 
[[/TABLE]]

# 5 Потписи по тест | Sign-off per test
[[TABLE]]
Тест~~Test ||| Извршил~~Executed by ||| Датум~~Date ||| Проверил (второ лице)~~Verified by (second person) ||| Датум~~Date
OQ-1 |||  |||  |||  ||| 
OQ-2 |||  |||  |||  ||| 
OQ-3 |||  |||  |||  ||| 
OQ-4 |||  |||  |||  ||| 
OQ-5 |||  |||  |||  ||| 
OQ-6 |||  |||  |||  ||| 
[[/TABLE]]
[[FORM]]
Заклучок за OQ ||| OQ conclusion ||| ☐ Сите критериуми исполнети — продолжи кон PQ | All criteria met — proceed to PQ   ☐ Не се исполнети — отстапување | Not met — deviation
[[/FORM]]
[[TABLE]]
Улога~~Role ||| Име~~Name ||| Датум~~Date ||| Потпис~~Signature
Одобрил продолжување кон PQ (QA)~~Released to PQ (QA) |||  |||  ||| 
[[/TABLE]]
