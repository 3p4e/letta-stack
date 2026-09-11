#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One notation for a not-detected result, everywhere it is printed.

    python3 deliverables/qc_gap_analysis/result_notation.py     # self-test + census

Owner's ruling, 10.09.2026:

    "we should have one use of any derivation of 'n.r.' and we will use ND
     everywhere: n.d., nd, н.д., нд, n.r., n.r. is stated as a parameter result
     inside eCoA, iCoA or CoQ documents."

The desk had **eight** spellings of it on the certificates alone — `ND`, `N.D.`,
`Н.д.`, `Н.д. (not detected)`, `н.д.`, `ND ᴰ`, and two carrying a residue gloss —
and six more in the 09.09 pass, including `n.r.` and `Н.Д.`. Every one of them is
the same assertion, and a results column that spells one assertion eight ways
invites a reader to think it means eight things.

`nd()` is the single definition. It rewrites the notation and **nothing else**:
the unit stays, a footnote marker stays, the residue gloss stays, and a value
that is not a not-detected result is returned untouched. It is applied where the
desk stores a printed result, so the certificates, the desk and the PDFs all
inherit one spelling from one place.

A note for the record, because it is a real distinction and the ruling settles it
rather than dissolves it: *not reported* and *not detected* are not the same
statement — one says the analyte was measured and absent, the other that it was
not measured. The owner's ruling is that in these documents `n.r.` is stated as a
parameter result and means what `n.d.` means, so both print `ND`.
"""
import os
import re
import sys

# Every derivation, in either alphabet, with or without stops and spaces. The
# boundaries exclude letters and digits on both sides so "and", "Found",
# "Standard" and "2nd" are not results.
_ND = re.compile(
    r"(?<![0-9A-Za-zЀ-ӿ])"
    # the dot after the second letter must be adjacent: a trailing \s* here would
    # swallow the space before a footnote marker and turn "ND ᴰ" into "NDᴰ"
    r"(?:[Nn]\s*\.?\s*[DdRr]\.?|[Нн]\s*\.?\s*[Дд]\.?)"
    r"(?![0-9A-Za-zЀ-ӿ])")
# "(not detected)" and "(не е детектирано)" gloss a notation that now says it
_GLOSS = re.compile(r"\s*\((?:not\s+detected|не\s+е\s+детектирано)\)", re.I)


def nd(value):
    """A result with every not-detected spelling written `ND`.

    The notation changes; nothing else does.

    >>> nd("N.D."), nd("н.д."), nd("Н.Д."), nd("nd"), nd("n.r.")
    ('ND', 'ND', 'ND', 'ND', 'ND')
    >>> nd("Н.д. (not detected)")
    'ND'
    >>> nd("н.д. mg/kg — all 25 residues")
    'ND mg/kg — all 25 residues'
    >>> nd("N.D. — all 13 residues")
    'ND — all 13 residues'
    >>> nd("ND ᴰ")
    'ND ᴰ'

    Anything that is not a not-detected result comes back untouched, including
    words that merely contain the letters.

    >>> nd("< LOQ (<0.20)"), nd("24.53"), nd("Одговара (Absent)")
    ('< LOQ (<0.20)', '24.53', 'Одговара (Absent)')
    >>> nd("Conforms and complies"), nd("Standard"), nd("2nd sample")
    ('Conforms and complies', 'Standard', '2nd sample')
    >>> nd(""), nd(None), nd("—")
    ('', '', '—')
    """
    s = (value or "").strip()
    if not s or not _ND.search(s):
        return s
    s = _ND.sub("ND", s)
    s = _GLOSS.sub("", s)
    return re.sub(r"\s{2,}", " ", s).strip()


def census(path=None):
    """How many printed results the ruling touches, and how they were spelled."""
    import collections
    import json
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "coq_artifact_data.json")
    data = json.load(open(path, encoding="utf-8"))
    was = collections.Counter()
    for c in data["coqs"]:
        for r in c["rows"]:
            v = (r.get("res") or "").strip()
            if v and nd(v) != v:
                was[v] += 1
    return was


if __name__ == "__main__":
    import doctest
    fail, ran = doctest.testmod()
    print("%d doctests, %d failed" % (ran, fail))
    if fail:
        sys.exit(1)
    was = census()
    print("printed results the ruling rewrites: %d" % sum(was.values()))
    for k, v in was.most_common():
        print("   %4d  %-32r -> %r" % (v, k, nd(k)))
    sys.exit(0)
