#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P060332 (CC012601/1, also CC012601_01): IPH 3161/2026 and CNP ППК26092 put on CoQ-PP_26-068.

    python3 tracker/apply_p060332_iph3161_cnp26092_2026-11-02.py --check | --apply

Head of QC, 30.10.2026: the scans 20261030145948.pdf (IPH 3161/2026, 01.06.2026, 4 pp., letter 138/2026 — the sibling of
P060342's 3160/2026) and 20261030150013.pdf (CNP ППК26092, 05.06.2026) are the batch's missing release certificates.
"Only the LoD parameter result will be cited from the center of natural products": its Total THC (15.33 %) does not enter,
Farmahem 197-6-К/26 is the newer result. Mycotoxins stay on Farmahem 197-6-М/26 by the same rule (newer, full panel);
IPH's total aflatoxins (< 2 µg/kg) is kept in `also`. Read in `intake_P060332_2026-11-02/`.
"""
import argparse, json, os, sys
GAP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(GAP, 'coq_artifact_data.json')
CODE = 'CoQ-PP_26-068'
IPH = dict(doc='3161/2026', dd='01.06.2026', lab='IPH — Institute of Public Health', fam='', route='',
           st="covered — IPH 3161/2026, the lot's release testing (scan of 30.10.2026)")
CNP = dict(doc='ППК26092', dd='05.06.2026', lab='UKIM Faculty of Pharmacy — Center for Natural Products', fam='UKIM CNP potency',
           route='', st="covered — CNP ППК26092, loss on drying only (Head of QC, 30.10.2026)")
SET = {'8': dict(CNP, res='5.50'), '11.1': dict(IPH, res='0.006'), '11.2': dict(IPH, res='0.009'),
       '11.3': dict(IPH, res='0.006'), '11.4': dict(IPH, res='< 0.0008'),
       '12': dict(IPH, res='ND — all 29 residues')}
ALSO = {'4': 'CNP ППК26092 Total Δ9-THC 15.33 % — not cited, Farmahem 197-6-К/26 is newer (Head of QC, 30.10.2026)',
        '10.2': 'IPH 3161/2026 total aflatoxins < 2 µg/kg — not cited, Farmahem 197-6-М/26 is newer'}


def main(argv):
    ap = argparse.ArgumentParser(); ap.add_argument('--apply', action='store_true'); ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv[1:])
    raw = open(REG, encoding='utf-8').read(); reg = json.loads(raw)
    c = [x for x in reg['coqs'] if x['regcode'][:13] == CODE][0]
    if c['pp'] != 'P060332':
        raise SystemExit('%s is not P060332' % CODE)
    for r in c['rows']:
        if r['no'] in SET:
            print(r['no'], r.get('res'), '->', SET[r['no']]['res'], SET[r['no']]['doc']); r.update(SET[r['no']])
        if r['no'] in ALSO and ALSO[r['no']] not in (r.get('also') or ''):
            r['also'] = '; '.join(x for x in (r.get('also'), ALSO[r['no']]) if x)
    if a.apply:
        indent = 1 if raw.startswith('{\n ') and not raw.startswith('{\n  ') else 2
        open(REG, 'w', encoding='utf-8').write(json.dumps(reg, ensure_ascii=False, indent=indent) + ('\n' if raw.endswith('\n') else ''))
        print('wrote the register')


if __name__ == '__main__':
    sys.exit(main(sys.argv))
