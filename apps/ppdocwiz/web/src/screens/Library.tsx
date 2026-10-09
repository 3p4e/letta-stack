// Library = PASS-only registry (handoff §7) + version history per code (COVERAGE #5).
import { useEffect, useMemo, useState } from 'react';
import { ApiError, type DocumentRow } from '../api/types';
import { PPPage } from '../components/PPPage';
import { Banner, Caps, Seg } from '../components/ui';
import { SAMPLE_ANNEX, SAMPLE_SOP } from '../data/samples';
import { diffLines } from '../lib/diff';
import { usePrimary } from '../lib/usePrimary';
import { lineColor, nbsp } from '../lib/verify';
import { useApp } from '../store/store';
import { C, MONO, T } from '../theme';

type Row = DocumentRow & { parent?: string; source?: string; supersedes?: string };
const when = (iso: string) => { const d = new Date(iso), m = (Date.now() - +d) / 60000; return m < 2 ? 'just now' : m < 1440 && d.getDate() === new Date().getDate() ? 'today ' + d.toTimeString().slice(0, 5) : m < 2880 ? 'yesterday' : d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }); };
const vnum = (v: string) => parseFloat(v.replace(',', '.')) || 0;
const src = (r: Row) => r.source || (r.job_id ? 'job ' + r.job_id.slice(0, 8) : 'build');

export function Library() {
  const { api, libSel, set, go, dataRev, run } = useApp();
  const [rows, setRows] = useState<Row[] | null>(null);
  const [err, setErr] = useState('');
  const [q, setQ] = useState('');
  const [allVersions, setAllVersions] = useState(false);
  const [tab, setTab] = useState<'detail' | 'versions'>('detail');
  const [detail, setDetail] = useState<Row | null>(null);
  const [avail, setAvail] = useState(200);
  const [pdfErr, setPdfErr] = useState('');
  const [cmp, setCmp] = useState<[string, string] | null>(null);
  const [cmpDocs, setCmpDocs] = useState<[Row, Row] | null>(null);
  useEffect(() => { api.documents().then(r => { setRows(r); setErr(''); }).catch((e: ApiError) => setErr(`${e.status} · ${e.message}`)); }, [api, dataRev]);

  const byCode = useMemo(() => { const m: Record<string, Row[]> = {}; (rows || []).forEach(r => (m[r.code] ||= []).push(r)); Object.values(m).forEach(v => v.sort((a, b) => vnum(b.version) - vnum(a.version) || Date.parse(b.created_at) - Date.parse(a.created_at))); return m; }, [rows]);
  const list = (rows || []).filter(r => allVersions || byCode[r.code][0].id === r.id)
    .filter(r => !q || (r.code + ' ' + r.title_mk + ' ' + r.title_en + ' ' + r.doctype).toLowerCase().includes(q.toLowerCase()));
  const sel = list.find(r => r.id === libSel) || list[0];
  useEffect(() => {
    if (!sel) return; setDetail(null); setAvail(200); setCmp(null);
    api.document(sel.id).then(setDetail).catch(() => setDetail(sel));
    api.documentAvailable(sel.id).then(setAvail);
  }, [api, sel?.id]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (!cmp) { setCmpDocs(null); return; } Promise.all(cmp.map(id => api.document(id))).then(d => setCmpDocs(d as [Row, Row])).catch(() => setCmpDocs(null)); }, [api, cmp]);
  usePrimary('Build ▸', () => run(sel?.code || 'WHSOP_002_A02', async () => ({ ok: true })));

  if (err) return <div style={{ flex: 1, padding: 22 }}><Banner kind="err">GET /documents → {err}. {err.startsWith('503') ? 'The registry lives in Postgres (docengine.documents); it is unavailable, so nothing can be listed or downloaded.' : 'DocEngine is not reachable from this page.'}</Banner></div>;
  if (!rows) return <div style={{ flex: 1, padding: 22, color: T.muted }}>loading…</div>;
  const r = detail || sel;
  const missing = avail === 410, versions = r ? byCode[r.code] || [] : [];
  const report = (r?.verify || '').split('\n').filter(Boolean);
  const cols = '140px minmax(0,1fr) 70px 56px 76px 110px';
  return <>
    <div style={{ flex: 1, minWidth: 0, padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 12, overflow: 'auto' }}>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="doctype:any · ⌕ code, title МК or EN" style={{ flex: 1, background: T.surface, border: `1px solid ${T.control}`, borderRadius: 6, padding: '8px 12px', fontFamily: MONO, fontSize: 12, color: '#fff', outline: 'none' }} />
        <Seg items={[['latest', 'latest'], ['all', 'all versions']]} value={allVersions ? 'all' : 'latest'} onPick={k => setAllVersions(k === 'all')} size={12} pad="4px 10px" />
        <span style={{ fontSize: 12, color: T.muted, whiteSpace: 'nowrap' }}>{list.length} documents · every row passed the gate</span>
      </div>
      <div style={{ border: `1px solid ${T.hair}`, borderRadius: 8, overflow: 'hidden' }}>
        <div style={{ display: 'grid', gridTemplateColumns: cols, gap: 10, padding: '9px 14px', background: T.pane, fontSize: 11, color: T.muted, fontFamily: MONO, letterSpacing: '.04em' }}><span>CODE</span><span>TITLE МК ||| EN</span><span>DOCTYPE</span><span>VER</span><span>BYTES</span><span>SOURCE</span></div>
        {list.map(x => { const nv = byCode[x.code].length, gone = (x as { missing?: boolean }).missing;
          return <div key={x.id} onClick={() => set({ libSel: x.id })} className="pp-hover-row" style={{ display: 'grid', gridTemplateColumns: cols, gap: 10, padding: '11px 14px', borderTop: `1px solid ${T.hair}`, alignItems: 'center', cursor: 'pointer', background: x.id === sel?.id ? T.selected : 'transparent' }}>
            <b style={{ color: '#fff', fontFamily: MONO, fontSize: 12.5 }}>{x.code}</b>
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{x.title_mk} <span style={{ color: C.warn, fontFamily: MONO, fontSize: 11 }}>|||</span> <span style={{ color: T.secondary }}>{x.title_en}</span></span>
            <span style={{ color: T.secondary, fontFamily: MONO, fontSize: 11.5 }}>{x.doctype}</span>
            <span>{x.version}{!allVersions && nv > 1 && <span style={{ fontSize: 10.5, color: T.muted }}> · {nv}</span>}</span>
            <span style={{ fontFamily: MONO, fontSize: 11.5, color: gone ? C.bad : T.secondary }}>{gone ? '410 gone' : nbsp(x.bytes)}</span>
            <span style={{ fontSize: 12, color: T.secondary, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{src(x)}</span></div>; })}
      </div>
      <div style={{ fontSize: 12, color: T.faint }}>A FAIL build is written as .partial, deleted, and never registered. It shows up in Verify or Jobs, never here.</div>
    </div>
    {r && <div style={{ width: 380, flex: 'none', borderLeft: `1px solid ${T.hair}`, background: T.pane, padding: 16, display: 'flex', flexDirection: 'column', gap: 12, fontSize: 13, overflow: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}><div style={{ flex: 1 }}><div style={{ fontFamily: MONO, fontSize: 13, fontWeight: 700, color: '#fff' }}>{r.code} · v{r.version}</div><div style={{ color: T.secondary }}>{r.title_mk} | {r.title_en}</div></div>
        <Seg items={[['detail', 'detail'], ['versions', `versions · ${versions.length}`]]} value={tab} onPick={setTab} size={11.5} pad="3px 8px" /></div>
      {tab === 'detail' ? <>
        <div style={{ display: 'flex', gap: 14 }}><PPPage doc={{ ...(r.doctype === 'SOP' ? SAMPLE_SOP : SAMPLE_ANNEX), code: r.code, mk_title: r.title_mk, en_title: r.title_en, version: r.version, parent: r.parent || '', status: 'approved' }} zoom={.16} />
          <div style={{ display: 'grid', gridTemplateColumns: '62px 1fr', gap: '6px 8px', fontSize: 12, alignContent: 'start' }}>
            <span style={{ color: T.muted }}>doctype</span><span>{r.doctype}</span><span style={{ color: T.muted }}>parent</span><span>{r.parent || '—'}</span><span style={{ color: T.muted }}>bytes</span><span>{nbsp(r.bytes)}</span>
            <span style={{ color: T.muted }}>created</span><span>{when(r.created_at)}</span><span style={{ color: T.muted }}>source</span><span>{src(r)}</span>{r.supersedes && <><span style={{ color: T.muted }}>supers.</span><span>{r.supersedes}</span></>}</div></div>
        <Caps>STORED VERIFY REPORT</Caps>
        <div style={{ background: T.deeper, border: `1px solid ${T.hair}`, borderRadius: 6, padding: '9px 10px', fontFamily: MONO, fontSize: 10.5, lineHeight: 1.6 }}>{report.length ? report.map((l, i) => <div key={i} style={{ whiteSpace: 'pre', overflow: 'hidden', textOverflow: 'ellipsis', color: lineColor(l) }}>{l}</div>) : <span style={{ color: T.muted }}>loading…</span>}</div>
        {missing && <Banner kind="err">410 · document artifact missing. The registry row exists, but the .docx is gone from disk. Rebuild from the source Markdown.</Banner>}
        {avail === 503 && <Banner kind="err">503 · DocEngine storage unavailable</Banner>}
        {pdfErr && <Banner kind="err">PDF → {pdfErr}</Banner>}
        <div style={{ marginTop: 'auto', display: 'flex', gap: 8 }}>
          <a href={missing ? undefined : api.documentHref(r.id, 'download')} style={{ flex: 1, textAlign: 'center', borderRadius: 6, padding: 9, fontWeight: 700, background: missing ? T.surface : T.navy, color: missing ? T.faint : '#fff', textDecoration: 'none', pointerEvents: missing ? 'none' : undefined }}>Download .docx</a>
          <a href={missing ? undefined : api.documentHref(r.id, 'pdf')} onClick={async e => {
            // Probe first: on 502/503 a plain navigation would leave the app for a bare JSON error page.
            if (api.mode !== 'live') return; e.preventDefault(); setPdfErr('');
            try { const res = await fetch(api.documentHref(r.id, 'pdf'), { credentials: 'same-origin' });
              if (!res.ok) { const j = await res.json().catch(() => ({})); setPdfErr(`${res.status} · ${(j as { detail?: string }).detail || res.statusText}`); return; }
              const a = document.createElement('a'); a.href = URL.createObjectURL(await res.blob()); a.download = `${r.code}.pdf`; a.click(); URL.revokeObjectURL(a.href);
            } catch (x) { setPdfErr(String((x as Error).message || x)); } }}
            title="Gotenberg renders on demand: 503 when no renderer is configured, 502 when conversion fails" style={{ flex: 1, textAlign: 'center', border: `1px solid ${T.control}`, borderRadius: 6, padding: 9, color: missing ? T.faint : '#fff', textDecoration: 'none', pointerEvents: missing ? 'none' : undefined }}>PDF · Gotenberg</a></div>
        {r.job_id && <span onClick={() => go('jobs', { jobSel: r.job_id! })} style={{ textAlign: 'center', color: C.run, cursor: 'pointer', fontSize: 12.5 }}>Open source job {r.job_id.slice(0, 8)} →</span>}
      </> : <>
        <div style={{ fontSize: 12, color: T.muted, lineHeight: 1.45 }}>The registry keys on <span style={{ fontFamily: MONO }}>code</span>: every passed build of {r.code} is kept. The newest approved row is effective; older rows are superseded, never deleted.</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>{versions.map((v, i) => <div key={v.id} style={{ display: 'grid', gridTemplateColumns: '14px 1fr auto', gap: 8, alignItems: 'start' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%' }}><span style={{ width: 10, height: 10, borderRadius: '50%', marginTop: 4, background: i === 0 ? C.ok : 'transparent', border: `2px solid ${i === 0 ? C.ok : T.faint}` }} />{i < versions.length - 1 && <span style={{ flex: 1, width: 2, background: T.control, minHeight: 26 }} />}</div>
          <div onClick={() => set({ libSel: v.id })} style={{ cursor: 'pointer', paddingBottom: 10 }}><div style={{ fontFamily: MONO, fontSize: 12.5, color: v.id === r.id ? '#fff' : T.text, fontWeight: v.id === r.id ? 700 : 400 }}>v{v.version} <span style={{ color: i === 0 ? C.ok : T.muted, fontWeight: 400, fontSize: 11 }}>{i === 0 ? 'effective' : 'superseded by v' + versions[i - 1].version}</span></div>
            <div style={{ fontSize: 11.5, color: T.muted }}>{when(v.created_at)} · {nbsp(v.bytes)} B · {src(v)}{v.supersedes ? ' · supersedes ' + v.supersedes.split(' ').pop() : ''}</div></div>
          {i < versions.length - 1 ? <span onClick={() => setCmp([versions[i + 1].id, v.id])} style={{ fontSize: 11.5, color: C.run, cursor: 'pointer', whiteSpace: 'nowrap' }}>diff ← v{versions[i + 1].version}</span> : <span />}</div>)}</div>
        {cmpDocs && <><Caps>DIFF · v{cmpDocs[0].version} → v{cmpDocs[1].version}</Caps>
          <div style={{ background: T.deeper, border: `1px solid ${T.hair}`, borderRadius: 6, padding: '9px 10px', fontFamily: MONO, fontSize: 10.5, lineHeight: 1.6, overflow: 'auto' }}>
            {diffLines(...(cmpDocs.map(d => [`title_mk: ${d.title_mk}`, `title_en: ${d.title_en}`, `version: ${d.version}`, `bytes: ${d.bytes}`, ...(d.verify || '').split('\n').filter(Boolean)]) as [string[], string[]])).map((l, i) =>
              <div key={i} style={{ whiteSpace: 'pre', color: l.op === '+' ? C.ok : l.op === '-' ? C.bad : T.muted, background: l.op === '+' ? 'rgba(111,208,140,.08)' : l.op === '-' ? 'rgba(224,122,111,.08)' : undefined }}>{l.op} {l.t}</div>)}</div>
          <div style={{ fontSize: 11.5, color: T.faint }}>Registry rows carry metadata and the verify report, not the Markdown. For a content diff, open both source jobs (result.markdown).</div></>}
      </>}
    </div>}
  </>;
}
