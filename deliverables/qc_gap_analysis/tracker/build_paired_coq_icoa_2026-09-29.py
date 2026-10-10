#!/usr/bin/env python3
"""Two-page CoQ+iCoA files per batch (page 1 = CoQ, page 2 = its internal certificate).

Head of QC, 29.09.2026: give the certificates as two-page files — the certificate of quality of a
batch, then the internal certificate of analysis for that batch — for T1/T2 retest and T3 retest into
one archived folder, the T1/T2/T3 initial-release pairs listed the same way, and a CoQ-code → iCoA-code
list in logical order.

Sources, each the current/authoritative one for its family, matched to the batch (never only the code):
  * CoQ (every record) — the current print of build_v40.js's pages (design_handoff/pdf/pages, newest
    file per code): Tranche 1 and 2 are the frozen pages held byte-for-byte against the sent scans;
    Tranche 3 carries the widened fades of 28.09. House fonts embedded (print_v40.py).
  * iCoA T3 (initial + retest) — DELIVER_2026-09-26_T3/iCoA.
  * iCoA T1/T2 retest — the SENT owner-format certificates of 24.09, matched to each lot BY BATCH
    (DELIVER_2026-09-24, its signed_LOD for the two loss-on-drying ones), rendered to PDF unchanged.
  * iCoA T1/T2 initial — regenerated in the current owner format from the (frozen) register; these were
    never issued to the customer, so there is no sent version to keep.
No internal certificate — CNP tested those parameters — so the file is the certificate of quality alone:
the Tranche-3 lots -075, -079, -080, and (per the approved scans of 25.09) the retests P060402 (CoQ-092)
and P060412 (CoQ-123), whose scans carry no iCoA row and credit 1,2,7,8 to CNP.
Signatures: every certificate is signed except the Tranche-3 retest, per the Head of QC (29.09.2026) —
the T3-retest iCoA is rendered here from the owner-format pages with the signature images stripped.

Every pairing asserts the internal certificate's batch equals the certificate of quality's batch.
"""
import collections, csv, glob, json, os, re, shutil, sys, zipfile
import fitz  # pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
STAMP = '2026-09-29'
OUT = os.path.join(GAP, 'DELIVER_%s_Paired' % STAMP)
PAGES = os.path.join(GAP, 'design_handoff', 'pdf', 'pages')
T3 = os.path.join(GAP, 'DELIVER_2026-09-26_T3', 'iCoA')
T3_RET_UNSIGNED = '/tmp/claude-0/pair/ico_t3ret_unsigned'   # T3 retest iCoA, signatures stripped
SENT_RET = ['/tmp/claude-0/pair/ico_t12ret', os.path.join(GAP, 'DELIVER_2026-09-24', 'signed_LOD')]
REGEN_RET = '/tmp/claude-0/pair/ico_t12ret_regen'
INI_T12 = '/tmp/claude-0/pair/ico_t12init'
# The approved scans (SCAN_INDEX 2026-09-25) carry no iCoA for these lots — 1,2,7,8 credited to CNP —
# so the file is the certificate of quality alone. P060402=CoQ-092 (GG012603), P060412=CoQ-123 (JD012603/02).
CNP_NO_ICOA = {'CoQ-PP_26-092', 'CoQ-PP_26-123'}
PLOT = re.compile(r'^P\d{6}$')
BATCH = re.compile(r'^(?:CoQ|iCoA)-PP_26-\d{3}_([A-Za-z0-9]+)_')


def tranche_map():
    m = {}
    with open(os.path.join(GAP, 'intake_tranches_2026-09-18', 'drive_folders_2026-09-18.tsv'), encoding='utf-8') as fh:
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
        if series == 'retest':                               # unsigned T3 retest (Head of QC: no signature)
            g = glob.glob(os.path.join(T3_RET_UNSIGNED, code + '_*.pdf'))
            return g[0] if g else None
        g = glob.glob(os.path.join(T3, 'Initial', 'PDF', code + '_*.pdf'))
        return g[0] if g else None
    if series == 'retest':                                   # T1/T2 sent retest, anchored on the batch
        return by_batch(SENT_RET, keys) or (glob.glob(os.path.join(REGEN_RET, code + '_*.pdf')) or [None])[0]
    return (glob.glob(os.path.join(INI_T12, code + '_*.pdf')) or [None])[0]   # T1/T2 initial, regenerated


def merge(coq, ico, dst):
    d = fitz.open()
    d.insert_pdf(fitz.open(coq), from_page=0, to_page=0)
    if ico:
        d.insert_pdf(fitz.open(ico), from_page=0, to_page=0)
    d.save(dst, garbage=4, deflate=True)
    n = d.page_count
    d.close()
    return n


def main():
    tm = tranche_map()
    reg = json.load(open(os.path.join(GAP, 'coq_artifact_data.json'), encoding='utf-8'))['coqs']

    def tr(c):
        for k in (c.get('pp'), c.get('cb'), (c.get('cb') or '').replace('＊', '')):
            if k and k in tm:
                return tm[k]

    def ser(c):
        return 'retest' if str(c['t']).lower().startswith('retest') else 'initial'

    shutil.rmtree(OUT, ignore_errors=True)
    rows, notes = [], []
    for c in sorted(reg, key=lambda c: int(c['regcode'].split('-')[-1])):
        t = tr(c)
        if t not in ('T1', 'T2', 'T3') or c.get('withdrawn'):
            continue
        s, rc, code = ser(c), c['regcode'], c.get('icoa_code')
        keys = {str(c.get('pp')), str(c.get('cb')), str(c.get('cb') or '').replace('＊', '')}
        coq = coq_pdf(rc)
        if not coq:
            raise SystemExit('%s: no CoQ page in %s' % (rc, PAGES))
        ico = None if rc in CNP_NO_ICOA else icoa_pdf(t, s, code, keys)
        # every pairing must be the same lot on both pages
        if ico and batch_of(ico) and batch_of(ico) not in keys:
            raise SystemExit('%s: iCoA %s is batch %s, not %s' % (rc, os.path.basename(ico), batch_of(ico), keys))
        if not ico and rc not in CNP_NO_ICOA and not (t == 'T3' and code and s in ('initial', 'retest')):
            raise SystemExit('%s: no iCoA resolved (code %s)' % (rc, code))

        base = os.path.basename(coq)[:-4]
        section = 'Retest' if s == 'retest' else 'Initial'
        d = os.path.join(OUT, section, t)
        os.makedirs(d, exist_ok=True)
        name = base + ('__%s' % code if ico else '__no-iCoA_CNP-tested') + '.pdf'
        pages = merge(coq, ico, os.path.join(d, name))
        src = ('none — CNP' if not ico else
               'T3 retest (unsigned)' if (t == 'T3' and s == 'retest') else
               'T3 delivery' if t == 'T3' else
               'sent 24.09' if (s == 'retest' and REGEN_RET not in ico) else
               'regenerated')
        rows.append({'coq': rc, 'icoa': (code if ico else ''), 'tranche': t, 'series': s,
                     'batch': c.get('pp') or c.get('cb'), 'strain': c.get('strain') or '',
                     'grade': c.get('grade') or '', 'coq_issue': c.get('issue') or '',
                     'icoa_issue': c.get('icoa_issue') or '', 'pages': pages, 'icoa_source': src})

    # the CoQ-code -> iCoA-code list, in logical (document-number) order
    mp = os.path.join(OUT, 'CoQ_iCoA_code_map_%s.tsv' % STAMP)
    fields = ['coq', 'icoa', 'tranche', 'series', 'batch', 'strain', 'grade', 'coq_issue', 'icoa_issue', 'pages', 'icoa_source']
    with open(mp, 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter='\t')
        w.writeheader()
        w.writerows(rows)
    # and a readable markdown table, grouped
    md = os.path.join(OUT, 'CoQ_iCoA_code_map_%s.md' % STAMP)
    with open(md, 'w', encoding='utf-8') as fh:
        fh.write('# Certificate of Quality -> internal Certificate of Analysis, in document-number order\n\n')
        fh.write('%d certificates (Tranches 1-3, initial and retest).\n\n' % len(rows))
        fh.write('| CoQ code | iCoA code | Tr | Series | Batch | Strain | Grade | CoQ issued | iCoA issued | iCoA source |\n')
        fh.write('|---|---|---|---|---|---|---|---|---|---|\n')
        for r in rows:
            fh.write('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |\n' % (
                r['coq'], r['icoa'] or '— (CNP; no iCoA)', r['tranche'], r['series'], r['batch'],
                r['strain'], r['grade'], r['coq_issue'], r['icoa_issue'], r['icoa_source']))

    zips = []
    for section in ('Retest', 'Initial'):
        base = os.path.join(OUT, section)
        files = sorted(glob.glob(os.path.join(base, '**', '*.pdf'), recursive=True))
        if not files:
            continue
        z = os.path.join(OUT, 'CoQ_iCoA_%s_pairs_%s.zip' % (section, STAMP))
        with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
            for p in files:
                zf.write(p, os.path.relpath(p, OUT))
            zf.write(md, os.path.basename(md))
        zips.append((section, z, len(files)))

    print('paired files written: %d' % len(rows))
    for k in sorted(collections.Counter((r['tranche'], r['series']) for r in rows)):
        n = sum(1 for r in rows if (r['tranche'], r['series']) == k)
        print('   %-3s %-8s %d' % (k[0], k[1], n))
    print('iCoA sources:', dict(collections.Counter(r['icoa_source'] for r in rows)))
    print('code map: %s / .md (%d rows)' % (os.path.relpath(mp, GAP), len(rows)))
    for s, z, cnt in zips:
        print('zip: %s (%d pairs)' % (os.path.relpath(z, GAP), cnt))
    return 0


if __name__ == '__main__':
    sys.exit(main())
