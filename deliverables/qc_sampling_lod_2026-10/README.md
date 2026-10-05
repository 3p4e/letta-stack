# PP-QC-SP-002/26 — in-house loss on drying before shipment, Tranches 1 and 2

Three documents, bilingual Macedonian / English, built with the Purely Plant document engine
(`pp-document-suite/`, python-docx) from committed records only. Head of QC, 05.10.2026: *one
execution document per sampling day, all the batches of that day together* — so the set is the
plan plus two daily execution records, not a form per batch.

| File (`out/`) | What it is |
|---|---|
| `PP-QC-SP-002_26_Sampling_Plan_LoD_T1_T2.docx` / `.pdf` | Sampling Plan & Execution Protocol — purpose, basis, formulas, per-batch plan (46 lots), day groups, conditions, homogenisation, the LoD method, schedule, record map, references, open items |
| `PP-QC-SP-002_26-ER-01_Execution_Record_Day1.docx` / `.pdf` | Execution record for every Day-1 batch: batch table, handover warehouse to QC, per-batch execution, per-bag inventory (493 prefilled rows), return, LoD determinations (44 prefilled rows), deviations, sign-offs |
| `PP-QC-SP-002_26-ER-02_Execution_Record_Day2.docx` / `.pdf` | The same for Day 2 (492 bag rows, 44 LoD rows) |
| `PACKET_PP-QC-SP-002_26_Plan_ER-01_ER-02.pdf` | The three PDFs merged, a bookmark per document |
| `PP-QC-SP-002_26_DOCX_PDF.zip` | Everything above in one archive |

Data behind every number: `SAMPLING_PLAN_T1_T2_2026-10.tsv` (one row per lot), `bag_selection.tsv`
(one row per selected bag), `DATA_NOTES.md` (the two data notes), `BUILD_LOG.md` (verify results,
page counts, SHA-256 of every file).

## What the campaign does

- 46 production batches (Tranche 1: 20, Tranche 2: 26) in 400 g triple-foil bags, 10 per carton, in
  the secure warehouse (sampling point SP-12 of QCSOP 011 v03).
- Per batch: N = kg / 0.400 rounded up (the warehouse's documented bag count governs if it differs),
  n = 1.5 x sqrt(N) rounded up bags opened (WHO TRS 929 Annex 4 r-plan, as in PP-QC-SP-001/26),
  systematic selection with a seeded random start (seed 20261005), one flower — the largest — per
  bag, all n flowers of a batch into ONE composite, k = 1 / 2 / 3 determinations by bag count
  (N up to 100 / 101 to 400 / above 400), about 1.000 g each.
- Method SAM_a02.2 (Ph. Eur. 2.2.32, monograph 3028): vacuum oven 40 degC, 15 to 25 mbar, 24 h,
  weigh, back into the oven for an additional period, weigh again until constant mass; criterion
  12.0 % w/w maximum (QCSP 001).
- Two sampling days balanced by bags to open (Day 1: 23 lots, 493 bags, 44 portions; Day 2: 23 lots,
  492 bags, 44 portions); Day-1 results read on Day 2, Day-2 results on Day 3.

## Decisions taken (Head of QC, 05.10.2026) and defaults he can overrule

1. kg basis = master v57, sheet `Reference`, block DELIVERY T1-T3, column E. One evident defect is
   corrected, not propagated: GG1024_01 (P050092) reads 0.87 kg in cell E216 against 223.734 kg on the
   owner's stock table and 560 bags in the July plan — the plan uses 223.73 kg and lists the cell for
   correction. KC102501 keeps the master's 21.67 kg (stock table 16.000 kg).
2. k = 1 / 2 / 3 by bag count; QCSOP 011 v03 writes a duplicate for LoD at SP-06 — noted in the plan.
3. Scope T1 + T2 only; T3 (31 lots) follows as PP-QC-SP-003/26 with the same builder.
4. Built locally with the repository engine (the master of the engine deployed on KVM4); no Letta or
   KVM4 call was needed — the content is authored here and the engine formats it.
5. Documents carry IN REVIEW — NOT FOR USE; on approval they are rebuilt as v1.0 with the effective
   date the Head of QC gives (`STATUS` in `build_campaign_docs.py`). No approval date is invented.
6. Signatories as on the owner's own documents: prepared / approved B. Nikolov, M.Pharm. (QC Head /
   QC Department Manager), checked J. Romevska (QA), analyst Hristina Cekic (QC Analyst).

## Open for the Head of QC (also section 11 of the plan)

- Master v57 Reference E216 (GG1024_01); KC102501 kg; documented bag counts at retrieval.
- k rule vs the SOP duplicate; oven capacity (44 bottles per night).
- The additional drying period for the second weighing (SAM_a02.2 or his instruction).
- Codes for the daily records (PP-QC-SP-002/26-ER-01/-02, or QCT 025); RQS registration before sampling.
- HMA pairing on the composites for the method-verification work (5 to 12 % range) — entered before
  approval if the verification agent asks for it.

## Rebuild

```
python3 campaign_data.py --test && python3 campaign_data.py      # data -> TSVs
python3 build_campaign_docs.py                                    # DOCX, pp_verify PASS required
cd out && for f in *.docx; do soffice --headless --convert-to pdf --outdir . "$f"; done
cd .. && python3 package.py                                       # packet PDF, zip, BUILD_LOG.md
```

Fonts: copy `pp-document-suite/assets/fonts/*.ttf` to `~/.local/share/fonts` and run `fc-cache -f`
before converting, so Calibri resolves to Carlito.
