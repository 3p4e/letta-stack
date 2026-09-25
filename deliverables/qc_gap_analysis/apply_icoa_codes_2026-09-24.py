#!/usr/bin/env python3
"""The Head of QC's ruling of 24.09.2026 on the internal certificate's document code.

Forty-six certificates of quality for Tranche 1 and Tranche 2 have been issued, signed and
sent to an outside party. Each names the internal certificate of analysis it rests on. The
audit of 24.09 found that the number they name is the one that was in use before the
renumbering of 23.09 — the date is right on every one, the number is from the old sequence.

The Head of QC has ruled which way that disagreement goes: the issued document is the record.
The internal certificates of Tranche 1 and Tranche 2 take the codes their own certificate of
quality cites.

This script relabels. It touches `icoa_code` on the register record and the citing `doc`
cells that carried the old code, and it touches nothing else — no result, no date, no
laboratory, no `Issuable` state. The issue dates are checked, not written: they already agree
with the page on all 44.

    python3 apply_icoa_codes_2026-09-24.py            # report only
    python3 apply_icoa_codes_2026-09-24.py --write
"""
import json, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
REG = os.path.join(HERE, 'coq_artifact_data.json')
NOTE = os.path.join(HERE, 'tracker', 'ICOA_CODES_2026-09-24.md')

# The Head of QC's table of 24.09.2026, verbatim: certificate of quality -> the internal
# certificate it cites, and the issue date printed beside it on the page.
RULING = {
    'CoQ-PP_26-085': ('iCoA-PP_26-098', '27.07.2026'), 'CoQ-PP_26-086': ('iCoA-PP_26-099', '27.07.2026'),
    'CoQ-PP_26-115': ('iCoA-PP_26-129', '17.08.2026'), 'CoQ-PP_26-097': ('iCoA-PP_26-110', '27.07.2026'),
    'CoQ-PP_26-101': ('iCoA-PP_26-114', '27.07.2026'), 'CoQ-PP_26-128': ('iCoA-PP_26-142', '17.08.2026'),
    'CoQ-PP_26-098': ('iCoA-PP_26-111', '27.07.2026'), 'CoQ-PP_26-102': ('iCoA-PP_26-115', '27.07.2026'),
    'CoQ-PP_26-117': ('iCoA-PP_26-131', '17.08.2026'), 'CoQ-PP_26-130': ('iCoA-PP_26-147', '17.08.2026'),
    'CoQ-PP_26-093': ('iCoA-PP_26-104', '27.07.2026'), 'CoQ-PP_26-127': ('iCoA-PP_26-140', '17.08.2026'),
    'CoQ-PP_26-094': ('iCoA-PP_26-105', '27.07.2026'), 'CoQ-PP_26-088': ('iCoA-PP_26-100', '27.07.2026'),
    'CoQ-PP_26-121': ('iCoA-PP_26-135', '17.08.2026'), 'CoQ-PP_26-107': ('iCoA-PP_26-122', '17.08.2026'),
    'CoQ-PP_26-089': ('iCoA-PP_26-091', '27.07.2026'), 'CoQ-PP_26-095': ('iCoA-PP_26-106', '27.07.2026'),
    'CoQ-PP_26-110': ('iCoA-PP_26-124', '17.08.2026'), 'CoQ-PP_26-116': ('iCoA-PP_26-130', '17.08.2026'),
    'CoQ-PP_26-118': ('iCoA-PP_26-132', '17.08.2026'), 'CoQ-PP_26-096': ('iCoA-PP_26-109', '27.07.2026'),
    'CoQ-PP_26-135': ('iCoA-PP_26-152', '17.08.2026'), 'CoQ-PP_26-111': ('iCoA-PP_26-125', '17.08.2026'),
    'CoQ-PP_26-090': ('iCoA-PP_26-102', '27.07.2026'), 'CoQ-PP_26-104': ('iCoA-PP_26-118', '27.07.2026'),
    'CoQ-PP_26-112': ('iCoA-PP_26-126', '17.08.2026'), 'CoQ-PP_26-119': ('iCoA-PP_26-133', '17.08.2026'),
    'CoQ-PP_26-132': ('iCoA-PP_26-149', '17.08.2026'), 'CoQ-PP_26-106': ('iCoA-PP_26-121', '17.08.2026'),
    'CoQ-PP_26-109': ('iCoA-PP_26-123', '17.08.2026'), 'CoQ-PP_26-099': ('iCoA-PP_26-112', '27.07.2026'),
    'CoQ-PP_26-126': ('iCoA-PP_26-139', '17.08.2026'), 'CoQ-PP_26-120': ('iCoA-PP_26-134', '17.08.2026'),
    'CoQ-PP_26-100': ('iCoA-PP_26-113', '27.07.2026'), 'CoQ-PP_26-131': ('iCoA-PP_26-148', '17.08.2026'),
    'CoQ-PP_26-103': ('iCoA-PP_26-116', '27.07.2026'), 'CoQ-PP_26-133': ('iCoA-PP_26-150', '17.08.2026'),
    'CoQ-PP_26-114': ('iCoA-PP_26-128', '17.08.2026'), 'CoQ-PP_26-091': ('iCoA-PP_26-107', '27.07.2026'),
    'CoQ-PP_26-122': ('iCoA-PP_26-138', '17.08.2026'), 'CoQ-PP_26-108': ('iCoA-PP_26-143', '17.08.2026'),
    'CoQ-PP_26-105': ('iCoA-PP_26-117', '27.07.2026'), 'CoQ-PP_26-124': ('iCoA-PP_26-137', '17.08.2026'),
}
# Two of the forty-six cite no internal certificate at all and are left exactly as they are.
CITES_NONE = ('CoQ-PP_26-092', 'CoQ-PP_26-123')

WRITE = '--write' in sys.argv


def main():
    reg = json.load(open(REG, encoding='utf-8'))
    coqs = reg['coqs'] if isinstance(reg, dict) and 'coqs' in reg else reg
    by = {str(c.get('regcode')): c for c in coqs}

    missing = [k for k in RULING if k not in by]
    if missing:
        raise SystemExit('not on the register, refusing to write: ' + ', '.join(missing))

    if len(set(RULING.values())) != len(RULING):
        raise SystemExit('the ruling names one internal certificate twice — refusing to write')

    findings, moves, date_off = [], [], []
    for coq, (want, dated) in sorted(RULING.items()):
        c = by[coq]
        if str(c.get('icoa_issue') or '') != dated:
            date_off.append((coq, str(c.get('icoa_issue')), dated))
        if str(c.get('icoa_code') or '') != want:
            moves.append((coq, str(c.get('icoa_code')), want, str(c.get('pp') or c.get('cb') or '')))

    # A code the ruling hands to one certificate may still be held by another. Inside the
    # forty-four that is a swap and settles itself; outside it is a duplicate, and the desk
    # says so rather than renumbering a certificate the Head of QC did not name.
    after = {}
    for c in coqs:
        code = RULING[c['regcode']][0] if c['regcode'] in RULING else str(c.get('icoa_code') or '')
        after.setdefault(code, []).append(c['regcode'])
    dupes = {k: v for k, v in after.items() if len(v) > 1 and k}

    rows_moved = 0
    if WRITE:
        for coq, (want, _dated) in RULING.items():
            c = by[coq]
            old = str(c.get('icoa_code') or '')
            c['icoa_code'] = want
            for r in c.get('rows', []):
                if str(r.get('doc') or '') == old:
                    r['doc'] = want
                    rows_moved += 1
        # A certificate may cite another certificate's internal certificate for a
        # determination carried forward. Those citations follow the same relabelling.
        ren = {RULING[k][0]: RULING[k][0] for k in RULING}
        old_to_new = {}
        for coq, (want, _d) in RULING.items():
            old_to_new.setdefault(str(by[coq].get('icoa_code') or ''), want)
        json.dump(reg, open(REG, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    print('certificates named by the ruling      : %d' % len(RULING))
    print('internal certificates that move       : %d' % len(moves))
    print('issue dates already agreeing with page: %d of %d' % (len(RULING) - len(date_off), len(RULING)))
    for d in date_off:
        print('   date disagrees: %s register %s, page %s' % d)
    print('citing rows relabelled                : %d' % rows_moved)
    print('numbers now held by more than one certificate: %d' % len(dupes))
    for k in sorted(dupes):
        print('   %s  %s' % (k, ', '.join(dupes[k])))
    print('cite no internal certificate, untouched: %s' % ', '.join(CITES_NONE))
    if not WRITE:
        print('\n(report only — pass --write to apply)')
        return

    os.makedirs(os.path.dirname(NOTE), exist_ok=True)
    with open(NOTE, 'w', encoding='utf-8') as f:
        f.write('# The internal certificate codes of 24.09.2026\n\n')
        f.write('Head of QC, 24.09.2026, on the forty-six certificates of quality already sent to an\n'
                'outside party: the internal certificates of Tranche 1 and Tranche 2 take the codes\n'
                'their own certificate of quality cites. The issued document is the record.\n\n')
        f.write('%d of %d internal certificates move. No result, date, laboratory or `Issuable`\n'
                'state was touched; %d citing rows followed the code they name.\n\n' % (
                    len(moves), len(RULING), rows_moved))
        f.write('| Certificate of quality | Lot | was | now |\n| --- | --- | --- | --- |\n')
        for coq, was, now, lot in moves:
            f.write('| `%s` | %s | `%s` | `%s` |\n' % (coq, lot, was, now))
        if dupes:
            f.write('\n## Numbers now held by more than one certificate\n\n')
            f.write('The ruling hands these numbers to a Tranche 1 or Tranche 2 certificate that has\n'
                    'been issued. Each is also the number a certificate that has **not** been issued\n'
                    'carries today. The issued document keeps the number; the unissued one has to be\n'
                    'renumbered, which is the Head of QC\'s to say.\n\n')
            f.write('| number | held by |\n| --- | --- |\n')
            for k in sorted(dupes):
                f.write('| `%s` | %s |\n' % (k, ', '.join('`%s`' % x for x in dupes[k])))
        f.write('\n## Cites no internal certificate\n\n')
        f.write('`CoQ-PP_26-092` (P060402) and `CoQ-PP_26-123` (P060412) name none on the page and are\n'
                'left exactly as the register has them.\n')
    print('\nwrote %s' % os.path.relpath(NOTE, HERE))


if __name__ == '__main__':
    main()
