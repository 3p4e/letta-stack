#!/usr/bin/env python3
"""Manufacture and packaging dates from the owner's workbook, for every certificate not yet issued.

    python3 tracker/apply_batch_dates_2026-09-27.py --check     # writes nothing
    python3 tracker/apply_batch_dates_2026-09-27.py --apply

Found on 27.09.2026, looking at the rebuilt Tranche 3 pages: 60 certificates of quality outside
Tranches 1 and 2 printed "—" for both the manufacture date and the packaging date, and their internal
certificates "—" for the packaging date, although the owner's workbook ("Batch Dates" sheet,
batch_dates_2026-09-10.csv) holds them. No gap list reported it. The standing rule (CLAUDE.md §7):
packaging and manufacturing dates come from the master workbook — manufacture = the first harvest
day, packaging = the first packaging day.

* A record takes the workbook row whose batch is its cultivation batch, or whose P number is its P
  lot — exactly; never a sister sub-lot (ruling 2). A starred spelling on the workbook is the same lot
  as the register's unstarred label only where the alias is recorded as a ruling
  (ingestion/ecoa_runner/identity_decisions.tsv, `batch_alias`, OI-28): GG012601* = GG012601,
  JD012601* = JD012601, SCR012601* = SCR012601, FB012602* = FB012602.
* Only an empty field is filled; a date already on the record is never overwritten.
* An initial internal certificate is tested on the packaging date (CLAUDE.md §7, "Dates"), so an
  initial record whose iCoA test date is empty takes its packaging date. Found in the review of
  27.09.2026: `-018` had its packaging date (01.09.2025) filled from the workbook and still printed "—"
  for the iCoA test date.
* Tranches 1 and 2 are issued and not touched; withdrawn records are skipped.
* A record the workbook does not cover is listed, never guessed.
* **The P lot.** Found in the same review: 30 certificates outside Tranches 1 and 2 had no P number on
  the register although the workbook gives one (SJ102501 → P060162 …). Their CoQ printed the
  cultivation batch as "Production Batch №" and their iCoA "—", so the two disagreed and the iCoA
  carried a silent blank. The workbook is the authority for which P number a cultivation batch is
  (ruling 2 of 26.09.2026, P060332 = CC012601/1), so an empty `pp` takes the workbook's `p_batch` for
  the record's exact batch (or recorded star alias) — refused if another live record of the same
  kind already holds that P number, or if it would move the lot to another tranche.
"""
import argparse, csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(GAP))
REG = os.path.join(GAP, 'coq_artifact_data.json')
sys.path.insert(0, HERE)
import audit_empty_results as A                                    # noqa: E402

FULL = re.compile(r'^\d\d\.\d\d\.\d{4}$')


def aliases():
    """unstarred label -> starred workbook spelling, from the recorded rulings."""
    out = {}
    with open(os.path.join(ROOT, 'ingestion', 'ecoa_runner', 'identity_decisions.tsv'), encoding='utf-8') as fh:
        for r in csv.DictReader(fh, delimiter='\t'):
            if r.get('field') == 'batch_alias' and r.get('confirmed_value') and r.get('was'):
                out[r['confirmed_value'].strip()] = r['was'].strip()
    return out


def p_lots(reg, rows, star, tranche):
    """Fill an empty P lot from the workbook's p_batch for the record's exact (or starred) batch."""
    by_batch = {}
    for r in rows:
        if r['batch']:
            by_batch.setdefault(r['batch'], []).append(r)
    held = {}
    for c in reg['coqs']:
        if c.get('pp') and not c.get('withdrawn'):
            held.setdefault((c['pp'], 'retest' in c['t']), c['regcode'])
    filled, refused = [], []
    for c in reg['coqs']:
        if c.get('pp') or c.get('withdrawn') or tranche(c) in A.FROZEN:
            continue
        cb = str(c.get('cb') or '')
        cand = by_batch.get(cb, []) + by_batch.get(star.get(cb, '\0'), [])
        ps = {r['p_batch'].strip() for r in cand if re.match(r'^P\d{6}$', r['p_batch'].strip())}
        if len(ps) != 1:
            continue
        pp = ps.pop()
        other = held.get((pp, 'retest' in c['t']))
        before = tranche(c)
        c['pp'] = pp
        if other or tranche(c) != before:
            c['pp'] = ''
            refused.append('%s %s → %s: %s' % (c['regcode'], cb, pp, 'held by ' + other if other
                                                else 'tranche %s → %s' % (before, tranche(c))))
            continue
        held[(pp, 'retest' in c['t'])] = c['regcode']
        filled.append((c['regcode'], cb, pp))
    return filled, refused


def tested(c, filled):
    """An initial iCoA with no test date takes the packaging date — it is tested on that day."""
    if 'retest' in c['t'] or c.get('icoa_tested') or not FULL.match(str(c.get('pk') or '')):
        return
    c['icoa_tested'] = c['pk']
    filled.append((c['regcode'], c.get('cb') or '', 'icoa_tested', c['pk'], 'its packaging date'))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv[1:])
    if not (a.apply or a.check):
        ap.error('pass --check or --apply')
    reg = json.load(open(REG, encoding='utf-8'))
    tm = A.tranche_map()

    def tranche(c):
        for k in (c.get('pp'), c.get('cb'), (c.get('cb') or '').replace('＊', '')):
            if k and k in tm:
                return tm[k]

    rows = list(csv.DictReader(open(os.path.join(GAP, 'batch_dates_2026-09-10.csv'), encoding='utf-8')))
    plot_filled, plot_refused = p_lots(reg, rows, aliases(), tranche)
    byb, byp = {}, {}
    for r in rows:
        if r['batch']:
            byb.setdefault(r['batch'], []).append(r)
        if r['p_batch']:
            byp.setdefault(r['p_batch'], []).append(r)
    star = aliases()
    filled, missing, clash, blank = [], [], [], []
    for c in reg['coqs']:
        if tranche(c) in A.FROZEN or c.get('withdrawn'):
            continue
        if c.get('md') and c.get('pk'):
            tested(c, filled)
            continue
        cb, pp = str(c.get('cb') or ''), str(c.get('pp') or '')
        cand = byb.get(cb, []) + byb.get(star.get(cb, '\0'), []) + byp.get(pp, [])
        uniq = {id(r): r for r in cand}
        if len(uniq) > 1:
            clash.append((c['regcode'], pp, cb))
            continue
        if not uniq:
            missing.append((c['regcode'], pp or '—', cb))
            tested(c, filled)
            continue
        r = next(iter(uniq.values()))
        for f, col in (('md', 'harvest_from'), ('pk', 'packaging_from')):
            v = r[col].strip()
            if not c.get(f) and not FULL.match(v):
                blank.append((c['regcode'], cb, f, v or 'empty', r['batch']))
            if not c.get(f) and FULL.match(v):
                c[f] = v
                filled.append((c['regcode'], cb, f, v, 'workbook row ' + r['batch']))
        tested(c, filled)
    print('fields filled: %d (on %d certificates)' % (len(filled), len({x[0] for x in filled})))
    for x in filled:
        print('   %s  %-13s %s = %s   (%s)' % x)
    print('in the workbook without a date — still "—": %d' % len(blank))
    for x in blank:
        print('   %s  %-13s %s: the workbook gives "%s" (row %s)' % x)
    print('not in the workbook — still "—": %d' % len(missing))
    for x in missing:
        print('   %s  %s  %s' % x)
    print('P lots filled from the workbook: %d' % len(plot_filled))
    for x in plot_filled:
        print('   %s  %-13s pp = %s' % x)
    for x in plot_refused:
        print('   refused  %s' % x)
    if clash or plot_refused:
        print('refused — two workbook rows match: %s' % ', '.join(x[0] for x in clash))
        return 1
    if a.check:
        print('--check: nothing written')
        return 0
    with open(REG, 'w', encoding='utf-8') as fh:
        json.dump(reg, fh, ensure_ascii=False, indent=1)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
