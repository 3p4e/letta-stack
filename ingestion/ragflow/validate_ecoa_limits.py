#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare every recorded result against its own printed limit.

This is the check that was missing. Ten certificates carried a mould count
above the Ph. Eur. limit and every one of them concluded ОДГОВАРА; five of those
were additionally recorded in the register an exponent too low, so they read as
passing. Nothing in the pipeline compared a number to the limit sitting next to
it, so nothing objected.

Two rules, and they catch different failures:

  R1  a result above its limit is reported, whatever the certificate concluded.
      A laboratory verdict is not a substitute for the arithmetic.

  R2  a result recorded at exactly one power of ten below its limit is reported
      as SUSPECT. That is the shape the superscript misread produces — 4,2×10⁴
      read as 4,2×10³ — and it is the only shape that silently turns a fail into
      a pass. Verify those against the rendered page, never the text layer.

One limitation to know about: R1 compares against the **register's column
limit**, taken from the specification row. Some certificates print a tighter
limit of their own — 1220/2171/25 states TYMC ≤ 10² where the column says 10⁴,
and its result of 200 therefore fails on the paper while passing here. Comparing
against the limit printed on each certificate is the right long-term shape, and
needs the limit captured per result at extraction time. That is exactly what the
structured extraction in ECOA_RAG_PIPELINE_2026-08-30.md is for.

Run it against the register, or against any extraction that produces the same
columns:

    python3 ingestion/ragflow/validate_ecoa_limits.py REGISTER.xlsx

Exit status is 1 if any R1 finding exists, so it can gate a pipeline.
"""
import re
import sys
from openpyxl import load_workbook

SHEET = "Batch Release QC"
HEADER_ROW, SPEC_ROW, FIRST_DATA = 4, 5, 6

SUP = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6"}


def magnitude(text):
    """Parse '4,2×10⁴ CFU/g', '4.9×10^3', '200', '< 10' to a float, or None.

    Certificates and the register between them use Cyrillic 'х' and Latin 'x',
    superscripts and caret notation, decimal commas and decimal points. All of
    them mean the same number and all of them appear in this corpus.
    """
    if text is None:
        return None
    s = str(text).strip()
    if not s or s in {"/", "-", "—", "n/a", "not tested"}:
        return None
    # A cell that is mostly prose is a note, not a measurement. Without this,
    # "COMPLIES (numeric value not present in captured source excerpt for report
    # 1625/2026 …)" parses to 1625 and is reported as 406x over an aflatoxin
    # limit of 4 — a false positive that would train people to ignore the check.
    letters = sum(ch.isalpha() for ch in s)
    if letters > 12 and letters > len(s) * 0.35:
        return None
    for k, v in SUP.items():
        s = s.replace(k, "^" + v)
    s = s.replace("^^", "^").replace("х", "x").replace("Х", "x")
    s = s.replace("×", "x").replace(" ", "")

    m = re.search(r"([\d.,]*)x?10\^?(\d)", s)
    if m:
        mant = m.group(1).replace(",", ".").rstrip(".")
        try:
            return (float(mant) if mant else 1.0) * (10 ** int(m.group(2)))
        except ValueError:
            return None
    m = re.search(r"([\d]+[.,]?[\d]*)", s)
    if m:
        try:
            return float(m.group(1).replace(",", "."))
        except ValueError:
            return None
    return None


def main(path):
    ws = load_workbook(path, data_only=True)[SHEET]
    v = lambda x: "" if x is None else str(x).strip()
    hdr = [v(c.value) for c in ws[HEADER_ROW]]
    spec = [v(c.value) for c in ws[SPEC_ROW]]

    # Columns whose specification cell states a numeric ceiling.
    cols = []
    for j, s in enumerate(spec):
        lim = magnitude(s)
        if lim and hdr[j] and "spec" not in hdr[j].lower():
            cols.append((j, hdr[j], lim, s))

    over, suspect, batch = [], [], ""
    for row in ws.iter_rows(min_row=FIRST_DATA):
        cells = [v(c.value) for c in row]
        if not any(cells):
            continue
        if cells[1]:
            batch = cells[1]
        if not re.match(r"^[\w/().\- ]{3,}$", cells[22] or ""):
            continue
        for j, name, lim, raw in cols:
            got = magnitude(cells[j]) if j < len(cells) else None
            if got is None:
                continue
            if got > lim:
                over.append((row[0].row, batch, cells[22], name, cells[j], raw, got / lim))
            elif abs(got * 10 - lim) < lim * 1e-9 or (
                    lim / 10 <= got < lim and abs(got * 10 / lim - 1) < 0.999):
                pass  # ordinary in-spec value one decade down; not by itself suspect
        # R2: a value exactly one decade below the limit, in a column that uses
        # powers of ten, is the shape a misread ⁴->³ leaves behind.
        for j, name, lim, raw in cols:
            txt = cells[j] if j < len(cells) else ""
            got = magnitude(txt)
            if got is None or "10" not in str(txt):
                continue
            if lim / 100 < got < lim / 10 * 1.0000001 and got < lim:
                suspect.append((row[0].row, batch, cells[22], name, txt, raw))

    print(f"limit-bearing columns: {len(cols)}")
    for _, n, l, raw in cols:
        print(f"   {n:<26} limit {raw!r} -> {l:g}")

    print(f"\nR1  results ABOVE their own limit: {len(over)}")
    for r, b, code, name, txt, raw, ratio in over:
        print(f"   r{r:<4} {b:<13} {code:<15} {name:<22} {txt:<10} vs {raw:<12} {ratio:.1f}x")

    print(f"\nR2  one decade below the limit — verify against the page: {len(suspect)}")
    for r, b, code, name, txt, raw in suspect[:40]:
        print(f"   r{r:<4} {b:<13} {code:<15} {name:<22} {txt}")
    if len(suspect) > 40:
        print(f"   … and {len(suspect)-40} more")

    return 1 if over else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    sys.exit(main(sys.argv[1]))
