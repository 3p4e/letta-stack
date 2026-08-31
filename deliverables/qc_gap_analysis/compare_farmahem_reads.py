# -*- coding: utf-8 -*-
"""Compare the Farmahem page readings against the register.

Two normalisations that are not laxity:

`<LOQ**` on the page and `< LOQ (<0.20)` in the register are the same statement. The
certificate defines its own footnote — `<LOQ** - под лимит на квантификација (<0.20%)`
— and the register has expanded it inline. That is more informative than the page, not
less, and treating it as a difference would bury the one difference that matters.

`±0.71` and `0.71` in the uncertainty column likewise differ only in how the
laboratory chose to print the sign that year.
"""
import json, re, sys

S = "/tmp/claude-0/-home-user-letta-stack/4877ce6e-ae82-551e-bf35-5698c379c3be/scratchpad"
man = json.load(open(S + "/fhm/manifest.json", encoding="utf-8"))
rd = json.load(open(S + "/fhm/reads.json", encoding="utf-8"))

KEY = {"thc": "THC %", "cbd": "CBD %", "cbn": "CBN %",
       "afla": "Aflatoxins Σ µg/kg", "aflab1": "Aflatoxin B1 µg/kg",
       "ota": "Ochratoxin A µg/kg", "lod": "Loss on drying %"}


def norm(v):
    s = str(v or "").strip().lower().replace(" ", "").replace("*", "").replace("±", "")
    s = re.sub(r"\(<?0?\.?20%?\)$", "", s)          # the register's inline LOQ footnote
    if s.startswith("<loq"): return "<loq"
    if s in ("nd", "n.d.", "н.д.", "нд"): return "nd"
    return s


tot = ok = 0
bad = []
for k, r in sorted(rd.items(), key=lambda kv: man[kv[0]]["row"]):
    m = man[k]
    for f, col in KEY.items():
        reg, page = m["vals"].get(col), r.get(f)
        if page is None or reg is None: continue
        agree = norm(page) == norm(reg)
        tot += 1; ok += agree
        if not agree:
            isU = norm(reg) == norm((r.get("u") or {}).get(f))
            bad.append((m["code"], m["row"], m["batch"], col, str(page), str(reg),
                        "IS THE U COLUMN" if isU else ""))

print(f"{len(rd)} of 63 certificates read")
print(f"{ok}/{tot} register values agree" + (f" ({100*ok/tot:.1f}%)" if tot else ""))
for b in bad: print("  DIFFERS:", b)
