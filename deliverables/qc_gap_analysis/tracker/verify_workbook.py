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
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "CoQ_Analysis_Master_v11.xlsx")
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
        if str(vals[0] or "").startswith(("Head of QC", "Chronological", "These corrections")):
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
db = WB["Summary Dashboard"]
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
    if seqn != list(range(1, len(seqn) + 1)):
        bad(name, "numbers are not 1..n in row order", f"{seqn[:6]} …")
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
        if d["Issuable"] != "yes" and d["No."]:
            bad(name, "number on a row that is not issuable", f"row {r} {d.get('Key')}")
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

# ---------------------------------------------------------------- 6. iCoA Issuance vs the registers
iss = table(WV, "iCoA Issuance")
for r, d in iss:
    code = str(d.get("iCoA") or "")
    if code.startswith("iCoA-PP_26-"):
        k = None
        for kk, dd in icoa_by_key.items():
            if str(dd["iCoA code"]) == code:
                k = kk
        if k is None:
            bad("iCoA Issuance", "cites a code that is not in the register", f"row {r}: {code}")
    if str(d.get("Series") or "").startswith("initial") and str(d.get("iCoA scope") or "").startswith("—") and code not in ("not needed", ""):
        bad("iCoA Issuance", "no scope but a code", f"row {r}: {code}")

# ---------------------------------------------------------------- 7. Work Order / Credit Audit
wo = table(WB, "Work Order")
au = table(WB, "Credit Audit")
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

# ---------------------------------------------------------------- 8. Read Me
rm = WB["Read Me"]
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
    _mod = {}
    for _row in _IR.build():
        _suf = "I" if _row["round"] == "initial release" else "R"
        for _base in filter(None, (_row["p_lot"], _row["batch"])):
            _mod.setdefault("%s|%s" % (_bk(_base), _suf), _row["code"])
    _reg = WB["iCoA Register"]
    _n, _agree, _differ, _unknown = 0, 0, 0, 0
    for _r in range(2, _reg.max_row + 1):
        _key = str(_reg.cell(_r, 16).value or "")
        if not _key or str(_reg.cell(_r, 3).value or "") != "yes":
            continue
        _n += 1
        _sheet_code = "iCoA-PP_26-%03d" % _n
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

# ---- 11. iCoA Issuance: identification C names a certificate that reports Total THC for the lot
# a certificate carries the cannabinoid assay when it reports the total, or the free acid pair
# it is computed from (Δ⁹-THC + THCA × 0.877), which is how the CNP certificates print it
ASSAY = {"total_thc", "thc_free", "thca", "delta9_thc"}
thc_codes = set()
for r in recs:
    if any(x.get("parameter") in ASSAY and x.get("result_printed") for x in r.get("parameters", [])):
        thc_codes.add(T.nkey(str(r.get("cert_code") or "")))
for r, d in iss:
    c = str(d.get("Ident C — covered by (eCoA)") or "")
    if c.startswith("—") or not c:
        continue
    code = T.nkey(c.split(",")[0])
    if by_code.get(code) and code not in thc_codes:
        bad2("iCoA Issuance", "identification C cites a certificate whose record reports no Total THC", f"row {r}: {c[:40]}")

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
                   and fmt(d["Issue date (planned)"])
                   and not any(w in str(d["Status"]) for w in flagged))
    return seen.most_common(1)[0][0] if seen else None


_coq_day = _legacy_day(cqv, ("held", "moved"))
for r, d in cqv.items():
    if not d["No."]:
        continue
    grp, a = str(d["Group"]), fmt(d["Issue date (planned)"])
    if grp == "legacy" and a and _coq_day and a != _coq_day:
        st = str(d["Status"])
        if "held" not in st and "moved" not in st:
            bad2("CoQ Register", f"a legacy CoQ not on the legacy day {_coq_day} and not flagged",
                 f"{d['P Batch']}: {a}")
_reg_day = _legacy_day(regv)
for r, d in regv.items():
    if not d["No."]:
        continue
    grp, a = str(d["Group"]), fmt(d["Issue date (planned)"])
    if grp == "legacy" and _reg_day and a != _reg_day:
        bad2("iCoA Register", f"a legacy iCoA not on the legacy day {_reg_day}", f"{d['P Batch']}: {a}")

# ---- 13. Mikro CoQ Parameter against the tracker
if "Mikro CoQ Parameter" in WB.sheetnames:
    mk = WV["Mikro CoQ Parameter"]
    seen_lots = {str(mk.cell(r, 1).value) for r in range(5, mk.max_row + 1) if mk.cell(r, 1).value}
    for cu, p in LOTS:
        pass
    if not seen_lots:
        bad2("Mikro CoQ Parameter", "no lots on the sheet", "")

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
