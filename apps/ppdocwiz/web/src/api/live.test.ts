import { afterEach, describe, expect, it, vi } from 'vitest';
import { liveApi } from './live';

// The Fleet & health page's engine panel showed a 501 until 18.10.2026: live mode threw instead of
// calling DocEngine. It must now read GET /engine/environment through the same-origin proxy.
describe('live engine environment', () => {
  afterEach(() => { vi.unstubAllGlobals(); });

  it('calls DocEngine /engine/environment through the proxy', async () => {
    const env = { canon: '2026-10-09', version: 'synced copy · ee8525395374', synced: true, hash: 'ee8525395374', hashExpected: 'ee8525395374', fonts: [], glyphAudit: [], manifestDrift: [] };
    const fetchMock = vi.fn(async () => new Response(JSON.stringify(env), { status: 200 }));
    vi.stubGlobal('window', {});
    vi.stubGlobal('fetch', fetchMock);
    expect(await liveApi().engineEnv()).toEqual(env);
    expect(fetchMock).toHaveBeenCalledWith('/api/docengine/engine/environment', expect.objectContaining({ credentials: 'same-origin' }));
  });

  it('passes a DocEngine error through instead of inventing data', async () => {
    vi.stubGlobal('window', {});
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ detail: 'Unauthorized' }), { status: 401 })));
    await expect(liveApi().engineEnv()).rejects.toMatchObject({ status: 401 });
  });
});

// 19.10.2026 review: the Jobs screen's re-run, selection by id and polling, and the error text of a validation failure.
const storage = () => { const m = new Map<string, string>(); return { getItem: (k: string) => m.get(k) ?? null, setItem: (k: string, v: string) => { m.set(k, v); }, removeItem: (k: string) => { m.delete(k); } }; };
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const job = (id: string, status = 'failed', result: Record<string, unknown> = {}) => ({ id, kind: 'workflow', status, stage: 'x', payload: { questionnaire: 'sop_qc', answers: {}, meta: {}, requested_by: 'a' }, result, error: null, created_by: 'a', created_at: '', updated_at: '' });

describe('live jobs', () => {
  afterEach(() => { vi.unstubAllGlobals(); });

  it('re-runs through POST /workflows/{id}/rerun and remembers the new job', async () => {
    const ls = storage(); vi.stubGlobal('window', {}); vi.stubGlobal('localStorage', ls);
    const fetchMock = vi.fn(async () => json({ job_id: 'new-1', status: 'queued' }));
    vi.stubGlobal('fetch', fetchMock);
    expect(await liveApi().rerunJob('old 1')).toEqual({ job_id: 'new-1', status: 'queued' });
    expect(fetchMock).toHaveBeenCalledWith('/api/docengine/workflows/old%201/rerun', expect.objectContaining({ method: 'POST' }));
    expect(JSON.parse(ls.getItem('ppsuite.jobs')!)).toEqual(['new-1']);
  });

  it('reads one job by id and lists it from then on', async () => {
    const ls = storage(); vi.stubGlobal('window', {}); vi.stubGlobal('localStorage', ls);
    vi.stubGlobal('fetch', vi.fn(async () => json(job('j1'))));
    expect((await liveApi().job('j1')).id).toBe('j1');
    expect(JSON.parse(ls.getItem('ppsuite.jobs')!)).toEqual(['j1']);
  });

  it('keeps the last row of a job whose read failed and names the error, instead of emptying the list', async () => {
    const ls = storage(); ls.setItem('ppsuite.jobs', JSON.stringify(['j1', 'j2']));
    vi.stubGlobal('window', {}); vi.stubGlobal('localStorage', ls);
    let fail = false;
    vi.stubGlobal('fetch', vi.fn(async (url: string) => url.endsWith('/j2') && fail ? json({ detail: 'DocEngine storage unavailable' }, 503) : json(job(url.endsWith('/j1') ? 'j1' : 'j2'))));
    const api = liveApi();
    expect((await api.jobs()).map(j => j.id)).toEqual(['j1', 'j2']);
    fail = true;
    const rows = await api.jobs();
    expect(rows.map(j => j.id)).toEqual(['j1', 'j2']);
    expect(rows.err).toBe('503 · DocEngine storage unavailable');
  });

  it('lists the annex jobs a package started (result.package_jobs) beside their SOP', async () => {
    const ls = storage(); ls.setItem('ppsuite.jobs', JSON.stringify(['sop']));
    vi.stubGlobal('window', {}); vi.stubGlobal('localStorage', ls);
    vi.stubGlobal('fetch', vi.fn(async (url: string) => json(url.endsWith('/sop') ? job('sop', 'done', { package_jobs: [{ code: 'QCSOP026A01', job_id: 'a1', title_en: 'Log' }] }) : job('a1', 'running'))));
    expect((await liveApi().jobs()).map(j => j.id)).toEqual(['sop', 'a1']);
    expect(JSON.parse(ls.getItem('ppsuite.jobs')!)).toEqual(['a1', 'sop']);
  });

  it('reads a Pydantic validation list into one message', async () => {
    vi.stubGlobal('window', {});
    vi.stubGlobal('fetch', vi.fn(async () => json({ detail: [{ msg: 'field required', loc: ['body', 'meta', 'code'] }, { msg: 'value is not a valid list', loc: ['body', 'sources'] }] }, 422)));
    await expect(liveApi().startWorkflow({ questionnaire: 'sop_qc', answers: {}, meta: { title_mk: '', title_en: '', code: '' }, requested_by: '' }))
      .rejects.toMatchObject({ status: 422, message: 'field required at body.meta.code; value is not a valid list at body.sources' });
  });
});

// 19.10.2026: source roles and the parent SOP's related documents, against the DocEngine contract.
describe('live sources and related documents', () => {
  afterEach(() => { vi.unstubAllGlobals(); });

  it('POSTs a source with its role (content by default) and PATCHes a role', async () => {
    const brief = { id: 'b1', rev: 3, sources: [{ id: 's1', role: 'format' }] };
    const fetchMock = vi.fn(async () => json({ id: 's1', chars: 5, note: '', brief }));
    vi.stubGlobal('window', {}); vi.stubGlobal('fetch', fetchMock);
    const api = liveApi();
    await api.addBriefSource('b1', 'a.md', 'aGVsbG8=');
    expect(JSON.parse((fetchMock.mock.calls[0] as unknown as [string, RequestInit])[1].body as string)).toMatchObject({ name: 'a.md', content_b64: 'aGVsbG8=', role: 'content' });
    await api.addBriefSource('b1', 'a.md', 'aGVsbG8=', 'example');
    expect(JSON.parse((fetchMock.mock.calls[1] as unknown as [string, RequestInit])[1].body as string).role).toBe('example');
    fetchMock.mockImplementationOnce(async () => json(brief));
    expect(await api.setSourceRole('b1', 's 1', 'format')).toEqual(brief);
    const [url, init] = fetchMock.mock.calls[2] as unknown as [string, RequestInit];
    expect(url).toBe('/api/docengine/briefs/b1/sources/s%201');
    expect(init.method).toBe('PATCH');
    expect(JSON.parse(init.body as string)).toMatchObject({ role: 'format' });
  });

  it('reads GET /house/related/{code} and passes a 409 at the source limit through', async () => {
    const rel = { code: 'QCSOP001', found: false, version: '', title_en: '', title_mk: '', related: [] };
    const fetchMock = vi.fn(async () => json(rel));
    vi.stubGlobal('window', {}); vi.stubGlobal('fetch', fetchMock);
    expect(await liveApi().houseRelated('QCSOP001')).toEqual(rel);
    expect(fetchMock).toHaveBeenCalledWith('/api/docengine/house/related/QCSOP001', expect.anything());
    vi.stubGlobal('fetch', vi.fn(async () => json({ detail: 'the brief already holds 20 sources' }, 409)));
    await expect(liveApi().addBriefSource('b1', 'x.md', 'aGVsbG8=')).rejects.toMatchObject({ status: 409, message: 'the brief already holds 20 sources' });
  });
});
