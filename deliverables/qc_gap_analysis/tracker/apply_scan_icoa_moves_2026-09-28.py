#!/usr/bin/env python3
"""The 25.09.2026 internal-certificate rule, held against the approved scans as well.

    python3 tracker/apply_scan_icoa_moves_2026-09-28.py --check     # writes nothing
    python3 tracker/apply_scan_icoa_moves_2026-09-28.py --apply

The ruling (Head of QC, 25.09.2026): *"if their document number is already cited to another document
that is from Tranche 2 or 1, that means you will take the first available number, for the first
chronological batch that needs one"*. The 25.09 run (`apply_t3_icoa_moves_2026-09-25.py`) and the
27.09 run for the lots outside the tranches compared numbers only with the 44 internal-certificate
pages delivered on 24.09, and only for retests. A number can also be *cited* on a certificate of
quality the customer holds: the approved scan of `CoQ-PP_26-107` (P050192, Tranche 2) credits loss on
drying to `iCoA-PP_26-023` of 03.06.2026, while the register gave that number to the unissued Tranche 3
initial `CoQ-PP_26-023` (P050172). Found on 28.09.2026 by `tracker/check_icoa_references.py`.

So a certificate not yet issued (outside Tranches 1 and 2, not withdrawn) whose internal-certificate
number an approved scan cites for another lot takes the lowest number that no delivered page, no scan
and no register record holds. Same guards as the 25.09 run: a delivered or scanned number never moves;
only the colliding records move; citing rows are rewritten only inside the moved record. Rerunning it
changes nothing.
"""
import argparse, collections, csv, importlib.util, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('m25', os.path.join(HERE, 'apply_t3_icoa_moves_2026-09-25.py'))
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
import glob                                                          # noqa: E402

SCANS = os.path.join(HERE, 'SCAN_INDEX_2026-09-25.tsv')


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv[1:])
    if not (a.apply or a.check):
        ap.error('pass --check or --apply')
    reg = json.load(open(M.REG, encoding='utf-8'))
    tm = M.tranche_map()

    def tranche(c):
        for k in (c.get('pp'), c.get('cb'), (c.get('cb') or '').replace('＊', '')):
            if k and k in tm:
                return tm[k]

    lot = lambda c: c.get('pp') or c.get('cb')                       # noqa: E731
    held = collections.defaultdict(set)
    fixed = set()                                  # numbers on a delivered page or an approved scan
    for p in glob.glob(M.DELIVERED):
        m = re.match(r'iCoA-PP_26-(\d{3})_([A-Za-z0-9]+)_', os.path.basename(p))
        if m:
            held[m.group(1)].add(m.group(2))
            fixed.add(m.group(1))
    scanned = collections.defaultdict(set)
    for r in csv.DictReader(open(SCANS, encoding='utf-8'), delimiter='\t'):
        for n in re.findall(r'iCoA-PP_26-(\d{3})', r.get('icoa_cited') or ''):
            scanned[n].add(r['batch'])
            held[n].add(r['batch'])
            fixed.add(n)
    for c in reg['coqs']:
        n = (c.get('icoa_code') or '')[-3:]
        if n.isdigit():
            held[n].add(lot(c))
    free = ['%03d' % i for i in range(1, 173) if not held['%03d' % i]]

    def names(c):
        return {x for x in (c.get('pp'), c.get('cb')) if x}

    need = []
    for c in reg['coqs']:
        n = (c.get('icoa_code') or '')[-3:]
        if (tranche(c) in ('T1', 'T2') or c.get('withdrawn') or n not in scanned or scanned[n] & names(c)
                or not any(r.get('doc') == c.get('icoa_code') for r in c.get('rows') or [])):
            continue
        need.append(c)
    if any(not M.batch_date(c.get('cb')) for c in need) or len(need) > len(free):
        print('cannot order or place the records that need a number — refusing')
        return 1
    need.sort(key=lambda c: (M.batch_date(c.get('cb')), c.get('pp') or '￿', c['regcode']))
    moves = {c['regcode']: (c.get('icoa_code'), 'iCoA-PP_26-' + n) for c, n in zip(need, free)}
    if any(new[-3:] in fixed for _, new in moves.values()):
        print('a move would land on a delivered or scanned number — refusing')
        return 1
    for c in need:
        old, new = moves[c['regcode']]
        print('%s  %-9s %-12s %s → %s   (an approved scan cites %s for %s)'
              % (c['regcode'], c.get('pp') or '—', c.get('cb'), old, new, old,
                 ', '.join(sorted(scanned[old[-3:]]))))
    print('records moved: %d; free numbers left: %s' % (len(moves), ' '.join(free[len(moves):]) or 'none'))
    if a.check or not moves:
        print('--check: nothing written' if a.check else 'nothing to move')
        return 0
    shutil.copy2(M.REG, M.REG + '.bak')
    n_rows = 0
    for c in reg['coqs']:
        if c['regcode'] not in moves:
            continue
        old, new = moves[c['regcode']]
        c['icoa_code'] = new
        for row in c.get('rows') or []:
            if row.get('doc') == old:
                row['doc'] = new
                n_rows += 1
    with open(M.REG, 'w', encoding='utf-8') as fh:
        json.dump(reg, fh, ensure_ascii=False, indent=1)
    os.remove(M.REG + '.bak')
    print('wrote %d records and %d citing rows' % (len(moves), n_rows))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
