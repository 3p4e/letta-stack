#!/usr/bin/env python3
"""The in-house iCoA issuance register.

Four specification rows have no external source anywhere in the corpus:

    row 1  Identification A, Appearance      (macroscopic)
    row 2  Identification B                  (microscopy, Ph. Eur. 2.8.23)
    row 3  Identification C                  (HPLC identity, Ph. Eur. 2.2.29)
    row 7  Foreign Matter                    (Ph. Eur. 2.8.2)

They were carried by QCCoA 001, which the Head of QC retired; nothing replaced
it. Every one of them is a test Purely Plant performs IN HOUSE, so the gap is
closed by issuing an internal Certificate of Analysis (iCoA) per batch and
referencing it from the CoQ's Section 03 like any external laboratory.

This register says, for each CoQ document the company owes, which of those four
rows it still lacks - and groups them into the iCoA documents that would close
them. One iCoA covers every missing row of ONE campaign of ONE batch: the four
tests are performed together on the same retained sample, so splitting them
across four certificates would multiply paperwork without adding evidence.

A row is reported in one of three states, and they are not interchangeable:

    MISSING     no certificate in the corpus covers this row at all
    NOT TESTED  a covering certificate exists but omits the row
    HELD        a value was read but the two reads disagree - a REVIEW item,
                not a testing item, so it never becomes an iCoA line

Numbering follows the CoQ it serves, so the two registers read side by side:
QCiCoA 007/01 is the in-house certificate for QCCoQ 007 v.01.
"""
import os, sys, json, sqlite3, argparse, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


CR = _load('cr', HERE + '/coq_register.py')

# The in-house rows, in specification order. The label is the one the CoQ
# prints, so the iCoA and the CoQ name the same test with the same words.
IN_HOUSE = [
    ('1', 'Ident A', 'Identification A, Appearance', 'Ph. Eur. mon. 3028 (macroscopic)'),
    ('2', 'Ident B', 'Identification B',             'Ph. Eur. 2.8.23 (microscopy)'),
    ('3', 'Ident C', 'Identification C',             'Ph. Eur. 2.2.29 (HPLC identity)'),
    ('7', 'Foreign M', 'Foreign Matter',             'Ph. Eur. 2.8.2'),
]
ROWS = [r[0] for r in IN_HOUSE]
PREFIX = 'QCiCoA'


def build(db):
    """One entry per CoQ document, carrying its in-house gap."""
    out = []
    for r in CR.register(db):
        ok, tot, miss, held, nt = CR.readiness(db, r['batch'], as_of=r['date'])
        # str() because readiness returns the spec numbers as printed on the CoQ.
        miss = {str(x) for x in miss}
        held = {str(x) for x in held}
        nt = {str(x) for x in nt}
        state = {}
        for n in ROWS:
            if n in miss:
                state[n] = 'MISSING'
            elif n in nt:
                state[n] = 'NOT TESTED'
            elif n in held:
                state[n] = 'HELD'
            else:
                state[n] = 'ok'
        need = [n for n in ROWS if state[n] in ('MISSING', 'NOT TESTED')]
        e = dict(r)
        e['state'] = state
        e['needs'] = need
        e['icoa'] = '%s %03d/%02d' % (PREFIX, r['no'], r['version']) if need else None
        out.append(e)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=HERE + '/ecoa.sqlite')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--tsv', action='store_true')
    a = ap.parse_args()
    rows = build(sqlite3.connect(a.db))

    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1)); return
    if a.tsv:
        print('\t'.join(['icoa_code', 'coq_code', 'coq_date', 'batch', 'strain',
                         'kind'] + [l for _, l, _, _ in IN_HOUSE]))
        for r in rows:
            print('\t'.join([r['icoa'] or '', r['code'], r['date'] or '',
                             r['batch'], r['strain'] or '', r['kind']]
                            + [r['state'][n] for n in ROWS]))
        return

    W = 116
    print('=' * W)
    print('IN-HOUSE iCoA ISSUANCE REGISTER — Identification A/B/C and Foreign Matter')
    print('chronological by CoQ date; one iCoA closes one campaign of one batch')
    print('=' * W)
    print('%-16s %-16s %-11s %-17s %-9s %-9s %-9s %-9s'
          % ('iCoA to issue', 'for CoQ', 'CoQ date', 'Batch',
             'Ident A', 'Ident B', 'Ident C', 'Foreign M'))
    print('-' * W)
    mark = {'ok': '.', 'MISSING': 'MISSING', 'NOT TESTED': 'NOT TEST', 'HELD': 'held'}
    for r in rows:
        print('%-16s %-16s %-11s %-17s %-9s %-9s %-9s %-9s'
              % (r['icoa'] or '—', r['code'], r['date'] or '(no date)',
                 r['batch'][:17],
                 *[mark[r['state'][n]] for n in ROWS]))
    print('-' * W)

    need = [r for r in rows if r['needs']]
    print('\n%d CoQ document(s); %d need an in-house iCoA before they can be issued.'
          % (len(rows), len(need)))
    for n, label, name, method in IN_HOUSE:
        c = {}
        for r in rows:
            c[r['state'][n]] = c.get(r['state'][n], 0) + 1
        print('  row %-2s %-28s  missing %-4d not tested %-4d held %-4d sourced %d'
              % (n, name, c.get('MISSING', 0), c.get('NOT TESTED', 0),
                 c.get('HELD', 0), c.get('ok', 0)))
    print('\nBatches to sample: %d' % len({r['batch'] for r in need}))
    print('An iCoA carries every row marked MISSING or NOT TEST for its CoQ.')
    print('A row marked "held" is a reading disagreement — settle it in the')
    print('confirmation queue; it is not retested.')


if __name__ == '__main__':
    main()
