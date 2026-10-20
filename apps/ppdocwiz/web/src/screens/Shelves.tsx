// Library shelves (Head of QC, 18.10.2026): every document code on one shelf — approved and in use, under revision,
// drafts, numbers only, retired — from the register, the approved copies (DB3), the ACME_SOP work in progress and
// what the engine itself built. A disagreement between them is shown as a note, never decided here.
import { useEffect, useState } from 'react';
import { ApiError, type LibraryShelves, type Shelf, type ShelfEntry } from '../api/types';
import { EntryDetail, holds } from '../components/EntryDetail';
import { Banner, Seg } from '../components/ui';
import { useApp } from '../store/store';
import { C, MONO, T } from '../theme';

const LABEL: Record<Shelf, string> = { approved: 'Approved · in use', revision: 'Under revision', drafts: 'Drafts in progress', numbers: 'Numbers only', retired: 'Superseded · withdrawn' };
const ORDER: Shelf[] = ['approved', 'revision', 'drafts', 'numbers', 'retired'];

export function Shelves() {
  const { api, dataRev } = useApp();
  const [lib, setLib] = useState<LibraryShelves | null>(null);
  const [err, setErr] = useState('');
  const [shelf, setShelf] = useState<Shelf>('approved');
  const [q, setQ] = useState('');
  const [sel, setSel] = useState<ShelfEntry | null>(null);
  useEffect(() => { api.library().then(l => { setLib(l); setErr(''); }).catch((e: ApiError) => setErr(`${e.status} · ${e.message}`)); }, [api, dataRev]);
  if (err) return <div style={{ flex: 1, padding: 22 }}><Banner kind="err">GET /library → {err}</Banner></div>;
  if (!lib) return <div style={{ flex: 1, padding: 22, color: T.muted }}>loading…</div>;
  const rows = lib.shelves[shelf].filter(e => !q || (e.code + ' ' + e.title_mk + ' ' + e.title_en).toLowerCase().includes(q.toLowerCase()));
  const cols = '130px minmax(0,1fr) 46px 150px minmax(0,220px)';
  return <>
    <div style={{ flex: 1, minWidth: 0, padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 12, overflow: 'auto' }}>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        <Seg items={ORDER.map(s => [s, `${LABEL[s]} · ${lib.counts[s]}`] as [Shelf, string])} value={shelf} onPick={s => { setShelf(s); setSel(null); }} size={12} pad="4px 10px" />
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="⌕ code or title" style={{ flex: 1, minWidth: 160, background: T.surface, border: `1px solid ${T.control}`, borderRadius: 6, padding: '7px 12px', fontFamily: MONO, fontSize: 12, color: T.strong, outline: 'none' }} />
      </div>
      <div className="pp-table" style={{ border: `1px solid ${T.hair}`, borderRadius: 8, overflow: 'hidden' }}>
        <div style={{ display: 'grid', gridTemplateColumns: cols, gap: 10, padding: '9px 14px', background: T.pane, fontSize: 11, color: T.muted, fontFamily: MONO }}><span>CODE</span><span>TITLE</span><span>VER</span><span>REGISTER</span><span>HELD</span></div>
        {rows.map(e => <div key={e.code} onClick={() => setSel(e)} className="pp-hover-row" style={{ display: 'grid', gridTemplateColumns: cols, gap: 10, padding: '10px 14px', borderTop: `1px solid ${T.hair}`, alignItems: 'center', cursor: 'pointer', background: e.code === sel?.code ? T.selected : 'transparent' }}>
          <b style={{ color: T.strong, fontFamily: MONO, fontSize: 12.5 }}>{e.code}</b>
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.title_mk || e.title_en}{e.title_mk && e.title_en && <span style={{ color: T.secondary }}> | {e.title_en}</span>}</span>
          <span>{e.version || '—'}</span>
          <span style={{ fontFamily: MONO, fontSize: 11.5, color: T.secondary }}>{e.status || 'not registered'}{e.notes.length > 0 && <span style={{ color: C.warn }}> · !</span>}</span>
          <span style={{ fontSize: 12, color: T.secondary, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{holds(e)}</span></div>)}
        {!rows.length && <div style={{ padding: 16, color: T.muted, fontSize: 12.5 }}>Nothing on this shelf{q ? ' matches' : ''}.</div>}
      </div>
      <div style={{ fontSize: 12, color: T.faint }}>A working copy for drafting, outside the QMS: QALI 001 and the signed originals stay the authority.</div>
    </div>
    {sel && <EntryDetail sel={sel} />}
  </>;
}
