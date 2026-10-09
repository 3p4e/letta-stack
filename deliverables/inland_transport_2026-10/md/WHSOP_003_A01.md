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
Превозник ||| Carrier ||| _
Возило (регистарски број) ||| Vehicle (registration) ||| _
Контрола на температура ||| Temperature control ||| ☐ Активна | Active   ☐ Пасивна (термо-ќебе) | Passive (thermal blanket)
Придружник на Пјурли Плант ||| Purely Plant accompanying person ||| ☐ Да | Yes   ☐ Не | No
[[/FORM]]

# 2 Материјал и палети | Material and pallets
[[FORM]]
Вид на материјал ||| Material type ||| ☐ Меѓупроизвод | Intermediate   ☐ Готов производ | Finished product   ☐ Клонови | Clones   ☐ Семе | Seeds   ☐ Отпад | Waste
[[/FORM]]
[[TABLE]]
№ ||| Серија~~Batch ||| Кеси~~Bags ||| Картони~~Cartons ||| Нето маса (g)~~Net mass (g) ||| Услови~~Conditions
1 |||  |||  |||  |||  ||| 
2 |||  |||  |||  |||  ||| 
3 |||  |||  |||  |||  ||| 
Вкупно~~Total |||  |||  |||  |||  ||| 
[[/TABLE]]
[[FORM:grid]]
Палети G (8 картони) ||| Pallets L (8 cartons) ||| _
Палети M (4 картони) ||| Pallets S (4 cartons) ||| _
Логери за еднократна употреба ||| Single-use loggers ||| _
USB логер (сериски број) ||| USB logger (serial No.) ||| _
[[/FORM]]
[[FORM]]
Распоред на палетите во возилото (скица или опис; позиција на USB логерот) ||| Pallet arrangement in the vehicle (sketch or description; USB logger position) ||| _
[[/FORM]]

# 3 Оценка на ризик (ICH Q9) | Risk evaluation (ICH Q9)
Секој ризик се оценува со веројатност (В) и последица (П) од 1 до 3; приоритет = В × П. Приоритет ≥ 6 бара дополнителна мерка пред одобрување; приоритет 9 бара одобрение од QP. ||| Each risk is scored for likelihood (L) and consequence (C) from 1 to 3; priority = L × C. Priority ≥ 6 requires an additional measure before approval; priority 9 requires QP approval.
[[TABLE]]
№ ||| Опасност~~Hazard ||| В~~L ||| П~~C ||| Приоритет~~Priority ||| Мерка за намалување~~Mitigation ||| Преостанат ризик~~Residual
1 ||| Кражба / напад на возилото~~Theft / attack on the vehicle |||  |||  |||  ||| полициско придружување, квалификуван превозник, неозначено возило~~police escort, qualified carrier, unmarked vehicle ||| 
2 ||| Отстапување од рутата~~Route deviation |||  |||  |||  ||| придружување, контролни јавувања, одобрени застанувања~~escort, check-in calls, approved stops ||| 
3 ||| Придружувањето не се појавува / доцни~~Escort does not arrive / is late |||  |||  |||  ||| потврда од МВР, отпремата се одложува~~MoIA confirmation, dispatch postponed ||| 
4 ||| Сезонска температура надвор од опсег~~Seasonal temperature out of range |||  |||  |||  ||| термо-ќебе, квалификувано времетраење, (контрола на температура)~~thermal blanket, qualified duration, (temperature control) ||| 
5 ||| Влага / кондензација~~Humidity / condensation |||  |||  |||  ||| стреч-фолија, сув товарен простор, USB логер за RH~~stretch film, dry load space, USB RH logger ||| 
6 ||| Доцнење (сообраќај, дефект)~~Delay (traffic, breakdown) |||  |||  |||  ||| резервно возило, време на задржување од OQ~~backup vehicle, hold time from OQ ||| 
7 ||| Оштетување на палета / картон~~Pallet / carton damage |||  |||  |||  ||| без препуштање, обезбедување на товарот~~no overhang, load securing ||| 
8 ||| Губење / замена (етикети на хартија)~~Loss / mix-up (paper labels) |||  |||  |||  ||| двојна проверка, листи на пакување, броење на секоја точка~~two-person check, packing lists, count at every transfer ||| 
9 ||| Логер не е активиран / изгубен~~Logger not started / lost |||  |||  |||  ||| проверка при активирање, сериски број во A04, USB логер~~check at start, serial No. in A04, USB logger ||| 
10 ||| Регулаторно (без потврда од МВР)~~Regulatory (no MoIA confirmation) |||  |||  |||  ||| чек-листа A05: блокира отпрема~~checklist A05 blocks dispatch ||| 
11 ||| Друго~~Other |||  |||  |||  |||  ||| 
[[/TABLE]]

# 4 Одобрена рута и застанувања | Approved route and stops
[[FORM]]
Опис на рутата (патишта, клучни точки) ||| Route description (roads, key points) ||| _
Место и време на почеток на придружувањето ||| Place and time the escort starts ||| _
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
