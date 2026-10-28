# Signing sets, 22.10.2026: P060252, P050292, P050102, P060442, P060332

No signed scan of these CoQs is on Drive (checked 22.10 and 28.10.2026: T3 SCANN BUNDLE and its `COQ+iCOA`, the raw scans
of 24.09, 09.10 and 16.10.2026), so they were not printed and signed. Two sets to print and sign in person, pages taken
unchanged from `DELIVER_2026-10-22_Batch_Bundles/` (no certificate rebuilt). Each CoQ is followed by its iCoA, where it
has one still to sign, and every external certificate it cites. `MANIFEST.tsv` lists every page.

Every CoQ here is a release CoQ of its batch (Head of QC, #231: "initial" and "retest" are labels only). A batch sent for
further testing gets a new version, dated when issued, that supersedes the last (#230). Version 1 is the batch's first
release CoQ; version 2 supersedes it after the batch's additional testing.

| set | release CoQs |
| --- | --- |
| `Release_CoQ_v1_…pdf` (38 pp.) | -016 P050102 + iCoA-016 · -033 P050292 + iCoA-033 · -061 P060252 + iCoA-061 · -068 P060332 + iCoA-068 · -080 P060442 (no iCoA: CNP tested 1, 2, 7, 8) |
| `Release_CoQ_v2_supersedes_v1_…pdf` (44 pp.) | -148 P060252 (supersedes -061) · -150 P050292 (-033) · -151 P050102 (-016) · -161 P060442 (-080, no iCoA) |

- The iCoAs of version 2, -097, -094 and -151, are already signed (`20261009180750.pdf` pp. 10, 12, 13), so they are not in
  the set; their signed originals go with -148, -150 and -151.
- P060332 has one testing campaign, so one release CoQ, -068 (#231); -087 is withdrawn.
- Print-safe (`tracker/print_safe_pdf.py --check`). Bookmarks per CoQ.
