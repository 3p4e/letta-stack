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
ws.append(['Rules: nominal = whole even number; range <= 10% of nominal each side; two-decimal bounds; '
           'no overlap within a strain; strongest grade takes the maximum range first; '
           'every batch falls in exactly one grade.'])
ws['A2'].alignment = LFT
ws.append([])
hdr = ['Strain', 'Code', 'Grade', 'Product Code', 'Spec. Doc. Code', 'Nominal %',
        'Lower %', 'Upper %', 'Width pp', 'Range status', 'Batches (latest Total THC %)']
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
        ws.append([strain if first else '', g['strain_code'] if first else '', g['grade'],
                   g['product_code'].replace(':', ' : '), g['spec_code'], g['nominal'],
                   g['lower'], g['upper'], g['width'], status, bl])
        r = ws.max_row
        for c in range(1, len(hdr) + 1):
            cell = ws.cell(r, c); cell.border = BORDER
            cell.alignment = LFT if c in (1, 11) else CTR
        for c in (6, 7, 8, 9):
            ws.cell(r, c).number_format = '0.00'
        ws.cell(r, 10).fill = FULLF if g['full'] else SUB
        if first:
            ws.cell(r, 1).font = BOLD
        first = False
widths = [22, 6, 7, 20, 18, 10, 9, 9, 9, 22, 78]
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
 ('3', 'Ranges within one strain do not overlap. The strongest grade is given the maximum range '
       'first; each weaker grade takes the widest window that remains. Where an even nominal two '
       'steps down must still contain its own nominal value, the stronger grade cedes the minimum '
       'necessary from the bottom of its window (this is why some strong-grade lower bounds sit '
       'above 0.90 x nominal).'),
 ('4', 'Every batch of the strain falls inside exactly one grade window at its latest certified '
       'Total THC value (register CoQ-forming value).'),
 ('5', 'Retest results are the CoQ-forming anchors (management rule, 27.08.2026): where a batch '
       'has a retest (Tranche 1 197-series of 07.08.2026, the April J31 retests, and the pending '
       'Tranche 2 re-analysis when it lands), the grade is designed on the retest value; '
       'superseded pre-retest results are out of specification scope.'),
 ('6', 'Contiguity (management rule, 27.08.2026): from the top grade down, consecutive grade '
       'ranges join without gap or overlap (upper of the weaker = lower of the stronger minus '
       '0.01). Where batch-bearing grades cannot join directly, RESERVE grades (spec-defined, '
       'no current batch) are inserted to close the span. Sole exception: below 10% THC, where '
       'the ladder mathematically cannot join, the lowest grade(s) may sit with a documented '
       'uncovered zone above them (GRC 7.71-10.79; OPM 8.81-8.99).'),
 ('7', 'ODD-nominal fallback (management rule, 27.08.2026): an isolated result that no even '
       'nominal can hold within ±10% (the even ladder has dead zones at 6.61–7.19 and 8.81–8.99) '
       'takes the adjacent ODD whole-number nominal instead, formed without overlap against the '
       'neighbouring ranges. With this fallback every result above ≈5.0% THC is always placeable '
       '(for any value v, at least one whole number lies between v/1.1 and v/0.9 once v ≥ 5).'),
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
