#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fill the empty certificate-of-quality results — the Head of QC's rulings of 26.09.2026.

    python3 tracker/apply_empty_results_ruling_2026-09-26.py --check     # writes nothing
    python3 tracker/apply_empty_results_ruling_2026-09-26.py --apply     # register + lab requests

The rulings, as given:

1. **A result measured after the certificate's date is printed, and the certificate is re-dated**
   on or after the last result it cites — no result may predate its document.
2. **Never another lot's certificate.** *"Do not use certificates of analysis for one batch for
   another batch regardless if it's a sub-lot; they are separate lots."* Parent batches and sibling
   sub-lots are not a source, however close the name.
3. **Mycotoxins: Tranche 3 is the same case as Tranches 1 and 2.** At release the IPH certificates
   report total aflatoxins only; aflatoxin B1 and ochratoxin A come from the Farmahem campaigns of
   August–September 2026. B1 is not derived from the total.
4. **What no certificate covers is requested from the laboratory, and the cell says so** — `n/t`,
   never a bare `[ — ]`.

Where the value comes from: the **same lot's retest record** — same P lot, same cultivation batch —
whose rows already carry the campaign certificates (`197-`, `220-`, `227-К/М/26`) with their dates.
A row the retest record itself only *carries from the initial testing* is not a source.

One case is not filled, on purpose: where the release round already holds results for the row and
they disagree, printing the later campaign's value would hide them. `CoQ-PP_26-026` Total CBN is the
instance — four UKIM results of 0.05, 1.09, 0.04 and 2.05 %, two above the ≤ 1.0 % limit. It is set
to await the Head of QC's ruling and prints `[pending]`.
"""
import argparse
import collections
import csv
import datetime
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import audit_empty_results as A                                    # noqa: E402

REG = os.path.join(GAP, 'coq_artifact_data.json')
STAMP = '26.09.2026'
LAB_FOR = {  # who is asked for what, by the laboratory that reports it elsewhere in the register
    '3': 'Farmahem (К, HPLC identification)', '4': 'Farmahem (К, cannabinoids)',
    '5': 'Farmahem (К, cannabinoids)', '6': 'Farmahem (К, cannabinoids)',
    '8': 'Farmahem (LoD, loss on drying)',
    '9.1': 'IPH microbiology (IJZ-MB)', '9.2': 'IPH microbiology (IJZ-MB)', '9.3': 'IPH microbiology (IJZ-MB)',
    '9.4': 'IPH microbiology (IJZ-MB)', '9.5': 'IPH microbiology (IJZ-MB)',
    '10.1': 'Farmahem (М, mycotoxins)', '10.2': 'IPH contaminants (IJZ)', '10.3': 'Farmahem (М, mycotoxins)',
    '11.1': 'IPH contaminants (IJZ)', '11.2': 'IPH contaminants (IJZ)', '11.3': 'IPH contaminants (IJZ)',
    '11.4': 'IPH contaminants (IJZ)', '12': 'IPH contaminants (IJZ)',
}
EMPTY = ('—', '', 'None')


def empty(row):
    return str(row.get('res')).strip() in EMPTY


def dt(s):
    try:
        d, m, y = str(s).strip().split('.')
        return datetime.date(int(y), int(m), int(d))
    except Exception:
        return None


def release_conflict(c, row):
    """Same-round results for this row, held in `also`, that the desk never chose between."""
    issue = dt(c.get('issue'))
    got = []
    for val, code in A.also_values(row):
        code = code.strip()
        if A.CAMPAIGN.match(code) or 'in-house' in code or 'no certificate' in code:
            continue
        got.append('%s (%s)' % (val.strip(), code))
    return got if len(got) > 1 else []


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--tranche', default='T3')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv[1:])
    if not (a.apply or a.check):
        ap.error('pass --check or --apply')

    reg = json.load(open(REG, encoding='utf-8'))
    tm = A.tranche_map()

    def tranche(c):
        for k in (c.get('pp'), c.get('cb'), (c.get('cb') or '').replace('＊', '')):
            if k and k in tm:
                return tm[k]

    recs = [c for c in reg['coqs'] if tranche(c) == a.tranche]
    key = lambda c: (str(c.get('pp') or ''), str(c.get('cb') or ''))
    ini = {key(c): c for c in recs if 'retest' not in c['t']}
    ret = {key(c): c for c in recs if 'retest' in c['t']}
    if set(ini) != set(ret):
        raise SystemExit('initial and retest records do not pair one to one: %s'
                         % sorted(set(ini) ^ set(ret)))

    filled, pending, untested, redated, requests = [], [], [], [], []
    for k in sorted(ini, key=lambda k: ini[k]['regcode']):
        c, r = ini[k], ret[k]
        rr = {x['no']: x for x in r['rows']}
        cited = []
        for row in c['rows']:
            if not empty(row) or row['no'] in ('9.6', '9.7'):
                continue
            src = rr.get(row['no'])
            conflict = release_conflict(c, row)
            if conflict:
                row['st'] = ("awaiting the Head of QC's ruling — the release round holds %d results that "
                             "disagree: %s" % (len(conflict), '; '.join(conflict)))
                pending.append((c['regcode'], row['no'], '; '.join(conflict)))
                continue
            if src and not empty(src) and 'carried' not in str(src.get('st')) and dt(src.get('dd')):
                for f in ('res', 'doc', 'dd', 'lab', 'fam', 'route'):
                    if f in src:
                        row[f] = src[f]
                row['st'] = ('covered — measured in the retest campaign, %s of %s; the certificate is '
                             'dated on or after it (Head of QC, %s)' % (src['doc'], src['dd'], STAMP))
                cited.append(dt(src['dd']))
                filled.append((c['regcode'], row['no'], src['res'], src['doc'], src['dd']))
            else:
                row['st'] = ('not tested — no certificate for this lot; requested from the laboratory '
                             '(Head of QC, %s)' % STAMP)
                untested.append((c['regcode'], row['no']))
                requests.append((c, row['no']))
        if cited:
            new = max(cited)
            old = dt(c.get('issue'))
            if not old or new > old:
                c['issue_before_redating'] = c.get('issue')
                c['issue'] = '%02d.%02d.%04d' % (new.day, new.month, new.year)
                redated.append((c['regcode'], c['issue_before_redating'], c['issue']))
        # the retest record: what it carries from an initial that has nothing is untested
        for row in r['rows']:
            if empty(row) and row['no'] not in ('9.6', '9.7'):
                row['st'] = ('not tested — no certificate for this lot; requested from the laboratory '
                             '(Head of QC, %s)' % STAMP)
                untested.append((r['regcode'], row['no']))
                if not any(q[0] is c and q[1] == row['no'] for q in requests):
                    requests.append((c, row['no']))

    # guards: nothing filled from another lot, nothing dated before its source, no value overwritten
    for code, no, res, doc, dd in filled:
        c = next(x for x in recs if x['regcode'] == code)
        if dt(c['issue']) < dt(dd):
            raise SystemExit('%s row %s: the certificate is dated before %s (%s)' % (code, no, doc, dd))

    print('%s: filled %d cells from the same lot\'s retest campaign, %d await a ruling, %d not tested'
          % (a.tranche, len(filled), len(pending), len(untested)))
    by = collections.Counter(no for _, no, *_ in filled)
    print('  filled by row: %s' % ', '.join('%s×%d' % (n, k) for n, k in sorted(by.items(), key=lambda x: [float(y) for y in x[0].split('.')[:1]] + [x[0]])))
    print('  initial CoQs re-dated: %d  (%s)' % (len(redated), ', '.join(sorted({'%s→%s' % (o, n) for _, o, n in redated}))))
    for p in pending:
        print('  awaiting ruling: %s row %s — %s' % p)

    if a.check:
        print('--check: nothing written')
        return 0

    shutil.copy2(REG, REG + '.bak')
    with open(REG, 'w', encoding='utf-8') as fh:
        json.dump(reg, fh, ensure_ascii=False, indent=1)
    os.remove(REG + '.bak')

    out = os.path.join(HERE, 'LAB_REQUESTS_%s_2026-09-26.tsv' % a.tranche)
    rows = collections.OrderedDict()
    for c, no in requests:
        k2 = (c.get('pp') or '', c.get('cb') or '', LAB_FOR.get(no, '?'))
        rows.setdefault(k2, {'coqs': set(), 'params': []})
        rows[k2]['coqs'].update({c['regcode'], ret[key(c)]['regcode']})
        if A.NAME.get(no) not in rows[k2]['params']:
            rows[k2]['params'].append(A.NAME.get(no, no))
    with open(out, 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh, delimiter='\t')
        w.writerow(['p_lot', 'cultivation_batch', 'laboratory', 'parameters to test', 'certificates waiting on it'])
        for (pp, cb, lab), v in rows.items():
            w.writerow([pp, cb, lab, ', '.join(v['params']), ' '.join(sorted(v['coqs']))])
    print('wrote the register and %s (%d requests)' % (os.path.relpath(out, GAP), len(rows)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
