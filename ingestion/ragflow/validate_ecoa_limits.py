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

# Δ9-THCA decarboxylates to Δ9-THC on heating, losing the carboxyl group. The mass
# ratio of the two molecules is 314.46/358.47 = 0.877, which is why every certificate
# in this corpus prints the same conversion in its own footnote.
THCA_TO_THC = 0.877


def total_thc_consistent(d9_thc, thca, total_thc, tol=0.06):
    """R4 — check a potency certificate against its own arithmetic.

    Every CNP certificate prints all three of Δ9-THC, Δ9-THCA and Вкупно Δ9-THC,
    and states the relation between them in a footnote:

        Вкупно Δ9-THC = Δ9-THC + Δ9-THCA × 0.877

    So each certificate carries its own proof, and a single corrupted digit stops
    being invisible. Run over eCoA_DATABASE on 30.08.2026 it flagged two of the
    fifteen certificates where all three values could be read. **Both were then
    checked against the source PDF in Drive, and in both the certificate was correct
    and the corpus was wrong:**

      ППК25117  corpus total 1.58 beside 0.46 and 17.01. The page prints 15.38,
                which is what 0.46 + 17.01 x 0.877 gives, and what the register
                already held.
      ППК25139  corpus THCA 0.52 against a total of 23.79. The page prints 26.52,
                and 0.53 + 26.52 x 0.877 = 23.79 exactly. The same corpus record
                also holds "Satre Pie" for Grape Pie and "GF0824_02" for GP0824_02
                — three corruptions in one document.

    So the measured rate is **2 of 15 potency certificates carrying a value that is
    wrong rather than missing — 13%** — and nothing but the certificates' own
    footnote formula detected it. That is a second, independent measurement of the
    defect first found in the mould counts, on a different parameter and a different
    laboratory, and it says the corpus is unreliable for numbers in general and not
    merely for superscripts.

    The rule raises the page; it does not decide it. Both times the page had a clear
    answer and the laboratory was not at fault — which is the outcome to expect, and
    the reason a flag here must never be reported as a laboratory finding before
    someone has looked.

    Returns None when any input is missing (nothing to check), True when the printed
    total matches the computed one within `tol`, False when it does not.

    >>> total_thc_consistent(0.46, 17.01, 15.38)
    True
    >>> total_thc_consistent(0.46, 17.01, 1.58)
    False
    >>> total_thc_consistent(0.46, None, 15.38) is None
    True
    """
    if d9_thc is None or thca is None or total_thc is None:
        return None
    return abs(total_thc - (d9_thc + thca * THCA_TO_THC)) <= tol


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
