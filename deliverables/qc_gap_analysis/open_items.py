#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""What the desk cannot decide: the standing register of items awaiting the owner.

    python3 deliverables/qc_gap_analysis/open_items.py            # self-test + census
    python3 deliverables/qc_gap_analysis/open_items.py --md       # write the note

A quality desk can normalise a spelling, derive a column and read a verdict off a
page. It cannot decide whether a grade IV lot may cite a grade III specification,
which analyte a mycotoxin figure belongs to, or whether a controlled document may
be dated on a Saturday. Those are the owner's, and until 11.09.2026 they lived in
chat messages and commit bodies, which is to say they were being rediscovered
every session.

This is the register. Each item says what was found, what the desk did with it,
and precisely what is being asked — because "there is a problem with the
specifications" is not a question anyone can answer, and "may a grade IV lot cite
the grade III specification of the same strain, given that no printed attribute
has ever differed between grades in 257 issued documents" is.

Every item carries its evidence: the file and the figure behind it, so the owner
is ruling on the record rather than on a summary of it.

`STATE` is one of:

    open        the desk is waiting; nothing is being printed on a certificate
    marked      the certificate prints the field bracketed in red, unticked
    ruled       the owner has ruled; kept here for the record with the ruling
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# (ref, area, state, headline, found, desk, asked, evidence)
ITEMS = [
    ("OI-01", "Specification", "marked",
     "A lot graded IV or V whose strain has no specification at that grade",
     "The QCSP 001 specification is issued per strain AND per grade. Cap Junky is on file "
     "at grades I, II and III; CJ082501/2 is grade IV. Grape Pie and Orange Punch Mimosa "
     "stop at IV and each has a grade V lot. Exactly one grade V specification exists in "
     "the whole issued set (Clemosa).",
     "The phenotype, chemotype, processing and packaging pills are left unticked and the "
     "band is marked, on 3 lots.",
     "May a lot cite the specification of its own strain at the nearest grade on file? "
     "The evidence says the attributes do not depend on grade: across 71 strains and 257 "
     "issued specifications, phenotype, dominance, chemotype, processing and packaging "
     "differ between grades of one strain in ZERO cases.",
     "spec_attributes_2026-09-10.csv; CJ082501/2, GP082501/2, OPM122501"),

    ("OI-02", "Specification", "marked",
     "Two certificates name a specification by potency band instead of grade",
     "GP052501 names QCSP_001_GP-THC18_v.01 and GRC102501/2 names QCSP_001_GRC-THC12_v.01. "
     "Neither exists in the issued set under any name — but QCSP_001_GP-IV_v.01 does, and "
     "IV is the grade GP052501 carries.",
     "Both pills are marked. No substitution was made without a ruling.",
     "Is the potency-band name an older convention for the same document? If so the desk "
     "joins on the grade and both resolve immediately.",
     "export_coq_artifact_data.py specification join; 2 lots"),

    ("OI-03", "Specification", "open",
     "Thirty-two lots have no grade, so no specification can be named at all",
     "The grade comes from product_specifications_QCSP001.json, built from the specification "
     "copies handed out with the tranches, which covers 48 of the 80 lots. For the other 32 "
     "the desk cannot compose a specification code, and the certificate names none.",
     "Nothing is printed and nothing is guessed.",
     "Where is the grade for the remaining 32 lots recorded? Once the desk has it, the "
     "specification code follows from the strain and the pills fill themselves.",
     "48 of 80 lots indexed; 68 of 164 certificate records carry no grade"),

    ("OI-04", "Result reading", "marked",
     "Four lots where which analyte the figure belongs to decides pass or fail",
     "The release certificates print the mycotoxin sub-parameters as one block and the desk "
     "maps the value to an analyte by its position in the block, not by a printed name. "
     "CLE072501, OPM092501, OPM1024_03 and OPM122501 report 2.1–2.2 µg/kg: as total "
     "aflatoxins (limit 4) they pass, as Aflatoxin B1 (limit 2) they fail.",
     "The figure is printed as the desk reads it and the lot is named here. None of the four "
     "may be signed until a person has read the page.",
     "Read the four certificates and confirm which analyte the figure belongs to.",
     "COQ_DRAFTING_2026-09-10.md; 4 lots"),

    ("OI-05", "Result reading", "open",
     "Nineteen lots print a Total Δ⁹-THC outside the range printed beside it",
     "The acceptance test was one-sided — it asked only whether a value exceeded its limit — "
     "so an assay BELOW its band was never flagged anywhere. Corpus-wide, 19 lots carry a "
     "potency outside the range on their own certificate, every one recorded as covered.",
     "The comparison now happens in the gap report, never on the certificate, and the report "
     "declines any criterion it cannot read as two numbers.",
     "Each of the 19 needs a disposition: re-read, re-test, or a regrade.",
     "status_of / the two-sided criterion; 19 lots"),

    ("OI-06", "Reconciliation", "open",
     "Forty-six disagreements between the desk and the owner's 09.09 pass",
     "Put side by side on the Reconciliation 09.09 sheet: 218 determinations agree, 46 do "
     "not. One was a loss on drying of 76.07 % read on GG1024 against a 12.0 % limit: the "
     "Head of QC ruled it a typo on 17.09.2026 and set the value to 7.8 % (ППК25008), so "
     "both GG1024 certificates now print 7.8 % within the limit; the pass file carries the "
     "corrected value. The other 45 stand.",
     "One of the 46 is resolved by the Head of QC's ruling. The rest are not resolved by the "
     "desk; both readings are shown with their sources.",
     "A person reads the page for each of the 46 and says which reading stands.",
     "Reconciliation 09.09 sheet; 46 rows"),

    ("OI-07", "Issuance", "open",
     "Fifty-seven certificates of quality are dated on a Saturday",
     "06.06.2026, the blanket date for everything that would otherwise issue before the "
     "specification SOP, is a Saturday. The builder's own convention is that a controlled "
     "document issues on a working day.",
     "The owner's date outranks the desk's convention, so it is kept as given and the "
     "workbook carries a flag saying it was chosen deliberately.",
     "Confirm 06.06.2026, or name the working day it moves to (08.06.2026 is the Monday).",
     "issuance_schedule.COQ_BLANKET; 57 certificates"),

    ("OI-08", "Reference", "open",
     "Five result cells cite an SOP form number instead of a certificate",
     "NGP-QCG-SOP-024 F3, (28.11.2025) [NGP] carries Identification C, Total Δ⁹-THC, Total "
     "CBD, Total CBN and loss on drying for BSS052501 and GP062501 — including the banner "
     "assays 20.39 % and 24.89 %. A form number is not a document code and cannot be cited "
     "on a certificate of quality.",
     "The reference is printed as it stands and the lots are named here.",
     "Does the NGP laboratory issue a numbered report for this work? If not, these results "
     "need a different basis.",
     "2 lots, 10 result cells"),

    ("OI-09", "Reference", "open",
     "One laboratory report is on file twice, once per language",
     "10802_2845-2 EN and 10802_2845-2 MK are the same DFL report for BSS052501, cited as "
     "two documents, which is why that lot's certificate count reads one higher than the "
     "sheet's.",
     "Both are cited as the desk found them.",
     "Confirm the two files are one report, and which language version is the controlled copy.",
     "BSS052501; Batch Coverage Certificates (n)"),

    ("OI-10", "Batch identity", "open",
     "Three delivered lots have no cultivation batch recorded anywhere",
     "P160012, P160022 and P160032 carry full CNP results (ППК26117/18/19, 06.07.2026) and a "
     "P number in a series of their own, but no cultivation batch, and no row at all in the "
     "Head of QC's Batch Dates list — so no manufacturing date and no internal CoA basis.",
     "Each row now names its P number inside the label so the three are distinguishable and "
     "no join collapses them; the cultivation batch is left unrecorded rather than invented.",
     "What are the cultivation batches, manufacturing and packaging dates for the P1600xx "
     "series?",
     "3 lots; also absent from Batch Dates: JD112501＊"),

    ("OI-11", "Batch identity", "open",
     "One lot carries two P batches in a single cell",
     "GRC102501 is recorded against P060142 / P060182 in one cell, so its coverage row "
     "aggregates what are arguably two lots and its certificate count cannot reconcile.",
     "Left as the owner's tracker records it.",
     "Are these one lot packed into two P batches, or two lots sharing a cultivation batch? "
     "If two, they need two rows.",
     "GRC102501"),

    ("OI-12", "Batch identity", "ruled",
     "A lot and its ＊ sub-lot are credited from the same three documents",
     "JD112501 and JD112501＊ both cite ППК26065, 2365-2026 and 306-0550-26. On the parent "
     "those readings are marked on file, not credited; on the sub-lot they are credited. The "
     "sub-lot's microbiology block also carries the parent's round-1 values while its "
     "cannabinoids and metals come from round 2. Read on the pages on 16.09.2026: ППК26063 "
     "and ППК26065 are the same lot P060212, the same sample description (Сув сомелен цвет "
     "од медицински канабис сорта Jelly Donutz), the same delivery of 21.04.2026, the same "
     "DAB method and the same 12 g — the batch number is the ONLY difference between the two "
     "pages, ППК26063 reading JD112501 and ППК26065 reading JD112501*. The owner's own "
     "resolution pass of 09.09.2026 gives JD112501/P060212 a complete panel and cites "
     "ППК26063 for #3-#6 and #8; ППК26065 is cited nowhere in it.",
     "Owner's ruling of 16.09.2026: \"The asterisk is probably some experiment and is "
     "generally not the result that will go for the batch release official documentation. If "
     "both THC results are assigned with the same P number production batch, that means it is "
     "the same batch, but two samples have been sent for the parameter. You will NOT ignore "
     "the value and data with the asterisk — you will include it in calculation statistics "
     "and all — but in the CoQ you will take the other value and corresponding certificate.\" "
     "So it is ONE batch and two samples, not two lots. testing_series.EXPERIMENTAL holds the "
     "starred certificates and build_coq_schedule drops them before the release/reissue "
     "split, so they source no certificate of quality; everywhere else the result stands. The "
     "certificates were already right: CoQ-PP_26-057 prints 19.64 % from ППК26063 and "
     "CoQ-PP_26-098 prints 20.32 % from 197-15-К/26. Neither prints 13.93 %.",
     "Two consequences of the ruling to see, and one thing still unwritten. (1) The 09.09 "
     "resolution pass cited 306-0550-26 — the STARRED sample's microbiology, TAMC 1 × 10⁴ — "
     "for JD112501's #9, and the unstarred 2361-2026 for #10–#12. Under the ruling the starred "
     "sample does not certify, so since the intake of 16.09.2026 (intake_IJZ0426_2026-09-16) "
     "CoQ-PP_26-057 cites 307/0551/26, TAMC 2,6 × 10³, for #9. Both conform. Is that right, or "
     "does the pass's choice stand for microbiology? (2) The certificate's \"Also on file\" "
     "note no longer names the starred value beside the release result (13.93 % beside "
     "19.64 %): the exclusion reaches the footnote as well as the cited document. Should the "
     "certificate declare on its face that a second sample exists, or stay silent about it? "
     "(3) What the asterisk DENOTES on the floor — hand-trimmed material, a different drying "
     "or milling treatment, a sampling position — is still unwritten; the pages do not say "
     "and the desk will not infer it.",
     "ППК26063 / ППК26065 (both P060212); the scans 110526_ППК26063_CNP_JD112501-P060212.pdf "
     "and 110526_ППК26065_CNP_JD112501＊-P060212.pdf; cell_resolution_2026-09-09.tsv; "
     "testing_series.EXPERIMENTAL"),

    ("OI-29", "Document identity", "open",
     "The two series count different things, so they cannot be the same length",
     "The ruling of 10.09.2026 says the internal certificates are \"one per testing round, "
     "which is EXACTLY the number of certificates of quality\". They are not, and the reason "
     "is that the two registers count different things. icoa_register.py counts rounds the "
     "testing record SHOWS: 102 over 76 lots. The certificate-of-quality model counts "
     "certificates it PLANS: exactly two per lot — one release and one 12-month retest — 164 "
     "over 82 lots, 103 of them predicted. Across the 76 lots both carry, the counts agree on "
     "14 and differ on 62. GP0824_02 has six testing rounds and two certificates of quality; "
     "GP062501 has five; GP0824_03 has four.",
     "Nothing renumbered. The internal register was brought to one row per round on "
     "11.09.2026 because that is what the ruling says it is; the CoQ series was left exactly "
     "as it stands, because renumbering controlled documents the owner has already seen is "
     "not a change to make on a reading. No certificate loses a code to this today: no lot "
     "has more than one non-initial certificate of quality, so the single |R row still "
     "resolves for every one of them.",
     "Does a lot with four retest rounds take four reissued certificates of quality — one per "
     "round, matching its four internal certificates — or one reissue per retest campaign, as "
     "the register plans now? The first reading makes the ruling's arithmetic true and "
     "renumbers the CoQ series; the second keeps the series and means the sentence describes "
     "the rounds that produce a certificate, not every round on the record.",
     "icoa_register.py 102 rounds / 76 lots vs coq_artifact_data.json 164 records / 82 lots; "
     "3 lots with 4, 5 and 6 rounds"),

    ("OI-28", "Batch identity", "ruled",
     "The starred spellings are one lot each with their unstarred namesakes — applied; one word confirms it",
     "Raised on 10.09.2026 as seven starred lots with no internal certificate. The audit of "
     "16.09.2026 re-read the premise: only THREE of the seven are starred anywhere (GG012601*, "
     "JD012601*, SCR012601* on the Head of QC's batch list; GG1024, BSS1024_01/2, WED102501 and "
     "GRC102501 carry no star and were resolved by v31), and all seven have carried an iCoA row "
     "since the 227-К and 220-М intakes. What the star still broke was two lots: the batch list "
     "writes GG012601* against P060302 and JD012601* against P060312, the release register "
     "labels the same blocks GG012601 and JD012601 with no P number, and icoa_register.py "
     "looked the packaging date and the P lot up by the unstarred label — so iCoA-PP_26-087 "
     "and -088 had no testing date and the two Tranche 3 release certificates stood at "
     "\"— at issue —\", withheld over a glyph. iCoA-PP_26-090 (SCR012601) had no testing date "
     "for the same reason. No unstarred twin sample exists for any of the three: the "
     "certificates that name the lot print the star (ППК26062, 310/0554/26, 2364/2026; "
     "ППК26064, 309/0553/26, 2363/2026), each P number has exactly one cultivation-batch "
     "spelling on the list, and the identity questions of 07.09.2026 proposed one lot for "
     "each (and for FB012602*, starred on the list alone).",
     "Applied as a consequence of the ruling of 16.09.2026 — \"if both THC results are "
     "assigned with the same P number production batch, that means it is the same batch\" — "
     "recorded as data: ingestion/ecoa_runner/identity_decisions.tsv carries a batch_alias row "
     "for each of GG012601*, JD012601*, SCR012601*, FB012602* and JD112501*, and batch_key "
     "applies them after normalising, so the two spellings key alike everywhere at once. The "
     "rule itself is unchanged — a star on a spelling no person has ruled on still keeps the "
     "mark. Consequence in the build: iCoA-PP_26-087, -088 and -090 take their testing dates "
     "from the packaging (20.05, 21.05, 25.05.2026) and the release certificates of P060302 "
     "and P060312 are no longer withheld.",
     "The four rows for GG012601*, JD012601*, SCR012601* and FB012602* say \"the desk, as a "
     "consequence of the ruling\" where the JD112501* row says \"Head of QC\". One word from "
     "the Head of QC turns the four into rulings; one word reverses them.",
     "ingestion/ecoa_runner/identity_decisions.tsv (batch_alias, 16.09.2026); "
     "identity_questions_2026-09-07.tsv rows 2–6; icoa_register.py:227/:246; "
     "tracker/FLEET_FINDINGS_2026-09-16.md"),

    ("OI-30", "Method status", "open",
     "The Loss on Drying method text is not verified per lot against the era it was tested in",
     "ISSUANCE_RULES_2026-09-10.md §4 records the ruling: \"the Center for Natural Products "
     "first used the German pharmacopoeia method for the cannabinoids with loss on drying "
     "< 10 %; after the Ph. Eur. cannabis monograph 3028 it uses the Ph. Eur. method and "
     "≤ 12 %. Both eras are on file and the certificates should attribute the method each "
     "lot was actually tested by.\" The certificate prints one method line for every lot — "
     "\"Ph. Eur. 2.2.32 (3028) · at 40 °C, 24 h, 15–25 mbar\", ≤ 12.0 % — regardless of which "
     "method the certifying laboratory actually used. Only one lot's own numeric result sits "
     "where the two criteria disagree — J31122501, 10.30 % on 100-2-ГС/26 — and that one is "
     "already resolved: the certificate prints its own limit as < 12, so ≤ 12.0 % is its own "
     "specification, not a substitution (export_coq_artifact_data.py corpus_contradictions, "
     "documented 31.08.2026). The other 69 numeric results are all under 10 %, where the two "
     "criteria agree regardless. What is NOT verified is the METHOD TEXT itself on the other "
     "~94 lots: no certificate's own method paragraph is in the desk's record, only its "
     "number, so a lot actually tested and reported under the German pharmacopoeia method "
     "would still print the Ph. Eur. 2.2.32 (3028) method line here.",
     "Nothing changed on the printed method text — it was already uniform before this "
     "check and stays uniform, because there is no per-certificate method record to read it "
     "from. Nothing is guessed.",
     "Is a fixed method line acceptable because Ph. Eur. 3028 is now the specification the "
     "desk certifies against regardless of what a given laboratory used at the time (i.e. the "
     "ACCEPTANCE CRITERION is what the SOP requires today, not a transcription of each "
     "certificate's own method paragraph)? If so this item closes as designed. If not, which "
     "lots were tested under the older method needs to come from re-reading each Loss on "
     "Drying certificate's own text, which the desk has not done.",
     "ISSUANCE_RULES_2026-09-10.md §4; extract_product_specifications.py #8; 70 numeric "
     "results, 1 in the disputed band (already resolved)"),

    ("OI-31", "Batch identity", "open",
     "Six batches are silently filed under one strain name where a source document keeps two",
     "DELIVERY_RECONCILIATION_2026-09-07.md records, and never closes: \"the desk files GG4 "
     "(GG012601, GG012603, GG112501) and Gorilla Glue (GG1024, GG1024_01, GG1024_02) under "
     "one strain name, while the delivery sheet keeps them apart as two strains.\" It was "
     "never promoted to a tracked question — unlike its six siblings in the same finding "
     "(Sleepy Joe/Joy, Permanent Marker/Market, Wedding Crusher/Crasher, Appels & Bananas/"
     "Apple and Banana, Jelly Donuts/Donutz, Clemosa/Clemosa a Bud), which all print on the "
     "Work Order sheet as \"strain name unruled\" rows. The iCoA Register today prints "
     "all six GG batches as strain ‘Gorilla Glue’ — a de facto merge nobody ruled on.",
     "Nothing decided. strains.py's own rule is explicit: it repairs a missing space "
     "(decides nothing) and lists a letter-for-letter disagreement in CONFLICTS for a ruling "
     "(decides nothing either) — it does not merge two names that differ in their letters, "
     "and GG4 / Gorilla Glue do. GG012601, GG012603, GG112501, GG1024_01 and GG1024_02 carry "
     "no specification on file today regardless (OI-03), so no certificate currently prints a "
     "grade or a THC range that would be wrong if the merge is wrong — but the moment a "
     "specification is filed for either name, whichever certificate resolution runs first "
     "decides the other five lots' grade by default.",
     "Is GG4 the same strain as Gorilla Glue, or a separate strain that happens to be filed "
     "under it? If separate, the six lots need their own strain field and, in time, their own "
     "specification.",
     "tracker/DELIVERY_RECONCILIATION_2026-09-07.md §5; tracker/strains.py; iCoA Register "
     "Strain column, 6 lots"),

    ("OI-32", "Batch identity", "open",
     "Five of the thirty Tranche 3 potency retests rest on one page read",
     "Farmahem's 227-К/26 series — thirty cannabinoid certificates for the Tranche 3 sampling, "
     "issued 11.09.2026 — is in the record since the intake of 15.09.2026 "
     "(intake_227K_2026-09-15/): every one of them a retest, as the owner ruled on 12.09.2026, "
     "each in a campaign round of its own and sampled 19–21.08.2026 by the owner's ruling of "
     "15.09.2026. Twenty-five were written after the page read and the checkpoint "
     "transcription of the same day (master_coa_table.tsv, commit 7393bc4) agreed on the "
     "batch, the P lot, the date and every result. Five have no second read on file: "
     "227-1-К/26 (BSS1024_01/2, P050142), 227-4-К/26 (WED102501, P060102), 227-8-К/26 "
     "(SCR012601, P060342), 227-16-К/26 (GRC102501/1, P060142) and 227-29-К/26 (BSS1024_01/1, "
     "P050122). The first four batches had no register block and were given one (No. 90–93), "
     "with the P lot the certificate prints — the same P lot the Head of QC's batch list "
     "gives them; the fifth went into the register's BSS1024_01 block, whose P lot P050122 "
     "the certificate prints.",
     "The five are written on the page read alone and say so in the tracker instance's "
     "source. The identity question the desk had raised — whether a 227-К certificate could be "
     "a batch's first potency determination — is settled by the ruling that the series is a "
     "retest series (testing_series.rounds), so the four batches' release potency is simply not "
     "on file, which the CoQ Register already flags per lot.",
     "A second read of the five pages (or the owner's confirmation of the transcribed values: "
     "26.69 / <LOQ / <LOQ; 25.15 / <LOQ / <LOQ; 22.40 / <LOQ / <LOQ; 7.50 / <LOQ / <LOQ; "
     "26.10 / <LOQ / 0.20 for THC / CBD / CBN), and confirmation that BSS1024_01/1 on "
     "227-29-К/26 is the register's BSS1024_01 (P050122).",
     "intake_227K_2026-09-15/ (reads_227K.json, checkpoint_master_coa_table.json, "
     "apply_227K.py); PP_Batch_Release_QC_Register_SUBLOT_2026-09-01.xlsx after apply_227K.py; "
     "tracker/batch_dates.csv"),

    ("OI-33", "Batch identity", "open",
     "Two batches on the Tranche 2 mycotoxin certificates are on no list the desk holds",
     "Farmahem 220-31-М/26 (Fat Bastard, printed FB042601) and 220-32-М/26 (Cash Cow, printed "
     "CC042601), issued 11.09.2026, name a cultivation batch and no P-number. Neither batch is "
     "in the release register, on the Head of QC's batch list (tracker/batch_dates.csv) or on "
     "the owner's tracker — the two certificates are the desk's only record that the batches "
     "exist. A third certificate of the same delivery, 220-30-М/26 (Jelly Donutz, printed "
     "JD042601), prints no P-number either, but the batch list carries JD042601 as P060492 "
     "(harvest 21.07.2026, packaged 13.08.2026, four days before the laboratory received the "
     "sample), so its block and its tracker lot took that P-number from the list.",
     "The intake of 14.09.2026 opens a release-register block for each (No. 88 and 89) with "
     "the cultivation code, no P-number and the strain as printed, and a tracker lot of the "
     "same name. With no packaging date there is no day to date an internal CoA on and no "
     "place in the issuance series; the one result each carries is ND.",
     "The P-number, harvest and packaging dates of FB042601 and CC042601 for the batch list — "
     "or the ruling that they are R&D lots outside the release series, as GG1024 and CJ1024 "
     "are listed. And confirmation that the JD042601 on 220-30-М/26 is the batch list's "
     "JD042601 (P060492).",
     "intake_220M_2026-09-14/ (reads_claude.json n=30, 31, 32; placement.json); "
     "tracker/batch_dates.csv; PP_Batch_Release_QC_Register_SUBLOT_2026-09-01.xlsx after "
     "apply_220M.py"),

    ("OI-34", "Register scope", "ruled",
     "The IJZ-MB campaign microbiology was on the tracker and not in the release register",
     "The thirty IJZ-MB certificates of the campaign sampling of 25/26.08.2026 (issued 31.08 "
     "and 01.09.2026) are testing instances on the tracker since 04.09.2026 and are not rows "
     "of the release register, which is the one source the certificates of quality are "
     "compiled from. Since 15.09.2026 a reissue prints, for every determination it did not "
     "retest, the initial certificate's result — so for a lot whose microbiology WAS retested "
     "in that campaign the reissue would print the release microbiology while a newer result "
     "sits on the tracker. No Tranche 1 lot is affected (none was in that delivery). Since v30 "
     "(15.09.2026) the thirty Tranche 2 reissues ARE numbered, planned 18.09.2026, so a "
     "Tranche 2 lot in that delivery would print its release microbiology; the Tranche 3 "
     "reissues still wait for their mycotoxin certificates.",
     "CLOSED 16.09.2026 by intake_IJZMB_2026-09-16. The sweep of that day measured the harm "
     "the item had predicted: 24 certificates of quality printed microbiology a newer "
     "certificate for the same lot contradicted, twelve of them reissues, and not by a "
     "little — P050012 printed TAMC 2.1 × 10⁴ where the campaign certificate reads < 10. "
     "29 of the 30 certificates are now rows of the release register, through the same "
     "two-read gate the 220-М, 227-К and 220-К intakes used, with four value disagreements "
     "settled by a third read of the page (OI-36's defect class, four more instances). One "
     "is held back: 548/1079/26, whose lot is in doubt — OI-37.",
     "Nothing further, unless the owner rules on OI-37 (the held certificate) or on OI-13 "
     "(the expanded panel this same delivery reports).",
     "tracker/new_instances.json (the 30 IJZ-MB instances); "
     "tracker/split_manifest_IJZ-MB_2026-09-01.csv; build_coq_schedule.py ST_CARRIED"),

    ("OI-37", "Batch identity", "open",
     "One campaign microbiology certificate names a strain that is not its filed lot's",
     "548/1079/26 of 31.08.2026 is filed under P050192 — BSS052501, Blue Sunset Sherbet — "
     "because its typed serial reads PO50192, which canonicalises to P050192. But the page "
     "prints the sample as \"Сув цвет од канабис сорта Sleepy Joe\" and carries a "
     "HANDWRITTEN P060192 beneath the typed serial; P060192 is SJ112501, whose strain the "
     "release register gives as Sleepy Joy. The printed strain and the handwriting agree "
     "with each other and disagree with the typed serial. Read on the page of 16.09.2026. "
     "P060192 has no campaign microbiology certificate of its own on file; P050192 would "
     "have this one. Three other campaign certificates print a strain the register spells "
     "differently (Cap Junky against the register's Cup Junky, on 556/1087/26, 558/1089/26 "
     "and 565/1096/26) — that is a spelling, not a different strain, and is not this.",
     "The certificate is NOT written into the release register: a microbiology result on the "
     "wrong lot's certificate of quality is worse than a missing one. The other 29 of the "
     "delivery are written. P050192's certificates therefore still print its release "
     "microbiology, and its reissue will say so.",
     "Which lot 548/1079/26 belongs to: P050192, as the typed serial reads, or P060192, as "
     "the printed strain and the handwritten correction say?",
     "the scan 310826_548-1079-26_IJZ-MB_BSS052501-P050192.pdf in eCoA_DATABASE; "
     "tracker/split_manifest_IJZ-MB_2026-09-01.csv; intake_IJZMB_2026-09-16/reads_IJZMB.json"),

    ("OI-38", "Certificate content", "open",
     "Fourteen reissues carry the initial result while a later one for the same lot is on file",
     "Since 16.09.2026 the IJZ-MB campaign certificates of 25/26.08.2026 are rows of the "
     "release register (intake_IJZMB_2026-09-16), so the desk now holds, for 29 lots, a "
     "microbiology result LATER than the release one. A reissue rests on its Farmahem "
     "campaign (220- or 227-), whose scope is the assay and the mycotoxins; microbiology is "
     "outside that scope, so the reissue carries the initial certificate's result — the "
     "owner's ruling of 15.09.2026, correctly applied. The consequence is that twelve "
     "reissues will print a microbiology result that a newer certificate for the same lot "
     "contradicts, and not narrowly: CoQ-PP_26-144 (P050012) carries TAMC 2.1 × 10⁴ where "
     "561/1092/26 of 01.09.2026 reads < 10, and CoQ-PP_26-153 (P050132) carries TYMC "
     "3.3 × 10⁴ where 560/1091/26 reads < 10. The 26 rows are listed in "
     "intake_IJZMB_2026-09-16/carried_microbiology_2026-09-16.csv. The twelve RELEASE "
     "certificates that print the same release values are not in question: a release "
     "certificate states the release testing, and a later retest does not belong on it. "
     "The sweep of 16.09.2026 (result_supersession.py) then asked the same question of "
     "all seventeen determinations the register carries and found the shape is not "
     "confined to microbiology: 31 rows on FOURTEEN reissues, 29 of them the twelve "
     "microbiology reissues above and TWO of them loss on drying — CoQ-PP_26-093 "
     "(P050022) carries 7.21 % from ППК25139 of 22.05.2025 where ППК25174 of 10.07.2025 "
     "reads 6.51 %, and CoQ-PP_26-150 (J31112501) carries 8.4 % from 051-5-GS/26 of "
     "02.03.2026 where 100-1-GS/26 of 09.04.2026 reads 7.6 %. Neither superseding "
     "certificate is a stability timepoint. The sweep reports its coverage beside every "
     "zero: no lot on file carries a second HEAVY-METAL certificate (45 documents, 0 lots "
     "with two), so #11 could not be compared at all and its silence is a gap in the record "
     "rather than a clean result; aflatoxin B1, ochratoxin A and the pesticide panel were "
     "comparable on one lot each. Total aflatoxins over 30 lots, Total CBN over 12 and "
     "Salmonella and E. coli over 14 each are real zeros. One more consequence the "
     "owner should weigh with this: for THIRTEEN lots the campaign certificate is the "
     "ONLY microbiology on file. Until 16.09.2026 those lots' RELEASE certificates "
     "printed it, which put a document of 31.08 or 01.09.2026 on a certificate dated "
     "06.06, 07.07 or 13.07.2026 — impossible, and now fixed: a retest-only document "
     "can no longer stand behind a release result, so those thirteen release "
     "certificates print nothing for #9.1-#9.5. If the ruling here is CARRY THE "
     "INITIAL, their reissues print nothing either and the thirteen lots have no "
     "microbiology on any certificate of quality at all. If it is PRINT THE LATEST, "
     "the campaign result lands on the reissue, which is the only certificate dated "
     "after it. The thirteen are BSS1024_01/2, CC112501, FB012603, FB012603V, "
     "FB112501, GG112501, GRC102501/1, J31112501, OPM112501, SCR012601, SCR022601, "
     "SJ102501 and WED102501.",
     "Nothing on the certificates. The campaign results are in the register, on the tracker "
     "and in the compilation, so the newer result is visible everywhere the desk shows its "
     "working; what a controlled document prints is the owner's to rule, not a defect to "
     "repair silently. The IJZ-MB delivery is also a different sampling from the tranche it "
     "would be printed on — 25/26.08.2026 against 12–14.08 (Tranche 2) and 19–21.08 "
     "(Tranche 3) — so it is not simply 'the same campaign, later certificate'.",
     "When a reissue carries a determination forward because its campaign did not retest it, "
     "should it carry the INITIAL result or the LATEST result on file? For microbiology that "
     "is the IJZ-MB campaign of 25/26.08.2026, sampled on a different day from the Farmahem "
     "campaign the reissue rests on; for loss on drying it is an ordinary repeat test by the "
     "same laboratory. If the answer is the latest, does the reissue then cite two or three "
     "samplings on one certificate?",
     "intake_IJZMB_2026-09-16/carried_microbiology_2026-09-16.csv (26 rows, 12 reissues); "
     "tracker/RESULT_SUPERSESSION_2026-09-16.md section 1 (31 rows, 14 reissues); "
     "build_coq_schedule.py ST_CARRIED; the ruling of 15.09.2026"),

    ("OI-39", "Batch identity", "open",
     "Two register blocks carry two sublots each, and the certificate prints one of them",
     "The sweep of 16.09.2026 (result_supersession.py, check `parallel`) looked for a block "
     "holding two certificates of the SAME testing on the SAME day that report DIFFERENT "
     "results. Over 93 blocks there were two; one of them, JD112501, was ruled on 16.09.2026 "
     "to be one batch and two samples and is now OI-12, leaving one. **J31122501** "
     "(Jokerz 31, P060262) holds three such pairs: the microbiology of 07.04.2026, where "
     "231/0394/26 names its sample Рачно тримиран цвет (hand-trimmed flower) and reads TAMC "
     "850 while 230/0393/26 names Тримиран цвет (trimmed flower) and reads 1900; the "
     "Farmahem cannabinoids of 09.04.2026, 100-2-К/26 at 19.84 % against 100-3-К/26 at "
     "21.84 %; and the IJZ mycotoxins and metals of 23.04.2026, 1628/2026 against "
     "1625/2026. The documents themselves say these are two products of one cultivation "
     "batch, tested in parallel. The owner's batch list gives J31122501 exactly one P lot, "
     "P060262, so the register has no second number to file the second product under. The "
     "starred-sample ruling does NOT reach this block: these pages carry no asterisk, and "
     "they name two PRODUCTS on three separate dates, not two samples of one.",
     "Nothing invented. testing_series.rounds() treats two documents of one day as one "
     "testing period — right when they describe one sample — so both sit in the release "
     "round and the certificate of quality prints the first: 231/0394/26, 100-2-К/26 and "
     "1628/2026. The tracker shows BOTH — 100-2/1628/231 and 100-3/1625/230 as separate "
     "testing instances — so nothing is hidden anywhere the desk shows its working. What the "
     "certificate of quality does not say is WHICH product it certifies.",
     "Is J31122501 one lot or two? If two, what P lot number does the second carry, and does "
     "it need its own certificate of quality — which would make the three documents the "
     "certificate does not print (230/0393/26, 100-3-К/26, 1625/2026) the second product's "
     "record rather than unused results? If one, which of each pair is the lot's result?",
     "tracker/RESULT_SUPERSESSION_2026-09-16.md section 3; the register block J31122501 "
     "(10 certificates); tracker/batch_dates.csv row 64; OI-12 for the JD112501 half"),

    ("OI-40", "Document identity", "open",
     "Six lots hold two register rows for one testing, the results on the composite row",
     "The audit of 16.09.2026 flagged six document codes of the form "
     "\"PP CoA #027 / ППК25370\" — an in-house certificate number and a Center for Natural "
     "Products number in one cell. Reading the register shows why it matters: EVERY one of "
     "the six also exists as a bare ППК row on the same lot, with its own EARLIER date and "
     "NO results. P050282 row 123 \"PP CoA #027 / ППК25370\" of 21.01.2026 carries THC 8.02, "
     "CBD 0.04 and loss on drying 9.68; row 124 \"ППК25370\" of 28.11.2025 carries nothing. "
     "The same shape on P050292/ППК25378 and P050302/ППК25379 (bare rows 12.12.2025), "
     "P050312/ППК25380, P050322/ППК25381 and P060052/ППК26005. So for these six lots the "
     "results sit on the composite row and the row that names the external certificate "
     "alone is empty — and the certificate of quality therefore prints "
     "\"PP CoA #027 / ППК25370\" dated 21.01.2026 as its document.",
     "Nothing changed. document_codes.py canonicalises SPELLING only and leaves these "
     "composites exactly as the register writes them: deciding which of two rows is the "
     "certificate, and which date the certificate of quality should cite, is not a "
     "spelling. The six are listed here with their rows so the owner rules on the record.",
     "For these six lots, which row is the certificate the certificate of quality should "
     "cite — the Center for Natural Products certificate on its own date, or the in-house "
     "certificate of 21.01.2026 that carries the results? And should the two rows be one "
     "row, with the in-house number as a cross-reference?",
     "register rows 123/124, 127/128, 131/132, 135/136, 139/140, 163/165; "
     "tracker/HANDOVER_RESPONSE_2026-09-16.md §2.2"),

    ("OI-41", "Document content", "open",
     "Forty-eight certificates print no result for the three determinations done in-house — and what remains is documents, not routing",
     "Determinations #1 Identification A, #2 Identification B and #7 Foreign matter are "
     "performed in the Purely Plant laboratory on every batch. On **48** of the 172 "
     "certificates — 24 lots — all three print nothing: the row cites the lot's internal "
     "certificate and "
     "the laboratory, and the result reads \"—\" with the status \"to be performed — see "
     "route\". The other 90 print Conforms. The audit of 16.09.2026 established what "
     "separates them, and it is not the kind of evidence: 78 of the 90 print Conforms "
     "because the owner's 09.09.2026 pass wrote Conforms against a then-unissued internal "
     "certificate and the exporter copies that statement into the cell once the certificate "
     "is issued; the other 12 take a CNP Ph. Eur. certificate that covers identity. So the "
     "line between 90 and 82 is 09.09-PASS COVERAGE, not a record one group has and the "
     "other lacks. Of the 44 blank lots: 12 have an in-house QCCoA scan on Drive that no "
     "desk record holds (OI-43), 6 are ones the pass itself marks \"NOTHING ON FILE — no "
     "document anywhere\", 19 are outside every record the desk or the owner holds, and the "
     "rest are the predicted reissues of CNP-covered lots, blank by the routing.",
     "Printed as the desk holds it: the determination named, the internal certificate cited, "
     "the result blank and the route stated. Nothing is asserted that no record supports. "
     "Two things changed on 16.09.2026, and between them the item halved — from 82 certificates "
     "over 44 lots to 48 over 24. First, a REISSUE no longer prints the pass's release-round "
     "statement against its own campaign's certificate: 39 certificates were asserting a retest "
     "result that no round had recorded. Second, and in the other direction, a reissue now "
     "CARRIES the release round's row for #1, #2 and #7 — the release result, the RELEASE "
     "round's internal certificate of analysis, its code and its date of issue — because the "
     "ruling of 15.09.2026 says every determination the retest did not run takes the initial "
     "testing's result, and the desk had been honouring that for every determination except "
     "these three. The distinction is the whole of it: the reissue states what the release round "
     "found and names the document that found it, rather than asserting a round of its own. "
     "What is left is 24 lots for which no in-house record has been read on either round, which "
     "is a document question (OI-43), not a routing one.",
     "Three answers are wanted, and they are different questions. (a) For the 12 lots with a "
     "QCCoA scan on Drive: may the desk read those scans in and print what they state? "
     "(OI-43.) (b) For the 39 lots already printing Conforms from the pass: is the internal "
     "certificate alone sufficient authority for that word, given the cell's own status still "
     "says the testing is to be performed? (c) For the 6 lots the pass marks NOTHING ON FILE "
     "and the 19 outside every record: is the in-house result written anywhere the desk has "
     "not been given, or is the blank simply correct?",
     "44 lots, 82 certificates, 246 determination rows; build_coq_schedule.ST_ICOA; "
     "export_coq_artifact_data.py (the 09.09 pass fill); "
     "tracker/FLEET_FINDINGS_2026-09-16.md (audit B); tracker/HANDOVER_RESPONSE_2026-09-16.md §2.1"),

    ("OI-42", "Record integrity", "open",
     "Forty-four laboratory certificates are on Drive and in no record of the desk; 58 more are only in the 09.09 pass",
     "The audit of 16.09.2026 enumerated the owner's eCoA_DATABASE on Drive (490 scans: 449 "
     "laboratory, 41 in-house) and held it against every desk record — the ingested corpus, "
     "the release register and the 09.09 resolution pass. Forty-four laboratory scans are in "
     "NONE of them: 20 IJZ contaminant reports (mycotoxins, metals, pesticides — 329/2026 "
     "WED102501, 1057/2026 J31112501, 1061/2026 SJ112501, 1062/2026 OPM112501, 1065/2026 "
     "SJ102501, 3654–3658/2026 P160032, P160022, P160012, SCR022601, JD022601, 3661/2026 "
     "FB012603, 3663/2026 FB012603V, 3924/2026 FB032601, 3925/2026 GG032601, 4374/2026 "
     "JD032601, and the five of 29–30.04.2026 taken in the same day), 22 IJZ-MB microbiology "
     "reports (319/0586/25 GP0824_01; 75/0118/26 WED102501; 130–137/02xx/26 SJ112501, "
     "J31112501, SJ102501, OPM112501; the five of 28.04.2026 taken in the same day; 362/0692/26 "
     "SCR012601; 402–411/07xx/26 JD022601, SCR022601, FB012603V, FB012603, P160012, P160032, "
     "P160022; 433/0847/26 and 434/0848/26 FB032601; 477/0929/26 JD032601) and the two "
     "Farmahem certificates 031-3-К/26 and 031-3-ГС/26 of WED102501. A further 58 scans are "
     "cited in the 09.09 pass and never reached the register or the corpus — among them the "
     "whole Farmahem 031 campaign of February 2026 and 534/1065/26 and 535/1066/26 of the "
     "31.08.2026 IJZ-MB delivery, which fall outside the 536–565 range the IJZ-MB intake "
     "took. For every one of the 20 IJZ reports the lot's register block holds NO metals, "
     "mycotoxin or pesticide document at all, so the certificate of quality prints "
     "\"not tested — no certificate covers it\" for #10–#12 while the report sits on Drive, "
     "dated before the certificate — and the sweep's \"no lot carries a second heavy-metal "
     "certificate\" is a register gap, not a testing fact. The reverse direction is clean: "
     "every laboratory code the desk holds has a scan (0 of 403 missing).",
     "The eighteen of 21.04.2026 whose two reads existed were taken in on 16.09.2026 "
     "(intake_IJZ0426_2026-09-16). The remaining 44 + 58 have no read on the desk yet; each "
     "needs the two-read gate before it is written, and until then the certificates named "
     "above print \"not tested\" where a document exists. Nothing is written from a listing.",
     "Nothing to decide for the intake itself — it is the desk's next work. Three lots on "
     "the batch list need a word: JD032601 (P060472) has an IJZ-MB and an IJZ report on Drive "
     "and no release-register block and no CNP potency certificate anywhere — is it a "
     "production lot? SC062501 (P050242) and GOG062501 (P050232) have no document on Drive "
     "at all — were they ever tested?",
     "tracker/FLEET_FINDINGS_2026-09-16.md (audit A); the Drive tree 1SmOicCRa8KEqoB-YlCojdap161YMQ-Di "
     "and _IN-HOUSE_PP 1bBGgFavrUTOu7PC7VVRcj0P4onWOAquN, enumerated 16.09.2026"),

    ("OI-43", "Record integrity", "open",
     "Twenty-eight in-house certificates of analysis are on Drive with no desk entry — twelve of them for lots OI-41 names",
     "_IN-HOUSE_PP holds 41 in-house scans: 38 QCCoA 001 / 001v02 forms named "
     "<ddmmyy>_QCCoA 001[v02]_PP_<batch>-<P lot>.pdf and the three Reports of Analysis of "
     "23.04.2025. The desk's in-house entries number 16 and match 13 of the scans. The 28 "
     "without any desk entry are the QCCoA 001 of BG1024, BSS1024, CJ1024, MB0824_04, "
     "OMP1024_01, GP0824_02 (twice), GG1024_02, GP0824_03, HPA1024_01, OPM1024_02, GG1024_01, "
     "P050102, HPA052501, CJ052501-01, BSS1024_01-1, GP062501 (v02) and the eleven QCCoA 001v02 "
     "of 21.01.2026 (GP082501-1/-2, GP072501-1/-2, CLE072501, PM072501, P050212, CJ052501-02, "
     "OPM052501, MB0824_05, OPM1024_03), plus the three Reports of Analysis. Twelve of the 44 "
     "lots whose certificates print nothing for #1, #2 and #7 (OI-41) have one of these scans "
     "— the in-house record OI-41 asks for exists on Drive for them.",
     "Nothing read, nothing written: an in-house scan reaches the desk through the same "
     "two-read gate as a laboratory certificate, and the desk holds no read of any of the 28.",
     "May the desk take the QCCoA 001 scans in as the record of the in-house results, so "
     "that the certificates of those twelve lots print what the form states for #1, #2 and #7 "
     "and cite the internal certificate that carries it? If yes, OI-41 shrinks from 44 lots "
     "to 32.",
     "tracker/FLEET_FINDINGS_2026-09-16.md (audits A and B); the 41 scans in _IN-HOUSE_PP"),

    ("OI-44", "Specification", "open",
     "The grade numerals were assigned against the desk's own rule, and 69 certificates cite a code that used to mean something else",
     "potency_grades.number() states that a numeral is \"assigned once for a strain and a "
     "nominal and never renumbered\". Its first numbering seeded itself from nothing and "
     "sorted by nominal, so it ignored the numerals the ISSUED QCSP 001 v.01 documents "
     "already carry. The codes therefore changed meaning under the same name: "
     "QCSP_001_GP-IV_v.01 named GP_THC20 (18.00–22.00 %) on the issued document and names "
     "GP_THC16 (14.40–17.59 %) on the certificate; QCSP_001_CJ-III_v.01 was CJ_THC24 "
     "(23.00–25.00 %) and is CJ_THC20 (18.40–21.59 %). Over the export 69 certificates on 20 "
     "codes carry a product-code change under an unchanged code, 54 on 17 codes change the "
     "window only, and 32 on 19 codes are new codes.",
     "Nothing hidden and nothing renumbered a second time. Every affected certificate's "
     "record prints spec_status — \"for review — replaces the issued QCSP_001_GP-IV_v.01 (was "
     "GP_THC20 : CBD1, 18.00 – 22.00 %); now GP_THC16 : CBD1 14.40 – 17.59 %\" — and 88 "
     "certificates carry the conflict sentence beside it. The ladder is used exactly as the "
     "potency specification of 15.09.2026 prints it, which is the ruling of that date.",
     "Two rulings meet here and only one can hold. Either the potency specification of "
     "15.09.2026 is used exactly as it prints (15.09.2026) and the issued v.01 documents are "
     "superseded numeral and all — in which case the 69 codes are correct and the issued "
     "documents are reissued under their new meaning — or a numeral once issued is never "
     "reused, in which case the ladder must be renumbered around the issued set and the new "
     "grades take fresh numerals. Which?",
     "potency_grades.py number(); potency_grades_2026-09-15.csv; "
     "product_specifications_QCSP001.json; tracker/FLEET_FINDINGS_2026-09-16.md (audit C)"),

    ("OI-45", "Register cell", "open",
     "One in-house microbiology cell states two bounds that cannot both be true, and two certificates print it",
     "The release register carries bile-tolerant gram-negative bacteria for OPM1024 as "
     "\u201c<10\u00b2>10\u00b3\u201d, from Purely Plant's own certificate of analysis of "
     "23.04.2025 \u2014 the block with no certificate or report number printed. Every other "
     "block in the register writes the pair as an upper bound and then a lower one "
     "(\u201c<10\u00b2 and >10\u201d, \u201c<10\u00b3 and >10\u00b2\u201d), so the two "
     "figures here are the wrong way round: nothing is both below 100 and above 1000. It "
     "reaches CoQ-PP_26-006 and CoQ-PP_26-101, both OPM1024, where assertion A11 of the "
     "Claude Design package refuses the cell as off-vocabulary.",
     "Nothing was corrected in place. The desk does not rewrite a figure on the company's own "
     "certificate of analysis, and the certificate prints the cell as the register states it "
     "rather than a reading the desk prefers. The two documents carry the assertion finding "
     "so the pair travels with them.",
     "Is the intended reading \u201c< 10\u00b3 and > 10\u00b2\u201d \u2014 the same pair as "
     "every other block, with the bounds transposed in transcription? One word corrects the "
     "register cell and both certificates with it.",
     "coq_artifact_data.json reg[OPM1024]; design_handoff/out/_build_report.txt; "
     "design_handoff/toolchain/coq_check.js A11"),

    ("OI-46", "Result read", "ruled",
     "Ten microbiology cells were read once and held; the Head of QC's own pass had all five "
     "values for every one of them",
     "The intake of 16.09.2026 read twenty-three Institute of Public Health certificates off "
     "the scans and held ten cells whose figures the page did not render \u2014 an exponent or a "
     "bound lost. That left certificates printing two or three of the five microbiological "
     "purity parameters and leaving the rest blank. The Head of QC objected the same day: a "
     "report determines all five on one sample, so a batch cannot have one and not the "
     "others. He was right, and the values were already on the desk \u2014 "
     "cell_resolution_2026-09-09.tsv, his own reading pass, carries all five for every lot, "
     "with the document, its date and its laboratory.",
     "apply_resolution_pass.py makes the pass the source and the scan the cross-check rather "
     "than the other way round: 66 certificates written into the release register and 39 "
     "columns added to certificates already there, taking #9 (five values), #11 (four \u2014 the "
     "order confirmed against the register's own long-standing 752/2025 row) and #12 (one "
     "determination over a uniform panel). #10 is not taken, because its rows carry one, "
     "three or five values and a mapping that is not certain is not a mapping. Where the two "
     "readings can be compared they agree, including on the figure this desk had held as "
     "contested: the pass reads 73/0116/26 TYMC as 3,9 \u00d7 10\u2074 too. **No certificate prints a "
     "partial panel now**, and verify_panels.py is the standing check that none may.",
     "Nothing. Two rows of the pass are still held and named in the script's output: "
     "305-0549-26 carries ten values where five are wanted, and 85/2026 five where four are.",
     "cell_resolution_2026-09-09.tsv; apply_resolution_pass.py; verify_panels.py; "
     "intake_ijz_2026-09-16/reads_microbiology.json"),

    ("OI-47", "Ingestion", "open",
     "Twenty-three certificates in the owner's database folder were never ingested, and every desk file recorded their absence as a coverage gap",
     "master_coa_table.tsv prints \u201c[COVERAGE GAP] \u2014 No record found in RAG for \u2026 "
     "Heavy metals (Cd/Pb/Hg/As), Pesticides\u201d against P060152, P060332, P060352 and others, "
     "and PP_eCoA_Master_Database.xlsx repeats it as a QC exception. For nineteen of those lots "
     "the certificate exists, in the owner's own folder, and has since 09.09.2026. The gap was "
     "in the ingestion, not in the record: every downstream file faithfully reported an absence "
     "that was not real.",
     "The twenty-three documents are now in the release register, and the certificates print "
     "from them. The ingestion itself is untouched \u2014 the same folder may hold more that the "
     "corpus lacks, and nothing in the pipeline would say so.",
     "Should the desk re-run the CoA_DATABASE_2026 ingestion against the whole folder and "
     "reconcile it against the register, so that a coverage gap means the document does not "
     "exist rather than that it was not fetched?",
     "ingestion/coa_track/letta-imb-coas/ingest_coa_database_2026.py; "
     "exports/master_coa_table.tsv; tracker/DRIVE_DATABASE_INTAKE_2026-09-16.md"),

    ("OI-48", "Document", "open",
     "One Tranche 3 mycotoxin certificate has not been read by anyone, and one lot's #10 waits on it",
     "The thirty Farmahem reports 227-1-\u041c/26 \u2026 227-30-\u041c/26 of 16.09.2026 were read twice "
     "and independently \u2014 by this desk and by the Head of QC \u2014 and the two readers failed on "
     "DIFFERENT certificates, so the blank page is a property of the reader and not of the "
     "scan. This desk could not extract 227-13, 227-18, 227-20 and 227-30 in three attempts "
     "each; the Head of QC could not extract 227-2, 227-7, 227-16, 227-18, 227-23 and "
     "227-27, five of which this desk read in full. Between the two reads 29 of the 30 are "
     "read and no certificate is read differently by the two. **227-18-\u041c/26 (GP062501, "
     "P050202) is the one nobody has read.**",
     "The 29 are in the release register and their certificates print them. P050202's #10.1 "
     "and #10.3 stay empty \u2014 the desk does not print a result from a page nobody has seen, "
     "and it will not take the value from the twenty-nine siblings that were all ND, because "
     "a batch's own mycotoxin result is not a property of the campaign it was submitted in.",
     "Open 227-18-\u041c/26 by hand and tell the desk the five analytes. It is the only "
     "certificate of the thirty that needs it \u2014 the six the Head of QC flagged on "
     "16.09.2026 were flagged from one reader's failures, and five of those six are read.",
     "intake_227M_2026-09-16/reads.json; tracker/T3_MYCOTOXIN_INTAKE_2026-09-16.md; "
     "apply_227M_intake.py"),

    ("OI-35", "Tracker scope", "open",
     "The tracker does not carry the documents of the 09.09 pass that eleven certificates print from",
     "The truth check of 15.09.2026 (tracker/truth_check_2026-09-15.py) compared every row of "
     "every certificate with the tracker's cells for the lot. Twenty rows on eleven certificates "
     "cite a document the tracker holds nowhere: the 17 documents the owner's 09.09.2026 pass "
     "over eCoA_DATABASE recorded (cell_resolution_2026-09-09.tsv) and the two-read pipeline "
     "never ingested — ППК25008 and 748/2025 (GG1024: the loss on drying — 7.8 % since the "
     "Head of QC's correction of 17.09.2026, 76.07 % before it — and the "
     "pesticides), 031-2/4/5-К/26 and 031-2/4/5-LoD/26 (P060112, P060122, P060132: the Farmahem "
     "cannabinoid and loss-on-drying certificates of 10.02.2026), 326/327/330/2026, "
     "1056/1058/1059/1060/2026 and 3659/3660/3662/2026 (the IJZ pesticide certificates of "
     "P060112, P060122, P060132, P060152, P060172, P060182, P060232, P060402, P060412, "
     "P060422). Each rests on one page read. The tracker's document pool is the desk's index "
     "plus the intake instances, so its cell for GG1024 #8 reads '— MISSING —' while the "
     "certificate prints 7.8 % from ППК25008, and J31122501 #8 cites the cannabinoid "
     "certificates where the certificate cites the loss-on-drying certificate 100-2-ГС/26.",
     "Recorded, not built: the 17 documents need the two-read intake the 220-М, 227-К and "
     "220-К certificates had before the tracker credits them, and the certificate rows that "
     "rest on them are marked on the references table as single-read.",
     "Whether the desk should read the 17 documents of the 09.09 pass through the two-read "
     "gate now, so that the tracker and the certificates cite one record — or whether the "
     "certificates that print from a single read (GG1024 above all) wait for it.",
     "tracker/TRUTH_CHECK_2026-09-15.md (T5); cell_resolution_2026-09-09.tsv; "
     "coq_artifact_data.json rows citing those codes"),

    ("OI-36", "Record integrity", "open",
     "Four two-read corpus records passed the gate with their reads disagreeing on a comparator",
     "The truth check of 15.09.2026 found four IJZ-MB microbiology results where the owner's v8 "
     "tracker and one of the two corpus reads carried a value the page contradicts, and the "
     "corpus record was marked as agreed: 5/0008/26 TAMC (read A '< 1 x 10²', read B '1 x 10²', "
     "record kept A; the page prints 1 x 10² CFU/g), 9/0012/26 bile-tolerant (A '10', B '< 10', "
     "record kept B; the page prints < 10), 471/0862/25 TYMC (A '10', B '< 10', record kept B; "
     "the page prints < 10), 304/0548/26 bile-tolerant (A '< 10²', B '< 10² и >10', record kept "
     "B; the page prints < 10² и > 10). In every case the release register was right and v8 "
     "was wrong; the certificates print the register's value. The same check found the 09.09 "
     "pass table (cell_resolution_2026-09-09.tsv) holding Total THC, CBD and CBN values for "
     "197-13-К/26, 197-7-К/26 and 197-6-К/26 that neither the register nor the two reads "
     "carry (19.68 / 24.09 / 23.29 % against 17.31 / 18.86 / 17.67 %); nothing prints them.",
     "The four tracker cells are corrected from a third read of each page "
     "(tracker/value_corrections_2026-09-15.json, applied in values_of). The corpus records "
     "and the pass table are the ingestion's and are left as they are, listed here.",
     "Whether the ingestion's reconciliation should treat a comparator ('<', '>') as part of "
     "the result when it compares two reads, and re-gate the four records; and whether the "
     "three pass-table cells should be corrected or the rows retired.",
     "tracker/TRUTH_CHECK_2026-09-15.md (T3, T4, T5); ingestion/ecoa_runner/records_corpus.json; "
     "the four page reads of 15.09.2026"),

    ("OI-13", "Panel scope", "open",
     "The expanded microbiology panel HAS been run and no certificate says so",
     "Corrected 16.09.2026. This item said until today that the expanded microbiology option "
     "(P. aeruginosa, S. aureus) \"has never been run\" and that \"neither is claimed on any "
     "certificate\". That was false, and it had been shipped in OPEN_ITEMS.md and in the "
     "workbook since 11.09.2026. Thirty-one certificates on file report the panel — every "
     "one of the thirty IJZ-MB campaign certificates of 31.08/01.09.2026 and 1221/2172/25 of "
     "01.12.2025 — and all report both organisms ABSENT. What remains true of the other "
     "panel: the pesticide option offers Ph. Eur. 2.8.13 and a CUMCS equivalency, and no lot "
     "was tested to equivalency. Determinations #9.6 and #9.7 print nothing on all 172 "
     "certificates of quality, marked \"upon request — not required for release\", while a "
     "result exists for 31 of them.",
     "The panel results are kept in intake_IJZMB_2026-09-16/reads_IJZMB.json. They are NOT "
     "written into the owner's release register, which has no column for either organism, "
     "and the certificates are not changed: what a controlled document claims is the owner's "
     "to decide, not a defect to repair silently.",
     "Should a certificate of quality print #9.6 and #9.7 where the laboratory reported them "
     "(31 lots, both absent) — and should the register gain a column for each so the result "
     "lives beside the other five? And, unchanged: should the certificates record that the "
     "pesticide equivalency option exists and was not exercised, or stay silent on it?",
     "Ph. Eur. 2.8.13; Ph. Eur. 2.6.13 expanded panel"),

    ("OI-14", "Document content", "open",
     "Two fields still print a specimen or a placeholder",
     "The two approvers' names are the master template's specimen. The potency acceptance "
     "range is a bracketed placeholder in both places it prints.",
     "Both print bracketed in red and unticked, so no draft can be mistaken for issued. (A "
     "third field once listed here — Identification C's document sourcing — is built: "
     "_pick(4, False) or _pick(3, False) resolves it on every one of the 22 drafts, 0 "
     "falling back to the unresolved message. Closed 11.09.2026, folded out of this item "
     "rather than left to read as still open.)",
     "The approvers' names and titles; the potency range per grade.",
     "_CoQ_MASTER_Template.html; 22 drafts"),

    ("OI-15", "Method status", "open",
     "The pesticide acceptance criterion is stated as ≤ LOQ, which is not the Ph. Eur. test",
     "Ph. Eur. 2.8.13 sets a maximum per compound, not a limit of quantitation. OPM1024_02 "
     "shows why it matters: delta-HCH is reported at < 0.01 mg/kg against a maximum of 0.3, "
     "which conforms to the monograph and is not ≤ LOQ, and the column has no way to say so. "
     "The owner confirmed on 11.09.2026 that the reading itself is correct.",
     "The result is printed as the laboratory reports it.",
     "Restate the criterion as the Ph. Eur. maximum table, and say how a conforming "
     "detection should print beside 28 not-detected residues.",
     "IJZ 2994/2025, 19.06.2025, OPM 1024_02 (P050062); verdict on the page: ОДГОВАРА"),

    ("OI-16", "Result", "open",
     "One lot's foreign matter is reported by the laboratory as not conforming",
     "FB032601 prints 0.08 % (Не одговара) on ППК26127 of 21.07.2026. The figure passes the "
     "gravimetric ≤ 2.0 % limb, so CNP is failing it on another limb of Ph. Eur. 2.8.2 "
     "(leaf and stem size). The desk used to fold Не одговара to absent — a pass — because "
     "the phrase contains одговара; that is fixed and the lot now reads as out of "
     "specification.",
     "Flagged OOS. An out-of-specification result needs an investigation record.",
     "Confirm the non-conformity with CNP and open the deviation, or obtain a corrected "
     "certificate.",
     "FB032601; ППК26127, 21.07.2026 [CNP]"),

    ("OI-17", "Result", "open",
     "Thirteen lots exceed a criterion — every one of them on #9.2, and on nothing else in "
     "the whole set",
     "Judged as the desk judges a counted limit, \u2264 10\u207f against 2 \u00d7 10\u207f (Ph. Eur. 5.1.4): "
     "**eight lots are out of specification** \u2014 P050092 4.2 \u00d7 10\u2074, P050212 4.9 \u00d7 10\u2074, "
     "P060132 3.9 \u00d7 10\u2074, P050152 3.6 \u00d7 10\u2074, P050132 3.3 \u00d7 10\u2074, P050182 2.6 \u00d7 10\u2074, "
     "P060332 and P060352 2.2 \u00d7 10\u2074 \u2014 and **five are in the undetermined band**: P050012 "
     "1.9 \u00d7 10\u2074, P060382 1.8 \u00d7 10\u2074, P050162 1.7 \u00d7 10\u2074, P050052 1.5 \u00d7 10\u2074, P050072 "
     "1.2 \u00d7 10\u2074. Thirteen lots, and **every one is #9.2 (TYMC) against the \u2264 10\u2074 CFU/g all "
     "172 certificates print**. Across 3,956 determination cells no other parameter exceeds "
     "its criterion anywhere \u2014 not TAMC against \u2264 10\u2075, not the bile-tolerant count, not a "
     "metal, not a mycotoxin, not a pesticide. Every laboratory that issued the thirteen "
     "declared the sample conforms. The Head of QC observed on 16.09.2026 that the printed "
     "specification may be 10\u2075; at 10\u2075 the maximum acceptable count is 2 \u00d7 10\u2075 and all "
     "thirteen clear with a fourfold margin. Four of the register cells have been saying "
     "\u201cUNDETERMINED \u2014 pending the QCSP 001 reading\u201d for some time.",
     "Printed red bold and amber bold respectively, and named in each lot's STATUS. "
     "mark_microbial_band.py states the rule over every counted row and defers to the "
     "register's own word where it already calls a cell out of specification or "
     "undetermined. Nothing about the criterion was changed: the certificate prints what "
     "QCSP 001 says.",
     "Is the #9.2 (TYMC) criterion in QCSP 001 10\u2074 or 10\u2075 CFU/g? A specification that "
     "thirteen batches fail on one parameter and nothing else, against thirteen laboratory "
     "declarations of conformity, is more likely a criterion transcribed one power out than "
     "thirteen excursions \u2014 but that is the Head of QC's to say, not the desk's. If 10\u2074 "
     "stands, each of the eight needs an investigation record and the five need a "
     "disposition.",
     "Ph. Eur. 5.1.4; 13 lots, all #9.2; QCSP 001; mark_microbial_band.py"),

    ("OI-18", "Document content", "ruled",
     "The same assertion printed bilingually on some certificates and in English on others",
     "Identification A and foreign matter print Conforms on 51 determinations and "
     "Conforms | Соодветствува on 12 — the certificate's own English | Macedonian pattern, "
     "applied to some cells and not others.",
     "Owner's ruling of 11.09.2026: every conformity result prints bilingually, in the "
     "convention the rest of the certificate uses. The master already set that convention "
     "for this exact cell and nothing had used it — .r-conform .mk stacks the Macedonian "
     "beneath the English in a smaller muted green — so the halves are stacked, not joined "
     "by the .bisep pipe the master keeps for inline pairs. 375 results paired. A measured "
     "number is not translated.",
     "Nothing further.",
     "375 determinations; .r-conform .mk in _CoQ_MASTER_Template.html"),

    ("OI-19", "Result", "open",
     "One ochratoxin result prints as a working note rather than a value",
     "2.06 — DETECTED, >LOQ on Ochratoxin A. The limit is 20 µg/kg so it conforms, but the "
     "cell carries the reader's note instead of the figure and its qualifier.",
     "Printed as the desk holds it.",
     "How should a conforming detection print — the figure alone, or the figure with a "
     "detected qualifier? The same question as OI-15 for pesticides.",
     "#10.3 Ochratoxin A, 1 determination"),

    ("OI-24", "Document content", "open",
     "The Identification C result no longer states the method on the face of the document",
     "The result read \"Conforms — cannabinoids identified and quantified by HPLC\", which "
     "restated the METHOD column two cells to its left on the same row. Measured with the "
     "embedded fonts, that one cell stood 85 px tall against 18 px for a normal row, and "
     "div.page clips at A4: three certificates were losing their second approver's signature "
     "date off the bottom of the sheet.",
     "Shortened to \"Conforms | Одговара\" like every other identity row. The basis for "
     "Identification C stays in the Section 03 citation, where a basis belongs.",
     "Do you want the method restated in the result cell? It would need a wider results "
     "column, which is a change to the master.",
     "#3 Identification C; 35 determinations"),

    ("OI-27", "Document identity", "ruled",
     "The register sheet carried 60 of the series' 95 internal certificates",
     "The numbering agreed wherever both carried a row, but the ROW SETS did not. The sheet "
     "held 60 numbered rows against the series' 95: it showed no retest certificate at all "
     "where the series issues 26 — its retest rows are one per lot per sampling campaign, so "
     "a lot with four retest rounds had ONE row standing for four certificates — and it "
     "withheld nine release certificates under \"where a CNP certificate reports all three, "
     "no iCoA is needed\".",
     "Built, 11.09.2026. The sheet now RENDERS icoa_register.py: one row per testing round, "
     "all 95 codes printed and numbered, retests 2-5 addressable for the first time (keys "
     "|R2 .. |R5, while retest 1 keeps the bare |R every existing lookup cites). The nine "
     "withheld release certificates are registered — the 05.09.2026 note was superseded by "
     "the ruling below, and which document the certificate of QUALITY cites for those three "
     "determinations is a separate question and is unchanged. A lot the series does not "
     "carry keeps its planning row, unnumbered and saying why. verify_workbook.py now checks "
     "COVERAGE, not just agreement: every certificate in the series appears on the sheet "
     "exactly once. Run against the previous workbook it reports the 35 that were missing.",
     "Nothing — this was already ruled and the desk had recorded it as a question. "
     "10.09.2026: \"the register encompasses every internal certificate that exists or ever "
     "will, not only what the drafted lots need ... one per testing round\", and "
     "\"identification A, identification B and foreign matter, ALWAYS\".",
     "95 of 95 series codes on the sheet (was 60); 166 rows; verify_workbook.py 0 findings"),

    ("OI-26", "Document identity", "ruled",
     "The internal-CoA number was defined twice and the two disagreed on every comparable row",
     "The certificates print the code from icoa_register.py, which sorts by the order of "
     "issuing exactly as ruled and numbers iCoA-PP_26-001 .. -099, leaving 7 lots unnumbered "
     "for want of a packaging date. The workbook's iCoA Register sheet numbers its own rows "
     "by position, COUNT(A$1:A{n})+1, over a different row order and a different rule — it "
     "also withholds a number from every retest and every held result, numbering 69. Of the "
     "49 rows that can be compared, 0 agree. J31122501 / P060262 is the owner's example: the "
     "sheet makes it iCoA-PP_26-001 because it is physically the first row; the certificate "
     "cites iCoA-PP_26-066, its true place in the issue order. The two also identify lots "
     "differently — the module's rows often carry no P number, so 20 sheet rows cannot even "
     "be matched to it.",
     "Closed against the ruling of 10.09.2026, which already answered it: \"the register "
     "encompasses every internal certificate that exists or ever will … one per testing "
     "round, which is exactly the number of certificates of quality.\" A retest takes a "
     "number and a held lot takes a number; only a certificate with no testing date takes "
     "none, because a code in an issue-ordered series says the certificate was issued. The "
     "workbook now takes its codes from icoa_register.py as literals — one definition — and "
     "mints none of its own; a row the series does not carry is left unnumbered and says so. "
     "Two defects were found on the way: the register carried 26 rows with no P number that "
     "Batch Dates could supply, and it registered four lots TWICE for the same round, once "
     "under the cultivation batch and once under the bare P number (J31102501/P060152, "
     "JD112501/P060212, OPM122501/P060242, GG012603/P060402) — same P number, same testing "
     "date, same issue date, so two internal certificates for one testing, which the ruling "
     "forbids. 106 rows -> 102. verify_workbook.py compares the two registers on every run "
     "and the workbook verifies with 0 findings.",
     "Nothing. Recorded because the numbers moved: de-duplicating shifted every code from "
     "045 onward, so any code quoted before 11.09.2026 is stale.",
     "icoa_register.py and the iCoA Register sheet; 49 of 49 differed, now 0"),

    ("OI-25", "Document rendering", "ruled",
     "The A4 page was never measured with the fonts it prints in",
     "\"One A4 page\" was checked by reading scrollHeight on the page itself — but div.page "
     "clips with overflow:hidden, so that reading returns the clipped height and always "
     "answers zero. Measured properly, inside an A4 frame with the subset fonts the PDF "
     "embeds, 5 of the 22 certificates stood past the bottom of the sheet, the worst by "
     "72 px, and P060152 was printing only one of its two signature dates.",
     "The builder measures it on every run and names any document that overflows. Four "
     "compiled-copy fit rules close the gap: the Identification C result shortened (OI-24), "
     "short paired results held on one line rather than wrapped, and the leading of Section "
     "03 and of the parameter column tightened. 21 of 22 now fit outright; the 22nd has a "
     "few px of trailing box space past the edge with no element beyond it.",
     "Nothing. Recorded because the claim had been made and was not true, and because the "
     "page has very little slack: the next thing that adds a line will need this check.",
     "build_coq_drafts.py page-height report; measured 5 of 22 -> 0 of 22 losing content"),

    ("OI-23", "Document content", "open",
     "The Macedonian for an absent organism was chosen from the laboratories' own usage",
     "The owner ruled the conformity result prints \"Conforms | Одговара\". The absence "
     "columns (Salmonella, E. coli) assert absence rather than conformity and were not "
     "covered by that word. The source certificates spell it four ways — отсутна (7), "
     "отсуство (2), отсуства (2) — and most often write Одговара there instead (84).",
     "The certificate prints \"Absent | Отсутна\" on 92 determinations: CNP's own most-used "
     "form (\"отсутна/25 g\"), capitalised, rather than a term translated afresh for a "
     "controlled document.",
     "Confirm Отсутна, or give the term the two absence rows should carry.",
     "#9.4 Salmonella, #9.5 E. coli; 92 determinations"),

    ("OI-22", "Result reading", "ruled",
     "An analyte the laboratory never tested was printing a line on the certificate",
     "The initial testing of a batch often runs only part of a parameter's panel: mycotoxins "
     "assayed for total aflatoxins alone, with Aflatoxin B1 and Ochratoxin A not tested. The "
     "certificate printed a bracketed blank for each untested analyte, which in a results "
     "column reads as a finding still to come; before the ND ruling was scoped it would have "
     "printed ND, asserting the analyte was measured and absent.",
     "Owner's ruling of 11.09.2026: \"since they're not tested, those sub-parameters are not "
     "going to enter inside the certificate of quality at all.\" fillCoq() removes the row "
     "from the compiled copy — only for a sub-determination inside a parameter that WAS "
     "tested, because if nothing in the group has a result the parameter itself is missing "
     "and that is a gap the certificate must show. 36 rows removed across the 22 drafts, all "
     "of them Aflatoxin B1 or Ochratoxin A on 18 release certificates; the retest of the same "
     "batch prints all three. Blank printed lines 87 -> 51. The master file is untouched.",
     "Nothing. Recorded because it is the boundary of the ND ruling: n.r. printed by a "
     "laboratory as a result means ND, and an analyte absent from the panel is not a result "
     "at all.",
     "BG1024 release vs 12-month retest, verified through fillCoq in headless Chromium"),

    ("OI-21", "Document rendering", "ruled",
     "Sixty-six faces in the tranche PDFs embedded as Type 3 rather than outlines",
     "39 faces in Tranche 1 and 27 in Tranche 2 were Montserrat Medium Italic rasterised "
     "into Type 3 glyph procedures, while the same family embedded as TrueType elsewhere "
     "in the same document. The count was identical in the previously committed PDFs, so "
     "it predates the 11.09 work. Cause: .ap-cred sets font-weight:600 in italic and the "
     "font request asked for italic at 400, 500 and 700 only, so the browser emboldened "
     "the nearest real italic — and a synthesised face has no outlines to embed.",
     "Fixed: italic 600 and 700 added to the font request in both print_coq_pdfs.py and "
     "house_fonts.py, and the rule written down beside them — when a stylesheet sets an "
     "italic weight, that weight belongs in FAMILIES.",
     "Nothing. Recorded because the first Type 3 fix (pinning the variable axes) looked "
     "complete and was not: it fixes the faces the page asks for by name, never one the "
     "page never asked for.",
     "print_coq_pdfs.py FAMILIES; pdffonts on both tranche PDFs"),

    ("OI-20", "Desk status", "open",
     "Nine result cells hold a desk status instead of a value",
     "not ingested (the document exists but has not been extracted into the eCoA database) "
     "on 5 cells, held for review (the two independent reads disagreed) on 3, and one "
     "Identification C awaiting a decision.",
     "Each is carried on the Work Order sheet with what it needs; none reaches a certificate.",
     "Nothing — these are desk work, listed so the count is visible.",
     "Work Order sheet"),
]

STATES = {"open", "marked", "ruled"}
HEAD = ("Ref", "Area", "State", "Item", "What was found", "What the desk did",
        "What is needed", "Evidence")


def items(state=None, area=None):
    """The register, optionally narrowed.

    >>> len(items())
    48
    >>> [i[0] for i in items(area="Specification")]
    ['OI-01', 'OI-02', 'OI-03', 'OI-44']
    >>> sorted({i[2] for i in items()})
    ['marked', 'open', 'ruled']
    >>> all(len(i) == len(HEAD) for i in items())
    True
    >>> sorted({i[0] for i in items()}) == sorted([i[0] for i in items()])
    True
    """
    out = ITEMS
    if state:
        out = [i for i in out if i[2] == state]
    if area:
        out = [i for i in out if i[1] == area]
    return out


def markdown():
    """The register as the note that travels with the package."""
    lines = ["# Open items — awaiting the owner", "",
             "Every finding the desk has raised and cannot itself settle, with the evidence",
             "behind it and the decision being asked for. Built by `open_items.py`; the same",
             "register is the **Open Items** sheet of the workbook.", "",
             f"**{len(items('open'))} open · {len(items('marked'))} marked on the certificate**",
             ""]
    area = None
    for ref, ar, state, head, found, desk, asked, ev in ITEMS:
        if ar != area:
            area = ar
            lines += [f"## {ar}", ""]
        lines += [f"### {ref} · {head}", "",
                  f"*State:* **{state}** · *Evidence:* {ev}", "",
                  f"**Found.** {found}", "",
                  f"**The desk.** {desk}", "",
                  f"**Needed.** {asked}", ""]
    return "\n".join(lines)


def sheet(wb, index=None):
    """Write the Open Items sheet into an open workbook."""
    from openpyxl.styles import Alignment, Font, PatternFill
    name = "Open Items"
    if name in wb.sheetnames:
        wb.remove(wb[name])
    sh = wb.create_sheet(name, index if index is not None else len(wb.sheetnames))
    fill = {"open": "FFF2CC", "marked": "FCE4D6", "ruled": "E2EFDA"}
    for c, t in enumerate(HEAD, 1):
        cell = sh.cell(1, c, t)
        cell.font = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F3864")
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    for r, row in enumerate(ITEMS, 2):
        for c, v in enumerate(row, 1):
            cell = sh.cell(r, c, v)
            cell.font = Font(name="Calibri", size=8, bold=(c <= 3))
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if c == 3:
                cell.fill = PatternFill("solid", fgColor=fill.get(v, "FFFFFF"))
        sh.row_dimensions[r].height = 66
    for col, w in zip("ABCDEFGH", (7, 15, 9, 34, 52, 40, 44, 30)):
        sh.column_dimensions[col].width = w
    # the workbook's standing claim: every sheet prints landscape, fitted to width
    sh.page_setup.orientation = "landscape"
    sh.page_setup.fitToWidth = 1
    sh.page_setup.fitToHeight = 0
    sh.sheet_properties.pageSetUpPr.fitToPage = True
    sh.freeze_panes = "D2"
    sh.auto_filter.ref = f"A1:H{len(ITEMS) + 1}"
    return sh


if __name__ == "__main__":
    import doctest
    fail, ran = doctest.testmod()
    print("%d doctests, %d failed" % (ran, fail))
    if fail:
        sys.exit(1)
    if "--md" in sys.argv:
        p = os.path.join(HERE, "tracker", "OPEN_ITEMS.md")
        open(p, "w", encoding="utf-8").write(markdown() + "\n")
        print("wrote", p)
    import collections
    print("open items: %d (%d open, %d marked on the certificate)"
          % (len(ITEMS), len(items("open")), len(items("marked"))))
    for a, n in collections.Counter(i[1] for i in ITEMS).most_common():
        print("   %-16s %d" % (a, n))
    sys.exit(0)
