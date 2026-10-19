// The right-hand detail of one library entry: register row, what is held, notes, engine jobs and the approved or
// work-in-progress text. Shared by the Shelves and the Packages views (19.10.2026), so both open the same pane.
import { useEffect, useState } from 'react';
import type { ReferenceDoc, ShelfEntry } from '../api/types';
import { useApp } from '../store/store';
import { Banner, Caps } from './ui';
import { MONO, T } from '../theme';

export function holds(e: ShelfEntry): string {
  const out: string[] = [];
  if (e.approved) out.push(`approved copy v${e.approved.version}${e.approved.ragflow_doc_id ? ' · DB3' : ''}`);
  if (e.wip.length) out.push(`${e.wip.length} draft${e.wip.length > 1 ? 's' : ''} (ACME)`);
  if (e.jobs.length) out.push(`${e.jobs.length} engine job${e.jobs.length > 1 ? 's' : ''}`);
  if (e.builds.length) out.push(`${e.builds.length} build${e.builds.length > 1 ? 's' : ''}`);
  return out.join(' · ') || 'register only';
}

export function EntryDetail({ sel }: { sel: ShelfEntry }) {
  const { api } = useApp();
  const [doc, setDoc] = useState<ReferenceDoc | null>(null);
  useEffect(() => {
    setDoc(null);
    const id = sel.approved?.id || sel.wip[0]?.id;
    if (id) api.reference(id).then(setDoc).catch(() => setDoc(null));
  }, [api, sel]);
  return <div style={{ width: 420, flex: 'none', borderLeft: `1px solid ${T.hair}`, background: T.pane, padding: 16, display: 'flex', flexDirection: 'column', gap: 10, fontSize: 13, overflow: 'auto' }}>
    <div><div style={{ fontFamily: MONO, fontSize: 13, fontWeight: 700, color: '#fff' }}>{sel.code}{sel.version && ` · v${sel.version}`}</div><div style={{ color: T.secondary }}>{sel.title_mk}{sel.title_mk && sel.title_en && ' | '}{sel.title_en}</div></div>
    <div style={{ display: 'grid', gridTemplateColumns: '84px 1fr', gap: '5px 8px', fontSize: 12 }}>
      <span style={{ color: T.muted }}>register</span><span>{sel.status || 'not registered'}{sel.effective_date && ` · since ${sel.effective_date}`}</span>
      <span style={{ color: T.muted }}>parent</span><span>{sel.parent || '—'}</span>
      <span style={{ color: T.muted }}>held</span><span>{holds(sel)}</span></div>
    {sel.notes.map(n => <Banner key={n} kind="warn">{n}</Banner>)}
    {sel.jobs.length > 0 && <><Caps>ENGINE JOBS</Caps>{sel.jobs.map(j => <div key={j.id} style={{ fontFamily: MONO, fontSize: 11.5, color: T.secondary }}>{j.id.slice(0, 8)} · {j.status} · {j.stage}</div>)}</>}
    {doc && <><Caps>{doc.kind === 'approved' ? 'APPROVED TEXT (WORD FILE)' : 'WORK IN PROGRESS (ACME_SOP)'} · {String(doc.source?.name || '')}</Caps>
      <pre style={{ whiteSpace: 'pre-wrap', fontFamily: MONO, fontSize: 11, color: T.secondary, background: T.surface, borderRadius: 6, padding: 10, maxHeight: 520, overflow: 'auto', margin: 0 }}>{doc.markdown.slice(0, 20000)}{doc.markdown.length > 20000 && '\n…'}</pre></>}
  </div>;
}
