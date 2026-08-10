#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared classification and pivot layer for the master eCoA table.

Both builders (workbook and HTML register) import from here so a classification fix
lands in both artifacts at once and they can never disagree about a batch's disposition.
"""
import csv
import os
import re
from collections import defaultdict, OrderedDict

DEFAULT_TSV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "exports", "master_coa_table.tsv")

# --- parameter buckets ------------------------------------------------------
# Certificates name the same analyte in several ways: a screen heading
# ("Pesticide/insecticide screen — Lindan") on some reports, a bare compound name
# ("Lindan", "Deltamethrin") on others. Matching only the heading dropped 644 of 2,339
# rows — 27.5% of the dataset, including whole pesticide panels that were then rendered
# as "no data". Order matters here: the first pattern to match wins, so totals are
# tested before the individual cannabinoid components they are computed from.
PESTICIDE_COMPOUND_RE = re.compile(
    r"deltamethrin|chlorpyri|endosulfan|lindan|aldrin|dieldrin|\bhch\b|\bhcb\b"
    r"|hexachlorbenz|hexachlorobenz|\bddt\b|\bdde\b|\bddd\b|heptachlor|endrin"
    r"|chlordane|meto?xychlor|methoxychlor|пестицид", re.I)

BUCKETS = [
    ("packaging", re.compile(r"packaging|closure integrity|label(l)?ing", re.I)),
    ("appearance", re.compile(r"^appearance|appearance\s*[—-]|изглед", re.I)),
    ("identification", re.compile(r"identification|идентифика", re.I)),
    ("foreign_matter", re.compile(r"foreign matter|страни матери", re.I)),
    ("loss_on_drying", re.compile(r"loss on drying|губиток.*сушењ", re.I)),

    ("pesticides", re.compile(
        r"pesticide|insecticide"
        r"|deltamethrin|chlorpyri|endosulfan|lindan|aldrin|dieldrin|\bhch\b|\bhcb\b"
        r"|hexachlorbenz|hexachlorobenz|\bddt\b|\bdde\b|\bddd\b|heptachlor|endrin"
        r"|chlordane|meto?xychlor|methoxychlor|пестицид", re.I)),

    ("aflatoxins", re.compile(r"aflatoxin|афлатоксин", re.I)),
    ("ochratoxin", re.compile(r"ochratoxin|охратоксин", re.I)),

    ("pb", re.compile(r"\blead\b|олово", re.I)),
    ("cd", re.compile(r"cadmium|кадмиум", re.I)),
    ("as_", re.compile(r"\barsenic\b|арсен", re.I)),
    ("hg", re.compile(r"\bmercury\b|жива", re.I)),
    ("cu", re.compile(r"\bcopper\b|бакар", re.I)),
    # Some bundles report the metals panel only as a single conformity statement.
    ("metals_panel", re.compile(r"heavy metals?.*(full panel|panel)|тешки метали", re.I)),

    ("tamc", re.compile(r"\btamc\b|total aerobic microbial", re.I)),
    ("tymc", re.compile(r"\btymc\b|yeasts.*moulds|combined yeast", re.I)),
    ("bile", re.compile(r"bile.?tolerant", re.I)),
    ("ecoli", re.compile(r"escherichia|e\.\s?coli", re.I)),
    ("salmonella", re.compile(r"salmonella", re.I)),
    ("micro_other", re.compile(r"staphylococc|pseudomonas|clostrid|candida|aspergill", re.I)),

    # Release assay totals — must precede the component patterns below.
    ("thc", re.compile(r"(total|вкупно)[^|]*?(δ9|delta.?9|\bthc\b|tetrahydrocannabinol)", re.I)),
    ("cbd", re.compile(r"(total|вкупен)[^|]*?(\bcbd\b|cannabidiol(?!ic))", re.I)),
    ("cbn", re.compile(r"(total|вкупен)[^|]*?(\bcbn\b|cannabinol)", re.I)),

    # Individual cannabinoid readings (acid and neutral forms) reported alongside the
    # totals. Kept in their own column so they can never overwrite a release assay value.
    ("cannabinoid_profile", re.compile(
        r"\bcbda\b|cannabidiolic|\bthca\b|tetrahydrocannabinolic"
        r"|\bcbd\b|cannabidiol(?!ic)|\bcbn\b|cannabinol"
        r"|\bthc\b|δ9|delta.?9|cannabinoid profile|related substances", re.I)),
]

COLS = OrderedDict([
    ("appearance", "Appearance"),
    ("identification", "Identification"),
    ("foreign_matter", "Foreign matter"),
    ("loss_on_drying", "Loss on drying"),
    ("thc", "Total Δ9-THC"),
    ("cbd", "Total CBD"),
    ("cbn", "Total CBN"),
    ("cannabinoid_profile", "Cannabinoid profile (components)"),
    ("aflatoxins", "Aflatoxins"),
    ("ochratoxin", "Ochratoxin A"),
    ("pb", "Lead"), ("cd", "Cadmium"), ("as_", "Arsenic"), ("hg", "Mercury"),
    ("cu", "Copper (informational)"),
    ("metals_panel", "Heavy metals (panel summary)"),
    ("pesticides", "Pesticide screen"),
    ("tamc", "TAMC"), ("tymc", "TYMC"), ("bile", "Bile-tol. GNB"),
    ("ecoli", "E. coli"), ("salmonella", "Salmonella"),
    ("micro_other", "Other microbiology"),
    ("packaging", "Packaging"),
])

PESTICIDE_RE = re.compile(r"pesticide|insecticide", re.I)
STABILITY_RE = re.compile(r"stabilit|стабилн|month\s*\d|месец|\d+\s*°?C\s*/\s*\d+\s*%\s*RH", re.I)
GAP_RE = re.compile(r"^\[COVERAGE GAP\]$")
OVERALL_RE = re.compile(r"overall result|заклучок|^\[NOTE\]", re.I)

# A result is only ever treated as a *finding* when nothing in it says otherwise.
# Anything asserting conformity, non-detection or a below-limit reading is compliant;
# inferring a detection from unmatched prose once turned a passing pesticide screen
# ("Not found any pesticide above LOQ — COMPLIES") into a red non-conformance.
COMPLIANT_RE = re.compile(
    r"^(н\.?д\.?|n\.?d\.?|nd)\b"
    r"|not\s+found|not\s+detect|non[- ]?detect|undetect"
    r"|complies|conform(?!ance)|одговара(?<!не одговара)"
    r"|<\s*loq|≤\s*loq|below\s+loq|blq|<\s*lod|absent|отсутна"
    r"|^\s*<", re.I)

# Explicit failure language. Single source of truth for status *and* cell colouring.
CRIT_RE = re.compile(r"does not conform|non[- ]?conform|не одговара|нe одговара", re.I)
FLAG_RE = re.compile(r"DATA INTEGRITY FLAG|" + CRIT_RE.pattern, re.I)

URL_RE = re.compile(r"^https?://", re.I)

# Accredited external laboratories, normalised. Purely Plant is the sponsor, never an issuer.
LAB_PATTERNS = [
    ("Farmahem", re.compile(r"farmahem", re.I)),
    ("UKIM Faculty of Pharmacy — Center for Natural Products", re.compile(r"ukim|faculty of pharmacy|природни производи", re.I)),
    ("IPH — Institute of Public Health", re.compile(r"institute of public health|јавно здравје|\biph\b", re.I)),
    ("State Phytosanitary Laboratory", re.compile(r"phytosanitary|фитосанитар", re.I)),
    ("New Garden Pharma", re.compile(r"new garden pharma", re.I)),
]


def clean_link(raw):
    """Return a usable URL, or '' when the field holds prose (e.g. a coverage-gap note)."""
    if not raw:
        return ""
    candidate = raw.split(" (folder")[0].strip()
    return candidate if URL_RE.match(candidate) else ""


def classify(param_text):
    if GAP_RE.match(param_text):
        return "gap"
    if OVERALL_RE.search(param_text):
        return "overall"
    if STABILITY_RE.search(param_text):
        return "stability"
    if PESTICIDE_RE.search(param_text):
        return "pesticides"
    for key, rx in BUCKETS:
        if rx.search(param_text):
            return key
    return None


def cite(row):
    parts = [p for p in (row["Certificate Code"].strip(), row["Issue Date"].strip(),
                         row["Issuing Institution"].strip())
             if p and p.lower() not in ("n/a", "na")]
    return " · ".join(parts)


def load_rows(path=None):
    """Load the extract. QUOTE_NONE keeps verbatim transcriptions intact — a result may
    legitimately begin with a double quote, which the default dialect would swallow."""
    path = path or DEFAULT_TSV
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        rows = []
        for r in reader:
            r["Seq"] = int(r["Seq"])
            rows.append(r)
    return rows


def group_by_seq(rows):
    by_seq = defaultdict(list)
    for r in rows:
        by_seq[r["Seq"]].append(r)
    return by_seq


def count_labs(rows):
    """Distinct accredited external laboratories actually cited."""
    found = set()
    for r in rows:
        inst = r.get("Issuing Institution", "")
        for name, rx in LAB_PATTERNS:
            if rx.search(inst):
                found.add(name)
    return len(found)


def pivot_batch(brows):
    """Collapse one batch's parameter rows into the wide column set.

    Returns dict with identity, status, per-column {value, sources[], links[]}, notes.
    """
    hits = defaultdict(list)
    gap_notes, overall_notes, flags = [], [], []
    pest_rows, pest_findings, stability_count = [], [], 0

    for r in brows:
        kind = classify(r["Parameter"])
        # Flags are captured for every row kind, including the ones we route away below;
        # a data-integrity flag on a stability or gap row still concerns the batch.
        if FLAG_RE.search(r["Result"]):
            flags.append(r["Parameter"])

        if kind == "gap":
            gap_notes.append(r["Result"])
            continue
        if kind == "overall":
            overall_notes.append(r["Result"])
            continue
        if kind == "stability":
            stability_count += 1
            continue
        if kind == "pesticides":
            pest_rows.append(r)
            if not COMPLIANT_RE.search(r["Result"].strip()):
                pest_findings.append("%s: %s" % (r["Parameter"], r["Result"]))
            continue
        if kind:
            hits[kind].append(r)

    out = {}
    for key in COLS:
        if key == "pesticides":
            if not pest_rows:
                out[key] = {"value": "—", "sources": [], "links": []}
            else:
                srcs, links = [], []
                for h in pest_rows:
                    c, l = cite(h), clean_link(h["Drive File Link"])
                    if c and c not in srcs:
                        srcs.append(c)
                        links.append(l)
                if pest_findings:
                    value = "Above LOQ — %s" % "; ".join(pest_findings)
                elif len(pest_rows) == 1:
                    # A single row is a screen-level statement (one report can cover
                    # hundreds of residues). Counting rows as "compounds" understated a
                    # 471-residue screen as "1 compound", so quote the laboratory instead.
                    value = pest_rows[0]["Result"].strip()
                else:
                    value = "All not detected · %d compounds" % len(pest_rows)
                out[key] = {"value": value, "sources": srcs, "links": links}
            continue

        hs = hits.get(key, [])
        if not hs:
            out[key] = {"value": "—", "sources": [], "links": []}
        else:
            vals, srcs, links = [], [], []
            for h in hs:
                v = h["Result"].strip()
                if v not in vals:
                    vals.append(v)
                c, l = cite(h), clean_link(h["Drive File Link"])
                if c and c not in srcs:
                    srcs.append(c)
                    links.append(l)
            out[key] = {"value": " | ".join(vals), "sources": srcs, "links": links}

    meta = brows[0]
    is_open = any(CRIT_RE.search(n) for n in overall_notes + gap_notes)
    if is_open:
        status = "open"
    elif gap_notes:
        status = "partial"
    elif flags:
        status = "flag"
    else:
        status = "complete"

    notes = []
    if overall_notes:
        notes.append("Conclusion: " + " / ".join(overall_notes))
    if gap_notes:
        cats = set()
        for n in gap_notes:
            low = n.lower()
            for pat, lab in (("pesticide", "pesticides"), ("heavy", "heavy metals"),
                             ("metal", "heavy metals"), ("mycotox", "mycotoxins"),
                             ("microbio", "microbiology"),
                             ("identification", "identity / foreign matter / LoD"),
                             ("foreign", "identity / foreign matter / LoD")):
                if pat in low:
                    cats.add(lab)
        notes.append("No certificate on file for: " + ", ".join(sorted(cats))
                     if cats else "Coverage gap recorded")
    if flags:
        notes.append("Data-integrity flag — " + ", ".join(sorted(set(flags))))
    if stability_count:
        notes.append("%d stability results held separately" % stability_count)

    return {
        "seq": meta["Seq"],
        "batch": meta["Cultivation Batch"],
        "p_number": meta["P-Number"],
        "strain": meta["Strain"],
        "status": status,
        "vals": out,
        "notes": " · ".join(notes),
    }


def severity(value):
    """'crit' | 'warn' | 'na' | '' for a rendered cell value."""
    if value == "—":
        return "na"
    if CRIT_RE.search(value) or value.startswith("Above LOQ —"):
        return "crit"
    if "data integrity flag" in value.lower():
        return "warn"
    return ""


def build(path=None):
    rows = load_rows(path)
    by_seq = group_by_seq(rows)
    seqs = sorted(by_seq)
    expected = list(range(1, len(seqs) + 1))
    if seqs != expected:
        raise SystemExit("Seq coverage broken: expected 1..%d, got %d values (missing %s)"
                         % (len(seqs), len(seqs), sorted(set(expected) - set(seqs))))
    batches = [pivot_batch(by_seq[s]) for s in seqs]
    return rows, batches
