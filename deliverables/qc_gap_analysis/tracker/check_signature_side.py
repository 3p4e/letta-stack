#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The signature block on every certificate not yet issued: the QC Manager on the right, the CoQ's formatting.

    python3 tracker/check_signature_side.py

Head of QC, 07.10.2026: *"edit the signature block and make the content there be the same formatting, size, font
choices, colours … on all documents, iCoA, CoQ and product specification, as it is on the certificates of quality.
With one additional and mandatory rule: that the QC Manager of all these three documents be on the right side of
the page, and on the left side the other person who signs — the QC Analyst on the internal certificates of
analysis, the QA Manager, as reviewed by, on the certificates of quality, and the same on the product
specifications."*

* **CoQ** (`design_handoff/out`, every certificate outside Tranches 1 and 2): left *Reviewed by · QA Manager*,
  right *Prepared & Approved by · QC Manager*. The issued Tranche 1/2 pages keep the order they were sent in.
* **iCoA** (the Tranche 3 and out-of-tranche bundles): left *Analysis Performed by · QC Analyst*, right
  *Created & Approved by · QC Manager*.
* **Specification** (`specs/QCSP_001_ImB/SHEETS`): left QA Manager, right QC Manager.

The iCoA and the specification must also carry the house kit as committed (`house_kit_2026-10-07.css`), which sets
their signature block, pills, heading bars and text as the CoQ sets them, and no signature image. Exit 1 on any
difference.
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import audit_empty_results as A                                    # noqa: E402
import house_kit as K                                               # noqa: E402

BOX = re.compile(r'<div class="ap-role">([^<]*)<span class="mk">[^<]*</span></div><div class="ap-sign">'
                 r'<div class="ap-line"></div></div><div class="ap-title">([^<]*)<span')
WANT = {'CoQ': [('Reviewed by', 'QA Manager'), ('Prepared &amp; Approved by', 'QC Manager')],
        'iCoA': [('Analysis Performed by', 'QC Analyst'), ('Created &amp; Approved by', 'QC Manager')],
        'spec': [('Reviewed by', 'QA Manager'), ('Prepared &amp; Approved by', 'QC Manager')]}


def boxes(page):
    body = re.sub(r'<style[\s\S]*?</style>', '', page)
    i = body.find('<div class="approval-grid')
    return [(r.strip(), t.strip()) for r, t in BOX.findall(body[i:])] if i >= 0 else []


def main():
    reg = json.load(open(os.path.join(GAP, 'coq_artifact_data.json'), encoding='utf-8'))
    tm = A.tranche_map()

    def tranche(c):
        for k in (c.get('pp'), c.get('cb'), (c.get('cb') or '').replace('＊', '')):
            if k and k in tm:
                return tm[k]

    kit = K.kit_style()
    pages = {os.path.basename(p)[:13]: p
             for p in glob.glob(os.path.join(GAP, 'design_handoff', 'out', '**', 'CoQ-PP_26-*.html'), recursive=True)}
    docs = []
    for c in reg['coqs']:
        if not c.get('withdrawn') and tranche(c) not in A.FROZEN and c['regcode'][:13] in pages:
            docs.append(('CoQ', pages[c['regcode'][:13]]))
    for d in ('DELIVER_2026-09-26_T3', 'DELIVER_2026-09-27_NoTranche'):
        docs += [('iCoA', p) for p in sorted(glob.glob(os.path.join(GAP, d, 'iCoA', '*', 'HTML', 'iCoA-PP_*.html')))]
    docs += [('spec', p) for p in sorted(glob.glob(os.path.join(GAP, 'specs', 'QCSP_001_ImB', 'SHEETS', '*.html')))]

    bad, n = [], {}
    for kind, p in docs:
        page = open(p, encoding='utf-8').read()
        name = os.path.basename(p)
        n[kind] = n.get(kind, 0) + 1
        got = boxes(page)
        if got != WANT[kind]:
            bad.append('%s: signature boxes left to right %s, want %s' % (name, got, WANT[kind]))
        if kind != 'CoQ':
            if kit not in page:
                bad.append('%s: the house kit is missing or not the committed one' % name)
            if 'ap-img' in re.sub(r'<style[\s\S]*?</style>', '', page):
                bad.append('%s: a signature image is on the page' % name)
    for b in bad:
        print(b)
    print('signature blocks: %s — QC Manager on the right%s on all but %d' % (
        ', '.join('%d %s' % (v, k) for k, v in sorted(n.items())), ', the house kit on every iCoA and sheet', len(bad)))
    return 1 if bad or not n.get('iCoA') or not n.get('spec') else 0


if __name__ == '__main__':
    sys.exit(main())
