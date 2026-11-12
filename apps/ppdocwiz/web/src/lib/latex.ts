// LaTeX formulas in the Builder (04.11.2026). The engine turns $…$ / $$…$$ into native Word equations (pp_math, pandoc);
// this file only FINDS formulas and inserts them. Whether one converts is the SERVER's answer (POST /api/equations/check),
// because the build uses the same converter: a browser-side maths library would be a second engine that accepts or
// draws things pandoc does not.

export interface FormulaPiece { kind: 'text' | 'math' | 'display'; value: string }

/** Mirror of pp_math._MATH: $$…$$ display; $…$ inline (no space inside the dollars, not followed by a digit); \$ is a dollar. */
const MATH = /(?<!\\)\$\$(.+?)(?<!\\)\$\$|(?<![\\$])\$(?=\S)((?:[^$\\\n]|\\.)+?)(?<=\S)\$(?![0-9$])/gs;

export function pieces(text: string): FormulaPiece[] {
  const out: FormulaPiece[] = []; let pos = 0;
  for (const m of text.matchAll(MATH)) {
    const at = m.index ?? 0;
    if (at > pos) out.push({ kind: 'text', value: text.slice(pos, at) });
    out.push(m[1] !== undefined ? { kind: 'display', value: m[1].trim() } : { kind: 'math', value: m[2].trim() });
    pos = at + m[0].length;
  }
  if (pos < text.length) out.push({ kind: 'text', value: text.slice(pos) });
  return out;
}

export const formulasOf = (text: string) => pieces(text).filter(p => p.kind !== 'text').map(p => p.value);

/** Cheap checks before the server is asked: an empty formula, unbalanced braces, \left without \right. */
export function localProblems(latex: string): string[] {
  const out: string[] = [], t = latex.replace(/\\[{}]/g, '');
  if (!latex.trim()) return ['the formula is empty'];
  let depth = 0;
  for (const ch of t) { if (ch === '{') depth++; if (ch === '}') depth--; if (depth < 0) break; }
  if (depth !== 0) out.push('braces { } do not match');
  if ((latex.match(/\\left\b/g) || []).length !== (latex.match(/\\right\b/g) || []).length) out.push('\\left and \\right do not pair');
  return out;
}

export type InsertMode = 'inline' | 'display' | 'eq';

/** The Markdown to write for a formula: `$x$` in a line, `$$x$$` on its own line, or a one-formula [[EQ]] panel. */
export function formulaMarkdown(latex: string, mode: InsertMode): string {
  const tex = latex.trim();
  return mode === 'inline' ? `$${tex}$` : mode === 'display' ? `$$${tex}$$` : `[[EQ]]\n$${tex}$\n[[/EQ]]`;
}

/** Finished formula Markdown written over [start, end); the caret goes after it. A block form ($$…$$, [[EQ]]) gets a line to itself. */
export function insertMarkdown(text: string, start: number, end: number, md: string): { text: string; caret: number } {
  if (md.startsWith('$$') || md.startsWith('[[EQ]]')) {
    const before = text.slice(0, start), after = text.slice(end);
    md = (before && !before.endsWith('\n') ? '\n' : '') + md + (after.startsWith('\n') ? '' : '\n');
  }
  return { text: text.slice(0, start) + md + text.slice(end), caret: start + md.length };
}

/** text with the formula written over [start, end) in the given mode. */
export function insertFormula(text: string, start: number, end: number, latex: string, mode: InsertMode): { text: string; caret: number } {
  return insertMarkdown(text, start, end, formulaMarkdown(latex, mode));
}

/** Quick-insert pieces for the dialog. Names are upright (\text), decimals use {,}: the grammar the engine documents. */
export const SNIPPETS: { label: string; tex: string; title: string }[] = [
  { label: 'a⁄b', tex: '\\frac{a}{b}', title: 'fraction' },
  { label: '√', tex: '\\sqrt{x}', title: 'square root' },
  { label: 'Σ', tex: '\\sum_{i=1}^{n} x_i', title: 'sum' },
  { label: 'xᵢ', tex: 'x_{i}', title: 'subscript' },
  { label: 'x²', tex: 'x^{2}', title: 'superscript' },
  { label: 'x̄', tex: '\\bar{x}', title: 'mean' },
  { label: 'THC', tex: '\\text{THC}', title: 'a name, upright' },
  { label: '×', tex: '\\times ', title: 'times' },
  { label: '·', tex: '\\cdot ', title: 'multiplication dot' },
  { label: '±', tex: '\\pm ', title: 'plus or minus' },
  { label: '≤', tex: '\\le ', title: 'less than or equal' },
  { label: '≥', tex: '\\ge ', title: 'greater than or equal' },
  { label: 'Δ', tex: '\\Delta ', title: 'delta' },
  { label: '%', tex: '\\,\\%', title: 'percent with a thin space' },
  { label: '0,877', tex: '0{,}877', title: 'decimal comma (Macedonian)' },
  { label: '( )', tex: '\\left( x \\right)', title: 'brackets that grow' },
];

/** A starting formula per common need, so the author edits instead of typing from nothing. */
export const TEMPLATES: { label: string; tex: string }[] = [
  { label: 'Total THC', tex: '\\text{Total THC}=\\text{THC}+\\left(\\text{THCA}\\times 0{,}877\\right)' },
  { label: 'RSD %', tex: '\\mathrm{RSD}=\\frac{s}{\\bar{x}}\\times 100' },
  { label: 'Combined uncertainty', tex: 'u_c=\\sqrt{\\sum_i u_i^2}' },
  { label: 'Expanded uncertainty', tex: 'U=k\\cdot u_c' },
  { label: 'Loss on drying', tex: '\\mathrm{LOD}=\\frac{m_0-m_1}{m_0}\\times 100' },
  { label: 'Recovery %', tex: '\\mathrm{Recovery}=\\frac{C_{found}}{C_{added}}\\times 100' },
];
