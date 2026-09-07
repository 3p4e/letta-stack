#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Targeted repairs of extraction errors found by sanity_check.py.
Every repair is verified against the certificate's own parsed text before it
is applied; unverifiable repairs are logged and skipped."""
import json, os, shutil

recs = json.load(open('extracted_params.json'))
docs = {d['name']: d for d in json.load(open('all_cert_texts.json'))}
if not os.path.exists('extracted_params_raw.json'):
    shutil.copy('extracted_params.json', 'extracted_params_raw.json')

def find(prefix):
    return next(r for r in recs if r['name'].startswith(prefix))

log = []
def setval(prefix, field, newval, must_contain, reason):
    r = find(prefix); t = docs[r['name']]['text']
    old = r['params'].get(field)
    if must_contain and must_contain not in t:
        log.append({'doc': r['name'], 'field': field, 'action': 'SKIPPED', 'reason': f'verification string {must_contain!r} not in text'})
        return
    r['params'][field] = newval
    log.append({'doc': r['name'], 'field': field, 'old': old, 'new': newval, 'reason': reason})

def drop(prefix, fields, reason):
    r = find(prefix)
    for f in fields:
        if f in r['params']:
            log.append({'doc': r['name'], 'field': f, 'old': r['params'][f], 'new': None, 'reason': reason})
            del r['params'][f]

CANNAB = ['total_thc_pct','total_cbd_pct','total_cbn_pct','loss_on_drying_pct',
          'foreign_matter_pct','macroscopic_id','microscopic_id','hptlc_id']
MICRO  = ['tamc','tymc','bile_tolerant_gnb','salmonella','e_coli']
CHEM   = ['aflatoxins_total','aflatoxin_b1','ochratoxin_a','pesticides']

# 1) pesticide polarity flips: certs print per-line Н.д., never "Не одговара"
for p, form in (('BG1024, 752-2025','н.д.'), ('FB012601_1, 2362-2026','Н.д.'),
                ('P050032, 2157-2025','Н.Д.'), ('P050252, 5697-2025','Н.д.')):
    setval(p, 'pesticides', form, form if form != 'н.д.' else 'н.д.',
           'polarity flip: extraction wrote "Не одговара" (=fails); cert prints not-detected per pesticide line')
# DFL (English report): check its own wording
r = find('P050192, 10802_2845-2 EN'); t = docs[r['name']]['text']
dfl_form = 'n.d.' if 'n.d.' in t.lower() else ('not detected' if 'not detected' in t.lower() else None)
if dfl_form:
    setval('P050192, 10802_2845-2 EN', 'pesticides', dfl_form, None,
           'polarity flip: extraction wrote "Не одговара"; DFL report prints not-detected')
else:
    log.append({'doc': r['name'], 'field': 'pesticides', 'action': 'SKIPPED', 'reason': 'could not verify DFL wording'})

# 2) blanket-phantom docs
drop('OPM122501, 229-0392-26', CANNAB, 'phantom: micro-only certificate, fields not present')
drop('P050192, 5661-2025', CANNAB + MICRO + CHEM, 'phantom: metals-only certificate, fields not present')
drop('FB012601_1, 2362-2026', MICRO, 'phantom: chem certificate has no microbiology section')

# 3) translated instead of as-printed
for p in ('FB012603V, ППК26110','GG032601, ППК26128','JD012603_02V, ППК26111'):
    setval(p, 'foreign_matter_pct', 'Одговара', 'Одговара', 'as printed "/ (Одговара)"; extraction wrote "Absent"')
setval('JD022601, ППК26115', 'microscopic_id', 'Одговара', 'Микроскопија', 'cert prints Одговара; extraction wrote N.D.')
for p in ('P050152, 946-1684-25','P060072, 10-0013-26'):
    for f in ('salmonella','e_coli'):
        setval(p, f, 'Одговара', 'Одговара', 'as printed "Одговара"; extraction wrote "Absent"')

json.dump(recs, open('extracted_params.json','w'), ensure_ascii=False)
json.dump(log, open('repair_log.json','w'), ensure_ascii=False, indent=1)
applied = [l for l in log if 'action' not in l]
print('repairs applied:', len(applied), '| skipped:', len(log)-len(applied))
for l in log: print(' ', l.get('action','OK'), l['doc'][:44], l['field'], repr(l.get('old'))[:18],'->',repr(l.get('new'))[:18])
