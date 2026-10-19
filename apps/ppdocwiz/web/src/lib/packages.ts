// The Library's Packages view (Head of QC, 19.10.2026): every SOP with the documents under it, approved and in use
// apart from the drafts, and the documents under no SOP grouped by family. Pure, so the grouping and the search are tested.
import type { LibraryPackage, ShelfEntry } from '../api/types';

/** The letters before the digits of a code: QCSOP001 → QCSOP, QCT002 → QCT. XXX is the engine's unconfirmed number
 *  (Head of QC, 18.10.2026), not part of the family: QASOPXXX → QASOP. */
export const family = (code: string) => (/^[A-Za-z]+?(?=XXX|\d|$)/.exec(code.replace(/[\s_-]/g, ''))?.[0] || code || '?').toUpperCase();

/** Loose entries grouped by family prefix, families alphabetical, codes in their given order. */
export function byFamily(entries: ShelfEntry[]): [string, ShelfEntry[]][] {
  const m = new Map<string, ShelfEntry[]>();
  for (const e of entries) { const f = family(e.code); if (!m.has(f)) m.set(f, []); m.get(f)!.push(e); }
  return [...m.entries()].sort((a, b) => a[0].localeCompare(b[0]));
}

const hit = (e: { code: string; title_en: string; title_mk: string }, q: string) => (e.code + ' ' + e.title_en + ' ' + e.title_mk).toLowerCase().includes(q);

/** Packages whose SOP or any member matches the query: a matching SOP keeps every member, a matching member keeps the
 *  package with only its matching members. An empty query keeps everything. `opened` names the packages a search should expand. */
export function filterPackages(packages: LibraryPackage[], query: string): { kept: LibraryPackage[]; opened: string[] } {
  const q = query.trim().toLowerCase();
  if (!q) return { kept: packages, opened: [] };
  const kept: LibraryPackage[] = [], opened: string[] = [];
  for (const p of packages) {
    if (hit(p.sop, q)) { kept.push(p); continue; }
    const members = p.members.filter(m => hit(m, q));
    if (members.length) { kept.push({ ...p, members }); opened.push(p.sop.code); }
  }
  return { kept, opened };
}

export const filterLoose = (entries: ShelfEntry[], query: string) => { const q = query.trim().toLowerCase(); return q ? entries.filter(e => hit(e, q)) : entries; };

/** Open by default when the group is small enough to read at a glance (≤ 8 packages), else collapsed. */
export const openByDefault = (count: number) => count <= 8;
