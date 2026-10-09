<!--HEADERDATA
mk_title: Процена на ризик од транспорт (TRA)
en_title: Transport Risk Assessment (TRA)
code: WHSOP_003_A01
version: 01
doctype: FORM
parent: WHSOP_003
orient: portrait
-->

# 1 Идентификација на транспортот | Transport identification
[[FORM:grid]]
UTID |||  ||| TR-________-___
Датум на транспорт ||| Transport date ||| _
Иницијатор ||| Initiator ||| _
Рута (код од QASOP_0XX_A06) ||| Lane (code from QASOP_0XX_A06) ||| _
Статус на рутата ||| Lane status ||| _
Важи до ||| Valid until ||| _
Место на испраќање ||| Dispatch point ||| _
Примач и адреса ||| Consignee and address ||| _
Растојание (km) ||| Distance (km) ||| _
Планирано времетраење (h:min) ||| Planned duration (h:min) ||| _
[[/FORM]]

# 2 Материјал | Material
[[FORM]]
Вид на материјал ||| Material type ||| ☐ Готов производ | Finished product   ☐ Меѓупроизвод | Intermediate   ☐ Клонови | Clones   ☐ Семе | Seeds   ☐ Отпад | Waste
[[/FORM]]
[[TABLE]]
№ ||| Серија~~Batch ||| Нето маса (g)~~Net mass (g) ||| Број на контејнери~~Containers ||| Услови~~Conditions
1 |||  |||  |||  ||| 
2 |||  |||  |||  ||| 
3 |||  |||  |||  ||| 
Вкупно~~Total |||  |||  |||  ||| 
[[/TABLE]]

# 3 Оценка на ризик (ICH Q9) | Risk evaluation (ICH Q9)
Секој ризик се оценува со веројатност (В) и последица (П) од 1 до 3; приоритет = В × П. Приоритет ≥ 6 бара дополнителна мерка пред одобрување; приоритет 9 бара одобрение од QP. ||| Each risk is scored for likelihood (L) and consequence (C) from 1 to 3; priority = L × C. Priority ≥ 6 requires an additional measure before approval; priority 9 requires QP approval.
[[TABLE]]
№ ||| Опасност~~Hazard ||| В~~L ||| П~~C ||| Приоритет~~Priority ||| Мерка за намалување~~Mitigation ||| Преостанат ризик~~Residual
1 ||| Кражба / напад на возилото~~Theft / attack on the vehicle |||  |||  |||  ||| двочлена посада, GPS, неозначено возило~~two-person crew, GPS, unmarked vehicle ||| 
2 ||| Отстапување од рутата~~Route deviation |||  |||  |||  ||| GPS во реално време, одобрени застанувања~~real-time GPS, approved stops ||| 
3 ||| Сезонска температура надвор од опсег~~Seasonal temperature out of range |||  |||  |||  ||| квалификувана климатизација, предкондиционирање 30 мин~~qualified climate control, 30 min pre-conditioning ||| 
4 ||| Влага / кондензација~~Humidity / condensation |||  |||  |||  ||| херметично пакување, логер за RH~~airtight packaging, RH logger ||| 
5 ||| Доцнење (сообраќај, дефект)~~Delay (traffic, breakdown) |||  |||  |||  ||| резервно возило, време на задржување од OQ~~backup vehicle, hold time from OQ ||| 
6 ||| Оштетување на пакувањето~~Packaging damage |||  |||  |||  ||| амортизација, обезбедување на товарот~~cushioning, load securing ||| 
7 ||| Губење/замена на материјал~~Material loss/mix-up |||  |||  |||  ||| двојна проверка, пломби, манифест~~two-person check, seals, manifest ||| 
8 ||| Регулаторно (без потврда од МВР)~~Regulatory (no MoIA confirmation) |||  |||  |||  ||| чек-листа A05: блокира отпрема~~checklist A05 blocks dispatch ||| 
9 ||| Друго~~Other |||  |||  |||  |||  ||| 
[[/TABLE]]

# 4 Одобрена рута и застанувања | Approved route and stops
[[FORM]]
Опис на рутата (патишта, клучни точки) ||| Route description (roads, key points) ||| _
Одобрени места за застанување ||| Approved stopping points ||| _
Контролни јавувања ||| Check-in calls ||| поаѓање, средина (> 2 h), 15–30 мин пред пристигнување, пристигнување | departure, mid-route (> 2 h), 15–30 min before arrival, arrival
Резервна рута / возило ||| Backup route / vehicle ||| _
[[/FORM]]

# 5 Заклучок | Conclusion
[[FORM]]
Заклучок ||| Conclusion ||| ☐ Транспортот е одобрен | Transport approved   ☐ Одобрен со дополнителни мерки | Approved with additional measures   ☐ Не е одобрен | Not approved
[[/FORM]]
[[TABLE]]
Улога~~Role ||| Име~~Name ||| Датум~~Date ||| Потпис~~Signature
Изготвил (Логистика / Обезбедување)~~Prepared (Logistics / Security) |||  |||  ||| 
Одобрил (QA)~~Approved (QA) |||  |||  ||| 
Одобрил (QP) — само при приоритет 9~~Approved (QP) — only for priority 9 |||  |||  ||| 
[[/TABLE]]
