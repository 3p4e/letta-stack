#!/usr/bin/env python3
"""Truth check of a built workbook: every sheet against the desk's own data.

Each check states what it compares and prints one line per finding. It reads the workbook
twice — once as written (formulas) and once recalculated through LibreOffice (values) — so a
formula column is judged by what it computes, not by its text.

    python3 verify_workbook.py CoQ_Analysis_Master_v11.xlsx
"""
import csv, importlib.util, json, os, re, shutil, subprocess, sys, tempfile, collections
import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from reference_sections import latest_master, sheet_or_section      # noqa: E402

SRC = sys.argv[1] if len(sys.argv) > 1 else latest_master(HERE)
if not SRC or not os.path.exists(SRC):
    raise SystemExit("no workbook to verify in " + HERE)
spec = importlib.util.spec_from_file_location("tracker_data", os.path.join(HERE, "tracker_data.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)

FIND = []


def bad(sheet, what, detail=""):
    FIND.append((sheet, what, detail))


NO_CALC = ""          # why the computed values are unavailable, if they are


def load_values(path):
    """The workbook with its formulas evaluated, or None where that is not possible.

    openpyxl writes formulas and no cached values, so the only way to read what
    a formula computes is to let a spreadsheet engine compute it. Where LibreOffice
    is not installed this used to raise FileNotFoundError and take the whole
    verifier down with it — which is how a CI job added to gate the registers
    failed on a missing dependency instead of on the thing it was watching, and
    would have failed the same way whether the registers agreed or not.

    The checks that read only literals — the register codes, the keys, the sheet
    inventory — do not need an engine. Those still run. The deeper pass over
    computed results is skipped, loudly, and the exit code still reflects
    everything that did run.
    """
    global NO_CALC
    if shutil.which("soffice") is None:
        NO_CALC = "LibreOffice (soffice) is not installed"
        return None
    tmp = tempfile.mkdtemp(prefix="verify_")
    try:
        shutil.copy(path, os.path.join(tmp, "in.xlsx"))
        subprocess.run(["soffice", "--headless", "--calc", "--convert-to", "xlsx", "--outdir",
                        os.path.join(tmp, "out"), os.path.join(tmp, "in.xlsx")],
                       check=True, capture_output=True, timeout=900)
        return openpyxl.load_workbook(os.path.join(tmp, "out", "in.xlsx"), data_only=True)
    except (subprocess.SubprocessError, OSError) as e:
        NO_CALC = "LibreOffice could not evaluate the workbook: %s" % e
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


WB = openpyxl.load_workbook(SRC)
WV = load_values(SRC)
if WV is None:
    # Cannot verify is not the same as verified, and must never read as success.
    # Most of these checks compare what a FORMULA computes against the record it
    # is built from, and openpyxl stores no cached values — without an engine
    # there is nothing to compare. Better to stop here saying so than to run a
    # partial pass that prints a reassuring number.
    print("CANNOT VERIFY: %s." % NO_CALC)
    print("  The workbook's registers and dates are live formulas and openpyxl "
          "stores no computed values, so an engine is needed to read them.")
    print("  Install libreoffice-calc and run again.")
    sys.exit(2)
TRACKER = next(n for n in WB.sheetnames if n.startswith("CoQ Parameter Tracker"))


def table(wb, name, key_row=1):
    sh = wb[name]
    hdr = [str(c.value or "").strip() for c in sh[key_row]]
    out = []
    for r in range(key_row + 1, sh.max_row + 1):
        vals = [sh.cell(r, c).value for c in range(1, len(hdr) + 1)]
        if not any(v not in (None, "") for v in vals[:3]):
            continue
        # The footnote under a table is one merged cell spanning its width, so it
        # arrives as a long string in the first column with nothing beside it.
        # That is how it is recognised. It used to be recognised by its opening
        # words — "Head of QC", "Chronological", "These corrections" — and
        # rewriting a note then fed its own text to int() as a row number.
        if isinstance(vals[0], str) and len(vals[0]) > 120 and not any(
                v not in (None, "") for v in vals[1:]):
            continue
        out.append((r, dict(zip(hdr, vals))))
    return out


def table_or_section(wb, name, key_row=1):
    """`table()` for a sheet, or for its section on the Reference sheet."""
    if name in wb.sheetnames:
        return table(wb, name, key_row)
    sh = sheet_or_section(wb, name)
    hdr = [str(sh.cell(key_row, c).value or "").strip() for c in range(1, sh.max_column + 1)]
    while hdr and not hdr[-1]:
        hdr.pop()
    out = []
    for r in range(key_row + 1, sh.max_row + 1):
        vals = [sh.cell(r, c).value for c in range(1, len(hdr) + 1)]
        if not any(v not in (None, "") for v in vals[:3]):
            continue
        if isinstance(vals[0], str) and len(vals[0]) > 120 and not any(
                v not in (None, "") for v in vals[1:]):
            continue
        out.append((r, dict(zip(hdr, vals))))
    return out


def fmt(v):
    return v.strftime("%d.%m.%Y") if hasattr(v, "strftime") else ("" if v is None else str(v))


# ---------------------------------------------------------------- the lots, as the tracker reads them
LOTS = {}                                   # (cu, p) -> {n: [refs]}
sh = WB[TRACKER]
starts = [c for c in range(4, sh.max_column + 1) if str(sh.cell(2, c).value or "").startswith("#")]
PCOL = {}
for i, s0 in enumerate(starts):
    e = (starts[i + 1] - 1) if i + 1 < len(starts) else sh.max_column
    n = int(re.match(r"#(\d+)", str(sh.cell(2, s0).value)).group(1))
    PCOL[n] = (s0, e)
anchors = [r for r in range(5, sh.max_row + 1) if sh.cell(r, 1).value not in (None, "")
           and not str(sh.cell(r, 1).value).startswith("KEY")]
for a, nxt in zip(anchors, anchors[1:] + [sh.max_row + 1]):
    cu, p = str(sh.cell(a, 1).value), str(sh.cell(a, 2).value or "")
    docs = collections.defaultdict(list)
    for n, (s0, e) in PCOL.items():
        single = (e - s0) <= 2
        for r in range(a, nxt, 2):
            # coverage means what the tracker means by it: a credited certificate reporting a
            # RELEASE result — the green fill. A credited certificate without a result (amber), a
            # stability timepoint (orange) and an uncredited document (grey) are not coverage.
            c = sh.cell(r, s0)
            fill = c.fill.fgColor.rgb[-6:] if c.fill and c.fill.fill_type == "solid" and isinstance(c.fill.fgColor.rgb, str) else None
            if fill != "C6EFCE":
                continue
            txt = str(WV[TRACKER].cell(r if single else r + 1, s0 + 1 if single else s0).value or "")
            if txt and "on file, not credited" not in txt:
                docs[n].append(txt)
    LOTS[(cu, p)] = {"row": a, "docs": docs, "status": str(sh.cell(a, 3).value or "")}

# ---------------------------------------------------------------- 1. Batch Coverage
cov = table(WB, "Batch Coverage")
cvv = {r: d for r, d in table(WV, "Batch Coverage")}
hdr = [str(c.value or "") for c in WB["Batch Coverage"][1]]
seen = collections.Counter()
for r, d in cov:
    cu, p = str(d[hdr[0]] or ""), str(d[hdr[1]] or "")
    seen[(re.sub(r"[＊*]", "", cu), p)] += 1
    key = next((k for k in LOTS if re.sub(r"[＊*]", "", k[0]) == re.sub(r"[＊*]", "", cu)
                and (k[1] == p or (p.startswith("—") and k[1].startswith("N/A")))), None)
    if key is None:
        bad("Batch Coverage", "row has no lot on the tracker", f"{cu} / {p}")
        continue
    docs = LOTS[key]["docs"]
    miss, onfile = [], set()
    for n in range(1, 13):
        mark = str(d[hdr[3 + n]] or "")
        want = "✓" if docs.get(n) else "✗"
        # ○ is a ✗ that says why: the tracker names no document, and a certificate
        # for this parameter was found in eCoA_DATABASE on 09.09.2026. It is not
        # coverage, so it counts as missing exactly as ✗ does.
        if mark == "○" and want == "✗":
            onfile.add(n)
        elif mark != want:
            bad("Batch Coverage", f"#{n} mark disagrees with the tracker", f"{cu} / {p}: sheet {mark!r}, tracker {want!r}")
        if want == "✗":
            miss.append(n)
    if int(d[hdr[16]] or 0) != len(miss):
        bad("Batch Coverage", "missing count", f"{cu} / {p}: sheet {d[hdr[16]]}, computed {len(miss)}")
    st = str(d[hdr[3]] or "")
    want_st = "✓ COMPLETE" if not miss else (
        f"○ {len(miss)} ON FILE, NOT RECORDED" if set(miss) == onfile and onfile else
        (f"⚠ {len(miss)} MISSING" if len(miss) <= 3 else f"❌ {len(miss)} MISSING"))
    if st != want_st:
        bad("Batch Coverage", "status text", f"{cu} / {p}: {st!r} vs {want_st!r}")
for k, n in seen.items():
    if n > 1:
        bad("Batch Coverage", "lot appears more than once", f"{k}: {n} rows")
for k in LOTS:
    if seen.get((re.sub(r"[＊*]", "", k[0]), k[1] if not k[1].startswith("N/A") else "— not assigned —"), 0) == 0:
        bad("Batch Coverage", "lot on the tracker has no coverage row", str(k))

# ---------------------------------------------------------------- 2. Summary Dashboard
db = sheet_or_section(WB, "Summary Dashboard")
lab = {str(db.cell(r, 1).value or ""): r for r in range(1, db.max_row + 1)}
nlots = len(cov)
miss_per = collections.Counter()
for r, d in cov:
    for n in range(1, 13):
        if str(d[hdr[3 + n]] or "") == "✗":
            miss_per[n] += 1
comp = sum(1 for r, d in cov if not any(str(d[hdr[3 + n]] or "") == "✗" for n in range(1, 13)))
part = sum(1 for r, d in cov if 1 <= sum(1 for n in range(1, 13) if str(d[hdr[3 + n]] or "") == "✗") <= 3)
inc = nlots - comp - part
for k, want in (("Total Batches", nlots), ("✅  COMPLETE  (all 12 params)", comp),
                ("⚠   PARTIAL  (1–3 missing)", part), ("❌  INCOMPLETE (4+ missing)", inc)):
    if k in lab:
        got = db.cell(lab[k], 2).value
        if int(got or 0) != want:
            bad("Summary Dashboard", k, f"sheet {got}, coverage says {want}")
for r in range(1, db.max_row + 1):
    m = re.match(r"#(\d+)\s", str(db.cell(r, 1).value or ""))
    if m:
        n = int(m.group(1))
        got = db.cell(r, 2).value
        if int(got or 0) != miss_per[n]:
            bad("Summary Dashboard", f"missing frequency #{n}", f"sheet {got}, coverage says {miss_per[n]}")

# ---------------------------------------------------------------- 3. Parameters
par = table(WB, "Parameters")
crit_sheet = {str(d["#"]).strip(): str(d["Acceptance criterion (global)"] or "") for _, d in par}
for no, c in crit_sheet.items():
    want = T.CRIT.get(no)
    if want and c.strip() != want.strip():
        bad("Parameters", f"acceptance criterion #{no}", f"sheet {c!r}, desk {want!r}")
# row 3 of the tracker must print the same criteria
for n, (s0, e) in PCOL.items():
    subs = T.GROUPS.get(n) or [str(n)]
    if len(subs) > 1:
        for j, sub in enumerate(subs):
            got = str(sh.cell(3, s0 + j).value or "").replace("A.C.: ", "")
            if T.CRIT.get(sub) and got.strip() != T.CRIT[sub].strip():
                bad(TRACKER, f"row 3 criterion {sub}", f"{got!r} vs {T.CRIT[sub]!r}")
    else:
        got = str(sh.cell(3, s0).value or "").replace("A.C.: ", "")
        if T.CRIT.get(str(n)) and got.strip() != T.CRIT[str(n)].strip():
            bad(TRACKER, f"row 3 criterion #{n}", f"{got!r} vs {T.CRIT[str(n)]!r}")
# the tracker column letters
from openpyxl.utils import get_column_letter as L
for _, d in par:
    no = str(d["#"]).strip()
    n = int(no.split(".")[0])
    want = (f"{L(PCOL[n][0])}–{L(PCOL[n][1])}" if "." not in no else None)
    if want and str(d.get("Tracker column") or "") != want:
        bad("Parameters", f"tracker column #{no}", f"sheet {d.get('Tracker column')!r}, layout {want!r}")

# ---------------------------------------------------------------- 4. Batch Dates
bd = table(WB, "Batch Dates")
raw = {r["p_batch"] or r["cu_batch"]: r for r in csv.DictReader(open(os.path.join(HERE, "batch_dates.csv"), encoding="utf-8"))}
if len(bd) != len(raw):
    bad("Batch Dates", "row count", f"sheet {len(bd)}, batch_dates.csv {len(raw)}")
for _, d in bd:
    k = str(d["P Batch"] or d["Batch (as listed)"])
    src = raw.get(k)
    if not src:
        bad("Batch Dates", "row not in batch_dates.csv", k)
        continue
    for col, field in (("Packaging from", "packaging_from"), ("Packaging to", "packaging_to"),
                       ("Harvest from", "harvest_from"), ("Harvest to", "harvest_to")):
        got = fmt(d[col])
        want = src[field] or "— not given —"
        if got != want:
            bad("Batch Dates", f"{col} for {k}", f"sheet {got!r}, csv {want!r}")

# ---------------------------------------------------------------- 5. the two registers
regv = {r: d for r, d in table(WV, "iCoA Register")}
regf = {r: d for r, d in table(WB, "iCoA Register")}
cqv = {r: d for r, d in table(WV, "CoQ Register")}
cqf = {r: d for r, d in table(WB, "CoQ Register")}
for name, rows, code_col, prefix in (("iCoA Register", regv, "iCoA code", "iCoA-PP_26-"),
                                     ("CoQ Register", cqv, "CoQ code", "CoQ-PP_26-")):
    nums = [(r, d) for r, d in rows.items() if d["No."] not in (None, "")]
    seqn = [int(d["No."]) for _, d in sorted(nums)]
    # Strictly increasing down the page, not contiguous 1..n. The iCoA series is
    # icoa_register.py's, which numbers every testing round; this sheet carries
    # the rounds it models, so its numbers are an ordered SUBSET with gaps where
    # a round is registered elsewhere. Contiguity was only ever true while the
    # sheet numbered its own rows by position — the defect that was removed.
    if any(b <= a for a, b in zip(seqn, seqn[1:])):
        bad(name, "numbers do not increase down the page", f"{seqn[:8]} …")
    if seqn and seqn[0] < 1:
        bad(name, "numbering does not start at 1", str(seqn[0]))
    for r, d in nums:
        want = f"{prefix}{int(d['No.']):03d}"
        if str(d[code_col]) != want:
            bad(name, "code does not follow its number", f"row {r}: {d[code_col]} vs {want}")
    keys = [str(d["Key"]) for _, d in rows.items()]
    dup = [k for k, c in collections.Counter(keys).items() if c > 1]
    if dup:
        bad(name, "duplicate key", str(dup[:5]))
    dates = [fmt(d["Issue date (planned)"]) for _, d in sorted(nums)]
    ds = [x[6:] + x[3:5] + x[:2] for x in dates if x]
    if ds != sorted(ds):
        bad(name, "planned issue dates are not in the numbering order", f"{dates[:8]} …")
    for r, d in rows.items():
        if d["Issuable"] == "yes" and not d["No."]:
            bad(name, "issuable row without a number", f"row {r} {d.get('Key')}")
        if d["Issuable"] not in ("yes", "allocated", "ruled") and d["No."]:
            bad(name, "number on a row that is not issuable", f"row {r} {d.get('Key')}")
        # a ruled row (Head of QC, 18.09.2026) carries its code and no date: the list
        # holds no packaging date for the lot, and the number was the only thing withheld
        if d["Issuable"] == "ruled":
            if not d["No."]:
                bad(name, "ruled row without a number", f"row {r} {d.get('Key')}")
            if fmt(d["Issue date (planned)"]):
                bad(name, "ruled row carries a planned date", f"row {r} {d.get('Key')}")
            if "no packaging date" not in str(d.get("Status", "")) and "packaging date" not in str(d.get("Status", "")):
                bad(name, "ruled row is not one the list lacks a packaging date for", f"row {r} {d.get('Key')}")
        # an allocated row (CoQ Register, Tranche 3, owner 15.09.2026) carries its code
        # and no date — the date follows the mycotoxin certificate
        if d["Issuable"] == "allocated":
            if not d["No."]:
                bad(name, "allocated row without a number", f"row {r} {d.get('Key')}")
            if not str(d.get("Series", "")).startswith("retest — Tranche 3"):
                bad(name, "allocated row is not a Tranche 3 reissue", f"row {r} {d.get('Key')}: {d.get('Series')}")
    # the allocated rows share ONE planned date — the owner's, for the whole tranche,
    # 15.09.2026 — or none, and it is not before any date the register has issued on
    _alloc_days = {fmt(d["Issue date (planned)"]) for d in rows.values() if d["Issuable"] == "allocated"}
    _yes_days = [fmt(d["Issue date (planned)"]) for d in rows.values() if d["Issuable"] == "yes" and fmt(d["Issue date (planned)"])]
    if len(_alloc_days) > 1:
        bad(name, "the allocated rows do not share one planned date", str(sorted(_alloc_days)))
    for _ad in _alloc_days:
        if _ad and _yes_days and (_ad[6:] + _ad[3:5] + _ad[:2]) < max(x[6:] + x[3:5] + x[:2] for x in _yes_days):
            bad(name, "an allocated row is planned before an issued row", f"{_ad} before {max(_yes_days, key=lambda x: x[6:] + x[3:5] + x[:2])}")
# every CoQ cites an iCoA that exists, and is not dated before it
icoa_by_key = {str(d["Key"]): d for d in regv.values()}
for r, d in cqv.items():
    k = str(d["Key"])
    ic = icoa_by_key.get(k)
    if ic is None:
        bad("CoQ Register", "no iCoA Register row for the key", k)
        continue
    a, b2 = fmt(d["Issue date (planned)"]), fmt(ic["Issue date (planned)"])
    if a and b2 and (b2[6:] + b2[3:5] + b2[:2]) > (a[6:] + a[3:5] + a[:2]):
        bad("CoQ Register", "CoQ is dated before its iCoA", f"{k}: CoQ {a}, iCoA {b2}")
    if d["No."] and fmt(d["Packaging complete"] if "Packaging complete" in d else "") == "":
        pass
# a CoQ is never dated before the lot's packaging
pk = {}
for _, d in bd:
    pk[str(d["P Batch"] or d["Batch (as listed)"])] = fmt(d["Packaging to"])
for r, d in cqv.items():
    if not d["No."]:
        continue
    lot = str(d["P Batch"] or "")
    end = pk.get(lot)
    a = fmt(d["Issue date (planned)"])
    if end and a and (end[6:] + end[3:5] + end[:2]) > (a[6:] + a[3:5] + a[:2]):
        bad("CoQ Register", "CoQ is dated before the lot was packed", f"{lot}: CoQ {a}, packed to {end}")
# the SOP floor
for name, rows, col in (("iCoA Register", regv, "Issue date (planned)"), ("CoQ Register", cqv, "Issue date (planned)")):
    for r, d in rows.items():
        a = fmt(d[col])
        if a and (a[6:] + a[3:5] + a[:2]) < "20260511":
            bad(name, "issue date before the SOP floor of 11.05.2026", f"row {r}: {a}")

# ---------------------------------------------------------------- 6. a code always states its scope
# This ran against the iCoA Issuance sheet, which no longer exists: its columns
# were folded into the iCoA Register on 14.09.2026, both having always been one
# row per batch and round. Half of what it checked went with the merge — "cites a
# code that is not in the register" cannot fail when the sheet IS the register —
# and that half is dropped rather than rewritten into a tautology. What survives
# is the half that still says something: a row carrying an issued code must also
# say what that certificate covers, because a certificate of quality cites this
# scope and an empty one would let it assert a determination nobody certified.
for r, d in table(WV, "iCoA Register"):
    code = str(d.get("iCoA code") or "")
    if not code.startswith("iCoA-PP_26-"):
        continue
    if str(d.get("Series") or "").startswith("initial") and str(d.get("iCoA scope") or "").startswith("—"):
        bad("iCoA Register", "an issued code with no scope", f"row {r}: {code}")

# ---------------------------------------------------------------- 7. Work Order / Credit Audit
wo = table_or_section(WB, "Work Order")
au = table_or_section(WB, "Credit Audit")
if not wo:
    bad("Work Order", "empty", "")
for r, d in au:
    if not str(d.get("Finding") or "").strip() or not str(d.get("Action") or "").strip():
        bad("Credit Audit", "row without a finding or an action", f"row {r}")
    if not str(d.get("Certificate") or "").strip():
        bad("Credit Audit", "row without a certificate", f"row {r}")
for r, d in wo:
    if not str(d.get("Task") or "").strip() or not str(d.get("What is needed") or "").strip():
        bad("Work Order", "row without a task or what is needed", f"row {r}")

# ---------------------------------------------------------------- 7b. an in-house lookup keys its own lot
# The tracker's in-house cells look the internal-CoA code up in the iCoA Register by the
# lot's own key, so a renumbering follows. v26 keyed eight of them to another lot's key
# (the at-issue placeholder folded to one key under nkey, and the last lot written held it):
# invisible while every one of those lots was at issue, wrong the day any was numbered.
for a, nxt in zip(anchors, anchors[1:] + [sh.max_row + 1]):
    cu, p = str(sh.cell(a, 1).value), str(sh.cell(a, 2).value or "")
    own = {p} | {x.strip() for x in p.split("/")} if not p.startswith("N/A") else {re.sub(r"[＊*]", "", cu)}
    for r in range(a, nxt):
        for c in range(4, sh.max_column + 1):
            v = sh.cell(r, c).value
            m = re.search(r'MATCH\("([^"|]+)\|[IR]', v) if isinstance(v, str) else None
            if m and m.group(1) not in own:
                bad(TRACKER, "an in-house lookup keys another lot", f"row {r} {cu} ({p}) looks up {m.group(1)}")

# ---------------------------------------------------------------- 8. Read Me
rm = sheet_or_section(WB, "Read Me")
txt = "\n".join(str(c.value) for row in rm.iter_rows() for c in row if isinstance(c.value, str))
listed = {str(rm.cell(r, 1).value) for r in range(1, rm.max_row + 1) if rm.cell(r, 2).value}
for n in WB.sheetnames:
    if n not in listed:
        bad("Read Me", "sheet not described", n)
for n in listed:
    if n in ("What it is",):
        continue
    if n not in WB.sheetnames and n[:1].isupper() and " " in n and not n.isupper() and n not in (
            "Batch names", "Certificate codes", "Do not", "OOS check", "Version history"):
        pass
for sh_ in WB.worksheets:
    if sh_.page_setup.orientation != "landscape" or not sh_.page_setup.fitToWidth:
        bad("Read Me", "the print claim is not true for this sheet", sh_.title)

# ---------------------------------------------------------------- the iCoA series
# The internal-CoA number exists in two places: icoa_register.py, which the
# certificates print from, and this workbook's iCoA Register sheet, which numbers
# its rows by position with COUNT(A$1:A{n})+1. Two definitions of one number will
# disagree, and on 11.09.2026 they did — on every row that could be compared. A
# certificate citing iCoA-PP_26-066 while the register gives that batch
# iCoA-PP_26-001 is two controlled documents contradicting each other about the
# identity of a third, so it is checked here rather than noticed by a reader.
try:
    # Both paths are derived from this file, never written down: an absolute path
    # to one machine's checkout is not a path on another, and hard-coding one is
    # how this check first ran in CI reporting "No module named 'ingestion'"
    # instead of the register disagreement it was added to catch.
    #   <root>/deliverables/qc_gap_analysis/tracker/verify_workbook.py
    import sys as _sys, os as _os
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _gap = _os.path.dirname(_here)
    _root = _os.path.dirname(_os.path.dirname(_gap))
    for _p in (_gap, _root):
        if _p not in _sys.path:
            _sys.path.insert(0, _p)
    import icoa_register as _IR
    from ingestion.common.batch_id import batch_key as _bk
    # The key names the ROUND, not merely "some retest". `setdefault` on a bare
    # |R gave the key to whichever retest the issue order happened to put first,
    # so GP0824_03's |R resolved to its retest 2 and the sheet's retest 1 was
    # reported as disagreeing with the series it had been taken from. Retest 1
    # keeps the bare |R that every existing lookup cites; rounds 2 and up take
    # |R2 … |R5, exactly as the builder writes them.
    _mod = {}
    for _row in _IR.build():
        _rd = _row["round"]
        _suf = "I" if _rd == "initial release" else ("R" if _rd == "retest 1" else "R" + _rd.split()[-1])
        for _base in filter(None, (_row["p_lot"], _row["batch"])):
            _mod.setdefault("%s|%s" % (_bk(_base), _suf), _row["code"])
    _reg = WB["iCoA Register"]
    _n, _agree, _differ, _unknown = 0, 0, 0, 0
    for _r in range(2, _reg.max_row + 1):
        _key = str(_reg.cell(_r, 16).value or "")
        if not _key or str(_reg.cell(_r, 3).value or "") != "yes":
            continue
        _n += 1
        # the code the sheet actually prints, read from the sheet. This used to
        # recompute it from the row's position — which was the very defect being
        # checked for, so once the sheet stopped numbering by position the check
        # went on comparing against a number no longer on the page.
        _sheet_code = str(_reg.cell(_r, 2).value or "").strip()
        _base, _, _suf = _key.rpartition("|")
        _want = _mod.get("%s|%s" % (_bk(_base), _suf))
        if _want is None:
            _unknown += 1
        elif _want == _sheet_code:
            _agree += 1
        else:
            _differ += 1
            if _differ <= 5:
                bad("iCoA Register", "code disagrees with icoa_register.py",
                    "%s: sheet %s, certificates cite %s" % (_key, _sheet_code, _want))
    if _differ:
        bad("iCoA Register", "the series is numbered twice and the two disagree",
            "%d of %d comparable rows differ; %d rows the module cannot identify"
            % (_differ, _agree + _differ, _unknown))

    # The check above compares the codes of the rows the sheet happens to carry,
    # and it passed while the sheet carried 60 of the series' 95 certificates:
    # a code cannot disagree with a row that is not on the page. The owner's
    # ruling is about COVERAGE — "every internal certificate that exists or ever
    # will" — so that is what is checked. Each certificate in the series appears
    # on the sheet exactly once, printed under its own code.
    _want_codes = [_row["code"] for _row in _IR.build() if _row["code"]]
    _seen_codes = collections.Counter()
    for _r in range(2, _reg.max_row + 1):
        _c = str(_reg.cell(_r, 2).value or "").strip()
        if _c.startswith("iCoA-PP_26-"):
            _seen_codes[_c] += 1
    _absent = [_c for _c in _want_codes if not _seen_codes[_c]]
    _twice = sorted(_c for _c, _k in _seen_codes.items() if _k > 1)
    _alien = sorted(set(_seen_codes) - set(_want_codes))
    if _absent:
        bad("iCoA Register", "the standing register does not carry every certificate in the series",
            "%d of %d absent: %s%s" % (len(_absent), len(_want_codes), ", ".join(_absent[:6]),
                                       " …" if len(_absent) > 6 else ""))
    if _twice:
        bad("iCoA Register", "a certificate is registered on more than one row", ", ".join(_twice[:6]))
    if _alien:
        bad("iCoA Register", "a code on the sheet is not in the series", ", ".join(_alien[:6]))
except Exception as _e:
    bad("iCoA Register", "could not be checked against icoa_register.py", str(_e))

print(f"{len(FIND)} finding(s)")
for s, w, d in FIND:
    print(f"  [{s}] {w}" + (f" — {d}" if d else ""))


# =================================================================== deeper checks: the sheets against the record
FIND2 = []


def bad2(sheet, what, detail=""):
    FIND2.append((sheet, what, detail))


CORPUS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "ingestion", "ecoa_runner", "records_corpus.json")
recs = json.load(open(CORPUS)) if os.path.exists(CORPUS) else []
by_code = {}
for r in recs:
    c = T.nkey(str(r.get("cert_code") or ""))
    if c:
        by_code.setdefault(c, []).append(r)

# ---- 9. every printed result against the two-read record of its certificate
KEYMAP = {"1": "identification_a_macroscopic", "2": "identification_b_microscopic", "4": "total_thc",
          "5": "total_cbd", "6": "total_cbn", "8": "loss_on_drying", "9.1": "tamc", "9.2": "tymc",
          "9.3": "bile_tolerant_gram_negative", "9.4": "salmonella", "9.5": "escherichia_coli"}


def num(x):
    m = re.search(r"(\d+(?:[.,]\d+)?)", str(x).replace(" ", " "))
    return float(m.group(1).replace(",", ".")) if m else None


checked = mismatch = 0
sh2 = WB[TRACKER]
for (cu, p), lot in LOTS.items():
    a = lot["row"]
    for n, (s0, e) in PCOL.items():
        single = (e - s0) <= 2
        subs = T.GROUPS.get(n) or [str(n)]
        for r in range(a, a + 40, 2):
            if r > sh2.max_row:
                break
            ref = str(WV[TRACKER].cell(r if single else r + 1, s0 + 1 if single else s0).value or "")
            if not ref or "not credited" in ref or ref.startswith("—"):
                continue
            code = T.nkey(ref.split(",")[0])
            for j, sub in enumerate(subs):
                key = KEYMAP.get(sub)
                if not key:
                    continue
                printed = str(WV[TRACKER].cell(r, s0 + (0 if single else j)).value or "")
                if not printed or printed.startswith(("not ", "n.r.", "no result", "held", "Conforms")):
                    continue
                for rec in by_code.get(code, []):
                    pm = next((x for x in rec.get("parameters", []) if x.get("parameter") == key), None)
                    if not pm or not pm.get("result_printed"):
                        continue
                    checked += 1
                    a_num, b_num = num(printed), num(pm["result_printed"])
                    if a_num is not None and b_num is not None and abs(a_num - b_num) > 0.005:
                        mismatch += 1
                        bad2(TRACKER, f"printed result differs from the certificate record ({sub})",
                             f"{cu}/{p} {code}: sheet {printed!r}, corpus {pm['result_printed']!r}")
                    break

# ---- 10. the specification verdicts: red = over the criterion, orange = undetermined
for (cu, p), lot in LOTS.items():
    a = lot["row"]
    for n, (s0, e) in PCOL.items():
        single = (e - s0) <= 2
        subs = T.GROUPS.get(n) or [str(n)]
        for r in range(a, a + 40, 2):        # results sit on a block's top row; the bottom row is the reference
            if r > sh2.max_row:
                break
            for j, sub in enumerate(subs):
                c = sh2.cell(r, s0 + (0 if single else j))
                v = str(WV[TRACKER].cell(c.row, c.column).value or "")
                # only a reported result is judged: the red of "— MISSING —" says no certificate,
                # and prose ("not on this certificate", "n.r.", "held for review") is never judged
                if not v or v.startswith(("—", "not ", "n.r.", "no result", "held", "on file")):
                    continue
                col = c.font.color.rgb[-6:] if c.font.color and isinstance(c.font.color.rgb, str) else None
                is_red, is_amber = col == "9C0006", col == "B45F06"
                over, und = T.over_limit(sub, v), T.undetermined(sub, v)
                if over and not is_red:
                    bad2(TRACKER, f"over the criterion but not marked ({sub})", f"{cu}/{p}: {v!r}")
                if is_red and not over:
                    bad2(TRACKER, f"marked out of specification but within it ({sub})", f"{cu}/{p}: {v!r}")
                if und and not (is_amber or is_red):
                    bad2(TRACKER, f"undetermined but not marked ({sub})", f"{cu}/{p}: {v!r}")

# ---- 11. identification C names a certificate that reports Total THC for the lot
# The "Ident C — covered by (eCoA)" column moved from iCoA Issuance to the iCoA
# Register with the fold of 14.09.2026; the check follows the column.
# a certificate carries the cannabinoid assay when it reports the total, or the free acid pair
# it is computed from (Δ⁹-THC + THCA × 0.877), which is how the CNP certificates print it
ASSAY = {"total_thc", "thc_free", "thca", "delta9_thc"}
thc_codes = set()
for r in recs:
    if any(x.get("parameter") in ASSAY and x.get("result_printed") for x in r.get("parameters", [])):
        thc_codes.add(T.nkey(str(r.get("cert_code") or "")))
for r, d in table(WV, "iCoA Register"):
    c = str(d.get("Ident C — covered by (eCoA)") or "")
    if c.startswith("—") or not c:
        continue
    code = T.nkey(c.split(",")[0])
    if by_code.get(code) and code not in thc_codes:
        bad2("iCoA Register", "identification C cites a certificate whose record reports no Total THC", f"row {r}: {c[:40]}")

# ---- 12. the registers: the group and the rule that dates it
# The legacy day is read off the workbook rather than pinned here. It is a ruling
# and rulings change — it moved from 15.05/27.05.2026 to 03.06/06.06.2026 on
# 10.09.2026 — and a literal in the checker means the same decision lives in two
# files and one of them is always the stale one. Taking the day the legacy rows
# agree on turns this into the stronger check anyway: that they agree at all.
def _legacy_day(rows, flagged=()):
    from collections import Counter
    seen = Counter(fmt(d["Issue date (planned)"]) for d in rows.values()
                   if d["No."] and str(d["Group"]) == "legacy"
                   and str(d["Series"]) == "initial release"
                   and fmt(d["Issue date (planned)"])
                   and not any(w in str(d["Status"]) for w in flagged))
    return seen.most_common(1)[0][0] if seen else None


_coq_day = _legacy_day(cqv, ("held", "moved"))
for r, d in cqv.items():
    if not d["No."]:
        continue
    grp, a = str(d["Group"]), fmt(d["Issue date (planned)"])
    # the release round only: a legacy lot's reissue is dated by its own retest
    # certificates and its campaign's internal certificate (15.09.2026)
    if grp == "legacy" and a and _coq_day and a != _coq_day and str(d["Series"]) == "initial release":
        st = str(d["Status"])
        if "held" not in st and "moved" not in st:
            bad2("CoQ Register", f"a legacy CoQ not on the legacy day {_coq_day} and not flagged",
                 f"{d['P Batch']}: {a}")
_reg_day = _legacy_day(regv)
for r, d in regv.items():
    if not d["No."]:
        continue
    grp, a = str(d["Group"]), fmt(d["Issue date (planned)"])
    # Only the RELEASE round. A legacy lot is one packed before the specification
    # SOP, so its release certificate is back-dated to the SOP's day — but its
    # retest is tested at a sampling in July or August 2026 and is issued then,
    # which is the ruling ("issued that day, or 03.06.2026 if that day is before
    # the SOP"), not a violation of it. The retest rounds only reached this sheet
    # on 11.09.2026, and the check had never had to say which round it meant.
    if grp == "legacy" and _reg_day and a != _reg_day and str(d["Series"]) == "initial release":
        bad2("iCoA Register", f"a legacy iCoA not on the legacy day {_reg_day}", f"{d['P Batch']}: {a}")

# ---- 13. Mikro CoQ Parameter against the tracker
# This check did nothing. Its body was `for cu, p in LOTS: pass`, and it was guarded on a
# SHEET name that stopped existing when the fold of 14.09.2026 made the sheet a section of
# Reference — so from v26 to v33 it was skipped entirely while appearing to pass. Found
# 16.09.2026. It now does what it says: every value the owner's microbiology sheet prints
# is compared with the tracker's cell for the same lot and determination.
_MIK = {10: "9.1", 11: "9.2", 12: "9.3", 13: "9.4", 14: "9.5",
        16: "10.1", 17: "10.2", 18: "10.3", 20: "11.1", 21: "11.2", 22: "11.3", 23: "11.4"}
_REFLINE = re.compile(r"^.+,\s*\(\d{2}\.\d{2}\.\d{4}\)\s*\[")   # a reference, not a result


def _not_a_value(v):
    """The sheet writes each group's REFERENCE in the first sub-column of the block's second
    row — a citation where one exists, else a placeholder. Neither is a result, and a
    placeholder on the value side ("— MISSING —") is the absence of one."""
    s = str(v or "").strip()
    return (not s) or s.startswith("\u2014") or _REFLINE.match(s) is not None
try:
    _mk = sheet_or_section(WV, "Mikro CoQ Parameter")
except Exception:
    _mk = None
if _mk is None:
    bad2("Mikro CoQ Parameter", "neither a sheet nor a Reference section", "")
else:
    _trk = {}
    for (_cu, _p), _lot in LOTS.items():
        _k = T.batch_key(_p) if _p and not _p.startswith(("N/A", "\u2014")) else T.cu_key(_cu)
        _a = _lot["row"]
        for _n, (_s0, _e) in PCOL.items():
            _subs = T.GROUPS.get(_n) or [str(_n)]
            _single = (_e - _s0) <= 2
            for _r in range(_a, _a + 40, 2):
                if _r > WV[TRACKER].max_row:
                    break
                for _j, _sub in enumerate(_subs):
                    _v = WV[TRACKER].cell(_r, _s0 + (0 if _single else _j)).value
                    if _not_a_value(_v):
                        continue
                    _trk.setdefault((_k, _sub), set()).add(str(_v).strip())
    _anch = [r for r in range(5, _mk.max_row + 1) if _mk.cell(r, 1).value]
    _seen = _diff = 0
    for _i, _a in enumerate(_anch):
        _nxt = _anch[_i + 1] if _i + 1 < len(_anch) else _mk.max_row + 1
        _cu = str(_mk.cell(_a, 1).value or "")
        _p = str(_mk.cell(_a, 2).value or "")
        _k = T.batch_key(_p) if _p and not _p.startswith(("N/A", "\u2014")) else T.cu_key(_cu)
        for _r in range(_a, _nxt):
            for _c, _det in _MIK.items():
                _v = _mk.cell(_r, _c).value
                if _not_a_value(_v):
                    continue
                _seen += 1
                _have = _trk.get((_k, _det))
                if not _have:
                    _diff += 1
                    bad2("Mikro CoQ Parameter", "a value the tracker has no cell for (#%s)" % _det,
                         "%s/%s: %r" % (_cu, _p, str(_v)[:30]))
                elif str(_v).strip() not in _have:
                    _diff += 1
                    bad2("Mikro CoQ Parameter", "differs from the tracker (#%s)" % _det,
                         "%s/%s: sheet %r, tracker %s" % (_cu, _p, str(_v)[:24], sorted(_have)[:2]))
    if not _anch:
        bad2("Mikro CoQ Parameter", "no lots on the sheet", "")
    print("   Mikro CoQ Parameter: %d value(s) compared with the tracker, %d differing" % (_seen, _diff))

print()
print(f"deeper checks: {checked} printed result(s) compared with the certificate records; {len(FIND2)} finding(s)")
for s, w, d in FIND2:
    print(f"  [{s}] {w}" + (f" — {d}" if d else ""))

# The exit code, which this never had: it printed its findings and exited 0, so
# nothing could gate on it and no workflow ran it. A verifier that cannot fail is
# a report, not a check — and on 11.09.2026 it reported that the iCoA series is
# numbered twice with 49 of 49 comparable rows disagreeing, while CI stayed green.
if FIND or FIND2:
    print()
    print("FAILED: %d finding(s) on the sheets, %d in the deeper checks"
          % (len(FIND), len(FIND2)))
    sys.exit(1)
print()
print("workbook verified: no findings")
sys.exit(0)
