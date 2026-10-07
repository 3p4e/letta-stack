#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reprint every certificate of quality not yet issued and put the new page into every delivery that carries it.

    python3 tracker/patch_unissued_coq_pages_2026-10-07.py --check     # prints and measures, writes nothing
    python3 tracker/patch_unissued_coq_pages_2026-10-07.py --apply

The certificates not yet issued are Tranche 3 and the lots outside the tranches; Tranches 1 and 2 are
issued and never reprinted here (Head of QC, 26.09.2026).

Second use, the same day (Head of QC, 07.10.2026, "check the real addresses of the labs"): section 03's
laboratory lines now print what each laboratory prints on its own certificates (coq_build.js LABS), on
the 75 pages of Tranche 3 and the lots outside the tranches.

Why (Head of QC, 07.10.2026): the full microbiology panel prints where the lot's own certificate reports
it (`apply_micro_panel_ruling_2026-10-07.py`), and the certificate stays one A4 page. Thirty-two Tranche 3
pages gained rows 9.6 and 9.7. The delivered PDFs had also never taken the section-bar bevel of 01.10.2026
(commit 6b7d4d6 rebuilt the HTML; the Tranche 3 PDFs in the deliveries were left at 30.09). So every
Tranche 3 page is printed again from `design_handoff/out`, the one source, and the delivery is brought to it.

The builders of 29 and 30.09 cannot be rerun: they read intermediate folders under /tmp that no longer
exist, and they delete their output first. This script changes nothing but the Tranche 3 CoQ pages:

* the single CoQ files in `DELIVER_2026-09-30_All/CoQ/{Initial,Retest}/T3/` are replaced;
* in every merged PDF of `DELIVER_2026-09-26_T3`, `DELIVER_2026-09-29_Paired` and `DELIVER_2026-09-30_All`, a
  page whose title is CERTIFICATE OF QUALITY and whose own code is one of these certificates is replaced by
  the new page, in place; bookmarks are kept. iCoA pages, Tranche 1 and 2 pages and the lots outside the
  tranches are not touched;
* `CoQ_all_2026-09-30.zip` takes the new single files.

Every new page is printed by the fleet's own printer (`live_instrument/print_coq_pdfs.render`, house
fonts inlined) and refused unless it is one A4 page (`build_t3_bundle_2026-09-26.layout_probe`) and every
letter is in a house face (`assert_house_fonts`).
"""
import argparse
import csv
import glob
import importlib.util
import os
import re
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
OUT = os.path.join(GAP, 'design_handoff', 'out')
ALL = os.path.join(GAP, 'DELIVER_2026-09-30_All')
DELIVERIES = [os.path.join(GAP, d) for d in ('DELIVER_2026-09-26_T3', 'DELIVER_2026-09-27_NoTranche',
                                              'DELIVER_2026-09-29_Paired', 'DELIVER_2026-09-30_All')]
NT = os.path.join(GAP, 'DELIVER_2026-09-27_NoTranche', 'CoQ')     # its CoQ/{Initial,Retest}/{HTML,PDF}
ZIP = os.path.join(ALL, 'CoQ_all_2026-09-30.zip')
LOG = os.path.join(HERE, 'COQ_REPRINT_LAB_LINES_2026-10-07.tsv')
CODE = re.compile(r'CoQ-PP_26-\d{3}')

spec = importlib.util.spec_from_file_location('B', os.path.join(HERE, 'build_t3_bundle_2026-09-26.py'))
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)


def page_of(name):
    """The certificate's page in design_handoff/out, wherever the build filed it."""
    got = glob.glob(os.path.join(OUT, '**', name + '.html'), recursive=True)
    if len(got) != 1:
        raise SystemExit('%d pages for %s in design_handoff/out' % (len(got), name))
    return got[0]


def sources():
    """Delivered single file -> its page in design_handoff/out, for every certificate not yet issued."""
    out = {}
    for series in ('Initial', 'Retest'):
        for group in ('T3', 'NoTranche'):
            for pdf in sorted(glob.glob(os.path.join(ALL, 'CoQ', series, group, '*.pdf'))):
                out[pdf] = page_of(os.path.basename(pdf)[:-4])
        for pdf in sorted(glob.glob(os.path.join(NT, series, 'PDF', '*.pdf'))):
            out[pdf] = page_of(os.path.basename(pdf)[:-4])
    return out


def own_code(text):
    """The certificate's own code: a CoQ page names it first, before any superseded or iCoA code."""
    if 'CERTIFICATE OF QUALITY' not in text.upper()[:200]:
        return None
    m = CODE.search(text)
    return m.group(0) if m else None


def main(argv):
    import pymupdf
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv[1:])
    if not (a.apply or a.check):
        ap.error('pass --check or --apply')

    src = sources()
    tmp = tempfile.mkdtemp(prefix='t3coq_')
    htmls = [src[p] for p in sorted(src)]
    B.LAYOUT.clear()
    made = B.render(htmls, tmp, css=B.house_css(htmls),
                    probe=lambda s, page: B.layout_probe(os.path.join(os.sep, 'CoQ', os.path.basename(s)), page))
    B.assert_layout()
    new = {}
    for pdf in made:
        B.assert_house_fonts(pdf)
        d = pymupdf.open(pdf)
        if d.page_count != 1:
            raise SystemExit('%s prints %d pages' % (os.path.basename(pdf), d.page_count))
        code = own_code(d[0].get_text())
        d.close()
        if not code or not os.path.basename(pdf).startswith(code):
            raise SystemExit('%s: own code %s does not match its name' % (os.path.basename(pdf), code))
        new[code] = pdf
    print('printed %d CoQ pages not yet issued, one A4 page each, house fonts only' % len(new))

    log = []
    for d_ in DELIVERIES:
        for path in sorted(glob.glob(os.path.join(d_, '**', '*.pdf'), recursive=True)):
            if path in src:
                continue                                   # a single file, replaced below
            doc = pymupdf.open(path)
            hits = [(i, own_code(doc[i].get_text())) for i in range(doc.page_count)]
            hits = [(i, c) for i, c in hits if c in new]
            if not hits:
                doc.close()
                continue
            toc = doc.get_toc(simple=False)
            for i, c in hits:
                with pymupdf.open(new[c]) as n:
                    doc.insert_pdf(n, start_at=i)
                doc.delete_page(i + 1)
                log.append((os.path.relpath(path, GAP), str(i + 1), c))
            if a.apply:
                doc.set_toc(toc)
                fd, out = tempfile.mkstemp(suffix='.pdf', dir=tmp)
                os.close(fd)
                doc.save(out, garbage=3, deflate=True)
                doc.close()
                shutil.move(out, path)
            else:
                doc.close()
    for pdf, html in sorted(src.items()):
        code = CODE.search(os.path.basename(pdf)).group(0)
        log.append((os.path.relpath(pdf, GAP), '1', code))
        if a.apply:
            shutil.copyfile(new[code], pdf)
    # the out-of-tranche bundle keeps each CoQ's page as HTML too; CI's reference checks read it
    for html in sorted(glob.glob(os.path.join(NT, '*', 'HTML', '*.html'))):
        log.append((os.path.relpath(html, GAP), 'html', CODE.search(os.path.basename(html)).group(0)))
        if a.apply:
            shutil.copyfile(page_of(os.path.basename(html)[:-5]), html)

    files = sorted({x[0] for x in log})
    print('%d page replacements in %d files' % (len(log), len(files)))
    if a.apply:
        # the zip of the single CoQ files takes the new Tranche 3 files; every other entry is copied as is
        rel = {os.path.relpath(p, ALL).replace(os.sep, '/'): p for p in src if p.startswith(ALL + os.sep)}
        fd, tz = tempfile.mkstemp(suffix='.zip', dir=tmp)
        os.close(fd)
        with zipfile.ZipFile(ZIP) as zin, zipfile.ZipFile(tz, 'w', zipfile.ZIP_DEFLATED) as zout:
            n = 0
            for info in zin.infolist():
                if info.filename in rel:
                    zout.write(rel[info.filename], info.filename)
                    n += 1
                else:
                    zout.writestr(info, zin.read(info.filename))
        if n != len(rel):
            raise SystemExit('zip: replaced %d of %d files' % (n, len(rel)))
        shutil.move(tz, ZIP)
        print('CoQ_all_2026-09-30.zip: %d files replaced' % n)
        with open(LOG, 'w', encoding='utf-8', newline='') as fh:
            w = csv.writer(fh, delimiter='\t', lineterminator='\n')
            w.writerow(['file', 'page', 'certificate'])
            w.writerows(sorted(log))
        print('written:', os.path.relpath(LOG, GAP))
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
