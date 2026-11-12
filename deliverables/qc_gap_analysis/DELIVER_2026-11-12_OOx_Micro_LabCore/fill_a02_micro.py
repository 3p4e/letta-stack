"""Fill the approved-draft QCSOP 019-A02 v02 template (Drive 1kf7rPLGMaqJK0mCkBfpTAJLSh9Y363Dj) for the six LabCore results.
The template is copied unchanged; only empty value cells are written and checkbox controls ticked."""
import copy, docx
from docx.oxml.ns import qn
W14='{http://schemas.microsoft.com/office/word/2010/wordml}'
T='TEMPLATE_QCSOP019-A02_v02.docx'
def tcs(row): return list(row._tr.iter(qn('w:tc')))
def boxes(row): return [s for s in row._tr.iter(qn('w:sdt')) if s.find('.//'+W14+'checkbox') is not None]
def plain(row,i,on=True):
    a,b=('☐','☒') if on else ('☒','☐'); n=-1
    for t in row._tr.iter(qn('w:t')):
        txt=t.text or ''
        for k,ch in enumerate(txt):
            if ch in '☐☒':
                n+=1
                if n==i: t.text=txt[:k]+b+txt[k+1:]; return
    raise IndexError(i)
def setbox(row,i,on=True):
    bx=boxes(row)
    if not bx: return plain(row,i,on)
    s=bx[i]; s.find('.//'+W14+'checked').set(W14+'val','1' if on else '0')
    for t in s.iter(qn('w:t')): t.text=t.text.replace('☐' if on else '☒','☒' if on else '☐')
def rpr_of(tc):
    r=tc.find('.//'+qn('w:r')); p=r.find(qn('w:rPr')) if r is not None else None
    return copy.deepcopy(p) if p is not None else None
def put(row,ci,text,like=0,newpara=False):
    cells=tcs(row); tc=cells[ci]; rp=rpr_of(cells[like])
    ps=tc.findall(qn('w:p'))
    if newpara or (''.join(t.text or '' for t in tc.iter(qn('w:t'))).strip() and ci!=like):
        p=copy.deepcopy(ps[-1]); [p.remove(x) for x in list(p) if x.tag!=qn('w:pPr')]; tc.append(p)
    else: p=ps[0]
    for k,line in enumerate(text.split('\n')):
        r=p.makeelement(qn('w:r'),{})
        if rp is not None: r.append(copy.deepcopy(rp))
        if k: r.append(r.makeelement(qn('w:br'),{}))
        t=r.makeelement(qn('w:t'),{qn('xml:space'):'preserve'}); t.text=line; r.append(t); p.append(r)
NA='N/A — LabCore is the laboratory of the customer (Versa Pharma), not a Purely Plant contract laboratory: no supplier approval, QTA or audit applies.'
B=[
 dict(k='HPA',sev=4,tgt='20 days (HIGH)',prod='CAYN HD 20 % THC / 1 % CBD (Hazy Daze)',sid='VZ26/284 – 1/2 · 000042-V90 · 26-HD-035',test='E. coli',res='Detected in 1 g',lim='Absent in 1 g (Ph. Eur. 5.1.8 C)',pp='P050182 (HPA052501), T2',st='High Pro Amnesia',spec='Absent in 1 g',
  coq='CoQ-PP_26-121 (18.09.2026) carries IPH 948/1686/25 (17.09.2025): E. coli absent, BTGN < 10, TAMC 2.7 × 10⁴, TYMC 2.6 × 10⁴, Salmonella absent. No microbiology since 09.2025 (14 months).',dev='Pathogen indicator detected; our only result (09.2025) absent',orig='Absent'),
 dict(k='CJ',sev=5,tgt='30 days (MEDIUM)',prod='STEADY OGB 24 % THC / 1 % CBD (OG Banana\'s)',sid='VZ26/292 – 1/2 · 000031-V90 · 26-OGB-022',test='Bile-tolerant gram-negative bacteria',res='> 10 000 MPN/g',lim='≤ 10⁴ /g (Ph. Eur. 5.1.8 C)',pp='P050222 (CJ062501/1), T2',st='Cap Junky',spec='≤ 10⁴ /g',
  coq='IPH 1217/2168/25 (01.12.2025): BTGN < 10; IPH 535/1066/26 (31.08.2026, cited on CoQ-PP_26-110): BTGN > 10³ and < 10⁴, TAMC 4.2 × 10³, TYMC < 10, E. coli and Salmonella absent. Rising trend.',dev='Above limit; our last result 10³–10⁴',orig='> 10³, < 10⁴'),
 dict(k='CJ',sev=5,tgt='30 days (MEDIUM)',prod='STEADY OGB 18 % THC / 1 % CBD (OG Banana\'s)',sid='VZ26/304 – 1/2 · 000012-V90 · 26-OGB-049',test='Bile-tolerant gram-negative bacteria',res='> 10 000 MPN/g',lim='≤ 10⁴ /g (Ph. Eur. 5.1.8 C)',pp='P050212 (CJ062501-2), T1',st='Cap Junky',spec='≤ 10⁴ /g',
  coq='IPH 1032/1851/25 (17.10.2025): BTGN > 10³ and < 10⁴, TYMC 4.9 × 10⁴; IPH 534/1065/26 (31.08.2026, cited on CoQ-PP_26-089): BTGN > 10³ and < 10⁴, TAMC 6.2 × 10³, TYMC 2.3 × 10², E. coli and Salmonella absent. Borderline at both tests.',dev='Above limit; our two results just below it',orig='> 10³, < 10⁴'),
]
for b in B:
    d=docx.Document(T); t=d.tables; R=lambda i,j:t[i].rows[j]
    setbox(R(0,1),0); setbox(R(0,1),b['sev'])                       # OOS, MEDIUM (QCSOP 019 §6: external lab OOx)
    put(R(1,0),1,'LabCore d.o.o. (customer’s laboratory)'); put(R(1,0),3,'Dunajska cesta 238e, 1000 Ljubljana, SI')
    put(R(1,1),1,'Not provided'); put(R(1,1),3,'N/A — no contract with PP')
    put(R(1,2),1,'Jaka Štirn, Head of Laboratory'); put(R(1,2),3,'jaka.stirn@labcore.eu'); put(R(1,2),5,'+386 30 920 094')
    put(R(2,1),1,b['prod']); put(R(2,1),3,b['sid']); put(R(2,2),1,b['pp']); put(R(2,2),3,'Dry cannabis flower (delivered product)')
    put(R(2,3),1,b['st']); put(R(2,4),1,'Released, delivered to Versa Pharma')
    put(R(3,0),1,b['test']); put(R(3,0),3,b['res']); put(R(3,1),1,'LabCore method, reference not provided (MPN / Ph. Eur. 2.6.13 to be confirmed)'); put(R(3,1),3,b['lim']+'; ours '+b['spec'])
    put(R(3,2),3,b['dev']); setbox(R(4,0),0)
    put(R(5,0),1,'PP-OOx-2026-'); put(R(5,0),3,'Via Versa Pharma (S. Suljaković) to PP CEO; e-mail M. Šoštarič to LabCore, 12.11.2026'); put(R(5,1),3,b['tgt'])
    for r in (3,4,5,6): setbox(R(6,r),2)
    put(R(7,1),0,NA+' ISO/IEC 17025 accreditation and scope to be requested from LabCore.',newpara=True)
    setbox(R(8,1),2); setbox(R(8,2),0)
    for r in range(3,10): setbox(R(8,r),1)
    put(R(9,1),0,'Result notified by e-mail (12.11.2026). No CoA, raw data, method, media, controls or sample-handling record. Request them with the report due 13.11.2026.',newpara=True)
    setbox(R(10,1),1); setbox(R(10,2),1)
    put(R(11,1),0,'LabCore Phase I laboratory OOS investigation in progress; report announced for 13.11.2026.',newpara=True)
    s=boxes(R(12,1))
    for i in range(len(s)): setbox(R(12,1),i,False)          # template ships "integrity in transport" pre-ticked: cleared, not yet verified
    for r in (7,8,9): setbox(R(12,r),0)
    put(R(13,1),0,'Our accredited results: '+b['coq']+' Three Versa lots reported OOS together (12.11.2026). To check: sampling and aseptic handling, storage and transport conditions, packaging integrity, time since release; retest of the PP retained sample at IPH.',newpara=True)
    put(R(14,1),1,'LabCore'); put(R(14,1),3,b['res']); put(R(14,1),4,b['spec']); put(R(14,1),5,'OOS')
    put(R(14,2),1,'IPH (retained sample)'); put(R(14,2),4,b['spec'])
    put(R(22,1),0,'Batch already released and delivered: the decision is on delivered product (no action / customer notification / market action).',newpara=True)
    for tb,rows in ((23,(1,2,3)),(25,(1,2,3)),(26,(1,))):
        names={1:'Blagoj Nikolov',2:'Jovana Romevska',3:'Sofija Petrova'} if tb!=26 else {1:'Jovana Romevska'}
        for r in rows: put(R(tb,r),1,names[r])
    out=f"QCSOP019-A02_{b['pp'].split()[0]}_{b['k']}_Micro_LabCore.docx"; d.save(out); print(out)
