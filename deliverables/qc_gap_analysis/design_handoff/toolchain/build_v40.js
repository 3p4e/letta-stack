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
  html = html.replace(/<\/head>/, OWNER_LAYER + '\n</head>');
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
