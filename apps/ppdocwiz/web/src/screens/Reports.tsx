// Reports composer (handoff §5, modelled on pp_report.py) + COVERAGE #7 data binding, #8 chart picker,
// #9 more blocks / editable sign-off, #11 platform notes.
import { useState, type CSSProperties, type ReactNode } from 'react';
import { create } from 'zustand';
import { ApiError, type DocStatus } from '../api/types';
import { Chart, CHARTS, type ChartKind } from '../components/Charts';
import { headerVersion, effectiveDisplay, STATUS_LABEL } from '../components/PPPage';
import { Banner, Caps, Input, PaneHead, Seg, stamp, type StampSpec } from '../components/ui';
import { Stamp } from '../components/ui';
import { SIGNOFF_DEFAULTS } from '../data/samples';
import { usePrimary } from '../lib/usePrimary';
import { ci95, consistent, mean, num, parseDataset, provenance, rsd, SAMPLE_CSV, sd, type Dataset } from '../lib/stats';
import { useApp } from '../store/store';
import { C, DISPLAY, MONO, PAGE, T } from '../theme';

type BT = 'cover' | 'toc' | 'text' | 'calc' | 'entry' | 'figure' | 'exec' | 'grid' | 'databox' | 'eqn' | 'note' | 'bullet' | 'minilabel';
interface RBlock { id: string; t: BT; fn: string; mk: string; en: string; help: string; mkText?: string; enText?: string; sub?: boolean;
  chart?: ChartKind; options?: string[]; ncols?: number; boxKind?: 'caveat' | 'status'; latex?: string }
const BASE: RBlock[] = [
  { id: 'b1', t: 'cover', fn: 'cover_page', mk: 'Насловна страна', en: 'Cover · unnumbered', help: 'Page 1 · status band, info, approval' },
  { id: 'b2', t: 'toc', fn: 'toc_page', mk: 'Содржина', en: 'Table of contents', help: 'Page 2 · native TOC field' },
  { id: 'b3', t: 'text', fn: 'chapter', mk: '1. Резиме', en: 'Executive summary', help: 'Outline level 0', mkText: 'Методата е верификувана на две серии со шест реплики.', enText: 'The method was verified on two batches with six replicates.' },
  { id: 'b4', t: 'text', fn: 'chapter', mk: '2. Метода', en: 'Method', help: 'Outline level 0', mkText: 'Губење при сушење според Ph. Eur. 2.2.32.', enText: 'Loss on drying per Ph. Eur. 2.2.32.' },
  { id: 'b5', t: 'calc', fn: 'calc_step', mk: '2.1 Губење при сушење', en: 'Loss on drying', help: 'formula → substituted → emphasised result', sub: true },
  { id: 'b6', t: 'entry', fn: 'entry_table', mk: '3. Сурови податоци', en: 'Raw data', help: 'blank write-in grid' },
  { id: 'b7', t: 'figure', fn: 'figure', mk: '4. Слики', en: 'Figures', help: 'PNG from pp_charts + bilingual caption', mkText: 'Губење при сушење по реплика за двете серии.', enText: 'Loss on drying per replicate for both batches.', chart: 'guardband' },
  { id: 'b8', t: 'exec', fn: 'execution_signoff', mk: '5. Потпишување', en: 'Execution sign-off', help: 'Executed → Reviewed → Approved', mkText: 'Протоколот е извршен и прегледан.', enText: 'The protocol was executed and reviewed.' },
];
const PAL: [string, BT, Partial<RBlock>][] = [
  ['chapter', 'text', {}], ['subsec', 'text', { sub: true }], ['body', 'text', { sub: true }], ['note', 'note', { sub: true }], ['bullet', 'bullet', { sub: true }], ['minilabel', 'minilabel', { sub: true }],
  ['calc_step', 'calc', { sub: true }], ['eqn_result', 'eqn', { sub: true, latex: '\\bar{x} = 11{,}24\\,\\%' }], ['entry_table', 'entry', { sub: true }],
  ['status_grid', 'grid', { sub: true, options: ['Одговара | Conforms', 'Не одговара | Does not conform', 'Не е применливо | N/A'], ncols: 2 }],
  ['databox', 'databox', { sub: true, boxKind: 'caveat', mkText: 'Податоците се од две серии.', enText: 'Data are from two batches.' }], ['figure', 'figure', { sub: true, chart: 'horrat_bar' }], ['step_signoff', 'text', { sub: true }],
];

interface RS { extra: RBlock[]; edits: Record<string, Partial<RBlock>>; status: DocStatus; eff: string; m: { m0: string; m1: string; m2: string }; stepSign: boolean; sign: boolean; rows: number;
  signoff: typeof SIGNOFF_DEFAULTS; data: Dataset | null; reported: string; dataErr: string }
const useR = create<RS>(() => ({ extra: [], edits: {}, status: 'draft', eff: '', m: { m0: '4.2210', m1: '12.4518', m2: '11.5236' }, stepSign: true, sign: true, rows: 6, signoff: { ...SIGNOFF_DEFAULTS }, data: null, reported: '11.28', dataErr: '' }));

const lodOf = (m0: number, m1: number, m2: number) => (m1 - m2) / (m1 - m0) * 100;
const navyTd: CSSProperties = { border: `1px solid ${PAGE.navy}`, padding: '5px 6px', background: PAGE.navy, color: '#fff', fontWeight: 700, textAlign: 'center' };
const td: CSSProperties = { border: `1px solid ${PAGE.navy}`, padding: 6, textAlign: 'center' };
const H1 = ({ mk, en }: { mk: string; en: string }) => <div style={{ marginTop: 22 }}><span style={{ fontSize: 26, color: PAGE.navy, fontWeight: 700 }}>{mk}</span><span style={{ color: PAGE.secondary, fontSize: 22 }}>  |  </span><span style={{ color: PAGE.secondary, fontSize: 20 }}>{en}</span></div>;
const Sign = ({ rows }: { rows: string[] }) => <><div style={{ fontSize: 12, color: PAGE.navy, fontWeight: 700, fontStyle: 'italic', margin: '14px 0 4px' }}>Потпис за овој запис <span style={{ color: PAGE.secondary, fontWeight: 400 }}>| Signature for this record</span></div>
  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11.5 }}><tbody><tr>{['Улога | Role', 'Име | Name', 'Датум | Date', 'Потпис | Signature'].map(h => <td key={h} style={navyTd}>{h}</td>)}</tr>
    {rows.map(r => <tr key={r}><td style={{ ...td, background: PAGE.label, width: '50%' }}>{r}</td><td style={td} /><td style={td} /><td style={td} /></tr>)}</tbody></table></>;

export function Reports() {
  const { api, run, repMeta, repSel, set } = useApp();
  const R = useR(), up = (p: Partial<RS>) => useR.setState(p);
  const [buildMsg, setBuildMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const rep = repMeta || { code: 'QCSOP_031_A02', mk: 'Верификација на LOD метода', en: 'LOD method verification', ver: '01' };
  const blocks = [...BASE.slice(0, 7), ...R.extra, BASE[7]].map(b => ({ ...b, ...R.edits[b.id] }));
  const cur = blocks.find(b => b.id === repSel) || blocks[4];
  const edit = (p: Partial<RBlock>) => up({ edits: { ...R.edits, [cur.id]: { ...R.edits[cur.id], ...p } } });
  const m0 = num(R.m.m0), m1 = num(R.m.m1), m2 = num(R.m.m2), lod = lodOf(m0, m1, m2), valid = Number.isFinite(lod) && m1 > m0, pass = valid && lod <= 12;
  const lodEn = valid ? lod.toFixed(2) : '—', lodMk = lodEn.replace('.', ',');
  const st = R.status, appr = st === 'approved', hdrVer = headerVersion(st, rep.ver).replace(/^v/, '');
  const [bandMk, bandEn] = STATUS_LABEL[st];

  // ---- dataset (COVERAGE #7) ----
  const lods = R.data ? R.data.rows.map(r => lodOf(num(r.m0), num(r.m1), num(r.m2))).filter(Number.isFinite) : [];
  const recomputed = lods.length ? mean(lods) : NaN;
  const reportedN = num(R.reported);
  const inconsistent = R.data && lods.length > 0 && Number.isFinite(reportedN) && !consistent(+reportedN.toFixed(2), +recomputed.toFixed(2));
  const loadText = async (name: string, text: string, prov: { sha256: string; bytes: number; modified: string }) => {
    try { up({ data: { ...parseDataset(name, text), ...prov }, dataErr: '' }); } catch (e) { up({ dataErr: String((e as Error).message) }); }
  };
  const onFile = async (f?: File) => { if (!f) return; if (!/\.(json|csv|tsv)$/i.test(f.name)) return up({ dataErr: 'Use .json, .csv or .tsv' }); const p = await provenance(f); loadText(f.name, p.text, p); };
  const loadSample = async () => onFile(new File([SAMPLE_CSV], 'lod_replicates.csv', { type: 'text/csv', lastModified: Date.now() }));

  const build = async () => {
    setBuildMsg(null);
    if (inconsistent) { setBuildMsg({ ok: false, text: `assert_consistent failed: printed mean LOD ${R.reported} % ≠ recomputed ${recomputed.toFixed(2)} % (tol 0.01). The build is refused so a report never prints figures its data does not support.` }); return; }
    await run(rep.code, async () => {
      try { const r = await api.buildReport({ code: rep.code, blocks, dataset: R.data ? { name: R.data.name, sha256: R.data.sha256 } : undefined }); setBuildMsg({ ok: true, text: r.verify.split('\n').slice(1, 2).join('') + ' · RESULT: PASS' }); return { ok: true }; }
      catch (e) { setBuildMsg({ ok: false, text: `${(e as ApiError).status} · ${(e as Error).message}` }); return { ok: false, failAt: 1, msg: `RESULT: FAIL · ${(e as ApiError).status}` }; }
    });
  };
  usePrimary('Build ▸', build);

  const pg = ({ cover: 1, toc: 2, text: 3, calc: 4, entry: 5, figure: 6, exec: 7 } as Record<string, number>)[cur.t] || 3;
  const statusSeg = <Seg items={[['draft', 'draft'], ['in_review', 'in review'], ['approved', 'approved']]} value={st} onPick={k => up({ status: k })} size={12.5} pad="5px 12px" />;
  const mono = { width: 110, fontFamily: MONO, fontSize: 11.5, color: T.muted } as const;
  const card = (children: ReactNode, extra: CSSProperties = {}) => <div style={{ background: T.surface, border: `1px solid ${T.control}`, borderRadius: 8, padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 12, fontSize: 13, ...extra }}>{children}</div>;
  const textEditor = <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
    <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}><span style={{ fontSize: 12, color: T.secondary }}>МК</span><textarea value={cur.mkText || ''} onChange={e => edit({ mkText: e.target.value })} style={{ height: 70, background: T.deeper, border: `1px solid ${T.control}`, borderRadius: 5, padding: 8, color: '#fff', resize: 'vertical', outline: 'none' }} /></label>
    <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}><span style={{ fontSize: 12, color: T.secondary }}>EN</span><textarea value={cur.enText || ''} onChange={e => edit({ enText: e.target.value })} style={{ height: 70, background: T.deeper, border: `1px solid ${!cur.enText && cur.mkText ? C.warn : T.control}`, borderRadius: 5, padding: 8, color: '#fff', resize: 'vertical', outline: 'none' }} /></label></div>;

  const stamps: StampSpec[] = cur.t === 'cover' ? [stamp(appr ? 'APPROVED' : 'NOT FOR USE', appr ? 'controlled v' + rep.ver : 'no effective date', appr ? 'ok' : 'warn', 0, '-2deg'), stamp('NO PAGE NO.', 'cover is unnumbered', 'run', 0, '1deg')]
    : cur.t === 'calc' || cur.t === 'eqn' ? [stamp('OMML', '3 native equations', 'ok', 0, '-2deg'), stamp('DECIMAL ,', 'MK uses commas', 'ok', 0, '1.5deg'), stamp('LINUX', 'falls back to text', 'warn', 0, '-1deg')]
    : cur.t === 'entry' ? [stamp('WRITE-INS', R.rows + ' blank rows', 'run', 0, '-2deg'), stamp('HEADER', 'repeats per page', 'ok', 0, '1deg')]
    : cur.t === 'toc' ? [stamp('TOC FIELD', 'press F9 in Word', 'warn', 0, '-2deg')]
    : cur.t === 'figure' ? [stamp('DATA', R.data ? R.data.sha256.slice(0, 8) : 'sample values', R.data ? 'ok' : 'warn', 0, '-2deg'), stamp('CAPTION', 'Слика | Figure', 'ok', 0, '1deg')]
    : [stamp('FONT FLOOR', 'min 7 pt', 'ok', 0, '-2deg'), stamp('BILINGUAL', cur.enText || cur.t === 'exec' || cur.t === 'grid' ? 'MK | EN' : 'EN missing', cur.enText || cur.t === 'exec' || cur.t === 'grid' ? 'ok' : 'warn', 0, '1deg')];

  return <>
    <div style={{ width: 236, flex: 'none', borderRight: `1px solid ${T.hair}`, background: T.pane, padding: '14px 10px', display: 'flex', flexDirection: 'column', gap: 4, overflow: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', padding: '0 4px 6px' }}><b style={{ color: '#fff' }}>Report outline</b><span style={{ fontFamily: MONO, fontSize: 11, color: T.faint }}>pp_report</span></div>
      {blocks.map(b => <div key={b.id} onClick={() => set({ repSel: b.id })} style={{ padding: '7px 9px', borderRadius: 6, cursor: 'pointer', background: b.id === cur.id ? T.selected : T.surface, border: `1px solid ${b.id === cur.id ? T.focus : T.control}`, marginLeft: b.sub ? 12 : 0 }}>
        <div style={{ fontFamily: MONO, fontSize: 10.5, color: C.run }}>{b.fn}</div><div style={{ color: '#fff', fontSize: 13 }}>{b.mk}</div><div style={{ fontSize: 11.5, color: T.secondary }}>{b.en}</div></div>)}
      <Caps style={{ padding: '12px 4px 4px' }}>ADD BLOCK</Caps>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>{PAL.map(([fn, t, extra]) => <span key={fn} className="pp-chip" onClick={() => { const id = 'x' + Date.now(); useR.setState(s => ({ extra: [...s.extra, { id, t, fn, mk: 'Нов блок', en: 'New ' + fn, help: 'added block', mkText: 'Текст на македонски.', enText: 'English text.', ...extra }] })); set({ repSel: id }); }}
        style={{ fontFamily: MONO, fontSize: 11, border: `1px dashed ${T.control}`, borderRadius: 4, padding: '3px 7px', color: T.secondary, cursor: 'pointer' }}>+ {fn}</span>)}</div>
      <Caps style={{ padding: '12px 4px 4px' }}>DATA · pp_data</Caps>
      <label onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); onFile(e.dataTransfer.files[0]); }} style={{ border: `1px dashed ${T.control}`, borderRadius: 6, padding: 8, textAlign: 'center', color: T.secondary, fontSize: 12, cursor: 'pointer' }}>
        {R.data ? <span style={{ color: '#fff', fontFamily: MONO }}>{R.data.name}</span> : 'Drop .json / .csv / .tsv'}<div style={{ fontSize: 11, color: C.run }}>or click to browse</div>
        <input type="file" accept=".json,.csv,.tsv" onChange={e => { onFile(e.target.files?.[0]); e.target.value = ''; }} style={{ display: 'none' }} /></label>
      <div style={{ display: 'flex', fontSize: 11.5 }}><span onClick={loadSample} style={{ color: C.run, cursor: 'pointer' }}>Load sample dataset</span>{R.data && <span onClick={() => up({ data: null })} style={{ marginLeft: 'auto', color: T.muted, cursor: 'pointer' }}>Remove</span>}</div>
      {R.dataErr && <div style={{ fontSize: 11.5, color: C.bad }}>{R.dataErr}</div>}
    </div>

    <div style={{ flex: 1, minWidth: 0, padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 14, overflow: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 10 }}><div><span style={{ fontFamily: MONO, fontSize: 12, color: C.run }}>{cur.fn}()</span>
        <div style={{ fontFamily: DISPLAY, fontWeight: 700, fontSize: 17, color: '#fff', display: 'flex', flexWrap: 'wrap', columnGap: 8, alignItems: 'baseline' }}><span>{cur.mk}</span><span style={{ fontFamily: 'Carlito', fontWeight: 400, fontSize: 14, color: T.secondary, whiteSpace: 'nowrap' }}>| {cur.en}</span></div></div>
        <span style={{ fontSize: 12, color: T.muted, textAlign: 'right' }}>{cur.help}</span></div>
      {buildMsg && <Banner kind={buildMsg.ok ? 'ok' : 'err'}>{buildMsg.text}</Banner>}
      {inconsistent && <Banner kind="err"><b>assert_consistent · FAIL</b> — printed mean LOD {R.reported} % vs recomputed {recomputed.toFixed(2)} % from {R.data!.name}. Build is blocked until they agree.</Banner>}

      {cur.t === 'cover' && card(<>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}><span style={mono}>status</span>{statusSeg}</div>
        <div style={{ fontSize: 12, color: T.secondary, lineHeight: 1.45, paddingLeft: 120 }}>A controlled version and an effective date appear only when the status is approved. A draft or in-review document is marked NOT FOR USE.</div>
        {appr && <label style={{ display: 'flex', gap: 10, alignItems: 'center' }}><span style={mono}>effective_date</span><Input value={R.eff} onChange={v => up({ eff: v })} placeholder="dd.mm.yyyy" style={{ width: 160 }} /></label>}
        <Caps>INFO ROWS</Caps>
        <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '6px 10px', fontSize: 13 }}><span style={{ color: T.secondary }}>Метода | Method</span><span>Ph. Eur. 2.2.32 — губење при сушење | loss on drying</span><span style={{ color: T.secondary }}>Инструмент | Instrument</span><span>Halogen moisture analyser · ID QC-EQ-014</span><span style={{ color: T.secondary }}>Серии | Batches</span><span>{R.data ? [...new Set(R.data.rows.map(r => r.batch).filter(Boolean))].join(', ') || 'P160012, P160022' : 'P160012, P160022'}</span><span style={{ color: T.secondary }}>Критериум | Criterion</span><span>NMT 12 %</span></div>
      </>)}
      {cur.t === 'toc' && card(<>
        <Banner kind="warn">Platform note · the TOC is a native Word field. The engine sets update-fields-on-open, but Word asks first; LibreOffice and Gotenberg PDFs show the placeholder until the field is updated: open the .docx, right-click the TOC → Update Field (F9), save.</Banner>
        <div style={{ fontSize: 12, color: T.muted }}>Chapters (level 0) and subsections (level 1) feed the TOC. Placeholder text: “Десен-клик → Ажурирај поле (Update Field) | Right-click → Update Field”.</div></>)}
      {cur.t === 'calc' && card(<>
        <div style={{ display: 'grid', gridTemplateColumns: '110px 1fr', gap: '8px 10px', alignItems: 'center', fontSize: 13 }}><span style={mono.fontFamily ? { fontFamily: MONO, fontSize: 11.5, color: T.muted } : {}}>formula</span><code style={{ background: T.deeper, border: `1px solid ${T.control}`, borderRadius: 5, padding: '6px 8px', color: T.purple, fontSize: 12 }}>{'\\mathrm{LOD} = \\frac{m_1 - m_2}{m_1 - m_0} \\times 100\\,\\%'}</code>
          <span style={{ fontFamily: MONO, fontSize: 11.5, color: T.muted }}>substituted</span><span style={{ color: T.secondary, fontSize: 12.5 }}>generated from the inputs below</span></div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,minmax(0,1fr))', gap: 10 }}>{([['m0', 'm₀ · empty dish (g)'], ['m1', 'm₁ · dish + sample (g)'], ['m2', 'm₂ · after drying (g)']] as const).map(([k, label]) =>
          <label key={k} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}><span style={{ fontSize: 12, color: T.secondary }}>{label}</span><Input mono value={R.m[k]} onChange={v => up({ m: { ...R.m, [k]: v } })} style={{ padding: '7px 9px' }} /></label>)}</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px 12px', alignItems: 'center', background: T.deeper, borderLeft: `3px solid ${C.run}`, borderRadius: 4, padding: '10px 12px' }}>
          <span style={{ whiteSpace: 'nowrap', fontFamily: "'Cambria Math',Cambria,serif", fontStyle: 'italic', color: '#fff', fontSize: 16 }}>LOD = {lodEn} %</span>
          <span style={{ whiteSpace: 'nowrap', fontFamily: MONO, fontSize: 12, fontWeight: 700, color: !valid ? C.warn : pass ? C.ok : C.bad }}>{!valid ? 'check inputs' : pass ? '✓ ≤ NMT 12 %' : '✗ > NMT 12 %'}</span>
          <span style={{ marginLeft: 'auto', fontSize: 12, color: T.muted, whiteSpace: 'nowrap' }}>MK shows {lodMk} % (decimal comma)</span></div>
        <label style={{ display: 'flex', gap: 8, alignItems: 'center', cursor: 'pointer' }}><input type="checkbox" checked={R.stepSign} onChange={() => up({ stepSign: !R.stepSign })} />Add step_signoff after this step (Operator + QC Department Manager)</label>
        <Banner kind="warn">Platform note · native OMML equations need Office's MML2OMML.XSL. Built on Linux (this container, Gotenberg) the equations fall back to text; build on Windows for native Word math.</Banner></>)}
      {cur.t === 'eqn' && card(<>
        <div style={{ display: 'grid', gridTemplateColumns: '110px 1fr', gap: 8, alignItems: 'center' }}><span style={{ fontFamily: MONO, fontSize: 11.5, color: T.muted }}>latex</span><Input mono value={cur.latex || ''} onChange={v => edit({ latex: v })} /></div>
        {R.data && <div style={{ fontSize: 12, color: T.secondary }}>From {R.data.name}: mean LOD {recomputed.toFixed(2)} % → <span onClick={() => edit({ latex: `\\bar{x} = ${recomputed.toFixed(2).replace('.', '{,}')}\\,\\%` })} style={{ color: C.run, cursor: 'pointer' }}>insert</span></div>}
        <div style={{ fontSize: 12, color: T.muted }}>eqn_result() renders the equation in the navy emphasised result box. Same OMML platform note as calc_step applies.</div></>)}
      {cur.t === 'entry' && card(<>
        <Caps>HEADERS · navy row, repeats on page break</Caps>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>{['Реплика | Replicate', 'm₀ (g)', 'm₁ (g)', 'm₂ (g)', 'Потпис | Signature'].map(c => <span key={c} style={{ background: T.navy, color: '#fff', borderRadius: 4, padding: '4px 9px', fontSize: 12 }}>{c}</span>)}</div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}><span style={mono}>rows</span><span onClick={() => up({ rows: Math.max(1, R.rows - 1) })} style={{ width: 28, height: 28, border: `1px solid ${T.control}`, borderRadius: 5, display: 'grid', placeItems: 'center', cursor: 'pointer' }}>−</span><b style={{ color: '#fff', width: 24, textAlign: 'center' }}>{R.rows}</b><span onClick={() => up({ rows: Math.min(20, R.rows + 1) })} style={{ width: 28, height: 28, border: `1px solid ${T.control}`, borderRadius: 5, display: 'grid', placeItems: 'center', cursor: 'pointer' }}>+</span><span style={{ color: T.muted, fontSize: 12 }}>blank write-in rows · first column labelled</span></div>
        <label style={{ display: 'flex', gap: 8, alignItems: 'center', cursor: 'pointer' }}><input type="checkbox" checked={R.sign} onChange={() => up({ sign: !R.sign })} />signoff=True · append the two-role step sign-off</label>
        <div style={{ fontSize: 12, color: T.muted }}>Name, Date and Signature columns are sized for handwriting even when empty (fixed() entry targets 5.2 / 2.6 / 3.8 cm).</div></>)}
      {cur.t === 'figure' && card(<>
        <Caps>CHART · pp_charts.py</Caps>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,minmax(0,1fr))', gap: 8 }}>{CHARTS.map(([k, label, d]) => <div key={k} onClick={() => edit({ chart: k })} style={{ border: `1px solid ${cur.chart === k ? T.focus : T.control}`, background: cur.chart === k ? T.selected : T.deeper, borderRadius: 6, padding: 6, cursor: 'pointer' }}>
          <Chart kind={k} values={lods.length ? lods : []} width={130} height={70} /><div style={{ fontFamily: MONO, fontSize: 10.5, color: cur.chart === k ? '#fff' : T.secondary, marginTop: 4 }}>{k}</div><div style={{ fontSize: 10.5, color: T.muted }}>{label} · {d}</div></div>)}</div>
        <div style={{ fontSize: 12, color: R.data ? T.secondary : C.warn }}>{R.data ? `Bound to ${R.data.name}: ${lods.length} LOD values (computed per row from m0, m1, m2).` : 'No dataset bound: the preview uses placeholder values. Upload the raw data in DATA so the figure and the printed statistics come from the same file.'}</div>
        {textEditor}</>)}
      {cur.t === 'exec' && card(<>
        <Caps>SIGN-OFF CASCADE · execution_signoff()</Caps>
        {([['mk_exec', 'Executed row'], ['reviewer', 'Reviewed (QA)'], ['approver', 'Approved (QC Mgr)']] as const).map(([k, label]) => <label key={k} style={{ display: 'grid', gridTemplateColumns: '130px 1fr auto', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 12, color: T.secondary }}>{label}</span><Input value={R.signoff[k]} onChange={v => up({ signoff: { ...R.signoff, [k]: v } })} />
          <span onClick={() => up({ signoff: { ...R.signoff, [k]: SIGNOFF_DEFAULTS[k] } })} style={{ fontSize: 11, color: R.signoff[k] === SIGNOFF_DEFAULTS[k] ? T.faint : C.run, cursor: 'pointer' }}>{R.signoff[k] === SIGNOFF_DEFAULTS[k] ? 'engine default' : 'reset'}</span></label>)}
        <div style={{ fontSize: 12, color: T.muted }}>pp_report.execution_signoff() hard-codes the reviewer and approver; the build passes these as reviewer= / approver= so a different QA reviewer is printed correctly. Date and Signature stay blank for wet ink.</div></>)}
      {cur.t === 'grid' && card(<>
        <Caps>status_grid · single-select checkbox grid</Caps>
        {(cur.options || []).map((o, i) => <div key={i} style={{ display: 'flex', gap: 6 }}><Input value={o} onChange={v => edit({ options: (cur.options || []).map((x, j) => j === i ? v : x) })} style={{ flex: 1 }} /><span onClick={() => edit({ options: (cur.options || []).filter((_, j) => j !== i) })} style={{ color: T.muted, cursor: 'pointer', alignSelf: 'center' }}>×</span></div>)}
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', fontSize: 12 }}><span onClick={() => edit({ options: [...(cur.options || []), 'МК | EN'] })} style={{ color: C.run, cursor: 'pointer' }}>＋ option</span><span style={{ marginLeft: 'auto', color: T.muted }}>columns</span><Seg items={[['1', '1'], ['2', '2'], ['3', '3']]} value={String(cur.ncols || 2) as '1'} onPick={k => edit({ ncols: +k })} size={12} pad="2px 8px" /></div>
        <div style={{ fontSize: 12, color: T.muted }}>Nothing is pre-ticked: the operator marks one box by hand.</div></>)}
      {cur.t === 'databox' && card(<>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}><span style={mono}>kind</span><Seg items={[['caveat', 'caveat'], ['status', 'status']]} value={cur.boxKind || 'caveat'} onPick={k => edit({ boxKind: k })} size={12} /></div>
        {textEditor}
        {R.data && <div style={{ fontSize: 12, color: T.secondary }}>Provenance line (pp_data.provenance): <span style={{ fontFamily: MONO }}>{R.data.name} · sha256 {R.data.sha256} · {R.data.bytes} B · {R.data.modified}</span></div>}</>)}
      {['text', 'note', 'bullet', 'minilabel'].includes(cur.t) && card(<>
        <span style={{ fontFamily: MONO, fontSize: 11.5, color: T.muted }}>MK ||| EN</span>{textEditor}
        <div style={{ fontSize: 12, color: T.muted }}>{cur.t === 'note' ? 'note(): MK 10 pt | EN 8 pt, justified.' : cur.t === 'bullet' ? 'bullet(): MK 11 | EN 8, tight within the list.' : cur.t === 'minilabel' ? 'minilabel(): unnumbered bold lead-in above a table.' : 'Body is justified; MK 11 pt, EN 8 pt italic grey. Chapters (level 0) and subsections (level 1) feed the native TOC.'}</div></>)}

      {R.data && card(<>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}><Caps>DATASET · {R.data.name}</Caps><span style={{ fontFamily: MONO, fontSize: 11, color: T.muted }}>sha256 {R.data.sha256} · {R.data.bytes} B · {R.data.modified}</span></div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,minmax(0,1fr))', gap: 8, fontSize: 12 }}>{([['n', String(lods.length)], ['mean LOD', recomputed.toFixed(2) + ' %'], ['SD', sd(lods).toFixed(3)], ['RSD', rsd(lods).toFixed(2) + ' %'], ['CI95', lods.length > 1 ? ci95(lods).map(x => x.toFixed(2)).join(' – ') : '—']] as const).map(([k, v]) =>
          <div key={k} style={{ background: T.deeper, border: `1px solid ${T.hair}`, borderRadius: 5, padding: '6px 8px' }}><div style={{ color: T.muted, fontSize: 11 }}>{k}</div><b style={{ color: '#fff', fontFamily: MONO, fontSize: 12 }}>{v}</b></div>)}</div>
        <label style={{ display: 'flex', gap: 10, alignItems: 'center' }}><span style={{ fontSize: 12, color: T.secondary }}>Printed mean LOD in the summary (%)</span><Input mono value={R.reported} onChange={v => up({ reported: v })} bad={!!inconsistent} style={{ width: 90 }} />
          <span style={{ fontFamily: MONO, fontSize: 12, color: inconsistent ? C.bad : C.ok }}>{inconsistent ? '✗ ≠ ' + recomputed.toFixed(2) : '✓ assert_consistent'}</span></label></>, { borderColor: inconsistent ? C.bad : T.control })}
      <div style={{ fontSize: 12, color: T.faint }}>Build → pp_report renders native Word equations (OMML) and charts → pp_verify counts equations and figures in the gate report.</div>
    </div>

    <div style={{ width: 400, flex: 'none', borderLeft: `1px solid ${T.hair}`, background: T.deep, display: 'flex', flexDirection: 'column' }}>
      <PaneHead title="Live page" right={cur.t === 'cover' ? 'Page 1 · unnumbered' : `Page ${pg} / 7 · 35 %`} />
      <div style={{ flex: 1, position: 'relative', padding: '16px 0 0 20px', overflow: 'hidden' }}>
        <div style={{ width: 278, height: 393, overflow: 'hidden', boxShadow: '0 8px 28px rgba(0,0,0,.4)' }}>
          <div style={{ transform: 'scale(.35)', transformOrigin: '0 0', width: 794, height: 1123, background: '#fff', fontFamily: 'Calibri,Carlito,sans-serif', color: '#000', padding: '36px 48px', boxSizing: 'border-box', position: 'relative' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', borderTop: `2px solid ${PAGE.rule}`, borderBottom: `2px solid ${PAGE.rule}`, fontSize: 11 }}><tbody><tr>
              <td rowSpan={2} style={{ width: 150, padding: '4px 8px', borderRight: `1px solid ${PAGE.ruleLight}` }}><img src="/assets/brand/pp_logo_header.jpg" alt="" style={{ width: 130, display: 'block' }} /></td>
              <td rowSpan={2} style={{ padding: '4px 10px', borderRight: `1px solid ${PAGE.ruleLight}`, textAlign: 'center' }}><div style={{ fontSize: 9, color: PAGE.secondary }}>Име на документ | Document name:</div><div style={{ fontFamily: "'Arial Narrow',Arial,sans-serif", fontWeight: 700, fontSize: 15, textTransform: 'uppercase', lineHeight: 1.1, marginTop: 2 }}>{rep.mk}</div><div style={{ fontFamily: "'Arial Narrow',Arial,sans-serif", fontSize: 10, textTransform: 'uppercase', color: '#333', marginTop: 2 }}>{rep.en}</div></td>
              <td style={{ width: 150, padding: '4px 8px', textAlign: 'center', borderBottom: `1px solid ${PAGE.ruleLight}` }}><div style={{ fontSize: 9, color: PAGE.secondary }}>Код на документ | Code of document:</div><div style={{ fontWeight: 700, fontSize: 14 }}>{rep.code}</div></td></tr>
              <tr><td style={{ padding: '4px 8px', textAlign: 'center', fontSize: 11 }}>Верзија | Ver: <b>{headerVersion(st, rep.ver)}</b></td></tr></tbody></table>
            {cur.t === 'cover' && <>
              <div style={{ textAlign: 'center', marginTop: 70, fontSize: 17, color: PAGE.secondary, fontWeight: 700 }}>Протокол за верификација <span style={{ fontWeight: 400, fontSize: 14 }}>| Verification protocol</span></div>
              <div style={{ textAlign: 'center', marginTop: 14, fontSize: 29, color: PAGE.navy, fontWeight: 700, lineHeight: 1.2 }}>{rep.mk}</div><div style={{ textAlign: 'center', fontSize: 17, color: PAGE.navy, marginTop: 4 }}>{rep.en}</div>
              <div style={{ margin: '34px 0 22px', border: `1px solid ${PAGE.ruleLight}`, background: appr ? PAGE.approvedFill : PAGE.draftFill, textAlign: 'center', padding: 10 }}><div style={{ fontWeight: 700, fontSize: 15, color: appr ? PAGE.green : PAGE.red }}>{bandMk} | {bandEn}</div><div style={{ fontWeight: 700, fontSize: 13, marginTop: 4 }}>Верзија | Version: {hdrVer === rep.ver ? 'v' + rep.ver : hdrVer}{'     ·     '}Датум на важност | Effective date: {effectiveDisplay(st, R.eff)}</div></div>
              <div style={{ fontSize: 17, color: PAGE.navy, fontWeight: 700, margin: '8px 0 6px' }}>Информации за документот | Document information</div>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}><tbody>{[['Метода | Method', 'Ph. Eur. 2.2.32'], ['Инструмент | Instrument', 'QC-EQ-014'], ['Серии | Batches', 'P160012, P160022']].map(([a, b]) => <tr key={a}><td style={{ ...td, background: PAGE.label, color: PAGE.navy, fontWeight: 700, width: '32%' }}>{a}</td><td style={td}>{b}</td></tr>)}</tbody></table>
              <div style={{ fontSize: 17, color: PAGE.navy, fontWeight: 700, margin: '18px 0 6px' }}>Одобрување | Approval</div>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5 }}><tbody><tr>{['Дејство | Action', 'Име/Позиција | Name/Position', 'Датум | Date', 'Потпис | Signature'].map(h => <td key={h} style={navyTd}>{h}</td>)}</tr>
                {['Изготвил | Prepared', 'Прегледал | Reviewed (QA)', 'Одобрил | Approved (QC Manager)'].map(a => <tr key={a}><td style={td}>{a}</td><td style={td} /><td style={td} /><td style={{ ...td, height: 30 }} /></tr>)}</tbody></table>
              <div style={{ textAlign: 'center', marginTop: 16, fontSize: 11, color: PAGE.secondary, fontStyle: 'italic' }}>Контролиран документ | Controlled document</div></>}
            {cur.t === 'toc' && <>
              <div style={{ marginTop: 26, fontSize: 21, color: PAGE.navy, fontWeight: 700 }}>СОДРЖИНА <span style={{ color: PAGE.secondary, fontWeight: 400, fontSize: 16 }}>| Table of Contents</span></div>
              <div style={{ marginTop: 14, fontSize: 12, color: PAGE.secondary, fontStyle: 'italic' }}>Десен-клик → Ажурирај поле (Update Field) | Right-click → Update Field</div>
              <div style={{ marginTop: 22, display: 'flex', flexDirection: 'column', gap: 10, fontSize: 15, color: '#9aa5b1' }}>{blocks.filter(b => ['chapter', 'subsec', 'calc_step', 'entry_table', 'figure', 'execution_signoff'].includes(b.fn) && b.t !== 'cover').map((b, i) =>
                <div key={i} style={{ display: 'flex', gap: 8 }}><span style={{ paddingLeft: b.sub ? 24 : 0 }}>{b.mk} | {b.en}</span><span style={{ flex: 1, borderBottom: '1px dotted #c3cbd3', marginBottom: 5 }} /><span>{3 + Math.min(4, Math.floor(i / 1.5))}</span></div>)}</div></>}
            {cur.t === 'calc' && <>
              <H1 mk="2.  Метода" en="Method" />
              <div style={{ marginTop: 12 }}><span style={{ fontSize: 20, color: PAGE.navy, fontWeight: 700 }}>2.1  Губење при сушење</span><span style={{ color: PAGE.secondary, fontSize: 15 }}>  |  Loss on drying</span></div>
              <p style={{ fontSize: 14, textAlign: 'justify', lineHeight: 1.4, margin: '10px 0' }}>Мострата се суши до константна маса според Ph. Eur. 2.2.32. <span style={{ fontSize: 10.5, color: PAGE.secondary, fontStyle: 'italic' }}>| The sample is dried to constant mass per Ph. Eur. 2.2.32.</span></p>
              <div style={{ fontSize: 16, color: PAGE.navy, fontWeight: 700, marginTop: 16 }}>Пресметка <span style={{ color: PAGE.secondary, fontWeight: 400, fontStyle: 'italic', fontSize: 14 }}>| Calculation</span></div>
              {[['m₁ − m₂', 'm₁ − m₀'], [`${valid ? m1.toFixed(4).replace('.', ',') : R.m.m1} − ${valid ? m2.toFixed(4).replace('.', ',') : R.m.m2}`, `${valid ? m1.toFixed(4).replace('.', ',') : R.m.m1} − ${valid ? m0.toFixed(4).replace('.', ',') : R.m.m0}`]].map(([a, b], i) =>
                <div key={i} style={{ textAlign: 'center', fontFamily: "'Cambria Math',Cambria,serif", fontStyle: 'italic', fontSize: 20, margin: '14px 0', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8 }}>LOD = <span style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center' }}><span style={{ borderBottom: '1.5px solid #000', padding: '0 6px' }}>{a}</span><span style={{ padding: '0 6px' }}>{b}</span></span> × 100 %</div>)}
              <div style={{ margin: '10px 0 18px 12px', borderLeft: `6px solid ${PAGE.navy}`, background: '#EAF1F8', padding: '8px 14px', fontFamily: "'Cambria Math',Cambria,serif", fontStyle: 'italic', fontWeight: 700, color: PAGE.navy, fontSize: 21 }}>LOD = {lodMk} %<span style={{ fontFamily: 'Calibri,Carlito,sans-serif', fontStyle: 'normal', fontSize: 15, marginLeft: 14 }}>{!valid ? '' : pass ? '✓ NMT 12 %' : '✗ NMT 12 %'}</span></div>
              {R.stepSign && <Sign rows={['Извршил и внел сурови податоци | Executed & entered raw data (Operator)', 'Проверил и одобрил | Checked & approved (QC Department Manager)']} />}</>}
            {cur.t === 'eqn' && <><H1 mk={cur.mk} en={cur.en} /><div style={{ margin: '24px 0 18px 12px', borderLeft: `6px solid ${PAGE.navy}`, background: '#EAF1F8', padding: '8px 14px', fontFamily: "'Cambria Math',Cambria,serif", fontStyle: 'italic', fontWeight: 700, color: PAGE.navy, fontSize: 21 }}>{(cur.latex || '').replace(/\\bar\{x\}/g, 'x̄').replace(/\{,\}/g, ',').replace(/\\,/g, ' ').replace(/\\%/g, '%').replace(/\\[a-z]+/g, '')}</div></>}
            {cur.t === 'entry' && <>
              <H1 mk="3.  Сурови податоци" en="Raw data" />
              <div style={{ fontSize: 16, color: PAGE.navy, fontWeight: 700, margin: '16px 0 6px' }}>Мерења по реплика <span style={{ color: PAGE.secondary, fontWeight: 400, fontStyle: 'italic', fontSize: 14 }}>| Measurements per replicate</span></div>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}><tbody><tr>{['Реплика | Replicate', 'm₀ (g)', 'm₁ (g)', 'm₂ (g)', 'Потпис | Signature'].map(c => <td key={c} style={navyTd}>{c}</td>)}</tr>
                {Array.from({ length: R.rows }, (_, i) => <tr key={i}><td style={{ ...td, background: PAGE.label, color: PAGE.navy, fontWeight: 700 }}>R{i + 1}</td><td style={td} /><td style={td} /><td style={td} /><td style={{ ...td, height: 24 }} /></tr>)}</tbody></table>
              {R.sign && <Sign rows={['Извршил | Executed (Operator/Analyst)', 'Проверил | Checked (QC Department Manager)']} />}</>}
            {['text', 'figure', 'exec', 'note', 'bullet', 'minilabel', 'grid', 'databox'].includes(cur.t) && <>
              <H1 mk={cur.mk} en={cur.en} />
              {cur.t !== 'grid' && cur.t !== 'databox' && <p style={{ fontSize: cur.t === 'note' ? 12 : 14, textAlign: 'justify', lineHeight: 1.45, margin: '12px 0', fontWeight: cur.t === 'minilabel' ? 700 : 400 }}>{cur.t === 'bullet' ? '• ' : ''}{cur.mkText} {cur.enText && <span style={{ fontSize: 10.5, color: PAGE.secondary, fontStyle: 'italic' }}>| {cur.enText}</span>}</p>}
              {cur.t === 'figure' && <><div style={{ margin: '18px auto 6px', width: '85%', display: 'grid', placeItems: 'center' }}><Chart kind={cur.chart || 'guardband'} values={lods} width={560} height={300} /></div>
                <div style={{ textAlign: 'center', fontSize: 12 }}><b style={{ color: PAGE.navy }}>Слика | Figure — </b><i style={{ color: PAGE.secondary }}>{cur.mkText}</i>  |  <i style={{ color: PAGE.secondary }}>{cur.enText}</i></div>
                {R.data && <div style={{ fontSize: 10, color: PAGE.secondary, textAlign: 'center', marginTop: 6 }}>Податоци | Data: {R.data.name} · sha256 {R.data.sha256} · {R.data.modified}</div>}</>}
              {cur.t === 'grid' && <div style={{ display: 'grid', gridTemplateColumns: `repeat(${cur.ncols || 2},1fr)`, gap: '10px 18px', marginTop: 16, fontSize: 14 }}>{(cur.options || []).map((o, i) => <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'center' }}><span style={{ width: 16, height: 16, border: '1.5px solid #000', flex: 'none' }} />{o}</div>)}</div>}
              {cur.t === 'databox' && <div style={{ marginTop: 16, border: `1px solid ${cur.boxKind === 'status' ? PAGE.green : PAGE.red}`, background: cur.boxKind === 'status' ? PAGE.approvedFill : PAGE.draftFill, padding: '10px 14px', fontSize: 13 }}><b>{cur.mkText}</b> <span style={{ color: PAGE.secondary }}>| {cur.enText}</span>
                {R.data && <div style={{ fontSize: 11, color: PAGE.secondary, marginTop: 4 }}>{R.data.name} · sha256 {R.data.sha256} · {R.data.bytes} B · {R.data.modified}</div>}</div>}
              {cur.t === 'exec' && <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5, marginTop: 10 }}><tbody><tr>{['Дејство | Action', 'Име | Name', 'Датум | Date', 'Потпис | Signature'].map(h => <td key={h} style={navyTd}>{h}</td>)}</tr>
                {[[R.signoff.mk_exec, '____________________'], ['Прегледал (QA) | Reviewed (QA)', R.signoff.reviewer], ['Одобрил (Раководител КК) | Approved (QC Manager)', R.signoff.approver]].map(([a, n]) => <tr key={a}><td style={td}>{a}</td><td style={td}>{n}</td><td style={td} /><td style={{ ...td, height: 32 }} /></tr>)}</tbody></table>}</>}
            {cur.t !== 'cover' && <div style={{ position: 'absolute', right: 48, bottom: 22, fontSize: 15 }}>Page {pg} of 7</div>}
          </div>
        </div>
        <div style={{ position: 'absolute', left: 304, top: 16, width: 90, display: 'flex', flexDirection: 'column', gap: 10 }}>{stamps.map((s, i) => <Stamp key={i} s={s} line={false} w={90} />)}</div>
      </div>
    </div>
  </>;
}
