#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write the April-2026 IJZ release panel — microbiology and contaminants of the lots
sampled 21.04.2026 — into the owner's release register, in the shape of its existing IJZ rows.

    python3 deliverables/qc_gap_analysis/intake_IJZ0426_2026-09-16/apply_IJZ0426.py
        [--register PATH]   the register to extend  (default: …SUBLOT_2026-09-01.xlsx)
        [--out PATH]        where to write          (default: in place)

Idempotent: a certificate whose laboratory number is already in the register is skipped.

WHY. Eighteen certificates of the Institute of Public Health — nine IJZ-MB microbiology
reports 304/0548/26 … 312/0556/26 of 28.04.2026 and nine IJZ contaminant reports 2357/2026 …
2365/2026 of 29/30.04.2026 — are the RELEASE testing of the nine lots sampled on 21.04.2026
(CC112501, FB112501, GG112501, SCR112501, JD112501 and its starred second sample, FB012601/1,
GG012601*, JD012601*). Seventeen of them have been in the ingested corpus since 04.09.2026 and
all eighteen are on the Head of QC's own tracker; not one is a row of the release register,
which is the one source the certificates of quality are compiled from. So the eight release
certificates of quality print "not tested — no certificate covers it" for #9 microbiology,
#10 mycotoxins and #11 heavy metals, and take #12 from the owner's 09.09 resolution pass
alone — while the documents sit on file, dated five weeks before the certificates. It is the
gap the IJZ-MB intake of 16.09.2026 closed for the August campaign, one sampling earlier.

THE GATE. Every certificate carries two independent reads (build_reads.py: the eCoA runner's
A and B; for 310/0554/26, which the runner never read, the RAGflow OCR and the Head of QC's
own transcription). `load_reads()` compares them on every determination the register has a
column for and refuses to write anything if any certificate disagrees. Four disagreed on a
value and each was settled by a third read of the page on 16.09.2026 (`read_C`, sources in
reads_IJZ0426.json and the texts in third_reads/):

  * 307/0551/26, 304/0548/26, 305/0549/26 — the bile-tolerant gram-negative line, every time
    one read stopping at one bound where the page carries the range ("< 10³ и >10²"). The
    fuller read was right all three times: OI-36's class, with three more instances. The Head
    of QC's tracker holds two of these lines as "held for review"; the third read settles them.
  * 2361/2026 — the NUMBER of pesticide lines (29 against 28), every line н.д. on both reads;
    the four-page scan carries 29.

Everything else the two reads differ on is notation — a unit written or not, "отсутна" against
"отсуство" against "отсуства", a superscript against a caret — and `_fold` reads those as one
assertion, which is the standing vocabulary ruling of 11.09.2026, not a new judgement.

THE STARRED SAMPLE. 306/0550/26 and 2365/2026 print the batch "JD112501*". They go into the
JD112501 block beside ППК26065, exactly as the owner's own register already holds that
certificate, and testing_series.EXPERIMENTAL names them: real data, in every statistic, never
sourcing a certificate of quality (owner's ruling, 16.09.2026). GG012601* and JD012601* are
not that case — each is the only spelling its lot has, with its own P number — and their
documents go into the blocks the register labels GG012601 and JD012601, as the 227-К and the
IJZ-MB campaign certificates of the same lots already did.

THE ROWS. Into the block of the lot the page names, after its last real certificate row, in
date order: the IJZ-MB row with TAMC, TYMC, bile-tolerant GNB, Salmonella and E. coli as the
page prints them; the IJZ row with total aflatoxins, Pb, Cd, As, Hg and the pesticide panel —
"<2", the four metals as numbers, "N.D." for a panel that is н.д. on every line, and "not
tested" for aflatoxin B1 and ochratoxin A, which this laboratory's fluorometric total does
not report, all exactly as the register's existing IJZ rows of 2025 carry them. "/" in every
other column, the laboratory number in the register's own spelling, the date of issue and
"IPH — Institute of Public Health".
"""
import argparse
import copy
import json
import os
import re
import sys

import openpyxl
from openpyxl.utils import range_boundaries

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(GAP)), "ingestion", "common"))
sys.path.insert(0, os.path.join(GAP, "intake_IJZMB_2026-09-16"))
from batch_id import batch_key                              # noqa: E402
from apply_IJZMB import reg_value as mb_value, _fold as mb_fold, cu_from_list   # noqa: E402  one gate, one spelling

PLACEHOLDER = {"", "(not numbered)", "n/a"}
# the register's columns: J … N microbiology, O … V contaminants
COLS_MB = {"9.1": 10, "9.2": 11, "9.3": 12, "9.4": 13, "9.5": 14}
COLS_CHEM = {"10.2": 15, "10.1": 16, "10.3": 17, "11.1": 18, "11.2": 19, "11.3": 20, "11.4": 21, "12": 22}
NOT_REPORTED = {"10.1", "10.3"}      # the fluorometric total does not report them; the register says "not tested"
# an existing row of each shape is the model for the new ones
TEMPLATE = {"MB": "1157/2058/25", "CHEM": "752/2025"}


_SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def _notation(s):
    """One spelling for what the two reads spell two ways: a caret exponent becomes the
    superscript the page prints ('5,1×10^3' -> '5,1×10³'), and a bound is set off from its
    number ('<10³ и >10²' -> '< 10³ и > 10²'). Notation only; no value changes."""
    s = re.sub(r"10\^(\d)", lambda m: "10" + m.group(1).translate(_SUP), str(s or ""))
    s = re.sub(r"([<>])\s*(\d)", r"\1 \2", s)
    return s


def _fold_chem(v, det):
    s = str(v or "").strip().lower().replace(" ", "").replace(" ", "")
    for unit in ("µg/kg", "μg/kg", "mg/kg"):
        s = s.replace(unit, "")
    s = s.replace(",", ".")
    return s


def chem_value(v, det):
    """A contaminant result in the register's own spelling, as its IJZ rows of 2025 carry it."""
    if det in NOT_REPORTED:
        return "not tested"
    s = _fold_chem(v, det)
    if det == "10.2":
        if not s.startswith("<"):
            sys.exit("total aflatoxins %r is not a '< LOQ' result — not written" % v)
        return "<" + s[1:]
    if det == "12":
        if not re.match(r"^н\.д\.—\d+lines$", s):
            sys.exit("pesticide panel %r is not н.д. on every line — not written" % v)
        return "N.D."
    # the register's IJZ rows carry the metals as text with a decimal point ('0.016'), not as numbers
    if not re.match(r"^\d+\.\d+$", s):
        sys.exit("metal result %r is not a number — not written" % v)
    return s


def disagreements(m):
    """Where the two reads differ on a determination the register carries; [] when they agree.
    A determination settled by the third read of 16.09.2026 is not a disagreement."""
    out = []
    cols = COLS_MB if m["kind"] == "MB" else COLS_CHEM
    a, b, c = m.get("read_A") or {}, m.get("read_B") or {}, m.get("read_C") or {}
    fold = mb_fold if m["kind"] == "MB" else _fold_chem
    for det in cols:
        if det in c:
            continue
        x, y = a.get(det), b.get(det)
        if x is None and y is None:
            if det in NOT_REPORTED:
                continue
            out.append("#%s on neither read" % det)
            continue
        if x is None or y is None:
            out.append("#%s on one read only (A %r, B %r)" % (det, x, y))
            continue
        if fold(x, det) != fold(y, det):
            out.append("#%s A %r vs B %r" % (det, x, y))
    return out


def settled(m):
    """{det: printed} — read A where the reads agree, read C where it settles them."""
    cols = COLS_MB if m["kind"] == "MB" else COLS_CHEM
    a, b, c = m.get("read_A") or {}, m.get("read_B") or {}, m.get("read_C") or {}
    return {det: (c[det] if det in c else (a.get(det) if a.get(det) is not None else b.get(det))) for det in cols}


def load_reads():
    R = json.load(open(os.path.join(HERE, "reads_IJZ0426.json"), encoding="utf-8"))
    bad = {code: d for code, m in R.items() if (d := disagreements(m))}
    if bad:
        for code, d in bad.items():
            print("DISAGREE %s — %s" % (code, "; ".join(d)))
        sys.exit("%d certificate(s) where the two reads differ and no third read settles them "
                 "— nothing written" % len(bad))
    return R


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--register", default=os.path.join(GAP, "PP_Batch_Release_QC_Register_SUBLOT_2026-09-01.xlsx"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or a.register
    R = load_reads()
    wb = openpyxl.load_workbook(a.register)
    ws = wb["Batch Release QC"]
    present = {str(ws.cell(r, 23).value or "").strip() for r in range(6, ws.max_row + 1)}
    real = lambda r: str(ws.cell(r, 23).value or "").strip() not in PLACEHOLDER

    labels = []
    for r in range(6, ws.max_row + 1):
        v = ws.cell(r, 2).value
        if v:
            labels.append((r, str(v).strip(), str(ws.cell(r, 3).value or "").strip()))
        elif str(ws.cell(r, 1).value or "").upper() == "LEGEND":
            labels.append((r, None, None))
            break
    blocks = {}
    for i, (r, b, p) in enumerate(labels):
        if b:
            blk = {"first": r, "last": labels[i + 1][0] - 1, "label": b}
            blocks[batch_key(b)] = blk
            if p.startswith("P"):
                blocks.setdefault(batch_key(p), blk)
    tmpl = {kind: next(r for r in range(6, ws.max_row + 1) if str(ws.cell(r, 23).value or "") == code)
            for kind, code in TEMPLATE.items()}
    last_data = max(r for r in range(6, ws.max_row + 1) if ws.cell(r, 23).value not in (None, ""))

    def values(m):
        v = [None] * 26
        for c in range(5, 23):
            v[c - 1] = "/"
        res = settled(m)
        if m["kind"] == "MB":
            for det, col in COLS_MB.items():
                v[col - 1] = _notation(mb_value(res.get(det), det))
        else:
            for det, col in COLS_CHEM.items():
                v[col - 1] = chem_value(res.get(det), det)
        v[22], v[23], v[24], v[25] = m["cert_code"], m["date_of_issue"], m["laboratory"], "Open"
        return v

    def style_from(src, dst):
        for c in range(1, 27):
            s, d = ws.cell(src, c), ws.cell(dst, c)
            d.font, d.fill, d.border, d.alignment, d.number_format = (
                copy.copy(s.font), copy.copy(s.fill), copy.copy(s.border),
                copy.copy(s.alignment), s.number_format)
        ws.row_dimensions[dst].height = ws.row_dimensions[src].height

    # A row the owner opened for a certificate and never filled — the laboratory number in
    # column W, "/" in every result column, no date — is that certificate's row, not a
    # reason to skip it: it is filled in place. 305/0549/26 sits in the SCR112501 block that way.
    def empty_row(code):
        for r in range(6, ws.max_row + 1):
            if str(ws.cell(r, 23).value or "").strip() == code:
                return r if all(str(ws.cell(r, c).value or "/").strip() == "/" for c in range(5, 23)) else None
        return None

    todo, fill = [], []
    for code, m in sorted(R.items()):
        if code not in present:
            todo.append(m)
        elif (r := empty_row(code)) is not None:
            fill.append((r, m))
    for r, m in fill:
        for c, v in enumerate(values(m), 1):
            if c >= 5:
                ws.cell(r, c).value = v
    into, missing, via = [], [], []
    for m in todo:
        lot = (m.get("batch_on_page") or "").strip()
        cands = [lot, m.get("p_number"), cu_from_list(m.get("p_number") or "")]
        # a starred spelling — the second sample of JD112501, or the two lots the batch list
        # writes starred and the register labels without the star — finds its lot's block
        for c in list(cands):
            if c and re.search(r"[＊*]", c):
                cands.append(re.sub(r"[＊*]", "", c))
        blk = next((blocks[batch_key(c)] for c in cands if c and batch_key(c) in blocks), None)
        if blk is None:
            missing.append(m["cert_code"])
            continue
        if batch_key(lot) not in blocks:
            via.append("%s = %s" % (lot, blk["label"]))
        into.append((m, blk))
    if missing:
        sys.exit("no register block for %s — nothing written" % ", ".join(missing))

    # after the block's last real row; where a lot takes both rows, microbiology (28.04) above
    # the contaminants (29/30.04) — the later-dated row is inserted first and pushed down
    order = {"MB": 0, "CHEM": 1}
    inserts = sorted(((max(r for r in range(blk["first"], blk["last"] + 1) if real(r)) + 1, m)
                      for m, blk in into), key=lambda t: (-t[0], -order[t[1]["kind"]]))
    merged_below = [str(mr) for mr in ws.merged_cells.ranges if mr.min_row > last_data]
    for mr in merged_below:
        ws.unmerge_cells(mr)
    shifted = 0
    for at, m in inserts:
        ws.insert_rows(at)
        src = tmpl[m["kind"]]
        style_from(src + (1 if src >= at else 0), at)
        for c, v in enumerate(values(m), 1):
            ws.cell(at, c).value = v
        for k in tmpl:
            if tmpl[k] >= at:
                tmpl[k] += 1
        shifted += 1
    last_data += shifted
    for mr in merged_below:
        c1, r1, c2, r2 = range_boundaries(mr)
        ws.merge_cells(start_row=r1 + shifted, start_column=c1, end_row=r2 + shifted, end_column=c2)
    ws.auto_filter.ref = "A4:Z%d" % last_data
    wb.save(out)
    print("%s: %d row(s) into existing blocks, 0 new blocks, %d empty row(s) filled in place (%s), "
          "%d already present, legend shifted by %d"
          % (os.path.basename(out), shifted, len(fill), ", ".join(m["cert_code"] for _, m in fill) or "—",
             len(R) - len(todo) - len(fill), shifted))
    if via:
        print("block found through the P number, the batch list or the star-stripped spelling: "
              + ", ".join(sorted(set(via))))
    exp = [m["cert_code"] for m, _ in into if m.get("experimental")]
    if exp:
        print("starred second sample of JD112501 written into the JD112501 block, experimental (testing_series): "
              + ", ".join(exp))


if __name__ == "__main__":
    main()
