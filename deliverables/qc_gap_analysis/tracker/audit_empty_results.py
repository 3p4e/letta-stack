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
* **IN-HOUSE-ONLY** — the only release result is the company's own record (the in-house CoA of
  23.04.2025 for GG1024, HPA1024 and OPM1024; the register's `also` note "in-house record …, no
  certificate"). Head of QC, 17.09.2026 (`apply_lab_attribution.py`, R3): an in-house record without a
  certificate is not cited, so the cell prints `n/t`. Not a miss.
* **UNTESTED** — no certificate anywhere in the repository reports it for this lot or any relative.
* **FIRST-TESTING** — a LATER-ROUND cell on an initial whose family the release round never tested:
  the later certificate is the lot's first testing, so it *is* the release testing and must print on
  the initial (Head of QC, 10.09 and 26.09.2026). A miss; `--strict` fails on it.
* **PENDING** — the register records what the cell is waiting for: the Head of QC's choice between
  release results that disagree, or the missing page of a certificate that exists (IPH 1065/2026,
  page 3 of 4). Prints `[pending]`; not a miss, because nothing on file can fill it.

The certificates searched: the eCoA corpus (`ingestion/ecoa_runner/records_corpus.json`, 283 double-read
certificates), the contaminant intake of 18.09 (58 double-read IPH certificates, several of which
the corpus lacks), and the CNP release certificates in the RAGflow page-text cache
(`ingestion/ragflow/cache/all_cert_texts_2026-08-30.json`) — the corpus lacks many of them, and on
26.09.2026 four Tranche 3 initials were found printing a retest CBN while their own CNP release
certificate reported it. The register's own attribution is not trusted here — it is what is being
audited.

Two more checks, on cells that are *not* empty, fail `--strict` as well:

* **RETEST-ON-INITIAL** — an initial prints a Farmahem campaign value (197-, 220-, 227-К/М/26) for
  a family the release round already tested (`release_family`): that value belongs to the retest.
* **BARE** — an empty result whose status the renderer cannot turn into `n/t` or `[pending]`: it
  would print a bare `[ — ]`, which CLAUDE.md §5 calls a defect.
* **SUPERSEDES** — a draft retest names its initial with a date the initial no longer carries. A
  Tranche 1 or 2 retest is the customer's document and is never changed, so its mismatches are
  listed, not failed.
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


INHOUSE = 'in-house record, no certificate'
CACHE = os.path.join(ROOT, 'ingestion', 'ragflow', 'cache', 'all_cert_texts_2026-08-30.json')
# the CNP cannabinoid table: "Вкупно Δ9-THC | / | 18.67", "Содржина на CBN | ≤ 1.00 | 0.03"
CNP_LINES = {'total_thc': r'Вкупно\s*Δ9-THC\**\s*\|[^|\n]*\|\s*([^\n|]+)',
             'total_cbd': r'Вкупно\s*CBD\**\s*\|[^|\n]*\|\s*([^\n|]+)',
             'total_cbn': r'Содржина на CBN\s*\|[^|\n]*\|\s*([^\n|]+)'}


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
        code = r.get('cert_code')
        if 'PURELY' in str(r.get('lab') or '').upper():
            code = INHOUSE                    # the company's own record, not a certificate
        out.append((ids, code, r.get('date_of_issue'), vals))
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
    have = {c for _, c, _, _ in out}
    for x in json.load(open(CACHE, encoding='utf-8')):
        m = x.get('meta') or {}
        if m.get('lab') != 'CNP' or m.get('test_type') != 'RELEASE' or m.get('cert_code') in have:
            continue
        vals = {}
        for key, pat in CNP_LINES.items():
            hit = re.search(pat, x.get('text') or '')
            if hit:
                vals[key] = hit.group(1).strip()
        if vals:
            out.append(({N(m.get('batch_canonical'))}, m.get('cert_code'), m.get('date_of_issue'), vals))
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

# Head of QC, 26.09.2026: only the Tranche 1 and 2 *retest* certificates are with the customer; every
# initial certificate, and all of Tranche 3, is a draft. Those retests are never changed — not their
# results, not the date they print for the initial they supersede. (The register's `issued` flag means a
# code was allocated, not that the customer holds the document.)
RETEST_WITH_CUSTOMER = {'T1', 'T2'}

# Which testing is the release testing — the Head of QC, 10.09.2026: "the first value of a parameter
# obtained would be counted as an initial quality control testing, and every other point of testing ...
# will be considered as a retest"; and 26.09.2026, by family: where IPH reported total aflatoxins at
# release, the Farmahem mycotoxin panel is the retest; where it did not, "the testing in Farmahem for
# mycotoxins is part of initial release testing". Where no cannabinoid certificate exists from CNP and
# only Farmahem's does, "the Farmahem testing is the initial release testing and there will be no
# reissuance". Identification C is cited from the cannabinoid certificate (ruling of 10.09.2026).
K_ROWS = ('3', '4', '5', '6')
M_ROWS = ('10.1', '10.2', '10.3')


def _has(row):
    return str(row.get('res')).strip() not in ('—', '', 'None')


def release_family(c):
    """(cannabinoids, mycotoxins): does the initial hold a release-round certificate for the family?

    A release certificate is any certificate the initial cites for the family that is not one of the
    August–September 2026 Farmahem campaigns — CNP, IPH, an earlier Farmahem series (031-, 051-,
    100-К; 276-М/25), or the internal certificate the 10.09 ruling lets carry an in-house assay — or a
    release result the Head of QC has been asked to choose between, or a certificate whose missing page
    is awaited.
    """
    rows = {r['no']: r for r in c['rows']}

    def release(nos):
        for no in nos:
            r = rows.get(no) or {}
            st = str(r.get('st') or '')
            if _has(r) and not CAMPAIGN.match(str(r.get('doc') or '').strip()):
                return True
            if st.startswith('awaiting'):
                return True
        return False
    return release(('4', '5', '6')), release(M_ROWS)


def initial_issue(c, retest=None):
    """An initial certificate's date under the standing rule (issuance_schedule.coq_issue): seven days
    after the last external certificate it cites, never before the internal certificate, never before
    its own scheduled date. *"How can a certificate of quality be dated on a date that is earlier than
    the last certificate of analysis obtained from external lab for that batch testing?"*

    The owner's rule is five to ten days; seven is the desk's one number. Where seven would date the
    initial after the retest that supersedes it, the initial takes the retest's date, provided that is
    still at least five days after its last certificate — otherwise the run stops."""
    if GAP not in sys.path:
        sys.path.insert(0, GAP)
    import issuance_schedule as IS
    base = dt(c.get('issue_before_redating') or c.get('issue'))
    ext = [dt(r.get('dd')) for r in c['rows'] if _has(r) and str(r.get('doc') or '').strip() not in ('', '—')
           and not str(r.get('doc')).startswith('iCoA') and dt(r.get('dd'))]
    icoa = next((r.get('dd') for r in c['rows'] if str(r.get('doc') or '').startswith('iCoA')), None)
    new = dt(IS.coq_issue('%02d.%02d.%04d' % (max(ext).day, max(ext).month, max(ext).year), icoa)) if ext else None
    out = max(d for d in (base, new) if d)
    rd = dt((retest or {}).get('issue')) if retest and not retest.get('withdrawn') else None
    if rd and rd < out and new and out == new:
        if (rd - max(ext)).days < 5:
            raise SystemExit('%s: its retest %s of %s is less than five days after %s'
                             % (c['regcode'], retest['regcode'], retest['issue'], max(ext)))
        out = rd
    return '%02d.%02d.%04d' % (out.day, out.month, out.year)


def supersedes_mismatches(recs):
    """Retests whose 'supersedes' line names a date its initial no longer carries."""
    ini = {c['regcode']: c for c in recs if 'retest' not in c['t']}
    out = []
    for r in recs:
        s = r.get('supersedes') or {}
        i = ini.get(s.get('code'))
        if i and s.get('date') and s['date'] != i.get('issue') and not r.get('withdrawn'):
            out.append((r['regcode'], s['code'], s['date'], i.get('issue')))
    return out


def retest_on_initial(recs):
    """Initial cells that print a retest-campaign value although the family was tested at release."""
    out = []
    for c in recs:
        if 'retest' in c['t'] or c.get('withdrawn'):
            continue
        k, m = release_family(c)
        for r in c['rows']:
            fam = k if r['no'] in K_ROWS else m if r['no'] in M_ROWS else None
            if fam and _has(r) and CAMPAIGN.match(str(r.get('doc') or '').strip()):
                out.append((c['regcode'], r['no'], r.get('doc')))
    return out


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
            hits.append(('in-house', False, INHOUSE, '', val.strip()))
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
        if code == INHOUSE:
            rel = 'in-house' if rel == 'exact' else rel
        later = bool(issue and dt(date) and dt(date) > issue)
        hits.append((rel, later, code, date, vals[k]))
    if any(r == 'exact' and not l for r, l, *_ in hits):
        cat = 'WIRED-MISS'
    elif any(r == 'exact' for r, *_ in hits):
        cat = 'LATER-ROUND'
    elif any(r == 'in-house' for r, *_ in hits):
        cat = 'IN-HOUSE-ONLY'
    elif hits:
        cat = 'OTHER-LOT'
    else:
        cat = 'UNTESTED'
    hits.sort(key=lambda h: (h[0] != 'exact', h[0] != 'in-house', h[1], str(h[2] or '')))
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

    recs = [c for c in reg['coqs'] if (a.tranche == 'all' or tranche(c) == a.tranche) and not c.get('withdrawn')]
    rows, tally = [], collections.Counter()
    # the same lot's retest record carries the campaign certificates the corpus lacks (227-М, ...)
    lot = lambda c: (str(c.get('pp') or ''), str(c.get('cb') or ''))
    retest_of = {lot(c): c for c in reg['coqs'] if 'retest' in c['t']}
    for c in sorted(recs, key=lambda c: c['regcode']):
        ser = 'retest' if 'retest' in c['t'] else 'initial'
        rel_k, rel_m = release_family(c)
        twin = {x['no']: x for x in (retest_of.get(lot(c)) or {}).get('rows', [])} if ser == 'initial' else {}
        for r in c['rows']:
            if str(r.get('res')).strip() not in ('—', '', 'None') or r['no'] in ('9.6', '9.7'):
                continue
            cat, hits = classify(c, r['no'], certs, r, dates)
            t = twin.get(r['no']) or {}
            if _has(t) and 'carried' not in str(t.get('st')) and CAMPAIGN.match(str(t.get('doc') or '').strip()):
                hits.append(('exact', True, t.get('doc'), t.get('dd'), str(t.get('res')).split('|')[0].strip()))
                if cat in ('UNTESTED', 'OTHER-LOT', 'IN-HOUSE-ONLY'):
                    cat = 'LATER-ROUND'
            # the campaign is this lot's first testing of the family: it is the release testing and
            # belongs on the initial (Head of QC, 10.09 and 26.09.2026)
            if cat == 'LATER-ROUND' and ser == 'initial' and not (rel_k if r['no'] in K_ROWS else
                                                                   rel_m if r['no'] in M_ROWS else False):
                cat = 'FIRST-TESTING'
            if str(r.get('st') or '').startswith('awaiting'):
                cat = 'PENDING'                   # recorded: a ruling or a missing page, not a miss
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
    miss = sum(k for (_, cat), k in tally.items() if cat in ('WIRED-MISS', 'FIRST-TESTING'))
    # a re-dated initial must carry its new date onto the draft retest that supersedes it
    sup, fail_sup = supersedes_mismatches(recs), []
    for x in sup:
        customer = tranche(next(c for c in recs if c['regcode'] == x[0])) in RETEST_WITH_CUSTOMER
        print('  SUPERSEDES  %s names %s of %s — the initial is dated %s%s'
              % (x + ('  (the customer\'s document: listed, not changed)' if customer else '',)))
        if not customer:
            fail_sup.append(x)
    # a result cell the renderer would print as a bare [ — ]: coq_build.js prints n/t only when the
    # status says "not tested", and [pending] only when it says "awaiting" (CLAUDE.md §5)
    bare = [(c['regcode'], r['no'], str(r.get('st') or '')[:60]) for c in recs for r in c['rows']
            if not _has(r) and r['no'] not in ('9.6', '9.7')
            and not re.search(r'not tested|awaiting', str(r.get('st') or ''), re.I)]
    for x in bare:
        print('  BARE  %s row %s would print [ — ]: %s' % x)
    roi = retest_on_initial(recs)
    for x in roi:
        print('  RETEST-ON-INITIAL  %s row %s cites %s, but the family was tested at release' % x)
    return 1 if (a.strict and (miss or fail_sup or roi or bare)) else 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
