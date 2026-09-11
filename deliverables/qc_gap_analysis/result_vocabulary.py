#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One spelling per assertion, everywhere a result is printed.

    python3 deliverables/qc_gap_analysis/result_vocabulary.py   # self-test + census

`result_notation.nd()` settled one family — the not-detected result — under the
owner's ruling of 10.09.2026. The audit of v22 on 11.09.2026 found the same
disease in five more families, in the workbook this time rather than on the
certificates, because the ND rule had been applied to the export path and never
to the desk that feeds it:

| assertion | spellings found in v22 |
| --- | --- |
| not detected | `n.r.` ×115, `н.д.` ×36, `Н.д.` ×17, `Н.Д.` ×6, `N.D.` ×1, beside 84 already `ND` |
| below quantitation | `<LOQ`, `< LOQ`, `<LOQ**`, `<LOQ (<0.20)`, `BLQ`, `BLQ ᴰ`, `<LOQ **`, `<LOQ ᴿ` |
| conforms | `Conforms` ×70, `Одговара` ×11, **`Confirms` ×7** |
| absent | `absent` ×60, `Одговара` ×84, and 9 Cyrillic spellings, every one a singleton |
| a counted colony | `×` ×49, ` x ` ×51, `·` ×4, `и` ×19, `and` ×6, `10^2` ×6 |
| a mass fraction | `0.02 ᴰ` ×11 beside `0.02 % ᴰ` ×5 — the same value, one carrying the unit |

None of it is a difference in meaning. A results column that spells one assertion
nine ways invites a reader to think it means nine things, and a reader of a batch
record is a person deciding whether to release a medicine.

## What this does not do

It rewrites **notation and nothing else**. A number keeps its digits, a footnote
marker keeps its position, a residue gloss survives, a parenthetical LOQ survives,
and the re-test and derived markers (ᴿ, ᴰ) are never touched. Where a lab printed
a verdict — `Одговара`, `Не одговара` — the verdict is preserved as a verdict, in
one spelling, because `Не одговара` is the laboratory saying the lot **fails** and
that is the last thing a normaliser may quietly drop.

## Why the determination number is an argument

`Одговара` means *conforms* in the identity columns and *absent* in the
Salmonella and E. coli columns — the same Macedonian word for two different
assertions, told apart only by which column it is printed in. So the caller says
which determination it is holding, and a spelling is only folded into the family
that determination belongs to. Guessing from the string alone would silently
print "Conforms" where the certificate says an organism was absent.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from result_notation import nd                                    # noqa: E402

# Which family a determination belongs to. The numbering is tracker_data.GROUPS.
QUALITATIVE = ("1", "2", "3", "7", "12")       # identity, foreign matter, pesticides
COUNT = ("9.1", "9.2", "9.3")                  # TAMC, TYMC, GNB — CFU/g
ABSENCE = ("9.4", "9.5")                       # Salmonella, E. coli
FRACTION = ("4", "5", "6", "8")                # % w/w
CONCENTRATION = ("10.1", "10.2", "10.3", "11.1", "11.2", "11.3", "11.4")

# The markers a result may carry, which survive every rewrite: ᴿ re-test, ᴰ derived,
# and the footnote asterisks the desk prints against a qualified reading.
_MARK = re.compile(r"(?:\s*(?:ᴿ|ᴰ|\*{1,3}))+$")

_BLQ = re.compile(r"(?<![0-9A-Za-z])(?:BLQ|<\s*LOQ)(?![0-9A-Za-z])", re.I)
_CONFORM = re.compile(r"^(?:Conf[io]rms|Одговара)$", re.I)
_NONCONFORM = re.compile(r"^(?:Не\s*одговара|Does\s+not\s+conform)$", re.I)
# отсутна / отсуство / отсуства, with or without the sample size the column states.
# "Odgovara" is the same word transliterated into Latin, which the certificates
# print beside the Cyrillic form for the same assertion.
_ABSENT = re.compile(r"^(?:absent|отсу(?:тна|ство|ства)(?:\s*/\s*\S+(?:\s*[гg])?)?"
                     r"|Одговара|Odgovara)$", re.I)
# the same assertion written as a word and its gloss: "Одговара (absent)",
# "Odgovara (Absent)", "Одговара (Complies/Absent)"
_ABSENT_GLOSSED = re.compile(
    r"^(?:Одговара|Odgovara|absent)\s*\((?:[^()]*\b(?:absent|отсу\w*)\b[^()]*)\)$", re.I)
# a unit the column header already states
_UNIT = re.compile(r"\s*(?:µg/kg|mg/kg|ug/kg|CFU/g)\s*$", re.I)
_SUP = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
        "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"}


def _split(s):
    """A result and the markers trailing it, which no rewrite may disturb."""
    m = _MARK.search(s)
    return (s[:m.start()].rstrip(), s[m.start():]) if m else (s, "")


def _power(s):
    r"""`10^4`, `10 4` and `104` written the way the column prints them: `10⁴`."""
    s = re.sub(r"10\^(\d+)", lambda m: "10" + "".join(_SUP[d] for d in m.group(1)), s)
    return s


def _counts(s):
    """One multiplication sign, one connective, superscript exponents."""
    s = _power(s)
    # every form must sit between digits: the middle dot is also the separator the
    # desk prints inside a reference ("... [IJZ-MB] · on file, not credited"), and a
    # rewrite that does not check its neighbours would corrupt one
    s = re.sub(r"(?<=\d)\s*(?:×|·|x)\s*(?=\d)", " × ", s)
    s = re.sub(r"\s+и\s+", " and ", s)
    s = re.sub(r"\s*([<>])\s*", r" \1 ", s).strip()
    return re.sub(r"\s{2,}", " ", s)


def canon(value, no=None):
    """A result in the desk's controlled spelling for its determination.

    The not-detected family, everywhere, unchanged from the owner's ruling:

    >>> canon("n.r.", "10.1"), canon("н.д.", "11.3"), canon("Н.Д.", "11.1")
    ('ND', 'ND', 'ND')

    Below quantitation gets one spelling, and keeps what qualifies it:

    >>> canon("BLQ ᴰ", "6"), canon("<LOQ", "5"), canon("<LOQ**", "5")
    ('< LOQ ᴰ', '< LOQ', '< LOQ**')
    >>> canon("<LOQ (<0.20) ᴿ", "5")
    '< LOQ (<0.20) ᴿ'

    `Confirms` is a typo for the verdict and `Одговара` is the same verdict in the
    other alphabet — but only in the columns where that word is a verdict:

    >>> canon("Confirms", "1"), canon("Одговара", "2"), canon("Conforms", "7")
    ('Conforms', 'Conforms', 'Conforms')

    ...and in the absence columns the same word says an organism was absent:

    >>> canon("Одговара", "9.4"), canon("отсутна/25", "9.4"), canon("отсуство/g", "9.5")
    ('Absent', 'Absent', 'Absent')
    >>> canon("absent ᴿ", "9.5")
    'Absent ᴿ'

    ...however the certificate glossed it, and in whichever alphabet:

    >>> canon("Odgovara (Absent)", "9.4"), canon("Одговара (absent)", "9.5")
    ('Absent', 'Absent')
    >>> canon("Одговара (Complies/Absent)", "9.4")
    'Absent'

    A concentration drops the unit its column states and spaces its comparator:

    >>> canon("<2", "10.2"), canon("< 2 µg/kg", "10.2"), canon("0.052 mg/kg", "11.1")
    ('< 2', '< 2', '0.052')

    A laboratory's own non-conformity is preserved as a verdict, never folded away:

    >>> canon("0.08% (Не одговара)", "7")
    '0.08 % (Does not conform)'
    >>> canon("0.42% (Одговара)", "7")
    '0.42 % (Conforms)'

    ...and where the form printed no figure at all, that is said rather than left
    as the bare mark the CNP form uses for it:

    >>> canon("/ (Одговара)", "7")
    'Conforms (no value printed)'

    The multiplication sign is only rewritten between digits, so the middle dot
    the desk prints inside a reference is never touched:

    >>> canon("536-1067-26, (31.08.2026) [IJZ-MB] · on file, not credited", "9.1")
    '536-1067-26, (31.08.2026) [IJZ-MB] · on file, not credited'

    Counts get one multiplication sign, one connective and real exponents:

    >>> canon("1.6 x 10⁴", "9.1"), canon("2.2×10³", "9.2"), canon("7·10² ᴿ", "9.1")
    ('1.6 × 10⁴', '2.2 × 10³', '7 × 10² ᴿ')
    >>> canon("<10² и >10", "9.3"), canon("<10^2 и >10", "9.3")
    ('< 10² and > 10', '< 10² and > 10')
    >>> canon("<10³ and >10² ᴿ", "9.3")
    '< 10³ and > 10² ᴿ'

    A mass fraction drops the unit its column already states:

    >>> canon("0.02 % ᴰ", "6"), canon("2.35 % ᴰ", "6"), canon("0.02 ᴰ", "6")
    ('0.02 ᴰ', '2.35 ᴰ', '0.02 ᴰ')

    Nothing else is touched — a value, a desk status, a controlled blank:

    >>> canon("24.53", "4"), canon("— MISSING —", "9.1"), canon("", "1")
    ('24.53', '— MISSING —', '')
    >>> canon("not on this certificate", "2"), canon("held for review", "6")
    ('not on this certificate', 'held for review')
    >>> canon("≤ LOQ (all 29 compounds)", "12")
    '≤ LOQ (all 29 compounds)'
    """
    s = (value or "").strip()
    if not s or s.startswith("—"):
        return s
    s = nd(s)
    body, mark = _split(s)

    # a verdict printed in parentheses beside a value — "0.08% (Не одговара)"
    def _verdict(m):
        w = m.group(1).strip()
        if _NONCONFORM.match(w):
            return "(Does not conform)"
        if _CONFORM.match(w):
            return "(Conforms)"
        return m.group(0)
    body = re.sub(r"\(([^()]+)\)", _verdict, body)
    # "/" is how the CNP form prints "no value here". Against a gravimetric
    # specification that wants a percentage, the absence of the figure is itself
    # the finding, so it is said in words rather than left as a mark a reader has
    # to know the form to decode.
    body = re.sub(r"^/\s*\((Conforms|Does not conform)\)$", r"\1 (no value printed)", body)

    if no in ABSENCE and (_ABSENT.match(body) or _ABSENT_GLOSSED.match(body)):
        body = "Absent"
    elif no in CONCENTRATION:
        body = _BLQ.sub("< LOQ", _UNIT.sub("", body))
        body = re.sub(r"^([<>≤≥])\s*(?=[\d.])", r"\1 ", body)
    elif no in QUALITATIVE:
        if _CONFORM.match(body):
            body = "Conforms"
        elif _NONCONFORM.match(body):
            body = "Does not conform"
        else:
            body = _BLQ.sub("< LOQ", body)
            body = re.sub(r"(\d)\s*%", r"\1 %", body)
    elif no in COUNT:
        body = _counts(_BLQ.sub("< LOQ", body))
    elif no in FRACTION:
        body = _BLQ.sub("< LOQ", body)
        body = re.sub(r"^(\d+(?:\.\d+)?)\s*%$", r"\1", body)   # the column states the unit
    else:
        body = _BLQ.sub("< LOQ", body)
    return (body + mark).strip()


def census(path=None):
    """Every result cell in a workbook the vocabulary would rewrite."""
    import collections
    import openpyxl
    from openpyxl.utils import column_index_from_string as ci
    path = path or os.path.join(HERE, "tracker", "CoQ_Analysis_Master_v22.xlsx")
    cols = {"D": "1", "G": "2", "J": "3", "M": "4", "P": "5", "S": "6", "V": "7", "Y": "8",
            "AB": "9.1", "AC": "9.2", "AD": "9.3", "AE": "9.4", "AF": "9.5",
            "AH": "10.1", "AI": "10.2", "AJ": "10.3",
            "AL": "11.1", "AM": "11.2", "AN": "11.3", "AO": "11.4", "AQ": "12"}
    ws = openpyxl.load_workbook(path).worksheets[0]
    for w in openpyxl.load_workbook(path).worksheets:
        if w.title.startswith("CoQ Parameter Tracker v"):
            ws = w
            break
    out = collections.Counter()
    for r in range(5, ws.max_row + 1):
        for col, no in cols.items():
            v = ws.cell(r, ci(col)).value
            if isinstance(v, str) and canon(v, no) != v.strip():
                out[(v.strip(), canon(v, no))] += 1
    return out


if __name__ == "__main__":
    import doctest
    fail, ran = doctest.testmod()
    print("%d doctests, %d failed" % (ran, fail))
    if fail:
        sys.exit(1)
    was = census()
    print("result cells the vocabulary rewrites: %d in %d spellings"
          % (sum(was.values()), len(was)))
    for (a, b), n in was.most_common(40):
        print("   %4d  %-26r -> %r" % (n, a, b))
    sys.exit(0)
