# Does any certificate of quality print a result the record has replaced?

The sweep of 16.09.2026, over 172 certificates of quality and 93 register blocks. Run it with `python3 deliverables/qc_gap_analysis/result_supersession.py`.

## 1 · A printed result a later certificate contradicts

114 comparisons — every (certificate, determination, later certificate for the same lot) triple where the later certificate was on file the day the certificate of quality issues. **51 contradict.**

**A zero is only as good as what could be compared**, so the coverage is beside it. A lot with one document for a determination can never contradict itself: the certificate's value rests on that one document and the sweep has nothing to hold it against.

| # | parameter | documents on file | lots with two or more | contradictions |
|---|---|---:|---:|---:|
| #4 | Total Δ9-THC | 160 | 64 | 2 |
| #5 | Total CBD | 160 | 64 | 1 |
| #6 | Total CBN | 106 | 12 | 0 |
| #8 | Loss on drying | 75 | 4 | 4 |
| #9.1 | TAMC | 85 | 20 | 19 |
| #9.2 | TYMC | 85 | 20 | 19 |
| #9.3 | Bile-tolerant GNB | 85 | 20 | 6 |
| #9.4 | Salmonella | 85 | 20 | 0 |
| #9.5 | E. coli | 85 | 20 | 0 |
| #10.1 | Aflatoxin B1 | 54 | 1 | 0 |
| #10.2 | Aflatoxins Σ | 107 | 33 | 0 |
| #10.3 | Ochratoxin A | 54 | 1 | 0 |
| #11.1 | Pb | 54 | 1 | 0 |
| #11.2 | Cd | 54 | 1 | 0 |
| #11.3 | As | 54 | 1 | 0 |
| #11.4 | Hg | 54 | 1 | 0 |
| #12 | Pesticides | 55 | 2 | 0 |

#10.1 Aflatoxin B1, #10.3 Ochratoxin A, #11.1 Pb, #11.2 Cd, #11.3 As, #11.4 Hg, #12 Pesticides were compared on 1 lot, 1 lot, 1 lot, 1 lot, 1 lot, 1 lot, 2 lots only — a zero there is real but thin.

Where the comparison was genuinely available and returned nothing, it is worth stating plainly: #6 Total CBN over 12 lots; #9.4 Salmonella over 20 lots; #9.5 E. coli over 20 lots; #10.2 Aflatoxins Σ over 33 lots.

The 51 split in two, and only the second half is an open question:

### cited as covering the determination — 8

The certificate cites the document as the one that covers the determination. Every one of these is a RELEASE certificate citing the RELEASE result while a later retest sits on file — which is the owner's ruling of 10.09.2026 working exactly as written: the earliest result for a parameter is the release result, and a later one belongs to a retest certificate, not to this one. Nothing to repair.

| certificate | series | lot | # | parameter | prints | from | superseded by |
|---|---|---|---|---|---|---|---|
| CoQ-PP_26-007 | initial release | P050022 | #8 | Loss on drying | 7.21 | ППК25139 (22.05.2025) | ППК25174 = 6.51 (10.07.2025) |
| CoQ-PP_26-056 | initial release — predicted | J31112501 | #8 | Loss on drying | 8.4 | 051-5-ГС/26 (02.03.2026) | 100-1-ГС/26 = 7.6 (09.04.2026) |
| CoQ-PP_26-026 | initial release — predicted | P050202 | #9.1 | TAMC | 1.3 × 10⁴ | 1009/1813/25 (08.10.2025) | 1155/2056/25 = 600 (24.11.2025) |
| CoQ-PP_26-026 | initial release — predicted | P050202 | #9.2 | TYMC | 4.2 × 10³ | 1009/1813/25 (08.10.2025) | 1155/2056/25 = 400 (24.11.2025) |
| CoQ-PP_26-026 | initial release — predicted | P050202 | #9.3 | Bile-tolerant GNB | < 10³ and > 10² | 1009/1813/25 (08.10.2025) | 1155/2056/25 = < 10 (24.11.2025) |
| CoQ-PP_26-007 | initial release | P050022 | #4 | Total Δ9-THC | 23.79 | ППК25139 (22.05.2025) | ППК25174 = 23.19 (10.07.2025) |
| CoQ-PP_26-056 | initial release — predicted | J31112501 | #4 | Total Δ9-THC | 25.27 | 051-5-К/26 (04.03.2026) | 100-1-К/26 = 20.21 (09.04.2026) |
| CoQ-PP_26-007 | initial release | P050022 | #5 | Total CBD | 0.10 | ППК25139 (22.05.2025) | ППК25174 = 0.07 (10.07.2025) |

### carried forward — 43

The certificate carries the result forward from the initial testing because the campaign it rests on did not retest that determination — the ruling of 15.09.2026. The question OI-38 puts to the owner is whether *forward from the initial testing* should mean the initial result or the latest result on file, and these are the rows it decides.

| certificate | series | lot | # | parameter | prints | from | superseded by |
|---|---|---|---|---|---|---|---|
| CoQ-PP_26-095 | additional testing (12-month) | P050022 | #8 | Loss on drying | 7.21 | ППК25139 (22.05.2025) | ППК25174 = 6.51 (10.07.2025) |
| CoQ-PP_26-153 | additional testing (12-month) — predicted | J31112501 | #8 | Loss on drying | 8.4 | 051-5-ГС/26 (02.03.2026) | 100-1-ГС/26 = 7.6 (09.04.2026) |
| CoQ-PP_26-137 | additional testing (12-month) — predicted | P050122 | #9.1 | TAMC | < 10 | 626/1127/25 (02.07.2025) | 561/1092/26 = 10 (01.09.2026) |
| CoQ-PP_26-139 | additional testing (12-month) — predicted | CC112501 | #9.1 | TAMC | 3,8 × 10³ | 311/0555/26 (28.04.2026) | 543/1074/26 = 1,6×10^3 (31.08.2026) |
| CoQ-PP_26-140 | additional testing (12-month) — predicted | P050172 | #9.1 | TAMC | 9 × 10³ | 947/1685/25 (17.09.2025) | 558/1089/26 = < 10 (01.09.2026) |
| CoQ-PP_26-141 | additional testing (12-month) — predicted | P050252 | #9.1 | TAMC | 4.5 × 10³ | 1218/2169/25 (01.12.2025) | 556/1087/26 = < 10 (01.09.2026) |
| CoQ-PP_26-142 | additional testing (12-month) — predicted | CJ1024 | #9.1 | TAMC | 8.4 × 10³ | 164/0272/25 (24.02.2025) | 565/1096/26 = < 10 (01.09.2026) |
| CoQ-PP_26-145 | additional testing (12-month) — predicted | FB112501 | #9.1 | TAMC | 3,9 × 10³ | 312/0556/26 (28.04.2026) | 542/1073/26 = 3×10^3 (31.08.2026) |
| CoQ-PP_26-146 | additional testing (12-month) — predicted | GG012601 | #9.1 | TAMC | 1 × 10⁴ | 310/0554/26 (28.04.2026) | 541/1072/26 = 2,2×10³ (31.08.2026) |
| CoQ-PP_26-147 | additional testing (12-month) — predicted | P050012 | #9.1 | TAMC | 2.1 × 10⁴ | 472/0863/25 (22.05.2025) | 564/1095/26 = < 10 (01.09.2026) |
| CoQ-PP_26-148 | additional testing (12-month) — predicted | GG112501 | #9.1 | TAMC | 5,1 × 10³ | 304/0548/26 (28.04.2026) | 545/1076/26 = 5×10³ (31.08.2026) |
| CoQ-PP_26-149 | additional testing (12-month) — predicted | P050202 | #9.1 | TAMC | 1.3 × 10⁴ | 1009/1813/25 (08.10.2025) | 1155/2056/25 = 600 (24.11.2025) |
| CoQ-PP_26-149 | additional testing (12-month) — predicted | P050202 | #9.1 | TAMC | 1.3 × 10⁴ | 1009/1813/25 (08.10.2025) | 557/1088/26 = < 10 (01.09.2026) |
| CoQ-PP_26-150 | additional testing (12-month) — predicted | P050292 | #9.1 | TAMC | 6 × 10³ | 1228/2194/25 (05.12.2025) | 553/1084/26 = < 10 (01.09.2026) |
| CoQ-PP_26-151 | additional testing (12-month) — predicted | P050102 | #9.1 | TAMC | 4.2 × 10³ | 318/0585/25 (14.04.2025) | 562/1093/26 = < 10 (01.09.2026) |
| CoQ-PP_26-154 | additional testing (12-month) — predicted | J31122501 | #9.1 | TAMC | 850 | 231/0394/26 (Racno trimiran cvet) (07.04.2026) | 544/1075/26 = 1×10³ (31.08.2026) |
| CoQ-PP_26-155 | additional testing (12-month) — predicted | JD012601 | #9.1 | TAMC | 1,9 × 10³ | 309/0553/26 (28.04.2026) | 540/1071/26 = 2,2×10³ (31.08.2026) |
| CoQ-PP_26-157 | additional testing (12-month) — predicted | P050132 | #9.1 | TAMC | 1.2 × 10⁴ | 904/1589/25 (02.09.2025) | 560/1091/26 = < 10 (01.09.2026) |
| CoQ-PP_26-159 | additional testing (12-month) — predicted | P050272 | #9.1 | TAMC | 110 | 1220/2171/25 (01.12.2025) | 554/1085/26 = < 10 (01.09.2026) |
| CoQ-PP_26-164 | additional testing (12-month) — predicted | P050262 | #9.1 | TAMC | 100 | 1221/2172/25 (01.12.2025) | 555/1086/26 = < 10 (01.09.2026) |
| CoQ-PP_26-137 | additional testing (12-month) — predicted | P050122 | #9.2 | TYMC | < 10 | 626/1127/25 (02.07.2025) | 561/1092/26 = 20 (01.09.2026) |
| CoQ-PP_26-139 | additional testing (12-month) — predicted | CC112501 | #9.2 | TYMC | 2,7 × 10³ | 311/0555/26 (28.04.2026) | 543/1074/26 = 1×10^3 (31.08.2026) |
| CoQ-PP_26-140 | additional testing (12-month) — predicted | P050172 | #9.2 | TYMC | 6.3 × 10³ | 947/1685/25 (17.09.2025) | 558/1089/26 = < 10 (01.09.2026) |
| CoQ-PP_26-141 | additional testing (12-month) — predicted | P050252 | #9.2 | TYMC | 3.5 × 10³ | 1218/2169/25 (01.12.2025) | 556/1087/26 = < 10 (01.09.2026) |
| CoQ-PP_26-142 | additional testing (12-month) — predicted | CJ1024 | #9.2 | TYMC | < 10 | 164/0272/25 (24.02.2025) | 565/1096/26 = 10 (01.09.2026) |
| CoQ-PP_26-145 | additional testing (12-month) — predicted | FB112501 | #9.2 | TYMC | 2,4 × 10³ | 312/0556/26 (28.04.2026) | 542/1073/26 = 5,2×10^2 (31.08.2026) |
| CoQ-PP_26-146 | additional testing (12-month) — predicted | GG012601 | #9.2 | TYMC | 1 × 10⁴ | 310/0554/26 (28.04.2026) | 541/1072/26 = 2,1×10³ (31.08.2026) |
| CoQ-PP_26-147 | additional testing (12-month) — predicted | P050012 | #9.2 | TYMC | 1.9 × 10⁴ | 472/0863/25 (22.05.2025) | 564/1095/26 = < 10 (01.09.2026) |
| CoQ-PP_26-148 | additional testing (12-month) — predicted | GG112501 | #9.2 | TYMC | 4,5 × 10³ | 304/0548/26 (28.04.2026) | 545/1076/26 = 1,1×10³ (31.08.2026) |
| CoQ-PP_26-149 | additional testing (12-month) — predicted | P050202 | #9.2 | TYMC | 4.2 × 10³ | 1009/1813/25 (08.10.2025) | 1155/2056/25 = 400 (24.11.2025) |
| CoQ-PP_26-149 | additional testing (12-month) — predicted | P050202 | #9.2 | TYMC | 4.2 × 10³ | 1009/1813/25 (08.10.2025) | 557/1088/26 = < 10 (01.09.2026) |
| CoQ-PP_26-150 | additional testing (12-month) — predicted | P050292 | #9.2 | TYMC | 6.5 × 10³ | 1228/2194/25 (05.12.2025) | 553/1084/26 = < 10 (01.09.2026) |
| CoQ-PP_26-151 | additional testing (12-month) — predicted | P050102 | #9.2 | TYMC | 6 × 10³ | 318/0585/25 (14.04.2025) | 562/1093/26 = 50 (01.09.2026) |
| CoQ-PP_26-154 | additional testing (12-month) — predicted | J31122501 | #9.2 | TYMC | 370 | 231/0394/26 (Racno trimiran cvet) (07.04.2026) | 544/1075/26 = 1,7×10² (31.08.2026) |
| CoQ-PP_26-155 | additional testing (12-month) — predicted | JD012601 | #9.2 | TYMC | 2,4 × 10³ | 309/0553/26 (28.04.2026) | 540/1071/26 = 1,7×10³ (31.08.2026) |
| CoQ-PP_26-157 | additional testing (12-month) — predicted | P050132 | #9.2 | TYMC | 3.3 × 10⁴ | 904/1589/25 (02.09.2025) | 560/1091/26 = < 10 (01.09.2026) |
| CoQ-PP_26-159 | additional testing (12-month) — predicted | P050272 | #9.2 | TYMC | 200 | 1220/2171/25 (01.12.2025) | 554/1085/26 = < 10 (01.09.2026) |
| CoQ-PP_26-164 | additional testing (12-month) — predicted | P050262 | #9.2 | TYMC | 90 | 1221/2172/25 (01.12.2025) | 555/1086/26 = < 10 (01.09.2026) |
| CoQ-PP_26-145 | additional testing (12-month) — predicted | FB112501 | #9.3 | Bile-tolerant GNB | < 10 | 312/0556/26 (28.04.2026) | 542/1073/26 = < 10² и > 10 (31.08.2026) |
| CoQ-PP_26-148 | additional testing (12-month) — predicted | GG112501 | #9.3 | Bile-tolerant GNB | < 10² and > 10 | 304/0548/26 (28.04.2026) | 545/1076/26 = < 10³ и > 10² (31.08.2026) |
| CoQ-PP_26-149 | additional testing (12-month) — predicted | P050202 | #9.3 | Bile-tolerant GNB | < 10³ and > 10² | 1009/1813/25 (08.10.2025) | 1155/2056/25 = < 10 (24.11.2025) |
| CoQ-PP_26-149 | additional testing (12-month) — predicted | P050202 | #9.3 | Bile-tolerant GNB | < 10³ and > 10² | 1009/1813/25 (08.10.2025) | 557/1088/26 = < 10 (01.09.2026) |
| CoQ-PP_26-154 | additional testing (12-month) — predicted | J31122501 | #9.3 | Bile-tolerant GNB | < 10² and > 10 | 231/0394/26 (Racno trimiran cvet) (07.04.2026) | 544/1075/26 = < 10³ и > 10² (31.08.2026) |

## 2 · A certificate resting on a document issued after it

None, over every determination of every certificate. Every cited document was on file the day its certificate of quality issues.

## 3 · One block, two sublots

3 group(s) where a register block holds two certificates of the same testing on the same day that report different results, over 1 block(s). The certificate of quality prints one of the pair; the other's results appear on no certificate at all.

**J31122501 — Jokerz 31, 2026-04-07, IPH microbiology.** Documents `231/0394/26 (Racno trimiran cvet)`, `230/0393/26 (Trimiran cvet)`; the certificate of quality prints `231/0394/26 (Racno trimiran cvet)`.

* #9.1 TAMC — `231/0394/26 (Racno trimiran cvet)` = 850; `230/0393/26 (Trimiran cvet)` = 1900
* #9.2 TYMC — `231/0394/26 (Racno trimiran cvet)` = 370; `230/0393/26 (Trimiran cvet)` = 840
* #9.3 Bile-tolerant GNB — `231/0394/26 (Racno trimiran cvet)` = < 10^2 and > 10; `230/0393/26 (Trimiran cvet)` = < 10^3 and > 10^2

**J31122501 — Jokerz 31, 2026-04-09, Farmahem — cannabinoids.** Documents `100-2-К/26`, `100-3-К/26`; the certificate of quality prints `100-2-К/26`.

* #4 Total Δ9-THC — `100-2-К/26` = 19.84; `100-3-К/26` = 21.84

**J31122501 — Jokerz 31, 2026-04-23, IPH mycotoxins, metals, pesticides.** Documents `1628/2026`, `1625/2026`; the certificate of quality prints `1628/2026`.

* #10.2 Aflatoxins Σ — `1628/2026` = 2.5; `1625/2026` = COMPLIES (numeric value not present in captured source excerpt for report 1625/2026 — see Bundle cross-reference)

## 4 · Results on file that no certificate of quality prints

214, over 34 lot(s). The number is large and almost all of it is already accounted for by the two sections above; it is here so a ruling can be costed.

**145 — the IJZ-MB campaign microbiology of 25/26.08.2026.** the delivery v34 wrote into the register. The reissues carry the initial microbiology instead — that is OI-38, and these are the results a ruling for *the latest on file* would put on the certificates.

**14 — a starred sample, which by the ruling of 16.09.2026 never certifies.** a second sample of the same packaged lot, sent for a limited panel outside the release testing. The Head of QC ruled on 16.09.2026 that its result stays in the record and in every statistic but never sources a certificate of quality, so appearing here is correct and not a gap (testing_series.EXPERIMENTAL).

**32 — an in-house document with no document number.** the two in-house certificates of analysis for HPA1024 and OPM1024, which print no report number, and the two in-house cross-checks. A certificate of quality cannot cite a document that has no code; these are routed through the lot's internal certificate instead. Nothing to do.

**23 — an ordinary laboratory certificate.** each is either an intermediate retest round no certificate of quality rests on, or the second sublot of section 2.

| lot | document | date | testing | determinations |
|---|---|---|---|---|
| GP062501 (P050202) | 1155/2056/25 | 24.11.2025 | IPH microbiology | 9.1 9.2 9.3 9.4 9.5 |
| GP0824_02 (P050022) | ППК25174 | 10.07.2025 | UKIM CNP potency | 4 5 8 |
| J31112501 | 100-1-ГС/26 | 09.04.2026 | Farmahem — loss on drying | 8 |
| J31112501 | 100-1-К/26 | 09.04.2026 | Farmahem — cannabinoids | 4 5 6 |
| J31122501 | 100-3-ГС/26 | 09.04.2026 | Farmahem — loss on drying | 8 |
| J31122501 | 100-3-К/26 | 09.04.2026 | Farmahem — cannabinoids | 4 5 6 |
| J31122501 | 1625/2026 | 23.04.2026 | IPH mycotoxins, metals, pesticides | 10.2 12 |
| J31122501 | 230/0393/26 (Trimiran cvet) | 07.04.2026 | IPH microbiology | 9.1 9.2 9.3 9.4 9.5 |

All of it by determination:

| determination | results |
|---|---|
| Aflatoxins Σ | 4 |
| As | 3 |
| Bile-tolerant GNB | 34 |
| Cd | 3 |
| E. coli | 34 |
| Hg | 3 |
| Loss on drying | 6 |
| Pb | 3 |
| Pesticides | 4 |
| Salmonella | 34 |
| TAMC | 34 |
| TYMC | 34 |
| Total CBD | 8 |
| Total CBN | 2 |
| Total Δ9-THC | 8 |

