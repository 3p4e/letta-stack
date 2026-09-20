#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""What makes one outsourced-laboratory eCOA the same document as another.

Filename-exact-match dedup (`ingest_new_documents.py`'s `have = {d['name']: ...}`)
breaks the moment a filename changes — which is exactly what the 20.09.2026 rename
of `eCoA_DATABASE` did to every one of the 283 documents already in `eCOA_DB`. This
module reads identity off the same fields a lab certificate is filed by, in either
of the two naming schemes this project has used, so a rename can never again turn
an already-ingested document into a "new" one.

Two schemes, both handled here:

  OLD  (RAGflow's current stored names, `eCOA_DB`)
       <batch or strain>_<doc code>, <date DD.MM.YYYY>_<Lab>.pdf
       e.g. "P060442_536-1067-26, 31.08.2026_IJZ-MB.pdf"

  NEW  (`eCoA_DATABASE`, renamed 20.09.2026)
       [P<batch> ][(<CU batch/strain>)]_<Lab>_<doc code>_<date DD.MM.YYYY>.pdf
       e.g. "P060182 (GRC102501)_FHM_031-1-K-26_10.02.2026.pdf"

Both parse into the same `Identity` tuple, and `identity_key()` is what dedup,
reissue-replace and cross-referencing should all compare — never the filename
string itself, and never a re-derivation of these rules inline.

The dedup key is (lab, doc_code, date) for a laboratory-issued certificate — a
lab's own filing/control-book number is unique to it by construction, so batch is
redundant there. The one exception is Purely Plant's own in-house reports, whose
"doc code" is a form/template number ("QCCoA 001", "QCCoA 001v02", "NO-DOC-CODE")
reused across many different batches on many different dates — there, the batch
(via `batch_key()`, which already carries the star/separator/collision rulings
this project has made) joins the key so two different in-house reports on the
same form, even on the same day, don't collide.
"""
import os
import re
import sys
from collections import namedtuple

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "common"))
from batch_id import batch_key  # noqa: E402

Identity = namedtuple("Identity", "p_batch cu_batch lab doc_code date")

# A P-number is P + six digits, per the ruling batch_id.py already encodes.
_P = r"P\d{6}"
_DATE = r"\d{2}\.\d{2}\.\d{4}"

_NEW = re.compile(
    r"^(?:(?P<p>" + _P + r"))?\s*"
    r"(?:\((?P<cu>.+?)\))?"
    r"_(?P<lab>[A-Za-z\-]+)_(?P<doc>.+)_(?P<date>" + _DATE + r")\.pdf$"
)
_OLD = re.compile(
    r"^(?:.*/)?(?P<rest>.+),\s*(?P<date>" + _DATE + r")_(?P<lab>[A-Za-z\-]+)\.pdf$"
)
# A pure sub-lot/verification/star segment: short, all-digit, nothing else attached.
# A doc-code segment that happens to start with digits ("565-1096-26", "051-6-LoD-26")
# always has more structure than this glued on, which is what tells the two apart.
_PURE_SUBLOT_SEGMENT = re.compile(r"^\d{1,3}[V]?[*＊]?$")


def _split_old_code_and_doc(rest):
    """Where the batch token ends and the doc code begins, in the OLD scheme.

    The two are both underscore-joined into one string with no other marker, so
    this can't be a single regex: "JD012603_02_ППК26113" is batch "JD012603_02"
    + doc "ППК26113" (02 is a bare sub-lot number), while "CJ1024_565-1096-26" is
    batch "CJ1024" + doc "565-1096-26" (565 only *looks* like one at a glance —
    it's glued to "-1096-26", which no sub-lot number ever is). So: split on "_",
    take the first segment as the base, then keep extending the batch across
    every following segment that is a bare short number (a genuine sub-lot/V/star
    marker) and stop at the first segment that isn't — that first non-matching
    segment starts the doc code, whatever segments follow it.
    """
    segs = rest.split("_")
    end = 1
    while end < len(segs) and _PURE_SUBLOT_SEGMENT.match(segs[end]):
        end += 1
    return "_".join(segs[:end]), "_".join(segs[end:])

# Doc "codes" that are form/template numbers, not per-document serials — the
# batch has to disambiguate two documents that legitimately share one of these.
# Found by running this module against the real corpus, not assumed up front:
# NGP's own "NGP-QCG-SOP-024 F3" collapsed two distinct certificates (P050202
# and P050192, same date) to one key before this pattern was added.
_GENERIC_DOC_CODE = re.compile(
    r"^(?:QCCoA\s*\d+(?:v\d+)?|NO-DOC-CODE\b.*|NGP-QCG-SOP-\d+\s*F\d+)$", re.IGNORECASE
)


def _norm_doc(doc):
    return re.sub(r"\s+", " ", doc.strip()).upper()


def _norm_lab(lab):
    return lab.strip().upper()


def parse_new_name(name):
    """Identity from a name already in the 20.09.2026 convention, or None."""
    m = _NEW.match(name.strip())
    if not m:
        return None
    return Identity(
        p_batch=m.group("p"),
        cu_batch=(m.group("cu") or "").strip() or None,
        lab=_norm_lab(m.group("lab")),
        doc_code=_norm_doc(m.group("doc")),
        date=m.group("date"),
    )


def parse_old_name(name):
    """Identity from a name in RAGflow's pre-rename scheme, or None.

    The leading token is a batch OR a bare strain code (both schemes let either
    stand alone) — it is kept as `cu_batch` unless it is itself a P-number, in
    which case there is no separate cultivation-batch spelling on this filename.
    """
    m = _OLD.match(name.strip())
    if not m:
        return None
    code, doc = _split_old_code_and_doc(m.group("rest").strip())
    if not doc:
        return None
    p_batch = code if re.fullmatch(_P, code) else None
    return Identity(
        p_batch=p_batch,
        cu_batch=None if p_batch else code,
        lab=_norm_lab(m.group("lab")),
        doc_code=_norm_doc(doc),
        date=m.group("date"),
    )


def parse_name(name):
    """Try both schemes; the new one first since it is the one going forward."""
    return parse_new_name(name) or parse_old_name(name)


def identity_key(ident):
    """The dedup/replace key: (lab, doc_code, date), with batch appended only
    where the doc code alone cannot tell two documents apart (finding: PP
    in-house reports reuse their form number across batches and dates)."""
    if ident is None:
        return None
    key = (ident.lab, ident.doc_code, ident.date)
    if _GENERIC_DOC_CODE.match(ident.doc_code):
        # p_batch first: the OLD scheme often records only the P-number and never
        # the cultivation batch, while the NEW scheme almost always records both —
        # preferring cu_batch here would key the same document differently across
        # the two schemes whenever the OLD name never carried a cultivation batch.
        batch = ident.p_batch or ident.cu_batch
        key = key + (batch_key(batch) if batch else None,)
    return key


if __name__ == "__main__":
    import doctest

    _CASES = [
        ("P060182 (GRC102501)_FHM_031-1-K-26_10.02.2026.pdf",
         Identity("P060182", "GRC102501", "FHM", "031-1-K-26", "10.02.2026")),
        ("(OPM1024)_FHM_197-17-K-26_07.08.2026.pdf",
         Identity(None, "OPM1024", "FHM", "197-17-K-26", "07.08.2026")),
        ("P050212_IJZ-MB_534-1065-26_31.08.2026.pdf",
         Identity("P050212", None, "IJZ-MB", "534-1065-26", "31.08.2026")),
        ("P050272 (PM072501)_PP_QCCoA 001v02_21.01.2026.pdf",
         Identity("P050272", "PM072501", "PP", "QCCOA 001V02", "21.01.2026")),
        ("(GG1024)_PP_NO-DOC-CODE (Report of Analysis)_23.04.2025.pdf",
         Identity(None, "GG1024", "PP", "NO-DOC-CODE (REPORT OF ANALYSIS)", "23.04.2025")),
    ]
    fails = 0
    for name, want in _CASES:
        got = parse_new_name(name)
        if got != want:
            fails += 1
            print("FAIL new:", name, "->", got, "!=", want)
    _OLD_CASES = [
        ("P060442_536-1067-26, 31.08.2026_IJZ-MB.pdf",
         Identity("P060442", None, "IJZ-MB", "536-1067-26", "31.08.2026")),
        ("CJ1024_565-1096-26, 01.09.2026_IJZ-MB.pdf",
         Identity(None, "CJ1024", "IJZ-MB", "565-1096-26", "01.09.2026")),
        ("eCoA_DATABASE/SCR112501_ППК26069, 11.05.2026_CNP.pdf",
         Identity(None, "SCR112501", "CNP", "ППК26069", "11.05.2026")),
        # a genuine sub-lot suffix on the batch, not the start of the doc code
        ("JD012603_02_ППК26113, 30.06.2026_CNP.pdf",
         Identity(None, "JD012603_02", "CNP", "ППК26113", "30.06.2026")),
        ("GRC102501_2_051-6-LoD-26, 02.03.2026_FHM.pdf",
         Identity(None, "GRC102501_2", "FHM", "051-6-LOD-26", "02.03.2026")),
        ("FB012601_1_2362-2026, 30.04.2026_IJZ.pdf",
         Identity(None, "FB012601_1", "IJZ", "2362-2026", "30.04.2026")),
    ]
    for name, want in _OLD_CASES:
        got = parse_old_name(name)
        if got != want:
            fails += 1
            print("FAIL old:", name, "->", got, "!=", want)
    # the identity that must survive a rename: same document, two schemes
    a = identity_key(parse_new_name("P060442 (SCR022601)_IJZ-MB_536-1067-26_31.08.2026.pdf"))
    b = identity_key(parse_old_name("P060442_536-1067-26, 31.08.2026_IJZ-MB.pdf"))
    if a != b:
        fails += 1
        print("FAIL rename-stability:", a, "!=", b)
    # two in-house reports sharing a form number, different batches -> must NOT collide
    c1 = identity_key(parse_new_name("P050272 (PM072501)_PP_QCCoA 001v02_21.01.2026.pdf"))
    c2 = identity_key(parse_new_name("P060012 (WC082501)_PP_QCCoA 001v02_20.02.2026.pdf"))
    if c1 == c2:
        fails += 1
        print("FAIL in-house collision guard:", c1, "==", c2)
    # NGP reuses its form code too (found in the real corpus, not assumed) -> must not collide
    n1 = identity_key(parse_old_name("P050202_NGP-QCG-SOP-024 F3, 28.11.2025_NGP.pdf"))
    n2 = identity_key(parse_old_name("P050192_NGP-QCG-SOP-024 F3, 28.11.2025_NGP.pdf"))
    if n1 == n2:
        fails += 1
        print("FAIL NGP collision guard:", n1, "==", n2)
    # a generic-doc-code document whose OLD name never recorded a cultivation batch
    # (only the P-number) must still key the same as its NEW-scheme counterpart,
    # which records both — found for real on P050202/P050192 (NGP)
    d1 = identity_key(parse_old_name("P050202_NGP-QCG-SOP-024 F3, 28.11.2025_NGP.pdf"))
    d2 = identity_key(parse_new_name("P050202 (GP062501)_NGP_NGP-QCG-SOP-024 F3_28.11.2025.pdf"))
    if d1 != d2:
        fails += 1
        print("FAIL generic-code rename-stability:", d1, "!=", d2)
    print(f"{'FAILED' if fails else 'OK'}: {fails} failing case(s) of "
          f"{len(_CASES) + len(_OLD_CASES) + 3}")
    raise SystemExit(1 if fails else 0)
