#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write the eCoA Coverage Audit's finding into RAGflow itself, on the documents
that already exist there, instead of leaving it as a one-off answer in a chat
reply. This is the gap the eCOA_PIPE plan flagged as finding #2: the project's
own verified, structured readings of a document never made it back into
RAGflow's own record of that document, so a retrieval answer could never
reflect them.

    python3 patch_coverage_status.py [--dry-run]

Patches `meta_fields` on every eCOA_DB document whose identity (via
ecoa_identity.py, content-keyed, not filename-keyed) matches one of the 479
external certificates in /tmp/claude-0/ecoa_coverage_status_full.json, with:

    coverage_status         "cited" | "also_on_file" | "other_sheet_only" | "absent"
    coverage_evidence       where in CoQ_Analysis_Master_v48 it was found
    coverage_evidence_detail  which parameter(s)/result(s) it sources, where known
    coverage_checked_date    the date of this audit

meta_fields is queryable via RAGflow's own metadata_condition filter — the
mechanism the eCOA_DB dataset's own description already names as the intended
way to do an exact lookup, but that nothing had ever populated.

Only patches documents that already exist in a RAGflow dataset; a certificate
among the 479 with no RAGflow doc_id yet (not ingested) is skipped and listed,
not silently dropped — it gets this same treatment once it exists, by re-running
this script after ingestion.
"""
import argparse
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
DATASETS = {
    "dd3ea108a3fd11f1858cf58865604f65": "eCOA_DB",
    "71b9c168b4a311f1a370a99b32e82467": "eCOA_INGEST",
}
COVERAGE = "/tmp/claude-0/ecoa_coverage_status_full.json"
CHECKED_DATE = time.strftime("%Y-%m-%d")


def req(p, data=None, method=None):
    body = json.dumps(data).encode() if data is not None else None
    h = {"Authorization": "Bearer " + K, "Content-Type": "application/json"}
    r = urllib.request.Request(B + p, data=body, method=method or ("PUT" if body is not None else "GET"), headers=h)
    try:
        return json.load(urllib.request.urlopen(r, timeout=60))
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    coverage = json.load(open(COVERAGE, encoding="utf-8"))
    by_key = {}
    for r in coverage:
        ident = parse_name(r["filename"])
        k = identity_key(ident)
        if k:
            by_key[k] = r

    patched, skipped, not_found = 0, 0, []
    for ds_id, ds_name in DATASETS.items():
        docs = all_docs(ds_id)
        print("%s: %d documents" % (ds_name, len(docs)))
        for d in docs:
            ident = parse_name(d["name"])
            k = identity_key(ident)
            r = by_key.get(k)
            if r is None:
                skipped += 1
                continue
            meta = dict(d.get("meta_fields") or {})
            meta.update({
                "coverage_status": r["status"],
                "coverage_evidence": r.get("evidence", ""),
                "coverage_evidence_detail": r.get("evidence_detail", ""),
                "coverage_checked_date": CHECKED_DATE,
            })
            if a.dry_run:
                print("  WOULD PATCH %-45s -> %s" % (d["name"][:45], r["status"]))
            else:
                resp = req("/api/v1/datasets/%s/documents/%s" % (ds_id, d["id"]), {"meta_fields": meta})
                if resp.get("code") != 0:
                    print("  FAILED %s: %s" % (d["name"][:45], str(resp)[:200]))
                    continue
                print("  patched %-45s -> %s" % (d["name"][:45], r["status"]))
            patched += 1

    ingested_keys = set()
    for ds_id in DATASETS:
        for d in all_docs(ds_id):
            ident = parse_name(d["name"])
            k = identity_key(ident)
            if k:
                ingested_keys.add(k)
    for k, r in by_key.items():
        if k not in ingested_keys:
            not_found.append(r["filename"])

    print()
    print("patched: %d  |  RAGflow docs with no coverage match: %d  |  coverage certs not yet in any RAGflow dataset: %d"
          % (patched, skipped, len(not_found)))
    for f in not_found[:20]:
        print("  not yet ingested (no RAGflow doc to patch):", f)
    if len(not_found) > 20:
        print("  ... and %d more" % (len(not_found) - 20))


if __name__ == "__main__":
    main()
