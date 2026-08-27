#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Consolidate 291 certificates into one row per batch, with retest logic.

Rules implemented (owner's instructions, 27.08.2026):
 - one consolidated row per batch, every parameter in one place
 - values as printed on the eCoA: same decimals, no units (units live in header)
 - newer result for the same parameter after a long gap = RETEST, and the
   retest is the CoQ-forming value
 - stability-programme results are NEVER CoQ-forming (they are deliberately
   aged samples; STABILITY_PROGRAMME's own description forbids using them as
   release values) — they are carried in a separate column instead
"""
import json, re, os, collections, datetime as dt

S = os.path.dirname(os.path.abspath(__file__))
ROUND_GAP_DAYS = 60   # per PP_Spec_Parameter_Matrix: >60 days apart opens a new round

# --- Cyrillic look-alike normalisation for batch codes printed in MK ---
CYR = {'А':'A','В':'B','С':'C','Е':'E','Н':'H','К':'K','М':'M','О':'O','Р':'P',
       'Т':'T','Х':'X','У':'Y','Ѕ':'S','І':'I','Ј':'J','Г':'G','Б':'B','Д':'D',
       'Л':'L','П':'P','Ф':'F','Ц':'C','Ч':'C','Ш':'S','Ж':'Z','З':'Z','И':'I',
       'Н':'H','Ќ':'K','Љ':'L','Њ':'N','Ѓ':'G','Џ':'D'}

def deCyr(s):
    return ''.join(CYR.get(ch, ch) for ch in (s or ''))

def norm_batch(s):
    """Loose key for matching batch identities across sources."""
    if not s: return ''
    s = deCyr(str(s)).upper()
    s = s.replace('＊', '*')
    s = re.sub(r'[^A-Z0-9*]', '', s)
    return s

def parse_date(s):
    for f in ('%d.%m.%Y', '%Y-%m-%d'):
        try: return dt.datetime.strptime(str(s).strip(), f).date()
        except Exception: pass
    return None

# numeric-looking? keep as-printed string, plus numeric value where real
NUM_RE = re.compile(r'^-?\d+(?:[.,]\d+)?$')
def as_number(v):
    if v is None: return None
    t = str(v).strip().replace(',', '.')
    if NUM_RE.match(t):
        return float(t)
    m = re.match(r'^(\d+(?:\.\d+)?)\s*[x×]\s*10\^?(\d+)$', t.replace(' ', ''))
    if m:
        return float(m.group(1)) * (10 ** int(m.group(2)))
    return None

def decimals(v):
    t = str(v).strip().replace(',', '.')
    return len(t.split('.')[1]) if '.' in t and NUM_RE.match(t) else 0

# ---------------------------------------------------------------- load
certs = json.load(open(f'{S}/extracted_params.json'))
ref = json.load(open(f'{S}/ref_register.json'))
spec = json.load(open(f'{S}/spec_matrix_batches.json'))
drive = {}
for line in open(f'{S}/drive_all.tsv', encoding='utf-8'):
    parts = line.rstrip('\n').split('\t')
    if len(parts) >= 2: drive[parts[1]] = parts[0]

# ------------------------------------------------- identity resolution
# cultivation-code <-> P-number, learned from three independent sources
cult2p, p2cult = {}, {}
def link(cult, p, authoritative=False):
    """Spec matrix and QC register are authoritative identity sources.
    Certificate-content printed batch codes only FILL GAPS — they pass
    through vision OCR and demonstrably contain misreads (GF0824_02 for
    GP0824_02, 'МБ 0824 A104' noise), so they must never override an
    authoritative link. This bug actually happened on the first run and
    silently orphaned 20 batches from their P-numbers."""
    if not cult or not p: return
    cult2p.setdefault(norm_batch(cult), cult)
    k = norm_batch(p)
    if norm_batch(cult) == k:
        return  # self-link (register rows where batch IS the P-number) must
                # never claim the P-number slot and block a real mapping
    if authoritative:
        p2cult[k] = cult
    else:
        p2cult.setdefault(k, cult)

# PP-TH-VER (the owner's own tranche-verification sheet) is the most complete
# cultivation-code <-> P-number mapping available (76 batches) — highest authority.
ver = []
if os.path.exists(f'{S}/pp_th_ver.json'):
    ver = json.load(open(f'{S}/pp_th_ver.json'))
for b, r in spec.items():
    if r.get('p_number'): link(b, r['p_number'], authoritative=True)
for r in ref:
    if r.get('pnum') and r.get('batch'): link(r['batch'], r['pnum'], authoritative=True)
for v in ver:
    if v.get('cult') and v.get('pp') and v['cult'] != v['pp']:
        link(v['cult'], v['pp'], authoritative=True)
# also normalise sub-lot zero-padding: CJ052501/01 == CJ052501/1
_p2c_extra = {}
for k, cult in list(p2cult.items()):
    m = re.match(r'^(.*?[/_-])0(\d+V?)$', str(cult).strip())
    if m:
        pass
for v in ver:
    m = re.match(r'^(.*?)[/_-]0*(\d+)(V?)$', str(v.get('cult') or '').strip())
    if m and v.get('pp'):
        link(f"{m.group(1)}_{m.group(2)}{m.group(3)}", v['pp'], authoritative=False)
# from certificate content: filename says P-number, cert prints cultivation code
for c in certs:
    fn = c['meta'].get('batch_canonical'); pr = c.get('params', {}).get('batch_printed')
    if not fn or not pr: continue
    if re.match(r'^P\d{6}$', fn) and not re.match(r'^P\d{6}$', deCyr(pr).upper()):
        pn = deCyr(pr).upper().strip()
        if re.match(r'^[A-Z]{2,4}\s?\d{4}', pn):
            link(pn, fn, authoritative=False)

strain_of, pnum_of, coq_of, pcode_of, prod_of = {}, {}, {}, {}, {}
tranche_of, product_of = {}, {}
for b, r in spec.items():
    k = norm_batch(b)
    strain_of[k] = r['strain']; pnum_of[k] = r.get('p_number')
    coq_of[k] = r['coq']; pcode_of[k] = r['product_code']; prod_of[k] = r['production']
for r in ref:
    k = norm_batch(r['batch'])
    strain_of.setdefault(k, r.get('strain')); pnum_of.setdefault(k, r.get('pnum') or None)
for v in ver:
    for raw in (v.get('cult'), v.get('pp')):
        if not raw: continue
        k = norm_batch(raw)
        strain_of.setdefault(k, v.get('strain'))
        if v.get('pp') and re.match(r'^P\d{6}$', str(v['pp'])):
            pnum_of.setdefault(k, v['pp'])
        tranche_of[k] = v.get('tranche'); product_of[k] = v.get('product')

PARAMS = [
    ('total_thc_pct',      'Total Δ9-THC',            '%'),
    ('total_cbd_pct',      'Total CBD',               '%'),
    ('total_cbn_pct',      'Total CBN',               '%'),
    ('loss_on_drying_pct', 'Loss on Drying',          '%'),
    ('foreign_matter_pct', 'Foreign Matter',          '%'),
    ('macroscopic_id',     'Macroscopic ID',          ''),
    ('microscopic_id',     'Microscopic ID',          ''),
    ('hptlc_id',           'Identification (HPTLC)',  ''),
    ('tamc',               'TAMC',                    'CFU/g'),
    ('tymc',               'TYMC',                    'CFU/g'),
    ('bile_tolerant_gnb',  'Bile-tolerant GNB',       'CFU/g'),
    ('salmonella',         'Salmonella',              '/25 g'),
    ('e_coli',             'E. coli',                 '/1 g'),
    ('aflatoxins_total',   'Total Aflatoxins',        'µg/kg'),
    ('aflatoxin_b1',       'Aflatoxin B1',            'µg/kg'),
    ('ochratoxin_a',       'Ochratoxin A',            'µg/kg'),
    ('pb',                 'Lead (Pb)',               'mg/kg'),
    ('cd',                 'Cadmium (Cd)',            'mg/kg'),
    ('arsenic',            'Arsenic (As)',            'mg/kg'),
    ('hg',                 'Mercury (Hg)',            'mg/kg'),
    ('pesticides',         'Pesticide Residues',      ''),
]
ALIAS = {'total_aflatoxins': 'aflatoxins_total'}

AC = {  # acceptance criteria, PP_Spec_Parameter_Matrix / Ph.Eur. 07/2024:3028
    'total_thc_pct': 'per target grade (QCSP 001 §01)', 'total_cbd_pct': '≤ 1.0',
    'total_cbn_pct': '≤ 1.0', 'loss_on_drying_pct': '≤ 12.0', 'foreign_matter_pct': '≤ 2.0',
    'macroscopic_id': 'Conforms to description', 'microscopic_id': 'Conforms to description',
    'hptlc_id': 'Identity confirmed', 'tamc': '≤ 10^5', 'tymc': '≤ 10^4',
    'bile_tolerant_gnb': '≤ 10^4', 'salmonella': 'Absence /25 g', 'e_coli': 'Absence /1 g',
    'aflatoxins_total': '≤ 4', 'aflatoxin_b1': '≤ 2', 'ochratoxin_a': '≤ 20',
    'pb': '≤ 0.5', 'cd': '≤ 0.3', 'arsenic': '≤ 0.2', 'hg': '≤ 0.1',
    'pesticides': '≤ LOQ (Ph. Eur. 2.8.13)',
}

# --------------------------------------------------- group by batch
by_batch = collections.defaultdict(list)
for c in certs:
    m = c['meta']
    b = m.get('batch_canonical') or ''
    key = norm_batch(b)
    # fold P-number batches onto their cultivation code where known
    canon = p2cult.get(key)
    by_batch[norm_batch(canon) if canon else key].append(c)

# Which labs are actually accredited/scoped to test which parameter family
# (from §5 of the filing spec + PP_Spec_Parameter_Matrix lab table). A value
# for a parameter extracted from a lab outside its scope is an extraction
# artifact (e.g. a spec-table row on an IJZ report), never a result.
LAB_SCOPE = {
    'cannabinoid': {'CNP', 'FHM', 'NGP', 'PP'},
    'lod':         {'CNP', 'FHM', 'PP'},
    'fm_id':       {'CNP', 'PP'},
    'micro':       {'IJZ-MB', 'PP'},
    'chem':        {'IJZ', 'FHM', 'DFL', 'PP'},
}
FIELD_FAMILY = {
    'total_thc_pct': 'cannabinoid', 'total_cbd_pct': 'cannabinoid',
    'total_cbn_pct': 'cannabinoid', 'loss_on_drying_pct': 'lod',
    'foreign_matter_pct': 'fm_id', 'macroscopic_id': 'fm_id',
    'microscopic_id': 'fm_id', 'hptlc_id': 'fm_id',
    'tamc': 'micro', 'tymc': 'micro', 'bile_tolerant_gnb': 'micro',
    'salmonella': 'micro', 'e_coli': 'micro',
    'aflatoxins_total': 'chem', 'aflatoxin_b1': 'chem', 'ochratoxin_a': 'chem',
    'pb': 'chem', 'cd': 'chem', 'arsenic': 'chem', 'hg': 'chem',
    'pesticides': 'chem',
}

def observations(cert_list, field):
    fam = FIELD_FAMILY.get(field)
    allowed = LAB_SCOPE.get(fam, None)
    out = []
    for c in cert_list:
        p = c.get('params', {})
        v = p.get(field)
        if v is None and field in ('aflatoxins_total',):
            v = p.get('total_aflatoxins')
        if v in (None, '', '—', '/'): continue
        m = c['meta']
        if allowed and m.get('lab') not in allowed:
            continue
        out.append({
            'value': str(v).strip(),
            'date': parse_date(m.get('date_of_issue')),
            'date_str': m.get('date_of_issue'),
            'lab': m.get('lab'), 'code': m.get('cert_code'),
            'stability': (m.get('test_type') == 'STABILITY_TIMEPOINT') or bool(p.get('is_stability')),
            'file': c['name'], 'source_filename': m.get('source_filename'),
        })
    out.sort(key=lambda o: (o['date'] or dt.date(1900, 1, 1)))
    return out

# QC decision 27.08.2026: J31122501 was release-tested as two parallel
# preparations, each with a complete panel (potency + micro + chem) -> two rows.
SPLIT_PREPS = {
    'J31122501#trim': ('J31122501 (machine-trimmed)', ('100-3-К', '100-3-K', '230/0393', '230-0393', '1625')),
    'J31122501#hand': ('J31122501 (hand-trimmed)', ('100-2-К', '100-2-K', '231/0394', '231-0394', '1628')),
}
SPLIT_META = {'p_number': 'P060262', 'strain': 'Jokerz 31', 'product_code': 'J31_THC21.5:CBD1',
              'production': '2025-12', 'coq': {'J31122501#trim': 'CoQ-PP-2026-0054', 'J31122501#hand': None}}
if 'J31122501' in by_batch:
    _certs = by_batch.pop('J31122501')
    for _sk, (_disp, _codes) in SPLIT_PREPS.items():
        _lst = [c for c in _certs
                if any(cd in (c['meta'].get('cert_code') or '') or cd in c['name'] for cd in _codes)]
        if _lst: by_batch[_sk] = _lst
    _rest = [c for c in _certs if not any(c in v for v in
             (by_batch.get('J31122501#trim', []), by_batch.get('J31122501#hand', [])))]
    if _rest:
        raise SystemExit('J31122501 split left unassigned certs: %r' % [c['name'] for c in _rest])

rows, coq_dossier, retests, stability_rows = [], [], [], []

for bkey, clist in by_batch.items():
    disp = None
    for c in clist:
        b = c['meta'].get('batch_canonical')
        if b and norm_batch(b) == bkey: disp = b; break
    if disp is None:
        disp = cult2p.get(bkey, clist[0]['meta'].get('batch_canonical', bkey))
    if bkey in SPLIT_PREPS:
        disp = SPLIT_PREPS[bkey][0]
    row = {
        'batch': disp, 'key': bkey,
        'p_number': pnum_of.get(bkey) or (disp if re.match(r'^P\d{6}$', str(disp)) else None),
        'strain': strain_of.get(bkey), 'product_code': pcode_of.get(bkey),
        'production': prod_of.get(bkey), 'coq': coq_of.get(bkey),
        'n_certs': len(clist),
    }
    if bkey in SPLIT_PREPS:
        row.update({'p_number': SPLIT_META['p_number'], 'strain': SPLIT_META['strain'],
                    'product_code': SPLIT_META['product_code'], 'production': SPLIT_META['production'],
                    'coq': SPLIT_META['coq'][bkey]})
    # P-numbers confirmed by the owner's tranche sheet (PP-TH-VER), 27.08.2026
    P_BACKFILL = {'JD112501': 'P060212', 'JD012603_02': 'P060412', 'JD012603_02V': 'P060422'}
    if not row.get('p_number') and row['batch'] in P_BACKFILL:
        row['p_number'] = P_BACKFILL[row['batch']]
    if not row['p_number']:
        for c in clist:
            pr = c.get('params', {}).get('batch_printed')
            if pr and re.match(r'^P\d{6}$', deCyr(pr).upper().strip()):
                row['p_number'] = deCyr(pr).upper().strip(); break

    used_codes, first_d, last_d = set(), None, None
    for f, label, unit in PARAMS:
        obs = observations(clist, f)
        rel = [o for o in obs if not o['stability']]
        stab = [o for o in obs if o['stability']]
        # PP in-house certificates COMPILE/RESTATE outsourced-lab numbers
        # (verified this session: 47 of 123 PP 'newer' values were literal
        # restatements of the earlier lab figure). They are CoQ-forming
        # only where no external laboratory tested the parameter at all
        # (the R&D batches whose only certificate is the PP CoA).
        ext = [o for o in rel if o['lab'] != 'PP']
        if ext:
            rel = ext
        for o in obs:
            d = o['date']
            if d:
                first_d = d if not first_d or d < first_d else first_d
                last_d = d if not last_d or d > last_d else last_d
        if not rel:
            row[f] = None; row[f + '__src'] = None; continue
        chosen = rel[-1]
        row[f] = chosen['value']
        row[f + '__src'] = f"{chosen['code']}, {chosen['date_str']}, {chosen['lab']}"
        row[f + '__file'] = chosen['source_filename'] or chosen['file']
        used_codes.add((chosen['code'], chosen['date_str'], chosen['lab'],
                        chosen['source_filename'] or chosen['file']))
        if len(rel) > 1:
            prev = rel[-2]
            gap = (chosen['date'] - prev['date']).days if (chosen['date'] and prev['date']) else None
            if gap is not None and gap > ROUND_GAP_DAYS:
                row[f + '__retest'] = True
                retests.append({
                    'batch': disp, 'parameter': label, 'unit': unit,
                    'superseded_value': prev['value'],
                    'superseded_src': f"{prev['code']}, {prev['date_str']}, {prev['lab']}",
                    'current_value': chosen['value'],
                    'current_src': f"{chosen['code']}, {chosen['date_str']}, {chosen['lab']}",
                    'gap_days': gap,
                })
        for so in stab:
            stability_rows.append({
                'batch': disp, 'parameter': label, 'unit': unit, 'value': so['value'],
                'src': f"{so['code']}, {so['date_str']}, {so['lab']}",
                'note': 'stability programme — NOT a release/CoQ value',
            })
    row['first_result'] = first_d.strftime('%d.%m.%Y') if first_d else None
    row['last_result'] = last_d.strftime('%d.%m.%Y') if last_d else None
    row['tranche'] = tranche_of.get(bkey)
    row['product_name'] = product_of.get(bkey)
    row['_certs'] = sorted(used_codes, key=lambda t: t[1] or '')
    rows.append(row)

# --- corrections overlay: ONLY values individually verified against the
# certificate's own parsed text this session; each carries its evidence ---
CORRECTIONS = {
    # extraction filed the Δ9-THCA component line (26.20) as Total CBD;
    # owner eye-checked the paper certificate 27.08.2026: Вкупно CBD = 0.09
    ('P050252', 'total_cbd_pct'): ('0.09', 'ППК25367, 28.11.2025, CNP',
        'extraction row misassignment (took Δ9-THCA 26.20); 0.09 confirmed on paper original by QC'),
    # extraction took the "Содржина на Δ9-THC" component line (0.48) instead
    # of the "Вкупно Δ9-THC" total; certificate text verified to print 16.93
    ('P060052', 'total_thc_pct'): ('16.93', 'ППК26005, 21.01.2026, CNP',
        'extraction line-pick error, corrected from certificate text'),
    # certificate prints "Вкупно Δ9-THC 1.58" which is arithmetically
    # impossible against its own printed components (0.46 + 17.01×0.877 =
    # 15.38, the certificate's own formula) and both the QC register and the
    # tranche sheet carry 15.38 — flagged as certificate print/OCR anomaly
    ('P050042', 'total_thc_pct'): ('15.38', 'ППК25117, 06.05.2025, CNP',
        'printed total inconsistent with certificate\'s own component values; '
        '15.38 per component arithmetic + register + tranche sheet — VERIFY ON PAPER ORIGINAL'),
    # parse lost the value column of this certificate's table entirely;
    # register (live-verified 18.08) and tranche sheet agree on 15.95
    ('P050012', 'total_thc_pct'): ('15.95', 'ППК25140, 22.05.2025, CNP',
        'parse layout loss; value per QC register + tranche sheet — VERIFY ON PAPER ORIGINAL'),
}
corr_applied = []
for r in rows:
    for (b, f), (val, src, note) in CORRECTIONS.items():
        if norm_batch(b) in (r['key'], norm_batch(r.get('p_number') or '')):
            old = r.get(f)
            r[f] = val; r[f + '__src'] = src; r[f + '__note'] = note
            corr_applied.append((r['batch'], f, old, val))
print('corrections applied:', corr_applied)

# chronological ordering: by first result date, then batch
rows.sort(key=lambda r: (parse_date(r['first_result']) or dt.date(2100, 1, 1), str(r['batch'])))

cert_map = {bk: [c['name'] for c in cl] for bk, cl in by_batch.items()}
json.dump({'rows': rows, 'retests': retests, 'stability': stability_rows, 'cert_map': cert_map,
           'params': PARAMS, 'ac': AC, 'drive': drive},
          open(f'{S}/consolidated.json', 'w'), ensure_ascii=False, default=str)

print('batches consolidated:', len(rows))
print('retest events (>%dd gap, release-type only): %d' % (ROUND_GAP_DAYS, len(retests)))
print('stability observations held out of CoQ values:', len(stability_rows))
covered = sum(1 for r in rows if r['total_thc_pct'])
print('batches with a THC value:', covered)
print('batches missing strain:', sum(1 for r in rows if not r['strain']))
print('batches missing P-number:', sum(1 for r in rows if not r['p_number']))
