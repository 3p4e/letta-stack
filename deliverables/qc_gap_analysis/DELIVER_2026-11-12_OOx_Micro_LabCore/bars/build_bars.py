import math,html
LIM={'TAMC':5e5,'TYMC':5e4,'BTGN':1e4}
# value: number used for bar (upper bound for ranges), label
def row(cert,date,tamc,tymc,btgn,ec,sal,src='IPH'):
    return dict(cert=cert,date=date,TAMC=tamc,TYMC=tymc,BTGN=btgn,EC=ec,SAL=sal,src=src)
N=lambda v,l:(v,l)
B=[
 ('P050182 · HPA052501 · 26-HD-035','Microbiology OOS — E. coli detected (LabCore)',[
   row('948/1686/25','17.09.2025',N(2.7e4,'2.7 × 10⁴'),N(2.6e4,'2.6 × 10⁴'),N(10,'< 10'),'A','A'),
   row('LabCore','12.11.2026',None,None,None,'D',None,'LC')]),
 ('P050222 · CJ062501/1 · 26-OGB-022','Microbiology OOS — BTGN > 10⁴ (LabCore)',[
   row('1217/2168/25','01.12.2025',N(10,'< 10'),N(20,'20'),N(10,'< 10'),'A','A'),
   row('535/1066/26','31.08.2026',N(4.2e3,'4.2 × 10³'),N(10,'< 10'),N(1e4,'10³–10⁴'),'A','A'),
   row('LabCore','12.11.2026',None,None,N(1e5,'> 10⁴ MPN'),None,None,'LC')]),
 ('P050212 · CJ062501/2 · 26-OGB-049','Microbiology OOS — BTGN > 10⁴ (LabCore)',[
   row('1032/1851/25','17.10.2025',N(2.2e4,'2.2 × 10⁴'),N(4.9e4,'4.9 × 10⁴'),N(1e4,'10³–10⁴'),'A','A'),
   row('534/1065/26','31.08.2026',N(6.2e3,'6.2 × 10³'),N(2.3e2,'2.3 × 10²'),N(1e4,'10³–10⁴'),'A','A'),
   row('LabCore','12.11.2026',None,None,N(1e5,'> 10⁴ MPN'),None,None,'LC')]),
]
def col(p): return '#2e9e5b' if p<=75 else ('#e0a100' if p<=100 else '#d0342c')
def bar(k,v):
    if v is None: return '<td class="na">—</td>'
    x,l=v; lim=LIM[k]
    p=100*math.log10(max(x,1))/math.log10(lim)   # log scale, 100 % = limit
    over=x>lim; w=min(p,100); c=col(101 if over else p)
    return f'<td><div class="b"><i style="width:{w:.0f}%;background:{c}"></i><span>{html.escape(l)}</span></div></td>'
def qual(v):
    if v is None: return '<td class="na">—</td>'
    if v=='A': return '<td><div class="b"><i style="width:4%;background:#2e9e5b"></i><span>Absent</span></div></td>'
    return '<td><div class="b"><i style="width:100%;background:#d0342c"></i><span class="w">Detected</span></div></td>'
rows=''
for name,why,rs in B:
    rows+=f'<tr class="g"><td colspan="6"><b>{name}</b> <em>{why}</em></td></tr>'
    for r in rs:
        cls=' class="lc"' if r['src']=='LC' else ''
        rows+=f'<tr{cls}><td class="c">{r["cert"]}<br><small>{r["date"]}</small></td>'+bar('TAMC',r['TAMC'])+bar('TYMC',r['TYMC'])+bar('BTGN',r['BTGN'])+qual(r['EC'])+qual(r['SAL'])+'</tr>'
H=f'''<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:A4 portrait;margin:12mm 11mm}}
body{{font-family:Calibri,'Carlito',sans-serif;font-size:9pt;color:#1d2a33}}
h1{{font-size:14pt;margin:0 0 2pt;color:#0f5132}} .sub{{color:#555;margin:0 0 6pt}}
table{{width:100%;border-collapse:collapse;table-layout:fixed}}
th{{background:#0f5132;color:#fff;font-weight:600;padding:3pt;font-size:8.5pt}} th small{{font-weight:400;opacity:.85}}
td{{border-bottom:.5pt solid #d6dde2;padding:2pt 3pt;vertical-align:middle}}
td.c{{font-size:8pt}} td.na{{text-align:center;color:#999}}
tr.g td{{background:#eef4f0;padding:3pt;border-top:1pt solid #0f5132}} tr.g em{{color:#a33;font-style:normal;margin-left:6pt}}
tr.lc td{{background:#fff4f2}}
.b{{position:relative;height:13pt;background:#f1f3f5;border-radius:2pt;overflow:hidden}}
.b i{{position:absolute;left:0;top:0;bottom:0;border-radius:2pt}}
.b span{{position:relative;padding-left:3pt;line-height:13pt;font-size:8pt;font-weight:600}} .b span.w{{color:#fff}}
.leg{{margin-top:6pt;font-size:7.8pt;color:#333}} .sw{{display:inline-block;width:10pt;height:7pt;margin:0 3pt 0 8pt;vertical-align:middle}}
</style></head><body>
<h1>Microbiology OOS batches — all microbiology results on file</h1>
<p class="sub">Purely Plant · QC · 12.11.2026 · Sources: IPH certificates (register, Google Drive, RAGflow eCOA_INGEST); LabCore e-mail of 12.11.2026</p>
<table><colgroup><col style="width:17%"><col><col><col><col style="width:13%"><col style="width:13%"></colgroup>
<tr><th>Certificate / date</th><th>TAMC, CFU/g<br><small>10⁵, max 500 000</small></th><th>TYMC, CFU/g<br><small>10⁴, max 50 000</small></th><th>BTGN /g<br><small>limit ≤ 10⁴</small></th><th><i>E. coli</i><br><small>absent /1 g</small></th><th><i>Salmonella</i><br><small>absent /25 g</small></th></tr>
{rows}</table>
<div class="leg"><b>Bars:</b> length = log₁₀(result) ÷ log₁₀(limit); the full cell width is the maximum acceptable count (QCSP 001 / Ph. Eur. 5.1.8 cat. C: TAMC 500 000, TYMC 50 000, BTGN 10⁴). “&lt; 10” is drawn at 10; a range “10³–10⁴” at its upper bound.
<span class="sw" style="background:#2e9e5b"></span>≤ 75 % of the limit (log)<span class="sw" style="background:#e0a100"></span>75–100 % — near the limit<span class="sw" style="background:#d0342c"></span>above the limit / detected.
Pink rows: LabCore (Versa) results. <i>P. aeruginosa</i> and <i>S. aureus</i> not tested.<br>
</div>
</body></html>'''
open('OOS_Micro_Bars_2026-11-12.html','w').write(H)
