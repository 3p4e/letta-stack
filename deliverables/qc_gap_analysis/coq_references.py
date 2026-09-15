#!/usr/bin/env python3
"""One row per certificate of quality, one column per determination #1 to #12: the document
the CoQ cites for it — code, date of issue, laboratory abbreviation — read from
coq_artifact_data.json (the CoQ rows the drafts print from) with the desk's own laboratory
abbreviations from the tracker index. Writes <out>.csv, <out>.md and <out>.xlsx.

    python3 deliverables/qc_gap_analysis/coq_references.py [--src coq_artifact_data.json] [--out PREFIX]

Cell notation: `code date LAB`; `*` an internal CoA to be issued at the certificate's issue;
`also X` a later document on file for the same determination (the retest); `n/t` not tested,
with the sub-determinations when only some are; `→ release` outside the retest scope, the
release certificate stands; `u/r` upon request; `OOS`, `undetermined`, `BLOCKED` the record's
own verdict flags. Rows: numbered CoQs in code order, then the unnumbered by batch.
"""
import json, re, sys, os, collections, csv, argparse
G = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(G, 'tracker'))
import tracker_data as T
ap = argparse.ArgumentParser()
ap.add_argument('--src', default=os.path.join(G, 'coq_artifact_data.json'))
ap.add_argument('--out', default=os.path.join(G, 'tracker', 'CoQ_references'))
ap.add_argument('--instances', default=os.path.join(G, 'tracker', 'new_instances.json'))
a = ap.parse_args()
d = json.load(open(a.src, encoding='utf-8'))
# the desk's abbreviation per document, from the owner's index and the new instances
LAB = {}
_, index_rows = T.load_owner()
for r in index_rows: LAB[T.nkey(r['code'])] = r['lab']
for i in json.load(open(a.instances, encoding='utf-8')): LAB[T.nkey(i['code'])] = i['lab']
LONG = {'UKIM Faculty of Pharmacy — Center for Natural Products': 'CNP', 'CNP': 'CNP', 'IPH — Institute of Public Health': 'IJZ', 'IJZ': 'IJZ',
        'Purely Plant GmbH (in-house)': 'PP', 'State Phytosanitary Laboratory': 'DFL'}
def abbr(doc, lab):
    k = T.nkey(doc)
    if k in LAB: return LAB[k]
    if lab.startswith('Farmahem') or lab == 'FHM':
        return 'FHM-M' if re.search(r'[МM]/\d\d$', doc) else 'FHM-K' if re.search(r'[КK]/\d\d$', doc) else 'FHM'
    if doc.startswith('iCoA'): return 'PP'
    return LONG.get(lab, lab or '?')
def sd(dd):
    m = re.match(r'(\d\d)\.(\d\d)\.(\d{4})$', dd or '')
    return f"{m.group(1)}.{m.group(2)}.{m.group(3)[2:]}" if m else (dd or '')
def cell(rows):
    """rows = the CoQ's rows for one determination (sub-rows folded)."""
    docs, notes = [], collections.OrderedDict()
    multi = len(rows) > 1
    for r in rows:
        doc, st = (r['doc'] or '').strip(), r['st']
        if doc and doc != '—':
            if doc.startswith('n/a — Purely Plant in-house CoA'): doc = 'in-house CoA, no number'
            tag = ''
            if st.startswith('to be performed'): tag = '*'
            elif st.startswith('OUT OF SPEC'): tag = ' OOS'
            elif st.startswith('UNDETERMINED'): tag = ' undetermined'
            elif st.startswith('BLOCKED'): tag = ' BLOCKED'
            item = f"{doc} {sd(r['dd'])} {abbr(doc, r['lab'])}{tag}"
            if item not in docs: docs.append(item)
            m = re.search(r'\(([^()]+)\)\s*$', r.get('also') or '')
            if m:
                a = f"also {m.group(1)}"
                if a not in docs: docs.append(a)
        else:
            if st.startswith('outside the retest scope'): n = '→ release'
            elif st.startswith('upon request'): n = 'u/r'
            elif st.startswith('not tested'): n = 'n/t'
            elif st.startswith('to be performed'): n = 'to be performed'
            elif st.startswith('awaiting the cannabinoid'): n = 'awaiting FHM-K'
            elif st.startswith('awaiting the mycotoxin'): n = 'awaiting FHM-M'
            elif st.startswith('in-house CoA only'): n = 'in-house record only'
            else: n = st[:40]
            notes.setdefault(n, []).append(str(r['no']))
    parts = list(docs)
    for n, subs in notes.items():
        if docs and n == 'u/r': continue
        parts.append(f"{n} {','.join(subs)}" if (multi and docs) else n)
    return '; '.join(parts)
def series(t):
    return {'initial release': 'release', 'initial release — predicted': 'release (predicted)',
            'additional testing (12-month)': 'retest', 'additional testing (12-month) — predicted': 'retest (predicted)'}[t]
out = []
for c in d['coqs']:
    code = c.get('regcode') or c.get('n') or '—'
    byno = collections.defaultdict(list)
    for r in c['rows']:
        n = int(str(r['no']).split('.')[0])
        if n == 9 and r['no'] in ('9.6', '9.7'): continue   # upon-request organisms, not release determinations
        byno[n].append(r)
    b = c['pp'] or c['cb']
    row = {'CoQ': code, 'Batch': b if (not c['cb'] or c['cb'] == b) else f"{b} ({c['cb']})", 'Series': series(c['t']), 'Issue': sd(c['issue']) or '—'}
    for n in range(1, 13): row[f'#{n}'] = cell(byno.get(n, []))
    out.append(row)
def sk(r):
    m = re.match(r'CoQ-PP_26-(\d+)', r['CoQ'])
    return (0, int(m.group(1)), r['Batch']) if m else (1, 0, r['CoQ'], r['Batch'])
out.sort(key=sk)
cols = ['CoQ', 'Batch', 'Series', 'Issue'] + [f'#{n}' for n in range(1, 13)]
O = a.out
with open(O + '.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)
md = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
for r in out: md.append('| ' + ' | '.join(str(r[c]).replace('|', '¦') for c in cols) + ' |')
open(O + '.md', 'w', encoding='utf-8').write('\n'.join(md) + '\n')
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'CoQ references'
ws.append(cols)
for r in out: ws.append([r[c] for c in cols])
for c in ws[1]: c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='1F3864'); c.alignment = Alignment(wrap_text=True, vertical='center')
for col, w in zip('ABCDEFGHIJKLMNOP', [16, 22, 18, 10] + [30] * 12): ws.column_dimensions[col].width = w
for row in ws.iter_rows(min_row=2):
    for c in row: c.alignment = Alignment(wrap_text=True, vertical='top'); c.font = Font(size=9)
ws.freeze_panes = 'E2'; ws.auto_filter.ref = ws.dimensions
wb.save(O + '.xlsx')
print(O + '.{csv,md,xlsx}:', len(out), 'rows')
print(collections.Counter(r['Series'] for r in out))
print(collections.Counter(r['CoQ'][:10] for r in out))
