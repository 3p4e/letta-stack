// The internal certificates, built from the register that cites them.
//
//     node icoa_handoff/v3/build_from_register.js [OUTDIR]
//
// `build_fleet.js` prints the 172 from `icoa_v44_recs.json`, a record file the register
// has since moved past: of the 172 pairs, the lot the record file gives a number and the
// lot the certificate of quality gives the same number agreed on **six**. Three fleets on
// disk disagree pairwise about `iCoA-PP_26-085` alone — the v44 record calls it GG012603,
// `icoa_handoff/out` calls it P060382 and the signed set calls it P160022. A number that
// names three lots is not a number.
//
// So this builds from the one record the certificates actually cite. Each internal
// certificate is synthesised from the certificate of quality that names it: its lot, its
// strain, its series, its tested and issue dates, and the results its own rows 1, 2 and 7
// carry. One certificate of quality, one internal certificate, the same number on both —
// the Head of QC's ruling of 23.09.2026 — and the lot is the lot by construction rather
// than by a lookup that can drift.
//
// The generator itself is untouched: `icoa3_gen.js` is the design system and is called
// exactly as `build_fleet.js` calls it. Only the records come from somewhere else.
//
// Three options, all off by default so a plain run prints exactly what it printed before:
//
//   --retest             only the retest series, in certificate-number order
//   --sig-scale 1.20     the deposited hands 20 % larger, so they cross the rule instead of
//                        sitting on it (Head of QC, 23.09.2026: "increase the signatures to
//                        overflow the horizontal signature line ... 15 % or 20 % bigger").
//                        PP_SIGNATURES=1 must also be set; signing stays opt-in.
//   --print-flat         the page made print-safe before it is printed, rather than leaving
//                        a RIP to flatten it: every fading fill replaced by the opaque
//                        colour it would have over white (the same printOpaqueLayer the
//                        certificates of quality use), text-shadow and box-shadow off, and
//                        the signature's multiply blend set to normal. Chromium flattens a
//                        transparency group at raster resolution, which is what prints as
//                        grey banding; and it draws a text-shadow by painting the glyphs a
//                        SECOND time, which is what doubles every chip in the text layer.
//                        Nothing moves and no colour is chosen: only what paints the page
//                        behind the ink is converted, and the two shadow families are off.
const fs = require('fs'), path = require('path');
const HERE = __dirname, GAP = path.resolve(HERE, '../..');
const SIGN = require(path.join(GAP, 'sign_block.js'));
const { printOpaqueLayer } = require(path.join(GAP, 'design_handoff', 'toolchain', 'print_opaque.js'));

const argv = process.argv.slice(2);
const flag = n => argv.indexOf(n) >= 0;
const val = (n, d) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : d };
const RETEST_ONLY = flag('--retest');
const SIG_SCALE = parseFloat(val('--sig-scale', '1')) || 1;
const PRINT_FLAT = flag('--print-flat');

// The print-safe layer, appended last so it outranks the document's own rules. A blanket
// selector rather than a list of them: the owner's planned source fix names
// .chip-sel/.chip-un/.sec-label/.sec-no/.mk/.pb-grade/.stmt .badge, and a blanket rule
// cannot miss the one that was not on the list.
const FLAT_CSS =
  '<style id="__print-flat">\n@media print{\n' +
  '*,*::before,*::after{text-shadow:none !important;box-shadow:none !important}\n' +
  '.ap-sign img.ap-img{mix-blend-mode:normal !important}\n' +
  '}</style>';
// The Head of QC, 24.09.2026: "from all iCOA please remove the QA manager signature ... and
// arrange the two remaining signatures like in the COQs."
//
// The internal certificate of analysis is a QC laboratory record: the Analyst performs it and
// the QC Manager approves it. The QA Manager's review belongs on the certificate of quality,
// and her block comes off this family entirely — role line, name, credential, date and rule.
//
// The two that remain then take the certificate of quality's own geometry. Nothing in the
// design system is edited to do it: `.approval-grid.cols-2` is already defined in _icoa.css,
// `1fr 1fr` with a 110 px gap, the same rule the certificate of quality uses. The grid is
// simply told it has two columns instead of three.
//
// The blocks are found by balancing the grid's own <div>s rather than by a pattern over the
// whole document, and the reviewer by the NAME printed beneath the rule — the same rule
// sign_block.js follows. A grid that does not hold exactly three blocks, or that holds no
// reviewer, stops the build: a signature panel is not something to repair by guesswork.
const REVIEWER = 'Jovana Romevska Cvetkovski';
function dropReviewer(html, code) {
  const open = html.indexOf('<div class="approval-grid cols-3">');
  if (open < 0) throw new Error('no three-column approval grid on ' + code);
  const bodyAt = html.indexOf('>', open) + 1;
  // walk the grid's children, balancing <div> against </div>
  const kids = [];
  let i = bodyAt, depth = 0, start = -1;
  const tag = /<\/?div\b[^>]*>/g;
  tag.lastIndex = bodyAt;
  let m;
  while ((m = tag.exec(html))) {
    if (m[0][1] !== '/') { if (depth === 0) start = m.index; depth++; }
    else {
      depth--;
      if (depth === 0) kids.push([start, tag.lastIndex]);
      if (depth < 0) { i = m.index; break; }          // the grid's own closing tag
    }
  }
  if (kids.length !== 3) throw new Error('the approval grid on ' + code + ' holds ' + kids.length + ' blocks, not 3');
  const which = kids.findIndex(k => html.slice(k[0], k[1]).indexOf('>' + REVIEWER + '<') >= 0);
  if (which < 0) throw new Error('no reviewer block on ' + code);
  const kept = kids.filter((_, n) => n !== which).map(k => html.slice(k[0], k[1]));
  const grid = '<div class="approval-grid cols-2">\n' + kept.join('\n') + '\n</div>';
  const out = html.slice(0, open) + grid + html.slice(i + '</div>'.length);
  if (out.indexOf(REVIEWER) >= 0) throw new Error('the reviewer is still named on ' + code);
  if (out.indexOf('approval-grid cols-3') >= 0) throw new Error('a three-column grid survived on ' + code);
  return out;
}

const build = new Function('return (' + fs.readFileSync(path.join(HERE, 'icoa3_gen.js'), 'utf8') + ')')();

const data = JSON.parse(fs.readFileSync(path.join(GAP, 'coq_artifact_data.json'), 'utf8'));
// phenotype, processing and the strain code are production attributes; they live on the
// desk's own plan and nowhere else. Grade and the specification code come off the
// certificate of quality, which is authoritative for both.
const plan = JSON.parse(fs.readFileSync(path.join(HERE, 'ISSUE_iCOA/_generator/coq_plan.json'), 'utf8'));
const meta = {};
for (const p of plan) if (!meta[p.rec.cult])
  meta[p.rec.cult] = { strainCode: p.strainCode, phenotype: p.rec.phenotype, processing: p.rec.processing };

const positional = argv.filter((a, i) => a.indexOf('--') !== 0 &&
  !(i > 0 && argv[i - 1] === '--sig-scale'));
// The internal certificate links its three stylesheets rather than carrying them, so the
// gradients printOpaqueLayer converts live in the sheets and not in the document. The layer
// is therefore built once from the sheets in the order the page links them, and appended to
// every document — which is also true after build_selfcontained.py folds those same sheets
// in, because the layer comes last either way.
const SHEETS = ['_icoa.css', '_coq-rules.css', '_icoa3-print.css'];
const OPAQUE = PRINT_FLAT ? printOpaqueLayer(SHEETS.map(n =>
  fs.readFileSync(path.join(HERE, 'ISSUE_iCOA', n), 'utf8')).join('\n')) : '';

const out = positional[0] || path.join(HERE, 'build_register');
const rows = [];
let noPheno = 0;
const wanted = data.coqs
  .filter(c => !RETEST_ONLY || !/^initial release/.test(String(c.t || '')))
  .sort((a, b) => String(a.regcode).localeCompare(String(b.regcode)));
for (const c of wanted) {
  const r = {}; for (const x of c.rows || []) r[String(x.no)] = x;
  const initial = /^initial release/.test(String(c.t || ''));
  const m = meta[String(c.cb)] || {};
  if (!m.phenotype) noPheno++;
  const rec = {
    code: c.icoa_code,
    series: initial ? 'initial release' : 'retest 1',
    strain: c.strain, p: c.pp, cu: c.cb,
    tested: c.icoa_tested || '', packaging: c.pk || '', issued: c.icoa_issue || '',
    identA: (r['1'] || {}).res || '', identB: (r['2'] || {}).res || '', fm: (r['7'] || {}).res || '',
  };
  const o = build(rec, Object.assign({ grade: c.grade, specCode: c.spec }, m));
  o.html = dropReviewer(o.html, rec.code);   // the ruling of 24.09.2026, before any ink is laid
  o.html = SIGN.sign(o.html, rec.code, { h: 52 * SIG_SCALE, dy: -9 });
  if (PRINT_FLAT) {
    o.html = o.html.replace('</body>', OPAQUE + '\n' + FLAT_CSS + '\n</body>');
    if (o.html.indexOf('__print-flat') < 0) throw new Error('the print-safe layer did not land on ' + rec.code);
  }
  const f = path.join(out, o.path);
  fs.mkdirSync(path.dirname(f), { recursive: true });
  fs.writeFileSync(f, o.html);
  rows.push([rec.code, c.regcode, rec.cu, rec.p, rec.strain, o.dir, rec.series,
             rec.tested, rec.issued, o.conforms ? 'conforms' : 'open',
             o.cnp ? 'carried' : 'in-house', o.path].join('\t'));
}
fs.mkdirSync(out, { recursive: true });
fs.writeFileSync(path.join(out, '_built.tsv'),
  'icoa\tcoq\tcu\tp\tstrain\tdir\tseries\ttested\tissued\tconforms\tsource\tpath\n' + rows.join('\n') + '\n');
console.log('internal certificates built from the register: %d%s', rows.length,
            RETEST_ONLY ? ' (the retest series only)' : '');
console.log('  signatures: %s   size: %d%% of nominal   print-safe layer: %s',
            SIGN.enabled() ? 'applied' : 'off (set PP_SIGNATURES=1)',
            Math.round(SIG_SCALE * 100), PRINT_FLAT ? 'yes' : 'no');
console.log('  conforming: %d   open: %d', rows.filter(r => r.includes('\tconforms\t')).length,
            rows.filter(r => r.includes('\topen\t')).length);
console.log('  no cultivar record on file (boxes stay open): %d', noPheno);
