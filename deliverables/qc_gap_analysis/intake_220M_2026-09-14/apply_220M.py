#!/usr/bin/env python3
"""Write the Tranche 2 Farmahem mycotoxin certificates (220-1-М/26 … 220-32-М/26) into the
owner's release register, in the shape of the Tranche 1 rows (197-n-М/26).

    python3 deliverables/qc_gap_analysis/intake_220M_2026-09-14/apply_220M.py
        [--register PATH]   the register to extend  (default: …SUBLOT_2026-09-01.xlsx)
        [--out PATH]        where to write          (default: in place)

Idempotent: a certificate whose code is already in the register is skipped. The desk
does not write the owner's register on its own; this script is the write, ready to run.

What it does, row by row (reads_claude.json, cross-checked against reads_gemini.json):
  * 23 certificates go into the batch's existing block, after its last real
    certificate row and before any "(not numbered)" / "n/a" placeholder;
  * 9 batches have no block and get one, numbered on from the last block: ACC102501
    (P060122), CF102501 (P060132), GG1024, JD012603/01 (P060362), PUM102501 (P060112),
    CC012603 (P060372) — the six the delivery reconciliation found absent from the
    register — and JD042601, FB042601, CC042601, three batches the certificates print
    with no P-number. The label row carries the certificate, as every block's does; the
    strain is the certificate's own, and so is the P-number where it prints one. Where it
    does not, the P-number is the Head of QC's batch list's (tracker/batch_dates.csv, the
    one place the desk keeps cultivation batch <-> P-number): JD042601 = P060492. FB042601
    and CC042601 are on no list the desk holds and keep no P-number (OI-33).
  * every row: "/" in the columns the certificate does not report, ND / ND / ND in
    Aflatoxins Σ / Aflatoxin B1 / Ochratoxin A (Σ is the register's own column; the
    certificate prints B1, B2, G1, G2 and OTA separately, all ND, and the Tranche 1 rows
    were written ND in Σ on the same reading), the code as printed (Cyrillic М), the
    date of issue 11.09.2026, "Farmahem", "Open".
"""
import argparse, copy, json, os, sys
import openpyxl
from openpyxl.utils import range_boundaries

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(GAP)), 'ingestion', 'common'))
from batch_id import batch_key  # noqa: E402

PLACEHOLDER = {'', '(not numbered)', 'n/a'}


def p_from_list(cu):
    """The P-number the Head of QC's batch list gives a cultivation batch, or None.

    For a certificate that names its lot by cultivation code alone. Keyed on batch_key,
    never on the string: the list spells a batch the way the floor does.
    """
    import csv
    path = os.path.join(GAP, 'tracker', 'batch_dates.csv')
    rows = {batch_key(r['cu_batch']): r for r in csv.DictReader(open(path, encoding='utf-8'))}
    return (rows.get(batch_key(cu)) or {}).get('p_batch') or None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--register', default=os.path.join(GAP, 'PP_Batch_Release_QC_Register_SUBLOT_2026-09-01.xlsx'))
    ap.add_argument('--out', default=None)
    ap.add_argument('--no-new-blocks', action='store_true',
                    help='write only the certificates whose batch already has a block; hold the nine that would open one '
                         '(opening a block numbers the batch into the issue-ordered internal-CoA series and renumbers every code after it)')
    a = ap.parse_args()
    out = a.out or a.register
    R = json.load(open(os.path.join(HERE, 'reads_claude.json'), encoding='utf-8'))
    plan = {p['n']: p for p in json.load(open(os.path.join(HERE, 'placement.json'), encoding='utf-8'))}
    wb = openpyxl.load_workbook(a.register)
    ws = wb['Batch Release QC']
    present = {str(ws.cell(r, 23).value or '').strip() for r in range(6, ws.max_row + 1)}
    real = lambda r: str(ws.cell(r, 23).value or '').strip() not in PLACEHOLDER

    # the register as it stands: blocks by identity, so the placement is re-derived here
    # rather than trusted from placement.json's row numbers
    labels = []
    for r in range(6, ws.max_row + 1):
        v = ws.cell(r, 2).value
        if v:
            labels.append((r, str(v).strip(), str(ws.cell(r, 3).value or '').strip()))
        elif str(ws.cell(r, 1).value or '').upper() == 'LEGEND':
            labels.append((r, None, None)); break
    blocks = {}
    for i, (r, b, p) in enumerate(labels):
        if b:
            blk = {'first': r, 'last': labels[i + 1][0] - 1, 'label': b}
            blocks[batch_key(b)] = blk
            if p.startswith('P'):
                blocks.setdefault(batch_key(p), blk)
    tmpl_row = next(r for r in range(6, ws.max_row + 1) if str(ws.cell(r, 23).value or '') == '197-17-М/26')
    tmpl_label = next(r for r in range(6, ws.max_row + 1) if str(ws.cell(r, 2).value or '') == 'OPM1024')
    last_data = max(r for r in range(6, ws.max_row + 1) if ws.cell(r, 23).value not in (None, ''))
    last_no = max(int(ws.cell(r, 1).value) for r in range(6, ws.max_row + 1) if isinstance(ws.cell(r, 1).value, (int, float)))

    def values(m):
        v = [None] * 26
        for c in range(5, 15): v[c - 1] = '/'
        assert all(x == 'ND' for x in m['results'].values()), m['cert_code']
        v[14], v[15], v[16] = 'ND', m['results']['Aflatoxin B1'], m['results']['Ochratoxin A']
        for c in range(18, 23): v[c - 1] = '/'
        v[22], v[23], v[24], v[25] = m['cert_code'], m['date_of_issue'], 'Farmahem', 'Open'
        return v

    def style_from(src, dst):
        for c in range(1, 27):
            s, d = ws.cell(src, c), ws.cell(dst, c)
            d.font, d.fill, d.border, d.alignment, d.number_format = copy.copy(s.font), copy.copy(s.fill), copy.copy(s.border), copy.copy(s.alignment), s.number_format
        ws.row_dimensions[dst].height = ws.row_dimensions[src].height

    todo = [(n, p, R['220-%d-M-26 Pjureli Plant.pdf' % n]) for n, p in sorted(plan.items())]
    todo = [(n, p, m) for n, p, m in todo if m['cert_code'] not in present]
    into, new = [], []
    for n, p, m in todo:
        b = m['batch_printed']; cands = [b, p.get('new_label')] + ([p['block']['label']] if p.get('block') else [])
        blk = next((blocks[batch_key(c)] for c in cands if c and batch_key(c) in blocks), None)
        (into if blk else new).append((n, p, m, blk))
    if a.no_new_blocks:
        print('held (no block, --no-new-blocks): %s' % ', '.join(p.get('new_label') or m['batch_printed'] for n, p, m, _ in new))
        new = []
    inserts = sorted(((max(r for r in range(blk['first'], blk['last'] + 1) if real(r)) + 1, m) for n, p, m, blk in into), key=lambda t: -t[0])
    merged_below = [str(mr) for mr in ws.merged_cells.ranges if mr.min_row > last_data]
    for mr in merged_below: ws.unmerge_cells(mr)
    for at, m in inserts:
        ws.insert_rows(at); style_from(tmpl_row + (1 if tmpl_row >= at else 0), at)
        for c, v in enumerate(values(m), 1): ws.cell(at, c).value = v
    last_data += len(inserts); tmpl_label += sum(1 for at, _ in inserts if at <= tmpl_label)
    from_list = []
    for i, (n, p, m, _) in enumerate(new):
        at = last_data + 1 + i; ws.insert_rows(at); style_from(tmpl_label, at)
        label = p['new_label'] or m['batch_printed']
        pn = m['p_number'] or p_from_list(label)
        if pn and not m['p_number']:
            from_list.append('%s = %s' % (label, pn))
        v = values(m); v[0], v[1], v[2], v[3] = last_no + 1 + i, label, pn, m['strain_printed']
        for c, val in enumerate(v, 1): ws.cell(at, c).value = val
    if from_list:
        print('P-number from the batch list (certificate prints the cultivation batch only): ' + ', '.join(from_list))
    shift = len(inserts) + len(new)
    for mr in merged_below:
        c1, r1, c2, r2 = range_boundaries(mr); ws.merge_cells(start_row=r1 + shift, start_column=c1, end_row=r2 + shift, end_column=c2)
    ws.auto_filter.ref = 'A4:Z%d' % (last_data + len(new))
    wb.save(out)
    print('%s: %d row(s) into existing blocks, %d new block(s) No. %d-%d, %d already present, legend shifted by %d'
          % (os.path.basename(out), len(inserts), len(new), last_no + 1, last_no + len(new), 32 - len(todo), shift))


if __name__ == '__main__':
    main()
