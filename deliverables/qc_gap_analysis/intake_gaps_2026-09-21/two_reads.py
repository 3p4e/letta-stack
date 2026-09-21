#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read A (OpenAI gpt-5) and read B (Gemini) of the seven pages of 21.09.2026.

Never the same engine twice: the runner's own two vendors, each reading the rendered
page without seeing the other's answer. Written to reads_A.json / reads_B.json for
reconcile.py.
"""
import concurrent.futures as cf
import glob
import hashlib
import json
import os
import sys

RUNNER = "/home/user/letta-stack/ingestion/ecoa_runner"
sys.path.insert(0, RUNNER)
import extract_ecoa_records as R                                         # noqa: E402

PDFS = sorted(glob.glob(os.path.join(
    "/tmp/claude-0/-home-user-letta-stack/4877ce6e-ae82-551e-bf35-5698c379c3be/scratchpad/gaps21", "*.pdf")))


def one(path, which):
    raw = open(path, "rb").read()
    imgs = R.render(raw)
    fn = R.read_openai if which == "A" else R.read_gemini
    txt, usage = R.with_retry(lambda: fn(imgs), "read %s %s" % (which, os.path.basename(path)))
    return {"scan": os.path.basename(path), "sha256": hashlib.sha256(raw).hexdigest(),
            "pages": len(imgs), "raw": txt, "usage": usage}


def main():
    for which in ("A", "B"):
        out = []
        with cf.ThreadPoolExecutor(max_workers=3) as pool:
            futs = {pool.submit(one, p, which): p for p in PDFS}
            for f in cf.as_completed(futs):
                p = futs[f]
                try:
                    out.append(f.result())
                    print("   read %s ok: %s" % (which, os.path.basename(p)))
                except Exception as e:
                    print("   read %s FAILED: %s — %s" % (which, os.path.basename(p), e))
                sys.stdout.flush()
        out.sort(key=lambda r: r["scan"])
        json.dump(out, open("reads_%s.json" % which, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("read %s: %d of %d pages" % (which, len(out), len(PDFS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
