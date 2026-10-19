#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The retests of the lots whose identification and foreign matter CNP tested carry CNP's certificate, and no iCoA.

    python3 tracker/apply_cnp_retest_no_icoa_2026-10-09.py --check
    python3 tracker/apply_cnp_retest_no_icoa_2026-10-09.py --apply

Head of QC, 09.10.2026: *"How come there are 29 [Tranche 3] retest certificates of quality and internal certificates
of analysis. There was one instance where one certificate of quality did not have an internal certificate of analysis
because all of those parameters were performed in [the UKIM] Center for Natural Products"*.

Three Tranche 3 lots had rows 1, 2, 7 (and 8) tested explicitly by CNP, so their initials carry no internal
certificate (§5 ruling 6): -075 (ППК26110), -079 (ППК26112), -080 (ППК26116). Their retests -144, -143, -161 said
rows 1, 2, 7 were "carried from the initial testing" yet cited a retest iCoA of their own (-144, -101, -161). A retest
carries a parameter it did not retest with its original citation (§7, "Retest CoQ"), and where CNP tested what an
iCoA would hold there is none (§7 item 5) — exactly as the approved scans of -092 and -123, the Tranche 2 retests of
the CNP-tested lots, credit 1, 2, 7, 8 to CNP and cite no iCoA (`SCAN_INDEX_2026-09-25.tsv`).

So rows 1, 2, 7 of each retest take the initial's row (result, CNP certificate, date, laboratory), keeping their
"carried" status. With nothing credited to it, the bundle issues no iCoA for the retest and lists its number in
`NO_INTERNAL_CERTIFICATE.tsv`, as for the initials.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
REG = os.path.join(GAP, 'coq_artifact_data.json')
PAIRS = (('CoQ-PP_26-075', 'CoQ-PP_26-144', 'ППК26110'), ('CoQ-PP_26-079', 'CoQ-PP_26-143', 'ППК26112'),
         ('CoQ-PP_26-080', 'CoQ-PP_26-161', 'ППК26116'))


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
    n = 0
    for ini, ret, cnp in PAIRS:
        i, r = by[ini], by[ret]
        if (r.get('supersedes') or {}).get('code') != ini or 'retest' not in r['t'] or (i['pp'], i['cb']) != (r['pp'], r['cb']):
            raise SystemExit('%s is not the retest of %s' % (ret, ini))
        ir, rr = {x['no']: x for x in i['rows']}, {x['no']: x for x in r['rows']}
        if any(ir[no]['doc'] != cnp for no in ('1', '2', '7', '8')):
            raise SystemExit('%s: rows 1, 2, 7, 8 do not all cite %s' % (ini, cnp))
        for no in ('1', '2', '7'):
            x, s = rr[no], ir[no]
            if (x['doc'], x['lab'], x['dd'], x['res']) == (s['doc'], s['lab'], s['dd'], s['res']):
                continue
            if not str(x.get('st', '')).startswith('carried from the initial'):
                raise SystemExit('%s row %s is not carried (%s)' % (ret, no, x.get('st')))
            print('%s row %s: %s %s (%s) → %s %s (%s)' % (ret, no, x['doc'], x['dd'], x['lab'], s['doc'], s['dd'], s['lab']))
            x.update({'doc': s['doc'], 'lab': s['lab'], 'dd': s['dd'], 'res': s['res']})
            n += 1
        if any(x['doc'] == r['icoa_code'] for x in r['rows']):
            raise SystemExit('%s still credits %s' % (ret, r['icoa_code']))
        print('%s: no internal certificate (%s not issued); rows 1, 2, 7, 8 cite %s' % (ret, r['icoa_code'], cnp))
    if not a.apply:
        print('--check: nothing written (%d rows to change)' % n)
        return 0
    indent = 1 if raw.startswith('{\n ') and not raw.startswith('{\n  ') else 2
    open(REG, 'w', encoding='utf-8').write(json.dumps(reg, ensure_ascii=False, indent=indent) + ('\n' if raw.endswith('\n') else ''))
    print('wrote the register: %d rows' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
