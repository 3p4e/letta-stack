#!/usr/bin/env python3
"""The 32 Tranche 2 cannabinoid certificates as testing instances for the tracker builder
(tracker/new_instances.json), the way the 197-n-K-26 and 227-n-K-26 certificates go in:
identification C 'Conforms' on the strength of the HPLC cannabinoid profile (owner,
02.09.2026), Total THC, Total CBD and Total CBN as printed. Idempotent: an instance whose
code is already in the file is replaced. The same two-read gate as apply_220K.py.

    python3 deliverables/qc_gap_analysis/intake_220K_2026-09-15/instances_220K.py [--out PATH]
"""
import os, sys, json, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(GAP, 'tracker'))
from apply_220K import load_reads, reg_value   # noqa: E402  one definition of the gate and the spelling
import tracker_data as T                        # noqa: E402

SOURCE = ('direct read 15.09.2026 · Claude transcription of the rendered page (eCoA_DATABASE copy), '
          'independent second transcription of the same pages agreeing on batch, dates, sample number and every result; '
          'not through the eCoA database pipeline')


def index_code(code):
    """The tracker index's form of a Farmahem code: Latin K, hyphens — '220-1-К/26' -> '220-1-K-26'."""
    return str(code).translate({ord('М'): 'M', ord('К'): 'K'}).replace('/', '-')


def p_from_list(cu):
    """The P lot the Head of QC's batch list gives for a cultivation batch, or ''."""
    import csv
    with open(os.path.join(GAP, 'tracker', 'batch_dates.csv'), encoding='utf-8-sig') as fh:
        for r in csv.DictReader(fh):
            if T.batch_key(r.get('cu_batch') or '') == T.batch_key(cu):
                return (r.get('p_batch') or '').strip()
    return ''


def instance(m):
    r = m['results_flat']
    vals = {'3': 'Conforms', '4': reg_value(r['Total THC']), '5': reg_value(r['Total CBD']), '6': reg_value(r['Total CBN'])}
    # a certificate that prints only the cultivation batch takes the P lot the batch
    # list gives it (JD042601 = P060492), as the 220-30-М/26 instance already does —
    # the same lot, one tracker row; FB042601, CC042601 and GG1024 are on no list
    p = m['p_number'] or p_from_list(m['batch_printed'])
    return {'p': p, 'cu': '' if m['p_number'] else m['batch_printed'],
            'strain': m['strain_printed'], 'code': index_code(m['cert_code']),
            'date': m['date_of_issue'], 'lab': 'FHM-K', 'params': [3, 4, 5, 6], 'vals': vals, 'held': [],
            'document': m['file'], 'doc_id': m.get('drive_id'), 'source': SOURCE}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(GAP, 'tracker', 'new_instances.json'))
    a = ap.parse_args()
    R, _ = load_reads()
    new = [instance(m) for _, m in sorted(R.items(), key=lambda kv: kv[1]['n'])]
    have = json.load(open(a.out, encoding='utf-8')) if os.path.exists(a.out) else []
    mine = {T.nkey(x['code']) for x in new}
    kept = [x for x in have if T.nkey(x['code']) not in mine]
    out = kept + new
    json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('%s: %d instance(s) kept, %d written for the 220-К/26 cannabinoid series (%d replaced)'
          % (a.out, len(kept), len(new), len(have) - len(kept)))
    for x in new:
        print('  %-9s %-13s %-12s %s  %s' % (x['p'] or '—', x['cu'] or '', x['code'], x['date'], json.dumps(x['vals'])))


if __name__ == '__main__':
    main()
