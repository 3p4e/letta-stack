import subprocess
B=[
 dict(k='GG4',prod='STEADY GG4 16 % THC / 1 % CBD',lc='VZ26/259 – 2/2 · 000015-V90 · 26-GG4-006',res='19.0',lim='14.4–17.6 (16 ± 10 %)',pp='P060402',cb='GG012603',st='Gorilla Glue',tr='Tranche 1',md='04.05.2026',pk='24.05.2026',spec='QCSP_001_GG-I_v.01: 16.23–19.76',coq='CoQ-PP_26-092 (17.08.2026): 16.70 % — Farmahem 197-8-К/26 (07.08.2026)',coq0='CoQ-PP_26-077 (07.07.2026): 17.59 % — CNP ППК26114 (30.06.2026)',dev='+2.3 points against our CoQ; +18.8 % against the label 16',verd='Outside the Versa label limit; within our specification GG-I',alt=''),
 dict(k='PT',prod='STEADY PT 10 % THC / 1 % CBD (Plum Tarte)',lc='VZ26/260 – 2/2 · 000041-V90 · 26-PT-034',res='6.3',lim='9.0–11.0 (10 ± 10 %)',pp='P060182',cb='GRC102501/2',st='Grapes and Cream',tr='Tranche 2',md='20.01.2026',pk='14.03.2026',spec='QCSP_001_GRC-II_v.01: 9.00–10.99',coq='CoQ-PP_26-120 (18.09.2026): 9.80 % — Farmahem 220-14-К/26 (25.08.2026)',coq0='CoQ-PP_26-054 (06.06.2026): 11.53 % — Farmahem 051-6-К/26 (04.03.2026)',dev='−3.5 points (−36 %) against our CoQ',verd='Outside the Versa limit and our specification',alt=''),
 dict(k='JD',prod='CAYN JD 14 % THC / 1 % CBD (Jelly Donuts)',lc='VZ26/273 – 2/2 · 000044-V90 · 26-JD-037',res='17.5',lim='12.6–15.4 (14 ± 10 %)',pp='P060412',cb='JD012603/02',st='Jelly Donuts',tr='Tranche 2',md='04.05.2026',pk='24.05.2026',spec='QCSP_001_JD-III_v.01: 13.80–16.19',coq='CoQ-PP_26-123 (18.09.2026): 14.43 % — Farmahem 220-17-К/26 (26.08.2026)',coq0='CoQ-PP_26-078 (07.07.2026): 20.54 % — CNP ППК26113 (30.06.2026)',dev='+3.1 points (+21 %) against our CoQ',verd='Outside the Versa limit and our specification',alt='Batch assignment to be confirmed by the receiving party: P060422 (JD012603/02V, CoQ-PP_26-124: 17.09 %) is the other Tranche 2 Jelly Donuts lot.'),
 dict(k='F1',prod='STEADY F1 12 % THC / 1 % CBD (Formula 1)',lc='VZ26/263 – 2/2 · 000027-V90 · 26-FO1-018',res='8.7',lim='10.8–13.2 (12 ± 10 %)',pp='P060062',cb='PM092501',st='Permanent Marker',tr='Tranche 1',md='11.12.2025',pk='30.01.2026',spec='QCSP_001_PM-II_v.01: 11.00–12.99',coq='CoQ-PP_26-104 (17.08.2026): 12.25 % — Farmahem 197-20-К/26 (07.08.2026)',coq0='CoQ-PP_26-042 (06.06.2026): 14.06 % — CNP ППК26004 (21.01.2026)',dev='−3.6 points (−29 %) against our CoQ',verd='Outside the Versa limit and our specification',alt='Batch assignment to be confirmed by the receiving party: P050272 (PM072501, Tranche 3, STEADY F1 12/1 on the Versa list; CoQ-PP_26-159: 12.77 %) also carries this product name.'),
 dict(k='ACC',prod='STEADY Amnesia Core 12 % THC / 1 % CBD',lc='VZ26/264 – 2/2 · 000029-V90 · 26-ACC-020',res='14.7',lim='10.8–13.2 (12 ± 10 %)',pp='P060122',cb='ACC102501',st='Amnesia Core Cut',tr='Tranche 2',md='09.01.2026',pk='18.02.2026',spec='QCSP_001_ACC-I_v.01: 10.80–13.19',coq='CoQ-PP_26-106 (18.09.2026): 12.09 % — Farmahem 220-1-К/26 (25.08.2026)',coq0='CoQ-PP_26-048 (06.06.2026): 12.91 % — Farmahem 031-5-К/26 (10.02.2026)',dev='+2.6 points (+22 %) against our CoQ',verd='Outside the Versa limit and our specification',alt=''),
 dict(k='PDY',prod='STEADY PDY 14 % THC / 1 % CBD (Payday)',lc='VZ26/267 – 2/2 · 000034-V90 · 26-PD-025',res='9.1',lim='12.6–15.4 (14 ± 10 %)',pp='P060372',cb='CC012603',st='Cash Cow',tr='Tranche 2',md='22.04.2026',pk='24.05.2026',spec='QCSP_001_CC-II_v.01: 12.65–15.34',coq='CoQ-PP_26-108 (18.09.2026): 14.76 % — Farmahem 220-29-К/26 (26.08.2026)',coq0='CoQ-PP_26-072 (06.06.2026): no cannabinoid result on the release CoQ',dev='−5.7 points (−38 %) against our CoQ',verd='Outside the Versa limit and our specification',alt=''),
]
NA='Н/П — резултатот е од лабораторијата на купувачот (LabCore), не од договорна лабораторија на PP ||| N/A — result from the customer’s laboratory (LabCore), not a PP contract laboratory'
for b in B:
  md=f'''<!--HEADERDATA
mk_title: Запис за истражување на OOx резултати од надворешна лабораторија — {b['pp']} ({b['cb']})
en_title: External Laboratory OOx Investigation Record — {b['pp']} ({b['cb']})
code: QCSOP019-A02 (QCT023)
version: 02
doctype: FORM
-->
# 1. ИДЕНТИФИКАЦИЈА НА OOx НАСТАН | OOx EVENT IDENTIFICATION
## 1.1 Класификација и ризик | Classification & risk
[[FORM]]
Тип на OOx ||| OOx type ||| ☒ OOS ☐ OOT ☐ OOE ☐ OOC
Ниво на ризик ||| Risk level ||| ☐ HIGH ☒ MEDIUM ☐ LOW (QCSOP 019 §6: External lab OOx)
[[/FORM]]
## 1.2 Надворешна лабораторија | External laboratory
[[FORM]]
Име на лабораторија ||| Laboratory name ||| LabCore d.o.o. (laboratory of the customer Versa Pharma)
Адреса ||| Address ||| Dunajska cesta 238e, 1000 Ljubljana, SI
ISO 17025 серт. бр. и рок ||| ISO 17025 cert. no. and expiry ||| _
Договор бр. ||| Contract no. ||| N/A — no contract with PP
Контакт лице ||| Contact person ||| Jaka Štirn, Head of Laboratory · jaka.stirn@labcore.eu · +386 30 920 094
[[/FORM]]
## 1.3 Производ и примерок | Product & sample
[[FORM]]
Име на производ (купувач) ||| Product name (customer) ||| {b['prod']}
ID на примерок (LabCore) ||| Sample ID (LabCore) ||| {b['lc']}
Број на серија (PP) ||| Batch number (PP) ||| {b['pp']} · cultivation batch {b['cb']} · {b['tr']}
Сорта ||| Cannabis strain ||| {b['st']}
Датум на производство / пакување ||| Manufacture / packaging date ||| {b['md']} / {b['pk']}
Статус на серија ||| Batch status ||| Released and delivered to Versa Pharma
Датум на земање / испраќање примерок ||| Sampling / dispatch date ||| _
[[/FORM]]
## 1.4 Информации за тест | Test information
[[FORM]]
Тест ||| Test ||| ☒ Cannabinoids — total Δ9-THC
Резултат (LabCore) ||| Result (LabCore) ||| {b['res']} % w/w
Метод ||| Method ||| LC (LabCore); method reference not provided
Граница на купувачот ||| Customer limit ||| {b['lim']} % w/w
Наша спецификација ||| Our specification ||| {b['spec']} % w/w
Отстапување ||| Deviation ||| {b['dev']}
Датум на тест ||| Test date ||| _
[[/FORM]]
## 1.5 Запис за истражување | Investigation record
[[FORM]]
Број на истражување ||| Investigation no. ||| PP-OOx-2026-_
Известување ||| Notification ||| Versa Pharma (S. Suljaković) to PP CEO; results table "Določen total d9THC"
Датум на детекција ||| Detection date ||| _
Датум на почеток ||| Start date ||| _
Целен завршеток ||| Target completion ||| _ (MEDIUM: 30 days)
[[/FORM]]
# 2. ВЕРИФИКАЦИЈА НА ЛАБОРАТОРИЈАТА | LABORATORY QUALIFICATION VERIFICATION
{NA}
[[FORM]]
Акредитација ISO/IEC 17025 и опфат ||| ISO/IEC 17025 accreditation and scope ||| _ (to be requested from LabCore)
[[/FORM]]
# 3. ПРЕГЛЕД НА ИЗВЕСТУВАЊЕТО И ДОКУМЕНТАЦИЈАТА | NOTIFICATION & DOCUMENTATION REVIEW
[[TABLE]]
Точка ~~ Item ||| Статус ~~ Status
Писмено известување ~~ Written notification ||| ☒ Да | Yes (results table)
CoA приложен ~~ CoA attached ||| ☒ Не ~~ No
Сурови податоци, хроматограми ~~ Raw data, chromatograms ||| ☒ Не ~~ No
Референца на метод, стандарди, SST ~~ Method reference, standards, SST ||| ☒ Не ~~ No
Известување во 24 ч ~~ Notification within 24 h ||| ☒ Н/П ~~ N/A (no QTA with LabCore)
[[/TABLE]]
# 4. ИСТРАЖУВАЊЕ ОД НАДВОРЕШНАТА ЛАБОРАТОРИЈА | EXTERNAL LABORATORY INVESTIGATION
LabCore не достави истражување. На 05.11.2026 праша за подготовката на примерокот: маса, хомогенизација, екстракција. ||| LabCore has not provided an investigation. On 05.11.2026 it asked about sample preparation: mass, homogenisation, extraction.
[[FORM]]
Резиме на истражувањето ||| Investigation summary ||| _
Коренска причина ||| Root cause ||| _
[[/FORM]]
# 5. ИНТЕРНА ПРОЦЕНКА | INTERNAL ASSESSMENT
[[FORM]]
Наш тековен CoQ ||| Our current CoQ ||| {b['coq']}
Наш претходен CoQ ||| Our earlier CoQ ||| {b['coq0']}
Интерен тест поминат ||| Internal test passing ||| ☒ Да | Yes — our accredited result conforms
Историски податоци ||| Historical data reviewed ||| ☒ Да | Yes — the six LabCore results differ from ours by 2.3–5.7 points
Поврзани серии ||| Related batches evaluated ||| ☒ Да | Yes — six T1/T2 lots reported OOS together
Интегритет при транспорт ||| Sample integrity in transport ||| _
Складирање кај купувачот ||| Storage at customer verified ||| _
Основа на пресметка ||| Reporting basis (dry / as is) ||| _ (CNP reports on dry mass; Farmahem % w/w)
[[/FORM]]
{b['alt'] and ('Забелешка: ' + 'идентификацијата на серијата треба да ја потврди купувачот. ||| Note: ' + b['alt'])}
## 5.1 Повторен тест / потврда | Retest / confirmation
[[TABLE]]
Тест ~~ Test ||| Лабораторија ~~ Lab ||| Датум ~~ Date ||| Резултат, % ~~ Result, % ||| Спец., % ~~ Spec, % ||| Статус ~~ Status
Оригинален ~~ Original ||| LabCore ||| _ ||| {b['res']} ||| {b['lim']} ||| OOS
Повторен тест 1 (задржан примерок) ~~ Retest 1 (retained sample) ||| Farmahem ||| _ ||| _ ||| {b['spec'].split(': ')[1]} ||| _
Повторен тест 2 ~~ Retest 2 ||| _ ||| _ ||| _ ||| _ ||| _
[[/TABLE]]
# 6. КОРЕНСКА ПРИЧИНА И ВЛИЈАНИЕ | ROOT CAUSE & IMPACT
[[FORM]]
Коренска причина ||| Root cause ||| ☐ External lab error ☐ External lab method ☐ PP sampling ☐ Sample integrity ☐ Product issue (true OOS) ☐ Unknown
Докази ||| Evidence ||| _
Влијание ||| Impact ||| ☐ No impact ☐ Within criteria ☐ Compromised ☐ Patient safety
Оправданост ||| Justification ||| _
[[/FORM]]
# 7. КАПА | CAPA
{NA}
[[FORM]]
КАПА на PP (ако е потребно) ||| PP CAPA (if needed) ||| _
[[/FORM]]
# 8. ДИСПОЗИЦИЈА НА СЕРИЈА | BATCH DISPOSITION
Серијата е веќе ослободена и испорачана; одлуката е за испорачан производ. ||| The batch is already released and delivered; the decision concerns delivered product.
[[FORM]]
Одлука ||| Decision ||| ☐ No action ☐ Customer notification ☐ Market action / recall ☐ Other: _
Научна оправданост ||| Scientific justification ||| _
[[/FORM]]
[[TABLE]]
Улога ~~ Role ||| Име ~~ Name ||| Потпис ~~ Signature ||| Датум ~~ Date
Раководител на КК ~~ Head of QC ||| Blagoj Nikolov ||| _ ||| _
Раководител на ОК (прегледал) ~~ Head of QA (reviewed) ||| Jovana Romevska ||| _ ||| _
КЛ (одобрил) ~~ QP (approved) ||| Sofija Petrova ||| _ ||| _
[[/TABLE]]
# 9. ЗАТВОРАЊЕ | CLOSURE
[[FORM]]
Резиме ||| Summary ||| _
[[/FORM]]
[[TABLE]]
Улога ~~ Role ||| Име ~~ Name ||| Потпис ~~ Signature ||| Датум ~~ Date
Раководител на КК ~~ Head of QC ||| Blagoj Nikolov ||| _ ||| _
Раководител на ОК ~~ Head of QA ||| Jovana Romevska ||| _ ||| _
КЛ ~~ QP ||| Sofija Petrova ||| _ ||| _
[[/TABLE]]
# 10. ЕФЕКТИВНОСТ НА КАПА | CAPA EFFECTIVENESS
Да се заврши 30–90 дена по имплементацијата. ||| Complete 30–90 days after implementation.
[[FORM]]
Раководител на ОК (верификувал) ||| Head of QA (verified) ||| _
[[/FORM]]
'''
  f=f"QCSOP019-A02_{b['pp']}_{b['cb'].replace('/','-')}_{b['k']}"
  open(f+'.md','w').write(md)
  r=subprocess.run(['python3','/home/user/letta-stack/pp-document-suite/scripts/build_from_md.py',f+'.md',f+'.docx'],capture_output=True,text=True); print(r.stdout.strip()[-80:],r.stderr[-300:])
  v=subprocess.run(['python3','/home/user/letta-stack/pp-document-suite/scripts/pp_verify.py',f+'.docx'],capture_output=True,text=True); print(v.stdout.strip().splitlines()[-1] if v.stdout else v.stderr[-300:])
