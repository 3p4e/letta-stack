#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One spelling per document code, everywhere a certificate code is printed.

    python3 deliverables/qc_gap_analysis/document_codes.py     # self-test + census

`result_vocabulary.py` settled the results. This settles the codes, and for the same
reason: a controlled document must name the certificate it rests on exactly as that
certificate names itself, so that a reader holding the paper can find it.

The other desk's audit of 16.09.2026 flagged six certificate codes as "carrying analysis
tags" — `031-2-LoD/26`, `051-1-GS/26` and their siblings — and asked whether the tag is
part of the code. **It is.** Farmahem numbers a report `<campaign>-<item>-<analysis>/<year>`
and the analysis letter is Macedonian: `К` for канабиноиди, `М` for микотоксини, and
**`ГС` for губитоци при сушење** — loss on drying. Read on the pages on 16.09.2026:

    020326_051-1-LoD-26_FHM_J31102501-P060152.pdf   prints  Извештај број: 051-1-ГС/26
    110226_031-2-LoD-26_FHM_PUM102501-P060112.pdf   prints  Извештај број: 031-2-ГС/26
    both titled  «Извештај од анализа на губитоци при сушење во цвет од канабис»

So `GS` is a Latin transliteration and `LoD` an English abbreviation; neither is what the
laboratory printed, and the owner's standing rule — Cyrillic К and М in laboratory codes
are genuine, do not transliterate — applies to `ГС` exactly as it does to them. The scans'
own file names carry `LoD` and one earlier extraction carries `GS`, which is how both
spellings reached the desk; the page outranks both.

The second family is a note that leaked into a code field. The register's row 32 holds

    2156/2025 (microbiology sub-report lab-ref not distinctly captured in OCR text)

as the document code for OPM1024_01's microbiology, so ten certificate rows would print a
seventy-character reader's note where the document code belongs. The report number is
`2156/2025` — row 31 of the same block carries it bare for the mycotoxins and metals half
of the same report — and the note is a note.

## What this does not do

It rewrites **spelling and nothing else**. A number keeps its digits; a parenthetical that
identifies the SAMPLE rather than the reader's confidence survives untouched, because
`231/0394/26 (Рачно тримиран цвет)` and `230/0393/26 (Тримиран цвет)` are how the desk
tells one sublot's certificate from the other's (OI-39). Nothing here merges two codes,
splits one, or changes which document a determination cites — the composite codes of the
form `PP CoA #027 / ППК25370` are left exactly as the register writes them and put to the
owner as OI-40, because deciding which of two rows is the certificate is not a spelling.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# The Farmahem loss-on-drying analysis letter, read off the pages on 16.09.2026.
_FHM_LOD = re.compile(r"^(\d{2,3}-\d{1,2})-(?:GS|LoD|LOD|lod|gs)([-/]\d\d)$")

# A reader's note that leaked into a code field: the parenthetical says something about
# the READING, not about the sample. Kept as a pattern rather than a list of codes so a
# second one cannot slip past.
_READER_NOTE = re.compile(
    r"\s*\((?:[^)]*\b(?:not distinctly captured|OCR|illegible|unreadable|"
    r"not legible|could not be read)\b[^)]*)\)\s*$", re.I)


def canon(code):
    """The document code as the certificate itself prints it.

    >>> canon("051-1-GS/26")
    '051-1-ГС/26'
    >>> canon("031-2-LoD/26")
    '031-2-ГС/26'
    >>> canon("051-5-LoD-26")
    '051-5-ГС-26'
    >>> canon("2156/2025 (microbiology sub-report lab-ref not distinctly captured in OCR text)")
    '2156/2025'

    A code the laboratory prints this way is returned unchanged, and so is a
    parenthetical that names the sample rather than the reading:

    >>> canon("051-1-К/26"), canon("197-11-М/26"), canon("ППК25174")
    ('051-1-К/26', '197-11-М/26', 'ППК25174')
    >>> canon("231/0394/26 (Racno trimiran cvet)")
    '231/0394/26 (Racno trimiran cvet)'
    >>> canon("PP CoA #027 / ППК25370")
    'PP CoA #027 / ППК25370'
    >>> canon(""), canon(None)
    ('', '')
    """
    s = str(code or "").strip()
    if not s:
        return ""
    s = _READER_NOTE.sub("", s).strip()
    m = _FHM_LOD.match(s)
    if m:
        return "%s-ГС%s" % (m.group(1), m.group(2))
    return s


def walk(obj, keys=("code", "doc", "Source document", "cert_code")):
    """Canonicalise every document-code field in a nested export structure, in place.
    Returns the number of fields the spelling changed.

    >>> d = {"coqs": [{"rows": [{"doc": "051-1-GS/26"}, {"doc": "051-1-К/26"}]}]}
    >>> walk(d), d["coqs"][0]["rows"][0]["doc"]
    (1, '051-1-ГС/26')
    """
    n = 0
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in keys and isinstance(v, str):
                c = canon(v)
                if c != v:
                    obj[k] = c
                    n += 1
            else:
                n += walk(v, keys)
    elif isinstance(obj, list):
        for v in obj:
            n += walk(v, keys)
    return n


def main():
    import doctest
    r = doctest.testmod()
    print("%d doctests, %d failed" % (r.attempted, r.failed))
    if r.failed:
        return 1
    try:
        import json
        d = json.load(open(os.path.join(HERE, "coq_artifact_data.json"), encoding="utf-8"))
    except OSError:
        return 0
    n = walk(d)
    print("document codes: %d field(s) would change spelling in the current export" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
