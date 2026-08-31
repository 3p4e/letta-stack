#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble the CoX Quality Desk — the live, self-republishing QC instrument.

    python3 deliverables/qc_gap_analysis/live_instrument/build_live_instrument.py

Reads head.html, body.html and script.js beside this file plus the exported
baseline (coq_artifact_data.json) and emits
deliverables/qc_gap_analysis/qc_quality_desk_artifact.html.

Two renderings of one page:
- the SHELL — a complete standalone document with @@DATA@@ / @@OVERLAY@@ /
  @@SHELL@@ placeholders, carried inside the page as base64. When a desk entry
  is recorded, the page rebuilds this document with the same baseline, the
  updated overlay and the same shell, and publishes it as the artifact's next
  version. The baseline never changes in the browser; only the overlay grows.
- the DELIVERABLE — the same content without doctype/html/head/body wrappers
  (the Artifact publisher adds its own skeleton), with the overlay empty.
"""
import base64
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)


def main():
    head = open(os.path.join(HERE, "head.html"), encoding="utf-8").read()
    body = open(os.path.join(HERE, "body.html"), encoding="utf-8").read()
    script = open(os.path.join(HERE, "script.js"), encoding="utf-8").read()
    data = open(os.path.join(GAP, "coq_artifact_data.json"), encoding="utf-8").read()
    for frag, name in ((head, "head"), (body, "body"), (script, "script"), (data, "data")):
        assert "@@" not in frag.replace("@@DATA@@", "").replace("@@OVERLAY@@", "") \
            .replace("@@SHELL@@", ""), f"stray placeholder text in {name}"
        assert "</script" not in data.lower(), "data would close the script tag"

    tags = ('<script id="qc-data" type="application/json">@@DATA@@</script>\n'
            '<script id="qc-shell" type="text/plain">@@SHELL@@</script>\n'
            '<script id="qc-overlay" type="application/json">@@OVERLAY@@</script>\n'
            '<script>\n' + script + '\n</script>')

    shell = ("<!doctype html>\n<html lang=\"en\">\n<head>\n"
             "<meta charset=\"utf-8\">\n"
             "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
             "<style>body{margin:0;font-size:14px}img{max-width:100%}"
             "[hidden]{display:none!important}</style>\n"
             + head + "\n</head>\n<body>\n" + body + "\n" + tags + "\n</body>\n</html>\n")
    shell_b64 = base64.b64encode(shell.encode("utf-8")).decode("ascii")
    assert "@@DATA@@" in shell and "@@OVERLAY@@" in shell and "@@SHELL@@" in shell

    empty_overlay = json.dumps({"v": 1, "batches": [], "ecoa": [], "attach": {},
                                "icoa": {}, "issue": {}, "log": []})
    deliverable = (head + "\n" + body + "\n" + tags) \
        .replace("@@DATA@@", data).replace("@@OVERLAY@@", empty_overlay) \
        .replace("@@SHELL@@", shell_b64)

    out = os.path.join(GAP, "qc_quality_desk_artifact.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(deliverable)
    print(f"{out}: {os.path.getsize(out) / 1024:.0f} KiB "
          f"(shell {len(shell_b64) / 1024:.0f} KiB b64)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
