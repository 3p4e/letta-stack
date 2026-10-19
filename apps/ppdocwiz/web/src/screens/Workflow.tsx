// The one workflow (Head of QC, 18.10.2026): a Document Brief edited page by page, saved on every answer, with every
// field suggested / chosen / locked, a scope change marking decided answers stale, sources uploaded on any page and
// "Build now" on every page — the authors fill what is not decided and the job lists it as assumed.
// The questions react to the answers: an answer marks the options of later questions it recommends (and says which
// answer led there), a changed answer makes its dependents stale, and "Suggest options" asks the advisor for options
// with a reason and a source for every open question of the page (its pick arrives as suggested, never chosen).
// DocEngine app/brief.py and app/question_rules.py hold the rules; this screen only shows and edits the brief.
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { ApiError, type Brief, type BriefField, type Package, type Questionnaire as Q, type ShelfEntry } from '../api/types';
import { Banner, Caps, Seg } from '../components/ui';
import { pick } from '../lib/i18n';
import { usePrimary } from '../lib/usePrimary';
import { useApp } from '../store/store';
import { C, DISPLAY, MONO, T } from '../theme';

const LS_BRIEF = 'ppsuite.brief';
const PACKAGES: [Package, string, string][] = [
  ['sop', 'SOP', 'one SOP'],
  ['sop_annexes', 'SOP + annexes', 'the SOP, then each annex from its sections 6–7'],
  ['annex', 'Annex of an SOP', 'a form, log or checklist for an existing SOP'],
  ['form', 'Form / log / checklist', 'standalone'],
  ['report', 'Report / record', 'computational record, protocol, report'],
];
type TextPage = { k: string; title: string; fields: [string, string, string][] };
const TEXT_PAGES: TextPage[] = [
  { k: 'purpose', title: 'Purpose', fields: [['doc.purpose', 'What this document is for', 'e.g. defines how QC samples finished dry cannabis flower for release testing']] },
  { k: 'scope', title: 'Scope', fields: [['doc.scope_in', 'Included', 'products, materials, areas, activities it covers'], ['doc.scope_out', 'Excluded', 'what it does not cover, and which document does']] },
  { k: 'use', title: 'Use and users', fields: [['doc.use', 'Who uses it, where and when', 'roles, rooms, the moment in the process']] },
  { k: 'resp', title: 'Responsibilities', fields: [['doc.responsibilities', 'Who does what', 'performs, checks, approves (the RACI author drafts section 3.0 from this)']] },
  { k: 'refs', title: 'References', fields: [['doc.references', 'Documents and regulations to cite', 'house SOPs by code; EudraLex, Ph. Eur., ICH, national law'], ['doc.notes', 'Further instructions to the authors', 'anything else they must know']] },
];
const STATE_C: Record<string, string> = { suggested: T.muted, chosen: C.ok, locked: C.warn };

function toB64(f: File): Promise<string> {
  return new Promise((ok, bad) => { const r = new FileReader(); r.onload = () => ok(String(r.result).split(',')[1] || ''); r.onerror = () => bad(r.error); r.readAsDataURL(f); });
}

function Badge({ f }: { f?: BriefField }) {
  if (!f) return <span style={{ fontSize: 10.5, color: T.faint, fontFamily: MONO }}>open</span>;
  return <span style={{ fontSize: 10.5, fontFamily: MONO, color: f.stale ? C.bad : STATE_C[f.state] }}>{f.stale ? 'stale — re-confirm' : f.state}</span>;
}

export function Workflow() {
  const { api, lang, go, flash } = useApp();
  const [b, setB] = useState<Brief | null>(null);
  const [page, setPage] = useState('start');
  const [bank, setBank] = useState<Q | null>(null);
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  const [suggesting, setSuggesting] = useState(false);
  const [built, setBuilt] = useState<{ job_id: string; code: string; assumed: string[] } | null>(null);
  const [open, setOpen] = useState<{ id: string; label: string }[]>([]);
  const [approved, setApproved] = useState<ShelfEntry[]>([]);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const fileRef = useRef<HTMLInputElement>(null);

  // Reopen the brief this browser was working on.
  useEffect(() => {
    let id = ''; try { id = localStorage.getItem(LS_BRIEF) || ''; } catch { /* storage blocked */ }
    if (id) api.brief(id).then(x => { setB(x); setPage('identity'); }).catch(() => { try { localStorage.removeItem(LS_BRIEF); } catch { /* */ } });
    api.briefs().then(l => setOpen(l.filter(x => x.status === 'open').map(x => ({ id: x.id, label: `${x.meta.code || '(no code)'} · ${x.meta.title_en || x.meta.title_mk || 'untitled'} · ${x.package}` })))).catch(() => {});
    api.library().then(l => setApproved([...l.shelves.approved, ...l.shelves.revision].filter(e => e.approved || e.wip.length))).catch(() => {});
  }, [api]);
  useEffect(() => { if (!b) { setBank(null); return; } api.questionnaire(b.questionnaire).then(setBank).catch(() => setBank(null)); }, [api, b?.questionnaire]); // eslint-disable-line react-hooks/exhaustive-deps

  const adopt = (x: Brief) => { setB(x); setErr(''); try { localStorage.setItem(LS_BRIEF, x.id); } catch { /* */ } };
  const fail = (e: unknown) => { const a = e as ApiError; setErr(`${a.status || ''} ${a.message}`.trim()); if (a.status === 409 && b) api.brief(b.id).then(setB).catch(() => {}); };
  const patch = async (p: Omit<Parameters<typeof api.patchBrief>[1], 'rev'>) => {
    if (!b) return;
    try { adopt(await api.patchBrief(b.id, { ...p, rev: b.rev })); } catch (e) { fail(e); }
  };
  const start = async (pkg: Package, from_reference = '') => {
    setBusy(true); setBuilt(null);
    try { const x = await api.createBrief({ package: pkg, from_reference, requested_by: api.mode === 'live' ? 'ppdocwiz-session' : 'demo' }); adopt(x); setPage('identity'); }
    catch (e) { fail(e); } finally { setBusy(false); }
  };
  const build = async () => {
    if (!b || busy) return;
    setBusy(true);
    try { const r = await api.buildBrief(b.id, b.rev); setBuilt(r); flash(`${r.code} · job ${r.job_id.slice(0, 8)} queued`); adopt(await api.brief(b.id)); }
    catch (e) { fail(e); } finally { setBusy(false); }
  };
  const upload = async (files: FileList | null) => {
    if (!b || !files) return;
    for (const f of Array.from(files)) {
      try { const r = await api.addBriefSource(b.id, f.name, await toB64(f)); adopt(r.brief); if (r.note) flash(`${f.name}: ${r.note}`); } catch (e) { fail(e); }
    }
  };
  const suggest = async (keys: string[]) => {
    if (!b || suggesting) return;
    setSuggesting(true);
    try { const r = await api.suggestBrief(b.id, b.rev, keys); adopt(r.brief); if (r.notes.length) flash(r.notes.join(' · ')); }
    catch (e) { fail(e); } finally { setSuggesting(false); }
  };
  usePrimary(busy ? 'Building…' : 'Build now ▸', build, !b || busy || !(b.meta.title_en || b.meta.title_mk));

  const rounds = bank?.rounds || [];
  const pages = useMemo(() => {
    const p: [string, string][] = [['start', 'Start'], ['identity', 'Identity']];
    TEXT_PAGES.slice(0, 4).forEach(t => p.push([t.k, t.title]));
    rounds.forEach((r, i) => p.push([`q${i}`, pick(lang, r)[0]]));
    if (b?.package === 'sop_annexes' || b?.package === 'annex') p.push(['annexes', b.package === 'annex' ? 'Parent SOP' : 'Annexes']);
    p.push(['refs', 'References'], ['review', 'Review & build']);
    return p;
  }, [rounds, lang, b?.package]);
  const fieldsOf = (k: string): string[] => k.startsWith('q') && k !== 'start' ? (rounds[+k.slice(1)]?.questions || []).map(q => q.key)
    : (TEXT_PAGES.find(t => t.k === k)?.fields || []).map(f => f[0]);
  const pageMark = (k: string) => {
    if (!b) return '';
    const fs = fieldsOf(k).map(x => b.fields[x]);
    if (!fs.length) return '';
    if (fs.some(f => f?.stale)) return '!';
    return fs.every(f => f) ? (fs.every(f => f!.state === 'locked') ? '🔒' : '✓') : fs.some(f => f) ? '·' : '';
  };

  const lockBtn = (key: string) => {
    const f = b?.fields[key];
    if (!f) return null;
    return <span onClick={() => patch(f.state === 'locked' ? { unlock: [key] } : { lock: [key] })} title={f.state === 'locked' ? 'unlock to change' : 'lock: nothing overwrites it'}
      style={{ cursor: 'pointer', fontSize: 11.5, color: f.state === 'locked' ? C.warn : T.muted, border: `1px solid ${T.control}`, borderRadius: 4, padding: '1px 7px' }}>{f.state === 'locked' ? '🔒 locked' : 'lock'}</span>;
  };
  const acceptBtn = (key: string) => {
    const f = b?.fields[key];
    if (!f || f.state !== 'suggested') return null;
    return <span onClick={() => patch({ set: { [key]: f.value } })} title={`suggested by ${f.by || 'an agent'}: accept it as your answer`} style={{ cursor: 'pointer', fontSize: 11.5, color: C.ok }}>accept</span>;
  };
  const why = (o: { why: string; source: string }) => `${o.why}${o.why ? ' — ' : ''}${o.source}`;
  const textField = ([key, label, ph]: [string, string, string]) => {
    const f = b?.fields[key], cur = drafts[key] ?? (f ? String(f.value) : ''), locked = f?.state === 'locked';
    const save = () => { if (drafts[key] === undefined) return; const v = drafts[key].trim(); setDrafts(d => { const n = { ...d }; delete n[key]; return n; }); if (v !== (f ? String(f.value) : '')) patch({ set: { [key]: v } }); };
    return <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}><span style={{ fontSize: 13, color: '#fff' }}>{label}</span><Badge f={f} />{lockBtn(key)}
        {acceptBtn(key)}
        {f?.stale && <span onClick={() => patch({ set: { [key]: f.value } })} style={{ cursor: 'pointer', fontSize: 11.5, color: C.bad }}>re-confirm</span>}</div>
      <textarea value={cur} disabled={locked} placeholder={ph} onChange={e => setDrafts(d => ({ ...d, [key]: e.target.value }))} onBlur={save} rows={4}
        style={{ background: T.deeper, border: `1px solid ${T.control}`, borderRadius: 6, padding: 10, color: locked ? T.muted : '#fff', fontSize: 13, resize: 'vertical', outline: 'none' }} />
      {!locked && (b?.proposals?.[key]?.options || []).filter(o => o.value !== cur).map(o => <div key={o.value} style={{ display: 'flex', gap: 8, fontSize: 12, alignItems: 'baseline' }}>
        <span onClick={() => patch({ set: { [key]: o.value } })} style={{ cursor: 'pointer', color: C.run, flex: 'none' }}>use</span>
        <span style={{ color: T.secondary }}>{o.value}</span><span style={{ color: T.faint, fontSize: 11 }}>{why(o)}</span></div>)}
    </div>;
  };

  const startPage = <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 820 }}>
    <div style={{ fontFamily: DISPLAY, fontSize: 18, color: '#fff', fontWeight: 700 }}>One workflow for every document</div>
    <Caps>NEW</Caps>
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(220px,1fr))', gap: 8 }}>
      {PACKAGES.map(([k, l, sub]) => <div key={k} onClick={() => !busy && start(k)} className="pp-hover-row" style={{ cursor: 'pointer', border: `1px solid ${T.control}`, borderRadius: 8, padding: '10px 12px' }}>
        <div style={{ color: '#fff', fontSize: 13.5 }}>{l}</div><div style={{ color: T.muted, fontSize: 12 }}>{sub}</div></div>)}
    </div>
    {approved.length > 0 && <><Caps>REVISE OR CONTINUE A DOCUMENT FROM THE LIBRARY</Caps>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 260, overflow: 'auto' }}>{approved.map(e => {
        const ref = e.wip[0] || e.approved!;
        return <div key={e.code} onClick={() => !busy && start(e.code.includes('SOP') && !/A\d{2}$/.test(e.code) ? 'sop' : 'annex', ref.id)} className="pp-hover-row" style={{ cursor: 'pointer', display: 'flex', gap: 10, padding: '6px 10px', borderRadius: 6, fontSize: 12.5 }}>
          <b style={{ fontFamily: MONO, color: '#fff', width: 110 }}>{e.code}</b><span style={{ color: T.secondary, flex: 1 }}>{e.title_mk || e.title_en}</span>
          <span style={{ color: T.muted, fontSize: 11.5 }}>{e.wip.length ? `continue draft v${e.wip[0].version}` : `revise v${e.approved!.version}`}</span></div>; })}</div></>}
    {open.length > 0 && <><Caps>CONTINUE A BRIEF</Caps>
      {open.map(o => <div key={o.id} onClick={() => api.brief(o.id).then(x => { adopt(x); setPage('identity'); }).catch(fail)} className="pp-hover-row" style={{ cursor: 'pointer', padding: '6px 10px', borderRadius: 6, fontSize: 12.5, color: T.secondary, fontFamily: MONO }}>{o.label}</div>)}</>}
  </div>;

  const identity = b && <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 760 }}>
    <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}><span style={{ fontSize: 12, color: T.muted, width: 96, fontFamily: MONO }}>package</span>
      <Seg items={PACKAGES.map(([k, l]) => [k, l] as [Package, string])} value={b.package} onPick={k => patch({ package: k })} size={12} pad="4px 10px" /></div>
    {([['title_mk', 'title МК', 'Наслов на македонски'], ['title_en', 'title EN', 'Title in English'], ['code', 'code', 'empty: the next free code at build'], ['version', 'version', '01'], ['department', 'department', 'QC · QA · WH · EQ · SP · CU']] as const).map(([k, l, ph]) =>
      <label key={k} style={{ display: 'grid', gridTemplateColumns: '96px 1fr', gap: 10, alignItems: 'center' }}><span style={{ fontSize: 12, color: T.muted, fontFamily: MONO }}>{l}</span>
        <input defaultValue={b.meta[k] || ''} placeholder={ph} key={b.id + k + (b.meta[k] || '')} onBlur={e => { const v = e.target.value.trim(); if (v !== (b.meta[k] || '')) patch({ meta: { [k]: v } }); }}
          style={{ background: T.deeper, border: `1px solid ${T.control}`, borderRadius: 5, padding: '7px 9px', color: '#fff', outline: 'none', fontFamily: k === 'code' ? MONO : undefined }} /></label>)}
    <div style={{ fontSize: 12, color: T.faint }}>A number not yet confirmed is written XXX (QASOPXXX). Leave the code empty and the build takes the register's next free one.</div>
  </div>;

  const qPage = (i: number) => {
    const r = rounds[i];
    if (!r || !b) return null;
    return <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 860 }}>
      {r.questions.map(q => {
        const f = b.fields[q.key], val = f ? f.value : undefined, locked = f?.state === 'locked';
        const has = (v: string) => Array.isArray(val) ? val.includes(v) : val === v;
        const toggle = (v: string) => {
          if (locked) return;
          const next = q.multi ? (Array.isArray(val) ? (val.includes(v) ? val.filter(x => x !== v) : [...val, v]) : [v]) : (val === v ? '' : v);
          patch({ set: { [q.key]: next } });
        };
        const g = b.guide?.questions[q.key], rec = new Map((g?.recommended || []).map(r => [r.value, r.because]));
        const offered = new Set(q.options.map(o => o.v));
        const prop = new Map((b.proposals?.[q.key]?.options || []).map(o => [o.value, o]));
        const extra = [...prop.values()].filter(o => !offered.has(o.value));
        const chip = (v: string, note: React.ReactNode, title: string) => <span key={v} onClick={() => toggle(v)} title={title} style={{ cursor: locked ? 'not-allowed' : 'pointer', padding: '5px 10px', borderRadius: 5, fontSize: 12.5, border: `1px solid ${has(v) ? C.ok : rec.has(v) ? C.run : T.control}`, background: has(v) ? 'rgba(80,170,120,.14)' : 'transparent', color: has(v) ? '#fff' : T.secondary }}>{v}{note}</span>;
        return <div key={q.key} style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}><span style={{ fontSize: 13, color: '#fff' }}>{pick(lang, q)[0]}</span><span style={{ fontSize: 11.5, color: T.muted }}>{pick(lang, q)[1]}</span><Badge f={f} />{lockBtn(q.key)}{acceptBtn(q.key)}
            {f?.stale && <span onClick={() => patch({ set: { [q.key]: f.value } })} style={{ cursor: 'pointer', fontSize: 11.5, color: C.bad }}>re-confirm</span>}</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>{q.options.map(o => chip(o.v, <>
            {o.isDefault && !f && <span style={{ color: C.ok, fontSize: 10, marginLeft: 5 }}>default</span>}
            {rec.has(o.v) && <span style={{ color: C.run, fontSize: 10, marginLeft: 5 }}>recommended</span>}
            {prop.has(o.v) && <span style={{ color: C.warn, fontSize: 10, marginLeft: 5 }}>advisor</span>}</>,
            [rec.has(o.v) ? `recommended because ${rec.get(o.v)!.join('; ')}` : '', prop.has(o.v) ? `advisor: ${why(prop.get(o.v)!)}` : ''].filter(Boolean).join('\n')))}
            {extra.map(o => chip(o.value, <span style={{ color: C.warn, fontSize: 10, marginLeft: 5 }}>advisor</span>, `advisor: ${why(o)}`))}</div>
          {extra.length > 0 && <div style={{ fontSize: 11, color: T.faint }}>{extra.map(o => `${o.value}: ${why(o)}`).join(' · ')}</div>}
          {g && g.depends_on.length > 0 && <div style={{ fontSize: 11, color: T.faint }}>rests on {g.depends_on.join(', ')}: a change there asks you to re-confirm this</div>}
        </div>;
      })}
      <div style={{ fontSize: 12, color: T.faint }}>An unanswered question takes its default at build and is listed as assumed.</div>
    </div>;
  };

  const annexPage = b && (b.package === 'annex'
    ? <label style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 10, alignItems: 'center', maxWidth: 600 }}><span style={{ fontSize: 12, color: T.muted, fontFamily: MONO }}>parent SOP</span>
      <input defaultValue={b.parent_sop} key={b.id + b.parent_sop} placeholder="e.g. QCSOP011" onBlur={e => { const v = e.target.value.trim(); if (v !== b.parent_sop) patch({ parent_sop: v }); }}
        style={{ background: T.deeper, border: `1px solid ${T.control}`, borderRadius: 5, padding: '7px 9px', color: '#fff', outline: 'none', fontFamily: MONO }} /></label>
    : <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 760 }}>
      <div style={{ fontSize: 12.5, color: T.secondary }}>Each annex is written after the SOP, from its sections 6–7, and numbered under its code (A01, A02 …).</div>
      {b.annexes.map((a, i) => <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <span style={{ fontFamily: MONO, color: T.muted, width: 36 }}>A{String(i + 1).padStart(2, '0')}</span>
        <input defaultValue={a.title_en} key={b.rev + 'a' + i} placeholder="title EN" onBlur={e => { const n = [...b.annexes]; n[i] = { ...a, title_en: e.target.value.trim() }; if (n[i].title_en !== a.title_en) patch({ annexes: n }); }} style={{ flex: 1, background: T.deeper, border: `1px solid ${T.control}`, borderRadius: 5, padding: '6px 8px', color: '#fff' }} />
        <input defaultValue={a.title_mk} key={b.rev + 'm' + i} placeholder="наслов МК" onBlur={e => { const n = [...b.annexes]; n[i] = { ...a, title_mk: e.target.value.trim() }; if (n[i].title_mk !== a.title_mk) patch({ annexes: n }); }} style={{ flex: 1, background: T.deeper, border: `1px solid ${T.control}`, borderRadius: 5, padding: '6px 8px', color: '#fff' }} />
        <Seg items={[['form', 'form'], ['log', 'log'], ['checklist', 'checklist']]} value={a.kind as 'form'} onPick={k => { const n = [...b.annexes]; n[i] = { ...a, kind: k }; patch({ annexes: n }); }} size={11} pad="3px 7px" />
        <span onClick={() => patch({ annexes: b.annexes.filter((_, j) => j !== i) })} style={{ cursor: 'pointer', color: T.muted }}>×</span></div>)}
      <span onClick={() => patch({ annexes: [...b.annexes, { title_en: `Annex ${b.annexes.length + 1}`, title_mk: '', kind: 'form' }] })} style={{ cursor: 'pointer', color: C.run, fontSize: 13 }}>＋ add annex</span>
    </div>);

  const review = b && <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxWidth: 860 }}>
    <div style={{ fontSize: 13, color: T.secondary }}>Build now and the authors take over the rest. What you have not decided is filled by them and listed in the review report as assumed.</div>
    <div style={{ border: `1px solid ${T.hair}`, borderRadius: 8 }}>
      {[...TEXT_PAGES.flatMap(t => t.fields.map(f => f[0])), ...rounds.flatMap(r => r.questions.map(q => q.key))].map(k => {
        const f = b.fields[k];
        return <div key={k} style={{ display: 'grid', gridTemplateColumns: '200px minmax(0,1fr) 140px', gap: 10, padding: '7px 12px', borderTop: `1px solid ${T.hair}`, fontSize: 12.5 }}>
          <span style={{ fontFamily: MONO, color: T.muted }}>{k}</span><span style={{ color: f ? '#fff' : T.faint, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f ? (Array.isArray(f.value) ? f.value.join(', ') : f.value) : 'not decided → assumed'}</span><Badge f={f} /></div>;
      })}
    </div>
    {built && <Banner kind="ok">{built.code} · job {built.job_id.slice(0, 8)} queued. Assumed: {built.assumed.join(', ') || 'nothing'}. <span onClick={() => go('jobs', { jobSel: built.job_id })} style={{ cursor: 'pointer', textDecoration: 'underline' }}>Open in Jobs</span></Banner>}
  </div>;

  const body = page === 'start' || !b ? startPage : page === 'identity' ? identity : page === 'annexes' ? annexPage : page === 'review' ? review
    : page.startsWith('q') ? qPage(+page.slice(1)) : <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 860 }}>{TEXT_PAGES.find(t => t.k === page)?.fields.map(textField)}</div>;
  const idx = pages.findIndex(p => p[0] === page);

  return <>
    <div style={{ width: 190, flex: 'none', borderRight: `1px solid ${T.hair}`, background: T.pane, padding: '14px 10px', display: 'flex', flexDirection: 'column', gap: 2, overflow: 'auto' }}>
      {pages.map(([k, l]) => <div key={k} onClick={() => (b || k === 'start') && setPage(k)} style={{ display: 'flex', gap: 8, padding: '7px 10px', borderRadius: 6, fontSize: 13, cursor: b || k === 'start' ? 'pointer' : 'default', color: page === k ? '#fff' : b || k === 'start' ? T.secondary : T.faint, background: page === k ? T.selected : 'transparent' }}>
        <span style={{ flex: 1 }}>{l}</span><span style={{ fontSize: 11, color: pageMark(k) === '!' ? C.bad : C.ok }}>{pageMark(k)}</span></div>)}
    </div>
    <div style={{ flex: 1, minWidth: 0, padding: '18px 24px', display: 'flex', flexDirection: 'column', gap: 14, overflow: 'auto' }}>
      {err && <Banner kind="err">{err}</Banner>}
      {b && <div style={{ display: 'flex', gap: 12, alignItems: 'baseline', fontFamily: MONO, fontSize: 12, color: T.muted }}>
        <b style={{ color: '#fff' }}>{b.meta.code || 'code at build'}</b><span>{b.meta.title_en || b.meta.title_mk || 'untitled'}</span><span>· {b.package} · rev {b.rev}</span>
        <span onClick={() => { try { localStorage.removeItem(LS_BRIEF); } catch { /* */ } setB(null); setPage('start'); setBuilt(null); }} style={{ marginLeft: 'auto', cursor: 'pointer' }}>close brief</span></div>}
      {b?.guide?.questionnaire_hint && b.guide.questionnaire_hint !== b.questionnaire && <Banner kind="info">The title or scope points to the <b>{b.guide.questionnaire_hint}</b> questions. <span onClick={() => patch({ questionnaire: b.guide!.questionnaire_hint })} style={{ cursor: 'pointer', textDecoration: 'underline' }}>Use them</span> (answers to the current ones stay in the history).</Banner>}
      {b && fieldsOf(page).length > 0 && <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
        <span onClick={() => suggest(fieldsOf(page))} style={{ cursor: suggesting ? 'wait' : 'pointer', color: C.run, fontSize: 13 }}>{suggesting ? 'Asking the advisor…' : '✦ Suggest options for this page'}</span>
        <span style={{ fontSize: 11.5, color: T.faint }}>from the approved house documents, the regulations and your sources; decided answers are left alone</span></div>}
      {body}
      {b && idx > 0 && <div style={{ display: 'flex', gap: 10, marginTop: 'auto', paddingTop: 10 }}>
        <span onClick={() => setPage(pages[idx - 1][0])} style={{ cursor: 'pointer', color: T.secondary, fontSize: 13 }}>‹ {pages[idx - 1][1]}</span>
        {idx < pages.length - 1 && <span onClick={() => setPage(pages[idx + 1][0])} style={{ cursor: 'pointer', color: C.run, fontSize: 13, marginLeft: 'auto' }}>{pages[idx + 1][1]} ›</span>}</div>}
    </div>
    {b && <div style={{ width: 280, flex: 'none', borderLeft: `1px solid ${T.hair}`, background: T.pane, padding: 14, display: 'flex', flexDirection: 'column', gap: 10, overflow: 'auto' }}>
      <button onClick={build} disabled={busy || !(b.meta.title_en || b.meta.title_mk)} style={{ background: T.navy, color: '#fff', border: 'none', borderRadius: 6, padding: '9px 12px', fontSize: 13.5, cursor: 'pointer' }}>{busy ? 'Building…' : 'Build now ▸'}</button>
      <div style={{ fontSize: 11.5, color: T.faint }}>Builds from this page: the authors write the rest.</div>
      <Caps>SOURCES · {b.sources.length}</Caps>
      <input ref={fileRef} type="file" multiple accept=".docx,.pdf,.json,.md" style={{ display: 'none' }} onChange={e => { upload(e.target.files); e.target.value = ''; }} />
      <span onClick={() => fileRef.current?.click()} style={{ cursor: 'pointer', color: C.run, fontSize: 13 }}>＋ upload .docx · .pdf · .json · .md</span>
      {b.sources.map(s => <div key={s.id} style={{ display: 'flex', gap: 6, fontSize: 12, alignItems: 'center' }}>
        <span style={{ flex: 1, color: T.secondary, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={s.name}>{s.name}</span>
        <span style={{ color: s.chars ? T.muted : C.warn, fontFamily: MONO, fontSize: 11 }}>{s.chars ? `${Math.round(s.chars / 1000)}k` : 'no text'}</span>
        <span onClick={() => api.removeBriefSource(b.id, s.id).then(adopt).catch(fail)} style={{ cursor: 'pointer', color: T.muted }}>×</span></div>)}
      {b.job_ids.length > 0 && <><Caps>BUILDS · {b.job_ids.length}</Caps>{b.job_ids.map(j => <span key={j} onClick={() => go('jobs', { jobSel: j })} style={{ cursor: 'pointer', fontFamily: MONO, fontSize: 11.5, color: T.secondary }}>job {j.slice(0, 8)}</span>)}</>}
    </div>}
  </>;
}
