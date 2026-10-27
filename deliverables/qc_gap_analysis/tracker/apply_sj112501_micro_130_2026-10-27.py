#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SJ112501 (P060192): the retest CoQ -163 cites the release microbiology 130/0227/26 in place of 548/1079/26.

    python3 tracker/apply_sj112501_micro_130_2026-10-27.py --check
    python3 tracker/apply_sj112501_micro_130_2026-10-27.py --apply

Head of QC, 27.10.2026 (#234): *"just for this batch, we must perform this change and instead of the already cited eCOA
for Microbiological purity to cite and reference the eCOA i just cited above"* (IJZ-MB 130/0227/26) *"and propagate the
change all the way up and down to all levels"*. This batch only; no other lot changes.

Rows 9.1-9.5 of -163 take -055's own rows (130/0227/26, 06.03.2026), marked as carried from the initial. 130/0227/26 does
not report P. aeruginosa or S. aureus, so rows 9.6/9.7 return to -055's "upon request" and print no row (the panel prints
as the cited certificate reports it, 07.10.2026). -163 was signed on 16.10.2026 as citing 548/1079/26, so it left the
signed set (`check_signed_t3.py`, `SIGNED_T3_2026-10-16.json`): it is printed and signed again, then added back.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
REG = os.path.join(GAP, 'coq_artifact_data.json')
INI, RET, PP, NEW, OLD = 'CoQ-PP_26-055', 'CoQ-PP_26-163', 'P060192', '130/0227/26', '548/1079/26'
ROWS = ('9.1', '9.2', '9.3', '9.4', '9.5', '9.6', '9.7')
NOTE = 'Head of QC, 27.10.2026 (#234): this batch only, the retest cites the release microbiology %s in place of %s' % (NEW, OLD)


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
    i, r = by[INI], by[RET]
    if i['pp'] != PP or r['pp'] != PP or (r.get('supersedes') or {}).get('code') != INI:
        raise SystemExit('%s/%s are not lot %s' % (INI, RET, PP))
    src = {x['no']: x for x in i['rows']}
    dst = {x['no']: x for x in r['rows']}
    if src['9.1'].get('doc') != NEW:
        raise SystemExit('%s row 9.1 no longer cites %s' % (INI, NEW))
    for no in ROWS:
        s, d = src[no], dst[no]
        was = '%s (%s %s)' % (d.get('res'), d.get('doc'), d.get('dd'))
        new = {k: s.get(k) for k in ('res', 'doc', 'dd', 'lab', 'fam')}
        new['route'] = ''
        new['st'] = ('carried from the initial testing (%s) — covered' % INI if str(s.get('doc') or '').strip() == NEW
                     else s.get('st'))
        new['ruling'] = NOTE + '; was ' + was
        print('%s row %s: %s -> %s (%s %s) | %s' % (RET, no, was, new['res'], new['doc'], new['dd'], new['st']))
        d.update(new)
    if not a.apply:
        print('--check: nothing written')
        return 0
    indent = 1 if raw.startswith('{\n ') and not raw.startswith('{\n  ') else 2
    open(REG, 'w', encoding='utf-8').write(json.dumps(reg, ensure_ascii=False, indent=indent) + ('\n' if raw.endswith('\n') else ''))
    print('wrote the register')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
