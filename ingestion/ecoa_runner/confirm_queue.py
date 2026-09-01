#!/usr/bin/env python3
"""What a human must confirm before CoQs can issue, ordered by consequence.

Everything here is a QUESTION, never a defect to be silently resolved. Each
entry names the document, what is in doubt, and what both models read - so the
reviewer opens one page and answers, rather than investigating from scratch.

Priority is by what the answer changes:
  A  a number that would appear on a CoQ            (held analytical results)
  B  the traceability of a result already confirmed (missing document codes)
  C  a conformity judgement                         (exceeds stated criterion)
  D  a laboratory's template                        (printed-limit defects)
"""
import os, sqlite3, argparse, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
# Rows the CoQ actually prints. A held pesticide compound or a held individual
# cannabinoid matters less than a held Total THC, because only the total is a
# specification row - so the queue leads with what the certificate must state.
SPEC_KEYS = ['total_thc','total_cbd','total_cbn','foreign_matter','loss_on_drying',
             'tamc','tymc','bile_tolerant_gram_negative','salmonella','escherichia_coli',
             'aflatoxin_b1','aflatoxins_total','ochratoxin_a',
             'lead','cadmium','arsenic','mercury','pesticide_residues',
             'identification_a_macroscopic','identification_b_microscopic',
             'identification_c_hplc']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=HERE + '/ecoa.sqlite')
    ap.add_argument('--limit', type=int, default=25)
    a = ap.parse_args()
    db = sqlite3.connect(a.db)
    W = 112
    print('=' * W); print('CONFIRMATION QUEUE — decisions required before CoQs can issue'); print('=' * W)

    ph = ','.join('?' * len(SPEC_KEYS))
    print('\nA. VALUE DISAGREEMENTS — the two reads returned different values for')
    print('   the same printed row. These need a page and a ruling.')
    rows = db.execute("""SELECT batch, cert_code, date_iso, parameter, read_a, read_b,
        parameter_printed FROM result WHERE confidence!='ok'
        AND read_a IS NOT NULL AND read_b IS NOT NULL
        AND read_a NOT IN ('null','') AND read_b NOT IN ('null','')
        ORDER BY CASE WHEN parameter IN (%s) THEN 0 ELSE 1 END, batch""" % ph,
        SPEC_KEYS).fetchall()
    def val(x):
        try: return (json.loads(x) or {}).get('result')
        except Exception: return None
    real = [r for r in rows if str(val(r[4])) != str(val(r[5]))]
    print('   %d row(s)\n' % len(real))
    for b, c, d, p, ra, rb, pp in real[:a.limit]:
        star = ' *SPEC ROW' if p in SPEC_KEYS else ''
        print('   %-13s %-13s %-11s %-24s%s' % (b or '?', (c or '—')[:13], d or '—', p[:24], star))
        print('        A: %-30s  B: %s' % (str(val(ra))[:30], str(val(rb))[:34]))
    if len(real) > a.limit: print('   ... and %d more' % (len(real) - a.limit))

    print('\nA2. SINGLE-READ ROWS — one model reported a row the other did not.')
    print('    The question is whether the row EXISTS on the page, not which value')
    print('    is right. Only specification rows are listed; pesticide compounds and')
    print('    non-specification rows are excluded (they do not reach a CoQ).')
    solo = db.execute("""SELECT batch, cert_code, date_iso, parameter, COUNT(*)
        FROM result WHERE confidence!='ok'
        AND (read_a IS NULL OR read_a IN ('null','')) 
        AND (read_b IS NULL OR read_b IN ('null',''))
        AND parameter IN (%s)
        GROUP BY batch, cert_code, parameter ORDER BY batch""" % ph, SPEC_KEYS).fetchall()
    excluded = db.execute("""SELECT COUNT(*) FROM result WHERE confidence!='ok'
        AND (read_a IS NULL OR read_a IN ('null','')) AND parameter NOT IN (%s)""" % ph,
        SPEC_KEYS).fetchone()[0]
    print('    %d specification row(s); %d non-specification rows excluded\n'
          % (len(solo), excluded))
    for b, c, d, p, n in solo[:a.limit]:
        print('    %-13s %-13s %-11s %s' % (b or '?', (c or '—')[:13], d or '—', p))
    if len(solo) > a.limit: print('    ... and %d more' % (len(solo) - a.limit))

    print('\nB. CERTIFICATES WITH NO DOCUMENT CODE — a CoQ cites every result by')
    print('   document code; these cannot be cited until the code is supplied.')
    nc = db.execute("""SELECT batch, date_iso, lab, document FROM certificate
        WHERE cert_code IS NULL ORDER BY date_iso""").fetchall()
    print('   %d certificate(s)\n' % len(nc))
    for b, d, lab, doc in nc[:a.limit]:
        print('   %-13s %-11s %-28s %s' % (b or '?', d or '—', (lab or '?')[:28], (doc or '')[-42:]))
    if len(nc) > a.limit: print('   ... and %d more' % (len(nc) - a.limit))

    print('\nC. RESULTS EXCEEDING THE STATED CRITERION — within the Ph. Eur. 5.1.8')
    print('   maximum acceptable count (5x), so not out of specification, but each')
    print('   needs a recorded QC judgement.')
    ex = db.execute("""SELECT batch, cert_code, date_iso, parameter, result_printed,
        governing_limit FROM result WHERE exceeds_criterion=1 AND confidence='ok'
        ORDER BY batch""").fetchall()
    print('   %d row(s)\n' % len(ex))
    for b, c, d, p, v, gl in ex:
        print('   %-13s %-14s %-11s %-12s %-18s (criterion %s)'
              % (b or '?', (c or '—')[:14], d or '—', p, str(v)[:18], gl))

    print('\nD. PRINTED-LIMIT DEFECTS — the certificate states an acceptance criterion')
    print('   that is not the specification\'s. Raise with the issuing laboratory.')
    pl = db.execute("""SELECT lab, parameter, limit_printed, governing_limit, COUNT(*)
        FROM result WHERE printed_limit_disagrees=1
        GROUP BY lab, parameter, limit_printed ORDER BY COUNT(*) DESC""").fetchall()
    print('   %d distinct defect(s)\n' % len(pl))
    for lab, p, lp, gl, n in pl[:a.limit]:
        print('   %-40s %-14s printed %-10s spec %-8s x%d'
              % ((lab or '?')[:40], p, str(lp)[:10], gl, n))

    print('\n' + '-' * W)
    print('Nothing above changes a stored value. Each is a question for the Head of QC;')
    print('answers are applied to the database, not assumed by it.')


if __name__ == '__main__':
    main()
