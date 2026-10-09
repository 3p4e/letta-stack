#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tranche 3 retest certificates, merged: the CoQs, the iCoAs, and each CoQ followed by its iCoA — three PDFs.

    python3 tracker/build_t3_retest_merged_2026-10-09.py               # Tranche 3 retest
    python3 tracker/build_t3_retest_merged_2026-10-09.py nontranche    # every lot outside the tranches, initial and retest

Head of QC, 09.10.2026: *"Give me only the T3 retest iCOA and COQ as pdf merged. One file pdf with all t3 retest coqs,
one pdf with t3 retest iCOA and one pdf with COQ and icoa one after another."*; then *"Give me also all out of tranche
iCOAs and COQs"* — the same three files for the lots outside the tranches (`DELIVER_2026-09-27_NoTranche`).

The pages are the bundles' own (`…/{CoQ,iCoA}/<series>/PDF`), unchanged; nothing is rebuilt. Each
CoQ is paired with the iCoA the register gives it (`icoa_code`) and refused if that PDF is missing, if a page
does not print its own code, or if a CoQ does not cite its iCoA. Order: CoQ number. Each file is made print-safe
(`print_safe_pdf.py`: one opaque background under vector text, no transparency).
"""
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
STAMP = '2026-10-09'
# set: (source bundle, series, output folder, file prefix, title)
SETS = {'t3-retest': ('DELIVER_2026-09-26_T3', ('Retest',), 'DELIVER_2026-10-09_T3_Retest_Merged', 'T3_Retest',
                      'Tranche 3 retest'),
        'nontranche': ('DELIVER_2026-09-27_NoTranche', ('Initial', 'Retest'), 'DELIVER_2026-10-09_NoTranche_Merged',
                       'NoTranche', 'lots outside the tranches, initial and retest')}
KEY = sys.argv[1] if len(sys.argv) > 1 else 't3-retest'
SRC, SERIES, OUT, PREFIX, TITLE = SETS[KEY]
SRC, OUT = os.path.join(GAP, SRC), os.path.join(GAP, OUT)


def one(kind, code):
    got = [os.path.join(SRC, kind, se, 'PDF', f) for se in SERIES for f in os.listdir(os.path.join(SRC, kind, se, 'PDF'))
           if f.startswith(code + '_')]
    if len(got) != 1:
        raise SystemExit('%d %s PDFs for %s' % (len(got), kind, code))
    return got[0]


def main():
    import pymupdf
    spec = importlib.util.spec_from_file_location('S', os.path.join(HERE, 'print_safe_pdf.py'))
    S = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(S)
    reg = {c['regcode'][:13]: c for c in json.load(open(os.path.join(GAP, 'coq_artifact_data.json'), encoding='utf-8'))['coqs']}
    coqs = sorted(re.match(r'CoQ-PP_26-\d{3}', f).group(0) for se in SERIES
                  for f in os.listdir(os.path.join(SRC, 'CoQ', se, 'PDF')) if f.endswith('.pdf'))
    pairs = []
    for code in coqs:
        c = reg[code]
        if c.get('withdrawn') or (SERIES == ('Retest',) and 'retest' not in c['t']):
            raise SystemExit('%s is not a live %s certificate' % (code, TITLE))
        ic = c.get('icoa_code')
        if not any(r.get('doc') == ic for r in c['rows']):
            ic = None                     # nothing credited to it: no iCoA (CNP tested 1, 2, 7, 8)
        cp = one('CoQ', code)
        ip = one('iCoA', ic) if ic else None
        flat = lambda p: ''.join(''.join(pg.get_text() for pg in pymupdf.open(p)).split())
        tc = flat(cp)
        if code not in tc or (ic and ic not in tc):
            raise SystemExit('%s does not print its code or its iCoA %s' % (code, ic))
        if ip and ic not in flat(ip):
            raise SystemExit('%s does not print its own code' % ic)
        pairs.append((code, cp, ic, ip))
    icoas = [p for p in pairs if p[3]]
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith('.pdf'):
            os.remove(os.path.join(OUT, f))

    def save(name, title, items):
        book, toc = pymupdf.open(), []
        for label, path in items:
            with pymupdf.open(path) as d:
                if d.page_count != 1:
                    raise SystemExit('%s is %d pages' % (os.path.basename(path), d.page_count))
                toc.append([1, label, book.page_count + 1])
                book.insert_pdf(d)
        book.set_toc(toc)
        book.set_metadata({'title': 'Purely Plant — %s: %s' % (TITLE, title), 'producer': 'Purely Plant Quality Desk'})
        book.save(os.path.join(OUT, name), garbage=4, deflate=True)
        book.close()
        # print-safe (Head of QC, 09.10.2026: every second page printed blank): no transparency left
        print('%-40s %s' % (name, S.flatten(os.path.join(OUT, name))), flush=True)

    save('%s_CoQ_all_%d_%s.pdf' % (PREFIX, len(pairs), STAMP), 'certificates of quality',
         [(c, cp) for c, cp, _, _ in pairs])
    save('%s_iCoA_all_%d_%s.pdf' % (PREFIX, len(icoas), STAMP), 'internal certificates of analysis',
         [(i, ip) for _, _, i, ip in icoas])
    both = []
    for c, cp, i, ip in pairs:
        both.append((c, cp))
        if ip:
            both.append(('%s (%s)' % (i, c), ip))
    save('%s_CoQ+iCoA_%s.pdf' % (PREFIX, STAMP), 'each CoQ followed by its iCoA', both)
    none = [c for c, _, i, _ in pairs if not i]
    if none:
        print('no iCoA (an outside laboratory tested what it would hold): %s' % ', '.join(none))
    return 0


if __name__ == '__main__':
    sys.exit(main())
