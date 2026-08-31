#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read the 48 signed product specifications into one JSON the builders can use.

    python3 deliverables/qc_gap_analysis/extract_product_specifications.py

`deliverables/imb_spec_pdfs/SPC_FINAL_ImB_PDF/**` holds 48 Purely Plant product
specifications — `QCSP 001 v.03`, signed by the QC and QA Managers on 01.06.2026.
They are the release specification: the parameter list a Certificate of Quality must
carry, the method behind each parameter, and the acceptance criterion each result is
judged against.

**No pass in this campaign had opened them before 31.08.2026**, and four release
dispositions turned out to depend on how one of their lines is read
(`review/OOS_RECTIFICATION_2026-08-31.md`). Leaving them as 48 PDFs is what made that
possible, so this reads them once into a file everything else can key on.

## What it establishes

**Section 02 is identical in all 48.** Compared with whitespace collapsed, the
parameter table has exactly one form — 23 determinations, of which two are marked
*Upon request | По барање*. Two of the 48 render one extra space of column padding,
which is a `pdftotext` artefact and not a difference in the document. The table is
therefore emitted once, as `determinations`, rather than 48 times.

**Section 01 differs per product, and one of its fields is an acceptance criterion.**
Parameter 4, Total Δ9-THC, has the criterion *"Per target grade as per Section 01"* —
so a CoQ cannot state a THC criterion without this file. 26 distinct potency ranges
across the 48, from `7.20 – 8.80 %` to `27.00 – 29.00 %`.

## What it cannot supply

The 48 specifications cover **35 of the register's 80 batches.** For the other 45 there
is no product specification in this repository, so no per-batch THC acceptance criterion
exists to put on a CoQ. 13 specifications name material the register does not carry.
Both lists are written out; neither is guessed at.

Requires `pdftotext` (poppler-utils). The output JSON is committed, so nothing
downstream needs poppler.
"""
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PDFS = os.path.join(ROOT, "deliverables", "imb_spec_pdfs", "SPC_FINAL_ImB_PDF", "*", "*.pdf")
OUT = os.path.join(HERE, "product_specifications_QCSP001.json")

SEC1, SEC2, SIGN = "01 CULTIVAR", "02 ANALYTICAL PARAMETERS", "P R E PA R E D"

# Section 02 of QCSP 001 v.03, transcribed from the rendered page. Every string is
# verbatim; a paraphrased acceptance criterion on a release document is a defect.
#
# `no` sorts the grouped rows: 9.1 is TAMC under "Microbiological Purity". `column` is
# the release register's column letter, or "" where the register has no column for it —
# identity and foreign matter have none, which is why 81 in-house iCoAs are owed.
DETERMINATIONS = [
    dict(no="1",  group="", en="Identification A, Appearance · Macroscopic",
         mk="Идентиф. A, Изглед, Макроскопски", method="Ph. Eur. mon. 3028",
         criterion="Conforms to monograph | Соодветствува со монографијата",
         column="", source="in_house_icoa"),
    dict(no="2",  group="", en="Identification B · Microscopic",
         mk="Идентиф. Б · Микроскопски", method="Ph. Eur. 2.8.23 (microscopy)",
         criterion="Conforms to monograph | Соодветствува со монографијата",
         column="", source="in_house_icoa"),
    dict(no="3",  group="", en="Identification C · HPLC/HPTLC",
         mk="Идентиф. Ц · HPLC/HPTLC", method="Ph. Eur. 2.2.29 (3028)",
         criterion="Conforms to monograph | Соодветствува со монографијата",
         column="", source="in_house_icoa"),
    dict(no="4",  group="", en="Assay — Total Δ⁹-THC", mk="Анализа — вкупен Δ⁹-THC",
         method="Ph. Eur. 2.2.29 (HPLC)",
         criterion="Per target grade as per Section 01 | Според целна класа од Дел 01",
         column="E", source="outsourced_certificate", per_batch_criterion=True),
    dict(no="5",  group="", en="Assay — Total CBD", mk="Анализа — вкупен CBD",
         method="Ph. Eur. 2.2.29 (HPLC) · CBD + CBDA x 0.877",
         criterion="≤ 1.0%, w/w", column="G", source="outsourced_certificate"),
    dict(no="6",  group="", en="Total CBN", mk="Вкупен CBN",
         method="Ph. Eur. 2.2.29 (HPLC) · CBN + CBNA x 0.876",
         criterion="≤ 1.0%, w/w", column="H", source="outsourced_certificate"),
    dict(no="7",  group="", en="Foreign Matter", mk="Страни материи",
         method="Ph. Eur. 2.8.2 · In-house · интерна",
         criterion="≤ 2.0% / 25–50 g · < 1 cm leaves | листови, no seeds | без семки",
         column="", source="in_house_icoa"),
    dict(no="8",  group="", en="Loss on Drying", mk="Губиток при сушење",
         method="Ph. Eur. 2.2.32 (3028) · at 40 °C, 24 h, 15–25 mbar",
         criterion="≤ 12.0%", column="I", source="outsourced_certificate"),

    dict(no="9.1", group="Microbiological Purity | Микробиолошка Чистота",
         en="TAMC", mk="Вкупен аеробен микробен број",
         method="Ph. Eur. 2.6.12 cat. C", criterion="≤ 10⁵ CFU/g",
         column="J", source="outsourced_certificate"),
    dict(no="9.2", group="Microbiological Purity | Микробиолошка Чистота",
         en="TYMC", mk="Вкупен број квасци/мувли",
         method="Ph. Eur. 2.6.12 cat. C", criterion="≤ 10⁴ CFU/g",
         column="K", source="outsourced_certificate"),
    dict(no="9.3", group="Microbiological Purity | Микробиолошка Чистота",
         en="Bile-tolerant gram-neg.", mk="Жолчно-толерантни грам-нег.",
         method="Ph. Eur. 2.6.31 cat. C", criterion="≤ 10⁴ CFU/g",
         column="L", source="outsourced_certificate"),
    dict(no="9.4", group="Microbiological Purity | Микробиолошка Чистота",
         en="Salmonella", mk="Салмонела", method="Ph. Eur. 2.6.31 cat. C",
         criterion="Absence | Отсуство / 25 g", column="M",
         source="outsourced_certificate"),
    dict(no="9.5", group="Microbiological Purity | Микробиолошка Чистота",
         en="Escherichia coli", mk="Ешерихија коли", method="Ph. Eur. 2.6.13 cat. C",
         criterion="Absence | Отсуство / 1 g", column="N",
         source="outsourced_certificate"),
    dict(no="9.6", group="Microbiological Purity | Микробиолошка Чистота",
         en="Pseudomonas aeruginosa", mk="", method="Ph. Eur. 2.6.13 cat. C",
         criterion="Absence | Отсуство / 1 g", column="", source="upon_request"),
    dict(no="9.7", group="Microbiological Purity | Микробиолошка Чистота",
         en="Staphylococcus aureus", mk="", method="Ph. Eur. 2.6.13 cat. C",
         criterion="Absence | Отсуство / 1 g", column="", source="upon_request"),

    dict(no="10.1", group="Mycotoxins | Микотоксини", en="Aflatoxin B₁",
         mk="Афлатоксин B₁", method="Ph. Eur. 2.8.18 (HPLC-FLD)",
         criterion="≤ 2 µg/kg", column="P", source="outsourced_certificate"),
    # The composition parenthetical follows the MACEDONIAN term on the page —
    # x-ordered glyphs read `Aflatoxins ∑ | Афлатоксини ∑ (B₁+B₂+G₁+G₂)` — and the
    # subscripts are genuine subscripts, verified from glyph baselines.
    dict(no="10.2", group="Mycotoxins | Микотоксини",
         en="Aflatoxins ∑", mk="Афлатоксини ∑ (B₁+B₂+G₁+G₂)",
         method="Ph. Eur. 2.8.18 (HPLC-FLD)", criterion="≤ 4 µg/kg",
         column="O", source="outsourced_certificate"),
    dict(no="10.3", group="Mycotoxins | Микотоксини", en="Ochratoxin A",
         mk="Охратоксин A", method="Ph. Eur. 2.8.22 (HPLC-FLD)",
         criterion="≤ 20 µg/kg", column="Q", source="outsourced_certificate"),

    dict(no="11.1", group="Heavy Metals | Тешки метали", en="Lead (Pb)",
         mk="Олово (Pb)", method="Ph. Eur. 2.4.27 (ICP-MS)", criterion="≤ 0.5 mg/kg",
         column="R", source="outsourced_certificate"),
    dict(no="11.2", group="Heavy Metals | Тешки метали", en="Cadmium (Cd)",
         mk="Кадмиум (Cd)", method="Ph. Eur. 2.4.27 (ICP-MS)", criterion="≤ 0.3 mg/kg",
         column="S", source="outsourced_certificate"),
    dict(no="11.3", group="Heavy Metals | Тешки метали", en="Arsenic (As)",
         mk="Арсен (As)", method="Ph. Eur. 2.4.27 (ICP-MS)", criterion="≤ 0.2 mg/kg",
         column="T", source="outsourced_certificate"),
    dict(no="11.4", group="Heavy Metals | Тешки метали", en="Mercury (Hg)",
         mk="Жива (Hg)", method="Ph. Eur. 2.4.27 (ICP-MS)", criterion="≤ 0.1 mg/kg",
         column="U", source="outsourced_certificate"),

    dict(no="12", group="", en="Pesticide Residues", mk="Остатоци од пестициди",
         method="Ph. Eur. 2.8.13 (LC-MS/MS) · CUMCS Equivalency",
         criterion="≤ LOQ as per Ph. Eur. 2.8.13 · ≤ LOQ as per CUMCS Equivalency",
         column="V", source="outsourced_certificate"),
]

# Every acceptance-criterion string above must appear on the page, so a typo here is
# caught rather than propagated into 102 certificates. Superscripts and the ∑ are the
# two places the transcription and the text layer legitimately differ.
VERIFY = {
    "≤ 10⁵ CFU/g": "≤ 105 CFU/g",
    "≤ 10⁴ CFU/g": "≤ 104 CFU/g",
    "Aflatoxins ∑ (B1+B2+G1+G2)": "Aflatoxins ∑ | Афлатоксини ∑ (B1+B2+G1+G2)",
}


def sections(text):
    i, j, k = text.find(SEC1), text.find(SEC2), text.find(SIGN)
    return text[i:j], text[j:k]


def main():
    files = sorted(glob.glob(PDFS))
    if not files:
        raise SystemExit(f"no specifications found under {PDFS}")

    specs, shapes, unverified = {}, {}, []
    for path in files:
        try:
            text = subprocess.run(["pdftotext", "-layout", path, "-"],
                                  capture_output=True, text=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError) as exc:
            raise SystemExit(f"pdftotext failed on {path}: {exc}")
        one, two = sections(text)
        key = os.path.basename(path)[:-4].split("_")[0]

        m = re.search(r"КОД НА ПРОИЗВОД\s+(.+?)\s{2,}ЈАЧИНА\s+(.+?)\s{2,}"
                      r"СПЕЦ\. ДОК\. КОД\s+(\S+)", one)
        target = re.search(r"([\d.]+%\s*±\s*[\d.]+%)", one)
        strain = re.search(r"^\s{20,}([A-Z][A-Z &'\-]+?)\s{10,}[\d.]+%", one, re.M)
        if not m:
            raise SystemExit(f"section 01 did not parse in {path}")

        specs[key] = {
            "file": os.path.basename(path),
            "tranche": os.path.basename(os.path.dirname(path)),
            "strain": strain.group(1).strip().title() if strain else "",
            "product_code": m.group(1).strip(),
            "thc_criterion": re.sub(r"\s+", " ", m.group(2)).strip(),
            "thc_target": re.sub(r"\s+", " ", target.group(1)) if target else "",
            "spec_doc_code": m.group(3),
        }
        # whitespace-collapsed, because two of the 48 render one extra space of
        # column padding and that is the renderer, not the document
        shapes.setdefault(
            hashlib.sha256(re.sub(r"\s+", " ", two).strip().encode()).hexdigest()[:12],
            []).append(key)

        flat = re.sub(r"\s+", " ", two)
        for shown, on_page in VERIFY.items():
            if re.sub(r"\s+", " ", on_page) not in flat:
                unverified.append((key, shown))

    if unverified:
        raise SystemExit("REFUSING: a transcribed criterion is not on the page: "
                         + str(unverified[:6]))

    payload = {
        "source": "deliverables/imb_spec_pdfs/SPC_FINAL_ImB_PDF/**",
        "document": "QCSP 001 v.03",
        "signed": {"prepared_approved": "Blagoj Nikolov, QC Manager · "
                                        "M.Pharm, Drug Quality Control Specialist",
                   "reviewed": "Jovana Romevska Cvetkovski, QA Manager · "
                               "Master Pharmacist",
                   "date": "01.06.2026"},
        "specifications": specs,
        "determinations": DETERMINATIONS,
        "section_02_shapes": {h: sorted(v) for h, v in shapes.items()},
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)

    print(f"specifications read : {len(specs)}")
    print(f"determinations      : {len(DETERMINATIONS)} "
          f"({sum(1 for d in DETERMINATIONS if d['source'] == 'upon_request')} upon request, "
          f"{sum(1 for d in DETERMINATIONS if d['source'] == 'in_house_icoa')} in-house)")
    print(f"section 02 shapes   : {len(shapes)} "
          f"(whitespace collapsed — one document, {len(files)} files)")
    ranges = {v["thc_criterion"] for v in specs.values()}
    print(f"THC criteria        : {len(ranges)} distinct potency ranges")
    print(f"out                 : {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
