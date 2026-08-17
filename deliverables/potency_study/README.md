# Strain Potency Study — 14 Aug 2026 (declarations reworked 17 Aug 2026)

Every Total Δ⁹-THC result ever tested, per strain, in one place + proposed new
warehouse grades for the T1/T2/T3 stock, declared as **nominal ± tolerance**.
Informal working analysis (no doc code); the laboratory certificates and the
issued QCSP 001 specifications remain authoritative — this study is a
proposed revision, not an amendment to any issued spec.

- `Strain_Potency_Study_14Aug2026.docx` / `.pdf` — the Word document.
- `Potency_Atlas.html` / `.pdf` — the same data as a self-contained,
  bilingual "creative" single-file artifact (light theme by default; dark
  toggle), with the renamed-specification cross-reference board.
- `build_potency_dataset.py` → `potency_dataset.json` — §6B bound dataset:
  99 register assays (77 batches, 20 strains) + the Grape Pie stability
  program (9 rows, 1 excluded as defective per PP-QC-ERR-002), per-strain
  stats (mean/SD/range/95% CI at n≥3), per-batch anchors and declared tiers.
- `render_figures.py` → `figures/` — 20 per-strain distribution charts
  (0–35% axis, ±1.5% zone per result, KDE, mean/CI, declared W-tiers vs old
  standard boundaries, Grape Pie stability points) + all-strain overview.
- `build_potency_report.py` — the Word document builder (PP engine).
- `build_potency_html.py` — the Potency Atlas builder.
- `incoming/` — source workbooks + comparison notes used to cross-check the
  dataset against the live `PP_THC_by_Strain.xlsx` register.

**Range rule.** Required window: floor = anchor − 1.5 %/yr degradation
allowance − measurement U (≈6.2% of value, k=2), never below the 5.00%
release A.C.; ceiling = anchor + max(1.0, U). Per-strain tiers are greedily
clustered on that window at ≤6.5 points wide (tiers may overlap — batches
grade individually).

The window is then **declared as NOMINAL ± TOLERANCE** — the same form the
issued QCSP 001 specifications already use — but here the nominal is fixed
to a whole number (18.00 %, never 18.50 %) and the tolerance is the minimum
that still covers the entire window, rounded up to the next 0.01 (always
outward: it can widen a declaration, never lose coverage). Because of that,
the declared span can end up close to a full percentage point wider than the
6.5-point clustering cap — the cap bounds the evidence window, not the final
declaration. **A batch's declaration is always its tier's declaration** —
the same nominal ± tolerance is printed everywhere that batch appears.

Verified live against ImB_QC_COAs (4,134 passages) and logged to the host's
shared memory (agent ecoa_retrieval_gpt4o, passage 90148f1a).
