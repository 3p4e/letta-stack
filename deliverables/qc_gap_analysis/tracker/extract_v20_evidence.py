#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lift the 09.09.2026 evidence out of the owner's v20 workbook, verbatim.

    python3 deliverables/qc_gap_analysis/tracker/extract_v20_evidence.py

`CoQ_Analysis_Master_v20_owner.xlsx` came from the owner on 10.09.2026 (Drive
`1cBmbOgHSMlzIGyGjuZFRP5DagigtXx29`, modified 09.09.2026 13:55). It carries the
09.09 pass over the certificate folder: 387 PDFs in `eCoA_DATABASE` read
name-for-name, and every one of the 600 determinations of Tranches 1 and 2
resolved to a document, a laboratory, an issue date and the result that document
prints.

That evidence is a *source*, not a conclusion, so it is lifted into three flat
files beside the other vendored sources and nothing is recomputed here. The
transcription is verbatim: what the sheet holds is what the file holds, cell for
cell, with only leading and trailing whitespace removed.

  cell_resolution_2026-09-09.tsv   600 rows — batch x determination
  coverage_update_2026-09-09.tsv   the parameters a 09.09 certificate closes
  identity_block_2026-09-09.tsv    the 40 batches whose identity determinations
                                   cite an iCoA that has not been issued

The three sheets they come from are `Cell Resolution 09.09`,
`Coverage Update 09.09` and `Identity Problem 09.09`.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
SRC = os.path.join(HERE, "CoQ_Analysis_Master_v20_owner.xlsx")
# The owner's workbooks live beside this script; the flat sources the CoQ
# schedule reads live one directory up, beside the schedule itself.
OUTDIR = GAP

# sheet -> (output file, the header row's first cell, the rows to keep)
JOBS = [
    ("Cell Resolution 09.09", "cell_resolution_2026-09-09.tsv", "Tranche",
     lambda r: r and r[0] in ("1", "2")),
    # The sheet has two blocks under two headers — the lots the coverage sheet
    # already carried, then the lots it carried no row for at all. The columns
    # line up (the second block simply has no "Status before"), so both are kept
    # in one table and a data row is any row that names a parameter.
    ("Coverage Update 09.09", "coverage_update_2026-09-09.tsv", "CU batch",
     lambda r: len(r) > 4 and r[4].startswith("#")),
    ("Identity Problem 09.09", "identity_block_2026-09-09.tsv", "Batch",
     lambda r: r and r[0]),
]


def cells(ws):
    """Every row of a sheet as a list of trimmed strings."""
    for row in ws.iter_rows(values_only=True):
        yield ["" if v is None else str(v).strip() for v in row]


def main():
    import openpyxl
    wb = openpyxl.load_workbook(SRC, data_only=True, read_only=True)
    rc = 0
    for sheet, out, first, keep in JOBS:
        if sheet not in wb.sheetnames:
            print("missing sheet: " + sheet, file=sys.stderr)
            rc = 1
            continue
        rows = list(cells(wb[sheet]))
        head = next((i for i, r in enumerate(rows) if r and r[0] == first), None)
        if head is None:
            print("no header row in " + sheet, file=sys.stderr)
            rc = 1
            continue
        hdr = [c for c in rows[head] if c]
        body = [r[:len(hdr)] for r in rows[head + 1:] if keep(r)]
        # A tab inside a cell would split a column; none of these sheets has one,
        # and the assertion keeps it that way rather than silently corrupting a row.
        for r in [hdr] + body:
            assert not any("\t" in c for c in r), "tab inside a cell of " + sheet
        path = os.path.join(OUTDIR, out)
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh, delimiter="\t", lineterminator="\n")
            w.writerow(hdr)
            w.writerows(body)
        print("%-34s %3d rows x %d cols -> %s" % (sheet, len(body), len(hdr), out))
    return rc


if __name__ == "__main__":
    sys.exit(main())
