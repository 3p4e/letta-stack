#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Potency grades on the certificates against the potency builder on KVM4, and every THC result against its ranges.

    python3 tracker/audit_potency_kvm4_2026-10-07.py            # reads the committed snapshot
    python3 tracker/audit_potency_kvm4_2026-10-07.py --fetch    # refreshes the snapshot from KVM4 first

Head of QC, 07.10.2026: check every Tranche 3 certificate of quality, initial and retest, for its specification
document code, its potency specification (nominal, tolerance, range) and its product code. Check them against the
latest potency grades and ranges, which are those held by the potency builder deployed on KVM4. Then check, for
every Purely Plant strain, that every potency result from any source (initial, retest, stability study,
standalone) is accounted for, and that the strain has enough ranges to cover the THC result of every production
batch.

The builder (`https://specs.srv1231216.hstgr.cloud`) is read two ways:

* `GET /api/specs` gives each strain's saved ranges (nominal, tolerance, low, high) and its status;
* the page's `DATA` holds the results the builder rests on (initial, retest, stability; certificate, batch, P lot).

Both are kept in `KVM4_POTENCY_SNAPSHOT_2026-10-07.json`, so the audit reruns without the server. The builder
gives no numerals. A grade's numeral, and with it the specification code `QCSP_001_{ABBR}-{numeral}_v.01`, comes
from `potency_grades_2026-09-15.csv`: same strain, same nominal.

THC results are gathered from every committed source. Each source and its key:

| source | what it reads |
| --- | --- |
| `register` | the printed Total Δ9-THC of every certificate of quality, and the results its `also` field names |
| `corpus` | the eCoA corpus (`ingestion/ecoa_runner/records_corpus.json`), parameter `total_thc` |
| `cnp-cache` | the CNP certificates in the RAGflow page-text cache (`Вкупно Δ9-THC` line) |
| `intake` | the two-read files of the 220-К, 227-К, gaps and sweep intakes |
| `builder` | the builder's own `DATA` |

Each result is labelled by kind: `release`, `retest` or `stability` where its source says so, otherwise `standalone`.
A result is *accounted for* when the builder's `DATA` holds the same value, to 0.01, for the same batch or P lot.
It is *covered* when it lies in a saved range of its strain.

Writes `POTENCY_COQ_KVM4_2026-10-07.tsv` (one row per certificate of quality) and `POTENCY_RESULTS_KVM4_2026-10-07.tsv`
(one row per distinct result), and prints the findings. Exit 1 on a Tranche 3 or out-of-tranche certificate whose
grade, window, specification code or product code disagrees with the builder.
"""
import ast
import csv
import glob
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(GAP))
sys.path.insert(0, HERE)
sys.path.insert(0, GAP)
import audit_empty_results as A                                    # noqa: E402
import potency_grading as PG                                        # noqa: E402

URL = 'https://specs.srv1231216.hstgr.cloud/'
SNAP = os.path.join(HERE, 'KVM4_POTENCY_SNAPSHOT_2026-10-07.json')
OUT_COQ = os.path.join(HERE, 'POTENCY_COQ_KVM4_2026-10-07.tsv')
OUT_RES = os.path.join(HERE, 'POTENCY_RESULTS_KVM4_2026-10-07.tsv')
OUT_STR = os.path.join(HERE, 'POTENCY_STRAINS_KVM4_2026-10-07.tsv')
GRADES = os.path.join(GAP, 'potency_grades_2026-09-15.csv')
REG = os.path.join(GAP, 'coq_artifact_data.json')
BATCH_DATES = os.path.join(GAP, 'batch_dates_2026-09-10.csv')
CORPUS = os.path.join(ROOT, 'ingestion', 'ecoa_runner', 'records_corpus.json')
CRIT = re.compile(r'([\d.]+)\s*[–-]\s*([\d.]+)\s*%\s*\(grade\s*(\w+),\s*nominal\s*([\d.]+)\s*±\s*([\d.]+)\)')
NUM = re.compile(r'^\s*(\d+(?:[.,]\d+)?)\s*(?:%|$|\s)')


def _get(path):
    req = urllib.request.Request(URL + path, headers={'accept': 'application/json, text/html'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8')


def page_data(page):
    """The builder page's `const DATA = [...]`, read by bracket matching (it is JSON)."""
    k = page.index('const DATA = ') + len('const DATA = ')
    depth, ins, esc = 0, False, False
    for n in range(k, len(page)):
        c = page[n]
        if ins:
            esc = (not esc and c == '\\')
            if c == '"' and not esc:
                ins = False
            continue
        if c == '"':
            ins = True
        elif c == '[':
            depth += 1
        elif c == ']':
            depth -= 1
            if not depth:
                return json.loads(page[k:n + 1])
    raise SystemExit('DATA not found on the builder page')


def fetch():
    snap = {'url': URL, 'version': json.loads(_get('api/version')).get('version'),
            'specs': json.loads(_get('api/specs'))['specs'], 'data': page_data(_get(''))}
    with open(SNAP, 'w', encoding='utf-8') as fh:
        json.dump(snap, fh, ensure_ascii=False, indent=1)
    return snap


def value(s):
    m = NUM.match(str(s or '').replace(',', '.'))
    return round(float(m.group(1)), 2) if m else None


def numerals():
    out = {}
    with open(GRADES, encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            out[(r['abbr'], float(r['nominal']))] = r['numeral']
    return out


def lots(reg):
    """Normalised cultivation batch <-> P lot, from the register and the owner's workbook."""
    p2b, b2p = {}, {}
    pairs = [(c.get('cb'), c.get('pp')) for c in reg['coqs']]
    with open(BATCH_DATES, encoding='utf-8') as fh:
        pairs += [(r['batch'], r['p_batch']) for r in csv.DictReader(fh)]
    for cb, pp in pairs:
        if cb and pp and re.match(r'^P\d{6}$', pp):
            p2b.setdefault(A.N(pp), cb)
            b2p.setdefault(A.N(cb), pp)
    return p2b, b2p


def collect(reg, data, specs, p2b):
    """(strain abbr, batch, P lot, value, kind, source, certificate) for every THC result on file."""
    out = []

    strain_of = {}
    for c in reg['coqs']:
        a = PG.abbr_of(c.get('cb'), c.get('strain'))
        for k in (c.get('pp'), c.get('cb')):
            if a and k:
                strain_of.setdefault(A.N(k), a)

    def add(batch, pp, strain, v, kind, src, cert, note=''):
        if v is None:
            return
        batch = re.sub(r'^PO(\d{5})$', r'P0\1', str(batch or '').strip())     # "PO50022" in the corpus
        if re.match(r'^P\d{6}$', batch):                              # a P lot where the batch belongs
            batch, pp = '', pp or batch
        if not batch and pp:
            batch = p2b.get(A.N(pp), '')
        a = PG.abbr_of(batch, strain) or PG.abbr_of(pp, strain) or strain_of.get(A.N(pp)) or strain_of.get(A.N(batch))
        out.append((a, batch or '', pp or '', v, kind, src, cert or '', note))

    for c in reg['coqs']:
        if c.get('withdrawn'):
            continue
        r4 = next((r for r in c['rows'] if r['no'] == '4'), {})
        kind = 'retest' if 'retest' in (c.get('t') or '') else 'release'
        add(c.get('cb'), c.get('pp'), c.get('strain'), value(r4.get('res')), kind, 'register', r4.get('doc'))
        for v, cert in re.findall(r'(\d+[.,]\d+)\s*\(([^)]+)\)', r4.get('also') or ''):
            add(c.get('cb'), c.get('pp'), c.get('strain'), value(v), 'standalone', 'register-also', cert)
    for r in json.load(open(CORPUS, encoding='utf-8')):
        for p in r.get('parameters') or []:
            if p.get('parameter') == 'total_thc':
                kind = {'release': 'release', 'stability': 'stability'}.get(r.get('test_type'), 'standalone')
                add(r.get('batch_canonical'), r.get('p_number') if re.match(r'^P\d{6}$', str(r.get('p_number'))) else '',
                    r.get('strain'), value(p.get('result_numeric') if p.get('result_numeric') is not None
                                           else p.get('result_printed')), kind, 'corpus', r.get('cert_code'))
    for x in json.load(open(A.CACHE, encoding='utf-8')):
        m = x.get('meta') or {}
        if isinstance(m, str):
            try:
                m = ast.literal_eval(m)
            except (ValueError, SyntaxError):
                continue
        if m.get('lab') != 'CNP':
            continue
        text = x.get('text') or ''
        hit = re.search(A.CNP_LINES['total_thc'], text)
        if hit:
            kind = {'RELEASE': 'release', 'STABILITY': 'stability'}.get(m.get('test_type'), 'standalone')
            # the certificate's own footnote: total = Δ9-THC + 0.877 × Δ9-THCA; a printed total that is not
            # is reported, never replaced
            th = re.search(r'Содржина на Δ9-THC\s*\|[^|\n]*\|\s*([\d.,]+)', text)
            ta = re.search(r'Содржина на Δ9-THCA\s*\|[^|\n]*\|\s*([\d.,]+)', text)
            note, v = '', value(hit.group(1))
            if th and ta and v is not None:
                calc = value(th.group(1)) + 0.877 * value(ta.group(1))
                if abs(calc - v) > 0.1:
                    note = ('the certificate prints total Δ9-THC %.2f; its own Δ9-THC %s + 0.877 × Δ9-THCA %s = %.2f'
                            % (v, th.group(1), ta.group(1), calc))
            add(m.get('batch_canonical'), '', m.get('strain') or '', v, kind, 'cnp-cache', m.get('cert_code'), note)
    for f in glob.glob(os.path.join(GAP, 'intake_220K_*', 'reads_220K.json')):
        for k, r in json.load(open(f, encoding='utf-8')).items():
            res = r.get('results_flat')
            res = ast.literal_eval(res) if isinstance(res, str) else (res or {})
            add(r.get('batch_printed') or '', r.get('p_number'), r.get('strain_printed'), value(res.get('Total THC')),
                'retest', 'intake', r.get('cert_code'))
    for f in glob.glob(os.path.join(GAP, 'intake_227K_*', 'reads_227K.json')):
        for k, r in json.load(open(f, encoding='utf-8')).items():
            res = r.get('results') or {}
            add(r.get('batch_printed'), r.get('p_number'), r.get('strain_printed'), value(res.get('Total THC')),
                'retest', 'intake', r.get('cert_code'))
    for f in glob.glob(os.path.join(GAP, 'intake_*', 'reads_A.json')):
        for x in json.load(open(f, encoding='utf-8')):
            r = json.loads(x['raw']) if isinstance(x.get('raw'), str) else (x.get('raw') or {})
            for p in r.get('parameters') or []:
                if p.get('parameter') == 'total_thc':
                    add(r.get('batch_canonical'), '', r.get('strain'), value(p.get('result_numeric')), 'standalone',
                        'intake', r.get('cert_code'))
    for a, _, res, _, _ in data:
        for v, cb, cert, meta in res:
            kind = {'initial': 'release'}.get(meta.get('k'), meta.get('k'))
            for pp in (meta.get('p') or '').split(' / '):
                out.append((a, cb, pp.strip(), round(float(v), 2), kind, 'builder', cert, ''))
    for s in specs:
        for v in s.get('results_entered') or []:
            out.append((s['id'], '', '', round(float(v), 2), 'standalone', 'builder-entered', '', ''))
    return out


def main(argv):
    snap = fetch() if '--fetch' in argv else json.load(open(SNAP, encoding='utf-8'))
    specs = {s['id']: s for s in snap['specs']}
    num = numerals()
    reg = json.load(open(REG, encoding='utf-8'))
    p2b, b2p = lots(reg)
    tm = A.tranche_map()

    def tranche(c):
        for k in (c.get('pp'), c.get('cb'), (c.get('cb') or '').replace('＊', '')):
            if k and k in tm:
                return tm[k]
        return 'outside'

    def ranges(a):
        return sorted(specs.get(a, {}).get('ranges', []), key=lambda r: -r['nominal'])

    # ---- 1. every certificate of quality against the builder
    coq, bad = [], []
    for c in reg['coqs']:
        if c.get('withdrawn'):
            continue
        r4 = next((r for r in c['rows'] if r['no'] == '4'), {})
        thc = value(r4.get('res'))
        a = PG.abbr_of(c.get('cb'), c.get('strain'))
        hit = [r for r in ranges(a) if thc is not None and r['lo'] <= thc <= r['hi']]
        m = CRIT.search(r4.get('crit') or '')
        t = tranche(c)
        row = [c['regcode'][:13], t, 'retest' if 'retest' in (c.get('t') or '') else 'initial', c.get('cb') or '',
               c.get('pp') or '', a or '', r4.get('res') or '', c.get('grade') or '', c.get('spec') or '',
               c.get('pcode') or '', r4.get('crit') or '']
        why = []
        if thc is None:
            why.append('no Total THC printed')
        elif not hit:
            why.append('%.2f %% is in no range of %s' % (thc, a))
        else:
            g = hit[0]                                  # the higher nominal first, as potency_grading grades
            n = num.get((a, float(g['nominal'])), '(none)')
            spec = 'QCSP_001_%s-%s_v.01' % (a, n)
            pcode = '%s_THC%d : CBD1' % (a, round(g['nominal']))
            row += ['%s %g ± %g (%.2f – %.2f)' % (n, g['nominal'], g['tol'], g['lo'], g['hi']), spec, pcode]
            if c.get('grade') != n:
                why.append('grade %s, builder %s' % (c.get('grade'), n))
            if c.get('spec') != spec or (c.get('spc') or {}).get('code') != spec:
                why.append('specification %s, builder %s' % (c.get('spec'), spec))
            if c.get('pcode') != pcode:
                why.append('product code %s, builder %s' % (c.get('pcode'), pcode))
            if not m:
                why.append('criterion not read: %r' % r4.get('crit'))
            else:
                lo, hi, rn, nom, tol = m.groups()
                if (round(float(lo), 2), round(float(hi), 2), float(nom), round(float(tol), 2)) != \
                        (round(g['lo'], 2), round(g['hi'], 2), float(g['nominal']), round(g['tol'], 2)):
                    why.append('window %s – %s (%s ± %s), builder %.2f – %.2f (%g ± %g, %s)' % (
                        lo, hi, nom, tol, g['lo'], g['hi'], g['nominal'], g['tol'], specs[a]['status']))
            if len(hit) > 1:
                why.append('note: %.2f lies in %d overlapping ranges (%s); the higher nominal is taken' % (
                    thc, len(hit), ', '.join('%.2f – %.2f' % (r['lo'], r['hi']) for r in hit)))
        while len(row) < 14:
            row.append('')
        row.append('; '.join(why) or 'agrees')
        coq.append(row)
        if any(not w.startswith('note:') for w in why) and t not in A.FROZEN:
            bad.append(row)

    # ---- 2. every result against the builder's ranges and its DATA
    res = collect(reg, snap['data'], snap['specs'], p2b)
    built, built_any = {}, {}

    def cert_key(c):
        return re.sub(r'[\s/\-]', '', str(c or '')).upper().replace('К', 'K').replace('М', 'M')

    def keys(cb, pp):
        """The batch, its parent cultivation batch, and both P lots, normalised."""
        ks = {A.N(cb), A.N(pp), A.N(b2p.get(A.N(cb), '')), A.N(p2b.get(A.N(pp), ''))}
        ks |= {A.N(x) for x in A.chain(cb or p2b.get(A.N(pp), ''))}
        return {k for k in ks if k}

    entered = {}
    for a, cb, pp, v, kind, src, cert, note in res:
        if src == 'builder-entered':                    # entered on the server against the strain, no batch
            entered.setdefault(a, set()).add(v)
        elif src == 'builder':
            built_any.setdefault(a, set()).add(v)
            for k in keys(cb, pp) | {cert_key(cert)}:
                built.setdefault((a, k), set()).add(v)
    seen, rows = {}, []
    for a, cb, pp, v, kind, src, cert, note in res:
        pp = pp or b2p.get(A.N(cb), '')
        key = (a, cert_key(cert) if cert and not cert.startswith('in-house') else A.N(cb) or A.N(pp), v)
        if key in seen:
            seen[key][5].add(src)
            seen[key][6].add(cert)
            seen[key][7] = seen[key][7] or note
            if seen[key][4] == 'standalone' and kind != 'standalone':
                seen[key][4] = kind
            continue
        seen[key] = [a, cb, pp, v, kind, {src}, {cert}, note]
    for a, cb, pp, v, kind, srcs, certs, note in seen.values():
        rng = ranges(a)
        cov = [r for r in rng if r['lo'] <= v <= r['hi']]
        if srcs == {'builder-entered'}:
            continue                                    # listed against its batch where a source names one
        ks = keys(cb, pp) | {cert_key(c) for c in certs if c}
        acc = any(any(abs(v - x) < 0.006 for x in built.get((a, k), ())) for k in ks) or \
            any(abs(v - x) < 0.006 for x in entered.get(a, ()))
        if not acc and not (keys(cb, pp) or any(certs - {''})) and any(abs(v - x) < 0.006 for x in built_any.get(a, ())):
            acc = True                                  # no batch or certificate to tie it, and the value is there
        rows.append([a or '?', cb, pp, '%.2f' % v, kind, ','.join(sorted(srcs)), ', '.join(sorted(x for x in certs if x)),
                     ' / '.join('%s %g (%.2f – %.2f)' % (num.get((a, float(r['nominal'])), '(none)'), r['nominal'],
                                                          r['lo'], r['hi']) for r in cov) or 'IN NO RANGE',
                     'yes' if acc else 'no', specs.get(a, {}).get('status', 'no strain in the builder'), note])
    rows.sort(key=lambda r: (r[0], r[1], float(r[3])))

    with open(OUT_COQ, 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh, delimiter='\t', lineterminator='\n')
        w.writerow(['certificate', 'tranche', 'series', 'batch', 'p_lot', 'strain', 'total_thc', 'grade', 'specification',
                    'product_code', 'criterion_printed', 'builder_grade', 'builder_specification', 'builder_product_code',
                    'finding'])
        w.writerows(coq)
    with open(OUT_RES, 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh, delimiter='\t', lineterminator='\n')
        w.writerow(['strain', 'batch', 'p_lot', 'total_thc', 'kind', 'sources', 'certificates', 'builder_ranges_covering',
                    'in_builder_data', 'builder_status', 'note'])
        w.writerows(rows)

    # ---- 3. per strain: its ranges against every result and every production batch
    strains = []
    for a in sorted({r[0] for r in rows} | {k for k in specs if not k.startswith('V_')}):
        rs = [r for r in rows if r[0] == a]
        vs = [float(r[3]) for r in rs]
        rng = sorted(specs.get(a, {}).get('ranges', []), key=lambda r: r['lo'])
        gaps = ['%.2f – %.2f' % (x['hi'], y['lo']) for x, y in zip(rng, rng[1:]) if y['lo'] - x['hi'] > 0.011]
        batches = {A.N(r[1]) or A.N(r[2]) for r in rs if r[1] or r[2]}
        out_ = [r for r in rs if r[7] == 'IN NO RANGE']
        strains.append([a, specs.get(a, {}).get('name', ''), specs.get(a, {}).get('status', 'not in the builder'),
                        str(len(rng)), ' / '.join('%s %g ± %g (%.2f – %.2f)' % (num.get((a, float(r['nominal'])), '(none)'),
                                                                               r['nominal'], r['tol'], r['lo'], r['hi'])
                                                  for r in sorted(rng, key=lambda r: -r['nominal'])),
                        str(len(batches)), str(len(rs)), '%.2f – %.2f' % (min(vs), max(vs)) if vs else '',
                        '; '.join('%s %s %s (%s)' % (r[3], r[1] or r[2], r[4], r[6] or r[5]) for r in out_) or 'all covered',
                        ', '.join(gaps) or '—'])
    with open(OUT_STR, 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh, delimiter='\t', lineterminator='\n')
        w.writerow(['strain', 'name', 'builder_status', 'ranges_n', 'ranges', 'batches_n', 'results_n', 'results_span',
                    'results_in_no_range', 'gaps_between_ranges'])
        w.writerows(strains)

    print('builder %s, %d Purely Plant strains with ranges; %d certificates of quality, %d distinct THC results'
          % (snap.get('version'), sum(1 for k in specs if not k.startswith('V_')), len(coq), len(rows)))
    for r in coq:
        if r[-1] != 'agrees' and r[1] not in A.FROZEN:
            print('CoQ  %s %-7s %-7s %-14s %6s  %s' % (r[0], r[1], r[2], r[3], r[6], r[-1]))
    frozen = [r for r in coq if r[-1] != 'agrees' and r[1] in A.FROZEN]
    if frozen:
        print('issued T1/T2, not touched: %s' % '; '.join('%s %s' % (r[0], r[-1]) for r in frozen))
    out = [r for r in rows if r[7] == 'IN NO RANGE']
    miss = [r for r in rows if r[8] == 'no']
    print('%d results in no range of their strain:' % len(out))
    for r in out:
        print('  %-4s %-14s %-8s %6s %-10s %s  %s' % (r[0], r[1], r[2], r[3], r[4], r[5], r[6]))
    print('%d results not in the builder\'s data (all in a range unless listed above)' % len(miss))
    print('per strain (ranges / batches / results / span / not covered):')
    for s in strains:
        print('  %-4s %-11s %s / %2s / %3s / %-13s / %s' % (s[0], s[2], s[3], s[5], s[6], s[7], s[8]))
    print('written:', ', '.join(os.path.relpath(x, GAP) for x in (OUT_COQ, OUT_RES, OUT_STR)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
