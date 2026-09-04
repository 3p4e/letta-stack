#!/usr/bin/env python3
"""Workbook -> v9_data.json for the artifact (coverage, parameters, lots with their
two-row blocks, work order, credit audit, credit corrections). Reads the rendered
sheet, so what the page shows is what the workbook shows."""
import sys, json, re, openpyxl

SRC = sys.argv[1]
OUT = sys.argv[2]
SHEET = sys.argv[3] if len(sys.argv) > 3 else 'CoQ Parameter Tracker v9'
STATE = {'C6EFCE': 'ok', 'FCE5CD': 'stab', 'FDE9D9': 'silent', 'F4CCCC': 'missing', 'EDEDED': 'extra'}
wb = openpyxl.load_workbook(SRC)


def rgb(cell):
    c = cell.fill.fgColor.rgb if cell.fill and cell.fill.fill_type == 'solid' else None
    return (c[-6:] if isinstance(c, str) else None)


def fcol(cell):
    c = cell.font.color.rgb if cell.font and cell.font.color else None
    return (c[-6:] if isinstance(c, str) else None)


def table(name):
    ws = wb[name]
    hdr = [str(c.value or '').strip() for c in ws[1]]
    rows = []
    for r in range(2, ws.max_row + 1):
        vals = [ws.cell(r, c).value for c in range(1, len(hdr) + 1)]
        if not any(v not in (None, '') for v in vals[:3]):
            continue
        if len(hdr) >= 9 and str(vals[0] or '').startswith('These corrections'):
            continue
        d = {}
        for h, v in zip(hdr, vals):
            if h:
                d[h] = v.strftime('%d.%m.%Y') if hasattr(v, 'strftime') else ('' if v is None else str(v))
        rows.append(d)
    return rows


# ---- coverage
cov = wb['Batch Coverage']
coverage_headers = [str(c.value or '') for c in cov[1]][:20]
coverage = []
for r in range(2, cov.max_row + 1):
    if not cov.cell(r, 1).value:
        continue
    coverage.append([('' if cov.cell(r, c).value is None else str(cov.cell(r, c).value)) for c in range(1, 21)])

# ---- tracker layout
ws = wb[SHEET]
maxc = ws.max_column
starts = [c for c in range(4, maxc + 1) if str(ws.cell(2, c).value or '').startswith('#')]
params = []
for i, s in enumerate(starts):
    e = (starts[i + 1] - 1) if i + 1 < len(starts) else max(c for c in range(s, maxc + 1) if ws.cell(4, c).value)
    title, method = (str(ws.cell(2, s).value) + '\n').split('\n')[:2]
    if str(ws.cell(4, s).value or '').startswith('Result'):
        params.append({'n': int(re.match(r'#(\d+)', title).group(1)), 'title': title.strip(), 'method': method.strip(),
                       'single': True, 'subs': None, 'ac': str(ws.cell(3, s).value or '').replace('A.C.: ', ''),
                       'start': s, 'end': e})
    else:
        subs = [str(ws.cell(4, c).value) for c in range(s, e)]
        params.append({'n': int(re.match(r'#(\d+)', title).group(1)), 'title': title.strip(), 'method': method.strip(),
                       'single': False, 'subs': subs,
                       'ac': [str(ws.cell(3, c).value or '').replace('A.C.: ', '') for c in range(s, e)],
                       'start': s, 'end': e})

# ---- lots and blocks
anchors = [r for r in range(5, ws.max_row + 1) if ws.cell(r, 1).value not in (None, '')]
lots = []
for i, a in enumerate(anchors):
    last = (anchors[i + 1] - 1) if i + 1 < len(anchors) else ws.max_row
    while last > a and not any(ws.cell(last, c).value not in (None, '') for c in range(1, maxc + 1)):
        last -= 1
    lot = {'cu': str(ws.cell(a, 1).value), 'p': str(ws.cell(a, 2).value or ''), 'status': str(ws.cell(a, 3).value or ''), 'blocks': []}
    for top in range(a, last + 1, 2):
        bot = top + 1
        blk = []
        for p in params:
            s, e = p['start'], p['end']
            if p['single']:
                cell = ws.cell(top, s)
                st = STATE.get(rgb(cell), 'none')
                res = '' if cell.value is None else str(cell.value)
                ref = '' if ws.cell(top, s + 1).value is None else str(ws.cell(top, s + 1).value)
                mark = '' if ws.cell(top, e).value is None else str(ws.cell(top, e).value)
                if st == 'none' and not res and not ref:
                    blk.append({'res': '', 'ref': '', 'st': 'none', 'mark': '', 'verdict': ''}); continue
                v = 'oos' if (st in ('ok', 'stab') and fcol(cell) == '9C0006') else ('und' if fcol(cell) == 'B45F06' else '')
                blk.append({'res': res, 'ref': ref, 'st': st, 'mark': mark, 'verdict': v})
            else:
                cells = [ws.cell(top, c) for c in range(s, e)]
                st = STATE.get(rgb(cells[0]), 'none')
                vals = ['' if c.value is None else str(c.value) for c in cells]
                ref = '' if ws.cell(bot, s).value is None else str(ws.cell(bot, s).value)
                mark = '' if ws.cell(top, e).value is None else str(ws.cell(top, e).value)
                if st == 'none' and not any(vals) and not ref:
                    blk.append({'vals': [''] * len(vals), 'ref': '', 'st': 'none', 'mark': '', 'verdicts': [''] * len(vals)}); continue
                verdicts = ['oos' if (st in ('ok', 'stab') and fcol(c) == '9C0006') else ('und' if fcol(c) == 'B45F06' else '') for c in cells]
                blk.append({'vals': vals, 'ref': ref, 'st': st, 'mark': mark, 'verdicts': verdicts})
        if any(b['st'] != 'none' for b in blk):
            lot['blocks'].append(blk)
    lots.append(lot)

data = {'coverage_headers': coverage_headers, 'coverage': coverage,
        'params': [{k: v for k, v in p.items() if k not in ('start', 'end')} for p in params],
        'lots': lots, 'work_order': table('Work Order'), 'credit_audit': table('Credit Audit'),
        'corrections': table('Credit Corrections')}
json.dump(data, open(OUT, 'w'), ensure_ascii=False)
print('lots', len(lots), 'blocks', sum(len(l['blocks']) for l in lots), 'coverage rows', len(coverage),
      'work order', len(data['work_order']), 'audit', len(data['credit_audit']), 'corrections', len(data['corrections']))
