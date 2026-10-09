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
Возило / пакување ||| Vehicle / packaging ||| _
Сезона ||| Season ||| _
Опсег ||| Range ||| _
Датум на извршување ||| Execution date ||| _
[[/FORM]]

# 2 Логери и позиции | Loggers and positions
[[TABLE]]
Позиција~~Position ||| Опис~~Description ||| Сериски број~~Serial No. ||| Калибрација важи до~~Calibration due ||| Проверка пред (Δ °C)~~Check before (Δ °C) ||| Проверка после (Δ °C)~~Check after (Δ °C)
P1 ||| Горе напред лево~~Top front left |||  |||  |||  ||| 
P2 ||| Горе напред десно~~Top front right |||  |||  |||  ||| 
P3 ||| Горе назад лево~~Top rear left |||  |||  |||  ||| 
P4 ||| Горе назад десно~~Top rear right |||  |||  |||  ||| 
P5 ||| Долу напред лево~~Bottom front left |||  |||  |||  ||| 
P6 ||| Долу напред десно~~Bottom front right |||  |||  |||  ||| 
P7 ||| Долу назад лево~~Bottom rear left |||  |||  |||  ||| 
P8 ||| Долу назад десно~~Bottom rear right |||  |||  |||  ||| 
P9 ||| Геометриски центар~~Geometric centre |||  |||  |||  ||| 
P10 ||| Кај вратата~~At the door |||  |||  |||  ||| 
P11 ||| Излез на климатизацијата~~Climate-control outlet |||  |||  |||  ||| 
P12 ||| Амбиент (надвор)~~Ambient (outside) |||  |||  |||  ||| 
[[/TABLE]]

[[PAGEBREAK]]
# 3 Резултати по тест | Results per test
[[TABLE]]
Тест~~Test ||| Почеток~~Start ||| Крај~~End ||| Амбиент мин./макс. (°C)~~Ambient min./max. (°C) ||| Мин. (°C) / позиција~~Min. (°C) / position ||| Макс. (°C) / позиција~~Max. (°C) / position ||| MKT (°C) ||| Време надвор (мин)~~Time out (min) ||| Критериум исполнет~~Criterion met
OQ-1 Празно — стабилизација~~Empty — stabilisation |||  |||  |||  |||  |||  |||  |||  ||| 
OQ-2 Полно ≥ 125 % времетраење~~Loaded ≥ 125 % duration |||  |||  |||  |||  |||  |||  |||  ||| 
OQ-3 Врата 2 × 5 мин~~Door 2 × 5 min |||  |||  |||  |||  |||  |||  |||  ||| 
OQ-4 Прекин на напојување~~Power interruption |||  |||  |||  |||  |||  |||  |||  ||| 
OQ-5 Летно мапирање~~Summer mapping |||  |||  |||  |||  |||  |||  |||  ||| 
OQ-6 Зимско мапирање~~Winter mapping |||  |||  |||  |||  |||  |||  |||  ||| 
[[/TABLE]]
[[FORM:grid]]
Време до опсег по вклучување (мин) ||| Time to range after start (min) ||| _
Враќање во опсег по врата 1 / врата 2 (мин) ||| Return to range after door 1 / door 2 (min) ||| _
Време на задржување (мин) ||| Hold time (min) ||| _
Жешка точка ||| Hot spot ||| _
Студена точка ||| Cold spot ||| _
Позиција за рутинскиот логер ||| Position for the routine logger ||| _
[[/FORM]]
Необработените податоци (извоз од секој логер, со сериски број и временски печат) се прилагаат и се чуваат со овој запис; печатените вредности мора да се пресметаат од нив. ||| The raw data (export from each logger, with serial number and timestamps) are attached and retained with this record; the printed values must be calculated from them.

[[PAGEBREAK]]
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
