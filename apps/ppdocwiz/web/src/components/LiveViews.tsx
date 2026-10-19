// Live-mode views for screens whose mock version is a scripted sample. In live mode a screen
// shows only what this session really built, or says plainly that there is nothing yet.
import type { ReactNode } from 'react';
import { usePrimary } from '../lib/usePrimary';
import { lineColor } from '../lib/verify';
import { useApp } from '../store/store';
import { C, G, MONO, T } from '../theme';
import { Banner, PaneHead } from './ui';

export function EmptyState({ title, children }: { title: string; children: ReactNode }) {
  return <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 40 }}>
    <div style={{ maxWidth: 520, background: T.surface, border: `1px solid ${T.control}`, borderRadius: 10, padding: '22px 26px', lineHeight: 1.55 }}>
      <div style={{ fontWeight: 700, color: '#fff', fontSize: 16, marginBottom: 8 }}>{title}</div>
      <div style={{ color: T.secondary, fontSize: 13.5 }}>{children}</div>
    </div>
  </div>;
}

/** A ribbon over a panel that has no backend yet, so its content is never mistaken for real data. */
export function SampleRibbon({ why }: { why: string }) {
  return <Banner kind="warn" style={{ margin: '10px 14px 0', fontSize: 12.5 }}><b>Sample content, not connected.</b> {why}</Banner>;
}

const CHECKS: [string, (r: string) => boolean][] = [
  ['Structure', r => /paragraphs \d+/.test(r)],
  ['Font floor', r => !/min font[^\n]*FAIL/.test(r)],
  ['Render env', r => !/render environment FAIL/.test(r)],
  ['Glyph coverage', r => !/glyph coverage FAIL/.test(r)],
  ['Bilingual MK+EN', r => !/bilingual[^\n]*(FAIL|WARN)/.test(r)],
  ['Fidelity §5A', r => !/FIDELITY[^\n]*FAIL/.test(r)],
];

export function VerifyLive() {
  const { lastBuild: b, go } = useApp();
  usePrimary('Open Builder ▸', () => go('builder'));
  if (!b) return <EmptyState title="Nothing verified in this session yet">
    Every build runs <code>pp_verify</code>. Build a document in the Builder and its gate report appears here: the checks, the full report and, on PASS, the downloads.
  </EmptyState>;
  const lines = b.verify.split('\n').filter(Boolean);
  return <>
    <div style={{ width: 236, flex: 'none', borderRight: `1px solid ${T.hair}`, background: T.pane, padding: '14px 10px', display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
      <div style={{ padding: '0 6px 8px' }}><b style={{ color: '#fff' }}>Gate checks</b><div style={{ fontSize: 12, color: T.muted }}>{b.code} · built {b.at}</div></div>
      {CHECKS.map(([label, f]) => { const ok = b.verify ? f(b.verify) : false; return <div key={label} style={{ padding: '8px 10px', borderRadius: 6, display: 'grid', gridTemplateColumns: '16px 1fr auto', gap: 8, background: ok ? 'transparent' : 'rgba(224,122,111,.12)' }}>
        <span style={{ color: ok ? C.ok : C.bad, fontWeight: 700 }}>{ok ? G.ok : G.bad}</span><span>{label}</span><span style={{ color: ok ? C.ok : C.bad, fontFamily: MONO, fontSize: 11 }}>{ok ? 'OK' : 'FAIL'}</span></div>; })}
    </div>
    <div style={{ flex: 1, minWidth: 0, padding: '18px 22px', display: 'flex', flexDirection: 'column', gap: 14, overflow: 'auto' }}>
      {b.ok ? <Banner kind="ok" style={{ borderRadius: 8, padding: '11px 14px', fontSize: 14 }}>Gate passed · <a href={b.docx}>.docx</a> · <a href={b.pdf}>.pdf</a></Banner>
        : <Banner kind="err" style={{ borderRadius: 8, padding: '11px 14px', fontSize: 14 }}>Rejected and <b>not saved</b>. A FAIL build is deleted and never offered for download.</Banner>}
      <div style={{ background: T.deeper, border: `1px solid ${T.hair}`, borderRadius: 8, padding: '14px 16px', fontFamily: MONO, fontSize: 12.5, lineHeight: 1.75, color: T.secondary, overflow: 'auto' }}>
        {lines.length ? lines.map((l, i) => <div key={i} style={{ whiteSpace: 'pre', color: lineColor(l), fontWeight: l.startsWith('RESULT') ? 700 : 400 }}>{l}</div>)
          : <div>No report returned (the build failed before pp_verify ran).</div>}
      </div>
    </div>
  </>;
}

export function PreviewLive() {
  const { lastBuild: b, go } = useApp();
  usePrimary('Open Builder ▸', () => go('builder'));
  if (!b || !b.ok || !b.pdf) return <EmptyState title="No built document to preview yet">
    The preview shows the PDF of the last document that passed the gate in this session. Build one in the Builder.
  </EmptyState>;
  return <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
    <PaneHead title={`${b.code} · PDF`} right={<a href={b.pdf}>download</a>} />
    <iframe title="preview" src={`${b.pdf}?inline=1`} style={{ flex: 1, border: 0, background: '#fff' }} />
  </div>;
}

/** Wraps a screen whose content has no backend in live mode under a SampleRibbon. */
export function WithRibbon({ on, why, children }: { on: boolean; why: string; children: ReactNode }) {
  if (!on) return <>{children}</>;
  return <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
    <SampleRibbon why={why} />
    <div style={{ flex: 1, minHeight: 0, display: 'flex' }}>{children}</div>
  </div>;
}
