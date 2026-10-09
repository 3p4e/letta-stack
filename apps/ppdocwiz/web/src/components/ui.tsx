import type { CSSProperties, ReactNode } from 'react';
import { C, DISPLAY, MONO, T, TINT, type Status } from '../theme';

// ---- margin stamps (handoff README · Margin stamps) ----
export interface StampSpec { t: string; d: string; s: Status; top: number; rot: string }
export const stamp = (t: string, d: string, s: Status, top: number, rot: string): StampSpec => ({ t, d, s, top, rot });

const SIZES = {
  sm: { line: 10, w: 100, pad: '4px 6px', r: 4, tf: 9.5, df: 11 },
  md: { line: 14, w: 126, pad: '5px 8px', r: 5, tf: 10, df: 11.5 },
  lg: { line: 18, w: 170, pad: '6px 9px', r: 5, tf: 11, df: 12 },
};

export function Stamp({ s, size = 'sm', w, line = true }: { s: StampSpec; size?: keyof typeof SIZES; w?: number; line?: boolean }) {
  const z = SIZES[size], c = C[s.s];
  return (
    <div style={{ display: 'flex', alignItems: 'center' }}>
      {line && <span style={{ width: z.line, height: 1.5, background: c, flex: 'none' }} />}
      <div style={{ border: `1.5px solid ${c}`, color: c, background: TINT[s.s], borderRadius: z.r, padding: z.pad, transform: `rotate(${s.rot})`, width: w ?? z.w }}>
        <div style={{ fontFamily: DISPLAY, fontWeight: 700, fontSize: z.tf, letterSpacing: '.05em' }}>{s.t}</div>
        <div style={{ fontSize: z.df, lineHeight: 1.25 }}>{s.d}</div>
      </div>
    </div>);
}

/** Absolutely-positioned column of stamps to the right of a page preview. */
export function StampRail({ stamps, size = 'sm', width, w }: { stamps: StampSpec[]; size?: keyof typeof SIZES; width: number; w?: number }) {
  return (
    <div style={{ position: 'absolute', left: '100%', top: 0, width, height: '100%' }}>
      {stamps.map((s, i) => <div key={i} style={{ position: 'absolute', left: 0, top: s.top }}><Stamp s={s} size={size} w={w} /></div>)}
    </div>);
}

/** Lay stamps out top-down from their desired positions so they never overlap. */
export function spread(stamps: StampSpec[], gap: number): StampSpec[] {
  let last = -Infinity;
  return [...stamps].sort((a, b) => a.top - b.top).map(s => { const top = Math.max(s.top, last + gap); last = top; return { ...s, top }; });
}

// ---- controls ----
export function Seg<K extends string>({ items, value, onPick, size = 13, pad = '5px 12px', fill, style }: { items: [K, string][]; value: K; onPick: (k: K) => void; size?: number; pad?: string; fill?: boolean; style?: CSSProperties }) {
  return (
    <div style={{ display: 'flex', background: T.deeper, border: `1px solid ${T.control}`, borderRadius: 6, padding: 2, fontSize: size, ...style }}>
      {items.map(([k, label]) => (
        <span key={k} onClick={() => onPick(k)} style={{ flex: fill ? 1 : undefined, textAlign: 'center', whiteSpace: 'nowrap', padding: pad, borderRadius: 4, cursor: 'pointer', background: value === k ? T.navy : 'transparent', color: value === k ? '#fff' : T.secondary }}>{label}</span>))}
    </div>);
}

export const Caps = ({ children, style }: { children: ReactNode; style?: CSSProperties }) =>
  <div style={{ fontFamily: MONO, fontSize: 10.5, color: T.faint, letterSpacing: '.1em', ...style }}>{children}</div>;

export const Sep = () => <span style={{ color: C.warn, fontFamily: MONO }}>|||</span>;

export function PaneHead({ title, right }: { title: ReactNode; right?: ReactNode }) {
  return (
    <div style={{ height: 42, flex: 'none', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 14px', fontSize: 12, color: T.muted, borderBottom: `1px solid ${T.hair}` }}>
      <b style={{ color: '#fff', fontSize: 13 }}>{title}</b><span>{right}</span>
    </div>);
}

export function Btn({ children, onClick, primary = true, disabled, style, title }: { children: ReactNode; onClick?: () => void; primary?: boolean; disabled?: boolean; style?: CSSProperties; title?: string }) {
  return <button title={title} disabled={disabled} onClick={disabled ? undefined : onClick} className={primary ? 'pp-btn' : 'pp-btn-ghost'} style={{
    background: disabled ? T.control : primary ? T.navy : 'transparent', color: primary ? '#fff' : T.text, border: primary ? 0 : `1px solid ${T.control}`,
    borderRadius: 6, padding: '8px 14px', font: 'inherit', fontWeight: primary ? 700 : 400, cursor: disabled ? 'not-allowed' : 'pointer', whiteSpace: 'nowrap', ...style,
  }}>{children}</button>;
}

export const Tag = ({ children, c = T.secondary, style }: { children: ReactNode; c?: string; style?: CSSProperties }) =>
  <span style={{ fontSize: 11, whiteSpace: 'nowrap', border: `1px solid ${c === T.secondary ? T.control : c}`, borderRadius: 3, padding: '1px 6px', color: c, ...style }}>{children}</span>;

export const DefTag = () => <span style={{ fontSize: 10, color: C.ok, border: `1px solid ${T.okBorder}`, borderRadius: 3, padding: '0 4px' }}>default</span>;

export function Banner({ kind, children, style }: { kind: 'err' | 'ok' | 'warn' | 'info'; children: ReactNode; style?: CSSProperties }) {
  const k = { err: [T.errSurface, T.errBorder, T.errText], ok: [T.okSurface, T.okBorder, T.okText], warn: [T.warnSurface, '#6b5326', '#f5d6a1'], info: [T.surface, T.control, T.secondary] }[kind];
  return <div style={{ background: k[0], border: `1px solid ${k[1]}`, borderRadius: 6, padding: '8px 12px', color: k[2], fontSize: 12.5, lineHeight: 1.45, ...style }}>{children}</div>;
}

export function Input({ value, onChange, placeholder, bad, style, mono, onKeyDown }: { value: string; onChange: (v: string) => void; placeholder?: string; bad?: boolean; style?: CSSProperties; mono?: boolean; onKeyDown?: (e: React.KeyboardEvent<HTMLInputElement>) => void }) {
  return <input value={value} placeholder={placeholder} onKeyDown={onKeyDown} onChange={e => onChange(e.target.value)} style={{ background: T.deeper, border: `1px solid ${bad ? C.bad : T.control}`, borderRadius: 5, padding: '6px 8px', color: '#fff', outline: 'none', minWidth: 0, fontFamily: mono ? MONO : undefined, ...style }} />;
}

export const Kv = ({ rows, cols = '110px minmax(0,1fr)' }: { rows: [string, ReactNode, string?][]; cols?: string }) => (
  <div style={{ background: T.deeper, border: `1px solid ${T.hair}`, borderRadius: 6, padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 5, fontFamily: MONO, fontSize: 11.5 }}>
    {rows.map(([k, v, c], i) => <div key={i} style={{ display: 'grid', gridTemplateColumns: cols, gap: 8 }}><span style={{ color: T.muted }}>{k}</span><span style={{ color: c || T.text, wordBreak: 'break-word' }}>{v}</span></div>)}
  </div>);

export function Avatar({ size = 28, filled = true }: { size?: number; filled?: boolean }) {
  return <span style={{ width: size, height: size, borderRadius: '50%', background: filled ? T.navy : T.surface, border: filled ? 0 : `1px solid ${T.focus}`, color: filled ? '#fff' : C.run, display: 'grid', placeItems: 'center', fontFamily: DISPLAY, fontWeight: 700, fontSize: size > 26 ? 11 : 10, flex: 'none' }}>gf</span>;
}

// ---- Markdown syntax colouring (handoff README · Builder · Source mode) ----
/** Colour one line of the engine's bilingual Markdown. */
export function MdLine({ text }: { text: string }) {
  if (/^<!--HEADERDATA|^-->$/.test(text)) return <span style={{ color: T.comment }}>{text}</span>;
  const hd = /^([a-z_]+):\s(.*)$/.exec(text);
  if (hd) return <><span style={{ color: T.secondary }}>{hd[1]}:</span> {hd[2]}</>;
  if (/^#{1,3}\s/.test(text)) return <span style={{ color: C.run, fontWeight: 700 }}>{text}</span>;
  const parts = text.split(/(\[\[\/?[A-Z]+(?::[a-z]+)?\]\]|\|\|\||~~)/g);
  return <>{parts.map((p, i) => /^\[\[/.test(p) ? <span key={i} style={{ color: T.purple }}>{p}</span> : p === '|||' || p === '~~' ? <span key={i} style={{ color: C.warn }}>{p}</span> : <span key={i}>{p}</span>)}</>;
}

/** Monospace code block with gutter. `hl` lines get the selection background. */
export function CodeView({ lines, hl = [], marks = {}, style, onLine }: { lines: string[]; hl?: number[]; marks?: Record<number, { msg: string; c: string }>; style?: CSSProperties; onLine?: (n: number) => void }) {
  return (
    <div style={{ background: T.surface, border: `1px solid ${T.hair}`, borderRadius: 6, padding: '12px 0', fontFamily: MONO, fontSize: 12.5, lineHeight: 1.75, overflow: 'auto', display: 'grid', gridTemplateColumns: '40px minmax(0,1fr)', alignContent: 'start', ...style }}>
      <div style={{ color: T.faint, textAlign: 'right', paddingRight: 12 }}>{lines.map((_, i) => <div key={i} style={{ minHeight: '1.75em' }}>{i + 1}</div>)}</div>
      <div>{lines.map((l, i) => {
        const n = i + 1, m = marks[n];
        return <div key={i} onClick={onLine ? () => onLine(n) : undefined} style={{ whiteSpace: 'pre', minHeight: '1.75em', background: hl.includes(n) ? T.selected : m ? T.warnSurface : 'transparent', cursor: onLine ? 'text' : undefined, paddingRight: 8 }}>
          {m ? <span style={{ color: m.c }}>{l}</span> : <MdLine text={l} />}{m ? <span style={{ color: m.c }}>{'  ◂ ' + m.msg}</span> : null}
        </div>;
      })}</div>
    </div>);
}

export function Dot({ c, size = 7 }: { c: string; size?: number }) {
  return <span style={{ width: size, height: size, borderRadius: '50%', background: c, flex: 'none', display: 'inline-block' }} />;
}
