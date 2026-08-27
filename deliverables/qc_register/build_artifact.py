#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QC Batch Release Results Register as a self-contained HTML artifact,
rendered from the RAGflow eCoA_DATABASE consolidated data (rev.5)."""
import json, re, unicodedata

C = json.load(open('consolidated.json'))
RECS = {r['name']: r for r in json.load(open('extracted_params.json'))}

def nrm(s):
    s = unicodedata.normalize('NFKC', str(s))
    return re.sub(r'[\s,_/()-]+', '', s).lower()
DRIVE = {}
for line in open('drive_all.tsv', encoding='utf-8'):
    fid, name = line.rstrip('\n').split('\t'); DRIVE[nrm(name)] = fid

LABNAME = {'CNP':'UKIM Faculty of Pharmacy — CNP','IJZ':'IPH (chemistry)','IJZ-MB':'IPH (microbiology)',
           'FHM':'Farmahem','PP':'Purely Plant (in-house)','NGP':'NGP in-house GC','DFL':'DFL (DE)'}
PARAMS = [('total_thc_pct','THC','%'),('total_cbd_pct','CBD','%'),('total_cbn_pct','CBN','%'),
 ('loss_on_drying_pct','LoD','%'),('foreign_matter_pct','FM','%'),('macroscopic_id','Macro',''),
 ('microscopic_id','Micro',''),('hptlc_id','HPTLC',''),('tamc','TAMC','CFU/g'),('tymc','TYMC','CFU/g'),
 ('bile_tolerant_gnb','BGNB','CFU/g'),('salmonella','Salm.','/25g'),('e_coli','E.coli','/1g'),
 ('aflatoxins_total','Afl Σ','µg/kg'),('aflatoxin_b1','Afl B1','µg/kg'),('ochratoxin_a','OTA','µg/kg'),
 ('pb','Pb','mg/kg'),('cd','Cd','mg/kg'),('arsenic','As','mg/kg'),('hg','Hg','mg/kg'),('pesticides','Pest.','')]
CORR = {'OMP1024_01','GG1024_02'}  # verify-on-paper corrections
data = []
for row in C['rows']:
    certs = []
    for n in C['cert_map'][row['key']]:
        rec = RECS[n]; m = rec['meta']; p = rec.get('params') or {}
        certs.append({'code': m.get('cert_code') or '', 'date': m.get('date_of_issue') or '',
                      'lab': m.get('lab') or '', 'labFull': LABNAME.get(m.get('lab'), m.get('lab') or ''),
                      'thc': p.get('total_thc_pct') or '',
                      'stab': bool(m.get('test_type') == 'STABILITY_TIMEPOINT' or p.get('is_stability')),
                      'id': DRIVE.get(nrm(n), '')})
    certs.sort(key=lambda c: tuple(reversed(c['date'].split('.'))) if c['date'].count('.') == 2 else ('9',))
    vals = {}
    for f, lab, unit in PARAMS:
        v = row.get(f)
        if v not in (None, '', 'None'): vals[f] = str(v)
    data.append({'batch': row['batch'], 'p': row.get('p_number') or '', 'strain': row.get('strain') or '',
                 'prod': row.get('production') or '', 'code': row.get('product_code') or '',
                 'coq': row.get('coq') or '', 'first': row.get('first_result') or '', 'last': row.get('latest_result') or '',
                 'n': row['n_certs'], 'thcSrc': row.get('total_thc_pct__src') or '',
                 'vals': vals, 'certs': certs,
                 'flag': 'corr' if row['batch'] in CORR else ('exp' if 'hand-trimmed' in row['batch'] else 'ok')})

PENDING = [
 {'batch':'ACC102501','p':'P060122','strain':'Amnesia Core Cut','decl':'12.91','st':'sampled 12.08.2026 — lab results pending'},
 {'batch':'CC012603','p':'P060372','strain':'Cash Cow','decl':'12.32','st':'sampled 12.08.2026 — lab results pending'},
 {'batch':'CF102501','p':'P060132','strain':'Chem Flyer','decl':'9.83','st':'sampled 12.08.2026 — lab results pending'},
 {'batch':'JD012603/01','p':'P060362','strain':'Jelly Donutz','decl':'16.71','st':'sampled 12.08.2026 — lab results pending'},
 {'batch':'PUM102501','p':'P060112','strain':'Pure Michigen','decl':'15.63','st':'sampled 12.08.2026 — lab results pending'},
 {'batch':'GRC102501/1','p':'','strain':'Graps & Creme','decl':'7.05','st':'no sampling record found'},
 {'batch':'SCR012601','p':'','strain':'Scrambler','decl':'18.07','st':'no sampling record found'},
 {'batch':'WED102501','p':'','strain':'Wedding Cake','decl':'22.05','st':'no sampling record found'},
]
PJ = json.dumps({'rows': data, 'pending': PENDING}, ensure_ascii=False)

HTML = """<title>eCoA Release Register</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
:root{
  --bg:#f6f7f6; --panel:#ffffff; --ink:#1c2426; --muted:#5c6b6f; --line:#dde3e2;
  --accent:#175e63; --accent-ink:#ffffff; --head:#eef2f1; --chip-ok:#e3efe7; --chip-ok-ink:#1e5c38;
  --chip-warn:#fdf1e2; --chip-warn-ink:#8a5410; --chip-info:#e7edf6; --chip-info-ink:#2b4d7e;
  --chip-exp:#f0e9f6; --chip-exp-ink:#5b3a86; --row-hover:#f0f4f3; --mono:'IBM Plex Mono',ui-monospace,monospace;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#12181a; --panel:#1a2224; --ink:#e3e9e8; --muted:#8fa0a3; --line:#2b3639;
  --accent:#4fb3ba; --accent-ink:#0c1a1b; --head:#20292c; --chip-ok:#1c3527; --chip-ok-ink:#8fd4ab;
  --chip-warn:#3c2c12; --chip-warn-ink:#e8b566; --chip-info:#1d2b40; --chip-info-ink:#9dbdec;
  --chip-exp:#2d2140; --chip-exp-ink:#c2a4ee; --row-hover:#212c2f;
}}
:root[data-theme="dark"]{
  --bg:#12181a; --panel:#1a2224; --ink:#e3e9e8; --muted:#8fa0a3; --line:#2b3639;
  --accent:#4fb3ba; --accent-ink:#0c1a1b; --head:#20292c; --chip-ok:#1c3527; --chip-ok-ink:#8fd4ab;
  --chip-warn:#3c2c12; --chip-warn-ink:#e8b566; --chip-info:#1d2b40; --chip-info-ink:#9dbdec;
  --chip-exp:#2d2140; --chip-exp-ink:#c2a4ee; --row-hover:#212c2f;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 'IBM Plex Sans',system-ui,sans-serif}
header{padding:26px 26px 16px;border-bottom:2px solid var(--accent);background:var(--panel)}
h1{margin:0 0 4px;font-size:21px;font-weight:700;letter-spacing:.01em}
h1 .co{color:var(--accent)}
.sub{color:var(--muted);font-size:12.5px;max-width:70ch}
.stats{display:flex;gap:26px;flex-wrap:wrap;margin-top:14px}
.stat b{display:block;font-size:19px;font-family:var(--mono);font-weight:600}
.stat span{font-size:10.5px;text-transform:uppercase;letter-spacing:.09em;color:var(--muted)}
.bar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:12px 26px;background:var(--panel);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
input,select{font:13px 'IBM Plex Sans',sans-serif;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:7px 10px}
input{width:230px}
input:focus,select:focus{outline:2px solid var(--accent);outline-offset:1px}
.count{margin-left:auto;color:var(--muted);font-size:12px;font-family:var(--mono)}
.wrap{padding:18px 26px 60px}
.tblbox{overflow-x:auto;background:var(--panel);border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;min-width:1750px;width:100%}
th{position:sticky;top:0;background:var(--head);font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);padding:9px 8px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}
th .u{display:block;font-weight:400;letter-spacing:0;text-transform:none;font-size:9.5px;opacity:.75}
td{padding:7px 8px;border-bottom:1px solid var(--line);white-space:nowrap;font-family:var(--mono);font-size:12.5px;font-variant-numeric:tabular-nums}
td.t{font-family:'IBM Plex Sans',sans-serif;font-size:13px}
tr.b:hover{background:var(--row-hover);cursor:pointer}
td.batch{font-weight:600;font-family:'IBM Plex Sans',sans-serif}
td.thc{font-weight:600;color:var(--accent)}
.chip{display:inline-block;padding:2px 8px;border-radius:99px;font:600 10.5px 'IBM Plex Sans',sans-serif;letter-spacing:.02em}
.c-ok{background:var(--chip-ok);color:var(--chip-ok-ink)} .c-warn{background:var(--chip-warn);color:var(--chip-warn-ink)}
.c-info{background:var(--chip-info);color:var(--chip-info-ink)} .c-exp{background:var(--chip-exp);color:var(--chip-exp-ink)}
tr.det td{background:var(--head);white-space:normal;padding:12px 16px 14px}
.certs{display:flex;flex-direction:column;gap:5px}
.cert{display:flex;gap:14px;align-items:baseline;font-family:var(--mono);font-size:12px;flex-wrap:wrap}
.cert .cd{min-width:170px;font-weight:600}.cert .dt{color:var(--muted);min-width:86px}
.cert .lb{min-width:230px;font-family:'IBM Plex Sans',sans-serif}
.cert .tv{color:var(--accent);font-weight:600;min-width:88px}
.cert a{color:var(--accent);text-decoration:none;border-bottom:1px dotted var(--accent)}
.cert a:focus{outline:2px solid var(--accent)}
h2{font-size:14px;margin:30px 0 10px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.pend{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px}
.pcard{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--chip-warn-ink);border-radius:8px;padding:12px 14px}
.pcard b{font-size:14px}.pcard .m{color:var(--muted);font-size:12px;margin-top:2px}
.pcard .d{font-family:var(--mono);margin-top:6px;font-size:13px}
footer{padding:20px 26px;color:var(--muted);font-size:11.5px;border-top:1px solid var(--line)}
.legend{display:flex;gap:14px;flex-wrap:wrap;margin:12px 0 0;font-size:11.5px;color:var(--muted)}
</style>
<header>
  <h1><span class="co">Purely Plant</span> — Batch Release QC Results Register</h1>
  <div class="sub">One row per batch · CoQ-forming values retrieved from the RAGflow <b>eCoA_DATABASE</b> (291 certificates, complete mirror of the ingestion folder) · retest rule: newer result &gt;60 days apart supersedes · stability results excluded · values exactly as printed on the certificates · rev.5, 27.08.2026 — full Tranche 1/2/3 THC audit passed (69/69)</div>
  <div class="stats">
    <div class="stat"><b id="sBatches">–</b><span>batches</span></div>
    <div class="stat"><b>291</b><span>certificates</span></div>
    <div class="stat"><b>69/69</b><span>THC audit OK</span></div>
    <div class="stat"><b id="sPending">–</b><span>awaiting eCoA</span></div>
  </div>
  <div class="legend">
    <span><span class="chip c-ok">CoQ</span> CoQ code assigned</span>
    <span><span class="chip c-warn">verify paper</span> value from documented certificate-anomaly correction</span>
    <span><span class="chip c-exp">experimental</span> processing-mode comparison lot</span>
    <span>Click a row to see every certificate with its Drive link.</span>
  </div>
</header>
<div class="bar">
  <input id="q" type="search" placeholder="Search batch, P-number, strain, CoQ…" aria-label="Search">
  <select id="fStrain" aria-label="Strain filter"><option value="">All strains</option></select>
  <select id="fFlag" aria-label="Status filter">
    <option value="">All statuses</option><option value="coq">With CoQ code</option>
    <option value="corr">Verify-on-paper</option><option value="exp">Experimental lot</option>
  </select>
  <span class="count" id="count"></span>
</div>
<div class="wrap">
  <div class="tblbox"><table id="tbl"><thead><tr id="hdr"></tr></thead><tbody id="body"></tbody></table></div>
  <h2>Awaiting eCoA — declared values only</h2>
  <div class="pend" id="pend"></div>
</div>
<footer>Source of truth: RAGflow eCoA_DATABASE (dataset f29f8f58…) · extraction sanity-checked in 3 layers (verbatim presence 2469/2512 · labeled-line anchors 106/107 · register cross-check) with 49 logged repairs · paper-loop vision-verified on 3 sample PDFs · J31122501 split per QC designation 27.08.2026 (machine-trimmed CoQ-forming) · Corrections marked "verify paper": OMP1024_01 (ППК25117), GG1024_02 (ППК25140).</footer>
<script>
const DATA = __DATA__;
const P = [["total_thc_pct","THC","%"],["total_cbd_pct","CBD","%"],["total_cbn_pct","CBN","%"],
["loss_on_drying_pct","LoD","%"],["foreign_matter_pct","FM","%"],["macroscopic_id","Macro",""],
["microscopic_id","Micro",""],["hptlc_id","HPTLC",""],["tamc","TAMC","CFU/g"],["tymc","TYMC","CFU/g"],
["bile_tolerant_gnb","BGNB","CFU/g"],["salmonella","Salm.","/25g"],["e_coli","E.coli","/1g"],
["aflatoxins_total","Afl Σ","µg/kg"],["aflatoxin_b1","Afl B1","µg/kg"],["ochratoxin_a","OTA","µg/kg"],
["pb","Pb","mg/kg"],["cd","Cd","mg/kg"],["arsenic","As","mg/kg"],["hg","Hg","mg/kg"],["pesticides","Pest.",""]];
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const hdr = document.getElementById('hdr');
hdr.innerHTML = '<th>#</th><th>Batch</th><th>P-number</th><th>Strain</th><th>Prod.</th><th>CoQ</th>' +
  P.map(p => `<th>${p[1]}${p[2] ? `<span class="u">${p[2]}</span>` : ''}</th>`).join('') + '<th>eCoAs</th>';
const strains = [...new Set(DATA.rows.map(r => r.strain).filter(Boolean))].sort();
const fs = document.getElementById('fStrain');
strains.forEach(s => { const o = document.createElement('option'); o.value = o.textContent = s; fs.appendChild(o); });
function chip(r){
  let c = '';
  if (r.coq) c += `<span class="chip c-ok">${esc(r.coq.replace('CoQ-PP-2026-',''))}</span> `;
  if (r.flag === 'corr') c += '<span class="chip c-warn">verify paper</span>';
  if (r.flag === 'exp') c += '<span class="chip c-exp">experimental</span>';
  return c || '<span class="chip c-info">proposed</span>';
}
function render(){
  const q = document.getElementById('q').value.toLowerCase();
  const st = fs.value, fl = document.getElementById('fFlag').value;
  const body = document.getElementById('body'); body.innerHTML = '';
  let n = 0;
  DATA.rows.forEach((r, i) => {
    const hay = (r.batch + ' ' + r.p + ' ' + r.strain + ' ' + r.coq + ' ' + r.code).toLowerCase();
    if (q && !hay.includes(q)) return;
    if (st && r.strain !== st) return;
    if (fl === 'coq' && !r.coq) return;
    if (fl === 'corr' && r.flag !== 'corr') return;
    if (fl === 'exp' && r.flag !== 'exp') return;
    n++;
    const tr = document.createElement('tr'); tr.className = 'b'; tr.tabIndex = 0;
    tr.setAttribute('aria-expanded', 'false');
    tr.innerHTML = `<td>${i + 1}</td><td class="batch">${esc(r.batch)}</td><td>${esc(r.p)}</td>` +
      `<td class="t">${esc(r.strain)}</td><td>${esc(r.prod)}</td><td class="t">${chip(r)}</td>` +
      P.map(p => `<td${p[0] === 'total_thc_pct' ? ' class="thc"' : ''}>${esc(r.vals[p[0]] ?? '/')}</td>`).join('') +
      `<td>${r.n}</td>`;
    const det = document.createElement('tr'); det.className = 'det'; det.style.display = 'none';
    det.innerHTML = `<td colspan="${P.length + 7}"><div class="certs">` +
      `<div style="font:600 11px 'IBM Plex Sans';text-transform:uppercase;letter-spacing:.07em;color:var(--muted)">Certificates — THC forming: ${esc(r.thcSrc || '—')}</div>` +
      r.certs.map(c => `<div class="cert"><span class="cd">${esc(c.code)}${c.stab ? ' <span class="chip c-info">stability</span>' : ''}</span>` +
        `<span class="dt">${esc(c.date)}</span><span class="lb">${esc(c.labFull)}</span>` +
        `<span class="tv">${c.thc ? 'THC ' + esc(c.thc) : ''}</span>` +
        (c.id ? `<a href="https://drive.google.com/file/d/${c.id}/view" target="_blank" rel="noopener">open PDF</a>` : '')
      + '</div>').join('') + '</div></td>';
    const tog = () => { const open = det.style.display !== 'none';
      det.style.display = open ? 'none' : ''; tr.setAttribute('aria-expanded', String(!open)); };
    tr.addEventListener('click', tog);
    tr.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); tog(); } });
    body.appendChild(tr); body.appendChild(det);
  });
  document.getElementById('count').textContent = n + ' / ' + DATA.rows.length + ' batches';
}
['q','fStrain','fFlag'].forEach(id => document.getElementById(id).addEventListener('input', render));
document.getElementById('sBatches').textContent = DATA.rows.length;
document.getElementById('sPending').textContent = DATA.pending.length;
document.getElementById('pend').innerHTML = DATA.pending.map(p =>
  `<div class="pcard"><b>${esc(p.batch)}</b>${p.p ? ' <span style="font-family:var(--mono);color:var(--muted)">' + esc(p.p) + '</span>' : ''}` +
  `<div class="m">${esc(p.strain)} · ${esc(p.st)}</div><div class="d">declared THC ${esc(p.decl)} %</div></div>`).join('');
render();
</script>
"""
out = HTML.replace('__DATA__', PJ)
open('qc_register_artifact.html', 'w', encoding='utf-8').write(out)
print('written', len(out), 'bytes')
