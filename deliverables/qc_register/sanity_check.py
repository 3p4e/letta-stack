#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RAG database sanity check: is the extracted data actually what the eCoA says?

Three independent layers:
  A) presence  — every extracted value must literally occur in its own
                 certificate's parsed text (catches hallucinated values)
  B) anchor    — for the potency-critical fields the value is re-read from the
                 labeled line/table row of the parse text with a regex and
                 compared (catches row-misassignment like CJ072501)
  C) register  — values compared against the human-transcribed batch-release
                 register row for the same CoA code (independent source)
"""
import json, re, unicodedata

S = '.'
docs = {d['name']: d for d in json.load(open(f'{S}/all_cert_texts.json'))}
recs = json.load(open(f'{S}/extracted_params.json'))

def norm(s):
    s = unicodedata.normalize('NFKC', str(s))
    s = s.replace('х', 'x').replace('Х', 'X').replace('•', 'x').replace('·', 'x').replace('×', 'x')
    return re.sub(r'\s+', '', s).lower()

NUMF = ('total_thc_pct','total_cbd_pct','total_cbn_pct','loss_on_drying_pct',
        'foreign_matter_pct','tamc','tymc','bile_tolerant_gnb','aflatoxins_total',
        'aflatoxin_b1','ochratoxin_a','pb','cd','arsenic','hg')

# ---------- layer A: presence ----------
presA = {'checked':0,'ok':0,'miss':[]}
for r in recs:
    t = norm(docs[r['name']]['text'])
    for f, v in (r.get('params') or {}).items():
        if f.startswith('_') or f in ('batch_printed','doc_code','is_stability'): continue
        if v is None or str(v).strip() in ('','/','—'): continue
        presA['checked'] += 1
        if norm(v) in t: presA['ok'] += 1
        else: presA['miss'].append((r['name'], f, str(v)))

# ---------- layer B: anchors ----------
def cnp_anchor(text, label):
    # same-line layout:  'Вкупно Δ9-THC***      /     16.93 %'
    for m in re.finditer(label + r'\**\s*[\n ]+(?:[≤\d.,/ %]*?[\n ]+)?([<>≤]?\s?(?:LOQ|BLQ|ND|Н\.?[Дд]\.?|\d+[.,]\d+|\d+))\s*%?\s*(?:\n|$)', text):
        return m.group(1).strip()
    return None

def fhm_anchor(text, en_label):
    m = re.search(re.escape(en_label) + r'\s*\|\s*([<>≤]?\s?(?:LOQ|BLQ|ND|\d+[.,]\d+|\d+))', text)
    return m.group(1).strip() if m else None

anchors = {'checked':0,'ok':0,'bad':[]}
def cmp_val(a, b):
    if a is None or b is None: return None
    na, nb = norm(a), norm(b)
    if na == nb: return True
    try: return abs(float(na.replace(',','.').lstrip('<>≤')) - float(nb.replace(',','.').lstrip('<>≤'))) < 1e-9
    except ValueError: return na.replace('<','').replace('≤','') == nb.replace('<','').replace('≤','')

for r in recs:
    name, t, p = r['name'], docs[r['name']]['text'], (r.get('params') or {})
    lab = name.rsplit(',',1)[-1].replace('.pdf','').strip().split('_')[-1]
    pairs = []
    if lab == 'CNP':
        pairs = [('total_thc_pct', cnp_anchor(t, r'Вкупно\s+Δ9-THC')),
                 ('total_cbd_pct', cnp_anchor(t, r'Вкупно\s+CBD')),
                 ('loss_on_drying_pct', cnp_anchor(t, r'Губиток\s+при\s+сушење'))]
    elif lab == 'FHM':
        pairs = [('total_thc_pct', fhm_anchor(t, 'Total Δ9-THC')),
                 ('total_cbd_pct', fhm_anchor(t, 'Total CBD')),
                 ('total_cbn_pct', fhm_anchor(t, 'Total CBN'))]
    for f, av in pairs:
        ev = p.get(f)
        if av is None or ev is None: continue
        anchors['checked'] += 1
        res = cmp_val(av, ev)
        if res: anchors['ok'] += 1
        else: anchors['bad'].append((name, f, f'extracted={ev}', f'anchor={av}'))

# ---------- layer C: register cross-check ----------
reg = json.load(open(f'{S}/ref_register.json'))
regmap = {}
for row in reg:
    code = norm(row.get('coa_code') or '')
    if code: regmap.setdefault(code, row)

REGF = {'total_thc_pct':'thc','total_cbd_pct':'cbd','total_cbn_pct':'cbn',
        'loss_on_drying_pct':'lod','pb':'pb','cd':'cd','arsenic':'as','hg':'hg'}
regchk = {'matched_rows':0,'checked':0,'ok':0,'diff':[]}
for r in recs:
    code = norm((r.get('params') or {}).get('doc_code') or '')
    row = regmap.get(code)
    if not row: continue
    regchk['matched_rows'] += 1
    for f, rf in REGF.items():
        ev, rv = (r.get('params') or {}).get(f), row.get(rf)
        if ev is None or rv in (None,'','/'): continue
        regchk['checked'] += 1
        if cmp_val(ev, rv): regchk['ok'] += 1
        else: regchk['diff'].append((r['name'], f, f'rag={ev}', f'register={rv}'))

out = {'presence': presA, 'anchors': anchors, 'register': regchk}
json.dump(out, open(f'{S}/sanity_results.json','w'), ensure_ascii=False, indent=1)
print('A presence:', presA['checked'], 'checked,', presA['ok'], 'found,', len(presA['miss']), 'missing')
print('B anchors :', anchors['checked'], 'checked,', anchors['ok'], 'match,', len(anchors['bad']), 'MISMATCH')
print('C register:', regchk['matched_rows'], 'rows matched by CoA code,', regchk['checked'], 'values,', regchk['ok'], 'agree,', len(regchk['diff']), 'differ')
for x in anchors['bad'][:25]: print('  B!', x)
for x in presA['miss'][:15]: print('  A!', x)
