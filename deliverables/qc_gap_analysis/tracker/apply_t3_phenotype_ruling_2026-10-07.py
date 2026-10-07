#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tranche 3: no certificate prints Indica or Sativa alone. Each is a hybrid, with its dominance where it is known.

    python3 tracker/apply_t3_phenotype_ruling_2026-10-07.py --check     # writes nothing
    python3 tracker/apply_t3_phenotype_ruling_2026-10-07.py --apply

Head of QC, 07.10.2026: *"in all tranche three certificates of quality, at phenotype, wherever it says indica or
sativa as only selected option, I want you to correct it and mark it as hybrid. And if information is available,
state is it indica dominant or sativa dominant, or if percentages are known or available, include the percentages
in the suitable formatting as it is now"*, and *"also correct in the iCoAs"*.

Thirteen Tranche 3 records print Indica alone: every Gorilla Glue, Blue Sunset Sherbet and Orange Punch Mimosa lot
in the tranche. Every source on file for these strains says Indica and gives no split:

* the approved scans (`COQ_SCAN_PHENOTYPE_2026-09-24.tsv`: GG1024, BSS1024, OPM1024);
* the specifications (`spec_attributes_2026-09-10.csv`: QCSP_001_GG-*, BSS-*, OPM-*);
* the 17.09 initial list.

So each becomes HYBRID, leaning Indica: dominance `INDICA-DOMINANT`, as the register already writes it for the ten
Tranche 3 hybrids known to lean Indica. No percentage is on record for them, and none is written.

Where the register holds the split (`INDICA 60 : SATIVA 40` …), the pages print it as they do now. Where it holds
only the leaning, the Tranche 3 pages now say it as well (`coq_build.js` section 01, `build_t3_bundle_2026-09-26.fields`).
Before this, a known leaning printed as a bare Hybrid.

**Tranches 1 and 2 are not touched** (Head of QC, 26.09.2026); the script refuses them. Lots outside the tranches
are not in this ruling. A withdrawn number is skipped.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import audit_empty_results as A                                    # noqa: E402

REG = os.path.join(GAP, 'coq_artifact_data.json')
LEAN = {'INDICA': ('INDICA-DOMINANT', 'Indica dom.'), 'SATIVA': ('SATIVA-DOMINANT', 'Sativa dom.')}


def run(reg, apply):
    tm = A.tranche_map()

    def tranche(c):
        for k in (c.get('pp'), c.get('cb'), (c.get('cb') or '').replace('＊', '')):
            if k and k in tm:
                return tm[k]

    done = []
    for c in reg['coqs']:
        if c.get('withdrawn') or tranche(c) != 'T3':
            continue
        if tranche(c) in A.FROZEN:
            raise SystemExit('%s is in an issued tranche' % c['regcode'])
        spc = c.get('spc') or {}
        ph = str(spc.get('pheno') or '').strip().upper()
        if ph not in LEAN:
            continue
        if str(spc.get('dominance') or '').strip():
            raise SystemExit('%s: %s with a dominance on record (%r) — read it before writing' % (
                c['regcode'], ph, spc.get('dominance')))
        dom, short = LEAN[ph]
        done.append((c['regcode'][:13], c.get('cb'), c.get('strain'), ph, 'HYBRID · %s' % dom))
        if apply:
            spc['pheno'], spc['dominance'], spc['dom'] = 'HYBRID', dom, short
    return done


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv[1:])
    if not (a.apply or a.check):
        ap.error('pass --check or --apply')
    reg = json.load(open(REG, encoding='utf-8'))
    done = run(reg, a.apply)
    for x in done:
        print('PHENOTYPE %s %-14s %-20s %s -> %s' % x)
    print('%d Tranche 3 certificates: Indica or Sativa alone -> Hybrid with its leaning' % len(done))
    if a.apply and done:
        with open(REG, 'w', encoding='utf-8') as fh:
            json.dump(reg, fh, ensure_ascii=False, indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
