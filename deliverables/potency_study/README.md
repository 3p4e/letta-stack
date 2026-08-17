# Strain Potency Study — 14 Aug 2026 (grade ladder rebuilt contiguous 17 Aug 2026)

Every Total Δ⁹-THC result ever tested, per strain, in one place + proposed new
warehouse grades for the T1/T2/T3 stock, declared as **Pot.-N: nominal ±
tolerance**. Informal working analysis (no doc code); the laboratory
certificates and the issued QCSP 001 specifications remain authoritative —
this study is a proposed revision, not an amendment to any issued spec.

- `Strain_Potency_Study_14Aug2026.docx` / `.pdf` — the Word document.
- `Potency_Atlas.html` / `.pdf` — the same data as a self-contained,
  bilingual "creative" single-file artifact (light theme by default; dark
  toggle), with the renamed-specification cross-reference board.
- `build_potency_dataset.py` → `potency_dataset.json` — §6B bound dataset:
  99 register assays (77 batches, 20 strains) + the Grape Pie stability
  program (9 rows, 1 excluded as defective per PP-QC-ERR-002), per-strain
  stats (n / min–max span only — no mean/SD/CI), per-batch anchors and
  declared tiers.
- `render_figures.py` → `figures/` — per-strain distribution charts (0–30%
  axis, ±1.5% zone per result, KDE shape only, declared Pot.-tiers with a
  hatched red band over any genuine gap, old standard boundaries) + an
  all-strain overview.
- `build_potency_report.py` — the Word document builder (PP engine).
- `build_potency_html.py` — the Potency Atlas builder.
- `build_potency_workbook.py` → `Potency_Specs_and_Results.xlsx` — the
  7-sheet spec/grade/result workbook.
- `incoming/` — source workbooks + comparison notes used to cross-check the
  dataset against the live `PP_THC_by_Strain.xlsx` register.
- `portfolio_master.json` — the company's own per-batch bracket labels (78
  batches; see below).

**Grade rule.** Each tier is a whole-number nominal ± a tolerance that never
exceeds 10.00% of that nominal (`Pot.-1: 20.00% ±2.00%`, i.e. 18.00%–22.00%).
A strain's whole ladder is planned together — fewest tiers first, then
closest fit to the tested results — so that **adjacent tiers of the same
strain carry no blind gap**: one tier's ceiling sits exactly 0.01 below the
next tier's floor, always, so a result between two established grades still
falls into one of them. Tolerance is therefore at the full 10% cap whenever
the data allows it, and shrinks only as far as needed to close the gap to
the neighbour exactly — never past what still covers every batch assigned to
the tier. A tier's floor never sits below the 5.00% release acceptance
criterion.

**Genuine gaps.** 2 of 24 strains (Graps & Creme; Orange Punch Mimosa) — and
their equivalents on the independently-clustered renamed-name board — contain
two neighbouring tested results so far apart that NO whole-number nominal
pair can bridge them within the 10% cap, even as bare single-batch tiers
either side. That is a real discontinuity in the strain's own tested history,
not an algorithm limitation, so it is left as an honest, flagged gap
(`gap_after: true` in the dataset) rather than force-closed by inventing an
unsupported "bridge" tier or exceeding the cap. A batch testing in one of
these zones has no precedent and should be assessed individually.

**Portfolio-Master brackets (for reference, not used by this study's tiers).**
The company's own batch labels in `portfolio_master.json` use a completely
different, simpler system: 7 fixed, strain-agnostic, contiguous 3-point-wide
bands (7–10 / 10–13 / 13–16 / 16–19 / 19–22 / 22–25 / ≥25%), every boundary
shared exactly with the next. A batch is simply assigned whichever fixed
bracket contains its raw result — there is no per-strain nominal in that
system, and no evidence of results being placed toward the top of their
bracket (mean fractional position across 75 dated batches ≈ 0.50).

**A batch's declaration is always its tier's declaration** — the same
nominal ± tolerance is printed everywhere that batch appears, in the HTML
Atlas, the Word study, and the Excel workbook alike.

Verified live against ImB_QC_COAs (4,134 passages) and logged to the host's
shared memory (agent ecoa_retrieval_gpt4o, passage 90148f1a).
