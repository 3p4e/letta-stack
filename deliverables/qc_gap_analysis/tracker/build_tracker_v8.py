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
import collections, csv, importlib.util, math, os, re, sys

import openpyxl
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD_DATE = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--build-date=")), "06.09.2026")
spec = importlib.util.spec_from_file_location("tracker_data", os.path.join(HERE, "tracker_data.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)

V9 = "--v9" in sys.argv
# --version=N names the build: the file, the tracker sheet and the Read Me carry vN.
VER = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--version=")), "9" if V9 else "8")
V9 = V9 or VER not in ("8",)
SRC = os.path.join(HERE, "CoQ_Analysis_Master_v6.xlsx")
V8VALS = os.path.join(HERE, "v8_values.json")
OUT = os.path.join(HERE, f"CoQ_Analysis_Master_v{VER}.xlsx")
SHEET = f"CoQ Parameter Tracker v{VER}"
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
FSUB = Font(name="Calibri", size=9, bold=True)        # row 4, the owner's size (v9, 04.09.2026)
RESULT_PT = {4: 13, 5: 10, 6: 10}                     # the owner's v10 (06.09.2026): Total THC 13 pt, CBD and CBN 10 pt
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
    """A merged range takes its format from the anchor cell in Excel and Google Sheets
    alike, so only the anchor is styled — writing the covered cells doubled the file."""
    ws.cell(r1, c1).fill = PatternFill("solid", fgColor=colour)


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
def tidy(v):
    """v8 prints the page verbatim, which mixes decimal commas with decimal points and
    repeats the unit the column header already states. The separator and the unit are
    rendering, not measurement: normalise those two and leave everything else as printed."""
    t = str(v or "").strip()
    t = re.sub(r"(?<=\d),(?=\d)", ".", t)
    t = re.sub(r"\s*[xх×]\s*10\s*\^?\s*(\d+)",
               lambda m: "×10" + "".join("⁰¹²³⁴⁵⁶⁷⁸⁹"[int(c)] for c in m.group(1)), t)
    t = re.sub(r"\s+(CFU/g|µg/kg|mg/kg|%|w/w)\s*$", "", t, flags=re.I)
    t = re.sub(r"([<>≤≥])\s+(?=[\d.])", r"\1", t)
    return t.strip()


_V8 = json.load(open(V8VALS))
SILENT = ("held for review", "not on this certificate", "not ingested", "n.r.")
V8VAL, V8SILENT = collections.defaultdict(dict), collections.defaultdict(dict)
_bycode = collections.defaultdict(set)
for _k in _V8:
    _bycode[_k.split("|", 1)[1]].add(_k)
for _k, _d in _V8.items():
    _cu, _ck = _k.split("|", 1)
    for _no, _v in _d.items():
        _val = _v if _v in SILENT else tidy(_v)
        (V8SILENT if _v in SILENT else V8VAL)[(_cu, _ck)][_no] = _val
        if len(_bycode[_ck]) == 1:                    # the code identifies one lot only
            (V8SILENT if _v in SILENT else V8VAL)[("*", _ck)][_no] = _val


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


# --------------------------------------------------------------------------- new testing instances
# Certificates ingested after the owner's tracker was read (eCOA_DB, 04.09.2026). Each is a
# testing instance credited to the parameter it reports, carrying the values the two
# independent reads agreed on; a value the reads disagreed on is 'held for review' until a
# person rules on the page. A certificate naming a P batch the tracker does not carry opens a
# new lot row with no CU code, and a Work Order task to record it.
NEW_INSTANCES = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--new-instances=")),
                     os.path.join(HERE, "new_instances.json"))
NEW = json.load(open(NEW_INSTANCES)) if os.path.exists(NEW_INSTANCES) else []
NEW_TOUCHED, NEW_LOTS, NEW_HELD = [], [], []


def _lot_of(inst):
    for b in batches:
        if inst["p"]:
            if inst["p"] in [x.strip() for x in b["p"].split("/")]:
                return b
        elif b["p"].startswith("N/A") and re.sub(r"[＊*]", "", b["cu"]) == inst["cu"]:
            return b
    return None


for inst in NEW:
    b = _lot_of(inst)
    if b is None:
        b = {"cu": "— not recorded —", "p": inst["p"] or "N/A — no P batch assigned", "status": "",
             "labs": [], "docs": {n: [] for n in range(1, 13)}, "certs": [],
             "strain": inst.get("strain", ""), "new_lot": True}
        batches.append(b)
        NEW_LOTS.append(b)
    b.setdefault("strain", inst.get("strain", ""))
    key = join_key(b)
    ck = T.nkey(inst["code"])
    for n in inst["params"]:
        if ck not in {T.nkey(c) for c, d, l in b["docs"][n]}:
            b["docs"][n].append((inst["code"], inst["date"], inst["lab"]))
    INDEX_DOCS[key].append((inst["code"], inst["date"], inst["lab"], set(inst["params"])))
    COVERS[(key, ck)] = set(inst["params"])
    V8VAL[("*", ck)] = dict(inst["vals"])        # read from the eCoA database: no ᴿ mark
    VAL[ck] = dict(inst["vals"])
    for no in inst.get("held", []):
        NEW_HELD.append((b["cu"], b["p"], inst["code"], inst["date"], inst["lab"], int(no.split(".")[0])))
    if b not in NEW_TOUCHED:
        NEW_TOUCHED.append(b)
# --------------------------------------------------------- the Head of QC's batch list
# Loaded here rather than inside the iCoA block, because the FIRST thing it is needed for is
# a lot's own name. A certificate that prints only the P number (IJZ-MB prints "Серија:
# P060102" and no cultivation batch) creates a lot above with cu "— not recorded —" — and the
# list has that lot's name. Before this, P060102 stood nameless in the tracker while the list
# said WED102501, and 34 kg of delivered Wedding Cake looked like an unknown lot; P060342
# likewise, where the list says SCR012601* and 90 kg of Scrambler was delivered in tranche 3.
_bd = importlib.util.spec_from_file_location("batch_dates", os.path.join(HERE, "batch_dates.py"))
BD = importlib.util.module_from_spec(_bd)
_bd.loader.exec_module(BD)
_dates_path = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--dates=")), os.path.join(HERE, "batch_dates.csv"))
DATES = BD.load_dates(_dates_path)
DATE_ROWS = sorted({r["seq"]: r for r in DATES.values()}.values(), key=lambda r: int(r["seq"]))
DATES_CU = {T.batch_key(r["cu_batch"]): r for r in DATE_ROWS}
DATES_P = {r["p_batch"]: r for r in DATE_ROWS if r.get("p_batch")}
NAMED_FROM_LIST = []
for _b in batches:
    if not str(_b.get("cu", "")).startswith("—"):
        continue
    _ps = [x.strip() for x in str(_b.get("p", "")).split("/") if x.strip().startswith("P")]
    _rows = [DATES_P[x] for x in _ps if x in DATES_P]
    _names = sorted({r["cu_batch"] for r in _rows})
    if len(_names) == 1:                    # one lot, one name; two names would be a roll-up
        NAMED_FROM_LIST.append((_names[0], _b["p"]))
        _b["cu"] = _names[0]
        _b["named_from_list"] = True
if NAMED_FROM_LIST:
    print("named from the Head of QC's list: " +
          "; ".join(f"{p} -> {c}" for c, p in NAMED_FROM_LIST))

if NEW:
    print(f"new instances: {len(NEW)} on {len(NEW_TOUCHED)} lot(s); "
          f"{len(NEW_LOTS)} lot(s) not on the owner's tracker; {len(NEW_HELD)} value(s) held for review")
    if V9 and VER == "9":
        VER = "9.1"
        OUT = os.path.join(HERE, "CoQ_Analysis_Master_v9.1.xlsx")

# --------------------------------------------------------------------------- the iCoA rule (04.09.2026)
# Head of QC, 04.09.2026: identification A (appearance) and B (microscopy) are tested at
# Purely Plant together with foreign matter, at the date of packaging, and ONE iCoA per batch
# carries the three results for release. Identification C conforms to the ImB specification
# and is referenced to the certificate that carries the cannabinoid assay (#4), which the
# desk already credits. Harvest and packaging dates per batch are the Head of QC's list of
# 04.09.2026 (batch_dates.csv, --dates=): the in-house instance is dated on the FIRST day of
# packaging — the day the issuance plan already uses as the CoQ basis — and a lot the list
# does not carry keeps "packaging date — to record" and sorts last. The iCoA Issuance sheet
# lists what each batch's iCoA must carry, Batch Dates the list itself. Foreign matter is "Conforms" by the declaration of 13.08.2026,
# except where an outsourced certificate reports otherwise (FB032601, ППК26127: 0.08 %,
# Не одговара) — that lot's foreign matter is held for the Head of QC.
ICOA_RULE = "--icoa" in sys.argv
# --cells absorbs the owner's 09.09.2026 pass over eCoA_DATABASE: the coverage it
# closes on Batch Coverage, and the Reconciliation sheet that says what the two
# records of those certificates agree and disagree about.
CELLS_0909 = "--cells" in sys.argv
GAPDIR = os.path.dirname(HERE)
COVERAGE_UPDATE = os.path.join(GAPDIR, "coverage_update_2026-09-09.tsv")
IDENTITY_BLOCK = os.path.join(GAPDIR, "identity_block_2026-09-09.tsv")
COV_0909_APPLIED, COV_0909_SKIPPED = [], []

IDENT_NOTE = (
    "Identification A, Identification B and foreign matter are blank on almost "
    "every lot in both tranches, and the reason is not that nobody transcribed "
    "them. 118 of the 600 cells cite an in-house iCoA-PP_26-nnn whose issue date "
    "is PLANNED, on 40 of the 50 batches: the certificate that carries the result "
    "has not been issued, so there is nothing to cite. What the in-house "
    "documents that DO exist carry is worse than missing. Appearance is the "
    "single word \u201cConfirms\u201d with no description. Foreign matter is "
    "\u201cConfirms\u201d against a < 2.0 % specification with NO PERCENTAGE "
    "PRINTED \u2014 Ph. Eur. 2.8.2 is gravimetric and EudraLex Vol. 4 Ch. 6 "
    "\u00a76.7 requires the result. Microscopy was NOT PERFORMED on any of the "
    "five documents read. Three Report of Analysis documents carry no document "
    "code, no version and no report number (EudraLex Vol. 4 Ch. 4 \u00a74.9), and "
    "this build refuses to cite them. Issuing the iCoAs does not by itself fix "
    "this: the microscopy has to be done and the foreign-matter percentage has "
    "to be printed.")

NOROW_NOTE = (
    "These lots have certificates on file and no row on Batch Coverage, so the "
    "closure had nowhere to land. Four of them \u2014 ACC102501, CF102501, "
    "PUM102501 and CC012603 \u2014 are the batches the delivery reconciliation "
    "of 07.09.2026 reported as delivered with nothing on file anywhere. That "
    "finding is now out of date for them: something IS on file. A row cannot be "
    "invented here, because a Batch Coverage row is a tracker lot and these are "
    "not on the owner's tracker; they have to be added there first.")


def load_coverage_update(path=COVERAGE_UPDATE):
    """The 09.09 closures, verbatim: one row per lot and parameter."""
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))
ICOA_ROWS = []
NEW_NONCONF = []
ADDED = collections.defaultdict(list)        # lot -> documents added by this build (coverage recount)
for _b in NEW_TOUCHED:
    ADDED[id(_b)] += [(x["code"], x["date"], x["lab"]) for x in NEW if _lot_of(x) is _b]
if ICOA_RULE:
    _D = json.load(open(T.DESK))
    _plan = {}
    for _x in _D["icoa_plan"]:
        _plan.setdefault(T.batch_key(re.sub(r"[＊*]", "", _x["cb"])), _x["icoa_ref"])
        if _x.get("pp"):
            _plan.setdefault("P:" + _x["pp"].strip(), _x["icoa_ref"])
    ICOA_DATE = "packaging date — to record"
    RETEST_DATE = "retest sampling date — to record"
    # DATES / DATE_ROWS / DATES_CU are loaded above, where the lot names are back-filled.
    DATE_USED = {}                                # seq -> the tracker lot it dated

    def _dates_of(b, cu0):
        """The list's rows for a lot: by P-number (one CU row may hold several P lots), else by CU code."""
        rows = []
        for p in b["p"].split("/"):
            r = DATES.get(p.strip())
            if r and r not in rows:
                rows.append(r)
        # the owner marks some CU codes with an asterisk (JD112501＊ beside JD112501, its own CNP
        # certificate): a lot of its own, which the list names only by an exact code
        if not rows and not re.search(r"[＊*]", b["cu"]) and DATES_CU.get(T.batch_key(cu0)):
            rows.append(DATES_CU[T.batch_key(cu0)])
        for r in rows:
            DATE_USED[r["seq"]] = b["cu"] if b["cu"] and not b["cu"].startswith("—") else b["p"]
        return rows

    def _span_of(rows, a, z, many):
        out = []
        for r in rows:
            t = BD.span(r[a], r[z]) or "— not given —"
            out.append(f"{r['p_batch']}: {t}" if many and r["p_batch"] else t)
        return " | ".join(dict.fromkeys(out))
    print(f"batch dates: {len(DATE_ROWS)} row(s) from {os.path.basename(_dates_path)}")
    _COQ, _RETEST = {}, {}
    for _c in _D["coqs"]:
        _tbl = _COQ if _c["t"].startswith("initial release") else _RETEST
        _tbl.setdefault(T.batch_key(re.sub(r"[＊*]", "", _c["cb"])), _c)
        if _c.get("pp"):
            _tbl.setdefault("P:" + _c["pp"].strip(), _c)

    def _lookup(tbl, b, cu0):
        return tbl.get(T.batch_key(cu0)) or next((tbl.get("P:" + p.strip()) for p in b["p"].split("/") if tbl.get("P:" + p.strip())), None)

    def _ident_c(b, after=None, before=None):
        """The cannabinoid-assay certificate that covers identification C: the assay
        certificate itself, never a loss-on-drying one; `after` restricts it to the retest
        campaign, `before` to the initial testing."""
        pool = list(b["docs"][4]) or list(b["docs"][3])
        pool = [x for x in pool if not re.search(r"LoD|ГС", x[0], re.I)] or pool
        if after:
            pool = [x for x in pool if str(T.date_key(x[1])) >= str(T.date_key(after))]
        if before:
            pool = [x for x in pool if str(T.date_key(x[1])) < str(T.date_key(before))]
        pool = sorted(pool, key=lambda x: (T.date_key(x[1]), x[0]))
        return f"{pool[0][0]}, ({pool[0][1]}) [{pool[0][2]}]" if pool else None

    CNP_COVERED = {}

    def _vals_of(code, cu):
        """v8's reading first, the desk's beneath it (values_of is defined further down)."""
        ck = T.nkey(code)
        out = dict(VAL.get(ck) or {})
        out.update(V8VAL.get(("*", ck)) or {})
        out.update(V8VAL.get((cu, ck)) or {})
        return out

    _pending_inst = []                            # (lot, key, scope, values, date, row): the in-house instance, keyed after the register
    import datetime as _dt
    SOP_D = _dt.date(2026, 5, 11)                 # the CoQ SOP came into use (ISSUE_COQ_CONVENTIONS)

    def _D_(v):
        try:
            return _dt.datetime.strptime(str(v), "%d.%m.%Y").date()
        except ValueError:
            return None

    def _F_(d):
        return d.strftime("%d.%m.%Y") if d else ""

    def _workday(d, plus):
        """The first working day (Mon–Fri) on or after d + plus days; public holidays are not applied."""
        x = d + _dt.timedelta(days=plus)
        while x.weekday() >= 5:
            x += _dt.timedelta(days=1)
        return x
    LEGACY_ICOA = _D_(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--legacy-icoa=")), "15.05.2026"))
    LEGACY_COQ = _D_(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--legacy-coq=")), "27.05.2026"))
    for _nm, _d in (("legacy iCoA day", LEGACY_ICOA), ("legacy CoQ day", LEGACY_COQ)):
        assert _d and _d.weekday() < 5 and _d >= SOP_D, f"the {_nm} must be a working day on or after the SOP floor"
    # the old in-house certificates (QCCoA 001 v.01/v.02) the desk knows, by P number and by batch
    OLD_COA = {}
    for _e in _D["ecoa"]:
        if _e["lab"].startswith("Purely Plant") and str(_e.get("code", "")).startswith("PP CoA"):
            OLD_COA.setdefault(_e.get("pn") or "", (_e["code"], _e["date"]))
            OLD_COA.setdefault(T.batch_key(_e["batch"]), (_e["code"], _e["date"]))
    OLD_COA.pop("", None)
    FLAGS, COQ_ROWS = [], []
    # the QP's retest campaign began in July 2026 with the sampling of Tranche 1 (the first 21 lots
    # produced), then Tranches 2 and 3 (Head of QC, 05.09.2026): a certificate dated on or after
    # RETEST_START is a retest document — it certifies the reissued CoQ, never the initial one
    RETEST_START = _D_(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--retest-start=")), "01.07.2026"))
    RETEST_START_S = _F_(RETEST_START)
    # A document is a RETEST document when the desk files it as a re-analysis (the Farmahem
    # 197-series), or when its lot is legacy and it is dated after the legacy CoQ day (the
    # legacy CoQ of 27.05.2026 cannot cite it, and for those lots everything later is the
    # campaign), or when its lot is post-SOP and it is a second certificate for the
    # determination. The first certificate of a post-SOP lot is its initial testing even when
    # the campaign was already running (P060452's CNP certificate of 21.07.2026).
    REANALYSIS = set()
    for _rg in _D["reg"]:
        for _ce in _rg.get("certs", []):
            if "re-analysis" in str(_ce.get("fam", "")).lower():
                REANALYSIS.add(T.nkey(_ce["code"]))
    # The IJZ-MB delivery of 25/26.08.2026 (requests 295–324/2026, certificates of 31.08 and
    # 01.09.2026, the split manifest) is one campaign sampling: 68 to 436 days after packaging,
    # against the one to two weeks release testing takes — so every certificate in it is a
    # retest document, for the post-SOP lots too (Head of QC, 06.09.2026).
    _cm = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--campaign-manifest=")),
               os.path.join(HERE, "split_manifest_IJZ-MB_2026-09-01.csv"))
    CAMPAIGN = set()
    if os.path.exists(_cm):
        import csv as _csv
        for _row in _csv.DictReader(open(_cm, encoding="utf-8-sig")):
            CAMPAIGN.add(T.nkey(_row["lab_no"]))
            CAMPAIGN.add(T.nkey(_row["doc_code_in_filename"]))
    REANALYSIS |= CAMPAIGN
    print(f"retest documents: {len(REANALYSIS)} (the desk's re-analysis family and the IJZ-MB campaign delivery of 25/26.08.2026)")
    REG_KEY_COL, COQ_KEY_COL = "P", "S"          # the Key columns of the iCoA Register and the CoQ Register (REG_COLS, COQ_COLS)
    for b in batches:
        cu0 = re.sub(r"[＊*]", "", b["cu"])
        key = join_key(b)
        _drows = _dates_of(b, cu0)
        # --- CNP first: a CNP certificate that reports identification A, B or foreign matter
        #     is the reference for them (its document code goes on the CoQ)
        cnp = {}
        seen = set()
        for c, d, l, cov in list(INDEX_DOCS.get(key, [])) + [(c, d, l, set()) for n in (1, 2, 3, 4, 7) for c, d, l in b["docs"][n]]:
            if l != "CNP" or T.nkey(c) in seen:
                continue
            seen.add(T.nkey(c))
            vals = _vals_of(c, b["cu"])
            for n in (1, 2, 7):
                if vals.get(str(n)) and n not in cnp:
                    cnp[n] = (c, d, l)
        for n, (c, d, l) in cnp.items():
            if T.nkey(c) not in {T.nkey(x[0]) for x in b["docs"][n]}:
                b["docs"][n].append((c, d, l))
            COVERS[(key, T.nkey(c))] = set(COVERS.get((key, T.nkey(c)), set())) | {n}
            ADDED[id(b)]
        CNP_COVERED[id(b)] = cnp
        if cnp and b not in NEW_TOUCHED:
            NEW_TOUCHED.append(b)
        fm_cnp = cnp.get(7)
        if fm_cnp and "Не одговара" in str(_vals_of(fm_cnp[0], b["cu"]).get("7", "")):
            NEW_NONCONF.append((b["cu"], b["p"], fm_cnp[0], fm_cnp[1], "CNP", 7))
        # --- ONE iCoA PER P LOT for identification A, B and foreign matter (Head of QC, 05.09.2026,
        #     confirming 04.09.2026), unless a CNP certificate reports the scope — then the CNP code is
        #     the reference and the iCoA covers the rest (all three on CNP: no iCoA). A tracker row
        #     that holds several P lots is one lot per P number. Two groups by packaging:
        #       legacy   — packed before the SOP floor (11.05.2026) or holding an old in-house CoA:
        #                  the iCoA is tested at packaging and issued on 15.05.2026; the CoQ
        #                  (CoQ-PP_26-nnn, superseding the old CoA) is issued on 27.05.2026;
        #       post-SOP — packed after the floor: the iCoA is issued on the first working day 5 days
        #                  after packaging, the CoQ on the first working day 7 days after the latest
        #                  eCoA it cites.
        #     Adherence (ISSUE_COQ_CONVENTIONS): a CoQ never precedes a document it cites, so a legacy
        #     lot whose latest eCoA is dated after 27.05.2026 takes the post-SOP CoQ rule and is
        #     flagged; a CoQ never precedes its iCoA; a lot whose initial certificate for a
        #     determination is not on file keeps its planned CoQ and number (the initial testing exists
        #     at CNP, the certificate is to be located); nothing is dated on a weekend.
        _plist = [p.strip() for p in b["p"].split("/") if p.strip().upper().startswith("P0")]
        _lots = _plist if len(_plist) > 1 else [b["p"]]
        _single = len(_lots) == 1
        scope = [n for n in (1, 2, 7) if n not in cnp]
        fm = (INH.get(T.cu_key(b["cu"])) or {}).get("7") or "Conforms"
        vals = {"1": "Conforms", "2": "Conforms", "7": fm}
        cell = lambda n: (f"CNP {cnp[n][0]}" if n in cnp else vals[str(n)])
        for _lot in _lots:
            _lot_id = _lot.strip() if re.match(r"^P\d{6}$", _lot.strip()) else cu0
            _lrows = [r for r in _drows if _single or r["p_batch"] == _lot]
            # the tracker names no P lot but the Head of QC's list does (JD112501 -> P060212): the
            # list's P number goes on the row, so the sheet's date lookups by P batch find it
            if not re.match(r"^P\d{6}$", _lot.strip()) and _lrows and _lrows[0]["p_batch"]:
                _lot = _lrows[0]["p_batch"]
            _lpk = sorted((r["packaging_from"] for r in _lrows if r["packaging_from"]), key=lambda d: str(T.date_key(d)))
            _lend = sorted((r["packaging_to"] for r in _lrows if r["packaging_to"]), key=lambda d: str(T.date_key(d)))
            _ldate = _lpk[0] if _lpk else ICOA_DATE
            _complete = _lend[-1] if _lend else "— packaging date to record —"
            _lharvest = _span_of(_lrows, "harvest_from", "harvest_to", False) if _lrows else "— not on the list —"
            _lpackaging = _span_of(_lrows, "packaging_from", "packaging_to", False) if _lrows else "— not on the list —"
            if _single:
                _pref = _plan.get(T.batch_key(cu0)) or next((_plan["P:" + p.strip()] for p in b["p"].split("/") if _plan.get("P:" + p.strip())), None)
            else:
                _pref = _plan.get("P:" + _lot)
            _pref = _pref if (_pref and _pref.startswith("iCoA-")) else ""
            _coq = _lookup(_COQ, b, cu0) if _single else _COQ.get("P:" + _lot)
            if _coq and _coq.get("basis") and _lpk and _coq["basis"] != _lpk[0]:
                _lpackaging += f" (the issuance plan's basis: {_coq['basis']})"
            _strain = b.get("strain") or STRAIN.get(T.batch_key(cu0), "")
            _cu_show = b["cu"] if not b["cu"].startswith("—") else (f"{_lrows[0]['cu_batch']} (from the list)" if _lrows else b["cu"])
            _old = OLD_COA.get(_lot) or OLD_COA.get(T.batch_key(cu0))
            _pkd, _cmd = _D_(_lpk[0]) if _lpk else None, _D_(_lend[-1]) if _lend else None
            _group = ("legacy" if (_pkd < SOP_D or _old) else "post-SOP") if _pkd else "—"
            # the documents the INITIAL CoQ cites, and the RETEST documents, per determination
            _first, _rt_docs = {}, {}
            for n in range(1, 13):
                pool = sorted([x for x in b["docs"][n] if x[2] != "PP"], key=lambda x: (str(T.date_key(x[1])), x[0]))
                ini, rt = [], []
                for x in pool:
                    xd = _D_(x[1])
                    is_rt = (T.nkey(x[0]) in REANALYSIS
                             or (_group == "legacy" and xd and xd > LEGACY_COQ)
                             or (_group != "legacy" and bool(ini)))
                    (rt if is_rt else ini).append(x)
                if ini:
                    _first[n] = ini[0]
                if rt:
                    _rt_docs[n] = rt[0]
            _latest = max(_first.values(), key=lambda x: str(T.date_key(x[1]))) if _first else None
            _gaps = [n for n in range(1, 13) if n not in _first and n not in scope and not (n == 3 and 4 in _first)]
            _rt_only = [n for n in _gaps if n in _rt_docs]
            _rt_latest = max(_rt_docs.values(), key=lambda x: str(T.date_key(x[1]))) if _rt_docs else None
            _ini_set = {(T.nkey(x[0]), n) for n, x in _first.items()}
            _rt_set = {T.nkey(x[0]) for x in _rt_docs.values()}
            if _old and _pkd and _pkd >= SOP_D:
                FLAGS.append(f"{_lot_id}: holds the old in-house CoA {_old[0]} but was packed {_lpk[0]}, after the SOP floor — treated as legacy")
            _icoa_issue = LEGACY_ICOA if _group == "legacy" else (_workday(_cmd, 5) if _cmd else None)
            _latest_d = _D_(_latest[1]) if _latest else None
            _coq_flag = ""
            if _group == "legacy":
                if _latest_d and _latest_d > LEGACY_COQ:
                    _coq_issue = _workday(_latest_d, 7)
                    _coq_flag = f"moved off 27.05.2026: cites {_latest[0]} of {_latest[1]}"
                    FLAGS.append(f"{_lot_id}: legacy CoQ cannot be dated 27.05.2026 — it cites {_latest[0]} of {_latest[1]}; planned {_F_(_coq_issue)} (first working day 7 days after)")
                else:
                    _coq_issue = LEGACY_COQ
            elif _group == "post-SOP":
                # the series continues after the legacy day: CoQ-PP_26-001 … are the legacy lots of
                # 27.05.2026, so a post-SOP CoQ is never dated before it
                _coq_issue = max(_workday(_latest_d, 7), LEGACY_COQ) if _latest_d else max(LEGACY_COQ, _icoa_issue or LEGACY_COQ)
                if not _latest_d:
                    _coq_flag = "provisional date: no initial certificate on file yet — the date follows the latest eCoA once located"
                    FLAGS.append(f"{_lot_id}: no initial certificate on file — the CoQ keeps its planned number with a provisional date {_F_(_coq_issue)}")
                if _latest_d and _workday(_latest_d, 7) < LEGACY_COQ:
                    _coq_flag = f"rule date {_F_(_workday(_latest_d, 7))} held to the legacy series day"
                    FLAGS.append(f"{_lot_id}: post-SOP CoQ rule date {_F_(_workday(_latest_d, 7))} precedes the legacy series day 27.05.2026 — held to it, so the legacy CoQs keep 001 onward")
            else:
                _coq_issue = None
            if _coq_issue and _icoa_issue and scope and _coq_issue < _icoa_issue:
                FLAGS.append(f"{_lot_id}: CoQ rule date {_F_(_coq_issue)} precedes its iCoA of {_F_(_icoa_issue)} — held to the iCoA date")
                _coq_issue = _icoa_issue
                _coq_flag = (_coq_flag + "; " if _coq_flag else "") + "held to the iCoA date"
            # a CoQ never precedes the packaging of its lot (a lot without an iCoA — CNP covers
            # A, B and foreign matter — whose certificates all predate packaging)
            if _coq_issue and _cmd and _coq_issue < _cmd:
                FLAGS.append(f"{_lot_id}: CoQ rule date {_F_(_coq_issue)} precedes the packaging of the lot ({_F_(_cmd)}) — held to the packaging date")
                _coq_issue = _workday(_cmd, 0)
                _coq_flag = (_coq_flag + "; " if _coq_flag else "") + "held to the packaging date"
            # --- RETEST SERIES: the QP's campaign, sampled by tranche from July 2026 (Tranche 1 the
            #     first 21 lots produced, then Tranches 2 and 3). At the sampling, identification A, B
            #     and foreign matter are tested in-house on every bag of the representative sample
            #     (ONE iCoA per lot); Farmahem tests the cannabinoids — identification C with them —
            #     and the mycotoxins; IJZ-MB the microbiology. The reissued CoQ carries those retest
            #     results and the initial external certificates for the rest; release-time CNP
            #     coverage does not excuse it. A retest document is one dated on or after RETEST_START.
            _rt = _lookup(_RETEST, b, cu0) if _single else _RETEST.get("P:" + _lot)
            def _pick(pool_n, want_rt):
                pool = [x for x in b["docs"][pool_n] if x[2] != "PP" and not re.search(r"LoD|ГС", x[0], re.I)]
                pool = [x for x in pool if (T.nkey(x[0]) in _rt_set) == want_rt]
                pool = sorted(pool, key=lambda x: (str(T.date_key(x[1])), x[0]))
                return f"{pool[0][0]}, ({pool[0][1]}) [{pool[0][2]}]" if pool else None
            c_rt = _pick(4, True) or _pick(3, True)

            m_rt, mb_rt = _pick(10, True), _pick(9, True)
            _tranche = ("Tranche 1 (sampled July 2026)" if (c_rt and _group == "legacy") else
                        "re-analysed" if c_rt else
                        "sampled — Tranche 2/3 (potency and mycotoxins pending)" if _rt_docs else "not yet sampled")
            _st_rt = ("due — retest assay, mycotoxins" + (" and microbiology" if mb_rt else "") + " on file; in-house iCoA to test" if (c_rt and m_rt) else
                      "due — retest assay on file, mycotoxins pending" if c_rt else
                      "sampled — microbiology on file, retest assay pending" if mb_rt else
                      "pending — not yet sampled")
            if _rt_only:
                _docs_txt = " / ".join(dict.fromkeys(_rt_docs[n][0] + " of " + _rt_docs[n][1] for n in _rt_only))
                FLAGS.append(f"{_lot_id}: no initial certificate for #{', #'.join(str(n) for n in _rt_only)} — only the retest "
                             f"{_docs_txt}; the {_group} CoQ cannot cite it "
                             f"(Head of QC to rule: report as not tested at initial testing, or wait for the reissue)")
            _names = {1: "Ident A", 2: "Ident B", 7: "Foreign matter"}
            _cnp_txt = " / ".join(f"{k}: {cnp[n][0]}" for k, n in (("A", 1), ("B", 2), ("FM", 7)) if n in cnp) or "—"
            _identc = _pick(4, False) or _pick(3, False) or "— no cannabinoid certificate from the initial testing —"
            common = {"cu": _cu_show, "p": _lot, "strain": _strain, "harvest": _lharvest, "packaging": _lpackaging,
                      "complete": _complete, "group": _group, "sortdate": (_lpk[0] if _lpk else ""), "test_date": _ldate}
            row = dict(common, series="initial release", icoa="" if scope else "not needed", plan_ref=_pref,
                       coq_plan=_coq["n"] if _coq else "— not in the issuance plan —",
                       basis=(_coq["basis"] if _coq and _coq.get("basis") else (_lpk[0] if _lpk else "")),
                       issue=_F_(_icoa_issue) if _icoa_issue else "— packaging date to record —",
                       icoa_issue=_icoa_issue, key=f"{_lot_id}|I",
                       scope=(" + ".join(_names[n] for n in scope) if scope else "— all three on the CNP certificate —"),
                       a=cell(1), b=cell(2), fm=cell(7), c=_identc, cnp=_cnp_txt,
                       assay_rt="", myco_rt="", carry="",
                       status="not needed — CNP covers A, B and foreign matter" if not scope else "to register")
            ICOA_ROWS.append(row)
            if scope:
                _pending_inst.append((b, key, scope, vals, _ldate, row))
            COQ_ROWS.append(dict(common, series="initial release", key=f"{_lot_id}|I", coq_issue=_coq_issue, coq_flag=_coq_flag,
                                 latest=_latest, icoa_needed=bool(scope), c=_identc, cnp=_cnp_txt, gaps=list(_gaps), old=_old,
                                 plan_coq=_coq["n"] if _coq else "— not in the issuance plan —",
                                 basis=(_coq["basis"] if _coq and _coq.get("basis") else (_lpk[0] if _lpk else ""))))
            if _rt:
                ICOA_ROWS.append(dict(common, series=f"retest — {_tranche}", icoa="", plan_ref="",
                                      coq_plan=_rt["n"] if not _rt["n"].startswith("(") else "CoQ reissue (assigned on issue)",
                                      basis=_rt.get("basis", ""), issue=f"at the retest sampling · {_tranche}", icoa_issue=None,
                                      key=f"{_lot_id}|R", scope="Ident A + Ident B + Foreign matter", a="to test", b="to test", fm="to test",
                                      c=c_rt or "— retest assay not yet on file —", cnp="—",
                                      assay_rt=c_rt or "— pending —", myco_rt=m_rt or "— pending —",
                                      carry="#8, #9, #11, #12 from the initial testing", status=_st_rt, sortdate=""))
                COQ_ROWS.append(dict(common, series=f"retest — {_tranche}", key=f"{_lot_id}|R", coq_issue=None, coq_flag="",
                                     latest=_rt_latest, icoa_needed=True, c=c_rt or "— retest assay not yet on file —", cnp="—",
                                     rt_micro=mb_rt or "— pending —",
                                     gaps=[], old=None, plan_coq=_rt["n"] if not _rt["n"].startswith("(") else "CoQ reissue (assigned on issue)",
                                     basis=_rt.get("basis", ""), rt_status=_st_rt, assay_rt=c_rt or "— pending —", myco_rt=m_rt or "— pending —",
                                     sortdate=""))

    def _bkey(r):
        d = r.get("sortdate") or r["basis"]
        return (0 if r["series"] == "initial release" else 1,
                str(T.date_key(d)) if d else "99999998", r["cu"], r["p"])
    ICOA_ROWS.sort(key=_bkey)
    for _i, _row in enumerate(ICOA_ROWS, 1):
        _row["seq"] = _i
    print(f"iCoA rule: {sum(1 for r in ICOA_ROWS if r['series'] == 'initial release')} initial rows "
          f"({sum(1 for r in ICOA_ROWS if r['status'].startswith('not needed'))} covered by CNP), "
          f"{sum(1 for r in ICOA_ROWS if r['series'] != 'initial release')} retest rows "
          f"({sum(1 for r in ICOA_ROWS if r['status'].startswith('due'))} with the retest assay on file)")
    print(f"batch dates: {len(DATE_USED)} of {len(DATE_ROWS)} list rows date a tracker lot; "
          f"{len({r['p'] for r in ICOA_ROWS if r['series'] == 'initial release' and r['packaging'].startswith('— not on')})} lot(s) not on the list")

    # ------------------------------------------------------------------ the preliminary registers
    # iCoA-PP_26-nnn and CoQ-PP_26-nnn (nnn = 001 … 999, one series each for the year of issue),
    # assigned in the order the documents are issued: by the planned issue date, then by the first
    # day of packaging. No number is reserved for a document that cannot be issued yet: a lot
    # without a packaging date, a held result, every
    # retest document. On the sheets the number, the code and the dates are FORMULAS; the values
    # computed here are the same numbers, for the page and the checks.
    _issuable, _later, _na = [], [], []
    for r in ICOA_ROWS:
        if r["icoa"] == "not needed":
            r["code"], r["issuable"], r["reg_status"] = "", "n/a", r["status"]
            _na.append(r)                     # on the sheet all the same: the CoQ Register reads its packaging date there
            continue
        if r["series"] != "initial release":
            r["why"] = ("retest assay on file; identification A, B and foreign matter to test at the retest sampling"
                        if r["status"].startswith("due") else "retest assay not yet on file")
            _later.append(r)
        elif not r["icoa_issue"]:
            r["why"] = "no packaging date on the list"
            _later.append(r)
        elif r["fm"] == "held for review":
            r["why"] = "foreign matter held for the Head of QC"
            _later.append(r)
        else:
            _issuable.append(r)
    _issuable.sort(key=lambda r: (r["icoa_issue"], str(T.date_key(r["sortdate"])) if r["sortdate"] else "9", r["cu"], r["p"]))
    for _i, r in enumerate(_issuable, 1):
        r["code"], r["issuable"] = f"iCoA-PP_26-{_i:03d}", "yes"
        r["reg_status"] = ("registered — issued with the legacy series on 15.05.2026" if r["group"] == "legacy"
                           else "registered — first working day 5 days after packaging")
        r["icoa"], r["status"] = r["code"], r["reg_status"]
    for r in _later:
        r["code"], r["issuable"] = "— at issue —", "no"
        r["reg_status"] = "not yet issuable — " + r["why"]
        r["icoa"] = r["code"]
        if r["series"] == "initial release":
            r["status"] = r["reg_status"]
    REGISTER = _issuable + sorted(_na, key=lambda r: (str(T.date_key(r["sortdate"])) if r["sortdate"] else "9", r["cu"], r["p"])) \
        + sorted(_later, key=lambda r: (0 if r["series"] == "initial release" else 1 if r["status"].startswith("due") else 2,
                                                          str(T.date_key(r["sortdate"] or r["basis"])) if (r["sortdate"] or r["basis"]) else "9", r["cu"], r["p"]))
    ICOA_BY_KEY = {r["key"]: r for r in ICOA_ROWS}
    _cq_ok, _cq_later = [], []
    for r in COQ_ROWS:
        ic = ICOA_BY_KEY.get(r["key"])
        if r["series"] != "initial release":
            r["why"] = r["rt_status"]
            _cq_later.append(r)
        elif not r["coq_issue"]:
            r["why"] = "no packaging date on the list" if r["group"] == "—" else "no certificate on file"
            _cq_later.append(r)
        elif r["icoa_needed"] and ic and ic["issuable"] != "yes":
            r["why"] = "its iCoA is not yet issuable"
            _cq_later.append(r)
        else:
            _cq_ok.append(r)
    _cq_ok.sort(key=lambda r: (r["coq_issue"], str(T.date_key(r["sortdate"])) if r["sortdate"] else "9", r["cu"], r["p"]))
    for _i, r in enumerate(_cq_ok, 1):
        r["code"], r["issuable"] = f"CoQ-PP_26-{_i:03d}", "yes"
        r["reg_status"] = (("registered — legacy series, issued 27.05.2026" if not r["coq_flag"] else "registered — " + r["coq_flag"])
                           if r["group"] == "legacy" else
                           ("registered — first working day 7 days after the latest eCoA" if not r["coq_flag"] else "registered — " + r["coq_flag"]))
        # Head of QC, 05.09.2026 (evening): a production lot whose initial certificate for a
        # determination is not on file keeps its planned CoQ and number — the initial testing
        # exists at the Faculty of Pharmacy's Center for Natural Products and the certificate is
        # to be located (Work Order); the number is not withheld for it
        if r["gaps"]:
            r["reg_status"] += " · initial certificate to locate: " + ", ".join(f"#{n} ({'IJZ' if n == 9 else 'CNP'})" for n in r["gaps"])
    for r in _cq_later:
        r["code"], r["issuable"] = "— at issue —", "no"
        r["reg_status"] = "not yet issuable — " + r["why"]
    COQ_REGISTER = _cq_ok + sorted(_cq_later, key=lambda r: (0 if r["series"] == "initial release" else 1,
                                                             str(T.date_key(r["sortdate"] or r["basis"])) if (r["sortdate"] or r["basis"]) else "9", r["cu"], r["p"]))
    print(f"iCoA register: {len(_issuable)} numbered (iCoA-PP_26-001 … {_issuable[-1]['code'][-3:] if _issuable else '—'}; "
          f"{sum(1 for r in _issuable if r['group'] == 'legacy')} legacy on 15.05.2026, "
          f"{sum(1 for r in _issuable if r['group'] != 'legacy')} post-SOP), {len(_later)} not yet issuable "
          f"({sum(1 for r in _later if r['series'] == 'initial release')} initial, {sum(1 for r in _later if r['series'] != 'initial release')} retest)")
    print(f"CoQ register: {len(_cq_ok)} numbered (CoQ-PP_26-001 … {_cq_ok[-1]['code'][-3:] if _cq_ok else '—'}; "
          f"{sum(1 for r in _cq_ok if r['group'] == 'legacy' and not r['coq_flag'])} legacy on 27.05.2026, "
          f"{sum(1 for r in _cq_ok if r['group'] == 'legacy' and r['coq_flag'])} legacy moved, "
          f"{sum(1 for r in _cq_ok if r['group'] != 'legacy')} post-SOP), {len(_cq_later)} not yet issuable "
          f"({sum(1 for r in _cq_later if r['series'] == 'initial release')} initial: "
          f"{sum(1 for r in _cq_ok if r['gaps'])} numbered with an initial certificate to locate; "
          f"{sum(1 for r in _cq_later if r['series'] != 'initial release')} retest)")
    print("adherence flags:", len(FLAGS))
    for _f in FLAGS:
        print("   ", _f)
    # the in-house instance carries the register code (or the at-issue placeholder); the tracker
    # cell that cites it is a lookup into the register by KEY (INST_KEY), so it follows a renumbering
    INST_KEY = {}
    for b, key, scope, vals, _ldate, row in _pending_inst:
        ref = row["code"] if row["code"].startswith("iCoA-PP_") else f"iCoA — at issue ({row['p'] if row['p'].startswith('P0') else row['cu']})"
        ck = T.nkey(ref)
        INST_KEY[ck] = row["key"]
        for n in scope:
            if ck not in {T.nkey(c) for c, d, l in b["docs"][n]}:
                b["docs"][n].append((ref, _ldate, "PP"))
        INDEX_DOCS[key].append((ref, _ldate, "PP", set(scope)))
        COVERS[(key, ck)] = set(scope)
        V8VAL[(b["cu"], ck)] = {str(n): vals[str(n)] for n in scope}
        ADDED[id(b)].append((ref, _ldate, "PP"))
        if b not in NEW_TOUCHED:
            NEW_TOUCHED.append(b)


# --------------------------------------------------------------------------- credit corrections
# Two corrections to the owner's credit table, each applied only where the evidence is
# explicit, each recorded on the "Credit Corrections" sheet, and neither written back to
# the owner's workbook. A removed credit does not remove the document: it still appears as
# a testing instance, marked "on file, not credited".
LOD_RX = re.compile(r"LoD|ГС", re.I)
K_RX = re.compile(r"(^|\D)\d+-\d+-[KК]-\d+")
corrections = []


def _reports(b, code, pno):
    lab = next((l for c, d, l in b["docs"][pno] if c == code), "")
    vals = values_of(code, lab, b["cu"], scope_of(b, code))
    return any(vals.get(no) for no in T.GROUPS[pno])


def apply_credit_corrections(batches):
    """R1  The Farmahem pair is credited jointly for #3–#6 and #8, but the "K" certificate
           reports identification C, THC, CBD and CBN, and the "LoD" certificate reports
           loss on drying alone. Each keeps only what it reports.
       R2  Identification B is credited to CNP certificates that carry no microscopy row.
           The credit is removed there, and kept on the certificates that do report it
           (ППК26110–26119, ППК26127–26128), where the laboratory's newer report format
           carries the determination."""
    for b in batches:
        for p in T.PARAMS:
            keep = []
            for c, d, l in b["docs"][p["n"]]:
                rule = why = None
                if LOD_RX.search(c) and p["n"] != 8 and not _reports(b, c, p["n"]):
                    rule, why = "R1 Farmahem pair", "loss-on-drying certificate; reports no such determination"
                elif K_RX.search(c) and p["n"] == 8 and not _reports(b, c, 8):
                    rule, why = "R1 Farmahem pair", "cannabinoid certificate; loss on drying is on the LoD certificate"
                elif p["n"] == 2 and l == "CNP" and not _reports(b, c, 2):
                    rule, why = "R2 CNP identification B", "no microscopy row on this certificate"
                if rule:
                    corrections.append((b["cu"], b["p"], c, d, l, p["n"], p["title"], rule, why))
                else:
                    keep.append((c, d, l))
            b["docs"][p["n"]] = keep
    return batches


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

batches = apply_credit_corrections(batches)
print(f"credit corrections applied: {len(corrections)} "
      f"({collections.Counter(c[7] for c in corrections)})")

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
        put(ws, 4, p["start"], "Result", FSUB, SUBHDR)                       # the owner's labels (v9, 04.09.2026)
        put(ws, 4, p["start"] + 1, "[eCOA code],[date],[Lab] ", FSUB, SUBHDR)
    put(ws, 3, p["end"], "", F6I, GREY)
    put(ws, 4, p["end"], "✓   ✗", FSUB, SUBHDR)
for h, height in ((1, 16), (2, 30), (3, 26), (4, 24)):
    ws.row_dimensions[h].height = height

# ---- body: one block of two rows per testing instance, batches boxed together
row = 5
stats = collections.Counter()
oos_rows = []
audit = []
LOT_STATE = {}      # lot -> {"pstate": {n: green|orange|amber|red}, "codes": {code: lab}}
SPAN = {}
for _cu, _pb, _code, _date, _lab, _pno in NEW_NONCONF:
    audit.append((_cu, _pb, _code, _date, _lab, _pno,
                  next(p["title"] for p in T.PARAMS if p["n"] == _pno), "non-conformance reported"))
for _cu, _pb, _code, _date, _lab, _pno in NEW_HELD:
    audit.append((_cu, _pb, _code, _date, _lab, _pno,
                  next(p["title"] for p in T.PARAMS if p["n"] == _pno), "held for review"))
BLANK = "FFFFFF"
for b in batches:
    docs = {p["n"]: instances(b, p["n"]) for p in T.PARAMS}
    K = max([len(v) for v in docs.values()] + [1])
    extra = len({(x[0], x[1]) for v in docs.values() for x in v if not x[3]})
    first, last = row, row + 2 * K - 1
    SPAN[id(b)] = (first, last)

    for cidx, v, font in ((1, b["cu"], FWS), (2, b["p"], FWS), (3, None, FWS)):
        if cidx != 3:
            ws.merge_cells(start_row=first, start_column=cidx, end_row=last, end_column=cidx)
            put(ws, first, cidx, v, font, NAVY)
            fill_range(ws, first, cidx, last, cidx, NAVY)

    no_cert = cert_no_result = stab_only = missing = 0
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
            st = "orange"; stab_only += 1
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
            if state == "none":
                continue                       # an empty later block: no cells, no styles
            fill = FILL[state] if state in FILL else BLANK
            glyph = {"green": "✓", "orange": "✓", "amber": "✗", "red": "✗", "extra": "•"}.get(state, "")
            gfill = GLYPHFILL[state] if state in GLYPHFILL else BLANK
            ref = (f"{code}, ({date}) [{lab}]" + ("" if here[3] else " · on file, not credited")) if here \
                else ("— no certificate —" if state == "red" else "")
            ref_disp = ref
            if here and ICOA_RULE and T.nkey(code) in INST_KEY:
                ref = ("=IFERROR(INDEX('iCoA Register'!$B:$B,MATCH(\"%s\",'iCoA Register'!$%s:$%s,0)),\"iCoA — at issue\")&\", (%s) [PP]\""
                       % (INST_KEY[T.nkey(code)], REG_KEY_COL, REG_KEY_COL, date))

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
                bot_lines = max(bot_lines, nlines(ref_disp, 8.6 * (len(p["subs"]) - 1) + 21))
            else:
                no = str(p["n"])
                if here:
                    v = values_of(here[0], here[2], b["cu"], scope_of(b, here[0])).get(no)
                    cell_v = v or silence_reason(here[0], here[2], b["cu"], no)
                    if ICOA_RULE and p["n"] == 3 and str(cell_v).startswith("Conforms"):
                        cell_v = str(cell_v).replace("Conforms", "Conforms (ImB spec.)", 1)
                    _sz = RESULT_PT.get(p["n"], 7)
                    font = (Font(name="Calibri", size=_sz, bold=True, color=RED) if T.over_limit(no, v or "") else
                            Font(name="Calibri", size=_sz, bold=True, color="B45F06") if T.undetermined(no, v or "") else
                            Font(name="Calibri", size=_sz, bold=True))
                else:
                    cell_v = "— MISSING —" if state == "red" else ""
                    font = FBAD if state == "red" else F7
                ws.merge_cells(start_row=top, start_column=p["start"], end_row=bot, end_column=p["start"])
                put(ws, top, p["start"], cell_v, font, fill)
                ws.merge_cells(start_row=top, start_column=p["start"] + 1, end_row=bot, end_column=p["start"] + 1)
                put(ws, top, p["start"] + 1, ref, F6, fill, TOPC)
                fill_range(ws, top, p["start"], bot, p["start"] + 1, fill)
                need = max(nlines(cell_v, 10), nlines(ref_disp, 21))
                if need > top_lines + bot_lines:
                    bot_lines = need - top_lines
                if here and RESULT_PT.get(p["n"], 7) > 7:              # room for the larger result
                    top_lines = max(top_lines, RESULT_PT[p["n"]] / 8.0)

            ws.merge_cells(start_row=top, start_column=p["end"], end_row=bot, end_column=p["end"])
            put(ws, top, p["end"], glyph, FWS, gfill, CEN)
            fill_range(ws, top, p["end"], bot, p["end"], gfill)

        ws.row_dimensions[top].height = max(14, 9.0 * top_lines + 3)
        ws.row_dimensions[bot].height = max(13, 9.0 * bot_lines + 3)
        if i:                                   # a hairline between testing instances
            outline(ws, top, 1, bot, LAST, MED)

    LOT_STATE[id(b)] = {"pstate": dict(pstate),
                        "codes": {c: l for v in docs.values() for c, d, l, cr in v if cr}}
    if missing == 0:
        st, colour = "✓ COMPLETE", STATUSFILL["green"]
    else:
        glyph = "⚠" if missing <= STATUS_PARTIAL_MAX else "✗"
        st = (f"{glyph} {missing} NO RESULT\n({no_cert} no cert / {cert_no_result} cert w/o result"
              + (f" / {stab_only} stability only)" if stab_only else ")"))
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

    for p in T.PARAMS:
        outline(ws, first, p["start"], last, p["end"], MED)
    outline(ws, first, 1, last, LAST, THICK)             # last, so the lot's medium edges win on every column
    # openpyxl gives a merged range the borders of its anchor cell on save, so the lot's medium
    # bottom edge must sit on the anchor of every merged range that ends on the lot's last row
    # (the identity cells A–C, the status cell, the two-row result and glyph merges of the
    # last block) — the owner drew those edges by hand in v9 and v10
    for _mr in ws.merged_cells.ranges:
        if _mr.max_row == last and _mr.min_row >= first and _mr.min_row < last:
            _an = ws.cell(_mr.min_row, _mr.min_col)
            _an.border = Border(left=_an.border.left, right=_an.border.right, top=_an.border.top, bottom=THICK)
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
    "non-conformance reported": "The certificate reports a result that does not conform. Open an investigation record; the "
                                "Head of QC rules on the lot, and the iCoA for this parameter is held until then.",
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

# --------------------------------------------------------------------------- Credit Corrections
cor = wb.create_sheet("Credit Corrections", wb.sheetnames.index("Credit Audit") + 1)
ccols = [("CU Batch", 14), ("P Batch", 14), ("Certificate", 24), ("Date", 11), ("Lab", 8),
         ("#", 5), ("Parameter", 30), ("Correction", 24), ("Evidence", 58)]
for _i, (_t, _w) in enumerate(ccols, 1):
    put(cor, 1, _i, _t, FW, NAVY, CEN)
    cor.column_dimensions[L(_i)].width = _w
cor.row_dimensions[1].height = 22
_r = 2
for cu, pb, code, date, lab, pno, title, rule, why in sorted(corrections, key=lambda x: (x[7], x[0], x[5])):
    put(cor, _r, 1, cu, F7B, None, CEN); put(cor, _r, 2, pb, F7, None, CEN)
    put(cor, _r, 3, code, F7, None, CEN)
    put(cor, _r, 4, T.as_date(date), F7, None, CEN); cor.cell(_r, 4).number_format = "DD.MM.YYYY"
    put(cor, _r, 5, lab, F7, None, CEN); put(cor, _r, 6, f"#{pno}", F7, None, CEN)
    put(cor, _r, 7, title, F7, None, Alignment(horizontal="left", vertical="center", wrap_text=True))
    put(cor, _r, 8, "credit removed", F7B, FILL["amber"], CEN)
    put(cor, _r, 9, f"{rule} — {why}", F6I, None, Alignment(horizontal="left", vertical="center", wrap_text=True))
    _r += 1
cor.auto_filter.ref = f"A1:{L(len(ccols))}{_r - 1}"
cor.freeze_panes = "A2"; cor.print_title_rows = "1:1"
cor.page_setup.orientation = "landscape"; cor.page_setup.fitToWidth = 1; cor.page_setup.fitToHeight = 0
cor.sheet_properties.pageSetUpPr.fitToPage = True
note = ("These corrections are applied when the workbook is built and are NOT written back to the owner's tracker. "
        "A removed credit does not remove the document: it still appears as a testing instance, marked • and "
        "\"on file, not credited\". R1 — the Farmahem pair was credited jointly for #3–#6 and #8, while the K "
        "certificate reports identification C, THC, CBD and CBN and the LoD certificate reports loss on drying alone; "
        "each now keeps only what it reports. R2 — identification B was credited to CNP certificates carrying no "
        "microscopy row; the credit is removed there and kept on ППК26110–26119 and ППК26127–26128, whose newer report "
        "format does carry it. Removing R2 leaves 51 lots with no evidence for identification B at all: those lots need "
        "an in-house iCoA for identification A and B, which is what the issuance plan already foresees.")
cor.merge_cells(start_row=_r + 1, start_column=1, end_row=_r + 1, end_column=len(ccols))
put(cor, _r + 1, 1, note, F6I, GREY, Alignment(horizontal="left", vertical="top", wrap_text=True))
cor.row_dimensions[_r + 1].height = 58
print("credit corrections sheet rows:", _r - 2)

# --------------------------------------------------------------------------- Work Order
# What no rebuild can fix: documents the database holds no read of, and figures the two
# independent reads disagreed on. Each row is a task for the ingestion queue or for a person.
wo = wb.create_sheet("Work Order", wb.sheetnames.index("Credit Corrections") + 1)
wcols = [("Task", 22), ("CU Batch", 14), ("P Batch", 14), ("Certificate", 24), ("Date", 11),
         ("Lab", 8), ("Parameters affected", 26), ("What is needed", 62)]
for _i, (_t, _w) in enumerate(wcols, 1):
    put(wo, 1, _i, _t, FW, NAVY, CEN)
    wo.column_dimensions[L(_i)].width = _w
wo.row_dimensions[1].height = 22
tasks = collections.defaultdict(lambda: {"params": set(), "meta": None})
for cu, pb, code, date, lab, pno, title, why in audit:
    if why not in ("not ingested", "held for review", "non-conformance reported"):
        continue
    k = (why, cu, code)
    tasks[k]["params"].add(pno)
    tasks[k]["meta"] = (pb, date, lab)
for _b in NEW_LOTS:
    for _c, _d, _l in _b["docs"][9]:
        _k = ("lot not on tracker", _b["p"], _c)
        tasks[_k]["params"].add(9)
        tasks[_k]["meta"] = (_b["p"], _d, _l)
NEED = {
    "not ingested": "Re-extract the document into the eCoA database (two independent reads, 300 DPI). "
                    "Until then the lot cannot reach a CoQ on these parameters.",
    "held for review": "The two independent reads disagreed. A person must read the figure from the page and confirm it.",
    "non-conformance reported": "The laboratory reports the result as not conforming (Не одговара). A deviation / OOS "
                                "record is needed before this lot's CoQ can issue.",
    "lot not on tracker": "The certificate names a P batch the owner's tracker does not carry. Record the lot "
                          "(cultivation batch code, strain) on the tracker so the certificate is credited under its batch.",
}
_r = 2
for (why, cu, code), d in sorted(tasks.items(), key=lambda x: (x[0][0], x[0][1])):
    pb, date, lab = d["meta"]
    put(wo, _r, 1, why, F7B, FILL["red"] if why == "not ingested" else FILL["amber"], CEN)
    put(wo, _r, 2, cu, F7B, None, CEN); put(wo, _r, 3, pb, F7, None, CEN)
    put(wo, _r, 4, code, F7, None, CEN)
    put(wo, _r, 5, T.as_date(date), F7, None, CEN); wo.cell(_r, 5).number_format = "DD.MM.YYYY"
    put(wo, _r, 6, lab, F7, None, CEN)
    put(wo, _r, 7, ", ".join(f"#{n}" for n in sorted(d["params"])), F7, None, CEN)
    put(wo, _r, 8, NEED[why], F6I, None, Alignment(horizontal="left", vertical="center", wrap_text=True))
    _r += 1
wo.auto_filter.ref = f"A1:{L(len(wcols))}{max(_r - 1, 2)}"
wo.freeze_panes = "A2"; wo.print_title_rows = "1:1"
wo.page_setup.orientation = "landscape"; wo.page_setup.fitToWidth = 1; wo.page_setup.fitToHeight = 0
wo.sheet_properties.pageSetUpPr.fitToPage = True
print("work order rows:", _r - 2)

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

if V9:
    for _n in ("Results Register", "CoQ Parameter Tracker (flat)", "eCOA Document Index"):
        if _n in wb.sheetnames:
            wb.remove(wb[_n])

# --------------------------------------------------------------------------- new instances: the other sheets
from copy import copy as _copy


def _style_from(dst, src):
    dst.font, dst.fill, dst.border, dst.alignment, dst.number_format = \
        _copy(src.font), _copy(src.fill), _copy(src.border), _copy(src.alignment), src.number_format


def patch_coverage(wb):
    """Batch Coverage is inherited from v6: mark the newly covered parameters, recount the
    missing list, the certificate count and the laboratories, and add the lots the owner's
    tracker did not carry."""
    cov = wb["Batch Coverage"]
    last = max(r for r in range(2, cov.max_row + 1) if cov.cell(r, 1).value) if cov.max_row > 1 else 1
    short = {}
    for r in range(2, last + 1):
        for tok in str(cov.cell(r, 18).value or "").split(";"):
            m = re.match(r"\s*#(\d+)\s+(.+)", tok)
            if m:
                short[int(m.group(1))] = m.group(2).strip()
    for p in T.PARAMS:
        short.setdefault(p["n"], p["title"].split(" ", 1)[1])
    tick = next((cov.cell(r, c) for r in range(2, last + 1) for c in range(5, 17)
                 if cov.cell(r, c).value == "✓" and cov.cell(r, c).fill.fgColor.rgb not in (None, "00000000")), None)
    cross = next((cov.cell(r, c) for r in range(2, last + 1) for c in range(5, 17) if cov.cell(r, c).value == "✗"), None)
    status_style = {}
    for r in range(2, last + 1):
        st = str(cov.cell(r, 4).value or "")
        status_style.setdefault(st[:1], cov.cell(r, 4))

    def rowkey(cu, p):
        return (re.sub(r"[＊*]", "", cu).strip(), "— not assigned —" if p.startswith("N/A") else p.strip())

    rows, _dups = {}, []
    for r in range(2, last + 1):
        k = rowkey(str(cov.cell(r, 1).value or ""), str(cov.cell(r, 2).value or ""))
        if k in rows:
            _dups.append(r)                 # the owner's re-analysis row of a lot the tracker already merged
        else:
            rows[k] = r

    def recount(r):
        # ○ is the owner's own third mark, from Batch Coverage v19: a certificate
        # is on file for this parameter and the tracker does not name it. It is
        # not coverage — nothing can be cited on a certificate of quality until
        # the desk records the document — so it counts as missing and says why.
        miss = [n for n in range(1, 13) if cov.cell(r, 4 + n).value in ("✗", "○")]
        onfile = {n for n in range(1, 13) if cov.cell(r, 4 + n).value == "○"}
        cov.cell(r, 17).value = len(miss)
        cov.cell(r, 18).value = "; ".join(
            f"#{n} {short[n]}" + (" (on file 09.09, not recorded)" if n in onfile else "")
            for n in miss) or "—"
        st = "✓ COMPLETE" if not miss else (
            f"○ {len(miss)} ON FILE, NOT RECORDED" if set(miss) == onfile else
            (f"⚠ {len(miss)} MISSING" if len(miss) <= 3 else f"❌ {len(miss)} MISSING"))
        cell = cov.cell(r, 4)
        cell.value = st
        if st[:1] in status_style:
            _style_from(cell, status_style[st[:1]])

    for b in NEW_TOUCHED:
        new_docs = sorted(set(ADDED.get(id(b), [])))
        if b.get("new_lot"):
            r = last + 1
            last = r
            src = next((rr for rr in range(2, r) if str(cov.cell(rr, 4).value or "").startswith("❌")), 2)
            for c in range(1, 21):
                _style_from(cov.cell(r, c), cov.cell(src, c))
            cov.cell(r, 1).value = b["cu"]
            cov.cell(r, 2).value = "— not assigned —" if b["p"].startswith("N/A") else b["p"]
            cov.cell(r, 3).value = b.get("strain", "")
            for n in range(1, 13):
                cell = cov.cell(r, 4 + n)
                cell.value = "✓" if b["docs"][n] else "✗"
                _style_from(cell, tick if b["docs"][n] else cross)
                if b["docs"][n] and all(T.kind_of(c, l, STAB) in ("In-house", "iCoA") for c, d, l in b["docs"][n]):
                    cell.fill = PatternFill("solid", fgColor="E7E6E6")
                    cell.font = Font(name="Calibri", size=9, color="595959")
            cov.cell(r, 19).value = len(new_docs)
            cov.cell(r, 20).value = f"[{new_docs[0][2]}] {len(new_docs)}" if new_docs else ""
            recount(r)
            continue
        r = rows.get(rowkey(b["cu"], b["p"]))
        if r is None:                       # the owner's row names the lot by its P batch only
            _kp = rowkey(b["cu"], b["p"])[1]
            r = next((rr for (kcu, kp), rr in rows.items() if kp == _kp and _kp != "— not assigned —"), None)
        if r is None:
            print("coverage: no row for", b["cu"], b["p"])
            continue
        # ✓ means what the tracker means by it: a credited certificate reports a release result.
        # A certificate credited without a result, and a stability timepoint, are not coverage —
        # the tracker's STATUS counts them as NO RESULT and the two sheets must not disagree.
        _ps = (LOT_STATE.get(id(b)) or {}).get("pstate", {})
        for n in range(1, 13):
            want = "✓" if _ps.get(n, "red") == "green" else "✗"
            if cov.cell(r, 4 + n).value != want:
                cov.cell(r, 4 + n).value = want
                _style_from(cov.cell(r, 4 + n), tick if want == "✓" else cross)
            if want == "✓" and b["docs"][n] and all(T.kind_of(c, l, STAB) in ("In-house", "iCoA") for c, d, l in b["docs"][n]):
                cov.cell(r, 4 + n).fill = PatternFill("solid", fgColor="E7E6E6")
                cov.cell(r, 4 + n).font = Font(name="Calibri", size=9, color="595959")
        cov.cell(r, 19).value = int(cov.cell(r, 19).value or 0) + len(new_docs)
        _cd = (LOT_STATE.get(id(b)) or {}).get("codes") or {}
        if _cd:                              # a merged lot carries the certificates of both its rows
            cov.cell(r, 19).value = len(_cd)
        labs = collections.OrderedDict()
        for tok in str(cov.cell(r, 20).value or "").split(";"):
            m = re.match(r"\s*\[([^\]]+)\]\s*(\d+)", tok)
            if m:
                labs[m.group(1)] = int(m.group(2))
        for c, d, l in new_docs:
            labs[l] = labs.get(l, 0) + 1
        if _cd:
            labs = collections.Counter(_cd.values())
        cov.cell(r, 20).value = "; ".join(f"[{k}] {v}" for k, v in sorted(labs.items()))
        recount(r)
    for r in range(2, last + 1):           # one name per thing: the tracker's label for a lot without a CU code
        _cu = str(cov.cell(r, 1).value or "")
        if _cu.startswith("—"):
            _p = str(cov.cell(r, 2).value or "").strip()
            _b = next((b for b in batches if _p and _p in (b["p"] or "")), None)
            if _b and _b["cu"] != _cu:
                cov.cell(r, 1).value = _b["cu"]
    for r in sorted(_dups, reverse=True):   # one row per lot
        cov.delete_rows(r)
        last -= 1
    if _dups:
        print(f"coverage: {len(_dups)} duplicate row(s) removed (the owner's re-analysis rows of merged lots)")

    # The owner's 09.09.2026 pass over eCoA_DATABASE names, per lot and per
    # parameter, a certificate on file that the coverage sheet still marks ✗.
    # Applied last, after the duplicate rows are gone, so the row map is the one
    # the finished sheet has; a closure that finds no row is reported, never
    # invented. See coverage_update_2026-09-09.tsv and the Reconciliation sheet.
    if CELLS_0909:
        by_row, by_key = {}, {}
        for r in range(2, last + 1):
            k = rowkey(str(cov.cell(r, 1).value or ""), str(cov.cell(r, 2).value or ""))
            by_row[k] = r
            by_key.setdefault(T.cu_key(k[0]), r)
            _p = str(cov.cell(r, 2).value or "").strip()
            if _p and not _p.startswith("—"):
                by_key.setdefault("P:" + _p, r)
        touched = set()
        for u in load_coverage_update():
            # The sheet's second block names several parameters in one cell —
            # the lots it carried no row for at all, closed wholesale by one
            # certificate. Every number in the cell is a parameter.
            nums = [int(x) for x in re.findall(r"#(\d+)", u["Parameter"])]
            if not nums:
                continue
            r = by_row.get(rowkey(u["CU batch"], u["P batch"])) \
                or by_key.get(T.cu_key(u["CU batch"])) \
                or by_key.get("P:" + u["P batch"].strip())
            if r is None:
                COV_0909_SKIPPED.append((u, "no row on Batch Coverage"))
                continue
            lab = re.search(r"\[([^\]]+)\]\s*$", u["Now covered by"].strip())
            for n in nums:
                cell = cov.cell(r, 4 + n)
                if cell.value == "✓":
                    COV_0909_SKIPPED.append((u, "#%d already covered" % n))
                    continue
                cell.value = "○"
                _style_from(cell, cross)
                cell.fill = PatternFill("solid", fgColor=FILL["amber"])
                cell.font = Font(name="Calibri", size=9, bold=True, color="B45F06")
                COV_0909_APPLIED.append((u, r, lab.group(1) if lab else ""))
                touched.add(r)
        for r in sorted(touched):
            cov.cell(r, 19).value = int(cov.cell(r, 19).value or 0) + \
                len({u["Now covered by"] for u, rr, _ in COV_0909_APPLIED if rr == r})
            labs = collections.OrderedDict()
            for tok in str(cov.cell(r, 20).value or "").split(";"):
                m2 = re.match(r"\s*\[([^\]]+)\]\s*(\d+)", tok)
                if m2:
                    labs[m2.group(1)] = int(m2.group(2))
            for _u, rr, lab in COV_0909_APPLIED:
                if rr == r and lab:
                    labs[lab] = labs.get(lab, 0) + 1
            cov.cell(r, 20).value = "; ".join(f"[{k}] {v}" for k, v in sorted(labs.items()))
            recount(r)
        print(f"coverage update 09.09: {len(COV_0909_APPLIED)} parameter(s) marked ○ "
              f"(on file, not recorded) on {len(touched)} lot(s); "
              f"{len(COV_0909_SKIPPED)} not applied")

    if cov.auto_filter.ref:
        cov.auto_filter.ref = f"A1:{L(20)}{last}"
    return last


def patch_dashboard(wb, last):
    cov, dash = wb["Batch Coverage"], wb["Summary Dashboard"]
    n = last - 1
    marks = {p: [cov.cell(r, 4 + p).value for r in range(2, last + 1)] for p in range(1, 13)}
    missing = [sum(1 for p in range(1, 13) if cov.cell(r, 4 + p).value == "✗") for r in range(2, last + 1)]
    complete = sum(1 for m in missing if m == 0)
    partial = sum(1 for m in missing if 1 <= m <= 3)
    incomplete = sum(1 for m in missing if m >= 4)
    for r in range(1, dash.max_row + 1):
        label = str(dash.cell(r, 1).value or "")
        if label == "Total Batches":
            dash.cell(r, 2).value = n
        elif label == "Total eCOA Documents":
            dash.cell(r, 2).value = int(dash.cell(r, 2).value or 0) + len({x["code"] for x in NEW})
        elif label.startswith("✅"):
            dash.cell(r, 2).value = complete; dash.cell(r, 3).value = f"{round(100 * complete / n)}% of batches"
        elif label.startswith("⚠"):
            dash.cell(r, 2).value = partial; dash.cell(r, 3).value = f"{round(100 * partial / n)}% of batches"
        elif label.startswith("❌"):
            dash.cell(r, 2).value = incomplete; dash.cell(r, 3).value = f"{round(100 * incomplete / n)}% of batches"
        else:
            m = re.match(r"#(\d+)\s", label)
            if m:
                p = int(m.group(1))
                k = sum(1 for v in marks[p] if v == "✗")
                dash.cell(r, 2).value = k
                dash.cell(r, 3).value = f"({round(100 * k / n)}% of batches missing this)"


def add_mikro(wb, src_path):
    """Rebuild the owner's 'Mikro CoQ Parameter' sheet from the tracker: the same lots, the
    identity columns and the #7–#12 blocks, copied cell for cell from the rebuilt tracker."""
    src = openpyxl.load_workbook(src_path, read_only=True)
    if "Mikro CoQ Parameter" not in src.sheetnames:
        return 0
    want = []
    for row in src["Mikro CoQ Parameter"].iter_rows(min_row=1, max_row=400, values_only=True):
        cu, p = str(row[0] or "").strip(), str(row[1] or "").strip()
        if cu and cu not in ("BATCH IDENTIFICATION", "CU Batch #") and not cu.startswith("KEY"):
            want.append((cu, p))
    src.close()
    lots = []
    for cu, p in want:
        cu0 = re.sub(r"[＊*]", "", cu)
        for b in batches:
            bp = "/" if b["p"].startswith("N/A") else b["p"]
            if (cu0 == re.sub(r"[＊*]", "", b["cu"]) and (p in ("", "/", bp) or p == "N/A — no P batch assigned" and bp == "/")) \
               or (cu0 == "— not recorded —" and p == bp) or (cu0 == "— not recorded —" and p and p in b["p"]):
                if b not in lots:
                    lots.append(b)
                break
    if "Mikro CoQ Parameter" in wb.sheetnames:
        wb.remove(wb["Mikro CoQ Parameter"])
    dst = wb.create_sheet("Mikro CoQ Parameter", wb.sheetnames.index(SHEET) + 1)
    p7, p12 = next(p for p in T.PARAMS if p["n"] == 7), next(p for p in T.PARAMS if p["n"] == 12)
    cols = [1, 2, 3] + list(range(p7["start"], p12["end"] + 1))
    cmap = {c: i + 1 for i, c in enumerate(cols)}
    rows = [1, 2, 3, 4]
    for b in lots:
        if id(b) in SPAN:
            rows += list(range(SPAN[id(b)][0], SPAN[id(b)][1] + 1))
    key_row = next((r for r in range(ws.max_row, 4, -1) if str(ws.cell(r, 1).value or "").startswith("KEY")), None)
    if key_row:
        rows.append(key_row)                 # the legend travels with the sheet
    rmap = {r: i + 1 for i, r in enumerate(rows)}
    for r in rows:
        for c in cols:
            sc, dc = ws.cell(r, c), dst.cell(rmap[r], cmap[c])
            dc.value = sc.value
            _style_from(dc, sc)
        if ws.row_dimensions[r].height:
            dst.row_dimensions[rmap[r]].height = ws.row_dimensions[r].height
    for rng in ws.merged_cells.ranges:
        if rng.min_row in rmap and rng.max_row in rmap and rng.min_col in cmap:
            dst.merge_cells(start_row=rmap[rng.min_row], start_column=cmap[rng.min_col],
                            end_row=rmap[rng.max_row], end_column=cmap.get(rng.max_col, len(cols)))
    for c in cols:
        w = ws.column_dimensions[L(c)].width
        if w:
            dst.column_dimensions[L(cmap[c])].width = w
    dst.freeze_panes = "D5"
    dst.sheet_view.zoomScale = ws.sheet_view.zoomScale
    matched = {(re.sub(r"[＊*]", "", b["cu"]), b["p"]) for b in lots}
    print(f"Mikro CoQ Parameter: {len(lots)} of {len(want)} lot(s) matched, {len(rows) - 4} row(s)")
    for cu, p in want:
        if not any(re.sub(r"[＊*]", "", cu) == mcu or (cu == "— not recorded —" and p in mp) for mcu, mp in matched):
            print("   not matched:", repr(cu), repr(p))
    return len(lots)


def _lookup_f(sheet, col, keycol, key, default):
    """A cell that follows a register: column `col` of the row whose key column holds `key`."""
    return f'=IFERROR(INDEX(\'{sheet}\'!${col}:${col},MATCH("{key}",\'{sheet}\'!${keycol}:${keycol},0)),"{default}")'


def REG_LOOKUP(col, key, default):
    return _lookup_f("iCoA Register", col, REG_KEY_COL, key, default)


def COQ_LOOKUP(col, key, default):
    return _lookup_f("CoQ Register", col, COQ_KEY_COL, key, default)


def _date(v):
    import datetime as _dt
    try:
        return _dt.datetime.strptime(str(v), "%d.%m.%Y").date()
    except ValueError:
        return None


def add_icoa_sheet(wb):
    sh = wb.create_sheet("iCoA Issuance", wb.sheetnames.index("Work Order") + 1)
    icols = [("Seq", 6), ("Series", 20), ("iCoA", 20), ("CoQ", 20), ("Plan references (31.08.2026)", 30), ("Group", 10),
             ("Basis date", 12), ("Test date (packaging)", 14), ("iCoA issue (planned)", 16), ("CoQ issue (planned)", 16),
             ("CU Batch", 16), ("P Batch", 22), ("Strain", 20), ("Harvest", 24), ("Packaging", 28), ("Packaging complete", 18),
             ("iCoA scope", 30), ("#1 Ident. A", 14), ("#2 Ident. B", 14), ("#7 Foreign matter", 16),
             ("Ident C — covered by (eCoA)", 34), ("Retest assay #4–#6 (eCoA)", 34), ("Retest mycotoxins #10 (eCoA)", 34),
             ("Carried forward", 30), ("Status", 48)]
    keys = ("seq", "series", "icoa", "coq", "plan_refs", "group", "basis", "test_date", "issue", "coq_issue", "cu", "p", "strain",
            "harvest", "packaging", "complete", "scope", "a", "b", "fm", "c", "assay_rt", "myco_rt", "carry", "status")
    for _i, (_t, _w) in enumerate(icols, 1):
        put(sh, 1, _i, _t, FW, NAVY, CEN)
        sh.column_dimensions[L(_i)].width = _w
    sh.row_dimensions[1].height = 22
    _r = 2
    for row in ICOA_ROWS:
        row["plan_refs"] = " / ".join(x for x in (row.get("plan_ref", ""), row.get("coq_plan", "")) if x and not x.startswith("—")) or "—"
        row["coq"] = COQ_LOOKUP("B", row["key"], "—")
        row["coq_issue"] = COQ_LOOKUP("D", row["key"], "")
        for _i, k in enumerate(keys, 1):
            v = row[k]
            if k == "icoa" and v != "not needed":
                v = REG_LOOKUP("B", row["key"], "— at issue —")           # the code follows the register
            if k == "issue" and row.get("issuable") == "yes":
                v = REG_LOOKUP("D", row["key"], "")                        # so does the planned date
            if k == "test_date" and row["series"] != "initial release":
                v = "at retest sampling"
            c = put(sh, _r, _i, v, F7B if k in ("icoa", "coq", "cu") else F7,
                    FILL["amber"] if (k == "fm" and v == "held for review") or (k in ("c", "assay_rt", "myco_rt", "harvest", "packaging", "complete") and str(v).startswith("—"))
                    or (k == "status" and str(v).startswith(("pending", "not yet"))) else
                    (FILL["green"] if k == "status" and str(v).startswith(("due", "registered")) else
                     (FILL["extra"] if k in ("a", "b", "fm") and str(v).startswith("CNP ") else None)), CEN)
            if k in ("issue", "coq_issue") and str(v).startswith("="):
                c.number_format = "DD.MM.YYYY"
        _r += 1
    note = ("Head of QC, 05.09.2026 (confirming 04.09.2026): ONE iCoA per P lot carries identification A, identification B and "
            "foreign matter, tested at packaging (the first day, when the sample is taken before primary packaging); where a "
            "CNP certificate reports one of them, its document code is the reference and the iCoA covers the rest; where CNP "
            "reports all three, no iCoA is needed. Identification C is 'Conforms', referenced to the eCoA that covers Total THC "
            "(the cannabinoid assay), on the CoQ. LEGACY lots — packed before the SOP floor of 11.05.2026, or holding an old "
            "in-house QCCoA 001 certificate — have their iCoAs issued together on 15.05.2026 and their CoQs (CoQ-PP_26-nnn, "
            "superseding the old certificate) on 27.05.2026; POST-SOP lots have the iCoA issued on the first working day 5 days "
            "after packaging and the CoQ on the first working day 7 days after the latest eCoA it cites. The codes and the "
            "planned dates on this sheet are looked up on the iCoA Register and the CoQ Register by the row's key and follow "
            "a renumbering there. The RETEST SERIES (the QP's campaign: medical use, GACP product / API) repeats the iCoA and "
            "the CoQ per lot at the retest sampling, sampled by tranche from July 2026 (Tranche 1 the first 21 lots produced, then "
            "Tranches 2 and 3): identification A, B and foreign matter are tested in-house on every bag of the representative "
            "sample (one iCoA); Farmahem tests the cannabinoids — identification C with them — and the mycotoxins, IJZ-MB the "
            "microbiology; the reissued CoQ carries those retest results and the initial external certificates for the rest. A "
            "certificate dated on or after 01.07.2026 is a retest document and never certifies the initial CoQ. A retest document "
            "takes a new number in the year of issue, never the initial one. "
            "'due' where the retest certificates are on file, 'pending' where they are not. Foreign matter is 'Conforms' by the "
            "declaration of 13.08.2026 unless an outsourced certificate reports otherwise.")
    sh.merge_cells(start_row=_r + 1, start_column=1, end_row=_r + 1, end_column=len(icols))
    put(sh, _r + 1, 1, note, F6I, GREY, Alignment(horizontal="left", vertical="top", wrap_text=True))
    sh.row_dimensions[_r + 1].height = 84
    sh.auto_filter.ref = f"A1:{L(len(icols))}{_r - 1}"
    sh.freeze_panes = "A2"
    print("iCoA issuance rows:", _r - 2)


REG_COLS = [("No.", 6), ("iCoA code", 18), ("Issuable", 9), ("Issue date (planned)", 18), ("Test date (packaging)", 16),
            ("Packaging complete", 16), ("Group", 10), ("Series", 20), ("CU Batch", 16), ("P Batch", 12), ("Strain", 20),
            ("iCoA scope", 30), ("CNP reference", 26), ("CoQ (register)", 16), ("Plan reference (31.08.2026)", 22),
            ("Key", 14), ("Status", 60)]
COQ_COLS = [("No.", 6), ("CoQ code", 18), ("Issuable", 9), ("Issue date (planned)", 18), ("Rule date", 14),
            ("Latest eCoA cited (date)", 16), ("Latest eCoA cited (code)", 22), ("iCoA (register)", 16), ("iCoA issue date", 14),
            ("Group", 10), ("Series", 20), ("CU Batch", 16), ("P Batch", 12), ("Strain", 20), ("Ident C — eCoA (Total THC)", 34),
            ("CNP references", 26), ("Supersedes (old in-house CoA)", 26), ("Plan reference (31.08.2026)", 22), ("Key", 14),
            ("Status", 64)]
REG_NOTE = ("Head of QC, 05.09.2026: preliminary iCoA issuance register — ONE iCoA per P lot for identification A, B and foreign "
            "matter, tested at packaging (the first day). Codes iCoA-PP_26-nnn (nnn = 001 … 999), one series for the year of "
            "issue, in the order of issue: LEGACY lots (packed before the SOP floor of 11.05.2026, or holding an old in-house "
            "QCCoA 001 certificate) are all issued on 15.05.2026, in chronological order of packaging; POST-SOP lots follow, each "
            "on the first working day 5 days after its packaging. No number is reserved for a row that cannot be issued yet (a lot "
            "without a packaging date, a held result, every retest iCoA, whose sampling date is not on the desk); where a CNP "
            "certificate reports all three, no iCoA is needed. FORMULAS: No. counts the issuable rows above it; the code is built "
            "from No.; the planned date is 15.05.2026 for a legacy row, else the first working day 5 days after Packaging complete; "
            "the packaging dates are looked up on Batch Dates by P batch (else by the batch as listed); CoQ (register) is looked up on "
            "the CoQ Register by Key. Insert a row, set Issuable to yes, and every code beneath moves by one — the iCoA Issuance "
            "sheet and the tracker cite this register by Key, so they follow. Rows are not re-sorted by a formula: a changed date "
            "that changes the order is a manual move. Working days are Monday to Friday; public holidays are not applied.")
COQ_NOTE = ("Head of QC, 05.09.2026: preliminary CoQ issuance register — codes CoQ-PP_26-nnn (nnn = 001 … 999), one series for the "
            "year of issue, in the order of issue. LEGACY lots (packed before the SOP floor of 11.05.2026, or holding an old "
            "in-house QCCoA 001 certificate, which the CoQ supersedes) are all issued on 27.05.2026, in chronological order of "
            "packaging; POST-SOP lots follow, each on the first working day 7 days after the latest eCoA the CoQ cites and never "
            "before 27.05.2026, so the legacy series keeps 001 onward. Every CoQ "
            "cites its lot's iCoA (identification A, B, foreign matter) and reports identification C as 'Conforms', referenced to "
            "the eCoA that covers Total THC. ADHERENCE (ISSUE_COQ_CONVENTIONS): a CoQ never precedes a document it cites — a legacy "
            "lot whose latest eCoA is dated after 27.05.2026 takes the post-SOP rule and is flagged in Status; a CoQ never precedes "
            "its iCoA; Head of QC, 05.09.2026 (evening): a production lot whose initial certificate for a determination is not on "
            "file keeps its planned CoQ and number — the initial testing exists at the Faculty of Pharmacy's Center for Natural "
            "Products (microbiology: IJZ) and the certificate is to be located (Work Order; Status names the determination); a "
            "certificate dated on or after 01.07.2026 is a retest document (the QP's campaign: Tranche 1, the first 21 lots, sampled "
            "July 2026; then Tranches 2 and 3) and never certifies the initial CoQ — a determination whose only certificate is a "
            "retest one is uncertified for the legacy CoQ and flagged; the IJZ-MB delivery of 25/26.08.2026 (certificates of 31.08 and "
            "01.09.2026, 68 to 436 days after packaging) is one campaign sampling and every certificate in it is a retest document, "
            "for the post-SOP lots too; nothing is dated on a weekend. RETEST ROWS: the reissued CoQ "
            "carries the retest results (cannabinoids with identification C by Farmahem, mycotoxins, microbiology by IJZ-MB) and the "
            "initial certificates for the rest; its rule date is the first working day 7 days after the latest retest certificate, "
            "and it is issued once the in-house retest iCoA exists. FORMULAS: No. and the code as on the iCoA Register; Rule date is 27.05.2026 for a legacy row "
            "whose latest eCoA is on or before it, else the first working day 7 days after the latest eCoA (not before 27.05.2026); the planned date is the "
            "latest of the rule date, the iCoA's date and the lot's last day of packaging; iCoA (register) and its date are looked up on the iCoA Register by Key. "
            "The latest eCoA cited is a value (the first credited certificate per determination dated before the retest campaign; "
            "for a retest row, the latest retest certificate), recomputed by the builder. Working days are Monday to Friday; public holidays are not applied.")


def _roll(expr):
    """The first working day on or after the date expression (Mon–Fri): Saturday +2, Sunday +1."""
    return f"({expr})+CHOOSE(WEEKDAY({expr},2),0,0,0,0,0,2,1)"


def _fill_register(sh):
    """The iCoA register as an Excel table whose number, code and dates are formulas."""
    from openpyxl.worksheet.table import Table, TableStyleInfo
    for _i, (_t, _w) in enumerate(REG_COLS, 1):
        put(sh, 1, _i, _t, FW, NAVY, CEN)
        sh.column_dimensions[L(_i)].width = _w
    sh.row_dimensions[1].height = 22
    BD_ = "'Batch Dates'"
    _r = 2
    for r in REGISTER:
        f_no = f'=IF(C{_r}="yes",COUNT(A$1:A{_r - 1})+1,"")'
        f_code = f'=IF(A{_r}<>"","iCoA-PP_26-"&TEXT(A{_r},"000"),IF(C{_r}="n/a","not needed","— at issue —"))'
        f_issue = f'=IF(A{_r}="","",IF(G{_r}="legacy",DATE(2026,5,15),IF(ISNUMBER(F{_r}),{_roll(f"F{_r}+5")},"")))'
        f_from = (f'=IFERROR(INDEX({BD_}!$F:$F,MATCH(J{_r},{BD_}!$C:$C,0)),'
                  f'IFERROR(INDEX({BD_}!$F:$F,MATCH(I{_r},{BD_}!$B:$B,0)),""))')
        f_to = (f'=IFERROR(INDEX({BD_}!$G:$G,MATCH(J{_r},{BD_}!$C:$C,0)),'
                f'IFERROR(INDEX({BD_}!$G:$G,MATCH(I{_r},{BD_}!$B:$B,0)),""))')
        cells = (f_no, f_code, r["issuable"], f_issue, f_from if r["series"] == "initial release" else "at retest sampling", f_to,
                 r["group"], r["series"], r["cu"], r["p"], r["strain"], r["scope"], r["cnp"],
                 COQ_LOOKUP("B", r["key"], "—"), r.get("plan_ref") or "—", r["key"], r["reg_status"])
        for _i, v in enumerate(cells, 1):
            c = put(sh, _r, _i, v, F7B if _i in (2, 9) else F7,
                    FILL["green"] if (_i == 17 and str(v).startswith("registered")) or (_i == 3 and v == "yes") else
                    FILL["amber"] if (_i == 17 and str(v).startswith("not yet")) or (_i == 3 and v == "no")
                    or (_i in (13, 15) and str(v).startswith("—")) else None,
                    CEN if _i != 17 else Alignment(horizontal="left", vertical="center", wrap_text=True))
            if _i in (4, 5, 6):
                c.number_format = "DD.MM.YYYY"
        _r += 1
    tab = Table(displayName="iCoA_Register", ref=f"A1:{L(len(REG_COLS))}{_r - 1}")
    tab.tableStyleInfo = TableStyleInfo(name="TableStyleLight1", showFirstColumn=False, showLastColumn=False,
                                        showRowStripes=False, showColumnStripes=False)
    sh.add_table(tab)
    sh.merge_cells(start_row=_r + 1, start_column=1, end_row=_r + 1, end_column=len(REG_COLS))
    put(sh, _r + 1, 1, REG_NOTE, F6I, GREY, Alignment(horizontal="left", vertical="top", wrap_text=True))
    sh.row_dimensions[_r + 1].height = 110
    sh.freeze_panes = "C2"
    return _r - 2


def _fill_coq_register(sh):
    """The CoQ register as an Excel table whose number, code and dates are formulas."""
    from openpyxl.worksheet.table import Table, TableStyleInfo
    for _i, (_t, _w) in enumerate(COQ_COLS, 1):
        put(sh, 1, _i, _t, FW, NAVY, CEN)
        sh.column_dimensions[L(_i)].width = _w
    sh.row_dimensions[1].height = 22
    _r = 2
    for r in COQ_REGISTER:
        f_no = f'=IF(C{_r}="yes",COUNT(A$1:A{_r - 1})+1,"")'
        f_code = f'=IF(A{_r}<>"","CoQ-PP_26-"&TEXT(A{_r},"000"),"— at issue —")'
        f_rule = (f'=IF(ISNUMBER(F{_r}),IF(AND(J{_r}="legacy",F{_r}<=DATE(2026,5,27)),DATE(2026,5,27),MAX(DATE(2026,5,27),{_roll(f"F{_r}+7")})),'
                  f'IF(J{_r}="legacy",DATE(2026,5,27),""))')
        _pkc = f"INDEX('iCoA Register'!$F:$F,MATCH(S{_r},'iCoA Register'!${REG_KEY_COL}:${REG_KEY_COL},0))"
        f_issue = f'=IF(A{_r}="","",MAX(E{_r},IF(ISNUMBER(I{_r}),I{_r},0),IFERROR(IF(ISNUMBER({_pkc}),{_roll(_pkc)},0),0)))'
        latest_d = _date(r["latest"][1]) if r["latest"] else None
        status = (r["reg_status"] if r["series"] == "initial release" else
                  "not yet issuable — " + r["rt_status"] + " · issued on the first working day 7 days after the latest retest certificate, once the in-house iCoA exists")
        f_rule_rt = f'=IF(ISNUMBER(F{_r}),MAX(DATE(2026,5,27),{_roll(f"F{_r}+7")}),"at retest sampling")'
        cells = (f_no, f_code, r["issuable"] if r["series"] == "initial release" else "no", f_issue,
                 f_rule if r["series"] == "initial release" else f_rule_rt,
                 latest_d or ("—" if r["series"] == "initial release" else "— not yet sampled —"), (r["latest"][0] if r["latest"] else "—"),
                 REG_LOOKUP("B", r["key"], "—"), REG_LOOKUP("D", r["key"], ""),
                 r["group"], r["series"], r["cu"], r["p"], r["strain"], r["c"], r["cnp"],
                 (f"{r['old'][0]} of {r['old'][1]}" if r.get("old") else "—"), r.get("plan_coq") or "—", r["key"], status)
        for _i, v in enumerate(cells, 1):
            c = put(sh, _r, _i, v, F7B if _i in (2, 12) else F7,
                    FILL["green"] if (_i == 20 and str(v).startswith("registered")) or (_i == 3 and v == "yes") else
                    FILL["amber"] if (_i == 20 and str(v).startswith("not yet")) or (_i == 3 and v == "no")
                    or (_i in (15, 16) and str(v).startswith("—")) else None,
                    CEN if _i != 20 else Alignment(horizontal="left", vertical="center", wrap_text=True))
            if _i in (4, 5, 6, 9):
                c.number_format = "DD.MM.YYYY"
        _r += 1
    tab = Table(displayName="CoQ_Register", ref=f"A1:{L(len(COQ_COLS))}{_r - 1}")
    tab.tableStyleInfo = TableStyleInfo(name="TableStyleLight1", showFirstColumn=False, showLastColumn=False,
                                        showRowStripes=False, showColumnStripes=False)
    sh.add_table(tab)
    note = COQ_NOTE + (" FLAGS: " + " | ".join(FLAGS) if FLAGS else " No adherence flag.")
    sh.merge_cells(start_row=_r + 1, start_column=1, end_row=_r + 1, end_column=len(COQ_COLS))
    put(sh, _r + 1, 1, note, F6I, GREY, Alignment(horizontal="left", vertical="top", wrap_text=True))
    sh.row_dimensions[_r + 1].height = 150
    sh.freeze_panes = "C2"
    return _r - 2


def add_register_sheet(wb):
    sh = wb.create_sheet("iCoA Register", wb.sheetnames.index("iCoA Issuance") + 1)
    print("iCoA register rows:", _fill_register(sh))


def add_coq_register_sheet(wb):
    sh = wb.create_sheet("CoQ Register", wb.sheetnames.index("iCoA Register") + 1)
    print("CoQ register rows:", _fill_coq_register(sh))


def write_register_file(path):
    """The two registers on their own, for the person issuing the documents (with the Batch Dates
    sheet their date formulas look up)."""
    w = openpyxl.Workbook()
    sh = w.active
    sh.title = "iCoA Register"
    _fill_register(sh)
    _fill_coq_register(w.create_sheet("CoQ Register"))
    _fill_dates(w.create_sheet("Batch Dates"))
    rm = w.create_sheet("Read Me")
    rm.column_dimensions["A"].width = 120
    for _i, t in enumerate((f"iCoA and CoQ Issuance Registers — preliminary — built with CoQ Analysis Master v{VER} on 05.09.2026",
                            REG_NOTE, COQ_NOTE + (" FLAGS: " + " | ".join(FLAGS) if FLAGS else ""),
                            "Source: CoQ_Analysis_Master_v" + VER + ".xlsx, sheets iCoA Issuance and Batch Dates; "
                            "dates from the Head of QC's list of 04.09.2026; the issuance plan of 31.08.2026 for the plan references."), 1):
        c = rm.cell(_i, 1, t)
        c.font = Font(name="Calibri", size=9, bold=(_i == 1))
        c.alignment = Alignment(vertical="top", wrap_text=True)
    rm.row_dimensions[2].height = 150
    rm.row_dimensions[3].height = 190
    w.save(path)
    print("saved", path)


def _fill_dates(sh):
    """The Head of QC's list of 04.09.2026, normalised (batch_dates.py), as DATE cells — the register's
    lookups read columns B (batch as listed), C (P batch), F (packaging from) and G (packaging to)."""
    cols = [("Seq", 6), ("Batch (as listed)", 18), ("P Batch", 12), ("Harvest from", 13), ("Harvest to", 13),
            ("Packaging from", 14), ("Packaging to", 14), ("iCoA basis (first day of packaging)", 20), ("Tracker lot", 16), ("Note", 60)]
    for _i, (_t, _w) in enumerate(cols, 1):
        put(sh, 1, _i, _t, FW, NAVY, CEN)
        sh.column_dimensions[L(_i)].width = _w
    sh.row_dimensions[1].height = 22
    _r = 2
    for r in DATE_ROWS:
        lot = DATE_USED.get(r["seq"])
        row = (int(r["seq"]), r["cu_batch"], r["p_batch"], _date(r["harvest_from"]) or "— not given —", _date(r["harvest_to"]) or "— not given —",
               _date(r["packaging_from"]) or "— not given —", _date(r["packaging_to"]) or "— not given —", f"=F{_r}",
               lot or "— not on the tracker —", r["note"])
        for _i, v in enumerate(row, 1):
            c = put(sh, _r, _i, v, F7B if _i in (2, 3) else F7,
                    FILL["amber"] if (_i in (4, 5, 6, 7, 9) and str(v).startswith("—")) else None,
                    CEN if _i != 10 else Alignment(horizontal="left", vertical="center", wrap_text=True))
            if _i in (4, 5, 6, 7, 8):
                c.number_format = "DD.MM.YYYY"
        _r += 1
    return _r, cols


def add_dates_sheet(wb):
    sh = wb.create_sheet("Batch Dates", wb.sheetnames.index("iCoA Issuance") + 1)
    _r, cols = _fill_dates(sh)
    note = ("Head of QC, 04.09.2026: date of harvest and packaging date per batch, as sent (batch_dates_raw_2026-09-04.tsv), "
            "normalised by batch_dates.py. A year the list does not print is the harvest year of the same row, else the "
            "year of the row above (the list is chronological); '11-13-11.2025' is read as 11-13.11.2025; '0' and ']' are "
            "no date. The iCoA for identification A, B and foreign matter is dated on the first day of packaging, the "
            "day the issuance plan of 31.08.2026 already uses as the CoQ basis. Rows without a tracker lot are batches "
            "the owner's tracker does not carry; tracker lots without a row keep 'packaging date — to record'. The "
            "iCoA Register looks its packaging dates up here by P batch (else by the batch as listed): a date "
            "corrected on this sheet moves the register's earliest and preliminary issue dates with it.")
    sh.merge_cells(start_row=_r + 1, start_column=1, end_row=_r + 1, end_column=len(cols))
    put(sh, _r + 1, 1, note, F6I, GREY, Alignment(horizontal="left", vertical="top", wrap_text=True))
    sh.row_dimensions[_r + 1].height = 52
    sh.auto_filter.ref = f"A1:{L(len(cols))}{_r - 1}"
    sh.freeze_panes = "A2"
    print("batch dates rows:", _r - 2)


SHEET_ABOUT = {
    "Read Me": "This sheet.",
    "CoQ Parameter Tracker": "One lot per block of two rows per testing instance: the result of each determination on the top row, the certificate that reports it (code, date, laboratory) beneath; acceptance criteria in row 3 and enforced; out-of-specification results in red and named in STATUS; the in-house iCoA cells cite the iCoA Register by key.",
    "Reconciliation 09.09": "The owner's 09.09.2026 pass over the 387 certificates in eCoA_DATABASE against the desk, cell by cell: the parameters it closed on Batch Coverage, the cells the two records disagree about, and why the identity determinations stay blank on almost every lot — the iCoA that carries them has not been issued, and the in-house documents that do exist print no microscopy and no foreign-matter percentage.",
    "ImB Register": "The customer's certificate register, scanned 04.09.2026: 43 certificates for the earliest production, each against its desk lot — the strain as printed and as ruled, the manufacturing and retest dates, and the four lots the register skips inside the span it covers.",
    "Delivery T1–T3": "The 78 cultivation batches delivered in the three tranches of 31.07, 14.08 and 28.08.2026, each against its row on Batch Coverage: the P lot, the CoQ status, what is missing, and the potency the batch was delivered under beside the potency its own certificate reports.",
    "Batch Coverage": "One row per lot: ✓/✗ for each of the 12 parameters, the missing list, the number of certificates and the laboratories present. A grey ✓ is covered by the in-house iCoA.",
    "Mikro CoQ Parameter": "The owner's microbiology sheet, rebuilt from the tracker: the #7–#12 spans per lot in the owner's layout.",
    "Credit Audit": "Certificates credited on the owner's tracker that the desk holds no value from, with the reason.",
    "Credit Corrections": "The two corrections applied to the owner's credits (the Farmahem pair, CNP identification B), one row each; nothing written back to the owner's workbook.",
    "Work Order": "What a person must do next: certificates to ingest, values to read on the page, lots to record.",
    "iCoA Issuance": "One row per P lot and series (initial release, retest): what its iCoA carries, the CNP references, the cannabinoid-assay eCoA that covers identification C, the codes and planned dates looked up on the registers.",
    "Batch Dates": "The Head of QC's harvest and packaging dates per batch (04.09.2026), as dates; the registers look their packaging dates up here.",
    "iCoA Register": "The preliminary iCoA issuance register: iCoA-PP_26-nnn in the order of issue, number, code and dates as formulas.",
    "CoQ Register": "The preliminary CoQ issuance register: CoQ-PP_26-nnn in the order of issue, the latest eCoA each CoQ cites, its iCoA, the adherence flags under the table.",
    "Parameters": "The 21 determinations with method, global acceptance criterion, source and tracker columns.",
    "Summary Dashboard": "Counts recomputed from Batch Coverage: lots, documents, complete / partial / incomplete, missing-parameter frequency.",
}


# --------------------------------------------------------------- delivery reconciliation
def add_delivery_sheet(wb):
    """The three delivery tranches against the desk: has every batch that LEFT THE SITE a CoQ?

    The tracker answers "what does the desk hold for this lot". This sheet answers the
    question the QP actually has to answer, which is not the same one: 1,480.66 + 2,747.87 +
    2,705.73 kg went to the customer in three deliveries, and each of those 78 cultivation
    batches needs a certificate of quality. The sheet is built by reading Batch Coverage, so
    the two can never drift.

    Three things it prints that the tracker cannot:

      * a batch delivered under a name the desk does not carry (the delivery list drops the
        asterisk the Head of QC's list writes, so GG012601 is the desk's GG012601*);
      * a batch delivered with no record at all — four of them, 193 kg;
      * the potency the batch was SOLD under, beside the potency its own certificate
        reports. Those disagree on five batches, and on five the certificate puts the batch
        in a different bracket from the one it was delivered in. That is a finding about
        the delivery, not about the desk, and it belongs in front of a person.
    """
    import importlib.util as _il
    _t = _il.spec_from_file_location("tranches", os.path.join(HERE, "tranches.py"))
    TRN = _il.module_from_spec(_t)
    _t.loader.exec_module(TRN)
    rows_t = TRN.load()

    cov = wb["Batch Coverage"]
    last = cov.max_row
    while last > 1 and not cov.cell(last, 1).value:
        last -= 1
    by_cu, by_p = {}, {}
    for r in range(2, last + 1):
        cu = str(cov.cell(r, 1).value or "")
        if not cu:
            continue
        if not cu.startswith("—"):
            by_cu.setdefault(T.batch_key(cu), r)
        for _p in str(cov.cell(r, 2).value or "").split("/"):
            _p = _p.strip()
            if _p.startswith("P"):
                by_p.setdefault(_p, r)

    thc = collections.defaultdict(list)
    cert_of = collections.defaultdict(set)          # batch -> the certificate codes that print it
    lot_of_code = {}                                # certificate code -> the tracker lot crediting it
    for _b0 in batches:
        for _n in range(1, 13):
            for _c, _d, _l in _b0["docs"][_n]:
                lot_of_code.setdefault(T.nkey(_c), _b0)
    _corp = os.path.join(T.ROOT, "ingestion", "ecoa_runner", "records_corpus.json")
    if os.path.exists(_corp):
        for _rec in json.load(open(_corp, encoding="utf-8")):
            _b = _rec.get("batch_canonical") or _rec.get("batch_printed")
            if not _b:
                continue
            if _rec.get("cert_code"):
                cert_of[T.batch_key(str(_b))].add(str(_rec["cert_code"]))
            for _pm in (_rec.get("parameters") or []):
                if str(_pm.get("parameter")) != "total_thc":
                    continue
                _v = str(_pm.get("result_printed") or _pm.get("result") or "")
                _m = re.match(r"^([\d.,]+)", _v.replace("%", "").strip())
                if _m:
                    thc[T.batch_key(str(_b))].append((float(_m.group(1).replace(",", ".")),
                                                      str(_rec.get("cert_code")), str(_rec.get("date_of_issue"))))

    sh = wb.create_sheet("Delivery T1–T3", wb.sheetnames.index("Batch Coverage") + 1)
    cols = [("Tranche", 8), ("Delivered", 11), ("Batch (as delivered)", 18), ("Strain", 20), ("kg", 9),
            ("Bracket", 9), ("Declared", 9), ("P lot", 10), ("Desk lot", 18), ("CoQ status", 14),
            ("Missing", 40), ("Total THC on the eCoA", 11), ("Certificate", 16), ("Δ", 7), ("Ready to issue", 46)]
    for i, (t, w) in enumerate(cols, 1):
        put(sh, 1, i, t, FW, NAVY, CEN)
        sh.column_dimensions[L(i)].width = w
    sh.row_dimensions[1].height = 24
    r = 2
    n_ready = n_short = n_none = n_pot = 0
    for t in sorted(rows_t, key=lambda x: (x["tranche"], x["batch_printed"])):
        name = t["batch_printed"]
        k, ks = T.batch_key(name), T.batch_key(name + "*")
        row = by_cu.get(k) or by_cu.get(ks)
        how = "" if by_cu.get(k) else ("the desk writes it " + name + "*" if by_cu.get(ks) else "")
        pl = ""
        _d = DATES_CU.get(k) or DATES_CU.get(ks)
        if _d:
            pl = _d.get("p_batch") or ""
        if row is None and pl:
            row = by_p.get(pl)
            if row is not None:
                _rcu = str(cov.cell(row, 1).value or "")
                how = ("through its P lot; the desk row is the roll-up " + _rcu
                       if T.batch_key(_rcu) not in (k, ks) else "through its P lot")
        if row is None:
            # Last resort, and the only one that is evidence rather than a name: the
            # certificates that PRINT this batch. SJ092501 is delivered, three certificates
            # print it, and the desk files them under SJ0925021 — the spelling the Head of
            # QC's list carries for P060082. Without this step the batch reads as having
            # nothing on file, which is the opposite of true.
            _codes = cert_of.get(k) or cert_of.get(ks) or set()
            _lots = {id(lot_of_code[T.nkey(c)]): lot_of_code[T.nkey(c)] for c in _codes if T.nkey(c) in lot_of_code}
            if len(_lots) == 1:
                _lot = next(iter(_lots.values()))
                row = by_cu.get(T.batch_key(_lot["cu"])) or by_p.get(str(_lot["p"]).split("/")[0].strip())
                if row is not None:
                    how = ("through the certificates that print this batch (" +
                           ", ".join(sorted(_codes)[:3]) + "); the desk names the lot " + _lot["cu"])
        # A batch with no row on Batch Coverage has no coverage this sheet can
        # state — but "nothing on file" is a different claim, and for four of
        # these it stopped being true on 09.09.2026. Say which it is.
        found0909 = [u for u, why in COV_0909_SKIPPED
                     if why == "no row on Batch Coverage"
                     and T.cu_key(u["CU batch"]) == T.cu_key(t["batch_printed"])]
        status = str(cov.cell(row, 4).value or "") if row else (
            "— CERTIFICATES ON FILE, NO TRACKER ROW —" if found0909 else "— NO RECORD —")
        missing = str(cov.cell(row, 18).value or "") if row else (
            "no lot on the tracker for this batch; certificates found on 09.09.2026 "
            "cover " + found0909[0]["Parameter"] + " — see Reconciliation 09.09"
            if found0909 else "no lot on the tracker for this batch")
        desk_lot = str(cov.cell(row, 1).value or "") if row else "—"
        vals = thc.get(k) or thc.get(ks) or []
        best = min(vals, key=lambda x: abs(x[0] - t["thc_pct"])) if vals else None
        delta = (best[0] - t["thc_pct"]) if best else None
        oob = bool(best) and not TRN.in_bracket(best[0], t["thc_bracket"])
        if row is None:
            verdict, fill = (
                ("NO — certificates are on file but the batch is on no tracker lot; "
                 "add the lot, then re-run", "amber") if found0909 else
                ("NO — nothing on file for a batch that has been delivered", "red"))
            n_none += 1
        elif status.startswith("✓"):
            verdict, fill = "yes — all 12 determinations covered", "green"
            n_ready += 1
        else:
            verdict, fill = "no — " + status.split(" ", 1)[-1].lower(), "amber"
            n_short += 1
        if oob:
            n_pot += 1
            verdict += "  |  POTENCY: the certificate reads %.2f %%, outside the %s it was delivered under" % (best[0], t["thc_bracket"])
            fill = "red"
        vals_row = (t["tranche"], t["delivery_date"], name, t["strain"], t["volume_kg"], t["thc_bracket"],
                    t["thc_pct"] / 100.0, pl or "—", desk_lot + ((" (" + how + ")") if how else ""),
                    status, missing if missing != "—" else "—",
                    (best[0] / 100.0) if best else "— none on the desk —", best[1] if best else "—",
                    (delta / 100.0) if delta is not None else "—", verdict)
        for i, v in enumerate(vals_row, 1):
            c = put(sh, r, i, v, F7B if i == 3 else F7,
                    FILL[fill] if i == 15 else (FILL["red"] if (i in (12, 13, 14) and oob) else None),
                    CEN if i != 15 and i != 11 else Alignment(horizontal="left", vertical="center", wrap_text=True))
            if i in (7, 12, 14):
                c.number_format = '0.00%;[Red]-0.00%'
            if i == 5:
                c.number_format = "#,##0.00"
        r += 1
    note = ("The three deliveries of 31.07, 14.08 and 28.08.2026 (Tranches Overview, the owner's sheet), verbatim in "
            "tranches_raw_2026-09-07.csv and reconciled against its own ВКУПНО totals. 'Desk lot' is the row on Batch "
            "Coverage this batch resolves to: directly, through the asterisk the delivery list drops, or through the P "
            "lot the Head of QC's list gives it. A roll-up in that column means the desk holds ONE row for several "
            "delivered sub-lots, so its coverage is not a statement about this sub-lot alone. 'Total THC on the eCoA' "
            "is the desk's record of the certificate for that batch, not a recalculation. A red potency line is not a "
            "desk error: the batch was delivered in a bracket its own certificate contradicts, and only the QP can "
            "settle which is right. Ready to issue: %d of %d; short of coverage: %d; nothing on file: %d; potency "
            "contradicted: %d." % (n_ready, len(rows_t), n_short, n_none, n_pot))
    sh.merge_cells(start_row=r + 1, start_column=1, end_row=r + 1, end_column=len(cols))
    put(sh, r + 1, 1, note, F6I, GREY, Alignment(horizontal="left", vertical="top", wrap_text=True))
    sh.row_dimensions[r + 1].height = 62
    sh.auto_filter.ref = f"A1:{L(len(cols))}{r - 1}"
    sh.freeze_panes = "D2"
    print(f"delivery: {len(rows_t)} delivered batches — ready {n_ready}, short {n_short}, "
          f"no record {n_none}, potency contradicted {n_pot}")


# ------------------------------------------------------------------ strain names
def _strains():
    import importlib.util as _il
    _sp = _il.spec_from_file_location("strains", os.path.join(HERE, "strains.py"))
    _m = _il.module_from_spec(_sp)
    _sp.loader.exec_module(_m)
    return _m


def apply_strain_rulings(wb):
    """Print the strain a person has ruled on, and print the disagreements rather than hide them.

    A strain name reaches the certificate of quality, so a strain written three ways is three
    strains to anything that groups by it. The ImB certificate register of 04.09.2026 prints
    "Cap Junky" (cert 041), "Cap Junkie" (028) and "Cup Junkie" (the P050162 entry) for one
    strain; the Head of QC ruled Cap Junky on 07.09.2026 and strains.py carries the ruling.

    What is NOT decided here: where the delivery sheet and the certificate register disagree
    in their letters — Sleepy Joe against Sleepy Joy, Permanent Marker against Permanent
    Market, Wedding Crusher against Wedding Crasher — both are the company's own documents,
    and choosing between them is a person's job. Those are listed on the Work Order.
    """
    ST = _strains()
    changed, conflicts = [], {}
    for sheet, col in (("Batch Coverage", 3), ("Delivery T1\u2013T3", 4)):
        if sheet not in wb.sheetnames:
            continue
        sh = wb[sheet]
        for r in range(2, sh.max_row + 1):
            v = sh.cell(r, col).value
            if not v or str(v).startswith("\u2014"):
                continue
            c = ST.canonical(str(v))
            if c != str(v).strip():
                changed.append((sheet, str(v), c))
                sh.cell(r, col).value = c
            cf = ST.conflict(c)
            if cf:
                conflicts[c] = cf
    # The unresolved ones go where a person will act on them, not into a log nobody reads.
    if conflicts and "Work Order" in wb.sheetnames:
        wo = wb["Work Order"]
        r = wo.max_row
        while r > 1 and not wo.cell(r, 1).value:
            r -= 1
        src = 2 if wo.max_row >= 2 else 1
        seen = set()
        for name, (a, b) in sorted(conflicts.items()):
            if (a, b) in seen:
                continue
            seen.add((a, b))
            r += 1
            for c in range(1, 9):
                _style_from(wo.cell(r, c), wo.cell(src, c))
            for c, v in ((1, "strain name unruled"), (2, name), (3, "—"), (4, "—"), (5, "—"),
                         (6, "—"), (7, "strain, printed on every CoQ"),
                         (8, "Two of the company's own documents disagree: " + a + " against " +
                             b + ". Both are yours, so the desk holds what it was given and "
                             "prints neither as correct. Rule it as Cap Junky was ruled on "
                             "07.09.2026, and strains.py will carry it.")):
                wo.cell(r, c).value = v
    print("strain rulings applied: %d cell(s); unresolved strain conflicts: %d (added to the Work Order)"
          % (len(changed), len(conflicts)))
    return changed, conflicts


def add_reconciliation_sheet(wb):
    """The owner's 09.09.2026 pass against the desk, and what this build took from it.

    The workbook the owner sent on 10.09.2026 (CoQ_Analysis_Master_v20_owner.xlsx,
    Drive 1cBmbOgHSMlzIGyGjuZFRP5DagigtXx29) carries a pass over the 387 PDFs in
    eCoA_DATABASE: every one of the 600 determinations of Tranches 1 and 2
    resolved to a document, a laboratory, an issue date and the result that
    document prints. This sheet says what came of putting the two records side
    by side — what the pass closed, what it could not, and where the two do not
    say the same thing about one certificate.

    Nothing here resolves a disagreement. Two records of one document that
    disagree are a finding for a person; the desk's value stands until someone
    reads the page.
    """
    import importlib.util as _il
    _r = _il.spec_from_file_location("reconcile_0909",
                                     os.path.join(GAPDIR, "reconcile_0909.py"))
    RC = _il.module_from_spec(_r)
    try:
        _r.loader.exec_module(RC)
        cen = RC.census()
        finds = RC.findings()
    except Exception as exc:                      # the desk export is the source
        print("reconciliation: %s" % exc)
        return
    CRm = RC.CR

    where = (wb.sheetnames.index("Delivery T1\u2013T3") + 1) if "Delivery T1\u2013T3" in wb.sheetnames \
        else len(wb.sheetnames)
    sh = wb.create_sheet("Reconciliation 09.09", where)
    LEFT = Alignment(horizontal="left", vertical="top", wrap_text=True)
    for i, w in enumerate((34, 15, 15, 46, 46), 1):
        sh.column_dimensions[L(i)].width = w
    r = 1

    def head(t):
        nonlocal r
        put(sh, r, 1, t, FW, NAVY, LEFT)
        for c in range(2, 6):
            put(sh, r, c, "", FW, NAVY, LEFT)
        r += 2

    def kv(k, v, note=""):
        nonlocal r
        put(sh, r, 1, k, F7, GREY, LEFT)
        put(sh, r, 2, v, F7, None, LEFT)
        if note:
            put(sh, r, 4, note, F6I, None, LEFT)
        r += 1

    head("THE PASS THIS BUILD READ")
    kv("Source", "CoQ_Analysis_Master_v20_owner.xlsx",
       "the owner's workbook of 09.09.2026, vendored beside this one; the three "
       "sheets it was read from are Cell Resolution 09.09, Coverage Update 09.09 "
       "and Identity Problem 09.09")
    kv("Certificates it read", "387", "eCoA_DATABASE, name for name")
    kv("Determinations it resolved", "600", "50 lots of Tranches 1 and 2 x 12")
    r += 1

    head("WHAT IT CLOSED ON BATCH COVERAGE")
    kv("Parameters closed", str(len(COV_0909_APPLIED)),
       "a certificate on file that this sheet still marked missing")
    kv("Lots affected", str(len({x[1] for x in COV_0909_APPLIED})))
    kv("Closures not applied", str(len(COV_0909_SKIPPED)),
       "already covered, or the lot has no row on Batch Coverage \u2014 listed below")
    r += 1

    head("WHAT THE TWO RECORDS SAY ABOUT THE SAME 600 CELLS")
    for k, note in (
            ("agree", "both hold a value and it is the same value"),
            ("values", "both hold a value and the values differ \u2014 a finding"),
            ("order", "the same values against different analytes \u2014 a finding"),
            ("fill", "the desk held nothing and the pass holds a printable result"),
            ("blocked", "the only document is an in-house iCoA that has not been issued"),
            ("uncited", "the only document carries no document code at all"),
            ("ambiguous", "the pass holds a list of values it does not label"),
            ("basis note", "the pass names where identity comes from, not a result"),
            ("none", "neither record holds anything"),
            ("not comparable", "the two records hold different numbers of lines"),
            ("no desk lot", "the desk carries no initial-release CoQ for the batch")):
        if cen.get(k):
            kv(k, str(cen[k]), note)
    r += 1

    head("THE DISAGREEMENTS")
    for i, t in enumerate(("Batch", "Determination", "Kind", "The desk holds",
                           "The 09.09 pass reads"), 1):
        put(sh, r, i, t, FW, NAVY, LEFT)
    r += 1
    for row, state, d in finds:
        put(sh, r, 1, row["Batch"], F7, None, LEFT)
        put(sh, r, 2, "#" + (CRm.det_no(row["Determination"]) or ""), F7, None, LEFT)
        put(sh, r, 3, "same values,\nother order" if state == "order" else "different values",
            F7, FILL["amber"] if state == "order" else FILL["red"], LEFT)
        put(sh, r, 4, "; ".join(d.get("desk", [])), F7, None, LEFT)
        put(sh, r, 5, "; ".join(d.get("pass", [])), F7, None, LEFT)
        r += 1
    r += 1

    head("THE IDENTITY DETERMINATIONS ARE NOT A TRANSCRIPTION PROBLEM")
    put(sh, r, 1, IDENT_NOTE, F6I, GREY, LEFT)
    sh.merge_cells(start_row=r, start_column=1, end_row=r + 6, end_column=5)
    r += 8

    head("CLOSURES THAT FOUND NO ROW")
    for i, t in enumerate(("CU batch", "P batch", "", "Parameters now covered",
                           "From"), 1):
        put(sh, r, i, t, FW, NAVY, LEFT)
    r += 1
    for u, why in COV_0909_SKIPPED:
        if why != "no row on Batch Coverage":
            continue
        put(sh, r, 1, u["CU batch"], F7, None, LEFT)
        put(sh, r, 2, u["P batch"], F7, None, LEFT)
        put(sh, r, 4, u["Parameter"], F7, None, LEFT)
        put(sh, r, 5, u["Now covered by"], F7, None, LEFT)
        r += 1
    put(sh, r, 1, NOROW_NOTE, F6I, GREY, LEFT)
    sh.merge_cells(start_row=r, start_column=1, end_row=r + 3, end_column=5)
    sh.freeze_panes = "A2"
    print("reconciliation sheet: %d disagreement(s), %d closure(s) with no row"
          % (len(finds), sum(1 for _, w in COV_0909_SKIPPED
                             if w == "no row on Batch Coverage")))


def add_imb_register_sheet(wb):
    """The ImB certificate register (scan of 04.09.2026) against the desk.

    43 certificates for the earliest production: the six 2024 lots, P050012-P050322 and
    P060012-P060092. It is the customer-facing numbering, so it answers a question the desk
    cannot: which batches ImB already holds a certificate for. Inside the span it covers it
    is contiguous except for four lots, and those four are the finding.
    """
    src = os.path.join(HERE, "imb_certificate_register_scan_2026-09-04.tsv")
    if not os.path.exists(src):
        return
    import csv as _csv
    rows = list(_csv.DictReader(open(src, encoding="utf-8"), delimiter="\t"))
    ST = _strains()
    cov = wb["Batch Coverage"]
    last = cov.max_row
    while last > 1 and not cov.cell(last, 1).value:
        last -= 1
    by_p, by_cu = {}, {}
    for r in range(2, last + 1):
        cu = str(cov.cell(r, 1).value or "")
        if cu and not cu.startswith("\u2014"):
            by_cu[T.batch_key(cu)] = r
        for _p in str(cov.cell(r, 2).value or "").split("/"):
            _p = _p.strip()
            if _p.startswith("P"):
                by_p[_p] = r
    where = (wb.sheetnames.index("Delivery T1\u2013T3") + 1) if "Delivery T1\u2013T3" in wb.sheetnames else len(wb.sheetnames)
    sh = wb.create_sheet("ImB Register", where)
    cols = [("Cert No", 9), ("Strain (as printed)", 20), ("Strain (ruled)", 18), ("Batch", 12),
            ("Manufactured", 14), ("Retest", 15), ("Desk lot", 18), ("CoQ status", 14), ("Note", 46)]
    for i, (t, w) in enumerate(cols, 1):
        put(sh, 1, i, t, FW, NAVY, CEN)
        sh.column_dimensions[L(i)].width = w
    sh.row_dimensions[1].height = 22
    r = 2
    seen_p = []
    for e in rows:
        b = e["batch"].strip()
        row = by_p.get(b) or by_cu.get(T.batch_key(b))
        if b.startswith("P0"):
            seen_p.append(b)
        printed = e["strain_printed"].strip()
        ruled = ST.canonical(printed)
        note = ""
        if ruled != printed:
            note = "strain ruled Cap Junky; the register prints " + printed
        elif ST.conflict(printed):
            note = "strain unresolved: " + ST.conflict(printed)[0] + " vs " + ST.conflict(printed)[1]
        vals = (e["cert_no"] or "\u2014 not read \u2014", printed, ruled, b, e["manufactured"] or "\u2014",
                e["retest"] or "\u2014 none printed \u2014",
                str(cov.cell(row, 1).value) if row else "\u2014 no desk lot \u2014",
                str(cov.cell(row, 4).value) if row else "\u2014", note)
        for i, v in enumerate(vals, 1):
            put(sh, r, i, v, F7B if i == 4 else F7,
                FILL["amber"] if ((i == 7 and not row) or (i == 1 and not e["cert_no"])) else
                (FILL["green"] if (i == 3 and ruled != printed) else None),
                CEN if i != 9 else Alignment(horizontal="left", vertical="center", wrap_text=True))
        r += 1
    # gaps are computed WITHIN each P series: P050332 -> P060012 is a change of series, not
    # a run of 970 missing lots, and treating it as one produced exactly that nonsense once
    gaps = []
    for _pre in ("P05", "P06"):
        _n = sorted(int(x[3:]) for x in seen_p if x.startswith(_pre))
        if not _n:
            continue
        gaps += ["%s%04d" % (_pre, m) for m in range(_n[0], _n[-1] + 1, 10) if m not in _n]
    note = ("The ImB certificate register, scanned 04.09.2026 (Emailing Scan - 2026-09-04 06_15_05.pdf), "
            "read through the Drive text extraction: the file is 12.3 MB and the connector will not "
            "download over 10 MB, so the PAGES have not been read here \u2014 a batch found is firm, a batch "
            "absent is well supported but not proven on the page. 43 entries; the certificate numbers "
            "below 017 did not survive the extraction and read '\u2014 not read \u2014'. The register covers the "
            "earliest production only: the six 2024 lots, P050012\u2013P050322 and P060012\u2013P060092, contiguous "
            "except for %s \u2014 which the Head of QC's list names BSS1024_01/2, GP062501, GOG062501 and "
            "SC062501. Everything from P060102 onward is outside this register entirely."
            % (", ".join(gaps) or "nothing"))
    sh.merge_cells(start_row=r + 1, start_column=1, end_row=r + 1, end_column=len(cols))
    put(sh, r + 1, 1, note, F6I, GREY, Alignment(horizontal="left", vertical="top", wrap_text=True))
    sh.row_dimensions[r + 1].height = 58
    sh.auto_filter.ref = f"A1:{L(len(cols))}{r - 1}"
    sh.freeze_panes = "A2"
    print("ImB register rows: %d (%d numbered); gaps inside the covered span: %s"
          % (len(rows), sum(1 for e in rows if e["cert_no"]), ", ".join(gaps) or "none"))


def write_read_me(wb):
    """The Read Me describes the workbook as it is: the sheets it holds, what the marks mean, the
    rulings in force, the version history — regenerated on every build, never inherited."""
    rm = wb["Read Me"]
    for mr in list(rm.merged_cells.ranges):
        rm.unmerge_cells(str(mr))
    for row in rm.iter_rows():
        for c in row:
            c.value = None
    for r_ in range(1, rm.max_row + 1):
        rm.row_dimensions[r_].height = None
    rm.column_dimensions["A"].width = 22
    rm.column_dimensions["B"].width = 118
    r = 1

    def head(t, size=12):
        nonlocal r
        c = rm.cell(r, 1, t); c.font = Font(name="Calibri", size=size, bold=True, color=NAVY); c.alignment = Alignment(vertical="top")
        r += 1

    def line(label, text):
        nonlocal r
        c0 = rm.cell(r, 1, label); c0.font = Font(name="Calibri", size=9, bold=True); c0.alignment = Alignment(vertical="top", wrap_text=True)
        c1 = rm.cell(r, 2, text); c1.font = Font(name="Calibri", size=9); c1.alignment = Alignment(vertical="top", wrap_text=True)
        rm.row_dimensions[r].height = 13 * (len(text) // 150 + 1)
        r += 1

    head(f"CoQ Analysis Master — v{VER}", 14)
    line("What it is", f"Built {BUILD_DATE} on the owner's CoQ_Analysis_Master. Which certificate is credited to which parameter is the owner's; results, dates "
         "and laboratories are the desk's record: the release register, the page reads and the two-read extraction of every certificate in eCOA_DB. "
         "Nothing is invented; a value the reads disagreed on is held until a person rules on the page.")
    r += 1
    head("SHEETS")
    for name in wb.sheetnames:
        about = SHEET_ABOUT.get(name) or (SHEET_ABOUT["CoQ Parameter Tracker"] if name.startswith("CoQ Parameter Tracker") else "")
        line(name, about)
    r += 1
    head("LEGEND (tracker and coverage)")
    line("✓ green", "A certificate is on file and its value is on the desk: an outsourced certificate (eCoA) or the in-house iCoA.")
    line("✓ grey", "Covered by the in-house iCoA only (identification A, identification B, foreign matter, tested at Purely Plant at packaging): coverage for the release CoQ (Head of QC, 04.09.2026).")
    line("✓ orange", "Stability-timepoint certificate — its value is not a release result.")
    line("✗ amber", "Certificate credited on the tracker, but the desk holds no value for this determination from it — the determination is not on that certificate, or the certificate never entered the record.")
    line("✗ red", "No certificate credited for the parameter.")
    line("•", "A document on file that is not credited for the parameter (an old in-house Report of Analysis, an NGP form, the QCCoA 001 certificate): shown, not coverage.")
    line("Conforms (ImB spec.)", "Identification C: conforms to the ImB specification on the certificate that carries the cannabinoid assay; the CoQ cites that eCoA (Head of QC, 04.09.2026).")
    line("Red result", "Out of specification against the global acceptance criterion (row 3). Orange: undetermined (a Ph. Eur. band the result sits in).")
    r += 1
    head("CONVENTIONS")
    line("Batch names", "CU batch as the owner names it; a sub-lot digit belongs to the batch (FB012601_1), never to the certificate code; an asterisk (JD112501＊) marks a lot of its own. The laboratory prints the zero of a P-number as a letter O (PO60052); it is folded to P060052.")
    line("Certificate codes", "As printed on the certificate (Cyrillic ППК codes kept). [Lab]: CNP (Faculty of Pharmacy, Center for Natural Products), IJZ-MB / IPH (Institute of Public Health), FHM-K / FHM-M (Farmahem), PP (Purely Plant, in-house).")
    line("Dates", "DD.MM.YYYY. The Batch Dates and register sheets hold real dates; the tracker prints them as text inside the reference.")
    line("Results", "Numeric results with the certificate's printed precision; qualitative results as text (Conforms, absent, <LOQ, ND). A microbiological range (< 10³ и > 10²) is judged by its upper bound.")
    line("OOS check", "A result is flagged only when it provably exceeds its criterion; ND, <LOQ, <10 and absent pass; a value that cannot be parsed is never flagged.")
    line("Formulas", "On the two registers the number, the code and the dates are formulas, and the iCoA Issuance sheet and the tracker's in-house cells look the registers up by key: insert a row and every code beneath moves by one.")
    line("Print", "Every sheet: landscape, A3, one page wide, the header rows repeated; panes frozen under the header.")
    line("Do not", "read counts from the eCOA_DB text layer. On five of six certificates checked it read the exponent or a digit too low, every time in the direction of a conforming result.")
    r += 1
    head("RULINGS IN FORCE (Head of QC)")
    line("04.09.2026 · iCoA", "Identification A and B are tested at Purely Plant together with foreign matter at packaging (the first day, when the sample is taken before primary packaging), and ONE iCoA per P lot carries the three results for the release CoQ. Where a CNP certificate reports one of them, the CNP document code is the reference; where CNP reports all three, no iCoA is needed.")
    line("04.09.2026 · Ident C", "Identification C is 'Conforms', referenced to the eCoA that covers Total THC (the cannabinoid assay); for a Farmahem lot the K certificate.")
    line("04.09.2026 · decisions", "The two bile-tolerant gram-negative rows the reads disagreed on: P060262 < 10³ и > 10² CFU/g, P060432 < 10² и > 10 CFU/g (decisions_2026-09-04.tsv).")
    line("05.09.2026 · issuance", "Legacy lots (packed before the SOP floor of 11.05.2026, or holding an old in-house QCCoA 001 certificate): iCoAs issued together on 15.05.2026, CoQs (CoQ-PP_26-nnn, superseding the old certificate) on 27.05.2026, both in chronological order of packaging. Post-SOP lots: the iCoA on the first working day 5 days after packaging, the CoQ on the first working day 7 days after the latest eCoA it cites, never before 27.05.2026. Codes iCoA-PP_26-nnn and CoQ-PP_26-nnn, one series each for the year of issue.")
    line("05.09.2026 · retest", "The QP's retest campaign, sampled by tranche from July 2026: identification A, B and foreign matter in-house on every bag of the representative sample (one iCoA), cannabinoids with identification C and mycotoxins at Farmahem, microbiology at IJZ-MB; the reissued CoQ carries those results and the initial certificates for the rest. A retest certificate never certifies the initial CoQ; the IJZ-MB delivery of 25/26.08.2026 is campaign sampling for every lot.")
    line("05.09.2026 · missing", "A production lot whose initial certificate for a determination is not on file keeps its planned CoQ and number: the initial testing exists at CNP (microbiology: IJZ) and the certificate is to be located (Work Order).")
    r += 1
    head("VERSION HISTORY")
    line("v7", "The two-row block tracker: one lot per block, certificates stacked in date order, sub-determinations in their own columns, acceptance criteria in row 3 and enforced, out-of-specification results in red and named in STATUS.")
    line("v9", "Verified and slimmed to live in Drive: every decision-bearing value checked against the filed page (review/V8_TRUTH_CHECK_2026-09-02.md); three sheets of v8 (a flat results register, a flat tracker, a document index) were retired to the repository.")
    line("v10", "The 30 IJZ-MB certificates of 31.08 and 01.09.2026 as testing instances credited to #9; the iCoA rule; the Head of QC's harvest and packaging dates (Batch Dates); one iCoA per P lot; the iCoA Issuance sheet.")
    line("v11", "The iCoA Register and the CoQ Register (formula-driven); the ruling of 05.09.2026 on the legacy and post-SOP series; the retest campaign kept off the initial CoQs; the owner's edits to the Drive copies (row 4, result sizes, lot borders); one coverage row per lot.")


def fix_parameters(wb):
    """The Parameters sheet is inherited from the owner's workbook: its Source and Tracker column
    values are set from the rulings and the live tracker layout."""
    if "Parameters" not in wb.sheetnames:
        return
    sh = wb["Parameters"]
    hdr = {str(sh.cell(1, c).value or "").strip(): c for c in range(1, sh.max_column + 1)}
    src_c, col_c = hdr.get("Source"), hdr.get("Tracker column")
    by_n = {p["n"]: p for p in T.PARAMS}
    for r in range(2, sh.max_row + 1):
        no = str(sh.cell(r, 1).value or "").strip()
        if not no:
            continue
        n = int(no.split(".")[0])
        p = by_n.get(n)
        if src_c:
            if n in (1, 2, 7):
                sh.cell(r, src_c).value = "In-house iCoA (Purely Plant, at packaging) — coverage for the release CoQ; CNP document code where CNP reported it"
            elif n == 3:
                sh.cell(r, src_c).value = "Outsourced certificate (eCoA): the cannabinoid-assay certificate, reported as Conforms (ImB spec.)"
            else:
                sh.cell(r, src_c).value = "Outsourced certificate (eCoA)"
        if col_c and p:
            if "." in no and p.get("subs"):
                j = int(no.split(".")[1]) - 1
                sh.cell(r, col_c).value = L(p["start"] + j)
            else:
                sh.cell(r, col_c).value = f"{L(p['start'])}–{L(p['end'])}"
    sh.column_dimensions[L(src_c)].width = 60 if src_c else None


def print_setup(wb):
    """Landscape, A3, one page wide, header rows repeated — on every sheet (the Read Me says so)."""
    for sh in wb.worksheets:
        sh.page_setup.orientation = "landscape"
        sh.page_setup.paperSize = sh.PAPERSIZE_A3
        sh.page_setup.fitToWidth = 1
        sh.page_setup.fitToHeight = 0
        sh.sheet_properties.pageSetUpPr.fitToPage = True
        if not sh.print_title_rows:
            sh.print_title_rows = "1:4" if sh.title.startswith(("CoQ Parameter Tracker", "Mikro")) else "1:1"


if NEW:
    _last = patch_coverage(wb)
    patch_dashboard(wb, _last)
    _mikro = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--mikro=")), None)
    if _mikro and os.path.exists(_mikro):
        add_mikro(wb, _mikro)
    if ICOA_RULE:
        add_icoa_sheet(wb)
        add_register_sheet(wb)
        add_coq_register_sheet(wb)
        add_dates_sheet(wb)
        write_register_file(os.path.join(HERE, "Issuance_Registers_prelim.xlsx"))
    add_delivery_sheet(wb)
    if CELLS_0909:
        add_reconciliation_sheet(wb)
    add_imb_register_sheet(wb)
    apply_strain_rulings(wb)
    write_read_me(wb)
    fix_parameters(wb)
    print_setup(wb)
wb.save(OUT)
print("saved", OUT)
print("batches:", len(batches), "two-row blocks:", (LASTROW - 4) // 2, "rows:", LASTROW - 4, "columns:", LAST)
print("parameter cells by state:", dict(stats))
import collections as _c
by = _c.Counter(k for _, k, _ in oos_rows)
print("verdicts:", dict(by))
for cu, kind, lst in oos_rows:
    print(f"    {kind:14s} {cu:14s} → {', '.join(lst)}")
