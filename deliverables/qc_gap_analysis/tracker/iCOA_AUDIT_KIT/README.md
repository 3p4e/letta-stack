# iCoA audit kit — 23.09.2026

Everything needed to check the internal certificates of analysis against the master workbook,
in one folder. Nothing here reads from memory: every number in `FULLNESS_2026-09-23.md` and
`reference/BASELINE.json` was produced by running `verify_fullness.py` on the workbook, and
every check re-derives its values from the workbook each time it runs.

## Put these two things in this folder

1. **`CoQ_Analysis_Master_v56.xlsx`** — the master workbook. The scripts find the highest
   `CoQ_Analysis_Master_v*.xlsx` lying beside them, so a later version is picked up on its own.
2. **The iCoA folder structure** — the per-batch folders with the documents filled in. Any
   layout: the checker walks the tree and finds the documents itself.

## Then, in order

    python3 verify_fullness.py --md FULLNESS.md          # step 1 — is the workbook full enough?
    python3 verify_icoa_folder.py <folder> --md FOLDER.md # step 2 — do the documents match it?

Exit code is the answer: **0** clean, **1** findings, **2** a check could not be performed.
Exit 2 is never a pass — a false clean is worse than no answer.

## What is in here

| | |
| --- | --- |
| `HANDOFF.md` | the brief: what was asked, what was found, what is left, and the rules that must not be broken |
| `verify_fullness.py` | step 1 — eight checks, A to H, on the workbook alone |
| `FULLNESS_2026-09-23.md` | step 1's output, run against v56 on 23.09.2026 — **27 findings** |
| `findings.json` | the same findings, machine-readable |
| `verify_icoa_folder.py` | step 2 — every document in the folder against the workbook, field by field |
| `reference/BASELINE.json` | the counts as measured, so a later run can prove it read the same workbook |
| `reference/SHEET_CONTRACT.md` | which sheet holds what, which columns are formulas, and how to read them |

No example certificate is bundled: the design system goes in this folder anyway, and one issued
iCoA with its stylesheets is 600 KB of the archive for no gain. If a reference for the layout is
wanted, the issued fleet is in the repository at
`deliverables/qc_gap_analysis/SIGNED_2026-09-21/iCoA/{Initial,Retest}/{HTML,PDF,DOCX}`.

Both scripts are stdlib + `openpyxl` only. `pip install openpyxl` is the whole setup.

## The one trap

Several register columns are **live Excel formulas, and openpyxl stores no cached value for
them** — read them and `CoQ code`, `iCoA (register)` and `CoQ (register)` all come back empty.
Two of those carry the iCoA-to-CoQ link. Anything that takes the blank at face value invents
gaps that are not there. `reference/SHEET_CONTRACT.md` lists every such column and the two ways
through. The scripts here do not read them at all; they join on the literal `Key` column instead.
