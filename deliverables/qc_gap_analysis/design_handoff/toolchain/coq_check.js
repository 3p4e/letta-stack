// Assertion suite for the rebuilt CoQ set.
globalThis.CoQCheck = (function () {
const SUP = { '⁰':'0','¹':'1','²':'2','³':'3','⁴':'4','⁵':'5','⁶':'6','⁷':'7','⁸':'8','⁹':'9' };
const desup = s => String(s).replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹]/g, c => SUP[c]);
// The closed token set of the design system's own specimen card
// (guidelines/rules-coq-result-cells.html): a result cell prints one of these eight
// tokens or a figure with its unit, and nothing else. Source spellings are normalised
// INTO the set, never the reverse — every extra spelling of one fact is a
// discrepancy an inspector will raise against the register.
const TOKENS = ['Conforms','Absent','Does not conform','ND','< LOQ','n/t','[ — ]','[pending]'];
const ROMAN = /^(I|II|III|IV|V|VI|VII|VIII|IX|X)$/;

// numeric upper bound implied by a printed result, or null if non-numeric
function upper(txt) {
  let t = desup(txt).replace(/\s*(CFU\/g|µg\/kg|mg\/kg|%|, w\/w)\s*$/,'').trim();
  if (TOKENS.includes(txt.trim())) return null;
  const pair = t.match(/^<\s*([\d.]+)(?:\s*\^?\s*)?(?:x|×)?\s*$/);
  const andm = t.match(/^<\s*(\d+)(?:\s*)?\s+and\s*>\s*(\d+)/);
  if (andm) return Number(andm[1]);
  const sci = t.match(/^(<\s*)?([\d.]+)\s*(?:×|x)\s*10(\d+)$/);
  if (sci) return Number(sci[2]) * Math.pow(10, Number(sci[3]));
  const lt10 = t.match(/^<\s*10(\d+)$/);
  if (lt10) return Math.pow(10, Number(lt10[1]));
  const lt = t.match(/^<\s*([\d.]+)$/);
  if (lt) return Number(lt[1]);
  const p10 = t.match(/^10(\d+)$/);
  if (p10) return Math.pow(10, Number(p10[1]));
  const plain = t.match(/^([\d.]+)$/);
  if (plain) return Number(plain[1]);
  if (pair) return Number(pair[1]);
  return null;
}
function limitOf(spec) {
  const t = desup(spec.replace(/<[^>]*>/g, ''));
  const m = t.match(/≤\s*([\d.]+)\s*(?:×|x)?\s*(?:10(\d+))?/);
  if (!m) return null;
  let v = Number(m[1]);
  if (m[2]) v = v * Math.pow(10, Number(m[2]));
  else { const pw = t.match(/≤\s*10(\d+)/); if (pw) v = Math.pow(10, Number(pw[1])) }
  return isFinite(v) ? v : null;
}
const txtOf = h => h.replace(/<[^>]*>/g, '').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&').replace(/\s+/g,' ').trim();

function check(file, html, rec) {
  const F = [];  // findings
  const g = (re, n) => { const m = html.match(re); return m ? m[n === undefined ? 1 : n] : null };

  const code = txtOf(g(/<div class="hb-code">([\s\S]*?)<\/div>/) || '');
  const issue = txtOf(g(/<div class="hb-issue">[\s\S]*?<b>([\s\S]*?)<\/b>/) || '');
  const title = g(/<title>([\s\S]*?)<\/title>/) || '';
  const spec = txtOf(g(/Специфик[\s\S]*?<span class="lk-val sm">([\s\S]*?)<\/span>/) ||
                     g(/Референца на спецификација<\/span><\/span><span class="lk-val sm">([\s\S]*?)<\/span>/) || '');
  const lot = txtOf(g(/<span class="pb-name"><span style="font-family:'Roboto Mono',monospace">([\s\S]*?)<\/span>/) || '');
  const banner = txtOf(g(/<span class="pbp-val">([\s\S]*?)<\/span><\/span>/) || '');

  // -- 6 filename / title / spec code / grade
  const assigned = /^CoQ-PP_/.test(code);
  const fnCode = assigned ? (file.match(/^(CoQ-PP_\d\d-\d\d\d)/) || [])[1] : (/^CoQ-UNASSIGNED/.test(file) ? 'UNASSIGNED' : null);
  if (assigned && fnCode !== code) F.push('A6 filename code ' + fnCode + ' != printed ' + code);
  if (!assigned && fnCode !== 'UNASSIGNED') F.push('A6 unassigned doc not named CoQ-UNASSIGNED');
  if (title.indexOf(assigned ? code : 'assigned on issue') < 0) F.push('A6 title code mismatch');
  if (title.indexOf(lot) < 0) F.push('A6 title lot mismatch');
  const fnGrade = (file.match(/_Grade_([IVX]+)\.html$/) || [])[1] || null;
  const tGrade = (title.match(/ — Grade ([IVX]+) /) || [])[1] || null;
  if (fnGrade !== tGrade) F.push('A6 grade filename ' + fnGrade + ' != title ' + tGrade);
  if (fnGrade && !ROMAN.test(fnGrade)) F.push('A6 grade not a Roman numeral: ' + fnGrade);
  if (fnGrade && spec && spec.indexOf('-' + fnGrade + '_') < 0) F.push('A6 spec code ' + spec + ' does not carry grade ' + fnGrade);

  // -- results cells
  const rt = html.slice(html.indexOf('<table class="results">'), html.indexOf('</table>', html.indexOf('<table class="results">')));
  const rows = [...rt.matchAll(/<tr[^>]*>([\s\S]*?)<\/tr>/g)].map(m => m[1]).filter(r => /r-cell/.test(r));
  if (rows.length !== 21) F.push('A-cells expected 21 result rows, found ' + rows.length);
  const cells = rows.map(r => {
    const spc = (r.match(/<span class="p-spec"[^>]*>([\s\S]*?)<\/span>(?=<\/td>|<\/span><\/td>)/) || r.match(/<td><span class="p-spec"[^>]*>([\s\S]*?)<\/td>/) || [,''])[1];
    const cell = (r.match(/<td class="r-cell[^"]*">([\s\S]*?)<\/td>/) || [,''])[1];
    return { spec: txtOf(spc), val: txtOf(cell), raw: cell };
  });

  // -- 7 / 16 banner == row-4 cell == v35 value
  const row4 = cells[3] ? cells[3].val : null;
  if (banner !== row4) F.push('A7 banner "' + banner + '" != row-4 "' + row4 + '"');
  if (rec) {
    const v35 = (rec.res['4'] || '').trim();
    const num = (row4 || '').replace(/\s*%$/, '');
    const isNum = /^[\d.]+$/.test(num);
    if (isNum) { if (num !== v35) F.push('A16 banner ' + num + ' != v35 ' + v35) }
    else if (/^[\d.]+$/.test(v35)) {
      const st4 = rec.st['4'] || '';
      if (/in-house CoA only|not tested|to be performed|awaiting/i.test(st4)) F.push('OI-NOTE #4 v35 ' + v35 + ' withheld (' + st4.slice(0, 40) + ')');
      else F.push('A16 v35 has ' + v35 + ' but banner prints "' + row4 + '"');
    }
  }

  // -- 11 grammar whitelist + length
  const DETS_ORDER = ['1','2','3','4','5','6','7','8','9.1','9.2','9.3','9.4','9.5','10.1','10.2','10.3','11.1','11.2','11.3','11.4','12'];
  // Owner, 21.09.2026: "there will be no empty space ... all parameter results must be
  // filled in". A result cell is therefore NEVER blank — it carries a value or it
  // carries the token that states what is absent. Three assertions, strongest first.
  const NORESULT = /not tested|upon request|to be performed|in-house CoA only/i;
  cells.forEach((c, i) => {
    const d = DETS_ORDER[i];
    if (c.val) return;
    // (a) nothing may print empty, on any determination.
    F.push('A11 #' + d + ' prints an EMPTY cell — every cell carries a value or a token');
    // (b) #1, #2 and #7 are performed in house and the batch's iCoA certifies all three
    //     (owner: "Ident A and Ident B and even the Foreign Matter parameters are
    //     contained in the iCoA for each CoQ, this is known"), so they are never absent.
    if (['1', '2', '7'].includes(d))
      F.push('A11 in-house determination #' + d + ' prints nothing — its iCoA certifies it');
    // (c) a cell empty while the record holds a figure is a LOST RESULT, not an absence.
    if (!rec) return;
    const res = String(rec.res[d] || '').trim(), st = String(rec.st[d] || '');
    if (res && res !== '—' && !NORESULT.test(st) && !NORESULT.test(res))
      F.push('A11 #' + d + ' prints nothing but the record holds "' + res + '" (' + st.slice(0, 40) + ')');
  });
  for (const c of cells) {
    if (!c.val) continue;
    if (c.val.length > 26) F.push('A11 cell too long (' + c.val.length + '): ' + c.val);
    const ok = TOKENS.includes(c.val) ||
      /^[\d.]+\s*(%|CFU\/g|µg\/kg|mg\/kg)$/.test(c.val) ||
      /^[\d.]+\s*×\s*10[⁰¹²³⁴⁵⁶⁷⁸⁹]+\s*(CFU\/g|µg\/kg|mg\/kg)$/.test(c.val) ||
      /^<\s*[\d.]+(\s*×\s*10[⁰¹²³⁴⁵⁶⁷⁸⁹]+)?\s*(%|CFU\/g|µg\/kg|mg\/kg)$/.test(c.val) ||
      /^<\s*10[⁰¹²³⁴⁵⁶⁷⁸⁹]*\s*and\s*>\s*10[⁰¹²³⁴⁵⁶⁷⁸⁹]*\s*(CFU\/g|µg\/kg|mg\/kg)$/.test(c.val);
    if (!ok) F.push('A11 cell off-whitelist: "' + c.val + '"');
  }

  // -- 12 numeric result <= its own limit
  cells.forEach((c, i) => {
    if (i === 3) return;                       // row 4 -> Section 01 window, checked separately
    const lim = limitOf(c.spec), up = upper(c.val);
    if (lim === null || up === null) return;
    if (up <= lim + 1e-9) return;
    const counted = /CFU\/g/.test(c.spec);
    const redCell = /B91C1C/.test(c.raw), amberCell = /8F5B00/.test(c.raw);
    if (counted && up <= 2 * lim + 1e-9) {
      if (!amberCell && !redCell) F.push('A12 row ' + (i + 1) + ' ' + c.val + ' in the 5.1.4 undetermined band but not marked');
      else F.push('OI-17 row ' + (i + 1) + ' ' + c.val + ' undetermined vs ' + c.spec);
    } else {
      if (!redCell) F.push('A12 row ' + (i + 1) + ' OOS ' + c.val + ' > ' + c.spec + ' and NOT marked red');
      else F.push('OI-OOS row ' + (i + 1) + ' ' + c.val + ' > ' + c.spec + ' (marked)');
    }
  });
  // row 4 against the Section 01 window (two-sided, OI-05)
  const win = txtOf(g(/<span class="pot-win">\(([\s\S]*?)\)<\/span>/) || '');
  const wm = win.match(/([\d.]+)\s*[–-]\s*([\d.]+)/);
  const r4n = Number((row4 || '').replace(/[^\d.]/g, ''));
  if (wm && isFinite(r4n) && r4n > 0 && (r4n < Number(wm[1]) - 1e-9 || r4n > Number(wm[2]) + 1e-9))
    F.push('OI-05 assay ' + row4 + ' outside its window ' + win);

  // -- Section 03
  const lt = html.slice(html.indexOf('<table class="labref">'), html.indexOf('</table>', html.indexOf('<table class="labref">')));
  const lrows = [...lt.matchAll(/<tr><td><span class="lr-lab"[^>]*>([\s\S]*?)<\/span><\/td><td class="lr-mono">([\s\S]*?)<\/td><td class="lr-mono pcell">([\s\S]*?)<\/td><\/tr>/g)];
  const labNames = lrows.map(m => txtOf(m[1]).split(' · ')[0]);
  if (new Set(labNames).size !== labNames.length) F.push('A13 laboratory on two rows: ' + labNames.join(' / '));

  // -- 14 params 1,2,7 credited to the iCoA
  // 14 — params 1, 2, 7 present and credited to exactly one laboratory; the batch's iCoA
  //      unless an external certificate reports all three (v35 / OI-27, nine release lots).
  const creditOf = n => lrows.filter(m => txtOf(m[3]).split(/,\s*/).includes(n));
  const creditedAs = n => lrows.filter(m => txtOf(m[3]).split(/,\s*/).some(x => x === n || x === String(n).split('.')[0]));
  for (const n of ['1','2','7']) {
    const cr = creditOf(n);
    if (cr.length === 0) F.push('A14 param ' + n + ' credited to no laboratory');
    else if (cr.length > 1) F.push('A14 param ' + n + ' credited to ' + cr.length + ' laboratories');
  }
  const pp = lrows.find(m => /Purely Plant/.test(m[1]));
  if (pp && !/iCoA-PP_/.test(pp[2])) F.push('A14 in-house row does not cite an iCoA: ' + txtOf(pp[2]));
  // Head of QC, 26.09.2026: #1, #2 and #7 cite the internal certificate unless the Center for
  // Natural Products tested them explicitly — then the CNP certificate is the source, and a page
  // with no in-house row is correct. Any other external credit is still a finding.
  if (!pp) {
    const ext = creditOf('1')[0];
    const lab = ext ? txtOf(ext[1]).split(' · ')[0] : '?';
    if (!/Center for Natural Products/i.test(lab))
      F.push('OI-27 #1/#2/#7 credited externally to ' + lab + ', no in-house row');
  }

  // -- 15 every param credited exactly once
  const allP = lrows.flatMap(m => txtOf(m[3]).split(/,\s*/)).filter(Boolean);
  const dupP = allP.filter((x, i) => allP.indexOf(x) !== i);
  if (dupP.length) F.push('A15 param credited twice: ' + [...new Set(dupP)].join(','));
  const DETS = DETS_ORDER;
  cells.forEach((c, i) => {
    const d = DETS[i];
    const hasResult = !['n/t', '[ — ]', '[pending]'].includes(c.val);
    if (hasResult && !allP.includes(d) && !allP.includes(String(d).split('.')[0])) F.push('A15 param ' + d + ' prints "' + c.val + '" but is credited to no laboratory');
  });

  // -- 9 signature dates == issue date, exactly 2 signatories
  const sigs = [...html.matchAll(/<span class="ap-date-val">([\s\S]*?)<\/span>/g)].map(m => txtOf(m[1]));
  if (sigs.length !== 2) F.push('A9 expected 2 signature dates, found ' + sigs.length);
  if (sigs.some(s => s !== issue)) F.push('A9 signature dates ' + sigs.join('/') + ' != issue ' + issue);
  const D = s => { const m = String(s).match(/(\d{2})\.(\d{2})\.(\d{4})/); return m ? new Date(+m[3], +m[2] - 1, +m[1]) : null };
  const certDates = [...lt.matchAll(/<span class="cert"><b>[\s\S]*?<\/b> · ([\d.]+)<\/span>/g)].map(m => D(m[1])).filter(Boolean);
  const iss = D(issue);
  if (iss && certDates.length) {
    const mx = new Date(Math.max(...certDates.map(d => d.getTime())));
    if (iss < mx) F.push('A9 issue ' + issue + ' precedes latest cited certificate ' +
      String(mx.getDate()).padStart(2,'0') + '.' + String(mx.getMonth()+1).padStart(2,'0') + '.' + mx.getFullYear());
  }

  // -- No. / № convention
  if (/\bNo\./.test(txtOf(html.slice(html.indexOf('<body'))))) F.push('CONV "No." found — must be №');

  return { file, code, issue, lot, banner, grade: fnGrade, spec, findings: F, labs: labNames, params: allP };
}
return { check, upper, limitOf, desup, txtOf };
})();
