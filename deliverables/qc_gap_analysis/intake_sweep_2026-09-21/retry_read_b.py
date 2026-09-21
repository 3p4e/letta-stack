#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read B for the pages that carry only one read, when the vendor's quota recovers.

    python3 retry_read_b.py

Five of the fifteen pages carry read A alone: Google's free tier retired a key in the
middle of the run of 21.09.2026 and answered 403 for the rest. One read is not a reading,
so those five were never applied. This asks for the second read of exactly those, merges
whatever comes back into reads_B.json, and leaves the rest untouched — so it can be run
again, and again, until the five are in.
"""
import concurrent.futures as cf
import glob
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER = "/home/user/letta-stack/ingestion/ecoa_runner"
PDFS = "/tmp/claude-0/-home-user-letta-stack/4877ce6e-ae82-551e-bf35-5698c379c3be/scratchpad/sweep21"
sys.path.insert(0, RUNNER)
import extract_ecoa_records as R                                         # noqa: E402


def one(path):
    raw = open(path, "rb").read()
    imgs = R.render(raw)
    txt, usage = R.with_retry(lambda: R.read_gemini(imgs), "read B " + os.path.basename(path))
    return {"scan": os.path.basename(path), "sha256": hashlib.sha256(raw).hexdigest(),
            "pages": len(imgs), "raw": txt, "usage": usage}


def main():
    have = {r["scan"]: r for r in json.load(open(os.path.join(HERE, "reads_B.json"), encoding="utf-8"))}
    allscans = {os.path.basename(p): p for p in sorted(glob.glob(os.path.join(PDFS, "*.pdf")))}
    todo = [p for s, p in allscans.items() if s not in have]
    if not todo:
        print("read B is complete: %d of %d" % (len(have), len(allscans)))
        return 0
    print("read B missing %d of %d: %s" % (len(todo), len(allscans),
                                           ", ".join(sorted(os.path.basename(p) for p in todo))))
    got = 0
    with cf.ThreadPoolExecutor(max_workers=2) as pool:
        futs = {pool.submit(one, p): p for p in todo}
        for f in cf.as_completed(futs):
            name = os.path.basename(futs[f])
            try:
                have[name] = f.result()
                got += 1
                print("   ok: %s" % name)
            except Exception as e:
                print("   still failing: %s — %s" % (name, str(e)[:120]))
            sys.stdout.flush()
    out = sorted(have.values(), key=lambda r: r["scan"])
    json.dump(out, open(os.path.join(HERE, "reads_B.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("read B now holds %d of %d (+%d)" % (len(out), len(allscans), got))
    return 0


if __name__ == "__main__":
    sys.exit(main())
