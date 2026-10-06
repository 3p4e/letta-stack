#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Package the campaign documents: two packages (the plan on its own; the execution records ER-01 and
ER-02 with their merged packet), the full three-document packet PDF with a bookmark per document, and
BUILD_LOG.md with the engine version, the verify results and a SHA-256 per delivered file. Run after
build_campaign_docs.py and the DOCX -> PDF conversion.

    python3 package.py
"""
import datetime
import hashlib
import os
import subprocess
import sys
import zipfile

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "out")
ENGINE = os.path.join(REPO, "pp-document-suite", "scripts")
DOCS = [
    ("PP-QC-SP-002/26 — Sampling plan and loss on drying, Tranches 1 and 2", "PP-QC-SP-002_26_Sampling_Plan_LoD_T1_T2"),
    ("PP-QC-SP-002/26-ER-01 — Execution record, Day 1", "PP-QC-SP-002_26-ER-01_Execution_Record_Day1"),
    ("PP-QC-SP-002/26-ER-02 — Execution record, Day 2", "PP-QC-SP-002_26-ER-02_Execution_Record_Day2"),
]
PLAN_DOCS = DOCS[:1]
ER_DOCS = DOCS[1:]
# Two separate packages (Head of QC, 06.10.2026): the plan on its own, the execution records on their own.
PACKET_ALL = os.path.join(OUT, "PACKET_PP-QC-SP-002_26_Plan_ER-01_ER-02.pdf")
PACKET_ER = os.path.join(OUT, "PACKET_PP-QC-SP-002_26_Execution_Records_ER-01_ER-02.pdf")
ZIP_PLAN = os.path.join(OUT, "PP-QC-SP-002_26_PLAN_DOCX_PDF.zip")
ZIP_ER = os.path.join(OUT, "PP-QC-SP-002_26_EXECUTION_RECORDS_DOCX_PDF.zip")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def merge(docs, target):
    merged = pymupdf.open()
    toc = []
    for title, stem in docs:
        src = pymupdf.open(os.path.join(OUT, stem + ".pdf"))
        toc.append([1, title, merged.page_count + 1])
        merged.insert_pdf(src)
        src.close()
    merged.set_toc(toc)
    merged.save(target, garbage=3, deflate=True)
    merged.close()


def zip_docs(docs, extra, target):
    files = []
    for _, stem in docs:
        files += [stem + ".docx", stem + ".pdf"]
    files += extra
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(os.path.join(OUT, f), f)
    return files


def main():
    merge(DOCS, PACKET_ALL)
    merge(ER_DOCS, PACKET_ER)
    plan_files = zip_docs(PLAN_DOCS, [], ZIP_PLAN)
    er_files = zip_docs(ER_DOCS, [os.path.basename(PACKET_ER)], ZIP_ER)
    files = plan_files + er_files + [os.path.basename(PACKET_ALL), os.path.basename(ZIP_PLAN), os.path.basename(ZIP_ER)]

    verify = {}
    for _, stem in DOCS:
        v = subprocess.run([sys.executable, os.path.join(ENGINE, "pp_verify.py"), os.path.join(OUT, stem + ".docx")],
                           capture_output=True, text=True)
        verify[stem] = "PASS" if "RESULT: PASS" in v.stdout else "FAIL"
    engine_ver = subprocess.run(["git", "-C", REPO, "log", "-1", "--format=%h %cs", "--", "pp-document-suite/scripts"],
                                capture_output=True, text=True).stdout.strip()
    head = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()

    lines = ["# Build log — PP-QC-SP-002/26 (in-house loss on drying before shipment, Tranches 1 and 2)", "",
             "Built %s UTC on repository head `%s`." % (datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M"), head),
             "Engine: `pp-document-suite/scripts` (python-docx), last engine commit `%s`; base template `assets/PP_BASE_TEMPLATE.docx`." % engine_ver,
             "Render: LibreOffice Writer (`soffice --headless --convert-to pdf`), Carlito for Calibri; the running header's "
             "document name falls back to DejaVu Sans where the template asks for Arial Narrow (the engine's known behaviour).",
             "Status printed on every document: IN REVIEW — NOT FOR USE, version IN REVIEW; rebuilt as v1.0 with an "
             "effective date only on the Head of QC's approval.", "",
             "| File | pp_verify | Pages | SHA-256 |", "|---|---|---|---|"]
    for _, stem in DOCS:
        for ext in (".docx", ".pdf"):
            p = os.path.join(OUT, stem + ext)
            pages = pymupdf.open(p).page_count if ext == ".pdf" else ""
            lines.append("| `%s` | %s | %s | `%s` |" % (stem + ext, verify[stem] if ext == ".docx" else "", pages, sha(p)))
    lines.append("| `%s` | | %d | `%s` |" % (os.path.basename(PACKET_ER), pymupdf.open(PACKET_ER).page_count, sha(PACKET_ER)))
    lines.append("| `%s` | | %d | `%s` |" % (os.path.basename(PACKET_ALL), pymupdf.open(PACKET_ALL).page_count, sha(PACKET_ALL)))
    lines.append("| `%s` | | | `%s` |" % (os.path.basename(ZIP_PLAN), sha(ZIP_PLAN)))
    lines.append("| `%s` | | | `%s` |" % (os.path.basename(ZIP_ER), sha(ZIP_ER)))
    lines += ["", "Data: `SAMPLING_PLAN_T1_T2_2026-10.tsv` (`%s`), `bag_selection.tsv` (`%s`); notes in `DATA_NOTES.md`."
              % (sha(os.path.join(HERE, "SAMPLING_PLAN_T1_T2_2026-10.tsv")), sha(os.path.join(HERE, "bag_selection.tsv")))]
    with open(os.path.join(HERE, "BUILD_LOG.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    for f in files:
        print("%9d  %s" % (os.path.getsize(os.path.join(OUT, f)), f))
    print("verify:", verify)
    if "FAIL" in verify.values():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
