#!/usr/bin/env python3
"""Build T3_Retest and NoTranche subfolders inside DELIVER_2026-09-30_All/.

Each subfolder gets:
  CoQ_<series>_<tranche>_2026-09-30.pdf        — merged CoQs
  iCoA_<series>_<tranche>_2026-09-30.pdf       — merged iCoAs
  CoQ_iCoA_<series>_<tranche>_2026-09-30.pdf   — CoQ+iCoA per lot (CNP lots excluded)
  Paired/<code>_<batch>_<strain>.pdf            — one 2-page (or 1-page) file per lot
"""
import glob, json, os, re, shutil, sys
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
STAMP = '2026-09-30'
DELIVER = os.path.join(GAP, 'DELIVER_%s_All' % STAMP)
PAGES = os.path.join(GAP, 'design_handoff', 'pdf', 'pages')

# CNP lots have no iCoA
CNP_NO_ICOA = {'CoQ-PP_26-075', 'CoQ-PP_26-079', 'CoQ-PP_26-080'}

# Build a map: CoQ code → iCoA code from register
def _icoa_map():
    reg = json.load(open(os.path.join(GAP, 'coq_artifact_data.json'), encoding='utf-8'))['coqs']
    return {c['regcode']: c.get('icoa_code') for c in reg if c.get('icoa_code')}

ICOA_MAP = _icoa_map()

BATCH = re.compile(r'^(CoQ|iCoA)-PP_26-\d{3}_(.*?)\.pdf$')
PLOTRE = re.compile(r'_(P\d{6})_')
CODE   = re.compile(r'^(CoQ|iCoA)-PP_26-(\d{3})')


def merge_pages(paths, dest):
    out = pymupdf.open()
    toc = []
    for p in paths:
        d = pymupdf.open(p)
        for pg in d:
            txt = pg.get_text()
            code_m = re.search(r'CoQ-PP_26-\d{3}|iCoA-PP_26-\d{3}', txt)
            label = code_m.group(0) if code_m else os.path.splitext(os.path.basename(p))[0]
            out.insert_pdf(d, from_page=pg.number, to_page=pg.number)
            toc.append([1, label, out.page_count])
        d.close()
    out.set_toc(toc)
    out.set_metadata({'title': 'Purely Plant — Certificates of Quality',
                      'producer': 'Purely Plant Quality Desk'})
    out.save(dest, garbage=4, deflate=True)
    out.close()
    return len(toc)


def get_pdfs(tranche, series):
    """Return sorted CoQ and iCoA PDF paths from DELIVER_2026-09-30_All."""
    section = 'Retest' if series == 'retest' else 'Initial'
    coqs  = sorted(glob.glob(os.path.join(DELIVER, 'CoQ',  section, tranche, '*.pdf')),
                   key=lambda p: int(CODE.match(os.path.basename(p)).group(2)) if CODE.match(os.path.basename(p)) else 999)
    icos  = sorted(glob.glob(os.path.join(DELIVER, 'iCoA', section, tranche, '*.pdf')),
                   key=lambda p: int(CODE.match(os.path.basename(p)).group(2)) if CODE.match(os.path.basename(p)) else 999)
    return coqs, icos


def plot(path):
    m = PLOTRE.search(os.path.basename(path))
    return m.group(1) if m else None


def match_icoa(coq_path, icos):
    """Find the iCoA for this CoQ using register icoa_code, then P-lot, then number."""
    coq_code_m = CODE.match(os.path.basename(coq_path))
    if coq_code_m:
        coq_code = 'CoQ-PP_26-' + coq_code_m.group(2)
        ico_code = ICOA_MAP.get(coq_code)  # e.g. 'iCoA-PP_26-089'
        if ico_code:
            for ico in icos:
                if ico_code in os.path.basename(ico):
                    return ico
    # fallback: P-lot code
    p = plot(coq_path)
    if p:
        for ico in icos:
            if p in os.path.basename(ico):
                return ico
    # fallback: same number
    if coq_code_m:
        num = coq_code_m.group(2)
        for ico in icos:
            mi = CODE.match(os.path.basename(ico))
            if mi and mi.group(2) == num:
                return ico
    return None


def build_set(tranche, series, out_dir):
    section_label = 'Retest' if series == 'retest' else 'Initial'
    tranche_label = tranche  # 'T3' or 'NoTranche'
    coqs, icos = get_pdfs(tranche, series)
    if not coqs:
        print('  skip %s %s — no CoQ pages found' % (tranche_label, section_label))
        return

    os.makedirs(out_dir, exist_ok=True)
    paired_dir = os.path.join(out_dir, 'Paired')
    os.makedirs(paired_dir, exist_ok=True)

    stamp = STAMP
    # 1. merged CoQs
    coq_merged = os.path.join(out_dir, 'CoQ_%s_%s_%s.pdf' % (section_label, tranche_label, stamp))
    n_coq = merge_pages(coqs, coq_merged)
    print('  CoQ   merged: %d pages → %s' % (n_coq, os.path.basename(coq_merged)))

    # 2. merged iCoAs
    if icos:
        ico_merged = os.path.join(out_dir, 'iCoA_%s_%s_%s.pdf' % (section_label, tranche_label, stamp))
        n_ico = merge_pages(icos, ico_merged)
        print('  iCoA  merged: %d pages → %s' % (n_ico, os.path.basename(ico_merged)))

    # 3. paired files + combined
    combined_pages = []
    n_paired = 0
    n_no_ico = 0
    for coq in coqs:
        rc = CODE.match(os.path.basename(coq))
        code = rc.group(0) if rc else None  # 'CoQ-PP_26-NNN'
        # determine stem for paired filename
        stem = os.path.splitext(os.path.basename(coq))[0][len('CoQ-PP_26-'):]  # 'NNN_...'
        paired_name = os.path.join(paired_dir, os.path.basename(coq))  # keep original name

        is_cnp = code in CNP_NO_ICOA
        ico = None if is_cnp else match_icoa(coq, icos)

        if is_cnp or ico is None:
            # just copy the CoQ as the paired file (single page)
            shutil.copy2(coq, paired_name)
            n_no_ico += 1
        else:
            # merge CoQ + iCoA into one paired file
            out = pymupdf.open()
            for src_path in (coq, ico):
                d = pymupdf.open(src_path)
                out.insert_pdf(d)
                d.close()
            out.save(paired_name, garbage=4, deflate=True)
            out.close()
            combined_pages.extend([coq, ico])
            n_paired += 1

    print('  Paired: %d with iCoA, %d without → %s/' % (n_paired, n_no_ico, os.path.basename(paired_dir)))

    # 4. combined merged PDF (lots with iCoA only)
    if combined_pages:
        comb = os.path.join(out_dir, 'CoQ_iCoA_%s_%s_%s.pdf' % (section_label, tranche_label, stamp))
        n_comb = merge_pages(combined_pages, comb)
        print('  Combined: %d pages → %s' % (n_comb, os.path.basename(comb)))


def main():
    # T3 Retest
    t3_ret_dir = os.path.join(DELIVER, 'T3_Retest')
    shutil.rmtree(t3_ret_dir, ignore_errors=True)
    print('Building T3 Retest ...')
    build_set('T3', 'retest', t3_ret_dir)

    # NoTranche Initial
    nt_ini_dir = os.path.join(DELIVER, 'NoTranche', 'Initial')
    nt_ret_dir = os.path.join(DELIVER, 'NoTranche', 'Retest')
    shutil.rmtree(os.path.join(DELIVER, 'NoTranche'), ignore_errors=True)
    print('Building NoTranche Initial ...')
    build_set('NoTranche', 'initial', nt_ini_dir)
    print('Building NoTranche Retest ...')
    build_set('NoTranche', 'retest', nt_ret_dir)

    return 0


if __name__ == '__main__':
    sys.exit(main())
