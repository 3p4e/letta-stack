#!/usr/bin/env python3
"""Recover certificate issue dates from the controlled filename.

Extraction missed the date of issue on 17 certificates, and a missing date is a
blocker on signing: Section 03 must cite each certificate by code AND date. But
the dates are not lost. The corpus filename is a controlled string,

    <batch>_<certificate code>, <dd.mm.yyyy>_<laboratory>.pdf

and the date it carries agrees with the extracted date on ALL 219 certificates
where extraction captured one. That is not a model reading a page; it is a field
a person typed when filing the document, and it has a perfect record.

So the date is taken from the filename rather than re-read at cost. The gate
below refuses to write anything if that agreement is ever less than perfect - if
a future document breaks the convention, this script stops rather than filling
a date from a string it no longer trusts.

The CODE is NOT taken from the filename. There the same string is demonstrably a
human rendering, not a transcription: it writes "051-1-LoD-26" where the
certificate prints "051-1-ГС/26", appends " MK" / " EN" to distinguish language
variants of one DFL certificate, and names an NGP form number instead of a
certificate number. A code is cited verbatim on the CoQ, so it is re-read from
the page instead.
"""
import os, re, sys, sqlite3, datetime, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = re.compile(r'^(?P<rest>.+?),\s*(?P<date>\d{2}\.\d{2}\.\d{4})_(?P<lab>[^.]+)\.pdf$',
                  re.IGNORECASE)


def filename_date(document):
    """ISO issue date the filename states, or None if it does not follow the form."""
    m = NAME.match(document or '')
    if not m:
        return None
    try:
        return datetime.datetime.strptime(m['date'], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return None


def audit(db):
    """(agree, disagree, examples) of filename date against extracted date."""
    agree, dis, ex = 0, 0, []
    for doc, name, date in db.execute(
            "SELECT doc_id, document, date_iso FROM certificate "
            "WHERE date_iso IS NOT NULL"):
        fd = filename_date(name)
        if fd is None:
            continue
        if fd == date:
            agree += 1
        else:
            dis += 1
            ex.append((name, date, fd))
    return agree, dis, ex


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=os.path.join(HERE, 'ecoa.sqlite'))
    ap.add_argument('--apply', action='store_true',
                    help='write the recovered dates; without it, only report')
    a = ap.parse_args()
    db = sqlite3.connect(a.db)

    agree, dis, ex = audit(db)
    print('Filename date vs extracted date: %d agree, %d disagree' % (agree, dis))
    for name, was, now in ex[:10]:
        print('   %-52s extracted %s  filename %s' % (name[:52], was, now))
    if dis:
        print('\nREFUSING TO WRITE. The filename convention no longer agrees with')
        print('the page on every certificate, so it cannot be trusted to supply a')
        print('date on the ones where the page was not read. Resolve the')
        print('disagreements above first.')
        return 1

    targets = [(d, n) for d, n in db.execute(
        "SELECT doc_id, document FROM certificate WHERE date_iso IS NULL")]
    fill = [(d, n, filename_date(n)) for d, n in targets]
    ok = [f for f in fill if f[2]]
    no = [f for f in fill if not f[2]]

    print('\n%d certificate(s) carry no extracted date.' % len(targets))
    print('%d recoverable from the filename, %d not:' % (len(ok), len(no)))
    for d, n, v in ok:
        print('   %-52s -> %s' % (n[:52], v))
    for d, n, _ in no:
        print('   %-52s -> filename does not follow the convention' % n[:52])

    if not a.apply:
        print('\nDry run. Re-run with --apply to write these dates.')
        return 0

    for d, n, v in ok:
        db.execute("UPDATE certificate SET date_iso=? WHERE doc_id=?", (v, d))
        db.execute("UPDATE result SET date_iso=? WHERE doc_id=? AND date_iso IS NULL",
                   (v, d))
    db.commit()
    print('\nWrote %d certificate date(s) and the result rows beneath them.' % len(ok))
    print('Provenance: the controlled filename, not the certificate page.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
