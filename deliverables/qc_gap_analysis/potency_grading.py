#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Which potency grade a Total Δ9-THC result falls in, and the codes that follow from it.

    python3 deliverables/qc_gap_analysis/potency_grading.py     # self-test + a census over the record

Owner, 15.09.2026: for every certificate of quality of every batch, determine under
which grade — nominal, tolerance, specification window — the batch's Total Δ9-THC
result falls, state it beside the certificate, and generate the product code and the
specification document code from it.

The grades are the Head of QC's potency specification of 15.09.2026
(`potency_grades.py`, one row per strain and grade). Three rules, each the convention
the issued documents already use (product_specifications_QCSP001.json, 48 issued
specifications):

* **The strain is read off the batch code**: its letters before the first digit are the
  strain's abbreviation (BSS1024 → BSS, J31122501 → J31). Where the batch is named by
  its P lot alone, or the prefix is not an abbreviation the specification knows
  (OMP1024_01), the strain name decides, through the tracker's strain rulings and the
  spellings the record carries.
* **The grade is the window the result falls in**, nominal − tolerance to nominal +
  tolerance as the specification prints them. A result in no window is graded to the
  nearest window and says so — a fact for the Head of QC, not a certificate.
* **Product code** `{ABBR}_THC{nominal} : CBD1` and **specification document code**
  `QCSP_001_{ABBR}-{grade numeral}_v.NN`, the numeral ranking the strain's grades from
  the highest nominal (I) down — the issued convention (Cap Junky: I = 28, II = 26 …).
  Owner, 15.09.2026: every grade, nominal, tolerance and range already in the issued
  specifications and on the certificates is old and potentially wrong; the specification
  of 15.09.2026 is used exactly, everywhere — and there is no second version: every
  specification document code is v.01, because the initially issued ones were wrong and
  this is not the official issuing of the document; the set goes for review. The status
  beside each code records, for that review, what the v.01 already issued under the same
  strain and numeral printed.
"""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.join(HERE, "tracker") not in sys.path:
    sys.path.insert(0, os.path.join(HERE, "tracker"))
GRADES_CSV = os.path.join(HERE, "potency_grades_2026-09-15.csv")
SPEC_JSON = os.path.join(HERE, "product_specifications_QCSP001.json")
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]

# the record's spellings that are not the specification's, squashed (lower, no spaces)
_ALIAS = {"cupjunky": "CJ", "capjunkie": "CJ", "capjunky": "CJ", "jellydonutz": "JD", "jellydonuts": "JD",
          "weddingcrasher": "WC", "weddingcrusher": "WC", "permanentmarket": "PM", "permanentmarker": "PM",
          "sleepyjoy": "SJ", "sleepyjoe": "SJ", "grapesandcream": "GRC", "gg4": "GG", "gorillaglue": "GG"}

_G, _NAMES, _ISSUED, _BY_PCODE = None, None, None, None


def _load():
    global _G, _NAMES, _ISSUED
    if _G is not None:
        return
    _G, _NAMES = {}, {}
    with open(GRADES_CSV, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            _G.setdefault(r["abbr"], []).append({"nominal": float(r["nominal"]), "tol": float(r["tolerance"]),
                                                 "lo": float(r["window_low"]), "hi": float(r["window_high"]),
                                                 "strain": r["strain"]})
            _NAMES[_squash(r["strain"])] = r["abbr"]
    for abbr, gs in _G.items():
        gs.sort(key=lambda g: -g["nominal"])
        for i, g in enumerate(gs):
            g["roman"] = ROMAN[i]
    global _BY_PCODE
    _ISSUED, _BY_PCODE = {}, {}
    if os.path.exists(SPEC_JSON):
        for lot, s in json.load(open(SPEC_JSON, encoding="utf-8")).get("specifications", {}).items():
            if s.get("spec_doc_code"):
                _ISSUED.setdefault(s["spec_doc_code"], s.get("product_code", ""))
                _BY_PCODE.setdefault(s.get("product_code", ""), (s["spec_doc_code"], s.get("thc_criterion", "")))


def _squash(s):
    return re.sub(r"[^a-z0-9]", "", str(s or "").lower())


def abbr_of(cb, strain=""):
    """The strain's abbreviation from the batch code, else from the strain name.

    >>> abbr_of("BSS1024"), abbr_of("J31122501"), abbr_of("GRC102501/1"), abbr_of("OMP1024_01", "Orange Punch Mimosa")
    ('BSS', 'J31', 'GRC', 'OPM')
    >>> abbr_of("P060332", "CashCow"), abbr_of("P160012", "Cup Junky"), abbr_of("X999", "nobody") is None
    ('CC', 'CJ', True)
    """
    _load()
    m = re.match(r"^([A-Z]+\d*)", str(cb or "").strip())
    if m and not str(cb).startswith("P0") and not str(cb).startswith("P1"):
        head = m.group(1)
        for n in range(len(head), 0, -1):
            if head[:n] in _G:
                return head[:n]
    k = _squash(strain)
    if k in _NAMES:
        return _NAMES[k]
    if k in _ALIAS:
        return _ALIAS[k]
    try:
        import strains as ST
        k2 = _squash(ST.canonical(strain))
        if k2 in _NAMES:
            return _NAMES[k2]
        if k2 in _ALIAS:
            return _ALIAS[k2]
    except Exception:
        pass
    return None


def number(res):
    """The Total THC figure inside a printed result, or None.

    >>> number("25.01"), number("21.03 % w/w"), number("< LOQ"), number("—"), number("")
    (25.01, 21.03, None, None, None)
    """
    m = re.search(r"\d+(?:[.,]\d+)?", str(res or ""))
    if not m or str(res).strip().startswith(("<", "≤")):
        return None
    return float(m.group(0).replace(",", "."))


def grade_of(abbr, thc):
    """The grade a result falls in — or the nearest, with a note.

    >>> g = grade_of("BSS", 25.01); g["nominal"], g["roman"], g["note"]
    (24.0, 'II', '')
    >>> g = grade_of("BSS", 21.03); g["nominal"], g["lo"], g["hi"]
    (20.0, 18.11, 21.88)
    >>> g = grade_of("CJ", 29.9); g["nominal"], g["note"]
    (28.0, 'above the highest window (26.40 – 29.59): graded to the nearest')
    >>> grade_of("ZZZ", 10) is None
    True
    """
    _load()
    gs = _G.get(abbr)
    if not gs or thc is None:
        return None
    for g in gs:
        if g["lo"] <= thc <= g["hi"]:
            return dict(g, note="")
    near = min(gs, key=lambda g: min(abs(thc - g["lo"]), abs(thc - g["hi"])))
    if thc > gs[0]["hi"]:
        note = "above the highest window (%.2f – %.2f): graded to the nearest" % (gs[0]["lo"], gs[0]["hi"])
    elif thc < gs[-1]["lo"]:
        note = "below the lowest window (%.2f – %.2f): graded to the nearest" % (gs[-1]["lo"], gs[-1]["hi"])
    else:
        note = "between two windows: graded to the nearest (%.2f – %.2f)" % (near["lo"], near["hi"])
    return dict(near, note=note)


def product_code(abbr, nominal):
    """The product code a grade implies.

    >>> product_code("BSS", 24.0)
    'BSS_THC24 : CBD1'
    """
    return "%s_THC%d : CBD1" % (abbr, round(nominal))


def spec_code(abbr, roman, pcode, lo=None, hi=None):
    """The specification document code — always v.01 — and what it stands against.

    Owner, 15.09.2026: no second version. Every specification document is v.01,
    because the initially issued ones were wrong and this is not the official issuing
    of the document — the set goes for review. The status records, for that review,
    what the v.01 already issued under the same strain and numeral printed.

    >>> spec_code("BSS", "II", "BSS_THC24 : CBD1", 21.89, 26.10)
    ('QCSP_001_BSS-II_v.01', 'for review — replaces the issued QCSP_001_BSS-II_v.01 (was BSS_THC20 : CBD1, 18.00 – 22.00 %); now BSS_THC24 : CBD1 21.89 – 26.10 %')
    >>> spec_code("ZZ", "I", "ZZ_THC10 : CBD1", 9.0, 10.99)
    ('QCSP_001_ZZ-I_v.01', 'for review — new')
    """
    _load()
    code = "QCSP_001_%s-%s_v.01" % (abbr, roman)
    win = "%.2f – %.2f %%" % (lo, hi) if lo is not None else ""
    if code in _ISSUED:
        was_pcode = _ISSUED[code]
        was_crit = _BY_PCODE.get(was_pcode, ("", ""))[1]
        if was_pcode == pcode and _same_window(was_crit, lo, hi):
            return code, "for review — same as issued (%s)" % was_crit
        return code, "for review — replaces the issued %s (was %s, %s); now %s %s" % (code, was_pcode, was_crit, pcode, win)
    return code, "for review — new"


def _same_window(crit, lo, hi):
    """Does an issued criterion print this window?

    >>> _same_window("22.01 – 25.99 %", 22.01, 25.99), _same_window("22.01 – 25.99 %", 21.89, 26.10)
    (True, False)
    """
    m = re.findall(r"\d+\.\d+", str(crit or ""))
    return len(m) >= 2 and lo is not None and abs(float(m[0]) - lo) < 0.005 and abs(float(m[1]) - hi) < 0.005


def grading(cb, strain, res):
    """Everything the register prints for one certificate's Total THC result.

    >>> g = grading("BSS1024", "Blue Sunset Sherbet", "25.01")
    >>> g["abbr"], g["thc"], g["grade"], g["window"], g["product_code"], g["spec_code"], g["spec_status"][:5]
    ('BSS', 25.01, '24.00 ± 2.11 (II)', '21.89 – 26.10 %', 'BSS_THC24 : CBD1', 'QCSP_001_BSS-II_v.01', 'for r')
    >>> grading("BSS1024", "Blue Sunset Sherbet", "—")["note"]
    'no Total THC result on this certificate'
    """
    out = {"abbr": abbr_of(cb, strain), "thc": number(res), "grade": "", "window": "", "product_code": "",
           "spec_code": "", "spec_status": "", "note": ""}
    if not out["abbr"]:
        out["note"] = "strain not in the potency specification of 15.09.2026"
        return out
    if out["thc"] is None:
        out["note"] = "no Total THC result on this certificate"
        return out
    g = grade_of(out["abbr"], out["thc"])
    if not g:
        out["note"] = "no grades for %s in the specification" % out["abbr"]
        return out
    out["grade"] = "%.2f ± %.2f (%s)" % (g["nominal"], g["tol"], g["roman"])
    out["window"] = "%.2f – %.2f %%" % (g["lo"], g["hi"])
    out["product_code"] = product_code(out["abbr"], g["nominal"])
    out["spec_code"], out["spec_status"] = spec_code(out["abbr"], g["roman"], out["product_code"], g["lo"], g["hi"])
    out["nominal"], out["tol"], out["lo"], out["hi"], out["roman"] = g["nominal"], g["tol"], g["lo"], g["hi"], g["roman"]
    out["note"] = g["note"]
    return out


def main(argv):
    import doctest
    fail, ran = doctest.testmod()
    print("%d doctests, %d failed" % (ran, fail))
    if fail:
        return 1
    from collections import Counter
    d = json.load(open(os.path.join(HERE, "coq_artifact_data.json"), encoding="utf-8"))
    st, notes = Counter(), Counter()
    for c in d["coqs"]:
        r4 = next((r for r in c["rows"] if r["no"] == "4"), None)
        g = grading(c["cb"], c["strain"], r4["res"] if r4 else "")
        st[g["spec_status"] or ("— " + g["note"])] += 1
        if g["note"] and g["grade"]:
            notes[(c["cb"], c["t"][:7], g["thc"], g["note"][:40])] += 1
    print("  %d certificates of quality graded:" % len(d["coqs"]))
    for k, v in st.most_common():
        print("    %3d  %s" % (v, k))
    if notes:
        print("  results in no window (graded to the nearest):")
        for k in sorted(notes):
            print("    ", k)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
