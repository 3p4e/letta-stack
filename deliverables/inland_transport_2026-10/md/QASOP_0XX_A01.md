<!--HEADERDATA
mk_title: План за валидација и процена на ризик на транспортна рута
en_title: Lane Validation Plan and Risk Assessment
code: QASOP_0XX_A01
version: 01
doctype: FORM
parent: QASOP_0XX
orient: portrait
-->

# 1 Идентификација на рутата | Lane identification
[[FORM:grid]]
Код на рутата ||| Lane code ||| L__
Број на проект за валидација ||| Validation project No. ||| TVP-___-__
Место на испраќање ||| Dispatch point ||| Којлија 1043, Петровец | Kojlija 1043, Petrovec
Место на прием ||| Receipt point ||| _
Опис на патеката ||| Route description ||| _
Растојание (km) ||| Distance (km) ||| _
Нормално времетраење (h:min) ||| Normal duration (h:min) ||| _
Максимално времетраење со застои (h:min) ||| Maximum duration with delays (h:min) ||| _
Превозник ||| Carrier ||| _
Возило / пакување (идентификација) ||| Vehicle / packaging (identification) ||| _
[[/FORM]]

# 2 Материјал и опсег | Material and range
[[FORM]]
Материјал ||| Material ||| ☐ Готов производ / меѓупроизвод / мостри (15–25 °C, RH ≤ 60 %) | Finished product / intermediate / samples (15–25 °C, RH ≤ 60 %)   ☐ Клонови (+2 до +8 °C) | Clones (+2 to +8 °C)   ☐ Семе (5–20 °C) | Seeds (5–20 °C)
[[/FORM]]
[[FORM:grid]]
Максимален товар (kg / број на кутии) ||| Maximum load (kg / boxes) ||| _
Термичка маса на симулираниот товар ||| Thermal mass of the simulated load ||| _
Летен амбиентен екстрем (°C) ||| Summer ambient extreme (°C) ||| _
Зимски амбиентен екстрем (°C) ||| Winter ambient extreme (°C) ||| _
Извор на климатските податоци ||| Source of climate data ||| _
[[/FORM]]

# 3 Процена на ризик (FMEA) | Risk assessment (FMEA)
Оценка 1–5 за веројатност (В), последица (П) и откривање (О); RPN = В × П × О. RPN ≥ 40 мора да се покрие со тест во OQ/PQ или со мерка; RPN ≥ 80 бара образложение одобрено од QA пред протоколот. ||| Scores 1–5 for likelihood (L), severity (S) and detectability (D); RPN = L × S × D. RPN ≥ 40 must be covered by an OQ/PQ test or a control; RPN ≥ 80 requires a QA-approved justification before the protocol.
[[TABLE]]
№ ||| Режим на откажување~~Failure mode ||| Ефект~~Effect ||| В~~L ||| П~~S ||| О~~D ||| RPN ||| Тест / мерка~~Test / control
1 ||| Дефект на климатизацијата~~Climate-control failure ||| температура надвор од опсег~~temperature out of range |||  |||  |||  |||  ||| OQ прекин на напојување (време на задржување)~~OQ power interruption (hold time)
2 ||| Нерамномерна распределба во товарниот простор~~Uneven distribution in the load space ||| локална екскурзија~~local excursion |||  |||  |||  |||  ||| OQ мапирање 9+ точки~~OQ mapping 9+ points
3 ||| Отворање на вратата при прием/предавање~~Door opening at receipt/hand-over ||| краток пик~~short peak |||  |||  |||  |||  ||| OQ тест врата 2 × 5 мин~~OQ door test 2 × 5 min
4 ||| Летен екстрем~~Summer extreme ||| прегревање~~overheating |||  |||  |||  |||  ||| летно мапирање и летна PQ~~summer mapping and summer PQ
5 ||| Зимски екстрем~~Winter extreme ||| поладување / кондензација~~undercooling / condensation |||  |||  |||  |||  ||| зимско мапирање~~winter mapping
6 ||| Сообраќаен застој~~Traffic delay ||| подолго време надвор~~longer exposure |||  |||  |||  |||  ||| OQ ≥ 125 % од максималното времетраење~~OQ ≥ 125 % of maximum duration
7 ||| Неправилна позиција на логерот~~Wrong logger position ||| неоткриена екскурзија~~undetected excursion |||  |||  |||  |||  ||| позиција на жешка/студена точка од OQ~~hot/cold spot position from OQ
8 ||| Дефект / некалибриран логер~~Logger failure / out of calibration ||| загубени податоци~~data lost |||  |||  |||  |||  ||| калибрација пред и после; резервен логер~~calibration before and after; backup logger
9 ||| Влага во пакувањето~~Moisture in packaging ||| RH > 60 % |||  |||  |||  |||  ||| логер за RH, херметично пакување~~RH logger, airtight packaging
10 ||| Друго~~Other |||  |||  |||  |||  |||  ||| 
[[/TABLE]]

# 4 Стратегија | Strategy
[[FORM]]
Обем ||| Scope ||| ☐ Целосна OQ + PQ | Full OQ + PQ   ☐ Само PQ (групирање со рута ___) | PQ only (bracketed with lane ___)   ☐ Реквалификација | Requalification
[[/FORM]]
[[FORM]]
Образложение за групирање / обем ||| Justification for bracketing / scope ||| _
Тестови во OQ ||| OQ tests ||| празно, полно (≥ 125 % времетраење), врата 2 × 5 мин, прекин на напојување, летно и зимско мапирање | empty, loaded (≥ 125 % duration), door 2 × 5 min, power interruption, summer and winter mapping
Број на PQ пратки ||| Number of PQ shipments ||| 3 последователни, барем 1 во сезоната на најлош случај | 3 consecutive, at least 1 in the worst-case season
Планиран почеток и крај ||| Planned start and end ||| _
Членови на тимот ||| Team members ||| _
[[/FORM]]

# 5 Одобрување | Approval
[[TABLE]]
Улога~~Role ||| Име~~Name ||| Датум~~Date ||| Потпис~~Signature
Изготвил (тим за валидација)~~Prepared (validation team) |||  |||  ||| 
Прегледал (Логистика / Обезбедување)~~Reviewed (Logistics / Security) |||  |||  ||| 
Одобрил (QA)~~Approved (QA) |||  |||  ||| 
[[/TABLE]]
