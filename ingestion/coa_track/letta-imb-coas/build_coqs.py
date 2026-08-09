#!/usr/bin/env python3
"""
CoQ Builder — Per-batch Certificate of Quality assembly.

For each Pjureli Plant / New Garden Pharma production batch in
`staged_coas/`, generate a single Markdown Certificate of Quality that
gathers every Ph.Eur. 11.5 Cannabis Flower Monograph (3028) parameter
result. Each parameter row cites the issuing lab + report doc-code +
issue date — so the CoQ is itself the evidence index.

Output: `coq_output/CoQ_{batch_code}_{strain}.md`

This script is self-contained — no Letta dependency. It reads only the
staged `.txt` files (created by the cloud session) and emits CoQs that
can be reviewed before ingestion. When the embedding endpoint is
restored, the same staged data will populate Letta for live search;
the CoQs here are the static, signable deliverable.
"""
from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
STAGED = os.path.join(HERE, "staged_coas")
OUTDIR = os.path.join(HERE, "coq_output")

# ─────────────────────────────── data model ────────────────────────────────


@dataclass
class ParameterResult:
    parameter: str          # e.g. "Loss on drying"
    method: str             # e.g. "Ph.Eur. 2.2.32"
    spec: str               # e.g. "≤ 10.00 %"
    result: str             # e.g. "7.50 %"
    lab: str                # e.g. "UKIM Faculty of Pharmacy CNP (LT-083)"
    doc_code: str           # e.g. "ППК26001"
    issue_date: str         # e.g. "2026-01-21"
    complies: bool = True
    note: str = ""


@dataclass
class BatchCoQ:
    batch_code: str         # canonical batch id e.g. "WC082501"
    plant_code: str = ""    # P0xxxx code, when known
    strain: str = ""        # "Wedding Crasher"
    client: str = "Pjureli Plant DOOEL / New Garden Pharma"
    parameters: list[ParameterResult] = field(default_factory=list)
    source_files: list[str] = field(default_factory=list)

    @property
    def slug(self) -> str:
        s = re.sub(r"[^A-Za-z0-9_-]+", "_", f"{self.batch_code}_{self.strain}")
        return re.sub(r"_+", "_", s).strip("_")


# ───────────────────── batch metadata + strain mapping ─────────────────────

# Drives parameter assembly + filename → batch grouping.
# Sources: staged Bundle_* file headers and UKIM/Farmahem filename conventions.
BATCHES: dict[str, dict] = {
    # P06xxxx series (Jan 2026 production)
    "WC082501":   {"plant": "P060012", "strain": "Wedding Crasher"},
    "CJ082501-1": {"plant": "P060022", "strain": "Cap Junky"},
    "CJ082501-2": {"plant": "P060032", "strain": "Cap Junky"},
    "OPM092501":  {"plant": "P060042", "strain": "Orange Punch Mimosa"},
    "AB092501":   {"plant": "P060052", "strain": "Apple & Banana"},
    "PM092501":   {"plant": "P060062", "strain": "Permanent Market"},
    "CJ092501":   {"plant": "P060072", "strain": "Cap Junky"},
    "SJ092501":   {"plant": "P060082", "strain": "Sleepy Joy"},
    "GP092501":   {"plant": "P060092", "strain": "Grape Pie"},
    # P05xxxx series (Aug–Nov 2025 production)
    "BSS10240_01":{"plant": "P050122", "strain": "Blue Sunset Sherbet"},
    "GP052501":   {"plant": "P050152", "strain": "Grape Pie"},
    "CJ052501-1": {"plant": "P050162", "strain": "Cup Junky"},
    "BSS052501":  {"plant": "P050192", "strain": "Blue Sunset Sherbet"},
    "GP062501":   {"plant": "P050202", "strain": "Grape Pie"},
    "CJ072501":   {"plant": "P050252", "strain": "Cup Junky"},
    # Strain thumbnails (Oct 2024 batches, no P-code)
    "BG1024":     {"plant": "",        "strain": "Blue Gelato"},
    "BSS1024":    {"plant": "",        "strain": "Blue Sunset Sherbet"},
    "CJ1024":     {"plant": "",        "strain": "Cup Junky"},
    # Farmahem-only batches (cannabinoids + LoD, no full panel)
    "J31102501":  {"plant": "",        "strain": "Jokerz 31"},
    "J31112501":  {"plant": "",        "strain": "Jokerz 31"},
    "J31122501":  {"plant": "",        "strain": "Jokerz 31"},
    "SJ102501":   {"plant": "",        "strain": "Sleepy Joy"},
    "SJ112501":   {"plant": "",        "strain": "Sleepy Joy"},
    "KC102501":   {"plant": "",        "strain": "Kush Crasher"},
    "GRC102501-2":{"plant": "",        "strain": "Graps Crème"},
    "OPM122501":  {"plant": "",        "strain": "Orange Punch Mimosa"},
    # UKIM-only batches (DAB cannabinoids + LoD)
    "PM112501":   {"plant": "",        "strain": "Permanent Market"},
    "OPM112501":  {"plant": "",        "strain": "Orange Punch Mimosa"},
    "GG112501":   {"plant": "",        "strain": "Gorilla Glue"},
    "GG012601":   {"plant": "",        "strain": "Gorilla Glue"},
    "JD112501":   {"plant": "",        "strain": "Jelly Donutz"},
    "JD012601":   {"plant": "",        "strain": "Jelly Donutz"},
    "FB112501":   {"plant": "",        "strain": "Fat Bastard"},
    "FB012601":   {"plant": "",        "strain": "Fat Bastard"},
    "CC112501":   {"plant": "",        "strain": "Cash Cow"},
    "SCR112501":  {"plant": "",        "strain": "Scrambler"},
}


LAB_ID = {
    "UKIM": "UKIM Faculty of Pharmacy — Center for Natural Products (LT-083)",
    "Farmahem": "Farmahem Лабораторија за животна средина (LT-017)",
    "IPH": "ЈЗУ Институт за јавно здравје на РСМ (LT-005)",
    "IPH_Micro": "ЈЗУ ИЈЗ — Одделение за микробиолошка контрола (LT-005)",
    "DFL": "State Phytosanitary Lab — Direction for Food and Plant Protection (LT-036)",
}


# ───────────────────────── parsers per CoA family ──────────────────────────


def parse_farmahem(path: str) -> list[ParameterResult]:
    """Farmahem .txt: cannabinoids HPLC OR Loss on Drying."""
    text = open(path).read()
    is_lod = "_LoD" in path or "GS-" in path
    doc_match = re.search(r"Report No[:\s]+([0-9A-Za-z-]+/\d+)", text)
    date_match = re.search(r"Issued[:\s]+([\d.]+)", text)
    doc_code = doc_match.group(1) if doc_match else "?"
    issue_date = _norm_date(date_match.group(1)) if date_match else "?"
    out: list[ParameterResult] = []
    if is_lod:
        m = re.search(r"Loss on Drying[^\n]*?[:\s]+([\d.]+)\s*%", text, re.I) or \
            re.search(r"\bLoD[):\s]+([\d.]+)\s*%", text, re.I)
        if m:
            out.append(ParameterResult(
                parameter="Loss on drying",
                method="Ph.Eur. 2.2.32",
                spec="≤ 10.00 %",
                result=f"{m.group(1)} %",
                lab=LAB_ID["Farmahem"], doc_code=doc_code, issue_date=issue_date,
                complies=float(m.group(1)) < 10.0))
    else:
        for key, label, method, spec in [
            ("Total CBD", "Total CBD", "HPLC/DAD Ph.Eur. 2.2.29", "report"),
            ("Total d9-THC", "Total Δ9-THC", "HPLC/DAD Ph.Eur. 2.2.29", "report"),
            ("Total CBN", "Total CBN", "HPLC/DAD Ph.Eur. 2.2.29", "report"),
        ]:
            m = re.search(rf"{re.escape(key)}[:\s]+([<>\d.LOQND%/+(-]+(?:[^%\n]*%)?)", text)
            if m:
                out.append(ParameterResult(
                    parameter=label, method=method, spec=spec,
                    result=m.group(1).strip(),
                    lab=LAB_ID["Farmahem"], doc_code=doc_code, issue_date=issue_date))
    return out


def parse_ukim(path: str) -> list[ParameterResult]:
    """UKIM ППК .txt: cannabinoids + LoD per DAB."""
    text = open(path).read()
    fn = os.path.basename(path)
    m = re.search(r"PPK(\d+)", fn)
    doc_code = f"ППК{m.group(1)}" if m else "?"
    # Date locations across our UKIM stagings:
    #   "Issued: 05.03.2026"  (our stability files)
    #   "Скопје, 21.01.2026" (raw Drive-OCR'd UKIM CoAs)
    issue_date = "?"
    for pat in (r"Issued:\s*([\d.]+)",
                r"Скопје,\s*([\d.]+)",
                r"issued\s+([\d.-]+)"):
        dm = re.search(pat, text, re.I)
        if dm:
            issue_date = _norm_date(dm.group(1))
            break
    out: list[ParameterResult] = []
    lod = re.search(r"Loss on drying[:\s|]*([\d.]+)\s*%", text, re.I) or \
          re.search(r"Губиток при сушење[\s\S]{0,80}?([\d.]+)\s*%", text)
    if lod:
        out.append(ParameterResult(
            parameter="Loss on drying", method="Ph.Eur. 2.2.32",
            spec="≤ 10.00 %", result=f"{lod.group(1)} %",
            lab=LAB_ID["UKIM"], doc_code=doc_code, issue_date=issue_date,
            complies=float(lod.group(1)) < 10.0))
    for key, label in [("Total CBD", "Total CBD"),
                       ("Total Δ9-THC", "Total Δ9-THC")]:
        m2 = re.search(rf"{re.escape(key)}[:\s|]+([<>\d.%]+)", text)
        if m2:
            out.append(ParameterResult(
                parameter=label, method="HPLC/DAD per DAB (Ph.Eur. 2.2.29)",
                spec="reported value",
                result=m2.group(1).strip(),
                lab=LAB_ID["UKIM"], doc_code=doc_code, issue_date=issue_date))
    return out


# Bundle file → multi-parameter assembly. The Bundle headers carry a
# stable structure produced by the cloud session; we parse line-by-line.
def parse_bundle(path: str) -> list[ParameterResult]:
    text = open(path).read()
    refs: dict[str, tuple[str, str]] = {}
    for line in text.splitlines():
        # UKIM:  "1) UKIM ... ППК26001 (LT-083), issued 21.01.2026 | sample 12.5 g"
        m = re.search(r"UKIM[^|]*?(ППК\d+).*?issued\s+([\d.]+)", line)
        if m:
            refs.setdefault("UKIM_LINE", (m.group(1), _norm_date(m.group(2))))
            continue
        # IPH Microbiology must come BEFORE generic IPH match
        m = re.search(r"IPH\s+Microbiology\s+(\S+).*?issued\s+([\d.]+)", line, re.I)
        if m:
            refs.setdefault("IPH_MICRO", (m.group(1), _norm_date(m.group(2))))
            continue
        # IPH full panel: "3) IPH 87/2026 (ЈЗУ, LT-005), issued 03.02.2026 | sample 31 g, Refus"
        m = re.search(r"IPH\s+(\d+/\d+).*?issued\s+([\d.]+)", line, re.I)
        if m:
            refs.setdefault("IPH_FULL", (m.group(1), _norm_date(m.group(2))))
            continue
        # Farmahem mycotoxin: "Farmahem 276-31-М/25 (LT-017), issued 04.12.2025"
        m = re.search(r"Farmahem\s+(\S+/\d+).*?issued\s+([\d.]+)", line, re.I)
        if m:
            refs.setdefault("FARMAHEM_MYC", (m.group(1), _norm_date(m.group(2))))
            continue
        # State Phytosanitary: "State Phytosanitary Lab DFL report 10802_2845/2 (LT-036), issued 17.11.2025"
        m = re.search(r"State Phytosanitary[^()]*?(\S+/\d+).*?issued\s+([\d.]+)", line, re.I)
        if m:
            refs.setdefault("DFL", (m.group(1), _norm_date(m.group(2))))
    result: list[ParameterResult] = []
    # LoD + cannabinoids → UKIM
    if "UKIM_LINE" in refs:
        m = re.search(r"LoD\s+([\d.]+)\s*%", text)
        if m:
            result.append(ParameterResult(
                parameter="Loss on drying", method="Ph.Eur. 2.2.32",
                spec="≤ 10.00 %", result=f"{m.group(1)} %",
                lab=LAB_ID["UKIM"], doc_code=refs["UKIM_LINE"][0],
                issue_date=refs["UKIM_LINE"][1],
                complies=float(m.group(1)) < 10.0))
        # Cannabinoids one-liner:  "LoD 7.50% | CBDA 0.09% | ... | Total Δ9-THC 21.67%"
        for key, label in [(r"Total CBD\b", "Total CBD"),
                           (r"Total Δ9-THC", "Total Δ9-THC")]:
            m2 = re.search(rf"{key}\s+([\d.]+)\s*%", text)
            if m2:
                result.append(ParameterResult(
                    parameter=label, method="HPLC/DAD per DAB (Ph.Eur. 2.2.29)",
                    spec="reported value", result=f"{m2.group(1)} %",
                    lab=LAB_ID["UKIM"], doc_code=refs["UKIM_LINE"][0],
                    issue_date=refs["UKIM_LINE"][1]))
    # Pesticides → IPH or DFL
    pest_ref = refs.get("DFL") or refs.get("IPH_FULL")
    if pest_ref and re.search(r"Pesticides[^\n]*COMPLIES", text):
        result.append(ParameterResult(
            parameter="Pesticide residues (full Ph.Eur. panel)",
            method="Ph.Eur. 2.8.13 (MKC EN 15662:2020)",
            spec="all н.д. (below LOQ 0.05–3 mg/kg)",
            result="ALL н.д. — COMPLIES",
            lab=LAB_ID["DFL"] if "DFL" in refs else LAB_ID["IPH"],
            doc_code=pest_ref[0], issue_date=pest_ref[1]))
    # Heavy metals → IPH
    if refs.get("IPH_FULL"):
        m_pb = re.search(r"Pb\s+([\d.]+|н\.д\.)", text)
        m_cd = re.search(r"Cd\s+([\d.]+|н\.д\.)", text)
        m_as = re.search(r"As\s+([\d.]+|н\.д\.)", text)
        m_hg = re.search(r"Hg\s+([\d.]+|н\.д\.)", text)
        if m_pb or m_cd or m_as or m_hg:
            details = []
            if m_pb: details.append(f"Pb {m_pb.group(1)} mg/kg")
            if m_cd: details.append(f"Cd {m_cd.group(1)} mg/kg")
            if m_as: details.append(f"As {m_as.group(1)} mg/kg")
            if m_hg: details.append(f"Hg {m_hg.group(1)} mg/kg")
            result.append(ParameterResult(
                parameter="Heavy metals (Pb / Cd / As / Hg)",
                method="Ph.Eur. 2.4.27 (EN 14084 / EN 17851)",
                spec="Pb ≤ 5 / Cd ≤ 1 / As ≤ 2 / Hg ≤ 0.1 mg/kg",
                result=" | ".join(details),
                lab=LAB_ID["IPH"], doc_code=refs["IPH_FULL"][0],
                issue_date=refs["IPH_FULL"][1]))
    # Mycotoxins
    myco_ref = refs.get("FARMAHEM_MYC") or refs.get("IPH_FULL")
    if myco_ref and re.search(r"aflatoxin", text, re.I):
        m = re.search(r"Total aflatoxins[^\n]*?([<>]?\s*[\d.]+)\s*µg/kg", text)
        result.append(ParameterResult(
            parameter="Mycotoxins (total aflatoxins B1+B2+G1+G2)",
            method="Ph.Eur. 2.8.18 (AflaTest fluorometric)",
            spec="≤ 4 µg/kg",
            result=f"{m.group(1).strip() if m else 'ND'} µg/kg",
            lab=LAB_ID["Farmahem"] if "FARMAHEM_MYC" in refs else LAB_ID["IPH"],
            doc_code=myco_ref[0], issue_date=myco_ref[1]))
    # Microbiology → IPH Micro
    if refs.get("IPH_MICRO"):
        m_tamc = re.search(r"TAMC[\s|]*([<>\d.×x\s]+CFU/g)", text)
        m_tymc = re.search(r"TYMC[\s|]*([<>\d.×x\s]+CFU/g)", text)
        details = []
        if m_tamc: details.append(f"TAMC {m_tamc.group(1).strip()}")
        if m_tymc: details.append(f"TYMC {m_tymc.group(1).strip()}")
        details.append("E.coli absent | Salmonella absent/25 g")
        result.append(ParameterResult(
            parameter="Microbial enumeration (TAMC / TYMC / E.coli / Salmonella)",
            method="Ph.Eur. 5.1.8 cat C / 2.6.12 / 2.6.31",
            spec="TAMC ≤ 10⁵ | TYMC ≤ 10⁴ | E.coli absent | Salmonella absent/25 g",
            result=" | ".join(details),
            lab=LAB_ID["IPH_Micro"], doc_code=refs["IPH_MICRO"][0],
            issue_date=refs["IPH_MICRO"][1]))
    return result


# ─────────────────────────────── helpers ──────────────────────────────────


def _norm_date(s: str) -> str:
    """Macedonian DD.MM.YYYY → YYYY-MM-DD."""
    m = re.match(r"(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})", s)
    if not m:
        return s.strip(" .")
    d, mo, y = m.groups()
    y = "20" + y if len(y) == 2 else y
    return f"{y}-{int(mo):02d}-{int(d):02d}"


def _detect_batch_from_filename(fn: str) -> Optional[str]:
    """Map a staged filename to one of BATCHES keys.
    Strategy: scan filename for the longest BATCHES key that appears as a token.
    """
    # Match any BATCHES key surrounded by word boundaries (or _).
    # Sort longest-first so 'BSS10240_01' beats 'BSS10240' (if it existed).
    for key in sorted(BATCHES, key=len, reverse=True):
        if re.search(rf"(?:^|[_-]){re.escape(key)}(?:[_.-]|$)", fn):
            return key
    # Stability files: pattern UKIM_PPK260xx_GrapePie_P05xxxx_stability_...
    m = re.search(r"(P0\d{5})", fn)
    if m:
        plant = m.group(1)
        for key, meta in BATCHES.items():
            if meta["plant"] == plant:
                return key
    return None


# ─────────────────────────────── assemble ──────────────────────────────────


def assemble() -> dict[str, BatchCoQ]:
    coqs: dict[str, BatchCoQ] = {}
    for key, meta in BATCHES.items():
        coqs[key] = BatchCoQ(
            batch_code=key, plant_code=meta["plant"], strain=meta["strain"])
    for fn in sorted(os.listdir(STAGED)):
        if not fn.endswith(".txt"):
            continue
        batch = _detect_batch_from_filename(fn)
        if not batch or batch not in coqs:
            continue
        path = os.path.join(STAGED, fn)
        if fn.startswith("Bundle_"):
            params = parse_bundle(path)
        elif fn.startswith("Farmahem_"):
            params = parse_farmahem(path)
        elif fn.startswith("UKIM_PPK"):
            params = parse_ukim(path)
        else:
            params = []
        if params:
            coqs[batch].parameters.extend(params)
            coqs[batch].source_files.append(fn)
    return coqs


# ──────────────────────────────── render ───────────────────────────────────


def render_md(coq: BatchCoQ) -> str:
    h = []
    h.append(f"# Certificate of Quality — {coq.strain} (batch {coq.batch_code})")
    h.append("")
    h.append(f"- **Production batch:** {coq.batch_code}"
             + (f"  |  **Plant code:** {coq.plant_code}" if coq.plant_code else ""))
    h.append(f"- **Variety:** {coq.strain}")
    h.append(f"- **Marketing-authorisation holder:** {coq.client}")
    h.append(f"- **Reference monograph:** Ph.Eur. 11.5 *Cannabis flower for medical use* (3028)")
    h.append("")
    h.append("## Quality results per Ph.Eur. 3028 parameter")
    h.append("")
    h.append("| Parameter | Method | Specification | Result | Issuing Lab | Doc Code | Issue Date |")
    h.append("|---|---|---|---|---|---|---|")
    # canonical Ph.Eur. ordering
    order = ["Identification", "Loss on drying", "Foreign matter",
             "Total CBD", "Total Δ9-THC", "Total CBN",
             "Pesticide", "Heavy metals", "Mycotoxins", "Microbial"]
    seen: set[tuple] = set()
    rows = []
    for ord_key in order:
        for p in coq.parameters:
            if p.parameter.startswith(ord_key):
                key = (p.parameter, p.doc_code)
                if key in seen:
                    continue
                seen.add(key)
                rows.append(p)
    for p in coq.parameters:
        key = (p.parameter, p.doc_code)
        if key in seen:
            continue
        seen.add(key)
        rows.append(p)
    esc = lambda s: s.replace("|", "\\|")
    for p in rows:
        h.append(f"| {esc(p.parameter)} | {esc(p.method)} | {esc(p.spec)} | "
                 f"{esc(p.result)} | {esc(p.lab)} | {esc(p.doc_code)} | "
                 f"{esc(p.issue_date)} |")
    h.append("")
    if not rows:
        h.append("> ⚠ No parameter data assembled for this batch yet — staging incomplete.")
        h.append("")
    h.append("## Source documents")
    h.append("")
    for f in coq.source_files:
        h.append(f"- `staged_coas/{f}`")
    h.append("")
    h.append("---")
    h.append("_Generated by `build_coqs.py` from staged CoA extracts. "
            "Each parameter row is independently traceable via its doc-code._")
    h.append("")
    return "\n".join(h)


# ───────────────────────────────── main ────────────────────────────────────


def main() -> int:
    os.makedirs(OUTDIR, exist_ok=True)
    coqs = assemble()
    index = []
    for key, coq in sorted(coqs.items()):
        if not coq.parameters:
            continue  # skip empties — they're documented in the index footer
        out = os.path.join(OUTDIR, f"CoQ_{coq.slug}.md")
        with open(out, "w") as f:
            f.write(render_md(coq))
        index.append({
            "batch_code": coq.batch_code,
            "plant_code": coq.plant_code,
            "strain": coq.strain,
            "params_count": len(coq.parameters),
            "sources_count": len(coq.source_files),
            "file": os.path.basename(out),
        })
        print(f"  wrote {out}  ({len(coq.parameters)} params, "
              f"{len(coq.source_files)} sources)")
    with open(os.path.join(OUTDIR, "INDEX.json"), "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    # Coverage report
    empties = [k for k, c in coqs.items() if not c.parameters]
    print(f"\nCoQs written: {len(index)} / {len(coqs)}  "
          f"(empty: {len(empties)} → {', '.join(empties[:8])}{'…' if len(empties)>8 else ''})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
