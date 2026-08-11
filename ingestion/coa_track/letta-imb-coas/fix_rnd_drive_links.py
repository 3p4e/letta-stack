#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Point the three R&D in-house CoA rows at the file, now that the file is filed.

GG1024, HPA1024 and OPM1024 each carry an in-house Purely Plant Report of Analysis, and
the register could not cite a file for any of them. GG1024's link said the document was
not in Drive at all; HPA1024's and OPM1024's pointed at their batch folder with the
admission "(folder, exact file unmatched)".

All three were in Drive the whole time — sitting in the staging folder
12lswtFOhrfxLSNZRJu7lv-hooqk0j15p, which is where the PDFs the knowledgebase was built
from live, and never copied into the CoA folder tree:

    GG1024.pdf    644 999 bytes   ->  new folder GG1024   (none existed; the other five
                                      R&D batches each had one)
    HPA1024.pdf   637 866 bytes   ->  HPA1024   (held only 197-13-K/M)
    OPM1024.pdf   647 093 bytes   ->  OPM1024   (held only 197-17-K/M)

Each is a CamScanner capture with no text layer, which is why the knowledgebase holds a
separate transcription (GG1024.txt and the equivalents) rather than extracted text — and
why a filename search for the certificate number never found them.

Only the Drive File Link column changes. No Parameter, Acceptance Criterion, Result,
Certificate Code, Issue Date or Issuing Institution is touched.
"""
import csv
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, "exports", "master_coa_table.tsv")

FIELDS = ["Seq", "Cultivation Batch", "P-Number", "Strain", "Parameter",
          "Acceptance Criterion", "Result", "Certificate Code", "Issue Date",
          "Issuing Institution", "Drive File Link"]

VIEW = "https://drive.google.com/file/d/%s/view"

# batch -> (link cell to replace, id of the copy now filed in the batch folder)
RELINK = {
    "GG1024": ("Not in Drive — in-house CoA held in the knowledgebase as GG1024.txt; "
               "no GG1024 folder exists under the CoA parent",
               "1hBg1kL2hM7OlvFCwu488aNMj0Rrny_JC"),
    "HPA1024": ("https://drive.google.com/drive/folders/"
                "1NwOwMGV2XKiSd2VGwnHdwYmIWsaLZXN8 (folder, exact file unmatched)",
                "1MIhYvfj3rHj3MqkKE2wfGAW0xlMQVzRo"),
    "OPM1024": ("https://drive.google.com/drive/folders/"
                "1SwEMG2znGwlCNHmcC48TvGI80cct7iMn (folder, exact file unmatched)",
                "1ekMcYjkE4pdgxKw00geQ0_tIy37FF50m"),
}


def main():
    with open(TSV, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))

    changed = Counter()
    for r in rows:
        batch = (r["Cultivation Batch"] or "").strip()
        if batch not in RELINK:
            continue
        old, fid = RELINK[batch]
        if (r["Drive File Link"] or "").strip() == old:
            r["Drive File Link"] = VIEW % fid
            changed[batch] += 1

    if not changed:
        print("no rows matched — already relinked?")
        return 0

    with open(TSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, delimiter="\t",
                           extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    print("rows relinked: %d" % sum(changed.values()))
    for b, n in sorted(changed.items()):
        print("   %-8s %3d rows -> %s" % (b, n, VIEW % RELINK[b][1]))

    left = sum(1 for r in rows
               if "unmatched" in (r["Drive File Link"] or "")
               or "Not in Drive" in (r["Drive File Link"] or ""))
    print("rows still without a file link: %d" % left)
    return 0


if __name__ == "__main__":
    sys.exit(main())
