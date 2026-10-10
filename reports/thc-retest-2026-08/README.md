# Total Δ9-THC re-test vs. previous release result (August 2026)

Comparative QC report for 48 production batches (Tranche 1 and Tranche 2), evaluating the
August 2026 re-test against each batch's previous result and classifying both against the
grade specification band `[0.90·G, 1.10·G]`, G ∈ {8, 10, …, 28} % w/w.

## Contents

| File | What it is |
|---|---|
| `PP-QC-THC-VER-001_Total_THC_Retest_vs_Previous_v1.0.docx` | The report — bilingual MK\|EN, Purely Plant house style |
| `PP_THC_PrevVsRetest_T1_T2_2026-08-26.xlsx` | Underlying per-batch register (previous vs re-test, CoA refs, Δ) |
| `thc_dataset.json` | Bound dataset — the single source of truth for every statistic |
| `build.py`, `figs.py` | Builder — recomputes and re-asserts every reported figure at build time |

## Headline result

42 of 48 batches are comparable (6 have no prior test). After re-test, 21 (50.0 %) retain
their grade band and 21 (50.0 %) migrate — 16 upward, 5 downward. Mean change +0.91 pp,
median absolute change 1.81 pp, 11 batches moving more than 3 pp.

## Status of the data

The Tranche 2 values (25–26.08.2026) are **working extracts with no certificate of analysis
issued** and are not valid as batch-release results until certificated. Tranche 1 re-test
values are the Farmahem certificates 197-x-К/26 of 07.08.2026.

## Rebuilding

```
pip install python-docx latex2mathml lxml matplotlib
python build.py
```

Run it on a machine with Microsoft Word installed to get native OMML equations (the builder
falls back to Unicode typesetting when `MML2OMML.XSL` is unavailable) and to render the PDF
via the document suite's `render_pdf.ps1`.
