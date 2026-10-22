import { C } from '../theme';

/** Colour a pp_verify output line the way the prototype does (FAIL red, PASS/[OK] green). */
export const lineColor = (t: string) => /FAIL/.test(t) ? C.bad : /RESULT: PASS|\[OK\]| OK$/.test(t) ? C.ok : '#9fb6cc';

/** A pp_verify report in the exact line format pp_verify.main() prints. */
export function verifyReport(file: string, o: { paras: number; tables: number; words: number; chars: number; srcWords?: number; minFont?: number; bilingual?: boolean; omath?: number; figures?: number }): string {
  const floorOk = (o.minFont ?? 7) >= 6;
  const fid = o.srcWords === undefined || o.words >= o.srcWords;
  const ok = floorOk && fid;
  return [
    `== VERIFY: ${file}`,
    `   paragraphs ${o.paras} · tables ${o.tables} · equations(oMath) ${o.omath ?? 0} · figures ${o.figures ?? 0}`,
    `   words ${o.words} · chars ${o.chars}`,
    `   min font ${(o.minFont ?? 7).toFixed(1)} pt  [${floorOk ? 'OK' : 'FAIL <6 pt'}]`,
    '   render environment OK',
    '   glyph coverage OK',
    `   bilingual MK+EN ${o.bilingual === false ? 'WARN (missing a language)' : 'OK'}`,
    ...(o.srcWords !== undefined ? [`   FIDELITY (§5A, markdown-source) output>=source: words ${o.words}>=${o.srcWords}  [${fid ? 'OK' : 'FAIL'}]`] : []),
    'RESULT: ' + (ok ? 'PASS' : 'FAIL'),
  ].join('\n');
}

export const nbsp = (n: number) => n.toLocaleString('de-DE').replace(/\./g, ' ');
