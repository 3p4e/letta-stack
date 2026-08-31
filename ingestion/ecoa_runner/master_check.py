#!/usr/bin/env python3
"""Reconcile the potency master against the extracted certificate corpus.

Two independent records of the same batches: the master the Head of QC keeps,
and what 253 certificates actually say. Where they disagree, one of them is
wrong, and a CoQ built from either alone would carry the error onto a released
document. This says where they disagree and in which direction.

Three checks:

  A  IDENTITY   every batch in the database resolves to a master row, and
                every master row is represented in the database.
  B  STRAIN     the master's strain and the certificates' strain agree.
  C  THC        the Total THC the certificates report falls inside the
                per-batch acceptance range the master sets. Where it does
                not, the batch was released outside its own class.
"""
import os, sys, sqlite3, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'common'))
import master_spec as MS
from controlled import canonical_strain


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=os.path.join(HERE, 'ecoa.sqlite'))
    a = ap.parse_args()
    db = sqlite3.connect(a.db)

    batches = [r[0] for r in db.execute(
        'SELECT DISTINCT batch FROM result WHERE batch IS NOT NULL ORDER BY batch')]

    print('=' * 78)
    print('POTENCY MASTER vs CERTIFICATE CORPUS')
    print('=' * 78)

    # --- A identity ----------------------------------------------------------
    unknown = [b for b in batches if not MS.spec_for(b)]
    seen = {MS.spec_for(b)['batch'] for b in batches if MS.spec_for(b)}
    absent = [r['batch'] for r in MS.ROWS if r['batch'] not in seen]

    print('\nA. IDENTITY')
    print('   %d batches in the database, %d rows in the master.'
          % (len(batches), len(MS.ROWS)))
    print('   %d database batches have NO master row:' % len(unknown))
    for b in unknown:
        print('       %s' % b)
    print('   %d master rows have NO certificate in the corpus:' % len(absent))
    for b in absent:
        r = MS.BY_BATCH[b]
        print('       %-14s %-20s %s' % (b, r['strain'], r['pp_batch']))

    # --- B strain ------------------------------------------------------------
    print('\nB. STRAIN')
    bad = []
    for b in batches:
        r = MS.spec_for(b)
        if not r:
            continue
        got = {canonical_strain(x[0]) for x in db.execute(
            'SELECT DISTINCT strain FROM result WHERE batch=? AND strain IS NOT NULL',
            (b,))}
        got.discard(None)
        if got and r['strain'] not in got:
            bad.append((b, r['strain'], sorted(got)))
    if bad:
        for b, want, got in bad:
            print('   %-14s master says %-20s certificates say %s'
                  % (b, want, ', '.join(got)))
    else:
        print('   All batches agree.')

    # --- C THC ---------------------------------------------------------------
    # --- C THC ---------------------------------------------------------------
    # The master's figure matches the LATEST assay, not the release assay:
    # BG1024 is carried at 26.14 %, which is Farmahem's 07.08.2026 retest, not
    # CNP's 21.80 % of 26.02.2025. So the master is compared against the most
    # recent campaign, and the spread between campaigns is reported separately -
    # it is the more interesting number, because it is two laboratories
    # disagreeing about one batch.
    print('\nC. TOTAL THC vs the batch acceptance range')
    print('   Compared against the LATEST campaign, which is what the master')
    print('   carries.')
    print()
    print('   %-14s %-7s %-7s %-6s %-15s %s'
          % ('Batch', 'master', 'latest', 'delta', 'range', 'verdict'))
    out = []
    spread = []
    for b in batches:
        r = MS.spec_for(b)
        if not r:
            continue
        rows = list(db.execute(
            "SELECT date_iso, result_numeric, lab, cert_code FROM result "
            "WHERE batch=? AND parameter='total_thc' AND result_numeric IS NOT NULL "
            "AND reads_agree=1 AND date_iso IS NOT NULL ORDER BY date_iso", (b,)))
        if not rows:
            continue
        last = rows[-1][0]
        v = max(x[1] for x in rows if x[0] == last)
        lo, hi = r['range_low'], r['range_high']
        ok = lo <= v <= hi
        d = v - r['thc_exact'] if r['thc_exact'] is not None else None
        if not ok or (d is not None and abs(d) > 0.05):
            out.append((b, r['thc_exact'], v, d, '%.2f-%.2f' % (lo, hi),
                        'OUT OF RANGE' if not ok else 'differs'))
        # Campaign spread: first vs last, when there is more than one campaign.
        first = rows[0][0]
        if first != last:
            fv = max(x[1] for x in rows if x[0] == first)
            spread.append((b, first, fv, rows[0][2], last, v, rows[-1][2], v - fv))
    for b, mv, v, d, rng, verdict in out:
        print('   %-14s %-7s %-7.2f %-6s %-15s %s'
              % (b, ('%.2f' % mv) if mv is not None else '-', v,
                 ('%+.2f' % d) if d is not None else '-', rng, verdict))
    oor = [x for x in out if x[5] == 'OUT OF RANGE']
    print()
    print('   %d batch(es) differ from the master; %d fall OUTSIDE the range'
          % (len(out), len(oor)))
    print('   the master itself sets for them.')

    print('\nD. CAMPAIGN SPREAD - the same batch, assayed twice')
    print('   %-14s %-11s %-7s %-11s %-7s %s'
          % ('Batch', 'first', 'THC', 'latest', 'THC', 'change'))
    spread.sort(key=lambda x: -abs(x[7]))
    for b, f, fv, flab, l, lv, llab, d in spread:
        print('   %-14s %-11s %-7.2f %-11s %-7.2f %+.2f pp'
              % (b, f, fv, l, lv, d))
    up = [x for x in spread if x[7] > 0.5]
    print()
    print('   %d batch(es) assayed twice. %d came back HIGHER on retest by more'
          % (len(spread), len(up)))
    print('   than 0.5 pp, which THC degradation cannot explain: cannabinoids')
    print('   decay with age, they do not accumulate in a packed batch. Each is')
    print('   a laboratory-to-laboratory disagreement, not a shelf-life effect.')


if __name__ == '__main__':
    main()
