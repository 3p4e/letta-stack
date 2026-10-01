#!/usr/bin/env python3
"""A "carried from the initial" row really is the initial's, and no value papers over a pending.

    python3 tracker/check_carry_provenance.py        # exit 1 on any finding

Head of QC, 28.09.2026, on the retest of SJ102501: a result must not be printed around a missing page.
The retest CoQ is built by carrying every parameter from the initial and then overwriting the ones the
retest re-ran. Two failures follow if the overwrite is partial:

  * a row keeps the status "carried from the initial testing (X)" while its value or document no longer
    matches X's row — the value was re-measured (a Farmahem retest panel) but the provenance string is
    stale, and the References sheet then tags a retest result "(initial)";
  * a row prints a value although X's same row is empty or pending — the retest states a result the
    initial itself does not hold, papering over a pending (ruling 4 of 26.09.2026). This had let
    CoQ-PP_26-162 print pesticides "ND — all 26 residues" while its initial CoQ-PP_26-052, and page 3
    of IPH 1065/2026, held them pending.

For every delivered retest certificate of quality this checks each row whose status begins "carried
from the initial testing (X)": X is a real record, and its same-numbered row carries the identical
result and document. Any mismatch is a finding.
"""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
CARRIED = re.compile(r'^carried from the initial testing \((CoQ-PP_26-\d{3})\)')
EMPTY = ('', '—', 'None', None)


def main():
    reg = {c['regcode']: c for c in json.load(open(os.path.join(GAP, 'coq_artifact_data.json'), encoding='utf-8'))['coqs']}
    delivered = {re.search(r'CoQ-PP_26-\d{3}', os.path.basename(p)).group(0)
                 for p in glob.glob(os.path.join(GAP, 'DELIVER_2026-09-2*', 'CoQ', '*', 'HTML', 'CoQ-PP_26-*.html'))}
    bad = []
    for code in sorted(delivered):
        c = reg.get(code)
        if not c:
            continue
        for r in c['rows']:
            m = CARRIED.match(str(r.get('st') or ''))
            if not m:
                continue
            init = reg.get(m.group(1))
            if init is None:
                bad.append((code, r['no'], 'names %s, which is not a record' % m.group(1)))
                continue
            src = next((x for x in init['rows'] if x['no'] == r['no']), None)
            if src is None:
                bad.append((code, r['no'], 'the initial %s has no such row' % m.group(1)))
                continue
            if str(src.get('res') or '').strip() in EMPTY and str(r.get('res') or '').strip() not in EMPTY:
                bad.append((code, r['no'], 'prints %r while the initial %s holds it empty/pending'
                            % (r.get('res'), m.group(1))))
            elif (str(r.get('res') or '').strip(), str(r.get('doc') or '').strip()) != \
                    (str(src.get('res') or '').strip(), str(src.get('doc') or '').strip()):
                bad.append((code, r['no'], 'says "carried" but result/doc differ from the initial %s '
                            '(%r/%s vs %r/%s)' % (m.group(1), r.get('res'), r.get('doc'), src.get('res'), src.get('doc'))))
    print('carry-provenance: %d delivered CoQ read, %d finding(s)' % (len(delivered & set(reg)), len(bad)))
    for x in bad:
        print('   %s row %s: %s' % x)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
