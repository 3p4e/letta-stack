#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rectify the receipt register's flagged and not-page-verified entries from
every local materialisation of the ingested corpus.

    python3 deliverables/qc_gap_analysis/rectify_ecoa_receipts.py

Three tiers of evidence, never conflated (the corpus measured 13% corrupted on
the values whose arithmetic could be checked, so corpus agreement is weak
evidence — trap 12: if chunk text and page disagree, the page wins):

  T1  review/*_page_reads_*.json          values read off the rendered page
  T2  a corpus value that passed an independent check (the CNP R4 arithmetic,
      total = Δ9-THC + 0.877·THCA ± 0.06)
  T3  a corpus value with no independent check — usable to pre-fill a blank
      row, never to verify one; the desk's remediation path promotes it after
      the scan is opened

Sources for T2/T3, in order:
  deliverables/qc_register/extracted_params.json   (structured, git-tracked)
  ingestion/ragflow/cache/all_cert_texts_2026-08-30.json  (raw chunk text,
      vendored 31.08.2026 from the scratchpad cache of eCoA_DATABASE — the
      live server credential is a different tenant and cannot read it)

Outputs (idempotent — a second run produces identical bytes):
  deliverables/qc_gap_analysis/ecoa_rectification_2026-08-31.json
  review/ECOA_RECTIFICATION_2026-08-31.md
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.chdir(ROOT)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "ingestion", "ragflow"))

import build_document_registers as DR          # noqa: E402
import verification_coverage as VC             # noqa: E402
from validate_ecoa_limits import total_thc_consistent  # noqa: E402

EP = os.path.join(ROOT, "deliverables", "qc_register", "extracted_params.json")
CACHE = os.path.join(ROOT, "ingestion", "ragflow", "cache",
                     "all_cert_texts_2026-08-30.json")
OUT_JSON = os.path.join(HERE, "ecoa_rectification_2026-08-31.json")
OUT_MD = os.path.join(ROOT, "review", "ECOA_RECTIFICATION_2026-08-31.md")

# extracted_params field -> receipt-register display label
EP_LABELS = [
    ("total_thc_pct", "Total Δ9-THC %"), ("total_cbd_pct", "Total CBD %"),
    ("total_cbn_pct", "Total CBN %"), ("loss_on_drying_pct", "Loss on drying %"),
    ("foreign_matter_pct", "Foreign matter"), ("microscopic_id", "Ident B (microscopic)"),
    ("hptlc_id", "Ident C (HPTLC)"), ("tamc", "TAMC CFU/g"), ("tymc", "TYMC CFU/g"),
    ("bile_tolerant_gnb", "Bile-tolerant GNB CFU/g"), ("salmonella", "Salmonella /25 g"),
    ("e_coli", "E. coli /1 g"), ("aflatoxins_total", "Aflatoxins Σ µg/kg"),
    ("aflatoxin_b1", "Aflatoxin B1 µg/kg"), ("ochratoxin_a", "Ochratoxin A µg/kg"),
    ("pb", "Pb mg/kg"), ("cd", "Cd mg/kg"), ("arsenic", "As mg/kg"), ("hg", "Hg mg/kg"),
    ("pesticides", "Pesticides"),
]

RANGE_RX = re.compile(r"\d\s*[–\-—]\s*\d|мин\.|макс\.|min\.|max\.")


def is_spec_shape(v):
    """An in-house CoA prints the spec range where a result belongs (trap C4/E5);
    a two-bound or min/max string is a criterion, never a measurement."""
    return bool(RANGE_RX.search(str(v)))


def num(v):
    m = re.search(r"-?\d+(?:[.,]\d+)?", str(v))
    return float(m.group(0).replace(",", ".")) if m else None


def canon(v):
    """Comparison form for a printed value: decimal comma folded, LOQ/ND
    unified, the register's own annotations dropped — a bracketed LOQ bound
    ("< LOQ (<0.20)") or a dash-appended note ("2.06 — DETECTED, >LOQ") is
    commentary on the value, not a different value."""
    s = str(v or "").strip().replace(",", ".")
    s = re.sub(r"\s*\([^)]*\)", "", s)
    s = s.split("—")[0].strip()
    s = re.sub(r"\s+", " ", s)
    u = s.upper().replace(" ", "")
    if u in ("<LOQ", "N.D.", "ND", "Н.Д.", "НД"):
        return "<LOQ/ND"
    return s


def main():
    rows = DR.load_register()
    docs = [r for r in rows
            if not r["code"].lower().startswith(("n/a", "(not numbered)"))]
    docs.sort(key=lambda r: (DR.key(r["date"]), r["row"]))
    seen = set()
    docs = [r for r in docs
            if not (r["code"].strip() in seen or seen.add(r["code"].strip()))]
    ver = DR.verified_map()

    ep = json.load(open(EP, encoding="utf-8"))
    by_pn, by_fold = {}, {}
    for rec in ep:
        pn = rec["meta"].get("batch_canonical", "")
        if pn:
            by_pn.setdefault(pn, []).append(rec)
        for c in (rec["meta"].get("cert_code", ""), rec["meta"].get("source_filename", "")):
            f = VC.fold(c)
            if f:
                by_fold.setdefault(f, []).append(rec)

    cache = {}
    if os.path.exists(CACHE):
        for rec in json.load(open(CACHE, encoding="utf-8")):
            cache[rec["name"]] = rec

    targets = [r for r in docs
               if r["flags"] or not DR.page_verified(r["code"], ver)]

    certs, no_corpus, spec_only = {}, [], []
    for r in targets:
        if DR.page_verified(r["code"], ver) and not r["flags"]:
            continue
        # match a corpus record: exact-ish code first, then the batch's own
        # in-house CoA (the register's "PP CoA #0xx" series and the corpus's
        # "QCCoA 001v02" filenames are the same in-house certificate line,
        # keyed differently)
        cands = list(VC.candidates(r["code"]))
        recs = next((by_fold[c] for c in cands if c in by_fold), None)
        via = "cert code"
        if recs is None:
            # the register's "PP CoA #0xx" series and the corpus's per-batch
            # "QCCoA 001v02" filenames are the same in-house certificate line,
            # keyed differently — so the batch fallback may match ONLY the
            # batch's own in-house (lab PP) record, never another laboratory's
            # certificate for the same batch
            pool = (by_pn.get((r["pn"] or "").strip()) or
                    by_pn.get(VC.fold(r["batch"])) or [])
            pool = [x for x in pool if x["meta"].get("lab") == "PP"]
            if pool:
                recs = pool
                via = "batch %s (its in-house QCCoA)" % (r["pn"] or r["batch"]).strip()
        if not recs:
            no_corpus.append(r["code"])
            continue
        rec = recs[0]
        params, spec_hits = [], []
        p = rec["params"]
        # R4: does this record carry its own arithmetic proof?
        r4 = None
        if all(k in p for k in ("total_thc_pct", "d9_thc_pct", "thca_pct")):
            a, b, c = num(p["total_thc_pct"]), num(p["d9_thc_pct"]), num(p["thca_pct"])
            if None not in (a, b, c):
                r4 = total_thc_consistent(b, c, a)
        for field, label in EP_LABELS:
            v = p.get(field)
            if v in (None, "", "/"):
                continue
            if is_spec_shape(v):
                spec_hits.append(label)
                continue
            tier = "T2" if (r4 and field == "total_thc_pct") else "T3"
            src = ("corpus — checked (R4 arithmetic)" if tier == "T2"
                   else "corpus — verify on page") + " · " + rec["name"]
            if via != "cert code":
                src += " · matched via " + via
            params.append({"k": label, "v": str(v), "src": src, "t": tier})
        if spec_hits:
            spec_only.append((r["code"], spec_hits))
        if params:
            certs[r["code"].strip()] = {
                "params": params,
                "note": "corpus-derived — the page wins on any disagreement; "
                        "promote through the remediation desk after opening the scan",
            }
        else:
            no_corpus.append(r["code"])

    # ---- Farmahem cross-check: current register values vs the page reads ----
    art = json.load(open(os.path.join(HERE, "coq_artifact_data.json"),
                         encoding="utf-8"))
    colname = {L: c["name"] for L, c in art["reg_columns"].items()}
    fhm = json.load(open("review/farmahem_page_reads_2026-08-31.json",
                         encoding="utf-8"))
    FIELD_BY_COL = {"THC %": "thc", "CBD %": "cbd", "CBN %": "cbn",
                    "Loss on drying %": "lod", "Aflatoxins Σ µg/kg": "afla",
                    "Aflatoxin B1 µg/kg": "aflab1", "Ochratoxin A µg/kg": "ota"}
    mismatches = []
    for blk in art["reg"]:
        for ct in blk.get("certs", []):
            f = VC.fold(ct.get("code", ""))
            rec = fhm.get(f)
            if not rec:
                continue
            for L, v in ct.get("vals", {}).items():
                fld = FIELD_BY_COL.get(colname.get(L, ""))
                if not fld or rec.get(fld) in (None, ""):
                    continue
                if canon(v) != canon(rec[fld]):
                    mismatches.append({"code": ct["code"], "batch": blk["cb"],
                                       "column": colname[L], "register": str(v),
                                       "page": str(rec[fld])})

    out = {
        "generated": "31.08.2026",
        "method": "T1 page reads carried by the exporter; this file adds the "
                  "corpus tiers for entries the page campaign does not cover",
        "certs": certs,
        "no_corpus": sorted(set(no_corpus)),
        "spec_shape_skipped": [{"code": c, "labels": ls} for c, ls in spec_only],
        "farmahem_register_vs_page": mismatches,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=True)

    lines = [
        "# eCoA receipt rectification — 31.08.2026",
        "",
        "## The root cause of “not read” everywhere",
        "",
        "The receipt register's page-verified bit matched certificate codes with",
        "`nk()`, which deletes every non-ASCII character: the Cyrillic К and М that",
        "distinguish a Farmahem cannabinoid certificate from its mycotoxin sibling",
        "vanished, ГС never folded to LOD, and a trailing bracketed note defeated the",
        "match. **59 of the 74 “not read” receipts were false negatives** (56 Farmahem",
        "+ 3 IPH). Re-keyed on `verification_coverage.fold()`: **232 of 247 receipts",
        "are page-verified**; the 15 that remain are all Purely Plant in-house rows.",
        "Independently corroborated by `verification_coverage.py`: 1,033 of 1,073",
        "populated result cells (96.3%) sit on a page-verified certificate.",
        "",
        "## Corpus tier for the remainder",
        "",
        "The live RAGflow server answers, but the session credential is a different",
        "tenant (`code 102` inside HTTP 200 — trap 10 in a new costume), so the",
        "corpus is read from its local materialisations: the structured extraction",
        "(`deliverables/qc_register/extracted_params.json`) and the vendored chunk",
        "cache (`ingestion/ragflow/cache/all_cert_texts_2026-08-30.json`).",
        "",
        "Corpus-derived entries: **%d certificates**, tiered T2 (passed the R4"
        % len(certs),
        "arithmetic) or T3 (no independent check — pre-fill only, promote through",
        "the remediation desk after opening the scan).",
        "",
    ]
    if no_corpus:
        lines += ["## Not in the corpus — open the scan", ""]
        lines += ["- `%s`" % c for c in sorted(set(no_corpus))] + [""]
    if spec_only:
        lines += ["## Spec-shaped strings skipped (a criterion is not a result)", ""]
        lines += ["- `%s`: %s" % (c, ", ".join(ls)) for c, ls in spec_only] + [""]
    lines += ["## Farmahem register vs page cross-check", ""]
    if mismatches:
        lines += ["%d residual disagreement(s):" % len(mismatches), ""]
        lines += ["- `%s` (%s) %s: register `%s` vs page `%s`"
                  % (m["code"], m["batch"], m["column"], m["register"], m["page"])
                  for m in mismatches]
    else:
        lines += ["All register values for the 63 Farmahem receipts agree with the",
                  "page reads — the CBD/CBN defects the campaign found (rows 9, 276,",
                  "286) are corrected in the FHM2 register."]
    lines += [""]
    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print("certs with corpus values: %d | no corpus: %d | spec-shaped skipped: %d "
          "| farmahem mismatches: %d"
          % (len(certs), len(set(no_corpus)), len(spec_only), len(mismatches)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
