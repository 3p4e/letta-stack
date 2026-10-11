import { describe, expect, it } from 'vitest';
import { pick, tr } from './i18n';

describe('interface language', () => {
  it('translates known interface strings and leaves the rest as they are', () => {
    expect(tr('mk', 'Jobs')).toBe('Задачи');
    expect(tr('en', 'Jobs')).toBe('Jobs');
    expect(tr('mk', 'POST /workflows ▸')).toBe('POST /workflows ▸');
  });
  it('puts the chosen language first in a bilingual label', () => {
    const l = { mk: 'Р1 — Опсег', en: 'R1 — Scope' };
    expect(pick('en', l)).toEqual(['R1 — Scope', 'Р1 — Опсег']);
    expect(pick('mk', l)).toEqual(['Р1 — Опсег', 'R1 — Scope']);
  });
});
