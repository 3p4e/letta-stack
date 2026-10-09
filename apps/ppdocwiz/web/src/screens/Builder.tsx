// Builder (handoff §1) + the wizard block editor (COVERAGE #2) + SOP/annex lifecycle (COVERAGE #4).
import { useMemo, useState } from 'react';
import type { Block, Cell, DocStatus, Section, WizardPayload } from '../api/types';
import { ApiError } from '../api/types';
import { PPPage, type AnchorMap, type Highlight } from '../components/PPPage';
import { Avatar, Banner, Btn, Caps, CodeView, Input, PaneHead, Seg, Sep, spread, stamp, StampRail, Tag } from '../components/ui';
import { TERMS } from '../data/samples';
import { composeLines, composeMarkdown, lint, type Lint } from '../lib/compose';
import { usePrimary } from '../lib/usePrimary';
import { useApp } from '../store/store';
import { C, MONO, T } from '../theme';
import { headerMeta } from '../lib/docparse';

const clone = <X,>(x: X): X => structuredClone(x);
const short = (t: string) => t.split(/\s[—–-]\s/)[0];
const blockTag = (b: Block) => b.type.toUpperCase();

/** Locate a lint's cell and return the terminology suggestion for its EN half, if the glossary knows it. */
function suggestion(p: WizardPayload, l: Lint): { mk: string; en: string } | null {
  const s = p.sections[l.section]; if (!s) return null;
  const b = s.blocks[l.block];
  let mk = '';
  if (!b) mk = s.mk;
  else if (b.type === 'table') mk = (l.row < 0 ? b.cols[l.col ?? 0] : b.rows[l.row]?.[l.col ?? 0])?.mk || '';
  else if (b.type === 'form') mk = b.rows[l.row]?.label_mk || '';
  else mk = b.paras[l.row]?.mk || '';
  const en = TERMS[mk.trim()];
  return en ? { mk, en } : null;
}
function applyEn(p: WizardPayload, l: Lint, en: string): WizardPayload {
  const q = clone(p), s = q.sections[l.section], b = s.blocks[l.block];
  if (!b) s.en = en;
  else if (b.type === 'table') { const c = l.row < 0 ? b.cols[l.col ?? 0] : b.rows[l.row][l.col ?? 0]; c.en = en; }
  else if (b.type === 'form') b.rows[l.row].label_en = en;
  else b.paras[l.row].en = en;
  return q;
}

/** Parse an anchor like s1b0r2 / s1b0h / s1t. */
const parseAnchor = (a: string) => { const m = /^s(\d+)(?:b(\d+)(?:r(\d+)|(h))?)?/.exec(a); return m ? { s: +m[1], b: m[2] !== undefined ? +m[2] : -1, r: m[3] !== undefined ? +m[3] : m[4] ? -1 : -2 } : null; };

export function Builder() {
  const { bdoc: doc, bdocIsSample, builderMode: mode, hlLine, set, api, run, flash } = useApp();
  const setDoc = (d: WizardPayload) => set({ bdoc: d });
  const [sel, setSel] = useState(0);
  const [dismissed, setDismissed] = useState<number[]>([]);
  const [cellA, setCellA] = useState<string | null>(null);
  const [anchors, setAnchors] = useState<AnchorMap>({});
  const [raw, setRaw] = useState<string | null>(null);
  const [result, setResult] = useState<{ ok: boolean; verify: string; docx?: string; pdf?: string; err?: string } | null>(null);

  const lines = useMemo(() => composeLines(doc), [doc]);
  const lints = useMemo(() => lint(doc), [doc]);
  const firstLint = lints.find(l => !dismissed.includes(l.line));
  const sug = firstLint ? suggestion(doc, firstLint) : null;
  const marks = Object.fromEntries(lints.filter(l => !dismissed.includes(l.line)).map(l => [l.line, { msg: l.msg, c: l.level === 'bad' ? C.bad : C.warn }]));
  const enWarn = lints.filter(l => l.msg.startsWith('EN') || l.msg.startsWith('heading'));
  const blanks = doc.sections.reduce((n, s) => n + s.blocks.reduce((m, b) => m + (b.type === 'form' ? b.rows.filter(r => !r.value || r.value === '_').length : b.type === 'table' ? b.rows.reduce((k, r) => k + r.filter(c => !c.mk && !c.en).length, 0) : 0), 0), 0);
  const isEmptySkeleton = !bdocIsSample && doc.sections.every(s => s.blocks.every(b => (b.type === 'text' && b.paras.every(p => !p.mk && !p.en)) || (b.type === 'form' && b.rows.every(r => !r.label_mk))));
  const lintText = raw !== null ? '○ raw Markdown · POST /build' : lints.some(l => l.level === 'bad') ? '✗ ' + lints[0].msg : isEmptySkeleton ? '○ new draft' : enWarn.length ? `! ${enWarn.length} lint · ${enWarn[0].msg} (line ${enWarn[0].line})` : '✓ dry-run clean · MK ||| EN paired';
  const lintColor = raw !== null || isEmptySkeleton ? T.secondary : lints.some(l => l.level === 'bad') ? C.bad : enWarn.length ? C.warn : C.ok;

  // outline: HEADERDATA card + one per section; picking highlights its source line
  const lineOfSection = (si: number) => 1 + lines.findIndex(l => l.ref.section === si && l.ref.block === undefined);
  const outline = [{ tag: 'HEADERDATA', mk: doc.code || '…', en: `v${doc.version} · ${doc.doctype} · ${bdocIsSample ? 'parent ' + (doc.parent || '—') : 'new draft'}`, line: 1 },
    ...doc.sections.map((s, si) => {
      const sl = lints.filter(l => l.section === si);
      const kinds = [...new Set(s.blocks.map(blockTag))].join(' · ');
      return { tag: '#'.repeat(s.level) + ' ' + s.num + (kinds ? ' · ' + kinds : ''), mk: `${s.num} ${s.mk}`, en: (s.en || '…') + (sl.length ? ` · ! ${sl.length} EN half missing` : s.blocks.length ? '' : ' · empty'), line: lineOfSection(si) }; })];
  const hl = hlLine === 1 ? lines.map((l, i) => l.ref.header ? i + 1 : 0).filter(Boolean) : hlLine ? [hlLine] : [];

  // page highlights + stamps from measured anchors
  const lintAnchor = (l: Lint) => l.block < 0 ? `s${l.section}t` : `s${l.section}b${l.block}${l.row < 0 ? 'h' : 'r' + l.row}`;
  const highlights: Highlight[] = [
    ...(cellA && mode === 'page' ? [{ anchor: cellA, kind: 'sel' as const }] : []),
    ...enWarn.map(l => ({ anchor: lintAnchor(l), kind: 'warn' as const })),
  ];
  const mkStamps = (k: number, gap: number) => spread([
    stamp('FONT FLOOR', 'min 7 pt ≥ 6 pt', 'ok', ((anchors.header?.top ?? 0)) * k, '-2deg'),
    stamp('BLANK BY DESIGN', `${blanks} value${blanks === 1 ? '' : 's'} for the operator`, 'run', (anchors.s0?.top ?? 118) * k, '1.5deg'),
    enWarn.length ? stamp('BILINGUAL', enWarn[0].block < 0 ? `section ${enWarn[0].section + 1} heading · EN missing` : `table ${enWarn[0].section + 1} row ${enWarn[0].row + 1} · EN missing`, 'warn', (anchors[lintAnchor(enWarn[0])]?.top ?? 205) * k, '-1deg')
      : stamp('BILINGUAL', isEmptySkeleton ? 'checked on build' : 'every run paired', isEmptySkeleton ? 'run' : 'ok', (anchors.s1?.top ?? 205) * k, '-1deg'),
    stamp('GLYPHS', 'ѓ ќ ѕ covered', 'ok', ((anchors[`s${doc.sections.length - 1}`]?.top ?? 300)) * k, '1deg'),
  ], gap);

  const remember = (code: string, r: { ok: boolean; verify: string; docx?: string; pdf?: string }) =>
    set({ lastBuild: { code: code || 'document', ...r, at: new Date().toLocaleTimeString() } });
  const build = async () => {
    setResult(null);
    const code = (raw !== null && headerMeta(raw).code) || doc.code || 'document';
    const ok = await run(code, async () => {
      try {
        // Source view: same engine as the wizard path (ppdocwiz POST /api/build); the pasted HEADERDATA names the file.
        const r = raw !== null ? await api.rawBuild(raw, code) : await api.build(doc);
        const res = { ok: r.ok, verify: r.verify, docx: r.ok ? api.downloadHref(r.doc_id, 'docx') : undefined, pdf: r.ok ? api.downloadHref(r.doc_id, 'pdf') : undefined };
        setResult(res); remember(code, res);
        return { ok: r.ok, failAt: 2, msg: r.ok ? undefined : 'RESULT: FAIL · gate' };
      } catch (e) {
        const er = e as ApiError, body = er.body as { verify?: string; detail?: { verify?: string } } | undefined;
        const verify = body?.verify || body?.detail?.verify || '';
        setResult({ ok: false, verify, err: `${er.status || ''} · ${er.message}` }); remember(code, { ok: false, verify });
        return { ok: false, failAt: er.status === 422 ? 2 : 1, msg: `RESULT: FAIL · ${er.status || 'error'}` };
      }
    });
    if (ok) flash(`${code} built · RESULT: PASS`);
  };
  usePrimary('Build ▸', build);

  const pick = (i: number, line: number) => { setSel(i); set({ hlLine: i === 0 ? 1 : line }); };

  return <>
    {/* outline */}
    <div style={{ width: 208, flex: 'none', borderRight: `1px solid ${T.hair}`, background: T.pane, padding: '14px 10px', display: 'flex', flexDirection: 'column', gap: 6, overflow: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', padding: '0 4px 6px' }}><b style={{ color: '#fff' }}>Outline</b><span style={{ fontSize: 12, color: T.muted }}>{doc.doctype === 'SOP' ? 'SOP' : 'Annex'} · A4 {doc.orient}</span></div>
      {outline.map((o, i) => <div key={i} onClick={() => pick(i, o.line)} style={{ padding: '8px 10px', borderRadius: 6, cursor: 'pointer', background: sel === i ? T.selected : T.surface, border: `1px solid ${sel === i ? T.focus : T.control}` }}>
        <div style={{ fontSize: 11, color: T.muted, fontFamily: MONO }}>{o.tag}</div><div style={{ fontWeight: 700, color: '#fff' }}>{o.mk}</div><div style={{ fontSize: 12, color: o.en.includes('!') ? C.warn : T.secondary }}>{o.en}</div></div>)}
      <div onClick={() => { const q = clone(doc); q.sections.push({ num: String(q.sections.length + 1), mk: '', en: '', level: doc.doctype === 'SOP' ? 2 : 1, blocks: [{ type: 'text', paras: [{ mk: '', en: '' }] }] }); setDoc(q); set({ builderMode: 'blocks' }); }} style={{ padding: '8px 10px', borderRadius: 6, border: `1px dashed ${T.control}`, color: T.muted, textAlign: 'center', cursor: 'pointer' }}>＋ Section</div>
      <MetaBox doc={doc} setDoc={setDoc} />
    </div>

    {/* work pane */}
    <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
      <div style={{ height: 42, flex: 'none', display: 'flex', alignItems: 'center', gap: 10, padding: '0 14px', borderBottom: `1px solid ${T.hair}` }}>
        <Seg items={[['src', 'Source · Markdown'], ['page', 'Page · edit on A4'], ['blocks', 'Blocks · wizard']]} value={mode} onPick={m => set({ builderMode: m })} />
        <span style={{ fontFamily: MONO, fontSize: 12, color: T.muted, whiteSpace: 'nowrap' }}>{doc.code || 'untitled'}.md</span><Tag>wizard · no LLM</Tag>
        <span style={{ marginLeft: 'auto', fontSize: 12, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', color: lintColor }}>{lintText}</span>
      </div>
      {result && <div style={{ margin: '10px 14px 0' }}><Banner kind={result.ok ? 'ok' : 'err'}>
        {result.ok ? <>Gate passed · {result.docx ? <><a href={result.docx}>.docx</a> · <a href={result.pdf}>.pdf</a></> : 'registered via POST /build'}</> : <>Rejected and not saved · {result.err || 'RESULT: FAIL'}</>}
        {result.verify && <pre style={{ margin: '6px 0 0', fontFamily: MONO, fontSize: 11, whiteSpace: 'pre-wrap', color: 'inherit' }}>{result.verify.split('\n').slice(-3).join('\n')}</pre>}
        <span onClick={() => setResult(null)} style={{ float: 'right', cursor: 'pointer', marginTop: -18 }}>×</span></Banner></div>}

      {mode === 'src' && <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', padding: '12px 14px', gap: 12 }}>
        {raw === null
          ? <CodeView lines={lines.map(l => l.text)} hl={hl} marks={marks} style={{ flex: 1, minHeight: 0 }} />
          : <textarea value={raw} onChange={e => setRaw(e.target.value)} spellCheck={false} style={{ flex: 1, minHeight: 0, background: T.surface, border: `1px solid ${T.focus}`, borderRadius: 6, padding: 12, color: T.text, fontFamily: MONO, fontSize: 12.5, lineHeight: 1.75, resize: 'none', outline: 'none' }} />}
        <div style={{ display: 'flex', gap: 10, fontSize: 12, color: T.muted, alignItems: 'center' }}>
          {raw === null ? <span onClick={() => setRaw(composeMarkdown(doc))} style={{ color: C.run, cursor: 'pointer' }}>Edit raw Markdown</span>
            : <><span onClick={() => setRaw(null)} style={{ color: C.run, cursor: 'pointer' }}>Discard raw edits, back to blocks</span><span>Raw Markdown builds with the same engine as the wizard (POST /api/build); the wizard payload is left as it was.</span></>}
        </div>
        {raw === null && firstLint && sug && <div style={{ flex: 'none', background: T.surface, border: `1px solid ${T.control}`, borderRadius: 8, padding: '12px 14px', display: 'flex', gap: 14, alignItems: 'center' }}>
          <Avatar />
          <div style={{ flex: 1, minWidth: 0 }}><div style={{ fontFamily: MONO, fontSize: 11.5, color: T.muted }}>{api.mode === 'mock' ? 'gf_annex_author' : 'glossary'} · suggestion · line {firstLint.line}</div>
            <div style={{ marginTop: 2 }}>Fill the missing EN half: <span style={{ fontFamily: MONO, color: C.warn }}>~~</span><b style={{ color: '#fff' }}>{sug.en}</b> (term from DB3_PP_CURRENT_unified)</div></div>
          <Btn onClick={() => setDoc(applyEn(doc, firstLint, sug.en))} style={{ padding: '7px 14px' }}>Accept</Btn>
          <span onClick={() => setDismissed([...dismissed, firstLint.line])} style={{ color: T.muted, fontSize: 13, cursor: 'pointer' }}>Dismiss</span>
        </div>}
      </div>}

      {mode === 'page' && <PageEdit doc={doc} setDoc={setDoc} cellA={cellA} setCellA={setCellA} highlights={highlights} stamps={mkStamps(.6, 64)} onLayout={setAnchors} />}
      {mode === 'blocks' && <BlockEditor doc={doc} setDoc={setDoc} lints={lints} />}
    </div>

    {mode !== 'page' && <div style={{ width: 400, flex: 'none', borderLeft: `1px solid ${T.hair}`, background: T.deep, display: 'flex', flexDirection: 'column' }}>
      <PaneHead title="Live page" right={`Page 1 / 1 · 34 %`} />
      <div style={{ flex: 1, position: 'relative', padding: '16px 0 0 14px', overflow: 'hidden' }}>
        <div style={{ position: 'relative', width: 270 }}>
          <PPPage doc={doc} zoom={.34} highlights={highlights.filter(h => h.kind !== 'sel')} onLayout={setAnchors} onPick={a => { const p = parseAnchor(a); if (p) { const ln = 1 + lines.findIndex(l => l.ref.section === p.s && (p.b < 0 || l.ref.block === p.b) && (p.r < -1 || l.ref.row === p.r)); set({ hlLine: ln, builderMode: 'src' }); } else if (a === 'header' || a === 'title') set({ hlLine: 1 }); }} />
          <StampRail stamps={mkStamps(.34, 58)} width={120} />
        </div>
      </div>
    </div>}
  </>;
}

function MetaBox({ doc, setDoc }: { doc: WizardPayload; setDoc: (d: WizardPayload) => void }) {
  const st = doc.status;
  const up = (p: Partial<WizardPayload>) => setDoc({ ...doc, ...p });
  const lab = { color: T.muted } as const;
  return <div style={{ marginTop: 'auto', background: T.surface, border: `1px solid ${T.control}`, borderRadius: 6, padding: 10, display: 'grid', gridTemplateColumns: '56px 1fr', gap: '6px 8px', fontSize: 12.5 }}>
    <span style={lab}>Code</span><b style={{ color: '#fff', wordBreak: 'break-all' }}>{doc.code}</b>
    <span style={lab}>Ver.</span><span>{doc.version} · {st.replace('_', ' ')}</span>
    <span style={lab}>Parent</span><span>{doc.parent || '—'}</span>
    <span style={lab}>Supers.</span><span>{doc.supersedes || '—'}</span>
    <span style={lab}>Orient</span><span>{doc.orient}</span>
    <span style={lab}>Title</span><span>{short(doc.mk_title)} <span style={{ fontFamily: MONO, fontSize: 10.5, color: C.warn }}>|||</span> {short(doc.en_title)}</span>
    <span style={lab}>Status</span>
    <select value={st} onChange={e => up({ status: e.target.value as DocStatus })} style={{ fontSize: 12, padding: '2px 4px' }}><option value="draft">draft</option><option value="in_review">in review</option><option value="approved">approved</option></select>
    {st === 'approved' && <><span style={lab}>Effect.</span><Input value={doc.effective_date} onChange={v => up({ effective_date: v })} placeholder="dd.mm.yyyy" style={{ padding: '3px 6px', fontSize: 12 }} />
      <span style={lab}>Review</span><Input value={doc.review_date} onChange={v => up({ review_date: v })} placeholder="dd.mm.yyyy" style={{ padding: '3px 6px', fontSize: 12 }} /></>}
    <span style={{ gridColumn: '1 / -1', fontSize: 11, color: st === 'approved' ? C.ok : C.warn, lineHeight: 1.35 }}>{st === 'approved' ? 'Controlled version and effective date print on the title block.' : 'Marked NOT FOR USE · header shows ' + (st === 'draft' ? 'DRAFT' : 'IN REVIEW') + ' · no effective date'}</span>
  </div>;
}

// ---------------- Page · edit on A4 ----------------
function cellText(doc: WizardPayload, a: string): string | null {
  const p = parseAnchor(a); if (!p || p.b < 0) return null;
  const b = doc.sections[p.s]?.blocks[p.b]; if (!b) return null;
  if (b.type === 'form' && p.r >= 0) { const r = b.rows[p.r]; return `${r.label_mk} ||| ${r.label_en} ||| ${r.value || '_'}`; }
  if (b.type === 'table') { const row = p.r === -1 ? b.cols : b.rows[p.r]; return row ? row.map(c => c.mk + (c.en ? '~~' + c.en : '')).join(' ||| ') : null; }
  if ((b.type === 'text' || b.type === 'bullets') && p.r >= 0) { const q = b.paras[p.r]; return q.mk + ' ||| ' + q.en; }
  return null;
}
function setCellText(doc: WizardPayload, a: string, t: string): WizardPayload {
  const p = parseAnchor(a)!, q = clone(doc), b = q.sections[p.s].blocks[p.b], parts = t.split(/\s*\|\|\|\s*/);
  const cell = (x: string): Cell => { const [mk, en = ''] = x.split('~~'); return { mk: mk.trim(), en: en.trim() }; };
  if (b.type === 'form') b.rows[p.r] = { label_mk: parts[0] || '', label_en: parts[1] || '', value: (parts[2] || '').replace(/^_$/, '') };
  else if (b.type === 'table') { const row = parts.map(cell); if (p.r === -1) b.cols = row; else b.rows[p.r] = row; }
  else if (b.type === 'text' || b.type === 'bullets') b.paras[p.r] = { mk: parts[0] || '', en: parts.slice(1).join(' ') };
  return q;
}

function PageEdit({ doc, setDoc, cellA, setCellA, highlights, stamps, onLayout }: { doc: WizardPayload; setDoc: (d: WizardPayload) => void; cellA: string | null; setCellA: (a: string | null) => void; highlights: Highlight[]; stamps: ReturnType<typeof spread>; onLayout: (m: AnchorMap) => void }) {
  const { set } = useApp();
  const [boxes, setBoxes] = useState<AnchorMap>({});
  const txt = cellA ? cellText(doc, cellA) : null;
  const p = cellA ? parseAnchor(cellA) : null;
  const b = p ? doc.sections[p.s]?.blocks[p.b] : undefined;
  const top = cellA && boxes[cellA] ? boxes[cellA].top * .6 + boxes[cellA].height * .6 + 18 : 206;
  const addRow = () => { if (!p || !b) return; const q = clone(doc), bb = q.sections[p.s].blocks[p.b];
    if (bb.type === 'form') bb.rows.splice(p.r + 1, 0, { label_mk: '', label_en: '', value: '' });
    else if (bb.type === 'table') bb.rows.splice(p.r + 1, 0, bb.cols.map(() => ({ mk: '', en: '' })));
    else if (bb.type === 'text' || bb.type === 'bullets') bb.paras.splice(p.r + 1, 0, { mk: '', en: '' });
    setDoc(q); setCellA(`s${p.s}b${p.b}r${p.r + 1}`); };
  const toTable = () => { if (!p || !b || b.type !== 'form') return; const q = clone(doc);
    q.sections[p.s].blocks[p.b] = { type: 'table', cols: [{ mk: 'Поле', en: 'Field' }, { mk: 'Вредност', en: 'Value' }], rows: b.rows.map(r => [{ mk: r.label_mk, en: r.label_en }, { mk: r.value, en: '' }]) }; setDoc(q); };
  const ask = () => { if (txt) { set({ chatDraft: `Translate to EN, keep MK as is: ${txt}`, screen: 'chat' }); } };
  return <div style={{ flex: 1, minHeight: 0, position: 'relative', overflow: 'auto', background: T.deep }}>
    <div style={{ position: 'absolute', left: '50%', top: 22, marginLeft: -238, width: 476 }}>
      <PPPage doc={doc} zoom={.6} highlights={highlights} onLayout={m => { setBoxes(m); onLayout(m); }} onPick={a => { if (cellText(doc, a) !== null) setCellA(a); }} />
      {txt !== null && cellA && <div style={{ position: 'absolute', left: 150, top, width: 380, background: T.surface, border: `1px solid ${T.focus}`, borderRadius: 10, boxShadow: '0 18px 40px rgba(0,0,0,.45)', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13, zIndex: 5 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: T.muted }}><b style={{ color: C.run }}>{b?.type === 'form' ? 'Form' : b?.type === 'table' ? 'Table' : 'Text'} row {p!.r + 1 || 'header'}</b><span>{b?.type === 'form' ? 'label МК ||| label EN ||| value' : b?.type === 'table' ? 'МК~~EN ||| …' : 'МК ||| EN'}<span onClick={() => setCellA(null)} style={{ marginLeft: 10, cursor: 'pointer' }}>×</span></span></div>
        <input autoFocus value={txt} onChange={e => setDoc(setCellText(doc, cellA, e.target.value))}
          onKeyDown={e => { if (e.key === 'Tab') { e.preventDefault(); const el = e.currentTarget, i = el.selectionStart ?? txt.length; setDoc(setCellText(doc, cellA, txt.slice(0, i) + ' ||| ' + txt.slice(i))); } if (e.key === 'Escape') setCellA(null); }}
          style={{ border: `1.5px solid ${C.run}`, borderRadius: 6, padding: '8px 10px', fontFamily: MONO, fontSize: 12, background: T.deeper, color: '#fff', outline: 'none' }} />
        <div style={{ display: 'flex', gap: 6, fontSize: 12, flexWrap: 'wrap' }}>
          <span className="pp-chip" onClick={addRow} style={{ border: `1px solid ${T.control}`, borderRadius: 999, padding: '4px 10px', cursor: 'pointer' }}>＋ Row below</span>
          {b?.type === 'form' && <span className="pp-chip" onClick={toTable} style={{ border: `1px solid ${T.control}`, borderRadius: 999, padding: '4px 10px', cursor: 'pointer' }}>Convert to table</span>}
          <span className="pp-chip" onClick={ask} style={{ border: `1px solid ${T.control}`, borderRadius: 999, padding: '4px 10px', cursor: 'pointer' }}>Ask agent to translate</span>
        </div>
      </div>}
      <StampRail stamps={stamps} size="lg" width={200} />
    </div>
    <div style={{ position: 'sticky', left: 18, top: 'calc(100% - 26px)', fontSize: 12, color: T.faint, padding: '0 18px' }}>Click any cell to edit · Tab inserts ||| · the gate stamps the margin live</div>
  </div>;
}

// ---------------- Blocks · wizard (COVERAGE #2) ----------------
function BlockEditor({ doc, setDoc, lints }: { doc: WizardPayload; setDoc: (d: WizardPayload) => void; lints: Lint[] }) {
  const { api, flash } = useApp();
  const [serverMd, setServerMd] = useState<{ md: string; same: boolean } | null>(null);
  const edit = (fn: (q: WizardPayload) => void) => { const q = clone(doc); fn(q); setDoc(q); setServerMd(null); };
  const move = <X,>(arr: X[], i: number, d: number) => { const j = i + d; if (j < 0 || j >= arr.length) return; [arr[i], arr[j]] = [arr[j], arr[i]]; };
  const loadExample = async () => { try { const r = await api.example(); setDoc({ ...r.payload, status: 'draft', effective_date: '', review_date: '', supersedes: r.payload.supersedes || '' } as WizardPayload); flash('Loaded GET /api/example'); } catch (e) { flash(String((e as Error).message)); } };
  const preview = async () => { try { const md = await api.preview(doc); setServerMd({ md, same: md === composeMarkdown(doc) }); } catch (e) { flash(String((e as Error).message)); } };
  const mini = { padding: '2px 7px', fontSize: 11.5, border: `1px solid ${T.control}`, borderRadius: 4, cursor: 'pointer', color: T.secondary, whiteSpace: 'nowrap' } as const;
  const BI = (p: { v: string; on: (v: string) => void; ph: string; w?: number | string; bad?: boolean }) => <Input value={p.v} onChange={p.on} placeholder={p.ph} bad={p.bad} style={{ width: p.w ?? '100%', padding: '4px 7px', fontSize: 12.5 }} />;
  const warnAt = (si: number, bi: number, r: number, c?: number) => lints.some(l => l.section === si && l.block === bi && l.row === r && (c === undefined || l.col === c));

  const blockEd = (_s: Section, si: number, b: Block, bi: number) => {
    const upB = (fn: (bb: Block) => void) => edit(q => fn(q.sections[si].blocks[bi]));
    let body: JSX.Element;
    if (b.type === 'text' || b.type === 'bullets') body = <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>{b.paras.map((pa, i) =>
      <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 14px 1fr auto', gap: 6, alignItems: 'center' }}>
        <BI v={pa.mk} on={v => upB(bb => { (bb as { paras: { mk: string }[] }).paras[i].mk = v; })} ph="МК" /><Sep />
        <BI v={pa.en} on={v => upB(bb => { (bb as { paras: { en: string }[] }).paras[i].en = v; })} ph="EN" bad={warnAt(si, bi, i)} />
        <span style={mini} onClick={() => upB(bb => { (bb as { paras: unknown[] }).paras.splice(i, 1); })}>×</span></div>)}
      <span style={{ ...mini, alignSelf: 'flex-start' }} onClick={() => upB(bb => { (bb as { paras: unknown[] }).paras.push({ mk: '', en: '' }); })}>＋ paragraph</span></div>;
    else if (b.type === 'form') body = <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>{b.rows.map((r, i) =>
      <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 14px 1fr 14px 110px auto auto', gap: 6, alignItems: 'center' }}>
        <BI v={r.label_mk} on={v => upB(bb => { (bb as { rows: { label_mk: string }[] }).rows[i].label_mk = v; })} ph="label МК" /><Sep />
        <BI v={r.label_en} on={v => upB(bb => { (bb as { rows: { label_en: string }[] }).rows[i].label_en = v; })} ph="label EN" bad={warnAt(si, bi, i)} /><Sep />
        <BI v={r.value} on={v => upB(bb => { (bb as { rows: { value: string }[] }).rows[i].value = v; })} ph="_ blank for operator" />
        <span style={mini} onClick={() => upB(bb => move((bb as { rows: unknown[] }).rows, i, -1))}>↑</span>
        <span style={mini} onClick={() => upB(bb => { (bb as { rows: unknown[] }).rows.splice(i, 1); })}>×</span></div>)}
      <span style={{ ...mini, alignSelf: 'flex-start' }} onClick={() => upB(bb => { (bb as { rows: unknown[] }).rows.push({ label_mk: '', label_en: '', value: '' }); })}>＋ row</span></div>;
    else body = <div style={{ overflowX: 'auto' }}><table style={{ borderCollapse: 'separate', borderSpacing: 4 }}><tbody>
      <tr>{b.cols.map((c, ci) => <td key={ci} style={{ minWidth: 130 }}>
        <div style={{ display: 'flex', gap: 3, marginBottom: 3 }}><span style={{ ...mini, background: T.navy, color: '#fff', border: 0 }}>col {ci + 1}</span>
          <span style={mini} onClick={() => upB(bb => { const t = bb as Extract<Block, { type: 'table' }>; move(t.cols, ci, -1); t.rows.forEach(r => move(r, ci, -1)); })}>←</span>
          <span style={mini} onClick={() => upB(bb => { const t = bb as Extract<Block, { type: 'table' }>; t.cols.splice(ci, 1); t.rows.forEach(r => r.splice(ci, 1)); })}>×</span></div>
        <BI v={c.mk} on={v => upB(bb => { (bb as Extract<Block, { type: 'table' }>).cols[ci].mk = v; })} ph="МК" />
        <div style={{ height: 3 }} /><BI v={c.en} on={v => upB(bb => { (bb as Extract<Block, { type: 'table' }>).cols[ci].en = v; })} ph="EN" bad={warnAt(si, bi, -1, ci)} /></td>)}
        <td style={{ verticalAlign: 'top' }}><span style={mini} onClick={() => upB(bb => { const t = bb as Extract<Block, { type: 'table' }>; t.cols.push({ mk: '', en: '' }); t.rows.forEach(r => r.push({ mk: '', en: '' })); })}>＋ col</span></td></tr>
      {b.rows.map((r, ri) => <tr key={ri}>{r.map((c, ci) => <td key={ci}>
        <BI v={c.mk + (c.en ? '~~' + c.en : '')} bad={warnAt(si, bi, ri, ci)} ph="МК~~EN" on={v => upB(bb => { const [mk, en = ''] = v.split('~~'); (bb as Extract<Block, { type: 'table' }>).rows[ri][ci] = { mk, en }; })} /></td>)}
        <td><span style={mini} onClick={() => upB(bb => { (bb as Extract<Block, { type: 'table' }>).rows.splice(ri, 1); })}>×</span></td></tr>)}
      <tr><td colSpan={b.cols.length + 1}><span style={mini} onClick={() => upB(bb => { const t = bb as Extract<Block, { type: 'table' }>; t.rows.push(t.cols.map(() => ({ mk: '', en: '' }))); })}>＋ row</span>
        {b.cols.length >= 9 && <span style={{ marginLeft: 10, fontSize: 11.5, color: C.warn }}>9+ columns: EN halves will shrink below the 6 pt floor; split the table or go landscape</span>}</td></tr>
    </tbody></table></div>;
    return <div key={bi} style={{ background: T.deeper, border: `1px solid ${T.hair}`, borderRadius: 6, padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: 6 }}>
      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}><span style={{ fontFamily: MONO, fontSize: 11, color: T.purple }}>[[{b.type === 'text' || b.type === 'bullets' ? b.type : b.type.toUpperCase()}]]</span>
        <span style={{ marginLeft: 'auto', ...mini }} onClick={() => edit(q => move(q.sections[si].blocks, bi, -1))}>↑</span>
        <span style={mini} onClick={() => edit(q => move(q.sections[si].blocks, bi, 1))}>↓</span>
        <span style={mini} onClick={() => edit(q => { q.sections[si].blocks.splice(bi, 1); })}>delete</span></div>
      {body}</div>;
  };

  const NEW: Record<Block['type'], () => Block> = {
    text: () => ({ type: 'text', paras: [{ mk: '', en: '' }] }), bullets: () => ({ type: 'bullets', paras: [{ mk: '', en: '' }] }),
    form: () => ({ type: 'form', rows: [{ label_mk: '', label_en: '', value: '' }] }),
    table: () => ({ type: 'table', cols: [{ mk: '№', en: '' }, { mk: '', en: '' }], rows: [[{ mk: '1', en: '' }, { mk: '', en: '' }]] }),
  };
  return <div style={{ flex: 1, minHeight: 0, overflow: 'auto', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 10 }}>
    <div style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 12.5 }}>
      <Caps>WIZARD PAYLOAD · sections → blocks</Caps>
      <span style={{ marginLeft: 'auto' }} /><Btn primary={false} onClick={loadExample} style={{ padding: '5px 10px', fontSize: 12.5 }}>Load example</Btn>
      <Btn primary={false} onClick={preview} style={{ padding: '5px 10px', fontSize: 12.5 }}>POST /api/wizard/preview</Btn>
    </div>
    {serverMd && <Banner kind={serverMd.same ? 'ok' : 'warn'}>{serverMd.same ? 'Server Markdown matches the live page byte for byte.' : 'Server Markdown differs from the in-browser composer; the server is authoritative for the build.'}</Banner>}
    {doc.sections.map((s, si) => <div key={si} style={{ background: T.surface, border: `1px solid ${T.control}`, borderRadius: 8, padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ display: 'grid', gridTemplateColumns: '54px 1fr 14px 1fr 64px auto auto auto', gap: 6, alignItems: 'center' }}>
        <Input value={s.num} onChange={v => edit(q => { q.sections[si].num = v; })} placeholder="№" style={{ padding: '4px 7px', fontFamily: MONO, fontSize: 12 }} />
        <Input value={s.mk} onChange={v => edit(q => { q.sections[si].mk = v; })} placeholder="Наслов МК" style={{ padding: '4px 7px', fontWeight: 700 }} /><span style={{ color: T.muted }}>|</span>
        <Input value={s.en} onChange={v => edit(q => { q.sections[si].en = v; })} placeholder="Heading EN" bad={lints.some(l => l.section === si && l.block < 0)} style={{ padding: '4px 7px' }} />
        <select value={s.level} onChange={e => edit(q => { q.sections[si].level = Number(e.target.value) as 1 | 2 | 3; })} title="level → # ## ###"><option value={1}>#</option><option value={2}>##</option><option value={3}>###</option></select>
        <span style={mini} onClick={() => edit(q => move(q.sections, si, -1))}>↑</span><span style={mini} onClick={() => edit(q => move(q.sections, si, 1))}>↓</span>
        <span style={mini} onClick={() => edit(q => { q.sections.splice(si, 1); })}>delete</span>
      </div>
      {s.blocks.map((b, bi) => blockEd(s, si, b, bi))}
      <div style={{ display: 'flex', gap: 6, fontSize: 11 }}><span style={{ color: T.faint, fontFamily: MONO }}>ADD</span>{(['text', 'bullets', 'form', 'table'] as const).map(t =>
        <span key={t} className="pp-chip" onClick={() => edit(q => { q.sections[si].blocks.push(NEW[t]()); })} style={{ fontFamily: MONO, border: `1px dashed ${T.control}`, borderRadius: 4, padding: '2px 7px', color: T.secondary, cursor: 'pointer' }}>+ {t}</span>)}</div>
    </div>)}
    <div style={{ fontSize: 12, color: T.faint }}>Level 1 sections render as navy banners on annexes; level 2–3 as sub-bars. On an SOP every section is a two-column MK | EN row. Build sends this payload to POST /api/wizard/build.</div>
  </div>;
}
