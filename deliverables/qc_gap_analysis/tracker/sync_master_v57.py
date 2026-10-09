#!/usr/bin/env python3
"""CoQ_Analysis_Master_v57 — v56 brought into line with the register the certificates print from.

    python3 deliverables/qc_gap_analysis/tracker/sync_master_v57.py

Found in the review of 27.09.2026. The standing rule, given eleven times: carry every change into every
deliverable and every sheet of the latest master. v56 was built on 21.09.2026 and nothing after it
reached it — the 23.09 ruling that an internal certificate takes its CoQ's number, the 25.09
renumbering, the P060332 move, the Tranche 3 re-dating, the withdrawals, GRC-IV, the moves of 27.09.
Held against `coq_artifact_data.json` — which the 46 approved scans confirm (43 of 43 iCoA citations,
every CoQ code) — v56's live registers gave 23 CoQ codes to the wrong lot (`-068`…`-073`,
`-089`…`-105`, Tranche 1 numbers among them), 132 CoQs the wrong iCoA, and 16 issue dates, and still
numbered five withdrawn certificates. CI stayed green: its check compared the workbook with
`icoa_register.py`, which was stale in the same way (fixed in the same review).

What changes, and nothing else:

* **iCoA Register, CoQ Register** — the number, the code, the issue date, the test date, the cited
  iCoA, the lot, the strain and the grading are written as values from the register; the rows are
  put in number order; a withdrawn certificate keeps its row, loses its number and says so; an iCoA
  round no certificate cites takes no number. The number no longer follows the row: a code on a sent
  scan never moves (CLAUDE.md §7). Formulas that still read their own row are translated with it.
* **CoQ References, CoQ Compilation, CoQ Compilation (long), Result Supersession, Potency Grades** —
  rebuilt by their own builders (coq_references, coq_compilation, result_supersession,
  potency_grades) from the register, with the register's codes; withdrawn certificates are left out.
* **Everything else is v56's**, the CoQ Parameter Tracker (renamed v57; its in-house cells look the
  iCoA up by key, so they follow the register sheet) and the dated sections of Reference among it.
"""
import copy, csv, datetime, json, os, re, sys, tempfile

import openpyxl
from openpyxl.formula.translate import Translator
from openpyxl.styles import Alignment, Font, PatternFill

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(GAP))
sys.path.insert(0, HERE)
sys.path.insert(0, GAP)
sys.path.insert(0, ROOT)
from ingestion.common.batch_id import batch_key as bk                 # noqa: E402
import icoa_register as IR                                          # noqa: E402

SRC = os.path.join(HERE, 'CoQ_Analysis_Master_v56.xlsx')
OUT = os.path.join(HERE, 'CoQ_Analysis_Master_v57.xlsx')
REG = os.path.join(GAP, 'coq_artifact_data.json')
BUILT = '27.09.2026'
WITHDRAWN = 'withdrawn — number free, no certificate (Head of QC, 26–27.09.2026)'


def day(s):
    m = re.fullmatch(r'(\d\d)\.(\d\d)\.(\d{4})', str(s or '').strip())
    return datetime.datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else None


def header(ws):
    return {str(c.value): c.column for c in ws[1] if c.value}


def rows_of(ws, last):
    return [[ws.cell(r, c) for c in range(1, ws.max_column + 1)] for r in range(2, last + 1)]


def rewrite(ws, table, rows, values):
    """Write `rows` (lists of source cells) back in the given order, `values` overriding by column.

    A formula moves with its row (Translator); styles are copied from the source cell."""
    tab = ws.tables[table]
    first, last = 2, int(re.search(r'(\d+)$', tab.ref).group(1))
    note = [(c.value, copy.copy(c._style)) for c in ws[last + 2]] if ws.max_row >= last + 2 else None
    merged_note = [m for m in ws.merged_cells.ranges if m.min_row == last + 2]
    for m in merged_note:
        ws.unmerge_cells(str(m))
    snap = []
    for src in rows:
        snap.append([(c.value, copy.copy(c._style), c.coordinate, c.number_format) for c in src])
    for r in range(first, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            ws.cell(r, c).value = None
    for i, cells in enumerate(snap):
        r = first + i
        over = values[i]
        for ci, (v, st, coord, nf) in enumerate(cells, 1):
            cell = ws.cell(r, ci)
            cell._style = st
            if ci in over:
                v = over[ci]
                if isinstance(v, datetime.datetime):
                    cell.number_format = 'DD.MM.YYYY'
            elif isinstance(v, str) and v.startswith('='):
                v = Translator(v, origin=coord).translate_formula(cell.coordinate)
            cell.value = v
    end = first + len(snap) - 1
    tab.ref = re.sub(r'\d+$', str(end), tab.ref)
    if note:
        for ci, (v, st) in enumerate(note, 1):
            cell = ws.cell(end + 2, ci)
            cell.value, cell._style = v, st
        ws.merge_cells(start_row=end + 2, start_column=1, end_row=end + 2, end_column=ws.max_column)
    return end


def main():
    data = json.load(open(REG, encoding='utf-8'))
    coqs = data['coqs']
    rec = {}
    for c in coqs:
        kind = 'R' if c['t'].startswith('retest') else 'I'
        for nm in filter(None, (c.get('pp'), c.get('cb'))):
            k = (bk(nm), kind)
            if k in rec and rec[k] is not c and not rec[k].get('withdrawn') and not c.get('withdrawn'):
                raise SystemExit('two live records for %s: %s, %s' % (k, rec[k]['regcode'], c['regcode']))
            if k not in rec or rec[k].get('withdrawn'):
                rec[k] = c
    by_icoa = {c['icoa_code']: c for c in coqs if not c.get('withdrawn')
               and any(str(r.get('doc') or '') == c['icoa_code'] for r in c['rows'])}
    icoa_of = {}
    for r in IR.build():
        suf = 'I' if r['round'] == 'initial release' else ('R' if r['round'] == 'retest 1' else 'R' + r['round'].split()[-1])
        for base in filter(None, (r['p_lot'], r['batch'])):
            icoa_of.setdefault('%s|%s' % (bk(base), suf), r['code'])
    grades = {}
    for g in csv.DictReader(open(os.path.join(GAP, 'potency_grades_2026-09-15.csv'), encoding='utf-8')):
        grades[(g['abbr'], g.get('numeral') or '')] = g

    wb = openpyxl.load_workbook(SRC)
    report = []

    # ---------------------------------------------------------------- CoQ Register
    ws = wb['CoQ Register']
    H = header(ws)
    last = int(re.search(r'(\d+)$', ws.tables['CoQ_Register'].ref).group(1))
    src_rows, vals, seen = rows_of(ws, last), [], set()

    def names(cells, base):
        out = [base]
        for col in ('P Batch', 'CU Batch'):
            v = str(cells[H[col] - 1].value or '').strip()
            if v and not v.startswith(('N/A', '—')):
                out.append(v)
        return out

    # a lot's retest certificate goes to its campaign row ("retest — Tranche n"), else its first retest row
    owner = {}
    for i, cells in enumerate(src_rows):
        key = str(cells[H['Key'] - 1].value or '')
        base, _, suf = key.rpartition('|')
        kind = 'I' if suf == 'I' else 'R'
        c = next((rec[(bk(n), kind)] for n in names(cells, base) if (bk(n), kind) in rec), None)
        if c is None:
            continue
        camp = 'Tranche' in str(cells[H['Series'] - 1].value or '')
        held = owner.get(id(c))
        if held is None or (kind == 'R' and camp and not held[1]):
            owner[id(c)] = (i, camp, c)
    row_rec = {i: c for i, _, c in owner.values()}
    for i, cells in enumerate(src_rows):
        key = str(cells[H['Key'] - 1].value or '')
        c = row_rec.get(i)
        v = {}
        if c is None:
            v.update({H['No.']: '', H['CoQ code']: '— not a certificate on the register —', H['Issuable']: 'no',
                      H['Issue date (planned)']: ''})
        elif c.get('withdrawn'):
            seen.add(id(c))
            v.update({H['No.']: '', H['CoQ code']: '— withdrawn (%s) —' % c['regcode'][4:], H['Issuable']: 'withdrawn',
                      H['Issue date (planned)']: '', H['Status']: WITHDRAWN})
        else:
            seen.add(id(c))
            n = int(c['regcode'][-3:])
            g = grades.get((str(c.get('pcode') or '').split('_')[0], c.get('grade') or ''), {})
            r4 = next((r for r in c['rows'] if r['no'] == '4'), {})
            ic = c.get('icoa_code') if c.get('icoa_code') in by_icoa else '— none: CNP tested 1, 2, 7 —'
            v.update({H['No.']: n, H['CoQ code']: c['regcode'], H['Issuable']: 'yes',
                      H['Issue date (planned)']: day(c.get('issue')) or '',
                      H['iCoA (register)']: ic,
                      H['iCoA issue date']: day(c.get('icoa_issue')) if ic.startswith('iCoA') else '',
                      H['CU Batch']: c.get('cb') or '—',
                      H['P Batch']: c.get('pp') or 'N/A — no P batch assigned',
                      H['Strain']: c.get('strain') or '—',
                      H['Total THC (%)']: r4.get('res') or '—', H['THC certificate']: r4.get('doc') or '—',
                      H['Grade nominal ± tol. (numeral)']: ('%s ± %s (%s)' % (g['nominal'], g['tolerance'], c.get('grade'))
                                                          if g else (c.get('grade') or '—')),
                      H['Grade window']: ('%s – %s %%' % (g['window_low'], g['window_high']) if g else '—'),
                      H['Product code']: c.get('pcode') or '—',
                      H['Specification code']: c.get('spec') or '—',
                      H['Specification status']: c.get('spec_status') or '—'})
            was = str(c.get('issue_before_redating') or '').strip()
            if was and was != c.get('issue'):
                v[H['Status']] = ('moved — re-dated from %s to %s: its release testing is the later certificate '
                                  '(Head of QC, 26–27.09.2026)' % (was, c.get('issue')))
            if 'retest' in c['t']:
                sup = c.get('supersedes') or {}
                if sup.get('code'):
                    v[H['Supersedes (initial CoQ)']] = '%s of %s' % (sup['code'], sup.get('date', ''))
        vals.append(v)
    missing = [c for c in coqs if id(c) not in seen]
    for c in missing:
        report.append('CoQ Register: %s (%s %s) has no row on the sheet' % (c['regcode'], c.get('pp'), c.get('cb')))
    order = sorted(range(len(src_rows)), key=lambda i: (vals[i].get(H['No.']) in ('', None),
                                                         vals[i].get(H['No.']) or 0, i))
    rewrite(ws, 'CoQ_Register', [src_rows[i] for i in order], [vals[i] for i in order])
    n_coq = sum(1 for v in vals if v.get(H['No.']))

    # ---------------------------------------------------------------- iCoA Register
    ws = wb['iCoA Register']
    H = header(ws)
    last = int(re.search(r'(\d+)$', ws.tables['iCoA_Register'].ref).group(1))
    src_rows, vals = rows_of(ws, last), []
    placed = set()
    for cells in src_rows:
        key = str(cells[H['Key'] - 1].value or '')
        base, _, suf = key.rpartition('|')
        cand = [base] + [str(cells[H[col] - 1].value or '').strip() for col in ('P Batch', 'CU Batch')]
        code = next((icoa_of['%s|%s' % (bk(n), suf)] for n in cand
                     if n and not n.startswith(('N/A', '—')) and '%s|%s' % (bk(n), suf) in icoa_of), '')
        c = by_icoa.get(code)
        v = {}
        if not code or c is None or code in placed:
            v.update({H['No.']: '', H['iCoA code']: '— not issued —', H['Issuable']: 'no',
                      H['Issue date (planned)']: ''})
            w = rec.get((bk(base), 'R' if suf.startswith('R') else 'I'))
            if w is not None and w.get('withdrawn') and suf in ('I', 'R'):
                v[H['Status']] = WITHDRAWN
        else:
            placed.add(code)
            v.update({H['No.']: int(code[-3:]), H['iCoA code']: code, H['Issuable']: 'yes',
                      H['Issue date (planned)']: day(c.get('icoa_issue')) or '',
                      H['Test date (packaging)']: day(c.get('icoa_tested')) or '— not on record —',
                      H['CU Batch']: c.get('cb') or '—', H['P Batch']: c.get('pp') or 'N/A — no P batch assigned',
                      H['Strain']: c.get('strain') or '—'})
        vals.append(v)
    absent = sorted(set(by_icoa) - placed)
    for code in absent:
        report.append('iCoA Register: %s (%s) has no round on the sheet' % (code, by_icoa[code]['regcode']))
    order = sorted(range(len(src_rows)), key=lambda i: (vals[i].get(H['No.']) in ('', None),
                                                         vals[i].get(H['No.']) or 0, i))
    rewrite(ws, 'iCoA_Register', [src_rows[i] for i in order], [vals[i] for i in order])
    n_icoa = len(placed)

    # ---------------------------------------------------------------- the sheets built from the register
    live = dict(data)
    live['coqs'] = [c for c in coqs if not c.get('withdrawn')]
    tmp = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8')
    json.dump(live, tmp, ensure_ascii=False)
    tmp.close()

    def replace(name, fill):
        at = wb.sheetnames.index(name)
        old = wb[name]
        ps, fit = copy.copy(old.page_setup), old.sheet_properties.pageSetUpPr
        del wb[name]
        sh = wb.create_sheet(name, at)
        n = fill(sh)
        # the Read Me says every sheet prints landscape, one page wide — so does the rebuilt one
        sh.page_setup.orientation = ps.orientation or 'landscape'
        sh.page_setup.paperSize = ps.paperSize
        sh.page_setup.fitToWidth, sh.page_setup.fitToHeight = ps.fitToWidth or 1, ps.fitToHeight or 0
        sh.sheet_properties.pageSetUpPr = copy.copy(fit) if fit is not None else None
        if sh.sheet_properties.pageSetUpPr is not None:
            sh.sheet_properties.pageSetUpPr.fitToPage = True
        return n

    import coq_references as CRF
    import coq_compilation as CCP
    import result_supersession as RSU
    refs = CRF.build_rows(tmp.name, os.path.join(HERE, 'new_instances.json'), None)
    replace('CoQ References', lambda sh: CRF.fill_sheet(sh, refs))
    wide, long_ = CCP.build(tmp.name, None)
    replace('CoQ Compilation', lambda sh: CCP.fill_wide(sh, wide))
    replace('CoQ Compilation (long)', lambda sh: CCP.fill_long(sh, long_))
    sup = RSU.sheet_rows(live)
    replace(RSU.SHEET, lambda sh: RSU.fill(sh, sup))
    replace('Potency Grades', potency_sheet)
    os.unlink(tmp.name)

    # what v57 is, where a reader looks: the Read Me head, and the notes under the two registers
    moved = sorted((c['regcode'], c.get('pp') or c.get('cb'), c.get('issue_before_redating'), c.get('issue'))
                   for c in coqs if not c.get('withdrawn') and c.get('issue_before_redating')
                   and c.get('issue_before_redating') != c.get('issue'))
    gone = sorted(c['regcode'] for c in coqs if c.get('withdrawn'))
    v57 = ('v57, %s (tracker/sync_master_v57.py): v56 brought into line with coq_artifact_data.json, the register '
           'the certificates print from and the 46 approved scans confirm. Numbers, codes, issue and test dates, the '
           'cited iCoA, lot, strain and grading are the register\'s, as values: a code on a sent scan never moves, so '
           'the number no longer follows the row. Re-dated by the rulings of 26–27.09.2026 (the release testing is the '
           'later certificate): %s. Withdrawn, numbers free: %s. CoQ References, both Compilation tabs, Result '
           'Supersession and Potency Grades rebuilt from the register (withdrawn left out; GRC-IV added). The numbers '
           'out of date order are listed in tracker/ISSUANCE_ORDER_CHECK_2026-09-27.tsv, with the Head of QC. '
           % (BUILT, '; '.join('%s (%s) %s → %s' % (m[0][4:], m[1], m[2], m[3]) for m in moved),
              ', '.join(g[4:] for g in gone)))
    ref = wb['Reference']
    for row in ref.iter_rows(min_row=1, max_row=20):
        for cell in row:
            if cell.value == 'CoQ Analysis Master — v56':
                cell.value = 'CoQ Analysis Master — v57'
            elif cell.column == 2 and isinstance(cell.value, str) and cell.value.startswith('Built 21.09.2026'):
                cell.value = v57 + 'Before that: ' + cell.value
            elif cell.column == 2 and isinstance(cell.value, str) and '(172 × 23)' in cell.value:
                cell.value = cell.value.replace('(172 × 23)', '(%d × 23; the withdrawn numbers are left out)'
                                                % sum(1 for c in coqs if not c.get('withdrawn')))
    for name, table in (('CoQ Register', 'CoQ_Register'), ('iCoA Register', 'iCoA_Register')):
        ws = wb[name]
        end = int(re.search(r'(\d+)$', ws.tables[table].ref).group(1))
        cell = ws.cell(end + 2, 1)
        cell.value = v57 + str(cell.value or '')
        ws.row_dimensions[end + 2].height = max(ws.row_dimensions[end + 2].height or 0, 190)

    # the tracker sheet carries the build's version in its name
    wb['CoQ Parameter Tracker v56'].title = 'CoQ Parameter Tracker v57'
    for row in wb['Reference'].iter_rows():
        for cell in row:
            if cell.value == 'CoQ Parameter Tracker v56':
                cell.value = 'CoQ Parameter Tracker v57'
    for dn in list(wb.defined_names.keys()) if hasattr(wb.defined_names, 'keys') else []:
        d = wb.defined_names[dn]
        if 'v56' in str(d.attr_text):
            d.attr_text = str(d.attr_text).replace('CoQ Parameter Tracker v56', 'CoQ Parameter Tracker v57')
    for sh in wb.worksheets:
        for row in sh.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and "'CoQ Parameter Tracker v56'" in cell.value:
                    cell.value = cell.value.replace("'CoQ Parameter Tracker v56'", "'CoQ Parameter Tracker v57'")
    wb.save(OUT)
    print('written: %s' % os.path.relpath(OUT, GAP))
    print('CoQ Register: %d numbered, %d withdrawn; iCoA Register: %d issued'
          % (n_coq, sum(1 for c in coqs if c.get('withdrawn')), n_icoa))
    print('CoQ References %d rows, Compilation %d × %d, Result Supersession %d'
          % (len(refs), len(wide), len(CCP.DETS), len(sup)))
    for r in report:
        print('   ' + r)
    return 0


def potency_sheet(sh):
    """The Potency Grades tab, as build_tracker_v8.add_potency_sheet lays it out, from the current CSV."""
    import potency_grades as PG
    from openpyxl.styles import Border, Side
    from openpyxl.utils import get_column_letter as L
    thin = Side(style='thin', color='BFBFBF')
    box = Border(left=thin, right=thin, top=thin, bottom=thin)
    fw = Font(name='Calibri', size=8, bold=True, color='FFFFFF')
    f7, f7b = Font(name='Calibri', size=7), Font(name='Calibri', size=7, bold=True)
    cen = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left = Alignment(horizontal='left', vertical='center', wrap_text=True)

    def put(r, c, v, font=f7, fill=None, al=cen):
        cell = sh.cell(r, c, v)
        cell.font, cell.alignment, cell.border = font, al, box
        if fill:
            cell.fill = PatternFill('solid', fgColor=fill)
        return cell

    hdr = [('Strain', 22), ('Abbr.', 7), ('Status', 10), ('Grade nominal (% THC)', 12), ('Tolerance (±%)', 12),
           ('Window low (%)', 12), ('Window high (%)', 12), ('Grades', 8), ('Measured results (n)', 10),
           ('Measured range (%)', 14), ('Basis', 22), ('Measured Total Δ9-THC results, as printed', 60)]
    for i, (t, w) in enumerate(hdr, 1):
        put(1, i, t, fw, '1F3864')
        sh.column_dimensions[L(i)].width = w
    sh.row_dimensions[1].height = 30
    r = 2
    for g in PG.load():
        vals = (g['strain'], g['abbr'], g['status'].title(), float(g['nominal']), float(g['tolerance']),
                float(g['window_low']), float(g['window_high']), int(g['grades_n']), int(g['results_n']),
                g['results_range'], g['basis'], g['measured'])
        for i, v in enumerate(vals, 1):
            c = put(r, i, v, f7b if i == 1 else f7, None, cen if i != 12 else left)
            if i in (4, 5, 6, 7):
                c.number_format = '0.00'
        r += 1
    note = ('Head of QC, 15.09.2026: the potency grades per strain as the potency specification prints them, '
            'corrected to Potency_specifications_25.pdf of 17.09.2026, with the grades set since on the KVM4 potency '
            'builder (WED-II, 26.09.2026) and by the Head of QC (GRC-IV, 7.00 ± 0.70, 27.09.2026; GRC-III, which held '
            'no result, removed under "no empty potency ranges", 07.10.2026). The window is '
            'nominal ± tolerance; a lot\'s grade is the window its Total Δ9-THC result falls in. Source: '
            'potency_grades_2026-09-15.csv. Rebuilt for v57 on %s.' % BUILT)
    sh.merge_cells(start_row=r + 1, start_column=1, end_row=r + 1, end_column=len(hdr))
    put(r + 1, 1, note, Font(name='Calibri', size=6.5, italic=True, color='595959'), 'EFEFEF',
        Alignment(horizontal='left', vertical='top', wrap_text=True))
    sh.row_dimensions[r + 1].height = 60
    sh.auto_filter.ref = 'A1:%s%d' % (L(len(hdr)), r - 1)
    sh.freeze_panes = 'B2'
    return r - 2


if __name__ == '__main__':
    raise SystemExit(main())
