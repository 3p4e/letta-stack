#!/usr/bin/env python3
"""Hold the signed Tranche 3 certificates to what was signed.

    python3 tracker/check_signed_t3.py               # exit 1 on any change to what a signed page prints
    python3 tracker/check_signed_t3.py --snapshot    # only on the Head of QC's word, after a new signing

Head of QC, 22.10.2026: *"You should not rebuild any document. The last and approved versions if you are building
them should be exactly the same with exactly the same content parameters cited — information copies of the
certificates of quality and their accompanying documents for tranche one two and three."*

Tranches 1 and 2 are held by `check_frozen_records.py`. Tranche 3's approved versions are the 24 retest CoQs signed
and scanned on 16.10.2026 (Drive `T3 SCANN BUNDLE`, `_T3_SCAN_BUNDLE_MANIFEST.xlsx`), and the signed iCoAs of
`20260924183229.pdf`, `20260924183321.pdf` and `20261009180750.pdf`. On 22.10.2026 a re-dating of the unsigned initial
-073 moved the supersedes line of the signed -160 (18.09.2026 -> 12.06.2026) and was reversed; this check is what
stops that happening again. It holds every field a signed page prints — header, potency, specification, product
code, supersedes line, iCoA, and each row's result, document and date — against `SIGNED_T3_2026-10-16.json`, taken
from the register as it stands for those certificates (verified against the scans of -149 and -160 on 22.10.2026).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
SNAP = os.path.join(HERE, 'SIGNED_T3_2026-10-16.json')
# T3 SCANN BUNDLE manifest of 19.10.2026: the 24 signed retest CoQs
SIGNED_COQ = ('136', '137', '139', '140', '141', '142', '143', '144', '146', '147', '149', '152', '153', '154', '155',
              '156', '157', '158', '159', '160', '162', '163', '164', '165')
HEAD = ('pp', 'cb', 'strain', 'issue', 'supersedes', 'grade', 'thc', 'spec', 'pcode', 'md', 'pk', 'icoa_code', 'icoa_issue',
        'icoa_tested')


def printed(c):
    return {'head': {k: c.get(k) for k in HEAD},
            'rows': [[r.get('no'), r.get('res'), r.get('doc'), r.get('dd')] for r in c['rows']]}


def state():
    reg = {c['regcode'][:13]: c for c in json.load(open(os.path.join(GAP, 'coq_artifact_data.json'), encoding='utf-8'))['coqs']}
    return {'CoQ-PP_26-' + n: printed(reg['CoQ-PP_26-' + n]) for n in SIGNED_COQ}


def main(argv):
    now = state()
    if '--snapshot' in argv:
        json.dump(now, open(SNAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
        print('snapshot: %d signed Tranche 3 CoQs' % len(now))
        return 0
    was = json.load(open(SNAP, encoding='utf-8'))
    bad = []
    for code in sorted(set(was) | set(now)):
        a, b = was.get(code), now.get(code)
        if a == b:
            continue
        if not a or not b:
            bad.append('%s %s' % (code, 'added' if b else 'gone'))
            continue
        for k in HEAD:
            if a['head'].get(k) != b['head'].get(k):
                bad.append('%s %s: %r -> %r' % (code, k, a['head'].get(k), b['head'].get(k)))
        ra, rb = {r[0]: r for r in a['rows']}, {r[0]: r for r in b['rows']}
        for no in sorted(set(ra) | set(rb)):
            if ra.get(no) != rb.get(no):
                bad.append('%s row %s: %s -> %s' % (code, no, ra.get(no), rb.get(no)))
    print('Tranche 3, signed 16.10.2026: %d CoQs held against the signed state, %d differences' % (len(now), len(bad)))
    for x in bad[:40]:
        print('   SIGNED  ' + x)
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
