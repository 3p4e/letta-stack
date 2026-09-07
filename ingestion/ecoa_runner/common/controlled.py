"""Controlled vocabularies: laboratories, strains, pesticide panels.

Certificate text is not authoritative for names. A laboratory prints its own
name five different ways across five certificates and a strain arrives with a
typo ("Cap Junkie" for Cap Junky). The CoQ must name each laboratory once and
each strain by its established nomenclature, so certificate text is resolved
against these lists rather than reproduced.

Nothing here changes a RESULT. Only identity is canonicalised.
"""
import re
import unicodedata


def _fold(s):
    """Case-, space- and punctuation-insensitive key for matching printed text."""
    if s is None:
        return ''
    s = unicodedata.normalize('NFKD', str(s)).lower()
    return re.sub(r'[^0-9a-zа-шјњќѓџ]+', '', s)


# --- Laboratories -------------------------------------------------------------
# One row per INSTITUTION. The Head of QC's ruling: IJZ is referenced on one
# Section 03 row carrying every certificate code and issue date it supplied,
# regardless of which department (microbiology, chemistry, ...) issued them.
# Departments therefore deliberately do NOT appear in the canonical name.
LABORATORIES = [
    {
        'id': 'IJZ',
        'name': 'ЈЗУ Институт за јавно здравје на Република Северна Македонија',
        'name_en': 'Institute of Public Health of the Republic of North Macedonia',
        # Every printed variant folds to a string containing one of these.
        'match': ['институтзајавнoздравје', 'институтзајавноздравје',
                  'instituteofpublichealth'],
    },
    {
        'id': 'DFL',
        'name': 'Државна фитосанитарна лабораторија',
        'name_en': 'State Phytosanitary Laboratory',
        'match': ['државнафитосанитарналабораторија', 'statephytosanitarylaboratory'],
    },
    {
        'id': 'FARMAHEM',
        'name': 'Фармахем — Лабораторија за животна средина',
        'name_en': 'Farmahem Environmental Laboratory',
        'match': ['фармахем', 'farmahem'],
    },
    {
        'id': 'UKIM_CNP',
        'name': 'УКИМ Фармацевтски факултет — Центар за природни производи',
        'name_en': 'Ss. Cyril and Methodius University, Faculty of Pharmacy — '
                   'Center for Natural Products',
        'match': ['центарзаприроднипроизводи', 'centerfornaturalproducts'],
    },
    {
        'id': 'NGP',
        'name': 'New Garden Pharma',
        'name_en': 'New Garden Pharma',
        'match': ['newgardenpharma'],
    },
    {
        'id': 'PP',
        'name': 'Purely Plant DOOEL',
        'name_en': 'Purely Plant DOOEL',
        'match': ['purelyplant'],
    },
]


def canonical_lab(printed):
    """(id, canonical name) for a printed laboratory name, or (None, printed).

    An unmatched name is returned unchanged rather than guessed at: a laboratory
    the list does not know must be added to the list, not silently renamed.
    """
    f = _fold(printed)
    for lab in LABORATORIES:
        if any(m in f for m in lab['match']):
            return lab['id'], lab['name']
    return None, printed


# --- Strains ------------------------------------------------------------------
# Established nomenclature. A certificate spelling that resolves here refers to
# the canonical strain: "Cap Junkie" on an eCoA means Cap Junky.
STRAINS = [
    # Established names are the Head of QC's own manifest (priority_batches.tsv).
    # Aliases are every spelling the corpus actually produced across 221
    # certificates - laboratory typos, transliterations and case variants.
    # Without these, query 2 (THC per strain) splits one strain into four rows:
    # Cap Junky appeared as Cup Junky / Cup Junkie / Cup Jankie / CUP JUNKIE.
    ('Cap Junky',           ['capjunky', 'capjunkie', 'capjunki', 'capjuncky',
                             'cupjunky', 'cupjunkie', 'cupjankie', 'cupjanky']),
    ('Blue Gelato',         ['bluegelato']),
    ('Blue Sunset Sherbet', ['bluesunsetsherbet', 'bluesunsetsherbert', 'bluesunsetsherb']),
    ('Grape Pie',           ['grapepie', 'grappie']),
    ('Gorilla Glue',        ['gorillaglue', 'gorilaglue']),
    ('Orange Punch Mimosa', ['orangepunchmimosa', 'orangepiemimosa', 'orangepunch',
                             'orangepunchmimoza']),
    ('High Pro Amnesia',    ['highproamnesia']),
    ('Jelly Donuts',        ['jellydonuts', 'jellydonutz']),
    ('Jokerz 31',           ['jokerz31', 'jokers31']),
    ('Permanent Marker',    ['permanentmarker', 'permanentmarket']),
    ('Scrambler',           ['scrambler']),
    ('Fat Bastard',         ['fatbastard']),
    ('Cash Cow',            ['cashcow']),
    ('Sleepy Joe',          ['sleepyjoe', 'sleepyjoy']),
    ('Kush Crasher',        ['kushcrasher', 'kushkrasher']),
    ('Motor Breath',        ['motorbreath']),
    ('Grapes and Cream',    ['grapesandcream', 'grapscreme', 'grapsandcreme',
                             'grapescream']),
    ('Appels & Bananas',    ['appelsbananas', 'appleandbanana', 'applesandbananas',
                             'appleandbananas']),
    ('Clemosa A Bud',       ['clemosaabud']),
    ('Amnesia Core Cut',    ['amnesiacorecut']),
    ('Chem Flyer',          ['chemflyer']),
    ('Pure Michigen',       ['puremichigen', 'puremichigan']),
    ('Wedding Crusher',     ['weddingcrusher']),
    ('Wedding Cake',        ['weddingcake']),
]


def canonical_strain(printed):
    """Established strain name for a printed one, or the printed value unchanged.

    Batch codes may be embedded in the printed strain ("Blue Gelato BG1024"), so
    matching is containment, not equality.
    """
    if printed is None:
        return None
    f = _fold(printed)
    for name, aliases in STRAINS:
        if any(a in f for a in aliases):
            return name
    return printed


# --- Units --------------------------------------------------------------------
# Heavy metals and mycotoxins are reported in mg/kg and µg/kg across the corpus;
# no certificate prints ppm. Should one appear, ppm IS mg/kg and ppb IS µg/kg for
# a solid matrix, so the unit strings are unified rather than the numbers
# converted - a conversion factor here would be a factor of one and a place for a
# future bug to hide.
_UNITS = {
    'mg/kg': ['mg/kg', 'ppm', 'мг/кг'],
    'µg/kg': ['µg/kg', 'ug/kg', 'mcg/kg', 'ppb', 'мкг/кг'],
    'CFU/g': ['cfu/g', 'кое/г'],
    '%':     ['%', '% w/w', '%w/w', '% m/m'],
}
_UNIT_LOOKUP = {_fold(v): k for k, vs in _UNITS.items() for v in vs}


def canonical_unit(printed):
    """Canonical unit for a printed one, or the printed value unchanged.

    Certificate capture picks up footnote markers ("mg/kg(1)" read as "mg/kg(l)"),
    so a trailing parenthesised marker is stripped before matching.
    """
    if printed is None:
        return None
    s = re.sub(r'\s*\([^)]*\)\s*$', '', str(printed).strip())
    return _UNIT_LOOKUP.get(_fold(s), printed)


# --- Pesticide panels ---------------------------------------------------------
# The specification offers a choice of panel by jurisdiction. Both reporting
# shapes occur in the corpus and both are valid:
#
#   PANEL-WIDE   one statement covering the whole panel
#                DFL 10802_2845/2: "≤ LOQ", 471 compounds, LOQ 0.01 mg/kg
#   PER-COMPOUND one row per compound, each with its own result
#                IJZ 752/2025: 29 organochlorine compounds, each н.д.
#
# A per-compound panel conforms only if EVERY compound conforms; any compound
# above LOQ is a find and is named individually on the CoQ.
PANELS = {
    'PH_EUR_2813': {
        'name': 'Ph. Eur. 2.8.13 — Pesticide residues',
        'criterion': '≤ LOQ per Ph. Eur. 2.8.13',
        'method': 'Ph. Eur. 2.8.13 (LC-MS/MS, GC-MS/MS)',
        'match': ['pheur2813', 'ph.eur.2.8.13', '2813'],
    },
    'MKS_EN_15662': {
        'name': 'МКС EN 15662 (QuEChERS) — national equivalency',
        'criterion': '≤ LOQ per МКС EN 15662',
        'method': 'МКС EN 15662 (LC-MS/MS, GC-MS/MS)',
        'match': ['mks en15662', 'мксen15662', 'mkcen15662', 'en15662'],
    },
}

# A printed parameter that names the panel rather than a compound.
_PANEL_PHRASES = ['пестицид', 'pesticid', 'немапронајдено', 'nopesticide']

# Results that mean "not present above the reporting limit".
_NOT_FOUND = ['нд', 'nd', 'notdetected', 'loq', 'непронајдено', 'neg']


def is_panel_statement(parameter_printed):
    """True when this row states the panel as a whole, not a single compound."""
    f = _fold(parameter_printed)
    return any(p in f for p in _PANEL_PHRASES)


def is_not_found(result_printed):
    """True when a pesticide result reports nothing above LOQ."""
    f = _fold(result_printed)
    return bool(f) and any(f == n or f.endswith(n) or f.startswith(n) for n in _NOT_FOUND)


def panel_of(method_printed):
    """Panel id a certificate's printed method belongs to, or None."""
    f = _fold(method_printed)
    for pid, p in PANELS.items():
        if any(_fold(m) in f for m in p['match']):
            return pid
    return None


# --- Qualitative result equivalence ------------------------------------------
# A qualitative result is a WORD, and Macedonian inflects it: one model reads
# "отсуство" (absence, noun), another "отсутна" (absent, fem.) or "отсуства"
# from the same printed cell. These are the same finding, and holding them as a
# disagreement wastes a reviewer on grammar. Latin "g" vs Cyrillic "г" in the
# unit is the same class.
#
# The map is EXPLICIT, never fuzzy: "присутна" (present) must never resolve to
# absent, so nothing is matched by stem or edit distance.
_QUALITATIVE = {
    'absent':   ['отсуство', 'отсутна', 'отсутен', 'отсутно', 'отсуства', 'отсутни',
                 'отсуствува',           # "is absent" - the verb form IJZ prints since 09.2026
                 'absent', 'absence', 'notdetected', 'negative', 'неутврдено'],
    'conforms': ['одговара', 'соодветствува', 'conforms', 'confirms', 'complies',
                 'conform', 'compliant'],
    'nd':       ['нд', 'nd', 'н.д.', 'n.d.', 'notdetected'],
    'blq':      ['blq', 'loq', 'подloq'],
}
_LAT2CYR = str.maketrans('aceopxyABCEHKMOPTXY', 'асеорхуАВСЕНКМОРТХУ')
_CYR2LAT = str.maketrans('асеорхуАВСЕНКМОРТХУ', 'aceopxyABCEHKMOPTXY')
_QUAL_LOOKUP = {}
for _k, _vs in _QUALITATIVE.items():
    for _v in _vs:
        _QUAL_LOOKUP[_fold(_v)] = _k


def qualitative_key(printed):
    """The finding a qualitative result states, ignoring inflection and script.

    Returns a canonical token ('absent', 'conforms', ...) when the value is a
    recognised qualitative finding, else None - so a caller can fall back to
    comparing the printed strings and never silently equate two numbers.
    A trailing unit ("отсутна/25 g") is stripped before matching.
    """
    if printed is None:
        return None
    t = str(printed).split('/')[0]
    t = re.sub(r'[\d\s]+$', '', t)
    k = _QUAL_LOOKUP.get(_fold(t))
    if k is None:
        # A model can finish a Cyrillic word with a Latin look-alike ("Отсуствa",
        # Latin a) or the reverse. Try the word in one script, then the other -
        # still an exact lookup in the explicit map, never a stem match.
        for tbl in (_LAT2CYR, _CYR2LAT):
            k = _QUAL_LOOKUP.get(_fold(t.translate(tbl)))
            if k is not None:
                break
    return k
