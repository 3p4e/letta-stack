"""Ph. Eur. governing acceptance criteria for Purely Plant dry cannabis flower.

Microbiological quality is assessed under **Ph. Eur. 5.1.8, Category C**
(herbal medicinal products for oral use where processing does not reduce the
level of micro-organisms) - as stated in the product specification, Section 02,
which cites "Ph. Eur. 2.6.12 cat. C" and "Ph. Eur. 2.6.31 cat. C".

The certificate's PRINTED limit is not authoritative. Several in-house CoAs print
"< 10^4 CFU/g" against TAMC, where Category C gives 10^5 - a template defect
already raised by the Head of QC (Reconciliation Log section 5.1). Comparing the
printed limit against this table finds every certificate carrying that defect.
"""

# Ph. Eur. 5.1.8 Category C, as carried in the product specification Section 02.
CATEGORY_C = {
    'tamc':                        {'limit': 1e5, 'unit': 'CFU/g',  'ref': 'Ph. Eur. 2.6.12 cat. C'},
    'tymc':                        {'limit': 1e4, 'unit': 'CFU/g',  'ref': 'Ph. Eur. 2.6.12 cat. C'},
    'bile_tolerant_gram_negative': {'limit': 1e4, 'unit': 'CFU/g',  'ref': 'Ph. Eur. 2.6.31 cat. C'},
    'salmonella':                  {'limit': None, 'qualitative': 'Absence / 25 g', 'ref': 'Ph. Eur. 2.6.31 cat. C'},
    'escherichia_coli':            {'limit': None, 'qualitative': 'Absence / 1 g',  'ref': 'Ph. Eur. 2.6.13 cat. C'},
    'pseudomonas_aeruginosa':      {'limit': None, 'qualitative': 'Absence / 1 g',  'ref': 'Ph. Eur. 2.6.13 cat. C'},
    'staphylococcus_aureus':       {'limit': None, 'qualitative': 'Absence / 1 g',  'ref': 'Ph. Eur. 2.6.13 cat. C'},
}

# Non-microbiological criteria, product specification Section 02 (grade-invariant).
SPEC_SECTION_02 = {
    'total_cbd':          {'limit': 1.0,  'unit': '% w/w'},
    'total_cbn':          {'limit': 1.0,  'unit': '% w/w'},
    'foreign_matter':     {'limit': 2.0,  'unit': '%'},
    'loss_on_drying':     {'limit': 12.0, 'unit': '%'},
    'aflatoxin_b1':       {'limit': 2.0,  'unit': 'ug/kg'},
    'aflatoxins_total':   {'limit': 4.0,  'unit': 'ug/kg'},
    'ochratoxin_a':       {'limit': 20.0, 'unit': 'ug/kg'},
    'lead':               {'limit': 0.5,  'unit': 'mg/kg'},
    'cadmium':            {'limit': 0.3,  'unit': 'mg/kg'},
    'arsenic':            {'limit': 0.2,  'unit': 'mg/kg'},
    'mercury':            {'limit': 0.1,  'unit': 'mg/kg'},
}
# total_thc is deliberately absent: it is per grade (specification Section 01).

# --- Superseded criteria ------------------------------------------------------
# A criterion has a history. Loss on drying was ≤ 10.0 % under the DAB 2018
# monograph method; the monograph was later updated and Ph. Eur. sets ≤ 12.0 %.
# A certificate issued while the earlier criterion was in force and printing that
# earlier value is CORRECT for its date - it is not a template defect, and
# reporting it as one sends QC chasing a laboratory that did nothing wrong.
#
# `until` is the last date on which the earlier criterion applied. It is a QA
# determination and is NOT guessed here: while it is None, a printed value that
# matches a superseded criterion is classified as superseded regardless of date,
# which is the safe direction (it never manufactures a defect). Set it to the
# changeover date from the Product Specification version history to date-bound it.
SUPERSEDED_CRITERIA = {
    'loss_on_drying': [
        {'limit': 10.0, 'unit': '%', 'ref': 'DAB 2018 monograph, dry cannabis flower',
         'until': None},
    ],
}


def classify_printed_limit(parameter, printed_limit, date_iso=None):
    """How a certificate's printed acceptance criterion relates to the governing one.

    'match'       - the printed criterion is the governing one
    'superseded'  - it is a criterion that WAS in force (correct for its date)
    'disagrees'   - it is neither: a template defect to raise with the laboratory
    'unknown'     - nothing printed, or no governing criterion for this parameter
    """
    gl, _ = governing(parameter)
    if gl is None or printed_limit is None:
        return 'unknown', None
    if abs(gl - printed_limit) <= 1e-9:
        return 'match', None
    for old in SUPERSEDED_CRITERIA.get(parameter, []):
        if abs(old['limit'] - printed_limit) > 1e-9:
            continue
        if old['until'] is None or date_iso is None or date_iso <= old['until']:
            return 'superseded', old['ref']
        # The earlier criterion, printed after it ceased to apply: still a defect.
        return 'disagrees', 'superseded criterion printed after %s' % old['until']
    return 'disagrees', None

# --- Maximum acceptable count -------------------------------------------------
# A Ph. Eur. acceptance criterion stated as 10^n is interpreted with a maximum
# acceptable count above it, and a result is out of specification only above THAT.
# Ph. Eur. 5.1.8 states the interpretation as "maximum acceptable count = 5 x 10^n"
# (10^4 CFU/g -> 50 000), which is what the in-house template already prints.
#
# This is confirmed by the issuing laboratory's own practice. Four IJZ (ИЈЗ)
# microbiology certificates report TYMC above the printed 10^4 criterion and
# conclude ОДГОВАРА (conforms) on every one:
#
#   163/0271/25  24.02.2025  BG1024      TYMC 1,0 x 10^4
#   320/0587/25  14.04.2025  GG1024_01   TYMC 4,2 x 10^4
#   628/1129/25  02.07.2025  GP0824_03   TYMC 1,2 x 10^4
#   904/1589/25  02.09.2025  OPM052501   TYMC 3,3 x 10^4
#   1032/1851/25 17.10.2025  CJ062501_2  TYMC 4,9 x 10^4   (newest)
#
# All five sit below 5 x 10^4 and none below 2 x 10^4, so the laboratory applying
# these criteria uses the 5x rule; 2x would have failed four of the five.
MAX_MULTIPLIER = 5


def governing(parameter):
    """Return (limit, reference) that governs this parameter, or (None, None)."""
    if parameter in CATEGORY_C:
        e = CATEGORY_C[parameter]
        return e.get('limit'), e['ref']
    if parameter in SPEC_SECTION_02:
        return SPEC_SECTION_02[parameter]['limit'], 'Product specification Section 02'
    return None, None


def max_acceptable(parameter):
    lim, _ = governing(parameter)
    if lim is None or MAX_MULTIPLIER is None:
        return None
    return lim * MAX_MULTIPLIER
