#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Loss on drying for P050202 (ППК25312) and P060342 (ППК26093), the two CNP certificates filed on 14.10.2026.

    python3 tracker/apply_cnp_lod_p050202_p060342_2026-10-16.py --check
    python3 tracker/apply_cnp_lod_p050202_p060342_2026-10-16.py --apply

Head of QC, 13.10.2026: *"P060342 LOD and correct the false value for LOD from the last created COQ"* and *"P050202 LOD
check eCOA and correct the false value for LOD from the last created COQ ППК25312"*; asked, he would upload both and
have them read twice and printed on the lot's initial and its retest (14.10.2026). Both were filed in eCoA_DATABASE on
14.10.2026. Two reads — the Drive text of each scan and the rendered page image — agree:

* **ППК25312** — GP062501 (P050202), issued 13.10.2025, testing completed 10.10.2025: loss on drying **6.21 %**
  (DAB 2018). -026 printed 8.19 % credited to its in-house iCoA ("avg of 4 weighings"), the New Garden Pharma figure;
  -149 carried it.
* **ППК26093** — SCR012601* (P060342), issued 05.06.2026, testing completed 03.06.2026: loss on drying **6.61 %**
  (Ph. Eur. 2.2.32). -073 and -160 printed n/t.

The initial prints the CNP result, the retest carries it with its original citation. Nothing else on the four
certificates changes here: both certificates also report cannabinoids, which is the Head of QC's to rule on.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
REG = os.path.join(GAP, 'coq_artifact_data.json')
STAMP = '16.10.2026'
LAB, FAM = 'UKIM Faculty of Pharmacy — Center for Natural Products', 'UKIM CNP potency'
LOTS = (('CoQ-PP_26-026', 'CoQ-PP_26-149', 'P050202', '6.21', 'ППК25312', '13.10.2025'),
        ('CoQ-PP_26-073', 'CoQ-PP_26-160', 'P060342', '6.61', 'ППК26093', '05.06.2026'))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv[1:])
    if not (a.apply or a.check):
        ap.error('pass --check or --apply')
    raw = open(REG, encoding='utf-8').read()
    reg = json.loads(raw)
    by = {c['regcode'][:13]: c for c in reg['coqs']}
    for ini, ret, pp, val, cert, dd in LOTS:
        i, r = by[ini], by[ret]
        if i['pp'] != pp or r['pp'] != pp or (r.get('supersedes') or {}).get('code') != ini:
            raise SystemExit('%s/%s are not lot %s' % (ini, ret, pp))
        ri = {x['no']: x for x in i['rows']}['8']
        rr = {x['no']: x for x in r['rows']}['8']
        was = '%s (%s)' % (ri.get('res'), ri.get('doc'))
        print('%s row 8: %s → %s %% %s (%s)' % (ini, was, val, cert, dd))
        ri.update({'res': val, 'doc': cert, 'dd': dd, 'lab': LAB, 'fam': FAM, 'route': '',
                   'st': 'covered — CNP %s, filed 14.10.2026, two reads (Head of QC, %s)' % (cert, STAMP),
                   'also': 'replaces %s' % was if ri.get('doc') not in ('—', '', None) else ''})
        print('%s row 8: %s (%s) → carried %s %% %s' % (ret, rr.get('res'), rr.get('doc'), val, cert))
        rr.update({'res': val, 'doc': cert, 'dd': dd, 'lab': LAB, 'fam': FAM, 'route': '', 'also': '',
                   'st': 'carried from the initial testing (%s) — covered' % ini})
    if not a.apply:
        print('--check: nothing written')
        return 0
    indent = 1 if raw.startswith('{\n ') and not raw.startswith('{\n  ') else 2
    open(REG, 'w', encoding='utf-8').write(json.dumps(reg, ensure_ascii=False, indent=indent) + ('\n' if raw.endswith('\n') else ''))
    print('wrote the register')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
