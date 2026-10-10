#!/usr/bin/env python3
"""Write the IJZ-MB campaign microbiology certificates of 25/26.08.2026 into the owner's
release register, in the shape of the existing IJZ-MB rows.

    python3 deliverables/qc_gap_analysis/intake_IJZMB_2026-09-16/apply_IJZMB.py
        [--register PATH]   the register to extend  (default: …SUBLOT_2026-09-01.xlsx)
        [--out PATH]        where to write          (default: in place)

Idempotent: a certificate whose code is already in the register is skipped.

WHY. The thirty certificates (laboratory numbers 536/1067/26 … 565/1096/26, received
25/26.08.2026, issued 31.08 and 01.09.2026) have been testing instances on the tracker
since 04.09.2026 and were never rows of the release register — which is the one source
the certificates of quality are compiled from. OI-34 recorded that; the sweep of
16.09.2026 measured it: **24 certificates of quality print microbiology that a newer
certificate for the same lot contradicts**, twelve of them reissues, and the gap is not
small — P050012's certificate prints TAMC 2.1 × 10⁴ where the campaign certificate for
the same lot reads < 10. A reissue of a retest campaign must print the campaign's
microbiology; this intake is what makes it.

THE GATE. Each certificate carries two independent reads (the eCoA runner's A and B,
ingested 04.09.2026) and a page in the owner's eCoA_DATABASE whose SHA-256 and
pixel verification are in tracker/split_manifest_IJZ-MB_2026-09-01.csv. `load_reads()`
compares the two reads on all five release determinations and refuses to write on any
disagreement. Four certificates disagreed — 537/1068/26, 542/1073/26, 544/1075/26 and
547/1078/26, every one on the bile-tolerant gram-negative line, one read stopping at
"< 10²" where the other carried the full range "< 10² и > 10" — and each was settled by a
third read of the page on 16.09.2026 (`read_C`): the fuller read was right all four times,
which is the defect class OI-36 records. Four more differed only in how the laboratory
spells absence (Отсутна, Отсуства, Отсуствa, Отсуствува); `_fold` reads those as one
assertion, which is the standing vocabulary ruling, not a new judgement.

WHAT IS HELD BACK. 548/1079/26 is filed under P050192 (BSS052501, Blue Sunset Sherbet)
because its typed serial reads "PO50192", but the page prints the strain **Sleepy Joe**
and carries a handwritten "P060192" — and P060192 is SJ112501, whose strain the register
gives as Sleepy Joy. The lot is the Head of QC's to settle (OI-37), so this certificate
is NOT written: a microbiology result on the wrong lot's certificate is worse than a
missing one.

THE ROW. Into the block of the lot the file names, after its last real certificate row:
TAMC, TYMC, bile-tolerant GNB, Salmonella and E. coli as the page prints them, "/" in
every column the certificate does not report, the laboratory number in the register's own
spelling (548/1079/26), the date of issue and "IPH — Institute of Public Health". The
expanded panel this laboratory also reports — P. aeruginosa and S. aureus, absent on all
thirty — has no column in the owner's register and is not written; it is recorded in
reads_IJZMB.json and in OI-13, which said until today that the panel had never been run.
"""
import argparse
import copy
import csv
import json
import os
import re
import sys

import openpyxl
from openpyxl.utils import range_boundaries

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(GAP)), "ingestion", "common"))
from batch_id import batch_key  # noqa: E402

PLACEHOLDER = {"", "(not numbered)", "n/a"}
# the five the owner's register has a column for: J … N
COLS = {"9.1": 10, "9.2": 11, "9.3": 12, "9.4": 13, "9.5": 14}
# the lot question of 16.09.2026 (OI-37): held until the Head of QC rules
HELD = {"548/1079/26": "the page prints the strain Sleepy Joe and a handwritten P060192, "
                       "while the typed serial reads PO50192 (P050192, Blue Sunset Sherbet)"}


def reg_value(v, det):
    """A printed result in the register's own spelling, as its IJZ-MB rows carry it."""
    s = str(v or "").strip()
    if det in ("9.4", "9.5"):
        return "Одговара (absent)"
    s = s.replace(" CFU/g", "").replace("CFU/g", "").strip()
    s = s.replace(" x ", "×").replace(" х ", "×").replace(" и ", " и ")
    return s


def disagreements(m):
    """Where the two reads differ on a determination the register carries; [] when they agree.
    A determination settled by the third read of 16.09.2026 is not a disagreement."""
    out = []
    a, b, c = m.get("read_A") or {}, m.get("read_B") or {}, m.get("read_C") or {}
    for det in COLS:
        if det in c:
            continue
        x, y = a.get(det), b.get(det)
        if x is None and y is None:
            out.append("#%s on neither read" % det)
            continue
        if x is None or y is None:
            out.append("#%s on one read only (A %r, B %r)" % (det, x, y))
            continue
        if _fold(x, det) != _fold(y, det):
            out.append("#%s A %r vs B %r" % (det, x, y))
    return out


def _fold(v, det):
    """Enough normalisation to tell a real disagreement from a notation one."""
    s = str(v or "").lower().replace(" ", "").replace(" ", "")
    s = s.replace("cfu/g", "").replace("^", "").replace(",", ".")
    for a, b in (("⁰", "0"), ("¹", "1"), ("²", "2"), ("³", "3"), ("⁴", "4"), ("⁵", "5")):
        s = s.replace(a, b)
    s = s.replace("x10", "e").replace("х10", "e").replace("×10", "e")
    if det in ("9.4", "9.5"):
        # every spelling of absence this laboratory uses: отсутна, отсуства, отсуствa,
        # отсуствува — and the verdict Одговара, which in these two columns says the same
        return ("absent" if s.startswith(("отсут", "отсуств", "одговара", "absent", "negative"))
                else s)
    return s


def cu_from_list(p):
    """The cultivation batch the Head of QC's batch list gives for a P lot, or ''."""
    with open(os.path.join(GAP, "tracker", "batch_dates.csv"), encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            if (r.get("p_batch") or "").strip() == p:
                return (r.get("cu_batch") or "").strip()
    return ""


def cu_from_file(name):
    """The cultivation batch the scan's own file name carries:
    310826_547-1078-26_IJZ-MB_J31112501-P060202.pdf -> J31112501."""
    m = re.match(r"^\d{6}_[^_]+_IJZ-MB_(.+?)(?:-P\d{6})?\.pdf$", str(name or ""))
    return (m.group(1).strip() if m else "")


def load_reads():
    R = json.load(open(os.path.join(HERE, "reads_IJZMB.json"), encoding="utf-8"))
    bad = {}
    for code, m in R.items():
        d = disagreements(m)
        if d:
            bad[code] = d
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
    # an existing IJZ-MB row is the model for the new ones
    tmpl_row = next(r for r in range(6, ws.max_row + 1)
                    if str(ws.cell(r, 23).value or "") == "1157/2058/25")
    last_data = max(r for r in range(6, ws.max_row + 1) if ws.cell(r, 23).value not in (None, ""))

    def values(m):
        v = [None] * 26
        for c in range(5, 23):
            v[c - 1] = "/"
        for det, col in COLS.items():
            v[col - 1] = reg_value((m["results"] or {}).get(det), det)
        v[22], v[23], v[24], v[25] = m["cert_code"], m["date_of_issue"], m["laboratory"], "Open"
        return v

    def style_from(src, dst):
        for c in range(1, 27):
            s, d = ws.cell(src, c), ws.cell(dst, c)
            d.font, d.fill, d.border, d.alignment, d.number_format = (
                copy.copy(s.font), copy.copy(s.fill), copy.copy(s.border),
                copy.copy(s.alignment), s.number_format)
        ws.row_dimensions[dst].height = ws.row_dimensions[src].height

    todo, held, missing, into = [], [], [], []
    for code, m in sorted(R.items()):
        if code in HELD:
            held.append(code)
            continue
        if code in present:
            continue
        todo.append(m)
    via_list = []
    for m in todo:
        lot = (m.get("batch_canonical") or "").strip()
        cands = [lot, m.get("batch_printed")]
        # a block keyed by the cultivation batch whose label row carries no P number:
        # the Head of QC's batch list names it, and so does the scan's own file name
        for extra in (cu_from_list(lot), cu_from_file(m.get("file"))):
            if extra:
                cands.append(extra)
                # the two starred lots: the batch list writes GG012601＊ / JD012601＊ and the
                # register block is labelled without the star. Using it is not a ruling on
                # OI-28 — the 227-К certificate of the SAME lot (227-21-К/26 for P060302,
                # 227-15-К/26 for P060312) already sits in that block, placed by the intake
                # of 15.09.2026; this puts the lot's microbiology beside its own potency.
                if re.search(r"[＊*]", extra):
                    cands.append(re.sub(r"[＊*]", "", extra))
        blk = next((blocks[batch_key(c)] for c in cands if c and batch_key(c) in blocks), None)
        if blk is not None and batch_key(lot) not in blocks:
            via_list.append("%s = %s" % (lot, blk["label"]))
        if blk is None:
            missing.append(m["cert_code"])
            continue
        into.append((m, blk))
    if missing:
        sys.exit("no register block for %s — nothing written" % ", ".join(missing))

    inserts = sorted(((max(r for r in range(blk["first"], blk["last"] + 1) if real(r)) + 1, m)
                      for m, blk in into), key=lambda t: -t[0])
    merged_below = [str(mr) for mr in ws.merged_cells.ranges if mr.min_row > last_data]
    for mr in merged_below:
        ws.unmerge_cells(mr)
    for at, m in inserts:
        ws.insert_rows(at)
        style_from(tmpl_row + (1 if tmpl_row >= at else 0), at)
        for c, v in enumerate(values(m), 1):
            ws.cell(at, c).value = v
    last_data += len(inserts)
    for mr in merged_below:
        c1, r1, c2, r2 = range_boundaries(mr)
        ws.merge_cells(start_row=r1 + len(inserts), start_column=c1,
                       end_row=r2 + len(inserts), end_column=c2)
    ws.auto_filter.ref = "A4:Z%d" % last_data
    wb.save(out)
    print("%s: %d row(s) into existing blocks, 0 new blocks, %d already present, legend shifted by %d"
          % (os.path.basename(out), len(inserts), len(R) - len(todo) - len(held), len(inserts)))
    if via_list:
        print("block found through the batch list or the file name (label row carries no P lot): "
              + ", ".join(sorted(set(via_list))))
    for code in held:
        print("HELD %s — %s (OI-37)" % (code, HELD[code]))


if __name__ == "__main__":
    main()
