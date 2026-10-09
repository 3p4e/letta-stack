<!--HEADERDATA
mk_title: Регистар на квалификувани транспортни рути и тренд (пример)
en_title: Qualified Lane Register and Trend (example)
code: QASOP_0XX_A06
version: 01
doctype: LOG
parent: QASOP_0XX
orient: landscape
-->

ПРИМЕР / СИМУЛАЦИЈА — не е запис. Сите внесени податоци се во загради: сино — од нашите записи или пресметани; виолетово — пример, да се потврди; портокалово — се внесува на денот. ||| EXAMPLE / SIMULATION — not a record. Every entry is in brackets: blue — from our records or calculated; purple — example, to be confirmed; orange — entered on the day.

# 1 Регистар на рути | Lane register
Рута без статус QUALIFIED и важечки датум не се користи според WHSOP_003. Растојанието и времетраењето се внесуваат од TRA/A01 по мерење, не се проценуваат. ||| A lane without QUALIFIED status and a valid date is not used under WHSOP_003. Distance and duration are entered from the TRA/A01 after measurement, not estimated.
[[TABLE]]
Код~~Code ||| Место на прием~~Receipt point ||| Материјал / опсег~~Material / range ||| Превозник / возило / палети G/M~~Carrier / vehicle / pallets L/S ||| km ||| Макс. траење~~Max. duration ||| Извештај (A05)~~Report (A05) ||| Статус~~Status ||| Важи до~~Valid until ||| Ограничувања~~Limitations
L01 ||| [Versa] · [ ] ||| [меѓупроизвод 15–25 °C]~~[intermediate 15–25 °C] ||| [Kuehne + Nagel (предв.) / G-палети]~~[Kuehne + Nagel (prov.) / L pallets] ||| [ ] ||| [ ] ||| [ ] ||| [IN QUALIFICATION] ||| [—] ||| [PQ-1 = Т1, PQ-2 = Т2]~~[PQ-1 = T1, PQ-2 = T2]
L02 ||| Царински магацин → локација~~Bonded warehouse → site ||| клонови / семе~~clones / seeds ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ]
L03 ||| Овластено место за уништување~~Authorised destruction site ||| отпад (не е критична)~~waste (not critical) ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ]
[ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ]
[ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ]
[ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ]
[[/TABLE]]
Статус: PLANNED / IN QUALIFICATION / QUALIFIED / SUSPENDED / RETIRED. ||| Status: PLANNED / IN QUALIFICATION / QUALIFIED / SUSPENDED / RETIRED.

# 2 Квартален тренд по рута | Quarterly trend per lane
[[TABLE]]
Код~~Code ||| Квартал~~Quarter ||| Број на пратки~~Shipments ||| Мин. (°C) ||| Макс. (°C) ||| Највисок MKT (°C)~~Highest MKT (°C) ||| Екскурзии (бр.)~~Excursions (No.) ||| Тренд~~Trend ||| Мерка~~Action ||| Прегледал (QA)~~Reviewed (QA)
[ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ]
[ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ]
[ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ]
[ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ]
[[/TABLE]]

# 3 Реквалификации и промени | Requalifications and changes
[[TABLE]]
Код~~Code ||| Датум~~Date ||| Причина (годишна / промена / екскурзија / тренд)~~Reason (annual / change / excursion / trend) ||| Контрола на промени бр.~~Change control No. ||| Обем~~Scope ||| Извештај~~Report ||| Нов статус~~New status
[ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ]
[ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ] ||| [ ]
[[/TABLE]]
