#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trails behind RAGFlow's own parse queue for CoA_DATABASE_2026 and fixes
up the test_type on documents that were uploaded before the classify_ecoa
field-detection fix (commit 63a68fa) landed.

Why this exists: the fix (searching the whole certificate for "стабилн..."
instead of requiring one specific field label) only changes RESULTS for
documents whose test_type was computed before the fix. It costs nothing
extra to apply it to those documents once RAGFlow's own layout_recognize
model has already produced their parsed text — no re-download from Drive,
no re-run of vision OCR, just reading chunks RAGFlow already generated and
re-running classify_ecoa.classify_test_type() on the assembled text before
patching meta_fields. This is deliberately the slow, free path (as opposed
to re-fetching + re-OCRing ~196 files immediately), per the owner's choice.

Runs until every RUNNING document currently in the dataset has reached a
terminal parse state (DONE or FAIL) and been reclassified, then exits.
Safe to re-run: only touches documents whose meta_fields.test_type is
still UNKNOWN, and is a no-op on anything already RELEASE/STABILITY_TIMEPOINT.
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import classify_ecoa as ce  # noqa: E402

S = os.environ["RAGFLOW_API_SERVER"].rstrip("/")
K = os.environ["RAGFLOW_API_KEY"]
DATASET_ID = "f29f8f58a13c11f1858cf58865604f65"
LOG_PATH = os.path.join(
    "/tmp/claude-0/-home-user-letta-stack/4877ce6e-ae82-551e-bf35-5698c379c3be"
    "/scratchpad", "reclassify_watcher.log")


def api(path, method="GET", body=None, timeout=120):
    cmd = ["curl", "-sS", "--max-time", str(timeout), "-X", method, f"{S}{path}",
           "-H", f"Authorization: Bearer {K}", "-H", "Content-Type: application/json"]
    if body is not None:
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False,
                                          encoding="utf-8") as tf:
            json.dump(body, tf)
            tp = tf.name
        cmd += ["-d", f"@{tp}"]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
        finally:
            os.remove(tp)
    else:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"_raw": r.stdout[:500], "_err": r.stderr[:300]}


def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def list_all_docs():
    docs, page = [], 1
    while True:
        r = api(f"/api/v1/datasets/{DATASET_ID}/documents?page={page}&page_size=100")
        page_docs = r.get("data", {}).get("docs", [])
        if not page_docs:
            break
        docs.extend(page_docs)
        page += 1
    return docs


def fetch_full_text(doc_id):
    chunks, page = [], 1
    while True:
        r = api(f"/api/v1/datasets/{DATASET_ID}/documents/{doc_id}/chunks?page={page}&page_size=100")
        page_chunks = r.get("data", {}).get("chunks", [])
        if not page_chunks:
            break
        chunks.extend(page_chunks)
        page += 1
    return "\n\n".join(c.get("content", "") for c in chunks)


def reclassify_one(doc):
    mf = doc.get("meta_fields") or {}
    if mf.get("test_type") != "UNKNOWN":
        return "skip_not_unknown"
    text = fetch_full_text(doc["id"])
    tt = ce.classify_test_type(text)
    if tt["test_type"] == "UNKNOWN":
        return "still_unknown"
    patch = {
        "test_type": tt["test_type"],
        "sample_description": tt["sample_description"],
        "stability_month": tt["stability_month"],
        "stability_condition": tt["stability_condition"],
    }
    flat = {k: v for k, v in {**mf, **patch}.items() if v is not None}
    r = api(f"/api/v1/datasets/{DATASET_ID}/documents/{doc['id']}", "PUT",
            {"meta_fields": flat})
    if r.get("code") != 0:
        return f"patch_failed:{r}"
    return f"fixed:{tt['test_type']}"


def run_one_pass():
    """Single check-and-patch pass: reclassify every newly-DONE UNKNOWN
    document, then return a status dict. No sleeping, no looping — meant
    to be invoked repeatedly by an external scheduler (this session waking
    itself up via send_later) rather than by an in-process loop, since a
    long-lived background process in this environment isn't reliable
    across container/shell resets (confirmed this session: a plain
    nohup-backgrounded loop here died silently after ~10 minutes with no
    error, and the KVM4 remote-shell runner turned out to be its own
    minimal/uncertain-persistence container too, not the actual host)."""
    docs = list_all_docs()
    unknown_done = [d for d in docs if d["run"] == "DONE"
                    and (d.get("meta_fields") or {}).get("test_type") == "UNKNOWN"]
    still_running = sum(1 for d in docs if d["run"] == "RUNNING")
    failed = sum(1 for d in docs if d["run"] == "FAIL")

    fixed = still_unknown = errors = 0
    error_details = []
    for d in unknown_done:
        try:
            outcome = reclassify_one(d)
        except Exception as e:
            outcome = f"error:{e}"
        if outcome.startswith("fixed"):
            fixed += 1
        elif outcome == "still_unknown":
            still_unknown += 1
        else:
            errors += 1
            error_details.append((d["name"], outcome))

    import collections
    tt_counts = collections.Counter((d.get("meta_fields") or {}).get("test_type") for d in docs)
    result = {
        "newly_done_unknown_processed": len(unknown_done),
        "fixed": fixed, "still_unknown": still_unknown, "errors": errors,
        "error_details": error_details,
        "still_running": still_running, "failed_to_parse": failed,
        "total_docs": len(docs),
        "test_type_distribution": dict(tt_counts),
        "all_settled": still_running == 0,
    }
    log(f"pass complete: {len(unknown_done)} newly-DONE UNKNOWN processed — "
        f"fixed={fixed} still_unknown={still_unknown} errors={errors} "
        f"| {still_running} still parsing, {failed} failed to parse "
        f"| distribution={dict(tt_counts)}")
    return result


def loop_forever():
    """Original always-on mode — kept for use on a genuinely persistent
    host if one becomes available. NOT what this session actually uses;
    see run_one_pass()'s docstring."""
    log("watcher started (loop mode)")
    while True:
        result = run_one_pass()
        if result["all_settled"]:
            log("no documents left RUNNING — watcher exiting")
            break
        time.sleep(180)


if __name__ == "__main__":
    if "--once" in sys.argv:
        print(json.dumps(run_one_pass(), ensure_ascii=False))
    else:
        loop_forever()
