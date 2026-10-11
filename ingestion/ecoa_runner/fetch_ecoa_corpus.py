#!/usr/bin/env python3
"""Download the ACTIVE certificates of Drive `eCoA_DATABASE` into a local folder, verified.

    python3 fetch_ecoa_corpus.py /opt/ecoa_ingest/pdf

The folder is shared by link, so nothing here needs a Google credential:
  - `_eCoA_DATABASE_INDEX.xlsx` (in the folder) lists every file with its Status and SHA-256;
  - `drive.google.com/embeddedfolderview?id=<folder>` lists every file id in one page.
Only rows with Status ACTIVE are fetched (the 41 redacted in-house QCCoAs and the superseded file are
excluded, Head of QC ruling 16). A file is kept only if its SHA-256 equals the index's; a re-run skips
files already present and verified, so it is safe to repeat.
"""
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import unicodedata

import openpyxl

FOLDER = "1SmOicCRa8KEqoB-YlCojdap161YMQ-Di"
INDEX_ID = "1POqGQOU0B_eCWxCw2gUckvbcBfWsyW7l"
DL = "https://drive.usercontent.google.com/download?id=%s&export=download"


def get(url, path):
    subprocess.run(["curl", "-s", "-L", "--retry", "3", "-o", path, url], check=False)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest() if os.path.exists(path) else None


def main(out):
    os.makedirs(out, exist_ok=True)
    work = os.path.dirname(os.path.abspath(out))
    index, view = os.path.join(work, "index.xlsx"), os.path.join(work, "folder.html")
    get(DL % INDEX_ID, index)
    get("https://drive.google.com/embeddedfolderview?id=" + FOLDER, view)
    page = open(view, encoding="utf8").read()
    ids = {unicodedata.normalize("NFC", html.unescape(t)): i for i, t in re.findall(
        r'href="https://drive\.google\.com/file/d/([\w-]+)/view[^"]*".*?<div class="flip-entry-title">(.*?)</div>', page, re.S)}
    ws = openpyxl.load_workbook(index, read_only=True)["INDEX"]
    rows = [r for r in list(ws.iter_rows(values_only=True))[1:] if r[0] and r[1] == "ACTIVE"]
    ok, bad = 0, []
    for r in rows:
        name, want = r[8], r[12]
        p = os.path.join(out, name)
        if sha(p) == want:
            ok += 1
            continue
        fid = ids.get(unicodedata.normalize("NFC", name))
        if not fid:
            bad.append(("no drive id", name))
            continue
        for _ in range(3):
            get(DL % fid, p)
            if sha(p) == want:
                ok += 1
                break
        else:
            if os.path.exists(p):
                os.remove(p)
            bad.append(("sha256 mismatch", name))
    print("ACTIVE in index: %d   verified on disk: %d   problems: %d" % (len(rows), ok, len(bad)))
    for why, name in bad:
        print("  %s: %s" % (why, name))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "pdf"))
