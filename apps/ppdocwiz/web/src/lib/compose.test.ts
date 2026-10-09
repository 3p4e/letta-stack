import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import type { WizardPayload } from '../api/types';
import { composeMarkdown, lint } from './compose';

// Fixtures are written by backend/wizard.py (tests/test_wizard_parity.py regenerates and checks them),
// so this pins the in-browser composer to the server's byte for byte.
const fx = (n: string) => readFileSync(new URL('./fixtures/' + n, import.meta.url), 'utf-8');
const payload = JSON.parse(fx('payload.json')) as WizardPayload;

describe('composeMarkdown mirrors wizard.compose_markdown', () => {
  it('approved document with dates', () => expect(composeMarkdown(payload)).toBe(fx('payload.md')));
  it('draft omits status and dates', () => expect(composeMarkdown({ ...payload, status: 'draft' })).toBe(fx('payload_draft.md')));
});

describe('lint', () => {
  it('flags Cyrillic text without an EN half, not numbers', () => {
    const l = lint(payload);
    expect(l.map(x => x.msg)).toEqual(expect.arrayContaining(['EN half missing', 'heading EN half missing']));
    expect(l.find(x => x.msg === 'EN half missing')!.row).toBe(1);
  });
  it('rejects --> in a header field', () => {
    expect(lint({ ...payload, code: 'X-->' })[0]).toMatchObject({ level: 'bad' });
  });
});
