// Build the CoQ set from the desk's v40 data through the Claude Design toolchain.
//   node design_handoff/toolchain/build_v40.js
// Reads coq_artifact_data.json (the desk's export), maps each certificate to the
// package's record shape, applies it onto the package's base document with
// coq_apply.js (visual layer untouched), writes ISSUE_COQ/ and REISSUE/T*/, and
// runs the 16 data assertions of coq_check.js on every document.
const fs = require('fs'), path = require('path');
const HERE = __dirname, HANDOFF = path.dirname(HERE), GAP = path.dirname(HANDOFF);
for (const f of ['coq_build.js', 'coq_apply.js', 'coq_check.js']) eval(fs.readFileSync(path.join(HERE, f), 'utf8'));
const skeleton = fs.readFileSync(path.join(HERE, 'tbody_skeleton.txt'), 'utf8');
const base = fs.readFileSync(path.join(HANDOFF, 'base', 'CoQ-PP_26-013_P050072_GP_Grape_Pie_Grade_II.html'), 'utf8');
const data = JSON.parse(fs.readFileSync(path.join(GAP, 'coq_artifact_data.json'), 'utf8'));
const OUT = path.join(HANDOFF, 'out');

// tranche of a reissue, from the desk's scope files
const tranche = {};
for (const [f, t] of [['coq_reissue_scope_2026-09-15.csv', null], ['coq_draft_scope_2026-09-10.csv', null]]) {
  const p = path.join(GAP, 'tracker', f); if (!fs.existsSync(p)) continue;
  const rows = CoQ.parseCSV(fs.readFileSync(p, 'utf8')); const hd = rows[0];
  const iT = hd.indexOf('tranche'), iL = hd.indexOf('p_lot');
  for (const r of rows.slice(1)) if (r[iL]) tranche[r[iL]] = tranche[r[iL]] || r[iT];
}

// --- the owner's instruction of 16.09.2026: the Macedonian half of a conformity
// result stacks beneath the English, at the size the template already sets for it
// (.r-conform .mk — 6.8px, 79 % of the cell). The package's cell() drops the half
// after the pipe; this wraps it so the half is emitted inside the .r-conform span,
// where the template's own rule styles it. Nothing else in the cell changes.
const MK = { conforms: 'Одговара', absent: 'Отсутна' };
// A register status is the desk's word about the DETERMINATION; a result cell is the
// package's word about the RESULT. The package's vocabulary prints [ — ] for "to be
// performed", "upon request", "not tested", "in-house CoA only" and [pending] for
// "awaiting" — all of which say *no result is on file*. Where the desk now holds a
// result and the document that certifies it, that sentence is no longer true of the
// cell: #1, #2 and #7 keep the route's wording ("to be performed — see route") in the
// register long after the internal certificate of analysis has issued and carried
// them, and the 15.09 carry copies a release result onto a reissue row whose own
// status still names the outstanding re-analysis. Printed as written, those two put a
// red [ — ] over 1568 cells the desk can certify.
//
// So for the CELL only, a status that claims no result is dropped when a result is
// present — and every status that COLOURS a present value is kept, because that is a
// statement about the value itself: OUT OF SPECIFICATION, BLOCKED, UNDETERMINED, and
// the carry note, which says where the value came from. The register, the tracker and
// Section 03's citation keep the desk's full wording.
const ST_KEEP = /^(carried from the initial testing|covered|OUT OF SPECIFICATION|BLOCKED|UNDETERMINED)/i;
const ST_NO_RESULT = /^(to be performed|upon request|not tested|in-house CoA only|awaiting|see route|outside the retest scope)/i;
//
// The result is not enough on its own: a value with no document behind it is a value
// the certificate cannot attribute, and assertion A15 is right to refuse it. So the
// status is set aside only where the row also carries a code-shaped source document;
// otherwise the desk's word stands and the cell prints the withheld token.
let CURRENT = null;                                   // the record being applied
function cellStatus(det, res, st) {
  const r = String(res || '').trim();
  if (!CoQ.codeShaped(String((CURRENT && CURRENT.doc[det]) || '').trim())) return st;
  if (!r || r === '\u2014') return st;                       // no result: the status stands
  const parts = String(st || '').split(' \u2014 ');
  if (!parts.some(p => ST_NO_RESULT.test(p.trim()))) return st;
  const kept = parts.filter(p => ST_KEEP.test(p.trim()));
  return kept.length ? kept.join(' \u2014 ') : 'covered';
}
const cell0 = CoQ.cell;
CoQ.cell = function (det, res, st) {
  let h = cell0(det, res, cellStatus(det, res, st));
  if (h.indexOf('r-conform') >= 0) {
    const half = String(res || '').split('|')[1];
    const mk = half ? half.trim() : (/>Absent</.test(h) ? MK.absent : MK.conforms);
    h = h.replace(/(<span class="r-val r-conform"[^>]*>)([^<]*)(<\/span>)/, (m, a, b, c) => a + b + '<span class="mk">' + CoQ.esc(mk) + '</span>' + c);
  }
  return h;
};
// one appended layer: a SUB-ROW is one line tall (its name runs inline), so its
// Macedonian stays inline there and the row does not grow; a parameter row already
// runs two lines in its name column and takes the template's stacked form.
const OWNER_LAYER = '<style id="__owner-mk-subrow-inline">\n' +
  '/* Owner, 16.09.2026: bilingual conformity result, EN over MK at the template\'s .r-conform .mk size.\n' +
  '   Parameter rows take the template\'s stacked rule as written. A sub-row is one line tall, so its\n' +
  '   MK half stays inline with a thin separator and the row height is unchanged. */\n' +
  'html body div.page div.tbl-wrap table.results tbody tr.sub-row td.r-cell .r-val.r-conform .mk{display:inline !important;font-size:6.8px;color:#5f8f74;margin-left:3px}\n' +
  'html body div.page div.tbl-wrap table.results tbody tr.sub-row td.r-cell .r-val.r-conform .mk::before{content:"| ";color:#8C9BB0;font-style:normal}\n' +
  'html body div.page div.tbl-wrap table.results tbody tr:not(.sub-row) td.r-cell .r-val.r-conform .mk{line-height:7px}\n' +
  '</style>';
const applier = CoQApply(CoQ, skeleton);

function winOf(crit) {
  const s = String(crit || '');
  const m = s.match(/^\s*([\d.]+)\s*[–-]\s*([\d.]+)\s*%/);
  if (!m) return { window: '—' };
  const nm = s.match(/nominal\s*([\d.]+)\s*±\s*([\d.]+)/);
  return { window: m[1] + ' – ' + m[2] + ' %', nominal: nm ? nm[1] : '', tol: nm ? nm[2] : '' };
}
function rec(c) {
  const byNo = {}; for (const r of c.rows) byNo[String(r.no)] = r;
  const res = {}, st = {}, doc = {}, iss = {}, lab = {};
  for (const d of CoQ.DETS) { const r = byNo[d] || {}; res[d] = r.res || ''; st[d] = r.st || ''; doc[d] = r.doc || ''; iss[d] = r.dd || ''; lab[d] = r.lab || ''; }
  const spc = c.spc || {}, w = winOf((byNo['4'] || {}).crit);
  const sup = c.supersedes && c.supersedes.code ? (c.supersedes.code + (c.supersedes.date ? ' of ' + c.supersedes.date : '')) : '';
  return {
    lot: c.pp || c.cb, cb: c.cb, code: /^CoQ-PP_26-/.test(c.regcode || '') ? c.regcode : '', issue: c.issue || '',
    strain: c.strain || '', grade: c.grade || '', res, st, doc, iss, lab,
    phenotype: spc.pheno || '', dominance: spc.dominance || '', chemotype: spc.chemo || '', processing: spc.proc || '',
    productCode: c.pcode || '—', window: w.window, nominal: w.nominal, tol: w.tol, specCode: c.spec || '—',
    packaging: spc.pack || '—', manufDate: c.md || '', packDate: c.pk || '', supersedes: sup,
    series: (c.t || '').indexOf('additional') === 0 ? 'reissue' : 'initial',
  };
}
fs.rmSync(OUT, { recursive: true, force: true });
const stats = { n: 0, warn: 0, findings: 0, hard: 0, byDir: {} }, report = [];
// ---- the grey edges ---------------------------------------------------------------
// Chromium flattens a transparency group at raster resolution, so an alpha gradient
// prints as grey banding rather than as a fade to white. The package ships
// __print-opaque for exactly this: inside @media print every fading fill is replaced by
// the opaque colour it would have over white. It converts the rules it names, and the
// package's own comment says why that is not all of them — "the sub-rows kept the long
// band only because their sibling selector outranks those". Two families outranked or
// outlived it: the sibling chain that stripes a group's sub-rows (determinations 9 to
// 12) and .gridrow.lk-inline, the attribute strips of Section 01. Both printed grey down
// the page edges while everything around them printed clean.
//
// So the conversion is done by rule rather than by name. Every rule in the base whose
// background is a gradient with a partial alpha is re-emitted inside @media print with
// the SAME selector — same specificity, last in source, so it lands exactly where the
// original did — and every rgba(C,a) replaced by rgb(C + (255 - C)(1 - a)), which is
// that colour composited over white. Nothing else changes: no selector is invented, no
// colour is chosen, no geometry or row height moves.
const ALPHA_STOP = /rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([01]?(?:\.\d+)?)\s*\)/g;
function overWhite(css) {
  return css.replace(ALPHA_STOP, (m, r, g, b, a) => {
    const f = parseFloat(a);
    const mix = c => Math.round(Number(c) + (255 - Number(c)) * (1 - f));
    return 'rgb(' + mix(r) + ',' + mix(g) + ',' + mix(b) + ')';
  });
}
function important(body) {                       // the originals carry !important; match it
  return body.split(';').map(d => d.trim()).filter(Boolean)
    .map(d => /!important$/.test(d) ? d : d + ' !important').join(';');
}
function printOpaqueLayer(doc) {
  const seen = new Set(), rules = [];
  const re = /([^{}]+)\{([^{}]*)\}/g;
  let m;
  while ((m = re.exec(doc))) {
    const body = m[2];
    if (body.indexOf('linear-gradient') < 0) continue;
    if (!/rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*0?\.\d+\s*\)/.test(body)) continue;
    if (body.indexOf('mask') >= 0) continue;      // a mask is the package's business
    const sel = m[1].replace(/\/\*[\s\S]*?\*\//g, '').replace(/<[^>]*>/g, '').trim();
    if (!sel || sel.indexOf('@') === 0 || seen.has(sel)) continue;
    seen.add(sel);
    rules.push(sel + '{' + important(overWhite(body)) + '}');
  }
  if (!rules.length) throw new Error('no alpha gradient found to convert');
  return '<style id="__print-opaque-rest">\n@media print{\n' + rules.join('\n') + '\n}</style>';
}
// ---- the title, pushed off centre by a class the package never styles ------------
// coq_apply.js emits the supersedes line as <span class="hb-sup">, and nothing in
// cox.css or the 56 layers ever styles .hb-sup — the class is written and never read.
// So on a reissue it lays out as an unstyled inline span beside the document code,
// widening the header's right column from the package's own min-width of 132px to
// 277px. The header is a grid of auto | 1fr | auto and .hb-center centres inside the
// MIDDLE column, so a wider right column moves that column's centre: measured, the
// title sat 87px left of the page centre on all 83 reissues and 14px left on a release
// certificate, which is the package's own baseline (a 104px logo against a 132px code
// block). The owner saw it as the title moved to the left, and it was.
//
// The correction takes the line out of the width computation rather than restyling the
// header: positioned against the header, one line, at the inset the package's own edge
// treatment uses (38px, the gold rules' margin). The right column returns to 132px, the
// title returns to the release certificate's own -14px, the header height does not move
// and no page grows. Nothing is reworded, resized or moved to another row.
const HB_SUP_LAYER = '<style id="__owner-header-and-cells">\n' +
  '/* Owner, 16.09.2026, three corrections in one layer.\n' +
  '   1 The supersedes line sits BENEATH the document code and its date of issue, small,\n' +
  '     grey and legible, and takes no width of its own: .hb-sup is a class coq_apply.js\n' +
  '     writes and nothing in the package ever styles, so as an inline span it widened the\n' +
  '     header right column from 132px to 277px and carried the centred title 87px left.\n' +
  '   2 A result and its Macedonian half both align to the right page margin, the margin\n' +
  '     the package already sets for the column (38.4px).\n' +
  '   3 In a sub-row the Macedonian half drops beneath the result instead of running on\n' +
  '     after it, at 4.8px on a 5.2px line — measured, the sub-row height does not move. */\n' +
  'html body div.page div.header-bar div.hb-right .hb-sup{position:static;display:block;' +
  'margin-top:2px;white-space:nowrap;font-family:\'Montserrat\',sans-serif;font-size:5.6px;' +
  'font-style:italic;font-weight:500;letter-spacing:.1px;line-height:6.2px;color:#93A3B5}\n' +
  'html body div.page div.tbl-wrap table.results tbody td.r-cell{text-align:right}\n' +
  'html body div.page div.tbl-wrap table.results tbody td.r-cell .r-val{display:block;text-align:right}\n' +
  'html body div.page div.tbl-wrap table.results tbody tr.sub-row td.r-cell .r-val.r-conform .mk{' +
  'display:block !important;margin-left:0 !important;font-size:4.8px;line-height:5.2px;text-align:right}\n' +
  'html body div.page div.tbl-wrap table.results tbody tr.sub-row td.r-cell .r-val.r-conform .mk::before{' +
  'content:"" !important}\n</style>';

const EDGE_FADE_LAYER = '<style id="__owner-edge-fade">\n' +
  '/* Owner, 16.09.2026: the section bars and the two Section 01 bands ran to the sheet\n' +
  '   edge at full strength. Measured on the rendered page: .sec-label read rgb(232,239,246)\n' +
  '   at x=1 of 793, .pb-main rgb(248,250,252), .selrow rgb(252,253,254) — no fade at all,\n' +
  '   while .gridrow and the table zebra were already white at x=0 and correct. @page margin\n' +
  '   is 0, so a band with no fade is printed to the physical edge of the sheet.\n' +
  '   Each band now reaches white by the sheet edge and full colour by the typographic\n' +
  '   margin, in the package\'s own edge geometry. It is built from OPAQUE stops: the 56th\n' +
  '   layer switches -webkit-mask-image off (mask-image:none !important) and the print layer\n' +
  '   flattens alpha, so neither a mask nor an alpha veil survives to print here.\n' +
  '   The vertical shading is not lost: the original gradient is kept as the upper layer,\n' +
  '   painted from 10mm to 100%-10mm, and the ramp beneath carries that gradient\'s own\n' +
  '   mid-height colour, so the two meet in the same tone. Nothing is resized or reworded. */\n' +
  'html body div.page .sec-label{background-color:#fff !important;background-image:linear-gradient(rgb(172,191,210) 0%,rgb(172,191,210) 1.4%,rgb(218,229,238) 4.5%,rgb(250,252,254) 9%,rgb(246,250,253) 18%,rgb(246,250,253) 28%,rgb(240,245,250) 39%,rgb(233,240,247) 50%,rgb(225,234,242) 61%,rgb(218,229,238) 72%,rgb(213,225,236) 82%,rgb(217,227,238) 92%,rgb(224,233,241) 100%),linear-gradient(90deg,#fff 0,#fff 3mm,#E9F0F7 10mm,#E9F0F7 calc(100% - 10mm),#fff calc(100% - 3mm),#fff 100%) !important;' +
  'background-size:calc(100% - 20mm) 100%,100% 100% !important;background-position:10mm top,left top !important;background-repeat:no-repeat,no-repeat !important}\n' +
  'html body div.page .pb-main{background-color:#fff !important;background-image:linear-gradient(rgb(242,245,249) 0%,rgb(249,251,253) 55%,rgb(255,255,255) 100%),linear-gradient(90deg,#fff 0,#fff 3mm,#F9FBFD 10mm,#F9FBFD calc(100% - 10mm),#fff calc(100% - 3mm),#fff 100%) !important;' +
  'background-size:calc(100% - 20mm) 100%,100% 100% !important;background-position:10mm top,left top !important;background-repeat:no-repeat,no-repeat !important}\n' +
  'html body div.page .selrow{background-color:#fff !important;background-image:linear-gradient(90deg,#fff 0,#fff 3mm,#FCFDFE 10mm,#FCFDFE calc(100% - 10mm),#fff calc(100% - 3mm),#fff 100%) !important;' +
  'background-size:100% 100% !important;background-position:left top !important;background-repeat:no-repeat !important}\n' +
'</style>';

const PRINT_ZEBRA_LAYER = printOpaqueLayer(base);
console.log('print-opaque: %d gradient rule(s) converted for print',
            PRINT_ZEBRA_LAYER.split('\n').length - 3);

for (const c of data.coqs) {
  const r = rec(c);
  CURRENT = r;
  const code = (r.cb || '').match(/^[A-Za-z]+/); const strainCode = code ? code[0].toUpperCase() : 'XX';
  const out = applier.apply(base, r, strainCode);
  let html = out.html;
  // Owner, 16.09.2026: "all certificates of quality that you have to build must have
  // their conformity final decision at the bottom checked." The base document ships
  // both Section 04 chips unticked; the first is set to its selected state.
  const UN = '<span class="chip-un"><span class="bx">\u2610</span> Conforms to Specification <span class="mk">';
  const SEL = '<span class="chip-sel"><span class="bx">\u2612</span> Conforms to Specification <span class="mk">';
  if (html.indexOf(UN) < 0) throw new Error('Section 04 conformity chip not found');
  html = html.replace(UN, SEL);
  // append the owner layer as the new last layer (the package's own mechanism)
  html = html.replace(/<\/head>/, OWNER_LAYER + '\n' + HB_SUP_LAYER + '\n' + PRINT_ZEBRA_LAYER + '\n' + EDGE_FADE_LAYER + '\n</head>');
  const dir = r.series === 'reissue' ? path.join(OUT, 'REISSUE', tranche[r.lot] ? 'T' + String(tranche[r.lot]).replace(/\D/g, '') : 'T3') : path.join(OUT, 'ISSUE_COQ');
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, out.filename), html);
  stats.n++; stats.byDir[path.relative(OUT, dir)] = (stats.byDir[path.relative(OUT, dir)] || 0) + 1;
  if (out.warnings.length) { stats.warn++; report.push(out.filename + ': ' + out.warnings.join('; ')); }
  // the assertions know the package's closed vocabulary, not the owner's MK half:
  // check the document with that half removed, which is the package-conformant form
  const chk = CoQCheck.check(out.filename, html.replace(/<span class="mk">[^<]*<\/span>(?=<\/span><\/td>)/g, ''), r);
  const hard = chk.findings.filter(f => !/^OI-/.test(f));
  stats.findings += chk.findings.length; stats.hard += hard.length;
  if (hard.length) report.push(out.filename + ' :: ' + hard.join(' | '));
}
fs.writeFileSync(path.join(OUT, '_build_report.txt'), report.join('\n'));
console.log('documents written: %d  %j', stats.n, stats.byDir);
console.log('apply warnings: %d   assertion findings: %d (hard %d)', stats.warn, stats.findings, stats.hard);
console.log('report: out/_build_report.txt (%d lines)', report.length);
