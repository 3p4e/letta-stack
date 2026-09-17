// CoQ data-layer rebuild from v35. Visual layer (head + trailing <style> stack) untouched.
globalThis.CoQ = (function () {
const RED = 'color:#B91C1C;font-weight:700', AMBER = 'color:#8F5B00;font-weight:700';
const DETS = ['1','2','3','4','5','6','7','8','9.1','9.2','9.3','9.4','9.5','10.1','10.2','10.3','11.1','11.2','11.3','11.4','12'];
const UNIT = {'4':' %','5':' %','6':' %','8':' %','9.1':' CFU/g','9.2':' CFU/g','9.3':' CFU/g',
  '10.1':' µg/kg','10.2':' µg/kg','10.3':' µg/kg','11.1':' mg/kg','11.2':' mg/kg','11.3':' mg/kg','11.4':' mg/kg','7':' %','12':' mg/kg'};
// `ac` is the accreditation id, held apart from the EN name so it can print on the second
// line beside the Macedonian text rather than running the first line long.
const LABS = {
  PP:  {en:'Purely Plant QC Department · In-house', ac:'', mk:'Пјурли Плант — Сектор за КК · In-house', ad:'Kojlija 1043, Petrovec-Skopje, MK'},
  CNP: {en:'UKIM Faculty of Pharmacy — Center for Natural Products · ISO/IEC 17025:2017', ac:'LT-083 (IARM)', mk:'УКИМ ФФ — Центар за Природни Производи', ad:'Mother Theresa 47, 1000 Skopje, MK'},
  IPH: {en:'JZU Institute for Public Health (IPH Skopje) · ISO/IEC 17025:2017', ac:'LT-005 (IARM)', mk:'ЈЗУ Институт за јавно здравје (ИЈЗ Скопје)', ad:'50ta Divizija 6, 1000 Skopje, MK'},
  FHM: {en:'Farmahem DOOEL — Laboratory for Instrumental Analysis · ISO/IEC 17025:2017', ac:'LT-020 (IARM)', mk:'Фармахем ДООЕЛ — Лаборатoрија за инструментална анализа', ad:'Kisela Voda, 1000 Skopje, MK'},
  PHY: {en:'State Phytosanitary Laboratory · ISO/IEC 17025:2017', ac:'LT-034 (IARM)', mk:'Државна фитосанитарна лабораторија', ad:'Aleksandar Makedonski bb, 1000 Skopje, MK'}
};
const ORDER = ['PP','CNP','IPH','FHM','PHY'];
// Param. № column cites the DETERMINATION, not its sub-parts: 10.1/10.2/10.3 -> "10".
// Safe unconditionally here because no dotted family spans two laboratories on any document
// in the set (checked); if one ever did, the family would have to stay dotted on both rows or
// the same determination would read as credited twice.
function collapseParams(ds) {
  const out = [];
  for (const d of ds) { const f = String(d).split('.')[0]; if (!out.includes(f)) out.push(f) }
  return out;
}
// A citable document is a CODE, not prose. v35 carries four OCR sentences in the document
// field (OI-08 / addendum 2.2); a sentence cannot stand in the CoA Doc. Code column.
function codeShaped(d) {
  d = String(d || '').trim();
  if (!d || d === '—') return false;
  if (d.length > 28) return false;
  if (/^n\/a/i.test(d)) return false;
  if (/^in-house/i.test(d)) return false;
  if (d.includes('(')) return false;
  return true;
}
function canonLab(s) {
  s = (s || '').trim();
  if (!s || s === '—') return null;
  if (/purely plant/i.test(s)) return 'PP';
  if (/^CNP$/i.test(s) || /center for natural products/i.test(s)) return 'CNP';
  if (/^IJZ$/i.test(s) || /institute of public health|institute for public health/i.test(s)) return 'IPH';
  if (/^FHM$/i.test(s) || /farmahem/i.test(s)) return 'FHM';
  if (/phytosanitary/i.test(s)) return 'PHY';
  return null;
}
function parseCSV(t) {
  const rows = []; let r = [], f = '', q = false;
  for (let i = 0; i < t.length; i++) { const c = t[i];
    if (q) { if (c === '"') { if (t[i+1] === '"') { f += '"'; i++ } else q = false } else f += c }
    else { if (c === '"') q = true; else if (c === ',') { r.push(f); f = '' }
      else if (c === '\n') { r.push(f); rows.push(r); r = []; f = '' } else if (c !== '\r') f += c } }
  if (f !== '' || r.length) { r.push(f); rows.push(r) }
  return rows;
}
const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');
const mmyyyy = d => { const m = String(d||'').match(/(\d{2})\.(\d{2})\.(\d{4})/); return m ? m[2]+'.'+m[3] : '—' };
const strip = s => String(s).replace(/\s*\([^)]*\)\s*$/, '').trim();
const norm = v => v
  .replace(/\s*ᴰ\s*/g, ' ')
  .replace(/\s*—\s*DETECTED,\s*>\s*LOQ\s*/i, '')
  .replace(/\s*—\s*all\s+\d+\s+residues\s*/i, '')
  .replace(/^Not found any pesticide above LOQ.*$/i, 'ND')
  .replace(/^identity by the HPLC cannabinoid profile.*$/i, 'Conforms')
  .replace(/(\d),(\d)/g, '$1.$2')
  .replace(/\s*(?:%|CFU\/g|µg\/kg|mg\/[Kk]g|,\s*w\/w)\s*/g, ' ')
  .replace(/\s+/g, ' ').trim();
const red = t => '<span style="' + RED + '">' + t + '</span>';

// ---- one result cell -------------------------------------------------------
function cell(det, res, status) {
  res = (res || '').trim(); const st = (status || '');
  let txt, cls = '', style = '', conform = false;
  if (!res || res === '—')                                    { txt = '[ — ]'; style = RED }
  else if (/not tested/i.test(st) || /^not tested$/i.test(res)) { txt = 'n/t'; style = RED }
  else if (/to be performed/i.test(st) || /to be performed/i.test(res)) { txt = '[ — ]'; style = RED }
  else if (/awaiting/i.test(st))                              { txt = '[pending]'; style = AMBER }
  else if (/in-house CoA only/i.test(st))                     { txt = '[ — ]'; style = RED }
  else if (/upon request/i.test(res))                         { txt = '[ — ]'; style = RED }
  else {
    let v = norm(strip(res).split('|')[0].trim());
    if (/^conforms/i.test(v))      { txt = 'Conforms'; conform = true }
    else if (/^absent/i.test(v))   { txt = 'Absent';   conform = true }
    else if (/^не одговара/i.test(v)) { txt = 'Does not conform'; style = RED }
    else if (/^ND\b/i.test(v))     { txt = 'ND' }
    else if (/^<\s*LOQ/i.test(v))  { txt = '< LOQ' }
    else                           { txt = v + (UNIT[det] || '') }
    if (!conform) {
      if (/OUT OF SPECIFICATION|BLOCKED/i.test(st)) style = RED;
      else if (/UNDETERMINED/i.test(st)) style = AMBER;
    }
  }
  const n = txt.length;
  if (n >= 19) cls = ' r-xlong'; else if (n >= 14) cls = ' r-long';
  return '<td class="r-cell' + cls + '"><span class="r-val' + (conform ? ' r-conform' : '') + '"' +
    (style ? ' style="' + style + '"' : '') + '>' + esc(txt) + '</span></td>';
}

// ---- Section 03 ------------------------------------------------------------
function section03(rec) {
  const groups = {};
  for (const d of DETS) {
    const lab = canonLab(rec.lab[d]), doc = (rec.doc[d] || '').trim(), iss = (rec.iss[d] || '').trim();
    if (!lab || !codeShaped(doc)) continue;
    const g = groups[lab] = groups[lab] || { certs: new Map(), params: [] };
    g.params.push(d);
    const k = doc + '|' + iss;
    if (!g.certs.has(k)) g.certs.set(k, { doc: doc, iss: iss });
  }
  const rows = [];
  for (const key of ORDER) {
    const g = groups[key]; if (!g) continue;
    const L = LABS[key];
    const certs = [...g.certs.values()].map(c =>
      '<span class="cert"><b>' + esc(c.doc) + '</b> · ' + esc(c.iss || '—') + '</span>').join('');
    rows.push('<tr><td><span class="lr-lab">' + L.en + ' <i class="bisep">|</i> <span class="mk" style="display:inline">' +
      L.mk + (L.ac ? ' <span class="lr-ac">' + L.ac + '</span>' : '') + '</span><small>' + L.ad +
      '</small></span></td><td class="lr-mono">' + certs +
      '</td><td class="lr-mono pcell">' + collapseParams(g.params).join(', ') + '</td></tr>');
  }
  // rule 10 — a result with no citable certificate goes to the Work Order row
  const orphan = DETS.filter(d => {
    const r = (rec.res[d] || '').trim(), doc = (rec.doc[d] || '').trim();
    if (!r || r === '—' || /not tested|to be performed|upon request|^carried /i.test(r)) return false;
    if (/in-house CoA only|awaiting/i.test(rec.st[d] || '')) return false;
    return !codeShaped(doc) || !canonLab(rec.lab[d]);
  });
  if (orphan.length) rows.push('<tr><td><span class="lr-lab" style="' + RED +
    '">Certificate to be located · Work Order <i class="bisep">|</i> <span class="mk" style="display:inline;' + RED +
    '">Сертификатот да се пронајде · Работен налог</span><small>result on file, no citable certificate</small></span></td><td class="lr-mono">' +
    red('[ — ]') + '</td><td class="lr-mono pcell">' + collapseParams(orphan).join(', ') + '</td></tr>');
  return '<tbody>\n' + rows.join('\n') + '\n</tbody>';
}

// ---- Section 01 ------------------------------------------------------------
function chip(on, label, extra) {
  return '<span class="chip-' + (on ? 'sel' : 'un') + '"><span class="bx">' + (on ? '☒' : '☐') + '</span> ' +
    label + (extra || '') + '</span>';
}
function section01(rec) {
  const ph = (rec.phenotype || '').toUpperCase();
  const dom = (rec.dominance || '').trim();
  let ratio = '';
  const dm = dom.match(/^(INDICA|SATIVA)\s+(\d+)\s*:\s*(INDICA|SATIVA)\s+(\d+)$/i);
  if (dm) ratio = ' <span class="ratio" style="font-size:.86em;letter-spacing:.3px">' + dm[1].toUpperCase() +
    '<b style="color:#FFD98A;font-weight:800">' + dm[2] + '</b> : ' + dm[3].toUpperCase() +
    '<b style="color:#FFD98A;font-weight:800">' + dm[4] + '</b></span>';
  const isH = ph === 'HYBRID', isI = ph === 'INDICA', isS = ph === 'SATIVA';
  const pheno = chip(isH, 'Hybrid', isH ? ratio : '') +
    '<span class="stack">' + chip(isI, 'Indica') + chip(isS, 'Sativa') + '</span>';
  const chem = '<span class="stack">' + chip(rec.chemotype === 'THC', 'THC') + chip(rec.chemotype === 'CBD', 'CBD') + '</span>';
  const proc = (rec.processing || '').toUpperCase();
  const prc = '<span class="stack">' + chip(/MACHINE/.test(proc), 'Machine <span class="mk">Машинска</span>') +
    chip(/HAND/.test(proc), 'Hand') + '</span>';

  const pcode = rec.productCode && rec.productCode !== '—'
    ? esc(rec.productCode.replace(/\s*:\s*/, ':')) : red('[ — ]');
  const win = rec.window && rec.window !== '—'
    ? (rec.nominal ? '<span class="pot-nom">' + rec.nominal + '%</span><span class="pot-tol">± ' + rec.tol +
        '%</span><span class="pot-win">(' + esc(rec.window) + ')</span>'
       : '<span class="pot-win">(' + esc(rec.window) + ')</span>')
    : red('[ — ]');
  const spec = rec.specCode && rec.specCode !== '—' ? esc(rec.specCode) : red('[ — ]');
  const pkg = rec.packaging && rec.packaging !== '—'
    ? 'TRIPLEX ALU BAG <span class="mk" style="display:inline;text-transform:uppercase">Триплекс алу кеса</span><br><span class="attr-mono">PET 12 · ALU 7 · PE 80 · 300×500 mm · net 400.0 g ±3%</span>'
    : red('[ — ]');

  return '<div class="pb-main">\n' +
'    <span class="pb-name"><span style="font-family:\'Roboto Mono\',monospace">' + esc(rec.lot) +
      '</span> <i class="bisep" style="font-size:.7em">|</i> <span style="font-weight:800;text-transform:uppercase">' +
      esc(rec.strain) + '</span></span>\n' +
'    <span class="pb-potency"><span class="pbp-val">' + rec.bannerInner + '</span></span>\n' +
'  </div>\n' +
'  <div class="goldrule"></div>\n' +
'  <div class="selrow">\n' +
'    <span class="grp"><span class="lk-lbl">Phenotype <span class="mk">Фенотип</span></span>' + pheno + '</span>\n' +
'    <span class="grp"><span class="lk-lbl">Chemotype <span class="mk">Хемотип</span></span>' + chem + '</span>\n' +
'    <span class="grp"><span class="lk-lbl">Processing <span class="mk">Обработка</span></span>' + prc + '</span>\n' +
'  </div>\n' +
'  <div class="goldrule"></div>\n' +
'  <div class="gridrow lk-inline" style="padding-top:8px">\n' +
'    <span class="lk"><span class="lk-lbl">Product Code<span class="mk">Код на производ</span></span><span class="lk-val">' + pcode + '</span></span>\n' +
'    <span class="lk"><span class="lk-lbl">Potency<span class="mk">Јачина</span></span><span class="lk-val">' + win + '</span></span>\n' +
'    <span class="lk"><span class="lk-lbl">Specification Reference<span class="mk">Референца на спецификација</span></span><span class="lk-val sm">' + spec + '</span></span>\n' +
'  </div>\n' +
'  <div class="goldrule"></div>\n' +
'  <div class="gridrow lk-inline" style="grid-template-columns:repeat(4,auto)">\n' +
'    <span class="lk"><span class="lk-lbl">Production Batch №<span class="mk">Производна серија №</span></span><span class="lk-val">' + esc(rec.lot) + '</span></span>\n' +
'    <span class="lk"><span class="lk-lbl">Manufacture Date<span class="mk">Датум на производство</span></span><span class="lk-val sm">' + mmyyyy(rec.manufDate) + '</span></span>\n' +
'    <span class="lk"><span class="lk-lbl">Packaging Date<span class="mk">Датум на пакување</span></span><span class="lk-val sm">' + mmyyyy(rec.packDate) + '</span></span>\n' +
'    <span class="lk"><span class="lk-lbl">Manufacturer<span class="mk">Производител</span></span><span class="attr-val" style="margin-top:0">PURELY PLANT DOOEL <span class="mk" style="display:inline;text-transform:uppercase">Пјурли Плант ДООЕЛ</span><br><span class="attr-mono">Kojlija, Petrovec-Skopje, MK</span></span></span>\n' +
'  </div>\n' +
'  <div class="goldrule"></div>\n' +
'  <div class="gridrow lk-inline pkg-row" style="grid-template-columns:repeat(2,auto);padding-top:4px">\n' +
'    <span class="lk"><span class="lk-lbl">Contact Packaging<span class="mk">Контактно пакување</span></span><span class="attr-val" style="margin-top:0">' + pkg + '</span></span>\n' +
'    <span class="lk"><span class="lk-lbl">Dosage Form<span class="mk">Дозажна форма</span></span><span class="attr-val" style="margin-top:0">DRY CANNABIS FLOWER <span class="mk" style="display:inline;text-transform:uppercase">Сув цвет од канабис</span><br><span class="attr-mono"><i>Cannabis flos.</i> · Ph. Eur. 11.5 (3028)</span></span></span>\n' +
'  </div>\n' +
'  <div class="goldrule"></div>\n\n  ';
}
return { RED, AMBER, DETS, UNIT, LABS, ORDER, canonLab, codeShaped, collapseParams, parseCSV, esc, mmyyyy, strip, red, cell, section03, section01, chip };
})();
