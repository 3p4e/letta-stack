// The three iCOA_FIN tranche folders, rebuilt locally from the record they were printed from.
//
//     PP_SIGNATURES=1 node icoa_handoff/v3/build_drive_fin.js T1 OUT [--sig-scale 1.20] [--print-flat]
//
// The Head of QC asked for the documents in
// `ISSUE_iCOA/iCOA_FIN/{iCOA_T1,iCOA_T2,iCOA_T3}` converted. Those files cannot be pulled
// down — 178 of them at ~775 KB each does not fit through the tooling — but they do not
// need to be: they were printed from `icoa_v44_recs.json` and `icoa3_gen.js`, both of which
// are in this repository, so the same records print the same pages. Which code belongs to
// which folder is taken from the owner's own `_MANIFEST.tsv`, read off Drive and recorded
// verbatim in `drive_fin/tranches.json` — 178 codes, every one present in the record file,
// every INIT/RET placement agreeing with the record's own series, no duplicates.
//
// **This is the v44 fleet.** It is not the register's: 215 planned rounds rather than 172
// certificates, up to five retests on one lot where the ruling of 18.09.2026 allows one,
// the pre-ruling cultivar spellings, and numbering that does not pair with the certificates
// of quality. That is stated here so nobody mistakes these pages for the current ones.
const fs = require('fs'), path = require('path');
const HERE = __dirname, GAP = path.resolve(HERE, '../..');
const SIGN = require(path.join(GAP, 'sign_block.js'));
const { printOpaqueLayer } = require(path.join(GAP, 'design_handoff', 'toolchain', 'print_opaque.js'));
const build = new Function('return (' + fs.readFileSync(path.join(HERE, 'icoa3_gen.js'), 'utf8') + ')')();

const argv = process.argv.slice(2);
const tranche = argv[0], out = argv[1];
if (!/^T[123]$/.test(tranche || '') || !out) throw new Error('usage: build_drive_fin.js T1|T2|T3 OUTDIR');
const flag = n => argv.indexOf(n) >= 0;
const val = (n, d) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : d };
const SIG_SCALE = parseFloat(val('--sig-scale', '1')) || 1;
// how deep the pen sat below the rule. sign_block.js's own default is -9; the Head of QC,
// 23.09.2026, asked for the hands to "overflow the horizontal separator" further, so this
// is an argument rather than an edit to the shared module.
const SIG_DY = parseFloat(val('--sig-dy', '-9'));
const PRINT_FLAT = flag('--print-flat');

const index = JSON.parse(fs.readFileSync(path.join(HERE, 'drive_fin', 'tranches.json'), 'utf8'));
const recs = {}; for (const r of JSON.parse(fs.readFileSync(path.join(HERE, 'ISSUE_iCOA/_generator/icoa_v44_recs.json'), 'utf8'))) recs[r.code] = r;
const plan = JSON.parse(fs.readFileSync(path.join(HERE, 'ISSUE_iCOA/_generator/coq_plan.json'), 'utf8'));
const meta = {}; for (const p of plan) if (!meta[p.rec.cult]) meta[p.rec.cult] = Object.assign({ strainCode: p.strainCode }, p.rec);

// the same print-safe layer the signed retest set was printed with
const SHEETS = ['_icoa.css', '_coq-rules.css', '_icoa3-print.css'];
const OPAQUE = PRINT_FLAT ? printOpaqueLayer(SHEETS.map(n =>
  fs.readFileSync(path.join(HERE, 'ISSUE_iCOA', n), 'utf8')).join('\n')) : '';
const FLAT_CSS =
  '<style id="__print-flat">\n@media print{\n' +
  '*,*::before,*::after{text-shadow:none !important;box-shadow:none !important}\n' +
  '.ap-sign img.ap-img{mix-blend-mode:normal !important}\n' +
  '}</style>';

// INIT before RET, and numerically within each — the order the folders are read in
const codes = [].concat(index[tranche].INIT, index[tranche].RET).map(c => 'iCoA-PP_26-' + c);
fs.mkdirSync(out, { recursive: true });
const rows = [];
let n = 0;
for (const code of codes) {
  const r = recs[code];
  if (!r) throw new Error('no record for ' + code);
  const o = build(r, meta[r.cu] || {});
  o.html = SIGN.sign(o.html, code, { h: 52 * SIG_SCALE, dy: SIG_DY });
  if (PRINT_FLAT) {
    o.html = o.html.replace('</body>', OPAQUE + '\n' + FLAT_CSS + '\n</body>');
    if (o.html.indexOf('__print-flat') < 0) throw new Error('the print-safe layer did not land on ' + code);
  }
  // one flat directory, named so a sort gives the folder's own order
  const name = String(++n).padStart(3, '0') + '_' + path.basename(o.path);
  fs.writeFileSync(path.join(out, name), o.html);
  rows.push([n, code, r.cu, r.p, r.strain, r.series, o.conforms ? 'conforms' : 'open', name].join('\t'));
}
fs.writeFileSync(path.join(out, '_order.tsv'),
  'page\tcode\tcultivation\tlot\tstrain\tseries\tdisposition\tfile\n' + rows.join('\n') + '\n');
console.log('%s: %d document(s)  signatures %s at %d%%  print-safe layer %s',
  tranche, n, SIGN.enabled() ? 'applied' : 'off', Math.round(SIG_SCALE * 100), PRINT_FLAT ? 'on' : 'off');
