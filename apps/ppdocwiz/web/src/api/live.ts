import type { Api, JobList, ReviseResult, WorkflowIn } from './client';
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
    // Pydantic validation puts a list in `detail`; without this it read "[object Object]" (review 19.10.2026).
    const detail = typeof b?.detail === 'string' ? b.detail
      : Array.isArray(b?.detail) ? (b.detail as { msg: string; loc?: (string | number)[] }[]).map(d => `${d.msg} at ${(d.loc || []).join('.')}`).join('; ')
      : (b?.detail as { error?: string })?.error;
    throw new ApiError(r.status, b?.error || detail || r.statusText || 'HTTP ' + r.status, body);
  }
  return body as T;
}
const post = <T,>(url: string, body: unknown) => call<T>(url, { method: 'POST', body: JSON.stringify(body) });
const send = <T,>(url: string, method: string, body?: unknown) => call<T>(url, { method, body: body === undefined ? undefined : JSON.stringify(body) });

function rememberJob(id: string) {
  try {
    const ids: string[] = JSON.parse(localStorage.getItem(KNOWN_JOBS) || '[]');
    localStorage.setItem(KNOWN_JOBS, JSON.stringify([id, ...ids.filter(x => x !== id)].slice(0, 50)));
  } catch { /* storage blocked: the job is still shown for this session */ }
}
function knownJobs(): string[] {
  try { return JSON.parse(localStorage.getItem(KNOWN_JOBS) || '[]'); } catch { return []; }
}
// The last row read for each job: a poll that fails for one id keeps showing what it last knew (review 19.10.2026).
const lastRows = new Map<string, Job>();

export function liveApi(): Api {
  // DocEngine is internal-only (no published port); the browser reaches it through a
  // same-origin proxy. Configure with window.PP_SUITE_CONFIG.docengineBase.
  const de = (window.PP_SUITE_CONFIG?.docengineBase || '/api/docengine').replace(/\/$/, '');
  return {
    mode: 'live',
    openSession: async (key, username = '') => { await post('/api/session', { key, username }); },
    me: () => call('/api/me'),
    users: async () => (await call<{ users: never[] }>('/api/users')).users,
    addUser: u => post('/api/users', u),
    changeUser: (name, c) => send('/api/users/' + encodeURIComponent(name), 'PATCH', c),
    authLog: async () => (await call<{ events: never[] }>('/api/auth-log')).events,
    passwordState: () => call('/api/password'),
    changePassword: async (current, next) => { await post('/api/password', { current, new: next }); },
    // The server refuses the session from now on, even if the browser kept the cookie (review 14.10.2026).
    closeSession: async () => { await post('/api/session/close', {}); },
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
    // A job opened by id (a brief's build, a package annex) joins the list this browser knows.
    job: async id => { const j = await call<Job>(de + '/workflows/' + encodeURIComponent(id)); rememberJob(j.id); lastRows.set(j.id, j); return j; },
    jobs: async () => {
      const out: JobList = []; let firstErr: ApiError | null = null;
      const seen = new Set<string>(), queue = knownJobs();
      // Per id, with its own catch: one 503 used to empty the whole list. Annex jobs a package started
      // (result.package_jobs) are remembered too, so they appear beside their SOP (review 19.10.2026).
      for (let i = 0; i < queue.length; i++) {
        const id = queue[i]; if (seen.has(id)) continue; seen.add(id);
        try {
          const j = await call<Job>(de + '/workflows/' + encodeURIComponent(id)); lastRows.set(id, j); out.push(j);
          for (const a of (j.result.package_jobs as { job_id?: string }[] | undefined) || []) if (a.job_id && !seen.has(a.job_id)) { rememberJob(a.job_id); queue.push(a.job_id); }
        } catch (e) {
          const a = e as ApiError;
          if (a.status === 404) { lastRows.delete(id); continue; }
          firstErr ||= a; const prev = lastRows.get(id); if (prev) out.push(prev);
        }
      }
      if (firstErr && !out.length) throw firstErr;
      if (firstErr) out.err = `${firstErr.status} · ${firstErr.message}`;
      return out;
    },
    stopJob: id => post<Job>(de + '/workflows/' + encodeURIComponent(id) + '/stop', {}),
    reviseJob: (id, body) => post<ReviseResult>(de + '/workflows/' + encodeURIComponent(id) + '/revise', body),
    rerunJob: async id => { const r = await post<{ job_id: string; status: string }>(de + '/workflows/' + encodeURIComponent(id) + '/rerun', {}); rememberJob(r.job_id); return r; },
    reviewJob: (id, decision, note) => post(de + '/workflows/' + encodeURIComponent(id) + '/review', { decision, note }),
    directBuild: (markdown, out_name, meta) => post(de + '/build', { markdown, out_name, meta }),
    documents: async () => (await call<{ documents: never[] }>(de + '/documents')).documents,
    document: id => call(de + '/documents/' + encodeURIComponent(id)),
    documentHref: (id, kind) => `${de}/documents/${encodeURIComponent(id)}/${kind}`,
    documentAvailable: async id => { try { const r = await fetch(`${de}/documents/${encodeURIComponent(id)}/download`, { method: 'HEAD', credentials: 'same-origin' }); return r.status; } catch { return 0; } },
    buildReport: async () => { throw new ApiError(501, 'no report route yet: pp_report.py is called from Python scripts, not exposed by ppdocwiz or DocEngine'); },
    engineEnv: () => call(de + '/engine/environment'),
    library: () => call(de + '/library'),
    briefs: async () => (await call<{ briefs: never[] }>(de + '/briefs')).briefs,
    brief: id => call(de + '/briefs/' + encodeURIComponent(id)),
    createBrief: b => post(de + '/briefs', b),
    patchBrief: (id, p) => send(de + '/briefs/' + encodeURIComponent(id), 'PATCH', p),
    briefEvents: async id => (await call<{ events: never[] }>(de + '/briefs/' + encodeURIComponent(id) + '/events')).events,
    addBriefSource: (id, name, content_b64, role = 'content') => post(de + '/briefs/' + encodeURIComponent(id) + '/sources', { name, content_b64, actor: 'ppdocwiz-session', role }),
    setSourceRole: (id, sid, role) => send(de + '/briefs/' + encodeURIComponent(id) + '/sources/' + encodeURIComponent(sid), 'PATCH', { role, actor: 'ppdocwiz-session' }),
    houseRelated: code => call(de + '/house/related/' + encodeURIComponent(code)),
    removeBriefSource: (id, sid) => send(de + '/briefs/' + encodeURIComponent(id) + '/sources/' + encodeURIComponent(sid), 'DELETE'),
    suggestBrief: (id, rev, keys = []) => post(de + '/briefs/' + encodeURIComponent(id) + '/suggest', { rev, keys }),
    briefPackage: id => call(de + '/briefs/' + encodeURIComponent(id) + '/package'),
    packagePdfHref: id => `${de}/briefs/${encodeURIComponent(id)}/package.pdf`,
    buildBrief: async (id, rev) => { const r = await post<{ job_id: string; status: string; code: string; assumed: string[] }>(de + '/briefs/' + encodeURIComponent(id) + '/build', { rev }); rememberJob(r.job_id); return r; },
    reference: id => call(de + '/reference/' + encodeURIComponent(id)),
    nextCode: async q => (await call<{ code: string }>(de + '/register/next?' + new URLSearchParams(q.parent ? { parent: q.parent } : { family: q.family || '' }))).code,
  };
}
