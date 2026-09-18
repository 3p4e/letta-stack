#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The two-read gate for the contaminant intake of 18.09.2026.

    python3 reconcile.py

Sixty-five scans of the laboratories' contaminant panels — heavy metals, mycotoxins and
pesticide residues — were transcribed twice, by two readers who could not see each other's
work. This compares the two transcriptions document by document and value by value.

A value passes the gate only when BOTH readers wrote the same thing. Anything the two
readers disagree about, and anything either of them could not read, is held and named: the
desk does not take a laboratory figure on one reading, and it does not average two.

The comparison is on the printed string, not on a parsed number, because the printed form
carries meaning the number loses — "н.д." and "< 0,01" and "< 2" are different assertions
and the certificate must be able to say which one the laboratory made. Only presentation
is folded: surrounding space, the decimal comma against the point, and Cyrillic homoglyphs
in a Latin word.
"""
import collections
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
READS = "/tmp/claude-0"
CYR = {"А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P",
       "С": "C", "Т": "T", "У": "Y", "Х": "X", "Ј": "J", "І": "I"}


def fold(v):
    """One spelling for comparison: space, decimal mark and Cyrillic look-alikes."""
    s = str(v if v is not None else "").strip()
    s = "".join(CYR.get(c, c) for c in s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"(?<=\d),(?=\d)", ".", s)
    return s.lower()


def key_of(rec):
    """A document is identified by its own number, not by the file it came in."""
    return fold(rec.get("doc_code") or rec.get("scan"))


def params(rec):
    out = collections.OrderedDict()
    for i, p in enumerate(rec.get("parameters") or []):
        name = fold(p.get("name"))
        k = (name, out and sum(1 for x in out if x[0] == name) or 0)
        while k in out:
            k = (name, k[1] + 1)
        out[k] = p
    return out


def load(pass_letter):
    recs = {}
    for f in sorted(glob.glob(os.path.join(READS, "read%s_*.json" % pass_letter))):
        for rec in json.load(open(f, encoding="utf-8")):
            k = key_of(rec)
            if k in recs:                      # the same scan reached two slices
                continue
            recs[k] = rec
    return recs


def main():
    A, B = load("A"), load("B")
    both = sorted(set(A) & set(B))
    only = sorted(set(A) ^ set(B))
    agreed, held = {}, []
    for k in both:
        a, b = A[k], B[k]
        for field in ("doc_code", "issue_date", "receipt_date", "batch", "sample"):
            if fold(a.get(field)) != fold(b.get(field)):
                held.append((k, field, a.get(field), b.get(field)))
        pa, pb = params(a), params(b)
        rows = []
        for name in pa:
            if name not in pb:
                held.append((k, "parameter " + name[0], "present", "absent")); continue
            x, y = pa[name], pb[name]
            bad = [f for f in ("result", "limit", "unit") if fold(x.get(f)) != fold(y.get(f))]
            if bad:
                for f in bad:
                    held.append((k, "%s · %s" % (name[0], f), x.get(f), y.get(f)))
                continue
            rows.append({"name": x.get("name"), "limit": x.get("limit"),
                         "result": x.get("result"), "unit": x.get("unit"),
                         "method": x.get("method")})
        for name in pb:
            if name not in pa:
                held.append((k, "parameter " + name[0], "absent", "present"))
        unread = sorted(set(map(str, a.get("unreadable") or [])) |
                        set(map(str, b.get("unreadable") or [])))
        agreed[k] = {"doc_code": a.get("doc_code"), "issue_date": a.get("issue_date"),
                     "receipt_date": a.get("receipt_date"), "batch": a.get("batch"),
                     "sample": a.get("sample"), "laboratory": a.get("laboratory"),
                     "scan": a.get("scan"), "verdict": a.get("verdict"),
                     "pages_read": a.get("pages_read"), "unreadable": unread,
                     "parameters": rows}
    out = {"read_twice": len(both), "read_once": only,
           "documents": agreed,
           "held": [{"doc": h[0], "field": h[1], "read_A": h[2], "read_B": h[3]} for h in held]}
    json.dump(out, open(os.path.join(HERE, "two_read_result.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    vals = sum(len(v["parameters"]) for v in agreed.values())
    print("documents read twice: %d   read once: %d" % (len(both), len(only)))
    if only:
        for k in only[:10]:
            print("   only one reader: %s" % k)
    print("values agreed by both readers: %d" % vals)
    print("held — the readers differ or a field is unreadable: %d" % len(held))
    by = collections.Counter(h["doc"] for h in out["held"])
    for k, n in by.most_common(12):
        print("   %-14s %d" % (k, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
