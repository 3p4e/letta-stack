// Library · Packages (Head of QC, 19.10.2026): every SOP with the documents that belong to it — approved and in use
// apart from drafts in progress — and, per group, the documents under no SOP by family. The grouping is DocEngine's
// (GET /library packages / loose); this screen only lists it and opens the same detail pane as the Shelves.
import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { ApiError, type LibraryPackage, type LibraryShelves, type Relation, type ShelfEntry } from '../api/types';
import { EntryDetail } from '../components/EntryDetail';
import { Banner, Caps, Tag, press } from '../components/ui';
import { byFamily, filterLoose, filterPackages, openByDefault } from '../lib/packages';
import { RELATION_LABEL } from '../lib/related';
import { useApp } from '../store/store';
import { C, MONO, T } from '../theme';

const REL_C: Record<Relation, string> = { annex: C.run, child: C.ok, listed: C.warn };
const GROUPS: ['in_use' | 'drafts', string][] = [['in_use', 'Approved · in use'], ['drafts', 'Drafts · work in progress']];
const cols = '150px minmax(0,1fr) 40px 150px 110px';
const title = (e: ShelfEntry) => <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.title_mk || e.title_en}{e.title_mk && e.title_en && <span style={{ color: T.secondary }}> | {e.title_en}</span>}</span>;

export function Packages() {
  const { api, dataRev } = useApp();
  const [lib, setLib] = useState<LibraryShelves | null>(null);
  const [err, setErr] = useState('');
  const [q, setQ] = useState('');
  const [sel, setSel] = useState<ShelfEntry | null>(null);
  // Open state per SOP code: unset means the group's default (≤ 8 packages open), a search opens its matches.
  const [open, setOpen] = useState<Record<string, boolean>>({});
  useEffect(() => { api.library().then(l => { setLib(l); setErr(''); }).catch((e: ApiError) => setErr(`${e.status} · ${e.message}`)); }, [api, dataRev]);
  const view = useMemo(() => lib && GROUPS.map(([g, label]) => ({ g, label, all: lib.packages?.[g] || [], ...filterPackages(lib.packages?.[g] || [], q), loose: filterLoose(lib.loose?.[g] || [], q) })), [lib, q]);
  if (err) return <div style={{ flex: 1, padding: 22 }}><Banner kind="err">GET /library → {err}</Banner></div>;
  if (!lib || !view) return <div style={{ flex: 1, padding: 22, color: T.muted }}>loading…</div>;
  const isOpen = (p: LibraryPackage, group: { all: LibraryPackage[]; opened: string[] }) => open[p.sop.code] ?? (group.opened.includes(p.sop.code) || openByDefault(group.all.length));
  const row = (e: ShelfEntry, extra: ReactNode, indent = 0, bold = false) => <div key={e.code} onClick={() => setSel(e)} {...press(() => setSel(e))} className="pp-hover-row"
    style={{ display: 'grid', gridTemplateColumns: cols, gap: 10, padding: `8px 14px 8px ${14 + indent}px`, borderTop: `1px solid ${T.hair}`, alignItems: 'center', cursor: 'pointer', fontSize: 12.5, background: e.code === sel?.code ? T.selected : 'transparent' }}>
    <b style={{ color: bold ? '#fff' : T.text, fontFamily: MONO, fontSize: 12.5, fontWeight: bold ? 700 : 400 }}>{e.code}</b>
    {title(e)}<span>{e.version || '—'}</span>
    <span style={{ fontFamily: MONO, fontSize: 11.5, color: T.secondary }}>{e.status || 'not registered'}{e.notes.length > 0 && <span style={{ color: C.warn }}> · !</span>}</span>
    {extra}</div>;
  return <>
    <div style={{ flex: 1, minWidth: 0, padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 14, overflow: 'auto' }}>
      <input value={q} onChange={e => setQ(e.target.value)} placeholder="⌕ code or title — SOPs, their documents and the loose ones" style={{ background: T.surface, border: `1px solid ${T.control}`, borderRadius: 6, padding: '7px 12px', fontFamily: MONO, fontSize: 12, color: '#fff', outline: 'none' }} />
      {view.map(group => <div key={group.g} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <Caps>{group.label.toUpperCase()} · {group.kept.length} {group.kept.length === 1 ? 'PACKAGE' : 'PACKAGES'} · {group.kept.reduce((n, p) => n + p.members.length, 0)} UNDER THEM · {group.loose.length} LOOSE</Caps>
        <div style={{ border: `1px solid ${T.hair}`, borderRadius: 8, overflow: 'hidden' }}>
          <div style={{ display: 'grid', gridTemplateColumns: cols, gap: 10, padding: '9px 14px', background: T.pane, fontSize: 11, color: T.muted, fontFamily: MONO }}><span>CODE</span><span>TITLE · MK | EN</span><span>VER</span><span>REGISTER</span><span /></div>
          {group.kept.map(p => {
            const o = isOpen(p, group), toggle = () => setOpen(s => ({ ...s, [p.sop.code]: !o }));
            return <div key={p.sop.code}>
              {row(p.sop, <span style={{ display: 'flex', gap: 8, alignItems: 'center', justifyContent: 'flex-end' }}>
                <span style={{ fontSize: 11.5, color: T.muted }}>{p.members.length} {p.members.length === 1 ? 'document' : 'documents'}</span>
                <span onClick={e => { e.stopPropagation(); toggle(); }} {...press(toggle)} aria-expanded={o} aria-label={`${o ? 'collapse' : 'expand'} ${p.sop.code}`} style={{ cursor: 'pointer', color: T.secondary, width: 16, textAlign: 'center' }}>{o ? '▾' : '▸'}</span></span>, 0, true)}
              {o && p.members.map(m => row(m, <span style={{ textAlign: 'right' }}><Tag c={REL_C[m.relation]}>{RELATION_LABEL[m.relation]}</Tag></span>, 22))}
              {o && !p.members.length && <div style={{ padding: '6px 14px 8px 36px', borderTop: `1px solid ${T.hair}`, fontSize: 12, color: T.faint }}>no document under this SOP</div>}
            </div>;
          })}
          {!group.kept.length && <div style={{ padding: 14, color: T.muted, fontSize: 12.5 }}>No package{q ? ' matches' : ''}.</div>}
        </div>
        {group.loose.length > 0 && <>
          <Caps style={{ marginTop: 4 }}>NOT UNDER AN SOP · {group.loose.length}</Caps>
          <div style={{ border: `1px solid ${T.hair}`, borderRadius: 8, overflow: 'hidden' }}>
            {byFamily(group.loose).map(([fam, es]) => <div key={fam}>
              <div style={{ padding: '7px 14px', background: T.pane, fontFamily: MONO, fontSize: 11, color: T.muted }}>{fam} · {es.length}</div>
              {es.map(e => row(e, <span />, 22))}
            </div>)}
          </div></>}
      </div>)}
      <div style={{ fontSize: 12, color: T.faint }}>An SOP is in use when the library holds its approved copy or the register has it effective. annex = numbered under the SOP (…A01); child = the register names the SOP as parent; listed = the approved SOP's own text names the document.</div>
    </div>
    {sel && <EntryDetail sel={sel} />}
  </>;
}
