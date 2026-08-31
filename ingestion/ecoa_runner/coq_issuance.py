#!/usr/bin/env python3
"""The CoQ issuance schedule, in the order the Head of QC will issue them.

The register in `coq_register.py` is ordered by testing history. This one is
ordered by ISSUING WORK, in five waves, because that is the order the documents
are actually produced in:

  WAVE 1  supersede QCCoA 001 / 001 v.02
          37 batches carry a retired PP-group Certificate of Analysis. Each is
          replaced, one for one, by a CoQ compiled from the originating eCoAs.
          These come first: until they issue, those batches have no valid
          quality certificate at all.
  WAVE 2  first-issue CoQ for every remaining batch
  WAVE 3  Tranche 1 retest reissues
  WAVE 4  Tranche 2 retest reissues
  WAVE 5  Tranche 3 (and un-tranched) retest reissues

Within a wave the order is chronological. CoQ numbers are assigned in this
issuance order and belong to the BATCH for life - a retest in wave 3, 4 or 5
advances that batch's VERSION and reuses its number (QCSOP 012 v.03 04).

For every CoQ the schedule prints one cell per specification row: the value
where one exists, and where it came from - an accredited outsourced laboratory,
in house, or nowhere yet. A row with no source is what the iCoA register then
picks up, in this same order, so the two documents read side by side.
"""
import os, sys, json, sqlite3, argparse, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'common'))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


CR = _load('cr', HERE + '/coq_register.py')
CQ = _load('cq', HERE + '/build_coq.py')
import master_spec as MS

# The retired PP-group Certificates of Analysis, from the Head of QC's list
# (CORPUS_RUN_PLAN.md, 31.08). Batches are named by whichever identity the
# retired document used; master_spec resolves both to one batch.
QCCOA_001 = """BG1024 BSS1024 CJ1024 P050012 P050022 P050032 P050042 P050052
P050062 P050072 P050092 P050102 P050122 P050162 P050182""".split()
QCCOA_001_V02 = """P050082 P050112 P050132 P050172 P050192 P050202 P050212
P050272 P050282 P050292 P050302 P050312 P050322 P060012 P060022 P060032
P060042 P060052 P060062 P060072 P060082 P060092""".split()

WAVES = {
    1: 'Supersede QCCoA 001 / 001 v.02',
    2: 'First-issue CoQ, remaining batches',
    3: 'Tranche 1 retest reissue',
    4: 'Tranche 2 retest reissue',
    5: 'Tranche 3 / un-tranched retest reissue',
}

# A source is either an accredited external laboratory or Purely Plant's own
# bench. The distinction is the whole point of the checkbox: an outsourced
# result is already evidenced, an in-house one still needs an iCoA behind it.
IN_HOUSE_IDS = {'PP', 'NGP'}

# Which specification rows Purely Plant can actually close ITSELF. An iCoA is an
# in-house certificate: it cannot carry Salmonella, aflatoxins, heavy metals or
# a 471-compound pesticide panel, because the company does not run those methods.
# Naming a missing row "-> iCoA" when only an accredited laboratory can produce
# it would put an unissuable document on the schedule.
#
#   1  Identification A   macroscopic
#   2  Identification B   microscopy, Ph. Eur. 2.8.23
#   7  Foreign Matter     Ph. Eur. 2.8.2, a balance and a sieve
#   8  Loss on Drying     Ph. Eur. 2.2.32, an oven
#
# Identification C (HPLC identity) is in house ONLY if the HPLC method is
# qualified for identity; until the Head of QC confirms that, it is listed
# separately rather than assumed either way.
IN_HOUSE_CAPABLE = {'1', '2', '7', '8'}
IN_HOUSE_CONDITIONAL = {'3': 'in house only if the HPLC identity method is qualified'}


def _retired(batch):
    """Which retired QCCoA covered this batch, if any."""
    m = MS.spec_for(batch)
    names = {batch}
    if m:
        names |= {m['batch'], m['pp_batch'], m['cultiv_batch_src']}
    if names & set(QCCOA_001):
        return 'QCCoA 001'
    if names & set(QCCOA_001_V02):
        return 'QCCoA 001 v.02'
    return None


def _tranche(batch):
    m = MS.spec_for(batch)
    return m['tranche'] if m else None


def _cell(e):
    """(state, value, source, cert) for one specification row of one CoQ.

    States, and what each one costs to close:
        OUTSOURCED  an accredited laboratory reported it - nothing to do
        IN-HOUSE    Purely Plant reported it - an iCoA must carry it
        HELD        both reads disagree - a ruling, not a test
        NOT TESTED  a covering certificate exists but omits the row - retest
        MISSING     no covering certificate at all - test and issue an iCoA
    """
    if e['status'] != 'ok':
        return e['status'], None, None, None
    lab_id, _ = CQ.canonical_lab(e.get('lab'))
    state = 'IN-HOUSE' if lab_id in IN_HOUSE_IDS else 'OUTSOURCED'
    return state, e.get('result'), lab_id or (e.get('lab') or '')[:18], e.get('cert_code')


def schedule(db):
    """Every CoQ to issue, in wave order, with a cell per specification row."""
    rows = CR.register(db)
    for r in rows:
        ret = _retired(r['batch'])
        if r['version'] == 1:
            r['wave'] = 1 if ret else 2
        else:
            t = _tranche(r['batch'])
            r['wave'] = {'T1': 3, 'T2': 4}.get(t, 5)
        r['supersedes'] = ret
        r['tranche'] = _tranche(r['batch']) or '—'
        m = MS.spec_for(r['batch'])
        r['spec_code'] = m['spec_code'] if m else None
        r['pp_batch'] = m['pp_batch'] if m else None

    # Numbering follows ISSUANCE order, assigned on the batch's first document
    # and held for life. Sorting the release rows by (wave, date) is therefore
    # what fixes every number in the register.
    firsts = sorted((r for r in rows if r['version'] == 1),
                    key=lambda r: (r['wave'], r['date'] or '9999-12-31', r['batch']))
    number = {r['batch']: i + 1 for i, r in enumerate(firsts)}
    for r in rows:
        r['no'] = number[r['batch']]
        r['code'] = 'QCCoQ %03d v.%02d' % (r['no'], r['version'])
        # Each version is compiled AT ITS OWN DATE: v.01 must state what was
        # known when it issued, not what a later retest found.
        s02, _, _ = CQ.compile_coq(db, r['batch'], as_of=r['date'])
        r['cells'] = []
        for e in s02:
            state, val, src, cert = _cell(e)
            r['cells'].append({'no': e['no'], 'parameter': e['parameter'],
                               'criterion': e['criterion'], 'state': state,
                               'value': val, 'source': src, 'cert': cert})
        for c in r['cells']:
            if c['state'] in ('MISSING', 'NOT TESTED'):
                c['route'] = ('iCoA' if c['no'] in IN_HOUSE_CAPABLE else
                              'iCoA?' if c['no'] in IN_HOUSE_CONDITIONAL else
                              'OUTSOURCE')
            elif c['state'] == 'HELD':
                c['route'] = 'ruling'
            else:
                c['route'] = ''
        r['gaps'] = [c for c in r['cells']
                     if c['state'] in ('MISSING', 'NOT TESTED', 'IN-HOUSE')]
        r['icoa_rows'] = [c['no'] for c in r['cells'] if c['route'] in ('iCoA', 'iCoA?')]
        r['outsource_rows'] = [c['no'] for c in r['cells'] if c['route'] == 'OUTSOURCE']
    rows.sort(key=lambda r: (r['wave'], r['date'] or '9999-12-31', r['no'],
                             r['version']))
    return rows


# --- rendering ----------------------------------------------------------------
BOX = {'OUTSOURCED': '[x]', 'IN-HOUSE': '[x]', 'HELD': '[!]',
       'NOT TESTED': '[ ]', 'MISSING': '[ ]'}


def render(rows):
    W = 112
    print('=' * W)
    print('CERTIFICATE OF QUALITY — ISSUANCE SCHEDULE')
    print('%d CoQ documents, in the order they are to be issued' % len(rows))
    print('=' * W)
    wave = None
    for r in rows:
        if r['wave'] != wave:
            wave = r['wave']
            n = sum(1 for x in rows if x['wave'] == wave)
            print('\n' + '=' * W)
            print('WAVE %d — %s   (%d document%s)'
                  % (wave, WAVES[wave], n, '' if n == 1 else 's'))
            print('=' * W)
        print('\n%s   %s   %s   %s'
              % (r['code'], r['date'] or '(no date)', r['batch'],
                 r['strain'] or ''))
        head = '   spec %s' % (r['spec_code'] or 'NOT IN MASTER')
        if r['pp_batch'] and r['pp_batch'] != r['batch']:
            head += '   PP %s' % r['pp_batch']
        if r['supersedes']:
            head += '   supersedes %s' % r['supersedes']
        if r['version'] > 1:
            head += '   retest, tranche %s' % r['tranche']
        print(head)
        for c in r['cells']:
            val = c['value'] if c['value'] is not None else c['state']
            src = c['source'] or ''
            if c['route']:
                src = '-> ' + c['route']
            print('   %s %-4s %-30s %-22s %-20s %s'
                  % (BOX[c['state']], c['no'], c['parameter'][:30],
                     str(val)[:22], (c['cert'] or '')[:20], src))
        g = r['gaps']
        print('   %d of %d rows sourced from an accredited laboratory; %d gap%s'
              % (sum(1 for c in r['cells'] if c['state'] == 'OUTSOURCED'),
                 len(r['cells']), len(g), '' if len(g) == 1 else 's'))

    print('\n' + '=' * W)
    print('SUMMARY')
    print('=' * W)
    for w in sorted(WAVES):
        sel = [r for r in rows if r['wave'] == w]
        if not sel:
            continue
        ready = sum(1 for r in sel if not r['gaps'])
        print('  Wave %d  %-40s %3d documents, %d need no iCoA'
              % (w, WAVES[w], len(sel), ready))


def render_icoa(rows):
    """What must be produced to close the schedule, in the same order.

    Two registers, because two different things close a gap: an iCoA Purely
    Plant issues itself, and a fresh outsourced analysis it must commission.
    Listing them together would hide the second, which is the one with a lead
    time and a cost.
    """
    W = 112
    print('\n' + '=' * W)
    print('IN-HOUSE iCoA ISSUANCE REGISTER')
    print('same order as the CoQ schedule; one iCoA closes one CoQ')
    print('=' * W)
    print('%-17s %-16s %-11s %-17s %-5s %s'
          % ('iCoA', 'for CoQ', 'date', 'batch', 'rows', 'specification rows'))
    print('-' * W)
    n = 0
    for r in rows:
        if not r['icoa_rows']:
            continue
        n += 1
        print('%-17s %-16s %-11s %-17s %-5d %s'
              % ('QCiCoA %03d/%02d' % (r['no'], r['version']), r['code'],
                 r['date'] or '(no date)', r['batch'][:17], len(r['icoa_rows']),
                 ', '.join(r['icoa_rows'])))
    print('-' * W)
    print('%d iCoA document(s), covering %d batch(es).'
          % (n, len({r['batch'] for r in rows if r['icoa_rows']})))
    print('Rows 1, 2, 7 and 8 are in house. Row 3 (marked iCoA?) is in house only')
    print('if the HPLC identity method is qualified; otherwise it moves below.')

    print('\n' + '=' * W)
    print('OUTSOURCED RE-ANALYSIS REGISTER')
    print('rows no in-house iCoA can close - they need an accredited laboratory')
    print('=' * W)
    print('%-16s %-11s %-17s %-5s %s'
          % ('for CoQ', 'date', 'batch', 'rows', 'specification rows'))
    print('-' * W)
    m = 0
    for r in rows:
        if not r['outsource_rows']:
            continue
        m += 1
        print('%-16s %-11s %-17s %-5d %s'
              % (r['code'], r['date'] or '(no date)', r['batch'][:17],
                 len(r['outsource_rows']), ', '.join(r['outsource_rows'])))
    print('-' * W)
    print('%d CoQ(s) need outsourced re-analysis, covering %d batch(es).'
          % (m, len({r['batch'] for r in rows if r['outsource_rows']})))


def unaccounted(rows):
    """Retired QCCoA batches that produced no CoQ - they have no certificates."""
    covered = set()
    for r in rows:
        m = MS.spec_for(r['batch'])
        covered |= {r['batch']}
        if m:
            covered |= {m['batch'], m['pp_batch'], m['cultiv_batch_src']}
    return [b for b in QCCOA_001 + QCCOA_001_V02 if b not in covered]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=HERE + '/ecoa.sqlite')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--icoa-only', action='store_true')
    ap.add_argument('--tsv', action='store_true',
                    help='one row per CoQ per specification row, for a spreadsheet')
    a = ap.parse_args()
    rows = schedule(sqlite3.connect(a.db))
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1)); return
    if a.tsv:
        # One row per cell: the shape a reviewer can sort, filter and tick.
        print('\t'.join(['wave', 'wave_name', 'coq_code', 'coq_date', 'batch',
                         'pp_batch', 'strain', 'version', 'supersedes',
                         'tranche', 'spec_code', 'param_no', 'parameter',
                         'criterion', 'state', 'value', 'source', 'cert_code',
                         'route']))
        for r in rows:
            for c in r['cells']:
                print('\t'.join(str(x if x is not None else '') for x in [
                    r['wave'], WAVES[r['wave']], r['code'], r['date'] or '',
                    r['batch'], r['pp_batch'] or '', r['strain'] or '',
                    'v.%02d' % r['version'], r['supersedes'] or '', r['tranche'],
                    r['spec_code'] or '', c['no'], c['parameter'], c['criterion'],
                    c['state'], c['value'] or '', c['source'] or '',
                    c['cert'] or '', c['route']]))
        return
    if not a.icoa_only:
        render(rows)
    render_icoa(rows)
    left = unaccounted(rows)
    if left:
        print('\n' + '=' * 112)
        print('NOT ON THE SCHEDULE - %d retired QCCoA batch(es) with no certificate' % len(left))
        print('=' * 112)
        print('  ' + ', '.join(left))
        print('  Each still owes a CoQ. Nothing in the corpus covers them, so the')
        print('  originating eCoAs must be located before a CoQ can be compiled.')


if __name__ == '__main__':
    main()
