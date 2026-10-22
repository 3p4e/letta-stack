import { describe, expect, it } from 'vitest';
import { readQa, verdictOf } from './qa';

const LIVE_FIX = "I'll review the assembled document against the house rules.\n\n---\n\nVerdict: FIX\n\n**Issues to repair**\n- section 4 heading duplicated";

describe('§6A verdict', () => {
  it('reads the verdict line, not the first word', () => {
    expect(verdictOf(LIVE_FIX)).toBe('FIX');
    expect(verdictOf('Reviewed 9 sections.\n**Verdict: PASS**')).toBe('PASS');
    expect(verdictOf('PASS')).toBe('PASS');
    expect(verdictOf('FIX: section 2.0 cites the wrong clause')).toBe('FIX');
    expect(verdictOf('The bypass valve is fine.')).toBe('');
  });
  it('takes the last verdict when the text names both', () => {
    expect(verdictOf('Return verdict PASS or FIX.\n...\nVERDICT: FIX')).toBe('FIX');
  });
  it('a job that failed on the audit is never shown as PASS', () => {
    expect(readQa('Verdict: PASS', undefined, true)?.verdict).toBe('FIX');
    expect(readQa(LIVE_FIX, undefined, false)).toEqual({ verdict: 'FIX', text: LIVE_FIX.trim() });
  });
  it('prefers the verdict DocEngine stored', () => {
    expect(readQa('ambiguous text', 'PASS', false)?.verdict).toBe('PASS');
  });
  it('reads the older object shape and nothing stored', () => {
    expect(readQa({ verdict: 'FIX', issues: ['a', 'b'] }, undefined, true)).toEqual({ verdict: 'FIX', text: 'a\nb' });
    expect(readQa(undefined, undefined, false)).toBeNull();
  });
});
