#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phenotype, chemotype, processing and packaging, read off the issued specification.

    python3 deliverables/qc_gap_analysis/spec_attributes.py        # self-test + census
    python3 deliverables/qc_gap_analysis/spec_attributes.py --csv  # write the flat source

The certificate of quality carries four things the desk had been printing from the
master's worked specimen: the phenotype pill, the chemotype pill, the processing
pill and the primary-packaging line. None of them is a laboratory result and none
is in the release register — they are **product attributes, and the document that
states them is the issued QCSP 001 specification for that strain and grade**
(owner's ruling of 10.09.2026). That document is on file for every lot the desk
draws, so the values are read from it rather than assumed.

The specifications are PDFs generated from the company's own HTML, so they carry a
real text layer; this reads that layer. Nothing here is OCR — no page image is
looked at, and the policy chain in AGENT_MODEL_POLICY.md is untouched.

## How a tick is read

The specification does not print a ballot box. It prints all the options and sets
the selected one in cream on a filled pill, the rest in muted olive on the ground.
So the selection is a **colour**, and this module refuses to hard-code which
colour that is — a restyle would silently invert every certificate. It calibrates
per document instead:

  * the phenotype group prints three options, of which exactly one is selected, so
    the colour that appears **once** is the selected one and the colour that
    appears twice is not;
  * that reading is only accepted if the once-colour is the **lighter** of the two
    — cream on dark, never the other way round. Two ticked options would also
    produce a once-colour, and this is what catches it;
  * the colour so derived is then what selects in the two-option chemotype and
    processing groups, which cannot calibrate themselves.

A document whose phenotype group does not resolve that way is refused whole. It is
the same discipline as `cell_resolution.py`: a value that cannot be read the way
the document prints it is not printed at all.
"""
import csv
import html
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SPC = os.path.join(ROOT, "deliverables", "Final_Docs_PDF", "ImB_SPC")
OUT = os.path.join(HERE, "spec_attributes_2026-09-10.csv")
# BASE_SPCs is the issued set; the tranche folders are the copies handed out with
# each delivery. Both are read, and a disagreement between two copies of one
# document code is a finding rather than a winner.
FOLDERS = ["BASE_SPCs", "T1", "T2", "T3", "T1_rename", "RENs", "NEWs"]

GROUPS = {"phenotype": ["INDICA", "SATIVA", "HYBRID"],
          "chemotype": ["THC", "CBD"],
          "processing": ["MACHINE TRIMMED", "HAND TRIMMED"]}
_OPT_OF = {w: g for g, ws in GROUPS.items() for w in ws}
DOMINANCE = re.compile(r"\b(INDICA|SATIVA)\s*(\d+)\s*:\s*(INDICA|SATIVA)\s*(\d+)\b", re.I)
# The hybrid pill carries a dominance slot printed under it — either a ratio or the
# specification's own controlled blank, "TO BE DETERMINED". It is read by position
# rather than by pattern, so the blank is read as the blank it is.
_DOM_BELOW = (4, 22, 44)                          # min drop, max drop, max column drift
_PACK_LABEL = re.compile(r"^P\W*R\W*I\W*M\W*A\W*R\W*Y\b", re.I)
_TEXT = re.compile(r'<text top="(-?\d+)" left="(-?\d+)" width="-?\d+" height="-?\d+"'
                   r' font="(\d+)">(.*?)</text>')
_FONT = re.compile(r'<fontspec id="(\d+)" size="(-?\d+)" family="[^"]*" color="(#[0-9a-fA-F]{6})"/>')


def luminance(hexcolor):
    """Rec. 601 luma of a #rrggbb colour, 0-255.

    >>> round(luminance("#ffffff"))
    255
    >>> luminance("#f4efe3") > luminance("#ada383")
    True
    """
    r, g, b = (int(hexcolor[i:i + 2], 16) for i in (1, 3, 5))
    return 0.299 * r + 0.587 * g + 0.114 * b


def nodes(pdf):
    """Page one of the specification, as (text, colour, size, top, left) tuples."""
    xml = subprocess.run(["pdftohtml", "-xml", "-f", "1", "-l", "1", "-i", "-stdout", pdf],
                         capture_output=True).stdout.decode("utf-8", "replace")
    fonts = {m.group(1): (int(m.group(2)), m.group(3)) for m in _FONT.finditer(xml)}
    out = []
    for m in _TEXT.finditer(xml):
        txt = html.unescape(re.sub(r"<[^>]+>", "", m.group(4))).strip()
        size, colour = fonts.get(m.group(3), (0, "#000000"))
        out.append((txt, colour, size, int(m.group(1)), int(m.group(2))))
    return out


def selected_colour(opts):
    """The colour a tick is printed in, calibrated on the three phenotype options.

    ``opts`` maps the phenotype option word to its colour. Returns None when the
    group does not read as exactly one selection.

    >>> selected_colour({"INDICA": "#f4efe3", "SATIVA": "#ada383", "HYBRID": "#ada383"})
    '#f4efe3'
    >>> selected_colour({"INDICA": "#f4efe3", "SATIVA": "#f4efe3", "HYBRID": "#ada383"}) is None
    True
    >>> selected_colour({"INDICA": "#ada383", "SATIVA": "#ada383", "HYBRID": "#ada383"}) is None
    True
    """
    if len(opts) != 3:
        return None
    seen = {}
    for colour in opts.values():
        seen[colour] = seen.get(colour, 0) + 1
    if sorted(seen.values()) != [1, 2]:
        return None
    once = [c for c, n in seen.items() if n == 1][0]
    twice = [c for c, n in seen.items() if n == 2][0]
    # cream on a filled pill, never muted olive on the ground
    return once if luminance(once) > luminance(twice) else None


def packaging(rows):
    """The primary-packaging lines, exactly as the specification prints them.

    The label is letter-spaced in the PDF ("P R I M A RY  PAC KAG I N G"), so it is
    matched loosely; the value is the run of body-weight lines in its own column.
    """
    label = None
    for txt, _c, _s, top, left in rows:
        if _PACK_LABEL.match(txt) and "PAC" in txt.replace(" ", "").upper():
            label = (top, left)
            break
    if label is None:
        return []
    top0, left0 = label
    body = [r for r in rows if r[2] >= 9 and abs(r[4] - left0) <= 6
            and top0 < r[3] < top0 + 80 and r[0]]
    return [r[0] for r in sorted(body, key=lambda r: r[3])]


def dominance_slot(rows):
    """What the specification prints under its HYBRID pill, verbatim.

    Either a ratio ("INDICA 70 : SATIVA 30") or the specification's own controlled
    blank, "TO BE DETERMINED". Empty when the pill carries no slot at all.
    """
    hyb = [r for r in rows if r[0].upper() == "HYBRID" and r[2] <= 8]
    if not hyb:
        return ""
    _t, _c, _s, top, left = hyb[0]
    lo, hi, drift = _DOM_BELOW
    below = [r for r in rows
             if r is not hyb[0] and top + lo <= r[3] <= top + hi
             and abs(r[4] - left) <= drift and r[0].strip()]
    below.sort(key=lambda r: (r[3], r[4]))
    return below[0][0].strip() if below else ""


def read(pdf):
    """One issued specification as a record, or None where it cannot be read.

    Keys: ``code``, ``phenotype``, ``dominance``, ``chemotype``, ``processing``,
    ``packaging`` (the printed lines, joined by " "), ``file``.
    """
    rows = nodes(pdf)
    code = ""
    for txt, _c, _s, _t, _l in rows:
        if txt.upper().startswith("QCSP"):
            code = txt.strip()
            break
    found = {g: {} for g in GROUPS}
    for txt, colour, size, _t, _l in rows:
        g = _OPT_OF.get(txt.upper())
        if g and size <= 8:
            found[g].setdefault(txt.upper(), colour)
    sel = selected_colour(found["phenotype"])
    if not code or sel is None:
        return None
    picked = {}
    for g, opts in found.items():
        hit = [w for w, c in opts.items() if c == sel]
        if len(hit) != 1:
            return None
        picked[g] = hit[0]
    dom = dominance_slot(rows)
    return {"file": os.path.relpath(pdf, SPC), "code": normalise(code),
            "printed_code": code, "phenotype": picked["phenotype"],
            "dominance": dom, "dom": dominant(dom) or "",
            "chemotype": picked["chemotype"],
            "processing": picked["processing"], "packaging": " ".join(packaging(rows))}


def normalise(code):
    """A specification document code in the one spelling the desk keys on.

    >>> normalise("QCSP 001_BSS-II_v.01")
    'QCSP_001_BSS-II_v.01'
    >>> normalise("  QCSP  001_GG4-III_v.01 ")
    'QCSP_001_GG4-III_v.01'
    """
    return re.sub(r"\s+", "_", (code or "").strip())


_NAMED_DOM = re.compile(r"\b(INDICA|SATIVA)\s*[- ]\s*DOMINANT\b", re.I)


def dominant(dominance):
    """Which side the specification's hybrid slot favours, in the master's idiom.

    The certificate's Hybrid pill carries a short dominance sub-label and the
    specification states dominance three ways: as a ratio, as a word, or not at
    all. Only the first two resolve; "BALANCED" and the specification's own
    controlled blank do not, and a certificate may not be more certain than the
    document it cites.

    >>> dominant("INDICA 70 : SATIVA 30")
    'Indica dom.'
    >>> dominant("SATIVA 60 : INDICA 40")
    'Sativa dom.'
    >>> dominant("INDICA-DOMINANT")
    'Indica dom.'
    >>> dominant("INDICA 50 : SATIVA 50") is None
    True
    >>> dominant("BALANCED") is None
    True
    >>> dominant("TO BE DETERMINED") is None
    True
    >>> dominant("") is None
    True
    """
    m = DOMINANCE.search(dominance or "")
    if m:
        a, na, b, nb = m.group(1).upper(), int(m.group(2)), m.group(3).upper(), int(m.group(4))
        if na == nb:
            return None
        side = a if na > nb else b
        return "Indica dom." if side == "INDICA" else "Sativa dom."
    m = _NAMED_DOM.search(dominance or "")
    if m:
        return "Indica dom." if m.group(1).upper() == "INDICA" else "Sativa dom."
    return None


def scan(base=SPC, folders=FOLDERS):
    """Every issued specification on file, by document code — and the conflicts.

    Returns (records, conflicts). Two copies of one document code that disagree on
    an attribute are not resolved here; both readings are reported.
    """
    by, conflicts = {}, []
    for folder in folders:
        d = os.path.join(base, folder)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not name.lower().endswith(".pdf"):
                continue
            rec = read(os.path.join(d, name))
            if rec is None:
                continue
            old = by.get(rec["code"])
            if old is None:
                by[rec["code"]] = rec
                continue
            for k in ("phenotype", "chemotype", "processing", "packaging", "dominance"):
                if old[k] != rec[k]:
                    conflicts.append((rec["code"], k, old["file"], old[k], rec["file"], rec[k]))
    return by, conflicts


COLS = ["code", "phenotype", "dominance", "dom", "chemotype", "processing",
        "packaging", "printed_code", "file"]


def write_csv(path=OUT, base=SPC):
    by, conflicts = scan(base)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(COLS)
        for code in sorted(by):
            wr.writerow([by[code][c] for c in COLS])
    return by, conflicts


def load(path=OUT, _cache={}):
    """The flat source, by document code."""
    if path not in _cache:
        with open(path, encoding="utf-8") as fh:
            _cache[path] = {r["code"]: r for r in csv.DictReader(fh)}
    return _cache[path]


def main(argv):
    import doctest
    fail, ran = doctest.testmod()
    print("%d doctests, %d failed" % (ran, fail))
    if fail:
        return 1
    if "--csv" in argv:
        by, conflicts = write_csv()
        print("%s: %d specification(s)" % (os.path.basename(OUT), len(by)))
    else:
        by, conflicts = scan()
        print("%d specification(s) read" % len(by))
    from collections import Counter
    for g in ("phenotype", "chemotype", "processing"):
        c = Counter(r[g] for r in by.values())
        print("  %-11s %s" % (g, ", ".join("%s %d" % kv for kv in c.most_common())))
    packs = Counter(r["packaging"] for r in by.values())
    print("  packaging   %d distinct" % len(packs))
    for p, n in packs.most_common(4):
        print("      %3d  %s" % (n, p[:88]))
    for c in conflicts:
        print("  CONFLICT %s %s: %s=%r vs %s=%r" % c)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
