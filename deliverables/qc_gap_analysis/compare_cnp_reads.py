# -*- coding: utf-8 -*-
"""Compare the CNP page readings against the register.

`BLQ` on the page and `<LOQ` or `BLQ` in the register are the same statement — the
certificate defines BLQ in its own footnote as "под лимит на квантификација".
"""
import json, re

# Defaults are the committed copies, so the comparison can be re-run from the repo:
#   python3 deliverables/qc_gap_analysis/compare_cnp_reads.py [EXTRACT.json READS.json]
import sys
_D = "review/cnp_register_extract_2026-08-31.json", "review/cnp_page_reads_2026-08-31.json"
_ex, _rd = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else _D
man = json.load(open(_ex, encoding="utf-8"))
rd = json.load(open(_rd, encoding="utf-8"))

KEY = {"thc": "THC %", "cbd": "CBD %", "cbn": "CBN %", "lod": "Loss on drying %"}


def norm(v):
    s = str(v or "").strip().lower()
    # The register sometimes expands the certificate's own footnote inline —
    # `BLQ (below limit of quantification)` is what the page's `BLQ` plus its
    # footnote say together. That is the register being more informative than the
    # page, not disagreeing with it.
    s = re.sub(r"\s*\((?:below limit of quantification|not detected|под лимит[^)]*)\)", "", s)
    s = s.replace(" ", "").replace("%", "")
    s = re.sub(r"^(\d+),(\d+)$", r"\1.\2", s)
    if s in ("blq", "<loq", "bloq", "n.d.", "nd"): return "blq"
    # `0.10` and `0.1` are the same measurement written two ways: the page keeps the
    # laboratory's two decimals, the register drops a trailing zero. Compare numbers
    # as numbers, and fall back to the string only when it is not one.
    try:
        return f"{float(s):.4f}"
    except ValueError:
        return s


tot = ok = 0
bad = []
for k, r in sorted(rd.items(), key=lambda kv: man[kv[0]]["rows"][0]["row"]):
    for row in man[k]["rows"]:
        for f, col in KEY.items():
            reg, page = row["vals"].get(col), r.get(f)
            if page is None or reg is None: continue
            agree = norm(page) == norm(reg)
            tot += 1; ok += agree
            if not agree:
                bad.append((man[k]["code"], row["row"], row["batch"], col, str(page), str(reg)))

print(f"{len(rd)} of {len(man)} certificates read")
print(f"{ok}/{tot} register values agree" + (f" ({100*ok/tot:.1f}%)" if tot else ""))
for b in bad: print("  DIFFERS:", b)


# --- R4, the certificate's own arithmetic ----------------------------------------
# Every CNP page prints Δ9-THC, Δ9-THCA and Вкупно Δ9-THC, and its own footnote gives
# the relation between them: total = Δ9-THC + Δ9-THCA x 0.877, the THCA->THC mass
# ratio 314.46/358.47. So each certificate carries a proof of its own consistency,
# independent of the register. A page that fails this was misread by me or misprinted
# by the laboratory; either way it must not be used to correct anything.
def num(v):
    try: return float(str(v).replace(",", "."))
    except (TypeError, ValueError): return None

print()
r4ok = r4n = 0
for k, r in sorted(rd.items(), key=lambda kv: man[kv[0]]["rows"][0]["row"]):
    d9, thca, tot_ = num(r.get("d9")), num(r.get("thca")), num(r.get("thc"))
    if None in (d9, thca, tot_): continue
    calc = d9 + thca * 0.877
    good = abs(calc - tot_) <= 0.06
    r4n += 1; r4ok += good
    if not good:
        print(f"  R4 FAILS  {k}  {d9} + {thca} x 0.877 = {calc:.2f}  vs printed {tot_}")
print(f"R4: {r4ok}/{r4n} certificates internally consistent")
