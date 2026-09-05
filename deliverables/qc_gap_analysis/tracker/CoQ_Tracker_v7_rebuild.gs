/**
 * CoQ Parameter Tracker v7 — rebuild from the eCOA Document Index
 * ---------------------------------------------------------------
 * Corrected 02.09.2026. Differences from the first draft, and why:
 *
 *  1. COLUMNS ARE FOUND BY HEADER NAME, not by position. The draft read fixed
 *     positions (D = params covered, I = parameter values, K = batch key) that
 *     match no released workbook: in v6 D is Laboratory, I is Parameters covered,
 *     K is Filename, and no version had a batch-key column. Run against v6 the
 *     draft produced empty blocks. This version maps every column it needs from
 *     the header row and says plainly which one is missing.
 *  2. ACCEPTANCE CRITERIA ARE READ FROM THE "Parameters" SHEET, which is the
 *     controlled list of what is tested for QC batch release and CoQ compilation.
 *     No transcription, so the tracker and the specification cannot drift.
 *  3. THE CONFORMANCE CHECK FOLLOWS Ph. Eur. 5.1.4. A counted microbiological
 *     limit printed as "≤ 10^n CFU/g" is judged against 2 × 10^n; between the
 *     printed limit and twice it the result is UNDETERMINED, not failing. The
 *     draft flagged the whole band as out of specification, which would have
 *     turned four undetermined results into four false failures.
 *  4. ONLY RELEASE RESULTS ARE JUDGED. A stability-timepoint result above the
 *     criterion is reported separately in STATUS; it is not a release failure.
 *     The draft would have raised three false failures on aged-material CBN.
 *
 * Layout: one TESTING INSTANCE = one block of two rows — the result(s) on the top
 * row and the certificate that reports them on the bottom row. A batch holds as
 * many blocks as it has testing instances (the largest number of certificates
 * credited to any one of its parameters), so a parameter tested twice on two dates
 * gets two blocks, never two text lines inside one. A parameter's certificates are
 * taken in ascending date order, so the n-th block is the n-th round of testing.
 * #1–#8 and #12 use Result | eCOA ref | ✓/✗, each merged across its block's two
 * rows; #9, #10 and #11 give each sub-determination its own column on the top row.
 *
 * HOW TO RUN: Extensions ▸ Apps Script ▸ paste ▸ save ▸ run buildTrackerV7.
 * It reads two sheets and writes one; nothing else in the file is touched.
 */

const INDEX_SHEET  = 'eCOA Document Index';
const PARAMS_SHEET = 'Parameters';
const OUTPUT_SHEET = 'CoQ Parameter Tracker v7';
const STATUS_PARTIAL_MAX = 3;
const PH_EUR_FACTOR = 2;
const COUNTED = /tamc|tymc|cfu|gnb|gram-neg|aerobic|yeast|mould|mold/i;

const PARAMS = [
  { n: 1,  group: 'IDENTIFICATION  1–3',    title: '#1 Identification A',        method: 'Appearance · Ph. Eur. mon. 3028' },
  { n: 2,  group: 'IDENTIFICATION  1–3',    title: '#2 Identification B',        method: 'Microscopy · Ph. Eur. 2.8.23' },
  { n: 3,  group: 'IDENTIFICATION  1–3',    title: '#3 Identification C',        method: 'HPLC · Ph. Eur. 2.2.29' },
  { n: 4,  group: 'CANNABINOID ASSAY  4–6', title: '#4 Assay — Total Δ⁹-THC*',   method: 'Ph. Eur. 2.2.29 (HPLC)' },
  { n: 5,  group: 'CANNABINOID ASSAY  4–6', title: '#5 Assay — Total CBD',       method: 'Ph. Eur. 2.2.29 · CBD + CBDA×0.877' },
  { n: 6,  group: 'CANNABINOID ASSAY  4–6', title: '#6 Total CBN',               method: 'Ph. Eur. 2.2.29 · CBN + CBNA×0.876' },
  { n: 7,  group: 'PHYSICAL  7–8',          title: '#7 Foreign Matter',          method: 'Ph. Eur. 2.8.2 / in-house' },
  { n: 8,  group: 'PHYSICAL  7–8',          title: '#8 Loss on Drying',          method: 'Ph. Eur. 2.2.32 · 40 °C, 24 h' },
  { n: 9,  group: 'MICROBIOLOGY  9',        title: '#9 Microbiological Purity',  method: 'Ph. Eur. 2.6.12 / 2.6.13 / 2.6.31 · cat. C',
    subs: ['TAMC', 'TYMC', 'GNB', 'Salm.', 'E. coli'], det: ['9.1', '9.2', '9.3', '9.4', '9.5'] },
  { n: 10, group: 'CONTAMINANTS  10–12',    title: '#10 Mycotoxins',             method: 'Ph. Eur. 2.8.18 / 2.8.22 (HPLC-FLD)',
    subs: ['AfB₁', 'ΣAf', 'OTA'], det: ['10.1', '10.2', '10.3'] },
  { n: 11, group: 'CONTAMINANTS  10–12',    title: '#11 Heavy Metals',           method: 'Ph. Eur. 2.4.27 (ICP-MS)',
    subs: ['Pb', 'Cd', 'As', 'Hg'], det: ['11.1', '11.2', '11.3', '11.4'] },
  { n: 12, group: 'CONTAMINANTS  10–12',    title: '#12 Pesticide Residues',     method: 'Ph. Eur. 2.8.13 · CUMCS equivalency' }
];

const SUB_ALIASES = {
  'TAMC': ['TAMC'], 'TYMC': ['TYMC'], 'GNB': ['GNB', 'Bile-tolerant gram-negative bacteria'],
  'Salm.': ['Salm.', 'Salmonella', 'Salm'], 'E. coli': ['E. coli', 'E.coli', 'Escherichia coli'],
  'AfB₁': ['AfB₁', 'AfB1', 'Aflatoxin B₁', 'Aflatoxin B1'],
  'ΣAf': ['ΣAf', 'ΣAflatoxins', 'Aflatoxins ∑'], 'OTA': ['OTA', 'Ochratoxin A'],
  'Pb': ['Pb', 'Lead (Pb)'], 'Cd': ['Cd', 'Cadmium (Cd)'], 'As': ['As', 'Arsenic (As)'], 'Hg': ['Hg', 'Mercury (Hg)']
};

const C = {
  navy: '#1f3864', navyText: '#ffffff', subHdr: '#fff2cc', grey: '#efefef',
  green: '#c6efce', orange: '#fce5cd', amber: '#fde9d9', red: '#f4cccc', extra: '#ededed',
  greenFill: '#6aa84f', orangeFill: '#e69138', amberFill: '#f6b26b', redFill: '#cc0000', extraFill: '#a6a6a6',
  statusRed: '#cc0000', statusOrange: '#e69138', statusGreen: '#38761d',
  oosText: '#9c0006', undText: '#b45f06'
};

// ───────────────────────────────────────────── main

function buildTrackerV7() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const idx = ss.getSheetByName(INDEX_SHEET);
  if (!idx) throw new Error('Sheet "' + INDEX_SHEET + '" not found.');

  const AC = readAcceptanceCriteria_(ss);
  const batches = readIndex_(idx);
  if (!batches.length) throw new Error('No rows read from "' + INDEX_SHEET + '" — check its header row.');

  const layout = buildLayout_();
  let out = ss.getSheetByName(OUTPUT_SHEET);
  if (out) ss.deleteSheet(out);
  out = ss.insertSheet(OUTPUT_SHEET, ss.getSheets().length);

  writeHeaders_(out, layout, AC);
  const res = writeBatches_(out, layout, batches, AC);
  writeKey_(out, layout, res.lastRow + 2);
  finishSheet_(out, layout, res.lastRow);

  SpreadsheetApp.getUi().alert(
    'Tracker v7 built.\n\n' + batches.length + ' batches, ' + (res.lastRow - 4) + ' rows.\n' +
    res.oos + ' batches out of specification, ' + res.und + ' undetermined (Ph. Eur. band), ' +
    res.stab + ' stability results above the criterion.\n' +
    (res.missingAC.length ? 'No acceptance criterion on the Parameters sheet for: ' + res.missingAC.join(', ') : 'Every criterion read from the Parameters sheet.'));
}

// ───────────────────────────────────────────── readers

/** Map the columns this script needs from the header row, by name. */
function mapColumns_(sh) {
  const data = sh.getDataRange().getValues();
  let h = -1;
  for (let r = 0; r < Math.min(8, data.length); r++) {
    const joined = data[r].join(' ').toUpperCase();
    if (joined.indexOf('BATCH') >= 0 && (joined.indexOf('REF') >= 0 || joined.indexOf('CERTIFICATE') >= 0)) { h = r; break; }
  }
  if (h < 0) throw new Error('Header row not found on "' + sh.getName() + '".');
  const want = {
    p:      /^P\s*BATCH/i,
    cu:     /^CU\s*BATCH/i,
    lab:    /^LAB(\s*CODE)?$/i,
    code:   /(ECOA\s*REF|CERTIFICATE)/i,
    date:   /^DATE$/i,
    params: /PARAMS?\s*COVERED|PARAMETERS\s*COVERED/i,
    values: /PARAMETER\s*VALUES/i,
    key:    /^BATCH\s*KEY$/i,
    kind:   /^KIND$/i,
    credited: /^CREDITED\s*FOR$/i
  };
  const col = {};
  data[h].forEach(function (v, i) {
    const t = String(v || '').trim();
    Object.keys(want).forEach(function (k) { if (col[k] === undefined && want[k].test(t)) col[k] = i; });
  });
  ['cu', 'code', 'date', 'params'].forEach(function (k) {
    if (col[k] === undefined) throw new Error('Column "' + k + '" not found on "' + sh.getName() + '". Headers read: ' + data[h].join(' | '));
  });
  if (col.values === undefined)
    throw new Error('No "PARAMETER VALUES" column on "' + sh.getName() + '". Use the v7 workbook, whose index carries the values, ' +
                    'or add that column before running.');
  return { header: h, col: col, data: data };
}

function readIndex_(sh) {
  const m = mapColumns_(sh), col = m.col, data = m.data;
  const order = [], map = {};
  let lastP = '', lastCU = '';
  for (let r = m.header + 1; r < data.length; r++) {
    const row = data[r];
    const code = String(row[col.code] || '').trim();
    if (!code) continue;
    const p = String(row[col.p !== undefined ? col.p : -1] || '').trim();
    const cu = String(row[col.cu] || '').trim();
    if (p) lastP = p;
    if (cu) lastCU = cu;
    /* Group on the LOT, never on the CU code: four CU codes carry two rounds of testing
       and three lots share a CU with no code of their own, so a CU grouping merges lots. */
    const key = String(col.key !== undefined ? (row[col.key] || '') : '').trim() || p || lastP || cu || lastCU;
    if (!key) continue;
    if (!map[key]) { map[key] = { key: key, p: p || lastP, cu: cu || lastCU || key, certs: [] }; order.push(key); }
    const dateStr = row[col.date] instanceof Date
      ? Utilities.formatDate(row[col.date], Session.getScriptTimeZone(), 'dd.MM.yyyy')
      : String(row[col.date] || '').trim();
    const raw = String(row[col.values] || '');
    map[key].certs.push({
      lab: String(row[col.lab !== undefined ? col.lab : -1] || '').trim(),
      kind: String(col.kind !== undefined ? (row[col.kind] || '') : '').trim(),
      covers: (String(row[col.params] || '').match(/#\d+/g) || []).map(function (x) { return parseInt(x.slice(1), 10); }),
      ref: code, date: dateStr, sortKey: dateSortKey_(dateStr),
      credited: col.credited === undefined ? null
        : (String(row[col.credited] || '').match(/#\d+/g) || []).map(function (x) { return parseInt(x.slice(1), 10); }),
      values: parseValues_(raw)
    });
  }
  return order.map(function (k) {
    map[k].certs.sort(function (a, b) { return a.sortKey.localeCompare(b.sortKey) || a.ref.localeCompare(b.ref); });
    return map[k];
  });
}

/** Acceptance criteria from the controlled Parameters sheet, keyed by determination. */
function readAcceptanceCriteria_(ss) {
  const sh = ss.getSheetByName(PARAMS_SHEET);
  const AC = {};
  if (!sh) return AC;
  const data = sh.getDataRange().getValues();
  let h = -1, cNo = -1, cCrit = -1;
  for (let r = 0; r < Math.min(8, data.length); r++) {
    data[r].forEach(function (v, i) {
      const t = String(v || '').trim();
      if (/acceptance criterion/i.test(t)) { h = r; cCrit = i; }
      if (h === r && /^#$/.test(t)) cNo = i;
    });
    if (h >= 0) break;
  }
  if (h < 0 || cCrit < 0) return AC;
  if (cNo < 0) cNo = 0;
  for (let r = h + 1; r < data.length; r++) {
    const no = String(data[r][cNo] || '').trim();
    const crit = String(data[r][cCrit] || '').trim();
    if (no && crit) AC[no] = crit;
  }
  return AC;
}

function dateSortKey_(d) {
  const m = String(d).match(/(\d{1,2})\.(\d{1,2})\.(\d{4})/);
  return m ? m[3] + m[2].padStart(2, '0') + m[1].padStart(2, '0') : '99999999';
}

/** "#3 Conforms · #4 21.80 · #9 TAMC 10 · TYMC 30 · #12 ND" → {3:'Conforms', 4:'21.80', 9:{TAMC:'10',…}} */
function parseValues_(s) {
  const out = { stability: false, noResult: false };
  s = String(s || '').replace(/\s+/g, ' ').trim();
  if (!s || /no result on the desk/i.test(s)) { out.noResult = true; return out; }
  if (/stability/i.test(s)) { out.stability = true; s = s.replace(/·?\s*stability timepoint/i, '').trim(); }
  const re = /#(\d+)\s*/g, marks = [];
  let m;
  while ((m = re.exec(s)) !== null) marks.push({ n: parseInt(m[1], 10), start: m.index, end: re.lastIndex });
  for (let i = 0; i < marks.length; i++) {
    const seg = s.substring(marks[i].end, i + 1 < marks.length ? marks[i + 1].start : s.length).replace(/\s*·\s*$/, '').trim();
    const def = PARAMS.filter(function (p) { return p.n === marks[i].n; })[0];
    out[marks[i].n] = (def && def.subs) ? parseSubs_(seg, def.subs) : seg;
  }
  return out;
}

function parseSubs_(seg, subs) {
  const found = [];
  subs.forEach(function (sub) {
    SUB_ALIASES[sub].forEach(function (alias) {
      const rx = new RegExp('(^|[\\s·])' + escapeRx_(alias) + '(?=[\\s:·]|$)');
      const m = rx.exec(seg);
      if (m && !found.some(function (f) { return f.sub === sub; }))
        found.push({ sub: sub, pos: m.index + m[1].length, len: alias.length });
    });
  });
  found.sort(function (a, b) { return a.pos - b.pos; });
  const res = {};
  found.forEach(function (f, i) {
    const end = i + 1 < found.length ? found[i + 1].pos : seg.length;
    res[f.sub] = seg.substring(f.pos + f.len, end).replace(/^[\s:]+/, '').replace(/\s*·\s*$/, '').trim() || '(reported, no value)';
  });
  return res;
}

function escapeRx_(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

// ───────────────────────────────────────────── conformance (Ph. Eur. 5.1.4)

const SUP = { '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9' };
function sup_(t) { return String(t).replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹]/g, function (c) { return '^' + SUP[c]; }); }

function magnitude_(v) {
  let s = String(v == null ? '' : v).trim();
  if (!s || s === '/' || s === '—') return null;
  s = sup_(s).replace(/[хХ×✕·]/g, 'x').replace(/≤/g, '<=').replace(/≥/g, '>=').replace(/(\d),(\d)/g, '$1.$2');
  let m = s.match(/(\d+(?:\.\d+)?)\s*x\s*10\s*\^?\s*(\d+)/i);
  if (m) return parseFloat(m[1]) * Math.pow(10, parseInt(m[2], 10));
  m = s.match(/(?:^|[^\d.])10\s*\^\s*(\d+)/);
  if (m) return Math.pow(10, parseInt(m[1], 10));
  m = s.match(/(\d+(?:\.\d+)?)/);
  if (m && !/and|и/i.test(s)) return parseFloat(m[1]);
  return null;
}

/** A counted limit "≤ 10^n CFU/g" is judged against 2 × 10^n. */
function acceptanceLimit_(lim, name) {
  const s = String(lim || '').trim();
  if (!s) return null;
  const norm = sup_(s).replace(/[хХ×✕]/g, 'x').replace(/\s+/g, '');
  const m = norm.match(/^[<≤]?10\^(\d)(?!\d)/);
  if (m && COUNTED.test(String(name || '') + ' ' + s)) return PH_EUR_FACTOR * Math.pow(10, parseInt(m[1], 10));
  return magnitude_(s);
}

function isProse_(s) { return /[A-Za-zА-Яа-я]{4}/.test(String(s)); }

function judgeable_(v, lim) {
  const s = String(v || '').trim();
  if (!s || !lim) return null;
  if (/^[<≤]/.test(s) || /and|и/i.test(s)) return null;
  if (/^(n\.?d\.?|blq|absent|одговара|н\.д|n\.r\.)/i.test(s) || isProse_(s)) return null;
  return s;
}

function overLimit_(v, lim, name) {
  const s = judgeable_(v, lim);
  if (s === null) return false;
  if (!/[<≤]/.test(String(lim)) && !/max/i.test(String(lim))) return false;
  const a = magnitude_(s), b = acceptanceLimit_(lim, name);
  return a !== null && b !== null && a > b * 1.0000001;
}

function undetBand_(v, lim, name) {
  const s = judgeable_(v, lim);
  if (s === null) return false;
  const norm = sup_(String(lim)).replace(/×/g, 'x').replace(/\s+/g, '');
  const m = norm.match(/^[<≤]?10\^(\d)(?!\d)/);
  if (!m || !COUNTED.test(String(name || '') + ' ' + lim)) return false;
  const printed = Math.pow(10, parseInt(m[1], 10)), a = magnitude_(s);
  return a !== null && a > printed * 1.0000001 && a <= printed * PH_EUR_FACTOR * 1.0000001;
}

// ───────────────────────────────────────────── layout

function buildLayout_() {
  const cols = [];
  let col = 4;
  PARAMS.forEach(function (p) {
    p.startCol = col;
    if (p.subs) p.subs.forEach(function (s, i) { cols.push({ col: col++, p: p, sub: s, det: p.det[i] }); });
    else { cols.push({ col: col++, p: p, kind: 'result' }); cols.push({ col: col++, p: p, kind: 'ecoa' }); }
    cols.push({ col: col++, p: p, kind: 'check' });
    p.endCol = col - 1; p.width = p.endCol - p.startCol + 1;
  });
  return { cols: cols, lastCol: col - 1, headerRows: 4 };
}

function acFor_(AC, key) { return AC[key] || ''; }

function writeHeaders_(sh, L, AC) {
  sh.getRange(1, 1, 1, 3).merge().setValue('BATCH IDENTIFICATION');
  let g = null, gStart = 0;
  PARAMS.forEach(function (p, i) {
    if (p.group !== g) {
      if (g) sh.getRange(1, gStart, 1, p.startCol - gStart).merge().setValue(g);
      g = p.group; gStart = p.startCol;
    }
    if (i === PARAMS.length - 1) sh.getRange(1, gStart, 1, p.endCol - gStart + 1).merge().setValue(g);
  });
  sh.getRange(2, 1, 3, 1).merge().setValue('CU Batch');
  sh.getRange(2, 2, 3, 1).merge().setValue('P Batch');
  sh.getRange(2, 3, 3, 1).merge().setValue('STATUS');
  PARAMS.forEach(function (p) {
    sh.getRange(2, p.startCol, 1, p.width).merge().setValue(p.title + '\n' + p.method);
    if (p.subs) {
      p.subs.forEach(function (s, i) {
        sh.getRange(3, p.startCol + i).setValue(acLabel_(acFor_(AC, p.det[i])));
        sh.getRange(4, p.startCol + i).setValue(s);
      });
    } else {
      sh.getRange(3, p.startCol, 1, 2).merge().setValue(acLabel_(acFor_(AC, String(p.n))));
      sh.getRange(4, p.startCol).setValue('Result (as reported)');
      sh.getRange(4, p.startCol + 1).setValue('eCOA ref, (date) [Lab] — one certificate per line');
    }
    sh.getRange(4, p.endCol).setValue('✓/✗');
  });
  sh.getRange(1, 1, 2, L.lastCol).setBackground(C.navy).setFontColor(C.navyText).setFontWeight('bold');
  sh.getRange(2, 1, 3, 3).setBackground(C.navy).setFontColor(C.navyText).setFontWeight('bold');
  sh.getRange(3, 4, 1, L.lastCol - 3).setBackground(C.grey).setFontStyle('italic').setFontSize(6.5);
  sh.getRange(4, 4, 1, L.lastCol - 3).setBackground(C.subHdr).setFontWeight('bold').setFontSize(7);
  sh.getRange(1, 1, 4, L.lastCol).setHorizontalAlignment('center').setVerticalAlignment('middle').setWrap(true);
  sh.getRange(1, 1, 2, L.lastCol).setFontSize(8);
}

function acLabel_(v) { return v ? 'A.C.: ' + v : 'A.C.: not on the Parameters sheet'; }

// ───────────────────────────────────────────── batch blocks

function writeBatches_(sh, L, batches, AC) {
  let row = L.headerRows + 1, oosTotal = 0, undTotal = 0, stabTotal = 0;
  const missingAC = {};
  batches.forEach(function (b) {
    /* Every certificate that reports a parameter or is credited to it, in date order.
       The longest of these lists is how many testing instances the batch has. */
    const perParam = {}, oosList = [], undList = [], stabList = [];
    let K = 1;
    PARAMS.forEach(function (prm) {
      const list = [];
      b.certs.forEach(function (c) {
        const v = c.values[prm.n];
        const has = v !== undefined && v !== '' && !(typeof v === 'object' && Object.keys(v).length === 0);
        if (!has && c.covers.indexOf(prm.n) < 0) return;
        /* A document on file that the owner's tracker does not credit for this parameter
           is shown as a testing instance, greyed and marked •, but never counted as
           coverage: what discharges a parameter stays the owner's judgement. */
        const isCredited = c.credited === null ? true : c.credited.indexOf(prm.n) >= 0;
        list.push({ c: c, v: has ? v : null, credited: isCredited });
      });
      perParam[prm.n] = list;
      if (list.length > K) K = list.length;
    });

    const first = row, last = row + 2 * K - 1;
    sh.getRange(first, 1, 2 * K, 1).merge().setValue(b.cu || 'CU CODE NOT RECORDED — TBC');
    sh.getRange(first, 2, 2 * K, 1).merge().setValue((!b.p || b.p === b.cu) ? 'N/A — no P batch assigned' : b.p);
    sh.getRange(first, 1, 2 * K, 2).setBackground(C.navy).setFontColor(C.navyText).setFontWeight('bold');

    /* The verdict is the batch's: judged over every certificate the parameter holds,
       release results only, a stability exceedance named apart. */
    let noCert = 0, certNoResult = 0, missing = 0;
    const colourOf = {};
    PARAMS.forEach(function (prm) {
      const list = perParam[prm.n];
      const own = list.filter(function (x) { return x.credited; });
      const rel = own.filter(function (x) { return x.v !== null && !x.c.values.stability; });
      const stab = own.filter(function (x) { return x.v !== null && x.c.values.stability; });
      const credited = own.filter(function (x) { return x.v === null; });
      if (!rel.length && !stab.length) { if (credited.length) certNoResult++; else noCert++; }
      if (!rel.length) missing++;
      (prm.det || [String(prm.n)]).forEach(function (detKey, j) {
        const label = '#' + prm.n + (prm.subs ? ' ' + prm.subs[j] : '');
        const crit = acFor_(AC, detKey);
        if (!crit) missingAC[detKey] = 1;
        function pick(x) { return prm.subs ? ((x.v && typeof x.v === 'object') ? x.v[prm.subs[j]] : null) : x.v; }
        const bad = rel.some(function (x) { return overLimit_(pick(x), crit, label); });
        const und = !bad && rel.some(function (x) { return undetBand_(pick(x), crit, label); });
        if (bad && oosList.indexOf(label) < 0) oosList.push(label);
        else if (und && undList.indexOf(label) < 0) undList.push(label);
        if (stab.some(function (x) { return overLimit_(pick(x), crit, label); }) && stabList.indexOf(label) < 0) stabList.push(label);
        colourOf[label] = bad ? C.oosText : (und ? C.undText : null);
      });
    });

    for (let i = 0; i < K; i++) {
      const top = first + 2 * i, bot = top + 1;
      PARAMS.forEach(function (prm) {
        const list = perParam[prm.n], here = i < list.length ? list[i] : null;
        let state;
        const own = list.filter(function (x) { return x.credited; });
        if (!here) state = (!own.length && i === 0) ? 'red' : 'none';
        else if (!here.credited) state = 'extra';
        else if (here.v === null) state = 'amber';
        else state = here.c.values.stability ? 'orange' : 'green';
        const fill = { green: C.green, orange: C.orange, amber: C.amber, red: C.red, extra: C.extra, none: '#ffffff' }[state];
        const glyphFill = { green: C.greenFill, orange: C.orangeFill, amber: C.amberFill, red: C.redFill, extra: C.extraFill, none: '#ffffff' }[state];
        const glyph = { green: '✓', orange: '✓', amber: '✗', red: '✗', extra: '•', none: '' }[state];
        const ref = here ? (ecoa_(here.c) + (here.credited ? '' : ' · on file, not credited'))
                         : (state === 'red' ? '— no certificate —' : '');

        if (prm.subs) {
          prm.subs.forEach(function (sname, j) {
            const cell = sh.getRange(top, prm.startCol + j);
            let text;
            if (here) text = (here.v && typeof here.v === 'object') ? (here.v[sname] || 'n.r.') : 'n.r.';
            else text = state === 'red' ? '— MISSING —' : '';
            cell.setValue(text).setFontWeight('bold');
            const colour = colourOf['#' + prm.n + ' ' + sname];
            if (colour && here && here.v && typeof here.v === 'object' &&
                (overLimit_(here.v[sname], acFor_(AC, prm.det[j]), sname) || undetBand_(here.v[sname], acFor_(AC, prm.det[j]), sname)))
              cell.setFontColor(colour);
          });
          sh.getRange(bot, prm.startCol, 1, prm.subs.length).merge().setValue(ref).setFontSize(6);
          sh.getRange(top, prm.startCol, 2, prm.subs.length).setBackground(fill);
        } else {
          const rc = sh.getRange(top, prm.startCol, 2, 1).merge().setFontWeight('bold');
          if (here) rc.setValue(here.v === null ? 'no result on file' : String(here.v));
          else rc.setValue(state === 'red' ? '— MISSING —' : '');
          const colour = colourOf['#' + prm.n];
          if (colour && here && here.v !== null &&
              (overLimit_(String(here.v), acFor_(AC, String(prm.n)), '#' + prm.n) ||
               undetBand_(String(here.v), acFor_(AC, String(prm.n)), '#' + prm.n)))
            rc.setFontColor(colour);
          sh.getRange(top, prm.startCol + 1, 2, 1).merge().setValue(ref).setFontSize(6);
          sh.getRange(top, prm.startCol, 2, 2).setBackground(fill);
        }
        sh.getRange(top, prm.endCol, 2, 1).merge().setValue(glyph)
          .setFontColor('#ffffff').setFontWeight('bold').setBackground(glyphFill);
      });
      if (i) sh.getRange(top, 1, 2, L.lastCol)
        .setBorder(true, null, null, null, null, null, '#404040', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
    }

    let st, colour;
    if (missing === 0) { st = '✓ COMPLETE'; colour = C.statusGreen; }
    else {
      st = (missing <= STATUS_PARTIAL_MAX ? '⚠' : '✗') + ' ' + missing + ' NO RESULT\n(' + noCert + ' no cert / ' + certNoResult + ' cert w/o result)';
      colour = missing <= STATUS_PARTIAL_MAX ? C.statusOrange : C.statusRed;
    }
    if (K > 1) st += '\n' + K + ' testing instances';
    const uncredited = {};
    PARAMS.forEach(function (prm) {
      perParam[prm.n].forEach(function (x) { if (!x.credited) uncredited[x.c.ref] = 1; });
    });
    const nUn = Object.keys(uncredited).length;
    if (nUn) st += '\n• ' + nUn + ' document(s) on file, not credited';
    if (oosList.length) { st += '\n✗ OUT OF SPECIFICATION: ' + oosList.join(', '); colour = C.statusRed; oosTotal++; }
    if (undList.length) { st += '\n◐ UNDETERMINED (Ph. Eur. band): ' + undList.join(', '); if (!oosList.length) colour = C.statusOrange; undTotal++; }
    if (stabList.length) { st += '\n· stability above A.C.: ' + stabList.join(', '); stabTotal++; }
    sh.getRange(first, 3, 2 * K, 1).merge().setValue(st).setBackground(colour).setFontColor('#ffffff').setFontWeight('bold');

    const block = sh.getRange(first, 1, 2 * K, L.lastCol);
    block.setFontSize(7).setWrap(true).setVerticalAlignment('middle').setHorizontalAlignment('center');
    block.setBorder(true, true, true, true, null, null, '#000000', SpreadsheetApp.BorderStyle.SOLID_THICK);
    PARAMS.forEach(function (prm) {
      sh.getRange(first, prm.startCol, 2 * K, prm.width)
        .setBorder(null, true, null, true, null, null, '#404040', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
    });
    row = last + 1;
  });
  return { lastRow: row - 1, oos: oosTotal, und: undTotal, stab: stabTotal, missingAC: Object.keys(missingAC) };
}

function ecoa_(c) { return c.ref + ', (' + c.date + ') [' + c.lab + ']'; }

// ───────────────────────────────────────────── key / finish

function writeKey_(sh, L, row) {
  const key =
    'KEY — ✓ green: certificate on file AND its result in the eCOA Document Index. ' +
    '✓ orange: stability-timepoint certificate — the result is NOT a release result. ' +
    '✗ amber: the certificate is credited for this parameter but the Index holds no result from it. ' +
    '• grey: the document is on file and covers or reports this parameter, but the owner\'s tracker does not credit it here — ' +
    'shown as a testing instance, never counted as coverage. ' +
    '✗ red — MISSING —: no certificate covers this parameter for this batch. ' +
    'BLOCK RULE: one TESTING INSTANCE = one block of two rows — result(s) on the top row, the certificate that reports them on the ' +
    'bottom row. A batch holds as many blocks as it has testing instances, and a parameter\'s certificates are taken in ascending date ' +
    'order, so the n-th block is the n-th round of testing; a parameter tested once is empty in the later blocks. For #9, #10 and #11 ' +
    'each sub-determination has its own column on the top row. n.r. = that sub-determination is not reported on that certificate. ' +
    'RED result = OUT OF SPECIFICATION. AMBER result = UNDETERMINED: a counted microbiological limit printed as ≤ 10ⁿ CFU/g is judged ' +
    'against 2 × 10ⁿ (Ph. Eur. 5.1.4), and a result between the printed limit and twice it is undetermined, not failing. ' +
    'Only release results are judged; a stability timepoint above the criterion is named separately in STATUS. ND, <LOQ, <10, absent, ' +
    'a range written with "and", and any prose annotation are never judged. Every out-of-specification result needs an investigation record. ' +
    'Acceptance criteria in row 3 are read from the "' + PARAMS_SHEET + '" sheet — the controlled list of what is tested for QC batch ' +
    'release and CoQ compilation. Built ' + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'dd.MM.yyyy') + ' by buildTrackerV7().';
  sh.getRange(row, 1, 1, L.lastCol).merge().setValue(key).setFontSize(6.5).setWrap(true).setVerticalAlignment('top').setBackground(C.grey);
  sh.setRowHeight(row, 80);
}

function finishSheet_(sh, L, lastRow) {
  sh.setFrozenRows(L.headerRows);
  sh.setFrozenColumns(3);
  sh.setColumnWidth(1, 92); sh.setColumnWidth(2, 104); sh.setColumnWidth(3, 140);
  L.cols.forEach(function (c) {
    let w = 60;
    if (c.kind === 'result') w = 72;
    if (c.kind === 'ecoa') w = 150;
    if (c.kind === 'check') w = 24;
    if (c.sub) w = (c.sub === 'Salm.' || c.sub === 'E. coli') ? 56 : 62;
    sh.setColumnWidth(c.col, w);
  });
  sh.setRowHeight(1, 22); sh.setRowHeight(2, 34); sh.setRowHeight(3, 28); sh.setRowHeight(4, 22);
  sh.autoResizeRows(L.headerRows + 1, lastRow - L.headerRows);
  for (let r = L.headerRows + 1; r <= lastRow; r++) if (sh.getRowHeight(r) < 18) sh.setRowHeight(r, 18);
}
