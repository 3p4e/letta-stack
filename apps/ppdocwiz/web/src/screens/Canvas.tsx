// Document canvas (Head of QC, 20.10.2026: "the editing and interactive canvas after the initial generation … has no
// functions, is not interactive, cannot be edited, cannot input commands"). After a job has generated its draft the
// canvas holds the draft's Markdown: every section can be read side by side (MK | EN), edited by hand, or changed by an
// instruction to the author that wrote it (POST /workflows/{id}/revise, shown as a diff to accept or discard), and the
// result rebuilt through the engine's gate (POST /build) and shown as its PDF. The HEADERDATA block (code, version,
// titles) is never edited here. Edits are kept in this browser until rebuilt or reset.
import { useEffect, useMemo, useState } from 'react';
import type { ReviseResult } from '../api/client';
import { ApiError, type Job } from '../api/types';
import { EmptyState } from '../components/LiveViews';
import { Banner, Btn, Seg, press } from '../components/ui';
import { bilingual, columnChanges, headField, joinDraft, lineDiff, sectionTitle, splitDraft } from '../lib/draft';
import { usePrimary } from '../lib/usePrimary';
import { lineColor } from '../lib/verify';
import { useApp } from '../store/store';
import { C, DISPLAY, MONO, T } from '../theme';

const KEY = (jid: string) => `ppsuite.canvas.${jid}`;
const load = (jid: string) => { try { return localStorage.getItem(KEY(jid)); } catch { return null; } };
const save = (jid: string, md: string | null) => { try { md === null ? localStorage.removeItem(KEY(jid)) : localStorage.setItem(KEY(jid), md); } catch { /* storage blocked */ } };

// Instructions the Head of QC can start from; each fills the box, nothing is sent until "Send".
const QUICK = [
  'Make this section shorter and clearer; keep every requirement.',
  'Add a responsibilities table (role · responsibility).',
  'Tighten the English so it matches the Macedonian exactly.',
  'Use the house glossary terms (мострирање, мостра, во процес).',
  'Add the records this step produces, with their document codes.',
];

type Proposal = ReviseResult & { instruction: string; before: string };
type Built = { id: string | null; ok: boolean; verify: string; at: string };

export function Canvas() {
  const { api, canvasJob, go, flash } = useApp();
  const [job, setJob] = useState<Job | null>(null);
  const [err, setErr] = useState('');
  const [md, setMd] = useState('');          // the draft as the canvas holds it now
  const [base, setBase] = useState('');      // the draft as the engine generated it
  const [sel, setSel] = useState<number | null>(0);
  const [view, setView] = useState<'read' | 'edit' | 'pdf'>('read');
  const [cmd, setCmd] = useState('');
  const [busy, setBusy] = useState<'' | 'revise' | 'build'>('');
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [log, setLog] = useState<{ text: string; where: string; outcome: string }[]>([]);
  const [built, setBuilt] = useState<Built | null>(null);

  useEffect(() => {
    if (!canvasJob) return;
    let live = true;
    setJob(null); setErr(''); setProposal(null); setBuilt(null); setLog([]);
    api.job(canvasJob).then(j => {
      if (!live) return;
      const gen = String(j.result.markdown || '');
      setJob(j); setBase(gen); setMd(load(j.id) ?? gen); setSel(0);
      setView(j.result.document_id ? 'pdf' : 'read');
    }).catch((e: ApiError) => live && setErr(`${e.status} · ${e.message}`));
    return () => { live = false; };
  }, [api, canvasJob]);

  const draft = useMemo(() => splitDraft(md), [md]);
  const edited = md !== base;
  const code = headField(draft.head, 'code') || job?.payload.meta.code || 'document';
  const doctype = headField(draft.head, 'doctype') || job?.payload.meta.doctype || 'SOP';
  const target = sel === null ? draft.sections.join('\n\n') : draft.sections[sel] ?? '';
  const pdfId = built?.ok ? built.id : (!edited && job?.result.document_id ? String(job.result.document_id) : null);

  const setTarget = (text: string) => {
    const next = sel === null ? joinDraft(draft.head, splitDraft('\n' + text).sections) : joinDraft(draft.head, draft.sections.map((s, i) => i === sel ? text : s));
    setMd(next); save(job!.id, next === base ? null : next);
  };

  const send = async () => {
    if (!job || !cmd.trim() || busy) return;
    setBusy('revise'); setProposal(null);
    try {
      const r = await api.reviseJob(job.id, { instruction: cmd.trim(), markdown: md, section: sel });
      setProposal({ ...r, instruction: cmd.trim(), before: md });
    } catch (e) { flash(`revise → ${(e as ApiError).status || ''} ${(e as Error).message}`); }
    finally { setBusy(''); }
  };
  const decide = (accept: boolean) => {
    if (!proposal || !job) return;
    if (accept) { setMd(proposal.markdown); save(job.id, proposal.markdown === base ? null : proposal.markdown); setBuilt(null); setView('read'); }
    setLog(l => [{ text: proposal.instruction, where: proposal.section === null ? 'whole document' : proposal.title, outcome: accept ? 'accepted' : 'discarded' }, ...l]);
    if (accept) setCmd('');
    setProposal(null);
  };
  const rebuild = async () => {
    if (!job || busy) return;
    setBusy('build');
    const m = job.payload.meta;
    try {
      const r = await api.directBuild(md, code, { code, title_mk: headField(draft.head, 'mk_title') || m.title_mk, title_en: headField(draft.head, 'en_title') || m.title_en, version: headField(draft.head, 'version') || m.version || '01', doctype, source: 'canvas' });
      setBuilt({ id: r.document_id, ok: true, verify: r.verify, at: new Date().toLocaleTimeString() }); setView('pdf');
      flash(`${code} rebuilt · gate passed`);
    } catch (e) {
      const b = (e as ApiError).body as { detail?: { verify?: string }; verify?: string } | undefined;
      setBuilt({ id: null, ok: false, verify: b?.detail?.verify || b?.verify || String((e as Error).message), at: new Date().toLocaleTimeString() }); setView('pdf');
    } finally { setBusy(''); }
  };
  const reset = () => { if (!job) return; setMd(base); save(job.id, null); setBuilt(null); setProposal(null); flash('Back to the generated draft'); };
  usePrimary(busy === 'build' ? 'Building…' : 'Rebuild ▸', rebuild, !job || !md || !!busy);

  if (!canvasJob) return <EmptyState title="No document open in the canvas">
    Open a generated document from <b>Jobs</b> (“Open in canvas”). The canvas lets you read it side by side, edit any section, give the
    author an instruction, and rebuild it through the gate.
  </EmptyState>;
  if (err) return <div style={{ flex: 1, padding: 22 }}><Banner kind="err">GET /workflows/{canvasJob.slice(0, 8)}… → {err}</Banner></div>;
  if (!job) return <div style={{ flex: 1, padding: 22, color: T.muted }}>loading…</div>;
  if (!base) return <EmptyState title="This job has no draft yet">
    The draft appears once the job has passed generation. Status now: <b>{job.status}</b> · {job.stage || 'queued'}.
    <div style={{ marginTop: 12 }}><Btn primary={false} onClick={() => go('jobs', { jobSel: job.id })}>Back to the job</Btn></div>
  </EmptyState>;

  const diff = proposal ? lineDiff(proposal.section === null ? splitDraft(proposal.before).sections.join('\n\n') : splitDraft(proposal.before).sections[proposal.section] ?? '',
    proposal.section === null ? splitDraft(proposal.markdown).sections.join('\n\n') : splitDraft(proposal.markdown).sections[proposal.section] ?? '') : [];

  return <div className="pp-canvas">
    {/* Sections */}
    <aside className="pp-canvas-sections" style={{ background: T.pane, borderRight: `1px solid ${T.hair}` }}>
      <div style={{ padding: '14px 12px 8px' }}>
        <div style={{ fontFamily: DISPLAY, fontWeight: 700, color: T.strong, fontSize: 15 }}>{code}</div>
        <div style={{ fontSize: 12, color: T.secondary, lineHeight: 1.4 }}>{job.payload.meta.title_mk} | {job.payload.meta.title_en}</div>
        <div style={{ fontFamily: MONO, fontSize: 11, color: T.muted, marginTop: 4 }}>{doctype} · v{headField(draft.head, 'version') || '—'} · {edited ? <span style={{ color: C.warn }}>edited</span> : 'as generated'}</div>
      </div>
      <div className="pp-canvas-seclist">
        <SecItem on={sel === null} onPick={() => setSel(null)} label="Whole document" sub={`${draft.sections.length} section${draft.sections.length === 1 ? "" : "s"}`} />
        {draft.sections.map((s, i) => <SecItem key={i} on={sel === i} onPick={() => setSel(i)} label={sectionTitle(s)} sub={`${s.split('\n').length} lines`} />)}
      </div>
    </aside>

    {/* Document */}
    <section className="pp-canvas-doc" style={{ background: T.deep }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderBottom: `1px solid ${T.hair}`, flexWrap: 'wrap' }}>
        <Seg items={[['read', 'Read'], ['edit', 'Edit'], ['pdf', 'PDF']]} value={view} onPick={setView} pad="5px 14px" />
        <span style={{ fontSize: 12.5, color: T.muted, flex: 1, minWidth: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{sel === null ? 'Whole document' : sectionTitle(draft.sections[sel] || '')}</span>
        <span style={{ marginLeft: 'auto', display: 'flex', gap: 8, flex: 'none' }}>
          {edited && <Btn primary={false} onClick={reset} style={{ padding: '5px 10px', fontSize: 12.5 }}>Reset to generated</Btn>}
          <Btn onClick={rebuild} disabled={!!busy} style={{ padding: '5px 12px', fontSize: 12.5 }}>{busy === 'build' ? 'Building…' : 'Rebuild'}</Btn>
        </span>
      </div>
      <div style={{ flex: 1, minHeight: 0, overflow: 'auto', padding: view === 'pdf' ? 0 : '16px 18px' }}>
        {view === 'read' && <ReadView text={target} />}
        {view === 'edit' && <textarea aria-label="Section Markdown" value={target} onChange={e => setTarget(e.target.value)} spellCheck={false}
          style={{ width: '100%', minHeight: '60vh', height: '100%', background: T.surface, border: `1px solid ${T.control}`, borderRadius: 8, padding: 14, color: T.text, fontFamily: MONO, fontSize: 13, lineHeight: 1.7, resize: 'vertical', outline: 'none' }} />}
        {view === 'pdf' && (built && !built.ok
          ? <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
              <Banner kind="err">Rebuild at {built.at} was <b>rejected by the gate</b> and not saved. Fix the lines marked below and rebuild.</Banner>
              <div style={{ background: T.surface, border: `1px solid ${T.hair}`, borderRadius: 8, padding: 12, fontFamily: MONO, fontSize: 12, lineHeight: 1.7 }}>{built.verify.split('\n').map((l, i) => <div key={i} style={{ whiteSpace: 'pre-wrap', color: lineColor(l) }}>{l}</div>)}</div>
            </div>
          : pdfId && api.mode === 'mock'
            ? <div style={{ padding: 18 }}><Banner kind="info">Sample mode: the gate passed and the document was registered. On the live engine the rendered PDF opens here.</Banner></div>
          : pdfId
            ? <iframe title="document PDF" src={api.documentHref(pdfId, 'pdf') + '?inline=1'} style={{ width: '100%', height: '100%', minHeight: '70vh', border: 0, background: '#fff' }} />
            : <div style={{ padding: 18, color: T.secondary, lineHeight: 1.5 }}>{edited ? 'The draft has changed since it was built. Rebuild to see the PDF of this version.' : 'No PDF yet: this job has not registered a document. Rebuild to make one from the draft.'}
                <div style={{ marginTop: 10 }}><Btn onClick={rebuild} disabled={!!busy}>{busy === 'build' ? 'Building…' : 'Rebuild now'}</Btn></div></div>)}
      </div>
      {built?.ok && view === 'pdf' && <div style={{ padding: '8px 14px', borderTop: `1px solid ${T.hair}`, fontSize: 12.5, display: 'flex', gap: 12, flexWrap: 'wrap', color: T.secondary }}>
        <span style={{ color: C.ok, fontWeight: 700 }}>✓ gate passed {built.at}</span>
        {built.id && <><a href={api.documentHref(built.id, 'download')}>.docx</a><a href={api.documentHref(built.id, 'pdf')}>.pdf</a></>}
        <span style={{ marginLeft: 'auto', fontFamily: MONO, fontSize: 11.5, color: T.muted }}>registered as a new document · Library</span></div>}
    </section>

    {/* Commands */}
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

      {log.length > 0 && <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 4 }}>
        <div style={{ fontFamily: MONO, fontSize: 10.5, letterSpacing: '.1em', color: T.faint }}>INSTRUCTIONS THIS SESSION</div>
        {log.map((h, i) => <div key={i} style={{ fontSize: 12, color: T.secondary, borderTop: `1px solid ${T.hair}`, paddingTop: 4 }}>
          <span style={{ color: h.outcome === 'accepted' ? C.ok : T.muted, fontFamily: MONO, fontSize: 11 }}>{h.outcome}</span> · {h.where}<div style={{ color: T.text }}>{h.text}</div></div>)}
      </div>}
      <div style={{ marginTop: 'auto', fontSize: 11.5, color: T.faint, lineHeight: 1.45 }}>Ctrl/⌘ + Enter sends. Edits stay in this browser until you rebuild or reset. A rebuild goes through the same gate (pp_verify) and is registered as a new document.</div>
    </aside>
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
