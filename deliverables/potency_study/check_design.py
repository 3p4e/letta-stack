#!/usr/bin/env python3
"""Independent truth/sanity check of the ImB potency-grade design.

Second opinion: re-verifies every design rule numerically from the emitted
grade_design_even.json (NOT by re-running the design code), then audits
EVERY Total-THC analysis result on file — register results (all dates),
same-batch repeat pairs, stability-study (SS) measurements, stock declared
values — against the strain grade windows.
"""
import json
from collections import defaultdict
from datetime import datetime

D = json.load(open('grade_design_even.json'))
DS = json.load(open('/home/user/letta-stack/deliverables/potency_study/potency_dataset.json'))

problems, notes = [], []
def prob(m): problems.append(m)

# canonical batch spelling (same normalization the design used)
ALIAS = {'CJ052501/1': 'CJ052501/01', 'CJ052501/2': 'CJ052501/02',
         'JD012603/2': 'JD012603/02', 'JD012603/2V': 'JD012603/02V',
         'OPM1024_01': 'OMP1024_01', 'BSS1024_01/1': 'BSS1024_01',
         'CJ082501-2': 'CJ082501/2', 'FB012601_1': 'FB012601/1',
         'JD012603_02': 'JD012603/02', 'JD012603_02V': 'JD012603/02V',
         'GRC102501_2': 'GRC102501/2'}
STRAIN_FIX = {'JellyDonutz': 'Jelly Donutz', 'Permanent Market': 'Permanent Marker'}
DISPLAY_STAR = {'GG012601': 'GG012601*', 'JD012601': 'JD012601*'}
REATTRIBUTE = {('JD112501', 'ППК26065'): 'JD112501*'}
canon = lambda b: DISPLAY_STAR.get(ALIAS.get(b, b), ALIAS.get(b, b))

# ---------------------------------------------------- A. structural checks
grade_of_batch = {}     # batch -> (strain, nominal, lower, upper)
windows = defaultdict(list)
for strain, entry in D['strains'].items():
    seen_grades = set()
    prev = None
    gaps_declared = set()
    for e in D['exceptions']:
        if e.startswith(strain + ':') and 'uncovered zone' in e:
            # "...between THCa and THCb..."
            import re
            m = re.search(r'between THC(\d+) and THC(\d+)', e)
            if m: gaps_declared.add((int(m.group(1)), int(m.group(2))))
    for g in entry:
        N, lo, up = g['nominal'], g['lower'], g['upper']
        windows[strain].append((N, lo, up))
        # A1 caps and decimals
        if not (round(lo, 2) == lo and round(up, 2) == up):
            prob(f"{strain} THC{N}: bounds not 2dp ({lo}, {up})")
        if lo < 0.9 * N - 1e-9: prob(f"{strain} THC{N}: lower {lo} breaches 0.90x cap {0.9*N:.2f}")
        if up > 1.1 * N + 1e-9: prob(f"{strain} THC{N}: upper {up} breaches 1.10x cap {1.1*N:.2f}")
        # A2 nominal inside, even (or flagged odd)
        if not (lo <= N <= up): prob(f"{strain} THC{N}: nominal outside [{lo},{up}]")
        if N % 2 and not g.get('odd'): prob(f"{strain} THC{N}: odd nominal not flagged")
        if N % 2 and not any(('ODD fallback' in f or 'odd shift' in f or 'odd nominal' in f)
                             and strain in f for f in D['flags']):
            prob(f"{strain} THC{N}: odd nominal without a recorded fallback/shift flag")
        # A3 tolerance arithmetic
        if abs(round(N - g['minus_tol'], 2) - lo) > 1e-9:
            prob(f"{strain} THC{N}: minus_tol {g['minus_tol']} != N - lower")
        if abs(round(N + g['plus_tol'], 2) - up) > 1e-9:
            prob(f"{strain} THC{N}: plus_tol {g['plus_tol']} != upper - N")
        if not g['symmetric'] or abs(g['minus_tol'] - g['plus_tol']) > 1e-9:
            prob(f"{strain} THC{N}: tolerance not symmetric ({g['minus_tol']}/{g['plus_tol']})")
        if abs((N - lo) - (up - N)) > 1e-9:
            prob(f"{strain} THC{N}: window not centred on nominal")
        want = f"{N}.00% ±{g['plus_tol']:.2f}% ({lo:.2f}% — {up:.2f}%)"
        if g['expression'] != want:
            prob(f"{strain} THC{N}: expression mismatch: {g['expression']!r} vs {want!r}")
        # A4 width
        if abs(g['width'] - round(up - lo, 2)) > 1e-9:
            prob(f"{strain} THC{N}: width field wrong")
        # A5 batches inside their window
        for b in g['batches']:
            if not (lo - 1e-9 <= b['v'] <= up + 1e-9):
                prob(f"{strain} THC{N}: batch {b['batch']} {b['v']} outside [{lo},{up}]")
            grade_of_batch[b['batch']] = (strain, N, lo, up)
        if N in seen_grades: prob(f"{strain}: duplicate grade THC{N}")
        seen_grades.add(N)
        # A6 ordering / contiguity / overlap
        if prev is not None:
            pN, plo, pup = prev
            if N >= pN: prob(f"{strain}: grades not strictly descending ({pN} then {N})")
            if lo >= plo or up >= plo:
                if up >= plo: prob(f"{strain}: THC{N} overlaps THC{pN}")
            if (pN, N) in gaps_declared:
                if up >= plo: prob(f"{strain}: declared gap {pN}/{N} but ranges touch/overlap")
            else:
                if abs(round(plo - 0.01, 2) - up) > 1e-9:
                    prob(f"{strain}: THC{pN}->THC{N} not contiguous ({plo} vs {up}) and no declared gap")
        prev = (N, lo, up)

def find_grade(strain, v):
    for N, lo, up in windows.get(strain, []):
        if lo - 1e-9 <= v <= up + 1e-9:
            return N
    return None

# batch -> anchor (the graded value)
anchor = {b: g for b, g in grade_of_batch.items()}

# ---------------------------------------------------- B. all register results
def pdate(s):
    try: return datetime.strptime(s, '%d.%m.%Y')
    except Exception: return datetime.min

by_batch = defaultdict(list)
for r in DS['register_results']:
    b = canon(r['batch'])
    b = REATTRIBUTE.get((b, r.get('cert')), b)
    by_batch[b].append(r)

cat = defaultdict(list)
for b, results in by_batch.items():
    results.sort(key=lambda r: pdate(r['date']))
    latest_date = pdate(results[-1]['date'])
    if b not in grade_of_batch:
        cat['batch-not-graded'].append(f"{b}: {[r['value'] for r in results]}")
        continue
    strain, N, lo, up = grade_of_batch[b]
    for r in results:
        v = float(r['value'])
        is_latest = pdate(r['date']) == latest_date
        tag = f"{b} {v:.2f} ({r['cert']}, {r['date']}, {r['lab']})"
        if is_latest and b != 'J31122501':
            # anchor value: must equal the graded value and sit in the assigned grade
            if lo - 1e-9 <= v <= up + 1e-9:
                cat['anchor-in-assigned-grade'].append(tag)
            else:
                g2 = find_grade(strain, v)
                cat['ANCHOR-OUTSIDE-ASSIGNED'].append(f"{tag} assigned THC{N} [{lo},{up}], falls in {g2}")
        else:
            g2 = find_grade(strain, v)
            if g2 == N:
                cat['superseded-in-same-grade'].append(tag)
            elif g2 is not None:
                cat['superseded-in-other-grade'].append(f"{tag} -> THC{g2} (assigned THC{N})")
            else:
                cat['superseded-now-outside-spec'].append(f"{tag} (assigned grade THC{N} on retest)")

# J31122501 special: dataset latest = hand-trimmed 19.84 (experimental), graded on 21.84
for r in by_batch.get('J31122501', []):
    v = float(r['value'])
    strain, N, lo, up = grade_of_batch['J31122501']
    g2 = find_grade(strain, v)
    notes.append(f"J31122501 result {v:.2f} ({r['cert']}, {r['date']}): falls in "
                 f"{'THC'+str(g2) if g2 else 'NO grade'}; graded on machine-trimmed 21.84 -> THC{N}")

# repeat pairs: first values explicitly
for rp in DS.get('repeats', []):
    strain = STRAIN_FIX.get(rp['strain'], rp['strain'])
    g1 = find_grade(strain, rp['first'])
    g2 = find_grade(strain, rp['second'])
    cat['repeat-pairs'].append(
        f"{rp['batch']}: first {rp['first']:.2f} ({rp['first_date']}) -> "
        f"{'THC'+str(g1) if g1 else 'OUTSIDE spec (superseded)'}; "
        f"retest {rp['second']:.2f} ({rp['second_date']}) -> THC{g2}")

# ---------------------------------------------------- C. stability (SS) results
for s in DS.get('stability', []):
    strain = STRAIN_FIX.get(s['strain'], s['strain'])
    v = s['total_thc']
    g = find_grade(strain, v)
    b = canon(s['batch'])
    asg = grade_of_batch.get(b, (None, None, None, None))[1]
    line = (f"{b} [{s['arm']}, M{s['month']}] {v:.2f} ({s['report']}) -> "
            f"{'THC'+str(g) if g else 'outside all grades'}; release grade THC{asg}")
    if '40' in s['arm']:
        cat['stability-40C-accelerated'].append(line)
    else:
        cat['stability-25C-longterm'].append(line)

# ---------------------------------------------------- D. batch census
graded = set(grade_of_batch)
in_results = set(by_batch)
stock_batches = {canon(s['batch']) for s in DS['stock']}
for b in sorted((in_results | stock_batches) - graded):
    cat['batch-not-graded'].append(b)

# ---------------------------------------------------- report
out = {'problems': problems, 'notes': notes,
       'categories': {k: v for k, v in cat.items()}}
json.dump(out, open('design_check.json', 'w'), ensure_ascii=False, indent=1)

print(f"STRUCTURAL PROBLEMS: {len(problems)}")
for p in problems: print('  !!', p)
print()
for k in ['anchor-in-assigned-grade', 'superseded-in-same-grade', 'superseded-in-other-grade',
          'superseded-now-outside-spec', 'ANCHOR-OUTSIDE-ASSIGNED', 'repeat-pairs',
          'stability-25C-longterm', 'stability-40C-accelerated', 'batch-not-graded']:
    v = cat.get(k, [])
    print(f"[{k}] {len(v)}")
    for line in v:
        print('   ', line)
    print()
print("NOTES:")
for n in notes: print('  *', n)
