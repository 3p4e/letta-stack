#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One archive with everything the QC desk has produced, and a manifest of it.

    python3 deliverables/qc_gap_analysis/build_delivery_package.py [--no-pdf]

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
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DRAFTS = os.path.join(HERE, "drafts")
TRACKER = os.path.join(HERE, "tracker")
OUT_DIR = os.path.join(ROOT, "deliverables", "zips")

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
         "All 22 release certificates as one scrollable page"),
        ("certificates/Tranche_1_CoQ_Reissue_Drafts.pdf",
         os.path.join(DRAFTS, "Tranche_1_CoQ_Reissue_Drafts.pdf"),
         "Tranche 1 reissues — the 12-month certificates, one A4 page each"),
        ("certificates/Tranche_2_CoQ_Reissue_Drafts.pdf",
         os.path.join(DRAFTS, "Tranche_2_CoQ_Reissue_Drafts.pdf"),
         "Tranche 2 reissues — the 12-month certificates, one A4 page each"),
        ("certificates/Tranche_1_2_CoQ_Reissue_Draft_Set.html",
         os.path.join(DRAFTS, "Tranche_1_2_CoQ_Reissue_Draft_Set.html"),
         "Every reissue as one scrollable page"),
        ("compilation/CoQ_compilation_v%s.xlsx" % VER,
         os.path.join(TRACKER, "CoQ_compilation_v%s.xlsx" % VER),
         "The owner's first request: one row per certificate of quality, and for every "
         "determination #1 to #12 the result, the document, its date of issue and its laboratory"),
        ("compilation/CoQ_compilation_v%s_wide.csv" % VER,
         os.path.join(TRACKER, "CoQ_compilation_v%s_wide.csv" % VER),
         "The same table, one row per certificate"),
        ("compilation/CoQ_compilation_v%s_long.csv" % VER,
         os.path.join(TRACKER, "CoQ_compilation_v%s_long.csv" % VER),
         "The same table, one row per certificate AND determination, with the method, the "
         "acceptance criterion, the sample receipt date, the status and the route"),
        ("references/CoQ_references_v%s.xlsx" % VER,
         os.path.join(TRACKER, "CoQ_references_v%s.xlsx" % VER),
         "One row per certificate, one column per determination — the document each rests on"),
        ("references/CoQ_references_v%s.csv" % VER,
         os.path.join(TRACKER, "CoQ_references_v%s.csv" % VER), "The same, flat"),
        ("references/CoQ_references_v%s.md" % VER,
         os.path.join(TRACKER, "CoQ_references_v%s.md" % VER), "The same, readable"),
        ("references/CoQ_references_v%s_nt.md" % VER,
         os.path.join(TRACKER, "CoQ_references_v%s_nt.md" % VER),
         "Every cell that reads 'not tested', for review"),
        ("workbook/CoQ_Analysis_Master_v%s.xlsx" % VER, MASTER,
         "The desk workbook — coverage, registers with the 10-11.09 issue dates, Reconciliation 09.09"),
        ("workbook/coq_master_v%s.html" % VER, MASTER_PAGE,
         "The same workbook as a page, nine views"),
        ("desk/qc_quality_desk_artifact.html", os.path.join(HERE, "qc_quality_desk_artifact.html"),
         "The live Quality Desk — click a batch to compile its certificate"),
        ("sources/issuance_schedule_2026-09-10.csv", os.path.join(HERE, "issuance_schedule_2026-09-10.csv"),
         "Every certificate and internal CoA with its date, under the 10.09 rulings"),
        ("sources/batch_dates_2026-09-10.csv", os.path.join(HERE, "batch_dates_2026-09-10.csv"),
         "Harvest and packaging windows per batch — where the internal CoA's testing dates come from"),
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
        ("docs/OPEN_ITEMS.md", os.path.join(TRACKER, "OPEN_ITEMS.md"),
         "Everything still the owner's to decide — what was found, what the desk did, "
         "what is being asked, and the evidence behind each"),
        ("docs/RESULT_SUPERSESSION_2026-09-16.md",
         os.path.join(TRACKER, "RESULT_SUPERSESSION_2026-09-16.md"),
         "Does any certificate print a result the record has replaced? The sweep over all "
         "seventeen determinations — READ THE COVERAGE TABLE FIRST: no lot on file carries a "
         "second heavy-metal certificate, so #11 could not be compared at all"),
        ("tables/Batch_Parameter_Sources_v%s.xlsx" % VER,
         os.path.join(TRACKER, "Batch_Parameter_Sources_v%s.xlsx" % VER),
         "Asked for on 16.09.2026: one row per batch, one column per determination #1 to "
         "#12, and in the cell the document that certifies it with its date of issue — "
         "[internal] where the citation is the company's own certificate of analysis, and "
         "both the release and the reissue citation where they differ. Second sheet: the "
         "same one row per batch, certificate and determination"),
        ("tables/Batch_Parameter_Sources_v%s.csv" % VER,
         os.path.join(TRACKER, "Batch_Parameter_Sources_v%s.csv" % VER),
         "The same table as text, one row per batch"),
        ("tables/Batch_Parameter_Sources_v%s_long.csv" % VER,
         os.path.join(TRACKER, "Batch_Parameter_Sources_v%s_long.csv" % VER),
         "The same table, one row per batch, certificate and determination"),
        ("docs/FLEET_FINDINGS_2026-09-16.md", os.path.join(TRACKER, "FLEET_FINDINGS_2026-09-16.md"),
         "What twelve agents found reading the primary records on 16.09.2026, sorted into "
         "defect (fixed, or named as not fixed and why), question for the owner, and "
         "no action — including two claims that did not survive checking"),
        ("docs/HANDOVER_RESPONSE_2026-09-16.md",
         os.path.join(TRACKER, "HANDOVER_RESPONSE_2026-09-16.md"),
         "The parallel desk's audit of the 127 rendered certificates, answered finding by "
         "finding — four refuted with the comparison counted, three confirmed"),
        ("docs/TRUTH_CHECK_2026-09-15.md", os.path.join(TRACKER, "TRUTH_CHECK_2026-09-15.md"),
         "Every parameter result and every cited document checked from the primary records "
         "forward, by a code path that imports none of the builders"),
        ("docs/VOCABULARY_2026-09-11.md", os.path.join(TRACKER, "VOCABULARY_2026-09-11.md"),
         "The 11.09 audit of parameter values and references: one spelling per assertion, "
         "and the laboratory verdict the desk could not read"),
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
# The workbook version, derived rather than written down. Three places named v22
# by hand, and a hard-coded version is exactly the defect the 11.09.2026 audit
# found in Batch Coverage: a value carried forward stops being true and nothing
# says so. The newest master on disk is the one the package ships.
sys.path.insert(0, TRACKER)
from reference_sections import latest_master, sheet_or_section   # noqa: E402

MASTER = latest_master(TRACKER)
if MASTER is None:
    raise SystemExit("no CoQ_Analysis_Master_vN.xlsx in " + TRACKER)
VER = re.search(r"_v(\d+)\.xlsx$", MASTER).group(1)


def _build_date(master):
    """The archive is stamped with the build date the workbook states about itself.

    The stamp used to be a literal, so every rebuild overwrote the previous day's
    archive under the previous day's name, and the package could carry a v26
    built on the 14th under a file called the 11th.
    """
    import openpyxl
    wb = openpyxl.load_workbook(master, read_only=False)
    rm = sheet_or_section(wb, "Read Me")
    for row in rm.iter_rows(min_col=1, max_col=2, values_only=True):
        if row[0] and str(row[0]).strip() == "What it is":
            m = re.search(r"Built\s+(\d{2})\.(\d{2})\.(\d{4})", str(row[1]))
            if m:
                return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1))
    raise SystemExit("the Read Me of %s does not state its build date" % os.path.basename(master))


STAMP = _build_date(MASTER)
MASTER_PAGE = os.path.join(TRACKER, "coq_master_v%s.html" % VER)


FRESH = [
    (os.path.join(HERE, "coq_artifact_data.json"), os.path.join(HERE, "build_coq_schedule.py")),
    (os.path.join(HERE, "qc_quality_desk_artifact.html"), os.path.join(HERE, "coq_artifact_data.json")),
    (os.path.join(DRAFTS, "Tranche_1_2_CoQ_Draft_Set.html"), os.path.join(HERE, "coq_artifact_data.json")),
    (os.path.join(DRAFTS, "Tranche_1_CoQ_Drafts.pdf"), os.path.join(DRAFTS, "Tranche_1_2_CoQ_Draft_Set.html")),
    (os.path.join(DRAFTS, "Tranche_2_CoQ_Drafts.pdf"), os.path.join(DRAFTS, "Tranche_1_2_CoQ_Draft_Set.html")),
    (os.path.join(DRAFTS, "Tranche_1_2_CoQ_Reissue_Draft_Set.html"), os.path.join(HERE, "coq_artifact_data.json")),
    (os.path.join(DRAFTS, "Tranche_1_CoQ_Reissue_Drafts.pdf"), os.path.join(DRAFTS, "Tranche_1_2_CoQ_Reissue_Draft_Set.html")),
    (os.path.join(DRAFTS, "Tranche_2_CoQ_Reissue_Drafts.pdf"), os.path.join(DRAFTS, "Tranche_1_2_CoQ_Reissue_Draft_Set.html")),
    (os.path.join(TRACKER, "CoQ_compilation_v%s.xlsx" % VER), os.path.join(HERE, "coq_artifact_data.json")),
    (os.path.join(TRACKER, "CoQ_references_v%s.xlsx" % VER), os.path.join(HERE, "coq_artifact_data.json")),
    (MASTER_PAGE, MASTER),
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


def manifest(items, no_pdf=False):
    lines = ["# Purely Plant — QC package, %s — workbook v%s%s"
             % (STAMP, VER, " (no PDFs)" if no_pdf else ""), "",
             "Everything the QC desk has produced, as it stands. Every certificate in",
             "here is a **DRAFT**: watermarked, unsigned, its conformity statement",
             "unticked, and every field the desk cannot stand behind bracketed in red.",
             "**None has been issued.**", ""]
    if no_pdf:
        lines += ["The four compiled tranche PDFs are **not** in this archive — they come to",
                  "104 MiB together. Every certificate is still here as HTML, individually",
                  "under `certificates/individual/` and as two scrollable sets. The PDFs",
                  "download on their own from `deliverables/qc_gap_analysis/drafts/` in the",
                  "repository.", ""]
    lines += ["| file | size | what it is |", "| --- | ---: | --- |"]
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
    # The four tranche PDFs are 104 MiB of the 107 the archive otherwise carries,
    # and a reader who wants the workbook, the compilation and the reports does not
    # want to wait for them. --no-pdf drops the compiled certificate PDFs and
    # NOTHING ELSE: the individual certificates and the two scrollable draft sets
    # stay, so every document is still in the archive, as HTML rather than print.
    no_pdf = "--no-pdf" in sys.argv
    bad = stale()
    if bad:
        print("\nrefusing to package a stale build:")
        for derived, source in bad:
            print("  %s is older than %s" % (derived, source))
        print("\nrebuild it and run again.")
        return 2
    items = _items()
    suffix = ""
    if no_pdf:
        dropped = [a for a, _, _ in items if a.endswith(".pdf")]
        items = [(a, b, c) for a, b, c in items if not a.endswith(".pdf")]
        suffix = "_no_PDF"
        print("excluded %d compiled PDF(s): %s"
              % (len(dropped), ", ".join(os.path.basename(a) for a in dropped)))
    os.makedirs(OUT_DIR, exist_ok=True)
    # The archive names the workbook VERSION it carries as well as the day: two builds on
    # one day — v35 and v36 both on 16.09.2026 — would otherwise overwrite each other under
    # one name, and a person holding the file could not tell which they had.
    out = os.path.join(OUT_DIR, "PP_QC_Package_%s_v%s%s.zip" % (STAMP, VER, suffix))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("MANIFEST.md", manifest(items, no_pdf))
        for arc, src, _ in items:
            z.write(src, arc)
    print("%s: %d file(s), %s" % (os.path.relpath(out, ROOT), len(items) + 1,
                                  human(os.path.getsize(out))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
