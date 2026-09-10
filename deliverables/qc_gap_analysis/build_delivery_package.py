#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One archive with everything the QC desk has produced, and a manifest of it.

    python3 deliverables/qc_gap_analysis/build_delivery_package.py

The pieces of this work live where they are built — the certificates beside the
compiler, the workbook beside the tracker, the flat sources beside the schedule —
which is right for a repository and wrong for handing to a person. This gathers
the current state into `deliverables/zips/PP_QC_Package_<date>.zip`, one folder
per kind, with a `MANIFEST.md` that names every file, its size, its SHA-256 and
what it is.

**It refuses to package a stale build.** Every derived deliverable is checked
against the source it is derived from: a certificate older than the exported data
it was compiled from, or an exported dataset older than the schedule that built
it, is a deliverable that does not say what the desk currently knows. Both have
happened in this project — the whole reason the rulings of 10.09.2026 had to be
applied twice — so the check is part of the build rather than a thing to remember.
"""
import hashlib
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DRAFTS = os.path.join(HERE, "drafts")
TRACKER = os.path.join(HERE, "tracker")
OUT_DIR = os.path.join(ROOT, "deliverables", "zips")
STAMP = "2026-09-10"

# folder in the archive -> (source path, what it is)
def _items():
    items = []
    for name in sorted(os.listdir(DRAFTS)):
        if name.startswith("DRAFT_CoQ_") and name.endswith(".html"):
            items.append(("certificates/individual/" + name, os.path.join(DRAFTS, name),
                          "Certificate of quality, one lot — DRAFT, unsigned"))
    items += [
        ("INDEX.html", os.path.join(HERE, "PACKAGE_INDEX.html"),
         "Start here — every sheet, what the archive holds, what to read first"),
        ("certificates/Tranche_1_CoQ_Drafts.pdf", os.path.join(DRAFTS, "Tranche_1_CoQ_Drafts.pdf"),
         "Tranche 1 — 13 certificates, one A4 page each, fonts embedded"),
        ("certificates/Tranche_2_CoQ_Drafts.pdf", os.path.join(DRAFTS, "Tranche_2_CoQ_Drafts.pdf"),
         "Tranche 2 — 9 certificates, one A4 page each, fonts embedded"),
        ("certificates/Tranche_1_2_CoQ_Draft_Set.html", os.path.join(DRAFTS, "Tranche_1_2_CoQ_Draft_Set.html"),
         "All 22 certificates as one scrollable page"),
        ("workbook/CoQ_Analysis_Master_v21.xlsx", os.path.join(TRACKER, "CoQ_Analysis_Master_v21.xlsx"),
         "The desk workbook — coverage, registers, Reconciliation 09.09"),
        ("workbook/coq_master_v21.html", os.path.join(TRACKER, "coq_master_v21.html"),
         "The same workbook as a page, nine views"),
        ("desk/qc_quality_desk_artifact.html", os.path.join(HERE, "qc_quality_desk_artifact.html"),
         "The live Quality Desk — click a batch to compile its certificate"),
        ("sources/issuance_schedule_2026-09-10.csv", os.path.join(HERE, "issuance_schedule_2026-09-10.csv"),
         "Every certificate and internal CoA with its date, under the 10.09 rulings"),
        ("sources/icoa_register_2026-09-10.csv", os.path.join(HERE, "icoa_register_2026-09-10.csv"),
         "The standing internal-CoA register — 106 certificates, coded in issue order"),
        ("sources/spec_attributes_2026-09-10.csv", os.path.join(HERE, "spec_attributes_2026-09-10.csv"),
         "Phenotype, dominance, chemotype, processing and packaging, read off 257 issued specifications"),
        ("sources/coq_register_2026-09-10.csv", os.path.join(HERE, "coq_register_2026-09-10.csv"),
         "The workbook's own CoQ register, lifted"),
        ("sources/cell_resolution_2026-09-09.tsv", os.path.join(HERE, "cell_resolution_2026-09-09.tsv"),
         "The owner's 09.09 pass — 600 determinations resolved to a document"),
        ("sources/coverage_update_2026-09-09.tsv", os.path.join(HERE, "coverage_update_2026-09-09.tsv"),
         "The 09.09 coverage update"),
        ("sources/identity_block_2026-09-09.tsv", os.path.join(HERE, "identity_block_2026-09-09.tsv"),
         "The identity determinations, batch by batch"),
        ("sources/coq_draft_scope_2026-09-10.csv", os.path.join(TRACKER, "coq_draft_scope_2026-09-10.csv"),
         "Which of the 50 delivered batches are draftable, and why the rest are not"),
        ("sources/coq_draft_gaps.csv", os.path.join(DRAFTS, "coq_draft_gaps.csv"),
         "Every blank printed line on the 22 certificates, with its cause"),
        ("docs/ISSUANCE_RULES_2026-09-10.md", os.path.join(TRACKER, "ISSUANCE_RULES_2026-09-10.md"),
         "The 10.09 rulings, what they changed, and what is still to build"),
        ("docs/COQ_DRAFTING_2026-09-10.md", os.path.join(TRACKER, "COQ_DRAFTING_2026-09-10.md"),
         "How the certificates were drafted, in five revisions"),
        ("docs/V20_RECONCILIATION_2026-09-10.md", os.path.join(TRACKER, "V20_RECONCILIATION_2026-09-10.md"),
         "The owner's v20 workbook reconciled into the desk"),
        ("docs/DELIVERY_RECONCILIATION_2026-09-07.md", os.path.join(TRACKER, "DELIVERY_RECONCILIATION_2026-09-07.md"),
         "Delivery against what is on file"),
        ("docs/drafts_README.md", os.path.join(DRAFTS, "README.md"),
         "What the certificates are, and what they still lack"),
    ]
    return [(a, b, c) for a, b, c in items if os.path.exists(b)]


# derived deliverable -> what it is derived from. A deliverable older than its
# source is stale and the build stops.
FRESH = [
    (os.path.join(HERE, "coq_artifact_data.json"), os.path.join(HERE, "build_coq_schedule.py")),
    (os.path.join(HERE, "qc_quality_desk_artifact.html"), os.path.join(HERE, "coq_artifact_data.json")),
    (os.path.join(DRAFTS, "Tranche_1_2_CoQ_Draft_Set.html"), os.path.join(HERE, "coq_artifact_data.json")),
    (os.path.join(DRAFTS, "Tranche_1_CoQ_Drafts.pdf"), os.path.join(DRAFTS, "Tranche_1_2_CoQ_Draft_Set.html")),
    (os.path.join(DRAFTS, "Tranche_2_CoQ_Drafts.pdf"), os.path.join(DRAFTS, "Tranche_1_2_CoQ_Draft_Set.html")),
    (os.path.join(TRACKER, "coq_master_v21.html"), os.path.join(TRACKER, "CoQ_Analysis_Master_v21.xlsx")),
]


def stale():
    """Derived deliverables older than what they are derived from."""
    out = []
    for derived, source in FRESH:
        if not (os.path.exists(derived) and os.path.exists(source)):
            continue
        if os.path.getmtime(derived) < os.path.getmtime(source):
            out.append((os.path.relpath(derived, ROOT), os.path.relpath(source, ROOT)))
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def human(n):
    """A byte count a person reads.

    >>> human(999), human(2048), human(19530086)
    ('999 B', '2.0 KiB', '18.6 MiB')
    """
    if n < 1024:
        return "%d B" % n
    if n < 1024 ** 2:
        return "%.1f KiB" % (n / 1024.0)
    return "%.1f MiB" % (n / 1024.0 ** 2)


def manifest(items):
    lines = ["# Purely Plant — QC package, %s" % STAMP, "",
             "Everything the QC desk has produced, as it stands. Every certificate in",
             "here is a **DRAFT**: watermarked, unsigned, its conformity statement",
             "unticked, and every field the desk cannot stand behind bracketed in red.",
             "**None has been issued.**", "",
             "| file | size | what it is |", "| --- | ---: | --- |"]
    for arc, src, what in items:
        lines.append("| `%s` | %s | %s |" % (arc, human(os.path.getsize(src)), what))
    lines += ["", "## Checksums", "", "```"]
    for arc, src, _ in items:
        lines.append("%s  %s" % (sha256(src), arc))
    lines.append("```")
    return "\n".join(lines) + "\n"


def main():
    import doctest
    fail, ran = doctest.testmod()
    print("%d doctests, %d failed" % (ran, fail))
    if fail:
        return 1
    bad = stale()
    if bad:
        print("\nrefusing to package a stale build:")
        for derived, source in bad:
            print("  %s is older than %s" % (derived, source))
        print("\nrebuild it and run again.")
        return 2
    items = _items()
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "PP_QC_Package_%s.zip" % STAMP)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("MANIFEST.md", manifest(items))
        for arc, src, _ in items:
            z.write(src, arc)
    print("%s: %d file(s), %s" % (os.path.relpath(out, ROOT), len(items) + 1,
                                  human(os.path.getsize(out))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
