#!/usr/bin/env python3
"""The 30 certificates as testing instances for the tracker builder (tracker/new_instances.json).

The tracker's document pool is the owner's tracker index plus new_instances.json — never
the release register — so a certificate written into the register alone reaches the
schedule and the registers and never a tracker cell (the v27 lesson, intake_220M). This
writes the 30 as #3–#6 testing instances, one per certificate, the way the desk's index
carries the 197-n-K-26 certificates: identification C 'Conforms' on the strength of the
HPLC cannabinoid profile (owner, 02.09.2026), Total THC, Total CBD and Total CBN as
printed. Idempotent: an instance whose code is already in the file is replaced.

The same two-read gate as apply_227K.py: the page read and the checkpoint transcription
must agree; the five certificates the checkpoint does not hold are written on the page
read alone and say so in their source.

    python3 deliverables/qc_gap_analysis/intake_227K_2026-09-15/instances_227K.py [--out PATH]
"""
import os, sys, json, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(GAP, 'tracker'))
from apply_227K import load_reads, reg_value   # noqa: E402  one definition of the gate and the spelling
import tracker_data as T                        # noqa: E402

SOURCE = ('direct read 12.09.2026 · Claude transcription of the rendered page (ProcessedECOAs copy), '
          'checkpoint transcription in master_coa_table.tsv agreeing on batch, P lot, date and every result; '
          'not through the eCoA database')
SOURCE_SINGLE = ('direct read 12.09.2026 · Claude transcription of the rendered page (ProcessedECOAs copy); '
                 'no second read on file — OI-32')


def index_code(code):
    """The tracker index's form of a Farmahem code: Latin K, hyphens — '227-1-К/26' -> '227-1-K-26'."""
    return str(code).translate({ord('М'): 'M', ord('К'): 'K'}).replace('/', '-')


def instance(fn, m, single):
    r = m['results']
    vals = {'3': 'Conforms', '4': reg_value(r['Total THC']), '5': reg_value(r['Total CBD']), '6': reg_value(r['Total CBN'])}
    return {'p': m['p_number'] or '', 'cu': '' if m['p_number'] else m['batch_printed'],
            'strain': m['strain_printed'], 'code': index_code(m['cert_code']),
            'date': m['date_of_issue'], 'lab': 'FHM-K', 'params': [3, 4, 5, 6], 'vals': vals, 'held': [],
            'document': fn, 'doc_id': m.get('drive_id'),
            'source': SOURCE_SINGLE if m['cert_code'] in single else SOURCE}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(GAP, 'tracker', 'new_instances.json'))
    a = ap.parse_args()
    R, single = load_reads()
    new = [instance(fn, m, single) for fn, m in sorted(R.items(), key=lambda kv: kv[1]['n'])]
    have = json.load(open(a.out, encoding='utf-8')) if os.path.exists(a.out) else []
    mine = {T.nkey(x['code']) for x in new}
    kept = [x for x in have if T.nkey(x['code']) not in mine]
    out = kept + new
    json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('%s: %d instance(s) kept, %d written for the 227-К/26 series (%d replaced), %d on the page read alone'
          % (a.out, len(kept), len(new), len(have) - len(kept), len(single)))
    for x in new:
        print('  %-9s %-13s %-12s %s  %s' % (x['p'] or '—', x['cu'] or '', x['code'], x['date'], json.dumps(x['vals'])))


if __name__ == '__main__':
    main()
