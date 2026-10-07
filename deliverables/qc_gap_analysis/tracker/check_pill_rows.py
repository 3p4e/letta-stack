#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every certificate not yet issued marks phenotype, leaning, chemotype and processing the same way on its CoQ, its
iCoA and the specification it cites.

    python3 tracker/check_pill_rows.py

Head of QC, 07.10.2026: *"check if everywhere there is Hybrid : Indica Dom. or suitable applied, as well as on the
CoQ and iCoA and the corresponding specification range"*. The CoQ page (`design_handoff/out`) is the reference.
The iCoA's row is the one `build_t3_bundle.icoa_page` writes (`house_kit.selrow`, the same register fields), and the
specification's is read off its sheet (`specs/QCSP_001_ImB/SHEETS`). Exit 1 on any difference.
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import audit_empty_results as A                                    # noqa: E402
import house_kit as K                                               # noqa: E402


def words(row):
    return ' '.join(re.sub(r'<[^>]+>', ' ', row).split())


def main():
    reg = json.load(open(os.path.join(GAP, 'coq_artifact_data.json'), encoding='utf-8'))
    tm = A.tranche_map()

    def tranche(c):
        for k in (c.get('pp'), c.get('cb'), (c.get('cb') or '').replace('＊', '')):
            if k and k in tm:
                return tm[k]

    sheets = {}
    for p in glob.glob(os.path.join(GAP, 'specs', 'QCSP_001_ImB', 'SHEETS', '*.html')):
        sheets[re.match(r'^(QCSP_001_[A-Z0-9]+-[IVX]+_v\.01)_', os.path.basename(p)).group(1)] = \
            K.coq_selrow(open(p, encoding='utf-8').read())
    pages = {os.path.basename(p)[:13]: p
             for p in glob.glob(os.path.join(GAP, 'design_handoff', 'out', '**', 'CoQ-PP_26-*.html'), recursive=True)}
    bad, n = [], 0
    for c in reg['coqs']:
        if c.get('withdrawn') or tranche(c) in A.FROZEN:
            continue
        code = c['regcode'][:13]
        if code not in pages:
            bad.append('%s: no CoQ page' % code)
            continue
        n += 1
        coq = K.coq_selrow(open(pages[code], encoding='utf-8').read())
        spc = c.get('spc') or {}
        if c.get('icoa_code'):
            icoa = K.selrow(spc.get('pheno'), spc.get('dominance'), spc.get('chemo'), spc.get('proc'), True)
            if icoa != coq:
                bad.append('%s: its iCoA %s reads [%s], the CoQ [%s]' % (code, c['icoa_code'], words(icoa), words(coq)))
        spec = sheets.get(c.get('spec'))
        if spec is None:
            bad.append('%s: no sheet for %s' % (code, c.get('spec')))
        elif spec != coq:
            bad.append('%s: %s reads [%s], the CoQ [%s]' % (code, c.get('spec'), words(spec), words(coq)))
    for b in bad:
        print(b)
    print('pill rows: %d certificates not yet issued, CoQ = iCoA = specification on all but %d' % (n, len(bad)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
