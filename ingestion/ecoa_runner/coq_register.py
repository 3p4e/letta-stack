#!/usr/bin/env python3
"""The CoQ register: every Certificate of Quality that must be issued, from the
first batch released to the reissues that retesting now compels.

A batch is tested in CAMPAIGNS. The certificates of one campaign fall within
days of each other; a retest arrives months later. Clustering the batch's
certificate dates on a gap threshold therefore recovers the issue history:

    campaign 1  ->  QCCoQ NNN v.01   the release certificate
    campaign 2  ->  QCCoQ NNN v.02   reissue carrying the retested value
    campaign 3  ->  QCCoQ NNN v.03   ... and so on

Numbering is CHRONOLOGICAL by release date - QCCoQ 001 is the first batch this
company released - so the register reads as the company's issue history and a
new batch simply takes the next number. The number belongs to the BATCH for
life; a reissue advances the version, never the number (QCSOP 012 v.03 §04).

Nothing here decides conformity. A version is ISSUABLE only when every
specification row it needs is confirmed; otherwise the register states exactly
what is missing, so the gap is worked rather than papered over.
"""
import os, sys, json, sqlite3, argparse, datetime, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
CQ = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location('cq', HERE + '/build_coq.py'))
importlib.util.spec_from_file_location('cq', HERE + '/build_coq.py').loader.exec_module(CQ)

# A campaign is a run of certificates close in time. 90 days is comfortably
# wider than any single testing campaign observed in the corpus (the widest is
# 16 days) and far narrower than the shortest retest interval (5 months).
CAMPAIGN_GAP_DAYS = 90
PREFIX = 'QCCoQ'


def _d(s):
    return datetime.date.fromisoformat(s) if s else None


def campaigns(dates):
    """Group sorted ISO dates into campaigns separated by more than the gap."""
    out = []
    for d in sorted(x for x in dates if x):
        if out and (_d(d) - _d(out[-1][-1])).days <= CAMPAIGN_GAP_DAYS:
            out[-1].append(d)
        else:
            out.append([d])
    return out


def register(db):
    batches = [r[0] for r in db.execute(
        "SELECT DISTINCT batch FROM certificate WHERE batch IS NOT NULL")]
    rows = []
    for b in batches:
        certs = db.execute(
            "SELECT cert_code, date_iso, lab FROM certificate WHERE batch=? AND date_iso IS NOT NULL",
            (b,)).fetchall()
        undated = db.execute(
            "SELECT COUNT(*) FROM certificate WHERE batch=? AND date_iso IS NULL", (b,)).fetchone()[0]
        strain = (db.execute(
            "SELECT strain FROM certificate WHERE batch=? AND strain IS NOT NULL LIMIT 1",
            (b,)).fetchone() or [None])[0]
        camps = campaigns([c[1] for c in certs])
        if not camps:
            rows.append({'batch': b, 'strain': strain, 'version': 1, 'date': None,
                         'certs': [], 'undated': undated, 'kind': 'release',
                         'no_dates': True})
            continue
        for i, camp in enumerate(camps):
            in_camp = [c for c in certs if c[1] in camp]
            rows.append({'batch': b, 'strain': strain, 'version': i + 1,
                         'date': camp[-1], 'first': camp[0],
                         'certs': sorted({(c[0] or '—', c[1]) for c in in_camp}),
                         'undated': undated if i == 0 else 0,
                         'kind': 'release' if i == 0 else 'reissue'})
    # Number by the batch's RELEASE date; every version of a batch shares it.
    releases = sorted({(r['date'] or '9999-12-31', r['batch'])
                       for r in rows if r['version'] == 1})
    number = {b: i + 1 for i, (_, b) in enumerate(releases)}
    for r in rows:
        r['no'] = number[r['batch']]
        r['code'] = '%s %03d v.%02d' % (PREFIX, r['no'], r['version'])
    rows.sort(key=lambda r: (r['no'], r['version']))
    return rows


def readiness(db, batch, as_of=None):
    s02, sources, unresolved = CQ.compile_coq(db, batch, as_of=as_of)
    miss = [e['no'] for e in unresolved if e['status'] == 'MISSING']
    held = [e['no'] for e in unresolved if e['status'] == 'HELD']
    nt = [e['no'] for e in unresolved if e['status'] == 'NOT TESTED']
    ok = sum(1 for e in s02 if e['status'] == 'ok')
    return ok, len(s02), miss, held, nt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=HERE + '/ecoa.sqlite')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    db = sqlite3.connect(a.db)
    rows = register(db)
    for r in rows:
        # Each version is compiled at ITS OWN date, so v.01 states the release
        # result and v.02 the retest - not both showing the newest value.
        ok, tot, miss, held, nt = readiness(db, r['batch'], as_of=r['date'])
        r['sourced'] = '%d/%d' % (ok, tot)
        r['missing'] = miss; r['held'] = held; r['not_tested'] = nt
        r['status'] = 'ISSUABLE' if not miss and not held else (
            'BLOCKED-REVIEW' if held and not miss else 'BLOCKED-MISSING')

    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1)); return

    W = 118
    print('=' * W)
    print('CERTIFICATE OF QUALITY REGISTER — every CoQ to be issued, in order of release')
    print('=' * W)
    rel = [r for r in rows if r['kind'] == 'release']
    reis = [r for r in rows if r['kind'] == 'reissue']
    print('%d batch(es) -> %d release certificate(s) + %d reissue(s) = %d CoQ document(s)\n'
          % (len(rel), len(rel), len(reis), len(rows)))
    print('%-18s %-11s %-19s %-6s %-8s %-16s %s'
          % ('CoQ code', 'Date', 'Batch', 'Ver', 'Rows', 'Status', 'Strain'))
    print('-' * W)
    for r in rows:
        print('%-18s %-11s %-19s %-6s %-8s %-16s %s'
              % (r['code'], r['date'] or '(no date)', r['batch'],
                 'v.%02d' % r['version'], r['sourced'], r['status'],
                 (r['strain'] or '')[:22]))
    print('-' * W)
    n_iss = sum(1 for r in rows if r['status'] == 'ISSUABLE')
    print('\nISSUABLE now: %d   BLOCKED: %d' % (n_iss, len(rows) - n_iss))
    print('\nCoQ numbers are permanent per batch; a retest advances the VERSION only.')


if __name__ == '__main__':
    main()
