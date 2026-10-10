// Jobs (handoff §4) mirrors apps/wwf-docengine/app/pipeline.py; review gate = COVERAGE #3.
import { useEffect, useState } from 'react';
import { ApiError, type Job } from '../api/types';
import { PPPage } from '../components/PPPage';
import { Banner, Btn, Kv } from '../components/ui';
import { ANX_SEC, SAMPLE_ANNEX, SAMPLE_SOP, SOP_SEC } from '../data/samples';
import { readQa } from '../lib/qa';
import { usePrimary } from '../lib/usePrimary';
import { lineColor } from '../lib/verify';
import { useApp } from '../store/store';
import { C, DISPLAY, G, MONO, T, TINT, type Status } from '../theme';

type Tel = { num: string; title: string; author: string; chars: number; cyr: number; lat: number; note: string };
type Finding = { section: string; verdict: string; citation: string; note: string };

const stC = (st: string) => st === 'done' ? C.ok : st === 'failed' ? C.bad : st === 'running' ? C.run : st === 'awaiting_review' ? C.warn : T.secondary;
const ago = (iso: string) => { const m = Math.round((Date.now() - Date.parse(iso)) / 60000); return m < 1 ? 'just now' : m < 60 ? m + ' min' : m < 1440 ? Math.round(m / 60) + ' h' : Math.round(m / 1440) + ' d'; };
const secsOf = (j: Job) => (j.payload.meta.doctype || (j.payload.questionnaire === 'sop_qc' ? 'SOP' : 'FORM')) === 'SOP' ? SOP_SEC : ANX_SEC;

/** Position in the stage sequence (queued=0 … registry=2n+4), from the job row's `stage`. */
function posOf(j: Job) {
  const secs = secsOf(j), n = secs.length;
  if (j.status === 'done') return 2 * n + 4;
  const [name, num] = j.stage.split(' ');
  const si = num ? Math.max(0, secs.findIndex(s => s[0] === num)) : 0;
  return name === 'generate' ? 1 + si : name === 'regulatory-check' ? n + 1 + si : name === 'bilingual-check' ? 2 * n + 1 : name === 'qa-audit' ? 2 * n + 2 : name === 'format' ? 2 * n + 3 : name === 'done' ? 2 * n + 4 : 0;
}

export function Jobs() {
  const { api, jobSel, set, go, dataRev, run, flash } = useApp();
  const [jobs, setJobs] = useState<Job[] | null>(null);
  const [err, setErr] = useState('');
  const [ins, setIns] = useState<string | null>(null);
  const [note, setNote] = useState('');
  const [reviewErr, setReviewErr] = useState('');
  const anyRunning = jobs?.some(j => j.status === 'running' || j.status === 'queued');
  useEffect(() => {
    let live = true;
    // One round at a time: the next poll starts 1 s after the previous one finished, so slow
    // rounds never overlap and an older list can never overwrite a newer one.
    let t: number | undefined;
    const load = () => api.jobs().then(j => { if (live) { setJobs(j); setErr(''); } }).catch((e: ApiError) => live && setErr(`${e.status} · ${e.message}`))
      .finally(() => { if (live && anyRunning) t = window.setTimeout(load, 1000); });
    load();
    return () => { live = false; if (t) clearTimeout(t); };
  }, [api, dataRev, anyRunning]);
  const job = jobs?.find(j => j.id === jobSel) || jobs?.[0];
  const rerun = async () => {
    if (!job) return;
    try { const r = await api.startWorkflow({ questionnaire: job.payload.questionnaire, answers: job.payload.answers, meta: job.payload.meta as never, requested_by: job.payload.requested_by }); set({ jobSel: r.job_id }); setIns(null); }
    catch (e) { flash(`${(e as ApiError).status} · ${(e as Error).message}`); }
  };
  usePrimary(job?.status === 'failed' ? 'Re-run ▸' : 'Build ▸', () => job?.status === 'failed' ? rerun() : run(job?.payload.meta.code || 'WHSOP_002_A02', async () => ({ ok: true })));

  if (err && !jobs) return <div style={{ flex: 1, padding: 22 }}><Banner kind="err">GET /workflows → {err}. {err.startsWith('503') ? 'DocEngine storage (Postgres) is down; job state lives there, so nothing can be listed or polled until it is back.' : err.startsWith('404') || err.startsWith('0') ? 'DocEngine is not reachable from this page. Configure a same-origin proxy and set window.PP_SUITE_CONFIG.docengineBase.' : ''}</Banner></div>;
  if (!jobs || !job) return <div style={{ flex: 1, padding: 22, color: T.muted }}>{jobs ? 'No jobs started from this browser yet. Start one from Questionnaire.' : 'loading…'}</div>;

  const secs = secsOf(job), n = secs.length, sop = n === 9, pos = posOf(job);
  const RG: Record<string, [number, number]> = { queued: [0, 0], generate: [1, n], reg: [n + 1, 2 * n], bil: [2 * n + 1, 2 * n + 1], qa: [2 * n + 2, 2 * n + 2], format: [2 * n + 3, 2 * n + 3], review: [2 * n + 3, 2 * n + 3], done: [2 * n + 4, 2 * n + 4] };
  const failed = job.status === 'failed', review = job.status === 'awaiting_review';
  const stAt = (p: number): Status => job.status === 'done' ? 'ok' : pos > p ? 'ok' : pos === p ? (failed ? 'bad' : review ? 'ok' : 'run') : 'idle';
  const stOf = (k: string): Status => { const [a, b] = RG[k]; if (k === 'review') return review ? 'warn' : job.status === 'done' && job.result.review ? 'ok' : 'idle'; return job.status === 'done' ? 'ok' : pos > b ? 'ok' : pos >= a ? (failed ? 'bad' : review ? 'ok' : 'run') : 'idle'; };
  const GROUPS: [string, string, string][] = [['queued', 'queued', 'POST /workflows · job row created in Postgres'], ['generate', 'generate', sop ? 'gf_sop_author · section 3.0 by gf_raci_specialist' : 'gf_annex_author · one structured body'], ['reg', 'regulatory-check', 'gf_reg_checker_tmp_* · one ephemeral clone per section, deleted after'], ['bil', 'bilingual-check', 'per section: Cyrillic and Latin both present'], ['qa', 'qa-audit', 'gf_qa_auditor · §6A verdict PASS | FIX'], ['format', 'format', 'build_from_md → pp_verify → fidelity §5A · hard gate'],
    ...(review || job.result.review ? [['review', 'awaiting_review', 'human review · approve to register, or return for revision']] as [string, string, string][] : []), ['done', 'registry', 'docengine.documents · atomic publish (.partial → final)']];
  const auto = job.status === 'done' ? 'format' : review ? 'review' : (GROUPS.find(([k]) => k !== 'review' && pos >= RG[k][0] && pos <= RG[k][1]) || ['queued'])[0];
  const cur = ins || auto, reached = stOf(cur) !== 'idle';
  const stageLabel = job.status === 'done' ? 'done' : job.stage || 'queued';
  const tel = (job.result.telemetry as Tel[] | undefined) || [];
  const regs = (job.result.regulatory as Finding[] | undefined) || [];
  const qa = readQa(job.result.qa_audit, job.result.qa_verdict, failed && !!job.error?.includes('§6A'));
  const verify = job.result.verify as string | undefined;
  const INS: Record<string, [string, string]> = { queued: ['Queued', 'POST /workflows'], generate: ['Section drafts', '_clean_section() · preamble strip'], reg: ['Regulatory findings', 'cite only retrieved passages'], bil: ['Bilingual check, per section', '_bilingual_gaps()'], qa: ['§6A audit verdict', 'gf_qa_auditor'], format: ['Verify gate report', 'builder.build()'], review: ['Review before registry', 'status awaiting_review'], done: ['Registry row', 'docengine.documents'] };
  const notRecorded = <div style={{ color: T.muted, fontSize: 13 }}>Not recorded in the job row. DocEngine stores <span style={{ fontFamily: MONO }}>result.regulatory</span>, <span style={{ fontFamily: MONO }}>qa_audit</span> and <span style={{ fontFamily: MONO }}>verify</span>; per-section drafts and letter counts are not persisted.</div>;
  const decide = async (d: 'approve' | 'return') => {
    setReviewErr('');
    try { await api.reviewJob(job.id, d, note); setNote(''); flash(d === 'approve' ? `${job.payload.meta.code} approved · registering` : `${job.payload.meta.code} returned for revision`); setJobs(await api.jobs()); }
    catch (e) { setReviewErr(`${(e as ApiError).status} · ${(e as Error).message}`); }
  };
  const failHint = job.error?.includes('not bilingual') ? 'gf_sop_author drafted a section in one language only. A re-run regenerates the whole SOP; revisions are never patched.'
    : job.error?.includes('§6A') ? 'gf_qa_auditor returned FIX. Nothing was formatted or registered. Re-run, or open the Markdown in Builder and fix the issues.'
    : job.error?.includes('abandoned') ? 'The worker was killed mid-run (redeploy). The startup sweep marked the job failed instead of leaving it running forever.'
    : job.error?.startsWith('returned') ? 'A reviewer sent this back. Re-run with the same answers after addressing the note, or open it in Builder.' : 'Re-run creates a new job with the same payload.';

  return <>
    <div style={{ width: 260, flex: 'none', borderRight: `1px solid ${T.hair}`, background: T.pane, padding: '14px 10px', display: 'flex', flexDirection: 'column', gap: 6, overflow: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', padding: '0 4px 6px' }}><b style={{ color: '#fff' }}>Jobs</b><span style={{ fontFamily: MONO, fontSize: 11, color: T.faint }}>docengine.jobs</span></div>
      {jobs.map(j => { const act = j.id === job.id, c = stC(j.status), jp = posOf(j), js = secsOf(j), jn = js.length;
        const stg = j.status === 'done' ? 'done' : jp <= jn && jp > 0 ? 'generate ' + js[jp - 1][0] : jp > jn && jp <= 2 * jn ? 'reg-check ' + js[jp - jn - 1][0] : j.stage;
        return <div key={j.id} onClick={() => { set({ jobSel: j.id }); setIns(null); }} style={{ padding: '9px 10px', borderRadius: 6, cursor: 'pointer', background: act ? T.selected : T.surface, border: `1px solid ${act ? T.focus : T.control}`, display: 'flex', flexDirection: 'column', gap: 3 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}><b style={{ color: '#fff', fontFamily: MONO, fontSize: 12.5 }}>{j.payload.meta.code}</b><span style={{ fontFamily: MONO, fontSize: 10.5, padding: '1px 6px', borderRadius: 3, color: c, border: `1px solid ${c}` }}>{j.status}</span></div>
          <div style={{ fontSize: 12, color: T.secondary, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{j.payload.meta.title_mk} | {j.payload.meta.title_en}</div>
          <div style={{ fontFamily: MONO, fontSize: 11, color: T.muted, display: 'flex', justifyContent: 'space-between' }}><span>{j.id.slice(0, 8)} · {stg}</span><span>{ago(j.updated_at)}</span></div></div>; })}
      <div style={{ marginTop: 'auto', fontSize: 11.5, color: T.faint, lineHeight: 1.5, padding: '6px 4px' }}>State lives in Postgres, so any worker can answer a poll. Jobs idle &gt; 60 min are reaped at startup.{api.mode === 'live' ? ' DocEngine has no list route: this list holds the jobs started from this browser.' : ''}</div>
    </div>
    <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
      <div style={{ padding: '16px 20px 12px', borderBottom: `1px solid ${T.hair}`, display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'baseline', flexWrap: 'wrap' }}><span style={{ fontFamily: DISPLAY, fontWeight: 700, fontSize: 17, color: '#fff' }}>{job.payload.meta.code}</span><span style={{ color: T.secondary }}>{job.payload.meta.title_mk} | {job.payload.meta.title_en}</span>
          <span style={{ marginLeft: 'auto', fontFamily: MONO, fontSize: 11.5, padding: '2px 8px', borderRadius: 3, color: stC(job.status), border: `1px solid ${stC(job.status)}` }}>{job.status}</span></div>
        <div style={{ fontFamily: MONO, fontSize: 11.5, color: T.muted }}>job {job.id.slice(0, 8)}… · {job.kind} · {job.payload.questionnaire} · requested by {job.payload.requested_by || job.created_by}</div>
        {failed && <div style={{ background: T.errSurface, border: `1px solid ${T.errBorder}`, borderRadius: 6, padding: '8px 12px', color: T.errText, fontFamily: MONO, fontSize: 12 }}>error: {job.error}</div>}
      </div>
      <div style={{ padding: '12px 20px', display: 'flex', flexDirection: 'column', gap: 2 }}>
        {GROUPS.map(([k, label, who]) => { const st = stOf(k), subs = k === 'generate' || k === 'reg';
          return <div key={k} onClick={() => setIns(k)} className="pp-hover-pane" style={{ display: 'grid', gridTemplateColumns: '20px 150px minmax(0,1fr)', gap: 10, padding: '8px 10px', borderRadius: 6, cursor: 'pointer', alignItems: 'start', background: cur === k ? T.surface : 'transparent', border: `1px solid ${cur === k ? T.control : 'transparent'}` }}>
            <span style={{ fontFamily: MONO, color: C[st], fontWeight: 700 }}>{G[st]}</span><span style={{ fontFamily: MONO, fontSize: 12.5, color: '#fff' }}>{label}</span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, minWidth: 0 }}><span style={{ fontSize: 12.5, color: T.secondary }}>{who}</span>
              {subs && <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>{secs.map((x, i) => { const ss = stAt(RG[k][0] + i); return <span key={i} style={{ fontFamily: MONO, fontSize: 10.5, padding: '2px 6px', borderRadius: 3, color: C[ss], border: `1px solid ${ss === 'idle' ? T.control : C[ss]}`, background: TINT[ss] }}>{x[0]}</span>; })}</div>}</div></div>; })}
      </div>
      <div style={{ margin: '0 20px 20px', background: T.deeper, border: `1px solid ${T.hair}`, borderRadius: 8, padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}><b style={{ color: '#fff' }}>{INS[cur][0]}</b><span style={{ fontFamily: MONO, fontSize: 11, color: T.faint }}>{INS[cur][1]}</span></div>
        {(!reached || cur === 'queued' || cur === 'done') && cur !== 'review' && <div style={{ color: T.muted, fontSize: 13 }}>{cur === 'done' && job.status === 'done' ? `document ${String(job.result.document_id).slice(0, 8)}… · ${job.result.bytes} bytes` : 'Not reached yet.'}</div>}
        {reached && cur === 'generate' && (tel.length ? <div style={{ display: 'flex', flexDirection: 'column', fontSize: 12.5 }}>{tel.map((r, i) => { const hit = stAt(1 + i) !== 'idle';
          return <div key={i} style={{ display: 'grid', gridTemplateColumns: '38px minmax(0,1fr) 150px 60px', gap: 10, padding: '5px 0', borderTop: `1px solid ${T.surface}` }}><span style={{ fontFamily: MONO, color: C.run }}>{r.num}</span><span><span style={{ color: '#fff' }}>{r.title}</span>{hit && r.note && <span style={{ display: 'block', fontSize: 11.5, color: C.warn }}>{r.note}</span>}</span><span style={{ fontFamily: MONO, fontSize: 11.5, color: T.secondary }}>{r.author}</span><span style={{ fontFamily: MONO, fontSize: 11.5, color: T.muted, textAlign: 'right' }}>{hit ? r.chars + ' ch' : '—'}</span></div>; })}</div> : notRecorded)}
        {reached && cur === 'reg' && <div style={{ display: 'flex', flexDirection: 'column', fontSize: 12.5 }}>{secs.map((x, i) => { const ss = stAt(n + 1 + i), f = regs.find(r => r.section === x[0]);
          const [v, cite, nt, c] = ss === 'idle' ? ['—', '', '', T.faint] : ss === 'run' ? ['checking…', `gf_reg_checker_tmp_${job.id.slice(0, 8)}_${x[0].replace('.', '')}`, '', C.run] : ss === 'bad' ? ['NO REPLY', 'worker killed during this exchange', 'orphan clone swept by the next fleet audit', C.bad] : f ? [f.verdict, f.citation, f.note, f.verdict === 'OK' ? C.ok : f.verdict === 'GAP' ? C.warn : f.verdict === 'CONFLICT' ? C.bad : T.secondary] : ['—', 'not in result.regulatory', '', T.faint];
          return <div key={i} style={{ display: 'grid', gridTemplateColumns: '38px 96px minmax(0,1fr)', gap: 10, padding: '5px 0', borderTop: `1px solid ${T.surface}` }}><span style={{ fontFamily: MONO, color: C.run }}>{x[0]}</span><span style={{ fontFamily: MONO, fontSize: 11.5, fontWeight: 700, color: c }}>{v}</span><span><span style={{ color: T.text }}>{cite}</span>{nt && <span style={{ display: 'block', fontSize: 11.5, color: T.secondary }}>{nt}</span>}</span></div>; })}</div>}
        {reached && cur === 'bil' && (tel.length ? <div style={{ display: 'flex', flexDirection: 'column', fontSize: 12.5 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '38px 80px 80px minmax(0,1fr)', gap: 10, fontFamily: MONO, fontSize: 10.5, color: T.faint, paddingBottom: 4 }}><span>SEC</span><span>CYRILLIC</span><span>LATIN</span><span>VERDICT</span></div>
          {tel.map((r, i) => { const v = r.cyr + r.lat < 120 ? 'skipped (< 120 letters)' : r.cyr < 15 ? 'no MK' : r.lat < 15 ? 'no EN' : 'OK';
            return <div key={i} style={{ display: 'grid', gridTemplateColumns: '38px 80px 80px minmax(0,1fr)', gap: 10, padding: '4px 0', borderTop: `1px solid ${T.surface}`, fontFamily: MONO, fontSize: 12 }}><span style={{ color: C.run }}>{r.num}</span><span>{r.cyr}</span><span>{r.lat}</span><span style={{ color: v === 'OK' ? C.ok : v.startsWith('skipped') ? T.muted : C.bad }}>{v}</span></div>; })}
          <div style={{ fontSize: 11.5, color: T.muted, marginTop: 6 }}>Sections under 120 letters are skipped. A language counts as present at 15+ letters. Checked per section, before assembly, because the document-wide check passes on one stray word.</div></div>
          : (job.result.bilingual_gaps ? <div style={{ fontFamily: MONO, fontSize: 12, color: T.errText }}>bilingual_gaps: {(job.result.bilingual_gaps as string[]).join(', ')}</div> : notRecorded))}
        {reached && cur === 'qa' && stOf('qa') !== 'run' && <div style={{ fontFamily: MONO, fontSize: 12, lineHeight: 1.7 }}>
          {qa ? <>
            <div style={{ color: qa.verdict === 'PASS' ? T.okText : T.errText, fontWeight: 600 }}>{qa.verdict ? `verdict ${qa.verdict}` : 'verdict not stated — treated as FIX'}{job.result.qa_rounds ? ` · after ${job.result.qa_rounds} repair round(s)` : ''}</div>
            <div style={{ whiteSpace: 'pre-wrap', color: T.secondary, maxHeight: 420, overflow: 'auto', marginTop: 6 }}>{qa.text}</div>
          </> : <div style={{ color: T.muted }}>(no verdict stored)</div>}</div>}
        {reached && (cur === 'format' || cur === 'review') && (verify ? <div style={{ fontFamily: MONO, fontSize: 12, lineHeight: 1.7 }}>{verify.split('\n').map((l, i) => <div key={i} style={{ whiteSpace: 'pre', color: lineColor(l) }}>{l}</div>)}</div> : <div style={{ color: T.muted, fontSize: 13 }}>Not reached yet.</div>)}
      </div>
    </div>
    <div style={{ width: 320, flex: 'none', borderLeft: `1px solid ${T.hair}`, background: T.pane, padding: 16, display: 'flex', flexDirection: 'column', gap: 10, fontSize: 12.5, overflow: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}><b style={{ color: '#fff', fontSize: 14 }}>Job row</b><span style={{ fontFamily: MONO, fontSize: 11, color: T.faint }}>GET /workflows/{'{id}'}</span></div>
      <Kv rows={[['job_id', job.id.slice(0, 8) + '…'], ['kind', job.kind], ['questionnaire', job.payload.questionnaire], ['status', job.status, stC(job.status)], ['stage', stageLabel], ['requested_by', job.payload.requested_by], ['updated_at', ago(job.updated_at)],
        ...(job.error ? [['error', job.error, C.bad]] as [string, string, string][] : []),
        ...(job.status === 'done' ? [['result.document_id', String(job.result.document_id).slice(0, 8) + '…', C.ok], ['result.bytes', String(job.result.bytes)], ['result.verify', (verify || '').match(/RESULT\s*:?\s*(PASS|FAIL)/)?.[0] || '(not stored)', /FAIL/.test(verify || '') ? C.bad : C.ok]] as [string, string, string?][] : [])]} />
      {job.status === 'done' && <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}><div style={{ flex: 'none' }}><PPPage doc={{ ...(sop ? SAMPLE_SOP : SAMPLE_ANNEX), code: job.payload.meta.code, mk_title: job.payload.meta.title_mk, en_title: job.payload.meta.title_en }} zoom={.14} /></div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, color: T.secondary, lineHeight: 1.4 }}>Registered in docengine.documents. The verify report is stored with the row.<span onClick={() => go('library', { libSel: String(job.result.document_id) })} style={{ color: C.run, cursor: 'pointer' }}>Open in Library →</span></div></div>}
      {(job.status === 'running' || job.status === 'queued') && <div style={{ color: C.run, fontFamily: MONO, fontSize: 12 }}>● polling every 1 s · stage {stageLabel}</div>}
      {review && <div style={{ display: 'flex', flexDirection: 'column', gap: 8, background: T.surface, border: `1px solid ${C.warn}`, borderRadius: 8, padding: 12 }}>
        <b style={{ color: C.warn, fontFamily: MONO, fontSize: 12 }}>awaiting_review</b>
        <div style={{ color: T.secondary, lineHeight: 1.45 }}>The gate passed. A person checks the Markdown and verify report before the row reaches the registry.</div>
        <textarea value={note} onChange={e => setNote(e.target.value)} placeholder="Reviewer note (required to return)" style={{ height: 70, background: T.deeper, border: `1px solid ${T.control}`, borderRadius: 6, padding: 8, color: '#fff', resize: 'none', outline: 'none', fontSize: 12.5 }} />
        <div style={{ display: 'flex', gap: 8 }}><Btn onClick={() => decide('approve')} style={{ flex: 1 }}>Approve & register</Btn><Btn primary={false} disabled={!note.trim()} onClick={() => decide('return')} style={{ flex: 1 }}>Return for revision</Btn></div>
        <span onClick={() => { const md = String(job.result.markdown || ''); set({ builderMode: 'src' }); go('builder'); flash(md ? 'Markdown is in result.markdown; open it in Builder raw mode to edit' : 'no Markdown stored on this job'); }} style={{ color: C.run, cursor: 'pointer', textAlign: 'center' }}>Open Markdown in Builder →</span>
        {reviewErr && <Banner kind="err">{reviewErr}</Banner>}
      </div>}
      {failed && <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}><div style={{ color: T.secondary, lineHeight: 1.45 }}>{failHint}</div><Btn onClick={rerun} style={{ padding: 9 }}>Re-run with same answers</Btn></div>}
    </div>
  </>;
}
