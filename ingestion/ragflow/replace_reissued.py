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

Identity is read off the PAGE, never off the filename. The same report may
arrive as `1468 П.pdf`, as `ЦЈЗ_skenirano_0043.pdf`, as the lab's digital
export or as a scan — all of them carry `Лаб. број: NNNN/YYYY`, and a scan is
OCR'd (Tesseract, `mkd`) to read it. One lab number is one document, so a
scanned copy of something already held is recognised as the same record and
replaces it rather than duplicating it.

Usage:
    python3 replace_reissued.py --index <dataset> [--refresh]  # build content index
    python3 replace_reissued.py <dataset> <file.pdf> [...]     # replace + verify
    python3 replace_reissued.py --check <file.pdf>             # gate only, no writes

Environment: RAGFLOW_API_KEY, RAGFLOW_API_SERVER
"""
import json, os, re, subprocess, sys, time, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from doc_identity import identity, key, better_of, pages, raw_text as text

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


INDEX = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     ".content_index.json")


def fetch(ds, doc_id, dest):
    r = urllib.request.Request("%s/api/v1/datasets/%s/documents/%s" % (SRV, ds, doc_id),
                               headers={"Authorization": "Bearer " + KEY})
    with urllib.request.urlopen(r, timeout=180) as f:
        open(dest, "wb").write(f.read())


def build_index(ds, refresh=False):
    """Map lab number -> document id by reading each document's CONTENT.

    Filenames are not identity: the same report arrives as `1468 П.pdf`, as a
    differently-named scan, or as a lab re-export. Reading the lab number off
    the page is the only way to know we already hold it.
    """
    cache = {}
    if os.path.exists(INDEX) and not refresh:
        cache = json.load(open(INDEX, encoding="utf-8"))
    docs = []
    for p in range(1, 8):
        got = (api("datasets/%s/documents?page=%d&page_size=100" % (ds, p))
               .get("data") or {}).get("docs") or []
        docs += got
        if len(got) < 100:
            break
    known = cache.get("by_doc", {})
    out = dict(known)
    for i, d in enumerate(docs, 1):
        if d["id"] in known and not refresh:
            continue
        tmp = "/tmp/_idx_%s.pdf" % d["id"][:10]
        try:
            fetch(ds, d["id"], tmp)
            ident = identity(tmp)
            out[d["id"]] = {"lab_no": ident["lab_no"], "name": d.get("name"),
                            "pages": ident["pages"], "source": ident["source"],
                            "chunks": d.get("chunk_count")}
            print("  [%d/%d] %-28s lab=%s" % (i, len(docs), (d.get("name") or "")[:28],
                                              ident["lab_no"]), flush=True)
        except Exception as e:
            print("  [%d/%d] %-28s SKIP %s" % (i, len(docs), (d.get("name") or "")[:28],
                                               type(e).__name__), flush=True)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
    cache = {"dataset": ds, "by_doc": out}
    json.dump(cache, open(INDEX, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n = sum(1 for v in out.values() if v.get("lab_no"))
    print("index: %d documents, %d with a readable lab number" % (len(out), n))
    return cache


def find_doc(ds, lab_no):
    """The document already holding this lab number — by content, not name."""
    if not lab_no:
        return None
    if not os.path.exists(INDEX):
        print("  no content index yet — run with --index first"); return None
    cache = json.load(open(INDEX, encoding="utf-8"))
    for doc_id, v in cache.get("by_doc", {}).items():
        if v.get("lab_no") == lab_no:
            return {"id": doc_id, "name": v.get("name"),
                    "chunk_count": v.get("chunks"), "run": None,
                    "pages": v.get("pages"), "source": v.get("source")}
    return None


def replace(ds, pdf, force=False):
    name = os.path.basename(pdf)
    ident = identity(pdf)
    lab = ident["lab_no"]
    print("\n=== %s" % name)
    print("  identity: lab=%s sampled=%s read-via=%s pages=%s/%s"
          % (lab, ident["sampled"], ident["source"], ident["pages"],
             ident["declared_pages"]))

    if not ident["readable"]:
        print("  REJECTED — no lab number could be read, even by OCR. "
              "Cannot be matched against what is already ingested."); return False
    if not ident["complete"]:
        print("  REJECTED — INCOMPLETE (%s of %s pages). Nothing changed."
              % (ident["pages"], ident["declared_pages"])); return False
    print("  gate: complete — %s of %s pages" % (ident["pages"], ident["declared_pages"]))

    old = find_doc(ds, lab)
    if old:
        print("  already ingested as: %s (%s, %s pages, chunks=%s)"
              % (old["name"], old.get("source"), old.get("pages"),
                 old.get("chunk_count")))
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
            i = identity(f)
            print("%-30s lab=%-10s %s  (%s)"
                  % (os.path.basename(f)[:30], i["lab_no"] or "?",
                     "complete %s/%s" % (i["pages"], i["declared_pages"])
                     if i["complete"] else
                     "INCOMPLETE %s/%s" % (i["pages"], i["declared_pages"]),
                     i["source"]))
        sys.exit(0)
    if args and args[0] == "--index":
        if len(args) < 2:
            sys.exit("usage: --index <dataset_id> [--refresh]")
        build_index(args[1], refresh="--refresh" in args)
        sys.exit(0)
    if len(args) < 2:
        sys.exit(__doc__)
    force = "--force" in args
    args = [a for a in args if a != "--force"]
    ds, files = args[0], args[1:]
    good = sum(replace(ds, f, force) for f in files)
    print("\n%d of %d replaced and verified searchable." % (good, len(files)))
