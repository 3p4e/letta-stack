// Browser mirror of pp-document-suite/scripts/pp_data.py — enough to show the statistics a
// report would inject and to run assert_consistent() before the build is sent.
export const num = (x: unknown) => { const v = parseFloat(String(x ?? '').replace('±', '').replace(',', '.').trim()); return Number.isFinite(v) ? v : NaN; };
export const mean = (v: number[]) => v.reduce((a, b) => a + b, 0) / v.length;
export const sd = (v: number[]) => { if (v.length < 2) return 0; const m = mean(v); return Math.sqrt(v.reduce((a, b) => a + (b - m) ** 2, 0) / (v.length - 1)); };
export const rsd = (v: number[]) => { const m = mean(v); return m ? 100 * sd(v) / m : 0; };
const T975: Record<number, number> = { 1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 15: 2.131, 20: 2.086, 30: 2.042 };
export const t975 = (df: number) => { if (df <= 0) return NaN; const ks = Object.keys(T975).map(Number); const k = ks.filter(x => x <= df).pop() ?? 1; return df > 30 ? 1.96 : T975[k]; };
export const ci95 = (v: number[]) => { const h = t975(v.length - 1) * sd(v) / Math.sqrt(v.length); const m = mean(v); return [m - h, m + h] as const; };
export function ols(x: number[], y: number[]) { const mx = mean(x), my = mean(y); let sxy = 0, sxx = 0; x.forEach((xi, i) => { sxy += (xi - mx) * (y[i] - my); sxx += (xi - mx) ** 2; }); const slope = sxx ? sxy / sxx : 0; return { slope, intercept: my - slope * mx }; }
export function pearson(x: number[], y: number[]) { const mx = mean(x), my = mean(y); let a = 0, b = 0, c = 0; x.forEach((xi, i) => { a += (xi - mx) * (y[i] - my); b += (xi - mx) ** 2; c += (y[i] - my) ** 2; }); return b && c ? a / Math.sqrt(b * c) : 0; }
/** pp_data.assert_consistent: every printed figure must match its recomputation within tol. */
export const consistent = (reported: number, recomputed: number, tol = 0.01) => Math.abs(reported - recomputed) <= tol;

export interface Dataset { name: string; columns: string[]; rows: Record<string, string>[]; sha256: string; bytes: number; modified: string }

export function parseDataset(name: string, text: string): Omit<Dataset, 'sha256' | 'bytes' | 'modified'> {
  if (/\.json$/i.test(name)) {
    const j = JSON.parse(text); const rows: Record<string, unknown>[] = Array.isArray(j) ? j : Array.isArray(j.rows) ? j.rows : [];
    if (!rows.length) throw new Error('JSON must be an array of rows or {"rows": [...]}');
    const columns = Object.keys(rows[0]);
    return { name, columns, rows: rows.map(r => Object.fromEntries(columns.map(c => [c, String(r[c] ?? '')]))) };
  }
  const sep = /\.tsv$/i.test(name) ? '\t' : text.split('\n')[0].includes(';') ? ';' : ',';
  const lines = text.split(/\r?\n/).filter(l => l.trim());
  if (lines.length < 2) throw new Error('need a header row and at least one data row');
  const columns = lines[0].split(sep).map(s => s.trim());
  return { name, columns, rows: lines.slice(1).map(l => { const c = l.split(sep); return Object.fromEntries(columns.map((k, i) => [k, (c[i] ?? '').trim()])); }) };
}

export async function provenance(file: File) {
  const buf = await file.arrayBuffer();
  const h = await crypto.subtle.digest('SHA-256', buf);
  const hex = [...new Uint8Array(h)].map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 16);
  const d = new Date(file.lastModified), p = (n: number) => String(n).padStart(2, '0');
  return { sha256: hex, bytes: buf.byteLength, modified: `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`, text: new TextDecoder().decode(buf) };
}

export const SAMPLE_CSV = `replicate,batch,m0,m1,m2
R1,P160012,4.2210,12.4518,11.5236
R2,P160012,4.1987,12.3801,11.4603
R3,P160012,4.2302,12.5110,11.5772
R4,P160022,4.2051,12.4012,11.4911
R5,P160022,4.2144,12.4377,11.5180
R6,P160022,4.1899,12.3640,11.4532`;
