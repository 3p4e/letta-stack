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
const SIGN = require(path.join(GAP, 'sign_block.js'));

// Two sets, from one build. The Head of QC, 17.09.2026: "remove all signatures from all
// certificates of quality" - so by default each signature box keeps its line and the
// space above it, to be signed by hand on the printed page, and nothing is placed there.
// The Head of QC, 18.09.2026, asked for the deposited hands to be applied as well and for
// both sets to exist side by side; PP_SIGNATURES=1 builds the signed one. See
// sign_block.js.

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
    series: (c.t || '').indexOf('retest') === 0 ? 'reissue' : 'initial',
  };
}
fs.rmSync(OUT, { recursive: true, force: true });
const stats = { n: 0, warn: 0, findings: 0, hard: 0, byDir: {} }, report = [], every = [];
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
const { printOpaqueLayer, overWhite, important } =
  require(path.join(HERE, 'print_opaque.js'));
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

const EDGE_FADE_LAYER = '<style id="__owner-edges">\n' +
  '/* Owner, 16.09.2026 (later pass): the section heading bars (01/02/03/04) go edge to\n' +
  '   edge — full bleed, not faded — so the desk no longer touches .sec-label at all and\n' +
  '   it prints as the package draws it, a full-width bar on a page with a zero printer\n' +
  '   margin. The bands and rows BENEATH the bars fade to pure white through the page\n' +
  '   margin, so no row colour reaches the sheet edge. Every fade here is a SINGLE straight\n' +
  '   ramp — white at the edge, full colour by the typographic margin (~11mm) — with no\n' +
  '   flat-then-ramp junction, so there is no hard transition to read. The masthead and\n' +
  '   the footer keep their full bleed by design. */\n' +
  'html body div.page .pb-main{background-color:#fff !important;background-image:' +
     'linear-gradient(90deg,#fff 0,rgb(244,247,251) 11mm,rgb(244,247,251) calc(100% - 11mm),#fff 100%) !important;' +
     'background-size:100% 100% !important;background-position:left top !important;background-repeat:no-repeat !important}\n' +
  'html body div.page .selrow{background-color:#fff !important;background-image:' +
     'linear-gradient(90deg,#fff 0,rgb(250,252,254) 11mm,rgb(250,252,254) calc(100% - 11mm),#fff 100%) !important;' +
     'background-size:100% 100% !important;background-position:left top !important;background-repeat:no-repeat !important}\n' +
  '/* The table header rules and body carry the same single straight ramp, so the grey\n' +
  '   header bar and the row tint blend to white through the margin without a kink. */\n' +
  'html body div.page div.tbl-wrap table.results thead tr,\n' +
  'html body div.page div.tbl-wrap table.labref thead tr{background-color:transparent !important;background-image:' +
     'linear-gradient(90deg,#fff 0,#9EACBA 12mm,#9EACBA calc(100% - 12mm),#fff 100%),' +
     'linear-gradient(90deg,#fff 0,#9EACBA 12mm,#9EACBA calc(100% - 12mm),#fff 100%),' +
     'linear-gradient(90deg,#fff 0,#F2F5F9 12mm,#F2F5F9 calc(100% - 12mm),#fff 100%) !important;' +
     'background-size:100% 1px,100% 1px,100% calc(100% - 2px) !important;' +
     'background-position:top left,bottom left,left top 1px !important;background-repeat:no-repeat !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody tr:last-child{background-color:transparent !important;background-image:' +
     'linear-gradient(90deg,#fff 0,#9EACBA 12mm,#9EACBA calc(100% - 12mm),#fff 100%) !important;' +
     'background-size:100% 1px !important;background-position:bottom left !important;background-repeat:no-repeat !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody tr:nth-child(even){background-color:transparent !important;background-image:' +
     'linear-gradient(90deg,#fff 0,rgb(247,249,252) 12mm,rgb(247,249,252) calc(100% - 12mm),#fff 100%) !important;' +
     'background-size:100% 100% !important;background-position:left top !important;background-repeat:no-repeat !important}\n' +
  '/* Owner, 17.09.2026: the heading bars printed with a distorted gradient. The package\n' +
  '   opens each bar with a dark stop, a 1px inset white highlight and a dark bottom inset —\n' +
  '   a dark/bright/dark stripe along the top that a laser printer renders as banding. The\n' +
  '   bar is now one smooth two-stop vertical gradient in the same tone, no inset shadows,\n' +
  '   one clean hairline along its bottom — full bleed, edge to edge, as asked. */\n' +
  'html body div.page .sec-label{box-shadow:none !important;background-color:#E6EDF5 !important;' +
     'background-image:linear-gradient(180deg,rgb(233,239,246) 0%,rgb(221,230,240) 100%) !important;' +
     'background-size:100% 100% !important;background-position:left top !important;background-repeat:no-repeat !important;' +
     'border-top:1px solid rgb(186,201,218) !important;border-bottom:1px solid rgb(168,188,209) !important}\n' +
  '/* Owner, 17.09.2026: the top of the bar was lost against the white above it — a hairline\n' +
  '   along the top edge, a shade lighter than the bottom one, and the top stop a touch deeper. */\n' +
  '/* Owner, 17.09.2026: every faded horizontal separator that was 2px is a hairline. */\n' +
  'html body div.page div.goldrule{height:1px !important}\n' +
  'html body div.page div.approval-grid .ap-line{height:1px !important}\n' +
  'html body div.page div.tbl-wrap table.results tbody tr.last-row,\n' +
  'html body div.page div.tbl-wrap table.labref tbody{background-size:100% 1px !important}\n' +
'</style>';

const INK_LAYER = '<style id="__owner-uniform-result-ink">\n' +
  '/* Owner, 16.09.2026: "make all certificates of quality analysis results column in\n' +
  '   heading 2 be one colour dark navy blue and do not use any other colour indicating\n' +
  '   edge cases of the analysis results or reds or any other colour than the uniform\n' +
  '   navy blue." The RESULT column is now one ink: --navy #1B3A5C, the colour .r-val\n' +
  '   already carries by default, for every cell — the 738 red, the 10 amber and the\n' +
  '   green Conforms alike, in both halves of a bilingual cell.\n' +
  '   The inline colour is left in the MARKUP on purpose. A12 reads it to prove that a\n' +
  '   result above its own criterion was marked, so stripping it would quietly disarm the\n' +
  '   desk\'s own check; overriding it here changes the ink on the page and nothing else.\n' +
  '   Note for the reader of the page: a result above its criterion no longer announces\n' +
  '   itself by colour. It is still legible against the ACC. CRITERIA column beside it,\n' +
  '   and Section 04 still carries the conformity decision. */\n' +
  'html body div.page div.tbl-wrap table.results td.r-cell .r-val,\n' +
  'html body div.page div.tbl-wrap table.results td.r-cell .r-val .mk,\n' +
  'html body div.page div.tbl-wrap table.results td.r-cell .r-val.r-conform,\n' +
  'html body div.page div.tbl-wrap table.results td.r-cell .r-val.r-conform .mk{color:#1B3A5C !important}\n' +
'</style>';

// Owner, 16.09.2026 (second pass): the Section 03 cross-reference table and the Section
// 04 conformity row are re-aligned, the signature roles given air, and the two managers'
// signatures reapplied. Appended as one new last layer over the package's own stack; the
// selectors carry the full html body div.page ... chain so they win the cascade, and
// nothing is resized on the results table or reworded.
const S34_LAYER = '<style id="__owner-align-s1-s4">\n' +
  '/* Owner, 16.09.2026 (alignment pass): Sections 01-04 re-aligned. One appended layer,\n' +
  '   full html body div.page ... selectors so it wins the cascade; nothing on the results\n' +
  '   table is resized or reworded. */\n' +
  '/* -- Section 01 -- the info rows centre their label and value on the row; the\n' +
  '   manufacturer\'s Macedonian line is smaller and its cell content reads left, with the\n' +
  '   production-batch / manufacture-date / packaging-date group given room. */\n' +
  'html body div.page div.gridrow.lk-inline > .lk{align-items:center !important}\n' +
  'html body div.page div.gridrow.lk-inline .lk-lbl{align-self:center !important}\n' +
  'html body div.page div.gridrow.lk-inline .lk-val{align-self:center !important}\n' +
  'html body div.page div.gridrow.lk-inline .lk .attr-val{align-self:center !important;text-align:left !important}\n' +
  'html body div.page div.gridrow.lk-inline .lk .attr-val .mk{font-size:5.8px !important;line-height:1.15 !important}\n' +
  '/* -- Section 02 -- acceptance criteria reads left, centred on the row; the result\n' +
  '   reads to the right page margin, centred on the row; the parameter and number cells\n' +
  '   read left off the margin, centred on the row, keeping the sub-row indents of #9/#10/#11. */\n' +
  'html body div.page div.tbl-wrap table.results tbody td{vertical-align:middle !important;padding-bottom:0.5px !important}\n' +
  'html body div.page div.tbl-wrap table.results tbody td:nth-child(4){text-align:left !important;vertical-align:middle !important}\n' +
  'html body div.page div.tbl-wrap table.results tbody td.r-cell{text-align:right !important;vertical-align:middle !important;padding-right:var(--MARGIN-H) !important}\n' +
  'html body div.page div.tbl-wrap table.results tbody td.r-cell .r-val{text-align:right !important}\n' +
  '/* -- Section 03 -- laboratory column left to the page margin as clean lines, CoA codes\n' +
  '   centred on the row, parameter numbers to the right page margin, headers following\n' +
  '   their columns, issue dates smaller and grey. */\n' +
  'html body div.page div.tbl-wrap table.labref{table-layout:fixed !important}\n' +
  'html body div.page div.tbl-wrap table.labref colgroup col:nth-child(2){width:218px !important}\n' +
  'html body div.page div.tbl-wrap table.labref colgroup col:nth-child(3){width:172px !important}\n' +
  'html body div.page div.tbl-wrap table.labref thead th:first-child,\n' +
  'html body div.page div.tbl-wrap table.labref tbody td:first-child{text-align:left !important;padding-left:var(--MARGIN-H) !important}\n' +
  'html body div.page div.tbl-wrap table.labref thead th:nth-child(2),\n' +
  'html body div.page div.tbl-wrap table.labref tbody td.lr-mono:not(.pcell){text-align:center !important;vertical-align:middle !important}\n' +
  'html body div.page div.tbl-wrap table.labref thead th:nth-child(3),\n' +
  'html body div.page div.tbl-wrap table.labref tbody td.pcell{text-align:right !important;vertical-align:middle !important;padding-right:var(--MARGIN-H) !important;white-space:nowrap !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td .lr-lab{display:block !important;line-height:1.32 !important;text-align:left !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td .lr-lab .bisep{display:none !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td .lr-lab .mk{display:block !important;margin-left:0 !important;margin-top:1px !important;white-space:normal !important;line-height:1.25 !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td .lr-lab small{display:block !important;margin-top:1px !important;white-space:normal !important;line-height:1.2 !important;color:#7C8FA6 !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td .lr-lab small::before{content:"" !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td.lr-mono:not(.pcell){display:table-cell !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td.lr-mono:not(.pcell) .cert{display:block !important;text-align:center !important;white-space:nowrap !important;margin-top:0 !important;min-width:0 !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td.lr-mono:not(.pcell) .cert + .cert{margin-top:2px !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td.lr-mono .cert .cd{font-size:6.6px !important;font-weight:600 !important;color:#8C9BB0 !important;white-space:nowrap !important}\n' +
  '/* -- Section 04 -- the row packs to the left: the label (two lines) left, then the\n' +
  '   batch number in a box as tall as the label with its value centred, then the two\n' +
  '   verdict pills beside it, their content centred. The package\'s spreading auto-margins\n' +
  '   are removed. */\n' +
  'html body div.page div.disp-row{align-items:stretch !important}\n' +
  'html body div.page div.disp-row .grp{display:flex !important;flex-wrap:nowrap !important;justify-content:flex-start !important;align-items:stretch !important;gap:12px !important}\n' +
  'html body div.page div.disp-row .grp .lk-lbl{flex:0 0 auto !important;margin:0 !important;text-align:left !important;align-self:center !important;white-space:nowrap !important}\n' +
  'html body div.page div.disp-row .grp .lk-lbl .mk{display:block !important;margin-left:0 !important;text-align:left !important}\n' +
  'html body div.page div.disp-row .grp .lk-lbl .mk::before{content:none !important}\n' +
  'html body div.page div.disp-row .grp .lk-lbl .bisep{display:none !important}\n' +
  'html body div.page div.disp-row .grp .lk-lbl + *{margin-left:0 !important}\n' +
  'html body div.page div.disp-row .grp .disp-batch{flex:0 0 auto !important;align-self:stretch !important;display:flex !important;align-items:center !important;justify-content:center !important;text-align:center !important;min-width:104px !important;max-width:132px !important;padding:1px 10px !important;margin:0 !important;border:1px solid #C6D4E2 !important;border-radius:6px !important;background:linear-gradient(180deg,#FFFFFF 0%,#F6FAFD 100%) !important;font-size:13px !important;font-weight:700 !important;color:#1B3A5C !important;box-shadow:inset 0 1px 0 rgba(255,255,255,.6),0 1px 1.5px rgba(21,46,74,.12) !important}\n' +
  'html body div.page div.disp-row .grp .disp-batch + *{margin-left:0 !important}\n' +
  'html body div.page div.disp-row .grp .chip-sel,\n' +
  'html body div.page div.disp-row .grp .chip-un{flex:0 0 auto !important;align-self:stretch !important;display:inline-flex !important;align-items:center !important;justify-content:center !important;text-align:center !important;margin:0 !important}\n' +
  'html body div.page div.approval-grid .ap-role{padding-top:4px !important}\n' +
  'html body div.page div.approval-grid .ap-sign{height:32px !important}\n' +
  '/* Owner, 17.09.2026: on content-heavy certificates the lower stack (Section 03\'s three\n' +
  '   laboratory lines and the signature block) reached into the footer. The block and the\n' +
  '   lower sections are compacted so every certificate clears the footer, with no page\n' +
  '   growth and the three-line laboratory layout kept. */\n' +
  'html body div.page div.approval-grid{padding-top:0 !important}\n' +
  'html body div.page div.approval-grid .ap-name{margin-top:1px !important}\n' +
  'html body div.page div.approval-grid .ap-cred{margin-top:0 !important}\n' +
  'html body div.page div.approval-grid .ap-date-row{margin-top:1px !important}\n' +
  'html body div.page div.tbl-wrap + div.sec-label,html body div.page div.disp-row + div.goldrule{margin-top:5px !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td{padding-top:0 !important;padding-bottom:0 !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td .lr-lab{line-height:1.2 !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td .lr-lab small{font-size:6px !important;line-height:1.08 !important}\n' +
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
  // Append the desk's layers as the new LAST layers in the document. The package appends
  // its own final correction layers (__labref-ac-certgrid, __lk-shrink-fit, __sig-space)
  // at the end of the body, not in the head — so a desk layer in the head loses to them at
  // equal specificity. Placing the desk's layers right before </body>, after everything
  // the package appended, is the package's own "new last layer" mechanism done correctly.
// Section 03 in two lines per laboratory and one line of documents (Head of QC, 17.09.2026):
// "make the laboratory credentials two rows each, the document codes and dates in one row,
// in line, so the reference table takes the least height — and use the room to lighten the
// cramped spaces." Line 1 is the laboratory and its accreditation standard; line 2 its
// Macedonian name, accreditation number and address, small and grey. The certificates flow
// inline, each code with its date kept together, a light bar between documents.
const S03_LAYER = '<style id="__owner-s03-compact">\n' +
  // A certificate whose code carries a product note prints the note under the code, in
  // the reference column's own mono face at the size the Macedonian half uses. It is a
  // qualifier on the citation, not part of the code, so it never reads as one.
  'html body div.page div.tbl-wrap table.labref tbody td .cert .cert-note{display:block;font-style:italic;font-weight:500;font-size:5.9px;line-height:1.1;color:#6E7D92;letter-spacing:0}\n' +
  'html body div.page div.tbl-wrap table.labref colgroup col:nth-child(2){width:248px !important}\n' +
  'html body div.page div.tbl-wrap table.labref colgroup col:nth-child(3){width:172px !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td{padding-top:1px !important;padding-bottom:1px !important;vertical-align:middle !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td:first-child{padding-right:6px !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td .lr-lab{display:block !important;line-height:1.12 !important;text-align:left !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td .lr-lab .bisep{display:block !important;height:0 !important;font-size:0 !important;line-height:0 !important;overflow:hidden !important;margin:0 !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td .lr-lab .mk{display:inline !important;margin:0 !important;white-space:normal !important;line-height:1.15 !important;font-size:5.9px !important;color:#6E7D92 !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td .lr-lab .mk .lr-ac{margin-left:2px !important;font-size:5.9px !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td .lr-lab small{display:inline !important;margin:0 !important;white-space:normal !important;line-height:1.15 !important;font-size:5.9px !important;color:#7C8FA6 !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td .lr-lab small::before{content:" · " !important;color:#B3BFCC !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td.lr-mono:not(.pcell){line-height:1.3 !important;padding-left:4px !important;padding-right:4px !important}\n' +
  '/* Head of QC, 17.09.2026: the laboratory table was taking too much height — rows tight; the room\n' +
  '   goes to air after every heading bar, and a little more under the first one. */\n' +
  'html body div.page div.sec-label{margin-bottom:5px !important}\n' +
  'html body div.page div.sec-label + div.pb-main,html body div.page div.sec-label + .pb-main{margin-top:3px !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td.lr-mono:not(.pcell) .cert{display:inline-block !important;margin:0 !important;white-space:nowrap !important;vertical-align:baseline !important;font-size:7px !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td.lr-mono:not(.pcell) .cert + .cert{margin-top:0 !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td.lr-mono:not(.pcell) .cert + .cert::before{content:"|" !important;color:#C6D4E2 !important;font-weight:400 !important;margin:0 3px !important}\n' +
  'html body div.page div.tbl-wrap table.labref tbody td.lr-mono .cert .cd{font-size:6.2px !important}\n' +
  '/* the room the table gives back goes to air between the sections and around the signatures */\n' +
  'html body div.page div.tbl-wrap + div.sec-label,html body div.page div.disp-row + div.goldrule{margin-top:8px !important}\n' +
  'html body div.page div.approval-grid{padding-top:3px !important}\n' +
  'html body div.page div.approval-grid .ap-sign{height:34px !important}\n' +
  '</style>';

// Head of QC, 18.09.2026, after the processing group came off Section 01: "distribute
// the other items in the same row equally and align them suitably to the column
// distribution ... because there will be more space in that row you can increase the size
// of the parameter and the placeholder value."
// The row was flex with justify-content:space-between. Right for three groups, wrong for
// two - it throws Phenotype against the left page margin and Chemotype against the right
// with a hole between them. It becomes a three-track grid on the same 38.4 px margin the
// rows beneath it use: two columns of equal width, each group reading from its own
// column's left border rather than from a page edge (Head of QC, 18.09.2026 - "that first
// row will be in two columns ... the second column should have its content aligned to the
// left border"). The width the third group gave back is spent on type -
// the label, its Macedonian line and the option chips all rise about 17 %, the step the
// type took in Sections 03 and 04. The results table is not touched.
const S01_LAYER = '<style id="__owner-s01-selrow">\n' +
  'html body div.page div.selrow{display:grid !important;grid-template-columns:repeat(2,minmax(0,1fr)) !important;justify-content:stretch !important;justify-items:start !important;align-items:center !important;column-gap:12px !important;row-gap:0 !important}\n' +
  'html body div.page div.selrow > span.grp{display:inline-flex !important;align-items:center !important;gap:9px !important;min-width:0 !important;white-space:nowrap !important;flex:0 0 auto !important}\n' +
  'html body div.page div.selrow > span.grp:first-child{grid-column:1 !important}\n' +
  'html body div.page div.selrow > span.grp:last-child{grid-column:2 !important}\n' +
  'html body div.page div.selrow span.lk-lbl{font-size:8.4px !important;letter-spacing:.34px !important;line-height:1.12 !important}\n' +
  'html body div.page div.selrow span.lk-lbl > span.mk{font-size:6.9px !important;line-height:1.08 !important}\n' +
  'html body div.page div.selrow span.chip-sel{font-size:8.6px !important;padding:1.8px 6.5px 1.8px 5px !important;border-radius:9px !important}\n' +
  'html body div.page div.selrow span.chip-un{font-size:7.5px !important;padding:1.3px 6px !important;border-radius:9px !important}\n' +
  'html body div.page div.selrow span.chip-sel > span.bx{font-size:10.6px !important}\n' +
  'html body div.page div.selrow span.chip-un > span.bx{font-size:9.6px !important}\n' +
  'html body div.page div.selrow span.grp > span.stack{gap:7px !important}\n' +
  '</style>';


// The white band under the section 01 bar (Head of QC, 18.09.2026: "expand the background
// that is in that section"). Measured on the page: the bar ends at 154.80 and the product
// row begins at 162.80 - 8 px of page-white between the bar's blue and the row's gradient,
// from 5 px of margin below the bar and 3 px above the row. Both go to zero and the row
// takes the 8 px into its own padding-top, so its gradient fills the gap and NOTHING below
// moves: the row's first line of type sits at 174.80 either way. Only the bar that follows
// the masthead is scoped - the other three section labels keep their spacing, the page
// around them being white in any case.
const S01_BAND_LAYER = '<style id="__owner-s01-band">\n' +
  'html body div.page div.header-bar + div.sec-label{margin-bottom:0 !important}\n' +
  'html body div.page div.sec-label + div.pb-main,html body div.page div.sec-label + .pb-main{margin-top:0 !important;padding-top:12px !important}\n' +
  '</style>';
  const DESK_LAYERS = OWNER_LAYER + '\n' + HB_SUP_LAYER + '\n' + PRINT_ZEBRA_LAYER + '\n' + EDGE_FADE_LAYER + '\n' + INK_LAYER + '\n' + S34_LAYER + '\n' + S03_LAYER + '\n' + S01_LAYER + '\n' + S01_BAND_LAYER + '\n';
  if (html.indexOf('</body>') < 0) throw new Error('no </body> to append the desk layers before');
  html = html.replace('</body>', DESK_LAYERS + '</body>');
  // Owner, 16.09.2026 (second pass): the issue date in the Section 03 code column is
  // wrapped so the layer above can size and grey it. The package emits it as a bare text
  // node after the code, "<b>CODE</b> · DATE"; wrapping is a markup change, so it is
  // done here in the desk's adapter, not in the package's builder.
  html = html.replace(/(<span class="cert"><b>[^<]*<\/b>)\s*·\s*([^<]*)<\/span>/g,
                      '$1 <i class="cd">· $2</i></span>');
  // The signature boxes (Head of QC, 17.09.2026 and 18.09.2026). Unsigned, each box is a
  // rule with clear space above it, to be signed by hand on the printed page, and the
  // build refuses a document that would carry a scan. Signed - PP_SIGNATURES=1 - the two
  // deposited hands are applied over the rule, one iteration of nineteen per certificate,
  // tilted and offset from the same hash so a reprint is identical and the fleet is not
  // nineteen copies of one press. Nothing else on the page moves either way.
  // The house fallback chain (Head of QC, 18.09.2026: "you have not rendered and used the
  // fonts that are there and I explicitly want those fonts used in our certificates").
  // Orbitron is a Latin display face: it carries no Cyrillic, no \u2116 and no \u0394. It sets the
  // approval roles and titles, the section labels and the badges, so every Macedonian word
  // inside one of them left the house set and was drawn by the renderer's own Liberation
  // Sans - visible in the printed PDF as LiberationSans-Bold on "\u0418\u0417\u0413\u041e\u0422\u0412\u0418\u041b \u0418 \u041e\u0414\u041e\u0411\u0420\u0418\u041b" and
  // "\u041c\u0415\u041d\u0410\u040f\u0415\u0420 \u0417\u0410 \u041a\u041a". Naming Montserrat after Orbitron changes no Latin glyph - Chromium
  // falls through a stack per GLYPH, not per element - and puts the rest in the house face.
  html = html.replace(/font-family:'Orbitron',sans-serif/g, "font-family:'Orbitron','Montserrat',sans-serif")
             .replace(/font-family:'Orbitron',monospace/g, "font-family:'Orbitron','Montserrat',monospace");
  if (SIGN.enabled()) html = SIGN.sign(html, c.regcode || out.filename, { h: 60, dy: -10 });
  else if (/class="ap-img/.test(html)) throw new Error('a signature image reached the page: ' + c.regcode);
  // Owner, 21.09.2026: "empty results should not be included. There should be no
  // 'not tested' results in the retest CoQs."
  //
  // Until today every empty result cell was rewritten here from [ — ] to [NT] and the
  // Section 02 note glossed the abbreviation bilingually. Both are gone. A determination
  // with no result now prints an empty cell (coq_build.js `cell()`), and there is no
  // abbreviation left to gloss. The row itself stays — twenty-one determinations in the
  // specification's order — and so does the assay note the * on rows 4, 5 and 6 points at.
  // What is removed from the note is only the procedural sentence the owner struck on
  // 16.09.2026, which carried the only document code on the line.
  let htmlOut = html;
  const OLD_NOTE = /<br>Parameter attribution to the issuing laboratory[^<]*<\/div>/;
  if (!OLD_NOTE.test(htmlOut)) throw new Error('Section 02 note sentence not found');
  htmlOut = htmlOut.replace(OLD_NOTE, '</div>');
  const dir = r.series === 'reissue' ? path.join(OUT, 'REISSUE', tranche[r.lot] ? 'T' + String(tranche[r.lot]).replace(/\D/g, '') : 'T3') : path.join(OUT, 'ISSUE_COQ');
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, out.filename), htmlOut);
  stats.n++; stats.byDir[path.relative(OUT, dir)] = (stats.byDir[path.relative(OUT, dir)] || 0) + 1;
  if (out.warnings.length) { stats.warn++; report.push(out.filename + ': ' + out.warnings.join('; ')); }
  // the assertions know the package's closed vocabulary, not the owner's MK half:
  // check the document with that half removed, which is the package-conformant form
  const chk = CoQCheck.check(out.filename, html.replace(/<span class="mk">[^<]*<\/span>(?=<\/span><\/td>)/g, ''), r);
  const hard = chk.findings.filter(f => !/^OI-/.test(f));
  stats.findings += chk.findings.length; stats.hard += hard.length;
  if (hard.length) report.push(out.filename + ' :: ' + hard.join(' | '));
  // the OI- findings are observations the register already carries — an out-of-spec figure the
  // owner has marked, an assay outside its window, a determination credited to an external
  // certificate. They do not stop a document, but a gate whose soft half is invisible cannot
  // be audited, so every finding is written out as well, hard and soft alike.
  for (const f of chk.findings) every.push(out.filename + ' :: ' + f);
}
fs.writeFileSync(path.join(OUT, '_build_report.txt'), report.join('\n'));
fs.writeFileSync(path.join(OUT, '_findings_all.txt'), every.join('\n'));
console.log('documents written: %d  %j', stats.n, stats.byDir);
console.log('apply warnings: %d   assertion findings: %d (hard %d)', stats.warn, stats.findings, stats.hard);
console.log('report: out/_build_report.txt (%d lines)', report.length);
console.log('every finding: out/_findings_all.txt (%d lines)', every.length);
