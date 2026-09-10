#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The owner's 09.09.2026 cell resolution, as a source the schedule can read.

    python3 deliverables/qc_gap_analysis/cell_resolution.py        # self-test + census

`cell_resolution_2026-09-09.tsv` resolves every one of the 600 determinations of
Tranches 1 and 2 to a document, a laboratory, an issue date and the result that
document prints. It is evidence, not a conclusion, so this module answers one
question only: **for this cultivation batch and this determination, does the
09.09 pass hold a result the desk can print verbatim?**

Four rules decide, and each of them refuses more than it accepts.

0. **A result the desk cannot cite by document code is not printable.** Three
   in-house "Report of Analysis" documents carry no document code, no version
   and no report number (EudraLex Vol. 4 Ch. 4 §4.9), and the sheet names them
   `NO-DOC-CODE`. Section 03 of the certificate is a table of document codes;
   there is nothing to put in it. The register already refuses un-numbered
   documents, and so does this.

1. **A document that has not been issued certifies nothing.** 110 of the 600
   cells cite an in-house `iCoA-PP_26-nnn` with a PLANNED issue date — almost
   every Identification A, Identification B and foreign matter row in both
   tranches. The sheet records what the planned document would say; a
   certificate of quality may not. Those cells are `blocked`, never filled.

2. **A single printed value fills a single printed line.** Where the sheet holds
   one value and the determination prints one line, the value is the line.

3. **A list the sheet does not label is not a mapping.** Microbiology prints
   five lines and heavy metals four, and the sheet gives five and four values —
   but in the certificate's own order, with no analyte names. On BSS1024 the
   desk and this sheet hold the same four heavy-metal values in a different
   order, and on HPA1024 and OPM1024 the same again: the order cannot be
   assumed, and guessing which value is cadmium is exactly the fabrication this
   folder exists to prevent. Those cells are `ambiguous` and stay blank.

   The one list that does resolve is the pesticide panel: many residue rows
   against one printed line, all of them reporting the same thing. When every
   residue agrees, the panel collapses to that one result — the rule the
   schedule already applies to the in-house panel.

What this module does NOT do is overrule the desk. It is consulted only where
the desk holds nothing; the 09.09 pass itself found no error in the tracker
across 550 comparable cells, so where both hold a value the desk's stands.
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(HERE, "cell_resolution_2026-09-09.tsv")

# The determinations that print one line on the certificate. Everything else
# (9 microbiology, 10 mycotoxins, 11 heavy metals) prints one line per analyte,
# and the sheet does not name them — see rule 3.
SINGLE_LINE = {"1", "2", "3", "4", "5", "6", "7", "8"}
PANEL = "12"

_BI = None


def batch_key(cb):
    """Batch identity — the single definition, imported the way the schedule does.

    >>> batch_key("FB012601_1") == batch_key("FB012601/1")
    True
    """
    global _BI
    if _BI is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "batch_id", os.path.join(ROOT, "ingestion", "common", "batch_id.py"))
        _BI = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_BI)
    return _BI.batch_key(cb)


def det_no(label):
    """The determination number a sheet label starts with.

    >>> det_no("1 Identification A — appearance")
    '1'
    >>> det_no("12 Pesticide residues")
    '12'
    >>> det_no("") is None
    True
    """
    m = re.match(r"\s*(\d+)\b", label or "")
    return m.group(1) if m else None


def pieces(printed):
    """The printed result split into the values the document prints.

    An empty trailing field is a separator artefact, not a residue.

    >>> pieces("0,01 mg/kg; 0,016 mg/kg(l)")
    ['0,01 mg/kg', '0,016 mg/kg(l)']
    >>> pieces("н.д. mg/kg; н.д. mg/kg; ")
    ['н.д. mg/kg', 'н.д. mg/kg']
    >>> pieces("—")
    []
    """
    s = (printed or "").strip()
    if s in ("", "—"):
        return []
    return [p.strip() for p in s.split(";") if p.strip()]


def _panel_key(v):
    """A residue value with its unit stripped, for the all-agree test.

    >>> _panel_key("н.д. mg/kg(l)") == _panel_key("н.д. mg/Kg")
    True
    >>> _panel_key("< 0,01 mg/kg") == _panel_key("н.д. mg/kg")
    False
    """
    return re.sub(r"\s*mg\s*/\s*kg\s*(\(l\))?\s*$", "", v.strip(), flags=re.I).lower()


def uncitable(code):
    """Is this a document a certificate cannot cite by code?

    >>> uncitable("NO-DOC-CODE (Report of Analysis)")
    True
    >>> uncitable("—"), uncitable("")
    (True, True)
    >>> uncitable("ППК25051")
    False
    """
    c = (code or "").strip()
    return not c or c == "—" or c.upper().startswith("NO-DOC-CODE")


def resolve(row):
    """One sheet row as (state, value) — what may be printed, and why not.

    States are ``fill``, ``uncited`` (rule 0), ``blocked`` (rule 1),
    ``ambiguous`` (rule 3) and ``none`` (the sheet holds no result at all).

    >>> resolve({"Determination": "6 Total CBN", "Blocked: document not issued": "",
    ...          "Document to cite": "ППК25051", "What the document prints": "0.02 %"})
    ('fill', '0.02 %')
    >>> resolve({"Determination": "1 Identification A — appearance",
    ...          "Blocked: document not issued": "",
    ...          "Document to cite": "NO-DOC-CODE (Report of Analysis)",
    ...          "What the document prints": "Confirms"})[0]
    'uncited'
    >>> resolve({"Determination": "1 Identification A — appearance",
    ...          "Blocked: document not issued": "YES — the certificate has not been issued",
    ...          "Document to cite": "iCoA-PP_26-003",
    ...          "What the document prints": "Conforms"})[0]
    'blocked'
    >>> resolve({"Determination": "11 Heavy metals", "Blocked: document not issued": "",
    ...          "Document to cite": "752-2025",
    ...          "What the document prints": "0,01 mg/kg; 0,016 mg/kg"})[0]
    'ambiguous'
    >>> resolve({"Determination": "12 Pesticide residues", "Blocked: document not issued": "",
    ...          "Document to cite": "752-2025",
    ...          "What the document prints": "н.д. mg/kg; н.д. mg/kg; н.д. mg/kg"})
    ('fill', 'н.д. mg/kg — all 3 residues')
    >>> resolve({"Determination": "12 Pesticide residues", "Blocked: document not issued": "",
    ...          "Document to cite": "752-2025",
    ...          "What the document prints": "н.д. mg/kg; 0,02 mg/kg"})[0]
    'ambiguous'
    >>> resolve({"Determination": "8 Loss on drying", "Blocked: document not issued": "",
    ...          "Document to cite": "—", "What the document prints": "—"})[0]
    'none'
    """
    no = det_no(row.get("Determination", ""))
    vals = pieces(row.get("What the document prints", ""))
    if not vals:
        return "none", ""
    if uncitable(row.get("Document to cite")):
        return "uncited", ""
    if (row.get("Blocked: document not issued") or "").startswith("YES"):
        return "blocked", ""
    if no in SINGLE_LINE:
        return ("fill", vals[0]) if len(vals) == 1 else ("ambiguous", "")
    if no == PANEL:
        if len({_panel_key(v) for v in vals}) == 1:
            return ("fill", vals[0]) if len(vals) == 1 else \
                ("fill", "%s — all %d residues" % (vals[0], len(vals)))
        return "ambiguous", ""
    return "ambiguous", ""


def load(path=SRC):
    """Every row of the sheet, as it stands."""
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def results(cb, path=SRC, _cache={}):
    """What the 09.09 pass lets this cultivation batch print, by determination.

    The record shape is the one `build_coq_schedule` selects among: a value, the
    document it comes from, that document's date, the laboratory and a report
    series. `family` names the pass rather than a laboratory series, because the
    citation is to a certificate the desk had not previously recorded.
    """
    if path not in _cache:
        by = {}
        for r in load(path):
            state, value = resolve(r)
            if state != "fill":
                continue
            no = det_no(r["Determination"])
            by.setdefault(batch_key(r["Batch"]), {})[no] = {
                "value": value, "code": r["Document to cite"].strip(),
                "date": r["Issued"].strip(), "lab": r["Laboratory"].strip(),
                "family": "read 09.09.2026", "flag": None, "stability": False,
                "note": "", "row": None, "inhouse": False,
            }
        _cache[path] = by
    return _cache[path].get(batch_key(cb), {})


def census(path=SRC):
    """How the 600 cells fall out, by state — printed by the self-test."""
    from collections import Counter
    c = Counter()
    for r in load(path):
        c[resolve(r)[0]] += 1
    return c


if __name__ == "__main__":
    import doctest
    fail, ran = doctest.testmod()
    print("%d doctests, %d failed" % (ran, fail))
    for k, v in sorted(census().items()):
        print("  %-10s %3d" % (k, v))
    sys.exit(1 if fail else 0)
