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
# dataset misattribution fix (truth-check finding, 27.08.2026): cert ППК26065
# (13.93, CNP, 11.05.2026) prints серија JD112501* — the milled presentation,
# a separate register row — not JD112501 (whole flower, retest 20.32)
REATTRIBUTE = {('JD112501', 'ППК26065'): 'JD112501*'}
# certificates print the milled marker; restore it in display names
DISPLAY_STAR = {'GG012601': 'GG012601*', 'JD012601': 'JD012601*'}

def canon(b): return ALIAS.get(b, b)
def pdate(s):
    try: return datetime.strptime(s, '%d.%m.%Y')
    except Exception: return datetime.min

# ------------------------------------------------- latest anchor per batch
latest = {}
for r in DS['register_results']:
    b = canon(r['batch'])
    b = REATTRIBUTE.get((b, r.get('cert')), b)
    b = DISPLAY_STAR.get(b, b)
    if b not in latest or pdate(r['date']) > pdate(latest[b]['date']):
        latest[b] = {'batch': b, 'strain': STRAIN_FIX.get(r['strain'], r['strain']),
                     'value': r['value'], 'date': r['date'],
                     'src': f"{r.get('cert','')}, {r['date']}, {r.get('lab','')}",
                     'basis': 'certificate'}
for s in DS['stock']:
    b = DISPLAY_STAR.get(canon(s['batch']), canon(s['batch']))
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
pmap = {r['p_number'].upper(): DISPLAY_STAR.get(canon(r['batch']), canon(r['batch']))
        for r in CONS['rows'] if r.get('p_number')}
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

    # 4. SYMMETRIC ladder (management rule 27.08.2026): every grade is
    #    nominal +/- t with EQUAL tolerance above and below. Contiguity then
    #    binds neighbours by the equality  t_s + t_w = (N_s - N_w) - 0.01,
    #    chaining every tolerance to the top grade's. Where the initially
    #    selected even nominal cannot carry a symmetric window under all
    #    rules, the nominal shifts to the adjacent ODD whole number.
    import itertools
    TMIN = 0.50

    def tcap(N):
        return round(0.10 * N, 2)

    # batch clusters, strongest first (E = initially selected even nominal)
    gset = sorted({x['req'] for x in rows_g}, reverse=True)
    clusters = []
    for N in gset:
        mem = [x for x in rows_g if x['req'] == N]
        clusters.append({'E': N, 'vmin': min(x['v'] for x in mem),
                         'vmax': max(x['v'] for x in mem), 'mem': mem})

    def creq(N, c):
        return round(max(N - c['vmin'], c['vmax'] - N, TMIN), 2)

    def solve_chain(ladder, reqs):
        """maximize t of the strongest grade; all t chained by contiguity."""
        a, s = [0.0], [1]
        for i in range(1, len(ladder)):
            g = round(ladder[i - 1] - ladder[i] - 0.01, 2)
            a.append(round(g - a[i - 1], 4)); s.append(-s[i - 1])
        lo, hi = -1e9, 1e9
        for i, N in enumerate(ladder):
            lo_i, hi_i = reqs[i], tcap(N)
            if lo_i > hi_i + 1e-9: return None
            if s[i] > 0:
                lo = max(lo, lo_i - a[i]); hi = min(hi, hi_i - a[i])
            else:
                lo = max(lo, a[i] - hi_i); hi = min(hi, a[i] - lo_i)
        if lo > hi + 1e-9: return None
        t0 = round(hi, 2)
        ts = [round(a[i] + s[i] * t0, 2) for i in range(len(ladder))]
        for i, N in enumerate(ladder):
            if ts[i] < reqs[i] - 1e-9 or ts[i] > tcap(N) + 1e-9: return None
        return ts

    def solve_segment(cl):
        """cl: descending cluster list. Returns (rank, ladder, is_res, ts) or None."""
        opts = []
        for c in cl:
            o = []
            for N in (c['E'], c['E'] + 1, c['E'] - 1):
                if N >= 2 and creq(N, c) <= tcap(N) + 1e-9:
                    o.append(N)
            if not o: return None
            opts.append(o)
        best = None
        for combo in itertools.product(*opts):
            if any(combo[i] <= combo[i + 1] for i in range(len(combo) - 1)):
                continue
            gap_opts = []
            for i in range(len(combo) - 1):
                mids = list(range(combo[i + 1] + 1, combo[i]))
                subs = [()]
                for r in (1, 2, 3):
                    subs += [tuple(sorted(ss, reverse=True))
                             for ss in itertools.combinations(mids, r)]
                gap_opts.append(subs)
            for resv in itertools.product(*gap_opts):
                ladder, reqs, is_res = [], [], []
                for i, N in enumerate(combo):
                    ladder.append(N); reqs.append(creq(N, cl[i])); is_res.append(False)
                    if i < len(resv):
                        for M in resv[i]:
                            ladder.append(M); reqs.append(TMIN); is_res.append(True)
                if any(ladder[j] <= ladder[j + 1] for j in range(len(ladder) - 1)):
                    continue
                ts = solve_chain(ladder, reqs)
                if ts is None: continue
                n_ob = sum(1 for j, N in enumerate(ladder) if not is_res[j] and N % 2)
                n_or = sum(1 for j, N in enumerate(ladder) if is_res[j] and N % 2)
                n_r = sum(is_res)
                shift = sum(abs(N - c['E']) for N, c in zip(combo, cl))
                rank = (n_ob, n_or, n_r, tuple(-t for t in ts), shift)
                if best is None or rank < best[0]:
                    best = (rank, ladder, is_res, ts, combo)
        return best

    # segment splitting: only where the bottom cluster lives below 10% and
    # nothing (reserves, odd shifts) can join it — the permitted floater rule
    segments, gaps = [], []
    todo = clusters
    while todo:
        sol = solve_segment(todo)
        if sol is not None:
            segments.append((todo, sol)); todo = []
        elif len(todo) > 1 and todo[-1]['E'] < 10:
            top, bottom = todo[:-1], todo[-1:]
            sol_top = solve_segment(top)
            if sol_top is not None:
                segments.append((top, sol_top)); todo = bottom
            else:
                flags.append(f"{strain}: symmetric ladder UNSOLVABLE — CONFLICT"); todo = []
        else:
            flags.append(f"{strain}: symmetric ladder UNSOLVABLE — CONFLICT"); todo = []

    grades = []
    prev_seg_bottom = None
    for cl, (rank, ladder, is_res, ts, combo) in segments:
        # owner-code nominal shifts -> flags
        for N, c in zip(combo, cl):
            if N != c['E']:
                who = ', '.join(x['batch'] for x in c['mem'])
                own = any(x['owner'] for x in c['mem'])
                flags.append(f"{strain}: THC{c['E']} -> THC{N} (odd shift for symmetric "
                             f"tolerance){' [owner-coded]' if own else ''}: {who}")
        cmap = {N: c for N, c in zip(combo, cl)}
        if prev_seg_bottom is not None:
            za = round(prev_seg_bottom, 2); zb = round(ladder[0] + ts[0], 2)
            gaps.append((ladder[0], round(zb + 0.01, 2), za))
        for j, N in enumerate(ladder):
            t = ts[j]
            lo, up = round(N - t, 2), round(N + t, 2)
            mem = cmap.get(N, {}).get('mem', []) if not is_res[j] else []
            grades.append({'nominal': N, 'lower': lo, 'upper': up, 'tol': t,
                           'width': round(2 * t, 2), 'odd': bool(N % 2),
                           'bridge': is_res[j],
                           'full': abs(t - tcap(N)) < 1e-9,
                           'batches': [{'batch': x['batch'], 'v': x['v'],
                                        'owner_req': x['owner'], 'src': x['src'],
                                        'basis': x['basis']}
                                       for x in sorted(mem, key=lambda y: -y['v'])]})
        prev_seg_bottom = round(ladder[-1] - ts[-1], 2)
    gap_pairs = set()
    if len(segments) == 2:
        upN = segments[0][1][1][-1]; dnN = segments[1][1][1][0]
        gap_pairs.add((upN, dnN))
        za = round(segments[1][1][1][0] + segments[1][1][3][0] + 0.01, 2)
        zb = round(segments[0][1][1][-1] - segments[0][1][3][-1] - 0.01, 2)
        exceptions.append(f"{strain}: uncovered zone {za:.2f}-{zb:.2f} between "
                          f"THC{upN} and THC{dnN} (sub-10% territory — ladder cannot "
                          f"join symmetrically; permitted per rule)")

    # final assertions
    for i in range(len(grades) - 1):
        upg, dng = grades[i], grades[i + 1]
        assert upg['lower'] > dng['upper'], f"{strain}: overlap {upg['nominal']}/{dng['nominal']}"
        if (upg['nominal'], dng['nominal']) not in gap_pairs:
            assert abs(upg['lower'] - 0.01 - dng['upper']) < 1e-9, \
                f"{strain}: {upg['nominal']}/{dng['nominal']} not contiguous"
    for g in grades:
        N, t = g['nominal'], g['tol']
        assert abs((N - g['lower']) - (g['upper'] - N)) < 1e-9, f"{strain} THC{N}: not symmetric"
        assert t <= tcap(N) + 1e-9 and t >= TMIN - 1e-9
        assert g['lower'] <= N <= g['upper']
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

roman = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
out = {'strains': {}, 'flags': flags, 'exceptions': exceptions, 'note_retest': 'anchors are the latest (retest) results per batch — retest values are CoQ-forming; superseded pre-retest results are out of spec scope',
       'unmatched': unmatched, 'value_notes': value_notes}
for strain, grades in report.items():
    sc = strain_code(strain, grades)
    entry = []
    for i, g in enumerate(grades):
        N = g['nominal']
        tminus = round(N - g['lower'], 2)
        tplus = round(g['upper'] - N, 2)
        if abs(tminus - tplus) < 0.005:
            expr = f"{N}.00% ±{tplus:.2f}% ({g['lower']:.2f}% — {g['upper']:.2f}%)"
        else:
            expr = (f"{N}.00% +{tplus:.2f}%/−{tminus:.2f}% "
                    f"({g['lower']:.2f}% — {g['upper']:.2f}%)")
        entry.append({**g, 'grade': roman[i], 'strain_code': sc,
                      'minus_tol': tminus, 'plus_tol': tplus,
                      'symmetric': abs(tminus - tplus) < 0.005,
                      'expression': expr,
                      'product_code': f"{sc}_THC{N}:CBD1",
                      'spec_code': f"QCSP_001_{sc}-{roman[i]}"})
    out['strains'][strain] = entry
json.dump(out, open('grade_design_even.json', 'w'), ensure_ascii=False, indent=1)

for strain, entry in out['strains'].items():
    print(f"== {strain} ({entry[0]['strain_code']}) ==")
    for g in entry:
        tag = ('FULL +/-10%' if g['full'] else f"width {g['width']:.2f}") + (' ODD' if g['odd'] else '')
        bl = ', '.join(f"{b['batch']} {b['v']:.2f}{'*' if not b['owner_req'] else ''}"
                       + ('!' if b['basis'].startswith('declared') else '')
                       for b in g['batches']) or '— reserve grade (no current batch)'
        print(f"  {g['grade']:>3s}  {g['product_code']:<18s} {g['lower']:6.2f} - {g['upper']:6.2f}  [{tag:12s}]  {bl}")
    print()
print('(* = code assigned by value, not in owner list; ! = declared value, no eCoA yet)\n')
print('FLAGS:');      [print(' *', f) for f in flags]
print('EXCEPTIONS:'); [print(' *', e) for e in exceptions]
print('VALUE NOTES:');[print(' *', n) for n in value_notes]
print('UNMATCHED:', unmatched)
