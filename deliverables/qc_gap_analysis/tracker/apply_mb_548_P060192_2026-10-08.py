#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P060192 (SJ112501): IPH 548/1079/26 of 31.08.2026 is the retest microbiology of CoQ-PP_26-163.

    python3 tracker/apply_mb_548_P060192_2026-10-08.py

Head of QC, 08.10.2026: *"I've updated the eCOA database and the P060192 has full MB panel"*. He filed the
certificate on Drive as `P060192 (SJ112501)_IJZ-MB_548-1079-26_31.08.2026.pdf` (file 1g4zYE0W89RrVHT4aFrMQBQi0b7-8eXDD).
Its "Серија" prints P060192. That settles OI-37: on 07.10.2026 the lot was in doubt and the certificate was kept off.
It is the August 2026 round, three months after the release certificate 130/0227/26, so it is the lot's retest
microbiology (CLAUDE.md §5) and goes on the retest -163 only. The initial -055 keeps 130/0227/26, which does not
test P. aeruginosa or S. aureus.

Read twice: from the page image on 08.10.2026, and in the parameter search of the same day. The two agree:
TAMC 5,4 × 10², TYMC 3,7 × 10², BTGN < 10, E. coli, P. aeruginosa and S. aureus absent per g, Salmonella absent
per 25 g. IPH marks P. aeruginosa and S. aureus as outside its accreditation.
"""
import json
import os

GAP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(GAP, 'coq_artifact_data.json')
ROWS = {'9.1': '5,4 × 10²', '9.2': '3,7 × 10²', '9.3': '< 10', '9.4': 'Absent | Отсутна', '9.5': 'Absent | Отсутна',
        '9.6': 'Absent | Отсутна', '9.7': 'Absent | Отсутна'}

raw = open(REG, encoding='utf-8').read()
reg = json.loads(raw)
c = next(x for x in reg['coqs'] if x['regcode'].startswith('CoQ-PP_26-163'))
assert c.get('pp') == 'P060192' and 'retest' in c['t']
for r in c['rows']:
    if r['no'] in ROWS:
        r.update({'res': ROWS[r['no']], 'doc': '548/1079/26', 'dd': '31.08.2026', 'st': 'covered',
                  'lab': 'IPH — Institute of Public Health'})
open(REG, 'w', encoding='utf-8').write(json.dumps(reg, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
print('CoQ-PP_26-163: rows 9.1–9.7 from IPH 548/1079/26 of 31.08.2026')
