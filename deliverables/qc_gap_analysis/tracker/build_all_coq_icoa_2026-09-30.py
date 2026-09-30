#!/usr/bin/env python3
"""Collect all CoQ and iCoA PDFs into organised folders for delivery.

Output: DELIVER_2026-09-30_All/
  CoQ/{Initial,Retest}/{T1,T2,T3}/<code>_<batch>_<strain>.pdf
  iCoA/{Initial,Retest}/{T1,T2,T3}/<code>_<batch>_<strain>.pdf
  CoQ_all_2026-09-30.zip
  iCoA_all_2026-09-30.zip
"""
import collections, csv, glob, json, os, re, shutil, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
GAP  = os.path.dirname(HERE)
STAMP = '2026-09-30'
OUT   = os.path.join(GAP, 'DELIVER_%s_All' % STAMP)
PAGES = os.path.join(GAP, 'design_handoff', 'pdf', 'pages')

# iCoA sources (same as paired builder)
T3_INI    = os.path.join(GAP, 'DELIVER_2026-09-26_T3', 'iCoA', 'Initial', 'PDF')
T3_RET    = '/tmp/claude-0/pair/ico_t3ret_unsigned'
T12_RET   = ['/tmp/claude-0/pair/ico_t12ret',
             os.path.join(GAP, 'DELIVER_2026-09-24', 'signed_LOD')]
T12_INI   = '/tmp/claude-0/pair/ico_t12init'

CNP_NO_ICOA = {'CoQ-PP_26-092', 'CoQ-PP_26-123'}
PLOT  = re.compile(r'^P\d{6}$')
BATCH = re.compile(r'^(?:CoQ|iCoA)-PP_26-\d{3}_([A-Za-z0-9]+)_')


def tranche_map():
    m = {}
    with open(os.path.join(GAP, 'intake_tranches_2026-09-18',
                           'drive_folders_2026-09-18.tsv'), encoding='utf-8') as fh:
        for r in csv.DictReader(fh, delimiter='\t'):
            f, t = r['folder'], r['tranche']
            tail = f.rsplit('_', 1)[-1]
            if PLOT.match(tail):
                m[tail] = t
            m[f] = t
            m.setdefault(re.split(r'_P\d{6}$', f)[0].rstrip('_').replace('＊', ''), t)
    return m


def batch_of(path):
    m = BATCH.match(os.path.basename(path))
    return m.group(1) if m else None


def newest(paths):
    return max(paths, key=os.path.getmtime) if paths else None


def coq_pdf(code):
    return newest(glob.glob(os.path.join(PAGES, code + '_*.pdf')))


def by_batch(dirs, keys):
    for d in dirs:
        for p in glob.glob(os.path.join(d, 'iCoA-PP_26-*.pdf')):
            if batch_of(p) in keys:
                return p
    return None


def icoa_pdf(tr, series, code, keys):
    if tr == 'T3':
        if not code:
            return None
        if series == 'retest':
            g = glob.glob(os.path.join(T3_RET, code + '_*.pdf'))
            return g[0] if g else None
        g = glob.glob(os.path.join(T3_INI, code + '_*.pdf'))
        return g[0] if g else None
    if series == 'retest':
        return by_batch(T12_RET, keys) or \
               (glob.glob(os.path.join('/tmp/claude-0/pair/ico_t12ret_regen',
                                       code + '_*.pdf')) or [None])[0]
    return (glob.glob(os.path.join(T12_INI, code + '_*.pdf')) or [None])[0]


def main():
    tm  = tranche_map()
    reg = json.load(open(os.path.join(GAP, 'coq_artifact_data.json'),
                         encoding='utf-8'))['coqs']

    def tr(c):
        for k in (c.get('pp'), c.get('cb'),
                  (c.get('cb') or '').replace('＊', '')):
            if k and k in tm:
                return tm[k]

    def ser(c):
        return 'retest' if str(c['t']).lower().startswith('retest') else 'initial'

    shutil.rmtree(OUT, ignore_errors=True)
    coq_rows, ico_rows = [], []

    for c in sorted(reg, key=lambda c: int(c['regcode'].split('-')[-1])):
        t = tr(c)
        if t not in ('T1', 'T2', 'T3') or c.get('withdrawn'):
            continue
        s, rc, code = ser(c), c['regcode'], c.get('icoa_code')
        keys = {str(c.get('pp')), str(c.get('cb')),
                str(c.get('cb') or '').replace('＊', '')}
        section = 'Retest' if s == 'retest' else 'Initial'

        # --- CoQ ---
        coq = coq_pdf(rc)
        if not coq:
            raise SystemExit('%s: no CoQ page in %s' % (rc, PAGES))
        d = os.path.join(OUT, 'CoQ', section, t)
        os.makedirs(d, exist_ok=True)
        dst = os.path.join(d, os.path.basename(coq))
        shutil.copy2(coq, dst)
        coq_rows.append(dst)

        # --- iCoA ---
        if rc in CNP_NO_ICOA:
            continue
        ico = icoa_pdf(t, s, code, keys)
        if not ico:
            print('WARN: no iCoA for %s (code %s)' % (rc, code), file=sys.stderr)
            continue
        if batch_of(ico) and batch_of(ico) not in keys:
            raise SystemExit('%s: iCoA batch mismatch %s vs %s' % (
                rc, batch_of(ico), keys))
        d = os.path.join(OUT, 'iCoA', section, t)
        os.makedirs(d, exist_ok=True)
        dst = os.path.join(d, os.path.basename(ico))
        shutil.copy2(ico, dst)
        ico_rows.append(dst)

    # zip CoQs
    coq_zip = os.path.join(OUT, 'CoQ_all_%s.zip' % STAMP)
    with zipfile.ZipFile(coq_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(coq_rows):
            zf.write(p, os.path.relpath(p, OUT))

    # zip iCoAs
    ico_zip = os.path.join(OUT, 'iCoA_all_%s.zip' % STAMP)
    with zipfile.ZipFile(ico_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(ico_rows):
            zf.write(p, os.path.relpath(p, OUT))

    print('CoQ  PDFs: %d  → %s' % (len(coq_rows),
                                    os.path.relpath(coq_zip, GAP)))
    print('iCoA PDFs: %d  → %s' % (len(ico_rows),
                                    os.path.relpath(ico_zip, GAP)))
    cnt = collections.Counter()
    for c in reg:
        t = tr(c)
        if t in ('T1','T2','T3') and not c.get('withdrawn'):
            cnt[(t, ser(c))] += 1
    for k in sorted(cnt):
        print('  %-3s %-8s %d' % (k[0], k[1], cnt[k]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
