# Open items — awaiting the owner

Every finding the desk has raised and cannot itself settle, with the evidence
behind it and the decision being asked for. Built by `open_items.py`; the same
register is the **Open Items** sheet of the workbook.

**31 open · 3 marked on the certificate**

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

*State:* **ruled** · *Evidence:* ППК26063 / ППК26065 (both P060212); the scans 110526_ППК26063_CNP_JD112501-P060212.pdf and 110526_ППК26065_CNP_JD112501＊-P060212.pdf; cell_resolution_2026-09-09.tsv; testing_series.EXPERIMENTAL

**Found.** JD112501 and JD112501＊ both cite ППК26065, 2365-2026 and 306-0550-26. On the parent those readings are marked on file, not credited; on the sub-lot they are credited. The sub-lot's microbiology block also carries the parent's round-1 values while its cannabinoids and metals come from round 2. Read on the pages on 16.09.2026: ППК26063 and ППК26065 are the same lot P060212, the same sample description (Сув сомелен цвет од медицински канабис сорта Jelly Donutz), the same delivery of 21.04.2026, the same DAB method and the same 12 g — the batch number is the ONLY difference between the two pages, ППК26063 reading JD112501 and ППК26065 reading JD112501*. The owner's own resolution pass of 09.09.2026 gives JD112501/P060212 a complete panel and cites ППК26063 for #3-#6 and #8; ППК26065 is cited nowhere in it.

**The desk.** Owner's ruling of 16.09.2026: "The asterisk is probably some experiment and is generally not the result that will go for the batch release official documentation. If both THC results are assigned with the same P number production batch, that means it is the same batch, but two samples have been sent for the parameter. You will NOT ignore the value and data with the asterisk — you will include it in calculation statistics and all — but in the CoQ you will take the other value and corresponding certificate." So it is ONE batch and two samples, not two lots. testing_series.EXPERIMENTAL holds the starred certificates and build_coq_schedule drops them before the release/reissue split, so they source no certificate of quality; everywhere else the result stands. The certificates were already right: CoQ-PP_26-057 prints 19.64 % from ППК26063 and CoQ-PP_26-098 prints 20.32 % from 197-15-К/26. Neither prints 13.93 %.

**Needed.** Two consequences of the ruling to see, and one thing still unwritten. (1) The 09.09 resolution pass cited 306-0550-26 — the STARRED sample's microbiology, TAMC 1 × 10⁴ — for JD112501's #9, and the unstarred 2361-2026 for #10–#12. Under the ruling the starred sample does not certify, so since the intake of 16.09.2026 (intake_IJZ0426_2026-09-16) CoQ-PP_26-057 cites 307/0551/26, TAMC 2,6 × 10³, for #9. Both conform. Is that right, or does the pass's choice stand for microbiology? (2) The certificate's "Also on file" note no longer names the starred value beside the release result (13.93 % beside 19.64 %): the exclusion reaches the footnote as well as the cited document. Should the certificate declare on its face that a second sample exists, or stay silent about it? (3) What the asterisk DENOTES on the floor — hand-trimmed material, a different drying or milling treatment, a sampling position — is still unwritten; the pages do not say and the desk will not infer it.

## Document identity

### OI-29 · The two series count different things, so they cannot be the same length

*State:* **open** · *Evidence:* icoa_register.py 102 rounds / 76 lots vs coq_artifact_data.json 164 records / 82 lots; 3 lots with 4, 5 and 6 rounds

**Found.** The ruling of 10.09.2026 says the internal certificates are "one per testing round, which is EXACTLY the number of certificates of quality". They are not, and the reason is that the two registers count different things. icoa_register.py counts rounds the testing record SHOWS: 102 over 76 lots. The certificate-of-quality model counts certificates it PLANS: exactly two per lot — one release and one 12-month retest — 164 over 82 lots, 103 of them predicted. Across the 76 lots both carry, the counts agree on 14 and differ on 62. GP0824_02 has six testing rounds and two certificates of quality; GP062501 has five; GP0824_03 has four.

**The desk.** Nothing renumbered. The internal register was brought to one row per round on 11.09.2026 because that is what the ruling says it is; the CoQ series was left exactly as it stands, because renumbering controlled documents the owner has already seen is not a change to make on a reading. No certificate loses a code to this today: no lot has more than one non-initial certificate of quality, so the single |R row still resolves for every one of them.

**Needed.** Does a lot with four retest rounds take four reissued certificates of quality — one per round, matching its four internal certificates — or one reissue per retest campaign, as the register plans now? The first reading makes the ruling's arithmetic true and renumbers the CoQ series; the second keeps the series and means the sentence describes the rounds that produce a certificate, not every round on the record.

## Batch identity

### OI-28 · The starred spellings are one lot each with their unstarred namesakes — applied; one word confirms it

*State:* **ruled** · *Evidence:* ingestion/ecoa_runner/identity_decisions.tsv (batch_alias, 16.09.2026); identity_questions_2026-09-07.tsv rows 2–6; icoa_register.py:227/:246; tracker/FLEET_FINDINGS_2026-09-16.md

**Found.** Raised on 10.09.2026 as seven starred lots with no internal certificate. The audit of 16.09.2026 re-read the premise: only THREE of the seven are starred anywhere (GG012601*, JD012601*, SCR012601* on the Head of QC's batch list; GG1024, BSS1024_01/2, WED102501 and GRC102501 carry no star and were resolved by v31), and all seven have carried an iCoA row since the 227-К and 220-М intakes. What the star still broke was two lots: the batch list writes GG012601* against P060302 and JD012601* against P060312, the release register labels the same blocks GG012601 and JD012601 with no P number, and icoa_register.py looked the packaging date and the P lot up by the unstarred label — so iCoA-PP_26-087 and -088 had no testing date and the two Tranche 3 release certificates stood at "— at issue —", withheld over a glyph. iCoA-PP_26-090 (SCR012601) had no testing date for the same reason. No unstarred twin sample exists for any of the three: the certificates that name the lot print the star (ППК26062, 310/0554/26, 2364/2026; ППК26064, 309/0553/26, 2363/2026), each P number has exactly one cultivation-batch spelling on the list, and the identity questions of 07.09.2026 proposed one lot for each (and for FB012602*, starred on the list alone).

**The desk.** Applied as a consequence of the ruling of 16.09.2026 — "if both THC results are assigned with the same P number production batch, that means it is the same batch" — recorded as data: ingestion/ecoa_runner/identity_decisions.tsv carries a batch_alias row for each of GG012601*, JD012601*, SCR012601*, FB012602* and JD112501*, and batch_key applies them after normalising, so the two spellings key alike everywhere at once. The rule itself is unchanged — a star on a spelling no person has ruled on still keeps the mark. Consequence in the build: iCoA-PP_26-087, -088 and -090 take their testing dates from the packaging (20.05, 21.05, 25.05.2026) and the release certificates of P060302 and P060312 are no longer withheld.

**Needed.** The four rows for GG012601*, JD012601*, SCR012601* and FB012602* say "the desk, as a consequence of the ruling" where the JD112501* row says "Head of QC". One word from the Head of QC turns the four into rulings; one word reverses them.

## Method status

### OI-30 · The Loss on Drying method text is not verified per lot against the era it was tested in

*State:* **open** · *Evidence:* ISSUANCE_RULES_2026-09-10.md §4; extract_product_specifications.py #8; 70 numeric results, 1 in the disputed band (already resolved)

**Found.** ISSUANCE_RULES_2026-09-10.md §4 records the ruling: "the Center for Natural Products first used the German pharmacopoeia method for the cannabinoids with loss on drying < 10 %; after the Ph. Eur. cannabis monograph 3028 it uses the Ph. Eur. method and ≤ 12 %. Both eras are on file and the certificates should attribute the method each lot was actually tested by." The certificate prints one method line for every lot — "Ph. Eur. 2.2.32 (3028) · at 40 °C, 24 h, 15–25 mbar", ≤ 12.0 % — regardless of which method the certifying laboratory actually used. Only one lot's own numeric result sits where the two criteria disagree — J31122501, 10.30 % on 100-2-ГС/26 — and that one is already resolved: the certificate prints its own limit as < 12, so ≤ 12.0 % is its own specification, not a substitution (export_coq_artifact_data.py corpus_contradictions, documented 31.08.2026). The other 69 numeric results are all under 10 %, where the two criteria agree regardless. What is NOT verified is the METHOD TEXT itself on the other ~94 lots: no certificate's own method paragraph is in the desk's record, only its number, so a lot actually tested and reported under the German pharmacopoeia method would still print the Ph. Eur. 2.2.32 (3028) method line here.

**The desk.** Nothing changed on the printed method text — it was already uniform before this check and stays uniform, because there is no per-certificate method record to read it from. Nothing is guessed.

**Needed.** Is a fixed method line acceptable because Ph. Eur. 3028 is now the specification the desk certifies against regardless of what a given laboratory used at the time (i.e. the ACCEPTANCE CRITERION is what the SOP requires today, not a transcription of each certificate's own method paragraph)? If so this item closes as designed. If not, which lots were tested under the older method needs to come from re-reading each Loss on Drying certificate's own text, which the desk has not done.

## Batch identity

### OI-31 · Six batches are silently filed under one strain name where a source document keeps two

*State:* **open** · *Evidence:* tracker/DELIVERY_RECONCILIATION_2026-09-07.md §5; tracker/strains.py; iCoA Register Strain column, 6 lots

**Found.** DELIVERY_RECONCILIATION_2026-09-07.md records, and never closes: "the desk files GG4 (GG012601, GG012603, GG112501) and Gorilla Glue (GG1024, GG1024_01, GG1024_02) under one strain name, while the delivery sheet keeps them apart as two strains." It was never promoted to a tracked question — unlike its six siblings in the same finding (Sleepy Joe/Joy, Permanent Marker/Market, Wedding Crusher/Crasher, Appels & Bananas/Apple and Banana, Jelly Donuts/Donutz, Clemosa/Clemosa a Bud), which all print on the Work Order sheet as "strain name unruled" rows. The iCoA Register today prints all six GG batches as strain ‘Gorilla Glue’ — a de facto merge nobody ruled on.

**The desk.** Nothing decided. strains.py's own rule is explicit: it repairs a missing space (decides nothing) and lists a letter-for-letter disagreement in CONFLICTS for a ruling (decides nothing either) — it does not merge two names that differ in their letters, and GG4 / Gorilla Glue do. GG012601, GG012603, GG112501, GG1024_01 and GG1024_02 carry no specification on file today regardless (OI-03), so no certificate currently prints a grade or a THC range that would be wrong if the merge is wrong — but the moment a specification is filed for either name, whichever certificate resolution runs first decides the other five lots' grade by default.

**Needed.** Is GG4 the same strain as Gorilla Glue, or a separate strain that happens to be filed under it? If separate, the six lots need their own strain field and, in time, their own specification.

### OI-32 · Five of the thirty Tranche 3 potency retests rest on one page read

*State:* **open** · *Evidence:* intake_227K_2026-09-15/ (reads_227K.json, checkpoint_master_coa_table.json, apply_227K.py); PP_Batch_Release_QC_Register_SUBLOT_2026-09-01.xlsx after apply_227K.py; tracker/batch_dates.csv

**Found.** Farmahem's 227-К/26 series — thirty cannabinoid certificates for the Tranche 3 sampling, issued 11.09.2026 — is in the record since the intake of 15.09.2026 (intake_227K_2026-09-15/): every one of them a retest, as the owner ruled on 12.09.2026, each in a campaign round of its own and sampled 19–21.08.2026 by the owner's ruling of 15.09.2026. Twenty-five were written after the page read and the checkpoint transcription of the same day (master_coa_table.tsv, commit 7393bc4) agreed on the batch, the P lot, the date and every result. Five have no second read on file: 227-1-К/26 (BSS1024_01/2, P050142), 227-4-К/26 (WED102501, P060102), 227-8-К/26 (SCR012601, P060342), 227-16-К/26 (GRC102501/1, P060142) and 227-29-К/26 (BSS1024_01/1, P050122). The first four batches had no register block and were given one (No. 90–93), with the P lot the certificate prints — the same P lot the Head of QC's batch list gives them; the fifth went into the register's BSS1024_01 block, whose P lot P050122 the certificate prints.

**The desk.** The five are written on the page read alone and say so in the tracker instance's source. The identity question the desk had raised — whether a 227-К certificate could be a batch's first potency determination — is settled by the ruling that the series is a retest series (testing_series.rounds), so the four batches' release potency is simply not on file, which the CoQ Register already flags per lot.

**Needed.** A second read of the five pages (or the owner's confirmation of the transcribed values: 26.69 / <LOQ / <LOQ; 25.15 / <LOQ / <LOQ; 22.40 / <LOQ / <LOQ; 7.50 / <LOQ / <LOQ; 26.10 / <LOQ / 0.20 for THC / CBD / CBN), and confirmation that BSS1024_01/1 on 227-29-К/26 is the register's BSS1024_01 (P050122).

### OI-33 · Two batches on the Tranche 2 mycotoxin certificates are on no list the desk holds

*State:* **open** · *Evidence:* intake_220M_2026-09-14/ (reads_claude.json n=30, 31, 32; placement.json); tracker/batch_dates.csv; PP_Batch_Release_QC_Register_SUBLOT_2026-09-01.xlsx after apply_220M.py

**Found.** Farmahem 220-31-М/26 (Fat Bastard, printed FB042601) and 220-32-М/26 (Cash Cow, printed CC042601), issued 11.09.2026, name a cultivation batch and no P-number. Neither batch is in the release register, on the Head of QC's batch list (tracker/batch_dates.csv) or on the owner's tracker — the two certificates are the desk's only record that the batches exist. A third certificate of the same delivery, 220-30-М/26 (Jelly Donutz, printed JD042601), prints no P-number either, but the batch list carries JD042601 as P060492 (harvest 21.07.2026, packaged 13.08.2026, four days before the laboratory received the sample), so its block and its tracker lot took that P-number from the list.

**The desk.** The intake of 14.09.2026 opens a release-register block for each (No. 88 and 89) with the cultivation code, no P-number and the strain as printed, and a tracker lot of the same name. With no packaging date there is no day to date an internal CoA on and no place in the issuance series; the one result each carries is ND.

**Needed.** The P-number, harvest and packaging dates of FB042601 and CC042601 for the batch list — or the ruling that they are R&D lots outside the release series, as GG1024 and CJ1024 are listed. And confirmation that the JD042601 on 220-30-М/26 is the batch list's JD042601 (P060492).

## Register scope

### OI-34 · The IJZ-MB campaign microbiology was on the tracker and not in the release register

*State:* **ruled** · *Evidence:* tracker/new_instances.json (the 30 IJZ-MB instances); tracker/split_manifest_IJZ-MB_2026-09-01.csv; build_coq_schedule.py ST_CARRIED

**Found.** The thirty IJZ-MB certificates of the campaign sampling of 25/26.08.2026 (issued 31.08 and 01.09.2026) are testing instances on the tracker since 04.09.2026 and are not rows of the release register, which is the one source the certificates of quality are compiled from. Since 15.09.2026 a reissue prints, for every determination it did not retest, the initial certificate's result — so for a lot whose microbiology WAS retested in that campaign the reissue would print the release microbiology while a newer result sits on the tracker. No Tranche 1 lot is affected (none was in that delivery). Since v30 (15.09.2026) the thirty Tranche 2 reissues ARE numbered, planned 18.09.2026, so a Tranche 2 lot in that delivery would print its release microbiology; the Tranche 3 reissues still wait for their mycotoxin certificates.

**The desk.** CLOSED 16.09.2026 by intake_IJZMB_2026-09-16. The sweep of that day measured the harm the item had predicted: 24 certificates of quality printed microbiology a newer certificate for the same lot contradicted, twelve of them reissues, and not by a little — P050012 printed TAMC 2.1 × 10⁴ where the campaign certificate reads < 10. 29 of the 30 certificates are now rows of the release register, through the same two-read gate the 220-М, 227-К and 220-К intakes used, with four value disagreements settled by a third read of the page (OI-36's defect class, four more instances). One is held back: 548/1079/26, whose lot is in doubt — OI-37.

**Needed.** Nothing further, unless the owner rules on OI-37 (the held certificate) or on OI-13 (the expanded panel this same delivery reports).

## Batch identity

### OI-37 · One campaign microbiology certificate names a strain that is not its filed lot's

*State:* **open** · *Evidence:* the scan 310826_548-1079-26_IJZ-MB_BSS052501-P050192.pdf in eCoA_DATABASE; tracker/split_manifest_IJZ-MB_2026-09-01.csv; intake_IJZMB_2026-09-16/reads_IJZMB.json

**Found.** 548/1079/26 of 31.08.2026 is filed under P050192 — BSS052501, Blue Sunset Sherbet — because its typed serial reads PO50192, which canonicalises to P050192. But the page prints the sample as "Сув цвет од канабис сорта Sleepy Joe" and carries a HANDWRITTEN P060192 beneath the typed serial; P060192 is SJ112501, whose strain the release register gives as Sleepy Joy. The printed strain and the handwriting agree with each other and disagree with the typed serial. Read on the page of 16.09.2026. P060192 has no campaign microbiology certificate of its own on file; P050192 would have this one. Three other campaign certificates print a strain the register spells differently (Cap Junky against the register's Cup Junky, on 556/1087/26, 558/1089/26 and 565/1096/26) — that is a spelling, not a different strain, and is not this.

**The desk.** The certificate is NOT written into the release register: a microbiology result on the wrong lot's certificate of quality is worse than a missing one. The other 29 of the delivery are written. P050192's certificates therefore still print its release microbiology, and its reissue will say so.

**Needed.** Which lot 548/1079/26 belongs to: P050192, as the typed serial reads, or P060192, as the printed strain and the handwritten correction say?

## Certificate content

### OI-38 · Fourteen reissues carry the initial result while a later one for the same lot is on file

*State:* **open** · *Evidence:* intake_IJZMB_2026-09-16/carried_microbiology_2026-09-16.csv (26 rows, 12 reissues); tracker/RESULT_SUPERSESSION_2026-09-16.md section 1 (31 rows, 14 reissues); build_coq_schedule.py ST_CARRIED; the ruling of 15.09.2026

**Found.** Since 16.09.2026 the IJZ-MB campaign certificates of 25/26.08.2026 are rows of the release register (intake_IJZMB_2026-09-16), so the desk now holds, for 29 lots, a microbiology result LATER than the release one. A reissue rests on its Farmahem campaign (220- or 227-), whose scope is the assay and the mycotoxins; microbiology is outside that scope, so the reissue carries the initial certificate's result — the owner's ruling of 15.09.2026, correctly applied. The consequence is that twelve reissues will print a microbiology result that a newer certificate for the same lot contradicts, and not narrowly: CoQ-PP_26-144 (P050012) carries TAMC 2.1 × 10⁴ where 561/1092/26 of 01.09.2026 reads < 10, and CoQ-PP_26-153 (P050132) carries TYMC 3.3 × 10⁴ where 560/1091/26 reads < 10. The 26 rows are listed in intake_IJZMB_2026-09-16/carried_microbiology_2026-09-16.csv. The twelve RELEASE certificates that print the same release values are not in question: a release certificate states the release testing, and a later retest does not belong on it. The sweep of 16.09.2026 (result_supersession.py) then asked the same question of all seventeen determinations the register carries and found the shape is not confined to microbiology: 31 rows on FOURTEEN reissues, 29 of them the twelve microbiology reissues above and TWO of them loss on drying — CoQ-PP_26-093 (P050022) carries 7.21 % from ППК25139 of 22.05.2025 where ППК25174 of 10.07.2025 reads 6.51 %, and CoQ-PP_26-150 (J31112501) carries 8.4 % from 051-5-GS/26 of 02.03.2026 where 100-1-GS/26 of 09.04.2026 reads 7.6 %. Neither superseding certificate is a stability timepoint. The sweep reports its coverage beside every zero: no lot on file carries a second HEAVY-METAL certificate (45 documents, 0 lots with two), so #11 could not be compared at all and its silence is a gap in the record rather than a clean result; aflatoxin B1, ochratoxin A and the pesticide panel were comparable on one lot each. Total aflatoxins over 30 lots, Total CBN over 12 and Salmonella and E. coli over 14 each are real zeros. One more consequence the owner should weigh with this: for THIRTEEN lots the campaign certificate is the ONLY microbiology on file. Until 16.09.2026 those lots' RELEASE certificates printed it, which put a document of 31.08 or 01.09.2026 on a certificate dated 06.06, 07.07 or 13.07.2026 — impossible, and now fixed: a retest-only document can no longer stand behind a release result, so those thirteen release certificates print nothing for #9.1-#9.5. If the ruling here is CARRY THE INITIAL, their reissues print nothing either and the thirteen lots have no microbiology on any certificate of quality at all. If it is PRINT THE LATEST, the campaign result lands on the reissue, which is the only certificate dated after it. The thirteen are BSS1024_01/2, CC112501, FB012603, FB012603V, FB112501, GG112501, GRC102501/1, J31112501, OPM112501, SCR012601, SCR022601, SJ102501 and WED102501.

**The desk.** Nothing on the certificates. The campaign results are in the register, on the tracker and in the compilation, so the newer result is visible everywhere the desk shows its working; what a controlled document prints is the owner's to rule, not a defect to repair silently. The IJZ-MB delivery is also a different sampling from the tranche it would be printed on — 25/26.08.2026 against 12–14.08 (Tranche 2) and 19–21.08 (Tranche 3) — so it is not simply 'the same campaign, later certificate'.

**Needed.** When a reissue carries a determination forward because its campaign did not retest it, should it carry the INITIAL result or the LATEST result on file? For microbiology that is the IJZ-MB campaign of 25/26.08.2026, sampled on a different day from the Farmahem campaign the reissue rests on; for loss on drying it is an ordinary repeat test by the same laboratory. If the answer is the latest, does the reissue then cite two or three samplings on one certificate?

## Batch identity

### OI-39 · Two register blocks carry two sublots each, and the certificate prints one of them

*State:* **open** · *Evidence:* tracker/RESULT_SUPERSESSION_2026-09-16.md section 3; the register block J31122501 (10 certificates); tracker/batch_dates.csv row 64; OI-12 for the JD112501 half

**Found.** The sweep of 16.09.2026 (result_supersession.py, check `parallel`) looked for a block holding two certificates of the SAME testing on the SAME day that report DIFFERENT results. Over 93 blocks there were two; one of them, JD112501, was ruled on 16.09.2026 to be one batch and two samples and is now OI-12, leaving one. **J31122501** (Jokerz 31, P060262) holds three such pairs: the microbiology of 07.04.2026, where 231/0394/26 names its sample Рачно тримиран цвет (hand-trimmed flower) and reads TAMC 850 while 230/0393/26 names Тримиран цвет (trimmed flower) and reads 1900; the Farmahem cannabinoids of 09.04.2026, 100-2-К/26 at 19.84 % against 100-3-К/26 at 21.84 %; and the IJZ mycotoxins and metals of 23.04.2026, 1628/2026 against 1625/2026. The documents themselves say these are two products of one cultivation batch, tested in parallel. The owner's batch list gives J31122501 exactly one P lot, P060262, so the register has no second number to file the second product under. The starred-sample ruling does NOT reach this block: these pages carry no asterisk, and they name two PRODUCTS on three separate dates, not two samples of one.

**The desk.** Nothing invented. testing_series.rounds() treats two documents of one day as one testing period — right when they describe one sample — so both sit in the release round and the certificate of quality prints the first: 231/0394/26, 100-2-К/26 and 1628/2026. The tracker shows BOTH — 100-2/1628/231 and 100-3/1625/230 as separate testing instances — so nothing is hidden anywhere the desk shows its working. What the certificate of quality does not say is WHICH product it certifies.

**Needed.** Is J31122501 one lot or two? If two, what P lot number does the second carry, and does it need its own certificate of quality — which would make the three documents the certificate does not print (230/0393/26, 100-3-К/26, 1625/2026) the second product's record rather than unused results? If one, which of each pair is the lot's result?

## Document identity

### OI-40 · Six lots hold two register rows for one testing, the results on the composite row

*State:* **open** · *Evidence:* register rows 123/124, 127/128, 131/132, 135/136, 139/140, 163/165; tracker/HANDOVER_RESPONSE_2026-09-16.md §2.2

**Found.** The audit of 16.09.2026 flagged six document codes of the form "PP CoA #027 / ППК25370" — an in-house certificate number and a Center for Natural Products number in one cell. Reading the register shows why it matters: EVERY one of the six also exists as a bare ППК row on the same lot, with its own EARLIER date and NO results. P050282 row 123 "PP CoA #027 / ППК25370" of 21.01.2026 carries THC 8.02, CBD 0.04 and loss on drying 9.68; row 124 "ППК25370" of 28.11.2025 carries nothing. The same shape on P050292/ППК25378 and P050302/ППК25379 (bare rows 12.12.2025), P050312/ППК25380, P050322/ППК25381 and P060052/ППК26005. So for these six lots the results sit on the composite row and the row that names the external certificate alone is empty — and the certificate of quality therefore prints "PP CoA #027 / ППК25370" dated 21.01.2026 as its document.

**The desk.** Nothing changed. document_codes.py canonicalises SPELLING only and leaves these composites exactly as the register writes them: deciding which of two rows is the certificate, and which date the certificate of quality should cite, is not a spelling. The six are listed here with their rows so the owner rules on the record.

**Needed.** For these six lots, which row is the certificate the certificate of quality should cite — the Center for Natural Products certificate on its own date, or the in-house certificate of 21.01.2026 that carries the results? And should the two rows be one row, with the in-house number as a cross-reference?

## Document content

### OI-41 · Eighty-two certificates print no result for the three determinations done in-house

*State:* **open** · *Evidence:* 44 lots, 82 certificates, 246 determination rows; build_coq_schedule.ST_ICOA; tracker/HANDOVER_RESPONSE_2026-09-16.md §2.1

**Found.** Determinations #1 Identification A, #2 Identification B and #7 Foreign matter are performed in the Purely Plant laboratory on every batch. On 82 of the 172 certificates — 44 lots — all three print nothing: the row cites the lot's internal certificate and the laboratory, and the result reads "—" with the status "to be performed — see route". The other 90 certificates print Conforms. The desk is not failing to find the internal certificate (it cites one on all 172); it has no RECORD OF THE RESULT for those 44 lots, and rule six forbids printing a result that has not been certified. The audit of 16.09.2026 read the same 82 as a builder fault and counted 41 of them; it is not a builder fault and it is 82.

**The desk.** Printed as the desk holds it: the determination named, the internal certificate cited, the result blank and the route stated. Nothing is asserted that no record supports.

**Needed.** Either the in-house results for the 44 lots are recorded somewhere the desk has not been given — in which case, where — or the testing is on the internal certificate without a separate written result, in which case may the certificate of quality print Conforms on the strength of the internal certificate alone?

## Record integrity

### OI-42 · Forty-four laboratory certificates are on Drive and in no record of the desk; 58 more are only in the 09.09 pass

*State:* **open** · *Evidence:* tracker/FLEET_FINDINGS_2026-09-16.md (audit A); the Drive tree 1SmOicCRa8KEqoB-YlCojdap161YMQ-Di and _IN-HOUSE_PP 1bBGgFavrUTOu7PC7VVRcj0P4onWOAquN, enumerated 16.09.2026

**Found.** The audit of 16.09.2026 enumerated the owner's eCoA_DATABASE on Drive (490 scans: 449 laboratory, 41 in-house) and held it against every desk record — the ingested corpus, the release register and the 09.09 resolution pass. Forty-four laboratory scans are in NONE of them: 20 IJZ contaminant reports (mycotoxins, metals, pesticides — 329/2026 WED102501, 1057/2026 J31112501, 1061/2026 SJ112501, 1062/2026 OPM112501, 1065/2026 SJ102501, 3654–3658/2026 P160032, P160022, P160012, SCR022601, JD022601, 3661/2026 FB012603, 3663/2026 FB012603V, 3924/2026 FB032601, 3925/2026 GG032601, 4374/2026 JD032601, and the five of 29–30.04.2026 taken in the same day), 22 IJZ-MB microbiology reports (319/0586/25 GP0824_01; 75/0118/26 WED102501; 130–137/02xx/26 SJ112501, J31112501, SJ102501, OPM112501; the five of 28.04.2026 taken in the same day; 362/0692/26 SCR012601; 402–411/07xx/26 JD022601, SCR022601, FB012603V, FB012603, P160012, P160032, P160022; 433/0847/26 and 434/0848/26 FB032601; 477/0929/26 JD032601) and the two Farmahem certificates 031-3-К/26 and 031-3-ГС/26 of WED102501. A further 58 scans are cited in the 09.09 pass and never reached the register or the corpus — among them the whole Farmahem 031 campaign of February 2026 and 534/1065/26 and 535/1066/26 of the 31.08.2026 IJZ-MB delivery, which fall outside the 536–565 range the IJZ-MB intake took. For every one of the 20 IJZ reports the lot's register block holds NO metals, mycotoxin or pesticide document at all, so the certificate of quality prints "not tested — no certificate covers it" for #10–#12 while the report sits on Drive, dated before the certificate — and the sweep's "no lot carries a second heavy-metal certificate" is a register gap, not a testing fact. The reverse direction is clean: every laboratory code the desk holds has a scan (0 of 403 missing).

**The desk.** The eighteen of 21.04.2026 whose two reads existed were taken in on 16.09.2026 (intake_IJZ0426_2026-09-16). The remaining 44 + 58 have no read on the desk yet; each needs the two-read gate before it is written, and until then the certificates named above print "not tested" where a document exists. Nothing is written from a listing.

**Needed.** Nothing to decide for the intake itself — it is the desk's next work. Three lots on the batch list need a word: JD032601 (P060472) has an IJZ-MB and an IJZ report on Drive and no release-register block and no CNP potency certificate anywhere — is it a production lot? SC062501 (P050242) and GOG062501 (P050232) have no document on Drive at all — were they ever tested?

### OI-43 · Twenty-eight in-house certificates of analysis are on Drive with no desk entry — twelve of them for lots OI-41 names

*State:* **open** · *Evidence:* tracker/FLEET_FINDINGS_2026-09-16.md (audits A and B); the 41 scans in _IN-HOUSE_PP

**Found.** _IN-HOUSE_PP holds 41 in-house scans: 38 QCCoA 001 / 001v02 forms named <ddmmyy>_QCCoA 001[v02]_PP_<batch>-<P lot>.pdf and the three Reports of Analysis of 23.04.2025. The desk's in-house entries number 16 and match 13 of the scans. The 28 without any desk entry are the QCCoA 001 of BG1024, BSS1024, CJ1024, MB0824_04, OMP1024_01, GP0824_02 (twice), GG1024_02, GP0824_03, HPA1024_01, OPM1024_02, GG1024_01, P050102, HPA052501, CJ052501-01, BSS1024_01-1, GP062501 (v02) and the eleven QCCoA 001v02 of 21.01.2026 (GP082501-1/-2, GP072501-1/-2, CLE072501, PM072501, P050212, CJ052501-02, OPM052501, MB0824_05, OPM1024_03), plus the three Reports of Analysis. Twelve of the 44 lots whose certificates print nothing for #1, #2 and #7 (OI-41) have one of these scans — the in-house record OI-41 asks for exists on Drive for them.

**The desk.** Nothing read, nothing written: an in-house scan reaches the desk through the same two-read gate as a laboratory certificate, and the desk holds no read of any of the 28.

**Needed.** May the desk take the QCCoA 001 scans in as the record of the in-house results, so that the certificates of those twelve lots print what the form states for #1, #2 and #7 and cite the internal certificate that carries it? If yes, OI-41 shrinks from 44 lots to 32.

## Tracker scope

### OI-35 · The tracker does not carry the documents of the 09.09 pass that eleven certificates print from

*State:* **open** · *Evidence:* tracker/TRUTH_CHECK_2026-09-15.md (T5); cell_resolution_2026-09-09.tsv; coq_artifact_data.json rows citing those codes

**Found.** The truth check of 15.09.2026 (tracker/truth_check_2026-09-15.py) compared every row of every certificate with the tracker's cells for the lot. Twenty rows on eleven certificates cite a document the tracker holds nowhere: the 17 documents the owner's 09.09.2026 pass over eCoA_DATABASE recorded (cell_resolution_2026-09-09.tsv) and the two-read pipeline never ingested — ППК25008 and 748/2025 (GG1024: the loss on drying of 76.07 % and the pesticides), 031-2/4/5-К/26 and 031-2/4/5-LoD/26 (P060112, P060122, P060132: the Farmahem cannabinoid and loss-on-drying certificates of 10.02.2026), 326/327/330/2026, 1056/1058/1059/1060/2026 and 3659/3660/3662/2026 (the IJZ pesticide certificates of P060112, P060122, P060132, P060152, P060172, P060182, P060232, P060402, P060412, P060422). Each rests on one page read. The tracker's document pool is the desk's index plus the intake instances, so its cell for GG1024 #8 reads '— MISSING —' while the certificate prints 76.07 % from ППК25008, and J31122501 #8 cites the cannabinoid certificates where the certificate cites the loss-on-drying certificate 100-2-ГС/26.

**The desk.** Recorded, not built: the 17 documents need the two-read intake the 220-М, 227-К and 220-К certificates had before the tracker credits them, and the certificate rows that rest on them are marked on the references table as single-read.

**Needed.** Whether the desk should read the 17 documents of the 09.09 pass through the two-read gate now, so that the tracker and the certificates cite one record — or whether the certificates that print from a single read (GG1024 above all) wait for it.

## Record integrity

### OI-36 · Four two-read corpus records passed the gate with their reads disagreeing on a comparator

*State:* **open** · *Evidence:* tracker/TRUTH_CHECK_2026-09-15.md (T3, T4, T5); ingestion/ecoa_runner/records_corpus.json; the four page reads of 15.09.2026

**Found.** The truth check of 15.09.2026 found four IJZ-MB microbiology results where the owner's v8 tracker and one of the two corpus reads carried a value the page contradicts, and the corpus record was marked as agreed: 5/0008/26 TAMC (read A '< 1 x 10²', read B '1 x 10²', record kept A; the page prints 1 x 10² CFU/g), 9/0012/26 bile-tolerant (A '10', B '< 10', record kept B; the page prints < 10), 471/0862/25 TYMC (A '10', B '< 10', record kept B; the page prints < 10), 304/0548/26 bile-tolerant (A '< 10²', B '< 10² и >10', record kept B; the page prints < 10² и > 10). In every case the release register was right and v8 was wrong; the certificates print the register's value. The same check found the 09.09 pass table (cell_resolution_2026-09-09.tsv) holding Total THC, CBD and CBN values for 197-13-К/26, 197-7-К/26 and 197-6-К/26 that neither the register nor the two reads carry (19.68 / 24.09 / 23.29 % against 17.31 / 18.86 / 17.67 %); nothing prints them.

**The desk.** The four tracker cells are corrected from a third read of each page (tracker/value_corrections_2026-09-15.json, applied in values_of). The corpus records and the pass table are the ingestion's and are left as they are, listed here.

**Needed.** Whether the ingestion's reconciliation should treat a comparator ('<', '>') as part of the result when it compares two reads, and re-gate the four records; and whether the three pass-table cells should be corrected or the rows retired.

## Panel scope

### OI-13 · The expanded microbiology panel HAS been run and no certificate says so

*State:* **open** · *Evidence:* Ph. Eur. 2.8.13; Ph. Eur. 2.6.13 expanded panel

**Found.** Corrected 16.09.2026. This item said until today that the expanded microbiology option (P. aeruginosa, S. aureus) "has never been run" and that "neither is claimed on any certificate". That was false, and it had been shipped in OPEN_ITEMS.md and in the workbook since 11.09.2026. Thirty-one certificates on file report the panel — every one of the thirty IJZ-MB campaign certificates of 31.08/01.09.2026 and 1221/2172/25 of 01.12.2025 — and all report both organisms ABSENT. What remains true of the other panel: the pesticide option offers Ph. Eur. 2.8.13 and a CUMCS equivalency, and no lot was tested to equivalency. Determinations #9.6 and #9.7 print nothing on all 172 certificates of quality, marked "upon request — not required for release", while a result exists for 31 of them.

**The desk.** The panel results are kept in intake_IJZMB_2026-09-16/reads_IJZMB.json. They are NOT written into the owner's release register, which has no column for either organism, and the certificates are not changed: what a controlled document claims is the owner's to decide, not a defect to repair silently.

**Needed.** Should a certificate of quality print #9.6 and #9.7 where the laboratory reported them (31 lots, both absent) — and should the register gain a column for each so the result lives beside the other five? And, unchanged: should the certificates record that the pesticide equivalency option exists and was not exercised, or stay silent on it?

## Document content

### OI-14 · Two fields still print a specimen or a placeholder

*State:* **open** · *Evidence:* _CoQ_MASTER_Template.html; 22 drafts

**Found.** The two approvers' names are the master template's specimen. The potency acceptance range is a bracketed placeholder in both places it prints.

**The desk.** Both print bracketed in red and unticked, so no draft can be mistaken for issued. (A third field once listed here — Identification C's document sourcing — is built: _pick(4, False) or _pick(3, False) resolves it on every one of the 22 drafts, 0 falling back to the unresolved message. Closed 11.09.2026, folded out of this item rather than left to read as still open.)

**Needed.** The approvers' names and titles; the potency range per grade.

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

