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
# Owner, 15.09.2026 (evening): the Tranche 3 retest analyses complete within ten days,
# likely by Friday 18.09.2026, and all Tranche 3 certificates of quality issue on one
# day — "let's say Monday next week". The allocated rows carry that planned date,
# provisional until the 227-М certificates exist; blank when no date is given.
T3_ISSUE = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--t3-issue=")), "")
spec = importlib.util.spec_from_file_location("tracker_data", os.path.join(HERE, "tracker_data.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)
# The controlled result vocabulary — one spelling per assertion, applied in
# values_of() so every sheet in the workbook inherits it from one definition.
sys.path.insert(0, os.path.dirname(HERE))
import result_vocabulary as RV                                          # noqa: E402
import document_codes as DC                                             # noqa: E402
import sampling_dates as SD                                             # noqa: E402
import potency_grading as PGR                                           # noqa: E402
import testing_series as TS                                             # noqa: E402

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
SILENT = ("held for review", "not on this certificate", "not ingested", "not reported")
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
# Owner's ruling, 16.09.2026: a starred cultivation batch is a second SAMPLE of the same
# packaged lot, not a second lot (identity_decisions.tsv, batch_alias). The owner's tracker
# carries JD112501＊ as a row of its own with no P batch; its documents are P060212's and
# stay on that lot's row as testing instances — on file, not credited, and marked
# experimental (testing_series.EXPERIMENTAL) — while the starred row is not a lot and is
# folded away. A starred row whose namesake is not on the tracker is left as it is.
_folded, _named = [], {}
for _b in _merged:
    if _b["cu"] and not _b["p"].startswith("N/A"):
        _named.setdefault(T.batch_key(_b["cu"]), _b)
for _b in _merged:
    _t = _named.get(T.batch_key(_b["cu"])) if re.search(r"[＊*]", _b["cu"] or "") and _b["p"].startswith("N/A") else None
    if _t is not None and _t is not _b:
        print(f"starred row {_b['cu']} folded into {_t['cu']} / {_t['p']} — one lot, two samples (owner, 16.09.2026)")
        continue
    _folded.append(_b)
batches = _folded


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
DOC_LOT = {}          # certificate key -> the P lot it names (new instances only)


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
        # The cultivation batch is genuinely unrecorded — the certificate prints only
        # the P number — but three such lots (P160012, P160022, P160032) carried the
        # identical label, so batch_key collapsed them to one and any join keyed on
        # the printed cultivation batch silently picked one of the three. Naming the
        # P number inside the label keeps the row identifiable without inventing a
        # cultivation batch it does not have.
        # A certificate that prints the cultivation batch and no P number (Farmahem
        # 220-30/31/32-М/26: JD042601, FB042601, CC042601) names its lot itself; the
        # label is only for the lot nothing names.
        _unrec = "— not recorded —" + (f" ({inst['p']})" if inst.get("p") else "")
        b = {"cu": inst.get("cu") or _unrec, "p": inst["p"] or "N/A — no P batch assigned", "status": "",
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
    # A tracker row can hold several P lots (JD012603: three; GRC102501: two) and one
    # document pool. A certificate that names its P lot belongs to that lot alone;
    # the register part reads the pool per lot through DOC_LOT (15.09.2026: the
    # sister lot's certificate was being filed as this lot's retest, so the lot's
    # own 220-К/26 assay never matched and its reissue could not issue).
    if inst.get("p"):
        DOC_LOT[ck] = inst["p"]
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
    # The campaign each lot's retest round belongs to, from the series that numbers
    # it (icoa_register.py) — by P lot and by batch, so a tracker row that holds
    # several P lots (GRC102501: /1 in Tranche 3, /2 in Tranche 2; JD012603: three
    # lots) is read per lot and not from a document pool the lots share.
    _MOD_CAMP = {}
    try:
        import icoa_register as _IR0
        for _m0 in _IR0.build():
            if _m0.get("campaign"):
                for _b0 in filter(None, (_m0["p_lot"], _m0["batch"])):
                    _MOD_CAMP.setdefault(T.batch_key(_b0), (_m0["campaign"], _m0["tested_from"], _m0["issued"]))
    except Exception as _e0:
        print("campaign lookup not taken from icoa_register.py:", _e0)
    _COQ, _RETEST = {}, {}
    for _c in _D["coqs"]:
        _tbl = _COQ if _c["t"].startswith("initial release") else _RETEST
        _tbl.setdefault(T.batch_key(re.sub(r"[＊*]", "", _c["cb"])), _c)
        if _c.get("pp"):
            _tbl.setdefault("P:" + _c["pp"].strip(), _c)
        elif re.match(r"^P\d{6}$", _c["cb"].strip()):
            # a register block named by the P lot alone (P060332 is the tracker's
            # CC012601/1): the tracker row finds it by its P number
            _tbl.setdefault("P:" + _c["cb"].strip(), _c)

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
    # The desk's own convention is that a controlled document is issued on a
    # working day. It is a convention, not a rule from anywhere above it, so the
    # owner naming a date outranks it — 06.06.2026 is a Saturday and was chosen
    # deliberately. The date is honoured and the choice is flagged on the sheet
    # rather than quietly moved to the Monday.
    _DAY_FLAGS = []
    for _nm, _d in (("legacy iCoA day", LEGACY_ICOA), ("legacy CoQ day", LEGACY_COQ)):
        assert _d and _d >= SOP_D, f"the {_nm} must be on or after the SOP floor"
        if _d.weekday() >= 5:
            _DAY_FLAGS.append(f"the {_nm} {_F_(_d)} is a {_d.strftime('%A')} — the owner's date, kept as given")
    # the old in-house certificates (QCCoA 001 v.01/v.02) the desk knows, by P number and by batch
    OLD_COA = {}
    for _e in _D["ecoa"]:
        if _e["lab"].startswith("Purely Plant") and str(_e.get("code", "")).startswith("PP CoA"):
            OLD_COA.setdefault(_e.get("pn") or "", (_e["code"], _e["date"]))
            OLD_COA.setdefault(T.batch_key(_e["batch"]), (_e["code"], _e["date"]))
    OLD_COA.pop("", None)
    FLAGS, COQ_ROWS = list(_DAY_FLAGS), []
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
        # a release-register block is one lot: its certificates name that P lot (the
        # block's own, else the batch list's for its cultivation batch), so a tracker
        # row holding several P lots reads them per lot (DOC_LOT, 15.09.2026)
        _rp = str(_rg.get("pn") or "").strip() or str((DATES_CU.get(T.batch_key(str(_rg.get("cb") or ""))) or {}).get("p_batch") or "").strip()
        for _ce in _rg.get("certs", []):
            if "re-analysis" in str(_ce.get("fam", "")).lower():
                REANALYSIS.add(T.nkey(_ce["code"]))
            if re.match(r"^P\d{6}$", _rp):
                DOC_LOT.setdefault(T.nkey(_ce["code"]), _rp)
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
    # The Key columns of the iCoA Register and the CoQ Register (REG_COLS, COQ_COLS).
    # iCoA Register's Key moved P -> AA on 14.09.2026 when the iCoA Issuance sheet
    # was folded in and ten columns landed ahead of it. Every lookup into the
    # register goes through this one constant, and _fill_register asserts it still
    # names the column REG_COLS actually puts Key in — insert a column without
    # moving this and the build fails loudly instead of silently matching the
    # wrong column, which is how a register lookup returns another lot's code.
    REG_KEY_COL, COQ_KEY_COL = "AA", "S"
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
            # — read per lot: a certificate that names another P lot of this row is not
            # this lot's (DOC_LOT); one that names no lot is shared, as before
            _mine = lambda x, _l=_lot: DOC_LOT.get(T.nkey(x[0])) in (None, "", _l)
            _first, _rt_docs = {}, {}
            for n in range(1, 13):
                pool = sorted([x for x in b["docs"][n] if x[2] != "PP" and _mine(x)], key=lambda x: (str(T.date_key(x[1])), x[0]))
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
            # the internal certificate is issued on the first day of packaging, or on the
            # legacy day where that comes first — the same arithmetic as icoa_register.py
            # and the register sheet's own formula (it used to be "5 working days after
            # packaging complete" here alone, a third definition, which put JD042601's
            # CoQ after the Tranche 1 reissues while the sheet dated it before them)
            _icoa_issue = LEGACY_ICOA if _group == "legacy" else (max(_pkd, LEGACY_ICOA) if _pkd else None)
            _latest_d = _D_(_latest[1]) if _latest else None
            _coq_flag = ""
            if _group == "legacy":
                if _latest_d and _latest_d > LEGACY_COQ:
                    _coq_issue = _workday(_latest_d, 7)
                    _coq_flag = f"moved off 27.05.2026: cites {_latest[0]} of {_latest[1]}"
                    FLAGS.append(f"{_lot_id}: legacy CoQ cannot be dated {_F_(LEGACY_COQ)} — it cites {_latest[0]} of {_latest[1]}; planned {_F_(_coq_issue)} (first working day 7 days after)")
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
                    FLAGS.append(f"{_lot_id}: post-SOP CoQ rule date {_F_(_workday(_latest_d, 7))} precedes the legacy series day {_F_(LEGACY_COQ)} — held to it, so the legacy CoQs keep 001 onward")
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
            def _pick(pool_n, want_rt, series=None):
                pool = [x for x in b["docs"][pool_n] if x[2] != "PP" and not re.search(r"LoD|ГС", x[0], re.I) and _mine(x)]
                pool = [x for x in pool if (T.nkey(x[0]) in _rt_set) == want_rt]
                if series:                    # only this campaign's certificates
                    pool = [x for x in pool if TS.series_of(x[0]) == series]
                pool = sorted(pool, key=lambda x: (str(T.date_key(x[1])), x[0]))
                return f"{pool[0][0]}, ({pool[0][1]}) [{pool[0][2]}]" if pool else None
            _mc = _MOD_CAMP.get(T.batch_key(_lot)) or (_MOD_CAMP.get(T.batch_key(cu0)) if _single else None)
            _camp0 = _mc[0] if _mc else None
            c_rt = _pick(4, True, _camp0) or _pick(3, True, _camp0)

            m_rt, mb_rt = _pick(10, True, _camp0), _pick(9, True)
            # The campaign a lot's retest documents belong to (sampling_dates.py, owner
            # 15.09.2026): the series of its Farmahem re-analysis certificate names the
            # tranche, the certificate's running number names the sampling day, and the
            # campaign names the day its internal certificate issues.
            if _mc:
                _camp, _rt_sampled, _rt_icoa_day = _mc[0], _mc[1], _D_(_mc[2])
            else:
                _camp_doc = next((x[0] for n in (4, 3, 10) for x in b["docs"][n]
                                  if x[2] != "PP" and _mine(x) and T.nkey(x[0]) in _rt_set and TS.series_of(x[0])), None)
                _camp = TS.series_of(_camp_doc) if _camp_doc else None
                _rt_sampled = SD.sampling_day(_camp_doc) if _camp_doc else None
                _rt_icoa_day = _D_(SD.icoa_issue_day(_camp)) if _camp else None
            _tranche = (SD.label(_camp) if _camp else
                        "re-analysed — no campaign sampling date on file" if c_rt else
                        "IJZ-MB campaign sampling of 25/26.08.2026 — potency and mycotoxins pending" if _rt_docs else
                        "not yet sampled")
            _icoa_txt = ("iCoA tested %s, issued %s" % (_rt_sampled, _F_(_rt_icoa_day))) if _camp else "in-house iCoA at the retest sampling"
            _st_rt = ("due — retest assay and mycotoxins" + (" and microbiology" if mb_rt else "") + " on file; " + _icoa_txt if (c_rt and m_rt) else
                      "sampled — retest assay on file, mycotoxins pending; " + _icoa_txt if c_rt else
                      "sampled — mycotoxins on file, retest assay pending; " + _icoa_txt if m_rt else
                      "sampled — microbiology on file, retest assay pending" if mb_rt else
                      "pending — not yet sampled")
            # the reissued CoQ issues once the retest assay, the mycotoxins and the
            # internal certificate exist: the schedule's date (issuance_schedule.coq_issue,
            # 7 days after the last certificate it cites), never before the lot was packed
            # one campaign: the assay and the mycotoxins must both come from it
            _rt_issuable = bool(c_rt and m_rt and _camp and _rt and _D_(_rt.get("issue", ""))
                                and TS.series_of(c_rt.split(", (")[0]) == _camp == TS.series_of(m_rt.split(", (")[0]))
            _rt_coq_issue = max(_D_(_rt["issue"]), _cmd) if (_rt_issuable and _cmd) else (_D_(_rt["issue"]) if _rt_issuable else None)
            _rt_scope_docs = [_rt_docs[n] for n in (3, 4, 5, 6, 10) if n in _rt_docs]
            _rt_latest_cited = max(_rt_scope_docs, key=lambda x: str(T.date_key(x[1]))) if _rt_scope_docs else None
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

            def _grading(_entry):
                """Owner, 15.09.2026: the grade the certificate's Total THC result falls in,
                and the product and specification codes that follow (potency_grading.py)."""
                _r4 = next((_x for _x in (_entry or {}).get("rows", []) if _x.get("no") == "4"), None)
                _g = PGR.grading(cu0 if not cu0.startswith("—") else _lot, _strain, _r4["res"] if _r4 else "")
                _g["doc"] = (_r4["doc"] if _r4 and _r4.get("doc") not in (None, "", "—") else "—")
                return _g
            row = dict(common, series="initial release", icoa="", plan_ref=_pref,
                       coq_plan=_coq["n"] if _coq else "— not in the issuance plan —",
                       basis=(_coq["basis"] if _coq and _coq.get("basis") else (_lpk[0] if _lpk else "")),
                       issue=_F_(_icoa_issue) if _icoa_issue else "— packaging date to record —",
                       icoa_issue=_icoa_issue, key=f"{_lot_id}|I",
                       scope=" + ".join(_names[n] for n in (1, 2, 7)),
                       a=cell(1), b=cell(2), fm=cell(7), c=_identc, cnp=_cnp_txt,
                       assay_rt="", myco_rt="", carry="",
                       status="to register")
            ICOA_ROWS.append(row)
            if scope:
                _pending_inst.append((b, key, scope, vals, _ldate, row))
            COQ_ROWS.append(dict(common, series="initial release", key=f"{_lot_id}|I", coq_issue=_coq_issue, coq_flag=_coq_flag,
                                 latest=_latest, icoa_needed=bool(scope), c=_identc, cnp=_cnp_txt, gaps=list(_gaps), old=_old,
                                 grading=_grading(_coq),
                                 plan_coq=_coq["n"] if _coq else "— not in the issuance plan —",
                                 basis=(_coq["basis"] if _coq and _coq.get("basis") else (_lpk[0] if _lpk else ""))))
            if _rt:
                ICOA_ROWS.append(dict(common, series=f"retest — {_tranche}", icoa="", plan_ref="",
                                      coq_plan=_rt["n"] if not _rt["n"].startswith("(") else "CoQ reissue (assigned on issue)",
                                      basis=_rt.get("basis", ""),
                                      issue=_F_(_rt_icoa_day) if _rt_icoa_day else "— at the retest sampling —",
                                      icoa_issue=_rt_icoa_day, test_date=_rt_sampled or "",
                                      key=f"{_lot_id}|R", scope="Ident A + Ident B + Foreign matter",
                                      a=cell(1) if _camp else "to test", b=cell(2) if _camp else "to test", fm=fm if _camp else "to test",
                                      c=c_rt or "— retest assay not yet on file —", cnp="—",
                                      assay_rt=c_rt or "— pending —", myco_rt=m_rt or "— pending —",
                                      carry="#8, #9, #11, #12 from the initial testing", status=_st_rt, sortdate="", campaign=_camp or ""))
                COQ_ROWS.append(dict(common, series=f"retest — {_tranche}", key=f"{_lot_id}|R", coq_issue=_rt_coq_issue, coq_flag="",
                                     latest=_rt_latest_cited, icoa_needed=True, c=c_rt or "— retest assay not yet on file —", cnp="—",
                                     grading=_grading(_rt),
                                     rt_micro=mb_rt or "— pending —",
                                     gaps=[], old=None, plan_coq=_rt["n"] if not _rt["n"].startswith("(") else "CoQ reissue (assigned on issue)",
                                     basis=_rt.get("basis", ""), rt_status=_st_rt, assay_rt=c_rt or "— pending —", myco_rt=m_rt or "— pending —",
                                     sortdate="", campaign=_camp or "", rt_tranche=_tranche, rt_sampled=_rt_sampled or "",
                                     rt_icoa_day=_rt_icoa_day))

    def _bkey(r):
        d = r.get("sortdate") or r["basis"]
        return (0 if r["series"] == "initial release" else 1,
                str(T.date_key(d)) if d else "99999998", r["cu"], r["p"])
    ICOA_ROWS.sort(key=_bkey)
    for _i, _row in enumerate(ICOA_ROWS, 1):
        _row["seq"] = _i
    print(f"iCoA rule: {sum(1 for r in ICOA_ROWS if r['series'] == 'initial release')} initial rows "
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
    _NOT_IN_RELEASE_REGISTER = {c["pp"] for c in _D["coqs"] if c["t"] == "initial release" and not c.get("reg")}
    _issuable, _later, _na = [], [], []
    for r in ICOA_ROWS:
        if r["series"] != "initial release":
            r["why"] = ("sampled %s — the series numbers it" % r["test_date"] if r.get("campaign")
                        else "no campaign sampling date on file")
            _later.append(r)
        elif not r["icoa_issue"]:
            # Owner, 15.09.2026: identification A, B and foreign matter are performed
            # on every batch and every certificate of quality cites the internal
            # certificate, so the series numbers a round whose packaging date the list
            # does not hold; the sheet says the testing date is not stated.
            r["why"] = "no packaging date on the list"
            _later.append(r)
        elif r["fm"] == "held for review":
            r["why"] = "foreign matter held for the Head of QC"
            _later.append(r)
        else:
            _issuable.append(r)
    # The number comes from icoa_register.py and is not computed again here.
    #
    # It used to be: sort these rows, then number them 1..N by position. That is a
    # second definition of a controlled document code, and on 11.09.2026 the owner
    # found what two definitions do — batch J31122501 / P060262 was the first row
    # of this sheet, so it took iCoA-PP_26-001, while its own certificate cited
    # iCoA-PP_26-066. Of the 49 rows that could be compared, none agreed.
    #
    # The module implements the owner's ruling of 10.09.2026: "the register
    # encompasses every internal certificate that exists or ever will … one per
    # testing round, which is exactly the number of certificates of quality" —
    # 106 over 80 batches — ordered by the issue date, then when the work was
    # done, then the batch. The certificates print from it. So does this sheet
    # now, and the local sort survives only to order the rows the module has no
    # entry for.
    _MOD_CODE, _MOD_KNOWN, _MOD_ROWS = {}, set(), []
    try:
        import icoa_register as _IR
        _MOD_ROWS = _IR.build()
        for _m in _MOD_ROWS:
            _suf = "I" if _m["round"] == "initial release" else "R"
            for _base in filter(None, (_m["p_lot"], _m["batch"])):
                _k = f"{T.batch_key(_base)}|{_suf}"
                _MOD_KNOWN.add(_k)
                if _m["code"]:
                    _MOD_CODE.setdefault(_k, _m["code"])
    except Exception as _e:
        print("iCoA codes NOT taken from icoa_register.py:", _e)

    def _mod_keys(r):
        _base, _, _suf = r["key"].rpartition("|")
        return (f"{T.batch_key(_base)}|{_suf}", f"{T.batch_key(r['cu'])}|{_suf}")

    def _mod_code(r):
        return next((_MOD_CODE[k] for k in _mod_keys(r) if k in _MOD_CODE), None)

    def _mod_withheld(r):
        """The register knows this round and deliberately gave it no number.

        A code in an issue-ordered series says the certificate was issued, and a
        certificate with no testing date cannot be. Two lots were being numbered
        here that the register withholds a number from for exactly that reason.
        """
        return any(k in _MOD_KNOWN for k in _mod_keys(r)) and _mod_code(r) is None

    _issuable.sort(key=lambda r: (_mod_code(r) or "zzz",
                                  str(T.date_key(r["icoa_issue"])) if r["icoa_issue"] else "9",
                                  str(T.date_key(r["sortdate"])) if r["sortdate"] else "9",
                                  r["cu"], r["p"]))
    # A row the register does not number is not in the series, and must not be
    # given a number here. There used to be a positional fallback for rows the
    # register cannot identify, and it minted numbers out of this sheet's own
    # row count — which collided head-on with the real series: rows took 061-066
    # while the register had already given those numbers to other rounds.
    _withheld, _unknown = [], []
    for r in _issuable:
        if _mod_withheld(r):
            r["why"] = "no packaging date on the list — the register withholds a number"
            _withheld.append(r)
        elif _mod_code(r) is None:
            # The series is built from the owner's release register. A batch with
            # no entry there has no testing history for it to number, however
            # firmly the plan schedules its certificate — P060362 is packed
            # 23.05.2026 with a CoQ planned and is not in the register.
            if r["p"] in _NOT_IN_RELEASE_REGISTER:
                r["why"] = ("not in the release register — icoa_register.py builds from it and has no "
                            "testing history for this batch to number; the batch has to be entered there first")
            else:
                r["why"] = ("not in icoa_register.py — the register numbers the series and "
                            "does not carry this round")
            _unknown.append(r)
    _issuable = [r for r in _issuable if r not in _withheld and r not in _unknown]
    _later.extend(_withheld + _unknown)
    if _unknown:
        print("iCoA register: %d issuable row(s) the register does not carry, left unnumbered: %s"
              % (len(_unknown), ", ".join(sorted(r["key"] for r in _unknown))))
    _no_mod = 0
    if os.environ.get("ICOA_DEBUG"):
        print("DEBUG _MOD_CODE entries:", len(_MOD_CODE))
        for _k in ("P060152|I", "P060162|I"):
            print("   probe", _k, "->", _MOD_CODE.get(_k))
        for _rr in _issuable[:3]:
            print("   row key=%r cu=%r -> %r" % (_rr["key"], _rr["cu"], _mod_code(_rr)))
        _p = next((x for x in _issuable if x["key"] == "P060152|I"), None)
        print("   P060152 row:", (_p or {}).get("key"), "->", _mod_code(_p) if _p else "no such row")
    for _i, r in enumerate(_issuable, 1):
        _c = _mod_code(r)
        if _c is None:
            _no_mod += 1
        r["code"], r["issuable"] = _c, "yes"
        r["reg_status"] = ("registered — issued with the legacy series on " + _F_(LEGACY_ICOA) if r["group"] == "legacy"
                           else "registered — first working day 5 days after packaging")
        r["icoa"], r["status"] = r["code"], r["reg_status"]
    for r in _later:
        r["code"], r["issuable"] = "— at issue —", "no"
        r["reg_status"] = "not yet issuable — " + r["why"]
        r["icoa"] = r["code"]
        if r["series"] == "initial release":
            r["status"] = r["reg_status"]
    PLANNING = _issuable + sorted(_na, key=lambda r: (str(T.date_key(r["sortdate"])) if r["sortdate"] else "9", r["cu"], r["p"])) \
        + sorted(_later, key=lambda r: (0 if r["series"] == "initial release" else 1 if r["status"].startswith("due") else 2,
                                                          str(T.date_key(r["sortdate"] or r["basis"])) if (r["sortdate"] or r["basis"]) else "9", r["cu"], r["p"]))

    # ------------------------------------------------------- the register IS the standing series
    # Owner, 10.09.2026: "The register encompasses every internal certificate that
    # exists or ever will" — one per testing round. Two modules were deciding
    # which internal certificates exist: icoa_register.py, which holds the series
    # the certificates print from, and the rows above, which are this file's
    # issuance planning for the lots it drafts. A value defined twice disagrees,
    # and this pair did. The sheet printed 60 of the series' 95 codes; it showed
    # no retest certificate at all where the series issues 26, because its retest
    # rows are one per lot per tranche and a lot with four retest rounds had one
    # row standing for four certificates; and it withheld nine more on a rule the
    # owner has replaced. "Where a CNP certificate reports all three, no iCoA is
    # needed" is the note of 05.09.2026; the ruling of 10.09.2026 is
    # "identification A, identification B and foreign matter, ALWAYS", because
    # they are performed in house at packaging whatever an external laboratory
    # also reports. The certificate exists, so the register carries it. WHICH
    # document the certificate of quality cites for those three is a separate
    # question, decided by cell_resolution, and nothing here touches it.
    #
    # So the series is the definition and this sheet renders it, one row per
    # testing round. Planning columns come from the planning row for the same lot
    # and round; a lot the series does not carry keeps its planning row,
    # unnumbered and saying why.
    _plan_lot = {}
    for r in PLANNING:
        _suf = "I" if r["series"] == "initial release" else "R"
        for _b in (r["p"], re.sub(r"[＊*]", "", r["cu"])):
            if _b and not str(_b).startswith(("N/A", "—")):
                _plan_lot.setdefault((T.batch_key(str(_b)), _suf), r)
    _DETN = {"1": "Ident A", "2": "Ident B", "7": "Foreign matter"}

    def _dmy(v):
        import datetime as _dt
        try:
            return _dt.datetime.strptime(str(v), "%d.%m.%Y").date()
        except ValueError:
            return None

    REGISTER, _emitted = [], set()
    for _m in _MOD_ROWS:
        _rel = _m["round"] == "initial release"
        _base = "I" if _rel else "R"
        _plan = next((_plan_lot[(T.batch_key(_b), _base)] for _b in filter(None, (_m["p_lot"], _m["batch"]))
                      if (T.batch_key(_b), _base) in _plan_lot), None)
        # retest 1 keeps the bare |R the planning row already used, so every
        # lookup that cites a register key — the iCoA Issuance sheet, the CoQ
        # Register, and the tracker's own in-house cells through INST_KEY —
        # resolves to the same row it resolved to before. Rounds 2 and up were
        # unaddressable until now and take |R2 … |R5.
        _n = "" if _rel or _m["round"] == "retest 1" else _m["round"].split()[-1]
        _key = ((_plan or {}).get("key") or "%s|%s" % (_m["p_lot"] or _m["batch"], _base))
        _key = _key.rpartition("|")[0] + "|" + _base + _n
        if _key in _emitted:
            # Two certificates cannot share a key: the lookups that cite one
            # take the first match and the second would be invisible. Fall back
            # to the round's own names before giving up, and say so if even that
            # collides — a dropped row here is a certificate missing from the
            # register, which is the defect this block exists to fix.
            _alt = "%s|%s%s" % (_m["p_lot"] or _m["batch"], _base, _n)
            if _alt in _emitted:
                print("iCoA register: %s (%s, %s) collides on key %s and is NOT on the sheet"
                      % (_m["code"] or "unnumbered", _m["batch"], _m["round"], _key))
                continue
            _key = _alt
        _emitted.add(_key)
        _scope = " + ".join(_DETN.get(_d, "#" + _d) for _d in (_m["parameters"] or "").split())
        REGISTER.append({
            "code": _m["code"] or "", "issuable": "yes" if _m["code"] else "no",
            "series": _m["round"],          # the series' own vocabulary: "retest 1" … "retest 5"
            "campaign": _m.get("campaign", ""), "tranche": _m.get("tranche", ""),
            "group": (_plan or {}).get("group", "—"),
            "cu": (_plan or {}).get("cu") or _m["batch"],
            "p": (_plan or {}).get("p") or _m["p_lot"] or "N/A — no P batch assigned",
            "strain": _m["strain"] or (_plan or {}).get("strain", ""),
            "scope": _scope, "cnp": (_plan or {}).get("cnp", "—"),
            "plan_ref": (_plan or {}).get("plan_ref") or "—", "key": _key,
            # The iCoA Issuance sheet was folded into this one (owner, 14.09.2026:
            # "iCoA Issuance basically should be contained inside iCoA Register").
            # Both were already one row per batch and round, so the merge is a
            # column union, not a reshape: the register keeps the identity and the
            # dates it always had and gains the eleven columns only the issuance
            # sheet carried — the per-parameter results, the eCoA that covers each,
            # and the raw harvest/packaging dates behind the testing date.
            "basis": (_plan or {}).get("basis", "—"),
            "harvest": (_plan or {}).get("harvest", "—"),
            "packaging": (_plan or {}).get("packaging", "—"),
            "coq_issue": (_plan or {}).get("coq_issue", ""),
            "a": (_plan or {}).get("a", "—"), "b": (_plan or {}).get("b", "—"),
            "fm": (_plan or {}).get("fm", "—"), "c": (_plan or {}).get("c", "—"),
            "assay_rt": (_plan or {}).get("assay_rt", "—"),
            "myco_rt": (_plan or {}).get("myco_rt", "—"),
            "carry": (_plan or {}).get("carry", "—"),
            # A release round is dated from `Batch Dates` by formula, so the
            # workbook stays live; a retest is dated at its own sampling, which
            # is on no sheet, so the module's date is written as a literal.
            # A release round with no packaging date on the list has nothing for the
            # formula to find; the series dates it (15.09.2026) and the sheet prints
            # that date as a literal, with the testing date not stated.
            "lit_from": (None if _rel else _dmy(_m["tested_from"])) if not (_rel and _m["note"]) else "— not stated —",
            "lit_issue": (None if _rel else _dmy(_m["issued"])) if not (_rel and _m["note"]) else _dmy(_m["issued"]),
            "reg_status": (("registered — %s · %s, tested %s, issued %s" % (_m["round"], _m["tranche"], _m["tested_from"], _m["issued"])
                            if _m.get("campaign") else
                            "registered — %s, issued %s%s" % (_m["round"], _m["issued"],
                                                              (" · " + _m["note"]) if _m["note"] else ""))
                           if _m["code"] else "not yet issuable — %s" % (_m["note"] or "no testing date on file")),
        })
    # Every lot the series does not carry keeps the row the planning gave it. Ten
    # rows arrive here and none of them is an oversight to paper over: three lots
    # have no production record at all, and seven are the starred lots, whose
    # star batch_id.batch_key deliberately keeps — whether GG012601＊ is GG012601
    # is a fact about the floor and is the Head of QC's to rule, not a function's.
    for r in PLANNING:
        if r["key"] in _emitted:
            continue
        _emitted.add(r["key"])
        r["code"] = r.get("code") or ""
        REGISTER.append(r)
    ICOA_BY_KEY = {r["key"]: r for r in ICOA_ROWS}
    # The reissued CoQ cites the CAMPAIGN round's internal certificate. A lot with
    # earlier in-house re-tests has that round as retest 4 or 5 (|R4, |R5), so the
    # CoQ row's key follows the register row that carries the campaign.
    _camp_key = {}
    for _rg in REGISTER:
        if _rg.get("campaign"):
            _camp_key.setdefault(_rg["key"].rpartition("|")[0], _rg["key"])
    for r in COQ_ROWS:
        if r["series"] != "initial release" and r.get("campaign"):
            r["key"] = _camp_key.get(r["key"].rpartition("|")[0], r["key"])
    _cq_ok, _cq_alloc, _cq_later = [], [], []
    # A reissue supersedes the lot's initial certificate, so it cannot be numbered
    # before that certificate is: a lot whose release CoQ the register withholds
    # (no packaging date on the list — FB042601, CC042601) has its Tranche 2
    # reissue withheld with it, whatever the campaign has on file (15.09.2026).
    _init_held = set()
    for r in COQ_ROWS:
        if r["series"] == "initial release":
            ic = ICOA_BY_KEY.get(r["key"])
            if not r["coq_issue"] or (r["icoa_needed"] and ic and ic["issuable"] != "yes"):
                _init_held.add((r["cu"], r["p"]))
    # the campaign's internal certificate, as the iCoA Register numbers it (the
    # sheet's own rows, campaign keys included — not the planning row's status)
    _reg_code = {r["key"]: str(r.get("code") or "") for r in REGISTER}
    for r in COQ_ROWS:
        ic = ICOA_BY_KEY.get(r["key"])
        if r["series"] != "initial release":
            if (r["cu"], r["p"]) in _init_held:
                r["why"] = "its initial certificate is not yet issuable"
                r["rt_status"] = "initial certificate withheld — " + r.get("rt_status", "pending")
                _cq_later.append(r)
            elif r["coq_issue"]:
                _cq_ok.append(r)
            elif str(r.get("rt_tranche", "")).startswith("Tranche 3") and _reg_code.get(r["key"], "").startswith("iCoA-PP_26-"):
                # Owner, 15.09.2026 (evening): every Tranche 3 retest parameter is tested at
                # Farmahem and its certificates all issue on one date, so the Tranche 3
                # reissues take their codes now — after the last Tranche 2 reissue, in the
                # order the series would give them — and only the date waits for the 227-М
                # mycotoxin certificate. The one code computed in advance, by the owner's
                # own ruling; Issuable reads "allocated", never "yes".
                _cq_alloc.append(r)
            else:
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
        if r["series"] != "initial release":
            _kb, _, _ks = r["key"].rpartition("|")
            r["reg_status"] = ("registered — retest, %s, sampled %s; issued %s, 7 days after %s of %s; cites %s of %s"
                               % (r["rt_tranche"], r["rt_sampled"], _F_(r["coq_issue"]),
                                  r["latest"][0] if r["latest"] else "—", r["latest"][1] if r["latest"] else "—",
                                  _MOD_CODE.get(f"{T.batch_key(_kb)}|{_ks}", "the campaign iCoA"), _F_(r["rt_icoa_day"])))
            continue
        r["reg_status"] = (("registered — legacy series, issued " + _F_(LEGACY_COQ) if not r["coq_flag"] else "registered — " + r["coq_flag"])
                           if r["group"] == "legacy" else
                           ("registered — first working day 7 days after the latest eCoA" if not r["coq_flag"] else "registered — " + r["coq_flag"]))
        # Head of QC, 05.09.2026 (evening): a production lot whose initial certificate for a
        # determination is not on file keeps its planned CoQ and number — the initial testing
        # exists at the Faculty of Pharmacy's Center for Natural Products and the certificate is
        # to be located (Work Order); the number is not withheld for it
        if r["gaps"]:
            r["reg_status"] += " · initial certificate to locate: " + ", ".join(f"#{n} ({'IJZ' if n == 9 else 'CNP'})" for n in r["gaps"])
    _cq_alloc.sort(key=lambda r: (r["cu"], r["p"]))
    for _j, r in enumerate(_cq_alloc, len(_cq_ok) + 1):
        r["code"], r["issuable"] = f"CoQ-PP_26-{_j:03d}", "allocated"
        r["coq_issue"] = _D_(T3_ISSUE) if T3_ISSUE else None
        _kb, _, _ks = r["key"].rpartition("|")
        r["reg_status"] = ("allocated — code reserved 15.09.2026 for the %s reissue (owner: every Tranche 3 retest parameter is "
                           "tested at Farmahem and its certificates all issue on one date); sampled %s, retest assay %s on file, "
                           "mycotoxins pending; %s, after every Tranche 2 reissue; cites %s of %s"
                           % (r["rt_tranche"], r["rt_sampled"], str(r.get("assay_rt", "")).split(", (")[0],
                              ("planned %s — the owner's date of 15.09.2026 for all of Tranche 3, the 227-М certificates expected by "
                               "18.09.2026, provisional until they exist" % _F_(r["coq_issue"])) if r["coq_issue"] else
                              "issued on the owner's date once the 227-М certificate exists",
                              _MOD_CODE.get(f"{T.batch_key(_kb)}|{_ks}", "the campaign iCoA"), _F_(r["rt_icoa_day"])))
    for r in _cq_later:
        r["code"], r["issuable"] = "— at issue —", "no"
        r["reg_status"] = "not yet issuable — " + r["why"]
    for r in _cq_later:
        if r["series"] != "initial release":
            r["reg_status"] = "not yet issuable — " + r["rt_status"] + " · issued 7 days after the latest retest certificate once the assay, the mycotoxins and the iCoA exist"
    # After the numbered and the allocated rows, the batches the tranches do not cover
    # — under production, under testing, or on no tranche list — lot by lot. Such a
    # batch has a release row and no retest row: only the tranche batches are for
    # sale, so only they were retested at the QP's request (owner, 15.09.2026).
    _lot_day = {}
    for r in COQ_ROWS:
        if r["series"] == "initial release":
            _d = r["sortdate"] or r["basis"]
            _lot_day[(r["cu"], r["p"])] = str(T.date_key(_d)) if _d else "9"
    COQ_REGISTER = _cq_ok + _cq_alloc + sorted(_cq_later, key=lambda r: (_lot_day.get((r["cu"], r["p"]), "9"), r["cu"], r["p"],
                                                                         0 if r["series"] == "initial release" else 1))
    # The register sheet is the series, so it is the series that is counted here.
    # This line used to report the planning rows it numbered — 60 — while the
    # sheet carried 95 codes, which is how a stale statistic outlives the thing
    # it described.
    _rg_num = [r for r in REGISTER if r.get("code", "").startswith("iCoA-PP_26-")]
    print(f"iCoA register: {len(_rg_num)} numbered (iCoA-PP_26-001 … "
          f"{_rg_num[-1]['code'][-3:] if _rg_num else '—'}; "
          f"{sum(1 for r in _rg_num if r['series'] == 'initial release')} release, "
          f"{sum(1 for r in _rg_num if r['series'] != 'initial release')} retest), "
          f"{len(REGISTER) - len(_rg_num)} not yet issuable "
          f"({sum(1 for r in REGISTER if not r.get('code', '').startswith('iCoA-PP_26-') and r['series'] == 'initial release')} "
          f"initial, {sum(1 for r in REGISTER if not r.get('code', '').startswith('iCoA-PP_26-') and r['series'] != 'initial release')} retest)")
    print(f"CoQ register: {len(_cq_ok)} numbered (CoQ-PP_26-001 … {_cq_ok[-1]['code'][-3:] if _cq_ok else '—'}; "
          f"{sum(1 for r in _cq_ok if r['group'] == 'legacy' and not r['coq_flag'])} legacy on 27.05.2026, "
          f"{sum(1 for r in _cq_ok if r['group'] == 'legacy' and r['coq_flag'])} legacy moved, "
          f"{sum(1 for r in _cq_ok if r['group'] != 'legacy')} post-SOP), {len(_cq_alloc)} allocated in advance (Tranche 3: code reserved, planned {_F_(_D_(T3_ISSUE)) if T3_ISSUE else 'undated'}, provisional), {len(_cq_later)} not yet issuable "
          f"({sum(1 for r in _cq_later if r['series'] == 'initial release')} initial: "
          f"{sum(1 for r in _cq_ok if r['gaps'])} numbered with an initial certificate to locate; "
          f"{sum(1 for r in _cq_later if r['series'] != 'initial release')} retest)")
    print("adherence flags:", len(FLAGS))
    for _f in FLAGS:
        print("   ", _f)
    # the in-house instance carries the register code (or the at-issue placeholder); the tracker
    # cell that cites it is a lookup into the register by KEY (INST_KEY), so it follows a renumbering
    INST_KEY = {}

    def _inst_ck(ref):
        """INST_KEY's key for an in-house reference. nkey() folds a trailing parenthetical
        away, and the at-issue placeholder names its lot in one — so under nkey every lot
        whose internal CoA was at issue shared ONE key, the last lot written held it, and
        the in-house cells of the other eight (v26: GG012601*, GG1024, JD012601*, JD112501*,
        OMP1024_01, BSS1024_01/1, BSS1024_01/2, WED102501) looked SCR012601's certificate up.
        Invisible while every one of them was at issue; wrong the day any was numbered.
        The placeholder is its own key; a register code folds as before."""
        return ref if str(ref).startswith("iCoA — at issue") else T.nkey(ref)

    for b, key, scope, vals, _ldate, row in _pending_inst:
        ref = row["code"] if row["code"].startswith("iCoA-PP_") else f"iCoA — at issue ({row['p'] if row['p'].startswith('P0') else row['cu']})"
        ck = T.nkey(ref)
        INST_KEY[_inst_ck(ref)] = row["key"]
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
# a v8 value the page contradicts, corrected from a third read (15.09.2026)
VALUE_CORRECTIONS = {}
_vc = os.path.join(HERE, "value_corrections_2026-09-15.json")
if os.path.exists(_vc):
    for _c in json.load(open(_vc, encoding="utf-8"))["corrections"]:
        VALUE_CORRECTIONS.setdefault(T.nkey(_c["code"]), {})[str(_c["no"])] = _c["page"]


def values_of(code, lab, cu, scope=None):
    """v8's reading where it has one; the desk's verified value where it does not.

    Every value leaves here in the desk's controlled spelling. This is the one
    funnel a result passes through on its way into the workbook, so the audit of
    11.09.2026 — nine spellings of *absent*, seven of *below quantitation*, a
    `Confirms` typo for the verdict and three multiplication signs — is closed at
    the source rather than in each sheet that prints it. `canon` rewrites notation
    only: digits, markers, glosses and a laboratory's own verdict all survive.
    """
    out = dict(v8_of(code, cu, V8VAL))
    desk = desk_values(code, lab, cu, scope)
    for no, v in desk.items():
        if no not in out:
            out[no] = f"{v} ᴿ"        # ᴿ: the release register or a page read, not v8's extraction
            REGISTER_ONLY.add((T.nkey(code), no))
    # The owner's own "n.r." mark on a line the laboratory did not print. The ND
    # ruling (10.09.2026) folds n.r. PRINTED BY A LABORATORY into ND; the boundary
    # ruled on 11.09.2026 is that an analyte absent from the panel is not a result.
    # The IJZ release certificates print one mycotoxin line (total aflatoxins) and
    # the register says "not tested" for B1 and OTA — the page of 752/2025, read on
    # 15.09.2026, has no B1 or OTA line at all — so where the desk holds no result
    # for the determination, v8's n.r. is "not reported", never ND. Where the desk
    # does hold one (the Farmahem -М- certificates' total aflatoxins, ND on the
    # register), the ruling stands and the cell reads ND.
    for no, v in list(out.items()):
        if str(v).strip().lower() in ("n.r.", "n.r", "nr") and no not in desk:
            out[no] = "not reported"
    # Corrections from a third read of the page (tracker/value_corrections_2026-09-15.json)
    for no, v in VALUE_CORRECTIONS.get(T.nkey(code), {}).items():
        out[no] = v
    return {no: RV.canon(v, no) for no, v in out.items()}


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
            # The printed code is the one the certificate itself prints: Farmahem's
            # loss-on-drying series is ГС (губитоци при сушење), not the GS the register
            # spells it in seven rows nor the LoD the scans' file names carry
            # (document_codes.py, read off the pages on 16.09.2026). The LOOKUP key is
            # untouched — T.nkey folds all three spellings together already.
            # An uncredited document says why: the starred second sample of a lot is real
            # data that never certifies (owner, 16.09.2026); anything else is simply on file.
            _why = (" · experimental — starred sample, not certifying" if TS.is_experimental(code)
                    else " · on file, not credited") if here else ""
            ref = (f"{DC.canon(code)}, ({date}) [{lab}]" + ("" if here[3] else _why)) if here \
                else ("— no certificate —" if state == "red" else "")
            ref_disp = ref
            if here and ICOA_RULE and _inst_ck(code) in INST_KEY:
                # The suffix follows the credit flag here exactly as it does on
                # the literal reference above; this formula used to drop it, so
                # a grey in-house cell read like a credited one.
                ref = ("=IFERROR(INDEX('iCoA Register'!$B:$B,MATCH(\"%s\",'iCoA Register'!$%s:$%s,0)),\"iCoA — at issue\")&\", (%s) [PP]%s\""
                       % (INST_KEY[_inst_ck(code)], REG_KEY_COL, REG_KEY_COL, date,
                          "" if here[3] else _why))
            elif here and str(code).startswith("NO-DOC-CODE"):
                # An in-house report with no document code of its own, cited directly
                # on Identification A and foreign matter for GG1024, HPA1024 and
                # OPM1024. The standing ruling is that an in-house result is never
                # referenced on a certificate of quality — it is carried by an
                # internal CoA, which is what covers these determinations. None of
                # the three lots has a packaging date, so their internal CoA is one
                # of the seven the register leaves unnumbered; the reference says so
                # in the register's own words rather than printing a placeholder
                # that reads like a document code.
                ref = ref_disp = (f"iCoA — at issue ({b['p'] if b['p'].startswith('P0') else b['cu']})"
                                  f", ({date}) [PP]")

            if p["subs"]:
                for j, no in enumerate(p["subs"]):
                    if here:
                        v = values_of(here[0], here[2], b["cu"], scope_of(b, here[0])).get(no)
                        blank = not any(values_of(here[0], here[2], b["cu"], scope_of(b, here[0])).get(x)
                                        for x in p["subs"])
                        # "not reported" is the desk saying this certificate does not
                        # carry this sub-determination. It used to print "n.r.", which
                        # the owner's ruling of 10.09.2026 reserves: any derivation of
                        # n.r. printed as a PARAMETER RESULT is ND. This is not a
                        # result — writing ND here would assert the analyte was
                        # measured and absent, which is the one thing the cell knows
                        # to be untrue — so the annotation is spelled out instead and
                        # the notation is left to results.
                        cell_v = v or (silence_reason(here[0], here[2], b["cu"], no) if blank and j == 0
                                       else ("" if blank else "not reported"))
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
       "later blocks. For #9, #10 and #11 each sub-determination has its own column on the top row. \"not reported\" = that sub-determination "
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
    "not reported": "Not reported on this certificate.",
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
    put(aud, _r, 8, why, F7B, FILL["amber"] if why in ("not on this certificate", "not reported") else FILL["red"], CEN)
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
    for _n in range(1, 13):                  # every determination the new lot's certificates cover, not #9 alone
        for _c, _d, _l in _b["docs"][_n]:
            _k = ("lot not on tracker", _b["p"], _c)
            tasks[_k]["params"].add(_n)
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

    rows, _dups, _starred = {}, [], []
    for r in range(2, last + 1):
        _cu0 = str(cov.cell(r, 1).value or "")
        k = rowkey(_cu0, str(cov.cell(r, 2).value or ""))
        if k in rows:
            _dups.append(r)                 # the owner's re-analysis row of a lot the tracker already merged
        else:
            rows[k] = r
        # A starred row with no P batch beside an unstarred row that has one is not a
        # second lot: it is the same lot's second sample (owner, 16.09.2026), and the
        # tracker folds it the same way. rowkey strips the star but keeps the P lot, so
        # the two do not collide on their own.
        if re.search(r"[＊*]", _cu0) and k[1] == "— not assigned —":
            _starred.append((r, k[0]))
    for r, _base in _starred:
        if any(kc == _base and kp != "— not assigned —" for kc, kp in rows):
            _dups.append(r)
            print(f"coverage: starred row {_base}＊ folded into the {_base} row — one lot, two samples")

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

    # ---- Certificates (n) and Labs present, derived rather than inherited.
    #
    # Both columns came down from v6 and were *incremented* by each pass that
    # touched a lot, so they counted documents the tracker does not cite and could
    # not be reconciled with it: the audit of 11.09.2026 found 22 rows whose count
    # exceeded the documents actually referenced (JD012603 said 7, the tracker
    # cites 2) and 26 rows naming a laboratory that appears in no reference on the
    # lot. The count was not wrong so much as answering a different question —
    # it included the 09.09 documents the desk has not recorded — so the two
    # questions now get two pairs of columns, and both are computed from scratch
    # here rather than carried forward.
    _cited, _onfile = {}, collections.defaultdict(set)
    for b in batches:
        k = rowkey(b["cu"], b["p"])
        seen = {}
        for n in range(1, 13):
            for c, d, l in b["docs"][n]:
                seen.setdefault(T.nkey(c), l)
        _cited[k] = seen
    for u, rr, lab in COV_0909_APPLIED:
        _onfile[rr].add((u["Now covered by"].strip(), lab))
    _hdr = cov.cell(1, 19)
    for _c, _t in ((19, "Certificates (n)"), (20, "Labs present"),
                   (21, "On file, not recorded (n)"), (22, "Labs on file, not recorded")):
        if _c > 20:
            _style_from(cov.cell(1, _c), _hdr)
            cov.column_dimensions[L(_c)].width = 22
        cov.cell(1, _c).value = _t
    for r in range(2, last + 1):
        k = rowkey(str(cov.cell(r, 1).value or ""), str(cov.cell(r, 2).value or ""))
        cites = _cited.get(k)
        if cites is None:                    # a row whose lot the tracker names differently
            _p = k[1]
            cites = next((v for (kc, kp), v in _cited.items() if kp == _p and _p != "— not assigned —"), {})
        cov.cell(r, 19).value = len(cites)
        _labs = collections.Counter(cites.values())
        cov.cell(r, 20).value = "; ".join(f"[{a}] {b_}" for a, b_ in sorted(_labs.items())) or "—"
        extra = _onfile.get(r, set())
        for _c in (21, 22):
            if cov.cell(r, _c).value is None:
                _style_from(cov.cell(r, _c), cov.cell(r, 19 if _c == 21 else 20))
        cov.cell(r, 21).value = len({c for c, l in extra})
        _el = collections.Counter(l for c, l in extra if l)
        cov.cell(r, 22).value = "; ".join(f"[{a}] {b_}" for a, b_ in sorted(_el.items())) or "—"
    print("coverage: Certificates (n) and Labs present derived from the tracker's own "
          f"references; {sum(1 for r in range(2, last + 1) if cov.cell(r, 21).value)} row(s) "
          "carry documents on file that the desk has not recorded")

    if cov.auto_filter.ref:
        cov.auto_filter.ref = f"A1:{L(22)}{last}"
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
               or (cu0.startswith("— not recorded —") and p == bp) or (cu0.startswith("— not recorded —") and p and p in b["p"]):
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
        if not any(re.sub(r"[＊*]", "", cu) == mcu or (cu.startswith("— not recorded —") and p in mp) for mcu, mp in matched):
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
                v = row.get("test_date") or "— at the retest sampling —"
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
            # From here: the columns the iCoA Issuance sheet used to carry alone,
            # folded in on 14.09.2026 so one sheet answers both questions — which
            # internal certificates exist, and what each one actually covers.
            ("Basis date", 12), ("Harvest", 24), ("Packaging", 28), ("CoQ issue (planned)", 16),
            ("#1 Ident. A", 14), ("#2 Ident. B", 14), ("#7 Foreign matter", 16),
            ("Ident C — covered by (eCoA)", 34), ("Retest assay #4–#6 (eCoA)", 34),
            ("Retest mycotoxins #10 (eCoA)", 34), ("Carried forward", 30),
            ("Key", 14), ("Status", 60)]
COQ_COLS = [("No.", 6), ("CoQ code", 18), ("Issuable", 9), ("Issue date (planned)", 18), ("Rule date", 14),
            ("Latest eCoA cited (date)", 16), ("Latest eCoA cited (code)", 22), ("iCoA (register)", 16), ("iCoA issue date", 14),
            ("Group", 10), ("Series", 20), ("CU Batch", 16), ("P Batch", 12), ("Strain", 20), ("Ident C — eCoA (Total THC)", 34),
            ("CNP references", 26), ("Supersedes (old in-house CoA)", 26), ("Plan reference (31.08.2026)", 22), ("Key", 14),
            ("Status", 64),
            # Owner, 15.09.2026: a reissue names the initial certificate it supersedes,
            # by the register's own code (a lookup by key, so it follows a renumbering);
            # and every certificate states the grade its Total THC result falls in, with
            # the product and specification codes that follow (potency_grading.py).
            ("Supersedes (initial CoQ)", 20), ("Total THC (%)", 11), ("THC certificate", 20),
            ("Grade nominal ± tol. (numeral)", 20), ("Grade window", 16), ("Product code", 18),
            ("Specification code", 22), ("Specification status", 34), ("Grading note", 36)]
REG_NOTE = ("THE STANDING REGISTER OF INTERNAL CERTIFICATES OF ANALYSIS. Head of QC, 10.09.2026: \"the register encompasses every "
            "internal certificate that exists or ever will\" — ONE PER TESTING ROUND, not one per lot and not only the ones the "
            "drafted certificates happen to need. Each carries identification A, identification B and foreign matter ALWAYS "
            "(performed in house, on the first day of packaging for the release round and at its own sampling for a retest), plus "
            "any determination whose only result in that round is an in-house record. Codes iCoA-PP_26-nnn, one series for the "
            "year of issue, in the order of issue: by issue date, then by when the work was done, then by batch — {icoa} for "
            "anything that would otherwise predate the specification SOP, so the backlog shares one date and orders by packaging, "
            "as the CoQ series does. THE ROWS, THE NUMBER AND THE CODE ARE NOT COMPUTED HERE (11.09.2026): this sheet RENDERS "
            "icoa_register.py, which is the series, and writes its numbers as literal values. Two things were being decided twice "
            "and disagreed. The number used to be a formula over this sheet's own row order, so the first physical row took "
            "iCoA-PP_26-001 while its own certificate cited iCoA-PP_26-066 and none of the 49 comparable rows agreed; and the ROW "
            "SET was this sheet's issuance planning, so it printed 60 of the series' 95 codes, showed no retest certificate at all "
            "where the series issues 26 (its retest rows are one per lot per tranche — a lot with four retest rounds had one row "
            "standing for four certificates), and withheld nine more under \"where a CNP certificate reports all three, no iCoA is "
            "needed\", the note of 05.09.2026 that the ruling of 10.09.2026 replaced: the in-house laboratory performs those three "
            "whatever an external laboratory also reports, so the certificate exists and is registered. Which document the "
            "CERTIFICATE OF QUALITY cites for them is a separate question and is unchanged. Rows below the series are lots it does "
            "not carry — a retest that is planned but not yet sampled, a lot with no production record, and the starred lots, "
            "whose star batch_id.batch_key deliberately keeps because whether GG012601＊ is GG012601 is the Head of QC's to rule. "
            "They are unnumbered and say why. Inserting a row renumbers nothing. verify_workbook.py compares sheet and series on "
            "every run. FORMULAS remaining: a release round's testing date and packaging-complete date are looked up on Batch "
            "Dates by P batch (else by the batch as listed) and its issue date is the later of that testing date and {icoa}; a "
            "RETEST is dated at its own sampling day and issued on its campaign's day (sampling_dates.py, owner 15.09.2026: "
            "Tranche 1 sampled 21–24.07.2026 and issued 27.07.2026, Tranche 2 sampled 12–14.08.2026 and issued 17.08.2026, "
            "Tranche 3 sampled 19–21.08.2026 and issued 24.08.2026, each batch on the day its certificate number falls), "
            "which no sheet holds, so the series' dates are written as literals rather than guessed by a formula. A round "
            "whose packaging date the list does not hold is numbered all the same (owner, 15.09.2026: identification A, B "
            "and foreign matter are performed on every batch) and says its testing date is not stated. CoQ (register) is looked up on the CoQ Register by Key — the "
            "tracker's in-house cells cite this register by Key, so they follow it. Working days are Monday to Friday; public "
            "holidays are not applied.")
COQ_NOTE = ("Head of QC, 05.09.2026: preliminary CoQ issuance register — codes CoQ-PP_26-nnn (nnn = 001 … 999), one series for the "
            "year of issue, in the order of issue. LEGACY lots (packed before the SOP floor of 11.05.2026, or holding an old "
            "in-house QCCoA 001 certificate, which the CoQ supersedes) are all issued on {coq}, in chronological order of "
            "packaging; POST-SOP lots follow, each on the first working day 7 days after the latest eCoA the CoQ cites and never "
            "before {coq}, so the legacy series keeps 001 onward. Every CoQ "
            "cites its lot's iCoA (identification A, B, foreign matter) and reports identification C as 'Conforms', referenced to "
            "the eCoA that covers Total THC. ADHERENCE (ISSUE_COQ_CONVENTIONS): a CoQ never precedes a document it cites — a legacy "
            "lot whose latest eCoA is dated after {coq} takes the post-SOP rule and is flagged in Status; a CoQ never precedes "
            "its iCoA; Head of QC, 05.09.2026 (evening): a production lot whose initial certificate for a determination is not on "
            "file keeps its planned CoQ and number — the initial testing exists at the Faculty of Pharmacy's Center for Natural "
            "Products (microbiology: IJZ) and the certificate is to be located (Work Order; Status names the determination); a "
            "certificate dated on or after 01.07.2026 is a retest document (the QP's campaign: Tranche 1, the first 21 lots, sampled "
            "July 2026; then Tranches 2 and 3) and never certifies the initial CoQ — a determination whose only certificate is a "
            "retest one is uncertified for the legacy CoQ and flagged; the IJZ-MB delivery of 25/26.08.2026 (certificates of 31.08 and "
            "01.09.2026, 68 to 436 days after packaging) is one campaign sampling and every certificate in it is a retest document, "
            "for the post-SOP lots too; nothing is dated on a weekend. RETEST ROWS: the reissued CoQ "
            "carries the retest results (cannabinoids with identification C by Farmahem, mycotoxins) and, for every determination "
            "not retested, the initial certificate's result and document (owner, 15.09.2026); its rule date is 7 days after the "
            "latest retest certificate it cites, and it is numbered, in date order with the release series, once the retest assay, "
            "the mycotoxins and the campaign's internal certificate (sampled and issued per sampling_dates.py) all exist — Tranche 1 "
            "and Tranche 2 in this build (Tranche 2 since v30, its potency certificates of 25/26.08.2026 taken in on 15.09.2026). TRANCHE 3 (owner, 15.09.2026, evening): "
            "every Tranche 3 retest parameter is tested at Farmahem and its certificates all issue on one date, so the Tranche 3 reissues take their codes now — "
            "after the last Tranche 2 reissue, in the order the series gives them — with Issuable reading 'allocated' and the planned date the owner's: {t3}, all "
            "Tranche 3 certificates on one day, the 227-М mycotoxin certificates expected by 18.09.2026, provisional until they exist; the one code computed "
            "in advance, by the owner's ruling. After the numbered and the allocated "
            "rows, the batches the tranches do not cover — under production, under testing, or on no tranche list — are listed lot by lot; such a batch carries "
            "its release certificate and no retest row, because only the tranche batches are for sale and only they were retested at the QP's request "
            "(owner, 15.09.2026). FORMULAS: No. counts the rows whose Issuable is 'yes' or 'allocated'; No. and the code as on the iCoA Register; Rule date is {coq} for a legacy row "
            "whose latest eCoA is on or before it, else the first working day 7 days after the latest eCoA (not before {coq}); the planned date is the "
            "latest of the rule date, the iCoA's date and the lot's last day of packaging; iCoA (register) and its date are looked up on the iCoA Register by Key. "
            "SUPERSEDES (initial CoQ): a reissue names the initial certificate of the same lot by the register's own code, looked up by Key, so it follows a "
            "renumbering; n/a on an initial certificate. POTENCY GRADING (owner, 15.09.2026): the Total THC result the certificate prints, the certificate it "
            "comes from, the grade of the Head of QC's potency specification of 15.09.2026 (Potency Grades tab) whose window it falls in — nominal ± tolerance, "
            "with the strain's grade numeral — and the product code {{ABBR}}_THC{{nominal}} : CBD1 and specification document code "
            "QCSP_001_{{ABBR}}-{{numeral}}_v.01 that follow — always v.01 (owner, 15.09.2026: the initially issued specifications were wrong and this is not the "
            "official issuing; the set goes for review), the status recording what the issued v.01 of the same strain and numeral printed. The numeral is "
            "SEQUENTIAL within the strain (owner, 15.09.2026): the grades of the specification of 15.09.2026 are numbered as that table lists them, frozen in "
            "potency_grades_2026-09-15.csv, and a grade defined later takes the strain's next numeral whatever its nominal — so -II is not lower or higher than -I, "
            "only later. A result in no window of its strain needs a specification of its own: the row says 'new specification required', names the nearest window "
            "and reserves the strain's next numeral for it; no grade is guessed. "
            "The latest eCoA cited is a value (the first credited certificate per determination dated before the retest campaign; "
            "for a retest row, the latest retest certificate), recomputed by the builder. Working days are Monday to Friday; public holidays are not applied.")

# Both notes used to print the legacy issue days as literals while the rows took
# theirs from --legacy-icoa / --legacy-coq, so a sheet could state one date and
# issue on another — as the CoQ Register did, saying 27.05.2026 over rows dated
# 06.06.2026. The note now says whatever the series issues on.
REG_NOTE = REG_NOTE.format(icoa=_F_(LEGACY_ICOA))
COQ_NOTE = COQ_NOTE.format(coq=_F_(LEGACY_COQ), t3=(_F_(_D_(T3_ISSUE)) if T3_ISSUE else "not yet set"))


def _roll(expr):
    """The first working day on or after the date expression (Mon–Fri): Saturday +2, Sunday +1."""
    return f"({expr})+CHOOSE(WEEKDAY({expr},2),0,0,0,0,0,2,1)"


def _XD(d):
    """A Python date as an Excel DATE() literal, so one constant drives both."""
    return "DATE(%d,%d,%d)" % (d.year, d.month, d.day)


def _fill_register(sh):
    """The iCoA register as an Excel table whose number, code and dates are formulas."""
    from openpyxl.worksheet.table import Table, TableStyleInfo
    # Every lookup into this register matches on REG_KEY_COL. If a column is ever
    # inserted ahead of Key without moving that constant, MATCH silently starts
    # reading a different column and hands back another lot's code — so the build
    # refuses rather than shipping a register whose own lookups are off by n.
    _key_at = L([_t for _t, _w in REG_COLS].index("Key") + 1)
    assert _key_at == REG_KEY_COL, (
        "REG_KEY_COL is %r but REG_COLS puts Key in column %r — every formula that "
        "looks this register up by key would match the wrong column." % (REG_KEY_COL, _key_at))
    for _i, (_t, _w) in enumerate(REG_COLS, 1):
        put(sh, 1, _i, _t, FW, NAVY, CEN)
        sh.column_dimensions[L(_i)].width = _w
    sh.row_dimensions[1].height = 22
    BD_ = "'Batch Dates'"
    _r = 2
    for r in REGISTER:
        # The number and the code are LITERALS taken from icoa_register.py, not
        # formulas over this sheet's row order. COUNT(A$1:A{n})+1 numbered a
        # controlled series by where a row happened to sit, which is how the
        # first physical row took iCoA-PP_26-001 while its certificate cited
        # iCoA-PP_26-066. A document code is not a function of its row.
        import re as _re
        _m = _re.search(r"(\d+)$", str(r.get("code") or ""))
        f_no = int(_m.group(1)) if _m else ""
        f_code = r.get("code") or "— at issue —"
        # Owner, 10-11.09.2026: the internal certificate is tested on the FIRST
        # day of packaging (column E, not the packaging-complete date in F) and
        # issued that day, or on the specification SOP's day where that day comes
        # first. No lag and no roll to a working day — this is the same arithmetic
        # `issuance_schedule.icoa_issue` does, and the certificates print that.
        f_issue = f'=IF(A{_r}="","",IF(ISNUMBER(E{_r}),MAX({_XD(LEGACY_ICOA)},E{_r}),{_XD(LEGACY_ICOA)}))'
        f_from = (f'=IFERROR(INDEX({BD_}!$F:$F,MATCH(J{_r},{BD_}!$C:$C,0)),'
                  f'IFERROR(INDEX({BD_}!$F:$F,MATCH(I{_r},{BD_}!$B:$B,0)),""))')
        f_to = (f'=IFERROR(INDEX({BD_}!$G:$G,MATCH(J{_r},{BD_}!$C:$C,0)),'
                f'IFERROR(INDEX({BD_}!$G:$G,MATCH(I{_r},{BD_}!$B:$B,0)),""))')
        # A release round is tested on the packaging date, which `Batch Dates`
        # carries, so both dates stay formulas and the workbook stays live. A
        # retest is tested at its own sampling, which is on no sheet to look up:
        # the series computed it and it is written here as a literal, because a
        # formula over a value the workbook does not hold can only be a guess.
        if r.get("lit_from"):
            f_from = r["lit_from"]          # a date, or "— not stated —"
        if r.get("lit_issue"):
            f_issue = r["lit_issue"]
        cells = (f_no, f_code, r["issuable"], f_issue,
                 f_from if (r["series"] == "initial release" or r.get("lit_from")) else "— at the retest sampling —", f_to,
                 r["group"], r["series"], r["cu"], r["p"], r["strain"], r["scope"], r["cnp"],
                 COQ_LOOKUP("B", r["key"], "—"), r.get("plan_ref") or "—",
                 # folded in from the former iCoA Issuance sheet
                 r.get("basis") or "—", r.get("harvest") or "—", r.get("packaging") or "—",
                 COQ_LOOKUP("D", r["key"], ""),
                 r.get("a") or "—", r.get("b") or "—", r.get("fm") or "—", r.get("c") or "—",
                 r.get("assay_rt") or "—", r.get("myco_rt") or "—", r.get("carry") or "—",
                 r["key"], r["reg_status"])
        # Column roles are looked up by HEADER, not written as numbers. They were
        # literals — Status was 17, Key was 16 — and folding the issuance sheet in
        # moved both ten columns to the right, which would have painted the fill
        # on "Ident C — covered by" and left Status unwrapped.
        _hdr = [_t for _t, _w in REG_COLS]
        _at = lambda name: _hdr.index(name) + 1
        _c_status, _c_cnp, _c_plan = _at("Status"), _at("CNP reference"), _at("Plan reference (31.08.2026)")
        _c_dates = {_at("Issue date (planned)"), _at("Test date (packaging)"),
                    _at("Packaging complete"), _at("CoQ issue (planned)")}
        for _i, v in enumerate(cells, 1):
            c = put(sh, _r, _i, v, F7B if _i in (2, 9) else F7,
                    FILL["green"] if (_i == _c_status and str(v).startswith("registered")) or (_i == 3 and v == "yes") else
                    FILL["amber"] if (_i == _c_status and str(v).startswith("not yet")) or (_i == 3 and v == "no")
                    or (_i in (_c_cnp, _c_plan) and str(v).startswith("—")) else None,
                    CEN if _i != _c_status else Alignment(horizontal="left", vertical="center", wrap_text=True))
            if _i in _c_dates:
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
        f_no = f'=IF(OR(C{_r}="yes",C{_r}="allocated"),COUNT(A$1:A{_r - 1})+1,"")'
        f_code = f'=IF(A{_r}<>"","CoQ-PP_26-"&TEXT(A{_r},"000"),"— at issue —")'
        # Owner, 10.09.2026: five to ten days after the last external certificate
        # the sheet cites, floored to the blanket day. LAG_DAYS is 7 in
        # issuance_schedule.py and 7 here, and neither rolls to a working day.
        f_rule = (f'=IF(ISNUMBER(F{_r}),MAX({_XD(LEGACY_COQ)},F{_r}+7),{_XD(LEGACY_COQ)})')
        # never before the rule date, never before the internal certificate it
        # references, and never before the lot finished being packed. The last is
        # not decoration: P060482's last external certificate is dated 30.06.2026
        # and the lot was still being packed on 05.08.2026.
        _pkc = f"INDEX('iCoA Register'!$F:$F,MATCH(S{_r},'iCoA Register'!${REG_KEY_COL}:${REG_KEY_COL},0))"
        # an allocated row (Tranche 3, 15.09.2026) carries its code and no date: the date
        # is 7 days after the mycotoxin certificate, which does not exist yet
        f_issue = (f'=IF(OR(A{_r}="",C{_r}="allocated"),"",MAX(E{_r},IF(ISNUMBER(I{_r}),I{_r},0),'
                   f'IFERROR(IF(ISNUMBER({_pkc}),{_pkc},0),0)))')
        latest_d = _date(r["latest"][1]) if r["latest"] else None
        status = r["reg_status"]
        f_rule_rt = f'=IF(ISNUMBER(F{_r}),MAX({_XD(LEGACY_COQ)},F{_r}+7),"— awaiting the retest certificates —")'
        _g = r.get("grading") or {}
        _sup = ("n/a — initial certificate" if r["series"] == "initial release"
                else COQ_LOOKUP("B", r["key"].rpartition("|")[0] + "|I", "— initial certificate not on the register —"))
        # an allocated row carries the owner's planned date as a value, not the formula
        _issue_cell = ((_date(T3_ISSUE) if T3_ISSUE else "") if r["issuable"] == "allocated" else f_issue)
        cells = (f_no, f_code, r["issuable"], _issue_cell,
                 f_rule if r["series"] == "initial release" else
                 ("— the owner's date for all of Tranche 3 (15.09.2026), the 227-М certificates expected by 18.09.2026; provisional —"
                  if r["issuable"] == "allocated" else f_rule_rt),
                 latest_d or ("—" if r["series"] == "initial release" else "— no retest certificate on file —"), (r["latest"][0] if r["latest"] else "—"),
                 REG_LOOKUP("B", r["key"], "—"), REG_LOOKUP("D", r["key"], ""),
                 r["group"], r["series"], r["cu"], r["p"], r["strain"], r["c"], r["cnp"],
                 (f"{r['old'][0]} of {r['old'][1]}" if r.get("old") else "—"), r.get("plan_coq") or "—", r["key"], status,
                 _sup, (_g.get("thc") if _g.get("thc") is not None else "—"), _g.get("doc") or "—",
                 _g.get("grade") or "—", _g.get("window") or "—", _g.get("product_code") or "—",
                 _g.get("spec_code") or "—", _g.get("spec_status") or "—", _g.get("note") or "")
        for _i, v in enumerate(cells, 1):
            c = put(sh, _r, _i, v, F7B if _i in (2, 12) else F7,
                    FILL["green"] if (_i == 20 and str(v).startswith("registered")) or (_i == 3 and v == "yes") else
                    FILL["orange"] if (_i == 20 and str(v).startswith("allocated")) or (_i == 3 and v == "allocated") else
                    FILL["amber"] if (_i == 20 and str(v).startswith("not yet")) or (_i == 3 and v == "no")
                    or (_i in (15, 16) and str(v).startswith("—")) or (_i == 29 and v) or (_i == 28 and "replaces" in str(v)) else None,
                    CEN if _i not in (20, 28, 29) else Alignment(horizontal="left", vertical="center", wrap_text=True))
            if _i in (4, 5, 6, 9):
                c.number_format = "DD.MM.YYYY"
            if _i == 22 and isinstance(v, float):
                c.number_format = "0.00"
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


def add_potency_sheet(wb):
    """The potency grades per strain — nominal, tolerance, specification window — as the
    owner's potency specification of 15.09.2026 prints them (potency_grades.py, from
    Potency_specifications_233.pdf), one row per strain and grade, with the measured
    Total THC results the page rests on. Owner, 15.09.2026: "include this information
    inside the workbook"."""
    import potency_grades as PG
    rows = PG.load()
    sh = wb.create_sheet("Potency Grades", wb.sheetnames.index("CoQ References") + 1)
    hdr = [("Strain", 22), ("Abbr.", 7), ("Status", 10), ("Grade nominal (% THC)", 12), ("Tolerance (±%)", 12),
           ("Window low (%)", 12), ("Window high (%)", 12), ("Grades", 8), ("Measured results (n)", 10),
           ("Measured range (%)", 14), ("Basis", 22), ("Measured Total Δ9-THC results, as printed", 60)]
    for _i, (_t, _w) in enumerate(hdr, 1):
        put(sh, 1, _i, _t, FW, NAVY, CEN)
        sh.column_dimensions[L(_i)].width = _w
    sh.row_dimensions[1].height = 30
    _r = 2
    for r in rows:
        vals = (r["strain"], r["abbr"], r["status"].title(), float(r["nominal"]), float(r["tolerance"]),
                float(r["window_low"]), float(r["window_high"]), int(r["grades_n"]), int(r["results_n"]),
                r["results_range"], r["basis"], r["measured"])
        for _i, v in enumerate(vals, 1):
            c = put(sh, _r, _i, v, F7B if _i == 1 else F7, None,
                    CEN if _i != 12 else Alignment(horizontal="left", vertical="center", wrap_text=True))
            if _i in (4, 5, 6, 7):
                c.number_format = "0.00"
        _r += 1
    note = ("Head of QC, 15.09.2026: the potency grades per strain as the potency specification of 15.09.2026 prints them "
            "(Potency_specifications_233.pdf, Drive id 1NEZSRNPt5GtPvUfpi1dotAG9dkorEAGn; starting nominals QCSP 001 v.03, "
            "results CoQ_Analysis_Master_v25; text layer read by potency_grades.py, one row per strain and grade). The "
            "specification window is nominal ± tolerance as printed; the measured results are the page's own list, in "
            "the page's own order, and 'Basis' says whether every result or the initial result per batch was used. "
            "A lot's grade on its certificate of quality is the window its Total Δ9-THC result falls in.")
    sh.merge_cells(start_row=_r + 1, start_column=1, end_row=_r + 1, end_column=len(hdr))
    put(sh, _r + 1, 1, note, F6I, GREY, Alignment(horizontal="left", vertical="top", wrap_text=True))
    sh.row_dimensions[_r + 1].height = 60
    sh.auto_filter.ref = f"A1:{L(len(hdr))}{_r - 1}"
    sh.freeze_panes = "B2"
    print("potency grades: %d row(s)" % (_r - 2))


def add_references_sheet(wb):
    """The CoQ references table as a tab of the workbook, and its n/t cells as a section
    of Reference (owner, 15.09.2026: "inside the v28 workbook"). One row per certificate
    of quality, one column per determination, the document each cites with its date and
    laboratory, the sampling day and the laboratory's receipt date; every n/t cell red.
    The CoQ code is the one the CoQ Register tab of THIS workbook prints — the table is
    keyed to the register's rows, not to the export's copy of an earlier register — so
    the two tabs cannot disagree."""
    import coq_references as CRF
    codes = {}
    for r in COQ_REGISTER:
        if str(r.get("code", "")).startswith("CoQ-PP_26-"):
            _base, _, _sfx = r["key"].rpartition("|")
            codes.setdefault((T.batch_key(_base), "R" if _sfx.startswith("R") else "I"), r["code"])
            if r.get("cu") and not str(r["cu"]).startswith("—"):
                codes.setdefault((T.batch_key(re.sub(r"[＊*]", "", str(r["cu"]))), "R" if _sfx.startswith("R") else "I"), r["code"])
    rows = CRF.build_rows(T.DESK, os.path.join(HERE, "new_instances.json"), codes)
    sh = wb.create_sheet("CoQ References", wb.sheetnames.index("CoQ Register") + 1)
    n = CRF.fill_sheet(sh, rows)
    nt = CRF.nt_rows(rows)
    CRF.fill_nt_sheet(wb.create_sheet("Not Tested Review"), nt)
    print("CoQ references: %d rows, %d n/t cell(s) painted red (Not Tested Review: %d rows)" % (len(rows), n, len(nt)))
    # The CoQ compilation — the owner's first request (31.08.2026): for every certificate
    # of quality, the template's header fields and, for every determination #1 … #12,
    # the result, the document, its date of issue and its laboratory. One row per
    # certificate on the wide tab, one row per certificate and determination on the
    # long one; both carry this register's code.
    import coq_compilation as CCP
    _wide, _long = CCP.build(T.DESK, codes)
    CCP.fill_wide(wb.create_sheet("CoQ Compilation", wb.sheetnames.index("CoQ References") + 1), _wide)
    CCP.fill_long(wb.create_sheet("CoQ Compilation (long)", wb.sheetnames.index("CoQ Compilation") + 1), _long)
    print("CoQ compilation: %d certificates × %d determinations = %d rows, %d with a document"
          % (len(_wide), len(CCP.DETS), len(_long), sum(1 for r in _long if r["Document"] != "—")))

    # Result supersession — the sweep of 16.09.2026. One filterable tab holding every
    # place a certificate prints a result the record has since replaced, every register
    # block that carries two sublots, and every result on file that no certificate of
    # quality cites. Colour says what the desk can do: grey is settled by a ruling or is
    # information, amber is OI-38, rose is OI-39.
    import result_supersession as RSU
    _sup = RSU.sheet_rows(json.load(open(T.DESK, encoding="utf-8")))
    RSU.fill(wb.create_sheet(RSU.SHEET, wb.sheetnames.index("CoQ Compilation (long)") + 1), _sup)
    print("Result supersession: %d row(s) — %s"
          % (len(_sup), ", ".join("%d %s" % (sum(1 for r in _sup if r["Check"] == k), k)
                                  for k in ("cited as covering", "carried forward",
                                            "two sublots in one block",
                                            "on file, on no certificate"))))


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
    for _i, t in enumerate((f"iCoA and CoQ Issuance Registers — preliminary — built with CoQ Analysis Master v{VER} on {BUILD_DATE}",
                            REG_NOTE, COQ_NOTE + (" FLAGS: " + " | ".join(FLAGS) if FLAGS else ""),
                            "Source: CoQ_Analysis_Master_v" + VER + ".xlsx, sheets iCoA Register and Batch Dates; "
                            "dates from the Head of QC's list of 04.09.2026; the issuance plan of 31.08.2026 for the plan references."), 1):
        c = rm.cell(_i, 1, t)
        c.font = Font(name="Calibri", size=9, bold=(_i == 1))
        c.alignment = Alignment(vertical="top", wrap_text=True)
    rm.row_dimensions[2].height = 150
    rm.row_dimensions[3].height = 190
    apply_strain_rulings(w)
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
    "Batch Coverage": "One row per lot: ✓/✗/○ for each of the 12 parameters, the missing list, and two pairs of document columns — the certificates the tracker actually cites with their laboratories, and separately the documents on file from the 09.09.2026 pass that the desk has not recorded. Both pairs are derived here from the tracker rather than carried forward, which is what let them drift apart. ○ counts as missing: nothing can be cited until the desk records the document. A grey ✓ is covered by the in-house iCoA.",
    "Mikro CoQ Parameter": "The owner's microbiology sheet, rebuilt from the tracker: the #7–#12 spans per lot in the owner's layout.",
    "Credit Audit": "Certificates credited on the owner's tracker that the desk holds no value from, with the reason.",
    "Credit Corrections": "The two corrections applied to the owner's credits (the Farmahem pair, CNP identification B), one row each; nothing written back to the owner's workbook.",
    "Work Order": "What a person must do next: certificates to ingest, values to read on the page, lots to record.",
    "CoQ References": "One row per certificate of quality, one column per determination #1 to #12: the document the CoQ cites for it — code, date of issue, laboratory abbreviation (CNP, IJZ, IJZ-MB, FHM-K, FHM-M, DFL, PP) — with the sampling day (the campaign's for a reissue, the packaging day for a release certificate) and the date each cited external certificate says the laboratory admitted the sample (receipt_dates.py). `*` an internal CoA issued at the certificate's issue; `also X` a later document for the same determination; `(initial)` a reissue's row carried from the initial certificate; `DAB` the cited CNP certificate used the DAB monograph; `u/r` upon request; `n/t` not tested — every n/t cell is red for the owner's check and listed in the Not Tested Review section of Reference. The CoQ code is the CoQ Register's. Built by coq_references.py.",
    "CoQ Compilation": "The owner's first request (31.08.2026): one row per certificate of quality — release and reissue, every batch — with the template's header fields (code, date of issue, the certificate it supersedes, batch, P lot, strain, harvest and packaging, the internal certificate, Total THC and its certificate, grade, potency window, product and specification codes, the specification's bands) and, for every determination #1 to #12 with its sub-determinations (23), four columns: the result the certificate prints, the document it rests on, that document's date of issue and its laboratory. A determination the certificate prints no result for shows why (not tested, upon request, to be performed in house, awaiting a certificate). The code is the CoQ Register's.",
    "CoQ Compilation (long)": "The same compilation one row per certificate of quality and determination (172 × 23), with the method, the acceptance criterion, the laboratory's receipt date of the sample, the desk's status for the row, the route where nothing is on file yet, and the other documents on file that also carry the result.",
    "Result Supersession": "The sweep of 16.09.2026 (result_supersession.py), one row per finding, filterable on CHECK. \u0022cited as covering\u0022 \u2014 a RELEASE certificate citing the release result while a later retest is on file, which is the owner\u0027s ruling of 10.09.2026 working as written and is not a defect. \u0022carried forward\u0022 \u2014 a reissue carrying a determination forward from the initial testing because its campaign did not retest it, while a later result for the same lot is on file: the rows OI-38 decides. \u0022cited after the issue date\u0022 \u2014 a certificate resting on a document issued AFTER it, which is a defect and not a question. \u0022two sublots in one block\u0022 \u2014 two certificates of the same testing on the same day reporting different results in one register block, where the certificate of quality prints one of the pair and does not say which sublot it certifies (OI-39). \u0022on file, on no certificate\u0022 \u2014 a result in the release register that no certificate of quality for that lot cites, listed so the owner can see the whole of what a ruling would move. A stability timepoint is excluded throughout: it measures the lot ageing and no certificate of quality prints it. The tab is read with the coverage table in tracker/RESULT_SUPERSESSION_2026-09-16.md: no lot on file carries a second heavy-metal certificate, so the sweep is blind on #11 and its silence there is a gap in the record, not a clean result.",
    "Potency Grades": "The potency grades per strain — grade nominal, tolerance and specification window (nominal ± tolerance) — as the Head of QC's potency specification of 15.09.2026 prints them (Potency_specifications_233.pdf; starting nominals QCSP 001 v.03, results CoQ_Analysis_Master_v25 — confirmed grade by grade against the owner's Potency_specifications_25.pdf of 17.09.2026, which corrected Amnesia Core Cut's tolerance to ± 1.20 and added Wedding Cake at 26.00 ± 2.60), one row per strain and grade, with the measured Total Δ9-THC results each page rests on. Built from potency_grades_2026-09-15.csv by potency_grades.py.",
    "Not Tested Review": "Every n/t cell of the CoQ References tab — certificate, batch, series, determination, the cell as printed — for the owner's check (owner, 15.09.2026: legitimate only where nothing was ever tested — aflatoxin B1 and ochratoxin A beside an IJZ total-aflatoxin result, and the upon-request organisms and pesticide panel).",
    "Open Items": "The standing register of what the desk cannot decide: every finding raised and left to the owner, with what was found, what the desk did with it, the decision being asked for, and the evidence behind it. STATE is open (waiting, nothing printed), marked (the certificate prints the field bracketed in red and unticked) or ruled (kept for the record with the ruling). Built from open_items.py, which also writes OPEN_ITEMS.md.",
    "iCoA Issuance": "One row per P lot and series (initial release, retest): what its iCoA carries, the CNP references, the cannabinoid-assay eCoA that covers identification C, the codes and planned dates looked up on the registers.",
    "Batch Dates": "The Head of QC's harvest and packaging dates per batch (04.09.2026), as dates; the registers look their packaging dates up here.",
    "iCoA Register": "The standing register of internal certificates of analysis, one row per testing round (the owner's ruling of "
                     "10.09.2026: every internal certificate that exists or ever will). It renders icoa_register.py — the series the "
                     "certificates print from — so the number and the code are literals taken from it, never computed from a row's "
                     "position; a lot the series does not carry follows below, unnumbered and saying why.",
    "CoQ Register": "The preliminary CoQ issuance register: CoQ-PP_26-nnn in the order of issue — release and reissue — the latest eCoA each CoQ cites, its iCoA, the adherence flags under the table; since v29 the initial certificate a reissue supersedes (by the register's own code) and the potency grading of the certificate's Total THC result: grade nominal ± tolerance, window, product code and specification document code from the potency specification of 15.09.2026 (Potency Grades tab).",
    "Parameters": "The 21 determinations with method, global acceptance criterion, source and tracker columns.",
    "Summary Dashboard": "Counts recomputed from Batch Coverage: lots, documents, complete / partial / incomplete, missing-parameter frequency.",
    "Reference": "Everything that is neither a primary view nor a formula source, on one sheet (owner, 14.09.2026: six tabs, "
                 "not sixteen), each section under its own title in capitals and separated by a blank gutter; the sections "
                 "are listed under '(folded in)' below. Nothing was deleted — none of these is read by a formula, so they could "
                 "be moved without touching a lookup, but they are the audit trail and taking that out of a controlled record "
                 "is the one direction that cannot be undone from inside the workbook.",
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
    # The two registers print the strain the series module carries, which is the
    # certificate register's own spelling — "Cup Junky", "GorillaGlue". They were
    # never on this list, so the one sheet that printed the ruled spelling was the
    # iCoA Issuance sheet, and when that was folded away on 14.09.2026 the ruling
    # of 07.09.2026 left the workbook with it.
    targets = [("Batch Coverage", 3), ("Delivery T1\u2013T3", 4)]
    for reg in ("iCoA Register", "CoQ Register"):
        if reg in wb.sheetnames:
            hdr = [str(c.value or "").strip() for c in wb[reg][1]]
            if "Strain" in hdr:
                targets.append((reg, hdr.index("Strain") + 1))
    for sheet, col in targets:
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
    # The sheet list as the workbook will READ once the fold has run, not as it
    # stands at this moment. This Read Me is written before fold_reference_sheet()
    # — it has to be, because it is itself one of the sheets folded in — so
    # enumerating wb.sheetnames here would describe sixteen tabs that are about to
    # become seven, and the verifier's "sheet not described" check would fail on
    # the one sheet this list forgot: Reference.
    _folding = [n for n in FOLD_INTO_REFERENCE if n in wb.sheetnames]
    _final = [n for n in wb.sheetnames if n not in _folding and n != "iCoA Issuance"]
    if _folding:
        _final.append("Reference")
    for name in _final:
        about = SHEET_ABOUT.get(name) or (SHEET_ABOUT["CoQ Parameter Tracker"] if name.startswith("CoQ Parameter Tracker") else "")
        line(name, about)
    if _folding:
        line("(folded in)", "The iCoA Issuance sheet is gone: every column it carried is on the iCoA Register (its CoQ plan "
                            "reference on the CoQ Register), which was always the same one row per batch and round; only its own "
                            "row number is not carried. These are now sections of Reference rather than tabs — "
                            + ", ".join(_folding) + ".")
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
    line("15.09.2026 · retest sampling and the reissued CoQ", "The retest campaigns were sampled in three campaigns (sampling_dates.py): Tranche 1 on 21–24.07.2026 (Tuesday to Friday of the week 25.07 falls in, 6/5/5/5 by certificate number, Farmahem receipt 27/29.07), Tranche 2 on 12–14.08.2026 (11/11/10, receipt 17.08), Tranche 3 on 19–21.08.2026 (10/10/10, receipt 24.08). The internal certificate for identification A, B and foreign matter is tested start = end on the batch's sampling day and every campaign's certificates issue on one day, three days after its last sampling day: 27.07, 17.08 and 24.08.2026. Identification A, B and foreign matter are performed on every batch and every CoQ cites the internal certificate for them, so a round the batch list holds no packaging date for is numbered with its testing date not stated. The reissued CoQ carries the retest results and, for everything not retested, the initial certificate's result and document; it is dated by the same rule as the release CoQ (7 days after the last certificate it cites, never before its iCoA) and numbered in date order with the release series once the assay, the mycotoxins and the iCoA exist. A CNP certificate up to ППК26069 (11.05.2026) reports the cannabinoid assay and loss on drying by the DAB monograph; the CoQ method reference says so where it cites one.")
    line("05.09.2026 · retest", "The QP's retest campaign, sampled by tranche from July 2026: identification A, B and foreign matter in-house on every bag of the representative sample (one iCoA), cannabinoids with identification C and mycotoxins at Farmahem, microbiology at IJZ-MB; the reissued CoQ carries those results and the initial certificates for the rest. A retest certificate never certifies the initial CoQ; the IJZ-MB delivery of 25/26.08.2026 is campaign sampling for every lot.")
    line("05.09.2026 · missing", "A production lot whose initial certificate for a determination is not on file keeps its planned CoQ and number: the initial testing exists at CNP (microbiology: IJZ) and the certificate is to be located (Work Order).")
    line("09.09.2026 · reconciliation", "The owner's own pass over the 387 certificates in eCoA_DATABASE (CoQ_Analysis_Master_v20.xlsx) is taken in as the base for everything after it. cell_resolution.py refuses more than it accepts when filling a cell from it: no citable document code, an unissued certificate, or an unlabelled list of analyte values are each left blank rather than guessed.")
    line("10.09.2026 · release vs retest", "\"The first value of a parameter obtained is counted as initial quality control testing; every other point of testing for any parameter from a batch is a retest.\" A result's round is its own position in its own parameter's history, never the certificate series it happens to sit in — one campaign can certify cannabinoids one day, microbiology another and metals a third, and that is still one testing period, not several (testing_series.py).")
    line("10.09.2026 · issuance dates", "Specification SOP approved 01.06.2026; nothing it governs is dated earlier. Internal CoA: tested and issued the first day of packaging (release) or the round's sampling date (retest), or 03.06.2026 where that day is before the SOP. Certificate of quality: 5–10 days after the last external certificate it cites (LAG_DAYS = 7) and never before its own internal CoA; anything that would land before the SOP issues on the blanket date 06.06.2026 — a Saturday, kept as given and flagged, because the owner's date outranks the desk's own working-day convention (issuance_schedule.py).")
    line("10.09.2026 · internal CoA scope", "One internal certificate per testing round, covering identification A, identification B and foreign matter ALWAYS — performed in house at packaging or sampling whatever an external laboratory also reports — plus any determination whose only result that round is in-house. In-house results are never referenced on a certificate of quality; they sit behind the internal certificate, which the CoQ cites. The register is standing: every internal certificate that exists or ever will, not only the ones a drafted lot needs (icoa_register.py).")
    line("10.09.2026 · untested analytes", "An analyte the laboratory never tested does not enter the certificate of quality at all — printed, not left blank, not marked ND. Where the initial mycotoxin testing ran only the total-aflatoxins method, Aflatoxin B₁ and Ochratoxin A are absent from that certificate; the retest date, once all three are tested, shows all three.")
    line("10.09.2026 · conformity wording", "'Conforms | Одговара', in the same ENG/MK formatting convention as the rest of the certificate's bilingual text; every conformity result is printed bilingually, with no other Macedonian rendering of 'conforms' surviving on a certificate (result_vocabulary.py).")
    line("11.09.2026 · packaging date", "A batch packaged over more than one day is tested — and its internal certificate dated — on the FIRST day of that window, not the day packaging completed.")
    r += 1
    head("VERSION HISTORY")
    line("v7", "The two-row block tracker: one lot per block, certificates stacked in date order, sub-determinations in their own columns, acceptance criteria in row 3 and enforced, out-of-specification results in red and named in STATUS.")
    line("v9", "Verified and slimmed to live in Drive: every decision-bearing value checked against the filed page (review/V8_TRUTH_CHECK_2026-09-02.md); three sheets of v8 (a flat results register, a flat tracker, a document index) were retired to the repository.")
    line("v10", "The 30 IJZ-MB certificates of 31.08 and 01.09.2026 as testing instances credited to #9; the iCoA rule; the Head of QC's harvest and packaging dates (Batch Dates); one iCoA per P lot; the iCoA Issuance sheet.")
    line("v11", "The iCoA Register and the CoQ Register (formula-driven); the ruling of 05.09.2026 on the legacy and post-SOP series; the retest campaign kept off the initial CoQs; the owner's edits to the Drive copies (row 4, result sizes, lot borders); one coverage row per lot.")
    line("v12", "The Delivery T1–T3 sheet: the 78 cultivation batches delivered in the three tranches of 31.07, 14.08 and 28.08.2026, each against its row on Batch Coverage.")
    line("v13", "The strain ruling (Cap Junky, Head of QC 07.09.2026) and the ImB Register: the customer's own certificate register, scanned 04.09.2026, 43 entries against their desk lots.")
    line("v20", "The owner's own workbook, built outside this pipeline and vendored in as the base for everything after it — not a version this desk produced.")
    line("v21", "The owner's v20 pass reconciled in: 387 certificates, all 600 determinations of Tranches 1 and 2 resolved through cell_resolution.py; 69 cells filled, 0 non-blank cells overwritten.")
    line("v22", "The rulings of 10.09.2026 written into the workbook's own live Excel formulas: release-versus-retest by position, the issuance dates, the internal-CoA register.")
    line("v23", "One controlled spelling per result (result_vocabulary.py): 175 non-canonical not-detected spellings to 0, the 'Одговара'/'Не одговара' confusion that read a laboratory's non-conformity as a pass (FB032601) corrected, untested analytes removed from certificates entirely, every conformity result made bilingual, the A4 page fit measured with the fonts it prints in and repaired (5 of 22 losing content → 0).")
    line("v24", "The internal-CoA number and the internal-CoA register unified on one definition: icoa_register.py is the standing series (a certificate a person can look up by code), and both the number and the row set on the iCoA Register sheet are taken from it rather than computed from a row's position — 95 of 95 series codes now on the sheet, up from 60.")
    line("v25", "The Read Me sheet's own version history and rulings-in-force brought forward from v11 / 05.09.2026 to this build — nine versions and six days of rulings that were built and verified but never written down here. Two findings promoted from doc prose that had never reached the standing register: OI-30 (the Loss on Drying method line is uniform across every lot and the desk holds no per-certificate method text to check it against) and OI-31 (six batches silently filed under one strain name, 'Gorilla Glue', where the delivery sheet keeps 'GG4' apart — never ruled, never tracked).")
    line("v42", "The decisions of 17.09.2026, on every certificate of quality. LOSS ON DRYING, GG1024: the 76.07 % of ППК25008 ruled a typo and set to 7.8 % — a pinpoint edit of both GG1024 certificates and of the 09.09 resolution pass they print from; the out-of-specification mark is gone. NO SIGNATURES: the certificates carry no signature scan; each box keeps its line for signing by hand. THE RETEST CERTIFICATE CITES THE RETEST INTERNAL CERTIFICATE for identification A, identification B and foreign matter (apply_retest_icoa.py: 142 cells on 51 reissues, 8 master-assigned CNP citations kept); the internal certificates rebuilt from the citations, 154 documents. EVERY DETERMINATION CITES THE LABORATORY THAT MADE IT (apply_lab_attribution.py, five rules): the internal certificate was cited under one code with two dates and credited with parameters 1 to 11 on GG1024 where the Institute had determined 9 to 12 and CNP 8 — 19 rows re-pointed to 166/0274/25 and 748/2025, 7 rows with no certificate behind them now not tested, 4 in-house CoA numbers replaced by the internal certificate, 30 'PP CoA #nnn / ППКnnnnn' citations reduced to the CNP certificate with its own date; 54 rows on eight certificates keep the internal certificate beyond 1, 2 and 7 under the ruling of 10.09.2026 (OI-49, decision wanted). POTENCY GRADES from the owner's Potency_specifications_25.pdf (17.09.2026), set grade by grade against potency_grades_2026-09-15.csv: 22 of 24 strains identical; Amnesia Core Cut's tolerance corrected to ± 1.20 (10.80 – 13.19), Wedding Cake added at 26.00 ± 2.60 (23.40 – 28.59) as the first specification of the new series, QCSP_001_WED-I_v.01, superseding the four issued WED documents (OI-50: dominance to be determined); every certificate re-graded through potency_grading, two moved (CoQ-PP_26-106, CoQ-PP_26-165), none outside its strain's windows; the status beside 149 specification codes now records the issued document each replaces. Checked the same day: potency of every certificate against the master (158 agree, 13 no potency, 0 conflicts); certificate codes and supersedes lines against the CoQ Register (0 mismatches); loss on drying cited only to laboratories that determined it. Two lists for the Head of QC (retest_list.py): the 83 retest certificates and the 83 release certificates they supersede. The engagement report (engagement_report.py) reads the repository's own record. The registers' rows and every laboratory result are otherwise v41's.")
    line("v26", "Seven tabs, not sixteen (owner, 14.09.2026). The iCoA Issuance sheet is gone — one row per batch and round, which is what the iCoA Register is, so its eleven columns are register columns and nothing looked it up by formula. Ten sheets are sections of one Reference sheet, each section's row range recorded as a defined name so a reader never guesses where it ends. verify_prose.py — what the sheets say about themselves — had never run against a shipping workbook (its default was v11, and it was not in CI); against v25 it found eleven false sentences, three the workbook's (a note and the register Status strings naming 27.05.2026 and 15.05.2026 for a legacy series that issues on 06.06 and 03.06; an uncredited in-house reference printed without its 'on file, not credited'), eight the checker's own. All fixed and the check is in CI. OI-32: thirty Tranche 3 Farmahem 227-K/26 potency retests found on file and none in the record — twenty-five prepared and not written, five held on batch identity.")
    line("v34", "The IJZ-MB campaign microbiology written into the release register (intake_IJZMB_2026-09-16), and two checks that were not checking. A cross-version sweep of every master workbook on disk (v3 … v33) found nothing lost along the way: across twenty builds the only substantive changes to microbiology, mycotoxins and heavy metals are the four page-read corrections of v32 and the n.r.-to-not-reported ruling — everything else was the controlled vocabulary rewriting notation. The inconsistency was elsewhere, and it was real: the thirty IJZ-MB certificates of the campaign sampling of 25/26.08.2026 (issued 31.08 and 01.09.2026) had been testing instances on the tracker since 04.09.2026 and were never rows of the RELEASE REGISTER, which is the one source the certificates of quality are compiled from — so 24 certificates printed microbiology a newer certificate for the same lot contradicted, twelve of them reissues, P050012 printing TAMC 2.1 × 10⁴ where the campaign certificate reads < 10 (OI-34, now closed). 29 of the 30 are written into the register through the two-read gate; four value disagreements, every one the bile-tolerant gram-negative line where one read stopped at < 10² and the other carried < 10² и > 10, were settled by a third read of the page on 16.09.2026 and the fuller read was right all four times (OI-36's class). One is held back: 548/1079/26 prints the strain Sleepy Joe and a handwritten P060192 while its typed serial reads PO50192, so which lot it belongs to is the Head of QC's to settle (OI-37) and a result on the wrong lot is worse than a missing one. Two checks were repaired: verify_workbook's check 13, which claimed to compare the owner's microbiology sheet with the tracker, had the body `for cu, p in LOTS: pass` and was guarded on a sheet name the fold of 14.09.2026 removed, so it had been skipped entirely since v26 — it now compares every value and reports the count; and OI-13 stated that the expanded microbiology panel had never been run when 31 certificates on file report P. aeruginosa and S. aureus, all absent, which is corrected with the question of what #9.6 and #9.7 should print put to the owner. The registers, the potency and the compilation are v33's.")
    line("v35", "The supersession sweep, generalised to every determination (result_supersession.py, and the Result Supersession tab). The Head of QC reports that a second desk flags heavy metals, microbiology and mycotoxins. The microbiology defect v34 repaired was found by asking whether a certificate prints a result that a LATER certificate for the SAME lot — already on file the day it issues — contradicts; that question was asked of microbiology alone, so it is now asked of all seventeen determinations the release register carries, over 172 certificates and 93 register blocks. The sweep prints its COVERAGE beside every zero, because a zero over nothing is not a result: **no lot on file carries a second heavy-metal certificate at all** (#11.1 to #11.4 — 45 documents, 0 lots with two), so the sweep is blind there and says nothing about metals; every certificate that prints Pb, Cd, As or Hg rests on one document, because the retest campaigns never re-ran them. Aflatoxin B1, ochratoxin A and the pesticide panel were comparable on one lot each. Where the comparison was genuinely available and returned nothing it is a real zero: total aflatoxins over 30 lots, Total CBN over 12, Salmonella and E. coli over 14 each. Of 89 comparisons, 39 contradict: 8 are release certificates citing the release result while a later retest sits on file, which is the ruling of 10.09.2026 working as written and is not a defect; 31 are reissues carrying a determination forward from the initial testing because their campaign did not retest it, which widens OI-38 from twelve microbiology reissues to fourteen certificates — the two new ones are loss on drying (CoQ-PP_26-093 on P050022, CoQ-PP_26-150 on J31112501). A stability timepoint is excluded throughout: it measures the lot ageing, it is not release or retest testing, and counting it raises 30 findings on the two Grape Pie lots alone that are not findings. Two further checks come with it. **Two register blocks carry two sublots each** (OI-39): J31122501 holds the 07.04.2026 microbiology of the hand-trimmed and the trimmed flower (TAMC 850 against 1900), the 09.04.2026 Farmahem pair 100-2-К/26 at 19.84 % against 100-3-К/26 at 21.84 %, and the 23.04.2026 IJZ pair 1628/2026 against 1625/2026; JD112501 holds ППК26063 at 19.64 % against ППК26065 at 13.93 %. The certificate of quality prints one of each pair and does not say which sublot it certifies. And 128 results are on file that no certificate of quality cites — 70 the campaign microbiology of OI-38, 32 in-house documents with no document number, 26 laboratory certificates on five lots. Also in v35, the answer to the parallel desk's audit of the 127 rendered certificates (tracker/HANDOVER_RESPONSE_2026-09-16.md), which reached the Head of QC as HANDOVER_to_ClaudeCode.md. Of its seven findings, four are REFUTED against this master: no certificate's grade disagrees with its own specification code (0 of 172); no register code sits on two lots; no external laboratory is credited for a determination with no result (0 of 172); and every printed Total THC is inside its own strain-and-grade window (120 compared against the Potency Grades ladder, 0 outside) — the four banner potencies the audit flags each carry the PREVIOUS lot's assay, a row-alignment slip on the document side. Three are CONFIRMED. The loss-on-drying 76.07 % on GG1024 is real and both its certificates already carry OUT OF SPECIFICATION (OI-06, OI-35). The Farmahem analysis tag IS part of the code and it is Macedonian — the pages of 051-1 and 031-2 print Извештај број: 051-1-ГС/26 and 031-2-ГС/26, губитоци при сушење, so GS is a transliteration and LoD an English abbreviation; document_codes.py now gives one spelling per document code the way result_vocabulary.py gives one per result, and it also takes a reader's OCR note out of the code field (2156/2025). And the in-house determinations #1, #2 and #7 print nothing on 82 certificates over 44 lots — confirmed as a document defect, refuted as a builder defect, because all 172 cite an internal certificate and what is missing is the RESULT (OI-41). Two questions the audit raised go to the owner rather than being settled here: the six PP CoA #nnn / ППКnnnnn composites, where the bare ППК row on the same lot is empty and earlier (OI-40), and the two sublots in one block (OI-39). One defect the sweep's fourth check found and v35 repairs: THIRTEEN release certificates were citing a microbiology certificate of 31.08 or 01.09.2026 while dated 06.06, 07.07 or 13.07.2026 — a controlled document resting on one that did not yet exist. The cause was v34's intake meeting a gap in build_coq_schedule: testing_series.rounds() has held since v34 that every certificate of the IJZ-MB delivery is a retest document (the owner's ruling of 10.09.2026), but the schedule's release branch did not, so wherever the delivery was the only microbiology a lot had, it stood behind that lot's release result. The release branch now excludes a retest-only document, those thirteen certificates print nothing for #9.1-#9.5, and where the campaign result should appear instead is OI-38 — which now records that for those thirteen lots a ruling of CARRY THE INITIAL leaves the lot with no microbiology on any certificate at all. Otherwise nothing in the tracker, the registers, the certificates or the compilation changed: v35 adds the sweep, the answer, the document-code spellings and that one repair.")
    line("v37", "The April-2026 release panel taken into the register, the starred spellings joined, and two read-backs that were reading nothing. EIGHTEEN CERTIFICATES OF THE INSTITUTE OF PUBLIC HEALTH on the nine lots sampled 21.04.2026 — the microbiology 304/0548/26 … 312/0556/26 of 28.04.2026 and the contaminants 2357/2026 … 2365/2026 of 29/30.04.2026 — had been on this tracker and (seventeen of them) in the two-read corpus since 04.09.2026 and were rows of no release register, which is the one source the certificates are compiled from: so eight release certificates printed \u0022not tested — no certificate covers it\u0022 for microbiology, mycotoxins and heavy metals with the documents on file five weeks before them. intake_IJZ0426_2026-09-16 writes them through the same two-read gate as the earlier intakes: 17 rows into existing blocks and one row the owner had opened for 305/0549/26 and left empty, filled in place. Four certificates disagreed between their reads and each was settled by a third read of the page — three on the bile-tolerant gram-negative line, every one a read stopping at one bound where the page carries the range (OI-36 with three more instances), and one on the NUMBER of pesticide lines, 29 against 28, every line \u043d.\u0434. on both. 310/0554/26, which the runner never read, took the RAGflow OCR and the Head of QC\u0027s own transcription as its two reads and a third from the scan. THE STARRED SPELLINGS ARE JOINED, as the ruling of 16.09.2026 implies: identity_decisions.tsv now carries a batch_alias row for JD112501*, GG012601*, JD012601*, SCR012601* and FB012602*, and batch_key applies the rulings after normalising — so GG012601* and GG012601 key alike, iCoA-PP_26-087, -088 and -090 take their testing dates from the packaging, and the two Tranche 3 release certificates that stood at \u0022— at issue —\u0022 over a glyph are numbered. The rule itself is unchanged: a star no person has ruled on still keeps the mark. The owner\u0027s tracker row JD112501\u272a, which the ruling says is not a lot, is folded into P060212 and its documents stay there as testing instances marked experimental. AND TWO READ-BACKS THAT WERE READING NOTHING: the certificate\u0027s title is now written by the compiler rather than the bulk driver, so the desk\u0027s own Print and Save carry it too, and the Section 01 read-back queried .l and .v, classes the master has never had — it reads .lk-lbl and .lk-val now and the build reports any document whose Section 01 does not print its own P lot, a potency and a specification reference. OI-28 ruled; OI-42 and OI-43 opened for the 44 laboratory scans and 28 in-house scans on Drive that no desk record holds.")
    line("v40", "The reissue carries the release round's result, on every determination the retest did not run — 142 of them, over 66 lots. The ruling of 15.09.2026 is unconditional: \u0022all of the parameter results that were not tested will be taken from the initial quality control testing.\u0022 The desk honoured it only for determinations outside four named classes. The three the Purely Plant laboratory performs (#1 Identification A, #2 Identification B, #7 Foreign matter), the cannabinoids, the mycotoxins and the two microbiological determinations tested on request each short-circuited the carry and printed an empty red cell — on a certificate whose own release round had certified that parameter months earlier. The cause was a layering one and is worth recording: build_coq_schedule cannot carry what it does not yet hold, because #1, #2 and #7 take their value in the EXPORT, from the owner's 09.09 pass and from the company's own certificates of analysis, long after the schedule is written. So the carry now runs twice — once in the schedule for everything it can see, and once in the export, at the only layer that holds both rounds. What is carried is the release row WHOLE: the result, the document that certifies it, that document's date of issue and its laboratory. For #1, #2 and #7 that document is the RELEASE round's internal certificate of analysis, its code and its date — never the reissue campaign's own, which would assert a retest nobody performed (the defect of 16.09.2026). The reissue's pending status is kept behind the carry note, so a sheet that carries a release result while a re-analysis is outstanding states both facts. Measured on the 73 compiled drafts: the red dash placeholder falls from 357 result cells to 226, and the documents that carry none at all rise from 18 to 49 of 73; on the compilation, the reissue rows blank although their own release certificate holds a result fall from 179 over 66 lots to ZERO. Also in v41, a result cell is no longer a truncated sentence: coq_compilation printed the first 60 characters of a status where no result existed, so 393 rows read \u0022carried from the initial testing (the batch's initial CoQ (n\u0022 — the cell now says what the reissue did and then, in the release round's own controlled word, what the release round found, with the certificate number kept in the Status column. What remains is documents, not logic: every one of the 226 is a determination for which NO laboratory certificate exists on either round — 100 microbiology, 80 heavy metals, 23 in-house identity and foreign matter, 9 mycotoxins, 8 loss on drying, 6 pesticides — which is OI-42 and OI-43, and needs scans, not code.")
    line("v36", "The starred-sample ruling, and a title that named another lot. OWNER'S RULING, 16.09.2026, on the asterisk some cultivation batches carry: \u0022the asterisk is probably some experiment and is generally not the result that will go for the batch release official documentation. If both THC results are assigned with the same P number production batch, that means it is the same batch, but two samples have been sent for the parameter. You will NOT ignore the value and data with the asterisk — you will include it in calculation statistics and all — but in the CoQ you will take the other value and corresponding certificate.\u0022 So a starred sample is a second SAMPLE of one packaged lot, not a second lot. Read on the pages the same day: \u041F\u041F\u041A26063 and \u041F\u041F\u041A26065 are both P060212, the same sample description, the same delivery of 21.04.2026, the same DAB method and the same 12 g — the batch number is the only difference, one reading JD112501 and the other JD112501*. The owner's 09.09 pass gives JD112501/P060212 a full panel and cites \u041F\u041F\u041A26063; \u041F\u041F\u041A26065 is cited nowhere in it. testing_series.EXPERIMENTAL now holds the starred certificates and build_coq_schedule drops them before the release/reissue split, so they source no certificate of quality while their results stand everywhere else. OI-12 is ruled and OI-39 keeps only its J31122501 half, where the laboratories' own pages name two PRODUCTS (\u0420\u0430\u0447\u043D\u043E \u0442\u0440\u0438\u043C\u0438\u0440\u0430\u043D \u0446\u0432\u0435\u0442 against \u0422\u0440\u0438\u043C\u0438\u0440\u0430\u043D \u0446\u0432\u0435\u0442) and no asterisk appears. AND A DEFECT ON EVERY DOCUMENT THE DESK HAS EVER COMPILED: the master template carries a literal <title> from the lot it was authored on and fillCoq never replaced it, so all 73 drafts and all four tranche PDFs went out titled \u0022CoQ-PP-2026-0005 — Amsterdam Amnesia (AA) — Grade I — Batch P060052\u0022 — another lot's code, strain, grade and batch in the browser tab and the PDF metadata. Nothing on the desk was reading the title, which is why it survived every verification pass. build_coq_drafts now writes each document's own title from its register code, strain, grade and lot, and reads it back off the compiled page beside the header band, so a document that does not name itself is reported at build time.")
    line("v33", "The CoQ compilation inside the workbook (owner, 15.09.2026, recalling the first request of 31.08.2026: \"for all certificates of quality, for all batches, for all initial and retest certificates … a table containing all information that is needed for the certificate of quality template, but most importantly, from parameter 1 to 12, the document codes and date of issuing of the certificate of analysis from external laboratories … and the analysis results for each of those parameters … for every certificate of quality document code individually\"): two tabs built by coq_compilation.py from the export the certificates are compiled from, with the CoQ Register's code. CoQ Compilation — one row per certificate of quality (172: 89 release, 83 reissue): the template's header fields, then for every determination #1 to #12 with its sub-determinations (23) the result the certificate prints, the document it rests on, that document's date of issue and its laboratory; a determination with no printed result says why. CoQ Compilation (long) — the same, one row per certificate and determination (3,956 rows), with the method, the acceptance criterion, the laboratory's receipt date, the status, the route and the other documents on file. The same tables stand alone as tracker/CoQ_compilation_v33.xlsx and the two CSVs. Nothing else changed: registers, tracker, certificates and references are v32's.")
    line("v32", "Truth check of 15.09.2026 (tracker/truth_check_2026-09-15.py; report tracker/TRUTH_CHECK_2026-09-15.md): every parameter result and every cited eCoA code, date and laboratory compared, by an independent code path, from the primary records — the release register with the intakes applied, the intake transcriptions and their second reads, the two-read corpus, the 09.09 pass — forward to the tracker, the export, the references table, the CoQ Register and every compiled draft. Two defects on the tracker corrected in this build. (1) The owner's v8 tracker marks Aflatoxin B1 and Ochratoxin A 'n.r.' on the IJZ release certificates, and the desk read that as ND under the ND ruling of 10.09.2026; the page of 752/2025, read 15.09.2026, prints one mycotoxin line only (total aflatoxins < 2 µg/kg) and the release register says 'not tested' — the laboratory printed no line, so the mark is the owner's, not a result, and the cell now reads 'not reported' (the boundary ruled on 11.09.2026: an analyte absent from the panel is not a result; the compiled certificates already omit the line). Where the desk holds a result for the determination — the Farmahem -М- certificates' total aflatoxins, ND on the register — the ruling stands and the cell reads ND. (2) Four microbiology cells whose v8 value the page contradicts, each corrected from a third read of the page (tracker/value_corrections_2026-09-15.json): 5/0008/26 TAMC 1 × 10² CFU/g (v8 and the corpus read A said < 1 × 10²; the register and read B were right), 9/0012/26 bile-tolerant < 10 (v8 said 10), 471/0862/25 TYMC < 10 (v8 said 10), 304/0548/26 bile-tolerant < 10² and > 10 (v8 stopped at < 10²). The desk's document index no longer lists a register column marked 'not tested' as reported. Two open items record what the check found and did not change: the tracker does not carry the 17 documents of the 09.09 pass that eleven certificates print from (OI-35), and four two-read corpus records passed the gate with their reads disagreeing on a comparator (OI-36). The registers, the certificates and the references are v31's.")
    line("v31", "Tranche 3 codes allocated (owner, 15.09.2026, evening: every Tranche 3 retest parameter is tested at Farmahem and its certificates all issue on one date — \"so practically you can even now allocate the certificates of quality document codes for tranche three batches\"; the analyses complete within ten days, likely by Friday 18.09.2026, and all Tranche 3 certificates issue on one day, \"let's say Monday next week\"): the 28 Tranche 3 reissues whose release certificate is numbered take CoQ-PP_26-134 … 161 after the last Tranche 2 reissue, in the order the series gives them, with Issuable reading 'allocated' and the planned date the owner's — 21.09.2026, provisional until the 227-М mycotoxin certificates exist — the one code computed in advance, by the owner's ruling; the compiled certificates print the allocated code and are not drafted until the mycotoxin results exist. The two Tranche 3 lots whose release certificate the register withholds (GG012601＊, JD012601＊: no internal certificate, OI-28) wait with it. One Tranche 3 lot had no reissue row at all — BSS1024_01/1 (P050122), spelled BSS1024_01 on the 31.08 list — because the schedule's placeholder carried no P lot; a placeholder now takes its register block's packaged lot. And the retest programme is the QP's, not universal (owner, 15.09.2026): only the batches of Tranches 1, 2 and 3 are for sale, so only they were retested and get a reissue; the six batches outside every tranche with a predicted reissue on v30 (JD022601/P060482, FB032601/P060452, GG032601/P060462, P160012, P160022, P160032) carry their release certificate and no retest row, and after the numbered and the allocated rows the CoQ Register lists the batches the tranches do not cover — under production, under testing, or on no tranche list — lot by lot, none of which can take a code before its external results and packaging exist. The registers' rows, the tracker and every laboratory result are otherwise v30's.")
    line("v30", "The Tranche 2 potency certificates taken in (intake_220K_2026-09-15): the 32 Farmahem 220-1-К/26 … 220-32-К/26 cannabinoid reports — received 17.08.2026, analysed 24/25.08, issued 25/26.08.2026 — were in the owner's eCoA database from 09.09.2026 and had never been read into the desk, which is why every Tranche 2 reissue stood 'retest assay pending' on v29 (owner, 15.09.2026: \"here are all retest results that I have on file and correct yourself\"). Read from the rendered pages and gated against an independent second transcription of the same pages (32 of 32 agree on batch, dates, sample number, every result and its uncertainty), then written into the release register (apply_220K.py) and the tracker instances (instances_220K.py); the receipt date 17.08.2026 joins the references table. With the mycotoxins of 11.09.2026 and the campaign's internal certificates of 17.08.2026, all three parts of every Tranche 2 reissue now exist, so the CoQ Register numbers the Tranche 2 reissues after Tranche 1, each planned for the first working day 7 days after the last certificate it cites, and the reissue drafts are compiled for them. Tranche 3 still waits for its mycotoxin certificates (227-М/26), which are on no list the desk holds. The registers' rows, the tracker and every other laboratory result are otherwise v29's.")
    line("v29 · 15.09.2026, later the same day", "Sequential grade numerals (owner, 15.09.2026: \"I choose sequential naming of specification grades\"): the grades of the potency specification of 15.09.2026 are numbered as its table lists them, frozen in potency_grades_2026-09-15.csv (column numeral); a grade defined later takes the strain's next numeral whatever its nominal, and a result in no window of its strain reads 'new specification required' with the next numeral reserved — every code in this build is unchanged by the rule, which only fixes what happens next. The two registers were audited for order and completeness (see Reference: 'Register audit, 15.09.2026'). And the compiled certificate: the document code it prints is the one the CoQ Register states, like its date of issue since 10.09.2026, and a reissue prints under that date, in small bracketed type, '(supersedes <code> of <date>)' naming the initial certificate it replaces — the 21 numbered Tranche 1 reissues are compiled as drafts beside the 22 initial drafts (drafts/…_reissue.html, Tranche_1_CoQ_Reissue_Drafts.pdf). The registers' rows, the tracker and every laboratory result are otherwise unchanged.")
    line("v29", "The CoQ References table inside the workbook (owner, 15.09.2026: \"inside the v28 workbook\"): a tab of one row per certificate of quality and one column per determination — the cited document, its date and laboratory, the sampling day and the laboratory's receipt date — with every n/t cell red, and its Not Tested Review as a section of Reference. The CoQ code on the tab is the one the CoQ Register tab prints, keyed to its rows. And the Potency Grades tab (owner, 15.09.2026): the potency grades per strain — nominal, tolerance, specification window — as the Head of QC's potency specification of 15.09.2026 prints them, one row per strain and grade, with the measured results each page rests on. On the CoQ Register, two things the owner asked for the same day: a reissue names the initial certificate it supersedes by the register's own code (looked up by Key), and every certificate states the potency grade its Total THC result falls in — nominal ± tolerance, window, grade numeral — with the product code and the specification document code generated from it (potency_grading.py: every specification document code is v.01 — the initially issued ones were wrong and this is not the official issuing, the set goes for review — and the status records what the issued v.01 of the same strain and numeral printed). Every certificate's Total THC criterion, grade, product code and specification code now come from that specification alone (owner, 15.09.2026: the grades, nominals, tolerances and ranges in the issued specifications and on the certificates are old and potentially wrong); the issued v.01 document is recorded beside the generated code, not used. The registers' rows, the tracker and every laboratory result are otherwise v28's.")
    line("v28", "Retest sampling dated and the retest series issued (owner, 15.09.2026). The 30 Farmahem 227-К/26 Tranche 3 potency certificates taken in (intake_227K_2026-09-15/: 26 into existing register blocks, four batches given a block — BSS1024_01/2 P050142, WED102501 P060102, SCR012601 P060342, GRC102501/1 P060142 — five rest on the page read alone, OI-32). testing_series.rounds() now places every Farmahem re-analysis certificate in a campaign round of its own, never the release round, so every Tranche 1, 2 and 3 batch has a retest round and its internal certificate: Tranche 1 tested 21–24.07 and issued 27.07.2026, Tranche 2 tested 12–14.08 and issued 17.08.2026, Tranche 3 tested 19–21.08 and issued 24.08.2026. The iCoA Register numbers every round, including the seven whose packaging date the list does not hold. The CoQ Register numbers the Tranche 1 reissues (retest assay, mycotoxins and iCoA all on file) in date order with the release series; Tranche 2 waits for its potency certificates and Tranche 3 for its mycotoxin certificates, and says so. A reissue now prints the initial certificate's result and document for every determination it did not retest. The Parameters sheet and the CoQ rows name the DAB monograph where the cited CNP certificate used it (cnp_methods.py: ППК25050–ППК26069). The export reads its own register on the same build (it read the previous build's file, so an intake numbered nothing until the build after). verify_workbook.py holds the legacy-day check to the release round.")
    line("v27", "Tranche 2 mycotoxin retests taken in: 32 Farmahem certificates 220-1-М/26 to 220-32-М/26 (received 17.08.2026, analysed 07.09.2026, issued 11.09.2026), every result ND for aflatoxins B1, B2, G1, G2 and ochratoxin A. Read directly from the rendered pages at the owner's request and cross-checked against an independent Gemini read of every page, 32 of 32 agreeing. 26 are the Tranche 2 list; the laboratory also tested P050282, P060042, P060082 and three batches printed with no P-number (JD042601, FB042601, CC042601). 23 certificates joined an existing release-register block; nine batches had none and were given one (No. 81 to 89), six of them the batches the delivery reconciliation had found absent from the register; JD042601 took its P-number (P060492) from the Head of QC's batch list, FB042601 and CC042601 are on no list the desk holds (OI-33). Documented in intake_220M_2026-09-14/. Two definition gaps found by the first build, which rendered none of the 32 on this sheet: family() labelled only the 197- series a re-analysis while is_reanalysis() already knew 220- was one, and the tracker files a retest by the label — the label now derives from the same list (REANALYSIS_SERIES, which also carries the 227- potency series the owner called retests on 12.09.2026); and the tracker's document pool is the owner's index plus new_instances.json, never the release register — the 32 are now testing instances there (instances_220M.py), seven of them opening a lot the owner's tracker did not carry. Found on the way and fixed: the in-house cells of eight lots (GG012601*, GG1024, JD012601*, JD112501*, OMP1024_01, BSS1024_01/1, BSS1024_01/2, WED102501) looked their internal CoA up under another lot's key — the at-issue placeholder folded to one key and the last lot written held it — invisible while every one of them was at issue, wrong the day any was numbered; verify_workbook.py now checks that every lookup keys its own lot (27 cells in v26).")


def fix_parameters(wb):
    """The Parameters sheet is inherited from the owner's workbook: its Source and Tracker column
    values are set from the rulings and the live tracker layout."""
    if "Parameters" not in wb.sheetnames:
        return
    sh = wb["Parameters"]
    hdr = {str(sh.cell(1, c).value or "").strip(): c for c in range(1, sh.max_column + 1)}
    src_c, col_c = hdr.get("Source"), hdr.get("Tracker column")
    # Owner, 15.09.2026: the method reference names the method the cited certificate used.
    # CNP ran the cannabinoid assay and loss on drying by the DAB monograph on every
    # certificate up to ППК26069 (11.05.2026) and by Ph. Eur. 3028 from ППК26110
    # (30.06.2026) — cnp_methods.py reads it off each certificate, and the CoQ rows
    # citing a DAB certificate print the DAB reference (coq_artifact_data.json, "mth").
    mth_c = hdr.get("Method")
    if mth_c:
        for r in range(2, sh.max_row + 1):
            if str(sh.cell(r, 1).value or "").strip() in ("3", "4", "5", "6", "8"):
                v = str(sh.cell(r, mth_c).value or "")
                if "DAB" not in v:
                    sh.cell(r, mth_c).value = v + " · on a CoQ citing a CNP certificate up to ППК26069 (11.05.2026): DAB 2018 monograph Cannabis flos (2.2.29 / 2.2.32), the method CNP used before its Ph. Eur. 3028 accreditation (cnp_methods_2026-09-15.csv)"
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


# The nine sheets that are neither a primary view nor a formula source. Owner,
# 14.09.2026: the workbook had sixteen tabs and needs six. None of these is read
# by a formula anywhere — only iCoA Register, CoQ Register and Batch Dates are —
# so they can be moved without breaking a single lookup. They are CONSOLIDATED
# rather than deleted: they are the audit trail (what was reconciled, what is
# credited, what a person must still do, what is unresolved), and taking that out
# of a controlled record is the one direction that cannot be undone from inside
# the workbook. Deleting the one sheet they now share is a keystroke if the owner
# decides otherwise.
FOLD_INTO_REFERENCE = ["Read Me", "Delivery T1–T3", "ImB Register", "Mikro CoQ Parameter",
                       "Reconciliation 09.09", "Credit Audit", "Credit Corrections",
                       "Work Order", "Open Items", "Not Tested Review", "Summary Dashboard"]


def fold_reference_sheet(wb, names=None):
    """Stack the leaf sheets onto one Reference sheet and drop the originals.

    Values, fonts, fills, alignment and number formats come across cell for cell;
    merged ranges are translated by the row offset so a note that spans its table
    still reads as one block. Column widths cannot follow — one sheet has one set
    — so the widest section's widths are taken and the rest wrap under them.

    Each section's row range is recorded as a defined name, `_fold_<slug>`. Where
    a section ends is a fact this function knows and nothing downstream can infer:
    several of the folded sheets separate their own sections with the same blank
    gutter used between sections here, so a reader guessing from blank rows stops
    at the first inner gutter and silently loses the rest of the sheet.
    """
    import copy as _copy
    import re as _re
    from openpyxl.utils import range_boundaries
    from openpyxl.workbook.defined_name import DefinedName

    names = [n for n in (names or FOLD_INTO_REFERENCE) if n in wb.sheetnames]
    if not names:
        return 0, 0
    ref = wb.create_sheet("Reference")
    row = 1
    widths = {}
    for name in names:
        src = wb[name]
        c = ref.cell(row, 1, name.upper())
        c.font = Font(name="Calibri", size=12, bold=True, color=NAVY)
        c.alignment = Alignment(vertical="center")
        ref.row_dimensions[row].height = 20
        row += 1
        top = row
        for r in range(1, src.max_row + 1):
            for col in range(1, src.max_column + 1):
                s = src.cell(r, col)
                if s.value is None and not s.has_style:
                    continue
                d = ref.cell(row, col, s.value)
                d.font = _copy.copy(s.font)
                d.fill = _copy.copy(s.fill)
                d.border = _copy.copy(s.border)
                d.alignment = _copy.copy(s.alignment)
                d.number_format = s.number_format
            if src.row_dimensions[r].height:
                ref.row_dimensions[row].height = src.row_dimensions[r].height
            row += 1
        for m in list(src.merged_cells.ranges):
            c1, r1, c2, r2 = range_boundaries(str(m))
            ref.merge_cells(start_row=r1 + top - 1, start_column=c1,
                            end_row=r2 + top - 1, end_column=c2)
        for letter, dim in src.column_dimensions.items():
            if dim.width and dim.width > widths.get(letter, 0):
                widths[letter] = dim.width
        wb.defined_names.add(DefinedName(
            "_fold_" + _re.sub(r"\W+", "_", name).strip("_"),
            attr_text="Reference!$A$%d:$A$%d" % (top, row - 1)))
        row += 2                                    # a blank gutter between sections
    for letter, w in widths.items():
        ref.column_dimensions[letter].width = w
    for name in names:
        del wb[name]
    return len(names), row - 1


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
        add_references_sheet(wb)
        add_potency_sheet(wb)
        add_dates_sheet(wb)
        write_register_file(os.path.join(HERE, "Issuance_Registers_prelim.xlsx"))
    add_delivery_sheet(wb)
    if CELLS_0909:
        add_reconciliation_sheet(wb)
    add_imb_register_sheet(wb)
    apply_strain_rulings(wb)
    # The standing register of what the desk cannot decide. Its own module, so the
    # same list drives the sheet and the note that travels with the package and an
    # item is written down once rather than rediscovered each session. Added before
    # the Read Me, so it is described there like every other sheet.
    try:
        import open_items as OI
        OI.sheet(wb, wb.sheetnames.index("Work Order") + 1)
        print("open items: %d (%d awaiting a ruling, %d marked on the certificate)"
              % (len(OI.ITEMS), len(OI.items("open")), len(OI.items("marked"))))
    except Exception as _e:
        print("Open Items sheet not written:", _e)
    write_read_me(wb)
    fix_parameters(wb)
    # Sixteen tabs down to seven (owner, 14.09.2026). iCoA Issuance is already
    # gone by here — its columns were folded into the iCoA Register, which was
    # always the same one-row-per-round shape — and these nine fold onto one
    # Reference sheet. What is left is the six sheets the owner asked for plus
    # the audit trail behind them.
    _folded, _ref_rows = fold_reference_sheet(wb)
    # iCoA Issuance is DROPPED, not folded: every column it carried is now on the
    # iCoA Register beside the code and dates those columns belong to. Stacking it
    # onto Reference as well would put the same values in the workbook twice, and
    # a value that exists in two places is the defect this folder keeps finding.
    if "iCoA Issuance" in wb.sheetnames:
        del wb["iCoA Issuance"]
        print("iCoA Issuance: dropped — its columns are on the iCoA Register")
    print("reference sheet: %d sheet(s) folded into one, %d rows; workbook now %d tabs — %s"
          % (_folded, _ref_rows, len(wb.sheetnames), ", ".join(wb.sheetnames)))
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
