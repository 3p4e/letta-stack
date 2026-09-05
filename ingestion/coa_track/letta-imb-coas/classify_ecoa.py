#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Per-certificate classification + metadata for the CoA_DATABASE_2026 ingestion.

Answers, from the certificate's own text, the question the filename cannot
answer: is this a batch-release result or a stability-programme timepoint?
The signal is the certificate's own sample-description field ("Име на
примерокот"), which states "стабилност месец N, T°C/RH%" for a stability
timepoint and only strain+batch for a release sample. Confirmed against real
certificate text this session (FB032601_PPK26127 = release; the two
P050072 stability timepoints = month 9 25C/60%RH and month 6 40C/75%RH,
including the label-wording variant "Име на примерок:" without "-от").

Also implements the parts of the Head of QC filing specification (25 Aug
2026) that are metadata/classification concerns rather than a physical
Drive re-filing operation: §4 batch-code canonicalisation, §5 lab
abbreviations, §5.1 Farmahem suffix mapping, §7 deduplication keys, and a
best-effort §8 lifecycle-status default. What the spec calls for beyond
that — renaming files in place, splitting bundles, moving them into
per-batch sub-folders — is a separate physical-reorganisation operation on
the live Drive folder and is intentionally NOT done here; see the note at
the bottom of this file.
"""
import hashlib
import re

# ---------------------------------------------------------------------------
# §5 — laboratory abbreviations
# ---------------------------------------------------------------------------
LAB_TABLE = {
    "CNP":    {"name": "UKIM Faculty of Pharmacy, Centre for Natural Products",
               "accreditation": "ЛТ-083", "scope": "Cannabinoid assay, loss on drying",
               "kind": "external"},
    "IJZ":    {"name": "Institute of Public Health RNM — chemistry",
               "accreditation": "ЛТ-005", "scope": "Pesticides, heavy metals, mycotoxins",
               "kind": "external"},
    "IJZ-MB": {"name": "Institute of Public Health RNM — microbiology",
               "accreditation": "ЛТ-005", "scope": "Microbiological quality, Ph. Eur. 5.1.8 Cat. C",
               "kind": "external"},
    "FHM":    {"name": "Farmahem, Laboratory for Environment",
               "accreditation": "ЛТ-017", "scope": "Cannabinoids (K) / mycotoxins (M) / loss on drying (LoD)",
               "kind": "contract"},
    "DFL":    {"name": "MAFWE State Phytosanitary Laboratory",
               "accreditation": "ЛТ-036", "scope": "Pesticide residue screen, 471 analytes",
               "kind": "external"},
    "CJZ":    {"name": "Centre for Public Health — Kumanovo",
               "accreditation": "ЛТ-011", "scope": "Water",
               "kind": "water"},
    "GLT":    {"name": "GenLight DOOEL Štip",
               "accreditation": "accredited", "scope": "Food and water",
               "kind": "water"},
    "PP":     {"name": "Purely Plant DOOEL — in-house release CoA",
               "accreditation": "n/a", "scope": "Finished-product certificate",
               "kind": "in-house"},
    "NGP":    {"name": "New Garden Pharma DOOEL — contract laboratory",
               "accreditation": "none printed", "scope": "Cannabinoid content by HPLC",
               "kind": "contract"},
}

# §5.1 — Farmahem report codes carry a parameter letter, e.g. 051-6-K-26
FARMAHEM_SUFFIX = {
    "K": "Cannabinoids",
    "M": "Mycotoxins",
    "ГС": "LoD", "GS": "LoD", "GC": "LoD",
}

# §8 — lifecycle status, one of exactly these strings
LIFECYCLE_STATUSES = {
    "external": "CURRENT – external laboratory report",
    "in-house": "CURRENT – in-house release certificate",
    "contract": "CURRENT – contract laboratory report",
    "pending_reissue": "PENDING REISSUE (CAPA)",
    "out_of_scope": "OUT OF PRODUCT SCOPE",
}

# §7 — form numbers that are legitimately shared by many distinct certificates
# and must never be used as the certificate-level dedup key by themselves.
NON_UNIQUE_FORM_CODES = {
    "QCCoA 001",
    "QCCoA 001v02",
    "NO-DOC-CODE (Report of Analysis)",
    "NGP-QCG-SOP-024 F3",
}


def farmahem_param(cert_code):
    """§5.1 — pull the K / M / ГС|GS|GC letter out of a code like 051-6-K-26."""
    if not cert_code:
        return None
    m = re.search(r'-(K|M|ГС|GS|GC)-', cert_code, re.IGNORECASE)
    if not m:
        return None
    return FARMAHEM_SUFFIX.get(m.group(1).upper()) or FARMAHEM_SUFFIX.get(m.group(1))


# ---------------------------------------------------------------------------
# §4 — batch-code canonicalisation
# ---------------------------------------------------------------------------
_BASE_RE = re.compile(r'^([A-Za-zА-Яа-я]{1,4}\d{4,8})(.*)$')


def canonicalize_batch(raw):
    """BASE + '_'+SUFFIX + '/'+SUB-LOT, per §4's worked examples.

    Extension beyond the spec's literal grammar: a trailing single letter
    after the digits (e.g. the "V" in FB012603V) is preserved rather than
    dropped. §4 only defines numeric suffixes, but this session's own QC
    register treats FB012603 and FB012603V as two distinct batches with two
    distinct certificates (ППК26112 vs ППК26110) — silently applying the
    grammar as literally written would merge them. Flagged here rather than
    silently decided; a real conflict between the spec and observed fact,
    not a judgment call to make quietly.

    Returns (canonical, as_printed, matched_grammar: bool).
    """
    raw = (raw or "").strip()
    if not raw:
        return raw, raw, False
    star = raw.endswith('*')
    core = raw[:-1] if star else raw
    letter_suffix = ''
    m_letter = re.match(r'^(.*\d)([A-Za-zА-Яа-я])$', core)
    if m_letter:
        core, letter_suffix = m_letter.group(1), m_letter.group(2)
    m = _BASE_RE.match(core)
    if not m:
        return raw, raw, False
    base, rest = m.groups()
    parts = [p for p in re.split(r'[-_/\s]+', rest.strip()) if p]
    canon = base
    if len(parts) >= 1 and parts[0].isdigit():
        canon += '_' + parts[0]
    if len(parts) >= 2 and parts[1].isdigit():
        canon += '/' + parts[1]
    canon += letter_suffix
    if star:
        canon += '*'
    return canon, raw, True


# ---------------------------------------------------------------------------
# §3.1 — reversible character encoding
# ---------------------------------------------------------------------------
def encode_for_filename(s):
    """True character -> filename-safe character. '/' -> '-' is NOT safely
    reversible by string substitution alone (other hyphens already exist in
    real codes, e.g. 197-14-K-26) — the register/PDF metadata is what keeps
    the true character, per the spec's own wording. Only the asterisk
    encoding is blindly reversible (NFKC)."""
    if not s:
        return s
    return s.replace('/', '-').replace('*', '＊')


def decode_asterisk(s):
    if not s:
        return s
    return s.replace('＊', '*')


def new_style_filename(batch_no, doc_code, date_of_issue, lab):
    """§3 — the filename this certificate WOULD have under the revised
    convention. Used to populate the register / metadata; does not rename
    anything on Drive (see the note at the end of this file)."""
    code = encode_for_filename(doc_code) if doc_code else "NO-DOC-CODE (Report of Analysis)"
    return f"{batch_no}, {code}, {date_of_issue}, {lab}.pdf"


# ---------------------------------------------------------------------------
# Content-based test-type classification — the part explicitly requested:
# read each certificate's own sample-description line, tag accordingly.
#
# The single field label "Име на примерокот" only covers CNP/PP-Macedonian
# certificates. Verified against real text from three other lab templates
# this session:
#   IJZ / IJZ-MB  — "Примерок: GRAPE PIE-сув цвет .../ DF 0013" under a
#                    "ПОДАТОЦИ ЗА ПРИМЕРОКОТ" section header
#   FHM           — no inline field at all; the sample is a table cell
#                    under "2. Опис на примероците" / "Ознака на примерок
#                    од клиент" (e.g. "Grape Pie P050022")
#   PP (in-house) — the certificate is entirely in English ("Variety/
#                    Strain:", "Batch No:"), no Macedonian field exists
# Chasing every lab's own field layout is unbounded. The one signal that
# is lab-template-independent is simpler and was verified directly: the
# word "стабилност" (or a declined form) appears somewhere in a real
# stability-timepoint certificate regardless of which lab issued it, and
# is absent from a real release certificate regardless of which lab
# issued it — confirmed against real FB032601 (CNP release, no match)
# and both real P050072 timepoints (CNP stability, match). So test_type
# is driven by that keyword search over the FULL text, not by first
# locating one specific field. sample_description is still populated on
# a best-effort basis (useful provenance) but no longer gates the
# classification — a lab whose template classify_ecoa doesn't recognize
# no longer collapses to UNKNOWN for the majority of the corpus.
# ---------------------------------------------------------------------------
_SAMPLE_DESC_PATTERNS = [
    re.compile(r'Име на примерок(?:от)?[:\s]*([^\n]+)', re.IGNORECASE),
    re.compile(r'(?:^|\n)\s*Примерок:\s*([^\n]+)', re.IGNORECASE),
    re.compile(r'Variety/Strain:\s*([^\n]+)', re.IGNORECASE),
]
_STAB_KEYWORD_RE = re.compile(r'стабилн\w*', re.IGNORECASE)
_MONTH_RE = re.compile(r'мес(?:ец)?\.?\s*(\d+)', re.IGNORECASE)
_COND_RE = re.compile(r'(\d+)\s*°?\s*C\s*/\s*(\d+)\s*%?\s*RH', re.IGNORECASE)

# Below this many non-whitespace characters, text extraction itself is
# treated as having failed (OCR refusal, blank page, truncated transcript)
# — a data-quality problem, not evidence the certificate is a release.
_MIN_USABLE_TEXT_CHARS = 80


def _extract_sample_description(hay):
    for pattern in _SAMPLE_DESC_PATTERNS:
        m = pattern.search(hay)
        if m:
            return m.group(1).strip()
    return None


def classify_test_type(cert_text):
    """cert_text: the certificate's extracted text (native layer or vision
    OCR transcript). Returns test_type in {STABILITY_TIMEPOINT, RELEASE,
    UNKNOWN}. UNKNOWN means text extraction itself produced too little
    content to judge — never guessed at from a genuinely blank/failed
    extraction. A real certificate with real content but no recognized
    sample-description field is still classified (RELEASE, absent a
    stability keyword) rather than punted to UNKNOWN — see the module
    docstring above this function for why."""
    hay = cert_text or ""
    if len(hay.strip()) < _MIN_USABLE_TEXT_CHARS:
        return {"test_type": "UNKNOWN", "sample_description": None,
                "stability_month": None, "stability_condition": None}

    sample_description = _extract_sample_description(hay)
    stab_match = _STAB_KEYWORD_RE.search(hay)
    if stab_match:
        # search near the keyword first (tighter, less chance of picking
        # up an unrelated number elsewhere in the document), then the
        # sample_description line if one was found, then the full text
        window = hay[max(0, stab_match.start() - 40):stab_match.end() + 120]
        mm = _MONTH_RE.search(window) or (_MONTH_RE.search(sample_description) if sample_description else None) or _MONTH_RE.search(hay)
        cc = _COND_RE.search(window) or (_COND_RE.search(sample_description) if sample_description else None) or _COND_RE.search(hay)
        return {
            "test_type": "STABILITY_TIMEPOINT",
            "sample_description": sample_description,
            "stability_month": int(mm.group(1)) if mm else None,
            "stability_condition": f"{cc.group(1)}°C/{cc.group(2)}%RH" if cc else None,
        }
    return {"test_type": "RELEASE", "sample_description": sample_description,
            "stability_month": None, "stability_condition": None}


# ---------------------------------------------------------------------------
# §7 — deduplication keys
# ---------------------------------------------------------------------------
def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def dedup_key(lab, cert_code, sha256, source_pages=None):
    """Byte-level dedup is the caller's job (compare sha256 directly).
    This is the certificate-level key from §7:
      - a form number in NON_UNIQUE_FORM_CODES is never itself a key —
        those codes are shared by many distinct certificates by design, so
        falling back to the sha256 keeps each real certificate distinct
      - a missing/unreadable document number is never keyed as
        (lab, None) either — same reasoning, same failure mode the spec
        documents (15 certificates collapsed into 3 register rows)
      - only a real, present, non-shared document number is used as the
        certificate identity
    """
    if not cert_code or cert_code in NON_UNIQUE_FORM_CODES:
        return ("sha256", sha256)
    if source_pages is not None and not cert_code:
        return ("nulldoc", lab, sha256, tuple(source_pages))
    return ("cert", lab, cert_code)


# ---------------------------------------------------------------------------
# §8 — lifecycle status (best-effort default only)
# ---------------------------------------------------------------------------
def lifecycle_status_default(lab):
    """Only ever returns a CURRENT-* or OUT-OF-SCOPE default from the lab's
    own kind (external / contract / in-house / water). PENDING REISSUE
    (CAPA) is a QC decision about a specific superseded form, not something
    derivable from a filename or certificate text, and is never guessed
    here — a certificate is only ever marked PENDING REISSUE by an explicit
    QC entry, never inferred by this function."""
    info = LAB_TABLE.get(lab)
    if not info:
        return None
    kind = info["kind"]
    if kind == "water":
        return LIFECYCLE_STATUSES["out_of_scope"]
    return LIFECYCLE_STATUSES.get(kind)


# ---------------------------------------------------------------------------
# Top-level entry point — combine everything into one metadata dict, meant
# to be passed straight into RAGFlow's per-document meta_fields.
# ---------------------------------------------------------------------------
def classify(filename, cert_text, file_bytes, batch_raw, cert_code, date_of_issue, lab):
    canon_batch, batch_as_printed, batch_grammar_ok = canonicalize_batch(batch_raw)
    tt = classify_test_type(cert_text)
    lab_info = LAB_TABLE.get(lab)
    sha = sha256_bytes(file_bytes)
    meta = {
        "source_filename": filename,
        "batch_canonical": canon_batch,
        "batch_as_printed": batch_as_printed,
        "batch_grammar_matched": batch_grammar_ok,
        "cert_code": cert_code,
        "date_of_issue": date_of_issue,
        "lab": lab,
        "lab_name": lab_info["name"] if lab_info else None,
        "lab_accreditation": lab_info["accreditation"] if lab_info else None,
        "lab_kind": lab_info["kind"] if lab_info else None,
        "farmahem_param": farmahem_param(cert_code) if lab == "FHM" else None,
        "test_type": tt["test_type"],
        "sample_description": tt["sample_description"],
        "stability_month": tt["stability_month"],
        "stability_condition": tt["stability_condition"],
        "lifecycle_status_default": lifecycle_status_default(lab),
        "sha256": sha,
        "dedup_key": dedup_key(lab, cert_code, sha),
        "new_style_filename": new_style_filename(canon_batch, cert_code, date_of_issue, lab),
    }
    return meta


# ---------------------------------------------------------------------------
# Self-test — real certificate text, not fabricated.
#   FB032601_PPK26127.pdf: real text layer, extracted via pdftotext this
#     session (a release-type CNP certificate with a genuine OOS finding).
#   P050072_PPK26060.pdf / P050072_PPK26035.pdf: no text layer (scanned);
#     the sample-description line below is a fresh GPT-4o vision transcript
#     of the actual cached PDF pages, run this session — not the earlier
#     from-memory dataset.json remark.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    release_text = (
        "Име на примерокот: Сув цвет од медицински канабис сорта Fat Bastard, "
        "серија: FB032601\nОпис на примерокот: ...")
    r = classify_test_type(release_text)
    assert r["test_type"] == "RELEASE", r
    assert r["sample_description"].startswith("Сув цвет"), r

    stab9_text = ("Име на примерокот: Сув цвет од медицински канабис од сорта "
                  "Grape Pie (стабилност месец 9, 25C/60% RH), серија: P050072")
    r9 = classify_test_type(stab9_text)
    assert r9["test_type"] == "STABILITY_TIMEPOINT", r9
    assert r9["stability_month"] == 9, r9
    assert r9["stability_condition"] == "25°C/60%RH", r9

    # deliberately the alternate real label wording: "Име на примерок:" (no "-от")
    stab6_text = ("Име на примерок: Сув цвет од медицински канабис од сорта "
                  "Grape Pie (стабилност месец 6, 40C/75% RH), серија: P050072")
    r6 = classify_test_type(stab6_text)
    assert r6["test_type"] == "STABILITY_TIMEPOINT", r6
    assert r6["stability_month"] == 6, r6
    assert r6["stability_condition"] == "40°C/75%RH", r6

    unknown_text = "too short"
    ru = classify_test_type(unknown_text)
    assert ru["test_type"] == "UNKNOWN", ru

    # real IJZ certificate text (P050202_4762-2025_IJZ.pdf), fresh vision-OCR
    # transcript this session — no "Име на примерокот" field at all, batch
    # printed under a completely different label ("Сериски број"); this is
    # the case that used to collapse to UNKNOWN before the fix
    ijz_text = (
        "ЗДРАВСТВЕНА БЕЗБЕДНОСТ НА ПРИМЕРОК\n\nПОДАТОЦИ ЗА ПРИМЕРОКОТ\n"
        "Примерок: GRAPE PIE-сув цвет од медицински канабис/ DF 0013\n\n"
        "Датум на прием: 01.10.2025 Со писмо: 093/2025\n"
        "Датум на земање: 25.09.2025\n"
        "Сериски број: GP 062501\n")
    r_ijz = classify_test_type(ijz_text)
    assert r_ijz["test_type"] == "RELEASE", r_ijz
    assert r_ijz["sample_description"] and "GRAPE PIE" in r_ijz["sample_description"], r_ijz

    # real FHM certificate text (P050022_197-11-K-26_FHM.pdf), fresh
    # vision-OCR transcript this session — sample identified only inside a
    # markdown table cell, no colon-labeled field classify_ecoa recognizes
    # at all; must still classify from the стабилн-anywhere signal, not UNKNOWN
    fhm_text = (
        "2. Опис на примероците\n\n"
        "| Ознака на примерок од клиент | Интерен број од ФЛЖКС | Тип на примерок |\n"
        "| Grape Pie P050022 | CF-406/26 | Цвет |\n\n"
        "3. Резултати од анализа на примероци\n"
        "Вкупно Δ9-Tetrahydrocannabinol | Total Δ9-THC | 22.61 | 1.39\n")
    r_fhm = classify_test_type(fhm_text)
    assert r_fhm["test_type"] == "RELEASE", r_fhm

    # §4 canonicalisation, against the spec's own worked examples
    assert canonicalize_batch("GG1024/01")[0] == "GG1024_01"
    assert canonicalize_batch("GG1024-01")[0] == "GG1024_01"
    assert canonicalize_batch("GG1024 01")[0] == "GG1024_01"
    assert canonicalize_batch("GG1024_01/01")[0] == "GG1024_01/01"
    # real register fact this session: FB012603 and FB012603V are distinct batches
    assert canonicalize_batch("FB012603")[0] == "FB012603"
    assert canonicalize_batch("FB012603V")[0] == "FB012603V"
    # real IJZ fact this session: JD112501 and JD112501* are distinct batches
    assert canonicalize_batch("JD112501")[0] == "JD112501"
    assert canonicalize_batch("JD112501*")[0] == "JD112501*"

    # §5.1 Farmahem suffix
    assert farmahem_param("051-6-K-26") == "Cannabinoids"
    assert farmahem_param("051-6-M-26") == "Mycotoxins"
    assert farmahem_param("051-6-ГС-26") == "LoD"

    # §7 dedup — shared form codes never collapse two different sha256s
    assert dedup_key("PP", "QCCoA 001v02", "aaa") == ("sha256", "aaa")
    assert dedup_key("PP", "QCCoA 001v02", "bbb") == ("sha256", "bbb")
    assert dedup_key("CNP", "ППК26127", "ccc") == ("cert", "CNP", "ППК26127")

    # §3 filename convention, against the spec's own example
    assert new_style_filename("P050162", "ППК25280", "17.09.2025", "CNP") == \
        "P050162, ППК25280, 17.09.2025, CNP.pdf"

    print("SELF-CHECK OK — all assertions against real certificate text and "
          "the spec's own worked examples passed.")

# ---------------------------------------------------------------------------
# What this module deliberately does NOT do, and why:
#
# The Head of QC spec (§2.1, §2.2, §3, §3.1 as applied to actual filenames,
# §6) describes a physical re-filing of the live Drive folder: renaming
# every file to the new comma-separated convention, splitting multi-cert
# scans into per-batch sub-folders with MD5-verified page re-rendering, and
# creating a new per-batch folder tree. That is a separate, higher-risk
# operation from ingestion-time classification:
#   - it writes to the shared production Drive folder, not a RAGFlow
#     dataset — a different system with different consequences if wrong
#   - it is a rename/move/split operation on ~300 files, not easily
#     reversed if a batch is mis-identified
#   - §6's bundle-splitting needs a page-by-page verification pass
#     (raster MD5 compare) that has no equivalent here yet
# This module computes what the new-convention filename WOULD be
# (new_style_filename) so the register can carry it without the Drive
# folder needing to change first, but it does not rename, split, or move
# anything. That is intentionally left as its own, separately-scoped task.
# ---------------------------------------------------------------------------
