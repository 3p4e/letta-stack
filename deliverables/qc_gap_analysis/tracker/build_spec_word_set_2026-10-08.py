#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The specifications changed on 08.10.2026, as merged Word files, and every specification as one Word file.

    python3 specs/merge_qcsp_by_strain.py              # first: the per-strain PDFs and the all-58 PDF
    python3 tracker/build_spec_word_set_2026-10-08.py

Head of QC, 08.10.2026: *"make the pinpoint edits only to these … documents and then give me merged word files with
all of these changes, and one final merged word document with all the specs"*. The edits are in
`specs/build_qcsp_imb.py` (`PHENOTYPE_RULING`: every OPM grade Hybrid · Indica dominant; KC-I, HPA-I/II/III, BG-I/II
and BSS-III Hybrid) and the Grapes and Cream grade IV (8.00 ± 0.80, `tracker/apply_grc_grade_8_2026-10-08.py`).

Into `DELIVER_2026-10-08_Specs/`:
* for each strain with a changed sheet (OPM, KC, HPA, BG, BSS, GRC): its all-grades PDF, taken from the per-strain
  zip unchanged, and the same as Word;
* every one of the 58 sheets as one Word file, from `QCSP_001_ImB_all_58_specifications_2026-10-08.pdf`.

The Word files are the PDF pages (`design_handoff/toolchain/pdf_to_docx_exact.py`): each page's graphics behind real,
editable text in the house faces. Each is refused unless it has as many pages as its PDF and every changed sheet in
it prints what the ruling says.
"""
import glob
import os
import re
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
STAMP = '2026-10-08'
OUT = os.path.join(GAP, 'DELIVER_%s_Specs' % STAMP)
ZIP = os.path.join(GAP, 'specs', 'QCSP_001_ImB', '_zip', 'QCSP_001_ImB_by_strain_%s.zip' % STAMP)
ALL = os.path.join(OUT, 'QCSP_001_ImB_all_58_specifications_%s.pdf' % STAMP)
CONVERT = os.path.join(GAP, 'design_handoff', 'toolchain', 'pdf_to_docx_exact.py')
CHANGED = ('OPM', 'KC', 'HPA', 'BG', 'BSS', 'GRC')
# what each changed sheet must print, read off the PDF text: (code, phenotype words, potency words)
EXPECT = {
    'QCSP_001_OPM-I_v.01': ('HYBRID', 'INDICA DOMINANT'), 'QCSP_001_KC-I_v.01': ('HYBRID', None),
    'QCSP_001_HPA-I_v.01': ('HYBRID', None), 'QCSP_001_HPA-II_v.01': ('HYBRID', None),
    'QCSP_001_HPA-III_v.01': ('HYBRID', None), 'QCSP_001_BG-I_v.01': ('HYBRID', None),
    'QCSP_001_BG-II_v.01': ('HYBRID', None), 'QCSP_001_BSS-III_v.01': ('HYBRID', None),
}


def pages(pdf):
    import pymupdf
    with pymupdf.open(pdf) as d:
        return d.page_count


def to_word(pdf):
    docx = pdf[:-4] + '.docx'
    subprocess.run([sys.executable, CONVERT, pdf, docx], check=True, stdout=subprocess.DEVNULL)
    return docx


def word_pages(docx):
    """Pages of the Word file as LibreOffice lays it out."""
    import tempfile
    import pymupdf
    tmp = tempfile.mkdtemp(prefix='wordpages_')
    subprocess.run(['soffice', '-env:UserInstallation=file://%s/lo' % tmp, '--headless', '--convert-to', 'pdf',
                    '--outdir', tmp, docx], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with pymupdf.open(os.path.join(tmp, os.path.basename(docx)[:-5] + '.pdf')) as d:
        return d.page_count


def check_sheets(pdf):
    """Every changed sheet in this PDF prints the ruled phenotype; GRC-IV prints 8.00 ± 0.80."""
    import pymupdf
    bad = []
    with pymupdf.open(pdf) as d:
        for p in d:
            t = ' '.join(p.get_text().split())
            code = re.search(r'QCSP_001_[A-Z]+-[IVX]+_v\.01', t)
            if not code:
                continue
            code = code.group(0)
            if code in EXPECT:
                ph, lean = EXPECT[code]
                pt = t[t.find('PHENOTYPE'):t.find('CHEMOTYPE')]
                if '☒ HYBRID' not in pt.replace('☒HYBRID', '☒ HYBRID') or ('☒ INDICA' in pt or '☒ SATIVA' in pt):
                    bad.append('%s: phenotype reads %r' % (code, pt[:80]))
                if lean and lean not in pt:
                    bad.append('%s: no %s' % (code, lean))
                if not lean and 'DOMINANT' in pt:
                    bad.append('%s: prints a leaning' % code)
            if code == 'QCSP_001_GRC-IV_v.01' and not ('8.00%' in t and '0.80%' in t and 'GRC_THC8' in t):
                bad.append('GRC-IV does not print 8.00 ± 0.80 / GRC_THC8')
    return bad


def main():
    os.makedirs(OUT, exist_ok=True)
    if not os.path.exists(ALL):
        raise SystemExit('run specs/merge_qcsp_by_strain.py first: %s is missing' % os.path.relpath(ALL, GAP))
    made = []
    with zipfile.ZipFile(ZIP) as z:
        for name in z.namelist():
            abbr = re.match(r'QCSP_001_([A-Z0-9]+)_v\.01_', name).group(1)
            if abbr in CHANGED:
                dst = os.path.join(OUT, name)
                open(dst, 'wb').write(z.read(name))
                made.append(dst)
    if sorted(re.match(r'QCSP_001_([A-Z0-9]+)_', os.path.basename(p)).group(1) for p in made) != sorted(CHANGED):
        raise SystemExit('the per-strain zip does not hold one file for each of %s' % ', '.join(CHANGED))
    bad = []
    for pdf in sorted(made) + [ALL]:
        bad += check_sheets(pdf)
    if bad:
        raise SystemExit('refused:\n  ' + '\n  '.join(bad))
    for pdf in sorted(made) + [ALL]:
        docx = to_word(pdf)
        n, w = pages(pdf), word_pages(docx)
        if n != w:
            raise SystemExit('%s: %d pages in the PDF, %d in Word' % (os.path.basename(docx), n, w))
        print('%-64s %2d page%s  PDF %.1f MiB  Word %.1f MiB' % (os.path.basename(docx), n, '' if n == 1 else 's',
              os.path.getsize(pdf) / 1048576.0, os.path.getsize(docx) / 1048576.0))
    return 0


if __name__ == '__main__':
    sys.exit(main())
