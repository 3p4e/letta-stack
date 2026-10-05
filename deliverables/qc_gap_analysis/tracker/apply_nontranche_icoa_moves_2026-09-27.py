#!/usr/bin/env python3
"""The 25.09.2026 internal-certificate renumbering, applied to the lots outside every tranche.

    python3 tracker/apply_nontranche_icoa_moves_2026-09-27.py --check     # writes nothing
    python3 tracker/apply_nontranche_icoa_moves_2026-09-27.py --apply

The ruling (Head of QC, 25.09.2026, `T3_ICOA_RENUMBERING_2026-09-25.md`): *"if their document number
is already cited to another document that is from Tranche 2 or 1, that means you will take the first
available number, for the first chronological batch that needs one"*. It was given for Tranche 3. On
27.09.2026 the Head of QC asked for the certificates of the lots outside every tranche to be delivered,
and approved the same rule for them: four of those lots held an internal-certificate number that a
delivered Tranche 1/2 page carries (the 44 of 24.09; cited on the approved scans of CoQ-PP_26-100,
-111, -115, -120). They take the numbers the 25.09 run left free and reserved for exactly them.

Same machinery and guards as the 25.09 run, imported from it: a delivered number never moves; only
records outside every tranche and colliding with a delivered page move; every number taken was free;
chronology by the cultivation batch's month and year, then the packaging lot; citing rows are
rewritten only inside the moved record.
"""
import argparse, collections, importlib.util, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('m25', os.path.join(HERE, 'apply_t3_icoa_moves_2026-09-25.py'))
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
import glob, re


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

    lot = lambda c: c.get('pp') or c.get('cb')
    delivered = {}
    for p in glob.glob(M.DELIVERED):
        m = re.match(r'iCoA-PP_26-(\d{3})_([A-Za-z0-9]+)_', os.path.basename(p))
        if m:
            delivered[m.group(1)] = m.group(2)
    if len(delivered) != 44:
        print('the delivered set reads %d pages, expected 44 — refusing' % len(delivered))
        return 1
    held = collections.defaultdict(set)
    for n, l in delivered.items():
        held[n].add(l)
    for c in reg['coqs']:
        n = (c.get('icoa_code') or '')[-3:]
        if n.isdigit():
            held[n].add(lot(c))
    free = ['%03d' % i for i in range(1, 173) if not held['%03d' % i]]
    need = [c for c in reg['coqs'] if tranche(c) is None and not c.get('withdrawn')
            and (c.get('icoa_code') or '')[-3:] in delivered
            and delivered[(c.get('icoa_code') or '')[-3:]] != lot(c)]
    if any(not M.batch_date(c.get('cb')) for c in need) or len(need) > len(free):
        print('cannot order or place the records that need a number — refusing')
        return 1
    need.sort(key=lambda c: (M.batch_date(c.get('cb')), c.get('pp') or '￿', c['regcode']))
    moves = {c['regcode']: (c.get('icoa_code'), 'iCoA-PP_26-' + n) for c, n in zip(need, free)}
    if any(n[-3:] in delivered for _, n in moves.values()):
        print('a move would land on a delivered number — refusing')
        return 1
    print('%-16s %-11s %-8s %-9s %-16s %s' % ('CoQ', 'cult.batch', 'batch', 'P lot', 'was', 'becomes'))
    for c in need:
        y, m = M.batch_date(c.get('cb'))
        print('%-16s %-11s %04d-%02d  %-9s %-16s %s' % (c['regcode'], c.get('cb'), y, m, c.get('pp') or '—', *moves[c['regcode']]))
    print('free numbers left: %s' % ' '.join(free[len(moves):]))
    if a.check:
        print('--check: nothing written')
        return 0
    shutil.copy2(M.REG, M.REG + '.bak')
    n_code = n_rows = 0
    for c in reg['coqs']:
        if c['regcode'] not in moves:
            continue
        old, new = moves[c['regcode']]
        if c.get('icoa_code') == old:
            c['icoa_code'] = new
            n_code += 1
        for row in c.get('rows') or []:
            if old and row.get('doc') and old in row['doc']:
                row['doc'] = row['doc'].replace(old, new)
                n_rows += 1
    with open(M.REG, 'w', encoding='utf-8') as fh:
        json.dump(reg, fh, ensure_ascii=False, indent=1)
    after = collections.defaultdict(set)
    for n, l in delivered.items():
        after[n].add(l)
    for c in reg['coqs']:
        n = (c.get('icoa_code') or '')[-3:]
        if n.isdigit():
            after[n].add(lot(c))
    print('wrote %d icoa_code fields and %d citing rows; numbers still held by two lots: %s'
          % (n_code, n_rows, ' '.join(sorted(n for n in after if len(after[n]) > 1)) or 'none'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
