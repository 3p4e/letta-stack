#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The specification set, one PDF per strain: every grade of the strain in one document.

    python3 specs/merge_qcsp_by_strain.py

Head of QC, 07.10.2026: *"I want them … as individual PDF files per strain, all grades merged into one
document"*.

Source: the 58 sheets `specs/print_qcsp_imb.py` printed, `specs/QCSP_001_ImB/PDF` (one A4 page each, rebuilt
07.10.2026 on `potency_grades_2026-09-15.csv`). Nothing is re-rendered: the pages are joined as they are, in
grade order (I, II, III …), one bookmark per grade with its nominal, tolerance, window and product code.

Before anything is written, each sheet must print its own code, and `INDEX.json`, the grade table and the PDF
folder must name the same grades with the same nominal and tolerance. A grade the table no longer holds
(GRC-III, deleted 07.10.2026) must not be on file.

Output: `specs/QCSP_001_ImB/_zip/QCSP_001_ImB_by_strain_2026-10-07.zip`, one file per strain,
`QCSP_001_{abbr}_v.01_{Strain}_all_grades.pdf`.
"""
import csv
import glob
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
SET = os.path.join(HERE, 'QCSP_001_ImB')
PDF = os.path.join(SET, 'PDF')
GRADES = os.path.join(GAP, 'potency_grades_2026-09-15.csv')
STAMP = '2026-10-07'
ZIP = os.path.join(SET, '_zip', 'QCSP_001_ImB_by_strain_%s.zip' % STAMP)
ROMAN = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10}


def safe(s):
    return re.sub(r'[^A-Za-z0-9_.-]+', '_', s).strip('_')


def main(argv=()):
    import pymupdf
    index = json.load(open(os.path.join(SET, 'INDEX.json'), encoding='utf-8'))['sheets']
    table = {(r['abbr'], r['numeral']): r for r in csv.DictReader(open(GRADES, encoding='utf-8'))}
    on_file = {os.path.basename(p)[:-4]: p for p in glob.glob(os.path.join(PDF, '*.pdf'))}

    bad, strains = [], {}
    for s in index:
        stem = s['file'][:-5]
        t = table.get((s['cultivar'], s['grade']))
        if stem not in on_file:
            bad.append('%s: no PDF' % s['code'])
        if not t:
            bad.append('%s: the grade table holds no %s-%s' % (s['code'], s['cultivar'], s['grade']))
        elif (float(t['nominal']), float(t['tolerance'])) != (float(s['nominal']), float(s['tolerance'])):
            bad.append('%s: %s ± %s on the sheet, %s ± %s in the table' % (
                s['code'], s['nominal'], s['tolerance'], t['nominal'], t['tolerance']))
        strains.setdefault((s['cultivar'], s['strain']), []).append(dict(s, pdf=on_file.get(stem)))
    extra = set(on_file) - {s['file'][:-5] for s in index}
    if extra:
        bad.append('PDFs no sheet in INDEX.json names: %s' % ', '.join(sorted(extra)))
    missing = {k for k in table} - {(s['cultivar'], s['grade']) for s in index}
    if missing:
        bad.append('grades with no sheet: %s' % ', '.join('%s-%s' % k for k in sorted(missing)))
    if bad:
        raise SystemExit('refused:\n  ' + '\n  '.join(bad))

    tmp = tempfile.mkdtemp(prefix='qcsp_strain_')
    made = []
    with zipfile.ZipFile(ZIP + '.part', 'w', zipfile.ZIP_DEFLATED) as z:
        for (abbr, strain), sheets in sorted(strains.items(), key=lambda kv: kv[0][1]):
            sheets.sort(key=lambda s: ROMAN[s['grade']])
            book, toc = pymupdf.open(), []
            for s in sheets:
                with pymupdf.open(s['pdf']) as d:
                    if d.page_count != 1:
                        raise SystemExit('%s prints %d pages' % (s['code'], d.page_count))
                    if s['code'] not in d[0].get_text():
                        raise SystemExit('%s: the sheet does not print its own code' % s['code'])
                    toc.append([1, 'Grade %s · %.2f ± %.2f %% · %s · %s' % (
                        s['grade'], s['nominal'], s['tolerance'], s['window'], s['product_code']), book.page_count + 1])
                    book.insert_pdf(d)
            book.set_toc(toc)
            book.set_metadata({'title': 'Purely Plant — QCSP 001 — %s (%s), all grades: %s' % (
                strain, abbr, ', '.join(s['grade'] for s in sheets)), 'producer': 'Purely Plant Quality Desk'})
            name = 'QCSP_001_%s_v.01_%s_all_grades.pdf' % (abbr, safe(strain))
            p = os.path.join(tmp, name)
            book.save(p, garbage=4, deflate=True)
            made.append((name, book.page_count, os.path.getsize(p)))
            book.close()
            z.write(p, name)
    os.replace(ZIP + '.part', ZIP)
    shutil.rmtree(tmp, ignore_errors=True)
    for n, pg, b in made:
        print('%-62s %d grade%s  %.1f MiB' % (n, pg, '' if pg == 1 else 's', b / 1048576.0))
    print('%s — %d strains, %d sheets (%.1f MiB)' % (os.path.relpath(ZIP, GAP), len(made), sum(m[1] for m in made),
                                                    os.path.getsize(ZIP) / 1048576.0))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
