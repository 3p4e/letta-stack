/** Line diff (LCS). Small inputs only — verify reports and HEADERDATA. */
export type DiffLine = { t: string; op: ' ' | '+' | '-' };
export function diffLines(a: string[], b: string[]): DiffLine[] {
  const n = a.length, m = b.length, L = Array.from({ length: n + 1 }, () => new Array<number>(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) L[i][j] = a[i] === b[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
  const out: DiffLine[] = [];
  let i = 0, j = 0;
  while (i < n && j < m) {
    if (a[i] === b[j]) { out.push({ t: a[i], op: ' ' }); i++; j++; }
    else if (L[i + 1][j] >= L[i][j + 1]) out.push({ t: a[i++], op: '-' });
    else out.push({ t: b[j++], op: '+' });
  }
  while (i < n) out.push({ t: a[i++], op: '-' });
  while (j < m) out.push({ t: b[j++], op: '+' });
  return out;
}
