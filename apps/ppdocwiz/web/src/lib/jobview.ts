// Which job the Jobs screen shows (review 19.10.2026). The selected id used to fall back to jobs[0] silently when the
// list did not hold it, so a job opened from a brief or the Library showed another job's row.
import type { Job } from '../api/types';

export type Picked = { job: Job | null; fetch: string | null; empty: boolean };

/** `job` to show; `fetch` the id to read by GET /workflows/{id} when the selection is not listed (and not already read);
 *  `empty` when nothing is selected and the list is empty. */
export function pickJob(list: Job[], jobSel: string | null, fetched: Job | null): Picked {
  if (!jobSel) return { job: list[0] || null, fetch: null, empty: !list.length };
  const inList = list.find(j => j.id === jobSel);
  if (inList) return { job: inList, fetch: null, empty: false };
  if (fetched?.id === jobSel) return { job: fetched, fetch: null, empty: false };
  return { job: null, fetch: jobSel, empty: false };
}

/** A review in flight disables both decisions; Return also needs a note (the server returns 422 without one). */
/** Approve waits for a reason when the draft conflicts with, or was not checked against, an approved document (Head of
 *  QC, 19.10.2026); Return always needs a note. */
export const reviewLocks = (deciding: boolean, note: string, houseBlocks = false) =>
  ({ approve: !deciding && (!houseBlocks || !!note.trim()), ret: !deciding && !!note.trim() });

export type HouseVerdict = { verdict: string; detail: string };
export type HouseCheck = { checked: { code: string; version: string; title: string; why: string }[]; verdicts: Record<string, HouseVerdict>; note?: string; error?: string };
/** The documents the house check names as conflicting or unchecked — the ones that hold the approval. */
export const houseBlocking = (hc: HouseCheck | undefined) =>
  hc ? Object.entries(hc.verdicts || {}).filter(([, v]) => v.verdict === 'CONFLICT' || v.verdict === 'UNCHECKED').map(([c]) => c).sort() : [];

/** The list is polled only while a job can still change by itself. */
export const stillRunning = (list: Job[]) => list.some(j => j.status === 'running' || j.status === 'queued');
