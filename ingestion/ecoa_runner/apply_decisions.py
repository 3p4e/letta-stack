#!/usr/bin/env python3
"""Apply the Head of QC's rulings from the confirmation worksheet.

A held value is never resolved by the pipeline. It is resolved HERE, by a named
person, against the page - and this records that: who ruled, when, on what
basis, and what the two models had read. The audit trail travels with the value
for the life of the record.

Worksheet columns (tab-separated, editable in Excel):

    doc_id  parameter  parameter_printed  read_A  read_B  DECISION  RULED_BY  BASIS

DECISION is one of:
    A            the value read A gave is correct
    B            the value read B gave is correct
    <a value>    neither; this is what the page says
    ABSENT       the row does not exist on the page - drop it
    (blank)      not yet ruled; the row stays held

Nothing is applied without RULED_BY. A decision with no name is not a decision.
"""
import os, sys, json, csv, argparse, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
COLS = ['doc_id', 'batch', 'cert_code', 'parameter', 'parameter_printed',
        'read_A', 'read_B', 'arithmetic_says', 'DECISION', 'RULED_BY', 'BASIS']


def open_items(records):
    for r in records:
        for p in r.get('parameters') or []:
            if p.get('confidence') == 'ok':
                continue
            a = (p.get('read_a') or {}).get('result')
            b = (p.get('read_b') or {}).get('result')
            yield r, p, a, b


def write_sheet(records, path, spec_only=True, spec_keys=()):
    n = 0
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, delimiter='\t', extrasaction='ignore')
        w.writeheader()
        for r, p, a, b in open_items(records):
            if spec_only and p.get('parameter') not in spec_keys:
                continue
            adj = p.get('arithmetic_says') or {}
            w.writerow({'doc_id': r.get('doc_id'), 'batch': r.get('batch_canonical'),
                        'cert_code': r.get('cert_code'), 'parameter': p.get('parameter'),
                        'parameter_printed': p.get('parameter_printed'),
                        'read_A': a, 'read_B': b,
                        'arithmetic_says': adj.get('working', ''),
                        'DECISION': '', 'RULED_BY': '', 'BASIS': ''})
            n += 1
    return n


def apply_sheet(records, path):
    idx = {}
    for r in records:
        for p in r.get('parameters') or []:
            idx[(r.get('doc_id'), p.get('parameter'), p.get('parameter_printed'))] = (r, p)
    applied = skipped = unnamed = 0
    stamp = datetime.date.today().isoformat()
    for row in csv.DictReader(open(path, encoding='utf-8'), delimiter='\t'):
        dec = (row.get('DECISION') or '').strip()
        who = (row.get('RULED_BY') or '').strip()
        if not dec:
            skipped += 1; continue
        if not who:
            unnamed += 1
            print('  ! no RULED_BY, not applied: %s / %s' % (row.get('batch'), row.get('parameter')))
            continue
        key = (row.get('doc_id'), row.get('parameter'), row.get('parameter_printed') or None)
        hit = idx.get(key) or idx.get((row.get('doc_id'), row.get('parameter'), None))
        if not hit:
            print('  ! no such row: %s %s' % (row.get('doc_id'), row.get('parameter')))
            continue
        r, p = hit
        if dec.upper() == 'ABSENT':
            p['confidence'] = 'resolved-absent'
            p['result_printed'] = None; p['result_numeric'] = None
        else:
            if dec.upper() == 'A':
                val = (p.get('read_a') or {}).get('result')
            elif dec.upper() == 'B':
                val = (p.get('read_b') or {}).get('result')
            else:
                val = dec
            p['result_printed'] = val
            # Re-derive the number from the ruled text; never trust a stale one.
            sys.path.insert(0, HERE)
            from extract_ecoa_records import norm_num
            p['result_numeric'] = norm_num(val)
            p['confidence'] = 'ok'
        p['resolution'] = {'decision': dec, 'ruled_by': who, 'date': stamp,
                           'basis': (row.get('BASIS') or '').strip() or None,
                           'read_a': (p.get('read_a') or {}).get('result'),
                           'read_b': (p.get('read_b') or {}).get('result')}
        applied += 1
    return applied, skipped, unnamed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--records', default=HERE + '/records_corpus.json')
    ap.add_argument('--sheet', default=HERE + '/decisions.tsv')
    ap.add_argument('--write', action='store_true', help='generate a blank worksheet')
    ap.add_argument('--all', action='store_true', help='include non-specification rows')
    a = ap.parse_args()
    records = json.load(open(a.records))
    sys.path.insert(0, HERE)
    from confirm_queue import SPEC_KEYS
    if a.write:
        n = write_sheet(records, a.sheet, spec_only=not a.all, spec_keys=set(SPEC_KEYS))
        print('worksheet written: %s  (%d open item(s))' % (a.sheet, n))
        print('Fill DECISION and RULED_BY, then re-run without --write to apply.')
        return
    applied, skipped, unnamed = apply_sheet(records, a.sheet)
    json.dump(records, open(a.records, 'w'), ensure_ascii=False, indent=1)
    print('applied %d ruling(s); %d still blank; %d rejected for having no RULED_BY'
          % (applied, skipped, unnamed))
    if applied:
        print('Now rebuild: python3 build_table.py --records %s --db ecoa.sqlite' % a.records)


if __name__ == '__main__':
    main()
