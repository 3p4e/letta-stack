<!--HEADERDATA
mk_title: Чек-листа пред отпрема и при прием — Т2 (пример)
en_title: Pre-dispatch and Receipt Checklist — T2 (example)
code: WHSOP_003_A05
version: 01
doctype: CHECKLIST
parent: WHSOP_003
orient: portrait
-->

ПРИМЕР / СИМУЛАЦИЈА — не е запис. Сите внесени податоци се во загради: сино — од нашите записи или пресметани; виолетово — пример, да се потврди; портокалово — се внесува на денот. ||| EXAMPLE / SIMULATION — not a record. Every entry is in brackets: blue — from our records or calculated; purple — example, to be confirmed; orange — entered on the day.

# 1 Идентификација | Identification
[[FORM:grid]]
UTID |||  ||| [TR-20261027-001]
Датум ||| Date ||| [27.10.2026]
Рута (код) ||| Lane (code) ||| [L01]
Примач ||| Consignee ||| [Versa (купувач според листата за продажба) | Versa (buyer per the sale list)]
[[/FORM]]

# Дел А — Пред отпрема | Part A — Pre-dispatch
Ако која било ставка е „Не“, транспортот НЕ започнува додека не се реши (WHSOP_003 §6.5.1). ||| If any item is "No", the transport does NOT start until it is resolved (WHSOP_003 §6.5.1).
[[TABLE]]
№ ||| Ставка~~Item ||| Да~~Yes ||| Не~~No ||| N/A ||| Референца~~Reference
A1 ||| Барањето до МВР поднесено ≥ 24 h пред поаѓање~~MoIA request submitted ≥ 24 h before departure ||| [ ] ||| [ ] ||| [ ] ||| A02
A2 ||| Писмена потврда од МВР примена, придружувањето потврдено~~Written MoIA confirmation received, escort confirmed ||| [ ] ||| [ ] ||| [ ] ||| A02
A3 ||| TRA одобрен од QA~~TRA approved by QA ||| [ ] ||| [ ] ||| [ ] ||| A01
A4 ||| Рутата е QUALIFIED за ова возило и конфигурација на палети~~Lane QUALIFIED for this vehicle and pallet configuration ||| [ ] ||| [ ] ||| [ ] ||| QASOP_0XX_A06
A5 ||| Превозникот е квалификуван, Договорот за квалитет важи~~Carrier qualified, Quality Agreement valid ||| [ ] ||| [ ] ||| [ ] ||| QAS-10-003
A6 ||| Примачот потврди прием~~Consignee confirmed receipt ||| [ ] ||| [ ] ||| [ ] ||| [ ]
A7 ||| Материјалот е во статус ОДОБРЕНО~~Material APPROVED ||| [ ] ||| [ ] ||| [ ] ||| WHSOP 001
A8 ||| Листите на пакување за картоните потпишани од две лица~~Carton packing lists signed by two persons ||| [ ] ||| [ ] ||| [ ] ||| A03 §4
A9 ||| Картоните затворени со безбедносна лента, бројот запишан~~Cartons closed with security tape, number recorded ||| [ ] ||| [ ] ||| [ ] ||| A03 §5
A10 ||| Ретенционите мостри подготвени, означени, евидентирани и спакувани во картонот RS~~Retention samples prepared, labelled, recorded and packed in the RS carton ||| [ ] ||| [ ] ||| [ ] ||| A03 §7
A11 ||| Палетите формирани (G 8 / M 4 картони), без препуштање~~Pallets built (L 8 / S 4 cartons), no overhang ||| [ ] ||| [ ] ||| [ ] ||| §6.4.2
A12 ||| Стреч-фолија, термо-ќебе и лента на завиткувањето потпишана~~Stretch film, thermal blanket and signed wrap tape ||| [ ] ||| [ ] ||| [ ] ||| §6.4.2
A13 ||| Етикетите на палетите на две страни, проверени со листите~~Pallet labels on two sides, checked against the lists ||| [ ] ||| [ ] ||| [ ] ||| A03
A14 ||| Логер за еднократна употреба активиран и поставен во секоја палета~~Single-use logger started and placed in every pallet ||| [ ] ||| [ ] ||| [ ] ||| A03 §5
A15 ||| USB логер калибриран, активиран, на позицијата од OQ~~USB logger calibrated, started, at the OQ position ||| [ ] ||| [ ] ||| [ ] ||| A04 §3
A16 ||| Возилото одговара на A02, чисто, суво и заклучливо~~Vehicle matches A02, clean, dry and lockable ||| [ ] ||| [ ] ||| [ ] ||| [ ]
A17 ||| Контрола на температура: ☐ активна — поставена и предкондиционирана ≥ 30 мин; ☐ пасивна — термо-ќебињата цели~~Temperature control: ☐ active — set and pre-conditioned ≥ 30 min; ☐ passive — thermal blankets intact ||| [ ] ||| [ ] ||| [ ] ||| §6.5.2
A18 ||| Палетите натоварени по распоредот од TRA и обезбедени~~Pallets loaded per the TRA arrangement and secured ||| [ ] ||| [ ] ||| [ ] ||| A01 §2
A19 ||| Идентитет и овластување на возачот (и придружникот) проверени~~Identity and authorisation of the driver (and accompanying person) verified ||| [ ] ||| [ ] ||| [ ] ||| [ ]
A20 ||| Лицата брифирани (рута, застанувања, инциденти, логери)~~Persons briefed (route, stops, incidents, loggers) ||| [ ] ||| [ ] ||| [ ] ||| [ ]
[[/TABLE]]
[[TABLE]]
Улога~~Role ||| Име~~Name ||| Датум/време~~Date/time ||| Потпис~~Signature
Проверил (Обезбедување)~~Checked (Security) ||| [ ] ||| [ ] ||| [ ]
Проверил (Логистика)~~Checked (Logistics) ||| [ ] ||| [ ] ||| [ ]
[[/TABLE]]

# Дел Б — При прием | Part B — On receipt
Примачот ја пополнува пред да го потпише ланецот на надзор. При оштетена пломба, лента или завиткување, или неусогласен број — не прифаќајте, фотографирајте и известете ја QA на Пјурли Плант. ||| The consignee completes this before signing the chain of custody. If a seal, tape or wrapping is damaged or a count does not match — do not accept, photograph and notify Purely Plant QA.
[[TABLE]]
№ ||| Ставка~~Item ||| Да~~Yes ||| Не~~No ||| Резултат / забелешка~~Result / remark
B1 ||| Идентитет на лицата и регистарски број одговараат~~Identity of the persons and registration match ||| [ ] ||| [ ] ||| [ ]
B2 ||| Пломбата на вратата е цела, бројот одговара~~Door seal intact, number matches ||| [ ] ||| [ ] ||| [ ]
B3 ||| Број на палети: очекуван / примен~~Pallets: expected / received ||| [ ] ||| [ ] ||| [ ]
B4 ||| Завиткувањето, термо-ќебињата и лентите се цели~~Wrapping, thermal blankets and tapes intact ||| [ ] ||| [ ] ||| [ ]
B5 ||| Етикетите на палетите одговараат на манифестот A04~~Pallet labels match manifest A04 ||| [ ] ||| [ ] ||| [ ]
B6 ||| Логерите за еднократна употреба извадени и запрени (број)~~Single-use loggers removed and stopped (number) ||| [ ] ||| [ ] ||| [ ]
B7 ||| Без аларм на ниеден логер; мин./макс. запишани во A04~~No alarm on any logger; min./max. recorded in A04 ||| [ ] ||| [ ] ||| [ ]
B8 ||| Број на картони по палета одговара; лентите на картоните цели~~Cartons per pallet match; carton tapes intact ||| [ ] ||| [ ] ||| [ ]
B9 ||| Картонот со ретенциони мостри примен, лентата цела, бројот на мостри одговара~~Retention-sample carton received, tape intact, sample count matches ||| [ ] ||| [ ] ||| [ ]
B10 ||| Надворешна состојба без оштетување, влага или притисок~~External condition free of damage, wetness or crushing ||| [ ] ||| [ ] ||| [ ]
B11 ||| Маса при прием евидентирана по картон~~Mass on receipt recorded per carton ||| [ ] ||| [ ] ||| [ ]
[[/TABLE]]
[[FORM]]
Статус на приемот ||| Receipt status ||| ☐ Прифатено | Accepted   ☐ Прифатено со резерва | Accepted with reservation   ☐ Одбиено | Rejected
[[/FORM]]
[[TABLE]]
Улога~~Role ||| Име~~Name ||| Организација~~Organisation ||| Датум/време~~Date/time ||| Потпис~~Signature
Примач~~Consignee ||| [ ] ||| [ ] ||| [ ] ||| [ ]
[[/TABLE]]
