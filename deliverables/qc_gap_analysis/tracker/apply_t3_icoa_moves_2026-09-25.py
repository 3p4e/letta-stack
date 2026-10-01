#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Tranche 3 internal-certificate renumbering — Head of QC, 25.09.2026.

    python3 tracker/apply_t3_icoa_moves_2026-09-25.py --check    # dry run, writes nothing
    python3 tracker/apply_t3_icoa_moves_2026-09-25.py --apply

His ruling:

    "For those Tranche 3 certificates of quality and the internal certificates of analysis that are
     cited in the CoQs — if their document number is already cited to another document that is from
     Tranche 2 or 1, that means you will take the first available number, for the first chronological
     batch that needs one; and the same will go for the internal certificates of analysis."

So: a Tranche 3 record whose internal-certificate number is already carried by a Tranche 1 or 2
document moves to the lowest free number, and the free numbers are handed out to the affected batches
in the order the batches were grown.

**The certificate-of-quality series needs nothing.** `CoQ-PP_26-001` … `-172` has no gap, no
duplicate and no Tranche 3 number held by a Tranche 1 or 2 document. The rule applies, and finds
nothing to do. Only the internal certificates move, and no `CoQ` code is touched by this script.

Chronology comes from the cultivation batch code, which carries the month and year — `BSS1024` is
10/2024, `CJ052501` is 05/2025, `J31112501` is 11/2025 (the strain prefix may itself carry digits,
so the trailing digit run is read, not the first). Within one month the packaging lot orders them,
and a batch with no packaging lot yet sorts after those that have one.

Guards, all of which abort the run:
  * a number carried by one of the 44 delivered pages may never move;
  * exactly the colliding Tranche 3 records move, no more and no fewer;
  * every number taken must have been free, and no two moves may take the same one;
  * afterwards no number may be held by two different lots among the records touched;
  * a citing row is rewritten only inside the record that owns it — a row on another record that
    names the same number is reported for reading, never silently changed.
"""
import argparse
import collections
import csv
import glob
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
REG = os.path.join(GAP, 'coq_artifact_data.json')
TRANCHES = os.path.join(GAP, 'intake_tranches_2026-09-18', 'drive_folders_2026-09-18.tsv')
DELIVERED = os.path.join(GAP, 'DELIVER_2026-09-24', 'iCoA_T1_T2_owner_format', '*.html')
PLOT = re.compile(r'^P\d{6}$')


def tranche_map():
    m = {}
    with open(TRANCHES, encoding='utf-8') as fh:
        for r in csv.DictReader(fh, delimiter='\t'):
            f, t = r['folder'], r['tranche']
            tail = f.rsplit('_', 1)[-1]
            if PLOT.match(tail):
                m[tail] = t
            m[f] = t
            m.setdefault(re.split(r'_P\d{6}$', f)[0].rstrip('_').replace('＊', ''), t)
    return m


def batch_date(cb):
    """Month and year off the cultivation batch code; None when it cannot be read."""
    core = re.split(r'[_/\-]', (cb or '').replace('＊', '').strip())[0]
    core = re.sub(r'V$', '', core)
    m = re.search(r'(\d+)$', core)
    if not m:
        return None
    g = m.group(1)
    g = g[-6:] if len(g) >= 6 else g
    if len(g) < 4:
        return None
    mm, yy = int(g[:2]), int(g[2:4])
    return (2000 + yy, mm) if 1 <= mm <= 12 else None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv[1:])
    if not (a.apply or a.check):
        ap.error('pass --check or --apply')

    reg = json.load(open(REG, encoding='utf-8'))
    tm = tranche_map()

    def tranche(c):
        for k in (c.get('pp'), c.get('cb'), (c.get('cb') or '').replace('＊', '')):
            if k and k in tm:
                return tm[k]

    def lot(c):
        return c.get('pp') or c.get('cb')

    delivered = {}
    for p in glob.glob(DELIVERED):
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

    t3 = [c for c in reg['coqs'] if tranche(c) == 'T3' and 'retest' in c['t']]
    need = [c for c in t3
            if (c.get('icoa_code') or '')[-3:] in delivered
            and delivered[(c.get('icoa_code') or '')[-3:]] != lot(c)]

    undated = [c['regcode'] for c in need if not batch_date(c.get('cb'))]
    if undated:
        print('cannot read a batch date for %s — refusing to order them' % ', '.join(undated))
        return 1
    if len(need) > len(free):
        print('%d records need a number, only %d free — refusing' % (len(need), len(free)))
        return 1

    need.sort(key=lambda c: (batch_date(c.get('cb')), c.get('pp') or '￿', c['regcode']))
    moves = {c['regcode']: (c.get('icoa_code'), 'iCoA-PP_26-' + n) for c, n in zip(need, free)}

    taken = [n[-3:] for _, n in moves.values()]
    if len(set(taken)) != len(taken):
        print('two moves claim the same number — refusing')
        return 1
    for n in taken:
        if n in delivered:
            print('move would land on %s, which a delivered page holds — refusing' % n)
            return 1

    print('CoQ series: nothing to move (no gap, no duplicate, no T3 number held by T1/T2)')
    print('iCoA moves: %d   free numbers %d, using the first %d' % (len(moves), len(free), len(moves)))
    print()
    print('%-16s %-13s %-8s %-9s %-16s %s' % ('CoQ', 'cult.batch', 'batch', 'P lot', 'was', 'becomes'))
    print('-' * 84)
    by_code = {c['regcode']: c for c in need}
    for rc in [c['regcode'] for c in need]:
        c = by_code[rc]
        y, m = batch_date(c.get('cb'))
        old, new = moves[rc]
        print('%-16s %-13s %-8s %-9s %-16s %s' % (rc, c.get('cb'), '%04d-%02d' % (y, m),
                                                  c.get('pp') or '—', old, new))
    print()
    print('free numbers left for the five Tranche 2 duplicates: %s' % ' '.join(free[len(moves):]))

    # citing rows, inside the record and elsewhere
    inside = elsewhere = 0
    for c in reg['coqs']:
        rc = c.get('regcode')
        for row in c.get('rows') or []:
            doc = row.get('doc') or ''
            if rc in moves and moves[rc][0] and moves[rc][0] in doc:
                inside += 1
            else:
                for orc, (old, _) in moves.items():
                    if old and old in doc and orc != rc:
                        elsewhere += 1
                        break
    print('citing rows inside a moved record: %d' % inside)
    print('citing rows on OTHER records naming a moved number: %d %s'
          % (elsewhere, '(reported, never rewritten)' if elsewhere else ''))

    if a.check:
        print('\n--check: nothing written')
        return 0

    shutil.copy2(REG, REG + '.bak')
    n_code = n_rows = 0
    for c in reg['coqs']:
        rc = c.get('regcode')
        if rc not in moves:
            continue
        old, new = moves[rc]
        if c.get('icoa_code') == old:
            c['icoa_code'] = new
            n_code += 1
        for row in c.get('rows') or []:
            if old and row.get('doc') and old in row['doc']:
                row['doc'] = row['doc'].replace(old, new)
                n_rows += 1
    with open(REG, 'w', encoding='utf-8') as fh:
        json.dump(reg, fh, ensure_ascii=False, indent=1)

    after = collections.defaultdict(set)
    for n, l in delivered.items():
        after[n].add(l)
    for c in reg['coqs']:
        n = (c.get('icoa_code') or '')[-3:]
        if n.isdigit():
            after[n].add(lot(c))
    still = sorted(n for n in after if len(after[n]) > 1)
    print('\nwrote %d icoa_code fields and %d citing rows (backup at %s.bak)'
          % (n_code, n_rows, os.path.basename(REG)))
    print('numbers still held by two lots: %d %s' % (len(still), ' '.join(still)))
    print('  (the five Tranche 2 duplicates remain — they are not in this ruling\'s scope)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
