#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tranches 1 and 2 with section 03's laboratory lines corrected: a copy, next to the pages as sent.

    python3 tracker/build_t1_t2_lab_lines_corrected_2026-10-07.py --check    # prints and compares, writes nothing
    python3 tracker/build_t1_t2_lab_lines_corrected_2026-10-07.py --apply

Head of QC, 07.10.2026, on the issued Tranche 1 and 2 certificates of quality: *"Correct T1 and T2 also
but they stay as sent to the outside party and we will decide additionally what we are going to do, or
are we going to contact the outside party for replacement of certificates."*

The issued pages stay as sent. `design_handoff/out` and the register are not touched, so
`check_frozen_records.py` holds them as before. This script writes a separate set,
`DELIVER_2026-10-07_T1_T2_LabLines_Corrected/`. It is not issued and nobody has decided to send it.

* **Source:** each Tranche 1 and 2 page held in `FROZEN_T1_T2_2026-09-26.json`.
* **The one change:** every laboratory field that differs between `coq_build.js` `LABS_SENT` (the lines
  as sent) and `LABS` (each laboratory's own line, Head of QC 07.10.2026) is replaced:
  * Farmahem: name, LT-017, Shar Planina 20, where the old line had Kisela Voda;
  * State Phytosanitary Laboratory: LT-036;
  * UKIM: "Mother Teresa";
  * IPH: "50 Divizija".
  Nothing else on the page changes: codes, dates, values, footer and layout are as sent.
* **The guard:** substituting back must give the page as sent, byte for byte.
* **Printing:** the fleet's own printer, with the house fonts inlined. A page that prints on more than one
  sheet, or that uses a face other than the house faces, is refused. So is a page that is taller, or has a
  laboratory entry on more rows, than the page as sent. The layout is kept as sent; the 28.09 layout rules
  were given for the certificates not yet issued.
* **The PDF check:** each new PDF's text is compared with the PDF as delivered
  (`DELIVER_2026-09-30_All/CoQ`). They must differ only in the laboratory lines.

Output: one merged PDF, the initials and then the retests in code order, with a bookmark per certificate
(a zip in `DELIVER_*` is ignored by the repository); `CHANGES.tsv` listing each page's replaced lines.
"""
import argparse
import csv
import difflib
import glob
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
SNAP = os.path.join(HERE, 'FROZEN_T1_T2_2026-09-26.json')
JS = os.path.join(GAP, 'design_handoff', 'toolchain', 'coq_build.js')
SENT = os.path.join(GAP, 'DELIVER_2026-09-30_All', 'CoQ')
STAMP = '2026-10-07'
OUT = os.path.join(GAP, 'DELIVER_%s_T1_T2_LabLines_Corrected' % STAMP)
NAME = 'CoQ_T1_T2_lab_lines_corrected_%s' % STAMP
CODE = re.compile(r'CoQ-PP_26-\d{3}')
FIELDS = ('en', 'ac', 'mk', 'ad')

spec = importlib.util.spec_from_file_location('B', os.path.join(HERE, 'build_t3_bundle_2026-09-26.py'))
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)


def lab_tables():
    """LABS_SENT and LABS exactly as coq_build.js holds them."""
    js = r"""
const t = require('fs').readFileSync(process.argv[1], 'utf8');
const pick = n => eval('(' + t.match(new RegExp('const ' + n + ' = (\\{[\\s\\S]*?\\n\\});'))[1] + ')');
process.stdout.write(JSON.stringify({sent: pick('LABS_SENT'), now: pick('LABS')}));
"""
    got = json.loads(subprocess.run(['node', '-e', js, JS], check=True, capture_output=True, text=True).stdout)
    return got['sent'], got['now']


def swaps():
    """(lab, field, line as sent, corrected line) for every field the two tables disagree on."""
    sent, now = lab_tables()
    if set(sent) != set(now):
        raise SystemExit('LABS_SENT and LABS name different laboratories')
    out = [(k, f, sent[k][f], now[k][f]) for k in sorted(sent) for f in FIELDS if sent[k][f] != now[k][f]]
    olds = [x[2] for x in out]
    for k, f, old, new in out:
        if any(old in o for o in olds if o != old) or any(new in o for o in olds):
            raise SystemExit('ambiguous replacement for %s.%s' % (k, f))
    return out


def correct(page, table):
    """The page with the corrected lines, and what changed. Refused unless reversing it gives the page back."""
    text = open(page, encoding='utf-8').read()
    new, done = text, []
    for k, f, old, rep in table:
        if rep in text:
            raise SystemExit('%s already carries %r' % (os.path.basename(page), rep))
        n = new.count(old)
        if n:
            new = new.replace(old, rep)
            done.append((k, f, n))
    back = new
    for k, f, old, rep in table:
        back = back.replace(rep, old)
    if back != text:
        raise SystemExit('%s: substitution does not reverse' % os.path.basename(page))
    return new, done


def series_of(page):
    return 'Retest' if os.sep + 'REISSUE' + os.sep in page else 'Initial'


def sent_pdf(series, base):
    got = glob.glob(os.path.join(SENT, series, 'T[12]', base + '.pdf'))
    if len(got) != 1:
        raise SystemExit('%d delivered PDFs for %s' % (len(got), base))
    return got[0]


def words(pdf):
    import pymupdf
    with pymupdf.open(pdf) as d:
        return ' '.join(' '.join(p.get_text() for p in d).split())


def main(argv):
    import pymupdf
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv[1:])
    if not (a.apply or a.check):
        ap.error('pass --check or --apply')

    table = swaps()
    pages = sorted(os.path.join(GAP, p) for p in json.load(open(SNAP, encoding='utf-8'))['pages'])
    tmp = tempfile.mkdtemp(prefix='t12lab_')
    hdir = os.path.join(tmp, 'CoQ')                # layout_probe measures pages under a CoQ folder
    os.makedirs(hdir)
    todo, rows, same = [], [], []
    for p in pages:
        new, done = correct(p, table)
        if not done:
            same.append(os.path.basename(p)[:-5])
            continue
        dst = os.path.join(hdir, os.path.basename(p))
        open(dst, 'w', encoding='utf-8').write(new)
        todo.append((p, dst))
        rows.append((CODE.search(os.path.basename(p)).group(0), series_of(p), os.path.basename(p)[:-5],
                     '; '.join('%s %s ×%d' % d for d in done)))

    # Measured in the pass that prints them. The 28.09 rules (one A4 page, two rows per laboratory) were
    # given for the certificates not yet issued, and two pages as sent (-025, -107) pass them already;
    # the copy keeps the layout as sent, so it may be no taller and no laboratory entry longer than that.
    geo = {}
    probe = lambda s, page: geo.__setitem__(s, page.evaluate(B.LAYOUT_JS))
    odir = os.path.join(tmp, 'sent', 'CoQ')
    os.makedirs(odir)
    origs = [shutil.copyfile(p, os.path.join(odir, os.path.basename(p))) for p, _ in todo]
    htmls = [d for _, d in todo]
    B.render(origs, os.path.join(tmp, 'sent_pdf'), css=B.house_css(origs), probe=probe)
    made = B.render(htmls, os.path.join(tmp, 'pdf'), css=B.house_css(htmls), probe=probe)
    worse, past = [], []
    for o, h in zip(origs, htmls):
        g, n = geo[o], geo[h]
        if n['h'] > max(1123, g['h']) or len(n['lab']) != len(g['lab']) or \
                any(b > max(2, x) for x, b in zip(g['lab'], n['lab'])):
            worse.append('%s: as sent %s, corrected %s' % (os.path.basename(h), g, n))
        if g['h'] > 1123 or any(x > 2 for x in g['lab']):
            past.append((CODE.search(os.path.basename(h)).group(0), n))
    if worse:
        raise SystemExit('layout worse than the page as sent:\n  ' + '\n  '.join(worse))
    olds = [x[2] for x in table] + [x[3] for x in table]
    bad, out = [], {}
    for (src, _), pdf in zip(todo, made):
        B.assert_house_fonts(pdf)
        with pymupdf.open(pdf) as d:
            if d.page_count != 1:
                raise SystemExit('%s prints %d pages' % (os.path.basename(pdf), d.page_count))
        base = os.path.basename(src)[:-5]
        series = series_of(src)
        # The letters of the two texts once every laboratory line, old and new, is taken out. Spaces are
        # left out of the comparison: the text layer splits a letter-spaced word differently from print
        # to print ("INTERMEDIATE" against "I NT ER M ED I AT E").
        strip = lambda s: re.sub('|'.join(re.escape(''.join(o.split())) for o in olds), '', ''.join(s.split()))
        was, now = strip(words(sent_pdf(series, base))), strip(words(pdf))
        if was != now:
            sm = difflib.SequenceMatcher(None, was, now, autojunk=False)
            diff = ['%s %r→%r' % (op, was[i1:i2], now[j1:j2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != 'equal']
            bad.append('%s: %s' % (base, '; '.join(diff[:6])))
        out[pdf] = os.path.join(series, os.path.basename(os.path.dirname(sent_pdf(series, base))), base + '.pdf')
    if bad:
        raise SystemExit('the new page differs from the page as sent beyond the laboratory lines:\n  '
                         + '\n  '.join(bad))
    print('%d of %d Tranche 1/2 pages carry a line as sent and are corrected; %d carry none: %s'
          % (len(todo), len(pages), len(same), ', '.join(same) or '—'))
    print('printed one A4 page each, house fonts only; text equal to the page as sent but for the laboratory lines')
    if past:
        still = ['%s %d px, rows %s' % (c, n['h'], n['lab']) for c, n in past
                 if n['h'] > 1123 or any(x > 2 for x in n['lab'])]
        print('%d pages as sent fall outside the 28.09 layout rules (a laboratory on 3 rows, or past 1123 px); '
              'corrected, %d still do: %s' % (len(past), len(still), '; '.join(still) or '—'))

    if a.apply:
        if os.path.isdir(OUT):
            shutil.rmtree(OUT)
        for pdf, rel in out.items():
            os.makedirs(os.path.join(OUT, 'CoQ', os.path.dirname(rel)), exist_ok=True)
            shutil.copyfile(pdf, os.path.join(OUT, 'CoQ', rel))
        order = sorted(out.values(), key=lambda r: (r.split(os.sep)[0] != 'Initial', CODE.search(r).group(0)))
        merged, toc = pymupdf.open(), []
        for rel in order:
            with pymupdf.open(os.path.join(OUT, 'CoQ', rel)) as d:
                toc.append([1, '%s · %s' % (rel.split(os.sep)[0], os.path.basename(rel)[:-4]), merged.page_count + 1])
                merged.insert_pdf(d)
        merged.set_toc(toc)
        merged.save(os.path.join(OUT, NAME + '.pdf'), garbage=3, deflate=True)
        merged.close()
        shutil.rmtree(os.path.join(OUT, 'CoQ'))           # the merged file carries them, one bookmark each
        with open(os.path.join(OUT, 'CHANGES.tsv'), 'w', encoding='utf-8', newline='') as fh:
            w = csv.writer(fh, delimiter='\t', lineterminator='\n')
            w.writerow(['certificate', 'series', 'page', 'lines replaced (laboratory field ×count)'])
            w.writerows(sorted(rows))
            for k, f, old, new in table:
                w.writerow(['#', k, f, '%s → %s' % (old, new)])
        print('written:', os.path.relpath(OUT, GAP))
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
