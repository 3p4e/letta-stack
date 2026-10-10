// Applies a v35 record's data layer onto an existing CoQ document. Visual layer untouched.
globalThis.CoQApply = function (CoQ, skeleton) {
const red = CoQ.red, esc = CoQ.esc;

function resultsTbody(rec) {
  const cells = CoQ.DETS.map(d => CoQ.cell(d, rec.res[d], rec.st[d]));
  let i = 0;
  let tb = skeleton.replace(/@CELL@/g, () => cells[i++]);
  if (i !== 21) throw new Error('expected 21 cells, filled ' + i);
  const hasWin = rec.window && rec.window !== '—';
  const withWin = '<td><span class="p-spec">Per Section 01 <i class="bisep">|</i> <span class="mk" style="display:inline">Согласно Погл. 01</span></span></td>';
  const noWin = '<td><span class="p-spec" style="' + CoQ.RED + '">[ — ]</span></td>';
  if (tb.indexOf(withWin) < 0) throw new Error('row-4 criterion anchor not found');
  tb = tb.replace(withWin, hasWin ? withWin : noWin);
  return tb + '</tbody>';
}

function bannerInner(rec) {
  const c = CoQ.cell('4', rec.res['4'], rec.st['4']);
  const m = c.match(/<span class="r-val[^"]*"(?:\s+style="([^"]*)")?>([\s\S]*?)<\/span>/);
  return '<span' + (m[1] ? ' style="' + m[1] + '"' : '') + '>' + m[2] + '</span>';
}

function fileSlug(rec, strainCode) {
  const s = String(rec.strain || '').replace(/&/g, 'and').replace(/[^A-Za-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  const g = rec.grade && /^[IVX]+$/.test(rec.grade) ? '_Grade_' + rec.grade : '';
  return (rec.code || 'CoQ-UNASSIGNED') + '_' + rec.lot + '_' + strainCode + '_' + s + g + '.html';
}

function apply(html, rec, strainCode) {
  const codeTxt = rec.code ? esc(rec.code) : red('[assigned on issue]');
  const issueTxt = rec.code ? esc(rec.issue) : red('[DD.MM.YYYY]');
  const sup = (rec.supersedes && !/^n\/a/i.test(rec.supersedes) && rec.supersedes !== '—')
    ? '<span class="hb-sup">(supersedes ' + esc(rec.supersedes) + ')</span>' : '';
  const gradePart = rec.grade && /^[IVX]+$/.test(rec.grade) ? ' — Grade ' + rec.grade : '';
  const title = 'Purely Plant — Certificate of Quality — ' + (rec.code || 'CoQ № assigned on issue') +
    ' — ' + rec.strain + ' (' + strainCode + ')' + gradePart + ' — Batch ' + rec.lot;
  rec.bannerInner = bannerInner(rec);

  const steps = [
    ['title', /<title>[\s\S]*?<\/title>/, '<title>' + esc(title) + '</title>'],
    ['header', /<div class="hb-right">.*\n/,
      '<div class="hb-right"><div class="hb-code-lbl">Document ID <span class="mk">Код на документ</span></div>' +
      '<div class="hb-code">' + codeTxt + '</div><div class="hb-issue">Issued · Издаден <b>' + issueTxt +
      '</b></div>' + sup + '</div>\n'],
    ['sec01', /<div class="pb-main">[\s\S]*?(?=<div class="sec-label" style="margin-top:10px"><span class="sec-no">02<\/span>)/,
      CoQ.section01(rec)],
    ['results', /(<table class="results">[\s\S]*?)<tbody>[\s\S]*?<\/tbody>/,
      (m, pre) => pre + resultsTbody(rec)],
    ['labref', /(<table class="labref">[\s\S]*?)<tbody>[\s\S]*?<\/tbody>/,
      (m, pre) => pre + CoQ.section03(rec)],
    ['sec04', /<span class="disp-batch">[^<]*<\/span>/, '<span class="disp-batch">' + esc(rec.lot) + '</span>'],
    ['sigdates', /<span class="ap-date-val">[\s\S]*?<\/span>/g, '<span class="ap-date-val">' + issueTxt + '</span>']
  ];
  let out = html; const warnings = [];
  for (const [name, re, rep] of steps) {
    if (!new RegExp(re.source, re.flags.replace('g', '')).test(out)) { warnings.push('NO MATCH: ' + name); continue }
    out = typeof rep === 'function' ? out.replace(re, rep) : out.replace(re, () => rep);
  }
  return { html: out, filename: fileSlug(rec, strainCode), warnings, title };
}
return { apply, resultsTbody, bannerInner, fileSlug };
};
