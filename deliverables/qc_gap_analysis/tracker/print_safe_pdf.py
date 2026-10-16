#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A certificate PDF made safe to print: on each page one opaque 300 dpi background under the page's own vector text.

    python3 tracker/print_safe_pdf.py FILE.pdf [FILE.pdf …]      # rewrites each in place
    python3 tracker/print_safe_pdf.py --check FILE.pdf …         # says what transparency each still carries

Head of QC, 09.10.2026: *"When I print this PDF documents it always prints the first page and the second page is blank
and this is repeated in every other page"*. The CoQ and iCoA pages carry their fades as soft masks and transparency
groups — about eight of each per page, some 400 in a 58-page file — and a printer short of memory flattening that much
transparency drops a page, as the specification sheets did on 07.10.2026 (`specs/print_qcsp_imb.py`). The same cure,
done on the PDF itself, so nothing is re-laid out:

1. **background** — the page with its text removed (a redaction that removes text only), rendered by MuPDF to one
   opaque 300 dpi image: bands, rules, fades, pills and logo exactly as drawn;
2. **text** — the page with its images and drawings removed (text kept), and every transparency switch in what remains
   neutralised (groups dropped, soft masks /None, alpha 1), placed over the background as vector text in the
   embedded house faces.

A page is refused unless the result carries no soft mask, group, alpha or blend mode, reads exactly as before
(the same text), and matches the page to the eye (mean pixel difference at 100 dpi under 3 of 255 — what is left is
the resampling of hairline rules). The bookmarks and the document's metadata are kept.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
DPI = 300
LIMIT = 3.0


def _transparency():
    s = importlib.util.spec_from_file_location('P', os.path.join(GAP, 'specs', 'print_qcsp_imb.py'))
    P = importlib.util.module_from_spec(s)
    s.loader.exec_module(P)
    return P.transparency


transparency = _transparency()


def _single(src, i, keep_text):
    import pymupdf
    d = pymupdf.open()
    d.insert_pdf(src, from_page=i, to_page=i)
    pg = d[0]
    pg.add_redact_annot(pg.rect)
    if keep_text:
        pg.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_REMOVE,
                            graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED, text=pymupdf.PDF_REDACT_TEXT_NONE)
        for x in range(1, d.xref_length()):
            if d.xref_get_key(x, 'Group')[0] != 'null':
                d.xref_set_key(x, 'Group', 'null')
            if d.xref_get_key(x, 'Type')[1] == '/ExtGState':
                if d.xref_get_key(x, 'SMask')[0] != 'null':
                    d.xref_set_key(x, 'SMask', '/None')
                for k in ('ca', 'CA'):
                    if d.xref_get_key(x, k)[0] != 'null':
                        d.xref_set_key(x, k, '1')
                if d.xref_get_key(x, 'BM')[0] != 'null':
                    d.xref_set_key(x, 'BM', '/Normal')
    else:
        pg.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
                            text=pymupdf.PDF_REDACT_TEXT_REMOVE)
    return d


def flatten(path):
    import pymupdf
    src = pymupdf.open(path)
    if not transparency(src):
        return 'already print-safe'
    out = pymupdf.open()
    flat = lambda pg: ''.join(pg.get_text().split())
    worst = 0.0
    for i, page in enumerate(src):
        bg, tx = _single(src, i, False), _single(src, i, True)
        p = out.new_page(width=page.rect.width, height=page.rect.height)
        p.insert_image(p.rect, pixmap=bg[0].get_pixmap(dpi=DPI, alpha=False))
        p.show_pdf_page(p.rect, tx, 0)
        if flat(p) != flat(page):
            raise SystemExit('%s page %d: the text differs after flattening' % (os.path.basename(path), i + 1))
        a, b = page.get_pixmap(dpi=100, alpha=False), p.get_pixmap(dpi=100, alpha=False)
        mean = sum(abs(x - y) for x, y in zip(a.samples, b.samples)) / float(len(a.samples))
        if mean >= LIMIT:
            raise SystemExit('%s page %d: looks different after flattening (mean %.2f)' % (os.path.basename(path), i + 1, mean))
        worst = max(worst, mean)
    out.set_toc(src.get_toc())
    out.set_metadata(src.metadata)
    tmp = path + '.tmp'
    out.save(tmp, garbage=4, deflate=True)
    left = transparency(pymupdf.open(tmp))
    if left:
        os.remove(tmp)
        raise SystemExit('%s: transparency left (%s)' % (os.path.basename(path), ', '.join(left)))
    os.replace(tmp, path)
    return '%d pages, no transparency, text unchanged, worst mean pixel difference %.2f' % (out.page_count, worst)


def main(argv):
    import pymupdf
    if argv[1:2] == ['--check']:
        for f in argv[2:]:
            print('%-60s %s' % (os.path.basename(f), ', '.join(transparency(pymupdf.open(f))) or 'print-safe'))
        return 0
    for f in argv[1:]:
        print('%-60s %s' % (os.path.basename(f), flatten(f)), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
