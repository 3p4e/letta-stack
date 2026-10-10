#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The two-read gate for the gap intake of 21.09.2026.

    python3 reconcile.py

Seven pages the desk had never read, each one behind a cell that a certificate of quality
prints empty: six microbiological panels of the Institute of Public Health and one
Farmahem cannabinoid report. Each page was read twice, by two different vendors' models —
read A on OpenAI's, read B on Google's, neither seeing the other's answer, never the same
engine twice.

A value passes only where both reads wrote the same thing. The comparison is on the
PRINTED string, because the printed form carries meaning a parsed number loses: "< 10",
"< 10² и > 10" and "Отсутна" are three different assertions and the certificate has to be
able to say which one the laboratory made. Only presentation is folded — space, the
decimal comma, the multiplication sign, Cyrillic look-alikes in a Latin word, the unit,
and the superscript against the caret, because `10⁴` and `10^4` and `104` are one number
written three ways by a text layer that flattens exponents. That flattening is exactly
what a second read exists to catch, and it is why a magnitude that disagrees is HELD
rather than guessed: an exponent read wrong is a microbiological result wrong by a factor
of ten.
"""
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CYR = {"А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P",
       "С": "C", "Т": "T", "У": "Y", "Х": "X", "Ј": "J", "І": "I"}
SUP = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5",
       "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9"}


def parse(raw):
    t = str(raw or "").strip()
    t = re.sub(r"^```(?:json)?|```$", "", t, flags=re.M).strip()
    try:
        return json.loads(t)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", t)
        return json.loads(m.group(0)) if m else None


def fold(v):
    """One spelling for comparison. Notation only — never what is stored."""
    s = str(v if v is not None else "").strip()
    s = "".join(SUP.get(c, c) for c in s)
    s = "".join(CYR.get(c, c) for c in s)
    s = re.sub(r"\s*\^\s*", "", s)                       # 10^4 -> 104
    s = re.sub(r"\s*[x×·*]\s*10\s*", "x10", s, flags=re.I)
    s = re.sub(r"(?<=\d),(?=\d)", ".", s)
    s = re.sub(r"\s*(CFU\s*/\s*g|\bg\b|%\s*w/w|%|mg/kg|µg/kg)\s*", " ", s, flags=re.I)
    s = re.sub(r"^(отсу\w*|absent|не\s*е\s*детектирано)$", "absent", s.strip(), flags=re.I)
    s = re.sub(r"[<≤]\s*", "<", s)
    s = re.sub(r"[>≥]\s*", ">", s)
    s = re.sub(r"\s+(и|and)\s+", " и ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def rows(rec):
    out = collections.OrderedDict()
    for p in rec.get("parameters") or []:
        name = fold(re.sub(r"^\s*\*+|\*+\s*$", "", str(p.get("parameter") or p.get("parameter_printed") or "")))
        k, n = name, 0
        while k in out:
            n += 1
            k = "%s#%d" % (name, n)
        out[k] = p
    return out


def main():
    A = {r["scan"]: r for r in json.load(open(os.path.join(HERE, "reads_A.json"), encoding="utf-8"))}
    B = {r["scan"]: r for r in json.load(open(os.path.join(HERE, "reads_B.json"), encoding="utf-8"))}
    # Where the two reads disagreed, the desk read the page itself and said which one the
    # page supports. A third read settles ONE named field of ONE document and is recorded
    # with the region it was cut from, so it can be re-cut and disputed. It never invents
    # a value the page does not carry and it never averages the two.
    C = json.load(open(os.path.join(HERE, "reads_C.json"), encoding="utf-8"))
    settled = 0
    both = sorted(set(A) & set(B))
    docs, held = {}, []
    for scan in both:
        a, b = parse(A[scan]["raw"]), parse(B[scan]["raw"])
        if a is None or b is None:
            held.append({"doc": scan, "field": "the read itself", "read_A": a is not None,
                         "read_B": b is not None}); continue
        if A[scan]["sha256"] != B[scan]["sha256"]:
            held.append({"doc": scan, "field": "page", "read_A": A[scan]["sha256"][:12],
                         "read_B": B[scan]["sha256"][:12]}); continue
        for f in ("cert_code", "date_of_issue", "batch_canonical"):
            if fold(a.get(f)) == fold(b.get(f)):
                continue
            third = (C.get(scan) or {}).get(f)
            if third:
                a[f] = third["settled"]
                settled += 1
            else:
                held.append({"doc": scan, "field": f, "read_A": a.get(f), "read_B": b.get(f)})
        ra, rb = rows(a), rows(b)
        taken = []
        thirds = C.get(scan) or {}
        dropped = {p.strip() for key, v in thirds.items() if key.startswith("parameter ")
                   and v.get("settled") == "not on the page"
                   for p in key[len("parameter "):].split("/")}

        def _dropped(name):
            base = re.sub(r"#\d+$", "", name)
            return any(base == d or base.startswith(d.rstrip("_")) or d.endswith(base) for d in dropped)

        for k in ra:
            if k not in rb:
                held.append({"doc": scan, "field": "parameter " + k, "read_A": "present", "read_B": "absent"})
                continue
            x, y = ra[k], rb[k]
            va, vb = x.get("result_printed"), y.get("result_printed")
            if fold(va) != fold(vb):
                third = (C.get(scan) or {}).get("%s · result" % k)
                if third:
                    va = third["settled"]
                    settled += 1
                else:
                    held.append({"doc": scan, "field": "%s · result" % k, "read_A": va, "read_B": vb})
                    continue
            taken.append({"parameter": x.get("parameter"), "printed": x.get("parameter_printed"),
                          "result": va, "limit_A": x.get("limit_printed") or x.get("specification_printed"),
                          "unit": x.get("unit")})
        for k in rb:
            if k in ra:
                continue
            if _dropped(k):
                settled += 1
                continue
            held.append({"doc": scan, "field": "parameter " + k, "read_A": "absent", "read_B": "present"})
        docs[scan] = {"scan": scan, "sha256": A[scan]["sha256"], "pages": A[scan]["pages"],
                      "doc_code": a.get("cert_code"), "issue_date": a.get("date_of_issue"),
                      "receipt_date": a.get("date_of_receipt") or a.get("date_of_sampling"),
                      "batch": a.get("batch_canonical"), "strain": a.get("strain"),
                      "verdict": a.get("overall_conclusion"), "parameters": taken}
    out = {"read_twice": len(both), "read_once": sorted(set(A) ^ set(B)),
           "documents": docs, "held": held}
    json.dump(out, open(os.path.join(HERE, "two_read_result.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    vals = sum(len(v["parameters"]) for v in docs.values())
    print("documents read twice: %d   read once: %d" % (len(both), len(out["read_once"])))
    print("values agreed by both readers: %d" % vals)
    print("settled by a third read of the page (reads_C.json): %d" % settled)
    print("held — the readers differ or a field is unreadable: %d" % len(held))
    for h in held:
        print("   %-26s %-34s A=%-22r B=%r"
              % (h["doc"][:26], str(h["field"])[:34], h["read_A"], h["read_B"]))
    for k, v in sorted(docs.items()):
        print("\n%s  %s  %s  %s" % (k, v["doc_code"], v["issue_date"], v["batch"]))
        for p in v["parameters"]:
            print("     %-34s %s" % (str(p["printed"])[:34], p["result"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
