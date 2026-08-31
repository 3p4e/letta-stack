#!/usr/bin/env python3
"""Assemble the CoQ dataset for a batch, in the structure of QCSOP 012 v.03.

Section 02  Consolidated Analytical Results - the twelve numbered specification
            rows, groups 9/10/11 carrying their sub-rows.
Section 03  Laboratory & Certificate Cross-Reference - one row per issuing
            laboratory, with its accreditation, the CoA document code and date,
            and the PARAMETER NUMBERS that laboratory supplied.

Every result on the certificate must trace to a laboratory and a document code.
A parameter with no confirmed result is reported MISSING; nothing is inferred
from a sibling batch, from an earlier test, or from the specification.
"""
import os, sys, json, sqlite3, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'common'))
sys.path.insert(0, HERE)
from common.master_spec import spec_for, thc_criterion
from common.controlled import (canonical_lab, canonical_strain, PANELS,
                               is_panel_statement, is_not_found, panel_of)

# Specification Section 02 exactly as printed: (number, sub, key, English, criterion, method)
SPEC = [
    ('1',  None, 'identification_a_macroscopic', 'Identification A, Appearance',      'Conforms to monograph', 'Ph. Eur. mon. 3028'),
    ('2',  None, 'identification_b_microscopic', 'Identification B',                  'Conforms to monograph', 'Ph. Eur. 2.8.23 (microscopy)'),
    ('3',  None, 'identification_c_hplc',        'Identification C',                  'Conforms to monograph', 'Ph. Eur. 2.2.29 (3028)'),
    ('4',  None, 'total_thc',                    'Assay — Total Δ9-THC',              'per grade, Section 01', 'Ph. Eur. 2.2.29 (HPLC); THC + THCA × 0.877'),
    ('5',  None, 'total_cbd',                    'Assay — Total CBD',                 '≤ 1.0 %, w/w',          'Ph. Eur. 2.2.29 (HPLC); CBD + CBDA × 0.877'),
    ('6',  None, 'total_cbn',                    'Total CBN',                         '≤ 1.0 %, w/w',          'Ph. Eur. 2.2.29 (HPLC); CBN + CBNA × 0.876'),
    ('7',  None, 'foreign_matter',               'Foreign Matter',                    '≤ 2.0 % / 25–50 g',     'Ph. Eur. 2.8.2 / in-house'),
    ('8',  None, 'loss_on_drying',               'Loss on Drying',                    '≤ 12.0 %',              'Ph. Eur. 2.2.32 (3028)'),
    ('9',  'a',  'tamc',                         'TAMC',                              '≤ 10^5 CFU/g',          'Ph. Eur. 2.6.12 cat. C'),
    ('9',  'b',  'tymc',                         'TYMC',                              '≤ 10^4 CFU/g',          'Ph. Eur. 2.6.12 cat. C'),
    ('9',  'c',  'bile_tolerant_gram_negative',  'Bile-tolerant gram-neg.',           '≤ 10^4 CFU/g',          'Ph. Eur. 2.6.31 cat. C'),
    ('9',  'd',  'salmonella',                   'Salmonella',                        'Absence / 25 g',        'Ph. Eur. 2.6.31 cat. C'),
    ('9',  'e',  'escherichia_coli',             'Escherichia coli',                  'Absence / 1 g',         'Ph. Eur. 2.6.13 cat. C'),
    ('10', 'a',  'aflatoxin_b1',                 'Aflatoxin B1',                      '≤ 2 µg/kg',             'Ph. Eur. 2.8.18 (HPLC-FLD)'),
    ('10', 'b',  'aflatoxins_total',             'Aflatoxins ∑ (B1+B2+G1+G2)',        '≤ 4 µg/kg',             'Ph. Eur. 2.8.18 (HPLC-FLD)'),
    ('10', 'c',  'ochratoxin_a',                 'Ochratoxin A',                      '≤ 20 µg/kg',            'Ph. Eur. 2.8.22 (HPLC-FLD)'),
    ('11', 'a',  'lead',                         'Lead (Pb)',                         '≤ 0.5 mg/kg',           'Ph. Eur. 2.4.27 (ICP-MS)'),
    ('11', 'b',  'cadmium',                      'Cadmium (Cd)',                      '≤ 0.3 mg/kg',           'Ph. Eur. 2.4.27 (ICP-MS)'),
    ('11', 'c',  'arsenic',                      'Arsenic (As)',                      '≤ 0.2 mg/kg',           'Ph. Eur. 2.4.27 (ICP-MS)'),
    ('11', 'd',  'mercury',                      'Mercury (Hg)',                      '≤ 0.1 mg/kg',           'Ph. Eur. 2.4.27 (ICP-MS)'),
    ('12', None, 'pesticide_residues',           'Pesticide Residues',                '≤ LOQ per 2.8.13',      'Ph. Eur. 2.8.13 (LC-MS/MS)'),
]
# Reported only when requested; absence is not a gap.
ON_REQUEST = {'pseudomonas_aeruginosa', 'staphylococcus_aureus', 'pesticide_residues_cumcs'}

# ---------------------------------------------------------------------------
# Source precedence (Head of QC)
#
# QCCoA 001 / QCCoA 001v02 are a superseded attempt at a Purely Plant group
# certificate compiled FROM the outsourced laboratories' eCoAs. Every parameter on
# them is derived; none originates there. Citing one on a CoQ would attribute an
# accredited determination to the wrong laboratory. The CoQ supersedes them.
#
#   tier 1  external accredited laboratory eCoA        - the originating source
#   tier 2  in-house iCoA                              - parameters PP performs itself
#   tier 3  QCCoA 001 / 001v02                         - fallback ONLY where the
#           originating eCoA is missing or not yet ingested, and always flagged
# ---------------------------------------------------------------------------
SUPERSEDED_INHOUSE = ('QCCOA 001', 'QCCOA001')


def source_tier(cert_code, lab):
    code = (cert_code or '').upper().replace(' ', '')
    if any(code.startswith(x.replace(' ', '')) for x in SUPERSEDED_INHOUSE):
        return 3
    if code.startswith('ICOA') or 'PURELYPLANT' in (lab or '').upper().replace(' ', ''):
        return 2
    return 1


def _dedupe(rows):
    """Collapse repeats of the same value from the same certificate.

    A pesticide panel reports dozens of compounds that currently share the key
    pesticide_residues, so the same "N.D." from one certificate would otherwise
    print as dozens of superseding retests. Distinct compounds need distinct keys
    (pesticide:<compound>); until then, do not present them as a retest history.
    """
    seen, out = set(), []
    for d, v, c in rows:
        k = (d, _canon(v), c)
        if k in seen:
            continue
        seen.add(k); out.append((d, v, c))
    return out


GROUP_KEYS = {
    '9':  ['tamc', 'tymc', 'bile_tolerant_gram_negative', 'salmonella', 'escherichia_coli'],
    '10': ['aflatoxin_b1', 'aflatoxins_total', 'ochratoxin_a'],
    '11': ['lead', 'cadmium', 'arsenic', 'mercury'],
}


def _group_cover(by, group):
    """The certificate that covered this parameter group, if any.

    Returns (cert_code, lab, date) from the most recent certificate that reported
    ANY parameter in the group - evidence the panel was run.
    """
    best = None
    for k in GROUP_KEYS.get(group, []):
        for r in by.get(k, []):
            if r[8] == 'ok' and r[1] not in (None, ''):
                if best is None or (r[5] or '') > (best[2] or ''):
                    best = (r[6], r[7], r[5])
    return best


_EQUIV = {'н.д.': 'nd', 'n.d.': 'nd', 'nd': 'nd', 'not detected': 'nd',
          'одговара': 'conforms', 'conforms': 'conforms',
          'confirms': 'conforms', 'отсуство': 'absent',
          'absent': 'absent', 'absence': 'absent'}


def _canon(v):
    # Normalise a printed result for comparison. 'n.d.' and its Cyrillic form are
    # the same result, as are '<LOQ' and '<= LOQ'. Comparing printed strings makes a
    # transcription difference look like a retest and would trigger a CoQ reissue
    # where no new test was performed.
    if v is None:
        return None
    t = str(v).strip().lower().replace('≤', '<').replace(' ', ' ')
    t = ' '.join(t.split())
    if t in _EQUIV:
        return _EQUIV[t]
    t = t.replace(' ', '').replace(',', '.')
    return _EQUIV.get(t, t)


def _num(n, sub):
    return n if sub is None else '%s%s' % (n, sub)


def compile_coq(db, batch, as_of=None):
    """Assemble the CoQ dataset for a batch.

    `as_of` (ISO date) compiles the certificate AS IT STOOD on that date -
    what version v.01 must say, rather than what the later retest found. A
    result dated after `as_of` did not exist when that version was issued and
    must not appear on it; without this every version of a batch would show
    the newest value and the reissue history would be meaningless.
    """
    rows = db.execute("""SELECT r.parameter, r.result_printed, r.result_numeric, r.unit,
             r.method, r.date_iso, r.cert_code, r.lab, r.confidence,
             r.exceeds_criterion, r.outside_range, c.document, c.doc_id,
             r.parameter_printed, r.method_accredited, r.test_type
        FROM result r JOIN certificate c ON c.doc_id = r.doc_id
        WHERE r.batch = ? ORDER BY r.date_iso""", (batch,)).fetchall()
    if as_of:
        # An undated row cannot be proven to predate the cut, so it is excluded
        # from a point-in-time compile rather than assumed contemporaneous.
        rows = [r for r in rows if r[5] and r[5] <= as_of]
    by = {}
    for r in rows:
        by.setdefault(r[0], []).append(r)

    section02, sources, unresolved = [], {}, []

    def cite(entry, lab, code, date, accredited=None):
        """Record a citation on the Section 03 row for this LABORATORY.

        Grouping is by institution, not by certificate and not by department:
        IJZ appears once, carrying every certificate code and issue date it
        supplied for this batch (Head of QC ruling).
        """
        lab_id, lab_name = canonical_lab(lab)
        s = sources.setdefault(lab_id or lab_name, {'lab': lab_name, 'id': lab_id,
                                                    'certs': [], 'params': [],
                                                    'non_accredited': []})
        if (code, date) not in s['certs']:
            s['certs'].append((code, date))
        if entry not in s['params']:
            s['params'].append(entry)
        # A result the laboratory marked as obtained by a non-accredited method must
        # not be presented under that laboratory's accreditation on the CoQ.
        if accredited == 0 and entry not in s['non_accredited']:
            s['non_accredited'].append(entry)

    for n, sub, key, name, criterion, method in SPEC:
        # Total THC has no monograph limit: the criterion is the batch's own
        # class from the potency master (nominal +/- 10 % relative). Without it
        # the CoQ would print a placeholder where the acceptance limit belongs.
        if key == 'total_thc':
            tc = thc_criterion(batch)
            criterion = tc[2] if tc else 'NO MASTER ROW - criterion unknown'
        if key == 'pesticide_residues':
            entry = _pesticides(by, n, criterion, method, cite)
            section02.append(entry)
            if entry['status'] != 'ok':
                unresolved.append(entry)
            continue
        usable = [r for r in by.get(key, []) if r[8] == 'ok' and r[1] not in (None, '')]
        # Take the best available tier, then the most recent within it.
        tiers = {}
        for r in usable:
            tiers.setdefault(source_tier(r[6], r[7]), []).append(r)
        best = min(tiers) if tiers else None
        cands = tiers.get(best, [])
        # Stability timepoints are genuine analyses but not release results. A CoQ
        # states the batch's release quality; a later stability pull must never
        # silently supersede it (register F2: P050022 alone carries five CNP
        # certificates - timepoints, not retests). Prefer non-stability rows; fall
        # back to stability only when nothing else exists, and say so.
        rel = [r for r in cands if (r[15] or 'unknown') != 'stability']
        stability_only = bool(cands) and not rel
        if rel:
            cands = rel
        held  = [r for r in by.get(key, []) if r[8] != 'ok']
        entry = {'no': _num(n, sub), 'group': n, 'key': key, 'parameter': name,
                 'criterion': criterion, 'method': method}
        if not cands:
            entry['result'] = None
            if held:
                entry['status'] = 'HELD'
            else:
                # A parameter absent from a certificate that DID cover its group is
                # "not tested" - the laboratory ran the panel and did not include it.
                # That is declarable on the CoQ. A parameter with no covering
                # certificate at all is MISSING, and blocks issuance. The ImB
                # specification lists three mycotoxins; many eCoAs report only one.
                cover = _group_cover(by, n)
                if cover:
                    entry['status'] = 'NOT TESTED'
                    entry['covered_by_cert'] = cover[0]
                    entry['covered_by_lab'] = cover[1]
                    entry['covered_on'] = cover[2]
                else:
                    entry['status'] = 'MISSING'
            unresolved.append(entry)
        else:
            latest = cands[-1]
            entry.update(result=latest[1], numeric=latest[2], status='ok',
                         stability_only=stability_only or None,
                         source_tier=best,
                         provenance={1: 'accredited eCoA', 2: 'in-house iCoA',
                                     3: 'DERIVED — superseded QCCoA, originating eCoA not available'}[best],
                         date=latest[5], cert_code=latest[6], lab=latest[7],
                         document=latest[11],
                         exceeds_criterion=latest[9], outside_range=latest[10],
                         method_accredited=latest[14],
                         superseded=_dedupe([(r[5], r[1], r[6]) for r in cands[:-1]
                                             if _canon(r[1]) != _canon(latest[1])]))
            cite(_num(n, sub), latest[7], latest[6], latest[5],
                 accredited=latest[14])
        section02.append(entry)
    return section02, sources, unresolved


def _pesticides(by, n, criterion, method, cite):
    """Row 12, supporting either panel reporting shape.

    The specification offers a choice of panel by jurisdiction, so the panel that
    was actually run is read from the certificate rather than assumed. A panel-wide
    "≤ LOQ" covers every compound in it; a per-compound panel conforms only if every
    compound conforms, and any compound above LOQ is named on the CoQ.
    """
    rows = [r for r in by.get('pesticide_residues', []) if r[8] == 'ok' and r[1] not in (None, '')]
    entry = {'no': '12', 'group': '12', 'key': 'pesticide_residues',
             'parameter': 'Pesticide Residues', 'criterion': criterion, 'method': method}
    if not rows:
        held = [r for r in by.get('pesticide_residues', []) if r[8] != 'ok']
        entry.update(result=None, status='HELD' if held else 'MISSING')
        return entry

    # Best available tier, then the certificate that reported the most compounds.
    tiers = {}
    for r in rows:
        tiers.setdefault(source_tier(r[6], r[7]), []).append(r)
    best = min(tiers)
    cands = tiers[best]
    rel = [r for r in cands if (r[15] or 'unknown') != 'stability']
    if rel:
        cands = rel
    per_cert = {}
    for r in cands:
        per_cert.setdefault((r[6], r[7], r[5]), []).append(r)
    (code, lab, date), crows = max(per_cert.items(), key=lambda kv: (kv[0][2] or '', len(kv[1])))

    compounds = [r for r in crows if not is_panel_statement(_printed(r))]
    finds = [(_printed(r), r[1]) for r in compounds if not is_not_found(r[1])]
    pid = panel_of(' '.join(filter(None, (r[4] for r in crows))))
    panel = PANELS.get(pid)

    if compounds:
        shape, result = 'per-compound', ('≤ LOQ (all %d compounds)' % len(compounds)
                                         if not finds else 'FINDS: %d compound(s) above LOQ'
                                         % len(finds))
    else:
        shape, result = 'panel-wide', crows[-1][1]

    entry.update(result=result, status='ok', source_tier=best, shape=shape,
                 panel=pid, panel_name=panel['name'] if panel else None,
                 criterion=panel['criterion'] if panel else criterion,
                 method=panel['method'] if panel else method,
                 compounds_tested=len(compounds) or None,
                 finds=[{'compound': c, 'result': v} for c, v in finds],
                 exceeds_criterion=bool(finds), outside_range=False,
                 provenance={1: 'accredited eCoA', 2: 'in-house iCoA',
                             3: 'DERIVED — superseded QCCoA, originating eCoA not available'}[best],
                 date=date, cert_code=code, lab=lab, document=crows[-1][11], superseded=[])
    cite('12', lab, code, date, accredited=crows[-1][14])
    return entry


def _printed(r):
    """The parameter label as printed on the certificate (compound name, if any)."""
    return r[13]


def render(db, batch):
    s02, sources, unresolved = compile_coq(db, batch)
    cert = db.execute("SELECT strain FROM certificate WHERE batch=? AND strain IS NOT NULL LIMIT 1",
                      (batch,)).fetchone()
    W = 104
    print('=' * W)
    print('CERTIFICATE OF QUALITY — data assembly   batch %s%s   (QCSOP 012 v.03 structure)'
          % (batch, '  ·  %s' % canonical_strain(cert[0]) if cert else ''))
    print('=' * W)

    # 01 identifies the batch and, crucially, the SPECIFICATION it is judged
    # against. A CoQ that does not name its specification cannot be audited.
    m = spec_for(batch)
    print('\n01  IDENTIFICATION')
    if m:
        print('    Specification      %s' % m['spec_code'])
        print('    Product type       %s' % m['product_type'])
        # Grade is a rank within the strain, not an absolute potency.
        print('    Class / grade      %s  (%s — this strain\'s no. %d class)'
              % (m['class'], m['grade'],
                 ['I', 'II', 'III', 'IV', 'V'].index(m['grade'].split()[-1]) + 1))
        print('    Cultivation batch  %s' % m['cultiv_batch_src'])
        print('    PP batch number    %s' % m['pp_batch'])
        print('    Harvest date       %s' % (m['harvest'] or '(not recorded)'))
        print('    Packaging date     %s' % m['packaging'])
    else:
        print('    NO ROW IN THE POTENCY MASTER for this batch - the specification,')
        print('    product type and packaging date cannot be stated, and the Total')
        print('    THC acceptance range is unknown. Add the batch to the master.')
    print('\n02  CONSOLIDATED ANALYTICAL RESULTS')
    print('%-5s %-32s %-24s %-18s %s' % ('№', 'Parameter', 'Acceptance criterion', 'Result', 'Source'))
    print('-' * W)
    last = None
    for e in s02:
        if e['group'] != last and e['group'] in ('9', '10', '11'):
            title = {'9': 'Microbiological Purity', '10': 'Mycotoxins', '11': 'Heavy Metals'}[e['group']]
            print('%-5s %s' % (e['group'], title))
        last = e['group']
        res = e['result'] if e['status'] == 'ok' else '— ' + e['status']
        flag = ' ⚑' if e.get('exceeds_criterion') or e.get('outside_range') else ''
        print('%-5s %-32s %-24s %-18s %s%s'
              % (e['no'], e['parameter'][:32], e['criterion'][:24], str(res)[:18],
                 (e.get('cert_code') or '') if e['status'] == 'ok' else '', flag))
        if e.get('stability_only'):
            print('%-5s   ⚑ STABILITY TIMEPOINT — no release result available' % '')
        if e.get('panel_name'):
            print('%-5s   panel: %s' % ('', e['panel_name']))
        for f in e.get('finds', []):
            print('%-5s   ⚑ %-30s %s' % ('', f['compound'][:30], f['result']))
        for d, v, c in e.get('superseded', []):
            print('%-5s   ↳ superseded %-25s %-24s %s' % ('', v, '', '%s, %s' % (c or '—', d)))
    print('-' * W)
    print('\n03  LABORATORY & CERTIFICATE CROSS-REFERENCE')
    print('%-46s %-26s %s' % ('Laboratory · Accreditation', 'CoA doc. code, issued', 'Param. №'))
    print('-' * W)
    for s in sorted(sources.values(), key=lambda s: _sortkey(s['params'][0])):
        certs = ['%s, %s' % (c or '—', d or '—') for c, d in s['certs']]
        print('%-46s %-26s %s' % ((s['lab'] or '?')[:46], certs[0],
                                  ','.join(sorted(s['params'], key=_sortkey))))
        for extra in certs[1:]:
            print('%-46s %-26s' % ('', extra))
        cred = _credentials(db, s)
        print('%-46s' % ('    ' + cred[:70]))
        if s['non_accredited']:
            print('    ⚑ NON-ACCREDITED method per the certificate: param. %s'
                  % ','.join(sorted(s['non_accredited'], key=_sortkey)))
    print('-' * W)
    ok = sum(1 for e in s02 if e['status'] == 'ok')
    miss = [e for e in unresolved if e['status'] == 'MISSING']
    held = [e for e in unresolved if e['status'] == 'HELD']
    print('\n%d of %d specification rows sourced.' % (ok, len(SPEC)))
    if miss:
        print('MISSING (no result on any certificate for this batch): %s'
              % ', '.join('%s %s' % (e['no'], e['parameter']) for e in miss))
    if held:
        print('HELD FOR REVIEW (reads disagreed): %s'
              % ', '.join('%s %s' % (e['no'], e['parameter']) for e in held))
    if miss or held:
        print('\nA CoQ cannot be issued: every specification row must carry a confirmed,')
        print('traceable result before the QC conformity statement can be made.')
    return s02, sources, unresolved


def _sortkey(no):
    """'9a' sorts after '8' and before '10'."""
    d = ''.join(c for c in no if c.isdigit())
    return (int(d or 0), no)


def _credentials(db, source):
    """Accreditation as printed on any certificate from this laboratory.

    Certificates from one institution print its name several ways, so credentials
    are looked up across every variant that canonicalised to this row rather than
    by exact name match - otherwise the row carrying the credentials is missed.
    """
    if not _has_accred(db):
        return '· accreditation NOT CAPTURED'
    for lab, acc, body, std in db.execute(
            """SELECT lab, lab_accreditation, lab_accreditation_body, lab_standard
               FROM certificate WHERE lab_accreditation IS NOT NULL"""):
        lab_id, name = canonical_lab(lab)
        if (lab_id or name) == (source['id'] or source['lab']):
            return '· ' + ' · '.join(x for x in (acc, body, std) if x)
    return '· accreditation NOT CAPTURED'


def _has_accred(db):
    cols = {r[1] for r in db.execute("PRAGMA table_info(certificate)")}
    return 'lab_accreditation' in cols


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=HERE + '/ecoa.sqlite')
    ap.add_argument('--batch', required=True)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    db = sqlite3.connect(a.db)
    if a.json:
        s02, src, un = compile_coq(db, a.batch)
        print(json.dumps({'section02': s02,
                          'section03': [{'lab': s['lab'], 'lab_id': s['id'],
                                         'certificates': [{'cert_code': c, 'date': d}
                                                          for c, d in s['certs']],
                                         'params': sorted(s['params'], key=_sortkey),
                                         'non_accredited': sorted(s['non_accredited'],
                                                                  key=_sortkey)}
                                        for s in src.values()],
                          'unresolved': un}, ensure_ascii=False, indent=1))
    else:
        render(db, a.batch)
