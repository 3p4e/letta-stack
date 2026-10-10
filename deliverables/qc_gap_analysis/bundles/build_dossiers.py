#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every batch documentation bundle, derived from the desk's own record.

    python3 deliverables/qc_gap_analysis/bundles/build_dossiers.py --round retest --tranche 1 2

One PDF per production batch PER TESTING ROUND (Head of QC, 18.09.2026):

    page 1   the certificate of quality for that batch and round
    page 2   the internal certificate of analysis behind it
    then     every external laboratory certificate that certificate of quality cites,
             in chronological order of issue
    last     the intermediate bulk product specification for that strain and grade -
             the sheet the certificate itself cites, at QCSP 001 v.04

The certificate of quality and the internal certificate are OUR OWN latest print — never a
copy found in Drive ("it's mandatory that you use our latest iteration and print off the
certificates not any previous copy that you can find in Drive"). Every page of every
EXTERNAL certificate is stamped with THAT bundle's certificate code and date of issue and
the Head of QC's true-copy mark; the internal certificate is not stamped, because it is
clearly marked as ours on its own face.

Excluded, by the Head of QC's ruling: the CNP certificate carrying the loss-on-drying
result. It is the one external document that does not travel with the bundle.

Nothing here decides what a certificate cites. The citations, their dates and the internal
certificate's code are read from coq_artifact_data.json, which is what the certificate
itself was printed from, so the bundle and the certificate can never disagree.
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from build_bundle import build, SIGS                                     # noqa: E402

COQ_PAGES = os.path.join(GAP, "design_handoff", "pdf", "pages")
ICOA_PAGES = os.path.join(GAP, "icoa_handoff", "v3", "pdf", "pages")
SPEC_PAGES = os.path.join(GAP, "specs", "QCSP_001_v04", "pdf", "pages")
CACHE_DIRS = ("/tmp/claude-0/ecoa_cache", "/tmp/claude-0/contaminants")
OUT = os.path.join(GAP, "bundles", "dossiers")

# The corpus writes a document code two ways: the certificate cites it as the laboratory
# types it, in Cyrillic, and the scan's file name carries a transliteration. So a code is
# compared in one canonical form - Cyrillic folded to Latin PHONETICALLY (С is S, not C),
# punctuation dropped, and the loss-on-drying suffix ГС written the way the file names
# write it, LoD. Without the last of those, 031-2-ГС/26 and 031-2-LoD-26 are two documents.
CYR = {"А": "A", "Б": "B", "В": "V", "Г": "G", "Д": "D", "Ѓ": "G", "Е": "E", "Ж": "Z",
       "З": "Z", "Ѕ": "DZ", "И": "I", "Ј": "J", "К": "K", "Л": "L", "Љ": "LJ", "М": "M",
       "Н": "N", "Њ": "NJ", "О": "O", "П": "P", "Р": "R", "С": "S", "Т": "T", "Ќ": "K",
       "У": "U", "Ф": "F", "Х": "H", "Ц": "C", "Ч": "C", "Џ": "DZ", "Ш": "S"}


def fold(x):
    return "".join(CYR.get(c, c) for c in str(x).upper())


def norm(x):
    v = re.sub(r"[\s\-/.,_]", "", fold(x))
    return v.replace("GS", "LOD")


def dmy(s):
    m = re.match(r"^(\d\d)\.(\d\d)\.(\d{4})$", str(s or "").strip())
    return (int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else (9999, 99, 99)


# A laboratory that issues one report in two languages files it as two scans under the one
# document number. They are one certificate, so both travel with the bundle, original
# first; they are not two candidates to choose between.
LANG = re.compile(r"(?<![A-Za-z])(EN|ENG|MK|MKD)(?![A-Za-z])", re.I)

# A citation may carry the desk's own qualifier in brackets, to tell apart two certificates
# the laboratory numbered a day apart for two products of one lot. The qualifier is a note
# to the reader, not part of the document number, so it is dropped before matching.
QUALIFIER = re.compile(r"\s*\([^)]*\)\s*$")


def index_cache(dirs=None):
    """Every cached scan, by the normalised code in its file name.

    A scan is registered under the code field of its name and under the whole stem, so a
    code the naming convention did not isolate cleanly can still be found by containment.
    """
    idx = collections.defaultdict(list)
    stems = []
    for base in (dirs or CACHE_DIRS):
        for root, _dirs, files in os.walk(base):
            for f in files:
                if not f.lower().endswith(".pdf"):
                    continue
                path = os.path.join(root, f)
                stem = f.rsplit(".", 1)[0]
                parts = stem.split("_")
                if len(parts) > 1:
                    idx[norm(parts[1])].append(path)
                stems.append((norm(stem), norm(LANG.sub("", stem)), path))
    idx["__stems__"] = stems
    return idx


def find(idx, code):
    """Every scan for a cited code, oldest spelling first - or an empty list.

    Exact on the code field, else by containment of the whole stem. Containment accepts
    more than one scan only when the several are the same document in another language,
    which is what the stems say when they are identical with the language token removed.
    """
    k = norm(QUALIFIER.sub("", str(code)))
    hit = idx.get(k)
    if hit:
        return sorted(hit)
    cand = [(nl, p) for st, nl, p in idx["__stems__"] if k and k in st]
    if len(cand) == 1:
        return [cand[0][1]]
    if cand and len(set(nl for nl, _p in cand)) == 1:
        return sorted(p for _nl, p in cand)
    return []


def page_of(directory, code):
    """Our own printed page for a document code."""
    hits = [f for f in os.listdir(directory) if f.startswith(code + "_") and f.endswith(".pdf")]
    return os.path.join(directory, hits[0]) if len(hits) == 1 else None


def citations(cert):
    """(code, date, dets) for every external document the certificate cites, oldest first.

    The internal certificate is not an external document and never appears here; nor does
    the CNP certificate that carries the loss-on-drying result, which the Head of QC
    excluded from the bundle.
    """
    by = collections.OrderedDict()
    for r in cert.get("rows", []):
        code = str(r.get("doc") or "").strip()
        if not code or code in ("—", "N/A") or code.startswith("iCoA-PP_"):
            continue
        rec = by.setdefault(code, {"date": str(r.get("dd") or "").strip(), "dets": set()})
        rec["dets"].add(str(r.get("no")))
        if not rec["date"]:
            rec["date"] = str(r.get("dd") or "").strip()
    out = []
    for code, rec in by.items():
        if fold(code).startswith("PPK") and "8" in rec["dets"]:
            continue                       # the CNP loss-on-drying certificate
        out.append((code, rec["date"], sorted(rec["dets"])))
    out.sort(key=lambda t: (dmy(t[1]), t[0]))
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", choices=("initial", "retest", "both"), default="both")
    ap.add_argument("--tranche", nargs="*", default=["1", "2", "3", ""])
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(argv[1:])

    data = json.load(open(os.path.join(GAP, "coq_artifact_data.json"), encoding="utf-8"))
    tranche = {}
    for f in ("coq_reissue_scope_2026-09-15.csv", "coq_draft_scope_2026-09-10.csv"):
        p = os.path.join(GAP, "tracker", f)
        if not os.path.exists(p):
            continue
        import csv
        for r in csv.DictReader(open(p, encoding="utf-8")):
            if r.get("p_lot"):
                tranche.setdefault(r["p_lot"], (r.get("tranche") or "").strip())

    idx = index_cache()
    made, skipped = [], []
    for c in data["coqs"]:
        code = (c.get("regcode") or "").strip()
        rnd = "retest" if str(c.get("t") or "").startswith("retest") else "initial"
        if not code.startswith("CoQ-PP_26-"):
            # A certificate still at issue has no number, so no page of it can be stamped
            # with one. It is held by name and round, not silently folded into its lot.
            skipped.append(("%s %s" % (c.get("pp") or c.get("cb"), rnd),
                            "no register code")); continue
        if a.round != "both" and rnd != a.round:
            continue
        lot = c.get("pp") or c.get("cb")
        t = tranche.get(lot, "")
        if a.tranche and t not in a.tranche:
            continue
        coq_pdf = page_of(COQ_PAGES, code)
        icoa = (c.get("icoa_code") or "").strip()
        icoa_pdf = page_of(ICOA_PAGES, icoa) if icoa.startswith("iCoA-PP_") else None
        if not coq_pdf:
            skipped.append((code, "our certificate is not printed")); continue
        if not icoa_pdf:
            skipped.append((code, "no internal certificate (%s)" % (icoa or "none cited"))); continue
        speccode = (c.get("spec") or "").strip()
        spec_pdf = None
        if speccode:
            hits = [f for f in os.listdir(SPEC_PAGES) if f.startswith(speccode + "_")] \
                if os.path.isdir(SPEC_PAGES) else []
            spec_pdf = os.path.join(SPEC_PAGES, hits[0]) if len(hits) == 1 else None
        # A lot with no Total THC result has no grade, so there is no grade-specific sheet
        # to append. The bundle is still that batch's documentation and is built without
        # one; the index records which those are rather than the desk choosing a grade.
        nospec = None if spec_pdf else (speccode or "no grade assigned")
        ext, missing = [], []
        for doccode, date, _dets in citations(c):
            hits = find(idx, doccode)
            if hits:
                ext.extend((h, doccode, date) for h in hits)
            else:
                missing.append(doccode)
        if missing:
            skipped.append((code, "scan not cached: " + ", ".join(missing))); continue
        d = os.path.join(a.out, "T%s" % (t or "x"), rnd)
        os.makedirs(d, exist_ok=True)
        name = "%s_%s_%s_%s.pdf" % (lot, (c.get("cb") or "").replace("/", "-"), code, rnd)
        dest = os.path.join(d, re.sub(r"[^A-Za-z0-9_.\-]", "_", name))
        n, _toc = build(coq_pdf, icoa_pdf, ext, code, c.get("issue") or "", dest,
                        spec_pdf=spec_pdf, spec_code=speccode)
        made.append((code, lot, rnd, t, n, len(ext), dest, speccode if spec_pdf else ""))
        if a.limit and len(made) >= a.limit:
            break

    print("bundles built: %d  (%d signature iterations in rotation)" % (len(made), len(SIGS)))
    byt = collections.Counter("T%s %s" % (m[3] or "x", m[2]) for m in made)
    for k in sorted(byt):
        print("   %-12s %d" % (k, byt[k]))
    if skipped:
        print("not built: %d" % len(skipped))
        why = collections.Counter(s[1].split(":")[0] for s in skipped)
        for k, v in why.most_common():
            print("   %-34s %d" % (k, v))
    # The index is the whole shelf, not this run. A run may cover one tranche or one
    # round, and an index that forgot the rest would misdescribe what is on disk.
    ipath = os.path.join(a.out, "INDEX.json")
    shelf = {}
    if os.path.exists(ipath):
        for r in json.load(open(ipath, encoding="utf-8")):
            shelf[r["file"]] = r
    for m in made:
        rel = os.path.relpath(m[6], GAP)
        shelf[rel] = {"coq": m[0], "lot": m[1], "round": m[2], "tranche": m[3],
                      "pages": m[4], "externals": m[5], "file": rel, "specification": m[7]}
    for rel in list(shelf):
        if not os.path.exists(os.path.join(GAP, rel)):
            del shelf[rel]
    json.dump([shelf[k] for k in sorted(shelf)], open(ipath, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    npath = os.path.join(a.out, "NOT_BUILT.json")
    held = {}
    if os.path.exists(npath):
        for r in json.load(open(npath, encoding="utf-8")):
            held[r["coq"]] = r
    for k in [m[0] for m in made]:
        held.pop(k, None)
    for s in skipped:
        held[s[0]] = {"coq": s[0], "why": s[1]}
    json.dump([held[k] for k in sorted(held)], open(npath, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    sys.exit(main(sys.argv))
