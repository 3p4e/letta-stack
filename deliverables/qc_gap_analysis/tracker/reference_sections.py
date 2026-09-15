#!/usr/bin/env python3
"""Shared reading of the built workbook: which one, and where a folded sheet went.

Nine leaf sheets were folded into one on 14.09.2026 (the owner asked for six
tabs, not sixteen). `fold_reference_sheet` in build_tracker_v8.py writes the
fold; this reads it. Each folded sheet keeps its own title row — the sheet name
in capitals in column 1, nothing in column 2 — then its content, then a blank
gutter of two rows.

Everything downstream of the workbook (the verifier, the artifact extractor)
goes through `sheet_or_section`, so a check written before the fold keeps
reading `.cell(r, c)` and `.max_row` as though nothing moved.
"""

import os
import re

REFERENCE = "Reference"


def latest_master(here):
    """The newest CoQ_Analysis_Master_vN.xlsx in `here`, or None.

    Every checker's default used to be a literal version, so a gate watched
    whichever workbook someone last typed into it and a rebuild quietly left it
    verifying a stale one. The newest on disk is the one that ships.
    """
    best, path = -1, None
    for f in os.listdir(here):
        m = re.fullmatch(r"CoQ_Analysis_Master_v(\d+)\.xlsx", f)
        if m and int(m.group(1)) > best:
            best, path = int(m.group(1)), os.path.join(here, f)
    return path


def ref_bounds(wb, name):
    """(first_content_row, last_content_row) of a folded sheet's section, or None.

    Read from the `_fold_<slug>` defined name the fold wrote, never inferred from
    the sheet: several folded sheets separate their own inner sections with the
    same blank gutter that separates one folded sheet from the next, so a reader
    that scans for blank rows stops early and loses the rest of the section.
    """
    if REFERENCE not in wb.sheetnames:
        return None
    dn = wb.defined_names.get("_fold_" + re.sub(r"\W+", "_", name).strip("_"))
    if dn is None:
        return None
    m = re.search(r"\$(\d+):\$?[A-Z]*\$(\d+)$", dn.attr_text)
    return (int(m.group(1)), int(m.group(2))) if m else None


def sheet_or_section(wb, name):
    """The sheet if it still exists, else a read-only view of its Reference section."""
    if name in wb.sheetnames:
        return wb[name]
    b = ref_bounds(wb, name)
    if b is None:
        raise KeyError("neither a sheet nor a Reference section: %r" % name)
    first, last = b

    class _Section:
        title = name
        max_row = last - first + 1

        def __init__(self):
            self._sh = wb[REFERENCE]
            self.max_column = self._sh.max_column

        def cell(self, row, column=1):
            return self._sh.cell(first + row - 1, column)

        def iter_rows(self, min_col=1, max_col=None, values_only=False):
            hi = self.max_column if max_col is None else max_col
            for r in range(first, last + 1):
                row = [self._sh.cell(r, c) for c in range(min_col, hi + 1)]
                yield tuple(c.value for c in row) if values_only else row

    return _Section()


def has(wb, name):
    """Is this sheet readable at all — still a tab, or a section of Reference?"""
    return name in wb.sheetnames or ref_bounds(wb, name) is not None
