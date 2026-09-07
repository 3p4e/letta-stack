#!/usr/bin/env python3
"""records (two reads, reconciled) + the split manifest -> new_instances.json for the
tracker builder: one #9 testing instance per IJZ-MB certificate of 31.08/01.09.2026.

Values are written in the desk's own vocabulary ('2.1×10⁴', '<10', 'absent',
'<10² и >10'); a parameter the two reads disagreed on is 'held for review'.
"""
import os, sys, json, re, csv

HERE = os.path.dirname(os.path.abspath(__file__))
SUP = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'}
KEYS = {'tamc': '9.1', 'tymc': '9.2', 'bile_tolerant_gram_negative': '9.3', 'salmonella': '9.4', 'escherichia_coli': '9.5'}


def desk_form(v):
    """'1,7 x 10² CFU/g' -> '1.7×10²';  '< 10 CFU/g' -> '<10';  'Отсутна/25 g', 'Отсуствува/g' -> 'absent'."""
    t = str(v or '').strip()
    if not t:
        return ''
    # 'Отсутна', 'Отсуства', 'Отсуствува' (a Latin a may close the word) — all 'absent'
    if re.match(r'^(отсу|absen|нема|not detected)', t, re.I):
        return 'absent'
    t = re.sub(r'\s*CFU\s*/\s*g\s*$', '', t, flags=re.I)
    t = re.sub(r'(?<=\d),(?=\d)', '.', t)
    t = re.sub(r'\s*[xх×]\s*10\s*\^?\s*([0-9⁰¹²³⁴⁵⁶⁷⁸⁹]+)',
               lambda m: '×10' + ''.join(SUP.get(c, c) for c in m.group(1)), t)
    t = re.sub(r'10\^(\d)', lambda m: '10' + SUP[m.group(1)], t)
    t = re.sub(r'([<>≤≥])\s+', r'\1', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()


manifest = {}
for row in csv.DictReader(open((sys.argv[2] if len(sys.argv) > 2 else HERE + '/split_manifest.csv'), encoding='utf-8-sig')):
    manifest[row['filename']] = row

SRC = sys.argv[1] if len(sys.argv) > 1 else HERE + '/new_records.json'
recs = [r for r in json.load(open(SRC)) if r.get('document') in manifest]   # the corpus, restricted to the manifest's documents
print('records source:', SRC, '->', len(recs), 'of', len(manifest), 'manifest documents')
out = []
for r in recs:
    m = manifest.get(r['document']) or {}
    p = m.get('batch_canonical') or r.get('batch_canonical') or ''
    code = (m.get('lab_no') or r.get('cert_code') or '').replace('/', '-')   # 552/1083/26 -> 552-1083-26, the index form
    vals, held = {}, []
    for prm in r.get('parameters', []):
        k = KEYS.get(prm.get('parameter'))
        if not k:
            continue
        if prm.get('confidence') != 'ok':
            vals[k] = 'held for review'; held.append(k)
        else:
            vals[k] = desk_form(prm.get('result_printed'))
    out.append({'p': p if p.startswith('P') else '', 'cu': '' if p.startswith('P') else p,
                'strain': m.get('strain') or r.get('strain') or '',
                'code': code, 'date': m.get('issue_date') or r.get('date_of_issue') or '',
                'lab': 'IJZ-MB', 'params': [9], 'vals': vals, 'held': held,
                'document': r['document'], 'doc_id': r.get('doc_id'),
                'source': 'eCOA_DB ingest 04.09.2026 · two reads reconciled'})
out.sort(key=lambda x: (x['p'] or x['cu']))
json.dump(out, open((sys.argv[3] if len(sys.argv) > 3 else HERE + '/new_instances.json'), 'w'), ensure_ascii=False, indent=1)
print('%d instance(s) written; held: %d' % (len(out), sum(len(x['held']) for x in out)))
for x in out:
    print('  %-9s %-14s %s  %s' % (x['p'] or x['cu'], x['code'], x['date'], json.dumps(x['vals'], ensure_ascii=False)))
