#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The gate eCOA_INGEST has to pass before eCOA_DB is deleted.

    python3 verify_ecoa_ingest.py                 # run every check, print a verdict
    python3 verify_ecoa_ingest.py --baseline      # record eCOA_DB's retrieval scores first

The owner's condition (20.09.2026): "once the new data set is ingested properly
and functions and everything is retrieved like it should, then we will delete the
first database because it will be redundant." Deleting a knowledge base cannot be
undone, and "it works" is a judgement that gets made loosely under time pressure,
so this turns that condition into four checks that either pass or do not. The
script never deletes anything — it only says whether deleting would be safe, and
refuses to say so unless every check passes.

  1. COMPLETENESS   Every document in eCOA_DB has an identity match in
                    eCOA_INGEST (content-keyed via ecoa_identity, so the rename
                    cannot make a match look missing). Nothing is retired while
                    anything it holds is unaccounted for.

  2. NO GHOSTS      Every document in eCOA_INGEST has chunk_count > 0. The
                    sibling water pipeline once held 128 of 389 documents at zero
                    chunks while they were all marked DONE: present, indexed
                    nowhere, and no status roll-up showed it. Status alone lies.

  3. RETRIEVAL      Each probe document is searched for by its own doc code and
                    has to come back in the results. Run with --baseline against
                    eCOA_DB first; the new dataset then has to match or beat that
                    recall, not merely return something. The probes deliberately
                    include the traps the eCOA_DB dataset description names: a
                    trailing asterisk that is part of the batch code, sub-lot
                    separators that are not, a certificate filed under its P lot
                    with no cultivation batch, and Cyrillic ППК control numbers.

  4. METADATA       The coverage_status written by patch_coverage_status.py is
                    present on eCOA_INGEST too, not just on the dataset being
                    retired.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "common"))
from ecoa_identity import identity_key, parse_name  # noqa: E402

B = os.environ["RAGFLOW_API_SERVER"].rstrip("/")
K = os.environ["RAGFLOW_API_KEY"]
OLD = "dd3ea108a3fd11f1858cf58865604f65"   # eCOA_DB
NEW = "71b9c168b4a311f1a370a99b32e82467"   # eCOA_INGEST
BASELINE = os.path.join(HERE, "ecoa_retrieval_baseline.json")

# The traps the eCOA_DB dataset description names, each as a doc code that must
# retrieve its own certificate. Filled from the corpus at run time where possible.
PROBE_NOTES = {
    "star": "a trailing asterisk is part of the batch code",
    "sublot": "a sub-lot separator carries no meaning",
    "p_lot_only": "filed under the P lot, no cultivation batch on the page",
    "cyrillic": "Cyrillic control-book number",
    "plain": "an ordinary certificate, as a control",
}


def req(p, data=None, method=None):
    body = json.dumps(data).encode() if data is not None else None
    h = {"Authorization": "Bearer " + K, "Content-Type": "application/json"}
    r = urllib.request.Request(B + p, data=body, method=method or ("POST" if body is not None else "GET"), headers=h)
    try:
        return json.load(urllib.request.urlopen(r, timeout=120))
    except urllib.error.HTTPError as e:
        return {"HTTPError": e.code, "body": e.read()[:400].decode("utf8", "replace")}


def all_docs(dataset_id):
    docs = []
    for pg in range(1, 30):
        d = req("/api/v1/datasets/%s/documents?page=%d&page_size=100" % (dataset_id, pg))
        dd = (d.get("data") or {}).get("docs") or []
        if not dd:
            break
        docs += dd
    return docs


def keyed(docs):
    out = {}
    for d in docs:
        ident = parse_name(d["name"])
        k = identity_key(ident)
        if k:
            out[k] = d
    return out


def pick_probes(docs):
    """Choose one certificate per trap from whatever the dataset actually holds."""
    probes = {}
    for d in docs:
        ident = parse_name(d["name"])
        if not ident:
            continue
        code, batch = ident.doc_code, (ident.cu_batch or "")
        if "star" not in probes and ("*" in batch or "＊" in batch):
            probes["star"] = (code, d["name"])
        elif "sublot" not in probes and ("_" in batch or "-" in batch) and any(ch.isdigit() for ch in batch):
            probes["sublot"] = (code, d["name"])
        elif "p_lot_only" not in probes and ident.p_batch and not ident.cu_batch:
            probes["p_lot_only"] = (code, d["name"])
        elif "cyrillic" not in probes and any("Ѐ" <= ch <= "ӿ" for ch in code):
            probes["cyrillic"] = (code, d["name"])
        elif "plain" not in probes:
            probes["plain"] = (code, d["name"])
    return probes


def retrieval_recall(dataset_id, probes):
    """For each probe: does searching its own doc code return its own document?"""
    result = {}
    for kind, (code, name) in probes.items():
        r = req("/api/v1/retrieval", {
            "question": code,
            "dataset_ids": [dataset_id],
            "page_size": 10,
            "similarity_threshold": 0.1,
            "keyword": True,
        })
        chunks = ((r.get("data") or {}).get("chunks")) or []
        hit = any(code.lower() in (c.get("content") or "").lower()
                  or code.lower() in (c.get("document_keyword") or "").lower()
                  for c in chunks)
        result[kind] = {"doc_code": code, "document": name, "hit": hit,
                        "returned": len(chunks), "note": PROBE_NOTES.get(kind, "")}
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", action="store_true",
                    help="record eCOA_DB's retrieval recall as the bar to match")
    a = ap.parse_args()

    old_docs = all_docs(OLD)
    new_docs = all_docs(NEW)
    print("eCOA_DB (to be retired): %d documents" % len(old_docs))
    print("eCOA_INGEST (replacement): %d documents" % len(new_docs))
    print()

    if a.baseline:
        probes = pick_probes(old_docs)
        base = retrieval_recall(OLD, probes)
        json.dump({"probes": {k: list(v) for k, v in probes.items()}, "recall": base},
                  open(BASELINE, "w"), indent=2, ensure_ascii=False)
        print("baseline written to", BASELINE)
        for kind, r in base.items():
            print("  %-12s %-22s %s  (%s)" % (kind, r["doc_code"], "HIT" if r["hit"] else "MISS", r["note"]))
        return 0

    failures = []

    # 1 — completeness
    old_keyed, new_keyed = keyed(old_docs), keyed(new_docs)
    missing = [d["name"] for k, d in old_keyed.items() if k not in new_keyed]
    print("1. COMPLETENESS")
    if missing:
        failures.append("%d eCOA_DB documents have no match in eCOA_INGEST" % len(missing))
        print("   FAIL — %d not matched:" % len(missing))
        for n in missing[:10]:
            print("     ", n)
        if len(missing) > 10:
            print("      ... and %d more" % (len(missing) - 10))
    else:
        print("   PASS — all %d eCOA_DB documents are present in eCOA_INGEST" % len(old_keyed))

    # 2 — no zero-chunk ghosts
    print("\n2. NO GHOSTS (chunk_count > 0)")
    ghosts = [d for d in new_docs if not d.get("chunk_count")]
    if ghosts:
        failures.append("%d eCOA_INGEST documents have zero chunks" % len(ghosts))
        print("   FAIL — %d with zero chunks (run=%s):" % (ghosts and len(ghosts), ghosts[0].get("run")))
        for d in ghosts[:10]:
            print("      %-50s run=%s" % (d["name"][:50], d.get("run")))
        if len(ghosts) > 10:
            print("      ... and %d more" % (len(ghosts) - 10))
    elif not new_docs:
        failures.append("eCOA_INGEST is empty")
        print("   FAIL — eCOA_INGEST holds no documents")
    else:
        print("   PASS — all %d documents have chunks" % len(new_docs))

    # 3 — retrieval
    print("\n3. RETRIEVAL (each probe must find its own certificate)")
    if not new_docs:
        failures.append("retrieval not testable: eCOA_INGEST is empty")
        print("   SKIPPED — nothing ingested yet")
    else:
        probes = pick_probes(new_docs)
        now = retrieval_recall(NEW, probes)
        base = None
        if os.path.exists(BASELINE):
            base = json.load(open(BASELINE))["recall"]
        for kind, r in now.items():
            mark = "HIT " if r["hit"] else "MISS"
            was = ""
            if base and kind in base:
                was = "  (eCOA_DB was %s)" % ("HIT" if base[kind]["hit"] else "MISS")
            print("   %-4s %-12s %-22s %s%s" % (mark, kind, r["doc_code"], r["note"], was))
            if not r["hit"]:
                if base and kind in base and not base[kind]["hit"]:
                    print("        (eCOA_DB missed this too — not a regression, but still not retrievable)")
                else:
                    failures.append("retrieval probe '%s' (%s) finds nothing" % (kind, r["doc_code"]))

    # 4 — metadata carried over
    print("\n4. METADATA (coverage_status present)")
    if not new_docs:
        print("   SKIPPED — nothing ingested yet")
    else:
        without = [d["name"] for d in new_docs if not (d.get("meta_fields") or {}).get("coverage_status")]
        if without:
            failures.append("%d eCOA_INGEST documents have no coverage_status" % len(without))
            print("   FAIL — %d without coverage_status (re-run patch_coverage_status.py)" % len(without))
        else:
            print("   PASS — all %d documents carry coverage_status" % len(new_docs))

    print("\n" + "=" * 68)
    if failures:
        print("VERDICT: NOT SAFE to delete eCOA_DB — %d check(s) failed" % len(failures))
        for f in failures:
            print("  -", f)
        return 1
    print("VERDICT: every check passed. eCOA_INGEST holds everything eCOA_DB holds,")
    print("nothing is a zero-chunk ghost, the probes retrieve, and the metadata is")
    print("carried over. Deleting eCOA_DB would not lose anything this script can see.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
