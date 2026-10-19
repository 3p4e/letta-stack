#!/usr/bin/env python3
"""Upload the approved Certificate of Quality scans into PP_COQs and run them through CoQ_PIPE, one at a time.

    python3 run_coq_ingest.py <scan_dir>       # <scan_dir> holds the PDFs, named as in the Drive folder

The folder is Drive 1vXy-8drEqBJjBpaadW-E8hGnnb7Q4BmU (46 scans). Each document is uploaded under its Drive title,
parsed by the dataset's pipeline, and then gated exactly as eCOA_INGEST's are (chunk present, no ERROR text in the
indexed fields, no wrong-script letters, questions and keywords non-empty - quality_guard.py). A document that fails
is re-run in place up to --tries times and then listed, never forced through. Idempotent: a title already in the
dataset is not uploaded again; a failed or empty one is re-run on its existing id.
Needs RAGFLOW_API_SERVER / RAGFLOW_API_KEY; ECOA_RUN_LOG keeps the log out of the repository."""
import glob, importlib.util, json, os, subprocess, sys, time

B = os.environ["RAGFLOW_API_SERVER"].rstrip("/")
K = os.environ["RAGFLOW_API_KEY"]
DS = "02dbd0d6cb6611f1a114bdd109af559f"   # PP_COQs
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.environ.get("ECOA_RUN_LOG") or HERE + "/run_coq_ingest.log"
TRIES = int(sys.argv[sys.argv.index("--tries") + 1]) if "--tries" in sys.argv else 3


def say(msg):
    line = "%s %s" % (time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    open(LOG, "a", encoding="utf8").write(line + "\n")


def req(path, data=None, method=None):
    a = ["curl", "-s", "-m", "120", "-X", method or ("POST" if data is not None else "GET"), B + path,
         "-H", "Authorization: Bearer " + K, "-H", "Content-Type: application/json"]
    if data is not None:
        a += ["-d", json.dumps(data, ensure_ascii=False)]
    return json.loads(subprocess.run(a, capture_output=True, text=True).stdout)


def all_docs():
    out, pg = [], 1
    while True:
        d = req("/api/v1/datasets/%s/documents?page=%d&page_size=100" % (DS, pg))["data"]["docs"]
        out += d
        if len(d) < 100:
            return out
        pg += 1


def upload(path):
    a = ["curl", "-s", "-m", "300", "-X", "POST", B + "/api/v1/datasets/%s/documents" % DS,
         "-H", "Authorization: Bearer " + K, "-F", "file=@" + path]
    r = json.loads(subprocess.run(a, capture_output=True, text=True).stdout)
    return r["data"][0]["id"] if r.get("code") == 0 else None


def run_one(doc_id, timeout=25 * 60):
    r = req("/api/v1/documents/ingest", {"doc_ids": [doc_id], "run": 1, "delete": True})
    if r.get("code") != 0:
        return "ingest call refused: %s" % str(r)[:120]
    end = time.time() + timeout
    while time.time() < end:
        time.sleep(12)
        d = next((x for x in all_docs() if x["id"] == doc_id), None)
        if d and d.get("run") in ("DONE", "FAIL") and float(d.get("progress") or 0) in (1.0, -1.0):
            return d["run"]
    return "TIMEOUT"


def gate(doc_id):
    spec = importlib.util.spec_from_file_location("qg", HERE + "/quality_guard.py")
    qg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(qg)
    ch = req("/api/v1/datasets/%s/documents/%s/chunks?page=1&page_size=100" % (DS, doc_id))["data"].get("chunks") or []
    if not ch:
        return False, "no chunks"
    for c in ch:
        if "ERROR" in str(c.get("important_keywords")) + str(c.get("questions")):
            return False, "error text in indexed fields"
        ok, probs = qg.check(c.get("content") or "")
        if not ok:
            return False, "; ".join(probs)
        if not c.get("questions"):
            return False, "questions empty"
        if not c.get("important_keywords"):
            return False, "keywords empty"
    return True, "ok (%d chunk(s))" % len(ch)


def main(scan_dir):
    files = sorted(glob.glob(os.path.join(scan_dir, "*.pdf")))
    have = {d["name"]: d for d in all_docs()}
    say("%d scans; %d already in PP_COQs" % (len(files), sum(1 for f in files if os.path.basename(f) in have)))
    bad = []
    for f in files:
        name = os.path.basename(f)
        d = have.get(name)
        if d and d["run"] == "DONE" and d["chunk_count"] and gate(d["id"])[0]:
            continue
        doc_id = d["id"] if d else upload(f)
        if not doc_id:
            say("UPLOAD FAILED %s" % name)
            bad.append((name, "upload failed"))
            continue
        for t in range(1, TRIES + 1):
            state = run_one(doc_id)
            ok, why = gate(doc_id) if state == "DONE" else (False, "run=" + state)
            say("%-8s try %d  %-34s %s" % ("OK" if ok else "again", t, name[:34], "" if ok else "| " + why[:100]))
            if ok:
                break
        else:
            bad.append((name, why))
    say("finished: %d scans, %d failing" % (len(files), len(bad)))
    for n, w in bad:
        say("  STILL FAILING  %s | %s" % (n, w[:140]))


if __name__ == "__main__":
    main(sys.argv[1])
