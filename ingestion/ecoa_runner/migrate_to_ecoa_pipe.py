#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ingest the renamed eCoA_DATABASE corpus into eCOA_INGEST without duplicating
what eCOA_DB already holds.

    python3 migrate_to_ecoa_pipe.py plan               # dry run: what would be skipped/ingested
    python3 migrate_to_ecoa_pipe.py run                # upload the genuinely-new files, then ingest
    python3 migrate_to_ecoa_pipe.py run NAME [NAME...] # only these (still checked against eCOA_DB)
    python3 migrate_to_ecoa_pipe.py status              # list eCOA_INGEST's documents and their state

This replaces `ingest_new_documents.py`'s `have = {d['name']: d for d in all_docs()}`
filename-exact-match dedup, which the 20.09.2026 rename of eCoA_DATABASE broke —
every one of eCOA_DB's 283 documents still carries its pre-rename name, so a bare
name comparison would see all 520 renamed files as "new" and duplicate all 283.

Dedup here is content-keyed instead, via `common/ecoa_identity.py`: each file in
eCOA_DB and each file under `ECOA_PDF_DIR` is reduced to (lab, doc code, date[,
batch]) regardless of which of the two naming schemes it's spelled in, so a
rename — this one or any future one — can never again produce a duplicate.
A run against the real corpus (283 eCOA_DB names against the 20.09.2026 rename
log's 520 new names) found exactly 2 eCOA_DB documents with no match at all
(both lab "DFL", batch P050192, 17.11.2025) — almost certainly a naming scheme
this pipeline has never seen and so didn't rename; `plan` below will call that
out explicitly rather than silently either skipping or duplicating it.
"""
import importlib.util
import json
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "common"))
from ecoa_identity import identity_key, parse_name  # noqa: E402

B = os.environ["RAGFLOW_API_SERVER"].rstrip("/")
K = os.environ["RAGFLOW_API_KEY"]
DS_NEW = "71b9c168b4a311f1a370a99b32e82467"   # eCOA_INGEST
AID_NEW = "405267c4b4a311f1a370a99b32e82467"  # eCOA_PIPE
DS_OLD = "dd3ea108a3fd11f1858cf58865604f65"   # eCOA_DB (the dedup source, read-only here)
PDFDIR = os.environ.get("ECOA_PDF_DIR", HERE + "/incoming_pdfs")
LOG = HERE + "/migrate_to_ecoa_pipe.log"


def say(m):
    print(m, flush=True)
    open(LOG, "a").write(time.strftime("%H:%M:%S ") + m + "\n")


def req(p, data=None, method=None, raw=None, ctype=None):
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    h = {"Authorization": "Bearer " + K, "Content-Type": ctype or "application/json"}
    r = urllib.request.Request(B + p, data=body, method=method or ("POST" if body is not None else "GET"), headers=h)
    try:
        return json.load(urllib.request.urlopen(r, timeout=300))
    except urllib.error.HTTPError as e:
        return {"HTTPError": e.code, "body": e.read()[:400].decode("utf8", "replace")}


def all_docs(dataset_id):
    docs = []
    for pg in range(1, 20):
        dd = req("/api/v1/datasets/%s/documents?page=%d&page_size=100" % (dataset_id, pg))["data"]["docs"]
        if not dd:
            break
        docs += dd
    return docs


def keys_of(dataset_id):
    """(identity key) -> document name, for every document a dataset holds.
    A name this module cannot parse is reported, never silently dropped."""
    have, unparsed = {}, []
    for d in all_docs(dataset_id):
        ident = parse_name(d["name"])
        if ident is None:
            unparsed.append(d["name"])
            continue
        have[identity_key(ident)] = d["name"]
    return have, unparsed


def already_ingested_keys():
    """What eCOA_INGEST — the DESTINATION — already holds.

    This used to read eCOA_DB instead, and that was wrong in a way the gate
    would have caught only after a wasted run. eCOA_INGEST is not a top-up of
    eCOA_DB, it is the dataset that REPLACES it: verify_ecoa_ingest.py's first
    check is that every eCOA_DB document has a match in eCOA_INGEST, and the
    owner's condition for deleting eCOA_DB is that the new set holds everything
    the old one did. Skipping a file because eCOA_DB already has it would have
    ingested only the 239 genuinely-new certificates, left the other 281 out of
    the replacement, and then failed completeness on all 281.

    So the whole renamed corpus goes in, and the dedup is against the
    destination — which is what makes a re-run safe: an interrupted or repeated
    run ingests only what is genuinely missing, however many times it is run.
    """
    return keys_of(DS_NEW)


def candidate_files():
    """The renamed corpus on disk. This script is meant to be run on the machine
    that holds eCoA_DATABASE, so a wrong ECOA_PDF_DIR is the most likely way a
    run goes wrong — it says so plainly rather than raising a traceback, and an
    empty directory is called out too, because "0 to ingest" on a silent empty
    folder reads exactly like "already done"."""
    if not os.path.isdir(PDFDIR):
        raise SystemExit(
            "ECOA_PDF_DIR is not a directory: %r\n"
            "Point it at the renamed eCoA_DATABASE folder, e.g.\n"
            '  set ECOA_PDF_DIR=C:\\Users\\Agent Zero\\My Drive\\1. PP\\DATA_B\\QC_eCoA\\eCoA_DATABASE'
            % PDFDIR)
    pdfs = sorted(n for n in os.listdir(PDFDIR) if n.lower().endswith(".pdf"))
    if not pdfs:
        raise SystemExit("no PDFs in ECOA_PDF_DIR (%r) — nothing to ingest, which is "
                         "not the same as everything being ingested already." % PDFDIR)
    return pdfs


def plan(names=None):
    have, unparsed = already_ingested_keys()
    say("eCOA_INGEST (destination) already holds: %d document(s), %d unparsed by ecoa_identity"
        % (len(have) + len(unparsed), len(unparsed)))
    for n in unparsed:
        say("  UNPARSED (cannot be deduped against, needs a human look): %s" % n)

    names = names or candidate_files()
    to_ingest, dupes, bad = [], [], []
    for n in names:
        ident = parse_name(n)
        if ident is None:
            bad.append(n)
            continue
        k = identity_key(ident)
        if k in have:
            dupes.append((n, have[k]))
        else:
            to_ingest.append(n)

    say("candidates: %d  ->  %d already in eCOA_INGEST (skip)  |  %d to ingest  |  %d unparsed"
        % (len(names), len(dupes), len(to_ingest), len(bad)))
    for n, matched in dupes[:20]:
        say("  SKIP  %s  (already in eCOA_INGEST as: %s)" % (n, matched))
    if len(dupes) > 20:
        say("  ... and %d more skips" % (len(dupes) - 20))
    for n in bad:
        say("  UNPARSED candidate (needs a human look, not auto-skipped or auto-ingested): %s" % n)

    # eCOA_DB's overlap is reported, never acted on. It is the retirement story —
    # how much of the dataset being replaced this corpus actually covers — and
    # anything of eCOA_DB's that the corpus does NOT cover is the thing that will
    # block deletion later, so it is worth seeing now rather than at the gate.
    old, old_unparsed = keys_of(DS_OLD)
    corpus = {identity_key(parse_name(n)) for n in names if parse_name(n)}
    uncovered = [v for k, v in old.items() if k not in corpus]
    say("eCOA_DB (to be retired): %d document(s); %d of them are NOT in this corpus%s"
        % (len(old) + len(old_unparsed), len(uncovered),
           " and would block deletion" if uncovered else ""))
    for n in uncovered[:20]:
        say("  NOT COVERED by the renamed corpus: %s" % n)
    if len(uncovered) > 20:
        say("  ... and %d more" % (len(uncovered) - 20))
    for n in old_unparsed:
        say("  eCOA_DB name unparsed, so coverage unknown: %s" % n)
    return to_ingest, dupes, bad


def upload(name):
    b = b"----ragflow" + str(int(time.time() * 1000)).encode()
    parts = [b"--" + b,
             ('Content-Disposition: form-data; name="file"; filename="%s"' % name).encode(),
             b"Content-Type: application/pdf\r\n",
             open(os.path.join(PDFDIR, name), "rb").read(),
             b"--" + b + b"--\r\n"]
    r = req("/api/v1/datasets/%s/documents" % DS_NEW, raw=b"\r\n".join(parts),
            ctype="multipart/form-data; boundary=" + b.decode())
    if r.get("code") != 0:
        say("  upload FAILED %s: %s" % (name, str(r)[:300]))
        return None
    return r["data"][0]["id"]


def gate(doc_id):
    QG = importlib.util.spec_from_file_location("qg", HERE + "/quality_guard.py")
    m = importlib.util.module_from_spec(QG)
    QG.loader.exec_module(m)
    ch = (req("/api/v1/datasets/%s/documents/%s/chunks?page=1&page_size=100" % (DS_NEW, doc_id))["data"].get("chunks") or [])
    if not ch:
        return False, "no chunks"          # "status DONE lies" — never trust status alone
    for c in ch:
        blob = str(c.get("important_keywords")) + str(c.get("questions"))
        if "ERROR" in blob:
            return False, "error text in indexed fields"
        ok, probs = m.check(c.get("content") or "")
        if not ok:
            return False, "; ".join(probs)
        if not c.get("questions"):
            return False, "questions empty"
        if not c.get("important_keywords"):
            return False, "keywords empty"
    return True, "ok (%d chunk(s))" % len(ch)


def run(names=None, timeout=40 * 60):
    to_ingest, dupes, bad = plan(names)
    if not to_ingest:
        say("nothing new to ingest"); return
    ids = {}
    for n in to_ingest:
        did = upload(n)
        if did:
            ids[n] = did
            say("uploaded %s -> %s" % (n, did))
    if not ids:
        return
    r = req("/api/v1/documents/ingest", {"doc_ids": list(ids.values()), "run": 1, "delete": True}, "POST")
    say("ingest queued %d doc(s) -> %s" % (len(ids), str(r)[:200]))
    deadline = time.time() + timeout
    pending = set(ids.values())
    while pending and time.time() < deadline:
        time.sleep(20)
        cur = {d["id"]: d for d in all_docs(DS_NEW) if d["id"] in pending}
        for did, d in cur.items():
            if d.get("run") in ("DONE", "FAIL") and float(d.get("progress") or 0) in (1.0, -1.0):
                pending.discard(did)
                ok, why = gate(did) if d.get("run") == "DONE" else (False, "run=FAIL")
                msg = (d.get("progress_msg") or "").strip().splitlines()
                say("%-8s %-48s %s | %s" % ("GATE-OK" if ok else "HELD", d["name"][:48], why,
                                             (msg[-1][:160] if msg else "")))
    for did in pending:
        say("TIMEOUT still running: %s" % did)


def status():
    for d in sorted(all_docs(DS_NEW), key=lambda x: x["create_date"]):
        msg = (d.get("progress_msg") or "").strip().splitlines()
        print("%-48s run=%-6s prog=%-5s chunks=%s | %s"
              % (d["name"][:48], d.get("run"), d.get("progress"), d.get("chunk_count"),
                 (msg[-1][:150] if msg else "")))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "plan"
    if cmd == "plan":
        plan(sys.argv[2:] or None)
    elif cmd == "status":
        status()
    elif cmd == "run":
        run(sys.argv[2:] or None)
    else:
        raise SystemExit(__doc__)
