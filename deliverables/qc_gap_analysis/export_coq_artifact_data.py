#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One JSON for the QC issuance artifact: CoQ schedule, iCoA plan, eCoA receipt.

    python3 deliverables/qc_gap_analysis/export_coq_artifact_data.py OUT.json

Everything is derived from the same computations the workbooks use —
build_coq_schedule.schedule() / icoa_plan() and build_document_registers
load_register() / verified_map() — so the artifact cannot drift from the
deliverables. No value is retyped here.
"""
import json
import os
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.chdir(ROOT)
sys.path.insert(0, HERE)

import build_coq_schedule as CQ            # noqa: E402
import build_document_registers as DR      # noqa: E402


def main(out):
    rows, per_coq, dets = CQ.schedule()
    plan = CQ.icoa_plan(per_coq)

    coqs, by_n = [], {}
    for r in rows:
        k = (r["CoQ number"], r["Cultivation batch"], r["CoQ type"])
        if k not in by_n:
            p = per_coq[len(coqs)]
            assert p["number"] == r["CoQ number"] and p["cb"] == r["Cultivation batch"]
            by_n[k] = {
                "n": p["number"], "t": p["type"], "basis": p["basis"],
                "issue": p["date"], "pp": p["pp"], "cb": p["cb"],
                "strain": p["strain"], "grade": p["grade"], "cls": p["cls"],
                "ic": p["icoa_ref"], "thc": p["banner_thc"],
                "spec": p["spec_doc"], "conflict": p["spec_conflict"],
                "reg": p["in_register"], "issued": p["issued"], "rows": [],
            }
            coqs.append(by_n[k])
        by_n[k]["rows"].append({
            "no": r["№"], "crit": r["Acceptance criterion"],
            "res": r["Result"], "doc": r["Source document"],
            "dd": r["Document date"], "lab": r["Issuing institution"],
            "fam": r["Report series"], "st": r["Status"],
            "route": r["Performed by"], "also": r["Also on file"],
        })

    docs = [r for r in DR.load_register()
            if not r["code"].lower().startswith(("n/a", "(not numbered)"))]
    docs.sort(key=lambda r: (DR.key(r["date"]), r["row"]))
    ver = DR.verified_map()
    ecoa = [{
        "date": r["date"], "lab": r["lab"], "code": r["code"], "batch": r["batch"],
        "ref": r["ref"], "strain": r["strain"], "pn": r["pn"],
        "reported": r["reported"], "flag": ("red" if "red" in r["flags"] else
                                            ("amber" if r["flags"] else "")),
        "verified": bool(DR.nk(r["code"]) in ver or any(
            DR.nk(m) in ver for m in
            __import__("re").findall(r"ППК\s*\d+", r["code"]))),
        "pdf": r["pdf"],
    } for r in docs]

    data = {
        "generated": "31.08.2026",
        "sop_effective": CQ.SOP_EFFECTIVE,
        "dets": [{"no": d["no"], "group": d["group"], "en": d["en"],
                  "mk": d["mk"], "method": d["method"], "crit": d["criterion"],
                  "src": d["source"], "col": d["column"]} for d in dets],
        "coqs": coqs,
        "icoa_plan": plan,
        "ecoa": ecoa,
    }
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{out}: {len(coqs)} CoQs, {sum(len(c['rows']) for c in coqs)} rows, "
          f"{len(plan)} iCoAs, {len(ecoa)} eCoA documents, "
          f"{os.path.getsize(out)//1024} KiB")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else
                  os.path.join(HERE, "coq_artifact_data.json")))
