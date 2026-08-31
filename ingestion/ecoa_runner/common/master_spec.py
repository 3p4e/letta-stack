"""The potency master specification, batch by batch.

Source: PP_Potency_MASTER_Spec.xlsx (Head of QC, 31.08.2026), sheet
"Master - All Batches". It is the authority for things no certificate carries:

  * which SPECIFICATION governs a batch  (QCSP_001_<STRAIN>-<GRADE>_v.01)
  * the batch's PRODUCT TYPE and grade   (CJ_THC28:CBD1, Grade I)
  * the ACCEPTANCE RANGE for Total THC   (nominal +/- 10 % relative)
  * the CULTIVATION <-> PP batch identity (CJ082501_1 is P060022)
  * harvest and packaging DATES

The CoQ needs all five: Section 01 names the specification and the product,
Section 02 states Total THC against a criterion that is per-batch rather than
per-monograph, and the batch identity is what joins a certificate to a batch.

Grade numbering is PER STRAIN - Grade I is that strain's strongest class, so
"Grade I" means 28 % on Cap Junky and 18 % on Fat Bastard. It is a rank, never
an absolute potency, and must not be compared across strains.

Batch codes are normalised to the grammar the corpus uses (2.1): the master
writes the first separator as "/", the database as "_". Both are kept -
cultiv_batch_src is what the master prints, 'batch' is what joins.
"""
import os
import csv

_TSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'master_spec.tsv')

# The master prints OMP1024_01 for row 21; its own strain column says Orange
# Punch Mimosa and every certificate in the corpus says OPM. A transposed pair
# of letters in a batch code is a typo, not a second batch - but it is
# corrected HERE and named, never silently inside a matcher.
TYPOS = {'OMP1024_01': 'OPM1024_01'}


def _norm(code):
    """Batch code in corpus grammar: first separator '_', typos corrected."""
    if not code:
        return None
    c = code.strip().replace('/', '_', 1)
    return TYPOS.get(c, c)


def _load():
    rows = []
    with open(_TSV, encoding='utf-8') as fh:
        for r in csv.DictReader(fh, delimiter='\t'):
            for k in ('nominal_pct', 'tolerance_pct', 'range_low',
                      'range_high', 'thc_exact'):
                r[k] = float(r[k]) if r[k] else None
            r['batch'] = _norm(r['cultiv_batch_src'])
            r['harvest'] = r['harvest'] or None
            rows.append(r)
    return rows


ROWS = _load()

# Both identities address the same row: certificates cite either.
BY_BATCH = {r['batch']: r for r in ROWS}
BY_PP = {r['pp_batch']: r for r in ROWS if r['pp_batch']}


def spec_for(batch):
    """Master row for a batch named by either identity, or None."""
    if not batch:
        return None
    b = _norm(batch)
    return BY_BATCH.get(b) or BY_PP.get(b)


def thc_criterion(batch):
    """(low, high, printed) acceptance range for Total THC, or None.

    Per-batch, from the class the batch was released against - not a monograph
    limit. A CoQ that prints a generic THC criterion prints the wrong one.
    """
    r = spec_for(batch)
    if not r:
        return None
    # Kept short: the CoQ's criterion column is narrow, and the class and
    # grade this range comes from are already stated in Section 01.
    return (r['range_low'], r['range_high'],
            '%.2f - %.2f %%' % (r['range_low'], r['range_high']))
