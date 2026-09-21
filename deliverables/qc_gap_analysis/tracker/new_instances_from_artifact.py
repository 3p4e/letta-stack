#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The documents the certificates already cite become testing instances on the tracker.

    python3 deliverables/qc_gap_analysis/tracker/new_instances_from_artifact.py [--dry-run]

Two records, one intake path. The intakes of 16.09.2026 (IJZ-MB microbiology) and
18.09.2026 (the Institute's contaminant panels) wrote their results into
coq_artifact_data.json and the release register — what the certificates print — and
never into new_instances.json, the tracker's own document pool. So Batch Coverage never
credited them, and the 09.09.2026 overlay (coverage_update_2026-09-09.tsv) kept painting
"○ on file, not recorded" over 81 cells whose document was already the cited source on
the certificate of quality.

This takes every document that (a) a certificate cites, (b) the 09.09 overlay names, and
(c) the manifest does not carry, and appends one manifest entry per document in the
existing shape — the lot row the overlay names, the values exactly as the certificate
prints them, folded to the manifest's own spelling ('<10', 'absent', '2.2×10³', '<LOQ').
Nothing is read from a page here: the values are the certificates' own, already through
their intake's two-read gate, and the entry says so in `source`.

Idempotent on the document code. A document the overlay names that no certificate cites
is reported and left for its own intake (intake_gaps_2026-09-21).
"""
import collections
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import tracker_data as T                                                 # noqa: E402

ART = os.path.join(ROOT, "coq_artifact_data.json")
MANIFEST = os.path.join(HERE, "new_instances.json")
OVERLAY = os.path.join(ROOT, "coverage_update_2026-09-09.tsv")
STATUS = os.path.join(HERE, "ecoa_coverage_status_2026-09-20.json")
DRIVE_IDS = os.path.join(HERE, "ecoa_drive_ids_2026-09-21.json")
TODAY = "21.09.2026"

SUP = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"}
# The laboratory abbreviation the tracker uses, from the family the certificate credits.
LAB = {"IJZ-MB": "IJZ-MB", "IJZ": "IJZ", "CNP": "CNP", "FHM": "FHM"}


def desk_form(v, no):
    """The certificate's printed result in the manifest's spelling (new_instances_from_records)."""
    t = str(v or "").strip()
    if no == "3":
        return "Conforms"                       # identification C: the assay certificate's own verdict
    if re.match(r"^(absent|отсу)", t, re.I):
        return "absent"
    t = re.sub(r"\s*\*+\s*%\s*w/w$", "", t)     # '< LOQ** %w/w' -> '< LOQ'
    t = re.sub(r"\s*CFU\s*/\s*g\s*$", "", t, flags=re.I)
    t = t.replace(" and ", " и ")               # '< 10² and > 10' -> the register's '<10² и >10'
    t = re.sub(r"\s*[x×]\s*10\s*\^?\s*([0-9⁰¹²³⁴⁵⁶⁷⁸⁹]+)",
               lambda m: "×10" + "".join(SUP.get(c, c) for c in m.group(1)), t)
    if no != "12":                               # #12 is the desk's own sentence, kept as printed
        t = re.sub(r"([<>≤≥])\s+", r"\1", t)
    return re.sub(r"\s+", " ", t).strip()


def main(argv):
    dry = "--dry-run" in argv
    art = json.load(open(ART, encoding="utf-8"))
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    have = {T.nkey(r["code"]) for r in manifest}
    status = {T.nkey(x["doc_code"]): x for x in json.load(open(STATUS, encoding="utf-8"))}
    drive = {T.nkey(k): v for k, v in json.load(open(DRIVE_IDS, encoding="utf-8")).items()}

    # the overlay: document -> the Batch Coverage row it was painted on
    overlay = collections.OrderedDict()
    with open(OVERLAY, encoding="utf-8") as fh:
        for u in csv.DictReader(fh, delimiter="\t"):
            for m in re.finditer(r"([^;]+?)\s*\((\d\d\.\d\d\.\d{4})\)\s*\[([^\]]+)\]", u["Now covered by"]):
                k = T.nkey(m.group(1))
                overlay.setdefault(k, {"code": m.group(1).strip(), "date": m.group(2), "lab": m.group(3),
                                       "cu": u["CU batch"].strip(), "p": u["P batch"].strip(),
                                       "strain": u["Strain"].strip()})

    # the certificates: document -> every row that cites it
    cited = collections.defaultdict(list)
    for c in art["coqs"]:
        for r in c["rows"]:
            doc = str(r.get("doc") or "").strip()
            if doc and not doc.startswith("iCoA"):
                cited[T.nkey(doc)].append((c, r, doc))

    added, uncited, skipped = [], [], []
    for k, o in overlay.items():
        if k in have:
            skipped.append(o["code"]); continue
        rows = cited.get(k)
        if not rows:
            uncited.append(o); continue
        c0 = rows[0][0]
        printed = rows[0][2]
        ps = [x.strip() for x in o["p"].split("/") if x.strip().startswith("P")]
        st = status.get(k) or {}
        # one P lot of a multi-lot row: the certificate's own (the file names it)
        p = ps[0] if len(ps) == 1 else (st.get("p_batch") or c0.get("pp") or "")
        # A P lot is P + six digits. GG1024 is a cultivation batch that the register
        # carries with no P number, and the certificate prints it in the pp field; taking
        # it as a P lot opened a second GG1024 row and left the real one's gaps unfilled.
        p = p if re.match(r"^P\d{6}$", str(p or "").strip()) else ""
        cu = "" if o["cu"].startswith("—") else o["cu"]
        vals, params = {}, set()
        for c, r, _ in rows:
            no = str(r["no"])
            if no in vals:
                continue
            vals[no] = desk_form(r.get("res"), no)
            params.add(int(no.split(".")[0]))
        fams = sorted({(r.get("lab") or "", r.get("fam") or "") for _, r, _ in rows})
        added.append({
            "p": p, "cu": cu, "strain": c0.get("strain") or o["strain"],
            "code": printed.replace("/", "-").replace(" ", ""),
            "date": rows[0][1].get("dd") or o["date"],
            "lab": LAB.get(o["lab"], o["lab"]) if o["lab"] != "FHM" or 8 in params else "FHM-K",
            "params": sorted(params),
            "vals": {n: vals[n] for n in sorted(vals, key=lambda s: [int(y) for y in s.split(".")])},
            "held": [],
            "document": st.get("filename") or "",
            "doc_id": drive.get(k),
            "source": "cited on the certificates (coq_artifact_data.json, %s) — registered on the "
                      "tracker %s by new_instances_from_artifact.py; the values are the certificate's"
                      % ("; ".join(f or l for l, f in fams), TODAY),
        })

    print("overlay documents: %d   already on the manifest: %d   cited, now registered: %d   "
          "uncited (own intake): %d" % (len(overlay), len(skipped), len(added), len(uncited)))
    for a in added:
        print("   %-13s %-8s %-13s %-6s #%s" % (a["code"], a["p"], a["cu"] or a["strain"][:13], a["lab"],
                                               ",".join(map(str, a["params"]))))
    for o in uncited:
        print("   not cited: %-13s %s %s [%s]" % (o["code"], o["cu"], o["p"], o["lab"]))
    if dry:
        print("--dry-run — nothing written")
        return 0
    manifest.extend(added)
    json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("written: %s (%d entries)" % (os.path.relpath(MANIFEST, ROOT), len(manifest)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
