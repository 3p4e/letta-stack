#!/usr/bin/env python3
"""CoQ readiness index — what each batch still needs before a CoQ can be issued.

The CoQ replaces the retired QCCoA 001 / 001v02 certificates. A batch can only be
certified once every specification row carries a confirmed result traceable to the
laboratory that performed it. This index says, per batch, exactly what is missing.

Reissue rule
------------
A retest does not produce a partial certificate. When a parameter is retested, a NEW
CoQ version is issued carrying the retested value together with the values already
established for every parameter that was NOT retested (heavy metals, microbiology,
identification, and so on). Those carry forward from the previous version with their
original certificate reference and date - they are not re-cited to the retest.

Statuses
--------
  READY            every row sourced and confirmed; CoQ can be compiled
  BLOCKED-MISSING  a specification row has no result on any certificate
  BLOCKED-REVIEW   a row's two reads disagreed and is held pending a human
  NEEDS-ICOA       only the retired QCCoA supplies an in-house parameter
  REISSUE-DUE      a retest exists that post-dates the values already in use
"""
import os, sys, sqlite3, argparse, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_coq import SPEC, compile_coq, source_tier      # noqa: E402

MANDATORY = [(n, sub, key, name) for n, sub, key, name, _c, _m in SPEC]


def index_batch(db, batch):
    s02, sources, unresolved = compile_coq(db, batch)
    missing  = [e['no'] for e in s02 if e['status'] == 'MISSING']
    nottested= [e['no'] for e in s02 if e['status'] == 'NOT TESTED']
    byno = {e['no']: e for e in s02}

    # --- parameters tracked individually, per the Head of QC ---------------
    # Foreign Matter must carry a document code AND a date, not merely a value:
    # it is cited on the CoQ like any other result.
    fm = byno.get('7', {})
    fm_state = ('absent' if fm.get('status') != 'ok' else
                'no doc code' if not fm.get('cert_code') else
                'no date' if not fm.get('date') else 'ok')
    # Identification A / B / C are three separate specification rows. A certificate
    # covering only one does not satisfy the other two.
    ident = {i: byno.get(i, {}).get('status', 'MISSING') for i in ('1', '2', '3')}
    ident_missing = [i for i, st in ident.items() if st != 'ok']
    # The ImB specification lists THREE mycotoxins; most eCoAs report fewer.
    myco = {i: byno.get(i, {}).get('status', 'MISSING') for i in ('10a', '10b', '10c')}
    myco_have = [i for i, st in myco.items() if st == 'ok']
    held    = [e['no'] for e in s02 if e['status'] == 'HELD']
    tier3   = [e['no'] for e in s02 if e.get('source_tier') == 3]
    retested = [(e['no'], e['result'], [s[1] for s in e.get('superseded', [])])
                for e in s02 if e.get('superseded')]
    certs = db.execute("""SELECT DISTINCT cert_code, date_iso, lab FROM result
                          WHERE batch=? ORDER BY date_iso""", (batch,)).fetchall()
    qccoa = [c for c in certs if (c[0] or '').upper().replace(' ', '').startswith('QCCOA')]
    strain = db.execute("SELECT strain FROM certificate WHERE batch=? AND strain IS NOT NULL LIMIT 1",
                        (batch,)).fetchone()

    if missing:      status = 'BLOCKED-MISSING'
    elif held:       status = 'BLOCKED-REVIEW'
    elif tier3:      status = 'NEEDS-ICOA'
    elif retested:   status = 'REISSUE-DUE'
    else:            status = 'READY'

    return {'batch': batch, 'strain': strain[0] if strain else None,
            'foreign_matter': fm_state,
            'foreign_matter_cert': fm.get('cert_code'), 'foreign_matter_date': fm.get('date'),
            'identification_missing': ident_missing,
            'mycotoxins_reported': '%d/3' % len(myco_have),
            'mycotoxins_not_tested': [i for i, st in myco.items() if st == 'NOT TESTED'],
            'not_tested': nottested,
            'certificates': len(certs), 'sourced': sum(1 for e in s02 if e['status'] == 'ok'),
            'of': len(SPEC), 'status': status,
            'missing': missing, 'held': held, 'derived_needs_icoa': tier3,
            'retested': retested,
            'qccoa_to_retire': [c[0] for c in qccoa],
            'labs': sorted({(c[2] or '?')[:40] for c in certs})}


def main(dbpath, batch=None, as_json=False):
    db = sqlite3.connect(dbpath)
    batches = ([batch] if batch else
               [r[0] for r in db.execute(
                   "SELECT DISTINCT batch FROM certificate WHERE batch IS NOT NULL ORDER BY batch")])
    rows = [index_batch(db, b) for b in batches]
    if as_json:
        print(json.dumps(rows, ensure_ascii=False, indent=1)); return rows
    W = 108
    print('=' * W)
    print('CoQ READINESS INDEX   %d batch(es)' % len(rows))
    print('=' * W)
    print('%-12s %-17s %-4s %-6s %-15s %-10s %-8s %s'
          % ('Batch', 'Strain', 'CoA', 'Src', 'Status', 'ForeignM', 'Ident', 'Mycotox'))
    print('-' * W)
    for r in rows:
        idm = ('missing ' + ','.join(r['identification_missing'])) if r['identification_missing'] else 'A,B,C ok'
        print('%-12s %-17s %-4d %-6s %-15s %-10s %-8s %s'
              % (r['batch'], (r['strain'] or '')[:17], r['certificates'],
                 '%d/%d' % (r['sourced'], r['of']), r['status'],
                 r['foreign_matter'], idm[:8], r['mycotoxins_reported']))
    print('-' * W)
    tally = {}
    for r in rows: tally[r['status']] = tally.get(r['status'], 0) + 1
    print('  ' + '   '.join('%s %d' % (k, v) for k, v in sorted(tally.items())))
    print('\nPER-PARAMETER GAPS')
    for r in rows:
        bits = []
        if r['foreign_matter'] != 'ok':
            bits.append('Foreign Matter: %s' % r['foreign_matter'])
        elif not r['foreign_matter_cert'] or not r['foreign_matter_date']:
            bits.append('Foreign Matter: doc code/date incomplete')
        if r['identification_missing']:
            bits.append('Identification %s absent' % '/'.join(r['identification_missing']))
        if r['mycotoxins_not_tested']:
            bits.append('mycotoxins %s NOT TESTED (declare on CoQ)' % ','.join(r['mycotoxins_not_tested']))
        if r['missing']:
            bits.append('no covering eCoA for %s' % ','.join(r['missing']))
        if bits:
            print('  %-12s %s' % (r['batch'], ' · '.join(bits)))
    retire = sorted({c for r in rows for c in r['qccoa_to_retire']})
    if retire:
        print('\nQCCoA certificates to retire and replace with a CoQ: %s' % ', '.join(retire))
    reissue = [r for r in rows if r['retested']]
    if reissue:
        print('\nRetests requiring a new CoQ version (carrying forward non-retested rows):')
        for r in reissue:
            for no, cur, prev in r['retested']:
                print('   %-12s row %-4s now %-14s (was %s)' % (r['batch'], no, str(cur)[:14],
                                                                ', '.join(str(p)[:14] for p in prev)))
    return rows


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=HERE + '/ecoa.sqlite')
    ap.add_argument('--batch')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    main(a.db, a.batch, a.json)
