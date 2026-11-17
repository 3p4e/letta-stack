// Document canvas. Head of QC, 20.10.2026: "the editing and interactive canvas after the initial generation … has no
// functions"; 12.11.2026: "it has zero functionality and it's not working proper". It could only be reached from a job
// this browser had started, kept edits in the browser, and could not open a Library document. Since 17.11.2026 a draft
// is held on the server (POST/GET/PUT /canvas, with revisions): it opens from any job, a Library document, an uploaded
// Markdown file or a blank page, on any device; it is read side by side, edited by hand (with blocks to insert),
// changed by an instruction to the author (shown as a diff to accept or discard), saved with a revision history and
// rebuilt through the engine's gate (POST /build). The HEADERDATA block is never edited by the author.
import { useEffect, useMemo, useRef, useState } from 'react';
import type { CanvasDraft, CanvasRevision, ReviseResult } from '../api/client';
import { ApiError, type DocumentRow, type Job } from '../api/types';
import { Banner, Btn, Seg, press } from '../components/ui';
import { bilingual, columnChanges, headField, joinDraft, lineDiff, sectionTitle, splitDraft } from '../lib/draft';
import { limitValue } from '../lib/limits';
import { usePrimary } from '../lib/usePrimary';
import { lineColor } from '../lib/verify';
import { useApp } from '../store/store';
import { C, DISPLAY, MONO, T } from '../theme';

const QUICK = [
  'Make this section shorter and clearer; keep every requirement.',
  'Add a responsibilities table (role · responsibility).',
  'Tighten the English so it matches the Macedonian exactly.',
  'Use the house glossary terms (мострирање, мостра, во процес).',
  'Add the records this step produces, with their document codes.',
];

// Blocks the engine draws (build_from_md.py); inserted at the end of the open section.
const BLOCKS: [string, string][] = [
  ['Text', 'Текст на македонски. ||| Text in English.'],
  ['Table', '[[TABLE]]\nКолона 1 ~~ Column 1 ||| Колона 2 ~~ Column 2\nВредност ~~ Value ||| Вредност ~~ Value\n[[/TABLE]]'],
  ['Form', '[[FORM]]\nДатум ||| Date ||| \nПотпис ||| Signature ||| \n[[/FORM]]'],
  ['Limit bars', '[[LIMITS]]\n@col TAMC, CFU/g ~~ ≤ 10⁵ | 100000 | log\n@col E. coli ~~ absent /1 g | absent | qual\n@group Batch ~~ finding\n01.01.2026 ~~ Lab · certificate ||| 2 × 10³ ||| Absent\n[[/LIMITS]]'],
  ['Box', '[[BOX:4]]\nПростор ||| Space\n[[/BOX]]'],
  ['Signatures', '[[SIGN]] Изготвил ||| Prepared by'],
  ['Page break', '[[PAGEBREAK]]'],
];

type Proposal = ReviseResult & { instruction: string; before: string };
type Built = { id: string | null; ok: boolean; verify: string; at: string };
const ago = (iso: string) => { const m = Math.round((Date.now() - Date.parse(iso)) / 60000); return m < 1 ? 'now' : m < 60 ? `${m} min` : m < 1440 ? `${Math.round(m / 60)} h` : `${Math.round(m / 1440)} d`; };

export function Canvas() {
  const { api, canvasDraft, canvasReq, set, flash } = useApp();
  const [draftRow, setDraftRow] = useState<CanvasDraft | null>(null);
  const [err, setErr] = useState('');
  const [md, setMd] = useState('');
  const [rev, setRev] = useState(0);
  const [savedMd, setSavedMd] = useState('');
  const [saveState, setSaveState] = useState<'' | 'saving' | 'saved' | 'conflict' | 'error'>('');
  const [sel, setSel] = useState<number | null>(0);
  const [view, setView] = useState<'read' | 'edit' | 'pdf' | 'history'>('read');
  const [cmd, setCmd] = useState('');
  const [busy, setBusy] = useState<'' | 'revise' | 'build' | 'open'>('');
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [built, setBuilt] = useState<Built | null>(null);
  const [revs, setRevs] = useState<CanvasRevision[]>([]);
  const [peek, setPeek] = useState<{ rev: number; md: string } | null>(null);
  const timer = useRef<number>();

  const openId = (id: string | null) => { try { id ? localStorage.setItem('ppsuite.canvasDraft', id) : localStorage.removeItem('ppsuite.canvasDraft'); } catch { /* */ } set({ canvasDraft: id }); };

  // A request from Jobs or the Library: make a server draft from it, then open that.
  useEffect(() => {
    if (!canvasReq) return;
    setBusy('open');
    api.canvasOpen(canvasReq).then(d => { set({ canvasReq: null }); openId(d.id); })
      .catch((e: ApiError) => { set({ canvasReq: null }); flash(`open → ${e.status || ''} ${e.message}`); })
      .finally(() => setBusy(''));
  }, [api, canvasReq]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!canvasDraft) { setDraftRow(null); return; }
    let live = true;
    setErr(''); setProposal(null); setBuilt(null); setPeek(null); setSaveState('');
    api.canvasGet(canvasDraft).then(d => {
      if (!live) return;
      setDraftRow(d); setMd(d.markdown || ''); setSavedMd(d.markdown || ''); setRev(d.rev); setSel(0);
      setView(d.document_id ? 'pdf' : 'read');
    }).catch((e: ApiError) => { if (!live) return; if (e.status === 404) openId(null); else setErr(`${e.status} · ${e.message}`); });
    return () => { live = false; };
  }, [api, canvasDraft]); // eslint-disable-line react-hooks/exhaustive-deps

  const draft = useMemo(() => splitDraft(md), [md]);
  const dirty = md !== savedMd;
  const code = headField(draft.head, 'code') || draftRow?.code || 'document';
  const doctype = headField(draft.head, 'doctype') || draftRow?.doctype || 'ANNEX';
  const target = sel === null ? draft.sections.join('\n\n') : draft.sections[sel] ?? '';
  const pdfId = built?.ok ? built.id : (!dirty && draftRow?.document_id) || null;

  const save = async (text: string, note = '', document_id: string | null = null) => {
    if (!draftRow) return;
    setSaveState('saving');
    try { const r = await api.canvasSave(draftRow.id, { markdown: text, rev, note, document_id }); setRev(r.rev); setSavedMd(text); setSaveState('saved'); }
    catch (e) { setSaveState((e as ApiError).status === 409 ? 'conflict' : 'error'); }
  };
  // Hand edits are saved two seconds after the last keystroke.
  useEffect(() => {
    if (!draftRow || !dirty || saveState === 'conflict') return;
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => save(md, 'edited by hand'), 2000);
    return () => window.clearTimeout(timer.current);
  }, [md]); // eslint-disable-line react-hooks/exhaustive-deps

  const setTarget = (text: string) => {
    setMd(sel === null ? joinDraft(draft.head, splitDraft('\n' + text).sections) : joinDraft(draft.head, draft.sections.map((s, i) => i === sel ? text : s)));
    setBuilt(null);
  };
  const insert = (block: string) => { setTarget(target.replace(/\s*$/, '') + '\n' + block + '\n'); setView('edit'); };

  const send = async () => {
    if (!draftRow || !cmd.trim() || busy) return;
    setBusy('revise'); setProposal(null);
    try {
      const r = await api.canvasRevise(draftRow.id, { instruction: cmd.trim(), markdown: md, section: sel });
      setProposal({ ...r, instruction: cmd.trim(), before: md });
    } catch (e) { flash(`revise → ${(e as ApiError).status || ''} ${(e as Error).message}`); }
    finally { setBusy(''); }
  };
  const decide = async (accept: boolean) => {
    if (!proposal) return;
    if (accept) { window.clearTimeout(timer.current); setMd(proposal.markdown); setBuilt(null); setView('read'); setCmd(''); await save(proposal.markdown, 'instruction: ' + proposal.instruction.slice(0, 240)); }
    setProposal(null);
  };
  const rebuild = async () => {
    if (!draftRow || busy) return;
    setBusy('build');
    try {
      const r = await api.directBuild(md, code, { code, title_mk: headField(draft.head, 'mk_title') || draftRow.title_mk, title_en: headField(draft.head, 'en_title') || draftRow.title_en, version: headField(draft.head, 'version') || '01', doctype, source: 'canvas' });
      setBuilt({ id: r.document_id, ok: true, verify: r.verify, at: new Date().toLocaleTimeString() }); setView('pdf');
      window.clearTimeout(timer.current); await save(md, 'rebuilt · gate passed', r.document_id);
      flash(`${code} rebuilt · gate passed`);
    } catch (e) {
      const b = (e as ApiError).body as { detail?: { verify?: string }; verify?: string } | undefined;
      setBuilt({ id: null, ok: false, verify: b?.detail?.verify || b?.verify || String((e as Error).message), at: new Date().toLocaleTimeString() }); setView('pdf');
    } finally { setBusy(''); }
  };
  const loadHistory = async () => { if (draftRow) { setView('history'); setRevs(await api.canvasRevisions(draftRow.id)); } };
  const restore = async (r: number) => { if (!draftRow) return; const text = await api.canvasRevision(draftRow.id, r); setMd(text); setPeek(null); setView('read'); await save(text, `restored revision ${r}`); };
  const reload = async () => { if (!draftRow) return; const d = await api.canvasGet(draftRow.id); setMd(d.markdown || ''); setSavedMd(d.markdown || ''); setRev(d.rev); setSaveState(''); };
  usePrimary(busy === 'build' ? 'Building…' : 'Rebuild ▸', rebuild, !draftRow || !md || !!busy);

  if (!canvasDraft || !draftRow) {
    if (err) return <div style={{ flex: 1, padding: 22 }}><Banner kind="err">canvas → {err}</Banner></div>;
    return <Start busy={busy === 'open'} onOpen={openId} />;
  }

  const diff = proposal ? lineDiff(proposal.section === null ? splitDraft(proposal.before).sections.join('\n\n') : splitDraft(proposal.before).sections[proposal.section] ?? '',
    proposal.section === null ? splitDraft(proposal.markdown).sections.join('\n\n') : splitDraft(proposal.markdown).sections[proposal.section] ?? '') : [];
  const stateTxt = saveState === 'saving' ? 'saving…' : saveState === 'conflict' ? 'changed elsewhere' : saveState === 'error' ? 'not saved' : dirty ? 'unsaved' : `saved · rev ${rev}`;

  return <div className="pp-canvas">
    <aside className="pp-canvas-sections" style={{ background: T.pane, borderRight: `1px solid ${T.hair}` }}>
      <div style={{ padding: '14px 12px 8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span onClick={() => openId(null)} {...press(() => openId(null))} style={{ cursor: 'pointer', color: T.muted, fontSize: 12 }}>◂ drafts</span></div>
        <div style={{ fontFamily: DISPLAY, fontWeight: 700, color: T.strong, fontSize: 15 }}>{code}</div>
        <div style={{ fontSize: 12, color: T.secondary, lineHeight: 1.4 }}>{headField(draft.head, 'mk_title') || draftRow.title_mk} | {headField(draft.head, 'en_title') || draftRow.title_en}</div>
        <div style={{ fontFamily: MONO, fontSize: 11, color: saveState === 'conflict' || saveState === 'error' ? C.bad : dirty ? C.warn : T.muted, marginTop: 4 }}>{doctype} · v{headField(draft.head, 'version') || '—'} · {stateTxt}</div>
      </div>
      <div className="pp-canvas-seclist">
        <SecItem on={sel === null} onPick={() => setSel(null)} label="Whole document" sub={`${draft.sections.length} section${draft.sections.length === 1 ? '' : 's'}`} />
        {draft.sections.map((s, i) => <SecItem key={i} on={sel === i} onPick={() => setSel(i)} label={sectionTitle(s)} sub={`${s.split('\n').length} lines`} />)}
        <div onClick={() => { setMd(joinDraft(draft.head, [...draft.sections, `# ${draft.sections.length + 1}. НОВ ДЕЛ | NEW SECTION\nТекст. ||| Text.`])); setSel(draft.sections.length); setView('edit'); }}
          {...press(() => undefined)} style={{ margin: '6px 8px', padding: '6px 10px', border: `1px dashed ${T.control}`, borderRadius: 6, cursor: 'pointer', fontSize: 12.5, color: T.secondary }}>+ Add section</div>
      </div>
    </aside>

    <section className="pp-canvas-doc" style={{ background: T.deep }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderBottom: `1px solid ${T.hair}`, flexWrap: 'wrap' }}>
        <Seg items={[['read', 'Read'], ['edit', 'Edit'], ['pdf', 'PDF'], ['history', 'History']]} value={view} onPick={v => v === 'history' ? loadHistory() : setView(v)} pad="5px 12px" />
        <span style={{ fontSize: 12.5, color: T.muted, flex: 1, minWidth: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{sel === null ? 'Whole document' : sectionTitle(draft.sections[sel] || '')}</span>
        <span style={{ marginLeft: 'auto', display: 'flex', gap: 8, flex: 'none' }}>
          {dirty && <Btn primary={false} onClick={() => save(md, 'saved by hand')} style={{ padding: '5px 10px', fontSize: 12.5 }}>Save</Btn>}
          <Btn onClick={rebuild} disabled={!!busy} style={{ padding: '5px 12px', fontSize: 12.5 }}>{busy === 'build' ? 'Building…' : 'Rebuild'}</Btn>
        </span>
      </div>
      {saveState === 'conflict' && <div style={{ padding: '8px 14px' }}><Banner kind="warn">Someone saved this draft on another device since you opened it. <span onClick={reload} {...press(reload)} style={{ textDecoration: 'underline', cursor: 'pointer' }}>Load their version</span> (your unsaved change is lost), or copy your text first.</Banner></div>}
      {view === 'edit' && <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', padding: '8px 14px 0' }}>
        <span style={{ fontSize: 11.5, color: T.faint, fontFamily: MONO, alignSelf: 'center' }}>INSERT</span>
        {BLOCKS.map(([label, text]) => <span key={label} className="pp-chip" onClick={() => insert(text)} {...press(() => insert(text))}
          style={{ fontSize: 12, padding: '3px 9px', borderRadius: 12, border: `1px solid ${T.control}`, color: T.secondary, cursor: 'pointer' }}>{label}</span>)}</div>}
      <div style={{ flex: 1, minHeight: 0, overflow: 'auto', padding: view === 'pdf' ? 0 : '16px 18px' }}>
        {view === 'read' && <ReadView text={target} />}
        {view === 'edit' && <textarea aria-label="Section Markdown" value={target} onChange={e => setTarget(e.target.value)} spellCheck={false}
          style={{ width: '100%', minHeight: '60vh', height: '100%', background: T.surface, border: `1px solid ${T.control}`, borderRadius: 8, padding: 14, color: T.text, fontFamily: MONO, fontSize: 13, lineHeight: 1.7, resize: 'vertical', outline: 'none' }} />}
        {view === 'history' && <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxWidth: 900 }}>
          {revs.map(r => <div key={r.rev} style={{ display: 'flex', gap: 10, alignItems: 'center', borderBottom: `1px solid ${T.hair}`, padding: '6px 0', fontSize: 13 }}>
            <span style={{ fontFamily: MONO, color: T.muted, width: 52 }}>rev {r.rev}</span>
            <span style={{ flex: 1, color: T.text }}>{r.note || '—'}<div style={{ fontSize: 11.5, color: T.muted }}>{r.actor || '—'} · {ago(r.at)} ago · {r.chars} chars</div></span>
            <Btn primary={false} onClick={async () => setPeek({ rev: r.rev, md: await api.canvasRevision(draftRow.id, r.rev) })} style={{ padding: '4px 10px', fontSize: 12 }}>View</Btn>
            {r.rev !== rev && <Btn primary={false} onClick={() => restore(r.rev)} style={{ padding: '4px 10px', fontSize: 12 }}>Restore</Btn>}
          </div>)}
          {peek && <div style={{ marginTop: 10 }}><b style={{ fontSize: 13 }}>Revision {peek.rev}</b><ReadView text={splitDraft(peek.md).sections.join('\n\n')} /></div>}
        </div>}
        {view === 'pdf' && (built && !built.ok
          ? <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
              <Banner kind="err">Rebuild at {built.at} was <b>rejected by the gate</b> and not registered. Fix the lines marked below and rebuild.</Banner>
              <div style={{ background: T.surface, border: `1px solid ${T.hair}`, borderRadius: 8, padding: 12, fontFamily: MONO, fontSize: 12, lineHeight: 1.7 }}>{built.verify.split('\n').map((l, i) => <div key={i} style={{ whiteSpace: 'pre-wrap', color: lineColor(l) }}>{l}</div>)}</div>
            </div>
          : pdfId && api.mode === 'mock'
            ? <div style={{ padding: 18 }}><Banner kind="info">Sample mode: the gate passed and the document was registered. On the live engine the rendered PDF opens here.</Banner></div>
          : pdfId
            ? <iframe title="document PDF" src={api.documentHref(pdfId, 'pdf') + '?inline=1'} style={{ width: '100%', height: '100%', minHeight: '70vh', border: 0, background: '#fff' }} />
            : <div style={{ padding: 18, color: T.secondary, lineHeight: 1.5 }}>{dirty || built === null ? 'Rebuild to see the PDF of this version.' : ''}
                <div style={{ marginTop: 10 }}><Btn onClick={rebuild} disabled={!!busy}>{busy === 'build' ? 'Building…' : 'Rebuild now'}</Btn></div></div>)}
      </div>
      {built?.ok && view === 'pdf' && <div style={{ padding: '8px 14px', borderTop: `1px solid ${T.hair}`, fontSize: 12.5, display: 'flex', gap: 12, flexWrap: 'wrap', color: T.secondary }}>
        <span style={{ color: C.ok, fontWeight: 700 }}>✓ gate passed {built.at}</span>
        {built.id && <><a href={api.documentHref(built.id, 'download')}>.docx</a><a href={api.documentHref(built.id, 'pdf')}>.pdf</a></>}
        <span style={{ marginLeft: 'auto', fontFamily: MONO, fontSize: 11.5, color: T.muted }}>registered as a new document · Library</span></div>}
    </section>

    <aside className="pp-canvas-cmd" style={{ background: T.pane, borderLeft: `1px solid ${T.hair}` }}>
      <div style={{ fontWeight: 700, color: T.strong, fontSize: 14 }}>Instruct the author</div>
      <div style={{ fontSize: 12.5, color: T.secondary, lineHeight: 1.45 }}>
        {doctype === 'SOP' ? 'gf_sop_author' : 'gf_annex_author'} rewrites <b>{sel === null ? 'the whole document' : `section “${sectionTitle(draft.sections[sel] || '')}”`}</b> by your instruction.
        You see the change before it is applied. Code, version and titles never change here.</div>
      <textarea aria-label="Instruction" value={cmd} onChange={e => setCmd(e.target.value)} placeholder="e.g. Add a step for labelling the sample before transport"
        onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); send(); } }}
        style={{ minHeight: 96, background: T.surface, border: `1px solid ${T.control}`, borderRadius: 8, padding: 10, color: T.text, resize: 'vertical', outline: 'none', fontSize: 13.5, lineHeight: 1.5 }} />
      <Btn onClick={send} disabled={!cmd.trim() || !!busy} style={{ padding: 10 }}>{busy === 'revise' ? 'The author is writing…' : 'Send instruction'}</Btn>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>{QUICK.map(q => <span key={q} onClick={() => setCmd(q)} {...press(() => setCmd(q))} className="pp-chip"
        style={{ fontSize: 12, padding: '4px 9px', borderRadius: 14, border: `1px solid ${T.control}`, color: T.secondary, cursor: 'pointer', lineHeight: 1.3 }}>{q}</span>)}</div>
      {proposal && <div style={{ display: 'flex', flexDirection: 'column', gap: 8, border: `1px solid ${T.focus}`, borderRadius: 8, padding: 10, background: T.surface }}>
        <b style={{ fontSize: 13, color: T.strong }}>Proposed change · {proposal.section === null ? 'whole document' : proposal.title}</b>
        {proposal.gaps.length > 0 && <Banner kind="warn">One language only in {proposal.gaps.join(', ')}. Discard, or accept and fix by hand.</Banner>}
        {(() => { const cc = columnChanges(diff); const show = (l: string) => l.split('~~').map(x => x.trim()).join(' · ');
          return (cc.added.length > 0 || cc.removed.length > 0) && <div style={{ fontSize: 12.5, lineHeight: 1.45, display: 'flex', flexDirection: 'column', gap: 3 }}>
            {cc.added.map(c => <div key={'+' + c} style={{ color: C.ok }}><b>+ column</b> {show(c)}</div>)}
            {cc.removed.map(c => <div key={'-' + c} style={{ color: C.bad }}><b>− column</b> {show(c)}</div>)}
          </div>; })()}
        <div style={{ maxHeight: 320, overflow: 'auto', fontFamily: MONO, fontSize: 11.5, lineHeight: 1.6, borderRadius: 6, border: `1px solid ${T.hair}` }}>
          {diff.filter(([k]) => k !== '=').length === 0 ? <div style={{ padding: 8, color: T.muted }}>No line changed.</div>
            : diff.map(([k, l], i) => k === '=' || /^[\s|]*$/.test(l) ? null : <div key={i} style={{ padding: '1px 8px', whiteSpace: 'pre-wrap', wordBreak: 'break-word', background: k === '+' ? 'rgba(46,139,87,.12)' : 'rgba(192,57,43,.10)', color: k === '+' ? C.ok : C.bad }}>{k} {l}</div>)}
        </div>
        <div style={{ display: 'flex', gap: 8 }}><Btn onClick={() => decide(true)} style={{ flex: 1 }}>Accept</Btn><Btn primary={false} onClick={() => decide(false)} style={{ flex: 1 }}>Discard</Btn></div>
      </div>}
      <div style={{ marginTop: 'auto', fontSize: 11.5, color: T.faint, lineHeight: 1.45 }}>Ctrl/⌘ + Enter sends. The draft is saved on the server (two seconds after you stop typing) with every revision kept: open it from any device. A rebuild goes through the gate (pp_verify) and is registered as a new document.</div>
    </aside>
  </div>;
}

/** The canvas home: server drafts, and new drafts from a blank page, an upload, a job or a Library document. */
function Start({ busy, onOpen }: { busy: boolean; onOpen: (id: string) => void }) {
  const { api, flash } = useApp();
  const [drafts, setDrafts] = useState<CanvasDraft[] | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [docs, setDocs] = useState<DocumentRow[]>([]);
  const [dt, setDt] = useState<'ANNEX' | 'SOP'>('ANNEX');
  const [err, setErr] = useState('');
  const file = useRef<HTMLInputElement>(null);
  const load = () => {
    api.canvasList().then(setDrafts).catch((e: ApiError) => { setDrafts([]); setErr(`${e.status} · ${e.message}`); });
    api.jobs().then(j => setJobs(j.filter(x => !!x.result?.markdown).slice(0, 12))).catch(() => undefined);
    api.documents().then(d => setDocs(d.slice(0, 12))).catch(() => undefined);
  };
  useEffect(load, [api]); // eslint-disable-line react-hooks/exhaustive-deps
  const open = async (b: Parameters<typeof api.canvasOpen>[0]) => {
    try { const d = await api.canvasOpen(b); onOpen(d.id); } catch (e) { flash(`open → ${(e as ApiError).status || ''} ${(e as Error).message}`); }
  };
  const upload = async (f: File) => { const text = await f.text(); open({ source: 'upload', markdown: text, source_id: f.name.slice(0, 60) }); };
  const card = { background: T.surface, border: `1px solid ${T.hair}`, borderRadius: 8, padding: 14 } as const;
  const row = (key: string, title: string, sub: string, onClick: () => void, extra?: JSX.Element) =>
    <div key={key} className="pp-hover-row" onClick={onClick} {...press(onClick)} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '7px 8px', borderTop: `1px solid ${T.hair}`, cursor: 'pointer' }}>
      <div style={{ flex: 1, minWidth: 0 }}><div style={{ fontSize: 13, color: T.strong, fontWeight: 600 }}>{title}</div><div style={{ fontSize: 11.5, color: T.muted, fontFamily: MONO }}>{sub}</div></div>{extra}</div>;
  return <div style={{ flex: 1, overflow: 'auto', padding: 22, display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 1100 }}>
    <div><div style={{ fontFamily: DISPLAY, fontSize: 20, fontWeight: 700, color: T.strong }}>Canvas</div>
      <div style={{ color: T.secondary, fontSize: 13.5, lineHeight: 1.5 }}>Open a draft to read it side by side, edit any section, give the author instructions and rebuild it through the gate. Drafts are kept on the server, with their history.</div></div>
    {busy && <Banner kind="info">Opening…</Banner>}
    {err && <Banner kind="err">GET /canvas → {err}</Banner>}
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 14 }}>
      <div style={card}><b style={{ fontSize: 14 }}>New</b>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 10, flexWrap: 'wrap' }}>
          <Seg items={[['ANNEX', 'Annex / report'], ['SOP', 'SOP']]} value={dt} onPick={setDt} pad="4px 10px" />
          <Btn onClick={() => open({ source: 'blank', doctype: dt })}>Blank document</Btn>
          <Btn primary={false} onClick={() => file.current?.click()}>Upload .md</Btn>
          <input ref={file} type="file" accept=".md,.markdown,.txt" style={{ display: 'none' }} onChange={e => { const f = e.target.files?.[0]; if (f) upload(f); e.target.value = ''; }} />
        </div></div>
      <div style={card}><b style={{ fontSize: 14 }}>Saved drafts</b>
        {drafts === null ? <div style={{ color: T.muted, fontSize: 13, marginTop: 8 }}>loading…</div>
          : drafts.length === 0 ? <div style={{ color: T.muted, fontSize: 13, marginTop: 8 }}>None yet.</div>
          : drafts.map(d => row(d.id, `${d.code || 'untitled'} · ${d.doctype}`, `${d.source} · rev ${d.rev} · ${ago(d.updated_at)} ago${d.updated_by ? ' · ' + d.updated_by : ''}`, () => onOpen(d.id),
              <span onClick={async e => { e.stopPropagation(); if (confirm(`Delete the canvas draft ${d.code}? Its revisions go too; registered documents stay.`)) { await api.canvasDelete(d.id); load(); } }}
                style={{ color: T.faint, fontSize: 12, padding: '2px 6px' }} title="Delete draft">✕</span>))}</div>
      <div style={card}><b style={{ fontSize: 14 }}>From a job</b>
        {jobs.length === 0 ? <div style={{ color: T.muted, fontSize: 13, marginTop: 8 }}>No job with a draft.</div>
          : jobs.map(j => row(j.id, `${j.payload.meta.code} · ${j.payload.meta.title_en || j.payload.meta.title_mk || ''}`, `${j.status} · ${ago(j.created_at)} ago`, () => open({ source: 'job', source_id: j.id })))}</div>
      <div style={card}><b style={{ fontSize: 14 }}>From the Library</b>
        {docs.length === 0 ? <div style={{ color: T.muted, fontSize: 13, marginTop: 8 }}>No document.</div>
          : docs.map(d => row(d.id, `${d.code} v${d.version}`, `${d.doctype} · ${d.title_en || d.title_mk} · ${ago(d.created_at)} ago`, () => open({ source: 'document', source_id: d.id })))}</div>
    </div>
  </div>;
}

function SecItem({ on, onPick, label, sub }: { on: boolean; onPick: () => void; label: string; sub: string }) {
  return <div onClick={onPick} {...press(onPick)} aria-current={on || undefined} className="pp-hover-row"
    style={{ padding: '8px 10px', margin: '0 8px 2px', borderRadius: 6, cursor: 'pointer', background: on ? T.selected : 'transparent', border: `1px solid ${on ? T.focus : 'transparent'}` }}>
    <div style={{ fontSize: 13, color: on ? T.strong : T.text, fontWeight: on ? 700 : 400, lineHeight: 1.35 }}>{label}</div>
    <div style={{ fontFamily: MONO, fontSize: 10.5, color: T.muted }}>{sub}</div></div>;
}

/** A cell as it reads: 'MK~~EN' stacked, the English under the Macedonian. */
function Cell({ text, head }: { text: string; head?: boolean }) {
  const [mk, en] = text.split('~~');
  return <><div style={{ fontWeight: head ? 700 : 400 }}>{mk.trim()}</div>{en !== undefined && <div style={{ color: head ? 'rgba(255,255,255,.82)' : T.secondary, fontSize: 11.5 }}>{en.trim()}</div>}</>;
}

/** A [[TABLE]] or [[FORM]] block drawn as the document draws it: a table's first row is its navy header; a form row is
 *  'label MK ||| label EN ||| value', the value left blank for a person to fill in. */
function Block({ kind, rows }: { kind: 'TABLE' | 'FORM'; rows: string[] }) {
  // A row of pipes only is an empty entry row, whatever its pipe count.
  const cells = rows.map(r => /^[\s|]*$/.test(r) ? [] : r.split('|||').map(c => c.trim()));
  const width = Math.max(...cells.map(r => r.length));
  const entries = cells.length - 1;
  // A wide log (header + empty rows) cannot be read clipped: list its columns instead.
  if (kind === 'TABLE' && width > 7 && cells.slice(1).every(r => r.every(c => !c)))
    return <div style={{ border: `1px solid ${T.control}`, borderRadius: 6, overflow: 'hidden' }}>
      <div style={{ background: T.navy, color: T.onAccent, padding: '6px 10px', fontSize: 12.5, fontWeight: 700 }}>
        Log table · {width} columns · {entries} empty entry {entries === 1 ? 'row' : 'rows'}</div>
      {cells[0].map((c, j) => <div key={j} style={{ display: 'grid', gridTemplateColumns: '34px 1fr', borderTop: j ? `1px solid ${T.hair}` : undefined, fontSize: 12.5, lineHeight: 1.35 }}>
        <span style={{ padding: '6px 8px', color: T.faint, fontFamily: MONO, textAlign: 'right' }}>{j + 1}</span>
        <span style={{ padding: '6px 8px' }}><Cell text={c} /></span></div>)}
    </div>;
  return <div style={{ overflowX: 'auto', border: `1px solid ${T.control}`, borderRadius: 6 }}>
    <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 12.5, lineHeight: 1.35 }}><tbody>
      {cells.map((r, i) => {
        const head = kind === 'TABLE' && i === 0;
        if (kind === 'FORM' && r.length === 3) return <tr key={i}><td style={{ padding: '6px 8px', borderTop: `1px solid ${T.hair}`, width: '38%', background: T.surface }}><Cell text={`${r[0]}~~${r[1]}`} /></td><td style={{ padding: '6px 8px', borderTop: `1px solid ${T.hair}`, color: T.muted }}>{r[2] || '…'}</td></tr>;
        const row = r.every(c => !c) ? new Array<string>(width).fill('') : r;
        return <tr key={i}>{row.map((c, j) => <td key={j} style={{ padding: '6px 8px', verticalAlign: 'top', minWidth: 90, borderTop: i ? `1px solid ${T.hair}` : undefined, borderLeft: j ? `1px solid ${T.hair}` : undefined, background: head ? T.navy : undefined, color: head ? T.onAccent : T.text }}>{c ? <Cell text={c} head={head} /> : <span style={{ color: T.faint }}>&nbsp;</span>}</td>)}</tr>;
      })}
    </tbody></table></div>;
}

/** The section as it reads: headings, each 'MK ||| EN' line as two columns, tables and forms as tables. */
function ReadView({ text }: { text: string }) {
  const out: JSX.Element[] = [];
  const lines = text.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i];
    if (/^\s*\[\[LIMITS\]\]\s*$/.test(l)) {
      const rows: string[] = [];
      while (++i < lines.length && !/^\s*\[\[\/LIMITS\]\]/.test(lines[i])) if (lines[i].trim()) rows.push(lines[i]);
      out.push(<Limits key={i} rows={rows} />); continue;
    }
    const box = /^\s*\[\[BOX(?::\s*([0-9.]+))?\]\]/.exec(l);
    if (box) {
      const rows: string[] = [];
      while (++i < lines.length && !/^\s*\[\[\/BOX/.test(lines[i])) if (lines[i].trim()) rows.push(lines[i]);
      out.push(<div key={i} style={{ border: `1px dashed ${T.control}`, borderRadius: 6, padding: 8, minHeight: Number(box[1] || 4) * 14, fontSize: 12.5, color: T.secondary }}>{rows.map((r, k) => <div key={k}>{r.replace(/\|\|\|/g, ' · ')}</div>)}</div>);
      continue;
    }
    const fig = /^\s*\[\[FIGURE:([^|\]]+)/.exec(l);
    if (fig) { out.push(<div key={i} style={{ border: `1px solid ${T.hair}`, borderRadius: 6, padding: 10, fontSize: 12.5, color: T.muted, textAlign: 'center' }}>Figure · {fig[1].trim()}</div>); continue; }
    const open = /^\s*\[\[(TABLE|FORM)[^\]]*\]\]\s*$/.exec(l);
    if (open) {
      const kind = open[1] as 'TABLE' | 'FORM', rows: string[] = [];
      while (++i < lines.length && !/^\s*\[\[\/(TABLE|FORM)\]\]\s*$/.test(lines[i])) if (lines[i].trim()) rows.push(lines[i]);
      out.push(<Block key={i} kind={kind} rows={rows} />);
      continue;
    }
    if (!l.trim()) { out.push(<div key={i} style={{ height: 4 }} />); continue; }
    const h = /^(#{1,3})\s+(.*)$/.exec(l);
    if (h) { out.push(<div key={i} style={{ marginTop: h[1].length === 1 ? 12 : 6, padding: h[1].length === 1 ? '7px 12px' : '4px 0', borderRadius: 6, background: h[1].length === 1 ? T.navy : 'transparent', color: h[1].length === 1 ? T.onAccent : T.strong, fontWeight: 700, fontSize: h[1].length === 1 ? 14 : 13.5 }}>{h[2]}</div>); continue; }
    if (/^\s*(\[\[|\|)/.test(l)) { out.push(<div key={i} style={{ fontFamily: MONO, fontSize: 12, color: T.secondary, background: T.surface, borderRadius: 4, padding: '2px 8px', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{l}</div>); continue; }
    const b = bilingual(l);
    out.push(b ? <div key={i} className="pp-bi" style={{ fontSize: 13.5, lineHeight: 1.55 }}><span style={{ color: T.text }}>{b[0]}</span><span style={{ color: T.secondary }}>{b[1]}</span></div>
      : <div key={i} style={{ fontSize: 13.5, lineHeight: 1.55, color: T.text }}>{l}</div>);
  }
  return <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxWidth: 1100 }}>{out}</div>;
}

/** A [[LIMITS]] block as the engine draws it: each value with a bar against its limit (pp_limitbars.py). */
function Limits({ rows }: { rows: string[] }) {
  const cols = rows.filter(r => r.trim().startsWith('@col')).map(r => { const [lab, lim, sc] = r.trim().slice(4).split('|').map(x => x.trim()); return { lab, lim: /absent/i.test(lim || '') ? null : Number(lim), sc: sc || 'log' }; });
  const items = rows.filter(r => !r.trim().startsWith('@col'));
  const cell = (raw: string, c: typeof cols[number]) => {
    const v = limitValue(raw);
    if (v.kind === 'nr') return <span style={{ color: T.faint, fontStyle: 'italic', fontSize: 11.5 }}>not reported</span>;
    let frac = 0.04, col = '#2E9E5B';
    if (v.kind === 'det') { frac = 1; col = '#D0342C'; }
    else if (v.kind === 'num' && v.x !== null && c.lim) { const f = c.sc === 'linear' ? v.x / c.lim : Math.log10(Math.max(v.x, 1)) / Math.log10(c.lim); frac = Math.min(Math.max(f, 0.04), 1); col = v.x > c.lim ? '#D0342C' : f > 0.75 ? '#E0A100' : '#2E9E5B'; }
    return <><div style={{ fontWeight: 700, color: col === '#2E9E5B' ? T.text : col }}>{v.label}</div>
      <div style={{ height: 6, background: 'rgba(128,128,128,.18)', borderRadius: 3, marginTop: 2 }}><div style={{ width: `${frac * 100}%`, height: '100%', background: col, borderRadius: 3 }} /></div></>;
  };
  return <div style={{ overflowX: 'auto', border: `1px solid ${T.control}`, borderRadius: 6 }}><table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 12.5 }}><tbody>
    <tr>{['Test / laboratory', ...cols.map(c => c.lab)].map((h, j) => <td key={j} style={{ background: T.navy, color: T.onAccent, padding: '6px 8px', fontWeight: 700 }}><Cell text={h} head /></td>)}</tr>
    {items.map((r, i) => {
      const t = r.trim();
      if (t.startsWith('@group')) { const [a, b] = t.slice(6).split('~~'); return <tr key={i}><td colSpan={cols.length + 1} style={{ padding: '6px 8px', borderTop: `1px solid ${T.hair}`, fontWeight: 700 }}>{a.trim()} {b && <span style={{ color: '#C0392B', fontWeight: 400 }}>{b.trim()}</span>}</td></tr>; }
      const ext = t.startsWith('@ext'); const cs = (ext ? t.slice(4) : t).split('|||').map(x => x.trim());
      return <tr key={i} style={{ background: ext ? 'rgba(208,52,44,.06)' : undefined }}>
        <td style={{ padding: '6px 8px', borderTop: `1px solid ${T.hair}` }}><Cell text={cs[0]} /></td>
        {cols.map((c, j) => <td key={j} style={{ padding: '6px 8px', borderTop: `1px solid ${T.hair}`, minWidth: 90 }}>{cell(cs[j + 1] ?? '-', c)}</td>)}</tr>;
    })}
  </tbody></table></div>;
}
