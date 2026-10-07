# PP-QC-SP-002/26 — in-house loss on drying before shipment, Tranches 1 and 2

Three separate document packages, bilingual Macedonian / English, built from committed records only.
Head of QC, 06.10.2026: the sampling of the bags and the loss-on-drying analysis are separate
documentation packages, on the company's own SOP forms. The forms reproduce the July 2026 layouts
field for field (QCT 024 v01, QCSOP 011_A03 v7.0, QCT 021 v01, QASOP_031_A05_v1, QASOP_031_A07);
only the values are prefilled. Each sampling form carries every batch (Head of QC, 05.10.2026),
except A03, whose layout is one batch per form.

**As executed (Head of QC, 06.10.2026):** one bag per batch, chosen at sampling and written on the
forms as K{carton}B{bag}; one sample from it; one test portion per batch; all 46 batches sampled on
one day and dried in one oven run. The plan is amended to match (chapter 1); this replaces the
r-plan, the k = 1/2/3 rule and the two-day split of the draft of 05.10.2026.

| Package (`out/`) | Contents |
|---|---|
| `1_PLAN/`, `PP-QC-SP-002_26_PACKAGE-1_PLAN.zip` | Sampling Plan and Execution Protocol, as amended 06.10.2026 (9 pages) |
| `2_SAMPLING_EXECUTION/`, `PP-QC-SP-002_26_PACKAGE-2_SAMPLING_EXECUTION.zip` | Package index, then the seven documents of the one sampling day below |
| `3_LOD_ANALYSIS_EXECUTION/`, `PP-QC-SP-002_26_PACKAGE-3_LOD_ANALYSIS_EXECUTION.zip` | LOD-01 (run 1, invalidated), its Attachment 1 (weighings on two balances), deviation DEV-01, and LOD-01R, the repeat of all 46 batches on the AUW220D |

Package 2, in order of use:

| Step | Document | Form | Record No. |
|---|---|---|---|
| 1 | Transfer, secure warehouse to sampling room: one bag per batch, its K#B# written at retrieval, net 400.0 g, gross at receipt | QCT 024 v01 | `PP-QC-SP-002/26-D1-RCPT` |
| 2 | Visual inspection on opening, one form per batch (46) | QCSOP 011_A03 v7.0 | from the A03 register |
| 3 | Before, sampled and after, one row per batch with its sample code; waste, loss, gain | QCT 021 v01 | MLR number from its register |
| 4 | SAMPLED bag labels, 52.5 x 33 mm, one per sampled bag (46), bag written in | QASOP_031_A05_v1 | none |
| 5 | Sample labels, A4 4 x 2, one per batch (46) | QASOP_031_A07 | none |
| 6 | Transfer, sampling room to secure warehouse: the same bags, new net and gross from QCT 021 | QCT 024 v01 | `PP-QC-SP-002/26-D1-RET` |
| 7 | Transfer, sampling room to QC laboratory: one sample per batch | QCT 024 v01 | `PP-QC-SP-002/26-D1-SMP` |

Package 3, the LoD execution record: A receipt of the samples (from step 7), B equipment and
conditions, C homogenisation and test portions, D weighings to constant mass, one test portion per
batch (46 prefilled rows), E results per batch (the one portion's LoD), F deviations and OOS, G sign-offs.

**DEV-01 (06.10.2026):** in run 1, m_B and the 1 g test portion (G1) were weighed on a precision balance
(d = 1 mg) instead of the AUW220D; G2 was weighed on both balances (Attachment 1). The method needs a
balance reading at least 4 decimals, and no later weighing can correct G1, so the Head of QC invalidated
run 1 and all 46 batches are repeated from the sample remainders under **LOD-01R**, every weighing on the
AUW220D. The repeat is reported for every batch; run 1 stays in the record, not reported. The band rule
first written in DEV-01 is kept there as superseded.

**INF-01 (07.10.2026):** `build_exec_memo.py` builds the Head of QC's official information note to the CEO and
executive management, `out/3_LOD_ANALYSIS_EXECUTION/PP-QC-SP-002_26-INF-01_Information_Note_LoD_Deviation_Repeat.pdf`
(3 pages + a 1-page annex of the 46 run-1 values): the deviation, the measures before the 24-h weighing, what the
run-1 values show and the cautions with their criteria, and the repeat of all 46 under LOD-01R. PDF only (Head of
QC: no Word files): the DOCX is built in a folder outside the repository. It is not in package 3's packet or zip.

**Run 1, for information** (`run1_LOD-01_2026-10-05/`): the laboratory's workbook and `check_run1.py`,
which recalculates every row from its raw weighings into `RUN1_CHECK.tsv`. The workbook's LoD agrees on
all 46 rows, and no value exceeds 11.7 %. For DEV-01 section D, G2 on the AUW220D minus G2 on the precision
balance gives mean +0.03 mg and SD 0.53 mg (n = 46). Seven portions fall outside 0.900–1.100 g
(Ph. Eur. ±10 % on 1.000 g).

Each package folder holds every DOCX and PDF and a merged packet PDF with a bookmark per document.
The label sheets are in the folder and the zip but not in the packet: they print on perforated
stock. `HANDOVER_LoD_a02.2_verification_2026-10-06.md` is the brief for the method-verification chat (Ph. Eur.
2.2.32, monograph 3028, the a02.2 package and what this campaign can add); it is not part of the packages.
Data behind every number: `SAMPLING_PLAN_T1_T2_2026-10.tsv` (one row per lot),
`bag_selection.tsv` (one row per batch, bag written in at sampling), `DATA_NOTES.md`, `BUILD_LOG.md` (pp_verify result,
page count and SHA-256 of every file).

## What the campaign does

- 46 production batches (Tranche 1: 20, Tranche 2: 26) in 400 g triple-foil bags, 10 per carton, in
  the secure warehouse (sampling point SP-12 of QCSOP 011 v03).
- Per batch (as executed, 06.10.2026): one bag opened, chosen at sampling and its number written on
  the forms; one sample from it; one test portion of about 1.000 g; the batch result is that portion's
  LoD. N = kg / 0.400 rounded up stays in the plan as information only.
- Method a02.2 (Ph. Eur. 2.2.32, monograph 3028): vacuum oven VO29 at 40 degC, 20 +/- 2 mbar, 24 h, over
  about 100 g molecular sieve R; 1.000 g cut, unsieved, in a pre-dried tared bottle; cool at least 30 min in
  the desiccator, weigh on the Shimadzu AUW220D, back into the oven and weigh again until constant mass
  (two weighings within 0.5 mg); LoD % = (m0 - m1) / m0 x 100; criterion 12.0 % w/w maximum (QCSP 001).
- One sampling day, all 46 batches (46 bags, 46 portions), one oven run; results read on Day 2 after
  the 24-hour weighing and the constant-mass check.

## Decisions taken (Head of QC, 05.10.2026) and defaults he can overrule

1. kg basis = master v57, sheet `Reference`, block DELIVERY T1-T3, column E. One evident defect is
   corrected, not propagated: GG1024_01 (P050092) reads 0.87 kg in cell E216 against 223.734 kg on the
   owner's stock table and 560 bags in the July plan — the plan uses 223.73 kg and lists the cell for
   correction. KC102501 keeps the master's 21.67 kg (stock table 16.000 kg).
2. One test portion per batch (06.10.2026); QCSOP 011 v03 writes a duplicate for LoD at SP-06 — noted in the plan.
3. Scope T1 + T2 only; T3 (31 lots) follows as PP-QC-SP-003/26 with the same builder.
4. Built locally with the repository engine (the master of the engine deployed on KVM4); no Letta or
   KVM4 call was needed — the content is authored here and the engine formats it.
5. Documents carry IN REVIEW — NOT FOR USE; on approval they are rebuilt as v1.0 with the effective
   date the Head of QC gives (`STATUS` in `build_campaign_docs.py`). No approval date is invented.
6. Signatories as on the owner's own documents: prepared / approved B. Nikolov, M.Pharm. (QC Head /
   QC Department Manager), checked J. Romevska (QA), analyst Hristina Cekic (QC Analyst).

## Open for the Head of QC (also section 11 of the plan)

- Master v57 Reference E216 (GG1024_01); KC102501 kg.
- One test portion per batch against the SOP duplicate (SP-06).
- The additional drying period for the second weighing (a02.2 or his instruction).
- Record numbers: D1-RCPT, -RET, -SMP for the QCT 024 transfers and LOD-01 for the analysis
  (or QCT 025); A03 and QCT 021 numbers from their registers; RQS registration before sampling.
- HMA pairing on the sample remainders for the method-verification work (5 to 12 % range) — entered before
  approval if the verification agent asks for it.

## Rebuild

```
python3 campaign_data.py --test && python3 campaign_data.py      # data -> TSVs
python3 build_campaign_docs.py                                    # package 1, pp_verify PASS required
python3 build_execution_packages.py                               # packages 2 and 3 (forms, LoD record)
python3 build_labels.py                                           # QASOP_031 label sheets
for f in out/1_PLAN out/2_SAMPLING_EXECUTION out/3_LOD_ANALYSIS_EXECUTION; do
  (cd $f && soffice --headless --convert-to pdf --outdir . *.docx); done
python3 package.py                                                # packets, zips, BUILD_LOG.md
python3 build_exec_memo.py                                        # INF-01 note to management, PDF only
```

Fonts: copy `pp-document-suite/assets/fonts/*.ttf` to `~/.local/share/fonts` and run `fc-cache -f`
before converting, so Calibri resolves to Carlito.
