// The Workflow's page list and the page to show when the list changes (review 19.10.2026): a package change can
// drop the page in view (the annexes page, a question round), and the screen then showed an empty body.
import type { Package } from '../api/types';

export const TEXT_PAGE_KEYS: [string, string][] = [['purpose', 'Purpose'], ['scope', 'Scope'], ['use', 'Use and users'], ['resp', 'Responsibilities']];

/** [key, label] of every page: start, identity, the four text pages, sources, one per question round, annexes (SOP + annexes,
 *  annex), references, review. The Sources page (Head of QC, 19.10.2026) follows the Parent SOP page of an annex, so the
 *  parent is named before the sources that complement it; every other package has it after Identity's content pages. */
export function briefPages(roundTitles: string[], pkg?: Package): [string, string][] {
  const p: [string, string][] = [['start', 'Start'], ['identity', 'Identity'], ...TEXT_PAGE_KEYS];
  if (pkg !== 'annex') p.push(['sources', 'Sources']);
  roundTitles.forEach((t, i) => p.push([`q${i}`, t]));
  if (pkg === 'sop_annexes' || pkg === 'annex') p.push(['annexes', pkg === 'annex' ? 'Parent SOP' : 'Annexes']);
  if (pkg === 'annex') p.push(['sources', 'Sources']);
  p.push(['refs', 'References'], ['review', 'Review & build']);
  return p;
}

/** The page itself while the list holds it, else Identity. */
export const pageOrIdentity = (pages: [string, string][], page: string) => pages.some(p => p[0] === page) ? page : 'identity';
