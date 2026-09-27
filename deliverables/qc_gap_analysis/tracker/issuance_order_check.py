#!/usr/bin/env python3
"""Which certificate-of-quality numbers are out of chronological issuance order.

    python3 tracker/issuance_order_check.py            # writes tracker/ISSUANCE_ORDER_CHECK_<date>.tsv
    python3 tracker/issuance_order_check.py --register <path> --stdout

Head of QC, 27.09.2026: every lot is issued, "and it should be issued chronologically, regardless if
it's in a tranche or not". This lists the live numbers (withdrawn ones are free) whose issue date breaks
the order, and where each would sit. It renumbers nothing: the list is with the Head of QC (CLAUDE.md
§7, "Numbering"), and Tranches 1 and 2 are issued and frozen.

* **In order** — the longest run of live numbers whose issue dates never go backwards (ties keep
  their numbering). Every other live number is listed.
* **Where it would sit** — after the last in-order number dated on or before it, before the next.
* An issue written "≥ dd.mm.yyyy" is read at that date.
"""
import argparse, csv, datetime, io, json, os, re, sys
from bisect import bisect_right

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import audit_empty_results as A                                    # noqa: E402

HEAD = ['number', 'tranche', 'p_lot', 'batch', 'type', 'issue', 'issue_before_redating',
        'chronologically_after', 'chronologically_before', 'status']


def day(s):
    m = re.search(r'(\d\d)\.(\d\d)\.(\d{4})', str(s or ''))
    return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else None


def in_order(seq):
    """Indices of the longest non-decreasing subsequence of seq (by value), earliest-ending on ties."""
    tails, tail_i, prev = [], [], [None] * len(seq)
    for i, v in enumerate(seq):
        k = bisect_right(tails, v)
        if k == len(tails):
            tails.append(v)
            tail_i.append(i)
        else:
            tails[k] = v
            tail_i[k] = i
        prev[i] = tail_i[k - 1] if k else None
    out, i = [], tail_i[-1] if tail_i else None
    while i is not None:
        out.append(i)
        i = prev[i]
    return set(out[::-1])


def rows(reg):
    tm = A.tranche_map()

    def tranche(c):
        for k in (c.get('pp'), c.get('cb'), (c.get('cb') or '').replace('＊', '')):
            if k and k in tm:
                return tm[k]

    live = sorted((c for c in reg['coqs'] if not c.get('withdrawn') and day(c.get('issue'))),
                  key=lambda c: c['regcode'])
    dates = [day(c['issue']) for c in live]
    keep = in_order(dates)
    ordered = [(dates[i], live[i]) for i in sorted(keep)]
    out = []
    for i, c in enumerate(live):
        if i in keep:
            continue
        d = dates[i]
        k = bisect_right([x for x, _ in ordered], d)
        num = lambda r: r['regcode'][-4:]                                     # noqa: E731
        after = 'after %s (%s)' % (num(ordered[k - 1][1]), ordered[k - 1][1]['issue']) if k else 'first'
        before = 'before %s (%s)' % (num(ordered[k][1]), ordered[k][1]['issue']) if k < len(ordered) else 'last'
        t = tranche(c)
        pp = str(c.get('pp') or '')
        has_p = bool(re.match(r'^[PJ]\d{5,6}$', pp))
        out.append([c['regcode'][-4:], t[1:] if t else '—', pp if has_p else str(c.get('cb') or ''),
                    str(c.get('cb') or '') if has_p else '', c['t'], c['issue'],
                    str(c.get('issue_before_redating') or ''), after, before,
                    'frozen (T1/T2, issued)' if t in A.FROZEN else 'free to renumber'])
    return len(live), out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--register', default=os.path.join(GAP, 'coq_artifact_data.json'))
    ap.add_argument('--stdout', action='store_true')
    ap.add_argument('--stamp', default=datetime.date.today().isoformat())
    a = ap.parse_args(argv[1:])
    n, out = rows(json.load(open(a.register, encoding='utf-8')))
    buf = io.StringIO()
    w = csv.writer(buf, delimiter='\t', lineterminator='\n')
    w.writerow(HEAD)
    w.writerows(out)
    if a.stdout:
        sys.stdout.write(buf.getvalue())
    else:
        dest = os.path.join(HERE, 'ISSUANCE_ORDER_CHECK_%s.tsv' % a.stamp)
        open(dest, 'w', encoding='utf-8').write(buf.getvalue())
        print('written: %s' % os.path.relpath(dest, GAP))
    print('live numbers: %d, in date order: %d, out of order: %d' % (n, n - len(out), len(out)), file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
