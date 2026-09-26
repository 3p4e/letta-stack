#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tranche 3 — which laboratory each result comes from. The Head of QC, 26.09.2026 (second ruling).

    python3 tracker/apply_t3_source_rulings_2026-09-26.py --check     # writes nothing
    python3 tracker/apply_t3_source_rulings_2026-09-26.py --apply

His words, taken point by point:

* **Mycotoxins, initial CoQ.** *"It is very much possible for Tranche 3 initial that ... aflatoxin B1
  and OTA are not tested, yes — but that means total aflatoxins are tested, and a result from Public
  Health needs to be available for that."* So on an initial certificate B1 and ochratoxin A print
  `n/t` (not tested at release — the IPH AflaTest reports the total only), and total aflatoxins must
  come from **IPH**. The Farmahem campaign value that ruling 1 of this morning carried onto the initial
  is taken off again.
* **Mycotoxins, retest CoQ.** *"For the retest of Tranche 3 all three parameters for mycotoxins are
  tested, in Farmahem."* Unchanged — they already are.
* **Heavy metals** *"are tested almost exclusively in the Institute of Public Health, and a result for
  those should be present for the initial and the retest series."* Searched in the eCoA database, the
  repository and the whole of Drive. For SJ102501 the IPH certificate exists — `1065/2026` of
  11.03.2026 — but every copy of its scan holds pages 1, 2 and 4 of 4; page 3, which prints the heavy
  metals, total aflatoxins and the last three pesticides, is not in the file. Those cells print
  `[pending]` until the complete scan arrives. For P050142, P060142, P060332 and P060342 no IPH
  certificate exists anywhere; they stay `n/t` and on the laboratory request list.
* **Identification A, identification B, foreign matter.** *"If there is no external certificate of
  analysis from the Center of Natural Products explicitly testing identification A (macroscopy),
  identification B (microscopy) and foreign matter, you will use the internal certificate of analysis
  for these three parameters."* So a CNP (`ППК`) certificate for the same lot that explicitly reports
  them is cited instead of the internal certificate: `ППК26112` for FB012603 (`CoQ-PP_26-079`) and
  `ППК26110` for FB012603V (`CoQ-PP_26-075`), both of 30.06.2026. Every other certificate keeps its
  internal certificate for rows 1, 2 and 7.

After the mycotoxin values come off, each initial certificate's date is recomputed: on or after the
last result it still cites from a later campaign, or back to its own date where none remains. The
retest that supersedes it names that date, so the retest's `supersedes` line moves with it.

The same rulings hold in every tranche (`--tranche T1`, `--tranche T2`), with one difference: the
Tranche 1 and 2 retests are with the customer and name their initial's date, so a Tranche 1 or 2
initial is never re-dated — the run stops if it would be.
"""
import argparse
import collections
import csv
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(GAP))
sys.path.insert(0, HERE)
import audit_empty_results as A                                    # noqa: E402

REG = os.path.join(GAP, 'coq_artifact_data.json')
STAMP = '26.09.2026'
FARMAHEM_M = re.compile(r'^(197|220|227)-\d+-[МM]/26$')
CAMPAIGN_NOTE = 'covered — measured in the retest campaign'
PAGE3 = ("awaiting the complete scan of IPH 1065/2026 — every copy holds pages 1, 2 and 4 of 4; page 3 "
         "(heavy metals, total aflatoxins, the last three pesticides) is missing (Head of QC, %s)" % STAMP)
NT_RELEASE = ("not tested at release — the IPH certificate reports total aflatoxins only; aflatoxin B1 and "
              "ochratoxin A are tested in the retest round, by Farmahem (Head of QC, %s)" % STAMP)
NT_REQUEST = ("not tested — no certificate for this lot; requested from the laboratory "
              "(Head of QC, %s)" % STAMP)
CNP_KEYS = {'1': 'identification_a_macroscopic', '2': 'identification_b_microscopic', '7': 'foreign_matter'}


def dt(s):
    try:
        d, m, y = str(s).strip().split('.')
        return datetime.date(int(y), int(m), int(d))
    except Exception:
        return None


def ds(d):
    return '%02d.%02d.%04d' % (d.day, d.month, d.year)


def is_sj(c):
    return 'SJ102501' in str(c.get('cb') or '') or 'P060162' in str(c.get('pp') or '')


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--tranche', default='T3')
    ap.add_argument('--reg', default=REG, help='register to read and write (a scratch copy for a dry run)')
    ap.add_argument('--outdir', default=HERE, help='where the laboratory request list goes')
    a = ap.parse_args(argv[1:])
    if not (a.apply or a.check):
        ap.error('pass --check or --apply')

    if a.tranche in A.FROZEN:
        raise SystemExit('Tranche %s is issued and with the customer: not touched (Head of QC, 26.09.2026)' % a.tranche)
    reg = json.load(open(a.reg, encoding='utf-8'))
    tm = A.tranche_map()

    def tranche(c):
        for k in (c.get('pp'), c.get('cb'), (c.get('cb') or '').replace('＊', '')):
            if k and k in tm:
                return tm[k]

    t3 = [c for c in reg['coqs'] if tranche(c) == a.tranche]
    ini = [c for c in t3 if 'retest' not in c['t']]
    corpus = json.load(open(os.path.join(ROOT, 'ingestion', 'ecoa_runner', 'records_corpus.json'), encoding='utf-8'))
    log = collections.defaultdict(list)

    # 1 · mycotoxins on the initial certificates — only where the release round tested the family:
    # where it did not, the Farmahem panel is the lot's release testing and stays (third ruling of
    # 26.09.2026, apply_first_testing_ruling_2026-09-26.py)
    for c in ini:
        rows = {r['no']: r for r in c['rows']}
        if not A.release_family(c)[1]:
            continue
        for no in ('10.1', '10.3'):
            r = rows[no]
            if FARMAHEM_M.match(str(r.get('doc') or '')):
                log['B1/OTA taken off the initial'].append((c['regcode'], no, r['doc']))
                r.update({'res': '—', 'doc': '—', 'dd': '', 'st': NT_RELEASE})
            elif str(r.get('res')).strip() in ('—', '', 'None'):
                r['st'] = NT_RELEASE
        r = rows['10.2']
        if FARMAHEM_M.match(str(r.get('doc') or '')):
            log['total aflatoxins taken off (Farmahem, not IPH)'].append((c['regcode'], r['doc']))
            r.update({'res': '—', 'doc': '—', 'dd': ''})
            r['st'] = PAGE3 if is_sj(c) else NT_REQUEST

    # 2 · SJ102501: the IPH certificate exists, its page 3 does not
    for c in t3:
        if not is_sj(c):
            continue
        for r in c['rows']:
            if r['no'] in ('11.1', '11.2', '11.3', '11.4') or (r['no'] == '10.2' and 'retest' not in c['t']):
                if r.get('res') in ('—', '') or str(r.get('st', '')).startswith('not tested'):
                    r.update({'res': '—', 'doc': '—', 'st': PAGE3})
                    log['SJ102501 awaiting page 3 of 1065/2026'].append((c['regcode'], r['no']))
            if r['no'] == '12' and '1065/2026' in str(r.get('doc')) and 'retest' not in c['t']:
                r.update({'res': '—', 'st': PAGE3})
                log['SJ102501 awaiting page 3 of 1065/2026'].append((c['regcode'], '12 (three pesticides on page 3)'))

    # 3 · identification A, B and foreign matter from a CNP certificate that tests them explicitly.
    # The corpus lacks many ППК certificates (ППК26116 for SCR022601, 06.07.2026, among them), so the
    # CNP release certificates in the RAGflow page-text cache are read too.
    cnp_recs = [r for r in corpus if str(r.get('cert_code') or '').startswith('ППК')]
    have = {r.get('cert_code') for r in cnp_recs}
    for x in json.load(open(A.CACHE, encoding='utf-8')):
        m = x.get('meta') or {}
        if m.get('lab') != 'CNP' or m.get('test_type') != 'RELEASE' or m.get('cert_code') in have:
            continue
        t = x.get('text') or ''
        params = []
        for key, word in (('identification_a_macroscopic', 'Макроскопија'), ('identification_b_microscopic', 'Микроскопија'),
                          ('foreign_matter', 'Страни материи')):
            hit = re.search(word + r'\s*\|[^|\n]*\|\s*([^|\n]+)', t)
            if hit:
                params.append({'parameter': key, 'result_printed': hit.group(1).strip()})
        if params:
            cnp_recs.append({'cert_code': m.get('cert_code'), 'batch_canonical': m.get('batch_canonical'),
                             'p_number': None, 'date_of_issue': m.get('date_of_issue'), 'parameters': params})
    for c in ini:
        ids = {A.N(c.get('pp')), A.N(c.get('cb'))} - {''}
        rows = {r['no']: r for r in c['rows']}
        for rec in cnp_recs:
            code = str(rec.get('cert_code') or '')
            if not code.startswith('ППК') or not ({A.N(rec.get('batch_canonical')), A.N(rec.get('p_number'))} & ids):
                continue
            vals = {p['parameter']: p.get('result_printed') for p in rec.get('parameters', [])}
            src = next((r for r in c['rows'] if r.get('doc') == code), None)
            for no, key in CNP_KEYS.items():
                if key not in vals or 'одговара' not in str(vals[key]).lower():
                    continue
                r = rows[no]
                if r.get('doc') == code:
                    continue
                log['rows 1, 2, 7 from CNP'].append((c['regcode'], no, r.get('doc'), code))
                r.update({'res': 'Conforms | Одговара', 'doc': code, 'dd': rec.get('date_of_issue'),
                          'st': 'covered — tested explicitly by CNP, %s (Head of QC, %s)' % (code, STAMP)})
                for f in ('lab', 'fam', 'route'):
                    if src and f in src:
                        r[f] = src[f]

    # 4 · date each initial by the standing rule (audit_empty_results.initial_issue): seven days after
    # the last external certificate it cites, never after its own retest
    for c in ini:
        rt = next((r for r in t3 if 'retest' in r['t'] and (r.get('supersedes') or {}).get('code') == c['regcode']), None)
        base = c.get('issue_before_redating') or c.get('issue')
        c.pop('issue_before_redating', None)
        c['issue'] = base
        new = A.initial_issue(c, rt)
        if new != base:
            c['issue_before_redating'] = base
            c['issue'] = new
            log['initial CoQ dated after its last certificate'].append((c['regcode'], base, new))
        s = (rt or {}).get('supersedes') or {}
        if rt and s.get('date') != c['issue']:
            if a.tranche in A.RETEST_WITH_CUSTOMER:     # the customer's document: listed, never changed
                log["customer's retest names the initial with another date"].append(
                    (rt['regcode'], c['regcode'], s.get('date'), c['issue']))
            else:
                log['retest supersedes line re-dated'].append((rt['regcode'], c['regcode'], s.get('date'), c['issue']))
                s['date'] = c['issue']
        for r in c['rows']:
            if dt(r.get('dd')) and dt(r['dd']) > dt(c['issue']):
                raise SystemExit('%s row %s: cites %s of %s, after the certificate'
                                 % (c['regcode'], r['no'], r.get('doc'), r['dd']))

    for k, v in log.items():
        print('%-48s %d' % (k, len(v)))
        for x in v[:6]:
            print('     ', ' '.join(map(str, x)))
    if a.check:
        print('--check: nothing written')
        return 0

    with open(a.reg, 'w', encoding='utf-8') as fh:
        json.dump(reg, fh, ensure_ascii=False, indent=1)

    # the laboratory requests, rebuilt from the register as it now stands
    out = os.path.join(a.outdir, 'LAB_REQUESTS_%s_2026-09-26.tsv' % a.tranche)
    req = collections.OrderedDict()
    for c in sorted([c for c in t3 if not c.get('withdrawn')], key=lambda c: c['regcode']):   # a withdrawn retest waits on nothing
        for r in c['rows']:
            st = str(r.get('st') or '')
            if st.startswith('not tested — no certificate') or st.startswith('awaiting the complete scan'):
                if st.startswith('awaiting'):
                    lab = 'IPH — the complete scan of 1065/2026 (page 3 of 4)'
                else:
                    lab = {'8': 'Farmahem (LoD, loss on drying)', '10.1': 'Farmahem (М, mycotoxins)',
                           '10.3': 'Farmahem (М, mycotoxins)'}.get(r['no'], 'IPH contaminants (IJZ)')
                k = (c.get('pp') or '', c.get('cb') or '', lab)
                req.setdefault(k, {'params': [], 'coqs': set()})
                if A.NAME.get(r['no']) not in req[k]['params']:
                    req[k]['params'].append(A.NAME.get(r['no'], r['no']))
                req[k]['coqs'].add(c['regcode'])
    with open(out, 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh, delimiter='\t')
        w.writerow(['p_lot', 'cultivation_batch', 'laboratory', 'parameters', 'certificates waiting on it'])
        for (pp, cb, lab), v in req.items():
            w.writerow([pp, cb, lab, ', '.join(v['params']), ' '.join(sorted(v['coqs']))])
    print('wrote the register and %s (%d requests)' % (os.path.relpath(out, GAP), len(req)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))

# Applied by hand after the run, in the same change: CoQ-PP_26-149 (P050202) was the one Tranche 3
# retest whose total aflatoxins still came from IPH (4762/2025, carried from the initial). Its own
# Farmahem certificate 227-18-М/26 prints B1, B2, G1 and G2 ND — the basis on which the other thirty
# retests print ND — so row 10.2 now cites it.
