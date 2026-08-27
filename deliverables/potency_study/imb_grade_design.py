#!/usr/bin/env python3
"""ImB spec potency-grade redesign: even whole-number nominals (v2).

Management rules (27.08.2026):
- nominal of every grade = whole EVEN number (nn.0), printed in the product
  code as THCnn : CBD1
- a grade's range extends at most 10% of the nominal to either side
  (lower >= 0.9*N, upper <= 1.1*N); bounds carry two decimals
- ranges within one strain must not overlap; the strongest grade is given
  the maximum range first, weaker grades take what remains
- every batch falls in exactly one grade; the owner's requested codes from
  the tranche 1-3 list are honored wherever the value permits
"""
import json
from datetime import datetime

DS = json.load(open('/home/user/letta-stack/deliverables/potency_study/potency_dataset.json'))
CONS = json.load(open('/home/user/letta-stack/deliverables/qc_register/consolidated.json'))

# ---------------------------------------------------------------- owner list
OWNER = {  # P-number or batch -> (requested even nominal, sheet value)
 'BG1024':(26,26.14),'BSS1024':(24,25.01),'P050162':(24,24.05),'P060032':(20,18.29),
 'P060352':(18,18.86),'P060402':(16,16.70),'P050092':(18,18.67),'P050152':(18,18.52),
 'P050022':(24,22.61),'P050322':(16,15.70),'HPA1024':(18,17.31),'P050052':(22,21.61),
 'P060212':(20,20.32),'P060152':(18,17.32),'OPM1024':(22,20.03),'P050062':(18,18.04),
 'P060242':(8,7.91),'P060062':(12,12.25),'P060382':(18,17.84),'P060122':(12,12.91),
 'P050192':(20,20.47),'P050222':(22,21.51),'P060022':(24,24.96),'P060072':(24,22.30),
 'P060372':(12,12.32),'P060132':(10,9.83),'P050282':(8,8.02),'P060322':(14,14.68),
 'GG1024':(14,13.34),'P050302':(20,19.81),'P050072':(24,25.45),'P050312':(20,21.29),
 'P060092':(24,25.73),'P060182':(12,11.53),'P050182':(22,20.39),'P060362':(16,16.71),
 'P060412':(20,20.54),'P060422':(16,15.16),'P060172':(18,17.40),'P050112':(16,16.82),
 'P050042':(16,15.38),'P060042':(10,9.43),'P050082':(16,16.55),'P060232':(12,13.00),
 'P060112':(16,15.63),'P060282':(18,17.13),'P060082':(10,10.96),'P060012':(22,21.67),
}
# register-audited corrections to the owner's sheet values
SHEET_FIX = {'P060172': 17.04, 'P060232': 13.33, 'P050192': 20.39}
# pending tranche-2 batches (sampled 12.08.2026, no eCoA yet) - manual map
MANUAL_P = {'P060122': 'ACC102501', 'P060372': 'CC012603', 'P060132': 'CF102501',
            'P060362': 'JD012603/01', 'P060112': 'PUM102501'}
# duplicate spellings in the dataset -> canonical register name
ALIAS = {'CJ052501/1': 'CJ052501/01', 'CJ052501/2': 'CJ052501/02',
         'JD012603/2': 'JD012603/02', 'JD012603/2V': 'JD012603/02V',
         'OPM1024_01': 'OMP1024_01', 'BSS1024_01/1': 'BSS1024_01',
         'CJ082501-2': 'CJ082501/2', 'FB012601_1': 'FB012601/1',
         'JD012603_02': 'JD012603/02', 'JD012603_02V': 'JD012603/02V',
         'GRC102501_2': 'GRC102501/2'}
# grading anchors that differ from a naive latest-date pick
VALUE_OVERRIDE = {  # batch -> (value, why)
 'J31122501': (21.84, 'machine-trimmed preparation, CoQ-forming (CoQ-PP-2026-0054); '
                      'hand-trimmed 19.84 is the experimental prep'),
}
STRAIN_FIX = {'JellyDonutz': 'Jelly Donutz', 'Permanent Market': 'Permanent Marker'}

def canon(b): return ALIAS.get(b, b)
def pdate(s):
    try: return datetime.strptime(s, '%d.%m.%Y')
    except Exception: return datetime.min

# ------------------------------------------------- latest anchor per batch
latest = {}
for r in DS['register_results']:
    b = canon(r['batch'])
    if b not in latest or pdate(r['date']) > pdate(latest[b]['date']):
        latest[b] = {'batch': b, 'strain': STRAIN_FIX.get(r['strain'], r['strain']),
                     'value': r['value'], 'date': r['date'],
                     'src': f"{r.get('cert','')}, {r['date']}, {r.get('lab','')}",
                     'basis': 'certificate'}
for s in DS['stock']:
    b = canon(s['batch'])
    if b not in latest:
        v = s.get('anchor') or s.get('declared')
        basis = 'certificate' if s.get('anchor') else 'declared (no eCoA yet)'
        src = (f"{s.get('anchor_date','')}, {s.get('anchor_lab','')}" if s.get('anchor')
               else 'owner-declared value')
        latest[b] = {'batch': b, 'strain': STRAIN_FIX.get(s['strain'], s['strain']),
                     'value': v, 'date': s.get('anchor_date') or '', 'src': src, 'basis': basis}
for b, (v, why) in VALUE_OVERRIDE.items():
    if b in latest:
        latest[b]['value'] = v; latest[b]['basis'] = 'certificate'
        latest[b]['src'] = why

# ------------------------------------------------- owner key -> batch
pmap = {r['p_number'].upper(): canon(r['batch']) for r in CONS['rows'] if r.get('p_number')}
pmap.update(MANUAL_P)
resolved, unmatched, value_notes = {}, [], []
for key, (nom, val) in OWNER.items():
    val = SHEET_FIX.get(key, val)
    b = canon(key) if canon(key) in latest else pmap.get(key)
    if b is None or b not in latest:
        unmatched.append((key, nom, val)); continue
    dv = latest[b]['value']
    if dv is not None and abs(float(dv) - val) > 0.005:
        value_notes.append(f"{key} ({b}): owner {val:.2f} vs dataset {float(dv):.2f} — owner value used")
    latest[b]['value'] = val
    resolved[b] = nom

# ------------------------------------------------- per-strain design
def feas(v, parity=2):
    """whole nominals holding v within +/-10%; parity=2 evens, parity=1 all"""
    step = 2 if parity == 2 else 1
    start = 2 if parity == 2 else 3
    return [N for N in range(start, 41, step)
            if 0.9 * N <= v + 1e-9 and v <= 1.1 * N + 1e-9]

def feas_odd(v):
    return [N for N in range(3, 41, 2)
            if 0.9 * N <= v + 1e-9 and v <= 1.1 * N + 1e-9]

strains = {}
for b, r in latest.items():
    if r['value'] is None: continue
    strains.setdefault(r['strain'], []).append(
        {'batch': b, 'v': round(float(r['value']), 2), 'req': resolved.get(b),
         'owner': b in resolved, 'src': r['src'], 'basis': r['basis']})

report, flags, exceptions = {}, [], []
for strain in sorted(strains):
    rows = sorted(strains[strain], key=lambda x: -x['v'])

    # 1. owner codes: validate feasibility (even first, odd fallback)
    for x in rows:
        if x['req'] is not None and x['req'] not in feas(x['v']):
            cands = feas(x['v']) or feas_odd(x['v'])
            new = min(cands, key=lambda N: (abs(N - x['v']), -N)) if cands else None
            odd = ' (ODD fallback)' if new is not None and new % 2 else ''
            flags.append(f"{strain} / {x['batch']}: owner code THC{x['req']} infeasible for "
                         f"{x['v']:.2f} (max window {0.9*x['req']:.2f}-{1.1*x['req']:.2f}) -> THC{new}{odd}")
            x['req'] = new

    # 2. uncoded batches: join an existing grade when feasible, else create one
    #    (even nominals preferred; adjacent odd nominal only when no even fits —
    #     management rule 27.08.2026)
    for x in rows:
        if x['req'] is None:
            cands = feas(x['v'])
            if not cands:
                cands = feas_odd(x['v'])
                if not cands:
                    exceptions.append(f"{strain} / {x['batch']}: {x['v']:.2f} ({x['basis']}) fits NO "
                                      f"whole-number nominal within +/-10% — excluded pending re-test")
                    x['req'] = 'EXC'; continue
                pick = min(cands, key=lambda N: (abs(N - x['v']), -N))
                flags.append(f"{strain} / {x['batch']}: {x['v']:.2f} fits no even nominal "
                             f"(even-ladder dead zone) -> ODD fallback THC{pick} "
                             f"[{0.9*pick:.2f}-{1.1*pick:.2f}]")
                x['req'] = pick; continue
            gset = {y['req'] for y in rows if isinstance(y['req'], int)}
            ing = [N for N in cands if N in gset]
            pool = ing if ing else cands
            x['req'] = min(pool, key=lambda N: (abs(N - x['v']), -N))  # tie -> higher

    rows_g = [x for x in rows if isinstance(x['req'], int)]

    # 3. value-order repair: no batch may sit at/above a weaker bound of a stronger grade
    changed = True
    while changed:
        changed = False
        gset = sorted({x['req'] for x in rows_g}, reverse=True)
        for i, N in enumerate(gset[:-1]):
            vminN = min(x['v'] for x in rows_g if x['req'] == N)
            for x in rows_g:
                if x['req'] < N and x['v'] >= vminN:
                    note = ' (owner-coded!)' if x['owner'] else ''
                    flags.append(f"{strain} / {x['batch']}: {x['v']:.2f} coded THC{x['req']} sits above "
                                 f"weakest THC{N} batch ({vminN:.2f}) -> re-coded THC{N}{note}")
                    x['req'] = N; changed = True

    # 4. windows: chain strongest -> weakest
    gset = sorted({x['req'] for x in rows_g}, reverse=True)
    grades, prev_lower = [], None
    for i, N in enumerate(gset):
        mem = [x for x in rows_g if x['req'] == N]
        vmin, vmax = min(x['v'] for x in mem), max(x['v'] for x in mem)
        nxt = gset[i + 1] if i + 1 < len(gset) else None
        lo_cap, hi_cap = round(0.9 * N, 2), round(1.1 * N, 2)
        upper = hi_cap if prev_lower is None else min(hi_cap, round(prev_lower - 0.01, 2))
        lower = lo_cap
        if nxt is not None:
            below = [x for x in rows_g if x['req'] < N]
            need = [lo_cap, round(nxt + 0.01, 2)]
            if below: need.append(round(max(x['v'] for x in below) + 0.01, 2))
            lower = max(need)
        ok = (lower <= vmin + 1e-9 and vmax <= upper + 1e-9 and lower <= N <= upper)
        if not ok:
            flags.append(f"{strain} THC{N}: window [{lower:.2f},{upper:.2f}] cannot hold "
                         f"batches [{vmin:.2f},{vmax:.2f}] + nominal — CONFLICT")
        grades.append({'nominal': N, 'lower': lower, 'upper': upper,
                       'width': round(upper - lower, 2), 'odd': bool(N % 2),
                       'full': (lower == lo_cap and upper == hi_cap),
                       'batches': [{'batch': x['batch'], 'v': x['v'], 'owner_req': x['owner'],
                                    'src': x['src'], 'basis': x['basis']}
                                   for x in sorted(mem, key=lambda y: -y['v'])]})
        prev_lower = lower
    # final assertions
    for i in range(len(grades) - 1):
        assert grades[i]['lower'] > grades[i + 1]['upper'], f"{strain}: overlap"
    for g in grades:
        N = g['nominal']
        assert g['lower'] >= 0.9 * N - 1e-9 and g['upper'] <= 1.1 * N + 1e-9
        assert g['lower'] <= N <= g['upper'], f"{strain} THC{N}: nominal outside window"
        for bb in g['batches']:
            assert g['lower'] - 1e-9 <= bb['v'] <= g['upper'] + 1e-9, \
                f"{strain} THC{N}: {bb['batch']} {bb['v']} outside"
    report[strain] = grades

STRAIN_CODE = {
 'Amnesia Core Cut': 'ACC', 'Apple and Banana': 'AB', 'Blue Gelato': 'BG',
 'Blue Sunset Sherbet': 'BSS', 'Cap Junky': 'CJ', 'Cash Cow': 'CC',
 'Chem Flyer': 'CF', 'Clemosa a bud': 'CLE', 'Fat Bastard': 'FB',
 'Gorilla Glue': 'GG', 'Grape Pie': 'GP', 'Graps & Creme': 'GRC',
 'High Pro Amnesia': 'HPA', 'Jelly Donutz': 'JD', 'Jokerz 31': 'J31',
 'Kush Crasher': 'KC', 'Motor Breath': 'MB', 'Orange Punch Mimosa': 'OPM',
 'Permanent Marker': 'PM', 'Pure Michigen': 'PUM', 'Scrambler': 'SCR',
 'Sleepy Joy': 'SJ', 'Wedding Cake': 'WED', 'Wedding Crasher': 'WC'}

def strain_code(strain, grades):
    return STRAIN_CODE[strain]

roman = ['I', 'II', 'III', 'IV', 'V', 'VI']
out = {'strains': {}, 'flags': flags, 'exceptions': exceptions,
       'unmatched': unmatched, 'value_notes': value_notes}
for strain, grades in report.items():
    sc = strain_code(strain, grades)
    entry = []
    for i, g in enumerate(grades):
        entry.append({**g, 'grade': roman[i], 'strain_code': sc,
                      'product_code': f"{sc}_THC{g['nominal']}:CBD1",
                      'spec_code': f"QCSP_001_{sc}-{roman[i]}"})
    out['strains'][strain] = entry
json.dump(out, open('grade_design_even.json', 'w'), ensure_ascii=False, indent=1)

for strain, entry in out['strains'].items():
    print(f"== {strain} ({entry[0]['strain_code']}) ==")
    for g in entry:
        tag = ('FULL +/-10%' if g['full'] else f"width {g['width']:.2f}") + (' ODD' if g['odd'] else '')
        bl = ', '.join(f"{b['batch']} {b['v']:.2f}{'*' if not b['owner_req'] else ''}"
                       + ('!' if b['basis'].startswith('declared') else '')
                       for b in g['batches'])
        print(f"  {g['grade']:>3s}  {g['product_code']:<18s} {g['lower']:6.2f} - {g['upper']:6.2f}  [{tag:12s}]  {bl}")
    print()
print('(* = code assigned by value, not in owner list; ! = declared value, no eCoA yet)\n')
print('FLAGS:');      [print(' *', f) for f in flags]
print('EXCEPTIONS:'); [print(' *', e) for e in exceptions]
print('VALUE NOTES:');[print(' *', n) for n in value_notes]
print('UNMATCHED:', unmatched)
