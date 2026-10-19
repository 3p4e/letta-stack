# QA's proposed specifications against ours — potency grades, nominals and ranges

Read only: nothing of ours changed. QA: folder `1TY-W5G2G8l7I6dLS1ITXH0e5WHcfruQW`, 51 documents, each read twice by independent agents. Ours: the 58 sheets on `potency_grades_2026-09-15.csv` (KVM4 builder); the Tranche 3 PDF holds 37 of them. Detail: `QA_SPEC_COMPARISON_2026-10-07.xlsx`.

## In short

- QA proposes **46 grades** in 46 documents, plus 20 in the two documents marked "NE".
- **18** are our grade exactly. QA writes the upper limit as nominal + tolerance and we write it as nominal + tolerance - 0.01; that counts as the same grade.
- **12** share a nominal with ours but not its tolerance or range.
- **16** are nominals we have no grade for, and **28** of our 58 grades have no QA document.
- **0** QA grades would hold no Total THC result on file (an empty range).
- QA's ranges are closed at both ends and set side by side, so neighbouring grades share a boundary value (17.00 is in both GG 16 and GG 18).
- Every QA document prints the code `…_v.01` with the footer `QCSP 001v03`, and most say "TEMPLATE" in the header.
- Of the 60 Tranche 3 certificates:
  - **29** fall in a QA grade of the same nominal as ours;
  - **20** fall in a QA grade of a different nominal;
  - **11** fall in no QA range.

## Per strain — ours | QA's

- **AB** — ours: AB-I 22.00 ± 2.20 (19.80 – 24.19) ·T3; AB-II 18.00 ± 1.80 (16.20 – 19.79) ·T3 | QA: 22.00 ± 2.20 (19.80 – 24.20) — same
  - results in no QA range: 16.93 release (AB092501)
- **ACC** — ours: ACC-I 12.00 ± 1.20 (10.80 – 13.19) | QA: 12.00 ± 1.20 (10.80 – 13.20) — same
- **BG** — ours: BG-I 26.00 ± 1.80 (24.20 – 27.79); BG-II 22.00 ± 2.20 (19.80 – 24.19) | QA: 26.00 ± 2.60 (23.40 – 28.60) — tolerance 2.60 vs ours 1.80; low 23.40 vs ours 24.20; high 28.60 vs ours 27.79
  - results in no QA range: 21.80 release (BG1024)
- **BSS** — ours: BSS-I 28.00 ± 1.93 (26.07 – 29.92) ·T3; BSS-II 24.00 ± 2.11 (21.89 – 26.10) ·T3; BSS-III 20.00 ± 1.89 (18.11 – 21.88) | QA: 20.00 ± 2.00 (18.00 – 22.00) — tolerance 2.00 vs ours 1.89; low 18.00 vs ours 18.11; high 22.00 vs ours 21.88; 26.00 ± 2.20 (23.80 – 28.20) — no grade of ours with this nominal
  - results in no QA range: 23.42 release (BSS1024_01)
- **CC** — ours: CC-I 17.00 ± 1.65 (15.35 – 18.64) ·T3; CC-II 14.00 ± 1.35 (12.65 – 15.34) ·T3 | QA: 13.00 ± 1.30 (11.70 – 14.30) — no grade of ours with this nominal; 16.00 ± 1.60 (14.40 – 17.60) — no grade of ours with this nominal
  - results in no QA range: 17.67 release (CC012601/1)
- **CF** — ours: CF-I 10.00 ± 1.00 (9.00 – 10.99) | QA: 10.00 ± 1.00 (9.00 – 11.00) — same
- **CJ** — ours: CJ-I 28.00 ± 1.60 (26.40 – 29.59) ·T3; CJ-II 24.00 ± 2.40 (21.60 – 26.39) ·T3; CJ-III 20.00 ± 1.60 (18.40 – 21.59) ·T3; CJ-IV 17.00 ± 1.40 (15.60 – 18.39); CJ-V 14.00 ± 1.40 (12.60 – 15.39) ·T3 | QA: 20.00 ± 2.00 (18.00 – 22.00) — tolerance 2.00 vs ours 1.60; low 18.00 vs ours 18.40; high 22.00 vs ours 21.59; 24.00 ± 2.00 (22.00 – 26.00) — tolerance 2.00 vs ours 2.40; low 22.00 vs ours 21.60; high 26.00 vs ours 26.39; 28.00 ± 2.00 (26.00 – 30.00) — tolerance 2.00 vs ours 1.60; low 26.00 vs ours 26.40; high 30.00 vs ours 29.59
  - QA ImB_Specification_CAPJUNKY20.docx (18.00–22.00) overlaps ImB_Specification_CAPJUNKY24.docx (22.00–26.00) · QA ImB_Specification_CAPJUNKY24.docx (22.00–26.00) overlaps ImB_Specification_CAPJUNKY28.docx (26.00–30.00) · results in no QA range: 14.93 release (CJ052501-2), 16.56 release (CJ062501-2)
- **CLE** — ours: CLE-I 8.00 ± 0.80 (7.20 – 8.79) | QA: no document
- **FB** — ours: FB-I 22.00 ± 2.20 (19.80 – 24.19) ·T3; FB-II 18.00 ± 1.80 (16.20 – 19.79) ·T3; FB-III 15.00 ± 1.20 (13.80 – 16.19); FB-IV 12.00 ± 1.20 (10.80 – 13.19) | QA: 18.00 ± 1.00 (17.00 – 19.00) — tolerance 1.00 vs ours 1.80; low 17.00 vs ours 16.20; high 19.00 vs ours 19.79; 20.00 ± 1.00 (19.00 – 21.00) — no grade of ours with this nominal
  - QA ImB_Specification_FATBASTARD18.docx (17.00–19.00) overlaps ImB_Specification_FATBASTARD20.docx (19.00–21.00) · results in no QA range: 12.39 release (FB032601), 14.68 release (FB012601/1), 14.99 release (FB042601), 16.69 release (FB112501)
- **GG** — ours: GG-I 18.00 ± 1.77 (16.23 – 19.76) ·T3; GG-II 15.00 ± 1.23 (13.77 – 16.22) ·T3 | QA: 16.00 ± 1.00 (15.00 – 17.00) — no grade of ours with this nominal; 18.00 ± 1.00 (17.00 – 19.00) — tolerance 1.00 vs ours 1.77; low 17.00 vs ours 16.23; high 19.00 vs ours 19.76; 20.00 ± 1.00 (19.00 – 21.00) — no grade of ours with this nominal
  - QA ImB_Specification_GORILLAGLUE16.docx (15.00–17.00) overlaps ImB_Specification_GORILLAGLUE18.docx (17.00–19.00) · QA ImB_Specification_GORILLAGLUE18.docx (17.00–19.00) overlaps ImB_Specification_GORILLAGLUE20.docx (19.00–21.00) · results in no QA range: 13.34 standalone (GG1024)
- **GP** — ours: GP-I 28.00 ± 2.00 (26.00 – 29.99) ·T3; GP-II 24.00 ± 2.00 (22.00 – 25.99) ·T3; GP-III 20.00 ± 2.00 (18.00 – 21.99) ·T3; GP-IV 16.00 ± 1.60 (14.40 – 17.59) | QA: 16.00 ± 1.00 (15.00 – 17.00) — tolerance 1.00 vs ours 1.60; low 15.00 vs ours 14.40; high 17.00 vs ours 17.59; 18.00 ± 1.00 (17.00 – 19.00) — no grade of ours with this nominal; 24.00 ± 1.00 (23.00 – 25.00) — tolerance 1.00 vs ours 2.00; low 23.00 vs ours 22.00; high 25.00 vs ours 25.99; 26.00 ± 1.00 (25.00 – 27.00) — no grade of ours with this nominal; 30.00 ± 3.00 (27.00 – 33.00) — no grade of ours with this nominal
  - QA ImB_Specification_GRAPEPIE16.docx (15.00–17.00) overlaps ImB_Specification_GRAPEPIE18.docx (17.00–19.00) · QA ImB_Specification_GRAPEPIE24.docx (23.00–25.00) overlaps ImB_Specification_GRAPEPIE26.docx (25.00–27.00) · QA ImB_Specification_GRAPEPIE26.docx (25.00–27.00) overlaps ImB_Specification_GRAPEPIE30.docx (27.00–33.00) · results in no QA range: 13.16 stability (GP0824_02), 14.83 release (GP082501/2), 14.99 stability (GP0824_03), 19.81 release (GP072501/2), 20.79 release (GP0824_01), 21.29 release (GP082501/1), 21.31 stability (GP0824_02), 21.36 release (GP072501-1), 22.61 retest (GP0824_02), 22.83 stability (GP062501)
- **GRC** — ours: GRC-I 12.00 ± 1.00 (11.00 – 12.99); GRC-II 10.00 ± 1.00 (9.00 – 10.99); GRC-IV 7.00 ± 0.70 (6.30 – 7.69) ·T3 | QA: 8.00 ± 0.80 (7.20 – 8.80) — no grade of ours with this nominal; 10.00 ± 1.00 (9.00 – 11.00) — same
  - results in no QA range: 7.05 release (GRC102501/1), 11.53 release (GRC102501/2), 11.53 standalone (GRC102501_2)
- **HPA** — ours: HPA-I 22.00 ± 2.20 (19.80 – 24.19); HPA-II 18.00 ± 1.80 (16.20 – 19.79); HPA-III 15.00 ± 1.20 (13.80 – 16.19) | QA: 18.00 ± 1.80 (16.20 – 19.80) — same; 22.00 ± 2.20 (19.80 – 24.20) — same
  - QA ImB_Specification_HPA18.docx (16.20–19.80) overlaps ImB_Specification_HPA22.docx (19.80–24.20) · results in no QA range: 14.97 release (HPA1024), 14.97 release (HPA1024), 14.97 standalone (HPA1024)
- **J31** — ours: J31-I 26.00 ± 1.80 (24.20 – 27.79) ·T3; J31-II 22.00 ± 2.20 (19.80 – 24.19) ·T3; J31-III 18.00 ± 1.80 (16.20 – 19.79) | QA: 18.00 ± 1.80 (16.20 – 19.80) — product code J31_THC18CBD1 vs ours J31_THC18 : CBD1; Product code 'J31_THC18CBD1' has no ':' between THC18 and CBD1 (raw runs '31','_THC','18','CBD1'). The other QA files print one, e.g. 'J31_THC24:CBD1'. Its nominal (18) matches the sheet.; 24.00 ± 2.40 (21.60 – 26.40) — no grade of ours with this nominal
  - results in no QA range: 19.84 release (J31122501), 20.21 retest (J31112501)
- **JD** — ours: JD-I 22.00 ± 2.20 (19.80 – 24.19) ·T3; JD-II 18.00 ± 1.80 (16.20 – 19.79) ·T3; JD-III 15.00 ± 1.20 (13.80 – 16.19) | QA: 14.00 ± 1.00 (13.00 – 15.00) — no grade of ours with this nominal; 16.00 ± 1.00 (15.00 – 17.00) — no grade of ours with this nominal; 20.00 ± 2.00 (18.00 – 22.00) — no grade of ours with this nominal
  - QA ImB_Specification_JD14.docx (13.00–15.00) overlaps ImB_Specification_JD16.docx (15.00–17.00) · results in no QA range: 17.09 retest (JD012603/02V)
- **KC** — ours: KC-I 18.00 ± 1.80 (16.20 – 19.79) | QA: 18.00 ± 1.80 (16.20 – 19.80) — same
- **MB** — ours: MB-I 18.00 ± 1.80 (16.20 – 19.79) ·T3 | QA: 18.00 ± 1.80 (16.20 – 19.80) — same
- **OPM** — ours: OPM-I 20.00 ± 1.40 (18.60 – 21.39); OPM-II 17.00 ± 1.60 (15.40 – 18.59) ·T3; OPM-III 14.00 ± 1.40 (12.60 – 15.39) ·T3; OPM-IV 10.00 ± 1.00 (9.00 – 10.99) ·T3; OPM-V 8.00 ± 0.80 (7.20 – 8.79) ·T3 | QA: 8.00 ± 0.80 (7.20 – 8.80) — same; 10.00 ± 1.00 (9.00 – 11.00) — same; 18.00 ± 1.80 (16.20 – 19.80) — no grade of ours with this nominal; 22.00 ± 2.20 (19.80 – 24.20) — no grade of ours with this nominal
  - QA ImB_Specification_OPM18.docx (16.20–19.80) overlaps ImB_Specification_OPM22.docx (19.80–24.20) · results in no QA range: 1.87 release (OPM1024_02), 14.16 release (OPM052501), 15.38 release (OMP1024_01)
- **PM** — ours: PM-I 14.00 ± 1.00 (13.00 – 14.99); PM-II 12.00 ± 1.00 (11.00 – 12.99) ·T3; PM-III 10.00 ± 1.00 (9.00 – 10.99) ·T3 | QA: 10.00 ± 1.00 (9.00 – 11.00) — same; 12.00 ± 1.00 (11.00 – 13.00) — same
  - QA ImB_Specification_PM10.docx (9.00–11.00) overlaps ImB_Specification_PM12.docx (11.00–13.00) · results in no QA range: 13.33 release (PM112501), 14.06 release (PM092501)
- **PUM** — ours: PUM-I 14.00 ± 1.40 (12.60 – 15.39) | QA: 14.00 ± 1.40 (12.60 – 15.40) — product code PUMTHC14:CBD1 vs ours PUM_THC14 : CBD1; Product code 'PUMTHC14:CBD1' has no '_' between PUM and THC14 (raw runs 'PUM','THC','1','4',':CBD1'). Every other QA file prints one, e.g. 'KC_THC18:CBD1'. Its nominal (14) matches the sheet.
- **SCR** — ours: SCR-I 22.00 ± 2.20 (19.80 – 24.19) ·T3; SCR-II 18.00 ± 1.80 (16.20 – 19.79) ·T3 | QA: 18.00 ± 1.80 (16.20 – 19.80) — same; 22.00 ± 2.20 (19.80 – 24.20) — same
  - QA ImB_Specification_SCR18.docx (16.20–19.80) overlaps ImB_Specification_SCR22.docx (19.80–24.20)
- **SJ** — ours: SJ-I 12.00 ± 1.00 (11.00 – 12.99) ·T3; SJ-II 10.00 ± 1.00 (9.00 – 10.99) ·T3 | QA: 10.00 ± 1.00 (9.00 – 11.00) — same; 12.00 ± 1.00 (11.00 – 13.00) — same
  - QA ImB_Specification_SJ10.docx (9.00–11.00) overlaps ImB_Specification_SJ12.docx (11.00–13.00)
- **WC** — ours: WC-I 26.00 ± 2.60 (23.40 – 28.59) ·T3; WC-II 22.00 ± 1.40 (20.60 – 23.39) ·T3 | QA: 22.00 ± 2.20 (19.80 – 24.20) — tolerance 2.20 vs ours 1.40; low 19.80 vs ours 20.60; high 24.20 vs ours 23.39; 26.00 ± 2.60 (23.40 – 28.60) — same
  - QA ImB_Specification_WC22.docx (19.80–24.20) overlaps ImB_Specification_WC26.docx (23.40–28.60)
- **WED** — ours: WED-I 26.00 ± 2.60 (23.40 – 28.59) ·T3; WED-II 22.00 ± 1.40 (20.60 – 23.39) ·T3 | QA: 26.00 ± 2.60 (23.40 – 28.60) — same
  - results in no QA range: 22.05 release (WED102501)

## The two documents marked "NE" (read, not counted above)

- NE - Specifikacii Transa 1 27.08.2026.pdf: BG 26.00 ± 2.60 (23.40 – 28.60)
- NE - Specifikacii Transa 1 27.08.2026.pdf: BSS 24.00 ± 1.99 (22.01 – 25.99)
- NE - Specifikacii Transa 1 27.08.2026.pdf: CJ 20.00 ± 2.00 (18.00 – 22.00)
- NE - Specifikacii Transa 1 27.08.2026.pdf: CJ 24.00 ± 1.00 (23.00 – 25.00)
- NE - Specifikacii Transa 1 27.08.2026.pdf: FB 18.00 ± 0.85 (17.15 – 18.85)
- NE - Specifikacii Transa 1 27.08.2026.pdf: GG 16.00 ± 1.00 (15.00 – 17.00)
- NE - Specifikacii Transa 1 27.08.2026.pdf: GG 18.00 ± 0.99 (17.01 – 18.99)
- NE - Specifikacii Transa 1 27.08.2026.pdf: GP 16.00 ± 1.60 (14.40 – 17.60) — Range 14.40 – 17.60 % overlaps GP-THC18 (page 16, 16.20 – 19.80 %) over 16.20 – 17.60 %
- NE - Specifikacii Transa 1 27.08.2026.pdf: GP 18.00 ± 1.80 (16.20 – 19.80) — Spec code 'QCSP_001_GP-THC18_v.01' uses 'THC18' where every other page uses a Roman-numeral grade; Range 16.20 – 19.80 % overlaps GP-V (page 18, 14.40 – 17.60 %) over 16.20 – 17.60 %
- NE - Specifikacii Transa 1 27.08.2026.pdf: GP 24.00 ± 1.39 (22.61 – 25.39)
- NE - Specifikacii Transa 1 27.08.2026.pdf: HPA 18.00 ± 1.00 (17.00 – 19.00)
- NE - Specifikacii Transa 1 27.08.2026.pdf: HPA 22.00 ± 1.00 (21.00 – 23.00)
- NE - ImB_Specification_J31-22.docx: J31 18.00 ± 1.80 (16.20 – 19.80) — The filename says 22 but the sheet prints 18 % everywhere: title line '18 % ± 1.80 %', product code THC18 and range 16.20 – 19.80 %.; Every printed potency field matches ImB_Specification_J31-18.docx: nominal, tolerance, range, product code and spec code QCSP001_J31-II_v.01. Two files claim grade J31-II.; Product code 'J31_THC18CBD1' has no ':' between THC18 and CBD1.
- NE - Specifikacii Transa 1 27.08.2026.pdf: J31 18.00 ± 1.80 (16.20 – 19.80)
- NE - Specifikacii Transa 1 27.08.2026.pdf: JD 20.00 ± 2.00 (18.00 – 22.00)
- NE - Specifikacii Transa 1 27.08.2026.pdf: OPM 8.00 ± 0.80 (7.20 – 8.80)
- NE - Specifikacii Transa 1 27.08.2026.pdf: OPM 18.00 ± 1.80 (16.20 – 19.80)
- NE - Specifikacii Transa 1 27.08.2026.pdf: OPM 22.00 ± 2.19 (19.81 – 24.19)
- NE - Specifikacii Transa 1 27.08.2026.pdf: PM 12.00 ± 0.99 (11.01 – 12.99)
- NE - Specifikacii Transa 1 27.08.2026.pdf: SCR 18.00 ± 1.80 (16.20 – 19.80)

## Where the second reading corrected the first (46 fields; the second is used)

- ImB_Specification_OPM10.docx — other_potency_mentions (Total CBN row): first 'Total CBN | Вкупен CBN — ≤ 1.0%, w/w (method column left out)', second 'Total CBN | Вкупен CBN — Ph. Eur. 2.2.29 (HPLC)CBN + CBNA x 0.876 — ≤ 1.0%, w/w'
- ImB_Specification_OPM18.docx — other_potency_mentions (Total CBN row): first 'Total CBN | Вкупен CBN — ≤ 1.0%, w/w', second 'Total CBN | Вкупен CBN — Ph. Eur. 2.2.29 (HPLC)CBN + CBNA x 0.876 — ≤ 1.0%, w/w'
- ImB_Specification_OPM22.docx — other_potency_mentions (Total CBN row): first 'Total CBN | Вкупен CBN — ≤ 1.0%, w/w', second 'Total CBN | Вкупен CBN — Ph. Eur. 2.2.29 (HPLC)CBN + CBNA x 0.876 — ≤ 1.0%, w/w'
- ImB_Specification_CAPJUNKY20.docx — other_potency_mentions (Total CBN row): first 'Total CBN | Вкупен CBN — ≤ 1.0%, w/w', second 'Total CBN | Вкупен CBN — Ph. Eur. 2.2.29 (HPLC)CBN + CBNA x 0.876 — ≤ 1.0%, w/w'
- ImB_Specification_CAPJUNKY24.docx — other_potency_mentions (Total CBN row): first 'Total CBN | Вкупен CBN — ≤ 1.0%, w/w', second 'Total CBN | Вкупен CBN — Ph. Eur. 2.2.29 (HPLC)CBN + CBNA x 0.876 — ≤ 1.0%, w/w'
- ImB_Specification_CAPJUNKY28.docx — other_potency_mentions (Total CBN row): first 'Total CBN | Вкупен CBN — ≤ 1.0%, w/w', second 'Total CBN | Вкупен CBN — Ph. Eur. 2.2.29 (HPLC)CBN + CBNA x 0.876 — ≤ 1.0%, w/w'
- ImB_Specification_CASHCOW13.docx — other_potency_mentions (Total CBN row): first 'Total CBN | Вкупен CBN — ≤ 1.0%, w/w', second 'Total CBN | Вкупен CBN — Ph. Eur. 2.2.29 (HPLC)CBN + CBNA x 0.876 — ≤ 1.0%, w/w'
- ImB_Specification_CASHCOW16.docx — other_potency_mentions (Total CBN row): first 'Total CBN | Вкупен CBN — ≤ 1.0%, w/w', second 'Total CBN | Вкупен CBN — Ph. Eur. 2.2.29 (HPLC)CBN + CBNA x 0.876 — ≤ 1.0%, w/w'
- ImB_Specification_BSS20.docx — notes: first "The page header still reads 'Purely Plant — Product Specification — Intermediate", second "That line is not printed on the page. It is the file's Title property, and the h"
- ImB_Specification_BSS26.docx — notes: first "The header still reads '… — TEMPLATE'; comments and tracked changes were not che", second "'TEMPLATE' is only the file's Title property and the header is empty. There are "
- ImB_Specification_BLUEGELATO.docx — notes: first "The header still reads '… — TEMPLATE'; comments and tracked changes were not che", second "'TEMPLATE' is only the file's Title property and the header is empty. There are "
- ImB_Specification_APPLES&BANANA.docx — notes: first "The header still reads '… — TEMPLATE'; comments and tracked changes were not che", second "'TEMPLATE' is only the file's Title property. This file has no header part at al"
- ImB_Specification_ACC12.docx — notes: first "The header still reads '… — TEMPLATE'; comments and tracked changes were not che", second "'TEMPLATE' is only the file's Title property and the header is empty. There are "
- ImB_Specification_FATBASTARD18.docx — notes: first "The header still reads '… — TEMPLATE'; comments and tracked changes were not che", second "'TEMPLATE' is only the file's Title property and the header is empty. There are "
- ImB_Specification_FATBASTARD20.docx — notes: first "The header still reads '… — TEMPLATE'; comments and tracked changes were not che", second "'TEMPLATE' is only the file's Title property and the header is empty. There are "
- ImB_Specification_BSS20.docx — potency_text: first 'BLUE SUNSET SHERBET 20 % ± 2.0 % | POTENCY ЈАЧИНА 18.00 – 22.0 %', second 'BLUE SUNSET SHERBET  20 % ± 2.0 % | POTENCY ЈАЧИНА 18.00 – 22.0 %. Two spaces ar'
- ImB_Specification_BSS26.docx — potency_text: first 'BLUE SUNSET SHERBET 26 % ± 2.2 % | POTENCY ЈАЧИНА 23.80 – 28.2 %', second 'BLUE SUNSET SHERBET  26 % ± 2.2 % | POTENCY ЈАЧИНА 23.80 – 28.2 % (two spaces; n'
- ImB_Specification_BLUEGELATO.docx — potency_text: first 'BLUE GELATO 26 % ± 2.6 % | POTENCY ЈАЧИНА 23.40 – 28.6 %', second 'BLUE GELATO  26 % ± 2.6 % | POTENCY ЈАЧИНА 23.40 – 28.6 % (two spaces; numbers a'
- ImB_Specification_APPLES&BANANA.docx — potency_text: first 'APPLES & BANANA 22 % ± 2.2 % | POTENCY ЈАЧИНА 19.80 – 24.20 %', second 'APPLES & BANANA  22 % ± 2.2 % | POTENCY ЈАЧИНА 19.80 – 24.20 % (two spaces; numb'
- ImB_Specification_ACC12.docx — potency_text: first 'AMNESIA CORE CUT 12 % ± 1.2 % | POTENCY ЈАЧИНА 10.80 – 13.2 %', second 'AMNESIA CORE CUT  12 % ± 1.2 % | POTENCY ЈАЧИНА 10.80 – 13.2 % (two spaces; numb'
- ImB_Specification_FATBASTARD18.docx — potency_text: first 'FAT BASTARD 18 % ± 1.0 % | POTENCY ЈАЧИНА 17.00 – 19.00 %', second 'FAT BASTARD  18 % ± 1.0 % | POTENCY ЈАЧИНА 17.00 – 19.00 % (two spaces; numbers '
- ImB_Specification_FATBASTARD20.docx — potency_text: first 'FAT BASTARD 20 % ± 1.0 % | POTENCY ЈАЧИНА 19.00 – 21.00 %', second 'FAT BASTARD  20 % ± 1.0 % | POTENCY ЈАЧИНА 19.00 – 21.00 % (two spaces; numbers '
- ImB_Specification_BSS20.docx — internal_inconsistencies: first "Listed 'The nominal, tolerance and range agree (20 ± 2.0 = 18.00 – 22.0).' as an", second 'That is a check that passed, not an inconsistency, so it moved to notes. The oth'
- ImB_Specification_BSS26.docx — internal_inconsistencies / other_potency_mentions: first "Listed 'The nominal, tolerance and range agree (26 ± 2.2 = 23.80 – 28.2)' as an ", second 'The agreement check moved to notes. The Total CBD assay row was added to other_p'
- ImB_Specification_BLUEGELATO.docx — internal_inconsistencies / other_potency_mentions: first "Listed 'The nominal, tolerance and range agree (26 ± 2.6 = 23.40 – 28.6)' as an ", second 'The agreement check moved to notes. The Total CBD assay row was added. No value '
- ImB_Specification_APPLES&BANANA.docx — internal_inconsistencies / other_potency_mentions: first "Listed 'The nominal, tolerance and range agree (22 ± 2.2 = 19.80 – 24.20)' as an", second 'The agreement check moved to notes. The Total CBD assay row was added. No value '
- ImB_Specification_ACC12.docx — internal_inconsistencies / other_potency_mentions: first "Listed 'The nominal, tolerance and range agree (12 ± 1.2 = 10.80 – 13.2)' as an ", second 'The agreement check moved to notes. The Total CBD assay row was added. No value '
- ImB_Specification_FATBASTARD18.docx — internal_inconsistencies / other_potency_mentions: first "Listed 'The nominal, tolerance and range agree (18 ± 1.0 = 17.00 – 19.00)' as an", second 'The agreement check moved to notes. The Total CBD assay row was added. No value '
- ImB_Specification_FATBASTARD20.docx — internal_inconsistencies / other_potency_mentions: first "Listed 'The nominal, tolerance and range agree (20 ± 1.0 = 19.00 – 21.00)' as an", second 'The agreement check moved to notes. The Total CBD assay row was added. No value '
- ImB_Specification_J31-18.docx — notes: first "Header line still reads 'Purely Plant — Product Specification — Intermediate Bul", second "'…— TEMPLATE' is not printed on the sheet. It is the Word document-properties ti"
- NE - ImB_Specification_J31-22.docx — notes: first "Header still reads '— TEMPLATE'. Word comments and tracked changes were not insp", second "'— TEMPLATE' is the document-properties title, not printed. There are no comment"
- ImB_Specification_J31-24.docx — notes: first "Header still reads '— TEMPLATE'.", second 'Not printed. It is the document-properties title. No comments, tracked changes o'
- ImB_Specification_JD14.docx — notes: first "Header still reads '— TEMPLATE'.", second 'Not printed. It is the document-properties title. No comments, tracked changes o'
- ImB_Specification_JD16.docx — notes: first "Header still reads '— TEMPLATE'.", second 'Not printed. It is the document-properties title. No comments, tracked changes o'
- ImB_Specification_JD20.docx — notes: first "Header still reads '— TEMPLATE'.", second 'Not printed. It is the document-properties title. No comments, tracked changes o'
- ImB_Specification_KC18.docx — notes: first "Header still reads '— TEMPLATE'.", second 'Not printed. It is the document-properties title. No comments, tracked changes o'
- ImB_Specification_PUM14.docx — notes: first "Header still reads '— TEMPLATE'.", second 'Not printed. It is the document-properties title. No comments, tracked changes o'
- ImB_Specification_CF10.docx — potency_text: first 'CHEM FLYER 10 % ± 1.0 % · POTENCY ЈАЧИНА 9.00 – 11.0 %', second 'CHEM FLYER  10 % ± 1.0 % · POTENCY ЈАЧИНА 9.00 – 11.0 %'
- ImB_Specification_HPA18.docx — potency_text: first 'HIGH PRO AMNESIA 18 % ± 1.8 % · POTENCY ЈАЧИНА 16.20 – 19.8 %', second 'HIGH PRO AMNESIA  18 % ± 1.8 % · POTENCY ЈАЧИНА 16.20 – 19.8 %'
- ImB_Specification_HPA22.docx — potency_text: first 'HIGH PRO AMNESIA 22 % ± 2.2 % · POTENCY ЈАЧИНА 19.80 – 24.2 %', second 'HIGH PRO AMNESIA  22 % ± 2.2 % · POTENCY ЈАЧИНА 19.80 – 24.2 %'
- ImB_Specification_PM12.docx — cbd_text: first 'Assay — Total CBD* | Анализа — вкупен CBD · CBD + CBDA x 0.877 · ≤ 1.0%, w/w', second 'Assay — Total CBD* | Анализа — вкупен CBD · Ph. Eur. 2.2.29 (HPLC)CBD + CBDA x 0'
- ImB_Specification_SJ12.docx — notes (tolerance basis): first 'No remark on the tolerance basis (the first read called WC/WED/SCR/MB tolerances', second 'SJ12 and PM12 print ± 1.00 on a 12 % nominal. Every other sheet in this group pr'
- ImB_Specification_BLANK_TEMPLATE.docx — version_and_dates / signatories (location of the review-check-approve block, effective date and 'QCSP 001v03'): first "Header table holds name, QCSP 001, Version 03 and 'Ефективна дата / Effective da", second "The header (first-page only) holds only the document name, 'Code of document: QC"
- NE - Specifikacii Transa 1 27.08.2026.pdf — entries[page 2 HPA-I, page 5 HPA-III].internal_inconsistencies: first "Page 2: 'No HPA-II in this file: HPA-I (22 %) and HPA-III (18 %) only'. Page 5: ", second 'Not an internal inconsistency. Both pages agree with themselves (nominal ± toler'
- Overview of Specifications per cultivar.xlsx — notes (tolerance-convention list): first "±10 % of nominal: 'MB, GP-I, BG, HPA, OPM-I/II, WC, AB, SCR, CC, ACC, J31, KC, P", second 'BSS-II and JD-I are also ±10 % of nominal (20 ± 2.0), and the list should includ'
- ImB_Specification_BLANK_TEMPLATE BN.docx — notes (doubled characters): first "'The extracted text doubles some characters (0011, IINNDDIICCAA), which looks li", second 'The doubling is in the file itself. document.xml stores each bold-label characte'
