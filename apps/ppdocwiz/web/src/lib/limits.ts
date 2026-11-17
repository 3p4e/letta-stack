/** A [[LIMITS]] value as pp_limitbars.parse_value reads it (17.11.2026). */
const SUP: Record<string, string> = { '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', '⁻': '-' };
export function limitValue(raw: string): { label: string; x: number | null; kind: 'num' | 'nr' | 'abs' | 'det' | 'txt' } {
  const s = raw.trim();
  if (!s || s === '-' || s === '—') return { label: 'not reported', x: null, kind: 'nr' };
  if (/^(absent|отсутна|одговара|conforms|not detected|nd)\b/i.test(s)) return { label: s, x: null, kind: 'abs' };
  if (/^(detected|present|најден)/i.test(s)) return { label: s, x: null, kind: 'det' };
  if (s.includes('=')) { const [a, b] = [s.slice(0, s.lastIndexOf('=')), s.slice(s.lastIndexOf('=') + 1)]; const n = Number(b.replace(/[ ,]/g, '')); if (!isNaN(n)) return { label: a.trim(), x: n, kind: 'num' }; }
  const t = s.replace(/ /g, '').replace(/,/g, '.');
  const nums: number[] = [];
  for (const m of t.matchAll(/(\d+(?:\.\d+)?)?[×x]?10([⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+|\^-?\d+)|(\d+(?:\.\d+)?)/g)) {
    if (m[2]) nums.push(Number(m[1] || 1) * 10 ** Number(m[2].replace('^', '').split('').map(c => SUP[c] ?? c).join('')));
    else if (m[3]) nums.push(Number(m[3]));
  }
  return nums.length ? { label: s, x: Math.max(...nums), kind: 'num' } : { label: s, x: null, kind: 'txt' };
}
