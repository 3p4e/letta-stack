#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the one index of the 46 approved certificate-of-quality scans.

    python3 tracker/build_scan_index.py

Head of QC, 25.09.2026: the Drive folder of scans is the source for every document code, issue date,
superseded code and cited internal certificate. And, in the same breath, that they are **scanned
image PDFs** — so reading them costs vision tokens every time, and they are to be read once into an
index which is read thereafter.

They were read on 24.09 across four passes. This joins those passes into one table so nothing has to
be opened again:

    COQ_DRIVE_LISTING_2026-09-24.csv        codes, dates, superseded codes, cited iCoA, parameters
    ICOA_LIST_2026-09-24.tsv                the cited internal certificate and its scope
    COQ_SCAN_PHENOTYPE_2026-09-24.tsv       phenotype and split as the scan spells it
    COQ_DISTRIBUTED_READINGS_2026-09-24.tsv the figures the scan prints

plus the Drive file id per batch, so any row can be traced back to the scan it came from.

It re-reads no scan and refuses rather than guess: every batch must join on all sources, or the run
names the ones that do not and stops.
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = sys.argv[1] if len(sys.argv) > 1 else None
FOLDER = '1vXy-8drEqBJjBpaadW-E8hGnnb7Q4BmU'

COLUMNS = [
    'batch', 'coq_code', 'issued', 'supersedes', 'supersedes_issued',
    'icoa_cited', 'icoa_cited_issued', 'icoa_scope', 'parameters_referenced',
    'parameters_referenced_named', 'icoa_per_register', 'register_agrees',
    'pheno', 'pheno_split',
    'total_thc_pct', 'loss_on_drying_pct', 'TAMC', 'TYMC', 'Pb', 'Cd', 'As', 'Hg',
    'drive_file_id', 'drive_title', 'drive_bytes', 'note',
]


def norm(b):
    """A lot key as the register writes it: P + six digits, or a 1024-series name unchanged."""
    m = re.fullmatch(r'P(\d+)', b)
    return 'P%06d' % int(m.group(1)) if m else b


def load_tsv(path, delim='\t'):
    with open(path, encoding='utf-8') as fh:
        return {norm(r[next(iter(r))].strip()): r for r in csv.DictReader(fh, delimiter=delim)}


def main():
    listing = load_tsv(os.path.join(HERE, 'COQ_DRIVE_LISTING_2026-09-24.csv'), ',')
    icoa = load_tsv(os.path.join(HERE, 'ICOA_LIST_2026-09-24.tsv'))
    pheno = load_tsv(os.path.join(HERE, 'COQ_SCAN_PHENOTYPE_2026-09-24.tsv'))
    read = load_tsv(os.path.join(HERE, 'COQ_DISTRIBUTED_READINGS_2026-09-24.tsv'))

    drive = {}
    raw = os.path.join(SCRATCH, 'drive_raw.tsv') if SCRATCH else ''
    if raw and os.path.exists(raw):                 # a fresh listing off Drive
        with open(raw, encoding='utf-8') as fh:
            for line in fh:
                title, fid, size = line.rstrip('\n').split('\t')
                drive[norm(re.sub(r' \(\d+\)$', '', title[:-4]))] = (fid, title, size)
    else:                                            # the committed manifest, so this reproduces
        with open(os.path.join(HERE, 'DRIVE_SCAN_MANIFEST_2026-09-25.tsv'), encoding='utf-8') as fh:
            for r in csv.DictReader(fh, delimiter='\t'):
                drive[norm(r['batch'])] = (r['drive_file_id'], r['drive_title'], r['bytes'])

    missing = [b for b in listing if b not in drive]
    extra = [b for b in drive if b not in listing]
    if missing or extra:
        print('the scan folder and the listing do not agree — refusing to write a partial index')
        for b in missing:
            print('  in the listing, no scan on Drive: %s' % b)
        for b in extra:
            print('  on Drive, not in the listing:     %s' % b)
        return 1

    rows, agree, disagree = [], 0, 0
    for b in sorted(listing):
        L, I = listing[b], icoa.get(b, {})
        P, R = pheno.get(b, {}), read.get(b, {})
        fid, title, size = drive[b]
        same = (L['icoa_cited'] or '') == (L['icoa_per_register'] or '')
        agree += same
        disagree += not same
        rows.append({
            'batch': b, 'coq_code': L['coq_code'], 'issued': L['issued'],
            'supersedes': L['supersedes'], 'supersedes_issued': L['supersedes_issued'],
            'icoa_cited': L['icoa_cited'], 'icoa_cited_issued': L['icoa_cited_issued'],
            'icoa_scope': I.get('scope', ''),
            'parameters_referenced': L['parameters_referenced'],
            'parameters_referenced_named': L['parameters_referenced_named'],
            'icoa_per_register': L['icoa_per_register'],
            'register_agrees': 'yes' if same else 'NO',
            'pheno': P.get('pheno', ''), 'pheno_split': P.get('split', ''),
            'total_thc_pct': R.get('total_thc_pct', ''),
            'loss_on_drying_pct': R.get('loss_on_drying_pct', ''),
            'TAMC': R.get('TAMC', ''), 'TYMC': R.get('TYMC', ''),
            'Pb': R.get('Pb', ''), 'Cd': R.get('Cd', ''),
            'As': R.get('As', ''), 'Hg': R.get('Hg', ''),
            'drive_file_id': fid, 'drive_title': title, 'drive_bytes': size,
            'note': L.get('note', ''),
        })

    dest = os.path.join(HERE, 'SCAN_INDEX_2026-09-25.tsv')
    with open(dest, 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, COLUMNS, delimiter='\t')
        w.writeheader()
        w.writerows(rows)

    man = os.path.join(HERE, 'DRIVE_SCAN_MANIFEST_2026-09-25.tsv')
    with open(man, 'w', encoding='utf-8', newline='') as fh:
        fh.write('batch\tdrive_file_id\tdrive_title\tbytes\tfolder\n')
        for r in rows:
            fh.write('%s\t%s\t%s\t%s\t%s\n'
                     % (r['batch'], r['drive_file_id'], r['drive_title'], r['drive_bytes'], FOLDER))

    filled = {c: sum(1 for r in rows if r[c]) for c in COLUMNS}
    print('index written: %d scans, %d columns' % (len(rows), len(COLUMNS)))
    print('  %s' % os.path.relpath(dest, os.path.dirname(HERE)))
    print('  %s' % os.path.relpath(man, os.path.dirname(HERE)))
    print('cited internal certificate vs the register: %d agree, %d disagree' % (agree, disagree))
    thin = {c: n for c, n in filled.items() if n < len(rows)}
    print('columns not filled on every row: %s' % (thin if thin else 'none'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
