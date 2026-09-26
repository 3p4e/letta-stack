#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Why is a certificate-of-quality result empty? Every empty cell, classified against every certificate.

    python3 tracker/audit_empty_results.py                 # Tranche 3, table + TSV
    python3 tracker/audit_empty_results.py --tranche all
    python3 tracker/audit_empty_results.py --strict        # exit 1 while any cell is a wiring miss

Head of QC, 26.09.2026: *"they're missing values for many of the parameters and there must not be
a case like that ... check in detail the results and why you do not print the actual values."*

A result prints `[ — ]` when the register row for it is empty. That can mean four different things,
and until this audit they were indistinguishable on the page:

* **WIRED-MISS** — a certificate for this exact lot (P lot or cultivation batch), dated on or before
  the certificate of quality, reports the parameter, and the register never took it. A defect of
  ours; `--strict` fails on it.
* **LATER-ROUND** — a certificate for this exact lot reports it, but it is dated after the certificate
  of quality (the August–September 2026 retest campaigns). Printing it on the earlier document would
  date a result before it existed.
* **OTHER-LOT** — only a parent batch or a sibling sub-lot reports it (`BSS1024` for `BSS1024_01/2`,
  `GRC102501/2` for `GRC102501/1`). Head of QC, 26.09.2026: never a source — *"they are separate
  lots"* — so these print `n/t` and go on the laboratory request list.
* **UNTESTED** — no certificate anywhere in the repository reports it for this lot or any relative.
* **PENDING-RULING** — the register records that the Head of QC must choose (release results that
  disagree). Prints `[pending]`; not a miss, because the choice is his.

The certificates searched: the eCoA corpus (`ingestion/ecoa_runner/records_corpus.json`, 283 double-read
certificates) and the contaminant intake of 18.09 (58 double-read IPH certificates, several of which
the corpus lacks). The register's own attribution is not trusted here — it is what is being audited.
"""
import argparse
import collections
import csv
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(GAP))
PLOT = re.compile(r'^P\d{6}$')

# CoQ row → the corpus keys that answer it. Total CBN is CBN where the laboratory reports no CBNA,
# which is how the register already credits UKIM's "Содржина на CBN" on CoQ-PP_26-001.
PARAM = {
    '1': ['identification_a_macroscopic'], '2': ['identification_b_microscopic'],
    '3': ['identification_c_hplc'], '4': ['total_thc'], '5': ['total_cbd'],
    '6': ['total_cbn', 'cbn_free'], '7': ['foreign_matter'], '8': ['loss_on_drying'],
    '9.1': ['tamc'], '9.2': ['tymc'], '9.3': ['bile_tolerant_gram_negative'], '9.4': ['salmonella'],
    '9.5': ['escherichia_coli'], '10.1': ['aflatoxin_b1'], '10.2': ['aflatoxins_total'],
    '10.3': ['ochratoxin_a'], '11.1': ['lead'], '11.2': ['cadmium'], '11.3': ['arsenic'],
    '11.4': ['mercury'], '12': ['pesticide_residues'],
}
NAME = {'1': 'Identification A', '2': 'Identification B', '3': 'Identification C (HPLC)',
        '4': 'Total THC', '5': 'Total CBD', '6': 'Total CBN', '7': 'Foreign matter', '8': 'Loss on drying',
        '9.1': 'TAMC', '9.2': 'TYMC', '9.3': 'Bile-tolerant GNB', '9.4': 'Salmonella', '9.5': 'E. coli',
        '10.1': 'Aflatoxin B1', '10.2': 'Aflatoxins total', '10.3': 'Ochratoxin A', '11.1': 'Lead',
        '11.2': 'Cadmium', '11.3': 'Arsenic', '11.4': 'Mercury', '12': 'Pesticide residues'}
# the IPH contaminant certificates print Macedonian names
MK = {'олово': 'lead', 'кадмиум': 'cadmium', 'арсен': 'arsenic', 'жива': 'mercury',
      'вкупни афлатоксини': 'aflatoxins_total'}


def N(s):
    return re.sub(r'[\s_\-/*＊]', '', str(s or '')).upper()


def chain(cb):
    """BSS1024_01/2 → [BSS1024_01/2, BSS1024_01, BSS1024]: the batch and its parents."""
    out = [str(cb or '').replace('＊', '*')]
    while True:
        m = re.match(r'^(.*?)[_/\-][^_/\-]*$', out[-1])
        if not m or len(N(m.group(1))) < 5:
            return [x for x in out if x]
        out.append(m.group(1))


def dt(s):
    try:
        d, m, y = str(s).strip().split('.')
        return datetime.date(int(y), int(m), int(d))
    except Exception:
        return None


def certificates():
    """(identity keys, code, date, {param key: result}) for every double-read certificate."""
    out = []
    for r in json.load(open(os.path.join(ROOT, 'ingestion', 'ecoa_runner', 'records_corpus.json'),
                            encoding='utf-8')):
        vals = {p['parameter']: p.get('result_printed') for p in r.get('parameters', [])
                if str(p.get('result_printed') or '').strip()}
        ids = {N(r.get('batch_canonical')), N(r.get('p_number'))}
        out.append((ids, r.get('cert_code'), r.get('date_of_issue'), vals))
    gate = json.load(open(os.path.join(GAP, 'intake_contaminants_2026-09-18', 'two_read_result.json'),
                          encoding='utf-8'))['documents']
    have = {c for _, c, _, _ in out}
    for code, doc in gate.items():
        if code in have:
            continue
        vals, pest = {}, []
        for p in doc.get('parameters', []):
            key = next((v for k, v in MK.items() if p['name'].lower().startswith(k)), None)
            if key:
                vals[key] = p['result']
            else:
                pest.append(p['result'])
        if pest:
            vals['pesticide_residues'] = 'н.д. — all %d' % len(pest) if all(
                str(x).strip().lower() in ('н.д.', 'n.d.', 'nd') for x in pest) else '; '.join(map(str, pest))
        scan = doc.get('scan', '')
        ids = {N(doc.get('batch'))} | {N(x) for x in re.findall(r'P\d{6}', scan)}
        out.append((ids, code, doc.get('issue_date'), vals))
    return out


def tranche_map():
    m = {}
    with open(os.path.join(GAP, 'intake_tranches_2026-09-18', 'drive_folders_2026-09-18.tsv'),
              encoding='utf-8') as fh:
        for r in csv.DictReader(fh, delimiter='\t'):
            f, t = r['folder'], r['tranche']
            tail = f.rsplit('_', 1)[-1]
            if PLOT.match(tail):
                m[tail] = t
            m[f] = t
            m.setdefault(re.split(r'_P\d{6}$', f)[0].rstrip('_').replace('＊', ''), t)
    return m


def code_dates(certs):
    """Certificate code → issue date, from every source that states one."""
    m = {code: date for _, code, date, _ in certs if code and date}
    for code, v in json.load(open(os.path.join(GAP, 'intake_227K_2026-09-15', 'checkpoint_master_coa_table.json'),
                                  encoding='utf-8')).items():
        m.setdefault(code, str(v.get('issue', '')).split(' ')[0])
    return m


# The Farmahem campaigns of August–September 2026 — 197-К/М (07–10.08), 220-К/М and 227-К/М
# (11–16.09) — are the twelve-month retest round, whatever a given certificate's own date field holds.
CAMPAIGN = re.compile(r'^(197|220|227)-\d+-[КKМM]/26$')


def also_values(row):
    """The register's `also` field: other results the desk found for this lot, `value (CODE)`."""
    return re.findall(r'([^;()]+?)\s*\(([^()]+)\)', str(row.get('also') or ''))


def classify(c, no, certs, row=None, dates=None):
    keys = PARAM.get(no, [])
    exact = {N(c.get('pp'))} | {N(chain(c.get('cb'))[0])} if c.get('cb') else {N(c.get('pp'))}
    exact.discard('')
    parents = {N(x) for x in chain(c.get('cb'))[1:]}
    issue = dt(c.get('issue'))
    hits = []
    # what the register itself already holds for this row, beside the empty result
    for val, code in also_values(row or {}):
        code = code.strip()
        if 'in-house record' in code or 'no certificate' in code:
            hits.append(('exact', False, 'in-house record, no certificate', '', val.strip()))
            continue
        later = bool(CAMPAIGN.match(code)) or bool(issue and dt((dates or {}).get(code)) and
                                                    dt((dates or {}).get(code)) > issue)
        hits.append(('exact', later, code, (dates or {}).get(code, ''), val.strip()))
    for ids, code, date, vals in certs:
        k = next((k for k in keys if k in vals), None)
        if not k:
            continue
        rel = 'exact' if ids & exact else 'parent' if ids & parents else None
        if not rel:
            continue
        later = bool(issue and dt(date) and dt(date) > issue)
        hits.append((rel, later, code, date, vals[k]))
    if any(r == 'exact' and not l for r, l, *_ in hits):
        cat = 'WIRED-MISS'
    elif any(r == 'exact' for r, *_ in hits):
        cat = 'LATER-ROUND'
    elif hits:
        cat = 'OTHER-LOT'
    else:
        cat = 'UNTESTED'
    hits.sort(key=lambda h: (h[0] != 'exact', h[1], str(h[2] or '')))
    return cat, hits


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--tranche', default='T3')
    ap.add_argument('--strict', action='store_true')
    ap.add_argument('--out', default=None)
    a = ap.parse_args(argv[1:])
    reg = json.load(open(os.path.join(GAP, 'coq_artifact_data.json'), encoding='utf-8'))
    tm, certs = tranche_map(), certificates()
    dates = code_dates(certs)

    def tranche(c):
        for k in (c.get('pp'), c.get('cb'), (c.get('cb') or '').replace('＊', '')):
            if k and k in tm:
                return tm[k]

    recs = [c for c in reg['coqs'] if a.tranche == 'all' or tranche(c) == a.tranche]
    rows, tally = [], collections.Counter()
    for c in sorted(recs, key=lambda c: c['regcode']):
        ser = 'retest' if 'retest' in c['t'] else 'initial'
        for r in c['rows']:
            if str(r.get('res')).strip() not in ('—', '', 'None') or r['no'] in ('9.6', '9.7'):
                continue
            cat, hits = classify(c, r['no'], certs, r, dates)
            if str(r.get('st') or '').startswith("awaiting the Head of QC's ruling"):
                cat = 'PENDING-RULING'            # a recorded decision, not a miss
            carried = 'carried' in str(r.get('st'))
            tally[(ser, cat)] += 1
            rows.append([c['regcode'], ser, c.get('pp') or '', c.get('cb') or '', r['no'], NAME.get(r['no'], ''),
                         cat, 'yes' if carried else '', str(r.get('st') or '')[:70],
                         ' | '.join('%s %s %s = %s%s' % (h[0], h[2], h[3], h[4], ' (after the CoQ)' if h[1] else '')
                                    for h in hits[:3])])
    out = a.out or os.path.join(HERE, 'EMPTY_RESULTS_AUDIT_%s.tsv' % a.tranche)
    with open(out, 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh, delimiter='\t')
        w.writerow(['coq', 'series', 'p_lot', 'cultivation_batch', 'row', 'parameter', 'class',
                    'carried_from_initial', 'register_status', 'certificates_that_report_it'])
        w.writerows(rows)
    print('empty result cells, %s: %d' % (a.tranche, len(rows)))
    for (ser, cat), k in sorted(tally.items()):
        print('  %-8s %-12s %4d' % (ser, cat, k))
    print('written: %s' % os.path.relpath(out, GAP))
    miss = sum(k for (_, cat), k in tally.items() if cat == 'WIRED-MISS')
    return 1 if (a.strict and miss) else 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
