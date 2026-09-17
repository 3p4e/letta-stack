# Does any certificate of quality print a result the record has replaced?

The sweep of 16.09.2026, over 172 certificates of quality and 93 register blocks. Run it with `python3 deliverables/qc_gap_analysis/result_supersession.py`.

## 1 · A printed result a later certificate contradicts

34 comparisons — every (certificate, determination, later certificate for the same lot) triple where the later certificate was on file the day the certificate of quality issues. **10 contradict.**

**A zero is only as good as what could be compared**, so the coverage is beside it. A lot with one document for a determination can never contradict itself: the certificate's value rests on that one document and the sweep has nothing to hold it against.

| # | parameter | documents on file | lots with two or more | contradictions |
|---|---|---:|---:|---:|
| #4 | Total Δ9-THC | 160 | 64 | 2 |
| #5 | Total CBD | 160 | 64 | 1 |
| #6 | Total CBN | 106 | 12 | 0 |
| #8 | Loss on drying | 76 | 4 | 4 |
| #9.1 | TAMC | 107 | 24 | 1 |
| #9.2 | TYMC | 108 | 25 | 1 |
| #9.3 | Bile-tolerant GNB | 108 | 25 | 1 |
| #9.4 | Salmonella | 108 | 25 | 0 |
| #9.5 | E. coli | 108 | 25 | 0 |
| #10.1 | Aflatoxin B1 | 83 | 1 | 0 |
| #10.2 | Aflatoxins Σ | 146 | 60 | 0 |
| #10.3 | Ochratoxin A | 83 | 1 | 0 |
| #11.1 | Pb | 68 | 2 | 0 |
| #11.2 | Cd | 68 | 2 | 0 |
| #11.3 | As | 68 | 2 | 0 |
| #11.4 | Hg | 68 | 2 | 0 |
| #12 | Pesticides | 69 | 3 | 0 |

#10.1 Aflatoxin B1, #10.3 Ochratoxin A, #11.1 Pb, #11.2 Cd, #11.3 As, #11.4 Hg were compared on 1 lot, 1 lot, 2 lots, 2 lots, 2 lots, 2 lots only — a zero there is real but thin.

Where the comparison was genuinely available and returned nothing, it is worth stating plainly: #6 Total CBN over 12 lots; #9.4 Salmonella over 25 lots; #9.5 E. coli over 25 lots; #10.2 Aflatoxins Σ over 60 lots; #12 Pesticides over 3 lots.

The 10 split in two, and only the second half is an open question:

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

### carried forward — 2

The certificate carries the result forward from the initial testing because the campaign it rests on did not retest that determination — the ruling of 15.09.2026. The question OI-38 puts to the owner is whether *forward from the initial testing* should mean the initial result or the latest result on file, and these are the rows it decides.

| certificate | series | lot | # | parameter | prints | from | superseded by |
|---|---|---|---|---|---|---|---|
| CoQ-PP_26-095 | additional testing (12-month) | P050022 | #8 | Loss on drying | 7.21 | ППК25139 (22.05.2025) | ППК25174 = 6.51 (10.07.2025) |
| CoQ-PP_26-153 | additional testing (12-month) — predicted | J31112501 | #8 | Loss on drying | 8.4 | 051-5-ГС/26 (02.03.2026) | 100-1-ГС/26 = 7.6 (09.04.2026) |

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

141, over 19 lot(s). The number is large and almost all of it is already accounted for by the two sections above; it is here so a ruling can be costed.

**0 — the IJZ-MB campaign microbiology of 25/26.08.2026.** the delivery v34 wrote into the register. The reissues carry the initial microbiology instead — that is OI-38, and these are the results a ruling for *the latest on file* would put on the certificates.

**19 — a starred sample, which by the ruling of 16.09.2026 never certifies.** a second sample of the same packaged lot, sent for a limited panel outside the release testing. The Head of QC ruled on 16.09.2026 that its result stays in the record and in every statistic but never sources a certificate of quality, so appearing here is correct and not a gap (testing_series.EXPERIMENTAL).

**32 — an in-house document with no document number.** the two in-house certificates of analysis for HPA1024 and OPM1024, which print no report number, and the two in-house cross-checks. A certificate of quality cannot cite a document that has no code; these are routed through the lot's internal certificate instead. Nothing to do.

**90 — an ordinary laboratory certificate.** each is either an intermediate retest round no certificate of quality rests on, or the second sublot of section 2.

| lot | document | date | testing | determinations |
|---|---|---|---|---|
| AB092501 (P060052) | PP CoA #037 / ППК26005 | 21.01.2026 | UKIM CNP potency | 4 5 8 |
| CLE072501 (P050282) | PP CoA #027 / ППК25370 | 21.01.2026 | UKIM CNP potency | 4 5 8 |
| GP062501 (P050202) | 1155/2056/25 | 24.11.2025 | IPH microbiology | 9.1 9.2 9.3 9.4 9.5 |
| GP072501-1 (P050292) | PP CoA #018 / ППК25378 | 21.01.2026 | UKIM CNP potency | 4 5 8 |
| GP072501-2 (P050302) | PP CoA #019 / ППК25379 | 21.01.2026 | UKIM CNP potency | 4 5 8 |
| GP0824_02 (P050022) | 2471-2025 | 30.05.2025 | IPH mycotoxins, metals, pesticides | 11.1 11.2 11.3 11.4 12 |
| GP0824_02 (P050022) | 471-0862-25 | 22.05.2025 | IPH microbiology | 9.1 9.2 9.3 9.4 9.5 |
| GP0824_02 (P050022) | ППК25174 | 10.07.2025 | UKIM CNP potency | 4 5 8 |
| GP082501-1 (P050312) | PP CoA #020 / ППК25380 | 21.01.2026 | UKIM CNP potency | 4 5 8 |
| GP082501-2 (P050322) | PP CoA #021 / ППК25381 | 21.01.2026 | UKIM CNP potency | 4 5 8 |
| GRC102501-2 | 1060/2026 | 09.03.2026 | IPH mycotoxins, metals, pesticides | 10.2 11.1 11.2 11.3 11.4 |
| GRC102501-2 | 136/0233/26 | 06.03.2026 | IPH microbiology | 9.1 9.2 9.3 9.4 9.5 |
| GRC102501-2 | 76/0119/26 | 09.02.2026 | IPH microbiology | 9.2 9.3 9.4 9.5 |
| J31112501 | 100-1-ГС/26 | 09.04.2026 | Farmahem — loss on drying | 8 |
| J31112501 | 100-1-К/26 | 09.04.2026 | Farmahem — cannabinoids | 4 5 6 |
| J31122501 | 100-3-ГС/26 | 09.04.2026 | Farmahem — loss on drying | 8 |
| J31122501 | 100-3-К/26 | 09.04.2026 | Farmahem — cannabinoids | 4 5 6 |
| J31122501 | 1625/2026 | 23.04.2026 | IPH mycotoxins, metals, pesticides | 10.2 12 |
| J31122501 | 230/0393/26 (Trimiran cvet) | 07.04.2026 | IPH microbiology | 9.1 9.2 9.3 9.4 9.5 |
| JD012603-02 | 3660/2026 | 22.06.2026 | IPH mycotoxins, metals, pesticides | 10.2 11.1 11.2 11.3 11.4 |
| JD012603-02 | 405/0788/26 | 24.06.2026 | IPH microbiology | 9.1 9.2 9.3 9.4 9.5 |
| JD012603-02V | 3662/2026 | 22.06.2026 | IPH mycotoxins, metals, pesticides | 10.2 11.1 11.2 11.3 11.4 |
| JD012603-02V | 406/0789/26 | 24.06.2026 | IPH microbiology | 9.1 9.2 9.3 9.4 9.5 |
| OPM1024_01 (P050042) | 407-0745-25 | 05.05.2025 | IPH microbiology | 9.1 9.2 9.3 9.4 9.5 |

All of it by determination:

| determination | results |
|---|---|
| Aflatoxins Σ | 7 |
| As | 7 |
| Bile-tolerant GNB | 12 |
| Cd | 7 |
| E. coli | 12 |
| Hg | 7 |
| Loss on drying | 12 |
| Pb | 7 |
| Pesticides | 5 |
| Salmonella | 12 |
| TAMC | 11 |
| TYMC | 12 |
| Total CBD | 14 |
| Total CBN | 2 |
| Total Δ9-THC | 14 |

