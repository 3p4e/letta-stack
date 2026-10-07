#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Carry the rebuilt Tranche 3 and out-of-tranche pages into the deliveries their builders cannot rebuild.

    python3 tracker/sync_unissued_deliveries_2026-10-07.py --check     # compares, writes nothing
    python3 tracker/sync_unissued_deliveries_2026-10-07.py --apply

Run after `node design_handoff/toolchain/build_v40.js`, `tracker/build_t3_bundle_2026-09-26.py` and
`tracker/build_nontranche_bundle_2026-09-27.py`. Those three rebuild every certificate not yet issued from the
register, and the Tranche 3 and out-of-tranche bundles with them. The 29.09 Paired and 30.09 All deliveries
cannot be rebuilt: their builders read /tmp folders that no longer exist. So their pages are replaced in place.

Three rulings of the Head of QC, 07.10.2026, change those pages:

1. **Grapes And Cream** (`apply_potency_grades.py`, `potency_grades_2026-09-15.csv`):
   * the four GRC results fill three ranges, none of them empty:
     * 7.00 ± 0.70;
     * 10.00 ± 1.00;
     * 12.00 ± 1.00;
   * GRC-III (8.00 ± 0.80) holds nothing and is removed;
   * -152 (7.50 %) moves from GRC-III to GRC-IV (`GRC_THC7 : CBD1`, `QCSP_001_GRC-IV_v.01`), and so does its
     internal certificate iCoA-PP_26-095;
   * the file names carrying the grade change with it.
2. **Phenotype, Tranche 3** (`apply_t3_phenotype_ruling_2026-10-07.py`):
   * no CoQ or iCoA prints Indica or Sativa alone; the thirteen that did are Hybrid, Indica dominant;
   * a hybrid's known leaning is spelled out where no split is on record (23 pages).
3. **Processing field on the iCoA** (`__owner-selrow-fit` in both iCoA bases):
   * the row of 30.09.2026 ran past the right margin and cut off the Hand chip;
   * it now takes the CoQ's chip scale and ends level with the values below.

The rebuilt bundles' own page PDFs are the source (`DELIVER_2026-09-26_T3/{CoQ,iCoA}/*/PDF`,
`DELIVER_2026-09-27_NoTranche/{CoQ,iCoA}/*/PDF`). In every PDF of the two deliveries:

* every page whose title and own code identify a Tranche 3 or out-of-tranche certificate is replaced, in place,
  bookmarks kept. These are a CoQ (CERTIFICATE OF QUALITY + CoQ-PP_26-nnn) or an iCoA (CERTIFICATE OF ANALYSIS +
  iCoA-PP_26-nnn).
* Pages of Tranches 1 and 2 are not touched (issued, Head of QC 26.09.2026), and neither are attached external
  certificates.

A single file takes its certificate's current name, and the two zips of the 30.09 delivery follow. The run then
checks:

* every Tranche 3 and out-of-tranche page in the two deliveries reads exactly as its rebuilt source;
* every other page reads as before.

The pages replaced are logged in `UNISSUED_SYNC_2026-10-07.tsv`.
"""
import argparse
import csv
import glob
import os
import re
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
SOURCES = [os.path.join(GAP, 'DELIVER_2026-09-26_T3'), os.path.join(GAP, 'DELIVER_2026-09-27_NoTranche')]
TARGETS = [os.path.join(GAP, 'DELIVER_2026-09-29_Paired'), os.path.join(GAP, 'DELIVER_2026-09-30_All')]
ALL = os.path.join(GAP, 'DELIVER_2026-09-30_All')
LOG = os.path.join(HERE, 'UNISSUED_SYNC_2026-10-07.tsv')
NAME = re.compile(r'^((?:CoQ|iCoA)-PP_26-\d{3})_[^_]')


def squash(text):
    return ''.join(text.split())


def own(text):
    """('CoQ' | 'iCoA', own code) from the page's title, or None for any other page."""
    s = squash(text)
    if 'CERTIFICATEOFQUALITY' in s[:120].upper():
        m = re.search(r'CoQ-PP_26-\d{3}', text)
        return ('CoQ', m.group(0)) if m else None
    if s.upper().startswith('CERTIFICATEOFANALYSIS'):
        m = re.search(r'iCoA-PP_26-\d{3}', s)
        return ('iCoA', m.group(0)) if m else None
    return None


def sources():
    """(kind, code) -> the rebuilt page PDF, from the Tranche 3 and out-of-tranche bundles."""
    import pymupdf
    out = {}
    for root in SOURCES:
        for pdf in sorted(glob.glob(os.path.join(root, '*', '*', 'PDF', '*.pdf'))):
            with pymupdf.open(pdf) as d:
                if d.page_count != 1:
                    raise SystemExit('%s has %d pages' % (pdf, d.page_count))
                k = own(d[0].get_text())
            if not k or not os.path.basename(pdf).startswith(k[1] + '_'):
                raise SystemExit('%s identifies as %s' % (pdf, k))
            if k in out:
                raise SystemExit('%s %s rebuilt twice: %s and %s' % (k + (out[k], pdf)))
            out[k] = pdf
    return out


def renamed(path, src):
    """The file's name after its certificate's: the rebuilt page's stem, keeping a paired file's iCoA suffix."""
    base = os.path.basename(path)
    m = NAME.match(base)
    stem = os.path.basename(src)[:-4]
    if not m or not stem.startswith(m.group(1) + '_'):
        return path
    tail = base[base.index('__'):] if '__' in base else '.pdf'
    return os.path.join(os.path.dirname(path), stem + (tail if tail != '.pdf' else '.pdf'))


def main(argv):
    import pymupdf
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv[1:])
    if not (a.apply or a.check):
        ap.error('pass --check or --apply')

    src = sources()
    text_of = {}
    for k, p in src.items():
        with pymupdf.open(p) as d:
            text_of[k] = squash(d[0].get_text())
    print('%d rebuilt pages: %d CoQ, %d iCoA' % (len(src), sum(1 for k in src if k[0] == 'CoQ'),
                                                sum(1 for k in src if k[0] == 'iCoA')))

    tmp = tempfile.mkdtemp(prefix='sync_')
    log, renames, before = [], {}, {}
    for root in TARGETS:
        for path in sorted(glob.glob(os.path.join(root, '**', '*.pdf'), recursive=True)):
            doc = pymupdf.open(path)
            ks = [own(doc[i].get_text()) for i in range(doc.page_count)]
            before[path] = [squash(doc[i].get_text()) for i in range(doc.page_count)]
            hits = [(i, k) for i, k in enumerate(ks) if k in src]
            single = doc.page_count == 1 or (doc.page_count == 2 and len(hits) == 2)
            first = next((k for k in ks if k and k[0] == 'CoQ'), None) or next((k for k in ks if k), None)
            target = renamed(path, src[first]) if single and first in src else path
            if not hits:
                doc.close()
                continue
            toc = doc.get_toc(simple=False)
            for i, k in hits:
                with pymupdf.open(src[k]) as n:
                    doc.insert_pdf(n, start_at=i)
                doc.delete_page(i + 1)
                log.append((os.path.relpath(path, GAP), str(i + 1), k[1],
                            'changed' if before[path][i] != text_of[k] else 'reprinted'))
            if target != path:
                renames[path] = target
                log.append((os.path.relpath(path, GAP), 'renamed', os.path.basename(target), ''))
            if a.apply:
                old_stem, new_stem = os.path.basename(path)[:-4].split('__')[0], os.path.basename(target)[:-4].split('__')[0]
                for t in toc:
                    if isinstance(t[1], str) and old_stem != new_stem:
                        t[1] = t[1].replace(old_stem, new_stem)
                doc.set_toc(toc)
                fd, outp = tempfile.mkstemp(suffix='.pdf', dir=tmp)
                os.close(fd)
                doc.save(outp, garbage=3, deflate=True)
                doc.close()
                os.remove(path)
                shutil.move(outp, target)
            else:
                doc.close()
    changed = sorted({x[2] for x in log if x[3] == 'changed'})
    print('%d page replacements in %d files; %d certificates read differently: %s' % (
        sum(1 for x in log if x[1] != 'renamed'), len({x[0] for x in log}), len(changed), ', '.join(changed)))
    for p, t in renames.items():
        print('renamed %s -> %s' % (os.path.relpath(p, GAP), os.path.basename(t)))

    if a.apply:
        # the zips of the 30.09 delivery hold its single files: every entry takes the file now on disk
        for zname in ('CoQ_all_2026-09-30.zip', 'iCoA_all_2026-09-30.zip'):
            zp = os.path.join(ALL, zname)
            fd, tz = tempfile.mkstemp(suffix='.zip', dir=tmp)
            os.close(fd)
            n = 0
            with zipfile.ZipFile(zp) as zin, zipfile.ZipFile(tz, 'w', zipfile.ZIP_DEFLATED) as zout:
                for info in zin.infolist():
                    p = os.path.join(ALL, info.filename)
                    p = renames.get(p, p)
                    if not os.path.exists(p):
                        raise SystemExit('%s: %s is not on disk' % (zname, info.filename))
                    name = os.path.relpath(p, ALL).replace(os.sep, '/')
                    if name != info.filename or open(p, 'rb').read() != zin.read(info.filename):
                        n += 1
                    zout.write(p, name)
            shutil.move(tz, zp)
            print('%s: %d entries renewed' % (zname, n))

        # every page of the two deliveries: a rebuilt certificate reads as its source, any other page as before
        bad = []
        for root in TARGETS:
            for path in sorted(glob.glob(os.path.join(root, '**', '*.pdf'), recursive=True)):
                was = before.get(next((p for p, t in renames.items() if t == path), path))
                with pymupdf.open(path) as d:
                    now = [squash(d[i].get_text()) for i in range(d.page_count)]
                    ks = [own(d[i].get_text()) for i in range(d.page_count)]
                if was is None or len(was) != len(now):
                    bad.append('%s: page count %s -> %d' % (os.path.relpath(path, GAP), was and len(was), len(now)))
                    continue
                for i, (w, n_, k) in enumerate(zip(was, now, ks)):
                    if k in src and n_ != text_of[k]:
                        bad.append('%s p%d: %s does not read as its source' % (os.path.relpath(path, GAP), i + 1, k[1]))
                    elif k not in src and n_ != w:
                        bad.append('%s p%d: a page not rebuilt changed' % (os.path.relpath(path, GAP), i + 1))
        if bad:
            raise SystemExit('after the sync:\n  ' + '\n  '.join(bad[:40]))
        with open(LOG, 'w', encoding='utf-8', newline='') as fh:
            w = csv.writer(fh, delimiter='\t', lineterminator='\n')
            w.writerow(['file', 'page', 'certificate', 'text'])
            w.writerows(sorted(log))
        print('every rebuilt page reads as its source, every other page as before; written:',
              os.path.relpath(LOG, GAP))
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
