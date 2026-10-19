#!/usr/bin/env python3
"""Re-read, in place, every eCOA_INGEST document that is present but fails the quality gate.

    python3 repair_ecoa_ingest.py [--tries 3]

A document that read but carries a wrong-script letter, empty keywords or '**ERROR**' text is re-ingested on its
existing id (delete:true clears the bad chunk) and gated again, up to --tries times; a second read usually clears a
hallucinated letter. Anything still failing is listed for a person - never forced through. Needs RAGFLOW_API_SERVER /
RAGFLOW_API_KEY (and ECOA_RUN_LOG to keep the repo log clean)."""
import sys, time
import migrate_to_ecoa_pipe as m

tries = int(sys.argv[sys.argv.index("--tries") + 1]) if "--tries" in sys.argv else 3


def reingest(doc_id, timeout=25 * 60):
    r = m.req("/api/v1/documents/ingest", {"doc_ids": [doc_id], "run": 1, "delete": True}, "POST")
    if r.get("code") != 0:
        return "ingest call refused: %s" % str(r)[:120]
    end = time.time() + timeout
    while time.time() < end:
        time.sleep(15)
        d = next((x for x in m.all_docs(m.DS_NEW) if x["id"] == doc_id), None)
        if d and d.get("run") in ("DONE", "FAIL") and float(d.get("progress") or 0) in (1.0, -1.0):
            return d["run"]
    return "TIMEOUT"


bad = []
for d in m.all_docs(m.DS_NEW):
    if d["run"] == "DONE" and d["chunk_count"]:
        ok, why = m.gate(d["id"])
        if not ok:
            bad.append((d["id"], d["name"], why))
m.say("repair: %d document(s) to re-read" % len(bad))
still = []
for did, name, why in bad:
    for t in range(1, tries + 1):
        state = reingest(did)
        ok, why2 = m.gate(did) if state == "DONE" else (False, "run=" + state)
        m.say("%-8s try %d  %-46s %s" % ("REPAIRED" if ok else "again", t, name[:46], "" if ok else "| " + why2[:90]))
        if ok:
            break
    else:
        still.append((name, why2))
m.say("repair finished: %d repaired, %d still failing" % (len(bad) - len(still), len(still)))
for n, w in still:
    m.say("  STILL FAILING  %s | %s" % (n, w[:140]))
