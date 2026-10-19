// TypeScript mirror of apps/ppdocwiz/backend/wizard.py::compose_markdown.
// The server stays authoritative (POST /api/wizard/preview); this copy lets the
// Source view, lint and live page update on every keystroke without a round trip.
// tests/compose.test.ts pins the two against the same example payload.
import type { Block, Section, WizardPayload } from '../api/types';

export const HEADER_KEYS = [
  'mk_title', 'en_title', 'code', 'version', 'doctype', 'supersedes', 'parent', 'orient',
  'status', 'effective_date', 'review_date',
] as const;

const bil = (mk = '', en = '') => { mk = mk.trim(); en = en.trim(); return mk + (en ? ' ||| ' + en : ''); };
const cell = (mk = '', en = '') => { mk = mk.trim(); en = en.trim(); return mk + (en ? '~~' + en : ''); };

/** Where a Markdown line came from, so the editor, outline and lint can point at it. */
export interface LineRef { section?: number; block?: number; row?: number; header?: boolean }
export interface ComposedLine { text: string; ref: LineRef }

export function headerData(p: WizardPayload): Record<string, string> {
  const status = (p.status || 'draft').trim();
  const hd: Record<string, string> = {
    mk_title: (p.mk_title || '').trim(), en_title: (p.en_title || '').trim(), code: (p.code || '').trim(),
    version: (p.version || '01').trim(), doctype: (p.doctype || 'ANNEX').trim().toUpperCase(),
    supersedes: (p.supersedes || '').trim(), parent: (p.parent || '').trim(), orient: (p.orient || 'portrait').trim(),
    // A draft carries no effective or review date (pp_format document-control lifecycle);
    // status is only written when it is not the engine default.
    status: status === 'draft' ? '' : status,
    effective_date: status === 'approved' ? (p.effective_date || '').trim() : '',
    review_date: status === 'approved' ? (p.review_date || '').trim() : '',
  };
  return hd;
}

function blockLines(b: Block): { text: string; row?: number }[] {
  const out: { text: string; row?: number }[] = [];
  if (b.type === 'text') b.paras.forEach((pa, i) => { const l = bil(pa.mk, pa.en); if (l) out.push({ text: l, row: i }); });
  else if (b.type === 'bullets') b.paras.forEach((pa, i) => { const l = bil(pa.mk, pa.en); if (l) out.push({ text: '- ' + l, row: i }); });
  else if (b.type === 'form') {
    out.push({ text: '[[FORM]]' });
    b.rows.forEach((r, i) => out.push({ text: `${(r.label_mk || '').trim()} ||| ${(r.label_en || '').trim()} ||| ${(r.value || '').trim() || '_'}`, row: i }));
    out.push({ text: '[[/FORM]]' });
  } else if (b.type === 'table') {
    out.push({ text: '[[TABLE]]' });
    out.push({ text: b.cols.map(c => cell(c.mk, c.en)).join(' ||| '), row: -1 });
    b.rows.forEach((r, i) => out.push({ text: r.map(c => cell(c.mk, c.en)).join(' ||| '), row: i }));
    out.push({ text: '[[/TABLE]]' });
  }
  return out;
}

export function sectionHeading(s: Section): string {
  const lvl = Math.max(1, Math.min(3, Number(s.level) || 1));
  const num = (s.num || '').trim();
  const mk = (num ? num + ' ' : '') + (s.mk || '').trim();
  const en = (s.en || '').trim();
  return '#'.repeat(lvl) + ' ' + mk + (en ? ' | ' + en : '');
}

export function composeLines(p: WizardPayload): ComposedLine[] {
  const hd = headerData(p);
  const out: ComposedLine[] = [{ text: '<!--HEADERDATA', ref: { header: true } }];
  for (const k of HEADER_KEYS) if (hd[k]) out.push({ text: `${k}: ${hd[k]}`, ref: { header: true } });
  out.push({ text: '-->', ref: { header: true } });
  out.push({ text: '', ref: {} });
  p.sections.forEach((s, si) => {
    out.push({ text: sectionHeading(s), ref: { section: si } });
    s.blocks.forEach((b, bi) => blockLines(b).forEach(l => out.push({ text: l.text, ref: { section: si, block: bi, row: l.row } })));
    out.push({ text: '', ref: {} });
  });
  while (out.length && out[out.length - 1].text === '') out.pop();
  return out;
}

export function composeMarkdown(p: WizardPayload): string {
  return composeLines(p).map(l => l.text).join('\n').replace(/\s+$/, '') + '\n';
}

// ---- lint: the bilingual checks the gate will run, surfaced while typing ----
export interface Lint { line: number; level: 'warn' | 'bad'; msg: string; section: number; block: number; row: number; col?: number }

const hasCyr = (t: string) => /[Ѐ-ӿ]/.test(t);
const hasLat = (t: string) => /[A-Za-z]{2}/.test(t);

/** A cell needs an EN half when its MK half carries Cyrillic words. Numbers and codes don't. */
const needsEn = (mk: string, en: string) => hasCyr(mk) && !en.trim();

export function lint(p: WizardPayload): Lint[] {
  const lines = composeLines(p), out: Lint[] = [];
  const lineOf = (si: number, bi: number, row: number) => 1 + lines.findIndex(l => l.ref.section === si && l.ref.block === bi && l.ref.row === row);
  p.sections.forEach((s, si) => {
    if (hasCyr(s.mk) && !s.en.trim()) out.push({ line: 1 + lines.findIndex(l => l.ref.section === si && l.ref.block === undefined), level: 'warn', msg: 'heading EN half missing', section: si, block: -1, row: -1 });
    s.blocks.forEach((b, bi) => {
      if (b.type === 'text' || b.type === 'bullets') b.paras.forEach((pa, i) => { if (needsEn(pa.mk, pa.en)) out.push({ line: lineOf(si, bi, i), level: 'warn', msg: 'EN half missing', section: si, block: bi, row: i }); });
      if (b.type === 'form') b.rows.forEach((r, i) => { if (needsEn(r.label_mk, r.label_en)) out.push({ line: lineOf(si, bi, i), level: 'warn', msg: 'EN half missing', section: si, block: bi, row: i }); });
      if (b.type === 'table') {
        b.cols.forEach((c, ci) => { if (needsEn(c.mk, c.en)) out.push({ line: lineOf(si, bi, -1), level: 'warn', msg: 'EN half missing (header)', section: si, block: bi, row: -1, col: ci }); });
        b.rows.forEach((r, i) => r.forEach((c, ci) => { if (needsEn(c.mk, c.en)) out.push({ line: lineOf(si, bi, i), level: 'warn', msg: 'EN half missing (~~)', section: si, block: bi, row: i, col: ci }); }));
      }
    });
  });
  const hd = headerData(p);
  const arrow = (['code', 'mk_title', 'en_title', 'version', 'parent', 'supersedes'] as const).find(k => (hd[k] || '').includes('-->'));
  if (arrow) out.unshift({ line: 1, level: 'bad', msg: `"-->" in ${arrow} ends HEADERDATA early`, section: -1, block: -1, row: -1 });
  return out;
}

export { hasCyr, hasLat };
