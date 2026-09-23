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
const fs = require('fs'), path = require('path');
const HERE = __dirname, GAP = path.resolve(HERE, '../..');
const SIGN = require(path.join(GAP, 'sign_block.js'));
const build = new Function('return (' + fs.readFileSync(path.join(HERE, 'icoa3_gen.js'), 'utf8') + ')')();

const data = JSON.parse(fs.readFileSync(path.join(GAP, 'coq_artifact_data.json'), 'utf8'));
// phenotype, processing and the strain code are production attributes; they live on the
// desk's own plan and nowhere else. Grade and the specification code come off the
// certificate of quality, which is authoritative for both.
const plan = JSON.parse(fs.readFileSync(path.join(HERE, 'ISSUE_iCOA/_generator/coq_plan.json'), 'utf8'));
const meta = {};
for (const p of plan) if (!meta[p.rec.cult])
  meta[p.rec.cult] = { strainCode: p.strainCode, phenotype: p.rec.phenotype, processing: p.rec.processing };

const out = process.argv[2] || path.join(HERE, 'build_register');
const rows = [];
let noPheno = 0;
for (const c of data.coqs) {
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
  o.html = SIGN.sign(o.html, rec.code, { h: 52, dy: -9 });
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
console.log('internal certificates built from the register: %d', rows.length);
console.log('  conforming: %d   open: %d', rows.filter(r => r.includes('\tconforms\t')).length,
            rows.filter(r => r.includes('\topen\t')).length);
console.log('  no cultivar record on file (boxes stay open): %d', noPheno);
