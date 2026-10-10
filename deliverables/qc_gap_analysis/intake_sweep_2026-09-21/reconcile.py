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
# Cyrillic letters that are drawn like Latin ones. A laboratory writes TAMC and TYMC in a
# Macedonian sentence and either alphabet's letters may come back from a reader — Ү (U+04AE)
# for Y is the one that cost six holds on the microbiology panels of 21.09.2026.
CYR = {"А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P",
       "С": "C", "Т": "T", "У": "Y", "Х": "X", "Ј": "J", "І": "I",
       "Ү": "Y", "ү": "y", "Ѕ": "S", "ѕ": "s", "Ғ": "F", "Һ": "H"}
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


# The Macedonian alphabet to Latin, for a parameter's NAME only. A laboratory prints
# "вкупно DDT" and one reader copies the Cyrillic while the other transliterates it; both
# mean the same row of the same table. This is never applied to a result or to a document
# code — the desk's standing rule is that a laboratory's code is printed exactly as its
# register holds it, and transliterating one would be a claim about someone else's record.
MK2LAT = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ѓ": "g", "е": "e", "ж": "z",
          "з": "z", "ѕ": "s", "и": "i", "ј": "j", "к": "k", "л": "l", "љ": "l", "м": "m",
          "н": "n", "њ": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "ќ": "k",
          "у": "u", "ф": "f", "х": "h", "ц": "c", "ч": "c", "џ": "d", "ш": "s"}


def name_key(v):
    """A parameter's IDENTITY, folded harder than its value.

    fold() is the gate's comparison for a RESULT and must stay strict: "< 10²" and
    "< 10^1" are different assertions. A parameter NAME is not an assertion, it is which
    row of the page this is, and the two vendors transcribe it with small differences that
    say nothing — "Вкупно Δ9-Tetrahydrocannabinol" against "Вкупно Δ9- Tetrahydrocannabinol",
    "4,4' DDE" against "4.4' DDE". Matching rows on that punctuation makes a hold out of a
    space. So the name key drops every space and separator; the value it carries is still
    compared character for character.
    """
    t = re.sub(r"[\s.,'\u2019\u02bc/()\-\u2010\u2011\u2012\u2013\u2014\u2212]+", "", fold(v))
    return "".join(MK2LAT.get(c, c) for c in t)


def rows(rec, alias=None):
    """Index a read's parameters by the name the PAGE prints.

    The runner gives every row two names: `parameter_printed`, transcribed from the page,
    and `parameter`, a normalised key from its own controlled list. Keying on the
    normalised key made a disagreement out of nothing on 328/2026 — one vendor filed the
    Institute's 29 residues under `pesticide_residues` and the other under `other`, while
    both transcribed the same 28 printed names and, on every one of them, the same result.
    Sixty-one holds, not one of which was about a value.

    So the index is the printed name, which is what this gate compares everywhere else and
    what the page can actually be held against. The normalised key is a reader's opinion
    about which determination a row belongs to; that mapping is the desk's to make, once,
    in the apply — not something two readers must agree on before a figure can be taken.
    """
    out = collections.OrderedDict()
    for p in rec.get("parameters") or []:
        # A row with NO result in this read contributes nothing and cannot be reconciled
        # against anything: it is not a figure one reader has and the other missed, it is
        # a label. Both vendors raised three such rows out of the Farmahem report's title
        # ("Идентификација и квантификација на канабиноиди") with a null result, and
        # holding them made six findings out of a page the two read identically.
        if str(p.get("result_printed") or "").strip() in ("", "None", "null"):
            continue
        printed = str(p.get("parameter_printed") or "").strip()
        # The page prints some names bilingually — "Вкупен Cannabidiol / Total CBD". One
        # reader transcribed both halves and the other only the first, which is a
        # difference in how much of the label was copied, not in what was measured. The
        # key is the first half. The separator must be a spaced slash, so a name that
        # carries one inside itself ("Идентификација C (HPLC/DAD)") is left whole.
        printed = re.split(r"\s+/\s+", printed)[0].strip() or printed
        name = name_key(re.sub(r"^\s*\*+|\*+\s*$", "", printed or str(p.get("parameter") or "")))
        name = (alias or {}).get(name, name)
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
        # A third read may settle that two differently-spelled labels are the same row of
        # the same table, naming the page's own spelling first. Applied to the index only:
        # it decides WHICH ROW this is, never what the row says.
        alias = {}
        for canon, spellings in ((C.get(scan) or {}).get("name_aliases") or {}).items():
            if canon.startswith("_"):
                continue
            for sp in spellings:
                alias[name_key(sp)] = name_key(canon)
        ra, rb = rows(a, alias), rows(b, alias)
        if alias:
            settled += 1
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
