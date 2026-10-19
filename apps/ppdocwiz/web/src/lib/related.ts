// The parent-SOP page (Head of QC, 19.10.2026): the authors receive the SOP and the documents already in use under it
// and must complement them, not duplicate them. A brief whose title reads like one of those documents is flagged here.
import type { Relation, RelatedDoc } from '../api/types';

export const RELATION_LABEL: Record<Relation, string> = { annex: 'annex', child: 'child', listed: 'listed in the SOP' };

// Words that carry no meaning for "is this the same form": articles, prepositions and the generic document nouns.
const STOP = new Set(['the', 'a', 'an', 'of', 'and', 'or', 'for', 'to', 'in', 'on', 'at', 'by', 'with', 'from', 'form', 'record', 'log', 'logbook', 'checklist', 'template', 'sheet',
  'и', 'на', 'за', 'од', 'во', 'со', 'до', 'образец', 'запис', 'дневник', 'листа']);

/** The significant words of a title: lower-cased, letters and digits only, 3+ characters, not a stop word. */
export const words = (title: string) => new Set(title.toLowerCase().split(/[^\p{L}\p{N}]+/u).filter(w => w.length >= 3 && !STOP.has(w)));

/** Related documents whose title shares `min` (3) or more significant words with the brief's title, EN or MK. */
export function similarTitles(title_en: string, title_mk: string, related: RelatedDoc[], min = 3): RelatedDoc[] {
  const mine = [words(title_en || ''), words(title_mk || '')];
  const shared = (a: Set<string>, b: Set<string>) => [...a].filter(w => b.has(w)).length;
  return related.filter(r => Math.max(shared(mine[0], words(r.title_en || '')), shared(mine[1], words(r.title_mk || ''))) >= min);
}
