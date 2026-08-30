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

# --- Maximum acceptable count -------------------------------------------------
# A Ph. Eur. acceptance criterion stated as 10^n is interpreted with a maximum
# acceptable count above it, and a result is out of specification only above THAT.
# The multiplier is a QA determination and is NOT set here: the in-house template
# prints 5x (10^4 -> "max 50 000"), while the general interpretation rule for
# non-sterile products is commonly cited as 2x. Getting this wrong in either
# direction misclassifies batches, so nothing is assumed.
#
# Set MAX_MULTIPLIER to the ruled value (e.g. 2 or 5) to enable out-of-specification
# determination. While it is None, only "exceeds the stated criterion" is reported.
MAX_MULTIPLIER = None


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
