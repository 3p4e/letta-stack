// Registry rules shared by the Formatter and the Library (review 14.10.2026).
//
// A document code is in the house form of QALI 001 (Head of QC, 18.10.2026): family letters, three digits, an
// annex as "A" + two digits — QCSOP011, QCT017, QCLB021, QCCoA001, QCSOP011A01. Latin only, no separators.
// The forms in circulation ("QCSOP 011", "WHSOP_003_A04", a Cyrillic "А") are normalised; a file name is not a code
// (the Formatter once registered "labels_raw (final) v3", and the Library showed it as an effective version).
// A number not yet confirmed is XXX (Head of QC, 18.10.2026): QASOPXXX, QASOPXXXA06; "QASOP_0XX" reads as QASOPXXX.
// Same rule as DocEngine app/house_codes.py.
export const CODE_RE = /^(?:[A-Z]{2,8}?|[A-Z]{2}CoA)(?:\d{3}|XXX)(?:A\d{2})?$/;
const LOOKALIKE: Record<string, string> = { А: 'A', В: 'B', С: 'C', Е: 'E', Н: 'H', І: 'I', Ј: 'J', К: 'K', М: 'M', О: 'O', Р: 'P', Т: 'T', Х: 'X', У: 'Y', а: 'a', е: 'e', с: 'c', о: 'o', р: 'p', х: 'x', у: 'y' };
const LOOSE = /^([A-Z]{2,8}?|[A-Z]{2}COA)(\d{1,3}|0?XXX|0XX)(?:A(\d{1,2}))?$/;
const CODE_IN_TEXT = /\b(?:[A-Z]{2,8}|[A-Z]{2}CoA)[ _-]?\d{3}(?:[ _-]?[AА]\d{2})?\b/;

/** The house form of a typed code, or '' when it is not a document code. */
export function normalizeCode(raw: string): string {
  const s = [...(raw || '')].map(ch => LOOKALIKE[ch] || ch).join('').toUpperCase().replace(/[\s_\-./]/g, '');
  const m = LOOSE.exec(s);
  if (!m) return '';
  const fam = m[1].endsWith('COA') ? m[1].slice(0, -3) + 'CoA' : m[1];
  return fam + (m[2].includes('X') ? 'XXX' : m[2].padStart(3, '0')) + (m[3] ? 'A' + m[3].padStart(2, '0') : '');
}

/** True for a code whose number is not yet confirmed (QASOPXXX): two such drafts are different documents. */
export function isUnconfirmed(code: string): boolean {
  return /^[A-Z]+?XXX(?:A\d{2})?$/.test(code);
}

export type RegMeta = { code: string; title_mk: string; title_en: string; version: string };

/** Code, titles and version for a document about to be registered: its own HEADERDATA first, then the first
 *  house code that appears in its text. Never the file name. */
export function guessMeta(header: Record<string, string>, text: string): RegMeta {
  return {
    code: normalizeCode(header.code || '') || normalizeCode((text.match(CODE_IN_TEXT) || [''])[0]),
    title_mk: (header.mk_title || '').trim(),
    title_en: (header.en_title || '').trim(),
    version: (header.version || '01').trim(),
  };
}

/** What is missing before a document may be registered; empty when it may. */
export function metaProblems(m: RegMeta): string[] {
  const out: string[] = [];
  if (!normalizeCode(m.code)) out.push('a document code in the house form, like QCSOP011 or QCSOP011A01');
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

/** The package a library row is revised or continued as (Workflow "Revise or continue", review 19.10.2026): its own
 *  `package` when the shelf says it; else from the code — an annex ends in A\d\d, an *SOP family is an SOP, and any
 *  other family (QCT, QCLB, QCCoA …) is a standalone form. Until then every non-annex code opened as an SOP. */
export function packageOf(e: { code: string; approved: { package?: string } | null; wip: { package?: string }[] }): 'sop' | 'sop_annexes' | 'annex' | 'form' | 'report' {
  const own = (e.wip[0] || e.approved)?.package;
  if (own === 'sop' || own === 'sop_annexes' || own === 'annex' || own === 'form' || own === 'report') return own;
  if (/A\d\d$/.test(e.code)) return 'annex';
  return /SOP/.test(e.code) ? 'sop' : 'form';
}
