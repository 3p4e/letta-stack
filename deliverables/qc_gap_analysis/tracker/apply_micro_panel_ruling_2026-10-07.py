#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The microbiology panel prints whole, as the lot's own certificate reports it — Head of QC, 07.10.2026.

    python3 tracker/apply_micro_panel_ruling_2026-10-07.py --check     # writes nothing
    python3 tracker/apply_micro_panel_ruling_2026-10-07.py --apply

His words:

* *"yes print all analysis results that are actually tested, the complete Microbiological Purity
  panel"*
* *"on that CoQ for that batch, you draw the Microbiology panel analysis results from a eCOA and you
  must include all parameters tested and present in the eCOA unless explicitly told"*
* *"you will not use analysis results from one batch to fill in for another batch and strain"*

Determinations 9.6 (*Pseudomonas aeruginosa*) and 9.7 (*Staphylococcus aureus*) printed "upon request —
not required for release" on every certificate of quality, although 32 of them cite a microbiology
certificate that reports both. Those certificates were ordered against the manufacturer's specification
(Ph. Eur. 5.1.8 cat. C *и производителска спецификација* / 2.6.12, 2.6.13, 2.6.31), which adds the two
organisms; the ordinary release certificates were ordered against Ph. Eur. 5.1.8 cat. C alone and report
five tests, and their certificates of quality are not touched.

What the run does, certificate by certificate:

1. The certificate the row 9.1 cites is the panel's certificate. Rows 9.1 to 9.5 must all cite it (one
   sample, one panel), or the record is refused.
2. Its 9.6 and 9.7 come from a committed two-read record: the IJZ-MB campaign of 31.08/01.09.2026
   (`intake_IJZMB_2026-09-16/reads_IJZMB.json`, `intake_IJZMB2_2026-09-17/reads_IJZMB2.json`) or the two
   release certificates of 01.12.2025 (`intake_micro_panel_2026-10-07/reads_release_panel.json`).
3. The certificate's lot must be the certificate of quality's own lot. `548/1079/26` stays out: its typed
   lot and its printed strain disagree (OI-37), and no other lot takes it.
4. The two rows take the absence wording row 9.5 prints from the same certificate, its document, date and
   laboratory, and the status "covered". Nothing else on the certificate changes: same document, same
   date, so neither the issue date nor Section 03 moves.

**Tranches 1 and 2 are not touched** (Head of QC, 26.09.2026); the script refuses them. A withdrawn number
is skipped. The renderer prints rows 9.6 and 9.7 only on a certificate that carries a result for them
(`design_handoff/toolchain/coq_apply.js`), so every other page is unchanged.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import audit_empty_results as A                                    # noqa: E402

REG = os.path.join(GAP, 'coq_artifact_data.json')
READS = [os.path.join(GAP, 'intake_IJZMB_2026-09-16', 'reads_IJZMB.json'),
         os.path.join(GAP, 'intake_IJZMB2_2026-09-17', 'reads_IJZMB2.json'),
         os.path.join(GAP, 'intake_micro_panel_2026-10-07', 'reads_release_panel.json')]
HELD = {'548/1079/26': 'OI-37 — typed lot PO50192 (BSS052501) against printed strain "Sleepy Joe"'}
PANEL = ('9.1', '9.2', '9.3', '9.4', '9.5')
NEW = ('9.6', '9.7')
# Every spelling the laboratory uses for "absent" or "complies with absent/g" on these pages.
ABSENT = re.compile(r'^\s*(отсут\S*|отсуст\S*|одговара)', re.I)


def panel_reads():
    """cert code -> (lot, {9.6, 9.7}, every read's 9.6/9.7) from every committed two-read record.

    The campaign intake's own agreement flag also covers wording on the page's header (accreditation,
    department, conclusion), so it is not the test here: each read of 9.6 and 9.7 must state an absence.
    """
    out = {}
    for path in READS:
        for code, x in json.load(open(path, encoding='utf-8')).items():
            res = x.get('results') or {}
            if all(res.get(n) for n in NEW):
                reads = [x[k] for k in ('read_A', 'read_B', 'read_C') if isinstance(x.get(k), dict)]
                # a third read taken to settle another value (read_C) need not cover these two rows
                out[code] = (x.get('batch_canonical') or '', {n: res[n] for n in NEW},
                             [str(r.get(n)) for r in reads for n in NEW if r.get(n)])
    return out


def run(reg, apply):
    tm = A.tranche_map()

    def tranche(c):
        for k in (c.get('pp'), c.get('cb'), (c.get('cb') or '').replace('＊', '')):
            if k and k in tm:
                return tm[k]

    reads = panel_reads()
    done, refused, skipped = [], [], []
    for c in reg['coqs']:
        rows = {r['no']: r for r in c['rows']}
        code = str((rows.get('9.1') or {}).get('doc') or '').strip()
        if code not in reads and code not in HELD:
            continue
        t = tranche(c)
        if t in A.FROZEN:
            skipped.append((c.get('regcode'), c.get('pp') or c.get('cb'), code, 'Tranche %s — not touched' % t[-1]))
            continue
        if c.get('withdrawn'):
            skipped.append((c.get('regcode'), c.get('pp') or c.get('cb'), code, 'withdrawn'))
            continue
        if code in HELD:
            skipped.append((c.get('regcode'), c.get('pp') or c.get('cb'), code, HELD[code]))
            continue
        lot, vals, every = reads[code]
        own = {A.N(c.get('pp')), A.N(c.get('cb')), A.N((c.get('cb') or '').replace('＊', ''))} - {''}
        why = None
        if A.N(lot) not in own:
            why = 'certificate lot %s is not this lot %s' % (lot, sorted(own))
        elif len(every) < 4 or not all(ABSENT.match(v) for v in every):
            why = 'not two reads stating an absence for both: %s' % every
        elif any(str((rows.get(n) or {}).get('doc') or '').strip() != code for n in PANEL):
            why = 'rows 9.1–9.5 do not all cite %s' % code
        elif not all(ABSENT.match(vals[n]) for n in NEW):
            why = 'a value is not an absence: %s' % vals
        elif not all(n in rows for n in NEW):
            why = 'no rows 9.6/9.7 in the record'
        if why:
            refused.append((c.get('regcode'), c.get('pp') or c.get('cb'), code, why))
            continue
        src = rows['9.5']
        word = src.get('res') or ''
        if not re.match(r'^\s*absent', word, re.I):
            refused.append((c.get('regcode'), c.get('pp') or c.get('cb'), code, 'row 9.5 does not print an absence: %r' % word))
            continue
        before = [(rows[n].get('res'), rows[n].get('doc'), rows[n].get('st')) for n in NEW]
        if apply:
            for n in NEW:
                r = rows[n]
                r['res'], r['doc'], r['dd'], r['lab'] = word, code, src.get('dd') or '', src.get('lab') or ''
                r['fam'] = src.get('fam') or ''
                r['st'], r['route'], r['also'] = 'covered', '', ''
        done.append((c.get('regcode'), c.get('t', '')[:7], c.get('pp') or c.get('cb'), code, src.get('dd'), word,
                     ' / '.join(vals[n] for n in NEW), before[0][2]))
    return done, refused, skipped


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--reg', default=REG)
    a = ap.parse_args(argv[1:])
    if not (a.apply or a.check):
        ap.error('pass --check or --apply')
    reg = json.load(open(a.reg, encoding='utf-8'))
    done, refused, skipped = run(reg, a.apply)
    for x in done:
        print('PANEL     %-15s %-7s %-12s %-13s %s  %s  (certificate: %s; was: %s)' % x)
    for x in skipped:
        print('SKIPPED   %-15s %-12s %-13s %s' % x)
    for x in refused:
        print('REFUSED   %-15s %-12s %-13s %s' % x)
    print('%d certificates of quality take 9.6 and 9.7; %d skipped; %d refused' % (len(done), len(skipped), len(refused)))
    if refused:
        return 1
    if a.apply:
        with open(a.reg, 'w', encoding='utf-8') as fh:
            json.dump(reg, fh, ensure_ascii=False, indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
