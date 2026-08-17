# incoming/ — source snapshots used for the 17.08.2026 Atlas comparison

## `PP_THC_by_Strain.flat.txt`

A flattened, line-per-result transcription of the Drive workbook
**`PP_THC_by_Strain.xlsx`** (file id `1x3gArmDBJnrNL7rvDYlIoXa8MiGuV4v3`,
folder `ImB_QC_COAs`, modified 2026-08-17 06:03 UTC), taken from the Drive
text rendering of the sheet.

The workbook itself was subsequently downloaded and is stored alongside it as
`PP_THC_by_Strain.xlsx` (sha256
`5173d24e5ae9b16b135335f05309b1b1ea22913814528fdad0ff1d3e50e657e5`, 24 558
bytes, sheet `THC by Strain`, header at row 4). The transcription was then
checked against the binary: **97 value rows in each, every value identical,
one-to-one** — the only differences are abbreviated certificate strings
(`ППК25378` for `PP CoA #018 / ППК25378`). The comparison below was re-run
against the real workbook and reproduced exactly.

`PP_Production_Batches_QC_Result_Table.xlsx` (sha256
`5d6d312f97b8a65eb57f72970f62ecff242524b7b60f63955c5674fcf8d70113`, 73 733
bytes, sheet `QC Result Table`, header at row 3, limits row at row 4) is stored
here for the same audit trail.

Format: `strain group|seq,batch,P-number,value,spec,cert,date,lab`.
Continuation lines with an empty batch are the Farmahem retest of the batch
on the line above — that is how the workbook itself lays them out.

It is **not** a source of record. It exists only so the comparison against
`../potency_dataset.json` is reproducible and auditable. The laboratory
certificates in the QMS remain authoritative.

### What the comparison found

| | |
|---|---|
| Value rows in the workbook | 97 (sequence 1–80 complete, no gaps) |
| Results in `potency_dataset.json` | 99 |
| Workbook results **absent** from the Atlas | 0 |
| Atlas results **absent** from the workbook | 2 |

The two results the workbook does not carry:

- **GG1024** — Gorilla Glue, 13.34 %, in-house CoA 23.04.2025, no certificate
  number printed.
- **GP0824_02** — Grape Pie, 23.79 %, ППК25139, 22.05.2025.

Every other apparent difference is a certificate-string formatting variant of
the same result (e.g. `PP CoA #018 / ППК25378` vs `ППК25378`), matched on
normalised certificate code + value.

**Conclusion: the workbook introduces no potency result the Atlas did not
already hold, and the Atlas is a strict superset of it.**
