// Registry rules shared by the Formatter and the Library (review 14.10.2026).
//
// A document code is a house code (WHSOP_003, QCSOP_025_A01, QCLB_021, PP-QC-SOP-025): upper case, parts joined
// by "_" or "-". The Formatter used to register the uploaded file's name as the code ("labels_raw (final) v3"),
// and the Library then showed that row as the effective version of the "code".
export const CODE_RE = /^[A-Z][A-Z0-9]{0,9}(?:[_-][A-Z0-9]{1,6}){1,4}$/;
const CODE_IN_TEXT = /\b[A-Z]{2,9}(?:[_-][A-Z0-9]{1,6}){1,4}\b/;

export type RegMeta = { code: string; title_mk: string; title_en: string; version: string };

/** Code, titles and version for a document about to be registered: its own HEADERDATA first, then the first
 *  house code that appears in its text. Never the file name. */
export function guessMeta(header: Record<string, string>, text: string): RegMeta {
  const code = (header.code || '').trim();
  return {
    code: CODE_RE.test(code) ? code : ((text.match(CODE_IN_TEXT) || [''])[0]),
    title_mk: (header.mk_title || '').trim(),
    title_en: (header.en_title || '').trim(),
    version: (header.version || '01').trim(),
  };
}

/** What is missing before a document may be registered; empty when it may. */
export function metaProblems(m: RegMeta): string[] {
  const out: string[] = [];
  if (!CODE_RE.test(m.code.trim())) out.push('a document code like WHSOP_003 or QCSOP_025_A01');
  if (!m.title_mk.trim()) out.push('the Macedonian title');
  if (!m.title_en.trim()) out.push('the English title');
  if (!m.version.trim()) out.push('the version');
  return out;
}

type Ranked = { job_id?: string | null; version: string; created_at: string };
const vnum = (v: string) => parseFloat(v.replace(',', '.')) || 0;

/** A row from an approved workflow (it has a job) is a controlled version; a row from POST /build (the Formatter,
 *  no job) is a format-only copy. Controlled rows rank first, newest version first, so a format-only copy can
 *  never be shown as the effective version of a code. */
export const controlled = (r: Ranked) => !!r.job_id;
export function rankVersions<T extends Ranked>(rows: T[]): T[] {
  return [...rows].sort((a, b) => (+controlled(b) - +controlled(a)) || vnum(b.version) - vnum(a.version)
    || Date.parse(b.created_at) - Date.parse(a.created_at));
}
