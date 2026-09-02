#!/usr/bin/env python3
"""Build CoQ_Analysis_Master_v8.xlsx — v8's readings in the block layout, criteria enforced.

This is the convergence of the two lines of work:

  from v8 (PR #17, built from the eCoA database on the ingestion host)
      the readings themselves — verbatim from the certificate, two independent reads,
      derived cannabinoid totals, the per-compound pesticide panel read as one result,
      and the vocabulary that never calls an accredited certificate silent:
      "held for review", "not on this certificate", "not ingested".
  from v7 (this line)
      the layout the Head of QC specified — one two-row block per TESTING INSTANCE —
      the acceptance criteria in header row 3 and enforced per Ph. Eur. 5.1.4, the lot
      join on the P batch, the merge of an original and a re-analysis row into one lot,
      and the Credit Audit.

Merge rule, and it matters: v8's reading wins where it has one, because it is verbatim
from the page. Where v8 reports no value but the desk holds one from the release register
or a page read, THE DESK VALUE STANDS and is marked ᴿ — "not ingested" is a statement
about v8's corpus, not about the certificate, and a verified result is never dropped by a
rebuild. Checked before adopting: of the values both hold, 754 agree once decimal commas,
unit suffixes and Cyrillic connectives are normalised, and none contradict.

The block rule, per the specification:

  * one TESTING INSTANCE = one block of two rows, and a batch holds as many blocks as it
    has testing instances (the largest number of certificates credited to any one of its
    parameters), so a parameter tested twice on two dates gets two blocks, never two text
    lines inside one; the batch identity and STATUS are merged down all of its blocks and
    the whole batch is boxed with a thick border;
  * single-value parameters (#1–#8, #12) occupy Result | eCOA ref | ✓/✗, each cell
    merged vertically across the two rows;
  * #9 Microbiology, #10 Mycotoxins and #11 Heavy metals give each sub-determination
    its own column: the top row carries the sub-results, the bottom row carries the
    certificate reference(s) merged across them;
  * a parameter's certificates are taken in ascending date order: the n-th certificate
    fills the n-th block, so a row of blocks reads across as "everything known from the
    n-th round of testing";
  * acceptance criteria live in header row 3 and are enforced: a result that provably
    exceeds its criterion is printed red and bold and is named in the batch's STATUS.

Sources: `tracker_data.py` (the desk's values, the owner's certificate credits).
"""
import collections, importlib.util, math, os, re, sys

import openpyxl
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("tracker_data", os.path.join(HERE, "tracker_data.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)

SRC = os.path.join(HERE, "CoQ_Analysis_Master_v6.xlsx")
V8VALS = os.path.join(HERE, "v8_values.json")
OUT = os.path.join(HERE, "CoQ_Analysis_Master_v8.xlsx")
SHEET = "CoQ Parameter Tracker v8"
BUILT = "02.09.2026"
import json  # noqa: E402
STATUS_PARTIAL_MAX = 3          # 1–3 without a release result → ⚠ PARTIAL; ≥4 → ✗

# --------------------------------------------------------------------------- palette
NAVY = "1F3864"; SUBHDR = "FFF2CC"; GREY = "EFEFEF"
FILL = {"green": "C6EFCE", "orange": "FCE5CD", "amber": "FDE9D9", "red": "F4CCCC", "extra": "EDEDED"}
GLYPHFILL = {"green": "6AA84F", "orange": "E69138", "amber": "F6B26B", "red": "CC0000", "extra": "A6A6A6"}
STATUSFILL = {"green": "38761D", "orange": "E69138", "red": "CC0000"}
RED = "9C0006"
F7 = Font(name="Calibri", size=7)
F7B = Font(name="Calibri", size=7, bold=True)
F7R = Font(name="Calibri", size=7, bold=True, color=RED)
F7U = Font(name="Calibri", size=7, bold=True, color="B45F06")
FBAD = Font(name="Calibri", size=7, bold=True, color=RED)
F6 = Font(name="Calibri", size=6)
F6I = Font(name="Calibri", size=6.5, italic=True, color="595959")
FW = Font(name="Calibri", size=8, bold=True, color="FFFFFF")
FWS = Font(name="Calibri", size=7, bold=True, color="FFFFFF")
FSUB = Font(name="Calibri", size=7, bold=True)
CEN = Alignment(horizontal="center", vertical="center", wrap_text=True)
TOPC = Alignment(horizontal="center", vertical="top", wrap_text=True)
thin = Side(style="thin", color="BFBFBF")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
THICK = Side(style="medium", color="000000")
MED = Side(style="thin", color="404040")


def put(ws, r, c, v, font=F7, fill=None, al=CEN):
    cell = ws.cell(r, c, v)
    cell.font, cell.alignment, cell.border = font, al, BOX
    if fill:
        cell.fill = PatternFill("solid", fgColor=fill)
    return cell


def fill_range(ws, r1, c1, r2, c2, colour):
    pf = PatternFill("solid", fgColor=colour)
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            ws.cell(r, c).fill = pf


def outline(ws, r1, c1, r2, c2, side):
    """Draw one rectangle without disturbing the inner borders."""
    for c in range(c1, c2 + 1):
        for r, edge in ((r1, "top"), (r2, "bottom")):
            b = ws.cell(r, c).border
            ws.cell(r, c).border = Border(left=b.left, right=b.right,
                                          top=side if edge == "top" else b.top,
                                          bottom=side if edge == "bottom" else b.bottom)
    for r in range(r1, r2 + 1):
        for c, edge in ((c1, "left"), (c2, "right")):
            b = ws.cell(r, c).border
            ws.cell(r, c).border = Border(top=b.top, bottom=b.bottom,
                                          left=side if edge == "left" else b.left,
                                          right=side if edge == "right" else b.right)


def nlines(text, width):
    per = max(1, int(width * 1.25))
    return sum(max(1, math.ceil(len(ln) / per)) for ln in str(text or "").split("\n")) or 1


# --------------------------------------------------------------------------- data
VAL, INH, STAB, STRAIN, DET = T.load_desk()
batches, index_rows = T.load_owner()

# Every document the index holds for a batch, with the parameters it covers. A document
# that covers a parameter but is not credited to it on the owner's tracker is still a
# testing instance and is shown — greyed, marked "•", and labelled "not credited" — but it
# is NOT counted as coverage: what discharges a parameter stays the owner's judgement.
# The index is joined on the P BATCH, never on the CU code: four CU codes carry two
# tracker rows (an original and the August re-analysis) and three lots share a CU with
# no code of their own, so a CU join pulls another lot's certificates into the batch.
COVERS = {}
INDEX_DOCS = collections.defaultdict(list)
for _r in index_rows:
    _cov = {int(x[1:]) for x in re.findall(r"#\d+", _r["params"])}
    _k = _r["p"] or re.sub(r"[＊*]", "", _r["cu"])
    INDEX_DOCS[_k].append((_r["code"], _r["date"], _r["lab"], _cov))
    COVERS[(_k, T.nkey(_r["code"]))] = _cov


# v8's readings, keyed on the certificate. Extracted from the v8 workbook of PR #17,
# which was built from the eCoA database; the map is committed so this build is
# reproducible without the database, which lives on the ingestion host.
_V8 = json.load(open(V8VALS))
SILENT = ("held for review", "not on this certificate", "not ingested", "n.r.")
V8VAL, V8SILENT = collections.defaultdict(dict), collections.defaultdict(dict)
_bycode = collections.defaultdict(set)
for _k in _V8:
    _bycode[_k.split("|", 1)[1]].add(_k)
for _k, _d in _V8.items():
    _cu, _ck = _k.split("|", 1)
    for _no, _v in _d.items():
        (V8SILENT if _v in SILENT else V8VAL)[(_cu, _ck)][_no] = _v
        if len(_bycode[_ck]) == 1:                    # the code identifies one lot only
            (V8SILENT if _v in SILENT else V8VAL)[("*", _ck)][_no] = _v


def v8_of(code, cu, table):
    ck = T.nkey(code)
    return table.get((cu, ck)) or table.get(("*", ck)) or {}


def was_read(code, lab, cu):
    """True when the desk holds any value from this document. A credited document with no
    value at all was never read into the corpus — a different problem from a document that
    was read and simply does not report the parameter."""
    if VAL.get(T.nkey(code)):
        return True
    return T.kind_of(code, lab, STAB) == "In-house" and bool(INH.get(T.cu_key(cu)))


def silence_reason(code, lab, cu, no=None):
    """v8's own words when it has them; otherwise derived from the desk."""
    if no is not None:
        said = silent_as(code, cu, no)
        if said:
            return said
    said = {v for d in (v8_of(code, cu, V8SILENT),) for v in d.values()}
    if said and len(said) == 1:
        return said.pop()
    return "not on this certificate" if was_read(code, lab, cu) else "not ingested"


def scope_of(b_or_key, code):
    key = b_or_key if isinstance(b_or_key, str) else join_key(b_or_key)
    return COVERS.get((key, T.nkey(code)))


def join_key(b):
    """The lot: its P batch, or its CU code when no P batch is assigned. The owner marks
    some CU codes with an asterisk; the index does not, so the mark is folded away."""
    return re.sub(r"[＊*]", "", b["cu"]) if b["p"].startswith("N/A") else b["p"]


# One batch is one lot: tracker rows that share a CU and a P batch are the same lot split
# by the owner across an original row and a re-analysis row, which the flat layout forced.
# The block layout carries both rounds, so they are merged back into a single batch.
_merged, _by = [], {}
for _b in batches:
    _k = (_b["cu"], _b["p"])
    if _k in _by:
        _t = _by[_k]
        for _n in range(1, 13):
            _have = {T.nkey(_x[0]) for _x in _t["docs"][_n]}
            for _d in _b["docs"][_n]:
                if T.nkey(_d[0]) not in _have:
                    _t["docs"][_n].append(_d)
                    _have.add(T.nkey(_d[0]))
        _t["labs"] = sorted(set(_t["labs"]) | set(_b["labs"]))
        _t["rows"] = _t.get("rows", 1) + 1
    else:
        _by[_k] = _b
        _merged.append(_b)
print(f"tracker rows {len(batches)} → batches {len(_merged)} "
      f"({sum(1 for b in _merged if b.get('rows', 1) > 1)} lots had an original and a re-analysis row)")
batches = _merged


def instances(b, pno):
    """(code, date, lab, credited) for every testing instance of this parameter, in date order."""
    credited = [(c, d, l) for c, d, l in b["docs"][pno]]
    seen = {T.nkey(c) for c, d, l in credited}          # fold: the tracker and the index
    out = [(c, d, l, True) for c, d, l in credited]     # spell the same code differently
    for c, d, l, cov in INDEX_DOCS.get(join_key(b), []):
        if T.nkey(c) in seen:
            continue
        reports = any((VAL.get(T.nkey(c)) or {}).get(no) for no in T.GROUPS[pno])
        if pno in cov or reports:
            out.append((c, d, l, False))
            seen.add(T.nkey(c))
    return sorted(out, key=lambda x: (T.date_key(x[1]), x[0]))


def desk_values(code, lab, cu, scope=None):
    """What this document reports. For an in-house record the desk keeps its values under
    the batch, not the document, so the fallback is restricted to the parameters the index
    says the document covers — otherwise one Report of Analysis would claim every in-house
    determination the batch holds."""
    src = VAL.get(T.nkey(code))
    if not src and T.kind_of(code, lab, STAB) == "In-house":
        src = INH.get(T.cu_key(cu))
        if src is not None and scope is not None:
            src = {no: v for no, v in src.items() if int(str(no).split(".")[0]) in scope}
    return src or {}


REGISTER_ONLY = set()          # (code, det) the desk holds and v8 does not — marked ᴿ


def values_of(code, lab, cu, scope=None):
    """v8's reading where it has one; the desk's verified value where it does not."""
    out = dict(v8_of(code, cu, V8VAL))
    for no, v in desk_values(code, lab, cu, scope).items():
        if no not in out:
            out[no] = f"{v} ᴿ"        # ᴿ: the release register or a page read, not v8's extraction
            REGISTER_ONLY.add((T.nkey(code), no))
    return out


def silent_as(code, cu, no):
    """What v8 says about a determination it holds no value for."""
    return v8_of(code, cu, V8SILENT).get(no)


def ecoa_line(code, date, lab):
    return f"{code}, ({date}) [{lab}]"


# --------------------------------------------------------------------------- layout
cols, col = [], 4
for p in T.PARAMS:
    p["start"] = col
    subs = T.GROUPS[p["n"]]
    if len(subs) > 1:
        p["subs"] = subs
        for no in subs:
            cols.append((col, p, no)); col += 1
    else:
        p["subs"] = None
        cols.append((col, p, "result")); col += 1
        cols.append((col, p, "ecoa")); col += 1
    cols.append((col, p, "check")); col += 1
    p["end"] = col - 1
    p["width"] = p["end"] - p["start"] + 1
LAST = col - 1

wb = openpyxl.load_workbook(SRC)
if SHEET in wb.sheetnames:
    wb.remove(wb[SHEET])
flat = wb["CoQ Parameter Tracker"]
flat.title = "CoQ Parameter Tracker (flat)"
ws = wb.create_sheet(SHEET, wb.sheetnames.index("Batch Coverage") + 1)

# ---- header rows 1–4
put(ws, 1, 1, "BATCH IDENTIFICATION", FW, NAVY)
ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=3)
g, gstart = None, 0
for i, p in enumerate(T.PARAMS):
    if p["group"] != g:
        if g:
            ws.merge_cells(start_row=1, start_column=gstart, end_row=1, end_column=p["start"] - 1)
            put(ws, 1, gstart, g, FW, NAVY)
        g, gstart = p["group"], p["start"]
    if i == len(T.PARAMS) - 1:
        ws.merge_cells(start_row=1, start_column=gstart, end_row=1, end_column=p["end"])
        put(ws, 1, gstart, g, FW, NAVY)
for c, t in ((1, "CU Batch"), (2, "P Batch"), (3, "STATUS")):
    ws.merge_cells(start_row=2, start_column=c, end_row=4, end_column=c)
    put(ws, 2, c, t, FWS, NAVY)
for p in T.PARAMS:
    ws.merge_cells(start_row=2, start_column=p["start"], end_row=2, end_column=p["end"])
    put(ws, 2, p["start"], p["title"] + "\n" + p["method"], FW, NAVY)
    if p["subs"]:
        for i, no in enumerate(p["subs"]):
            put(ws, 3, p["start"] + i, "A.C.: " + T.CRIT[no], F6I, GREY)
            put(ws, 4, p["start"] + i, T.SUB[no], FSUB, SUBHDR)
        put(ws, 3, p["end"], "", F6I, GREY)
    else:
        put(ws, 3, p["start"], "A.C.: " + T.CRIT[str(p["n"])], F6I, GREY)
        put(ws, 3, p["start"] + 1, "", F6I, GREY)
        ws.merge_cells(start_row=3, start_column=p["start"], end_row=3, end_column=p["start"] + 1)
        put(ws, 4, p["start"], "Result (as reported)", FSUB, SUBHDR)
        put(ws, 4, p["start"] + 1, "eCOA ref, (date) [Lab] — one certificate per line", FSUB, SUBHDR)
    put(ws, 3, p["end"], "", F6I, GREY)
    put(ws, 4, p["end"], "✓/✗", FSUB, SUBHDR)
for h, height in ((1, 16), (2, 30), (3, 26), (4, 24)):
    ws.row_dimensions[h].height = height

# ---- body: one block of two rows per testing instance, batches boxed together
row = 5
stats = collections.Counter()
oos_rows = []
audit = []
BLANK = "FFFFFF"
for b in batches:
    docs = {p["n"]: instances(b, p["n"]) for p in T.PARAMS}
    K = max([len(v) for v in docs.values()] + [1])
    extra = len({(x[0], x[1]) for v in docs.values() for x in v if not x[3]})
    first, last = row, row + 2 * K - 1

    for cidx, v, font in ((1, b["cu"], FWS), (2, b["p"], FWS), (3, None, FWS)):
        if cidx != 3:
            ws.merge_cells(start_row=first, start_column=cidx, end_row=last, end_column=cidx)
            put(ws, first, cidx, v, font, NAVY)
            fill_range(ws, first, cidx, last, cidx, NAVY)

    no_cert = cert_no_result = missing = 0
    oos_list, und_list, stab_list = [], [], []

    def verdict(det_no, release_vals, stability_vals, label):
        """Judge release results only; a stability exceedance is reported apart."""
        bad = any(T.over_limit(det_no, x) for x in release_vals)
        und = (not bad) and any(T.undetermined(det_no, x) for x in release_vals)
        if bad and label not in oos_list:
            oos_list.append(label)
        elif und and label not in und_list:
            und_list.append(label)
        if any(T.over_limit(det_no, x) for x in stability_vals) and label not in stab_list:
            stab_list.append(label)
        return F7R if bad else (F7U if und else F7B)

    # the batch-level state of each parameter, from all of its certificates together
    pstate = {}
    for p in T.PARAMS:
        rel = stab = credited = 0
        for code, date, lab, is_cred in docs[p["n"]]:
            if not is_cred:
                continue
            vals = values_of(code, lab, b["cu"], scope_of(b, code))
            if any(vals.get(no) for no in T.GROUPS[p["n"]]):
                if T.nkey(code) in STAB:
                    stab += 1
                else:
                    rel += 1
            else:
                credited += 1
        if rel:
            st = "green"
        elif stab:
            st = "orange"
        elif credited:
            st = "amber"; cert_no_result += 1
        else:
            st = "red"; no_cert += 1
        if st != "green":
            missing += 1
        stats[st] += 1
        pstate[p["n"]] = st
        # the verdict is the batch's, judged over every certificate it holds
        for no in T.GROUPS[p["n"]]:
            relv, stabv = [], []
            for code, date, lab, is_cred in docs[p["n"]]:
                if not is_cred:
                    continue
                v = values_of(code, lab, b["cu"], scope_of(b, code)).get(no)
                if v:
                    (stabv if T.nkey(code) in STAB else relv).append(v)
            verdict(no, relv, stabv, f"#{p['n']}" + (" " + T.SUB[no] if len(T.GROUPS[p['n']]) > 1 else ""))

    for i in range(K):
        top, bot = first + 2 * i, first + 2 * i + 1
        top_lines = bot_lines = 1
        for p in T.PARAMS:
            dlist = docs[p["n"]]
            here = dlist[i] if i < len(dlist) else None
            credited_here = [x for x in dlist if x[3]]
            if here is None:
                state = "red" if (not credited_here and i == 0) else "none"
            else:
                code, date, lab, is_cred = here
                vals = values_of(code, lab, b["cu"], scope_of(b, code))
                has = any(vals.get(no) for no in T.GROUPS[p["n"]])
                if not is_cred:
                    state = "extra"
                else:
                    state = ("orange" if T.nkey(code) in STAB else "green") if has else "amber"
                    if not has:
                        audit.append((b["cu"], b["p"], code, date, lab, p["n"], p["title"],
                                      silence_reason(code, lab, b["cu"], T.GROUPS[p["n"]][0])))
            fill = FILL[state] if state in FILL else BLANK
            glyph = {"green": "✓", "orange": "✓", "amber": "✗", "red": "✗", "extra": "•"}.get(state, "")
            gfill = GLYPHFILL[state] if state in GLYPHFILL else BLANK
            ref = (f"{code}, ({date}) [{lab}]" + ("" if here[3] else " · on file, not credited")) if here \
                else ("— no certificate —" if state == "red" else "")

            if p["subs"]:
                for j, no in enumerate(p["subs"]):
                    if here:
                        v = values_of(here[0], here[2], b["cu"], scope_of(b, here[0])).get(no)
                        blank = not any(values_of(here[0], here[2], b["cu"], scope_of(b, here[0])).get(x)
                                        for x in p["subs"])
                        cell_v = v or (silence_reason(here[0], here[2], b["cu"], no) if blank and j == 0
                                       else ("" if blank else "n.r."))
                        font = F7R if T.over_limit(no, v or "") else (F7U if T.undetermined(no, v or "") else F7B)
                    else:
                        cell_v = "— MISSING —" if state == "red" else ""
                        font = FBAD if state == "red" else F7
                    put(ws, top, p["start"] + j, cell_v, font, fill)
                    top_lines = max(top_lines, nlines(cell_v, 8.5))
                ws.merge_cells(start_row=bot, start_column=p["start"], end_row=bot, end_column=p["end"] - 1)
                put(ws, bot, p["start"], ref, F6, fill, TOPC)
                fill_range(ws, bot, p["start"], bot, p["end"] - 1, fill)
                bot_lines = max(bot_lines, nlines(ref, 8.6 * (len(p["subs"]) - 1) + 21))
            else:
                no = str(p["n"])
                if here:
                    v = values_of(here[0], here[2], b["cu"], scope_of(b, here[0])).get(no)
                    cell_v = v or silence_reason(here[0], here[2], b["cu"], no)
                    font = F7R if T.over_limit(no, v or "") else (F7U if T.undetermined(no, v or "") else F7B)
                else:
                    cell_v = "— MISSING —" if state == "red" else ""
                    font = FBAD if state == "red" else F7
                ws.merge_cells(start_row=top, start_column=p["start"], end_row=bot, end_column=p["start"])
                put(ws, top, p["start"], cell_v, font, fill)
                ws.merge_cells(start_row=top, start_column=p["start"] + 1, end_row=bot, end_column=p["start"] + 1)
                put(ws, top, p["start"] + 1, ref, F6, fill, TOPC)
                fill_range(ws, top, p["start"], bot, p["start"] + 1, fill)
                need = max(nlines(cell_v, 10), nlines(ref, 21))
                if need > top_lines + bot_lines:
                    bot_lines = need - top_lines

            ws.merge_cells(start_row=top, start_column=p["end"], end_row=bot, end_column=p["end"])
            put(ws, top, p["end"], glyph, FWS, gfill, CEN)
            fill_range(ws, top, p["end"], bot, p["end"], gfill)

        ws.row_dimensions[top].height = max(14, 9.0 * top_lines + 3)
        ws.row_dimensions[bot].height = max(13, 9.0 * bot_lines + 3)
        if i:                                   # a hairline between testing instances
            outline(ws, top, 1, bot, LAST, MED)

    if missing == 0:
        st, colour = "✓ COMPLETE", STATUSFILL["green"]
    else:
        glyph = "⚠" if missing <= STATUS_PARTIAL_MAX else "✗"
        st = f"{glyph} {missing} NO RESULT\n({no_cert} no cert / {cert_no_result} cert w/o result)"
        colour = STATUSFILL["orange"] if missing <= STATUS_PARTIAL_MAX else STATUSFILL["red"]
    if K > 1:
        st += f"\n{K} testing instances"
    if extra:
        st += f"\n• {extra} document(s) on file, not credited"
        stats["uncredited instances"] += extra
    if oos_list:
        st += "\n✗ OUT OF SPECIFICATION: " + ", ".join(oos_list)
        colour = STATUSFILL["red"]
        oos_rows.append((b["cu"], "OOS", oos_list))
    if und_list:
        st += "\n◐ UNDETERMINED (Ph. Eur. band): " + ", ".join(und_list)
        if not oos_list:
            colour = STATUSFILL["orange"]
        oos_rows.append((b["cu"], "UNDETERMINED", und_list))
    if stab_list:
        st += "\n· stability above A.C.: " + ", ".join(stab_list)
        oos_rows.append((b["cu"], "stability", stab_list))
    ws.merge_cells(start_row=first, start_column=3, end_row=last, end_column=3)
    put(ws, first, 3, st, FWS, colour)
    fill_range(ws, first, 3, last, 3, colour)

    outline(ws, first, 1, last, LAST, THICK)
    for p in T.PARAMS:
        outline(ws, first, p["start"], last, p["end"], MED)
    row = last + 1

LASTROW = row - 1

# ---- key
key = ("KEY — ✓ green: certificate on file AND its result on the desk (release or re-test). "
       "✓ orange: stability-timepoint certificate — the result is NOT a release result. "
       "✗ amber: the certificate is credited for this parameter but the desk holds no result from it. "
       "✗ red — MISSING —: no certificate covers this parameter for this batch. "
       "BLOCK RULE: one TESTING INSTANCE = one block of two rows — result(s) on the top row, the certificate that reports them on "
       "the bottom row. A batch holds as many blocks as it has testing instances, and a parameter's certificates are taken in "
       "ascending date order, so the n-th block is the n-th round of testing; a parameter tested once has an empty cell in the "
       "later blocks. For #9, #10 and #11 each sub-determination has its own column on the top row. n.r. = that sub-determination "
       "is not reported on that certificate; \"no result on file\" = the certificate is credited here but the desk holds no result "
       "from it. RED BOLD result = OUT OF SPECIFICATION against the criterion in row 3; AMBER BOLD result = UNDETERMINED, in the "
       "Ph. Eur. band between a printed count limit and twice it. The check follows the Quality Desk exactly: a counted "
       "microbiological limit printed as ≤ 10ⁿ CFU/g is judged against 2 × 10ⁿ (Ph. Eur. 5.1.4); ND, <LOQ, <10, absent, a range "
       "written with \"and\", and any prose annotation are never judged; only release results are judged, and a stability "
       "timepoint above the criterion is named separately in STATUS. Every out-of-specification result needs an investigation "
       "record, not just a red cell. Acceptance criteria in row 3 are the global criteria of the CoQ parameter "
       f"schedule. v7 — built {BUILT} from the desk's record and the owner's certificate credits.")
krow = LASTROW + 2
ws.merge_cells(start_row=krow, start_column=1, end_row=krow, end_column=LAST)
put(ws, krow, 1, key, F6I, GREY, Alignment(horizontal="left", vertical="top", wrap_text=True))
ws.row_dimensions[krow].height = 62

# ---- widths, panes, print
for c, w in ((1, 13), (2, 15), (3, 20)):
    ws.column_dimensions[L(c)].width = w
for c, p, kindc in cols:
    if kindc == "check":
        w = 3.4
    elif kindc == "result":
        w = 10
    elif kindc == "ecoa":
        w = 21
    else:
        w = 8 if kindc in ("9.4", "9.5") else 8.6
    ws.column_dimensions[L(c)].width = w
ws.freeze_panes = "D5"
ws.print_title_rows = "1:4"
ws.page_setup.orientation = "landscape"
ws.page_setup.paperSize = ws.PAPERSIZE_A3
ws.page_setup.fitToWidth = 1
ws.page_setup.fitToHeight = 0
ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.page_margins.left = ws.page_margins.right = 0.3
ws.page_margins.top = ws.page_margins.bottom = 0.4

# --------------------------------------------------------------------------- Credit Audit
# Every certificate the owner's tracker credits to a parameter that it does not report.
# Two different problems, and they need different action:
#   not on this certificate — the document was read and carries no such row; the credit
#                             belongs on the certificate that does report it;
#   not ingested            — the desk holds no value from this document at all; it has
#                             never been read into the corpus, so nothing can be credited
#                             until it is.
aud = wb.create_sheet("Credit Audit", wb.sheetnames.index(SHEET) + 1)
acols = [("CU Batch", 14), ("P Batch", 14), ("Certificate", 24), ("Date", 11), ("Lab", 8),
         ("#", 5), ("Parameter", 30), ("Finding", 22), ("Action", 52)]
for _i, (_t, _w) in enumerate(acols, 1):
    put(aud, 1, _i, _t, FW, NAVY, CEN)
    aud.column_dimensions[L(_i)].width = _w
aud.row_dimensions[1].height = 22
ACTION = {
    "not on this certificate": "Move the credit to the certificate that reports this parameter, or record why it stands.",
    "not ingested": "Re-extract the document into the corpus; the batch cannot reach a CoQ on this parameter until then.",
    "held for review": "The two independent reads disagreed. A person must confirm the figure from the page.",
    "n.r.": "Not reported on this certificate.",
}
_r = 2
for cu, pb, code, date, lab, pno, title, why in sorted(audit, key=lambda x: (x[7], x[0], x[5])):
    put(aud, _r, 1, cu, F7B, IDF if False else None, CEN)
    put(aud, _r, 2, pb, F7, None, CEN)
    put(aud, _r, 3, code, F7, None, CEN)
    put(aud, _r, 4, T.as_date(date), F7, None, CEN)
    aud.cell(_r, 4).number_format = "DD.MM.YYYY"
    put(aud, _r, 5, lab, F7, None, CEN)
    put(aud, _r, 6, f"#{pno}", F7, None, CEN)
    put(aud, _r, 7, title, F7, None, Alignment(horizontal="left", vertical="center", wrap_text=True))
    put(aud, _r, 8, why, F7B, FILL["amber"] if why in ("not on this certificate", "n.r.") else FILL["red"], CEN)
    put(aud, _r, 9, ACTION.get(why, ""), F6I, None, Alignment(horizontal="left", vertical="center", wrap_text=True))
    _r += 1
aud.auto_filter.ref = f"A1:{L(len(acols))}{_r - 1}"
aud.freeze_panes = "A2"
aud.print_title_rows = "1:1"
aud.page_setup.orientation = "landscape"
aud.page_setup.fitToWidth = 1
aud.page_setup.fitToHeight = 0
aud.sheet_properties.pageSetUpPr.fitToPage = True
print("credit audit rows:", _r - 2,
      dict(collections.Counter(x[7] for x in audit)))

# --------------------------------------------------------------------------- index: values + batch key
ix = wb["eCOA Document Index"]
hdr = [str(c.value or "") for c in ix[1]]
cv, ck, cc = len(hdr) + 1, len(hdr) + 2, len(hdr) + 3
put(ix, 1, cv, "PARAMETER VALUES", FW, NAVY)
put(ix, 1, ck, "BATCH KEY", FW, NAVY)
put(ix, 1, cc, "CREDITED FOR", FW, NAVY)
ix.column_dimensions[L(cv)].width = 60
ix.column_dimensions[L(ck)].width = 14
ix.column_dimensions[L(cc)].width = 22

# which parameters the owner's tracker credits each document with, per lot
CREDITED = collections.defaultdict(set)
for _b in batches:
    for _p in T.PARAMS:
        for _c, _d, _l in _b["docs"][_p["n"]]:
            CREDITED[(join_key(_b), T.nkey(_c))].add(_p["n"])
for r in range(2, ix.max_row + 1):
    code = str(ix.cell(r, 6).value or "").strip()
    cu = str(ix.cell(r, 2).value or "").strip()
    lab = str(ix.cell(r, 3).value or "").strip()
    if not code:
        continue
    pb = str(ix.cell(r, 1).value or "").strip()
    vals = values_of(code, lab, cu, COVERS.get((pb or re.sub(r"[＊*]", "", cu), T.nkey(code))))
    parts = []
    for p in T.PARAMS:
        subs = T.GROUPS[p["n"]]
        got = [(T.SUB[no] + " " + vals[no]) if len(subs) > 1 else vals[no] for no in subs if vals.get(no)]
        if got:
            parts.append(f"#{p['n']} " + " · ".join(got))
    stab = " · stability timepoint" if T.nkey(code) in STAB else ""
    cell = ix.cell(r, cv, (" · ".join(parts) + stab) if parts else "no result on the desk for this document")
    cell.font, cell.alignment, cell.border = F7, Alignment(vertical="top", wrap_text=True), BOX
    key = pb or re.sub(r"[＊*]", "", cu)
    cell = ix.cell(r, ck, key)
    cell.font, cell.alignment, cell.border = F7, CEN, BOX
    cred = sorted(CREDITED.get((key, T.nkey(code)), set()))
    cell = ix.cell(r, cc, ", ".join(f"#{n}" for n in cred) if cred else "— not credited —")
    cell.font, cell.alignment, cell.border = (F7 if cred else F6I), CEN, BOX
    if not cred:
        cell.fill = PatternFill("solid", fgColor=FILL["extra"])
ix.auto_filter.ref = f"A1:{L(cc)}{ix.max_row}"

# ---- Read Me: the v7 block rule
rm = wb["Read Me"]
r = rm.max_row + 2
for label, text in (("v7", "This workbook adds the sheet 'CoQ Parameter Tracker v7' — one batch per two-row block, "
                           "certificates stacked as lines in date order, sub-determinations in their own columns, acceptance "
                           "criteria in header row 3 and enforced, out-of-specification results printed red and named in STATUS. "
                           "The v6 flat table is kept as 'CoQ Parameter Tracker (flat)' for comparison."),
                    ("Index", "'eCOA Document Index' now also carries PARAMETER VALUES and BATCH KEY, so the tracker can be "
                              "rebuilt from the index alone (see CoQ_Tracker_v7_rebuild.gs)."),
                    ("OOS check", "A result is flagged only when it provably exceeds its criterion. ND, <LOQ, <10 and absent pass; "
                                  "'<10² and >10' is judged by its upper bound; a value that cannot be parsed is never flagged.")):
    c0 = rm.cell(r, 1, label); c0.font = Font(name="Calibri", size=9, bold=True); c0.alignment = Alignment(vertical="top")
    c1 = rm.cell(r, 2, text); c1.font = Font(name="Calibri", size=9); c1.alignment = Alignment(vertical="top", wrap_text=True)
    rm.row_dimensions[r].height = 13 * (len(text) // 118 + 1)
    r += 1

wb.save(OUT)
print("saved", OUT)
print("batches:", len(batches), "two-row blocks:", (LASTROW - 4) // 2, "rows:", LASTROW - 4, "columns:", LAST)
print("parameter cells by state:", dict(stats))
import collections as _c
by = _c.Counter(k for _, k, _ in oos_rows)
print("verdicts:", dict(by))
for cu, kind, lst in oos_rows:
    print(f"    {kind:14s} {cu:14s} → {', '.join(lst)}")
