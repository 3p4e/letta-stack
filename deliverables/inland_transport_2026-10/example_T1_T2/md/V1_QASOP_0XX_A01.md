<!--HEADERDATA
mk_title: План за валидација и процена на ризик на транспортна рута — L01 (пример)
en_title: Lane Validation Plan and Risk Assessment — L01 (example)
code: QASOP_0XX_A01
version: 01
doctype: FORM
parent: QASOP_0XX
orient: portrait
-->

ПРИМЕР / СИМУЛАЦИЈА — пополнето со податоците што ги имаме и со пресметките од листот за калкулација; не е запис. Мерењата, потписите, броевите на пломби и логери и податоците што се дознаваат на денот се оставени празни. ||| EXAMPLE / SIMULATION — filled with the data we hold and the calculations on the calculation sheet; not a record. Measurements, signatures, seal and logger numbers and data known only on the day are left blank.

# 1 Идентификација на рутата | Lane identification
[[FORM:grid]]
Код на рутата ||| Lane code ||| L01
Број на проект за валидација ||| Validation project No. ||| TVP-L01-26
Место на испраќање ||| Dispatch point ||| Којлија 1043, Петровец | Kojlija 1043, Petrovec
Место на прием ||| Receipt point ||| Versa (купувач според листата за продажба) | Versa (buyer per the sale list); [адреса — да се внесе | address — to be entered]
Опис на патеката ||| Route description ||| _
Растојание (km) ||| Distance (km) ||| _
Нормално времетраење (h:min) ||| Normal duration (h:min) ||| _
Максимално времетраење со застои (h:min) ||| Maximum duration with delays (h:min) ||| _
Превозник ||| Carrier ||| Kuehne + Nagel (предвиден, да се потврди) | Kuehne + Nagel (provisional, to be confirmed)
Возило (регистарски број, тип) ||| Vehicle (registration, type) ||| _
Контрола на температура ||| Temperature control ||| ☐ Активна | Active   ☐ Пасивна (термо-ќебе) | Passive (thermal blanket)
[[/FORM]]

# 2 Материјал и опсег | Material and range
[[FORM]]
Материјал ||| Material ||| ☒ Готов производ / меѓупроизвод (15–25 °C, RH ≤ 60 %) | Finished product / intermediate (15–25 °C, RH ≤ 60 %)   ☐ Клонови (+2 до +8 °C) | Clones (+2 to +8 °C)   ☐ Семе (5–20 °C) | Seeds (5–20 °C)
[[/FORM]]
[[FORM:grid]]
Максимален товар: палети G / M ||| Maximum load: pallets L / S ||| 20 по возило (Т1); Т2 во две возила | 20 per vehicle (T1); T2 in two vehicles
Картони / кеси / маса (kg) ||| Cartons / bags / mass (kg) ||| Т1: 159 / 1480 / 1 471,51 kg; Т2: 280 / 2688 / 2 677,36 kg
Симулиран товар (кеси со иста маса и материјал) ||| Simulated load (bags of the same mass and material) ||| OQ: 20 G-палети со кеси од 1000 g во картони, завиткани како во рутина | OQ: 20 L pallets with 1000 g bags in cartons, wrapped as in routine
Логери: USB (10) / за еднократна употреба (број) ||| Loggers: USB (10) / single-use (number) ||| 10 / OQ 40, PQ-1 40, PQ-2 70
Летен амбиентен екстрем (°C) ||| Summer ambient extreme (°C) ||| _
Зимски амбиентен екстрем (°C) ||| Winter ambient extreme (°C) ||| _
Извор на климатските податоци ||| Source of climate data ||| Управа за хидрометеоролошки работи (УХМР), Скопје | National Hydrometeorological Service, Skopje
[[/FORM]]

# 3 Процена на ризик (FMEA) | Risk assessment (FMEA)
Оценка 1–5 за веројатност (В), последица (П) и откривање (О); RPN = В × П × О. RPN ≥ 40 мора да се покрие со тест во OQ/PQ или со мерка; RPN ≥ 80 бара образложение одобрено од QA пред протоколот. ||| Scores 1–5 for likelihood (L), severity (S) and detectability (D); RPN = L × S × D. RPN ≥ 40 must be covered by an OQ/PQ test or a control; RPN ≥ 80 requires a QA-approved justification before the protocol.
[[TABLE]]
№ ||| Режим на откажување~~Failure mode ||| Ефект~~Effect ||| В~~L ||| П~~S ||| О~~D ||| RPN ||| Тест / мерка~~Test / control
1 ||| Дефект на контролата на температура (ако постои)~~Temperature-control failure (if fitted) ||| температура надвор од опсег~~temperature out of range |||  |||  |||  |||  ||| OQ прекин на напојување (време на задржување)~~OQ power interruption (hold time)
2 ||| Пасивната заштита не е доволна за времетраењето~~Passive protection insufficient for the duration ||| загревање / ладење на палетите~~pallets warm / cool |||  |||  |||  |||  ||| сезонско мапирање со товар ≥ 125 % времетраење~~seasonal loaded mapping ≥ 125 % duration
3 ||| Нерамномерна распределба во товарниот простор~~Uneven distribution in the load space ||| локална екскурзија~~local excursion |||  |||  |||  |||  ||| OQ мапирање P1–P9 + 2 логери по палета~~OQ mapping P1–P9 + 2 loggers per pallet
4 ||| Отворање на вратата при предавање/прием~~Door opening at hand-over/receipt ||| краток пик~~short peak |||  |||  |||  |||  ||| OQ тест врата 2 × 5 мин (P3, P4, P7, P8)~~OQ door test 2 × 5 min (P3, P4, P7, P8)
5 ||| Летен екстрем~~Summer extreme ||| прегревање~~overheating |||  |||  |||  |||  ||| летно мапирање и летна PQ~~summer mapping and summer PQ
6 ||| Зимски екстрем~~Winter extreme ||| поладување / кондензација~~undercooling / condensation |||  |||  |||  |||  ||| зимско мапирање~~winter mapping
7 ||| Застој или чекање на придружувањето~~Traffic delay or waiting for the escort ||| подолго време надвор~~longer exposure |||  |||  |||  |||  ||| OQ ≥ 125 % од максималното времетраење~~OQ ≥ 125 % of maximum duration
8 ||| Мала палета (помала термичка маса)~~Small pallet (less thermal mass) ||| побрзо загревање~~faster warming |||  |||  |||  |||  ||| мала палета во секој тест со товар~~small pallet in every loaded test
9 ||| Палета до ѕидот / вратата~~Pallet against the wall / door ||| пренос на топлина~~heat transfer |||  |||  |||  |||  ||| распоред во TRA, растојание од ѕидовите~~TRA arrangement, clearance from walls
10 ||| Оштетено термо-ќебе / фолија~~Damaged thermal blanket / film ||| изгубена заштита~~protection lost |||  |||  |||  |||  ||| проверка пред отпрема, A05~~pre-dispatch check, A05
11 ||| Неправилна позиција на логерот~~Wrong logger position ||| неоткриена екскурзија~~undetected excursion |||  |||  |||  |||  ||| позиции Е1/Е2 и жешка точка од OQ~~E1/E2 positions and hot spot from OQ
12 ||| Дефект / некалибриран логер~~Logger failure / out of calibration ||| загубени податоци~~data lost |||  |||  |||  |||  ||| проверка пред и после; сертификат на серијата; втор логер~~check before and after; lot certificate; second logger
13 ||| Влага во пакувањето~~Moisture in packaging ||| RH > 60 % |||  |||  |||  |||  ||| USB логер за RH, стреч-фолија~~USB RH logger, stretch film
14 ||| Друго~~Other |||  |||  |||  |||  |||  ||| 
[[/TABLE]]

# 4 Стратегија | Strategy
[[FORM]]
Обем ||| Scope ||| ☒ Целосна OQ + PQ | Full OQ + PQ   ☐ Само PQ (групирање со рута ___) | PQ only (bracketed with lane ___)   ☐ Реквалификација | Requalification
[[/FORM]]
[[FORM]]
Образложение за групирање / обем ||| Justification for bracketing / scope ||| Целосна OQ + PQ. OQ (13.10.2026 – 15.10.2026) на возилото на превозникот пред Т1; PQ-1 = Т1 (20.10.2026), PQ-2 = Т2 (27.10.2026), PQ-3 = следната пратка. Т1 и Т2 се изведуваат додека рутата е во квалификација, по исклучителна мерка одобрена од QA (WHSOP_003 §6.2.2) | Full OQ + PQ. OQ (13.10.2026 – 15.10.2026) on the carrier's vehicle before T1; PQ-1 = T1 (20.10.2026), PQ-2 = T2 (27.10.2026), PQ-3 = the next shipment. T1 and T2 run while the lane is in qualification, under a QA-approved exceptional measure (WHSOP_003 §6.2.2)
Тестови во OQ ||| OQ tests ||| празно, полно (≥ 125 % времетраење), врата 2 × 5 мин, прекин на напојување (само активна), летно и зимско мапирање | empty, loaded (≥ 125 % duration), door 2 × 5 min, power interruption (active only), summer and winter mapping
Број на PQ пратки ||| Number of PQ shipments ||| 3 последователни, барем 1 во сезоната на најлош случај | 3 consecutive, at least 1 in the worst-case season
Планиран почеток и крај ||| Planned start and end ||| 13.10.2026 — PQ-3 | 13.10.2026 — PQ-3
Членови на тимот ||| Team members ||| _
[[/FORM]]

# 5 Одобрување | Approval
[[TABLE]]
Улога~~Role ||| Име~~Name ||| Датум~~Date ||| Потпис~~Signature
Изготвил (тим за валидација)~~Prepared (validation team) |||  |||  ||| 
Прегледал (Логистика / Обезбедување)~~Reviewed (Logistics / Security) |||  |||  ||| 
Одобрил (QA)~~Approved (QA) |||  |||  ||| 
[[/TABLE]]
