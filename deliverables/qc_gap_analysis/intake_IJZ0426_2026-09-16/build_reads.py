#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The two reads of every certificate of the April-2026 IJZ release panel, as one file.

    python3 deliverables/qc_gap_analysis/intake_IJZ0426_2026-09-16/build_reads.py

Writes reads_IJZ0426.json beside this script: for each of the eighteen certificates the
runner's two independent vision reads (A and B, ingestion/ecoa_runner/records_corpus.json,
restricted to the determinations the owner's release register has a column for), the third
read where the two disagree on a value (third_reads/, fetched 16.09.2026), and the settled
result the register row will carry. Nothing here decides between two reads by itself: a
disagreement is settled only by a read that names its source, or it stays a disagreement
and apply_IJZ0426.py refuses to write.

WHAT THESE ARE. The Institute of Public Health's two reports on every lot sampled on
21.04.2026 — the release panel of the spring-2026 packaging:

  * IJZ-MB (microbiology), laboratory numbers 304/0548/26 … 312/0556/26, received
    22.04.2026, issued 28.04.2026: TAMC, TYMC, bile-tolerant gram-negative bacteria,
    E. coli, Salmonella, against Ph. Eur. 5.1.8 Kat. C.
  * IJZ (contaminants), report numbers 2357/2026 … 2365/2026, sampled and received
    21.04.2026, issued 29/30.04.2026: total aflatoxins (AflaTest, fluorometric), Pb, Cd, As,
    Hg (МКС EN 17851:2023) and the 29-line organochlorine/organophosphate pesticide panel
    (МКС EN 15662:2020), every line н.д.

Nine lots, eighteen documents, two of them the starred second sample of JD112501 (306/0550/26
and 2365/2026 — see testing_series.EXPERIMENTAL).

THE ONE THE RUNNER NEVER READ. 310/0554/26 (GG012601*, P060302) is absent from
records_corpus.json. Its two reads are the RAGflow OCR of 30.08.2026 (read A) and the Head
of QC's own transcription on the CoQ_Analysis_Master tracker (read B, tracker/v8_values.json);
the Drive OCR is its third read and confirms what it can (the exponents did not survive OCR).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(GAP))
CORPUS = os.path.join(ROOT, "ingestion", "ecoa_runner", "records_corpus.json")
V8 = os.path.join(GAP, "tracker", "v8_values.json")
OUT = os.path.join(HERE, "reads_IJZ0426.json")

LAB = "IPH — Institute of Public Health"
# runner parameter -> determination the register has a column for
MB = {"tamc": "9.1", "tymc": "9.2", "bile_tolerant_gram_negative": "9.3",
      "salmonella": "9.4", "escherichia_coli": "9.5"}
CHEM = {"aflatoxins_total": "10.2", "aflatoxin_b1": "10.1", "ochratoxin_a": "10.3",
        "lead": "11.1", "cadmium": "11.2", "arsenic": "11.3", "mercury": "11.4"}

# The eighteen: laboratory number -> (scan in the owner's eCoA_DATABASE, Drive file id)
FILES = {
    "304/0548/26": ("280426_304-0548-26_IJZ-MB_GG112501-P060252.pdf", "1SK1ZrflM6LUKuGPKzuFORz-WBXHUzDN3"),
    "305/0549/26": ("280426_305-0549-26_IJZ-MB_SCR112501-P060282.pdf", "18L9Gq1uAK0ePtR16uv0tJ7lRvgBkFDEs"),
    "306/0550/26": ("280426_306-0550-26_IJZ-MB_JD112501＊-P060212.pdf", "1rvvRUkeRl6OAqhgWhWVmJSItS4cIbKRe"),
    "307/0551/26": ("280426_307-0551-26_IJZ-MB_JD112501-P060212.pdf", "1z3Ggcc4eSbaJIeHrfhQPtD6SDk3WBkjt"),
    "308/0552/26": ("280426_308-0552-26_IJZ-MB_FB012601-1-P060322.pdf", "18b3rclg6mEfXseAIZewz5HVkF3cMpgpJ"),
    "309/0553/26": ("280426_309-0553-26_IJZ-MB_JD012601＊-P060312.pdf", "1AgkL4acihW4uknC4ST3wmdVnGDP_kQ3i"),
    "310/0554/26": ("280426_310-0554-26_IJZ-MB_GG012601＊-P060302.pdf", "16WO2J-yRSfKfGKcdH-5f5LXxdYrcVpXj"),
    "311/0555/26": ("280426_311-0555-26_IJZ-MB_CC112501-P060272.pdf", "1HlCtgbmlrWYTh-dTq3_fNqtT0tbB9a4_"),
    "312/0556/26": ("280426_312-0556-26_IJZ-MB_FB112501-P060292.pdf", "1LOMrAamOVdp1ctcvFkh08JDjSD0PMB-x"),
    "2357/2026": ("290426_2357-2026_IJZ_FB112501-P060292.pdf", "1tkzVjm6Yk-TUK9rYphkpegEMNiK5NtaD"),
    "2358/2026": ("290426_2358-2026_IJZ_GG112501-P060252.pdf", "1aaYdxsOpyWqBz143BxglXQ4mEqfIu4DF"),
    "2359/2026": ("290426_2359-2026_IJZ_CC112501-P060272.pdf", "16Lx2zrtTVfi6kcIojiCIC7jBVjDb7VSk"),
    "2360/2026": ("290426_2360-2026_IJZ_SCR112501-P060282.pdf", "11cc8pwmacFFP1bqVcWTIZBlYElfZzwxH"),
    "2361/2026": ("300426_2361-2026_IJZ_JD112501-P060212.pdf", "1kWpdg_S49wy8drQUfKll4TL4FeqdE17N"),
    "2362/2026": ("300426_2362-2026_IJZ_FB012601-1-P060322.pdf", "1FI9ARBAxuhPBVx_mBbvl5qQy2BY3Utom"),
    "2363/2026": ("300426_2363-2026_IJZ_JD012601＊-P060312.pdf", "1uicUI4S2YWflc30Drs9C0ahIhfbBW56L"),
    "2364/2026": ("300426_2364-2026_IJZ_GG012601＊-P060302.pdf", "100H4MN1Uk7HJVoUQMTLoJtGsdocaoTAg"),
    "2365/2026": ("300426_2365-2026_IJZ_JD112501＊-P060212.pdf", "1q0pDUlgrTmfDuc0HiUxcj5O40cIJClRa"),
}

# The starred second sample of JD112501 / P060212 (owner's ruling, 16.09.2026): real data,
# never certifying. Listed in testing_series.EXPERIMENTAL; carried here so the reads file
# says so beside the values.
EXPERIMENTAL = {"306/0550/26", "2365/2026"}

# Third reads, 16.09.2026 — only where reads A and B disagree on a VALUE the register
# carries. Each names what was read and where the page's text came from; the texts are in
# third_reads/ verbatim.
THIRD = {
    "307/0551/26": {
        "read": {"9.3": "< 10³ и >10² CFU/g"},
        "source": ("Drive OCR of the scan (third_reads/307-0551-26_drive_ocr.txt): '<10³ и>10² CFU/g'; "
                   "RAGflow OCR of 30.08.2026: '< 10^3 и >10^2 CFU/g'. Read B stands; read A "
                   "('< 10¹ – 10² CFU/g') misread both bounds."),
    },
    "304/0548/26": {
        "read": {"9.3": "< 10² и >10 CFU/g"},
        "source": ("Drive OCR of the scan (third_reads/304-0548-26_drive_ocr.txt): '<10² и>10 CFU/g'; "
                   "RAGflow OCR of 30.08.2026: '< 10^2 x 10' (the 'и' lost, both bounds present). Read B "
                   "stands; read A ('< 10^2 CFU/g') stopped at the first bound — OI-36's class, as on "
                   "537/1068/26, 542/1073/26, 544/1075/26 and 547/1078/26 of the IJZ-MB intake."),
    },
    "305/0549/26": {
        "read": {"9.3": "< 10³ и >10² CFU/g"},
        "source": ("RAGflow OCR of 30.08.2026: '< 10³ и >10² CFU/g'; the Drive OCR "
                   "(third_reads/305-0549-26_drive_ocr.txt) prints '< 10 и>10² CFU/g', which no page can "
                   "say (below 10 and above 10² at once) — the first exponent did not survive OCR. Read A "
                   "'<10³ x10² CFU/g' carries both exponents and a garbled connective. Read B stands. The "
                   "owner's tracker holds this line as 'held for review'."),
    },
    "2361/2026": {
        "read": {"12": "н.д. — 29 lines"},
        "source": ("Drive OCR of the four-page scan (third_reads/2361-2026_drive_ocr.txt): 26 pesticide lines "
                   "on page 2 and Dieldrin, Heptachlor, Endosulfan sulfate on page 3 = 29, every one н.д. "
                   "Read A's count (29) stands over read B's (28); the register's pesticide cell holds one "
                   "value for the panel either way."),
    },
}

# 310/0554/26 — never read by the runner. Read A: RAGflow OCR of 30.08.2026
# (ingestion/ragflow/cache/all_cert_texts_2026-08-30.json, 'GG012601*, 310-0554-26, 28.04.2026,
# IJZ-MB.pdf'). Read B: the Head of QC's transcription, tracker/v8_values.json.
READ_A_310 = {"9.1": "1 x 10⁴ CFU/g", "9.2": "1 x 10⁴ CFU/g", "9.3": "< 10 CFU/g",
              "9.4": "отсутна/25", "9.5": "отсутна/g"}
READ_C_310 = {"9.3": "< 10 CFU/g", "9.4": "отсутна/25", "9.5": "отсутна/g"}
SOURCE_310 = ("read A: RAGflow OCR of the scan, 30.08.2026; read B: the Head of QC's own transcription on "
              "the CoQ_Analysis_Master tracker (tracker/v8_values.json, GG012601＊|310/0554/26); read C: "
              "Drive OCR of the scan, 16.09.2026 (third_reads/310-0554-26_drive_ocr.txt), whose TAMC and "
              "TYMC exponents did not survive OCR ('1 х 10', '1 х 10%') and which confirms the other three "
              "lines. A and B agree on all five.")


def p_from_file(name):
    m = re.search(r"-(P\d{6})\.pdf$", name)
    return m.group(1) if m else ""


def cu_from_file(name):
    m = re.match(r"^\d{6}_[^_]+_IJZ(?:-MB)?_(.+?)-P\d{6}\.pdf$", name)
    return m.group(1).replace("-1", "/1") if m else ""   # FB012601-1 -> FB012601/1


def table(read, kind):
    """The register determinations a runner read holds, {det: printed}."""
    out = {}
    pest = []
    for p in (read or {}).get("parameters", []) or []:
        k = p.get("parameter")
        if kind == "MB" and k in MB:
            out[MB[k]] = p.get("result_printed")
        elif kind == "CHEM" and k in CHEM:
            out[CHEM[k]] = p.get("result_printed")
        elif kind == "CHEM" and k in ("pesticide_residues", "other"):
            pest.append(str(p.get("result_printed") or "").strip())
    if kind == "CHEM":
        vals = sorted({v.lower() for v in pest})
        out["12"] = ("%s — %d lines" % (" / ".join(vals), len(pest))) if pest else None
    return out


def main():
    corpus = json.load(open(CORPUS, encoding="utf-8"))
    recs = corpus if isinstance(corpus, list) else corpus.get("records", corpus)
    v8 = json.load(open(V8, encoding="utf-8"))
    by_code = {}
    for r in recs:
        c = re.sub(r"^Лабораториски број:\s*", "", str(r.get("cert_code") or "")).strip()
        if c in FILES and c not in by_code:
            by_code[c] = r
    out = {}
    for code, (fn, fid) in FILES.items():
        kind = "MB" if "IJZ-MB" in fn else "CHEM"
        rec = by_code.get(code)
        raw = (rec or {}).get("raw") or {}
        entry = {
            "cert_code": code, "file": fn, "drive_file_id": fid, "kind": kind, "laboratory": LAB,
            "batch_on_page": cu_from_file(fn), "p_number": p_from_file(fn),
            "date_of_issue": "28.04.2026" if kind == "MB" else ("30.04.2026" if fn.startswith("3004") else "29.04.2026"),
            "received": "22.04.2026" if kind == "MB" else "21.04.2026",
            "sampled": "21.04.2026",
            "experimental": code in EXPERIMENTAL,
        }
        if rec is None:
            if code != "310/0554/26":
                sys.exit("no corpus record for %s" % code)
            entry["read_A"] = READ_A_310
            entry["read_B"] = dict(v8["GG012601＊|310/0554/26"])
            entry["read_C"] = READ_C_310
            entry["read_source"] = SOURCE_310
        else:
            entry["read_A"] = table(raw.get("A"), kind)
            entry["read_B"] = table(raw.get("B"), kind)
            entry["read_source"] = ("reads A and B: the eCoA runner's two independent vision reads of the page "
                                    "rendered at 300 DPI (ingestion/ecoa_runner/records_corpus.json, %s)" % rec.get("document"))
            entry["batch_printed_A"] = (raw.get("A") or {}).get("batch_printed")
            entry["batch_printed_B"] = (raw.get("B") or {}).get("batch_printed")
        if code in THIRD:
            entry["read_C"] = THIRD[code]["read"]
            entry["read_C_source"] = THIRD[code]["source"]
        out[code] = entry
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("%s: %d certificate(s), %d with a third read" % (os.path.basename(OUT), len(out), sum(1 for e in out.values() if "read_C" in e)))


if __name__ == "__main__":
    main()
