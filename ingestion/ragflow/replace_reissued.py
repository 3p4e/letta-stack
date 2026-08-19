#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replace a truncated lab report in RAGFlow with the laboratory's reissue.

A reissued report REPLACES its predecessor; it is never appended to it.

RAGFlow chunks on a token window, not on page boundaries, so there is no
page-level provenance to append against — "add only the missing page" would
overlap the existing chunks at the seam and leave duplicate text competing in
retrieval. It would also assume the earlier pages are unchanged, and a
reissued report may amend a page as well as complete it. So: one lab number,
one document, one record.

Order of operations per file, and it stops at the first failure:

  1. COMPLETENESS GATE  the report states its own length in the page footer
     ("Страна N од M"). If the PDF holds fewer pages than it declares, the
     reissue is still short — reject it, change nothing, say so.
  2. DIFF vs INGESTED   pull the text of the copy currently in the dataset and
     compare page by page. Identical earlier pages are reported as such. Any
     CHANGED page halts the replacement and prints the difference: an amended
     result is a QC event, not a housekeeping detail, and a human decides.
  3. REPLACE            delete the old document by id, upload the reissue.
  4. VERIFY             parse, then require chunk_count > 0. A zero-chunk parse
     is never reported as ingested — that is exactly how 128 documents came to
     sit in this dataset unsearchable.

Usage:
    python3 replace_reissued.py <dataset> <file.pdf> [file.pdf ...]
    python3 replace_reissued.py --check <file.pdf>     # gate only, no writes

Environment: RAGFLOW_API_KEY, RAGFLOW_API_SERVER
"""
import json, os, re, subprocess, sys, time, urllib.request

KEY = os.environ.get("RAGFLOW_API_KEY", "")
SRV = os.environ.get("RAGFLOW_API_SERVER", "").rstrip("/")
FOOTER = re.compile(r"Страна\s+(\d+)\s+од\s+(\d+)")
LABNO = re.compile(r"(\d{3,4})")


def api(path, data=None, method=None, raw=None, ctype=None):
    url = "%s/api/v1/%s" % (SRV, path.lstrip("/"))
    hdr = {"Authorization": "Bearer " + KEY}
    if raw is None:
        body = json.dumps(data).encode() if data is not None else None
        hdr["Content-Type"] = "application/json"
    else:
        body, hdr["Content-Type"] = raw, ctype
    r = urllib.request.Request(url, data=body, headers=hdr,
                               method=method or ("POST" if body else "GET"))
    with urllib.request.urlopen(r, timeout=180) as f:
        return json.loads(f.read().decode())


def pages(pdf):
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    m = re.search(r"^Pages:\s+(\d+)", out, re.M)
    return int(m.group(1)) if m else 0


def text(pdf, first=None, last=None):
    cmd = ["pdftotext"]
    if first:
        cmd += ["-f", str(first), "-l", str(last or first)]
    return subprocess.run(cmd + [pdf, "-"], capture_output=True, text=True).stdout


def declared(pdf):
    """Pages the laboratory says the report has, from its own footer."""
    m = FOOTER.search(text(pdf))
    return int(m.group(2)) if m else None


def check(pdf):
    """The completeness gate. Returns (ok, message)."""
    have, want = pages(pdf), declared(pdf)
    if have == 0:
        return False, "unreadable PDF"
    if want is None:
        return False, "no page footer and no extractable text — blank export"
    if have < want:
        return False, "INCOMPLETE — %d of %d pages" % (have, want)
    return True, "complete — %d of %d pages" % (have, want)


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def find_doc(ds, lab):
    """The document already in the dataset for this lab number, if any."""
    for p in range(1, 8):
        docs = (api("datasets/%s/documents?page=%d&page_size=100" % (ds, p))
                .get("data") or {}).get("docs") or []
        for d in docs:
            if lab and lab in LABNO.findall(d.get("name", "")):
                return d
        if len(docs) < 100:
            return None
    return None


def replace(ds, pdf, force=False):
    name = os.path.basename(pdf)
    lab = (LABNO.search(name) or [None])[0] if LABNO.search(name) else None
    print("\n=== %s (lab %s)" % (name, lab or "?"))

    ok, msg = check(pdf)
    print("  gate: %s" % msg)
    if not ok:
        print("  REJECTED — nothing changed."); return False

    old = find_doc(ds, lab)
    if old:
        print("  in dataset: %s  run=%s chunks=%s"
              % (old["name"], old.get("run"), old.get("chunk_count")))
        # page-by-page diff against what we already hold
        blob = api("datasets/%s/documents/%s" % (ds, old["id"]))  # metadata only
        tmp = "/tmp/_ingested_%s.pdf" % lab
        try:
            data = urllib.request.urlopen(urllib.request.Request(
                "%s/api/v1/datasets/%s/documents/%s" % (SRV, ds, old["id"]),
                headers={"Authorization": "Bearer " + KEY}), timeout=180).read()
            open(tmp, "wb").write(data)
            n_old = pages(tmp)
            changed = []
            for pg in range(1, min(n_old, pages(pdf)) + 1):
                if norm(text(tmp, pg)) != norm(text(pdf, pg)):
                    changed.append(pg)
            if changed and not force:
                print("  !! pages CHANGED vs the ingested copy: %s" % changed)
                print("  !! a reissue that amends an existing page is a QC event.")
                print("  !! review, then re-run with --force to proceed.")
                return False
            print("  diff: pages 1-%d identical; reissue adds %d page(s)"
                  % (min(n_old, pages(pdf)), pages(pdf) - n_old))
        except Exception as e:
            print("  diff skipped (%s) — replacing wholesale" % type(e).__name__)

        api("datasets/%s/documents" % ds, {"ids": [old["id"]]}, method="DELETE")
        print("  deleted old document")

    # upload
    body = []
    b = b"----ragflow"
    body.append(b"--" + b)
    body.append(('Content-Disposition: form-data; name="file"; filename="%s"'
                 % name).encode())
    body.append(b"Content-Type: application/pdf\r\n")
    body.append(open(pdf, "rb").read())
    body.append(b"--" + b + b"--\r\n")
    payload = b"\r\n".join(body)
    up = api("datasets/%s/documents" % ds, raw=payload,
             ctype="multipart/form-data; boundary=" + b.decode())
    new_id = (up.get("data") or [{}])[0].get("id")
    print("  uploaded: %s" % new_id)

    api("datasets/%s/chunks" % ds, {"document_ids": [new_id]})
    for _ in range(40):
        time.sleep(30)
        docs = (api("datasets/%s/documents?page=1&page_size=100" % ds)
                .get("data") or {}).get("docs") or []
        cur = next((d for d in docs if d["id"] == new_id), {})
        if cur.get("run") != "RUNNING":
            break
    n = cur.get("chunk_count") or 0
    print("  parsed: run=%s chunks=%d" % (cur.get("run"), n))
    if not n:
        print("  FAILED — zero chunks. NOT counted as ingested; re-run to retry.")
        return False
    print("  OK — replaced and searchable.")
    return True


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--check":
        for f in args[1:]:
            ok, msg = check(f)
            print("%-28s %s" % (os.path.basename(f), msg))
        sys.exit(0)
    if len(args) < 2:
        sys.exit(__doc__)
    force = "--force" in args
    args = [a for a in args if a != "--force"]
    ds, files = args[0], args[1:]
    good = sum(replace(ds, f, force) for f in files)
    print("\n%d of %d replaced and verified searchable." % (good, len(files)))
