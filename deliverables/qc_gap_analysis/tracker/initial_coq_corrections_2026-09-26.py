#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every cell the rulings of 26.09.2026 changed on a Tranche 3 initial certificate, before and after.

    python3 tracker/initial_coq_corrections_2026-09-26.py

Before is the register at `8b39495`, ahead of the Tranche 3 correction; after is the register now. A
result cell with no value printed `[ — ]` on every page before 26.09 (the renderer tested the value
before the status), so that is what "before" shows for it.

Tranches 1 and 2 are issued and with the customer and are not touched (Head of QC, 26.09.2026). The
Tranche 3 retests withdrawn for no reissuance are listed at the end of the run.
"""
import collections
import csv
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import audit_empty_results as A                                    # noqa: E402

BEFORE = {'T3': '8b39495'}
OUT = os.path.join(HERE, 'INITIAL_COQ_CORRECTIONS_2026-09-26.tsv')


def at(ref):
    txt = subprocess.check_output(['git', 'show', '%s:deliverables/qc_gap_analysis/coq_artifact_data.json' % ref],
                                  cwd=GAP)
    return {(c['regcode'], c['t']): c for c in json.loads(txt)['coqs']}


def show(r, before):
    v = str(r.get('res') or '—').split('|')[0].strip()
    st = str(r.get('st') or '')
    if v in ('—', ''):
        if before:
            return '[ — ]', ''
        return ('n/t' if 'not tested' in st else '[pending]' if st.startswith('awaiting') else '[ — ]'), ''
    return v, str(r.get('doc') or '')


def kind(no, after, st, src=''):
    if no in ('10.1', '10.3') and after == 'n/t':
        return 'B1 / OTA → n/t (IPH tested total aflatoxins at release; the Farmahem panel is the retest)'
    if no in ('1', '2', '7'):
        return 'Ident A / Ident B / foreign matter → the CNP certificate that tested them'
    if no in ('grade', 'spec', 'pcode'):
        return 'grade / specification / product code assigned'
    if after == '[pending]':
        return '→ [pending] (a missing page, or results awaiting a ruling)'
    if after == 'n/t' and st.startswith('not tested by a release certificate'):
        return '→ n/t (the family was tested at release, but no release certificate carries this parameter)'
    if after == 'n/t':
        return '→ n/t (no certificate for the lot; requested from the laboratory)'
    if A.CAMPAIGN.match(src):
        return '→ Farmahem value: the lot\'s first testing, so its release testing (CoQ dated after it)'
    if src.startswith('ППК'):
        return '→ the CNP release certificate\'s own value, never printed before'
    if src == '276-31-М/25':
        return '→ total aflatoxins from the Farmahem release panel of 2025'
    return '→ the lot\'s first testing of the parameter (CoQ dated after it)'


def main():
    now = {(c['regcode'], c['t']): c for c in json.load(open(os.path.join(GAP, 'coq_artifact_data.json'),
                                                                 encoding='utf-8'))['coqs']}
    tm = A.tranche_map()

    def tr(c):
        for k in (c.get('pp'), c.get('cb'), (c.get('cb') or '').replace('＊', '')):
            if k and k in tm:
                return tm[k]

    cache, rows, tally = {}, [], collections.Counter()
    for key in sorted(now, key=lambda k: k[0]):
        c1 = now[key]
        t = tr(c1)
        if t not in BEFORE or 'retest' in c1['t']:
            continue
        ref = BEFORE[t]
        c0 = cache.setdefault(ref, at(ref))[key]
        r0 = {r['no']: r for r in c0['rows']}
        ch = []
        for r in c1['rows']:
            if r['no'] in ('9.6', '9.7'):
                continue
            x0, x1 = show(r0[r['no']], True), show(r, False)
            if x0 != x1:
                ch.append((r['no'], A.NAME.get(r['no'], r['no']), x0, x1, str(r.get('st') or '')))
        for f in ('grade', 'spec', 'pcode'):
            if str(c0.get(f) or '') != str(c1.get(f) or ''):
                ch.append((f, f, (c0.get(f) or '—', ''), (c1.get(f) or '—', ''), ''))
        for no, nm, x0, x1, st in ch:
            k = kind(no, x1[0], st, x1[1])
            tally[(t, k)] += 1
            rows.append([t, c1['regcode'], c1.get('pp') or '', c1.get('cb') or '', c0.get('issue'), c1.get('issue'),
                         no, nm, x0[0], x1[0], x1[1], k, st])
    with open(OUT, 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh, delimiter='\t')
        w.writerow(['tranche', 'coq', 'p_lot', 'cultivation_batch', 'date_before', 'date_after', 'row', 'parameter',
                    'before', 'after', 'after_source', 'correction', 'register_status'])
        w.writerows(rows)
    for t in sorted(BEFORE):
        n = len({r[1] for r in rows if r[0] == t})
        print('%s — %d initial CoQs corrected' % (t, n))
        for (tt, k), v in sorted(tally.items()):
            if tt == t:
                print('    %4d  %s' % (v, k))
        red = sorted({(r[1], r[4], r[5]) for r in rows if r[0] == t and r[4] != r[5]})
        print('    re-dated: %s' % (', '.join('%s %s→%s' % x for x in red) or 'none'))
    gone = sorted((tr(c), c['regcode'], c.get('icoa_code'), c['withdrawn']) for c in now.values() if c.get('withdrawn'))
    for x in gone:
        print('withdrawn: %s %s (%s) — %s' % (x[0], x[1], x[2], x[3][:90]))
    print('written %s (%d rows)' % (os.path.relpath(OUT, GAP), len(rows)))


if __name__ == '__main__':
    main()
