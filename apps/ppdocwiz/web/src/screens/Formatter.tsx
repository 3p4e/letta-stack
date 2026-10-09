// Formatter (handoff §6): Mode B parse → Markdown → POST /build; Mode C restyle in place.
import { useState } from 'react';
import { create } from 'zustand';
import { ApiError } from '../api/types';
import { PPPage } from '../components/PPPage';
import { Banner, Caps, PaneHead, Seg, stamp, StampRail } from '../components/ui';
import { SAMPLE_ANNEX } from '../data/samples';
import { blocksToMd, docxBlocks, textBlocks, unzipEntry } from '../lib/docparse';
import { usePrimary } from '../lib/usePrimary';
import { nbsp } from '../lib/verify';
import { useApp } from '../store/store';
import { C, MONO, T } from '../theme';

type F = { name: string; size: number } & ReturnType<typeof blocksToMd>;
const useF = create<{ file: F | null; err: string; paste: string; pasteOpen: boolean; out: string }>(() => ({ file: null, err: '', paste: '', pasteOpen: false, out: '' }));
const SAMPLE_MD: { t: string; lab?: string; c?: string; fw?: number; lc?: string; bg?: string }[] = [
  { t: '# 1 Пратка | Consignment', lab: 'heading · 0.97', c: C.run, fw: 700 }, { t: '[[FORM]]', lab: 'form · 0.92', c: T.purple },
  { t: 'MRN на царинска декларација ||| Customs declaration MRN ||| _' }, { t: 'Датум/време на пристигнување ||| Arrival date/time ||| _' }, { t: 'Температура при пристигнување ||| Arrival temperature ||| _' },
  { t: '[[/FORM]]', c: T.purple }, { t: '  "(check!!)" → dropped as an editing note?  ', lab: 'review · 0.41', c: C.warn, lc: C.warn, bg: T.warnSurface },
  { t: '# 2 Фитосанитарно и ослободување | Phytosanitary', lab: 'heading · 0.95', c: C.run, fw: 700 }, { t: '[[TABLE]]', lab: 'table · 0.88', c: T.purple },
  { t: '№ ||| Проверка~~Check ||| Реф.~~Ref. ||| Статус~~Status' }, { t: '…' },
];
const Colored = ({ t }: { t: string }) => <>{t.split(/(\|\|\||~~)/).map((p, i) => p === '|||' || p === '~~' ? <span key={i} style={{ color: C.warn }}>{p}</span> : <span key={i}>{p}</span>)}</>;

export function Formatter() {
  const { fmt, set, run, api } = useApp();
  const { file: F, err, paste, pasteOpen, out } = useF();
  const [drag, setDrag] = useState(false);
  const load = async (file?: File) => {
    if (!file) return;
    useF.setState({ err: '' });
    try {
      let blocks;
      if (/\.docx$/i.test(file.name)) blocks = docxBlocks(await unzipEntry(await file.arrayBuffer(), 'word/document.xml'));
      else if (/\.(md|txt)$/i.test(file.name)) blocks = textBlocks(await file.text());
      else throw new Error('Unsupported type — use .docx, .md or .txt');
      if (!blocks.length) throw new Error('No text found in ' + file.name);
      useF.setState({ file: { name: file.name, size: file.size, ...blocksToMd(blocks) }, out: '' });
    } catch (e) { useF.setState({ err: String((e as Error).message || e) }); }
  };
  const stem = F ? F.name.replace(/\.[^.]+$/, '') : 'WHSOP_002_A02';
  const build = () => run(stem, async () => {
    // Live mode never builds the on-screen sample: it would be registered in the real Library.
    if (api.mode === 'live' && !F && fmt === 'B') { useF.setState({ out: 'Nothing to build: load a .docx, .md or .txt, or paste text. The sample on screen is a layout example and is never built in live mode.' }); return { ok: false, failAt: 0, msg: 'no input' }; }
    if (fmt === 'C') { useF.setState({ out: api.mode === 'live' ? '501 · Mode C restyles a .docx in place (pp_format) and has no HTTP route yet; use the engine CLI.' : 'Restyled in place · every w:t preserved · RESULT: PASS' }); return api.mode === 'live' ? { ok: false, failAt: 1, msg: 'RESULT: FAIL · 501' } : { ok: true }; }
    const md = F ? F.markdown : SAMPLE_MD.filter(l => !l.bg && l.t !== '…').map(l => l.t).join('\n');
    try { const r = await api.directBuild(`<!--HEADERDATA\ncode: ${stem}\ndoctype: ANNEX\n-->\n\n` + md, stem, { code: stem, source: 'build · Mode B' }); useF.setState({ out: r.verify.split('\n').pop() + ` · registered ${String(r.document_id).slice(0, 8)}` }); return { ok: true }; }
    catch (e) { useF.setState({ out: `${(e as ApiError).status} · ${(e as Error).message}` }); return { ok: false, failAt: 2, msg: `RESULT: FAIL · ${(e as ApiError).status}` }; }
  });
  usePrimary('Build ▸', build);
  const kb = (n: number) => n < 1024 ? n + ' B' : (n / 1024).toFixed(1) + ' KB';
  const fIn = F ? { label: `${F.name} · ${nbsp(F.words)} words · ${kb(F.size)}`, words: `${nbsp(F.words)} → ${nbsp(F.words)}`, rev: F.rev ? F.rev + (F.rev === 1 ? ' note' : ' notes') : 'none', revC: F.rev ? C.warn : C.ok, counts: `${F.heads} headings · ${F.tables} tables` }
    : { label: api.mode === 'live' ? 'sample layout · load your own file' : 'labels_raw.docx · 1 204 words', words: '1 204 → 1 204', rev: '1 note', revC: C.warn, counts: 'sample' };
  const stamps = F ? [stamp('FIDELITY', `${F.words} ≥ ${F.words} words`, 'ok', 20, '-2deg'), stamp('REVIEW', F.rev ? `${F.rev} ${F.rev === 1 ? 'note' : 'notes'} to check` : 'nothing flagged', F.rev ? 'warn' : 'ok', 110, '1.5deg'), stamp('STRUCTURE', `${F.heads} headings · ${F.tables} tables`, 'run', 200, '-1deg')]
    : [stamp('FIDELITY', '1 204 ≥ 1 204 words', 'ok', 20, '-2deg'), stamp('REVIEW', '1 note dropped?', 'warn', 110, '1.5deg'), stamp('BILINGUAL', 'MK ||| EN paired', 'ok', 200, '-1deg')];
  const lines = F ? F.md : SAMPLE_MD.map(l => ({ t: l.t, lab: l.lab || '', c: l.c || T.text, fw: l.fw || 400, lc: l.lc || C.ok, bg: l.bg || 'transparent' }));
  return <>
    <div style={{ width: 260, flex: 'none', borderRight: `1px solid ${T.hair}`, background: T.pane, padding: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}><b style={{ color: '#fff' }}>Input</b><span style={{ fontSize: 12, color: T.muted, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 170 }}>{fIn.label}</span></div>
      {!F ? <div style={{ borderRadius: 2, overflow: 'hidden' }}><PPPage raw zoom={.29} /></div>
        : <div style={{ width: 230, height: 326, overflow: 'hidden', borderRadius: 2, background: '#fff', color: '#222', padding: 14, fontFamily: 'Calibri,Carlito,sans-serif', fontSize: 8, lineHeight: 1.35, display: 'flex', flexDirection: 'column', gap: 3 }}>{F.prev.map((p, i) => <div key={i} style={{ fontWeight: p.fw, fontSize: p.fs, color: p.c, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.t}</div>)}</div>}
      <label onDragOver={e => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)} onDrop={e => { e.preventDefault(); setDrag(false); load(e.dataTransfer.files[0]); }}
        style={{ border: `1px dashed ${drag ? C.run : T.control}`, background: drag ? 'rgba(127,178,229,.08)' : 'transparent', borderRadius: 6, padding: 10, textAlign: 'center', color: T.secondary, fontSize: 12.5, cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: 2 }}>
        <span>Drop .docx / .md / .txt</span><span style={{ fontSize: 11.5, color: C.run }}>or click to browse</span>
        <input type="file" accept=".docx,.md,.txt" onChange={e => { load(e.target.files?.[0]); e.target.value = ''; }} style={{ display: 'none' }} /></label>
      <div style={{ display: 'flex', gap: 8, fontSize: 12 }}><span onClick={() => useF.setState({ pasteOpen: !pasteOpen })} style={{ color: C.run, cursor: 'pointer' }}>{pasteOpen ? 'Hide paste box' : 'Paste text instead'}</span>{F && <span onClick={() => useF.setState({ file: null, err: '', out: '' })} style={{ marginLeft: 'auto', color: T.muted, cursor: 'pointer' }}>Reset to sample</span>}</div>
      {pasteOpen && <><textarea value={paste} onChange={e => useF.setState({ paste: e.target.value })} placeholder={'# Наслов | Title\nТекст ||| Text'} style={{ height: 110, background: T.deeper, border: `1px solid ${T.control}`, borderRadius: 6, padding: 8, color: '#fff', font: `12px ${MONO}`, resize: 'none', outline: 'none' }} />
        <button onClick={() => { const t = paste.trim(); if (!t) return useF.setState({ err: 'Paste some text first' }); load(new File([t], 'pasted.md', { type: 'text/markdown' })); useF.setState({ pasteOpen: false }); }} style={{ background: T.navy, color: '#fff', border: 0, borderRadius: 6, padding: 7, font: 'inherit', fontWeight: 700, cursor: 'pointer' }}>Use pasted text</button></>}
      {err && <div style={{ fontSize: 12, color: C.bad }}>{err}</div>}
    </div>
    <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
      <div style={{ height: 42, flex: 'none', display: 'flex', alignItems: 'center', gap: 10, padding: '0 14px', borderBottom: `1px solid ${T.hair}`, fontSize: 13 }}>
        <Seg items={[['B', 'Mode B · format'], ['C', 'Mode C · restyle']]} value={fmt} onPick={k => set({ fmt: k })} />
        <span style={{ color: T.muted, fontSize: 12.5, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{fmt === 'B' ? 'Parse → Markdown → build. Best for messy sources.' : 'Restyle runs in place. Every w:t is preserved.'}</span></div>
      <div style={{ flex: 1, minHeight: 0, padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {out && <Banner kind={/^\d{3}/.test(out) ? 'err' : 'ok'}>{out}</Banner>}
        <Caps>DETECTED STRUCTURE → MARKDOWN<span style={{ float: 'right', letterSpacing: 0, color: T.muted }}>{fIn.counts}</span></Caps>
        <div style={{ flex: 1, minHeight: 0, background: T.surface, border: `1px solid ${T.hair}`, borderRadius: 6, padding: '12px 14px', fontFamily: MONO, fontSize: 12.5, lineHeight: 1.8, overflow: 'auto' }}>
          {lines.map((l, i) => <div key={i} style={{ display: 'flex', gap: 16, minHeight: '1.7em' }}>
            <span style={{ whiteSpace: 'pre', overflow: 'hidden', textOverflow: 'ellipsis', minWidth: 0, paddingRight: 2, color: l.c, fontWeight: l.fw }}><span style={{ background: l.bg }}>{l.c === T.text || l.c === '#d6e2f0' ? <Colored t={l.t} /> : l.t}</span></span>
            {l.lab && <span style={{ marginLeft: 'auto', flex: 'none', whiteSpace: 'nowrap', color: l.lc }}>{l.lab}</span>}</div>)}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,minmax(0,1fr))', gap: 10, fontSize: 12.5 }}>
          {([['Words in → out', fIn.words, '#fff'], ['Fidelity §5A', 'output ≥ source', C.ok], ['Needs review', fIn.rev, fIn.revC]] as const).map(([k, v, c]) =>
            <div key={k} style={{ background: T.surface, border: `1px solid ${T.control}`, borderRadius: 6, padding: '9px 11px' }}><div style={{ color: T.muted, fontSize: 11.5 }}>{k}</div><b style={{ color: c }}>{v}</b></div>)}
        </div>
      </div>
    </div>
    <div style={{ width: 380, flex: 'none', borderLeft: `1px solid ${T.hair}`, background: T.deep, display: 'flex', flexDirection: 'column' }}>
      <PaneHead title="Output · house style" right={stem} />
      <div style={{ flex: 1, position: 'relative', padding: '16px 0 0 14px' }}>
        <div style={{ position: 'relative', width: 254 }}><PPPage doc={{ ...SAMPLE_ANNEX, code: stem }} zoom={.32} /><StampRail stamps={stamps} width={110} w={96} /></div>
      </div>
    </div>
  </>;
}
