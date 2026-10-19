// The §6A audit verdict as DocEngine stores it.
//
// DocEngine (apps/wwf-docengine/app/pipeline.py) stores `result.qa_audit` as the auditor's own text and
// `result.qa_verdict` as the verdict it parsed from that text. Older job rows carry only the text, and the
// mock adapter used to send `{ verdict, issues }`. All three shapes are read here, and the screen shows the
// auditor's words, never a canned summary: a failed job once displayed "PASS · every citation traced"
// from sample data while its stored verdict was FIX (live test 10.10.2026).
export type QaVerdict = 'PASS' | 'FIX' | '';
export type Qa = { verdict: QaVerdict; text: string };

const VERDICT_LINE = /\bverdict\b[\s:*_`-]*\**\s*(PASS|FIX)\b/gi;
const BARE_LINE = /^[\s*#_`>-]*(PASS|FIX)\b/i;

/** The verdict in an auditor's free text: the last "Verdict: X", else the last line that opens with PASS or FIX. */
export function verdictOf(text: string): QaVerdict {
  const all = [...text.matchAll(VERDICT_LINE)];
  if (all.length) return all[all.length - 1][1].toUpperCase() as QaVerdict;
  const lines = text.split('\n').map(l => BARE_LINE.exec(l)?.[1]).filter(Boolean) as string[];
  return lines.length ? (lines[lines.length - 1].toUpperCase() as QaVerdict) : '';
}

/** Read `result.qa_audit` / `result.qa_verdict` in any stored shape. `failedAt6A` = the job failed on the audit. */
export function readQa(raw: unknown, stored: unknown, failedAt6A: boolean): Qa | null {
  if (raw == null || raw === '') return null;
  let text: string, verdict: QaVerdict;
  if (typeof raw === 'string') { text = raw.trim(); verdict = verdictOf(text); }
  else {
    const o = raw as { verdict?: string; issues?: string[] };
    verdict = (String(o.verdict || '').toUpperCase() === 'PASS' ? 'PASS' : String(o.verdict || '').toUpperCase() === 'FIX' ? 'FIX' : '');
    text = (o.issues || []).join('\n');
  }
  if (stored === 'PASS' || stored === 'FIX') verdict = stored;
  // The job row is the authority: a job that failed on the audit did not pass it, whatever the text says.
  if (failedAt6A && verdict !== 'FIX') verdict = 'FIX';
  return { verdict, text };
}
