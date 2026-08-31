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

    # The owner's document masters, vendored beside this script and carried in
    # the page base64-encoded: the desk generates real certificates from them.
    # The four per-scope iCoA masters (31.08.2026) supersede the Variation F
    # master for compilation; the Variation F file stays vendored on record.
    tdir = os.path.join(HERE, "templates")
    coq_tpl = open(os.path.join(tdir, "_CoQ_MASTER_Template.html"),
                   encoding="utf-8").read()
    scoped = {
        "tpl-icoa-ab": "iCoA_P01-02_Appearance_Identification_AB.html",
        "tpl-icoa-c":  "iCoA_P03_Identification_C_Chromatographic.html",
        "tpl-icoa-fm": "iCoA_P07_Foreign_Matter.html",
        "tpl-icoa-mb": "iCoA_P09_Microbiological_Purity.html",
    }
    import re as _re
    tpls = {}
    for tid, fn in scoped.items():
        t = open(os.path.join(tdir, fn), encoding="utf-8").read()
        # A master may carry handwritten signature scans as data URIs (the
        # 31.08.2026 evening revisions of P01-02 and P07 each carry two); a
        # generated document carries a signature line, never an embedded
        # signature image.
        t, nsig = _re.subn(r'<img class="ap-img handwritten"[^>]*>', "", t)
        want = 2 if ("Identification_AB" in fn or "Foreign_Matter" in fn) else 0
        assert nsig == want, f"expected {want} handwritten sigs in {fn}, found {nsig}"
        assert "@@" not in t, f"stray placeholder text in {fn}"
        tpls[tid] = t
    assert "@@" not in coq_tpl
    b64 = lambda t: base64.b64encode(t.encode("utf-8")).decode("ascii")
    tags = ('<script id="qc-data" type="application/json">@@DATA@@</script>\n'
            '<script id="tpl-coq" type="text/plain">' + b64(coq_tpl) + '</script>\n'
            + "".join('<script id="' + tid + '" type="text/plain">' + b64(t) +
                      "</script>\n" for tid, t in sorted(tpls.items())) +
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
