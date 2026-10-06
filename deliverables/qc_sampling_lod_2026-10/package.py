#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Package PP-QC-SP-002/26 as three separate document packages (Head of QC, 06.10.2026):

  1  PLAN                      the sampling plan and execution protocol
  2  SAMPLING EXECUTION        per sampling day: QCT 024 receipt, QCSOP 011_A03, QCT 021, the
                               QASOP_031 label sheets, QCT 024 return, QCT 024 samples -> QC lab
  3  LOD ANALYSIS EXECUTION    one loss-on-drying execution record per group analysed together

Each package is a folder under out/ holding every DOCX and PDF, a merged packet PDF with a bookmark
per document (label sheets excluded: they print on perforated stock), and a zip of the folder.
BUILD_LOG.md records the engine version, the pp_verify result, the page count and a SHA-256 per file.
Run after the builders and the DOCX -> PDF conversion.

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


def day_docs(day):
    return [
        ("Ден %d — 1. QCT 024 пренос сеф-магацин → просторија за земање (D%d-RCPT) | Day %d — 1. QCT 024 transfer "
         "warehouse → sampling room" % (day, day, day), "S%d-1_QCT024_Transfer_Warehouse_to_Sampling_Day%d" % (day, day), True),
        ("Ден %d — 2. QCSOP 011_A03 визуелна инспекција | Day %d — 2. QCSOP 011_A03 visual inspection" % (day, day),
         "S%d-2_QCSOP011_A03_Visual_Inspection_Day%d" % (day, day), True),
        ("Ден %d — 3. QCT 021 пред и после мострирање | Day %d — 3. QCT 021 before and after sampling" % (day, day),
         "S%d-3_QCT021_Before_After_Sampling_Day%d" % (day, day), True),
        ("Ден %d — 4. QASOP_031_A05 етикети МОСТРИРАНО | Day %d — 4. QASOP_031_A05 SAMPLED bag labels" % (day, day),
         "S%d-4_QASOP031_A05_SAMPLED_Bag_Labels_Day%d" % (day, day), False),
        ("Ден %d — 5. QASOP_031_A07 етикети на примероци | Day %d — 5. QASOP_031_A07 sample labels" % (day, day),
         "S%d-5_QASOP031_A07_Sample_Labels_Day%d" % (day, day), False),
        ("Ден %d — 6. QCT 024 враќање во сеф-магацин (D%d-RET) | Day %d — 6. QCT 024 return to warehouse" % (day, day, day),
         "S%d-6_QCT024_Transfer_Return_to_Warehouse_Day%d" % (day, day), True),
        ("Ден %d — 7. QCT 024 примероци → КК лабораторија (D%d-SMP) | Day %d — 7. QCT 024 samples → QC laboratory"
         % (day, day, day), "S%d-7_QCT024_Transfer_Samples_to_QC_Lab_Day%d" % (day, day), True),
    ]


# (folder, package name, [(bookmark, stem, engine document?)])
PACKAGES = [
    ("1_PLAN", "PP-QC-SP-002_26_PACKAGE-1_PLAN", [
        ("PP-QC-SP-002/26 — план за земање примероци и губиток при сушење | sampling plan and loss on drying",
         "PP-QC-SP-002_26_Sampling_Plan_LoD_T1_T2", True)]),
    ("2_SAMPLING_EXECUTION", "PP-QC-SP-002_26_PACKAGE-2_SAMPLING_EXECUTION",
     [("0. Содржина на пакетот | Package index", "S0_Package_Index_Sampling_Execution", True)] + day_docs(1) + day_docs(2)),
    ("3_LOD_ANALYSIS_EXECUTION", "PP-QC-SP-002_26_PACKAGE-3_LOD_ANALYSIS_EXECUTION", [
        ("PP-QC-SP-002/26-LOD-01 — губиток при сушење, примероци од Ден 1 | loss on drying, Day-1 samples",
         "PP-QC-SP-002_26-LOD-01_LoD_Execution_Record_Day1_Samples", True),
        ("PP-QC-SP-002/26-LOD-02 — губиток при сушење, примероци од Ден 2 | loss on drying, Day-2 samples",
         "PP-QC-SP-002_26-LOD-02_LoD_Execution_Record_Day2_Samples", True)]),
]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pages(path):
    with pymupdf.open(path) as d:
        return d.page_count


def merge(folder, docs, target):
    merged = pymupdf.open()
    toc = []
    for title, stem, in_packet in docs:
        if not in_packet:
            continue
        with pymupdf.open(os.path.join(folder, stem + ".pdf")) as src:
            toc.append([1, title, merged.page_count + 1])
            merged.insert_pdf(src)
    merged.set_toc(toc)
    merged.save(target, garbage=3, deflate=True)
    merged.close()


def main():
    head = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    engine_ver = subprocess.run(["git", "-C", REPO, "log", "-1", "--format=%h %cs", "--", "pp-document-suite/scripts"],
                                capture_output=True, text=True).stdout.strip()
    lines = ["# Build log — PP-QC-SP-002/26 (in-house loss on drying before shipment, Tranches 1 and 2)", "",
             "Built %s UTC on repository head `%s`." % (datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M"), head),
             "Engine: `pp-document-suite/scripts` (python-docx), last engine commit `%s`; base template "
             "`assets/PP_BASE_TEMPLATE.docx`. Label sheets are plain python-docx on A4 perforated stock (no running header)."
             % engine_ver,
             "Render: LibreOffice Writer (`soffice --headless --convert-to pdf`), Carlito for Calibri.",
             "Status printed on every engine document: IN REVIEW — NOT FOR USE; rebuilt as v1.0 with an effective date only "
             "on the Head of QC's approval.", ""]
    failed = False
    for folder_name, name, docs in PACKAGES:
        folder = os.path.join(OUT, folder_name)
        packet = os.path.join(folder, "PACKET_%s.pdf" % name)
        merge(folder, docs, packet)
        zpath = os.path.join(OUT, name + ".zip")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for _, stem, _ in docs:
                for ext in (".docx", ".pdf"):
                    z.write(os.path.join(folder, stem + ext), os.path.join(name, stem + ext))
            z.write(packet, os.path.join(name, os.path.basename(packet)))
        lines += ["## %s" % name, "", "| File | pp_verify | Pages | SHA-256 |", "|---|---|---|---|"]
        for _, stem, engine_doc in docs:
            if engine_doc:
                v = subprocess.run([sys.executable, os.path.join(ENGINE, "pp_verify.py"), os.path.join(folder, stem + ".docx")],
                                   capture_output=True, text=True)
                res = "PASS" if "RESULT: PASS" in v.stdout else "FAIL"
                failed = failed or res == "FAIL"
            else:
                res = "label sheet"
            for ext in (".docx", ".pdf"):
                p = os.path.join(folder, stem + ext)
                lines.append("| `%s/%s` | %s | %s | `%s` |" % (folder_name, stem + ext, res if ext == ".docx" else "",
                                                             pages(p) if ext == ".pdf" else "", sha(p)))
        lines.append("| `%s/%s` | | %d | `%s` |" % (folder_name, os.path.basename(packet), pages(packet), sha(packet)))
        lines.append("| `%s` | | | `%s` |" % (os.path.basename(zpath), sha(zpath)))
        lines.append("")
        print("%-52s packet %3d pages  zip %8d bytes" % (name, pages(packet), os.path.getsize(zpath)))
    lines += ["Data: `SAMPLING_PLAN_T1_T2_2026-10.tsv` (`%s`), `bag_selection.tsv` (`%s`); notes in `DATA_NOTES.md`."
              % (sha(os.path.join(HERE, "SAMPLING_PLAN_T1_T2_2026-10.tsv")), sha(os.path.join(HERE, "bag_selection.tsv")))]
    with open(os.path.join(HERE, "BUILD_LOG.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    if failed:
        raise SystemExit("pp_verify FAIL")


if __name__ == "__main__":
    main()
