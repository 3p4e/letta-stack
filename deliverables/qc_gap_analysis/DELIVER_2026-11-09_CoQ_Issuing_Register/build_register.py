import json,csv,re,datetime as dt,collections
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.utils import get_column_letter
reg=json.load(open('coq_artifact_data.json'))['coqs']
scan={r['coq_code']:r for r in csv.DictReader(open('tracker/SCAN_INDEX_2026-09-25.tsv',encoding='utf-8'),delimiter='\t')}
signed=set(json.load(open('tracker/SIGNED_T3_2026-10-16.json')))|{'CoQ-PP_26-163'}
order={r['number']:r for r in csv.DictReader(open('tracker/ISSUANCE_ORDER_CHECK_2026-10-08.tsv',encoding='utf-8'),delimiter='\t')}
n=lambda s:re.sub(r'[^A-Z0-9]','',(s or '').upper())
tr={}
for r in csv.DictReader(open('tranche_assignment_2026-09-18.csv',encoding='utf-8')):
    tr[n(r['batch'])]=r['tranche']
    if r['p_lot']: tr[r['p_lot']]=r['tranche']
AL={'CJ0525012':'CJ052501_02','BSS102401':'BSS1024_01_1','GRC1025011':'GRC102501','GRC1025012':'GRC102501','JD01260301':'JD012603','JD01260302':'JD012603','JD01260302V':'JD012603'}
def tranche(c):
    t=tr.get(c.get('pp')) or tr.get(n(c.get('cb'))) or tr.get(n(AL.get(n(c.get('cb')),'')))
    return 'T'+t if t else 'outside'
def d(s):
    try: return dt.datetime.strptime(s,'%d.%m.%Y')
    except Exception: return None
rows=[]
for c in reg:
    code=c['regcode'][:13]; num=int(code[-3:]); t=tranche(c); sc=scan.get(code)
    issue=(sc or {}).get('issued') or c.get('issue') or ''
    if c.get('withdrawn'): st='WITHDRAWN — number free, no certificate'
    elif sc: st='ISSUED — sent to customer (approved scan)'
    elif t in ('T1','T2'): st='ISSUED — sent to customer'
    elif code in signed: st='SIGNED'+(' (re-signed after #234)' if code=='CoQ-PP_26-163' else ' (scanned 16.10.2026)')
    else: st='NOT YET SIGNED'
    sup=c.get('supersedes') or {}
    ver='v2 (supersedes '+sup['code']+' of '+sup.get('date','')+')' if sup.get('code') else 'v1'
    if sc and sc.get('supersedes'): ver='v2 (supersedes '+sc['supersedes']+' of '+sc.get('supersedes_issued','')+')'
    icoa=(sc or {}).get('icoa_cited') or (c.get('icoa_code') if c.get('icoa_code') and 'assigned' not in c.get('icoa_code') else '')
    o=order.get('-%03d'%num,{})
    rows.append([num,code,issue,c.get('pp') or '',c.get('cb') or '',c.get('strain') or '',c.get('pcode') or '',c.get('spec') or '',ver,icoa,t,st,'scan' if sc else 'register',('out of date order — '+o.get('status','')) if o else ''])
rows.sort(key=lambda r:r[0])
H=['No.','CoQ code','Issue date','Production batch','Cultivation batch','Strain','Product code','Specification','Version','iCoA cited','Tranche','Status','Date source','Order check (with Head of QC)']
wb=Workbook()
def sheet(ws,data,title):
    ws.title=title; ws.append(H)
    for r in data: ws.append(r)
    for c in ws[1]: c.font=Font(bold=True,color='FFFFFF'); c.fill=PatternFill('solid',fgColor='2B547E'); c.alignment=Alignment(wrap_text=True,vertical='center')
    for i,w in enumerate([6,15,11,12,14,18,16,24,30,15,9,36,10,30],1): ws.column_dimensions[get_column_letter(i)].width=w
    ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions
    for row in ws.iter_rows(min_row=2):
        if str(row[11].value).startswith('WITHDRAWN'):
            for c in row: c.font=Font(color='999999',strike=True)
sheet(wb.active,rows,'By number')
chron=sorted([r for r in rows if not r[11].startswith('WITHDRAWN')],key=lambda r:(d(r[2]) or dt.datetime(2100,1,1),r[0]))
sheet(wb.create_sheet(),chron,'Chronological')
ws=wb.create_sheet('Notes')
for line in ['Source: register coq_artifact_data.json; issue date from the approved scan where one exists (SCAN_INDEX_2026-09-25), else the register (scans govern, CLAUDE.md §1).',
 'Status: T1/T2 = issued and sent (frozen); T3 retests signed 16.10.2026 (SIGNED_T3) and -163 re-signed (scan 20261028131459); all others not yet signed.',
 'Withdrawn numbers carry no certificate. CoQ-PP_26-173 is reserved for JD032601 (P060472), not built.',
 "Order check: numbers out of date order per ISSUANCE_ORDER_CHECK_2026-10-08; renumbering is the Head of QC's decision.",
 "CoQ issue dates are the register's, not signing dates (Head of QC, 28.10.2026, #235)."]: ws.append([line])
ws.column_dimensions['A'].width=160
wb.save('DELIVER_2026-11-09_CoQ_Issuing_Register/CoQ_Issuing_Register_2026-11-09.xlsx')
print(len(rows),collections.Counter(r[11].split(' (')[0].split(' —')[0] for r in rows),'dates missing:',sum(1 for r in rows if not d(r[2])),'order flags:',sum(1 for r in rows if r[13]))
print('first/last chronological:',chron[0][:3],chron[-1][:3])
