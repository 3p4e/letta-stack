import { describe, expect, it } from 'vitest';
import { mockApi } from './mock';
import { limitValue } from '../lib/limits';

describe('canvas drafts (17.11.2026)', () => {
  it('opens a blank draft, saves with revisions, refuses a stale save, restores', async () => {
    const api = mockApi();
    const d = await api.canvasOpen({ source: 'blank', doctype: 'ANNEX' });
    expect(d.markdown).toContain('HEADERDATA');
    const r = await api.canvasSave(d.id, { markdown: d.markdown + '\nМ ||| E\n', rev: d.rev, note: 'x' });
    expect(r.rev).toBe(2);
    await expect(api.canvasSave(d.id, { markdown: 'stale text here', rev: 1 })).rejects.toMatchObject({ status: 409 });
    expect((await api.canvasRevisions(d.id)).map(x => x.rev)).toEqual([2, 1]);
    expect(await api.canvasRevision(d.id, 1)).toBe(d.markdown);
    expect((await api.canvasList()).length).toBe(1);
    await api.canvasDelete(d.id);
    expect((await api.canvasList()).length).toBe(0);
  });
  it('revises a section of a draft', async () => {
    const api = mockApi();
    const d = await api.canvasOpen({ source: 'blank' });
    const r = await api.canvasRevise(d.id, { instruction: 'shorter', markdown: d.markdown!, section: 0 });
    expect(r.markdown).toContain('shorter');
  });
});

describe('limit values', () => {
  it('reads the forms the engine reads', () => {
    expect(limitValue('2.7 × 10⁴').x).toBe(27000);
    expect(limitValue('< 10').x).toBe(10);
    expect(limitValue('10³–10⁴').x).toBe(10000);
    expect(limitValue('> 10 000 MPN/g = 100000').x).toBe(100000);
    expect(limitValue('-').kind).toBe('nr');
    expect(limitValue('Detected in 1 g').kind).toBe('det');
  });
});
