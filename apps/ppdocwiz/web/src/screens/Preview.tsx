// Preview (handoff §9). Blocks are measured from the rendered page; picking one opens its line in Builder.
import { useState } from 'react';
import { PPPage, type AnchorMap } from '../components/PPPage';
import { Seg, stamp, StampRail } from '../components/ui';
import { SAMPLE_SOP } from '../data/samples';
import { composeLines } from '../lib/compose';
import { usePrimary } from '../lib/usePrimary';
import { useApp } from '../store/store';
import { MONO, T } from '../theme';

const ZOOM = .58;
const lines = composeLines(SAMPLE_SOP);
const ZONES = ['header', ...SAMPLE_SOP.sections.map((_, i) => `s${i}`)];
// The SOP body is one table, so sections are a heading row + body rows: group them under s{i}.
const sopZones = (m: AnchorMap): AnchorMap => {
  const out: AnchorMap = { header: m.header };
  SAMPLE_SOP.sections.forEach((_, i) => { const parts = Object.entries(m).filter(([k]) => k === `s${i}t` || k.startsWith(`s${i}b`)).map(([, v]) => v);
    if (parts.length) { const top = Math.min(...parts.map(p => p.top)), bot = Math.max(...parts.map(p => p.top + p.height)); out[`s${i}`] = { top, height: bot - top }; } });
  return out;
};

export function Preview() {
  const { go, set, flash, run } = useApp();
  const [lens, setLens] = useState<'mk' | 'both' | 'en'>('both');
  const [sel, setSel] = useState('s0');
  const [map, setMap] = useState<AnchorMap>({});
  const zones = sopZones(map);
  const si = sel === 'header' ? -1 : +sel.slice(1), s = SAMPLE_SOP.sections[si];
  const line = si < 0 ? 1 : 1 + lines.findIndex(l => l.ref.section === si && l.ref.block === undefined);
  const b0 = s?.blocks[0];
  const pv = si < 0 ? { label: 'header block · HEADERDATA', src1: '<!--HEADERDATA', src2: `code: ${SAMPLE_SOP.code} · version: ${SAMPLE_SOP.version} · doctype: SOP`, font: 'Arial Narrow 15 pt bold caps', head: '—' }
    : { label: `section ${s.num} · ${s.en.toLowerCase()}${b0?.type === 'table' ? ' table' : ''}`, src1: lines[line - 1].text, src2: lines[line]?.text.slice(0, 64) + (lines[line]?.text.length > 64 ? '…' : ''), font: b0?.type === 'table' ? 'Calibri 9 pt (table)' : 'Calibri 10.5 pt', head: b0?.type === 'table' ? 'navy header row #2B547E' : 'Calibri 11.5 pt bold' };
  usePrimary('Build ▸', () => run('QCSOP_031', async () => ({ ok: true })));
  const jump = () => { set({ bdoc: structuredClone(SAMPLE_SOP), bdocIsSample: false, hlLine: line, builderMode: 'src' }); go('builder'); flash(`Jumped to ${SAMPLE_SOP.code}.md line ${line}`); };
  const top = (zones[sel]?.top ?? 0) * ZOOM;
  const thumb = (n: number, cur?: boolean) => <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
    <div style={{ opacity: cur ? 1 : .7, outline: cur ? '2px solid #7fb2e5' : undefined, outlineOffset: 2 }}><PPPage doc={SAMPLE_SOP} zoom={.121} page={n} pages={9} sopPage={n === 1 ? 'title' : 'body'} shadow={false} /></div>
    <span style={{ fontSize: 11, color: cur ? '#fff' : T.muted }}>{n}</span></div>;
  return <>
    <div style={{ width: 150, flex: 'none', borderRight: `1px solid ${T.hair}`, background: T.pane, padding: '14px 0', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, overflow: 'hidden' }}>
      <div style={{ fontSize: 12, color: T.muted }}>QCSOP_031 · 9 pp</div>{thumb(2)}{thumb(3, true)}{thumb(4)}</div>
    <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', background: T.deep }}>
      <div style={{ height: 42, flex: 'none', display: 'flex', alignItems: 'center', gap: 12, padding: '0 14px', borderBottom: `1px solid ${T.hair}`, fontSize: 13 }}>
        <span style={{ color: T.muted }}>Language lens</span><Seg items={[['mk', 'МК'], ['both', 'МК ||| EN'], ['en', 'EN']]} value={lens} onPick={setLens} pad="4px 12px" />
        <span style={{ marginLeft: 'auto', fontFamily: MONO, fontSize: 12, color: T.muted }}>.docx ⇄ Gotenberg PDF · parity 100 %</span></div>
      <div style={{ flex: 1, minHeight: 0, position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', left: '50%', top: 20, marginLeft: -290, width: 460 }}>
          <PPPage doc={SAMPLE_SOP} zoom={ZOOM} onLayout={setMap} extraBoxes={zones} zones={ZONES.filter(z => z !== sel)} highlights={[{ anchor: sel, kind: 'sel' }]} onPick={a => setSel(a === 'header' ? 'header' : ZONES.includes(a) ? a : ('s' + (/^s(\d+)/.exec(a)?.[1] ?? 0)))}>
            <div style={{ position: 'absolute', top: 100, bottom: 60, left: 48, width: 349, background: 'rgba(12,22,33,.55)', opacity: lens === 'en' ? 1 : 0, pointerEvents: 'none', transition: 'opacity .15s' }} />
            <div style={{ position: 'absolute', top: 100, bottom: 60, right: 48, width: 349, background: 'rgba(12,22,33,.55)', opacity: lens === 'mk' ? 1 : 0, pointerEvents: 'none', transition: 'opacity .15s' }} />
          </PPPage>
          <StampRail size="md" width={150} stamps={[stamp('SOURCE · L' + line, pv.src1.slice(0, 40), 'run', Math.round(top), '-1.5deg'), stamp('FONT FLOOR', 'min 9 pt on this page', 'ok', Math.max(400, top + 90), '1deg'), stamp('PDF PARITY', 'Gotenberg = .docx', 'ok', Math.max(480, top + 170), '-1deg')]} />
        </div>
      </div>
    </div>
    <div style={{ width: 320, flex: 'none', borderLeft: `1px solid ${T.hair}`, background: T.pane, padding: 16, display: 'flex', flexDirection: 'column', gap: 12, fontSize: 13 }}>
      <b style={{ color: '#fff', fontSize: 14 }}>Inspector</b>
      <div style={{ color: T.secondary }}>Selected: {pv.label}</div>
      <div style={{ fontFamily: MONO, fontSize: 10.5, color: T.faint, letterSpacing: '.1em' }}>SOURCE · {SAMPLE_SOP.code}.md : {line}</div>
      <div style={{ background: T.deeper, border: `1px solid ${T.hair}`, borderRadius: 6, padding: 10, fontFamily: MONO, fontSize: 11.5, lineHeight: 1.6, color: T.text, wordBreak: 'break-word' }}><span style={{ color: '#7fb2e5' }}>{pv.src1}</span><div>{pv.src2}</div></div>
      <div style={{ fontFamily: MONO, fontSize: 10.5, color: T.faint, letterSpacing: '.1em' }}>RESOLVED STYLE</div>
      <div style={{ display: 'grid', gridTemplateColumns: '96px 1fr', gap: '6px 8px', fontSize: 12.5 }}><span style={{ color: T.muted }}>Font</span><span>{pv.font}</span><span style={{ color: T.muted }}>Heading</span><span>{pv.head}</span><span style={{ color: T.muted }}>Shading</span><span><span style={{ display: 'inline-block', width: 10, height: 10, background: '#E8E8E8', verticalAlign: 'middle' }} /> #E8E8E8 · clear</span><span style={{ color: T.muted }}>Divider</span><span>0.5 pt #000 between columns</span><span style={{ color: T.muted }}>Align</span><span>justify</span></div>
      <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: 6 }}><button onClick={jump} style={{ background: T.navy, color: '#fff', border: 0, borderRadius: 6, padding: 9, font: 'inherit', fontWeight: 700, cursor: 'pointer' }}>Open line {line} in Builder →</button><div style={{ fontSize: 12, color: T.muted, lineHeight: 1.45, textAlign: 'center' }}>Click any block on the page to inspect it.</div></div>
    </div>
  </>;
}
