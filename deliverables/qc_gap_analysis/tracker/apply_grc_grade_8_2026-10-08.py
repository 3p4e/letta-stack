#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Grapes and Cream: the 7.00 ± 0.70 grade becomes 8.00 ± 0.80 (Head of QC, 08.10.2026).

    python3 tracker/apply_grc_grade_8_2026-10-08.py --check
    python3 tracker/apply_grc_grade_8_2026-10-08.py --apply

Head of QC, 08.10.2026: *"i have made a change that i want you to implement into the specification for grapes and
cream grade 7.00% into 8.00% +-0.8%, so make the changes to the Spec and corresponding coq and iCOA for the
corresponding batches"*. He saved it on the KVM4 potency builder the same morning (GRC: 8 ± 0.8, 10 ± 1, 12 ± 1;
updated 10:26 UTC). Asked about the initial CoQ-PP_26-050, whose release result is 7.05 % — below the new window
7.20–8.79 % — he chose: *both on 8.00 ± 0.80* (-050 and -152, and their iCoAs -050 and -095), -050 printing its
7.05 % below the window.

The grade keeps its code, QCSP_001_GRC-IV_v.01 (a code on certificates never moves; numerals say nothing about
potency). What changes:

* `potency_grades_2026-09-15.csv`, the GRC IV row: nominal 8.00, tolerance 0.80, window 7.20–8.79.
* `coq_artifact_data.json`, CoQ-PP_26-050 and -152: product code `GRC_THC8 : CBD1`, row 4's criterion
  `7.20 – 8.79 %  (grade IV, nominal 8.00 ± 0.80)`, the nominal class 8, and the specification note.

Nothing else: results, certificates, dates and every other record are as they were. The script refuses to run on
anything but the 7.00 grade it replaces, so a second run changes nothing.
"""
import argparse
import csv
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
GRADES = os.path.join(GAP, 'potency_grades_2026-09-15.csv')
REG = os.path.join(GAP, 'coq_artifact_data.json')
CODES = ('CoQ-PP_26-050', 'CoQ-PP_26-152')
OLD = {'pcode': 'GRC_THC7 : CBD1', 'crit': '6.30 – 7.69 %  (grade IV, nominal 7.00 ± 0.70)', 'cls': 7}
NEW = {'pcode': 'GRC_THC8 : CBD1', 'crit': '7.20 – 8.79 %  (grade IV, nominal 8.00 ± 0.80)', 'cls': 8}
NOTE = ('for review — replaces the issued QCSP_001_GRC-IV_v.01 (was GRC_THC12.5:CBD1, 12.50% ± 2.50%); now '
        'GRC_THC8 : CBD1 7.20 – 8.79 % (8.00 ± 0.80, Head of QC 08.10.2026, KVM4)')


def grades(apply):
    text = open(GRADES, encoding='utf-8').read()
    rows = list(csv.reader(io.StringIO(text)))
    head = rows[0]
    i = {k: head.index(k) for k in ('abbr', 'numeral', 'nominal', 'tolerance', 'window_low', 'window_high')}
    hit = [r for r in rows[1:] if r[i['abbr']] == 'GRC' and r[i['numeral']] == 'IV']
    if len(hit) != 1:
        raise SystemExit('expected one GRC IV row, found %d' % len(hit))
    r = hit[0]
    now = (r[i['nominal']], r[i['tolerance']], r[i['window_low']], r[i['window_high']])
    if now == ('8.00', '0.80', '7.20', '8.79'):
        print('grade table: GRC IV is already 8.00 ± 0.80')
        return
    if now != ('7.00', '0.70', '6.30', '7.69'):
        raise SystemExit('GRC IV is %s, not the 7.00 ± 0.70 this replaces' % (now,))
    r[i['nominal']], r[i['tolerance']], r[i['window_low']], r[i['window_high']] = '8.00', '0.80', '7.20', '8.79'
    print('grade table: GRC IV 7.00 ± 0.70 (6.30–7.69) → 8.00 ± 0.80 (7.20–8.79)')
    if apply:
        out = io.StringIO()
        csv.writer(out, lineterminator='\n').writerows(rows)
        open(GRADES, 'w', encoding='utf-8').write(out.getvalue())


def register(apply):
    raw = open(REG, encoding='utf-8').read()
    reg = json.loads(raw)
    recs = [c for c in reg['coqs'] if c['regcode'][:13] in CODES]
    if sorted(c['regcode'][:13] for c in recs) != list(CODES):
        raise SystemExit('expected exactly %s in the register' % ', '.join(CODES))
    changed = 0
    for c in recs:
        r4 = next(r for r in c['rows'] if r['no'] == '4')
        if (c['pcode'], r4['crit'], c.get('cls')) == (NEW['pcode'], NEW['crit'], NEW['cls']):
            print('%s: already on 8.00 ± 0.80' % c['regcode'][:13])
            continue
        if (c['pcode'], r4['crit'], c.get('cls')) != (OLD['pcode'], OLD['crit'], OLD['cls']):
            raise SystemExit('%s holds %r / %r / %r, not the 7.00 grade this replaces'
                             % (c['regcode'][:13], c['pcode'], r4['crit'], c.get('cls')))
        if c.get('spec') != 'QCSP_001_GRC-IV_v.01':
            raise SystemExit('%s cites %s' % (c['regcode'][:13], c.get('spec')))
        c['pcode'], r4['crit'], c['cls'], c['spec_status'] = NEW['pcode'], NEW['crit'], NEW['cls'], NOTE
        changed += 1
        print('%s: %s, THC %s %% → GRC_THC8 : CBD1, 7.20 – 8.79 %%%s' % (
            c['regcode'][:13], c.get('t'), r4.get('res'),
            '' if 7.20 <= float(r4['res']) <= 8.79 else ' (the result is outside the window: the Head of QC\'s choice)'))
    if apply and changed:
        indent = 1 if raw.startswith('{\n ') and not raw.startswith('{\n  ') else 2
        open(REG, 'w', encoding='utf-8').write(json.dumps(reg, ensure_ascii=False, indent=indent) + ('\n' if raw.endswith('\n') else ''))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv[1:])
    if not (a.apply or a.check):
        ap.error('pass --check or --apply')
    grades(a.apply)
    register(a.apply)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
