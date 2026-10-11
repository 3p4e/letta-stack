import type { Api, WorkflowIn } from './client';
import { normalizeQuestionnaire, type RawQuestionnaire } from './normalize';
import { ApiError, type Job } from './types';

declare global { interface Window { PP_SUITE_CONFIG?: { docengineBase?: string } } }

const KNOWN_JOBS = 'ppsuite.jobs';

async function call<T>(url: string, init?: RequestInit): Promise<T> {
  let r: Response;
  try {
    r = await fetch(url, { credentials: 'same-origin', ...init, headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) } });
  } catch (e) {
    throw new ApiError(0, 'network error: ' + String((e as Error).message || e));
  }
  const text = await r.text();
  let body: unknown = text;
  try { body = text ? JSON.parse(text) : {}; } catch { /* plain text body */ }
  if (!r.ok) {
    const b = body as { error?: string; detail?: unknown };
    const detail = typeof b?.detail === 'string' ? b.detail : (b?.detail as { error?: string })?.error;
    throw new ApiError(r.status, b?.error || detail || r.statusText || 'HTTP ' + r.status, body);
  }
  return body as T;
}
const post = <T,>(url: string, body: unknown) => call<T>(url, { method: 'POST', body: JSON.stringify(body) });

function rememberJob(id: string) {
  try {
    const ids: string[] = JSON.parse(localStorage.getItem(KNOWN_JOBS) || '[]');
    localStorage.setItem(KNOWN_JOBS, JSON.stringify([id, ...ids.filter(x => x !== id)].slice(0, 50)));
  } catch { /* storage blocked: the job is still shown for this session */ }
}
function knownJobs(): string[] {
  try { return JSON.parse(localStorage.getItem(KNOWN_JOBS) || '[]'); } catch { return []; }
}

export function liveApi(): Api {
  // DocEngine is internal-only (no published port); the browser reaches it through a
  // same-origin proxy. Configure with window.PP_SUITE_CONFIG.docengineBase.
  const de = (window.PP_SUITE_CONFIG?.docengineBase || '/api/docengine').replace(/\/$/, '');
  return {
    mode: 'live',
    openSession: async key => { await post('/api/session', { key }); },
    // There is no logout route; the cookie expires after 8 h. Clearing it needs the server.
    closeSession: async () => { throw new ApiError(501, 'no logout route on ppdocwiz; the session cookie expires after 8 h'); },
    health: () => call('/api/health'),
    doctypes: async () => (await call<{ doctypes: never[] }>('/api/doctypes')).doctypes,
    example: () => call('/api/example'),
    preview: async payload => (await post<{ markdown: string }>('/api/wizard/preview', { payload })).markdown,
    build: payload => post('/api/wizard/build', { payload }),
    rawBuild: (markdown, out_name) => post('/api/build', { markdown, out_name }),
    chat: (message, agent) => post('/api/chat', { message, agent }),
    downloadHref: (docId, ext) => `/api/download/${encodeURIComponent(docId)}.${ext}`,

    deHealth: () => call(de + '/health'),
    questionnaires: async () => (await call<{ questionnaires: never[] }>(de + '/questionnaires')).questionnaires,
    questionnaire: async key => normalizeQuestionnaire(key, await call<RawQuestionnaire>(de + '/questionnaires/' + encodeURIComponent(key))),
    startWorkflow: async (body: WorkflowIn) => { const r = await post<{ job_id: string; status: string }>(de + '/workflows', body); rememberJob(r.job_id); return r; },
    job: id => call(de + '/workflows/' + encodeURIComponent(id)),
    jobs: async () => {
      const out: Job[] = [];
      for (const id of knownJobs()) { try { out.push(await call<Job>(de + '/workflows/' + id)); } catch (e) { if ((e as ApiError).status !== 404) throw e; } }
      return out;
    },
    reviewJob: (id, decision, note) => post(de + '/workflows/' + encodeURIComponent(id) + '/review', { decision, note }),
    directBuild: (markdown, out_name, meta) => post(de + '/build', { markdown, out_name, meta }),
    documents: async () => (await call<{ documents: never[] }>(de + '/documents')).documents,
    document: id => call(de + '/documents/' + encodeURIComponent(id)),
    documentHref: (id, kind) => `${de}/documents/${encodeURIComponent(id)}/${kind}`,
    documentAvailable: async id => { try { const r = await fetch(`${de}/documents/${encodeURIComponent(id)}/download`, { method: 'HEAD', credentials: 'same-origin' }); return r.status; } catch { return 0; } },
    buildReport: async () => { throw new ApiError(501, 'no report route yet: pp_report.py is called from Python scripts, not exposed by ppdocwiz or DocEngine'); },
    engineEnv: async () => { throw new ApiError(501, 'no engine-environment endpoint yet: pp_assets.check_environment runs inside pp_verify only'); },
  };
}
