#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Grapes and Cream grade IV in two versions, side by side, for the Head of QC and QA to choose from.

    python3 tracker/build_grc_grade_options_2026-10-08.py

Head of QC, 08.10.2026: *"create additional set of documentation for GRC for 7.0% and tolerance 0.07% and
according to that specification, and the COQ and iCOA with the same codes and all else as for the 8.00% …
me and QA will decide on the final spec grade either 7 or 8.0%"*. The tolerance is read as ± 0.70: the grade
he set on 27.09.2026 was *"7 % plus minus 10 % of nominal value … 7 % plus minus 0.7"* (6.30–7.69 %); ± 0.07
would leave -152's own 7.50 % outside its grade.

* **A — 8.00 ± 0.80** (7.20–8.79 %, `GRC_THC8 : CBD1`): the main line since 08.10.2026, copied as built.
* **B — 7.00 ± 0.70** (6.30–7.69 %, `GRC_THC7 : CBD1`): the same pages with only those grade fields changed —
  the specification sheet QCSP_001_GRC-IV_v.01, CoQ-PP_26-050 and -152, iCoA-PP_26-050 and -095. Codes, dates,
  results, citations and layout are A's.

Guards: each B page is A's with the grade fields substituted, every substitution counted; B's specification
sheet and CoQ HTML must equal, byte for byte, the 7.00 pages committed before the change (`3572a89^`); each
printed B page must read as its A page but for those fields; one A4 page each, house fonts only.

Output `DELIVER_2026-10-08_GRC_Grade_Options/`, in `A_GRC-IV_8.00/` and `B_GRC-IV_7.00/` each:
the specification for every GRC grade (I, II, IV) as one file; the GRC-IV sheet; per lot the CoQ, its iCoA and
the GRC-IV sheet as one file (-050 initial, -152 retest); each as PDF and as Word.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
OUT = os.path.join(GAP, 'DELIVER_2026-10-08_GRC_Grade_Options')
BEFORE = '3572a89^'                       # the last commit with GRC-IV at 7.00 ± 0.70
SPECS = os.path.join(GAP, 'specs', 'QCSP_001_ImB')
SHEET = 'QCSP_001_GRC-IV_v.01_Grapes_And_Cream_Grade_IV'
OTHER_SHEETS = ['QCSP_001_GRC-I_v.01_Grapes_And_Cream_Grade_I', 'QCSP_001_GRC-II_v.01_Grapes_And_Cream_Grade_II']
T3 = os.path.join(GAP, 'DELIVER_2026-09-26_T3')
COQ_SRC = {  # code -> (series, design_handoff page)
    'CoQ-PP_26-050': ('Initial', 'design_handoff/out/ISSUE_COQ/CoQ-PP_26-050_P060142_GRC_Grapes_And_Cream_Grade_IV.html'),
    'CoQ-PP_26-152': ('Retest', 'design_handoff/out/REISSUE/T3/CoQ-PP_26-152_P060142_GRC_Grapes_And_Cream_Grade_IV.html'),
}
ICOA_OF = {'CoQ-PP_26-050': 'iCoA-PP_26-050', 'CoQ-PP_26-152': 'iCoA-PP_26-095'}
CONVERT = os.path.join(GAP, 'design_handoff', 'toolchain', 'pdf_to_docx_exact.py')

# (A as printed, B) — the grade fields only
SUBS = [
    ('GRC_THC8 : CBD1', 'GRC_THC7 : CBD1'),
    ('GRC_THC8:CBD1', 'GRC_THC7:CBD1'),
    ('GRC_THC8', 'GRC_THC7'),
    ('7.20 – 8.79', '6.30 – 7.69'),
    ('7.20 &ndash; 8.79', '6.30 &ndash; 7.69'),
    ('7.20–8.79', '6.30–7.69'),
    ('8.00%', '7.00%'),
    ('0.80%', '0.70%'),
    ('nominal 8.00 ± 0.80', 'nominal 7.00 ± 0.70'),
]
PCODE_SUBS = SUBS[:3]                     # the iCoA prints the product code and nothing else of the grade


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def to_b(text, what, need=1, subs=SUBS):
    """A's page with the grade fields substituted. Refused unless at least `need` fields changed and nothing of
    A's grade is left."""
    n = 0
    for a, b in subs:
        k = text.count(a)
        text = text.replace(a, b)
        n += k
    if n < need:
        raise SystemExit('%s: only %d grade field(s) found' % (what, n))
    left = [a for a, _ in SUBS if a in text]
    if left:
        raise SystemExit('%s: A grade text left: %s' % (what, left))
    return text, n


def git_show(path):
    r = subprocess.run(['git', 'show', '%s:./%s' % (BEFORE, path)], cwd=GAP, capture_output=True)
    if r.returncode:
        raise SystemExit('no %s at %s' % (path, BEFORE))
    return r.stdout.decode('utf-8')


def words(pdf):
    import pymupdf
    with pymupdf.open(pdf) as d:
        return ' '.join(' '.join(p.get_text() for p in d).split())


def same_but_grade(a_pdf, b_pdf):
    """B's text is A's text with the grade fields substituted (spaces ignored, as text extraction splits spaced
    letters differently from print to print)."""
    sq = lambda s: ''.join(s.split())
    want = sq(words(a_pdf))
    for a, b in SUBS:
        want = want.replace(sq(a), sq(b))
    got = sq(words(b_pdf))
    if got != want:
        import difflib
        sm = difflib.SequenceMatcher(None, want, got, autojunk=False)
        d = ['%r→%r' % (want[i1:i2], got[j1:j2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != 'equal']
        raise SystemExit('%s differs from %s beyond the grade fields: %s' % (
            os.path.basename(b_pdf), os.path.basename(a_pdf), '; '.join(d[:8])))


def one_page(pdf):
    import pymupdf
    with pymupdf.open(pdf) as d:
        if d.page_count != 1:
            raise SystemExit('%s prints %d pages' % (os.path.basename(pdf), d.page_count))


def merge(parts, dst, title):
    import pymupdf
    book, toc = pymupdf.open(), []
    for label, pdf in parts:
        with pymupdf.open(pdf) as d:
            toc.append([1, label, book.page_count + 1])
            book.insert_pdf(d)
    book.set_toc(toc)
    book.set_metadata({'title': title, 'producer': 'Purely Plant Quality Desk'})
    book.save(dst, garbage=4, deflate=True)
    book.close()


def to_word(pdf):
    docx = pdf[:-4] + '.docx'
    subprocess.run([sys.executable, CONVERT, pdf, docx], check=True, stdout=subprocess.DEVNULL)
    return docx


def main():
    import pymupdf
    B = load('B', os.path.join(HERE, 'build_t3_bundle_2026-09-26.py'))
    P = load('P', os.path.join(GAP, 'specs', 'print_qcsp_imb.py'))
    tmp = tempfile.mkdtemp(prefix='grc_opts_')
    a_pdf, b_pdf = {}, {}

    # --- the specification sheet
    a_html = open(os.path.join(SPECS, 'SHEETS', SHEET + '.html'), encoding='utf-8').read()
    b_html, n = to_b(a_html, SHEET, need=3)
    if b_html != git_show('specs/QCSP_001_ImB/SHEETS/%s.html' % SHEET):
        raise SystemExit('B sheet is not the 7.00 sheet committed at %s' % BEFORE)
    sdir = os.path.join(tmp, 'sheet')
    os.makedirs(sdir)
    src = os.path.join(sdir, SHEET + '.html')
    open(src, 'w', encoding='utf-8').write(b_html)
    css, _, _ = P.house_fonts.font_face_css(P.page_text([src]), P.FAMILIES, P.SUBSETS)
    P.PAGES = os.path.join(tmp, 'sheet_pdf')
    os.makedirs(P.PAGES)
    made = P.print_safe([src], css, None)
    b_pdf[SHEET] = made[0]
    a_pdf[SHEET] = os.path.join(SPECS, 'PDF', SHEET + '.pdf')
    same_but_grade(a_pdf[SHEET], b_pdf[SHEET])
    one_page(b_pdf[SHEET])
    print('sheet: %d grade fields; B equals the 7.00 sheet of %s' % (n, BEFORE))

    # --- the CoQs and their iCoAs
    coq_b, icoa_b = [], []
    for code, (series, page) in sorted(COQ_SRC.items()):
        name = os.path.basename(page)
        a_coq_html = open(os.path.join(T3, 'CoQ', series, 'HTML', name), encoding='utf-8').read()
        if a_coq_html != open(os.path.join(GAP, page), encoding='utf-8').read():
            raise SystemExit('%s: the delivered page is not the built page' % code)
        b_coq_html, n = to_b(a_coq_html, code, need=3)
        if b_coq_html != git_show(page):
            raise SystemExit('%s: B is not the 7.00 page committed at %s' % (code, BEFORE))
        d = os.path.join(tmp, 'CoQ', series)
        os.makedirs(d, exist_ok=True)
        dst = os.path.join(d, name)
        open(dst, 'w', encoding='utf-8').write(b_coq_html)
        coq_b.append(dst)
        a_pdf[code] = os.path.join(T3, 'CoQ', series, 'PDF', name[:-5] + '.pdf')
        print('%s: %d grade fields; B equals the 7.00 page of %s' % (code, n, BEFORE))
        ic = ICOA_OF[code]
        got = [f for f in os.listdir(os.path.join(T3, 'iCoA', series, 'HTML')) if f.startswith(ic + '_')]
        if len(got) != 1:
            raise SystemExit('%d iCoA pages for %s' % (len(got), ic))
        a_ic_html = open(os.path.join(T3, 'iCoA', series, 'HTML', got[0]), encoding='utf-8').read()
        b_ic_html, n = to_b(a_ic_html, ic, need=1, subs=PCODE_SUBS)
        if n != 1 or any(a in b_ic_html for a, _ in SUBS):
            raise SystemExit('%s: %d product codes, or other grade text on the page' % (ic, n))
        d = os.path.join(tmp, 'iCoA', series)
        os.makedirs(d, exist_ok=True)
        dst = os.path.join(d, got[0])
        open(dst, 'w', encoding='utf-8').write(b_ic_html)
        icoa_b.append(dst)
        a_pdf[ic] = os.path.join(T3, 'iCoA', series, 'PDF', got[0][:-5] + '.pdf')
        print('%s: %d grade field(s)' % (ic, n))
    pdir = os.path.join(tmp, 'pdf_coq')
    for h, pdf in zip(coq_b, B.render(coq_b, pdir, None, B.house_css(coq_b), B.layout_probe)):
        b_pdf[re.match(r'CoQ-PP_26-\d{3}', os.path.basename(h)).group(0)] = pdf
    pdir = os.path.join(tmp, 'pdf_icoa')
    for h, pdf in zip(icoa_b, B.render(B.print_copies(icoa_b), pdir, None, '', B.layout_probe)):
        b_pdf[re.match(r'iCoA-PP_26-\d{3}', os.path.basename(h)).group(0)] = pdf
    B.assert_layout()
    for k, pdf in b_pdf.items():
        if k != SHEET:
            B.assert_house_fonts(pdf)
        one_page(pdf)
        same_but_grade(a_pdf[k], pdf)
    print('B pages: one A4 page each, house fonts, the same text as A but for the grade fields')

    # --- the sets
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    for opt, pdfs, grade, pcode in (('A_GRC-IV_8.00', a_pdf, '8.00 ± 0.80 (7.20–8.79 %)', 'GRC_THC8-CBD1'),
                                    ('B_GRC-IV_7.00', b_pdf, '7.00 ± 0.70 (6.30–7.69 %)', 'GRC_THC7-CBD1')):
        o = os.path.join(OUT, opt)
        os.makedirs(o)
        files = []
        f = os.path.join(o, '%s_GRC-IV_%s.pdf' % (SHEET.split('_Grapes')[0], opt[-4:]))
        shutil.copyfile(pdfs[SHEET], f)
        files.append(f)
        parts = [('QCSP_001_GRC-I_v.01', os.path.join(SPECS, 'PDF', OTHER_SHEETS[0] + '.pdf')),
                 ('QCSP_001_GRC-II_v.01', os.path.join(SPECS, 'PDF', OTHER_SHEETS[1] + '.pdf')),
                 ('QCSP_001_GRC-IV_v.01 · %s' % grade, pdfs[SHEET])]
        f = os.path.join(o, 'QCSP_001_GRC_v.01_Grapes_And_Cream_all_grades_GRC-IV_%s.pdf' % opt[-4:])
        merge(parts, f, 'Purely Plant — QCSP_001 Grapes and Cream, every grade — GRC-IV %s' % grade)
        files.append(f)
        for code, (series, _) in sorted(COQ_SRC.items()):
            ic = ICOA_OF[code]
            f = os.path.join(o, 'P060142_%s_%s_%s+%s+QCSP_001_GRC-IV_v.01.pdf' % (pcode, series, code, ic))
            merge([(code, pdfs[code]), (ic, pdfs[ic]), ('QCSP_001_GRC-IV_v.01', pdfs[SHEET])], f,
                  'Purely Plant — GRC102501/1 (P060142) — %s, %s and QCSP_001_GRC-IV_v.01 (%s)' % (code, ic, grade))
            files.append(f)
        for f in files:
            n_pdf = pymupdf.open(f).page_count
            docx = to_word(f)
            print('%-15s %-92s %d page(s) + Word' % (opt, os.path.basename(f), n_pdf))
    shutil.rmtree(tmp, ignore_errors=True)
    print('written:', os.path.relpath(OUT, GAP))
    return 0


if __name__ == '__main__':
    sys.exit(main())
