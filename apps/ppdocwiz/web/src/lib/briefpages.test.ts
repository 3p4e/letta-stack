import { describe, expect, it } from 'vitest';
import { briefPages, pageOrIdentity } from './briefpages';

describe('Workflow pages (review 19.10.2026)', () => {
  it('lists the annexes page for SOP + annexes and the parent page for an annex, neither for a form', () => {
    expect(briefPages(['R1'], 'sop_annexes').map(p => p[0])).toEqual(['start', 'identity', 'purpose', 'scope', 'use', 'resp', 'sources', 'q0', 'annexes', 'refs', 'review']);
    expect(briefPages(['R1'], 'annex').find(p => p[0] === 'annexes')?.[1]).toBe('Parent SOP');
    expect(briefPages(['R1', 'R2'], 'form').map(p => p[0])).toEqual(['start', 'identity', 'purpose', 'scope', 'use', 'resp', 'sources', 'q0', 'q1', 'refs', 'review']);
  });
  it('puts the Sources page after Parent SOP for an annex, after the content pages otherwise (19.10.2026)', () => {
    expect(briefPages(['R1'], 'annex').map(p => p[0])).toEqual(['start', 'identity', 'purpose', 'scope', 'use', 'resp', 'q0', 'annexes', 'sources', 'refs', 'review']);
    expect(briefPages([], 'sop').map(p => p[0])).toEqual(['start', 'identity', 'purpose', 'scope', 'use', 'resp', 'sources', 'refs', 'review']);
    expect(briefPages([], 'annex').filter(p => p[0] === 'sources')).toHaveLength(1);
  });
  it('falls back to Identity when the page in view left the list', () => {
    const before = briefPages(['R1'], 'sop_annexes'), after = briefPages(['R1'], 'form');
    expect(pageOrIdentity(before, 'annexes')).toBe('annexes');
    expect(pageOrIdentity(after, 'annexes')).toBe('identity');
    expect(pageOrIdentity(after, 'q0')).toBe('q0');
  });
});
