import json, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
import sys
DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "v9_data.json")
d = json.load(open(DATA))

# summary numbers
lots = d["lots"]
inst = sum(len(l["blocks"]) for l in lots)
oos = und = stab = 0
for l in lots:
    for blk in l["blocks"]:
        for b in blk:
            if "res" in b:
                if b["st"] in ("ok", "stab") and b["verdict"] == "oos":
                    (stab if b["st"] == "stab" else oos)  # placeholder
                    if b["st"] == "stab": stab += 1
                    else: oos += 1
            else:
                for v in b["verdicts"]:
                    if b["st"] == "ok" and v == "oos": oos += 1
                    if b["st"] == "ok" and v == "und": und += 1
gaps = sum(int(c[16]) for c in d["coverage"])
st_counts = collections.Counter("warn" if c[3].startswith("⚠") else "bad" for c in d["coverage"])
summary = {"lots": len(lots), "instances": inst, "oos": oos, "und": und, "stab": stab, "gaps": gaps,
           "cover_rows": len(d["coverage"]), "warn": st_counts["warn"], "bad": st_counts["bad"],
           "work": len(d["work_order"]), "audit": len(d["credit_audit"]), "corr": len(d["corrections"])}
d["summary"] = summary
payload = json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

html = r'''<title>CoQ Analysis Master v9</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,500;8..60,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  --bg:#F5F6F4;--surface:#FFFFFF;--ink:#1B262B;--muted:#5F6E75;--line:#D6DDDA;--line-strong:#9AA8AC;
  --accent:#0F6B72;--accent-ink:#FFFFFF;--accent-soft:#E2F0F0;
  --ok:#2C7A4B;--ok-soft:#E1F2E6;--warn:#A8690F;--warn-soft:#FBEFD6;--bad:#B3382F;--bad-soft:#F8E1DE;
  --grey:#7B8A8F;--grey-soft:#ECEFEE;--stab:#6A4FA3;--stab-soft:#ECE6F7;--head:#EEF2F1;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#151B1E;--surface:#1E2629;--ink:#E6ECEC;--muted:#93A2A7;--line:#33403F;--line-strong:#586A6D;
  --accent:#5FC3C8;--accent-ink:#0F1A1B;--accent-soft:#173A3D;
  --ok:#6CCB8E;--ok-soft:#1B3527;--warn:#E3A94A;--warn-soft:#3B2E14;--bad:#F08A80;--bad-soft:#3F1F1C;
  --grey:#93A2A7;--grey-soft:#26302F;--stab:#B69CE8;--stab-soft:#2A2340;--head:#232D30;
}}
:root[data-theme="dark"]{
  --bg:#151B1E;--surface:#1E2629;--ink:#E6ECEC;--muted:#93A2A7;--line:#33403F;--line-strong:#586A6D;
  --accent:#5FC3C8;--accent-ink:#0F1A1B;--accent-soft:#173A3D;
  --ok:#6CCB8E;--ok-soft:#1B3527;--warn:#E3A94A;--warn-soft:#3B2E14;--bad:#F08A80;--bad-soft:#3F1F1C;
  --grey:#93A2A7;--grey-soft:#26302F;--stab:#B69CE8;--stab-soft:#2A2340;--head:#232D30;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 "IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:1500px;margin:0 auto;padding:20px 24px 60px}
h1{font:600 30px/1.1 "Source Serif 4",Georgia,serif;margin:0 0 4px;text-wrap:balance}
h2{font:600 20px/1.2 "Source Serif 4",Georgia,serif;margin:28px 0 10px;text-wrap:balance}
h3{font:500 15px/1.3 "Source Serif 4",Georgia,serif;margin:0}
.sub{color:var(--muted);margin:0 0 18px;max-width:70ch}
.mono,code{font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;font-size:12.5px}
.label{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:500}
nav.tabs{display:flex;gap:4px;border-bottom:1px solid var(--line);margin-bottom:18px;position:sticky;top:0;background:var(--bg);z-index:5;padding-top:6px}
nav.tabs button{background:none;border:0;border-bottom:2px solid transparent;padding:10px 14px;font:500 14px "IBM Plex Sans",sans-serif;color:var(--muted);cursor:pointer}
nav.tabs button[aria-selected="true"]{color:var(--accent);border-bottom-color:var(--accent)}
nav.tabs button:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:0 0 20px}
.kpi{background:var(--surface);border:1px solid var(--line);padding:12px 14px}
.kpi b{display:block;font:600 26px/1.1 "Source Serif 4",Georgia,serif;font-variant-numeric:tabular-nums}
.kpi.bad b{color:var(--bad)}.kpi.warn b{color:var(--warn)}.kpi.stab b{color:var(--stab)}.kpi.ok b{color:var(--ok)}
.toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:0 0 12px}
.toolbar input,.toolbar select{font:inherit;padding:6px 9px;border:1px solid var(--line-strong);background:var(--surface);color:var(--ink);border-radius:3px}
.toolbar label{display:flex;gap:6px;align-items:center;color:var(--muted)}
.scroll{overflow-x:auto;border:1px solid var(--line);background:var(--surface)}
table{border-collapse:collapse;font-size:12.5px;font-variant-numeric:tabular-nums}
th,td{border:1px solid var(--line);padding:4px 7px;text-align:left;vertical-align:top;white-space:nowrap}
th{background:var(--head);font-weight:500;position:sticky;top:0;z-index:2}
td.c,th.c{text-align:center}
.mark{display:inline-block;min-width:22px;padding:1px 5px;border-radius:2px;text-align:center;font-weight:600}
.m-ok{background:var(--ok-soft);color:var(--ok)}.m-bad{background:var(--bad-soft);color:var(--bad)}
.pill{display:inline-block;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:500;white-space:nowrap}
.p-warn{background:var(--warn-soft);color:var(--warn)}.p-bad{background:var(--bad-soft);color:var(--bad)}.p-ok{background:var(--ok-soft);color:var(--ok)}.p-grey{background:var(--grey-soft);color:var(--grey)}
tr.row-link{cursor:pointer}tr.row-link:hover td{background:var(--accent-soft)}
td.wrap{white-space:normal;min-width:340px;max-width:460px;font-size:12px}
.legend{display:flex;flex-wrap:wrap;gap:8px 16px;margin:10px 0 14px;color:var(--muted);font-size:12.5px}
.legend span i{display:inline-block;width:12px;height:12px;vertical-align:-1px;margin-right:5px;border:1px solid var(--line)}
/* checklist */
.check{background:var(--surface);border:1px solid var(--line);margin-bottom:8px;display:grid;grid-template-columns:28px 1fr;gap:10px;padding:10px 12px}
.check input{width:18px;height:18px;margin:2px 0 0;accent-color:var(--accent)}
.check.done{opacity:.6}.check.done .what{text-decoration:line-through}
.check .meta{color:var(--muted);font-size:12.5px;margin-top:3px}
.check .what{margin-top:4px;max-width:80ch}
.progress{display:flex;align-items:center;gap:10px;color:var(--muted);margin:0 0 10px}
.progress .bar{flex:1;max-width:320px;height:6px;background:var(--grey-soft);border-radius:3px;overflow:hidden}
.progress .bar i{display:block;height:100%;background:var(--accent);width:0}
details{background:var(--surface);border:1px solid var(--line);margin-bottom:8px}
details summary{padding:10px 12px;cursor:pointer;font-weight:500;list-style:revert}
details .scroll{border:0;border-top:1px solid var(--line)}
/* tracker */
.lot{margin:0 0 22px;background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--line-strong)}
.lot.has-bad{border-left-color:var(--bad)}.lot.has-warn{border-left-color:var(--warn)}
.lot header{display:flex;flex-wrap:wrap;gap:6px 18px;align-items:baseline;padding:10px 12px;border-bottom:1px solid var(--line)}
.lot header .st{color:var(--muted);font-size:12.5px;white-space:pre-line}
.lot .scroll{border:0}
.tr th{font-size:11.5px;line-height:1.25;vertical-align:bottom;white-space:normal;min-width:88px;position:static}
.tr th.id{min-width:70px}
.tr th.sub{font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:400;color:var(--muted)}
.tr td{font-size:12px}
.tr td.res{text-align:center;font-weight:500}
.tr td.ref{font-family:"IBM Plex Mono",monospace;font-size:10.5px;color:var(--muted);white-space:normal;min-width:140px;max-width:220px;border-bottom:2px solid var(--line-strong)}
.tr td.res.ok{background:var(--ok-soft)}.tr td.res.missing{background:var(--bad-soft);color:var(--bad)}
.tr td.res.extra{background:var(--grey-soft);color:var(--grey);font-weight:400}
.tr td.res.stab{background:var(--stab-soft)}.tr td.res.silent{background:var(--warn-soft);color:var(--warn);font-weight:400;font-style:italic}
.tr td.res.v-oos{box-shadow:inset 0 0 0 2px var(--bad);color:var(--bad)}
.tr td.res.v-und{box-shadow:inset 0 0 0 2px var(--warn);color:var(--warn)}
.tr td.blk{text-align:center;color:var(--muted);font-family:"IBM Plex Mono",monospace;font-size:11px;vertical-align:middle;border-bottom:2px solid var(--line-strong)}
.tr .g{font-weight:600;margin-right:4px}
.empty{color:var(--muted);padding:20px;border:1px dashed var(--line)}
footer{color:var(--muted);font-size:12.5px;margin-top:40px;max-width:80ch}
@media (prefers-reduced-motion:no-preference){.progress .bar i{transition:width .25s}}
</style>

<div class="wrap">
<h1>CoQ Analysis Master v9</h1>
<p class="sub" id="subline"></p>

<nav class="tabs" role="tablist">
  <button role="tab" aria-selected="true" data-view="overview">Batch Coverage</button>
  <button role="tab" aria-selected="false" data-view="checklist">Checklist</button>
  <button role="tab" aria-selected="false" data-view="tracker">CoQ Parameter Tracker</button>
  <button role="tab" aria-selected="false" data-view="icoa">iCoA Issuance</button>
</nav>

<section id="overview">
  <div class="kpis" id="kpis"></div>
  <div class="toolbar">
    <input id="ov-q" type="search" placeholder="Filter by batch, strain, lab, code…" aria-label="Filter coverage rows">
    <label>Status <select id="ov-st"><option value="">all</option><option value="warn">⚠ partial (1–3 missing)</option><option value="bad">❌ 4+ missing</option></select></label>
    <span id="ov-n" class="label"></span>
  </div>
  <div class="legend"><span><i style="background:var(--ok-soft)"></i>✓ a certificate on file covers the parameter</span><span><i style="background:var(--bad-soft)"></i>✗ no certificate covers it — a gap</span><span>Click a row to open the lot in the tracker.</span></div>
  <div class="scroll"><table id="ov-table"></table></div>
</section>

<section id="checklist" hidden>
  <p class="sub">Ticks are kept in this browser only. The workbook is the record; the list is the desk's working copy of what no rebuild can fix.</p>
  <h2>Work Order — needs a person</h2>
  <div class="progress"><div class="bar"><i id="wo-bar"></i></div><span id="wo-n"></span></div>
  <div id="wo"></div>
  <h2>Credit Audit — credited certificates that carry no such row</h2>
  <div class="progress"><div class="bar"><i id="ca-bar"></i></div><span id="ca-n"></span></div>
  <div id="ca"></div>
  <h2>Credit corrections applied at build time</h2>
  <p class="sub">Each row is a credit the build removed because the evidence was explicit. The document stays on file and appears in the tracker as “on file, not credited”. Nothing was written back to the owner's workbook.</p>
  <div id="corr"></div>
</section>

<section id="tracker" hidden>
  <div class="toolbar">
    <input id="tr-q" type="search" placeholder="Jump to batch or P number…" list="lot-list" aria-label="Jump to lot">
    <datalist id="lot-list"></datalist>
    <label><input type="checkbox" id="tr-flag"> only lots with a result flagged</label>
    <span id="tr-n" class="label"></span>
  </div>
  <div class="legend">
    <span><i style="background:var(--ok-soft)"></i>release result, credited</span>
    <span><i style="background:var(--stab-soft)"></i>stability result — reported, not judged</span>
    <span><i style="background:var(--grey-soft)"></i>• on file, not credited</span>
    <span><i style="background:var(--bad-soft)"></i>— MISSING — no certificate</span>
    <span><i style="background:var(--warn-soft)"></i>held for review / not ingested</span>
    <span><i style="box-shadow:inset 0 0 0 2px var(--bad)"></i>out of specification</span>
    <span><i style="box-shadow:inset 0 0 0 2px var(--warn)"></i>undetermined (within 2× band)</span>
    <span>ᴰ derived by the compiler · ᴿ held by the register, not the eCoA database</span>
  </div>
  <div id="lots"></div>
</section>

<section id="icoa" hidden>
  <p class="sub">One iCoA per P lot, in the order of packaging: the iCoA is dated on the first day of packaging (the Head of QC\u2019s list of 04.09.2026), the day the issuance plan uses as the CoQ basis. Each carries identification A, identification B and foreign matter, tested at Purely Plant at packaging, and is issued no earlier than the last day of packaging (Packaging complete). Identification C is covered by the cannabinoid-assay certificate named in the last column, cited on the CoQ directly.</p>
  <div class="toolbar"><input id="ic-q" type="search" placeholder="Filter by batch, number, strain, certificate…" aria-label="Filter iCoA rows"><span id="ic-n" class="label"></span></div>
  <div class="scroll"><table id="ic-table"></table></div>
</section>

<footer>One two-row block per testing instance: the result on the top row, the certificate that carries it on the bottom. Parameters 9–11 print each determination in its own column. Conformance is judged on release results only, against the acceptance criteria on the Parameters sheet (counted limits ≤10ⁿ judged against 2×10ⁿ, Ph. Eur. 2.6.12). Built from <code>CoQ_Analysis_Master_v10.xlsx</code>, 04.09.2026: the 30 IJZ-MB microbiology certificates of 31.08/01.09.2026 are included as testing instances.</footer>
</div>

<script type="application/json" id="data">__DATA__</script>
<script>
(function(){
const D = JSON.parse(document.getElementById('data').textContent);
const S = D.summary;
const esc = s => String(s==null?'':s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const lsGet = k => { try { return JSON.parse(localStorage.getItem(k)||'{}'); } catch(e){ return {}; } };
const lsSet = (k,v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch(e){} };

document.getElementById('subline').textContent =
  `v10 · 04.09.2026 · ${S.lots} lots · 12 parameters · ${S.instances} testing instances · ${S.gaps} parameter gaps · ${S.oos} out of specification · ${S.und} undetermined · ${S.stab} stability exceedances`;

/* ---------- tabs ---------- */
const tabs = [...document.querySelectorAll('nav.tabs button')];
function show(view){
  tabs.forEach(b => b.setAttribute('aria-selected', String(b.dataset.view===view)));
  ['overview','checklist','tracker','icoa'].forEach(v => document.getElementById(v).hidden = v!==view);
  try { localStorage.setItem('coq9.view', view); } catch(e){}
}
tabs.forEach(b => b.addEventListener('click', () => show(b.dataset.view)));

/* ---------- overview ---------- */
const kp = [
  ['Lots', S.lots, ''], ['Testing instances', S.instances, ''], ['Parameter gaps', S.gaps, 'warn'],
  ['Lots ≥4 missing', S.bad, 'bad'], ['Out of specification', S.oos, 'bad'], ['Undetermined', S.und, 'warn'],
  ['Stability exceedances', S.stab, 'stab'], ['Open work-order tasks', S.work, '']
];
document.getElementById('kpis').innerHTML = kp.map(([l,v,c]) => `<div class="kpi ${c}"><span class="label">${esc(l)}</span><b>${esc(v)}</b></div>`).join('');

const H = D.coverage_headers;
const ovTable = document.getElementById('ov-table');
const lotIndex = new Map(D.lots.map((l,i) => [l.cu, i]));
function statusPill(s){
  const cls = s.startsWith('⚠') ? 'p-warn' : s.startsWith('❌') ? 'p-bad' : 'p-ok';
  return `<span class="pill ${cls}">${esc(s)}</span>`;
}
function renderOverview(){
  const q = document.getElementById('ov-q').value.trim().toLowerCase();
  const st = document.getElementById('ov-st').value;
  let n = 0;
  const head = '<thead><tr>' + H.map((h,i) => {
    const c = (i>=4 && i<=15) ? ' class="c"' : '';
    const t = (i>=4 && i<=15) ? h.replace(/^(\d+) .*?— ?/, '$1 ').replace(/^(\d+) (Identification .)$/, '$1 Ident. $2') : h;
    return `<th${c} title="${esc(h)}">${esc(i>=4&&i<=15 ? t.split(' ').slice(0,3).join(' ') : h)}</th>`;
  }).join('') + '</tr></thead>';
  const body = D.coverage.filter(r => {
    if (st==='warn' && !r[3].startsWith('⚠')) return false;
    if (st==='bad' && !r[3].startsWith('❌')) return false;
    return !q || r.join(' ').toLowerCase().includes(q);
  }).map(r => {
    n++;
    const idx = lotIndex.has(r[0]) ? lotIndex.get(r[0]) : -1;
    return `<tr class="row-link" data-lot="${idx}">` + r.map((v,i) => {
      if (i>=4 && i<=15) return `<td class="c"><span class="mark ${v==='✓'?'m-ok':'m-bad'}">${esc(v)}</span></td>`;
      if (i===3) return `<td>${statusPill(v)}</td>`;
      if (i===17 || i===19) return `<td class="wrap">${esc(v)}</td>`;
      if (i===0 || i===1) return `<td class="mono">${esc(v)}</td>`;
      if (i===16 || i===18) return `<td class="c">${esc(v)}</td>`;
      return `<td>${esc(v)}</td>`;
    }).join('') + '</tr>';
  }).join('');
  ovTable.innerHTML = head + '<tbody>' + body + '</tbody>';
  document.getElementById('ov-n').textContent = `${n} of ${D.coverage.length} rows`;
}
ovTable.addEventListener('click', e => {
  const tr = e.target.closest('tr.row-link'); if (!tr) return;
  const i = +tr.dataset.lot; if (i < 0) return;
  document.getElementById('tr-flag').checked = false;
  document.getElementById('tr-q').value = D.lots[i].cu;
  renderTracker(); show('tracker');
  const el = document.getElementById('lot-'+i); if (el) el.scrollIntoView({block:'start'});
});
document.getElementById('ov-q').addEventListener('input', renderOverview);
document.getElementById('ov-st').addEventListener('change', renderOverview);

/* ---------- checklist ---------- */
const ticks = lsGet('coq9.ticks');
function checkItem(key, title, meta, what){
  const on = !!ticks[key];
  return `<div class="check${on?' done':''}"><input type="checkbox" data-key="${esc(key)}" ${on?'checked':''} aria-label="Done: ${esc(title)}"><div><h3>${esc(title)}</h3><div class="meta">${meta}</div><div class="what">${esc(what)}</div></div></div>`;
}
function renderChecklist(){
  const wo = D.work_order.map((w,i) => checkItem('wo'+i,
    `${w['Task']} · ${w['Parameters affected']} · ${w['CU Batch']}`,
    `<span class="mono">${esc(w['Certificate'])}</span> · ${esc(w['Date'])} · ${esc(w['Lab'])} · P ${esc(w['P Batch'])}`,
    w['What is needed'])).join('');
  document.getElementById('wo').innerHTML = wo;
  const ca = D.credit_audit.map((a,i) => checkItem('ca'+i,
    `${a['Parameter']} · ${a['CU Batch']} — ${a['Finding']}`,
    `<span class="mono">${esc(a['Certificate'])}</span> · ${esc(a['Date'])} · ${esc(a['Lab'])} · P ${esc(a['P Batch'])}`,
    a['Action'])).join('');
  document.getElementById('ca').innerHTML = ca;
  const groups = new Map();
  D.corrections.forEach(c => { const k = c['Evidence']; if (!groups.has(k)) groups.set(k, []); groups.get(k).push(c); });
  document.getElementById('corr').innerHTML = [...groups].map(([k, rows]) =>
    `<details><summary>${esc(k)} <span class="pill p-grey">${rows.length} credits removed</span></summary><div class="scroll"><table><thead><tr><th>CU Batch</th><th>P Batch</th><th>Certificate</th><th>Date</th><th>Lab</th><th>Parameter</th></tr></thead><tbody>` +
    rows.map(r => `<tr><td class="mono">${esc(r['CU Batch'])}</td><td class="mono">${esc(r['P Batch'])}</td><td class="mono">${esc(r['Certificate'])}</td><td>${esc(r['Date'])}</td><td>${esc(r['Lab'])}</td><td>${esc(r['Parameter'])}</td></tr>`).join('') +
    '</tbody></table></div></details>').join('');
  updateProgress();
}
function updateProgress(){
  const cnt = (p, n) => { let k=0; for (let i=0;i<n;i++) if (ticks[p+i]) k++; return k; };
  const a = cnt('wo', D.work_order.length), b = cnt('ca', D.credit_audit.length);
  document.getElementById('wo-bar').style.width = (100*a/D.work_order.length)+'%';
  document.getElementById('wo-n').textContent = `${a} of ${D.work_order.length} done`;
  document.getElementById('ca-bar').style.width = (100*b/D.credit_audit.length)+'%';
  document.getElementById('ca-n').textContent = `${b} of ${D.credit_audit.length} done`;
}
document.getElementById('checklist').addEventListener('change', e => {
  const cb = e.target.closest('input[type=checkbox][data-key]'); if (!cb) return;
  ticks[cb.dataset.key] = cb.checked; lsSet('coq9.ticks', ticks);
  cb.closest('.check').classList.toggle('done', cb.checked); updateProgress();
});

/* ---------- tracker ---------- */
const P = D.params;
const cols = P.map(p => p.subs ? p.subs.length : 1);
document.getElementById('lot-list').innerHTML = D.lots.map(l => `<option value="${esc(l.cu)}">${esc(l.p)}</option>`).join('');
function lotFlag(l){
  let bad=false, warn=false;
  l.blocks.forEach(blk => blk.forEach(b => {
    if ('res' in b){ if (b.st==='ok' && b.verdict==='oos') bad=true; if (b.st==='stab' && b.verdict==='oos') warn=true; if (b.st==='silent') warn=true; }
    else { b.verdicts.forEach(v => { if (b.st==='ok' && v==='oos') bad=true; if (b.st==='ok' && v==='und') warn=true; }); if (b.st==='silent') warn=true; }
  }));
  return bad ? 'has-bad' : warn ? 'has-warn' : '';
}
function resCell(b, val, verdict){
  const judged = b.st==='ok' || b.st==='stab';
  const v = judged && verdict==='oos' ? ' v-oos' : judged && verdict==='und' ? ' v-und' : '';
  const g = b.st==='extra' ? '<span class="g">•</span>' : '';
  return `<td class="res ${b.st}${v}">${g}${esc(val)}</td>`;
}
function renderLot(l, i){
  const head1 = '<tr><th class="id" rowspan="2">Block</th>' + P.map((p,k) => `<th colspan="${cols[k]}" title="${esc(p.ac)}">${esc(p.title)}<br><span class="sub">${esc(p.method)}</span></th>`).join('') + '</tr>';
  const head2 = '<tr>' + P.map((p,k) => p.subs ? p.subs.map((s,j) => `<th class="sub" title="${esc(p.ac[j])}">${esc(s)}<br>${esc(p.ac[j])}</th>`).join('') : `<th class="sub">${esc(p.ac)}</th>`).join('') + '</tr>';
  const rows = l.blocks.map((blk, bi) => {
    let top = `<tr><td class="blk" rowspan="2">${bi+1}</td>`, bot = '<tr>';
    blk.forEach((b, k) => {
      if (b.st === 'none'){ top += `<td colspan="${cols[k]}"></td>`; bot += `<td class="ref" colspan="${cols[k]}"></td>`; return; }
      if ('res' in b) top += resCell(b, b.res, b.verdict);
      else b.vals.forEach((v,j) => { top += resCell(b, v, b.verdicts[j]); });
      bot += `<td class="ref" colspan="${cols[k]}">${esc(b.ref)}</td>`;
    });
    return top + '</tr>' + bot + '</tr>';
  }).join('');
  const body = rows || `<tr><td colspan="${1+cols.reduce((a,b)=>a+b,0)}" class="empty">No testing instance on file for this lot.</td></tr>`;
  return `<article class="lot ${lotFlag(l)}" id="lot-${i}"><header><h3><span class="mono">${esc(l.cu)}</span></h3><span class="mono">P ${esc(l.p)}</span><span class="st">${esc(l.status)}</span></header><div class="scroll"><table class="tr">${head1}${head2}${body}</table></div></article>`;
}
function renderTracker(){
  const q = document.getElementById('tr-q').value.trim().toLowerCase();
  const flag = document.getElementById('tr-flag').checked;
  let n = 0;
  const html = D.lots.map((l,i) => {
    if (flag && !lotFlag(l)) return '';
    if (q && !(l.cu.toLowerCase().includes(q) || l.p.toLowerCase().includes(q))) return '';
    n++; return renderLot(l, i);
  }).join('');
  document.getElementById('lots').innerHTML = html || '<div class="empty">No lot matches.</div>';
  document.getElementById('tr-n').textContent = `${n} of ${D.lots.length} lots`;
}
document.getElementById('tr-q').addEventListener('input', renderTracker);
document.getElementById('tr-flag').addEventListener('change', renderTracker);

/* ---------- iCoA issuance ---------- */
function renderIcoa(){
  const rows = D.icoa || [];
  const q = document.getElementById('ic-q').value.trim().toLowerCase();
  const cols = rows.length ? Object.keys(rows[0]) : [];
  let n = 0;
  const body = rows.filter(r => !q || Object.values(r).join(' ').toLowerCase().includes(q)).map(r => { n++;
    return '<tr>' + cols.map(c => {
      const v = r[c] || '';
      const cls = (c === 'Seq') ? ' class="c"' : (c === 'iCoA' || c === 'CoQ' || c === 'CU Batch' || c === 'P Batch' || c.startsWith('Ident C')) ? ' class="mono"' : '';
      const pill = v === 'held for review' ? `<span class="pill p-warn">${esc(v)}</span>` : (v.startsWith('—') ? `<span class="pill p-bad">${esc(v)}</span>` : esc(v));
      return `<td${cls}>${pill}</td>`;
    }).join('') + '</tr>'; }).join('');
  document.getElementById('ic-table').innerHTML = '<thead><tr>' + cols.map(c => `<th>${esc(c)}</th>`).join('') + '</tr></thead><tbody>' + body + '</tbody>';
  document.getElementById('ic-n').textContent = `${n} of ${rows.length} iCoAs`;
}
document.getElementById('ic-q').addEventListener('input', renderIcoa);

renderOverview(); renderChecklist(); renderTracker(); renderIcoa();
let v = 'overview'; try { v = localStorage.getItem('coq9.view') || v; } catch(e){}
show(['overview','checklist','tracker','icoa'].includes(v) ? v : 'overview');
})();
</script>
'''
out = os.path.join(HERE, "coq_master_v9.html")
open(out, "w").write(html.replace("__DATA__", payload))
print(out, os.path.getsize(out), summary)
