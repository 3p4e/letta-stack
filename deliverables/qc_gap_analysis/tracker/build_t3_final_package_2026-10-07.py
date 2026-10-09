#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tranche 3, ready to send: each CoQ with its iCoA behind it, one file per certificate, and the merged sets.

    python3 tracker/build_t3_final_package_2026-10-07.py

Head of QC, 07.10.2026: *"give them as PDF file containing the coq and corresponding internal certificates of
analysis as individual files named by the batch number and product type … additionally all of the coqs as one
merged PDF and all of the icoas as one merged PDF document, and all coqs with their internal certificates of
analysis right behind them … merged as one PDF document … and the specifications merged"*.

Source: the pages `tracker/build_t3_bundle_2026-09-26.py` printed, `DELIVER_2026-09-26_T3/{CoQ,iCoA}/*/PDF`. These
are one A4 page each, house fonts only, rebuilt from the register on 07.10.2026. Nothing is re-rendered here.

Order: certificate-of-quality number, which is chronological (the initials, then the retests). A CoQ with no
internal certificate (-075, -079, -080: CNP tested 1, 2, 7 and 8) stands alone; its file name says so.

Before anything is written, every CoQ's printed Total Δ9-THC is held against the owner's master
(`CoQ_Analysis_Master_v57.xlsx`, sheet "CoQ Parameter Tracker v57", #4 Assay — Total Δ9-THC). The master must
record the same value, for the same batch, under the same certificate. A disagreement stops the build, except
where `NOT_YET_IN_MASTER` names the certificate found after the master was last written (-050's release result,
taken in on 27.09.2026).

Output, `DELIVER_2026-10-07_T3_Final/`:

| file | what it holds |
| --- | --- |
| `T3_CoQ+iCoA_by_batch_2026-10-07.zip` | one PDF per CoQ, its iCoA behind it, named `{batch}_{product code}_{Initial or Retest}_{CoQ}+{iCoA}.pdf` |
| `T3_CoQ_all_2026-10-07.pdf` | every CoQ |
| `T3_iCoA_all_2026-10-07.pdf` | every iCoA, in the order of its CoQ |
| `T3_CoQ_with_iCoA_2026-10-07.pdf` | each CoQ followed by its iCoA |
| `T3_Specifications_2026-10-07.pdf` | every specification sheet a Tranche 3 CoQ cites (`specs/QCSP_001_ImB/PDF`, rebuilt 07.10.2026), in code order |
| `T3_CoQ+iCoA+Spec_Initial_by_batch_2026-10-07.zip` | one PDF per initial CoQ: the CoQ, its iCoA, then the specification sheet its Total THC falls in, named `{batch}_{product code}_Initial_{CoQ}+{iCoA}+{specification}.pdf` |
| `T3_CoQ+iCoA+Spec_Retest_by_batch_2026-10-07.zip` | the same for each retest CoQ (two zips, each under GitHub's 100 MB file limit) |
| `T3_CoQ+iCoA+Spec_all_2026-10-07.pdf` | all of them in one file, in CoQ order |
| `T3_CoQ+iCoA+Spec_Initial_merged_2026-10-07.pdf` | the initials alone, as one merged file |
| `T3_CoQ+iCoA+Spec_Retest_merged_2026-10-07.pdf` | the retests alone, as one merged file |
| `CONTENTS.tsv` | the list of all of the above |

Head of QC, 07.10.2026, on the third set: *"one more deliverable for each production batch … the certificate of
quality followed by the internal certificate of analysis followed by the corresponding product specification by
the potency value of the certificate, as one merged PDF document"*. The sheet is the one the CoQ cites; the build
stops unless the CoQ prints that code and that product code, the sheet prints them too, and the printed Total THC
lies in the sheet's window (`potency_grades_2026-09-15.csv`) — but for a result the Head of QC ruled onto its
grade (`RULED_OUTSIDE`: -050, 7.05 % on GRC-IV 7.20–8.79 %, 08.10.2026).

Each merged PDF has a bookmark per certificate or sheet. `--specs` rebuilds the specifications file alone,
`--with-spec` the CoQ + iCoA + specification files and `CONTENTS.tsv` alone, `--by-series` only the initial and
retest merged files (Head of QC, 07.10.2026: *"the retest only as merged doc pdf and the initials merged alone as
one pdf"*).
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
sys.path.insert(0, HERE)
import audit_empty_results as A                                    # noqa: E402

SRC = os.path.join(GAP, 'DELIVER_2026-09-26_T3')
SPEC_PDF = os.path.join(GAP, 'specs', 'QCSP_001_ImB', 'PDF')
GRADES = os.path.join(GAP, 'potency_grades_2026-09-15.csv')
# A result the CoQ prints from a certificate found after the master's tracker sheet was last written. Each is
# named here with its source, and listed for the master; the build stops on any other disagreement.
NOT_YET_IN_MASTER = {
    # read twice off the certificate itself (intake_GRC102501_2026-09-27/two_reads.tsv); the Versa sale list is no
    # source for THC (Head of QC, 07.10.2026: it may not carry the retest values)
    'CoQ-PP_26-050': ('7.05', '031-1-К/26', 'intake_GRC102501_2026-09-27, two reads of the certificate; the tracker '
                                           'sheet\'s GRC102501 block has 11.53, 9.80, 7.50 only'),
}
MASTER = os.path.join(HERE, 'CoQ_Analysis_Master_v57.xlsx')
STAMP = '2026-10-07'
OUT = os.path.join(GAP, 'DELIVER_%s_T3_Final' % STAMP)
CODE = re.compile(r'(CoQ|iCoA)-PP_26-\d{3}')


def page_pdfs():
    out = {}
    for p in glob.glob(os.path.join(SRC, '*', '*', 'PDF', '*.pdf')):
        m = CODE.match(os.path.basename(p))
        if m:
            if m.group(0) in out:
                raise SystemExit('%s printed twice' % m.group(0))
            out[m.group(0)] = p
    return out


def master_thc():
    """(normalised batch, value) -> certificates, from the owner's tracker sheet, #4 Total Δ9-THC."""
    import openpyxl
    ws = openpyxl.load_workbook(MASTER, read_only=True, data_only=True)['CoQ Parameter Tracker v57']
    rows = list(ws.iter_rows(values_only=True))
    head = rows[1]
    col = next(i for i, h in enumerate(head) if h and str(h).startswith('#4 Assay'))
    out, cu, pp = {}, '', ''
    for r in rows[4:]:
        if r[0]:
            cu, pp = str(r[0]), str(r[1] or '')
        v = r[col]
        m = re.match(r'^\s*(\d+[.,]\d+)', str(v or ''))
        if not m:
            continue
        val = round(float(m.group(1).replace(',', '.')), 2)
        cert = str(r[col + 1] or '')
        for k in {A.N(cu), A.N(pp)} - {''}:
            out.setdefault((k, val), set()).add(cert)
    return out


def safe(s):
    return re.sub(r'[^A-Za-z0-9_+.-]+', '-', str(s)).strip('-')


def specs(rows):
    """Every specification sheet the Tranche 3 CoQs cite, merged in code order, one bookmark per sheet."""
    import pymupdf
    cited = {}
    for r in rows:
        cited.setdefault(r['spec'], []).append(r['coq'])
    book, toc = pymupdf.open(), []
    for code in sorted(cited):
        got = glob.glob(os.path.join(SPEC_PDF, code + '_*.pdf'))
        if len(got) != 1:
            raise SystemExit('%s: %d specification sheets on file' % (code, len(got)))
        with pymupdf.open(got[0]) as d:
            if d.page_count != 1:
                raise SystemExit('%s prints %d pages' % (code, d.page_count))
            if code not in d[0].get_text():
                raise SystemExit('%s: the sheet does not print its own code' % code)
            toc.append([1, '%s · cited by %s' % (code, ', '.join(c[-3:] for c in sorted(cited[code]))), book.page_count + 1])
            book.insert_pdf(d)
    book.set_toc(toc)
    book.set_metadata({'title': 'Purely Plant — Tranche 3 — the product specifications its certificates of quality cite',
                       'producer': 'Purely Plant Quality Desk'})
    dest = os.path.join(OUT, 'T3_Specifications_%s.pdf' % STAMP)
    book.save(dest, garbage=4, deflate=True)
    print('%s — %d sheets (%.1f MiB)' % (os.path.basename(dest), book.page_count, os.path.getsize(dest) / 1048576.0))
    book.close()


def spec_sheet(code):
    """The one printed sheet for a specification code, and its row of the grade table."""
    got = glob.glob(os.path.join(SPEC_PDF, code + '_*.pdf'))
    if len(got) != 1:
        raise SystemExit('%s: %d specification sheets on file' % (code, len(got)))
    m = re.match(r'^QCSP_001_([A-Z0-9]+)-([IVX]+)_v\.01$', code)
    grade = next((g for g in csv.DictReader(open(GRADES, encoding='utf-8'))
                  if m and (g['abbr'], g['numeral']) == m.groups()), None)
    if not grade:
        raise SystemExit('%s: no such grade in %s' % (code, os.path.basename(GRADES)))
    return got[0], grade


# A result outside its sheet's window that the Head of QC ruled the CoQ cites all the same (08.10.2026: GRC-IV became
# 8.00 ± 0.80 and -050's 7.05 % stays on it, "both on 8.00 ± 0.80"; tracker/apply_grc_grade_8_2026-10-08.py).
RULED_OUTSIDE = {('CoQ-PP_26-050', 'QCSP_001_GRC-IV_v.01'): 7.05}


def spec_rows(rows, pages):
    """Each row's specification sheet, held against its CoQ: same code, same product code, THC in the window."""
    import pymupdf
    bad = []
    for r in rows:
        sheet, g = spec_sheet(r['spec'])
        val = float(re.match(r'^\s*(\d+[.,]\d+)', r['thc']).group(1).replace(',', '.'))
        if not float(g['window_low']) <= val <= float(g['window_high']) and \
                RULED_OUTSIDE.get((r['coq'], r['spec'])) != val:
            bad.append('%s prints %.2f %%; %s holds %s–%s %%' % (r['coq'], val, r['spec'], g['window_low'], g['window_high']))
        with pymupdf.open(pages[r['coq']]) as d:
            t = ''.join(d[0].get_text().split())
        with pymupdf.open(sheet) as d:
            if d.page_count != 1:
                bad.append('%s prints %d pages' % (r['spec'], d.page_count))
            st = ''.join(d[0].get_text().split())
        for what, txt in (('the CoQ', t), ('the sheet', st)):
            for need in (r['spec'], (r['pcode'] or '').replace(' ', '')):
                if need not in txt:
                    bad.append('%s: %s does not print %s' % (r['coq'], what, need))
        r['spec_window'] = '%s–%s' % (g['window_low'], g['window_high'])
        r['file_with_spec'] = r['file'][:-4] + '+' + r['spec'] + '.pdf'
        r['_sheet'] = sheet
    if bad:
        raise SystemExit('refused:\n  ' + '\n  '.join(bad))


def append(book, toc, r, pages):
    """The CoQ, its iCoA and its specification sheet onto `book`, bookmarked under the CoQ."""
    import pymupdf
    toc.append([1, '%s · %s · %s · %s' % (r['coq'], r['batch'], r['pcode'], r['spec']), book.page_count + 1])
    for label, src in ((r['coq'], pages[r['coq']]), (r['icoa'], pages.get(r['icoa'])), (r['spec'], r['_sheet'])):
        if src:
            with pymupdf.open(src) as d:
                toc.append([2, label, book.page_count + 1])
                book.insert_pdf(d)


def by_series(rows, pages):
    """The initials alone and the retests alone, each as one merged PDF: CoQ, iCoA, specification per certificate."""
    import pymupdf
    for series, title in (('Initial', 'initial'), ('Retest', 'retest')):
        book, toc = pymupdf.open(), []
        for r in rows:
            if r['series'] == series:
                append(book, toc, r, pages)
        book.set_toc(toc)
        book.set_metadata({'title': 'Purely Plant — Tranche 3 — the %s certificates of quality, each with its internal '
                                    'certificate of analysis and its product specification' % title,
                           'producer': 'Purely Plant Quality Desk'})
        dest = os.path.join(OUT, 'T3_CoQ+iCoA+Spec_%s_merged_%s.pdf' % (series, STAMP))
        book.save(dest, garbage=4, deflate=True)
        print('%s — %d certificates, %d pages (%.1f MiB)' % (os.path.basename(dest), sum(1 for t in toc if t[0] == 1),
                                                            book.page_count, os.path.getsize(dest) / 1048576.0))
        book.close()


def with_spec(rows, pages):
    """Per CoQ: the CoQ, its iCoA, then the specification sheet its Total THC falls in. Two zips and one merged file."""
    import pymupdf
    tmp = tempfile.mkdtemp(prefix='t3spec_')
    book, toc = pymupdf.open(), []
    made = []
    for series in ('Initial', 'Retest'):
        zpath = os.path.join(OUT, 'T3_CoQ+iCoA+Spec_%s_by_batch_%s.zip' % (series, STAMP))
        n = 0
        with zipfile.ZipFile(zpath + '.part', 'w', zipfile.ZIP_DEFLATED) as z:
            for r in rows:
                if r['series'] != series:
                    continue
                one, sub = pymupdf.open(), []
                append(one, sub, r, pages)
                append(book, toc, r, pages)
                one.set_toc([[1, t[1], t[2]] for t in sub if t[0] == 2])
                one.set_metadata({'title': 'Purely Plant — %s — %s, %s and %s' % (
                    r['batch'], r['coq'], r['icoa'] or 'no iCoA', r['spec']), 'producer': 'Purely Plant Quality Desk'})
                p = os.path.join(tmp, r['file_with_spec'])
                one.save(p, garbage=4, deflate=True)
                one.close()
                z.write(p, r['file_with_spec'])
                os.remove(p)
                n += 1
        os.replace(zpath + '.part', zpath)
        made.append((os.path.basename(zpath), n, os.path.getsize(zpath)))
    book.set_toc(toc)
    book.set_metadata({'title': 'Purely Plant — Tranche 3 — each certificate of quality, its internal certificate '
                                'of analysis and its product specification', 'producer': 'Purely Plant Quality Desk'})
    dest = os.path.join(OUT, 'T3_CoQ+iCoA+Spec_all_%s.pdf' % STAMP)
    book.save(dest, garbage=4, deflate=True)
    print('%s — %d pages (%.1f MiB)' % (os.path.basename(dest), book.page_count, os.path.getsize(dest) / 1048576.0))
    book.close()
    for name, n, b in made:
        print('%s — %d files (%.1f MiB)' % (name, n, b / 1048576.0))
    shutil.rmtree(tmp, ignore_errors=True)


def write_contents(rows):
    rows = [{k: v for k, v in r.items() if not k.startswith('_')} for r in rows]
    with open(os.path.join(OUT, 'CONTENTS.tsv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def main(argv=()):
    import pymupdf
    reg = json.load(open(os.path.join(GAP, 'coq_artifact_data.json'), encoding='utf-8'))
    tm = A.tranche_map()

    def tranche(c):
        for k in (c.get('pp'), c.get('cb'), (c.get('cb') or '').replace('＊', '')):
            if k and k in tm:
                return tm[k]

    t3 = sorted((c for c in reg['coqs'] if tranche(c) == 'T3' and not c.get('withdrawn')), key=lambda c: c['regcode'])
    pages = page_pdfs()
    thc = master_thc()

    rows, bad = [], []
    for c in t3:
        code = c['regcode'][:13]
        r4 = next(r for r in c['rows'] if r['no'] == '4')
        m = re.match(r'^\s*(\d+[.,]\d+)', str(r4.get('res') or ''))
        val = round(float(m.group(1).replace(',', '.')), 2) if m else None
        keys = {A.N(c.get('cb')), A.N(c.get('pp')), A.N((c.get('cb') or '').replace('＊', ''))} - {''}
        keys |= {A.N(x) for x in A.chain(c.get('cb'))}
        doc = A.N(r4.get('doc'))
        hit = [cert for k in keys for cert in thc.get((k, val), ())]
        known = NOT_YET_IN_MASTER.get(code)
        if known and not hit and '%.2f' % val == known[0] and A.N(r4.get('doc')) == A.N(known[1]):
            print('NOT YET IN MASTER  %s %.2f %% (%s): %s' % (code, val, r4.get('doc'), known[2]))
        elif val is None:
            bad.append('%s prints no Total THC' % code)
        elif not hit:
            bad.append('%s prints %.2f %% (%s); the master has no such result for %s' % (code, val, r4.get('doc'), c.get('cb')))
        elif not any(doc and doc in A.N(h) for h in hit):
            bad.append('%s prints %.2f %% under %s; the master gives it under %s' % (code, val, r4.get('doc'), ' / '.join(sorted(set(hit)))))
        ic = c.get('icoa_code')
        has_icoa = ic in pages
        if code not in pages:
            bad.append('%s: no printed page' % code)
        series = 'Retest' if 'retest' in (c.get('t') or '') else 'Initial'
        batch = c['pp'] if re.match(r'^P\d{6}$', str(c.get('pp') or '')) else c.get('cb')
        name = '%s_%s_%s_%s%s.pdf' % (safe(batch), safe((c.get('pcode') or '').replace(' : ', '-')), series, code,
                                       ('+' + ic) if has_icoa else '_no-iCoA')
        rows.append({'coq': code, 'icoa': ic if has_icoa else '', 'series': series, 'batch': batch, 'cb': c.get('cb'),
                     'strain': c.get('strain'), 'pcode': c.get('pcode'), 'spec': c.get('spec'), 'thc': r4.get('res'),
                     'thc_cert': r4.get('doc'), 'file': name})
    if bad:
        raise SystemExit('refused:\n  ' + '\n  '.join(bad))
    if '--specs' in argv:
        specs(rows)
        return 0
    if '--with-spec' in argv or '--by-series' in argv:
        spec_rows(rows, pages)
        if '--with-spec' in argv:
            with_spec(rows, pages)
        by_series(rows, pages)
        write_contents(rows)
        return 0
    print('%d Tranche 3 CoQs (%d initial, %d retest), %d with an iCoA; every printed Total THC is the master\'s '
          '(same batch, same certificate) but the %d named above' % (
              len(rows), sum(r['series'] == 'Initial' for r in rows), sum(r['series'] == 'Retest' for r in rows),
              sum(bool(r['icoa']) for r in rows), sum(1 for r in rows if r['coq'] in NOT_YET_IN_MASTER)))

    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)
    tmp = tempfile.mkdtemp(prefix='t3final_')
    coq_all, ico_all, both = pymupdf.open(), pymupdf.open(), pymupdf.open()
    toc_c, toc_i, toc_b = [], [], []
    zpath = os.path.join(OUT, 'T3_CoQ+iCoA_by_batch_%s.zip' % STAMP)
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        for r in rows:
            label = '%s · %s · %s' % (r['coq'], r['batch'], r['pcode'])
            pair = pymupdf.open()
            with pymupdf.open(pages[r['coq']]) as d:
                toc_c.append([1, label, coq_all.page_count + 1])
                coq_all.insert_pdf(d)
                toc_b.append([1, label, both.page_count + 1])
                toc_b.append([2, r['coq'], both.page_count + 1])
                both.insert_pdf(d)
                pair.insert_pdf(d)
            if r['icoa']:
                with pymupdf.open(pages[r['icoa']]) as d:
                    toc_i.append([1, '%s · %s · for %s' % (r['icoa'], r['batch'], r['coq']), ico_all.page_count + 1])
                    ico_all.insert_pdf(d)
                    toc_b.append([2, r['icoa'], both.page_count + 1])
                    both.insert_pdf(d)
                    pair.insert_pdf(d)
            pair.set_toc([[1, r['coq'], 1]] + ([[1, r['icoa'], 2]] if r['icoa'] else []))
            pair.set_metadata({'title': 'Purely Plant — %s%s — %s' % (r['coq'], (' and ' + r['icoa']) if r['icoa'] else '',
                                                                       r['batch']), 'producer': 'Purely Plant Quality Desk'})
            p = os.path.join(tmp, r['file'])
            pair.save(p, garbage=4, deflate=True)
            pair.close()
            z.write(p, r['file'])
    made = []
    for doc, toc, name, title in ((coq_all, toc_c, 'T3_CoQ_all', 'certificates of quality'),
                                  (ico_all, toc_i, 'T3_iCoA_all', 'internal certificates of analysis'),
                                  (both, toc_b, 'T3_CoQ_with_iCoA', 'certificates of quality, each followed by its '
                                                                    'internal certificate of analysis')):
        doc.set_toc(toc)
        doc.set_metadata({'title': 'Purely Plant — Tranche 3 — %s' % title, 'producer': 'Purely Plant Quality Desk'})
        dest = os.path.join(OUT, '%s_%s.pdf' % (name, STAMP))
        doc.save(dest, garbage=4, deflate=True)
        made.append((os.path.basename(dest), doc.page_count, os.path.getsize(dest) / 1048576.0))
        doc.close()
    specs(rows)
    spec_rows(rows, pages)
    with_spec(rows, pages)
    by_series(rows, pages)
    write_contents(rows)
    shutil.rmtree(tmp, ignore_errors=True)
    for n, pg, mib in made:
        print('%s — %d pages (%.1f MiB)' % (n, pg, mib))
    print('%s — %d files (%.1f MiB)' % (os.path.basename(zpath), len(rows), os.path.getsize(zpath) / 1048576.0))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
