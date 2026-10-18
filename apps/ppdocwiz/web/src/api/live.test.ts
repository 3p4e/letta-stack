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
