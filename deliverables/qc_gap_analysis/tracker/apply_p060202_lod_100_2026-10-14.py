#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P060202 (J31112501): the retest CoQ-PP_26-153 prints the loss on drying of Farmahem's reanalysis 100-1-ГС/26.

    python3 tracker/apply_p060202_lod_100_2026-10-14.py --check
    python3 tracker/apply_p060202_lod_100_2026-10-14.py --apply

Head of QC, 13.10.2026: *"P060202 LOD check eCOA 100-ГС/26"*; asked which of its three portions and on which CoQ, he
chose **100-1-ГС/26 (7.6 %), retest only** (14.10.2026). OI-52 had asked exactly this since 17.09.2026.

The release certificate 051-5-ГС/26 (02.03.2026, 8.4 %) carries the handwritten note "Реанализа … 27.03.2026 во
Фармахем"; the reanalysis was received on 27.03.2026 and reported on 09.04.2026 in three portions — 100-1 (CF-150/26,
7.6 %), 100-2 (CF-152/26, hand-trimmed, 10.3 %), 100-3 (CF-154/26, trimmed, 10.3 %). Two reads of 100-1-ГС/26 agree
(the Drive text of the scan and the RAGflow eCOA_DB page text): LoD 7,6 % ± 0,2, analysed 08–09.04.2026, issued
09.04.2026 (`intake_P060202_LoD_2026-10-14/`).

The initial CoQ-PP_26-056 keeps its release result, 8.4 % from 051-5-ГС/26.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
REG = os.path.join(GAP, 'coq_artifact_data.json')
RET, INI = 'CoQ-PP_26-153', 'CoQ-PP_26-056'
NEW = {'res': '7.6', 'doc': '100-1-ГС/26', 'dd': '09.04.2026',
       'st': 'covered — Farmahem reanalysis 100-1-ГС/26 of 09.04.2026 (Head of QC, 14.10.2026)',
       'also': '8.4 (051-5-ГС/26, the release result on CoQ-PP_26-056); 10.3 (100-2-ГС/26, hand-trimmed); '
               '10.3 (100-3-ГС/26, trimmed)'}


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
    r, i = by[RET], by[INI]
    if (r['pp'], r['cb'], (r.get('supersedes') or {}).get('code')) != ('P060202', 'J31112501', INI):
        raise SystemExit('%s is not the retest of P060202' % RET)
    row = {x['no']: x for x in r['rows']}['8']
    ini = {x['no']: x for x in i['rows']}['8']
    if (ini['res'], ini['doc']) != ('8.4', '051-5-ГС/26'):
        raise SystemExit('%s row 8 is no longer 8.4 from 051-5-ГС/26' % INI)
    if all(row.get(k) == v for k, v in NEW.items()):
        print('%s row 8 already prints 7.6 from 100-1-ГС/26' % RET)
        return 0
    if (row['res'], row['doc']) != ('8.4', '051-5-ГС/26'):
        raise SystemExit('%s row 8 prints %s from %s, not the expected 8.4 from 051-5-ГС/26' % (RET, row['res'], row['doc']))
    print('%s row 8: %s %s (%s) → %s %s (%s); lab %s' % (RET, row['res'], row['doc'], row['dd'], NEW['res'], NEW['doc'],
                                                       NEW['dd'], row['lab']))
    if not a.apply:
        print('--check: nothing written')
        return 0
    row.update(NEW)
    indent = 1 if raw.startswith('{\n ') and not raw.startswith('{\n  ') else 2
    open(REG, 'w', encoding='utf-8').write(json.dumps(reg, ensure_ascii=False, indent=indent) + ('\n' if raw.endswith('\n') else ''))
    print('wrote the register')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
