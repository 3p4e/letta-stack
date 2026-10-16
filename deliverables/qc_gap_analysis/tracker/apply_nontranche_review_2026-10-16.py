#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lots outside the tranches, held against their own certificates: CNP's identification, the IPH page that is missing,
and the foreign-matter result CNP fails.

    python3 tracker/apply_nontranche_review_2026-10-16.py --check
    python3 tracker/apply_nontranche_review_2026-10-16.py --apply

Head of QC, 16.10.2026: *"check the out of tranche coq retest if not release and coa with possible corrections"*,
then *"check the actual documents and not intend or presume"*. The current certificate of each of the 12 lots — the
retest, or the release CoQ where there is none — was held against the pages on file (Drive scans, the RAGflow page
text, the two-read records in master v57). Three standing rulings had not been carried to these lots:

1. **Ruling 6 of 26.09.2026** — identification A, B and foreign matter cite the CNP certificate where it tests them
   explicitly, and then there is no internal certificate (as `-075`, `-079`, `-080`). ППК26127 (FB032601), ППК26128
   (GG032601), ППК26115 (JD022601), ППК26117/26118/26119 (P160012/22/32) each print *Идентификација — Макроскопија,
   Микроскопија* and *Страни материи* with their result; master v57's iCoA Register already writes their scope as
   "A/B/FM: ППК…". Rows 1, 2, 7 of -082, -083, -168, -169, -170 and rows 1, 2 of -081 take the CNP certificate; their
   iCoAs are not issued.
2. **Ruling 8 / 28.09.2026** — a certificate whose scan is incomplete prints `[pending]` for what the missing page
   holds, and no full-panel result is read around it. IPH 3925/2026 (GG032601) is pages 1, 2 and 4 of 4 in the
   company's archive (OI-59, byte for byte the eCoA_DATABASE file); page 3 carries the heavy metals and the last three
   pesticide residues. -082 printed "all 26 residues" from page 2 and n/t for the metals: both now `[pending]`.
3. **ППК26127 fails foreign matter** (OI-16): 0.08 %, *"НЕ ОДГОВАРА … поради утврдено присуство на семе од
   канабис"*. -081 printed "Conforms" for row 7 from its in-house iCoA, under a status that already said the
   laboratory had declared it out of specification. A failing external result is not overridden by an in-house one:
   row 7 cites ППК26127 and prints `[pending]` until the Head of QC rules on the lot.

Unchanged and left open: 434/0848/26 (OI-64, Gorilla Glue under Серија FB032601) — -082's microbiology stays n/t.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
REG = os.path.join(GAP, 'coq_artifact_data.json')
STAMP = '16.10.2026'
CNP = {'CoQ-PP_26-081': ('ППК26127', ('1', '2')), 'CoQ-PP_26-082': ('ППК26128', ('1', '2', '7')),
       'CoQ-PP_26-083': ('ППК26115', ('1', '2', '7')), 'CoQ-PP_26-168': ('ППК26117', ('1', '2', '7')),
       'CoQ-PP_26-169': ('ППК26118', ('1', '2', '7')), 'CoQ-PP_26-170': ('ППК26119', ('1', '2', '7'))}
OOS = ("awaiting the Head of QC's ruling on the lot — ППК26127 reports foreign matter 0.08 %% as NOT conforming "
       "(cannabis seeds present), OI-16 (%s)" % STAMP)
PAGE3 = ("awaiting the complete scan of IPH 3925/2026 — the archive holds pages 1, 2 and 4 of 4; page 3 (heavy metals, "
         "the last three pesticide residues) is missing, OI-59 (%s)" % STAMP)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv[1:])
    if not (a.apply or a.check):
        ap.error('pass --check or --apply')
    raw = open(REG, encoding='utf-8').read()
    reg = json.loads(raw)
    by = {c['regcode'][:13]: c for c in reg['coqs']}
    n = 0
    for code, (cnp, nos) in CNP.items():
        c = by[code]
        if 'initial' not in c['t'] or any('retest' in x['t'] and (x.get('supersedes') or {}).get('code') == code
                                          for x in reg['coqs'] if not x.get('withdrawn')):
            raise SystemExit('%s is not a release CoQ without a retest' % code)
        rows = {r['no']: r for r in c['rows']}
        src = rows['8']
        if src.get('doc') != cnp:
            raise SystemExit('%s row 8 does not cite %s' % (code, cnp))
        for no in nos:
            r = rows[no]
            if r.get('doc') == cnp:
                continue
            if not str(r.get('doc') or '').startswith('iCoA-PP_26-'):
                raise SystemExit('%s row %s cites %s, not its iCoA' % (code, no, r.get('doc')))
            print('%s row %s: %s → %s (%s)' % (code, no, r['doc'], cnp, src['dd']))
            r.update({'res': 'Conforms | Одговара', 'doc': cnp, 'dd': src['dd'], 'lab': src['lab'], 'fam': src.get('fam', ''),
                      'route': '', 'st': 'covered — tested explicitly by CNP, %s (ruling 6 of 26.09.2026; %s)' % (cnp, STAMP)})
            n += 1
    r7 = {r['no']: r for r in by['CoQ-PP_26-081']['rows']}['7']
    if r7.get('st') != OOS:
        print('CoQ-PP_26-081 row 7: %r from %s → [pending] (ППК26127 fails it)' % (r7.get('res'), r7.get('doc')))
        src = {r['no']: r for r in by['CoQ-PP_26-081']['rows']}['8']
        r7.update({'res': '—', 'doc': 'ППК26127', 'dd': src['dd'], 'lab': src['lab'], 'fam': src.get('fam', ''), 'route': '',
                   'st': OOS, 'also': '0.08 % — Не одговара (cannabis seeds present), ППК26127; in-house iCoA-PP_26-081: Conforms'})
        n += 1
    rows = {r['no']: r for r in by['CoQ-PP_26-082']['rows']}
    for no in ('11.1', '11.2', '11.3', '11.4', '12'):
        r = rows[no]
        if r.get('st') == PAGE3:
            continue
        print('CoQ-PP_26-082 row %s: %r (%s) → [pending], page 3 of 3925/2026 missing' % (no, r.get('res'), r.get('doc')))
        r.update({'res': '—', 'doc': '3925/2026' if no == '12' else '—', 'st': PAGE3})
        if no != '12':
            r.update({'dd': '', 'lab': ''})
        n += 1
    if not a.apply:
        print('--check: nothing written (%d rows)' % n)
        return 0
    indent = 1 if raw.startswith('{\n ') and not raw.startswith('{\n  ') else 2
    open(REG, 'w', encoding='utf-8').write(json.dumps(reg, ensure_ascii=False, indent=indent) + ('\n' if raw.endswith('\n') else ''))
    print('wrote the register: %d rows' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
