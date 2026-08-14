# Strain Potency Study — 14 Aug 2026

Every Total Δ⁹-THC result ever tested, per strain, in one place + proposed new
warehouse grade ranges for the T1/T2/T3 stock. Informal working analysis (no doc
code); the laboratory certificates remain authoritative.

- `Strain_Potency_Study_14Aug2026.docx` / `.pdf` — the document (14 pages A4).
- `build_potency_dataset.py` → `potency_dataset.json` — §6B bound dataset:
  99 register assays (77 batches, 20 strains) + the Grape Pie stability
  program (9 rows, 1 excluded as defective per PP-QC-ERR-002), per-strain
  stats (mean/SD/range/95% CI at n≥3), per-batch anchors and proposed tiers.
- `render_figures.py` → `figures/` — 20 per-strain distribution charts
  (0–35% axis, ±1.5% zone per result, KDE, mean/CI, proposed W-tiers vs old
  standard boundaries, Grape Pie stability points) + all-strain overview.
- `build_potency_report.py` — the document builder (PP engine).

Range rule: floor = anchor − 1.5%/yr degradation allowance − measurement U
(≈6.2% of value, k=2), rounded to 0.5, never below the 5.00% release A.C.;
ceiling = anchor + U. Per-strain tiers clustered at ≤6.5 points wide; tiers may
overlap (batches grade individually). Verified live against ImB_QC_COAs
(4,134 passages) and logged to the host's shared memory
(agent ecoa_retrieval_gpt4o, passage 90148f1a).
