#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The initial CoQ of P050202 and of P060342 cites CNP's cannabinoid release testing; the later Farmahem result is the
retest, on the reissue.

    python3 tracker/apply_cnp_initial_cannabinoids_2026-10-22.py --check
    python3 tracker/apply_cnp_initial_cannabinoids_2026-10-22.py --apply
    python3 apply_potency_grades.py          # then: the grade follows the printed Total THC

Head of QC, 22.10.2026: *"For -026 and -073 if those are initial and retest certificates of quality of one same batch
then the certificate of quality that is from an earlier date should be citing the center of natural products cannabinoid
analysis results and if there is a retest parameter from a later date then that particular bit needs to get a new
certificate of quality reissued containing the retested parameters and as well as the other parameters that are required
by the products specification"* — one result per parameter (#226).

Two reads of each certificate agree (`intake_CNP_LoD_2026-10-16/two_reads.tsv`, cannabinoid rows added 22.10.2026: the
eCOA_INGEST page text and the page image):

* **ППК25312** — GP062501 (P050202), 13.10.2025: Total Δ9-THC 22.89 %, Total CBD 0.05 %, CBN 0.03 %. -026 printed New
  Garden Pharma's 24.89 / 0.17 % (28.11.2025) and CBN `[pending]`. NGP's test is neither the earlier release testing nor
  the retest, so it leaves the CoQ. -149 keeps its retest, Farmahem 227-18-К/26.
* **ППК26093** — SCR012601* (P060342), 05.06.2026: Total Δ9-THC 16.99 %, Total CBD 0.05 %, CBN BLQ (printed `< LOQ`, as the
  other CNP rows do). -073 printed Farmahem 227-8-К/26 (11.09.2026) as its release testing, the 26.09 rule for a lot with
  no CNP result on record; with ППК26093 on file 227-8-К/26 is the retest and stands on -160 alone. -073 is dated again
  by the standing rule (seven days after its last external certificate), and -160's supersedes line follows.

Identification C is discharged by the certificate that tested the cannabinoids and cites it (owner's ruling, 02.09.2026).
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
REG = os.path.join(GAP, 'coq_artifact_data.json')
STAMP = '22.10.2026'
LAB, FAM = 'UKIM Faculty of Pharmacy — Center for Natural Products', 'UKIM CNP potency'
# initial, retest, lot, CNP certificate, its date, THC, CBD, CBN
LOTS = (('CoQ-PP_26-026', 'CoQ-PP_26-149', 'P050202', 'ППК25312', '13.10.2025', '22.89', '0.05', '0.03'),
        ('CoQ-PP_26-073', 'CoQ-PP_26-160', 'P060342', 'ППК26093', '05.06.2026', '16.99', '0.05', '< LOQ'))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv[1:])
    if not (a.apply or a.check):
        ap.error('pass --check or --apply')
    sys.path.insert(0, HERE)
    import audit_empty_results as AE
    raw = open(REG, encoding='utf-8').read()
    reg = json.loads(raw)
    by = {c['regcode'][:13]: c for c in reg['coqs']}
    for ini, ret, pp, cert, dd, thc, cbd, cbn in LOTS:
        i, r = by[ini], by[ret]
        if i['pp'] != pp or r['pp'] != pp or (r.get('supersedes') or {}).get('code') != ini:
            raise SystemExit('%s/%s are not lot %s' % (ini, ret, pp))
        if {x['no']: x for x in i['rows']}['8'].get('doc') != cert:
            raise SystemExit('%s row 8 no longer cites %s' % (ini, cert))
        st = 'covered — CNP %s is the release testing of the cannabinoids (Head of QC, %s)' % (cert, STAMP)
        rows = {x['no']: x for x in i['rows']}
        for no, res in (('3', 'Conforms | Одговара'), ('4', thc), ('5', cbd), ('6', cbn)):
            x = rows[no]
            was = '%s (%s %s)' % (x.get('res'), x.get('doc'), x.get('dd'))
            print('%s row %s: %s -> %s (%s %s)' % (ini, no, was, res, cert, dd))
            x.update({'res': res, 'doc': cert, 'dd': dd, 'lab': LAB, 'fam': FAM, 'route': '', 'st': st,
                      'also': 'replaces %s' % was})
        i['thc'] = thc
        # the retest: the Farmahem cannabinoids are its own retest result, no longer carried from the initial
        for no in ('3', '4', '5', '6'):
            x = {y['no']: y for y in r['rows']}[no]
            if str(x.get('st', '')).startswith('carried from the initial'):
                x['st'] = 'covered — Farmahem retest %s (Head of QC, %s)' % (x.get('doc'), STAMP)
                print('%s row %s: %s %s is the retest result, not carried' % (ret, no, x.get('res'), x.get('doc')))
        old = i['issue']
        i['issue'] = i.pop('issue_before_redating', i['issue'])   # undo the re-dating to the Farmahem result
        i['issue'] = AE.initial_issue(i, r)
        ext = [AE.dt(x.get('dd')) for x in i['rows'] if str(x.get('doc') or '').strip() not in ('', '—')
               and not str(x.get('doc')).startswith('iCoA') and AE.dt(x.get('dd'))]
        if ext:
            m = max(ext)
            i['last_external'] = '%02d.%02d.%04d' % (m.day, m.month, m.year)
        r.setdefault('supersedes', {})['date'] = i['issue']
        print('%s issue %s -> %s; %s supersedes %s of %s' % (ini, old, i['issue'], ret, ini, i['issue']))
    if not a.apply:
        print('--check: nothing written')
        return 0
    indent = 1 if raw.startswith('{\n ') and not raw.startswith('{\n  ') else 2
    open(REG, 'w', encoding='utf-8').write(json.dumps(reg, ensure_ascii=False, indent=indent) + ('\n' if raw.endswith('\n') else ''))
    print('wrote the register')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
