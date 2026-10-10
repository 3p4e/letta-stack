#!/usr/bin/env python3
"""The 32 certificates as testing instances for the tracker builder (tracker/new_instances.json).

What the tracker renders comes from two places: the owner's tracker index
(tracker_data.load_owner) and new_instances.json. The release register is not one of
them — the register gives the builder a certificate's family label and its values
(coq_artifact_data.json -> load_desk), never the document itself. So the first v27 build,
register written and schedule run, still rendered no 220 code in any tracker cell. This
writes the 32 as #10 testing instances, one per certificate, the way
new_instances_from_records.py wrote the 30 IJZ-MB instances of 04.09.2026 — idempotently:
an instance whose code is already in the file is replaced, never duplicated.

Two reads must agree before anything is written: reads_claude.json (the transcription) and
reads_gemini.json (the independent cross-read), compared on the code, the issue date, the
batch printed and every result. One disagreement stops the run.

Values: Aflatoxin B1 (10.1) and Ochratoxin A (10.3) are the page's own. Aflatoxins Σ (10.2)
is not printed — the certificate reports B1, B2, G1 and G2 separately — and is written ND
only when all four are ND, which is how the register's 197-М/26 rows (the owner's) and the
tracker's rendering of them already read it; anything else is held for review.

    python3 deliverables/qc_gap_analysis/intake_220M_2026-09-14/instances_220M.py [--out PATH]
"""
import os, sys, json, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(GAP, 'tracker'))
from apply_220M import p_from_list          # one definition: the P-number the batch list gives a cultivation code
import tracker_data as T

AFLATOXINS = ('Aflatoxin B1', 'Aflatoxin B2', 'Aflatoxin G1', 'Aflatoxin G2')
RESULTS = AFLATOXINS + ('Ochratoxin A',)
SOURCE = ('direct read 14.09.2026 · Claude transcription of the rendered page, Gemini cross-read, '
          'every result, code, date and batch agreeing; not through the eCoA database')


def index_code(code):
    """The tracker index's form of a Farmahem code: Latin M, hyphens — '220-1-М/26' -> '220-1-M-26'."""
    return str(code).translate({ord('М'): 'M', ord('К'): 'K'}).replace('/', '-')


def gemini_results(g):
    return {p.get('parameter_printed'): p.get('result_printed') for p in g['parsed'].get('parameters', [])}


def disagreements(m, g):
    """Where the two reads of one certificate differ; empty when they agree."""
    if not g:
        return ['no Gemini read']
    gp, out = g['parsed'], []
    if T.nkey(gp.get('cert_code')) != T.nkey(m['cert_code']):
        out.append('code %r vs %r' % (gp.get('cert_code'), m['cert_code']))
    if gp.get('date_of_issue') != m['date_of_issue']:
        out.append('issue date %r vs %r' % (gp.get('date_of_issue'), m['date_of_issue']))
    # Gemini's field mapping of the sample line varies (the submission number lands in
    # batch_printed or p_number); the batch agrees when it appears in any of the fields.
    seen = ' '.join(str(gp.get(k) or '') for k in ('batch_printed', 'batch_canonical', 'p_number')).upper()
    if m['batch_printed'].upper() not in seen:
        out.append('batch %r not read (%r)' % (m['batch_printed'], seen))
    gr = gemini_results(g)
    for name in RESULTS:
        if gr.get(name) != m['results'].get(name):
            out.append('%s %r vs %r' % (name, gr.get(name), m['results'].get(name)))
    return out


def instance(fn, m):
    r = m['results']
    vals, held = {'10.1': r['Aflatoxin B1'], '10.3': r['Ochratoxin A']}, []
    if all(r[a] == 'ND' for a in AFLATOXINS):
        vals['10.2'] = 'ND'
    else:
        vals['10.2'] = 'held for review'; held.append('10.2')
    p = m['p_number'] or p_from_list(m['batch_printed']) or ''
    return {'p': p, 'cu': '' if m['p_number'] else m['batch_printed'],
            'strain': m['strain_printed'], 'code': index_code(m['cert_code']),
            'date': m['date_of_issue'], 'lab': 'FHM-M', 'params': [10], 'vals': vals, 'held': held,
            'document': fn, 'doc_id': None, 'source': SOURCE}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(GAP, 'tracker', 'new_instances.json'))
    a = ap.parse_args()
    R = json.load(open(os.path.join(HERE, 'reads_claude.json'), encoding='utf-8'))
    G = json.load(open(os.path.join(HERE, 'reads_gemini.json'), encoding='utf-8'))
    bad = {fn: d for fn, m in R.items() for d in [disagreements(m, G.get(fn))] if d}
    if bad:
        for fn, d in bad.items():
            print('DISAGREE', fn, '—', '; '.join(d))
        sys.exit('%d certificate(s) where the two reads differ — nothing written' % len(bad))
    new = [instance(fn, m) for fn, m in sorted(R.items(), key=lambda kv: kv[1]['n'])]
    have = json.load(open(a.out, encoding='utf-8')) if os.path.exists(a.out) else []
    mine = {T.nkey(x['code']) for x in new}
    kept = [x for x in have if T.nkey(x['code']) not in mine]
    out = kept + new
    json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('%s: %d instance(s) kept, %d written for the 220-М/26 series (%d replaced), %d held'
          % (a.out, len(kept), len(new), len(have) - len(kept), sum(len(x['held']) for x in new)))
    for x in new:
        print('  %-9s %-10s %-12s %s  %s' % (x['p'] or '—', x['cu'] or '', x['code'], x['date'], json.dumps(x['vals'])))
    from_list = [x for x in new if x['p'] and x['cu']]
    if from_list:
        print('P-number from the batch list (certificate prints the cultivation batch only): '
              + ', '.join('%s = %s' % (x['cu'], x['p']) for x in from_list))


if __name__ == '__main__':
    main()
