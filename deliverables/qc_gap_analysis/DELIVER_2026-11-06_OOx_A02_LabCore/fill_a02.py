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
 dict(k='GG4',prod='STEADY GG4 16 % THC / 1 % CBD',sid='VZ26/259 – 2/2 · 000015-V90 · 26-GG4-006',res='19.0 % w/w total Δ9-THC',lim='16 ± 10 %: 14.4–17.6 % (customer)',pp='P060402 (GG012603), T1',st='Gorilla Glue',spec='GG-I 16.23–19.76 %',coq='CoQ-PP_26-092 (17.08.2026): 16.70 % — Farmahem 197-8-К/26 (07.08.2026); CoQ-PP_26-077 (07.07.2026): 17.59 % — CNP ППК26114',dev='+2.3 points vs our CoQ; outside the customer limit, within our specification GG-I',alt=''),
 dict(k='PT',prod='STEADY PT 10 % THC / 1 % CBD (Plum Tarte)',sid='VZ26/260 – 2/2 · 000041-V90 · 26-PT-034',res='6.3 % w/w total Δ9-THC',lim='10 ± 10 %: 9.0–11.0 % (customer)',pp='P060182 (GRC102501/2), T2',st='Grapes and Cream',spec='GRC-II 9.00–10.99 %',coq='CoQ-PP_26-120 (18.09.2026): 9.80 % — Farmahem 220-14-К/26 (25.08.2026); CoQ-PP_26-054 (06.06.2026): 11.53 % — Farmahem 051-6-К/26',dev='−3.5 points (−36 %) vs our CoQ; outside both limits',alt=''),
 dict(k='JD',prod='CAYN JD 14 % THC / 1 % CBD (Jelly Donuts)',sid='VZ26/273 – 2/2 · 000044-V90 · 26-JD-037',res='17.5 % w/w total Δ9-THC',lim='14 ± 10 %: 12.6–15.4 % (customer)',pp='P060412 (JD012603/02), T2',st='Jelly Donuts',spec='JD-III 13.80–16.19 %',coq='CoQ-PP_26-123 (18.09.2026): 14.43 % — Farmahem 220-17-К/26 (26.08.2026); CoQ-PP_26-078 (07.07.2026): 20.54 % — CNP ППК26113',dev='+3.1 points (+21 %) vs our CoQ; outside both limits',alt='Batch to be confirmed by the customer: P060422 (JD012603/02V, CoQ-PP_26-124: 17.09 %) is the other T2 Jelly Donuts lot.'),
 dict(k='F1',prod='STEADY F1 12 % THC / 1 % CBD (Formula 1)',sid='VZ26/263 – 2/2 · 000027-V90 · 26-FO1-018',res='8.7 % w/w total Δ9-THC',lim='12 ± 10 %: 10.8–13.2 % (customer)',pp='P060062 (PM092501), T1',st='Permanent Marker',spec='PM-II 11.00–12.99 %',coq='CoQ-PP_26-104 (17.08.2026): 12.25 % — Farmahem 197-20-К/26 (07.08.2026); CoQ-PP_26-042 (06.06.2026): 14.06 % — CNP ППК26004',dev='−3.6 points (−29 %) vs our CoQ; outside both limits',alt='Batch to be confirmed by the customer: P050272 (PM072501, T3, "STEADY F1 12/1" on the Versa list; CoQ-PP_26-159: 12.77 %) carries the same product name.'),
 dict(k='ACC',prod='STEADY Amnesia Core 12 % THC / 1 % CBD',sid='VZ26/264 – 2/2 · 000029-V90 · 26-ACC-020',res='14.7 % w/w total Δ9-THC',lim='12 ± 10 %: 10.8–13.2 % (customer)',pp='P060122 (ACC102501), T2',st='Amnesia Core Cut',spec='ACC-I 10.80–13.19 %',coq='CoQ-PP_26-106 (18.09.2026): 12.09 % — Farmahem 220-1-К/26 (25.08.2026); CoQ-PP_26-048 (06.06.2026): 12.91 % — Farmahem 031-5-К/26',dev='+2.6 points (+22 %) vs our CoQ; outside both limits',alt=''),
 dict(k='PDY',prod='STEADY PDY 14 % THC / 1 % CBD (Payday)',sid='VZ26/267 – 2/2 · 000034-V90 · 26-PD-025',res='9.1 % w/w total Δ9-THC',lim='14 ± 10 %: 12.6–15.4 % (customer)',pp='P060372 (CC012603), T2',st='Cash Cow',spec='CC-II 12.65–15.34 %',coq='CoQ-PP_26-108 (18.09.2026): 14.76 % — Farmahem 220-29-К/26 (26.08.2026)',dev='−5.7 points (−38 %) vs our CoQ; outside both limits',alt=''),
]
for b in B:
    d=docx.Document(T); t=d.tables; R=lambda i,j:t[i].rows[j]
    setbox(R(0,1),0); setbox(R(0,1),5)                       # OOS, MEDIUM (QCSOP 019 §6: external lab OOx)
    put(R(1,0),1,'LabCore d.o.o. (customer’s laboratory)'); put(R(1,0),3,'Dunajska cesta 238e, 1000 Ljubljana, SI')
    put(R(1,1),1,'Not provided'); put(R(1,1),3,'N/A — no contract with PP')
    put(R(1,2),1,'Jaka Štirn, Head of Laboratory'); put(R(1,2),3,'jaka.stirn@labcore.eu'); put(R(1,2),5,'+386 30 920 094')
    put(R(2,1),1,b['prod']); put(R(2,1),3,b['sid']); put(R(2,2),1,b['pp']); put(R(2,2),3,'Dry cannabis flower (delivered product)')
    put(R(2,3),1,b['st']); put(R(2,4),1,'Released, delivered to Versa Pharma')
    put(R(3,0),1,'Total Δ9-THC'); put(R(3,0),3,b['res']); put(R(3,1),1,'LC — LabCore method, reference not provided'); put(R(3,1),3,b['lim']+'; ours '+b['spec'])
    put(R(3,2),3,b['dev']); setbox(R(4,0),0)
    put(R(5,0),1,'PP-OOx-2026-'); put(R(5,0),3,'Via Versa Pharma (S. Suljaković) to PP CEO; results table'); put(R(5,1),3,'30 days (MEDIUM)')
    for r in (3,4,5,6): setbox(R(6,r),2)
    put(R(7,1),0,NA+' ISO/IEC 17025 accreditation and scope to be requested from LabCore.',newpara=True)
    setbox(R(8,1),2); setbox(R(8,2),0)
    for r in range(3,10): setbox(R(8,r),1)
    put(R(9,1),0,'Results received as a summary table (VZ26/259–273). No CoA, raw data, chromatograms, method, standards or SST data. Request them from LabCore.',newpara=True)
    setbox(R(10,1),1); setbox(R(10,2),1)
    put(R(11,1),0,'No investigation received. On 05.11.2026 LabCore (J. Štirn) asked PP about sample preparation: test portion, homogenisation, extraction.',newpara=True)
    s=boxes(R(12,1))
    for i in range(len(s)): setbox(R(12,1),i,False)          # template ships "integrity in transport" pre-ticked: cleared, not yet verified
    for r in (7,8,9): setbox(R(12,r),0)
    put(R(13,1),0,'Our accredited results conform: '+b['coq']+'. Six T1/T2 lots reported OOS together (2.3–5.7 points from our results), three high and three low. To check: reporting basis (dry mass / as received), sample preparation, storage at the customer. '+b['alt'],newpara=True)
    put(R(14,1),1,'LabCore'); put(R(14,1),3,b['res'].split(' %')[0]+' %'); put(R(14,1),4,b['lim'].split(': ')[1].split(' (')[0]); put(R(14,1),5,'OOS')
    put(R(14,2),1,'Farmahem (retained sample)'); put(R(14,2),4,b['spec'].split(' ',1)[1])
    put(R(22,1),0,'Batch already released and delivered: the decision is on delivered product (no action / customer notification / market action).',newpara=True)
    for tb,rows in ((23,(1,2,3)),(25,(1,2,3)),(26,(1,))):
        names={1:'Blagoj Nikolov',2:'Jovana Romevska',3:'Sofija Petrova'} if tb!=26 else {1:'Jovana Romevska'}
        for r in rows: put(R(tb,r),1,names[r])
    out=f"QCSOP019-A02_{b['pp'].split()[0]}_{b['k']}_LabCore.docx"; d.save(out); print(out)
