// In-browser structure detection for the Formatter (ported from the Hybrid v2 prototype).
// .docx → word/document.xml → paragraphs / headings / tables; .md/.txt by lines.
export type RawBlock = { k: 'head' | 'para'; t: string } | { k: 'table'; rows: string[][] };

export async function unzipEntry(buf: ArrayBuffer, name: string): Promise<string> {
  const dv = new DataView(buf), u8 = new Uint8Array(buf);
  let eocd = -1;
  for (let i = buf.byteLength - 22; i >= Math.max(0, buf.byteLength - 66000); i--) if (dv.getUint32(i, true) === 0x06054b50) { eocd = i; break; }
  if (eocd < 0) throw new Error('not a zip / .docx file');
  let p = dv.getUint32(eocd + 16, true); const n = dv.getUint16(eocd + 10, true), dec = new TextDecoder();
  for (let k = 0; k < n; k++) {
    if (dv.getUint32(p, true) !== 0x02014b50) break;
    const method = dv.getUint16(p + 10, true), csize = dv.getUint32(p + 20, true), nl = dv.getUint16(p + 28, true), xl = dv.getUint16(p + 30, true), cl = dv.getUint16(p + 32, true), off = dv.getUint32(p + 42, true);
    const nm = dec.decode(u8.subarray(p + 46, p + 46 + nl));
    if (nm === name) {
      const start = off + 30 + dv.getUint16(off + 26, true) + dv.getUint16(off + 28, true), data = u8.subarray(start, start + csize);
      if (method === 0) return dec.decode(data);
      const ds = new Blob([data]).stream().pipeThrough(new DecompressionStream('deflate-raw'));
      return await new Response(ds).text();
    }
    p += 46 + nl + xl + cl;
  }
  throw new Error(name + ' not found in archive');
}

const unesc = (s: string) => s.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'");
const xmlText = (x: string) => unesc((x.match(/<w:t(?:\s[^>]*)?>[^<]*<\/w:t>/g) || []).map(t => t.replace(/<[^>]+>/g, '')).join(''));

export function docxBlocks(xml: string): RawBlock[] {
  const body = (xml.split('<w:body>')[1] || xml).split('</w:body>')[0], out: RawBlock[] = [];
  const re = /<w:tbl>[\s\S]*?<\/w:tbl>|<w:p[ >][\s\S]*?<\/w:p>/g; let m;
  while ((m = re.exec(body))) {
    const b = m[0];
    if (b.startsWith('<w:tbl>')) out.push({ k: 'table', rows: (b.match(/<w:tr[ >][\s\S]*?<\/w:tr>/g) || []).map(r => (r.match(/<w:tc>[\s\S]*?<\/w:tc>/g) || []).map(xmlText)) });
    else { const t = xmlText(b).trim(); if (!t) continue; const st = (b.match(/<w:pStyle w:val="([^"]+)"/) || [])[1] || ''; const bold = /<w:b\/>|<w:b w:val="(1|true)"/.test(b);
      out.push({ k: /heading|title|naslov/i.test(st) || (bold && t.length < 70) ? 'head' : 'para', t }); }
  }
  return out;
}

export function textBlocks(txt: string): RawBlock[] {
  const out: RawBlock[] = [], lines = txt.split(/\r?\n/);
  let tbl: { rows: string[][]; raw: string[] } | null = null;
  const flush = () => { if (!tbl) return; if (tbl.rows.length >= 2 || /\t/.test(tbl.raw[0])) out.push({ k: 'table', rows: tbl.rows }); else out.push({ k: 'para', t: tbl.raw[0] }); tbl = null; };
  for (const raw of lines) { const l = raw.trim();
    if (/\|\|\||\t/.test(l) && !/^#/.test(l)) { (tbl = tbl || { rows: [], raw: [] }).rows.push(l.split(/\s*\|\|\|\s*|\t/)); tbl.raw.push(l); continue; }
    flush();
    if (!l) continue;
    if (/^#{1,3}\s/.test(l)) out.push({ k: 'head', t: l.replace(/^#+\s*/, '') });
    else if (l.length < 60 && l === l.toUpperCase() && /[A-ZА-Я]/.test(l)) out.push({ k: 'head', t: l });
    else out.push({ k: 'para', t: l });
  }
  flush();
  return out;
}

const hasCyr = (t: string) => /[Ѐ-ӿ]/.test(t), hasLat = (t: string) => /[A-Za-z]{3}/.test(t);
const wc = (t: string) => (t.match(/[\p{L}\p{N}]+/gu) || []).length;

export interface MdLine { t: string; lab: string; c: string; fw: number; lc: string; bg: string }
export function blocksToMd(blocks: RawBlock[]) {
  const md: MdLine[] = [], prev: { t: string; fw: number; fs: string; c: string }[] = [], src: string[] = [];
  let words = 0, rev = 0, heads = 0, tables = 0, n = 0;
  const L = (t: string, lab = '', o: Partial<MdLine> = {}) => { md.push({ t, lab, c: o.c || '#d6e2f0', fw: o.fw || 400, lc: o.lc || '#6fd08c', bg: o.bg || 'transparent' }); if (!o.bg) src.push(t); };
  for (const b of blocks) {
    if (b.k === 'head') { heads++; words += wc(b.t); const num = ++n, both = hasCyr(b.t) && hasLat(b.t);
      L('# ' + num + ' ' + (b.t.includes('|') ? b.t : b.t + (both ? '' : ' | ' + (hasCyr(b.t) ? '…EN' : '…МК'))), 'heading · ' + (both ? '0.96' : '0.71'), { c: '#7fb2e5', fw: 700, lc: both ? '#6fd08c' : '#f0b45a' });
      if (!both) rev++; prev.push({ t: b.t, fw: 700, fs: '10px', c: '#1f3b5a' }); }
    else if (b.k === 'para') { words += wc(b.t);
      if (/\(check!*\)|TODO|\?\?|xxx/i.test(b.t)) { rev++; L('  "' + b.t.slice(0, 40) + '" → editing note?', 'review · 0.41', { c: '#f0b45a', lc: '#f0b45a', bg: '#3a2a12' }); }
      else { const split = b.t.includes('|||') ? b.t : (hasCyr(b.t) && !hasLat(b.t) ? b.t + ' ||| …EN' : b.t);
        L(split, hasCyr(b.t) && hasLat(b.t) ? '' : hasCyr(b.t) ? 'EN missing' : 'MK missing', { lc: '#f0b45a' }); if (!(hasCyr(b.t) && hasLat(b.t))) rev++; }
      prev.push({ t: b.t, fw: 400, fs: '8px', c: '#333' }); }
    else if (b.k === 'table') { tables++; const r0 = b.rows[0] || [], kind = b.rows.length <= 8 && r0.length === 2 ? 'form' : 'table';
      L(kind === 'form' ? '[[FORM]]' : '[[TABLE]]', kind + ' · ' + (b.rows.length > 1 ? '0.9' + Math.min(4, b.rows.length) : '0.62'), { c: '#c59fe0', lc: b.rows.length > 1 ? '#6fd08c' : '#f0b45a' });
      b.rows.forEach((r, i) => { r.forEach(c => words += wc(c)); const line = r.map(c => c.trim() || '_').join(' ||| '); if (i < 6) L(line); else src.push(line); });
      if (b.rows.length > 6) md.push({ t: '… ' + (b.rows.length - 6) + ' more rows', lab: '', c: '#7f93a8', fw: 400, lc: '#6fd08c', bg: 'transparent' });
      L(kind === 'form' ? '[[/FORM]]' : '[[/TABLE]]', '', { c: '#c59fe0' });
      prev.push({ t: '▦ table ' + b.rows.length + '×' + r0.length, fw: 700, fs: '8px', c: '#2B547E' }); }
  }
  return { md, prev: prev.slice(0, 22), words, rev, heads, tables, markdown: src.join('\n') };
}

/** The `key: value` lines of a Markdown document's <!--HEADERDATA … --> block ({} when absent). */
export function headerMeta(md: string): Record<string, string> {
  const m = md.replace(/\r/g, '').match(/^<!--HEADERDATA\s*\n([\s\S]*?)^-->/m), out: Record<string, string> = {};
  for (const line of (m ? m[1] : '').split('\n')) { const i = line.indexOf(':'); if (i > 0) out[line.slice(0, i).trim()] = line.slice(i + 1).trim(); }
  return out;
}
