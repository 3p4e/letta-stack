#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tranche 3 — certificates of quality and internal certificates, initial and retest, as one bundle.

    node design_handoff/toolchain/build_v40.js          # the 172 CoQ pages, from the register
    python3 tracker/build_t3_bundle_2026-09-26.py       # this: select, build iCoA, print, merge, zip

Head of QC, 26.09.2026: "Give me the Tranche 3 certificates of quality initial and retest and
Tranche 3 internal certificates of analysis initial and retest, zip them in a bundle ... also merge
the PDFs into one document."

* **Selection** — the Tranche 3 grouping of 18.09 (`drive_folders_2026-09-18.tsv`), keyed on the
  `P` lot and on the cultivation batch, over `coq_artifact_data.json`: 31 initial + 31 retest.
* **Certificates of quality** — the pages `build_v40.js` writes from the current register, so they
  carry the internal-certificate numbers of the 25.09 renumbering.
* **Internal certificates** — the Head of QC's own page, filled by `build_owner_format.build`,
  scope `1, 2, 7` for every one: no approved scan credits loss on drying to a Tranche 3 lot.
* **No approved scan covers Tranche 3.** Every value on these pages is register-sourced, and the
  fields the register cannot supply print as "—" and are listed in `REGISTER_GAPS.tsv`, never guessed.
  Phenotype comes from the register's specification record (`spc.pheno`), the split only where it is
  numeric, spelled as the approved scans spell it (`INDICA60 : SATIVA40`).
"""
import csv
import glob
import json
import os
import re
import shutil
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(GAP))
sys.path.insert(0, os.path.join(GAP, 'icoa_handoff', 'v3'))
sys.path.insert(0, os.path.join(GAP, 'live_instrument'))
import build_owner_format as own                                     # noqa: E402
from print_coq_pdfs import render                                    # noqa: E402

STAMP = '2026-09-26'
OUT = os.path.join(GAP, 'DELIVER_%s_T3' % STAMP)
COQ_OUT = os.path.join(GAP, 'design_handoff', 'out')
PLOT = re.compile(r'^P\d{6}$')


def tranche_map():
    m = {}
    with open(os.path.join(GAP, 'intake_tranches_2026-09-18', 'drive_folders_2026-09-18.tsv'),
              encoding='utf-8') as fh:
        for r in csv.DictReader(fh, delimiter='\t'):
            f, t = r['folder'], r['tranche']
            tail = f.rsplit('_', 1)[-1]
            if PLOT.match(tail):
                m[tail] = t
            m[f] = t
            m.setdefault(re.split(r'_P\d{6}$', f)[0].rstrip('_').replace('＊', ''), t)
    return m


def split_of(dom):
    """`INDICA 60 : SATIVA 40` → `INDICA60 : SATIVA40`, the approved scans' spelling; words stay off."""
    m = re.match(r'^\s*([A-Z]+)\s*(\d+)\s*:\s*([A-Z]+)\s*(\d+)\s*$', str(dom or ''))
    return '%s%s : %s%s' % m.groups() if m else ''


def fields(c, gaps):
    rc = c['regcode']
    pp = str(c.get('pp') or '')
    cb = str(c.get('cb') or '')
    has_p = bool(re.match(r'^[PJ]\d{5,6}$', pp))
    spc = c.get('spc') or {}

    def val(key, what, transform=lambda x: x):
        v = str(c.get(key) or '').strip()
        if not v:
            gaps.append((rc, c.get('icoa_code'), what))
            return '—'
        return transform(v)

    pheno = str(spc.get('pheno') or '').strip().upper()
    if pheno not in ('HYBRID', 'INDICA', 'SATIVA'):
        gaps.append((rc, c.get('icoa_code'), 'phenotype — no box ticked'))
        pheno = ''
    return {
        'batch': pp if has_p else cb, 'coq': rc, 'code': c['icoa_code'],
        'issued': val('icoa_issue', 'internal-certificate issue date'),
        'headline': pp if has_p else cb,
        'strain': val('strain', 'strain'),
        'pheno': pheno, 'split': split_of(spc.get('dominance')) if pheno else '',
        'pcode': val('pcode', 'product code', lambda v: v.replace(' : ', ':')),
        'spec': val('spec', 'specification reference', lambda v: re.sub(r'_v\.\d+$', '_v.03', v)),
        'testdate': val('icoa_tested', 'test date'),
        'examined': str(c.get('icoa_tested') or '').strip() or '—',
        'production': pp if has_p else '—',
        'processing': cb or '—',
        'packaging': str(c.get('pk') or '—'),
        'scope': '1,2,7',
    }


def name_of(f):
    return '%s_%s_%s.html' % (f['code'], f['headline'],
                              re.sub(r'[^A-Za-z0-9]+', '_', f['strain']).strip('_'))


def main():
    import pymupdf
    reg = json.load(open(os.path.join(GAP, 'coq_artifact_data.json'), encoding='utf-8'))
    tm = tranche_map()

    def tranche(c):
        for k in (c.get('pp'), c.get('cb'), (c.get('cb') or '').replace('＊', '')):
            if k and k in tm:
                return tm[k]

    t3 = [c for c in reg['coqs'] if tranche(c) == 'T3']
    series = {'Initial': sorted([c for c in t3 if 'retest' not in c['t']], key=lambda c: c['regcode']),
              'Retest': sorted([c for c in t3 if 'retest' in c['t']], key=lambda c: c['regcode'])}
    if (len(series['Initial']), len(series['Retest'])) != (31, 31):
        raise SystemExit('expected 31 + 31 Tranche 3 records, found %d + %d'
                         % (len(series['Initial']), len(series['Retest'])))
    codes = [c['icoa_code'] for c in t3]
    if len(set(codes)) != len(codes):
        raise SystemExit('two Tranche 3 records share an internal-certificate number')

    coq_html = {os.path.basename(p)[:13]: p for p in glob.glob(os.path.join(COQ_OUT, '**', '*.html'),
                                                               recursive=True)}
    shutil.rmtree(OUT, ignore_errors=True)
    gaps, docs = [], []                     # docs: (section, label, html path)
    for s, recs in series.items():
        cdir = os.path.join(OUT, 'CoQ', s, 'HTML')
        idir = os.path.join(OUT, 'iCoA', s, 'HTML')
        os.makedirs(cdir), os.makedirs(idir)
        for c in recs:
            src = coq_html.get(c['regcode'])
            if not src:
                raise SystemExit('%s: build_v40.js wrote no page for it' % c['regcode'])
            # the page must cite the internal certificate the register now assigns
            if c['icoa_code'] not in open(src, encoding='utf-8').read():
                raise SystemExit('%s: the CoQ page does not cite %s — rerun build_v40.js'
                                 % (c['regcode'], c['icoa_code']))
            dst = os.path.join(cdir, os.path.basename(src))
            shutil.copy2(src, dst)
            docs.append(('CoQ %s' % s, os.path.basename(src)[:-5], dst))
        for c in recs:
            f = fields(c, gaps)
            dst = os.path.join(idir, name_of(f))
            open(dst, 'w', encoding='utf-8').write(own.build(f['scope'].split(','), f))
            docs.append(('iCoA %s' % s, name_of(f)[:-5], dst))

    # print every page, keep it, and merge in section order with a bookmark per certificate
    pdf_of = {}
    for hdir in dict.fromkeys(os.path.dirname(h) for _, _, h in docs):
        pdir = os.path.join(os.path.dirname(hdir), 'PDF')
        os.makedirs(pdir, exist_ok=True)
        srcs = [h for _, _, h in docs if os.path.dirname(h) == hdir]
        pdf_of.update(zip(srcs, render(srcs, pdir)))            # one browser session per folder
    merged, toc, last = pymupdf.open(), [], None
    for sec, label, html in docs:
        d = pymupdf.open(pdf_of[html])
        if sec != last:
            toc.append([1, sec, merged.page_count + 1])
            last = sec
        toc.append([2, label, merged.page_count + 1])
        merged.insert_pdf(d)
        d.close()
    one = os.path.join(OUT, 'T3_CoQ_iCoA_Initial_Retest_%s.pdf' % STAMP)
    merged.set_toc(toc)
    merged.set_metadata({'title': 'Purely Plant — Tranche 3 — Certificates of Quality and Internal '
                                  'Certificates of Analysis, initial and retest',
                         'producer': 'Purely Plant Quality Desk'})
    merged.save(one, garbage=4, deflate=True)
    pages = merged.page_count
    merged.close()

    with open(os.path.join(OUT, 'REGISTER_GAPS.tsv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh, delimiter='\t')
        w.writerow(['coq', 'icoa', 'field the register does not hold — printed as "—"'])
        w.writerows(gaps)
    with open(os.path.join(OUT, 'CONTENTS.tsv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh, delimiter='\t')
        w.writerow(['section', 'document'])
        w.writerows((s, l) for s, l, _ in docs)

    # Each page PDF embeds its fonts whole; subsetting them is pixel-identical and takes ~40% off.
    for pdf in pdf_of.values():
        d = pymupdf.open(pdf)
        d.subset_fonts()
        d.save(pdf + '.tmp', garbage=4, deflate=True, deflate_fonts=True)
        d.close()
        os.replace(pdf + '.tmp', pdf)

    # The app delivers files up to 30 MiB, so the bundle is four zips, each under that.
    parts = [('1of4_CoQ_PDF', ['CoQ/Initial/PDF', 'CoQ/Retest/PDF', 'CONTENTS.tsv', 'REGISTER_GAPS.tsv']),
             ('2of4_iCoA_Initial_PDF', ['iCoA/Initial/PDF']),
             ('3of4_iCoA_Retest_PDF', ['iCoA/Retest/PDF']),
             ('4of4_HTML', ['CoQ/Initial/HTML', 'CoQ/Retest/HTML', 'iCoA/Initial/HTML', 'iCoA/Retest/HTML'])]
    zips = []
    for tag, members in parts:
        zpath = os.path.join(OUT, 'T3_bundle_%s_%s.zip' % (tag, STAMP))
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for m in members:
                p = os.path.join(OUT, m)
                for fp in ([p] if os.path.isfile(p) else sorted(glob.glob(os.path.join(p, '*')))):
                    z.write(fp, os.path.join('T3_%s' % STAMP, os.path.relpath(fp, OUT)))
        mib = os.path.getsize(zpath) / 1048576.0
        if mib >= 30:
            raise SystemExit('%s is %.1f MiB — over the 30 MiB the app will deliver' % (zpath, mib))
        zips.append((os.path.relpath(zpath, GAP), mib))

    n = {k: sum(1 for s, _, _ in docs if s == k) for k in dict.fromkeys(s for s, _, _ in docs)}
    print('documents: %s' % ', '.join('%s %d' % kv for kv in n.items()))
    print('merged PDF: %s — %d pages (%.1f MiB)' % (os.path.relpath(one, GAP), pages,
                                                   os.path.getsize(one) / 1048576.0))
    for z, mib in zips:
        print('zip: %s (%.1f MiB)' % (z, mib))
    print('register gaps printed as "—": %d' % len(gaps))
    for g in gaps:
        print('   %s  %s  %s' % g)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
