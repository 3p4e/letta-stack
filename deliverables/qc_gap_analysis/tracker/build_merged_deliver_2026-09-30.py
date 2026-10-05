#!/usr/bin/env python3
"""Build merged Initial and Retest PDFs across all tranches in DELIVER_2026-09-30_All.

Outputs (in DELIVER_2026-09-30_All/):
  Initial/CoQ_Initial_T1_T2_T3_2026-09-30.pdf   — all initial CoQs merged
  Initial/iCoA_Initial_T1_T2_T3_2026-09-30.pdf  — all initial iCoAs merged
  Retest/CoQ_Retest_T1_T2_T3_2026-09-30.pdf     — all retest CoQs merged
  Retest/iCoA_Retest_T1_T2_T3_2026-09-30.pdf    — all retest iCoAs merged
"""
import glob, os, re, sys
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
STAMP = '2026-09-30'
DELIVER = os.path.join(GAP, 'DELIVER_%s_All' % STAMP)

CODE = re.compile(r'^(?:CoQ|iCoA)-PP_26-(\d{3})')
TRANCHES = ['T1', 'T2', 'T3', 'NoTranche']


def sort_key(p):
    m = CODE.match(os.path.basename(p))
    return int(m.group(1)) if m else 999


def merge_pages(paths, dest):
    out = pymupdf.open()
    toc = []
    for p in paths:
        d = pymupdf.open(p)
        for pg in d:
            txt = pg.get_text()
            code_m = re.search(r'(?:CoQ|iCoA)-PP_26-\d{3}', txt)
            label = code_m.group(0) if code_m else os.path.splitext(os.path.basename(p))[0]
            out.insert_pdf(d, from_page=pg.number, to_page=pg.number)
            toc.append([1, label, out.page_count])
        d.close()
    out.set_toc(toc)
    out.set_metadata({'title': 'Purely Plant — Certificates of Quality',
                      'producer': 'Purely Plant Quality Desk'})
    out.save(dest, garbage=4, deflate=True)
    out.close()
    return len(toc)


def build_section(section_label):
    coq_paths = []
    ico_paths = []
    for tr in TRANCHES:
        coq_dir = os.path.join(DELIVER, 'CoQ', section_label, tr)
        ico_dir = os.path.join(DELIVER, 'iCoA', section_label, tr)
        coq_paths += sorted(glob.glob(os.path.join(coq_dir, '*.pdf')), key=sort_key)
        ico_paths += sorted(glob.glob(os.path.join(ico_dir, '*.pdf')), key=sort_key)

    out_dir = os.path.join(DELIVER, section_label)
    os.makedirs(out_dir, exist_ok=True)

    coq_out = os.path.join(out_dir, 'CoQ_%s_T1_T2_T3_%s.pdf' % (section_label, STAMP))
    n_coq = merge_pages(coq_paths, coq_out)
    print('  CoQ  %s: %d pages → %s' % (section_label, n_coq, os.path.basename(coq_out)))

    if ico_paths:
        ico_out = os.path.join(out_dir, 'iCoA_%s_T1_T2_T3_%s.pdf' % (section_label, STAMP))
        n_ico = merge_pages(ico_paths, ico_out)
        print('  iCoA %s: %d pages → %s' % (section_label, n_ico, os.path.basename(ico_out)))


def main():
    print('Building Initial merged ...')
    build_section('Initial')
    print('Building Retest merged ...')
    build_section('Retest')
    return 0


if __name__ == '__main__':
    sys.exit(main())
