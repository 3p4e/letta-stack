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
]

# Spellings that differ from the canonical form ONLY by spacing or case. Repairing these
# decides nothing, so it is done here rather than left for a person.
_SPACING_ONLY = ["Gorilla Glue", "Fat Bastard", "Grape Pie", "Blue Gelato", "Motor Breath",
                 "Blue Sunset Sherbet", "High Pro Amnesia", "Orange Punch Mimosa",
                 "Grapes and Cream", "Amnesia Core Cut", "Chem Flyer", "Kush Crasher",
                 "Pure Michigen", "Wedding Cake", "Jokerz 31", "CashCow", "Scrambler",
                 "Clemosa", "GG4"]

# Where two of the company's own documents disagree in their LETTERS. Not decided here.
# strain as the desk holds it -> (the delivery sheet, the ImB certificate register)
CONFLICTS = {
    "Sleepy Joe":       ("Sleepy Joe (delivery sheet)", "Sleepy Joy (certificate register, P060082)"),
    "Sleepy Joy":       ("Sleepy Joe (delivery sheet)", "Sleepy Joy (certificate register, P060082)"),
    "Permanent Marker": ("Permanent Marker (delivery sheet)", "Permanent Market (certificate register, P060062 and P050272)"),
    "Permanent Market": ("Permanent Marker (delivery sheet)", "Permanent Market (certificate register, P060062 and P050272)"),
    "Wedding Crusher":  ("Wedding Crusher (delivery sheet)", "Wedding Crasher (certificate register, P060012 and P050262)"),
    "Wedding Crasher":  ("Wedding Crusher (delivery sheet)", "Wedding Crasher (certificate register, P060012 and P050262)"),
    "Appels & Bananas": ("Appels & Bananas (delivery sheet)", "Apple and Banana (certificate register, P060052)"),
    "Appel and Banana": ("Appels & Bananas (delivery sheet)", "Apple and Banana (certificate register, P060052)"),
    "Apple and Banana": ("Appels & Bananas (delivery sheet)", "Apple and Banana (certificate register, P060052)"),
    "Jelly Donuts":     ("Jelly Donuts (delivery sheet)", "Jelly Donutz (the desk's own record)"),
    "Jelly Donutz":     ("Jelly Donuts (delivery sheet)", "Jelly Donutz (the desk's own record)"),
    "Clemosa a Bud":    ("Clemosa (delivery sheet)", "Clemosa a Bud (certificate register, P050282)"),
    "Clemosa a bud":    ("Clemosa (delivery sheet)", "Clemosa a Bud (certificate register, P050282)"),
}


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


def conflict(name):
    """The unresolved disagreement for this strain, or None."""
    return CONFLICTS.get(str(name or "").strip()) or CONFLICTS.get(canonical(name))


if __name__ == "__main__":
    for s in ("Cap Junkie", "Cup Junkie", "Cap Junky", "GorillaGlue", "Sleepy Joy", "Grape Pie"):
        print("%-16s -> %-16s ruled=%-5s conflict=%s" % (s, canonical(s), ruled(s), bool(conflict(s))))
