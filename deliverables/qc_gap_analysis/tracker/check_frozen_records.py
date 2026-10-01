#!/usr/bin/env python3
"""Tranches 1 and 2 are issued: no record and no page of theirs changes.

    python3 deliverables/qc_gap_analysis/tracker/check_frozen_records.py            # exit 1 on a change
    python3 deliverables/qc_gap_analysis/tracker/check_frozen_records.py --snapshot # only with his word

Head of QC, 26.09.2026: "Don't touch T1 and T2 — they are already issued and sent to the customer."
The 26.09 apply scripts refuse a Tranche 1 or 2 record (`audit_empty_results.FROZEN`). The review of
27.09.2026 found that 28 older apply scripts — `apply_icoa_citations.py` among them, which the
citation verifier used to name as the repair — write `coq_artifact_data.json` with no such guard. So
the guard is here, where every change has to pass: each Tranche 1 and 2 record of the register (the
18.09 grouping, as the page builder reads it) and each of their certificate-of-quality pages in
`design_handoff/out` is held against `FROZEN_T1_T2_2026-09-26.json`, the state restored on 26.09.2026
(`26368c5`, equal to `f161da1`). Any difference fails.

`--snapshot` rewrites the snapshot. It is for a change the Head of QC has ordered to an issued
certificate, and for nothing else.
"""
import glob, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from check_certificate_claims import frozen_lots                     # noqa: E402

SNAP = os.path.join(HERE, 'FROZEN_T1_T2_2026-09-26.json')


def digest(obj):
    if isinstance(obj, bytes):
        return hashlib.sha256(obj).hexdigest()
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()


def state():
    reg = json.load(open(os.path.join(GAP, 'coq_artifact_data.json'), encoding='utf-8'))['coqs']
    frozen = frozen_lots()
    recs = {c['regcode']: digest(c) for c in reg if frozen(c)}
    pages = {}
    for p in sorted(glob.glob(os.path.join(GAP, 'design_handoff', 'out', '**', 'CoQ-PP_26-*.html'), recursive=True)):
        m = re.search(r'CoQ-PP_26-\d{3}', os.path.basename(p))
        if m and m.group(0) in recs:
            pages[os.path.relpath(p, GAP)] = digest(open(p, 'rb').read())
    return {'records': recs, 'pages': pages}


def main(argv):
    now = state()
    if '--snapshot' in argv:
        json.dump(now, open(SNAP, 'w', encoding='utf-8'), indent=1, sort_keys=True)
        print('snapshot: %d records, %d pages' % (len(now['records']), len(now['pages'])))
        return 0
    was = json.load(open(SNAP, encoding='utf-8'))
    bad = []
    for kind in ('records', 'pages'):
        for k in sorted(set(was[kind]) | set(now[kind])):
            if was[kind].get(k) != now[kind].get(k):
                bad.append('%s %s: %s' % (kind[:-1], k, 'changed' if k in was[kind] and k in now[kind]
                                          else 'added' if k in now[kind] else 'gone'))
    print('Tranches 1 and 2: %d records, %d pages held against the snapshot, %d changed'
          % (len(now['records']), len(now['pages']), len(bad)))
    for b in bad[:40]:
        print('   FROZEN  ' + b)
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
