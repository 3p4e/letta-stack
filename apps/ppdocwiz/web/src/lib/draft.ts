// A generated draft as the canvas edits it (Head of QC, 20.10.2026): the HEADERDATA block, then one entry per level-1
// section with its heading line. Mirrors apps/wwf-docengine/app/revise.py split/join, so a section index means the same
// section on both sides.
export type Draft = { head: string; sections: string[] };

const H1 = /^# (?!#)/gm, H2 = /^## (?!#)/gm;
// Level 1 where the draft has two or more (an SOP's '# 1.0 …'), else level 2 (a form: one '# ' title over '## ' sections).
const level = (body: string) => ((body.match(H1) || []).length >= 2 || !(body.match(H2) || []).length ? H1 : H2);

export function splitDraft(md: string): Draft {
  let head = '', body = md;
  if (md.trimStart().startsWith('<!--HEADERDATA')) {
    const end = md.indexOf('-->');
    if (end >= 0) { head = md.slice(0, end + 3) + '\n'; body = md.slice(end + 3); }
  }
  const starts = [...body.matchAll(level(body))].map(m => m.index ?? 0);
  const trim = (x: string) => x.replace(/^\n+|\n+$/g, '');
  if (!starts.length) return { head, sections: body.trim() ? [trim(body)] : [] };
  // Text before the first section heading (a form's title) is a section of its own, as in revise.py.
  const pre = trim(body.slice(0, starts[0]));
  return { head, sections: [...(pre ? [pre] : []), ...starts.map((a, i) => trim(body.slice(a, starts[i + 1] ?? body.length)))] };
}

export function joinDraft(head: string, sections: string[]): string {
  return head.replace(/\n+$/, '') + '\n' + sections.map(s => s.replace(/^\n+|\n+$/g, '')).join('\n\n') + '\n';
}

/** The heading of a section without its '#' marks. */
export const sectionTitle = (s: string) => s.split('\n', 1)[0].replace(/^#+\s*/, '').trim();

/** One HEADERDATA field ('code', 'version', 'doctype', 'mk_title', 'en_title'), '' when absent. */
export const headField = (head: string, key: string) => (head.match(new RegExp(`^${key}:\\s*(.*)$`, 'm'))?.[1] || '').trim();

/** A prose line split into its two languages ('MK ||| EN'); a line without the separator is kept whole. */
export const bilingual = (line: string): [string, string] | null => {
  const i = line.indexOf('|||');
  return i < 0 ? null : [line.slice(0, i).trim(), line.slice(i + 3).trim()];
};

/** Lines that differ between two texts, for the accept / discard view: [kind, text] with kind '=' | '-' | '+'. */
export function lineDiff(a: string, b: string): ['=' | '-' | '+', string][] {
  const x = a.split('\n'), y = b.split('\n'), n = x.length, m = y.length;
  // LCS table — sections are short (tens to a few hundred lines), so O(n·m) is fine.
  const L = Array.from({ length: n + 1 }, () => new Array<number>(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) L[i][j] = x[i] === y[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
  const out: ['=' | '-' | '+', string][] = [];
  let i = 0, j = 0;
  while (i < n && j < m) {
    if (x[i] === y[j]) { out.push(['=', x[i]]); i++; j++; }
    else if (L[i + 1][j] >= L[i][j + 1]) out.push(['-', x[i++]]);
    else out.push(['+', y[j++]]);
  }
  while (i < n) out.push(['-', x[i++]]);
  while (j < m) out.push(['+', y[j++]]);
  return out;
}

/** Columns a revision added or removed, read from each changed table row ('A ||| B ||| C') paired with the row it replaced. */
export function columnChanges(diff: ['=' | '-' | '+', string][]): { added: string[]; removed: string[] } {
  const isRow = (l: string) => l.includes('|||') && !/^[\s|]*$/.test(l);
  const cells = (l: string) => l.split('|||').map(c => c.trim()).filter(Boolean);
  const gone = diff.filter(([k, l]) => k === '-' && isRow(l)).flatMap(([, l]) => cells(l));
  const come = diff.filter(([k, l]) => k === '+' && isRow(l)).flatMap(([, l]) => cells(l));
  return { added: come.filter(c => !gone.includes(c)), removed: gone.filter(c => !come.includes(c)) };
}
