# Open items — awaiting the owner

Every finding the desk has raised and cannot itself settle, with the evidence
behind it and the decision being asked for. Built by `open_items.py`; the same
register is the **Open Items** sheet of the workbook.

**17 open · 3 marked on the certificate**

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

