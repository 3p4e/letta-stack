# Open items — awaiting the owner

Every finding the desk has raised and cannot itself settle, with the evidence
behind it and the decision being asked for. Built by `open_items.py`; the same
register is the **Open Items** sheet of the workbook.

**20 open · 3 marked on the certificate**

## Specification

### OI-01 · A lot graded IV or V whose strain has no specification at that grade

*State:* **marked** · *Evidence:* spec_attributes_2026-09-10.csv; CJ082501/2, GP082501/2, OPM122501

**Found.** The QCSP 001 specification is issued per strain AND per grade. Cap Junky is on file at grades I, II and III; CJ082501/2 is grade IV. Grape Pie and Orange Punch Mimosa stop at IV and each has a grade V lot. Exactly one grade V specification exists in the whole issued set (Clemosa).

**The desk.** The phenotype, chemotype, processing and packaging pills are left unticked and the band is marked, on 3 lots.

**Needed.** May a lot cite the specification of its own strain at the nearest grade on file? The evidence says the attributes do not depend on grade: across 71 strains and 257 issued specifications, phenotype, dominance, chemotype, processing and packaging differ between grades of one strain in ZERO cases.

### OI-02 · Two certificates name a specification by potency band instead of grade

*State:* **marked** · *Evidence:* export_coq_artifact_data.py specification join; 2 lots

**Found.** GP052501 names QCSP_001_GP-THC18_v.01 and GRC102501/2 names QCSP_001_GRC-THC12_v.01. Neither exists in the issued set under any name — but QCSP_001_GP-IV_v.01 does, and IV is the grade GP052501 carries.

**The desk.** Both pills are marked. No substitution was made without a ruling.

**Needed.** Is the potency-band name an older convention for the same document? If so the desk joins on the grade and both resolve immediately.

### OI-03 · Thirty-two lots have no grade, so no specification can be named at all

*State:* **open** · *Evidence:* 48 of 80 lots indexed; 68 of 164 certificate records carry no grade

**Found.** The grade comes from product_specifications_QCSP001.json, built from the specification copies handed out with the tranches, which covers 48 of the 80 lots. For the other 32 the desk cannot compose a specification code, and the certificate names none.

**The desk.** Nothing is printed and nothing is guessed.

**Needed.** Where is the grade for the remaining 32 lots recorded? Once the desk has it, the specification code follows from the strain and the pills fill themselves.

## Result reading

### OI-04 · Four lots where which analyte the figure belongs to decides pass or fail

*State:* **marked** · *Evidence:* COQ_DRAFTING_2026-09-10.md; 4 lots

**Found.** The release certificates print the mycotoxin sub-parameters as one block and the desk maps the value to an analyte by its position in the block, not by a printed name. CLE072501, OPM092501, OPM1024_03 and OPM122501 report 2.1–2.2 µg/kg: as total aflatoxins (limit 4) they pass, as Aflatoxin B1 (limit 2) they fail.

**The desk.** The figure is printed as the desk reads it and the lot is named here. None of the four may be signed until a person has read the page.

**Needed.** Read the four certificates and confirm which analyte the figure belongs to.

### OI-05 · Nineteen lots print a Total Δ⁹-THC outside the range printed beside it

*State:* **open** · *Evidence:* status_of / the two-sided criterion; 19 lots

**Found.** The acceptance test was one-sided — it asked only whether a value exceeded its limit — so an assay BELOW its band was never flagged anywhere. Corpus-wide, 19 lots carry a potency outside the range on their own certificate, every one recorded as covered.

**The desk.** The comparison now happens in the gap report, never on the certificate, and the report declines any criterion it cannot read as two numbers.

**Needed.** Each of the 19 needs a disposition: re-read, re-test, or a regrade.

## Reconciliation

### OI-06 · Forty-six disagreements between the desk and the owner's 09.09 pass

*State:* **open** · *Evidence:* Reconciliation 09.09 sheet; 46 rows

**Found.** Put side by side on the Reconciliation 09.09 sheet: 218 determinations agree, 46 do not. One is a loss on drying of 76.07 % read on GG1024 against a 12.0 % limit.

**The desk.** None is resolved by the desk. Both readings are shown with their sources.

**Needed.** A person reads the page for each of the 46 and says which reading stands.

## Issuance

### OI-07 · Fifty-seven certificates of quality are dated on a Saturday

*State:* **open** · *Evidence:* issuance_schedule.COQ_BLANKET; 57 certificates

**Found.** 06.06.2026, the blanket date for everything that would otherwise issue before the specification SOP, is a Saturday. The builder's own convention is that a controlled document issues on a working day.

**The desk.** The owner's date outranks the desk's convention, so it is kept as given and the workbook carries a flag saying it was chosen deliberately.

**Needed.** Confirm 06.06.2026, or name the working day it moves to (08.06.2026 is the Monday).

## Reference

### OI-08 · Five result cells cite an SOP form number instead of a certificate

*State:* **open** · *Evidence:* 2 lots, 10 result cells

**Found.** NGP-QCG-SOP-024 F3, (28.11.2025) [NGP] carries Identification C, Total Δ⁹-THC, Total CBD, Total CBN and loss on drying for BSS052501 and GP062501 — including the banner assays 20.39 % and 24.89 %. A form number is not a document code and cannot be cited on a certificate of quality.

**The desk.** The reference is printed as it stands and the lots are named here.

**Needed.** Does the NGP laboratory issue a numbered report for this work? If not, these results need a different basis.

### OI-09 · One laboratory report is on file twice, once per language

*State:* **open** · *Evidence:* BSS052501; Batch Coverage Certificates (n)

**Found.** 10802_2845-2 EN and 10802_2845-2 MK are the same DFL report for BSS052501, cited as two documents, which is why that lot's certificate count reads one higher than the sheet's.

**The desk.** Both are cited as the desk found them.

**Needed.** Confirm the two files are one report, and which language version is the controlled copy.

## Batch identity

### OI-10 · Three delivered lots have no cultivation batch recorded anywhere

*State:* **open** · *Evidence:* 3 lots; also absent from Batch Dates: JD112501＊

**Found.** P160012, P160022 and P160032 carry full CNP results (ППК26117/18/19, 06.07.2026) and a P number in a series of their own, but no cultivation batch, and no row at all in the Head of QC's Batch Dates list — so no manufacturing date and no internal CoA basis.

**The desk.** Each row now names its P number inside the label so the three are distinguishable and no join collapses them; the cultivation batch is left unrecorded rather than invented.

**Needed.** What are the cultivation batches, manufacturing and packaging dates for the P1600xx series?

### OI-11 · One lot carries two P batches in a single cell

*State:* **open** · *Evidence:* GRC102501

**Found.** GRC102501 is recorded against P060142 / P060182 in one cell, so its coverage row aggregates what are arguably two lots and its certificate count cannot reconcile.

**The desk.** Left as the owner's tracker records it.

**Needed.** Are these one lot packed into two P batches, or two lots sharing a cultivation batch? If two, they need two rows.

### OI-12 · A lot and its ＊ sub-lot are credited from the same three documents

*State:* **open** · *Evidence:* JD112501 / JD112501＊

**Found.** JD112501 and JD112501＊ both cite ППК26065, 2365-2026 and 306-0550-26. On the parent those readings are marked on file, not credited; on the sub-lot they are credited. The sub-lot's microbiology block also carries the parent's round-1 values while its cannabinoids and metals come from round 2.

**The desk.** Both rows are left as recorded and the pair is named here.

**Needed.** Is JD112501＊ a distinct lot? If so, which round's microbiology belongs to it?

## Document identity

### OI-29 · The two series count different things, so they cannot be the same length

*State:* **open** · *Evidence:* icoa_register.py 102 rounds / 76 lots vs coq_artifact_data.json 164 records / 82 lots; 3 lots with 4, 5 and 6 rounds

**Found.** The ruling of 10.09.2026 says the internal certificates are "one per testing round, which is EXACTLY the number of certificates of quality". They are not, and the reason is that the two registers count different things. icoa_register.py counts rounds the testing record SHOWS: 102 over 76 lots. The certificate-of-quality model counts certificates it PLANS: exactly two per lot — one release and one 12-month retest — 164 over 82 lots, 103 of them predicted. Across the 76 lots both carry, the counts agree on 14 and differ on 62. GP0824_02 has six testing rounds and two certificates of quality; GP062501 has five; GP0824_03 has four.

**The desk.** Nothing renumbered. The internal register was brought to one row per round on 11.09.2026 because that is what the ruling says it is; the CoQ series was left exactly as it stands, because renumbering controlled documents the owner has already seen is not a change to make on a reading. No certificate loses a code to this today: no lot has more than one non-initial certificate of quality, so the single |R row still resolves for every one of them.

**Needed.** Does a lot with four retest rounds take four reissued certificates of quality — one per round, matching its four internal certificates — or one reissue per retest campaign, as the register plans now? The first reading makes the ruling's arithmetic true and renumbers the CoQ series; the second keeps the series and means the sentence describes the rounds that produce a certificate, not every round on the record.

## Batch identity

### OI-28 · Seven starred lots have no internal certificate of analysis at all

*State:* **open** · *Evidence:* ingestion/common/batch_id.py; 7 lots on the iCoA Register with no series row

**Found.** GG1024, BSS1024_01/2 (P050142), WED102501 (P060102), GRC102501 (P060142), GG012601 (P060302), JD012601 (P060312) and SCR012601* (P060342) appear on the register sheet with no certificate in the series behind them. The cause is the star. The company writes GG012601* and the testing record writes GG012601, and batch_id.batch_key keeps the mark on purpose — its own docstring says whether a starred lot and its unstarred namesake are the same batch "is NOT a question this function may answer: it is a fact about the floor". So the two spellings are two batches, the testing record attaches to one and the register sheet's row to the other, and neither can see the other.

**The desk.** Nothing invented. batch_key is untouched, the seven rows sit on the register unnumbered, and each says the series does not carry it. They are the whole of the difference between the sheet's 83 release rows and the series' 76.

**Needed.** For each pair, is the starred lot the same batch as the unstarred one? A ruling goes in ingestion/ecoa_runner/identity_decisions.tsv, which is where batch_key says such a ruling belongs, and the seven certificates then issue by themselves.

## Panel scope

### OI-13 · Two optional test panels have never been exercised

*State:* **open** · *Evidence:* Ph. Eur. 2.8.13; Ph. Eur. 2.6.13 expanded panel

**Found.** The pesticide panel offers a Ph. Eur. 2.8.13 option and a CUMCS-equivalency option, and none of the lots was tested to equivalency. The expanded microbiology option (P. aeruginosa, S. aureus) has never been run.

**The desk.** Neither is claimed on any certificate.

**Needed.** Should the certificates record that the option exists and was not exercised, or stay silent on it?

## Document content

### OI-14 · Three fields still print a specimen or a placeholder

*State:* **open** · *Evidence:* _CoQ_MASTER_Template.html; 22 drafts

**Found.** The two approvers' names are the master template's specimen. The potency acceptance range is a bracketed placeholder in both places it prints. Identification C is not yet cited from the cannabinoid-determination document the owner's ruling names.

**The desk.** All three print bracketed in red and unticked, so no draft can be mistaken for issued.

**Needed.** The approvers' names and titles; the potency range per grade; confirmation of the Identification C sourcing rule for the initial series.

## Method status

### OI-15 · The pesticide acceptance criterion is stated as ≤ LOQ, which is not the Ph. Eur. test

*State:* **open** · *Evidence:* IJZ 2994/2025, 19.06.2025, OPM 1024_02 (P050062); verdict on the page: ОДГОВАРА

**Found.** Ph. Eur. 2.8.13 sets a maximum per compound, not a limit of quantitation. OPM1024_02 shows why it matters: delta-HCH is reported at < 0.01 mg/kg against a maximum of 0.3, which conforms to the monograph and is not ≤ LOQ, and the column has no way to say so. The owner confirmed on 11.09.2026 that the reading itself is correct.

**The desk.** The result is printed as the laboratory reports it.

**Needed.** Restate the criterion as the Ph. Eur. maximum table, and say how a conforming detection should print beside 28 not-detected residues.

## Result

### OI-16 · One lot's foreign matter is reported by the laboratory as not conforming

*State:* **open** · *Evidence:* FB032601; ППК26127, 21.07.2026 [CNP]

**Found.** FB032601 prints 0.08 % (Не одговара) on ППК26127 of 21.07.2026. The figure passes the gravimetric ≤ 2.0 % limb, so CNP is failing it on another limb of Ph. Eur. 2.8.2 (leaf and stem size). The desk used to fold Не одговара to absent — a pass — because the phrase contains одговара; that is fixed and the lot now reads as out of specification.

**The desk.** Flagged OOS. An out-of-specification result needs an investigation record.

**Needed.** Confirm the non-conformity with CNP and open the deviation, or obtain a corrected certificate.

### OI-17 · Five microbiological counts exceed the Ph. Eur. 5.1.4 band and four sit inside it

*State:* **open** · *Evidence:* Ph. Eur. 5.1.4; 9 lots

**Found.** Judged as the desk judges a counted limit — ≤ 10ⁿ against 2 × 10ⁿ — GG1024_01, OPM052501, GP052501, HPA052501 and CJ062501/2 are out of specification on TYMC; GG1024_02, HPA1024_01, GP0824_03 and CJ052501/01 are in the undetermined band.

**The desk.** Printed red bold and amber bold respectively, and named in each lot's STATUS.

**Needed.** Each out-of-specification count needs an investigation record; the four undetermined need a disposition.

## Document content

### OI-18 · The same assertion printed bilingually on some certificates and in English on others

*State:* **ruled** · *Evidence:* 375 determinations; .r-conform .mk in _CoQ_MASTER_Template.html

**Found.** Identification A and foreign matter print Conforms on 51 determinations and Conforms | Соодветствува on 12 — the certificate's own English | Macedonian pattern, applied to some cells and not others.

**The desk.** Owner's ruling of 11.09.2026: every conformity result prints bilingually, in the convention the rest of the certificate uses. The master already set that convention for this exact cell and nothing had used it — .r-conform .mk stacks the Macedonian beneath the English in a smaller muted green — so the halves are stacked, not joined by the .bisep pipe the master keeps for inline pairs. 375 results paired. A measured number is not translated.

**Needed.** Nothing further.

## Result

### OI-19 · One ochratoxin result prints as a working note rather than a value

*State:* **open** · *Evidence:* #10.3 Ochratoxin A, 1 determination

**Found.** 2.06 — DETECTED, >LOQ on Ochratoxin A. The limit is 20 µg/kg so it conforms, but the cell carries the reader's note instead of the figure and its qualifier.

**The desk.** Printed as the desk holds it.

**Needed.** How should a conforming detection print — the figure alone, or the figure with a detected qualifier? The same question as OI-15 for pesticides.

## Document content

### OI-24 · The Identification C result no longer states the method on the face of the document

*State:* **open** · *Evidence:* #3 Identification C; 35 determinations

**Found.** The result read "Conforms — cannabinoids identified and quantified by HPLC", which restated the METHOD column two cells to its left on the same row. Measured with the embedded fonts, that one cell stood 85 px tall against 18 px for a normal row, and div.page clips at A4: three certificates were losing their second approver's signature date off the bottom of the sheet.

**The desk.** Shortened to "Conforms | Одговара" like every other identity row. The basis for Identification C stays in the Section 03 citation, where a basis belongs.

**Needed.** Do you want the method restated in the result cell? It would need a wider results column, which is a change to the master.

## Document identity

### OI-27 · The register sheet carried 60 of the series' 95 internal certificates

*State:* **ruled** · *Evidence:* 95 of 95 series codes on the sheet (was 60); 166 rows; verify_workbook.py 0 findings

**Found.** The numbering agreed wherever both carried a row, but the ROW SETS did not. The sheet held 60 numbered rows against the series' 95: it showed no retest certificate at all where the series issues 26 — its retest rows are one per lot per sampling campaign, so a lot with four retest rounds had ONE row standing for four certificates — and it withheld nine release certificates under "where a CNP certificate reports all three, no iCoA is needed".

**The desk.** Built, 11.09.2026. The sheet now RENDERS icoa_register.py: one row per testing round, all 95 codes printed and numbered, retests 2-5 addressable for the first time (keys |R2 .. |R5, while retest 1 keeps the bare |R every existing lookup cites). The nine withheld release certificates are registered — the 05.09.2026 note was superseded by the ruling below, and which document the certificate of QUALITY cites for those three determinations is a separate question and is unchanged. A lot the series does not carry keeps its planning row, unnumbered and saying why. verify_workbook.py now checks COVERAGE, not just agreement: every certificate in the series appears on the sheet exactly once. Run against the previous workbook it reports the 35 that were missing.

**Needed.** Nothing — this was already ruled and the desk had recorded it as a question. 10.09.2026: "the register encompasses every internal certificate that exists or ever will, not only what the drafted lots need ... one per testing round", and "identification A, identification B and foreign matter, ALWAYS".

### OI-26 · The internal-CoA number was defined twice and the two disagreed on every comparable row

*State:* **ruled** · *Evidence:* icoa_register.py and the iCoA Register sheet; 49 of 49 differed, now 0

**Found.** The certificates print the code from icoa_register.py, which sorts by the order of issuing exactly as ruled and numbers iCoA-PP_26-001 .. -099, leaving 7 lots unnumbered for want of a packaging date. The workbook's iCoA Register sheet numbers its own rows by position, COUNT(A$1:A{n})+1, over a different row order and a different rule — it also withholds a number from every retest and every held result, numbering 69. Of the 49 rows that can be compared, 0 agree. J31122501 / P060262 is the owner's example: the sheet makes it iCoA-PP_26-001 because it is physically the first row; the certificate cites iCoA-PP_26-066, its true place in the issue order. The two also identify lots differently — the module's rows often carry no P number, so 20 sheet rows cannot even be matched to it.

**The desk.** Closed against the ruling of 10.09.2026, which already answered it: "the register encompasses every internal certificate that exists or ever will … one per testing round, which is exactly the number of certificates of quality." A retest takes a number and a held lot takes a number; only a certificate with no testing date takes none, because a code in an issue-ordered series says the certificate was issued. The workbook now takes its codes from icoa_register.py as literals — one definition — and mints none of its own; a row the series does not carry is left unnumbered and says so. Two defects were found on the way: the register carried 26 rows with no P number that Batch Dates could supply, and it registered four lots TWICE for the same round, once under the cultivation batch and once under the bare P number (J31102501/P060152, JD112501/P060212, OPM122501/P060242, GG012603/P060402) — same P number, same testing date, same issue date, so two internal certificates for one testing, which the ruling forbids. 106 rows -> 102. verify_workbook.py compares the two registers on every run and the workbook verifies with 0 findings.

**Needed.** Nothing. Recorded because the numbers moved: de-duplicating shifted every code from 045 onward, so any code quoted before 11.09.2026 is stale.

## Document rendering

### OI-25 · The A4 page was never measured with the fonts it prints in

*State:* **ruled** · *Evidence:* build_coq_drafts.py page-height report; measured 5 of 22 -> 0 of 22 losing content

**Found.** "One A4 page" was checked by reading scrollHeight on the page itself — but div.page clips with overflow:hidden, so that reading returns the clipped height and always answers zero. Measured properly, inside an A4 frame with the subset fonts the PDF embeds, 5 of the 22 certificates stood past the bottom of the sheet, the worst by 72 px, and P060152 was printing only one of its two signature dates.

**The desk.** The builder measures it on every run and names any document that overflows. Four compiled-copy fit rules close the gap: the Identification C result shortened (OI-24), short paired results held on one line rather than wrapped, and the leading of Section 03 and of the parameter column tightened. 21 of 22 now fit outright; the 22nd has a few px of trailing box space past the edge with no element beyond it.

**Needed.** Nothing. Recorded because the claim had been made and was not true, and because the page has very little slack: the next thing that adds a line will need this check.

## Document content

### OI-23 · The Macedonian for an absent organism was chosen from the laboratories' own usage

*State:* **open** · *Evidence:* #9.4 Salmonella, #9.5 E. coli; 92 determinations

**Found.** The owner ruled the conformity result prints "Conforms | Одговара". The absence columns (Salmonella, E. coli) assert absence rather than conformity and were not covered by that word. The source certificates spell it four ways — отсутна (7), отсуство (2), отсуства (2) — and most often write Одговара there instead (84).

**The desk.** The certificate prints "Absent | Отсутна" on 92 determinations: CNP's own most-used form ("отсутна/25 g"), capitalised, rather than a term translated afresh for a controlled document.

**Needed.** Confirm Отсутна, or give the term the two absence rows should carry.

## Result reading

### OI-22 · An analyte the laboratory never tested was printing a line on the certificate

*State:* **ruled** · *Evidence:* BG1024 release vs 12-month retest, verified through fillCoq in headless Chromium

**Found.** The initial testing of a batch often runs only part of a parameter's panel: mycotoxins assayed for total aflatoxins alone, with Aflatoxin B1 and Ochratoxin A not tested. The certificate printed a bracketed blank for each untested analyte, which in a results column reads as a finding still to come; before the ND ruling was scoped it would have printed ND, asserting the analyte was measured and absent.

**The desk.** Owner's ruling of 11.09.2026: "since they're not tested, those sub-parameters are not going to enter inside the certificate of quality at all." fillCoq() removes the row from the compiled copy — only for a sub-determination inside a parameter that WAS tested, because if nothing in the group has a result the parameter itself is missing and that is a gap the certificate must show. 36 rows removed across the 22 drafts, all of them Aflatoxin B1 or Ochratoxin A on 18 release certificates; the retest of the same batch prints all three. Blank printed lines 87 -> 51. The master file is untouched.

**Needed.** Nothing. Recorded because it is the boundary of the ND ruling: n.r. printed by a laboratory as a result means ND, and an analyte absent from the panel is not a result at all.

## Document rendering

### OI-21 · Sixty-six faces in the tranche PDFs embedded as Type 3 rather than outlines

*State:* **ruled** · *Evidence:* print_coq_pdfs.py FAMILIES; pdffonts on both tranche PDFs

**Found.** 39 faces in Tranche 1 and 27 in Tranche 2 were Montserrat Medium Italic rasterised into Type 3 glyph procedures, while the same family embedded as TrueType elsewhere in the same document. The count was identical in the previously committed PDFs, so it predates the 11.09 work. Cause: .ap-cred sets font-weight:600 in italic and the font request asked for italic at 400, 500 and 700 only, so the browser emboldened the nearest real italic — and a synthesised face has no outlines to embed.

**The desk.** Fixed: italic 600 and 700 added to the font request in both print_coq_pdfs.py and house_fonts.py, and the rule written down beside them — when a stylesheet sets an italic weight, that weight belongs in FAMILIES.

**Needed.** Nothing. Recorded because the first Type 3 fix (pinning the variable axes) looked complete and was not: it fixes the faces the page asks for by name, never one the page never asked for.

## Desk status

### OI-20 · Nine result cells hold a desk status instead of a value

*State:* **open** · *Evidence:* Work Order sheet

**Found.** not ingested (the document exists but has not been extracted into the eCoA database) on 5 cells, held for review (the two independent reads disagreed) on 3, and one Identification C awaiting a decision.

**The desk.** Each is carried on the Work Order sheet with what it needs; none reaches a certificate.

**Needed.** Nothing — these are desk work, listed so the count is visible.

