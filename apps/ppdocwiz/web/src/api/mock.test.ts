import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DEFAULT_BANK, fits, mockApi } from './mock';

// The mock drifted from DocEngine app/brief.py (review 19.10.2026): it accepted any field key, kept an SOP question
// set on an annex package, returned a job without a note and built a closed brief. Same rules now.
describe('mock brief rules (brief.py apply_patch)', () => {
  beforeEach(() => { vi.stubGlobal('window', { setInterval: globalThis.setInterval.bind(globalThis), clearInterval: globalThis.clearInterval.bind(globalThis) }); });
  afterEach(() => { vi.unstubAllGlobals(); });

  it('a package change swaps the question set to the package\'s own', async () => {
    const api = mockApi();
    const b = await api.createBrief({ package: 'sop' });
    expect(b.questionnaire).toBe('sop_qc');
    const b2 = await api.patchBrief(b.id, { rev: b.rev, package: 'annex' });
    expect(b2.package).toBe('annex');
    expect(b2.questionnaire).toBe(DEFAULT_BANK.annex);
    expect(fits('annex', b2.questionnaire)).toBe(true);
  });

  it('refuses a question set that does not fit the package, and an unknown one', async () => {
    const api = mockApi();
    const b = await api.createBrief({ package: 'form' });
    await expect(api.patchBrief(b.id, { rev: b.rev, questionnaire: 'sop_qc' })).rejects.toMatchObject({ status: 400 });
    await expect(api.patchBrief(b.id, { rev: b.rev, questionnaire: 'nope' })).rejects.toMatchObject({ status: 400 });
    await expect(api.createBrief({ package: 'annex', questionnaire: 'sop_qc' })).rejects.toMatchObject({ status: 400 });
  });

  it('refuses a field that is not a question of the brief and an unknown meta key; accepts its own', async () => {
    const api = mockApi();
    const b = await api.createBrief({ package: 'sop' });
    await expect(api.patchBrief(b.id, { rev: b.rev, set: { 'not.a.key': 'x' } })).rejects.toMatchObject({ status: 400 });
    await expect(api.patchBrief(b.id, { rev: b.rev, meta: { harvest: 'x' } })).rejects.toMatchObject({ status: 400 });
    const b2 = await api.patchBrief(b.id, { rev: b.rev, set: { 'doc.purpose': 'why' }, meta: { title_en: 'T' } });
    expect(b2.fields['doc.purpose'].value).toBe('why');
    expect(b2.rev).toBe(b.rev + 1);
    await expect(api.patchBrief(b.id, { rev: b.rev, set: {} })).rejects.toMatchObject({ status: 409 });
  });

  it('builds only with a title and at the current rev (a closed brief is refused the same way, 409)', async () => {
    const api = mockApi();
    const b = await api.createBrief({ package: 'sop' });
    await expect(api.buildBrief(b.id, b.rev)).rejects.toMatchObject({ status: 400 });
    const b2 = await api.patchBrief(b.id, { rev: b.rev, meta: { title_en: 'T' } });
    await expect(api.buildBrief(b2.id, b.rev)).rejects.toMatchObject({ status: 409 });
    expect((await api.buildBrief(b2.id, b2.rev)).status).toBe('queued');
    await expect(api.buildBrief('no-such', 0)).rejects.toMatchObject({ status: 404 });
  });
});

describe('mock jobs', () => {
  beforeEach(() => { vi.stubGlobal('window', { setInterval: globalThis.setInterval.bind(globalThis), clearInterval: globalThis.clearInterval.bind(globalThis) }); });
  afterEach(() => { vi.unstubAllGlobals(); });

  it('review: 422 without a note on return, 404 for a missing job, 409 when not awaiting review', async () => {
    const api = mockApi();
    const jobs = await api.jobs();
    const waiting = jobs.find(j => j.status === 'awaiting_review')!, failed = jobs.find(j => j.status === 'failed')!;
    await expect(api.reviewJob(waiting.id, 'return', '  ')).rejects.toMatchObject({ status: 422 });
    await expect(api.reviewJob('no-such', 'approve', '')).rejects.toMatchObject({ status: 404 });
    await expect(api.reviewJob(failed.id, 'approve', '')).rejects.toMatchObject({ status: 409 });
  });

  it('re-run copies the stored payload into a new job and refuses a job that is not failed', async () => {
    const api = mockApi();
    const jobs = await api.jobs();
    const failed = jobs.find(j => j.status === 'failed')!, done = jobs.find(j => j.status === 'done')!;
    const r = await api.rerunJob(failed.id);
    const j = await api.job(r.job_id);
    expect(j.payload.meta).toEqual(failed.payload.meta);
    expect(j.payload.rerun_of).toBe(failed.id);
    expect(['queued', 'running']).toContain(j.status);
    await expect(api.rerunJob(done.id)).rejects.toMatchObject({ status: 409 });
    await expect(api.rerunJob('no-such')).rejects.toMatchObject({ status: 404 });
  });
});

// 19.10.2026: brief sources carry a role, the brief holds at most 20, and the library groups SOP packages.
describe('mock sources, related documents and packages (19.10.2026)', () => {
  beforeEach(() => { vi.stubGlobal('window', { setInterval: globalThis.setInterval.bind(globalThis), clearInterval: globalThis.clearInterval.bind(globalThis) }); });
  afterEach(() => { vi.unstubAllGlobals(); });

  it('uploads with a role (content by default), changes it, and refuses the 21st source with 409', async () => {
    const api = mockApi();
    const b = await api.createBrief({ package: 'annex' });
    const r = await api.addBriefSource(b.id, 'a.md', 'aGVsbG8=');
    expect(r.brief.sources[0].role).toBe('content');
    const r2 = await api.addBriefSource(b.id, 'b.pdf', 'aGVsbG8=', 'format');
    expect(r2.brief.sources[1].role).toBe('format');
    const b2 = await api.setSourceRole(b.id, r.id, 'example');
    expect(b2.sources.find(s => s.id === r.id)?.role).toBe('example');
    expect(b2.rev).toBe(r2.brief.rev + 1);
    await expect(api.setSourceRole(b.id, 'nope', 'content')).rejects.toMatchObject({ status: 404 });
    await expect(api.addBriefSource(b.id, 'c.exe', 'aGVsbG8=')).rejects.toMatchObject({ status: 400 });
    for (let i = b2.sources.length; i < 20; i++) await api.addBriefSource(b.id, `s${i}.md`, 'aGVsbG8=');
    await expect(api.addBriefSource(b.id, 'one-too-many.md', 'aGVsbG8=')).rejects.toMatchObject({ status: 409 });
  });

  it('names the approved parent SOP and what is in use under it; found=false for a code without an approved copy', async () => {
    const api = mockApi();
    const r = await api.houseRelated('qcsop001');
    expect(r.found).toBe(true);
    expect(r.code).toBe('QCSOP001');
    expect(r.related.map(x => [x.code, x.relation])).toEqual([['QCT002', 'listed'], ['QCT003', 'listed'], ['QCLB001', 'listed']]);
    const none = await api.houseRelated('QCSOP019');
    expect(none).toMatchObject({ found: false, related: [] });
  });

  it('groups the library into in-use and draft packages with loose documents', async () => {
    const lib = await mockApi().library();
    expect(lib.packages.in_use.map(p => p.sop.code)).toEqual(['QCSOP001', 'QCSOP011', 'QCSOP022']);
    expect(lib.packages.drafts[0].members[0]).toMatchObject({ code: 'QCSOP019A01', relation: 'annex' });
    expect(lib.loose.drafts.map(e => e.code)).toEqual(['QASOPXXX']);
    expect(lib.counts.approved).toBe(lib.shelves.approved.length);
  });
});
