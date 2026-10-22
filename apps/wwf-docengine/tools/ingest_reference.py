#!/usr/bin/env python3
"""Load reference documents into the DocEngine: python3 ingest_reference.py <kind> <dir> [--dry-run]

kind  approved  the approved, in-use documents (text of the Word file) — stored and indexed in DB3_PP_CURRENT
      wip       the ACME_SOP work in progress — stored only, never indexed
dir   *.md files with a YAML front matter (code, version, title_mk, title_en, effective_date, department,
      parent, package, source_name, drive_docx_id / drive_id, drive_scan_ids, drive_folder)

Runs where the DocEngine answers on DOCENGINE_URL (default http://localhost:8000) with DOCENGINE_API_KEY, e.g. inside
the pp-docengine container. One PUT /reference per file; an unchanged text is skipped by the engine. Prints one line
per file and a summary; exits 1 if any file failed. See docs/DB3_RAGFLOW_PIPELINE_HANDOFF.md.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

FIELDS = ("code", "version", "title_mk", "title_en", "effective_date", "department", "parent", "package")


def parse(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError("no front matter")
    _, fm, body = text.split("---", 2)
    meta = yaml.safe_load(fm) or {}
    doc = {k: str(meta.get(k) or "") for k in FIELDS}
    doc["source"] = {"name": meta.get("source_name", ""),
                     "drive_id": meta.get("drive_docx_id") or meta.get("drive_id", ""),
                     "drive_scan_ids": meta.get("drive_scan_ids") or [],
                     "folder": meta.get("drive_folder", "")}
    doc["markdown"] = body.strip()
    return doc


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] not in ("approved", "wip"):
        print(__doc__)
        return 2
    kind, folder, dry = argv[0], Path(argv[1]), "--dry-run" in argv
    base = os.environ.get("DOCENGINE_URL", "http://localhost:8000").rstrip("/")
    key = os.environ.get("DOCENGINE_API_KEY") or os.environ.get("API_KEY", "")
    ok = failed = skipped = 0
    for f in sorted(folder.glob("*.md")):
        try:
            doc = {"kind": kind, **parse(f)}
            if len(doc["markdown"]) < 20:
                raise ValueError("text shorter than 20 characters")
            if dry:
                print(f"DRY  {f.name}: {doc['code']} v{doc['version']} {len(doc['markdown'])} chars")
                ok += 1
                continue
            req = urllib.request.Request(base + "/reference", method="PUT", data=json.dumps(doc).encode(),
                                         headers={"Content-Type": "application/json", "X-API-Key": key})
            r = json.load(urllib.request.urlopen(req, timeout=180))
            if r.get("index_error"):
                print(f"WARN {f.name}: stored {r['code']}, not indexed: {r['index_error']}")
                failed += 1
            elif not r.get("changed"):
                print(f"SAME {f.name}: {r['code']} unchanged")
                skipped += 1
            else:
                print(f"OK   {f.name}: {r['code']} id={r['id']} ragflow={r.get('ragflow_doc_id') or '-'}")
                ok += 1
        except (ValueError, urllib.error.URLError, OSError) as e:
            detail = e.read().decode()[:200] if isinstance(e, urllib.error.HTTPError) else str(e)
            print(f"FAIL {f.name}: {detail}")
            failed += 1
    print(f"done: {ok} stored, {skipped} unchanged, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
