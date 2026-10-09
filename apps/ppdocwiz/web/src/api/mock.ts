// In-browser stand-in for ppdocwiz + DocEngine. Same response shapes as the
// real services (see live.ts), sample data from the Hybrid v2 prototype, and
// switchable faults so every degraded state can be seen without breaking a server.
import type { Api, EngineEnv, WorkflowIn } from './client';
import { applyDefaults, normalizeQuestionnaire } from './normalize';
import { ApiError, type DocumentRow, type Job, type WizardPayload } from './types';
import { RAW_QUESTIONNAIRES } from '../data/questionnaires';
import { ANX_SEC, CH, CH_A, CY, CY_A, FIND, FIND_A, QA_FIX, SAMPLE_ANNEX, SOP_SEC } from '../data/samples';
import { composeMarkdown, lint } from '../lib/compose';
import { verifyReport } from '../lib/verify';

export interface Faults { storage: boolean; letta: boolean; chatDisabled: boolean; gotenberg: boolean; libreoffice: boolean; badKey: boolean }
export const NO_FAULTS: Faults = { storage: false, letta: false, chatDisabled: false, gotenberg: false, libreoffice: false, badKey: false };

const ALLOWLIST = ['qms_docx_formatter', 'gf_annex_author'];
const wait = (ms: number) => new Promise(r => setTimeout(r, ms));
const hex = (n: number) => Array.from({ length: n }, () => Math.floor(Math.random() * 16).toString(16)).join('');
const uuid = () => `${hex(8)}-${hex(4)}-4${hex(3)}-a${hex(3)}-${hex(12)}`;
const iso = (minAgo: number) => new Date(Date.now() - minAgo * 60000).toISOString();

const stagesFor = (doctype: string) => {
  const secs = doctype === 'SOP' ? SOP_SEC : ANX_SEC;
  return [
    'queued', ...secs.map(s => 'generate ' + s[0]), ...secs.map(s => 'regulatory-check ' + s[0]),
    'bilingual-check', 'qa-audit', 'format', 'done',
  ];
};

function telemetry(doctype: string, bilGap?: string) {
  const sop = doctype === 'SOP', secs = sop ? SOP_SEC : ANX_SEC;
  return secs.map((x, i) => {
    let [cyr, lat] = (sop ? CY : CY_A)[i];
    if (bilGap === x[0]) lat = 6;
    return { num: x[0], title: x[1] + ' | ' + x[2], author: !sop ? 'gf_annex_author' : x[0] === '3.0' ? 'gf_raci_specialist' : 'gf_sop_author', chars: (sop ? CH : CH_A)[i], cyr, lat, note: sop && i === 5 ? 'preamble strip removed 41 / 3 249 chars ("Let me align…")' : '' };
  });
}
const findings = (doctype: string) => (doctype === 'SOP' ? FIND : FIND_A).map((f, i) => ({ section: (doctype === 'SOP' ? SOP_SEC : ANX_SEC)[i][0], verdict: f[0], citation: f[1], note: f[2] }));
const sopReport = (code: string, sop: boolean) => verifyReport(code + '-3e9b1a77c0d2.docx', sop ? { paras: 212, tables: 6, words: 4870, chars: 29114, srcWords: 4812 } : { paras: 24, tables: 3, words: 388, chars: 2610, srcWords: 371 });

function mkJob(p: Partial<Job> & { id: string; code: string; mk: string; en: string; q: string; doctype: string; by: string; minAgo: number }): Job {
  return {
    id: p.id, kind: 'workflow', status: p.status || 'queued', stage: p.stage || 'queued',
    payload: { questionnaire: p.q, answers: {}, meta: { code: p.code, title_mk: p.mk, title_en: p.en, version: '01', doctype: p.doctype }, requested_by: p.by },
    result: p.result || {}, error: p.error ?? null, created_by: p.by, created_at: iso(p.minAgo + 9), updated_at: iso(p.minAgo),
  };
}

function seedJobs(): Job[] {
  return [
    mkJob({ id: '7b21d0aa-5f1c-4e0a-9d3e-1c2b3a4d5e6f', code: 'QCSOP_014', mk: 'Тестирање на стабилност', en: 'Stability testing', q: 'sop_qc', doctype: 'SOP', by: 'marija.k', minAgo: 32, status: 'failed', stage: 'bilingual-check', error: 'sections are not bilingual: 5.0 (no EN)', result: { bilingual_gaps: ['5.0 (no EN)'], telemetry: telemetry('SOP', '5.0'), regulatory: findings('SOP') } }),
    mkJob({ id: 'c04e88f3-2b7a-4c1d-8e9f-0a1b2c3d4e5f', code: 'WHSOP_011_A01', mk: 'Дневник на температура', en: 'Temperature log', q: 'annex_form', doctype: 'FORM', by: 'darko.s', minAgo: 53, status: 'failed', stage: 'qa-audit', error: '§6A audit did not pass', result: { qa_audit: { verdict: 'FIX', issues: QA_FIX.slice(2) }, telemetry: telemetry('FORM'), regulatory: findings('FORM') } }),
    mkJob({ id: '19d5e7b0-8c4d-4f2e-b1a0-9e8d7c6b5a49', code: 'QCSOP_022', mk: 'Микробиолошко тестирање', en: 'Microbiological testing', q: 'sop_qc', doctype: 'SOP', by: 'ivana.p', minAgo: 162, status: 'failed', stage: 'regulatory-check 6.0', error: 'abandoned: no progress for 60 minutes (worker killed mid-run)', result: { telemetry: telemetry('SOP'), regulatory: findings('SOP').slice(0, 5) } }),
    mkJob({ id: 'a3f19c22-6d5e-4b7a-8c9d-0e1f2a3b4c5d', code: 'QCSOP_033', mk: 'Контрола на влага во просторија', en: 'Room humidity control', q: 'sop_qc', doctype: 'SOP', by: 'darko.s', minAgo: 18, status: 'awaiting_review', stage: 'format', result: { verify: sopReport('QCSOP_033', true), regulatory: findings('SOP'), qa_audit: { verdict: 'PASS', issues: [] }, telemetry: telemetry('SOP'), markdown: '<!--HEADERDATA\nmk_title: Контрола на влага во просторија\nen_title: Room humidity control\ncode: QCSOP_033\nversion: 01\ndoctype: SOP\n-->\n\n## 1.0 ЦЕЛ | PURPOSE\n…' } }),
    mkJob({ id: 'e8812f4c-1a2b-4c3d-9e4f-5a6b7c8d9e0f', code: 'QCSOP_018', mk: 'Земање мостри', en: 'Sampling', q: 'sop_qc', doctype: 'SOP', by: 'darko.s', minAgo: 1440, status: 'done', stage: 'done', result: { document_id: '5d0c71e2-0000-4000-a000-000000000001', bytes: 212506, verify: sopReport('QCSOP_018', true), regulatory: findings('SOP'), qa_audit: { verdict: 'PASS', issues: [] }, telemetry: telemetry('SOP') } }),
  ];
}

type MockDoc = DocumentRow & { parent?: string; source?: string; supersedes?: string; missing?: boolean };
function seedDocs(): MockDoc[] {
  const rep = (code: string, sop: boolean) => sopReport(code, sop).replace('3e9b1a77c0d2', 'b71c09e2f4a3');
  const D = (id: string, code: string, doctype: string, mk: string, en: string, version: string, bytes: number, minAgo: number, source: string, parent: string, extra: Partial<MockDoc> = {}): MockDoc =>
    ({ id, code, doctype, title_mk: mk, title_en: en, version, bytes, created_at: iso(minAgo), verify: rep(code, doctype === 'SOP'), source, parent, job_id: null, ...extra });
  return [
    D('d0000000-0000-4000-a000-000000000001', 'WHSOP_002_A02', 'ANNEX', 'Записник за ослободување — клонови', 'Release Record — Propagation Material (Clones)', '01', 38412, 120, 'wizard', 'WHSOP 002'),
    D('5d0c71e2-0000-4000-a000-000000000001', 'QCSOP_018', 'SOP', 'Земање мостри', 'Sampling', '1.0', 212506, 1440, 'job e8812f4c', '—', { job_id: 'e8812f4c-1a2b-4c3d-9e4f-5a6b7c8d9e0f' }),
    D('d0000000-0000-4000-a000-000000000003', 'QCSOP_014_A03', 'ANNEX', 'Распоред за стабилност', 'Stability schedule', '01', 41980, 140, 'agent chat', 'QCSOP 014'),
    D('d0000000-0000-4000-a000-000000000004', 'QASOP_031_A10', 'ANNEX', 'Етикети за примарно пакување', 'Primary packaging labels', '03', 96233, 4300, 'build · Mode C', 'QASOP 031', { supersedes: 'QASOP_031_A10 v02' }),
    D('d0000000-0000-4000-a000-000000000005', 'QCSOP_011', 'SOP', 'Калибрација на ваги', 'Balance calibration', '02', 188120, 12000, 'build', '—', { missing: true }),
    D('d0000000-0000-4000-a000-000000000006', 'WHSOP_002', 'SOP', 'Прием на пропагационен материјал', 'Receipt of propagation material', '04', 176004, 38000, 'wizard', '—', { supersedes: 'WHSOP_002 v03' }),
    // older versions — the registry keeps every row under the same code (COVERAGE #5)
    D('d0000000-0000-4000-a000-000000000007', 'QASOP_031_A10', 'ANNEX', 'Етикети за примарно пакување', 'Primary packaging labels', '02', 94870, 30000, 'build · Mode B', 'QASOP 031', { supersedes: 'QASOP_031_A10 v01' }),
    D('d0000000-0000-4000-a000-000000000008', 'QASOP_031_A10', 'ANNEX', 'Етикети за примарно пакување', 'Primary packaging labels', '01', 90112, 90000, 'wizard', 'QASOP 031'),
    D('d0000000-0000-4000-a000-000000000009', 'WHSOP_002', 'SOP', 'Прием на пропагационен материјал', 'Receipt of propagation material', '03', 171540, 120000, 'wizard', '—', { supersedes: 'WHSOP_002 v02' }),
    D('d0000000-0000-4000-a000-00000000000a', 'WHSOP_002', 'SOP', 'Прием на пропагационен материал', 'Receipt of propagation material', '02', 160233, 260000, 'build', '—'),
  ];
}

export interface MockApi extends Api { faults: Faults; setFaults(f: Partial<Faults>): void }

export function mockApi(onChange?: () => void): MockApi {
  const jobs = seedJobs();
  const docs = seedDocs();
  const timers = new Map<string, number>();
  let authed = true;
  const faults: Faults = { ...NO_FAULTS };

  const gate = () => { if (!authed) throw new ApiError(401, 'bad api key'); };
  const store = () => { gate(); if (faults.storage) throw new ApiError(503, 'DocEngine storage unavailable'); };

  function advance(job: Job) {
    const seq = stagesFor(String(job.payload.meta.doctype || 'SOP'));
    const i = seq.indexOf(job.stage);
    const next = seq[Math.min(seq.length - 1, i + 1)];
    job.updated_at = new Date().toISOString();
    if (next === 'done') {
      const sop = job.payload.meta.doctype === 'SOP', id = uuid(), m = job.payload.meta;
      const verify = sopReport(m.code, sop);
      docs.unshift({ id, code: m.code, doctype: sop ? 'SOP' : String(m.doctype || 'FORM'), title_mk: m.title_mk, title_en: m.title_en, version: m.version || '01', bytes: sop ? 204118 : 44902, created_at: new Date().toISOString(), verify, job_id: job.id, source: 'job ' + job.id.slice(0, 8), parent: '—' });
      Object.assign(job, { status: 'done', stage: 'done', result: { ...job.result, document_id: id, bytes: sop ? 204118 : 44902, verify, regulatory: findings(sop ? 'SOP' : 'FORM'), qa_audit: { verdict: 'PASS', issues: [] } } });
      clearInterval(timers.get(job.id)); timers.delete(job.id);
    } else {
      job.status = 'running'; job.stage = next;
    }
    onChange?.();
  }

  function run(job: Job) {
    const t = window.setInterval(() => advance(job), job.stage.startsWith('generate') || job.stage === 'queued' ? 420 : 300);
    timers.set(job.id, t);
  }

  const api: MockApi = {
    mode: 'mock', faults,
    setFaults(f) { Object.assign(faults, f); onChange?.(); },
    async openSession(key) {
      await wait(250);
      if (faults.badKey || key.trim() === '' || key === 'bad') throw new ApiError(401, 'bad key');
      authed = true;
    },
    async closeSession() { authed = false; },
    async health() { await wait(60); return { ok: true, letta: !faults.chatDisabled, pdf: !faults.libreoffice }; },
    async doctypes() { gate(); return [
      { key: 'ANNEX', mk: 'Анекс', en: 'Annex', desc: 'Inline full-page bilingual annex (form / log / checklist / register).', default_orient: 'portrait' },
      { key: 'SOP', mk: 'СОП', en: 'SOP', desc: 'Two-column MK|EN Standard Operating Procedure (9-section).', default_orient: 'portrait' },
      { key: 'FORM', mk: 'Образец', en: 'Form', desc: 'Single-purpose bilingual data-entry form.', default_orient: 'portrait' },
    ]; },
    async example() {
      // wizard.EXAMPLE: the sample annex with every EN half filled.
      gate(); const payload = structuredClone(SAMPLE_ANNEX);
      const t = payload.sections[1].blocks[0]; if (t.type === 'table') t.rows[1][1].en = 'SPL sampling';
      payload.sections = payload.sections.slice(0, 2);
      return { payload, markdown: composeMarkdown(payload) };
    },
    async preview(p) { gate(); await wait(80); return composeMarkdown(p); },
    async build(p: WizardPayload) {
      gate(); await wait(300);
      const md = composeMarkdown(p), lints = lint(p), wide = p.sections.some(s => s.blocks.some(b => b.type === 'table' && b.cols.length >= 9));
      const words = (md.match(/[\p{L}\p{N}]+/gu) || []).length;
      const verify = verifyReport(`/data/${p.code || 'document'}.docx`, { paras: 6 + md.split('\n').length, tables: p.sections.reduce((n, s) => n + s.blocks.filter(b => b.type !== 'text' && b.type !== 'bullets').length, 0), words, chars: md.length, srcWords: words, minFont: wide ? 5.5 : 7, bilingual: !lints.some(l => l.msg.startsWith('EN')) });
      if (lints.some(l => l.level === 'bad')) throw new ApiError(422, 'HEADERDATA ended early', { markdown: md });
      const doc_id = (p.code || 'document').replace(/[^A-Za-z0-9._-]+/g, '_') + '_' + hex(8);
      return { ok: verify.includes('RESULT: PASS'), verify, doc_id, markdown: md, download_docx: `/api/download/${doc_id}.docx`, download_pdf: `/api/download/${doc_id}.pdf` };
    },
    async chat(message, agent) {
      gate(); await wait(500);
      if (faults.chatDisabled) throw new ApiError(503, 'chat disabled: set LETTA_BASE_URL');
      if (!ALLOWLIST.includes(agent)) throw new ApiError(400, `agent '${agent}' is not permitted by this deployment`);
      if (faults.letta) throw new ApiError(502, 'letta 503: upstream unavailable');
      return { ok: true, agent, reply: /^\/verify/.test(message) ? 'Verified: RESULT: PASS · min font 7.0 pt · MK+EN OK.' : 'Done. Rebuilt, the gate passed, and the change is highlighted on the live page.', built: { ok: true, path: '/data/WHSOP_002_A02_' + hex(8) + '.docx' } };
    },
    downloadHref: (id, ext) => `#mock-download/${id}.${ext}`,

    async deHealth() { await wait(60); return { ok: true, db: !faults.storage, letta: !faults.letta, engine: 'pp-document-suite (synced copy, canon revision 2026-10-09)' }; },
    async questionnaires() { gate(); return Object.entries(RAW_QUESTIONNAIRES).map(([key, q]) => ({ key, title: q.title as never, doctype: q.doctype, rounds: q.rounds.length })); },
    async questionnaire(key) { gate(); const q = RAW_QUESTIONNAIRES[key]; if (!q) throw new ApiError(404, 'unknown questionnaire'); return normalizeQuestionnaire(key, q); },
    async startWorkflow(body: WorkflowIn) {
      gate();
      if (!RAW_QUESTIONNAIRES[body.questionnaire]) throw new ApiError(400, 'unknown questionnaire');
      for (const k of ['title_mk', 'title_en', 'code'] as const) if (!body.meta[k]) throw new ApiError(400, `meta.${k} required`);
      if (faults.storage) throw new ApiError(503, 'DocEngine storage unavailable');
      if (faults.letta) throw new ApiError(503, 'Letta unavailable');
      const q = normalizeQuestionnaire(body.questionnaire, RAW_QUESTIONNAIRES[body.questionnaire]);
      const id = uuid();
      const job = mkJob({ id, code: body.meta.code, mk: body.meta.title_mk, en: body.meta.title_en, q: body.questionnaire, doctype: q.doctype, by: body.requested_by, minAgo: 0 });
      job.payload.answers = applyDefaults(q, body.answers);
      job.result = { telemetry: telemetry(q.doctype) };
      jobs.unshift(job); run(job); onChange?.();
      return { job_id: id, status: 'queued' };
    },
    async job(id) { store(); const j = jobs.find(x => x.id === id); if (!j) throw new ApiError(404, 'no such job'); return structuredClone(j); },
    async jobs() { store(); return structuredClone(jobs); },
    async reviewJob(id, decision, note) {
      store(); await wait(300);
      const j = jobs.find(x => x.id === id);
      if (!j || j.status !== 'awaiting_review') throw new ApiError(409, 'job is not awaiting review');
      if (decision === 'approve') { j.stage = 'format'; j.status = 'running'; advance(j); j.result = { ...j.result, review: { decision, note, by: 'darko.s' } }; }
      else Object.assign(j, { status: 'failed', error: 'returned for revision: ' + (note || 'no reason given'), result: { ...j.result, review: { decision, note, by: 'darko.s' } }, updated_at: new Date().toISOString() });
      onChange?.();
      return structuredClone(j);
    },
    async rawBuild(markdown, outName) {
      gate(); await wait(400);
      const words = (markdown.match(/[\p{L}\p{N}]+/gu) || []).length, doc_id = `${(markdown.match(/^code:\s*(.+)$/m)?.[1] || outName).trim()}_${uuid().slice(0, 8)}`;
      const verify = verifyReport(`/data/${doc_id}.docx`, { paras: markdown.split('\n').length, tables: (markdown.match(/\[\[(TABLE|FORM)/g) || []).length, words, chars: markdown.length, srcWords: words, minFont: 7 });
      if (!verify.includes('RESULT: PASS')) throw new ApiError(422, 'verify FAILED', { verify, error: 'verify FAILED' });
      return { ok: true, verify, doc_id, markdown, download_docx: `/api/download/${doc_id}.docx`, download_pdf: `/api/download/${doc_id}.pdf` };
    },
    async directBuild(markdown, outName, meta) {
      store(); await wait(400);
      const words = (markdown.match(/[\p{L}\p{N}]+/gu) || []).length;
      const verify = verifyReport(`/data/${outName}.docx`, { paras: markdown.split('\n').length, tables: (markdown.match(/\[\[(TABLE|FORM)/g) || []).length, words, chars: markdown.length, srcWords: words, minFont: meta.minFont ? Number(meta.minFont) : 7 });
      if (!verify.includes('RESULT: PASS')) throw new ApiError(422, 'verify FAILED', { detail: { verify, error: 'verify FAILED' } });
      const id = uuid();
      docs.unshift({ id, code: meta.code || outName, doctype: meta.doctype || 'ANNEX', title_mk: meta.title_mk || '', title_en: meta.title_en || '', version: meta.version || '1.0', bytes: 30000 + markdown.length * 9, created_at: new Date().toISOString(), verify, job_id: null, source: meta.source || 'build', parent: meta.parent || '—', supersedes: meta.supersedes });
      onChange?.();
      return { ok: true, document_id: id, bytes: 30000 + markdown.length * 9, verify };
    },
    async documents() { store(); await wait(60); return docs.map(({ verify: _v, path: _p, ...d }) => d); },
    async document(id) { store(); const d = docs.find(x => x.id === id); if (!d) throw new ApiError(404, 'no such document'); return { ...d }; },
    documentHref: (id, kind) => `#mock-${kind}/${id}`,
    async documentAvailable(id) {
      if (faults.storage) return 503;
      const d = docs.find(x => x.id === id);
      return !d ? 404 : d.missing ? 410 : 200;
    },
    async buildReport(spec) {
      gate(); await wait(500);
      const eq = (spec.blocks as { t: string }[]).filter(b => b.t === 'calc' || b.t === 'eqn').length * 3, fig = (spec.blocks as { t: string }[]).filter(b => b.t === 'figure').length;
      return { ok: true, verify: verifyReport(`/data/${spec.code}.docx`, { paras: 96, tables: 7, words: 1840, chars: 11902, omath: eq, figures: fig }) };
    },
    async engineEnv(): Promise<EngineEnv> {
      gate(); await wait(120);
      return {
        canon: '2026-07', version: '1.6.2', synced: true, hash: 'a91c3f0e', hashExpected: 'a91c3f0e',
        fonts: [
          { face: 'Calibri', file: 'Carlito-Regular.ttf (metric-compatible)', ok: true, missing: '' },
          { face: 'Carlito', file: 'Carlito-Regular.ttf', ok: true, missing: '' },
          { face: 'Carlito (webfont dir)', file: '/usr/share/fonts/web/Carlito-subset.woff2', ok: false, missing: 'ѓ ќ ѕ џ љ њ' },
        ],
        glyphAudit: [
          { run: '06:44 WHSOP_002_A02', ok: true, note: 'all MK letters render in Carlito' },
          { run: '06:39 WHSOP_009_A01', ok: true, note: 'all MK letters render in Carlito' },
          { run: 'Mon QASOP_031_A10', ok: false, note: '"№" fell back to DejaVu Sans' },
        ],
        manifestDrift: [
          { key: 'pp_theme.NAVY', manifest: '#2B547E', live: '#2B547E' },
          { key: 'pp_verify.min_pt', manifest: '6', live: '6' },
          { key: 'gf_house_rules (chars)', manifest: '1 963', live: '2 011' },
        ],
      };
    },
  };
  return api;
}
