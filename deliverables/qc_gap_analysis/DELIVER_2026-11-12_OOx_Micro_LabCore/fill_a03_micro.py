"""Fill the QCSOP 019-A03 v02 register template (Drive 1Wh0fgz9MtaQp2h6_MHPKeklq2-Fx40Ub) with the six LabCore OOS events.
Only empty log rows and the Q4 statistics row are written; the template is otherwise unchanged."""
import copy, docx
from docx.oxml.ns import qn
d=docx.Document('TEMPLATE_QCSOP019-A03_v02.docx')
def write(cell,text):
    p=cell.paragraphs[0]._p; ppr=p.find(qn('w:pPr')); mark=ppr.find(qn('w:rPr')) if ppr is not None else None
    r=p.makeelement(qn('w:r'),{})
    if mark is not None: r.append(copy.deepcopy(mark))
    t=r.makeelement(qn('w:t'),{qn('xml:space'):'preserve'}); t.text=text; r.append(t); p.append(r)
ROWS=[
 ('HD 20','P050182','E. coli','Abs/1 g','Det. 1 g','H'),
 ('OGB 24','P050222','BTGN','≤10⁴','>10⁴','M'),
 ('OGB 18','P050212','BTGN','≤10⁴','>10⁴','M'),
]
_OLD=[
 ('GG4 16','P060402','THC','14.4–17.6','19.0'),
 ('PT 10','P060182','THC','9.0–11.0','6.3'),
 ('JD 14','P060412*','THC','12.6–15.4','17.5'),
 ('F1 12','P060062*','THC','10.8–13.2','8.7'),
 ('ACC 12','P060122','THC','10.8–13.2','14.7'),
 ('PDY 14','P060372','THC','12.6–15.4','9.1'),
]
log=d.tables[1]
for i,(prod,batch,test,spec,res,sv) in enumerate(ROWS,1):
    c=log.rows[i].cells
    for j,v in enumerate(['OOx-26-','OOS',sv,'',prod,batch,test,spec,res,'EXT','','','','Deliv.','OPEN','','']):
        if v: write(c[j],v)
stats=d.tables[2]
for r in stats.rows:
    if r.cells[0].text.strip().startswith('Q4'):
        for tt in r.cells[0]._tc.iter(qn('w:t')):
            if '__' in (tt.text or ''): tt.text=tt.text.replace('__','26')
        for j,v in {1:'3',2:'3',6:'1',7:'2',12:'3'}.items(): write(r.cells[j],v)
d.save('QCSOP019-A03_OOx_Register_LabCore_Micro_3_batches.docx'); print('ok')
