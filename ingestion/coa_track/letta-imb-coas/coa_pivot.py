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

    ("afla_b1", re.compile(r"aflatoxin\s*[- ]?\s*b\s*1|афлатоксин\s*b\s*1", re.I)),
    ("afla_b2", re.compile(r"aflatoxin\s*[- ]?\s*b\s*2|афлатоксин\s*b\s*2", re.I)),
    ("afla_g1", re.compile(r"aflatoxin\s*[- ]?\s*g\s*1|афлатоксин\s*g\s*1", re.I)),
    ("afla_g2", re.compile(r"aflatoxin\s*[- ]?\s*g\s*2|афлатоксин\s*g\s*2", re.I)),
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

    # Individual cannabinoid readings reported alongside the totals, each in its own column
    # so a component can never be mistaken for a release assay value. Acid forms are tested
    # before their neutral counterparts.
    ("cbda", re.compile(r"\bcbda\b|cannabidiolic", re.I)),
    ("thca", re.compile(r"\bthca\b|tetrahydrocannabinolic|δ9-thca|delta.?9.?thca", re.I)),
    ("cbd_n", re.compile(r"\bcbd\b|cannabidiol(?!ic)", re.I)),
    ("cbn_n", re.compile(r"\bcbn\b|cannabinol", re.I)),
    ("thc_n", re.compile(r"\bthc\b|δ9|delta.?9|tetrahydrocannabinol", re.I)),
]

COLS = OrderedDict([
    ("appearance", "Appearance"),
    ("identification", "Identification"),
    ("foreign_matter", "Foreign matter"),
    ("loss_on_drying", "Loss on drying"),
    ("thc", "Total Δ9-THC"),
    ("cbd", "Total CBD"),
    ("cbn", "Total CBN"),
    ("cbda", "CBDA"), ("cbd_n", "CBD"), ("cbn_n", "CBN"),
    ("thc_n", "Δ9-THC"), ("thca", "Δ9-THCA"),
    ("afla_b1", "Aflatoxin B1"), ("afla_b2", "Aflatoxin B2"),
    ("afla_g1", "Aflatoxin G1"), ("afla_g2", "Aflatoxin G2"),
    ("aflatoxins", "Aflatoxins Σ"),
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

# Deliberately absent: any rule that decides whether a result "passes".
#
# Two earlier attempts failed in the same way. A rule of "not starting with N.D. means
# detected" turned "Not found any pesticide above LOQ — COMPLIES" into a red
# non-conformance. Widening it to a compliance vocabulary still mis-read "Confirms" (the
# standard pass wording on every Purely Plant CoA) and could not interpret the "/", "–"
# or blank notations different laboratories use for the same idea.
#
# No vocabulary covers every convention across four laboratories and two languages, and a
# wrong guess fabricates or hides a pharmaceutical finding. Summaries therefore report the
# distribution of the verbatim values themselves, and a result is called a failure only
# where the issuing laboratory says so (CRIT_RE below).

# Explicit failure language. Single source of truth for status *and* cell colouring.
CRIT_RE = re.compile(r"does not conform|non[- ]?conform|не одговара|нe одговара", re.I)

# A positive finding the laboratory itself put in words — e.g. Farmahem reporting
# ochratoxin A as "2.06 µg/kg (U 11.80%) — DETECTED, >LOQ". Matching the lab's own
# wording is reading, not judging; "not detected" is explicitly excluded.
# Only the explicit word, never a phrase like "above LOQ" — that appears inside
# "Not found any pesticide above LOQ", which is a pass.
LAB_FINDING_RE = re.compile(r"(?<!not )(?<!non-)(?<!non )\bdetected\b", re.I)
FLAG_RE = re.compile(r"DATA INTEGRITY FLAG|" + CRIT_RE.pattern, re.I)

URL_RE = re.compile(r"^https?://", re.I)

# Accredited external laboratories, normalised. Purely Plant is the sponsor, never an issuer.
# Accreditation numbers are not printed in the Issuing Institution field; they were read from
# the certificate texts in the knowledgebase by scanning every passage for an ISO/IEC 17025
# number and recording which laboratory it appears with. Each mapping below is the dominant
# co-occurrence by a wide margin (hit counts in brackets); the stray cross-hits come from
# multi-report bundle PDFs that name several laboratories on one page.
LAB_PATTERNS = [
    ("Farmahem", re.compile(r"farmahem|фармахем", re.I), "LT-017"),                        # [31]
    ("UKIM Faculty of Pharmacy — Center for Natural Products",
     re.compile(r"ukim|faculty of pharmacy|природни производи", re.I), "LT-083"),          # [67]
    ("IPH — Institute of Public Health",
     re.compile(r"institute of public health|јавно здравје|\biph\b", re.I), "LT-005"),     # [111]
    ("State Phytosanitary Laboratory", re.compile(r"phytosanitary|фитосанитар", re.I), "LT-036"),  # [4]
    ("New Garden Pharma", re.compile(r"new garden pharma", re.I), ""),
]


def short_label(param):
    """The analyte's own name, without the screen heading or method reference.

    "Pesticide/insecticide screen (Ph.Eur. 2.8.13, MKC EN 15662:2020) - Deltamethrin"
    becomes "Deltamethrin", so a value can name what it measures without repeating the
    panel heading in every cell.
    """
    t = (param or "").strip()
    for sep in ("\u2014", " - "):
        if sep in t:
            t = t.split(sep)[-1].strip()
    t = re.sub(r"\s*\((?:Ph\.?\s*Eur|MKC|ИР)[^)]*\)\s*$", "", t, flags=re.I).strip()
    return t or (param or "").strip()


def clean_link(raw):
    """Return a usable URL, or '' when the field holds prose (e.g. a coverage-gap note)."""
    if not raw:
        return ""
    candidate = raw.split(" (folder")[0].strip()
    return candidate if URL_RE.match(candidate) else ""


def summarise_values(values):
    """Describe a set of results by the values themselves, never by a verdict.

    One value repeated is reported as "N × «value»"; a mixed set lists each distinct
    value with its count. An unfamiliar notation ("/", "–", a blank) is carried through
    verbatim instead of being guessed at.
    """
    values = [v for v in values]
    if not values:
        return "—"
    if len(values) == 1:
        return values[0] or "—"
    counts = OrderedDict()
    for v in values:
        label = v if v else "(blank)"
        counts[label] = counts.get(label, 0) + 1
    if len(counts) == 1:
        only = next(iter(counts))
        return "%d × %s" % (len(values), only)
    parts = ["%d × %s" % (c, v) for v, c in counts.items()]
    head = "; ".join(parts[:3])
    if len(parts) > 3:
        head += "; +%d more" % (len(parts) - 3)
    return "%d results — %s" % (len(values), head)


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


DATE_RE = re.compile(r"(\d{1,2}[./]\d{1,2}[./]\d{4})")
ISSUED_DATE_RE = re.compile(r"issued\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{4})", re.I)
DATE_DOUBT_RE = re.compile(r"as printed|likely|typo|DATA INTEGRITY|predates", re.I)


def issue_date(raw):
    """The date of issue, and nothing else.

    Source rows carry things like "Issued 02.03.2026 (analyzed 26-27.02.2026; received
    23.02.2026)". Only the issue date was asked for, so the analysis and receipt dates are
    dropped. A qualifier is kept only where the date itself is in doubt.
    """
    if not raw:
        return ""
    raw = raw.strip()
    m = ISSUED_DATE_RE.search(raw) or DATE_RE.search(raw)
    if not m:
        return raw
    date = m.group(1)
    if DATE_DOUBT_RE.search(raw):
        return "%s [see source]" % date
    return date


def cite(row):
    parts = [p for p in (row["Certificate Code"].strip(), issue_date(row["Issue Date"]),
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
        for name, rx, _accred in LAB_PATTERNS:
            if rx.search(inst):
                found.add(name)
    return len(found)


def pivot_batch(brows):
    """Collapse one batch's parameter rows into the wide column set.

    Returns dict with identity, status, per-column {value, sources[], links[]}, notes.
    """
    hits = defaultdict(list)
    gap_notes, overall_notes, flags = [], [], []
    pest_rows, stability_count = [], 0

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
                value = summarise_values([h["Result"].strip() for h in pest_rows])
                out[key] = {"value": value, "sources": srcs, "links": links}
            continue

        hs = hits.get(key, [])
        if not hs:
            out[key] = {"value": "—", "sources": [], "links": []}
        else:
            # A parameter can be measured more than once — a release assay and a later
            # retest by a different laboratory. Reading "14.83% | 15.70% w/w" gives no way
            # to tell whether that is two tests or one badly formatted value, so each value
            # carries the code of the certificate it came from as soon as there is
            # more than one. Batch Detail keeps them on separate rows entirely.
            pairs, srcs, links = [], [], []
            for h in hs:
                v = h["Result"].strip()
                code = h["Certificate Code"].strip()
                if not any(v == pv for pv, _pc in pairs):
                    pairs.append((v, code))
                c, l = cite(h), clean_link(h["Drive File Link"])
                if c and c not in srcs:
                    srcs.append(c)
                    links.append(l)
            if len(pairs) == 1:
                value = pairs[0][0]
            else:
                value = "   ·   ".join(
                    ("%s  [%s]" % (v, c)) if c else v for v, c in pairs)
            out[key] = {"value": value, "sources": srcs, "links": links}

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
    """'crit' | 'warn' | 'na' | '' for a rendered cell value.

    'crit' is reserved for a non-conformity the issuing laboratory declared in the text.
    Nothing here judges a measurement against a limit — that call belongs to the
    laboratory and to a qualified reviewer, not to this renderer.
    """
    if value == "—":
        return "na"
    if CRIT_RE.search(value):
        return "crit"
    if "data integrity flag" in value.lower() or LAB_FINDING_RE.search(value):
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
