#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Three IPH contaminant certificates taken in on 08.10.2026, onto the certificates of quality they belong to.

    python3 tracker/apply_iph_intake_2026-10-08.py --check
    python3 tracker/apply_iph_intake_2026-10-08.py --apply

Head of QC, 08.10.2026, on three certificates placed in the eCoA folder on Drive: *"P060342 (SCR012601＊)_IJZ_3160-
2026_01.06.2026.pdf (added, new to the database); P060162 (SJ102501)_IJZ_1065-2026_11.03.2026.pdf (replaced the
3-of-4-page copy); P060182 (GRC102501)_IJZ_328-2026_11.02.2026.pdf (pre-existing complete copy) … update the
corresponding certificates of quality … with the correct values and the correct external CoA document code, date of
issuing and the analysis covered"*. Each certificate was read twice from its page images, the two reads agreeing on
every value (`intake_IPH_2026-10-08/`).

* **IPH 1065/2026** (SLEEPY JOY, SJ102501 = P060162), 11.03.2026, now complete. Page 3, missing from every copy
  until now (ruling 8 of 26.09.2026), holds the metals, total aflatoxins and the last three pesticides.
  - The initial **CoQ-PP_26-052**: total aflatoxins 2.6 µg/kg (10.2); lead, cadmium, arsenic, mercury ND (11.1–11.4);
    pesticides ND, all 29 residues (12). B1 and OTA stay n/t (IPH reports the total only; ruling 3).
  - The retest **CoQ-PP_26-162**: 11.1–11.4 and 12, carried from -052. Its mycotoxins stay the Farmahem
    227-6-М/26 retest panel.
* **IPH 3160/2026** (SCRAMBLER, SCR012601* = P060342 in the owner's workbook), 01.06.2026, new.
  - The initial **CoQ-PP_26-073**:
    - Total aflatoxins < 2 µg/kg (10.2).
    - Lead 0.006, cadmium 0.007, arsenic 0.006, mercury 0.001 mg/kg (11.1–11.4).
    - Pesticides "0 mg/kg — all 29 residues" (12), as printed: the certificate prints the digit 0 for every
      residue, and an IPH result prints as the certificate prints it (3924/2026 on -081 prints its arsenic "0").
    - With an IPH total on record, ruling 3 applies: B1 and OTA are n/t on the initial, and the Farmahem panel
      227-8-М/26 becomes the retest's.
  - The retest **CoQ-PP_26-160**:
    - 10.1–10.3 from 227-8-М/26 as its own retest panel, no longer "carried".
    - 11.1–11.4 and 12 carried from -073.
* **IPH 328/2026** (GRAPS & CREME, GRC102501), 11.02.2026: both reads agree with what -050 prints (2.2; 0.084 / ND /
  0.095 / ND; 29 residues ND), and -152 carries its metals and pesticides from -050. Nothing changes.

Dates: an initial is dated seven days after the last external certificate it cites (`audit_empty_results.
initial_issue`), never after its retest. -073 no longer cites the 16.09 mycotoxin panel, so its date is recomputed,
and -160's *supersedes* line follows. The two laboratory requests these certificates answer come off the list.
"""
import argparse
import collections
import csv
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
REG = os.path.join(GAP, 'coq_artifact_data.json')
REQ = os.path.join(HERE, 'LAB_REQUESTS_T3_2026-09-26.tsv')
IPH = 'IPH — Institute of Public Health'
STAMP = '08.10.2026'
NT_RELEASE = ("not tested at release — the IPH certificate reports total aflatoxins only; aflatoxin B1 and "
              "ochratoxin A are tested in the retest round, by Farmahem (Head of QC, 26.09.2026)")
CAMPAIGN_NOTE = 'covered — measured in the retest campaign'

# the two reads, agreed (intake_IPH_2026-10-08/two_reads.tsv)
CERTS = {
    '1065/2026': {'dd': '11.03.2026', 'lot': ('P060162', 'SJ102501'), 'initial': 'CoQ-PP_26-052', 'retest': 'CoQ-PP_26-162',
                  'note': 'covered — IPH 1065/2026 complete (page 3 of 4 received %s)' % STAMP,
                  'rows': {'10.2': '2.6', '11.1': 'ND', '11.2': 'ND', '11.3': 'ND', '11.4': 'ND',
                           '12': 'ND mg/kg — all 29 residues'}},
    '3160/2026': {'dd': '01.06.2026', 'lot': ('P060342', 'SCR012601'), 'initial': 'CoQ-PP_26-073', 'retest': 'CoQ-PP_26-160',
                  'note': 'covered — IPH 3160/2026, the lot\'s release testing (received %s)' % STAMP,
                  'rows': {'10.2': '< 2', '11.1': '0.006', '11.2': '0.007', '11.3': '0.006', '11.4': '0.001',
                           '12': '0 mg/kg — all 29 residues'}},
}
CHECK_ONLY = {'328/2026': {'CoQ-PP_26-050': {'10.2': '2.2', '11.1': '0.084', '11.2': 'ND', '11.3': '0.095', '11.4': 'ND',
                                             '12': 'ND mg/kg — all 29 residues'}}}


def load_audit():
    spec = importlib.util.spec_from_file_location('A', os.path.join(HERE, 'audit_empty_results.py'))
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    return A


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv[1:])
    if not (a.apply or a.check):
        ap.error('pass --check or --apply')
    A = load_audit()
    raw = open(REG, encoding='utf-8').read()
    reg = json.loads(raw)
    by = {c['regcode'][:13]: c for c in reg['coqs']}
    rows = lambda code: {r['no']: r for r in by[code]['rows']}
    log = collections.defaultdict(list)

    for code, want in CHECK_ONLY['328/2026'].items():
        got = rows(code)
        bad = [(no, got[no]['res'], v) for no, v in want.items() if str(got[no]['res']) != v or got[no]['doc'] != '328/2026']
        if bad:
            raise SystemExit('%s does not print 328/2026 as read: %s' % (code, bad))
    log['IPH 328/2026: -050 prints it as read (-152 carries 11 and 12 from it), unchanged'].append(('CoQ-PP_26-050',))

    for cert, x in sorted(CERTS.items()):
        ini, ret = by[x['initial']], by[x['retest']]
        if (ini.get('pp'), ini.get('cb')) != x['lot'] or (ret.get('pp'), ret.get('cb')) != x['lot']:
            raise SystemExit('%s: %s/%s are not lot %s' % (cert, x['initial'], x['retest'], x['lot']))
        if (ret.get('supersedes') or {}).get('code') != x['initial'] or 'retest' not in ret['t']:
            raise SystemExit('%s is not the retest of %s' % (x['retest'], x['initial']))
        ri, rr = rows(x['initial']), rows(x['retest'])
        for no, val in x['rows'].items():
            r = ri[no]
            if str(r.get('res')) == val and r.get('doc') == cert:
                continue
            if str(r.get('res')).strip() not in ('—', '') and r.get('doc') != '—' and not str(r.get('doc')).startswith('227-'):
                raise SystemExit('%s row %s already prints %r from %s' % (x['initial'], no, r.get('res'), r.get('doc')))
            log['%s → %s (initial)' % (cert, x['initial'])].append((no, r.get('res'), r.get('doc'), '→', val))
            r.update({'res': val, 'doc': cert, 'lab': IPH, 'dd': x['dd'], 'st': x['note']})
        # B1 and OTA: not tested at release where IPH tested the total (ruling 3)
        for no in ('10.1', '10.3'):
            r = ri[no]
            if r.get('doc') != '—' or r.get('st') != NT_RELEASE:
                log['%s: B1/OTA n/t at release (ruling 3)' % x['initial']].append((no, r.get('res'), r.get('doc')))
                r.update({'res': '—', 'doc': '—', 'dd': '', 'st': NT_RELEASE})
        # the retest: metals and pesticides carried from the initial; mycotoxins its own Farmahem panel
        carried = 'carried from the initial testing (%s) — covered' % x['initial']
        for no in ('11.1', '11.2', '11.3', '11.4', '12'):
            r, s = rr[no], ri[no]
            if (r.get('res'), r.get('doc'), r.get('st')) != (s['res'], cert, carried):
                log['%s → %s (retest, carried)' % (cert, x['retest'])].append((no, r.get('res'), r.get('doc'), '→', s['res']))
                r.update({'res': s['res'], 'doc': cert, 'lab': IPH, 'dd': x['dd'], 'st': carried})
        for no in ('10.1', '10.2', '10.3'):
            r = rr[no]
            if not A.CAMPAIGN.match(str(r.get('doc') or '')):
                raise SystemExit('%s row %s: the retest mycotoxins are not a Farmahem panel (%s)' % (x['retest'], no, r.get('doc')))
            if str(r.get('st') or '').startswith('carried'):
                log['%s: mycotoxins are its own retest panel' % x['retest']].append((no, r['doc']))
                r['st'] = CAMPAIGN_NOTE
        # the date of the initial, and the retest's supersedes line
        base = ini.get('issue_before_redating') or ini.get('issue')
        probe = dict(ini, issue=base)
        probe.pop('issue_before_redating', None)
        new = A.initial_issue(probe, ret)
        if new != ini.get('issue'):
            log['%s re-dated (seven days after its last external certificate)' % x['initial']].append((ini.get('issue'), '→', new))
            if new != base:
                ini['issue_before_redating'] = base
            else:
                ini.pop('issue_before_redating', None)
            ini['issue'] = new
        for r in ini['rows']:
            if A.dt(r.get('dd')) and A.dt(r['dd']) > A.dt(ini['issue']):
                raise SystemExit('%s row %s: %s of %s is after the certificate' % (x['initial'], r['no'], r['doc'], r['dd']))
        s = ret['supersedes']
        if s.get('date') != ini['issue']:
            log['%s supersedes %s of %s' % (x['retest'], x['initial'], ini['issue'])].append((s.get('date'), '→', ini['issue']))
            s['date'] = ini['issue']
        if ini.get('last_external') is not None:
            ext = max((A.dt(r['dd']), r['dd']) for r in ini['rows'] if A.dt(r.get('dd'))
                      and not str(r.get('doc')).startswith('iCoA'))[1]
            if ext != ini['last_external']:
                log['%s last external certificate' % x['initial']].append((ini['last_external'], '→', ext))
                ini['last_external'] = ext

    for k, v in log.items():
        print('%-70s %d' % (k, len(v)))
        for e in v:
            print('     ', ' '.join(map(str, e)))
    if not a.apply:
        print('--check: nothing written')
        return 0
    indent = 1 if raw.startswith('{\n ') and not raw.startswith('{\n  ') else 2
    open(REG, 'w', encoding='utf-8').write(json.dumps(reg, ensure_ascii=False, indent=indent) + ('\n' if raw.endswith('\n') else ''))

    # the laboratory requests: those this intake answers come off the list
    old = list(csv.reader(open(REQ, encoding='utf-8'), delimiter='\t'))
    keep = [old[0]] + [r for r in old[1:] if not (r[0] == 'P060162' and '1065/2026' in r[2])
                       and not (r[0] == 'P060342' and r[2].startswith('IPH'))]
    with open(REQ, 'w', encoding='utf-8', newline='') as fh:
        csv.writer(fh, delimiter='\t').writerows(keep)
    print('wrote the register and %s (%d requests; %d answered by this intake)'
          % (os.path.relpath(REQ, GAP), len(keep) - 1, len(old) - len(keep)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
