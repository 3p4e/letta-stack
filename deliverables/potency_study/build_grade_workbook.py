#!/usr/bin/env python3
"""Render grade_design_even.json into ImB_Potency_Grade_Ranges.xlsx."""
import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

D = json.load(open('grade_design_even.json'))

INK = '1C2426'; HEAD = '175E63'; HEADFILL = PatternFill('solid', fgColor='175E63')
SUB = PatternFill('solid', fgColor='EEF2F1'); WARN = PatternFill('solid', fgColor='FDEBD0')
FULLF = PatternFill('solid', fgColor='E3EFE7')
thin = Side(style='thin', color='C9D2D0')
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
BOLD = Font(bold=True); WHITE = Font(bold=True, color='FFFFFF')
CTR = Alignment(horizontal='center', vertical='center', wrap_text=True)
LFT = Alignment(horizontal='left', vertical='center', wrap_text=True)

wb = openpyxl.Workbook()

# ---------------------------------------------------------------- Sheet 1
ws = wb.active; ws.title = 'Grade Boards'
ws.append(['ImB POTENCY GRADE RANGES — EVEN WHOLE-NUMBER NOMINALS (proposal 27.08.2026)'])
ws['A1'].font = Font(bold=True, size=13)
ws.append(['Rules: nominal = whole even number (adjacent odd only where symmetry is impossible); '
           'tolerance EQUAL above and below the nominal, at most 10% of it; two-decimal bounds; '
           'no overlap; contiguous ladders; strongest grade takes the maximum range first; '
           'every batch falls in exactly one grade.'])
ws['A2'].alignment = LFT
ws.append([])
hdr = ['Strain', 'Code', 'Grade', 'Product Code', 'Spec. Doc. Code', 'Nominal %', 'Tolerance %',
        'Lower %', 'Upper %', 'Width pp', 'Potency expression', 'Range status',
        'Batches (latest Total THC %)']
ws.append(hdr)
hr = ws.max_row
for c in range(1, len(hdr) + 1):
    cell = ws.cell(hr, c); cell.font = WHITE; cell.fill = HEADFILL; cell.alignment = CTR; cell.border = BORDER
for strain, entry in D['strains'].items():
    first = True
    for g in entry:
        bl = ', '.join(f"{b['batch']} {b['v']:.2f}" for b in g['batches']) \
             or '— reserve grade (no current batch)'
        status = 'FULL ±10%' if g['full'] else 'clipped (contiguity rule)'
        if g.get('bridge'): status = 'RESERVE (contiguity bridge)'
        if g.get('odd'): status += ' — ODD nominal (fallback rule 5)'
        tol = (f"±{g['plus_tol']:.2f}" if g['symmetric']
               else f"+{g['plus_tol']:.2f} / −{g['minus_tol']:.2f}")
        ws.append([strain if first else '', g['strain_code'] if first else '', g['grade'],
                   g['product_code'].replace(':', ' : '), g['spec_code'], g['nominal'], tol,
                   g['lower'], g['upper'], g['width'], g['expression'], status, bl])
        r = ws.max_row
        for c in range(1, len(hdr) + 1):
            cell = ws.cell(r, c); cell.border = BORDER
            cell.alignment = LFT if c in (1, 11, 13) else CTR
        for c in (6, 8, 9, 10):
            ws.cell(r, c).number_format = '0.00'
        ws.cell(r, 12).fill = FULLF if g['full'] else SUB
        if first:
            ws.cell(r, 1).font = BOLD
        first = False
widths = [22, 6, 7, 20, 18, 10, 14, 9, 9, 9, 40, 24, 66]
for i, w in enumerate(widths, 1):
    ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
ws.freeze_panes = 'A5'

# ---------------------------------------------------------------- Sheet 2
ws2 = wb.create_sheet('Batch Assignments')
hdr2 = ['Batch', 'Strain', 'Grade', 'Product Code', 'Total THC %', 'Basis / source',
        'Owner-requested code', 'Note']
ws2.append(hdr2)
for c in range(1, len(hdr2) + 1):
    cell = ws2.cell(1, c); cell.font = WHITE; cell.fill = HEADFILL; cell.alignment = CTR; cell.border = BORDER
owner_note = {f.split('/ ')[1].split(':')[0].strip(): f for f in D['flags'] if 'owner code' in f}
for strain, entry in D['strains'].items():
    for g in entry:
        for b in g['batches']:
            note = ''
            if b['basis'].startswith('declared'):
                note = 'declared value — no eCoA yet, grade provisional until tested'
            if not b['owner_req'] and not note:
                note = 'code assigned by value (batch not on the tranche list)'
            if b['batch'] in owner_note:
                note = 'owner code THC12 infeasible for audited 13.33 — moved to THC14'
            ws2.append([b['batch'], strain, g['grade'], g['product_code'].replace(':', ' : '),
                        b['v'], b['src'], 'yes' if b['owner_req'] else '—', note])
            r = ws2.max_row
            for c in range(1, len(hdr2) + 1):
                cell = ws2.cell(r, c); cell.border = BORDER
                cell.alignment = CTR if c in (3, 5, 7) else LFT
            ws2.cell(r, 5).number_format = '0.00'
            if note and 'infeasible' in note:
                for c in range(1, len(hdr2) + 1):
                    ws2.cell(r, c).fill = WARN
for i, w in enumerate([16, 20, 7, 20, 11, 46, 12, 52], 1):
    ws2.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
ws2.freeze_panes = 'A2'

# ---------------------------------------------------------------- Sheet 3
ws3 = wb.create_sheet('Notes & Exceptions')
rows = [
 ('DESIGN RULES', ''),
 ('1', 'Nominal potency of every grade is a whole EVEN number (…8, 10, 12 … 26), printed in the '
       'product code as THCnn : CBD1 and shown on the specification as nn.00 %.'),
 ('2', 'A grade range never extends more than 10% of the nominal to either side '
       '(lower >= 0.90 x nominal, upper <= 1.10 x nominal). Bounds carry two decimals.'),
 ('3', 'SYMMETRIC tolerance (management rule, 27.08.2026): every grade is nominal ± t with the '
       'SAME t above and below, so the window is always centred on the nominal. Contiguity then '
       'binds neighbouring grades by the equality t_upper + t_lower = (N_upper - N_lower) - 0.01, '
       'which chains every tolerance to the top grade of the ladder.'),
 ('4', 'Ranges within one strain do not overlap; the strongest grade is given the maximum '
       'tolerance the chain allows first, each weaker grade takes what the equalities leave.'),
 ('5', 'Every batch of the strain falls inside exactly one grade window at its latest certified '
       'Total THC value (retest = CoQ-forming; superseded pre-retest results are out of scope).'),
 ('6', 'Contiguity: from the top grade down, consecutive ranges join at 0.01. RESERVE grades '
       '(spec-defined, no current batch) close spans that batch-bearing grades cannot bridge. '
       'Sole exception below 10% THC where no meaningful symmetric ladder joins: the lowest '
       'grade(s) sit with a documented uncovered zone (GRC 7.71-10.79; OPM 8.81-9.10).'),
 ('7', 'ODD-nominal adjustment (management rule, 27.08.2026): where the initially selected even '
       'nominal cannot carry a symmetric window under rules 2-6, the nominal shifts to the '
       'adjacent odd whole number (above or below). Also covers isolated results in the even '
       'ladder dead zones (GRC_THC7). No grade tolerance is allowed below 0.50 (a 0.40pp-wide '
       'grade is not a meaningful specification).'),
 ('', ''),
 ('FLAGS', ''),
]
for f in D['flags']: rows.append(('•', f))
if not D['flags']: rows.append(('•', 'none'))
rows.append(('', ''))
rows.append(('EXCEPTIONS', ''))
for e in D['exceptions']: rows.append(('•', e))
if not D['exceptions']: rows.append(('•', 'none — the odd-nominal fallback (rule 5) resolves all former dead-zone cases'))
rows += [
 ('', ''),
 ('OPEN VERIFICATIONS CARRIED OVER', ''),
 ('•', 'BSS052501: 20.39 (PP QCCoA 001v02) vs 20.47 on the owner sheet (unreadable NGP scan) — '
       'grade THC20 holds under either value; paper check pending.'),
 ('•', 'OMP1024_01: 15.38 correction (cert ППК25117 prints 1.58 — printing anomaly) — VERIFY ON '
       'PAPER ORIGINAL; grade THC16 assumes 15.38.'),
 ('•', 'GG1024_02: 15.95 correction (cert ППК25140 prints 15.59) — VERIFY ON PAPER ORIGINAL; '
       'grade THC16 holds under either value.'),
 ('•', 'GP062501: PP cert prints 24.89 vs owner sheet 22.89 — grade THC24 holds under either value.'),
 ('•', 'J31122501 graded on the machine-trimmed CoQ-forming preparation (21.84, CoQ-PP-2026-0054); '
       'the hand-trimmed 19.84 result is experimental only.'),
 ('•', 'Truth-check finding (27.08.2026): certificate ППК26065 (13.93, CNP, 11.05.2026) prints '
       'серија JD112501* — the milled Jelly Donutz presentation, a separate register batch — and was '
       'misattributed to JD112501 (whole flower, retest 20.32) in the source dataset. Reattributed; '
       'JD112501* now carries its own grade JD_THC14:CBD1 (12.60 — 14.39).'),
 ('•', 'Batches on declared values (no eCoA yet): ACC102501, CC012603, CF102501, JD012603/01, '
       'PUM102501 (T2 re-analysis sampled 12.08.2026, results pending), SCR012601, WED102501, '
       'JD022601, GRC102501/1, P160012, P160022, P160032 — their grades are provisional.'),
]
for a, b in rows:
    ws3.append([a, b])
    r = ws3.max_row
    ws3.cell(r, 1).font = BOLD if a and a not in '•' else Font()
    ws3.cell(r, 2).alignment = LFT
ws3.column_dimensions['A'].width = 26
ws3.column_dimensions['B'].width = 130

wb.save('ImB_Potency_Grade_Ranges.xlsx')
n_g = sum(len(e) for e in D['strains'].values())
n_b = sum(len(g['batches']) for e in D['strains'].values() for g in e)
print(f"saved: {len(D['strains'])} strains, {n_g} grades, {n_b} batches")
