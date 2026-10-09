#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The certificates of quality changed by the IPH intake of 08.10.2026, as PDF and Word, and the Tranche 3 Word sets
remade from the current final package.

    python3 tracker/build_iph_update_delivery_2026-10-08.py

Head of QC, 08.10.2026: *"Make pinpoint edits with the information that I gave you and propagate it into the word
document certificate and into the PDFs … and everywhere where it's needed and give me the documents for download"*.

* `DELIVER_2026-10-08_IPH_Updates/` — CoQ-PP_26-052, -162 (IPH 1065/2026, complete), -073 and -160 (IPH 3160/2026):
  each as PDF and Word, and the four in one PDF and one Word file. The PDFs are the bundle's own pages
  (`DELIVER_2026-09-26_T3/CoQ/*/PDF`), unchanged.
* `DELIVER_2026-10-07_Merged/T3_CoQ_all_60_2026-10-07.docx` and `T3_iCoA_all_57_2026-10-07.docx` — remade from the final
  package's merged PDFs, so the Word sets carry the GRC grade and these results too.

Each Word file is the PDF page for page (`pdf_to_docx_exact.py`). Each is refused unless LibreOffice lays it out on
as many pages as the PDF has, and unless every changed certificate's PDF prints its new certificate code.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
T3 = os.path.join(GAP, 'DELIVER_2026-09-26_T3', 'CoQ')
OUT = os.path.join(GAP, 'DELIVER_2026-10-08_IPH_Updates')
FINAL = os.path.join(GAP, 'DELIVER_2026-10-07_T3_Final')
MERGED = os.path.join(GAP, 'DELIVER_2026-10-07_Merged')
CONVERT = os.path.join(GAP, 'design_handoff', 'toolchain', 'pdf_to_docx_exact.py')
CHANGED = [('CoQ-PP_26-052', 'Initial', '1065/2026'), ('CoQ-PP_26-162', 'Retest', '1065/2026'),
           ('CoQ-PP_26-073', 'Initial', '3160/2026'), ('CoQ-PP_26-160', 'Retest', '3160/2026')]
WORD_SETS = [('T3_CoQ_all_2026-10-07.pdf', 'T3_CoQ_all_60_2026-10-07.docx'),
             ('T3_iCoA_all_2026-10-07.pdf', 'T3_iCoA_all_57_2026-10-07.docx')]


def text(pdf):
    import pymupdf
    with pymupdf.open(pdf) as d:
        return ''.join(''.join(p.get_text() for p in d).split())


def pages(pdf):
    import pymupdf
    with pymupdf.open(pdf) as d:
        return d.page_count


def word(pdf, docx):
    subprocess.run([sys.executable, CONVERT, pdf, docx], check=True, stdout=subprocess.DEVNULL)
    tmp = tempfile.mkdtemp(prefix='wordpages_')
    subprocess.run(['soffice', '-env:UserInstallation=file://%s/lo' % tmp, '--headless', '--convert-to', 'pdf',
                    '--outdir', tmp, docx], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    n = pages(os.path.join(tmp, os.path.basename(docx)[:-5] + '.pdf'))
    shutil.rmtree(tmp, ignore_errors=True)
    if n != pages(pdf):
        raise SystemExit('%s: %d pages in Word, %d in the PDF' % (os.path.basename(docx), n, pages(pdf)))
    return n


def main():
    import pymupdf
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    book, toc = pymupdf.open(), []
    for code, series, cert in CHANGED:
        got = [f for f in os.listdir(os.path.join(T3, series, 'PDF')) if f.startswith(code + '_')]
        if len(got) != 1:
            raise SystemExit('%d PDFs for %s' % (len(got), code))
        src = os.path.join(T3, series, 'PDF', got[0])
        t = text(src)
        if cert not in t or pages(src) != 1:
            raise SystemExit('%s does not cite %s on one page' % (code, cert))
        dst = os.path.join(OUT, got[0])
        shutil.copyfile(src, dst)
        n = word(dst, dst[:-4] + '.docx')   # remade every run: cheap, and the converter changed on 08.10.2026
        print('%-64s %s · Word %d page' % (got[0], cert, n))
        with pymupdf.open(dst) as d:
            toc.append([1, '%s (%s, %s)' % (code, series.lower(), cert), book.page_count + 1])
            book.insert_pdf(d)
    book.set_toc(toc)
    book.set_metadata({'title': 'Purely Plant — certificates of quality updated from IPH 1065/2026 and 3160/2026, '
                                '08.10.2026', 'producer': 'Purely Plant Quality Desk'})
    both = os.path.join(OUT, 'CoQ_IPH_updates_052_162_073_160_2026-10-08.pdf')
    book.save(both, garbage=4, deflate=True)
    book.close()
    print('%-64s Word %d pages' % (os.path.basename(both), word(both, both[:-4] + '.docx')))

    for pdf, docx in WORD_SETS:
        src, dst = os.path.join(FINAL, pdf), os.path.join(MERGED, docx)
        t = text(src)
        # the CoQs carry the IPH citations; both sets carry the GRC product code of 08.10.2026
        for code, _, cert in (CHANGED if pdf.startswith('T3_CoQ') else []):
            if cert not in t:
                raise SystemExit('%s does not carry %s' % (pdf, cert))
        if 'GRC_THC8' not in t:
            raise SystemExit('%s does not carry GRC_THC8' % pdf)
        if os.path.exists(dst) and os.path.getmtime(dst) > os.path.getmtime(src) and '--again' not in sys.argv:
            print('%-64s up to date' % docx)
            continue
        print('%-64s Word %d pages' % (docx, word(src, dst)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
