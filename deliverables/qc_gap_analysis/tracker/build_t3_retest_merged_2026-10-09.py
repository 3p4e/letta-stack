#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tranche 3 retest certificates, merged: the CoQs, the iCoAs, and each CoQ followed by its iCoA — three PDFs.

    python3 tracker/build_t3_retest_merged_2026-10-09.py

Head of QC, 09.10.2026: *"Give me only the T3 retest iCOA and COQ as pdf merged. One file pdf with all t3 retest coqs,
one pdf with t3 retest iCOA and one pdf with COQ and icoa one after another."*

The pages are the bundle's own (`DELIVER_2026-09-26_T3/{CoQ,iCoA}/Retest/PDF`), unchanged; nothing is rebuilt. Each
retest CoQ is paired with the iCoA the register gives it (`icoa_code`) and refused if that PDF is missing, if a page
does not print its own code, or if a CoQ does not cite its iCoA. Order: CoQ number.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
SRC = os.path.join(GAP, 'DELIVER_2026-09-26_T3')
OUT = os.path.join(GAP, 'DELIVER_2026-10-09_T3_Retest_Merged')
STAMP = '2026-10-09'


def one(kind, code):
    d = os.path.join(SRC, kind, 'Retest', 'PDF')
    got = [f for f in os.listdir(d) if f.startswith(code + '_')]
    if len(got) != 1:
        raise SystemExit('%d %s retest PDFs for %s' % (len(got), kind, code))
    return os.path.join(d, got[0])


def main():
    import pymupdf
    reg = {c['regcode'][:13]: c for c in json.load(open(os.path.join(GAP, 'coq_artifact_data.json'), encoding='utf-8'))['coqs']}
    coqs = sorted(re.match(r'CoQ-PP_26-\d{3}', f).group(0) for f in os.listdir(os.path.join(SRC, 'CoQ', 'Retest', 'PDF'))
                  if f.endswith('.pdf'))
    pairs = []
    for code in coqs:
        c = reg[code]
        if 'retest' not in c['t'] or c.get('withdrawn'):
            raise SystemExit('%s is not a live retest' % code)
        ic = c.get('icoa_code')
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
        book.set_metadata({'title': 'Purely Plant — Tranche 3 retest: %s' % title, 'producer': 'Purely Plant Quality Desk'})
        book.save(os.path.join(OUT, name), garbage=4, deflate=True)
        print('%-52s %3d pages' % (name, book.page_count))
        book.close()

    save('T3_Retest_CoQ_all_%d_%s.pdf' % (len(pairs), STAMP), 'certificates of quality',
         [(c, cp) for c, cp, _, _ in pairs])
    save('T3_Retest_iCoA_all_%d_%s.pdf' % (len(icoas), STAMP), 'internal certificates of analysis',
         [(i, ip) for _, _, i, ip in icoas])
    both = []
    for c, cp, i, ip in pairs:
        both.append((c, cp))
        if ip:
            both.append(('%s (%s)' % (i, c), ip))
    save('T3_Retest_CoQ+iCoA_%s.pdf' % STAMP, 'each CoQ followed by its iCoA', both)
    none = [c for c, _, i, _ in pairs if not i]
    if none:
        print('no iCoA (an outside laboratory tested what it would hold): %s' % ', '.join(none))
    return 0


if __name__ == '__main__':
    sys.exit(main())
