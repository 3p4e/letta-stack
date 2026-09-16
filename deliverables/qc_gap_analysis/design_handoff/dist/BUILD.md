# How this folder is rebuilt

These archives are a convenience for sending the set on. Everything in them is built from
the repository, so they can be thrown away and remade at any time:

```
node    design_handoff/toolchain/build_v40.js                              # 172 documents
python3 design_handoff/toolchain/print_v40.py                              # one PDF per page + four folder documents
python3 design_handoff/toolchain/merge_tranches_v40.py --no-print          # tranche 1 and 2, both rounds
python3 design_handoff/toolchain/merge_tranches_v40.py --no-print --series reissue
python3 design_handoff/toolchain/merge_tranches_v40.py --no-print --tranche 3
python3 design_handoff/toolchain/merge_tranches_v40.py --no-print --tranche 3 --series reissue
```

then zip `design_handoff/pdf/` into the four parts below. The split is by tranche plus one
by testing round, because each part has to stay under the 30 MiB a chat attachment allows.

| archive | contents |
| --- | --- |
| `PP_CoQ_Tranche_1_2026-09-16.zip` | `CoQ_Tranche_1.pdf` (42 pp) · `CoQ_Tranche_1_Retest.pdf` (21 pp) |
| `PP_CoQ_Tranche_2_2026-09-16.zip` | `CoQ_Tranche_2.pdf` (64 pp) · `CoQ_Tranche_2_Retest.pdf` (32 pp) |
| `PP_CoQ_Tranche_3_2026-09-16.zip` | `CoQ_Tranche_3.pdf` (60 pp) · `CoQ_Tranche_3_Retest.pdf` (30 pp) |
| `PP_CoQ_By_testing_round_2026-09-16.zip` | `CoQ_ISSUE_COQ.pdf` (89 pp) · `CoQ_REISSUE_T1/T2/T3.pdf` (21 / 32 / 30 pp) |

The 172 single-certificate PDFs are **not** in the archives — they are 88 MiB. They live in
`design_handoff/pdf/pages/`, one file per certificate, and `print_v40.py` writes them.

The 300 dpi flattened prints (`*_flat.pdf`) are not in the archives either, for the same
reason. The tranche flats are tracked in `design_handoff/pdf/`; the four per-folder flats are
one command away and deliberately untracked.
