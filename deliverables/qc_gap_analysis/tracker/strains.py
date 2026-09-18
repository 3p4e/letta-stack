#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Strain names: what one strain is called, and where the company's own documents disagree.

A strain name is printed on the certificate of quality, so it is not decoration. The desk
holds several spellings of the same strain, and it was tempting to call them reader errors.
They are not: the ImB certificate register scanned on 04.09.2026 prints "Sleepy Joy",
"Permanent Market", "Wedding Crasher" and "Clemosa a Bud" itself, while the owner's delivery
sheet prints "Sleepy Joe", "Permanent Marker", "Wedding Crusher" and "Clemosa". Two of the
company's own documents disagree, and picking a winner is a person's decision, not a
function's.

So this module does exactly two things, and refuses to do a third:

  1. CANONICAL applies the rulings a person has actually made. Today there is one, and it is
     the reason this file exists: **Cap Junky** (Head of QC, 07.09.2026). The register prints
     the same strain three ways — "Cap Junky" on certificate 041, "Cap Junkie" on 028 and
     "Cup Junkie" on the P050162 entry — so any grouping by strain split one strain into
     three until this was settled.

  2. It repairs a missing space where the letters are otherwise identical: "GorillaGlue" is
     "Gorilla Glue" with a space lost in transcription, and nothing is decided by saying so.

  3. It does NOT choose between two spellings that differ in their letters. Those are listed
     in CONFLICTS with both sources named, and the tracker prints them for a ruling.
"""
import re

# Ruled by a person. date -> (canonical, the spellings it replaces, who ruled it, when)
RULINGS = [
    ("Cap Junky",
     ["Cap Junkie", "Cup Junkie", "Cup Junky", "CapJunky", "Cap junky", "CJ"],
     "Head of QC (azu.sozon@gmail.com)", "07.09.2026",
     "The ImB certificate register of 04.09.2026 prints the strain three ways — Cap Junky "
     "(cert 041), Cap Junkie (cert 028) and Cup Junkie (the P050162 entry) — and the "
     "delivery sheet prints Cap Junkie. Cap Junky is correct."),

    ("Sleepy Joe",
     ["Sleepy Joy", "SleepyJoe", "SleepyJoy"],
     "Head of QC (azu.sozon@gmail.com)", "18.09.2026",
     "Ruled from the department's own Purely_Plant_Finished_Specifications_2026-09-16.pdf, "
     "which carries ONE spelling per cultivar across its 23 strains, and confirmed in words "
     "on 18.09.2026: \"yes align the 38 names\". That document outranks the analysis "
     "workbook's Strain column and the ImB certificate register, both of which disagree "
     "with it and with each other. The certificate register printed Sleepy Joy; the "
     "specification distribution prints Sleepy Joe, and it is the newer document and the "
     "one the grades are read from."),

    ("Permanent Marker",
     ["Permanent Market", "PermanentMarker", "PermanentMarket"],
     "Head of QC (azu.sozon@gmail.com)", "18.09.2026",
     "Ruled from the department's own Purely_Plant_Finished_Specifications_2026-09-16.pdf, "
     "which carries ONE spelling per cultivar across its 23 strains, and confirmed in words "
     "on 18.09.2026: \"yes align the 38 names\". That document outranks the analysis "
     "workbook's Strain column and the ImB certificate register, both of which disagree "
     "with it and with each other. This one runs AGAINST the analysis workbook, which prints "
     "Permanent Market: the distribution prints Permanent Marker, which is also the "
     "cultivar\'s real name, so the workbook carries the transcription error."),

    ("Wedding Crusher",
     ["Wedding Crasher", "WeddingCrusher", "WeddingCrasher"],
     "Head of QC (azu.sozon@gmail.com)", "18.09.2026",
     "Ruled from the department's own Purely_Plant_Finished_Specifications_2026-09-16.pdf, "
     "which carries ONE spelling per cultivar across its 23 strains, and confirmed in words "
     "on 18.09.2026: \"yes align the 38 names\". That document outranks the analysis "
     "workbook's Strain column and the ImB certificate register, both of which disagree "
     "with it and with each other. The certificate register printed Wedding Crasher. Distinct "
     "from Wedding Cake (WED), which is a different cultivar on a different lot."),

    ("Jelly Donuts",
     ["Jelly Donutz", "JellyDonutz", "JellyDonuts", "Jelly Donut"],
     "Head of QC (azu.sozon@gmail.com)", "18.09.2026",
     "Ruled from the department's own Purely_Plant_Finished_Specifications_2026-09-16.pdf, "
     "which carries ONE spelling per cultivar across its 23 strains, and confirmed in words "
     "on 18.09.2026: \"yes align the 38 names\". That document outranks the analysis "
     "workbook's Strain column and the ImB certificate register, both of which disagree "
     "with it and with each other. The desk\'s own record carried Jelly Donutz."),

    ("Grapes And Cream",
     ["Grapes and Cream", "Graps & Creme", "Graps and Creme", "Grapes & Cream",
      "GrapesAndCream", "Graps Creme"],
     "Head of QC (azu.sozon@gmail.com)", "18.09.2026",
     "Ruled from the department's own Purely_Plant_Finished_Specifications_2026-09-16.pdf, "
     "which carries ONE spelling per cultivar across its 23 strains, and confirmed in words "
     "on 18.09.2026: \"yes align the 38 names\". That document outranks the analysis "
     "workbook's Strain column and the ImB certificate register, both of which disagree "
     "with it and with each other. The capital And is the distribution\'s own spelling, kept "
     "verbatim even though the same document writes Apple and Banana with a lowercase and. "
     "That inconsistency is the department\'s to settle; the desk does not silently "
     "normalise a name it was given."),

    ("Clemosa A Bud",
     ["Clemosa a bud", "Clemosa a Bud", "Clemosa A bud", "Clemosa", "ClemosaABud"],
     "Head of QC (azu.sozon@gmail.com)", "18.09.2026",
     "Ruled from the department's own Purely_Plant_Finished_Specifications_2026-09-16.pdf, "
     "which carries ONE spelling per cultivar across its 23 strains, and confirmed in words "
     "on 18.09.2026: \"yes align the 38 names\". That document outranks the analysis "
     "workbook's Strain column and the ImB certificate register, both of which disagree "
     "with it and with each other. The delivery sheet printed the bare Clemosa and the "
     "certificate register Clemosa a Bud; the distribution gives the full name."),

    ("Apple and Banana",
     ["Appels & Bananas", "Appel and Banana", "Appels and Bananas", "AppleAndBanana"],
     "Head of QC (azu.sozon@gmail.com)", "18.09.2026",
     "Ruled from the department's own Purely_Plant_Finished_Specifications_2026-09-16.pdf, "
     "which carries ONE spelling per cultivar across its 23 strains, and confirmed in words "
     "on 18.09.2026: \"yes align the 38 names\". That document outranks the analysis "
     "workbook's Strain column and the ImB certificate register, both of which disagree "
     "with it and with each other. The delivery sheet printed Appels & Bananas."),
]

# Spellings that differ from the canonical form ONLY by spacing or case. Repairing these
# decides nothing, so it is done here rather than left for a person.
_SPACING_ONLY = ["Gorilla Glue", "Fat Bastard", "Grape Pie", "Blue Gelato", "Motor Breath",
                 "Blue Sunset Sherbet", "High Pro Amnesia", "Orange Punch Mimosa", "Cash Cow", "Jelly Donutz",
                 "Grapes and Cream", "Amnesia Core Cut", "Chem Flyer", "Kush Crasher",
                 "Pure Michigen", "Wedding Cake", "Jokerz 31", "CashCow", "Scrambler",
                 "Clemosa", "GG4"]

# Where two of the company's own documents disagree in their LETTERS. Not decided here.
# strain as the desk holds it -> (the delivery sheet, the ImB certificate register)
CONFLICTS = {}


def _squash(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


_MAP = {}
for _canon, _alts, _who, _when, _why in RULINGS:
    for _a in [_canon] + _alts:
        _MAP[_squash(_a)] = _canon
for _c in _SPACING_ONLY:
    _MAP.setdefault(_squash(_c), _c)


def canonical(name):
    """The strain as it should be printed, where that has been settled; else as given."""
    if not name:
        return name
    return _MAP.get(_squash(name), str(name).strip())


def ruled(name):
    """True when canonical(name) is a ruling rather than the name it was handed."""
    n = str(name or "").strip()
    return bool(n) and canonical(n) != n


def ruling_for(name):
    """The ruling that settled this name: (canonical, who, when), or None.

    The audit sheet used to name Cap Junky on every ruled row, because for a while it was
    the only ruling there was. There are now eight, so the row has to say which one it is.
    """
    c = canonical(name)
    for _canon, _alts, _who, _when, _why in RULINGS:
        if _canon == c:
            return (_canon, _who, _when)
    return None


def conflict(name):
    """The unresolved disagreement for this strain, or None."""
    return CONFLICTS.get(str(name or "").strip()) or CONFLICTS.get(canonical(name))


if __name__ == "__main__":
    for s in ("Cap Junkie", "Cup Junkie", "Cap Junky", "GorillaGlue", "Sleepy Joy", "Grape Pie"):
        print("%-16s -> %-16s ruled=%-5s conflict=%s" % (s, canonical(s), ruled(s), bool(conflict(s))))
