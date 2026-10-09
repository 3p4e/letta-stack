<!--HEADERDATA
mk_title: Калкулација на пратките — Транша 1 и Транша 2 (пример)
en_title: Shipment Calculation — Tranche 1 and Tranche 2 (example)
code: EX_T1T2_CALC
version: 01
doctype: FORM
parent: WHSOP_003
orient: landscape
-->

ПРИМЕР / СИМУЛАЦИЈА — пополнето со податоците што ги имаме и со пресметките од листот за калкулација; не е запис. Мерењата, потписите, броевите на пломби и логери и податоците што се дознаваат на денот се оставени празни. ||| EXAMPLE / SIMULATION — filled with the data we hold and the calculations on the calculation sheet; not a record. Measurements, signatures, seal and logger numbers and data known only on the day are left blank.

# 1 Параметри и претпоставки | Parameters and assumptions
[[FORM]]
Извор на сериите ||| Source of the batches ||| Транши T1 и T2 според одлуката од 18.09.2026 (tranche_assignment_2026-09-18.csv); маса по серија од листата на испораки (tranches_raw_2026-09-07.csv); подсериите се посебни серии | Tranches T1 and T2 per the decision of 18.09.2026; mass per batch from the delivery list; sub-lots are separate batches
Нето маса на една кеса ||| Net mass of one bag ||| 1000 g — ПРЕТПОСТАВКА, не е на досие; ја менува пресметката на кеси, картони и палети | 1000 g — ASSUMPTION, not on file; it drives the bag, carton and pallet counts
Пакување ||| Packaging ||| 10 кеси по картон; голема палета 8 картони, мала 4; една серија по картон | 10 bags per carton; large pallet 8 cartons, small 4; one batch per carton
Капацитет на возило ||| Vehicle capacity ||| 33 евро-палети во еден слој (приколка 13,6 m) | 33 Euro pallets single-stacked (13.6 m trailer)
Датуми ||| Dates ||| пример: OQ 13.10.2026 – 15.10.2026; Т1 20.10.2026; Т2 27.10.2026 | example: OQ 13.10.2026 – 15.10.2026; T1 20.10.2026; T2 27.10.2026
Превозник и примач ||| Carrier and consignee ||| Kuehne + Nagel (provisional, to be confirmed); Versa (buyer per the sale list)
[[/FORM]]

# 2 Преглед | Overview
[[TABLE]]
Транша~~Tranche ||| UTID ||| Датум~~Date ||| Серии~~Batches ||| Нето маса~~Net mass ||| Кеси~~Bags ||| Картони~~Cartons ||| Палети~~Pallets ||| Возила~~Vehicles ||| Логери рутина~~Loggers routine ||| Логери PQ (Е1+Е2)~~Loggers PQ (E1+E2) ||| USB логери PQ~~USB loggers PQ
Т1~~T1 ||| TR-20261020-001 ||| 20.10.2026 ||| 20 ||| 1 471,51 kg ||| 1480 ||| 159 ||| 20 (G 20 / M 0) ||| 1 ||| 20 ||| 40 ||| 3
Т2~~T2 ||| TR-20261027-001 ||| 27.10.2026 ||| 26 ||| 2 677,36 kg ||| 2688 ||| 280 ||| 35 (G 35 / M 0) ||| 2 ||| 35 ||| 70 ||| 6
Вкупно~~Total |||  |||  ||| 46 ||| 4 148,87 kg ||| 4168 ||| 439 ||| 55 |||  ||| 55 ||| 110 ||| 
[[/TABLE]]

# 3 Серии во Т1 | Batches in T1
[[TABLE]]
№ ||| P серија~~P lot ||| Културна серија~~Cultivation batch ||| Сорта~~Strain ||| Нето маса (g)~~Net mass (g) ||| Кеси~~Bags ||| Картони~~Cartons ||| Последен картон (кеси)~~Last carton (bags)
1 ||| — ||| BG1024 ||| Blue Gelato ||| 43 870 ||| 44 ||| 5 ||| 4
2 ||| — ||| BSS1024 ||| Blue Sunset Sherbet ||| 50 200 ||| 51 ||| 6 ||| 1
3 ||| P050162 ||| CJ052501/01 ||| Cap Junkie ||| 64 530 ||| 65 ||| 7 ||| 5
4 ||| P050212 ||| CJ062501/2 ||| Cap Junkie ||| 146 520 ||| 147 ||| 15 ||| 7
5 ||| P060032 ||| CJ082501/2 ||| Cap Junkie ||| 14 750 ||| 15 ||| 2 ||| 5
6 ||| P060352 ||| FB012602* ||| Fat Bastard ||| 75 920 ||| 76 ||| 8 ||| 6
7 ||| P060402 ||| GG012603 ||| GG4 ||| 40 000 ||| 40 ||| 4 ||| 10
8 ||| P050092 ||| GG1024_01 ||| Gorilla Glue ||| 870 ||| 1 ||| 1 ||| 1
9 ||| P050152 ||| GP052501 ||| Grape Pie ||| 151 140 ||| 152 ||| 16 ||| 2
10 ||| P050022 ||| GP0824_02 ||| Grape Pie ||| 208 460 ||| 209 ||| 21 ||| 9
11 ||| P050322 ||| GP082501/2 ||| Grape Pie ||| 22 840 ||| 23 ||| 3 ||| 3
12 ||| — ||| HPA1024 ||| High Pro Amnesia ||| 40 830 ||| 41 ||| 5 ||| 1
13 ||| P050052 ||| HPA1024_01 ||| High Pro Amnesia ||| 140 500 ||| 141 ||| 15 ||| 1
14 ||| P060152 ||| J31102501 ||| Jokerz 31 ||| 23 640 ||| 24 ||| 3 ||| 4
15 ||| P060212 ||| JD112501 ||| Jelly Donuts ||| 41 540 ||| 42 ||| 5 ||| 2
16 ||| — ||| OPM1024 ||| Orange Punch Mimosa ||| 45 460 ||| 46 ||| 5 ||| 6
17 ||| P050062 ||| OPM1024_02 ||| Orange Punch Mimosa ||| 156 140 ||| 157 ||| 16 ||| 7
18 ||| P060242 ||| OPM122501 ||| Orange Punch Mimosa ||| 104 260 ||| 105 ||| 11 ||| 5
19 ||| P060062 ||| PM092501 ||| Permanent Marker ||| 20 230 ||| 21 ||| 3 ||| 1
20 ||| P060382 ||| SCR012603 ||| Scrambler ||| 79 810 ||| 80 ||| 8 ||| 10
Вкупно~~Total |||  |||  |||  ||| 1 471 510 ||| 1480 ||| 159 ||| 
[[/TABLE]]

# 4 Серии во Т2 | Batches in T2
[[TABLE]]
№ ||| P серија~~P lot ||| Културна серија~~Cultivation batch ||| Сорта~~Strain ||| Нето маса (g)~~Net mass (g) ||| Кеси~~Bags ||| Картони~~Cartons ||| Последен картон (кеси)~~Last carton (bags)
1 ||| P060122 ||| ACC102501 ||| Amnesia Core Cut ||| 38 880 ||| 39 ||| 4 ||| 9
2 ||| P050192 ||| BSS052501 ||| Blue Sunset Sherbet ||| 345 710 ||| 346 ||| 35 ||| 6
3 ||| P060372 ||| CC012603 ||| CashCow ||| 56 180 ||| 57 ||| 6 ||| 7
4 ||| P060132 ||| CF102501 ||| Chem Flyer ||| 48 350 ||| 49 ||| 5 ||| 9
5 ||| P050222 ||| CJ062501/1 ||| Cap Junkie ||| 77 720 ||| 78 ||| 8 ||| 8
6 ||| P060022 ||| CJ082501/1 ||| Cap Junkie ||| 115 600 ||| 116 ||| 12 ||| 6
7 ||| P060072 ||| CJ092501 ||| Cap Junkie ||| 28 380 ||| 29 ||| 3 ||| 9
8 ||| P060322 ||| FB012601/1 ||| Fat Bastard ||| 8 850 ||| 9 ||| 1 ||| 9
9 ||| — ||| GG1024 ||| Gorilla Glue ||| 44 840 ||| 45 ||| 5 ||| 5
10 ||| P050302 ||| GP072501/2 ||| Grape Pie ||| 13 630 ||| 14 ||| 2 ||| 4
11 ||| P050072 ||| GP0824_03 ||| Grape Pie ||| 237 670 ||| 238 ||| 24 ||| 8
12 ||| P050312 ||| GP082501/1 ||| Grape Pie ||| 200 420 ||| 201 ||| 21 ||| 1
13 ||| P060092 ||| GP092501 ||| Grape Pie ||| 171 030 ||| 172 ||| 18 ||| 2
14 ||| P060182 ||| GRC102501/2 ||| Grapes and Cream ||| 20 170 ||| 21 ||| 3 ||| 1
15 ||| P050182 ||| HPA052501 ||| High Pro Amnesia ||| 249 950 ||| 250 ||| 25 ||| 10
16 ||| P060422 ||| JD012603/02V ||| Jelly Donuts ||| 11 000 ||| 11 ||| 2 ||| 1
17 ||| P060412 ||| JD012603/02 ||| Jelly Donuts ||| 46 000 ||| 46 ||| 5 ||| 6
18 ||| P060362 ||| JD012603/01 ||| Jelly Donuts ||| 12 000 ||| 12 ||| 2 ||| 2
19 ||| P060172 ||| KC102501 ||| Kush Crasher ||| 21 670 ||| 22 ||| 3 ||| 2
20 ||| P050112 ||| MB0824_05 ||| Motor Breath ||| 244 060 ||| 245 ||| 25 ||| 5
21 ||| P050042 ||| OMP1024_01 ||| Orange Punch Mimosa ||| 213 590 ||| 214 ||| 22 ||| 4
22 ||| P050082 ||| OPM1024_03 ||| Orange Punch Mimosa ||| 267 590 ||| 268 ||| 27 ||| 8
23 ||| P060232 ||| PM112501 ||| Permanent Marker ||| 48 090 ||| 49 ||| 5 ||| 9
24 ||| P060112 ||| PUM102501 ||| Pure Michigen ||| 49 910 ||| 50 ||| 5 ||| 10
25 ||| P060282 ||| SCR112501 ||| Scrambler ||| 23 440 ||| 24 ||| 3 ||| 4
26 ||| P060012 ||| WC082501 ||| Wedding Crusher ||| 82 630 ||| 83 ||| 9 ||| 3
Вкупно~~Total |||  |||  |||  ||| 2 677 360 ||| 2688 ||| 280 ||| 
[[/TABLE]]

# 5 Што треба да се одлучи | What must be decided
[[TABLE]]
№ ||| Прашање~~Question ||| Зошто~~Why
1 ||| Вистинската нето маса по кеса~~The actual net mass per bag ||| ги менува сите бројки на картони, палети и логери~~it changes every carton, pallet and logger count
2 ||| Т2 бара 35 палети — две возила~~T2 needs 35 pallets — two vehicles ||| над 33 палети во едно возило~~more than 33 pallets in one vehicle
3 ||| Логери за PQ: 110 за еднократна употреба~~PQ loggers: 110 single-use ||| располагаме со нешто над 100~~we hold a little over 100
4 ||| OQ пред Т1~~OQ before T1 ||| PQ не смее да почне без одобрена OQ (QASOP_0XX §6.1)~~PQ must not start without an approved OQ (QASOP_0XX §6.1)
5 ||| Последните картони на серијата не се полни~~The last carton of a batch is not full ||| една серија по картон; бројот на кеси е на етикетата~~one batch per carton; the bag count is on the label
6 ||| Адреса на примачот и рута~~Consignee address and route ||| потребни за барањето до МВР и за TRA~~needed for the MoIA request and the TRA
[[/TABLE]]
