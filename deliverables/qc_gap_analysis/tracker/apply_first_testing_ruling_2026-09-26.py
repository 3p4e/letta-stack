#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tranche 3: where Farmahem is the only testing on record, it is the release testing — the Head of
QC, 26.09.2026 (third ruling of the day). Tranche 3 only.

    python3 tracker/apply_first_testing_ruling_2026-09-26.py --check     # writes nothing
    python3 tracker/apply_first_testing_ruling_2026-09-26.py --apply

**Tranches 1 and 2 are not touched** (Head of QC, 26.09.2026): *"they are already issued and sent to
the customer"*; their release testing was CNP (potency) and IPH (mycotoxins) and their retest
testing Farmahem, for every lot. The script refuses them.

His words today:

* *"All retest certificates for all T1, T2 and T3 have all 3 parameters for mycotoxins (B1, total
  aflatoxins, OTA) tested in Farmahem."* Where IPH reported total aflatoxins at release, the Farmahem
  panel is the retest: the initial prints the IPH total, and B1 and OTA `n/t`.
* *"For a batch, if there are no analysis results tested only for total aflatoxins, but there is only
  the full mycotoxins panel tested in Farmahem ... the testing in Farmahem for mycotoxins is part of
  initial release testing for the batch, and this goes for all batches like that."*
* *"If there are no analysis results for cannabinoids available and on record from CNP and there are
  only cannabinoid results from Farmahem, the Farmahem testing is the initial release testing and there
  will be no reissuance for those CoQ, and those results are also going to enter the certificate of
  quality for the customer."*

What the run does, lot by lot (`audit_empty_results.release_family` decides the family):

1. **Cannabinoids** (Identification C with them). No CNP result on record → the Farmahem values
   print on the initial. A CNP result on record → Farmahem is the retest: a Farmahem value on the
   initial comes off, and the cell takes the CNP certificate's own value where it reports one. CNP
   reported CBN for P050032, P050132, P050272 and OPM112501 (ППК25118, ППК25257, ППК25368, ППК26031 —
   the page text is in the RAGflow cache); the register had never printed it, and this morning's run
   filled those four cells from the retest campaign instead.
2. **Mycotoxins.** No IPH total aflatoxins on record → the Farmahem panel (B1, total, OTA) prints on
   the initial.
3. **The date** of each initial (`audit_empty_results.initial_issue`): on or after the last result it
   cites — ruling 1 of 26.09.2026 — at the desk's usual seven days (`issuance_schedule.coq_issue`),
   and never after the lot's own retest (then the retest's date).
4. **No reissuance** — *"there will be no reissuance for those CoQ."* The retest drafts of such lots
   are withdrawn (`withdrawn` in the register; nothing is built for them; their numbers stay free) —
   unless a parameter was tested a second time, well after the first: *"the second certificate for
   microbiology is going to enter the CoQ, and if the initial testing was way before, then it is
   definitely a retest and the reissuing of the CoQ"* (Head of QC, 26.09.2026, on `-160`, P060342:
   IPH 539/1070/26 of 31.08.2026 after 362/0692/26 of 01.06.2026). Such a reissue is kept, and the
   rows it did not retest are marked as carried from the initial.
"""
import argparse
import collections
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import audit_empty_results as A                                    # noqa: E402

REG = os.path.join(GAP, 'coq_artifact_data.json')
STAMP = '26.09.2026'
RULING = 'Head of QC, %s' % STAMP
FIRST = 'covered — the lot\'s first testing, %s of %s, is its release testing (' + RULING + ')'
# prints `n/t`: coq_build.js reads "not tested" in the status (CLAUDE.md §5)
NOT_AT_RELEASE = ('not tested by a release certificate — the release round\'s cannabinoid certificate '
                  '(%s) does not carry it; the retest round determined it: %s of %s, on %s (' + RULING + ')')
RELEASE_CNP = 'covered — %s reports it at release; it had not been printed (' + RULING + ')'
HELD = {}
PANEL_TOTAL = {}
WITHDRAWN = ('no reissuance — the Farmahem campaign was this lot\'s first testing, so it is the release testing '
             'and the lot has one certificate, %s (' + RULING + ')')


def has(r):
    return A._has(r)


def campaign(r):
    return bool(A.CAMPAIGN.match(str(r.get('doc') or '').strip()))


def cnp_release():
    """CNP release certificates in the page-text cache: normalised lot → [(code, date, {row: value})]."""
    out = collections.defaultdict(list)
    rows = {'total_thc': '4', 'total_cbd': '5', 'total_cbn': '6'}
    for x in json.load(open(A.CACHE, encoding='utf-8')):
        m = x.get('meta') or {}
        if m.get('lab') != 'CNP' or m.get('test_type') != 'RELEASE':
            continue
        vals = {}
        for key, pat in A.CNP_LINES.items():
            hit = re.search(pat, x.get('text') or '')
            if hit:
                vals[rows[key]] = re.sub(r'\s*%$', '', hit.group(1).strip())
        out[A.N(m.get('batch_canonical'))].append((m.get('cert_code'), m.get('date_of_issue'), vals))
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--reg', default=REG)
    ap.add_argument('--outdir', default=HERE)
    a = ap.parse_args(argv[1:])
    if not (a.apply or a.check):
        ap.error('pass --check or --apply')

    reg = json.load(open(a.reg, encoding='utf-8'))
    tm = A.tranche_map()

    def tranche(c):
        for k in (c.get('pp'), c.get('cb'), (c.get('cb') or '').replace('＊', '')):
            if k and k in tm:
                return tm[k]

    lot = lambda c: (str(c.get('pp') or ''), str(c.get('cb') or ''))
    recs = [c for c in reg['coqs'] if tranche(c) == 'T3']            # T1 and T2: never (A.FROZEN)
    ini = {lot(c): c for c in recs if 'retest' not in c['t']}
    ret = {lot(c): c for c in recs if 'retest' in c['t']}
    cnp = cnp_release()
    log = collections.defaultdict(list)
    for k in sorted(ini, key=lambda k: ini[k]['regcode']):
        c, r, t = ini[k], ret.get(k), tranche(ini[k])
        rows = {x['no']: x for x in c['rows']}
        twin = {x['no']: x for x in (r or {}).get('rows', [])}
        rel_k, rel_m = A.release_family(c)
        keys = {A.N(c.get('pp')), A.N(c.get('cb'))} - {''}
        for no, row in rows.items():
            fam = 'K' if no in A.K_ROWS else 'M' if no in A.M_ROWS else None
            src = twin.get(no) or {}
            if (c['regcode'], no) in HELD:
                row.update({'res': '—', 'doc': '—', 'dd': '', 'st': HELD[(c['regcode'], no)]})
                log['held for the Head of QC'].append((t, c['regcode'], no))
                continue
            if fam and not (rel_k if fam == 'K' else rel_m):
                # the campaign is this lot's first testing of the family: its release testing
                if has(src) and campaign(src) and 'carried' not in str(src.get('st')):
                    if row.get('doc') != src.get('doc') or not has(row):
                        log['first testing printed on the initial (%s)' % fam].append((t, c['regcode'], no, src['doc']))
                    for f in ('res', 'doc', 'dd', 'lab', 'fam', 'route'):
                        if f in src:
                            row[f] = src[f]
                    row['st'] = FIRST % (src['doc'], src['dd'])
                continue
            if str(row.get('st') or '').startswith('awaiting'):
                continue                      # held for the Head of QC's ruling, or a missing page
            if fam == 'K' and (campaign(row) or not has(row)) and has(src) and campaign(src):
                # tested at release: the campaign value is the retest's; the release certificate's own
                # value, where it reports one, is the release result
                rel = next(((code, date, v[no]) for key in keys for code, date, v in cnp.get(key, [])
                            if no in v and any(x.get('doc') == code for x in c['rows'])), None)
                if rel:
                    like = next(x for x in c['rows'] if x.get('doc') == rel[0])
                    row.update({'res': rel[2], 'doc': rel[0], 'dd': rel[1], 'st': RELEASE_CNP % rel[0]})
                    for f in ('lab', 'fam', 'route'):
                        if f in like:
                            row[f] = like[f]
                    log['release value from CNP, in place of the retest value'].append((t, c['regcode'], no, rel[0], rel[2]))
                else:
                    if campaign(row):
                        log['retest value taken off the initial'].append((t, c['regcode'], no, row.get('doc')))
                    rdocs = sorted({x.get('doc') for x in c['rows'] if x['no'] in ('4', '5', '6') and has(x)
                                    and not campaign(x)}) or ['none printed']
                    row.update({'res': '—', 'doc': '—', 'dd': '',
                                'st': NOT_AT_RELEASE % (', '.join(rdocs), src['doc'], src['dd'], r['regcode'])})
                continue
            if fam == 'M' and c['regcode'] in PANEL_TOTAL and no == '10.2' and not has(row):
                res, doc, dd, st = PANEL_TOTAL[c['regcode']]
                like = rows['10.1']
                row.update({'res': res, 'doc': doc, 'dd': dd, 'st': st})
                for f in ('lab', 'fam', 'route'):
                    if f in like:
                        row[f] = like[f]
                log['total aflatoxins from the release panel'].append((t, c['regcode'], doc))
                continue
            if fam is None and has(row) and str(row.get('st', '')).startswith('covered — measured in the retest campaign'):
                row['st'] = FIRST % (row.get('doc'), row.get('dd'))       # first value of the parameter

        if r:
            # no reissuance: the campaign was the lot's first testing, and the retest adds nothing
            if not A.release_family(c)[0] and not A.release_family(c)[1]:
                extra = [x['no'] for x in r['rows'] if has(x) and x['no'] not in ('1', '2', '7')
                         and 'carried' not in str(x.get('st')) and x.get('doc') != rows[x['no']].get('doc')]
                if not extra:
                    if t in A.RETEST_WITH_CUSTOMER:
                        log['with the customer, but by the rule the lot has no reissue'].append((t, r['regcode'], c['regcode']))
                    elif not r.get('withdrawn'):
                        r['withdrawn'] = WITHDRAWN % c['regcode']
                        log['Tranche 3 retest withdrawn — no reissuance'].append((t, r['regcode'], r.get('icoa_code'), c['regcode']))
        # the date: seven days after the last external certificate cited, never before its own date
        base = c.get('issue_before_redating') or c.get('issue')
        c.pop('issue_before_redating', None)
        c['issue'] = base
        new = A.initial_issue(c, r)
        if new != base:
            c['issue_before_redating'] = base
            c['issue'] = new
            log['initial dated seven days after its last external certificate'].append((t, c['regcode'], base, new))
        for x in c['rows']:
            if A.dt(x.get('dd')) and A.dt(x['dd']) > A.dt(c['issue']):
                raise SystemExit('%s row %s: cites %s of %s, after the certificate' % (c['regcode'], x['no'], x['doc'], x['dd']))

        if not r:
            continue
        # a kept reissue carries the release testing it did not repeat: on -160 (P060342) the
        # cannabinoids and mycotoxins are -073's Farmahem release results, and only the microbiology is
        # the retest — "the second certificate for microbiology is going to enter the CoQ, and if the
        # initial testing was way before, then it is definitely a retest and the reissuing of the CoQ"
        if not r.get('withdrawn'):
            for x in r['rows']:
                if x['no'] in A.K_ROWS + A.M_ROWS and has(x) and x.get('doc') == rows[x['no']].get('doc') \
                        and not str(x.get('st') or '').startswith('carried') \
                        and not (rel_k if x['no'] in A.K_ROWS else rel_m):
                    x['st'] = 'carried from the initial testing (%s) — covered' % c['regcode']
                    log['reissue carries the release testing it did not repeat'].append((t, r['regcode'], x['no'], x['doc']))
        s = r.get('supersedes') or {}
        if s.get('code') == c['regcode'] and s.get('date') != c['issue']:
            if t in A.RETEST_WITH_CUSTOMER:
                log['customer\'s retest names the initial with another date'].append((t, r['regcode'], c['regcode'], s.get('date'), c['issue']))
            else:
                s['date'] = c['issue']

    for k, v in log.items():
        print('%-66s %d' % (k, len(v)))
        for x in v[:40]:
            print('     ', ' '.join(map(str, x)))
    if a.check:
        print('--check: nothing written')
        return 0

    with open(a.reg, 'w', encoding='utf-8') as fh:
        json.dump(reg, fh, ensure_ascii=False, indent=1)

    # the laboratory requests, rebuilt from the register as it now stands
    for t in ('T3',):
        out = os.path.join(a.outdir, 'LAB_REQUESTS_%s_2026-09-26.tsv' % t)
        req = collections.OrderedDict()
        for c in sorted([c for c in recs if tranche(c) == t and not c.get('withdrawn')], key=lambda c: c['regcode']):
            for x in c['rows']:
                st = str(x.get('st') or '')
                if not (st.startswith('not tested — no certificate') or st.startswith('awaiting the complete scan')):
                    continue
                lab = ('IPH — the complete scan of 1065/2026 (page 3 of 4)' if st.startswith('awaiting') else
                       {'8': 'Farmahem (LoD, loss on drying)'}.get(x['no'], 'IPH contaminants (IJZ)'))
                key = (c.get('pp') or '', c.get('cb') or '', lab)
                req.setdefault(key, {'params': [], 'coqs': set()})
                if A.NAME.get(x['no']) not in req[key]['params']:
                    req[key]['params'].append(A.NAME.get(x['no'], x['no']))
                req[key]['coqs'].add(c['regcode'])
        with open(out, 'w', encoding='utf-8', newline='') as fh:
            w = csv.writer(fh, delimiter='\t')
            w.writerow(['p_lot', 'cultivation_batch', 'laboratory', 'parameters', 'certificates waiting on it'])
            for (pp, cb, lab), v in req.items():
                w.writerow([pp, cb, lab, ', '.join(v['params']), ' '.join(sorted(v['coqs']))])
        print('wrote %s (%d requests)' % (os.path.relpath(out, GAP), len(req)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
