// Formula dialog (04.11.2026): write LaTeX, see whether the ENGINE accepts it, see how it prints, insert it as Markdown.
// The check and the picture come from the server (pp_math / pandoc, the same converter and renderer as the document),
// so what is shown here is what the build produces; a browser maths library would be a second engine.
import { useEffect, useRef, useState } from 'react';
import { formulaMarkdown, localProblems, SNIPPETS, TEMPLATES, type InsertMode } from '../lib/latex';
import { useApp } from '../store/store';
import { C, MONO, T } from '../theme';
import { Banner, Btn, Caps, Seg, Tag } from './ui';

type Check = { state: 'idle' | 'checking' | 'ok' | 'bad'; msg: string };
type Pic = { state: 'none' | 'loading' | 'ok' | 'unavailable' | 'bad'; src?: string; msg?: string };

export function FormulaDialog({ onInsert, onClose, initial = '' }: { onInsert: (markdown: string) => void; onClose: () => void; initial?: string }) {
  const { api } = useApp();
  const [tex, setTex] = useState(initial), [mode, setMode] = useState<InsertMode>('display');
  const [check, setCheck] = useState<Check>({ state: 'idle', msg: '' }), [pic, setPic] = useState<Pic>({ state: 'none' });
  const ta = useRef<HTMLTextAreaElement>(null), seq = useRef(0);
  const display = mode !== 'inline';

  // The engine's verdict (fast), then the picture (slow: it goes through the PDF renderer). Each round is dropped if a newer one started.
  useEffect(() => {
    const mine = ++seq.current, local = localProblems(tex);
    if (!tex.trim()) { setCheck({ state: 'idle', msg: '' }); setPic({ state: 'none' }); return; }
    if (local.length) { setCheck({ state: 'bad', msg: local.join('; ') }); setPic({ state: 'none' }); return; }
    setCheck({ state: 'checking', msg: '' });
    const t1 = setTimeout(async () => {
      try {
        const r = await api.checkEquations(display ? `$$${tex.trim()}$$` : `$${tex.trim()}$`);
        if (mine !== seq.current) return;
        const f = r.formulas[0];
        if (!r.engine.ok) { setCheck({ state: 'bad', msg: 'the equation engine is not available on the server: ' + r.engine.backend }); setPic({ state: 'none' }); return; }
        if (!f) { setCheck({ state: 'bad', msg: 'not read as a formula (a $ followed by a space, or a digit after the closing $?)' }); setPic({ state: 'none' }); return; }
        if (!f.ok) { setCheck({ state: 'bad', msg: f.error }); setPic({ state: 'none' }); return; }
        setCheck({ state: 'ok', msg: '' }); setPic({ state: 'loading' });
        try {
          const png = await api.previewEquation(tex.trim(), display);
          if (mine !== seq.current) return;
          setPic(png ? { state: 'ok', src: 'data:image/png;base64,' + png } : { state: 'unavailable' });
        } catch (e) { if (mine === seq.current) setPic({ state: 'bad', msg: String((e as Error).message || e) }); }
      } catch (e) { if (mine === seq.current) { setCheck({ state: 'bad', msg: String((e as Error).message || e) }); setPic({ state: 'none' }); } }
    }, 450);
    return () => clearTimeout(t1);
  }, [tex, display, api]);

  const put = (s: string) => {
    const el = ta.current, a = el?.selectionStart ?? tex.length, b = el?.selectionEnd ?? tex.length;
    setTex(tex.slice(0, a) + s + tex.slice(b));
    requestAnimationFrame(() => { el?.focus(); const c = a + s.length; el?.setSelectionRange(c, c); });
  };
  const ready = check.state === 'ok';
  const insert = () => { if (ready) { onInsert(formulaMarkdown(tex, mode)); onClose(); } };

  return <div role="dialog" aria-label="Insert formula" onClick={onClose} onKeyDown={e => { if (e.key === 'Escape') onClose(); if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) insert(); }}
    style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.38)', display: 'grid', placeItems: 'center', zIndex: 60 }}>
    <div onClick={e => e.stopPropagation()} style={{ width: 'min(680px, 94vw)', maxHeight: '92vh', overflow: 'auto', background: T.surface, border: `1px solid ${T.control}`, borderRadius: 10, padding: '16px 18px', display: 'flex', flexDirection: 'column', gap: 12, boxShadow: '0 10px 40px rgba(0,0,0,.25)' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
        <b style={{ color: T.strong, fontSize: 15 }}>Σ Formula</b><Tag>LaTeX → native Word equation</Tag>
        <span onClick={onClose} style={{ marginLeft: 'auto', cursor: 'pointer', color: T.muted, fontSize: 18 }} title="Close (Esc)">×</span>
      </div>

      <div><Caps style={{ marginBottom: 5 }}>START FROM</Caps>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>{TEMPLATES.map(t => <span key={t.label} onClick={() => { setTex(t.tex); requestAnimationFrame(() => ta.current?.focus()); }}
          style={{ cursor: 'pointer', fontSize: 12, border: `1px solid ${T.control}`, borderRadius: 14, padding: '2px 10px', color: T.secondary }}>{t.label}</span>)}</div></div>

      <div><Caps style={{ marginBottom: 5 }}>INSERT</Caps>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>{SNIPPETS.map(s => <span key={s.tex} title={s.title} onClick={() => put(s.tex)}
          style={{ cursor: 'pointer', minWidth: 34, textAlign: 'center', fontSize: 13, border: `1px solid ${T.control}`, borderRadius: 5, padding: '3px 8px', color: T.strong, background: T.deeper }}>{s.label}</span>)}</div></div>

      <textarea ref={ta} autoFocus value={tex} onChange={e => setTex(e.target.value)} spellCheck={false} rows={3} placeholder={'u_c=\\sqrt{\\sum_i u_i^2}'}
        style={{ background: T.deeper, border: `1px solid ${check.state === 'bad' ? C.bad : check.state === 'ok' ? C.ok : T.control}`, borderRadius: 6, padding: 10, color: T.text, fontFamily: MONO, fontSize: 13, lineHeight: 1.6, resize: 'vertical', outline: 'none' }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <Seg size={12} pad="4px 10px" items={[['display', 'Display · own line'], ['inline', 'Inline · in text'], ['eq', 'Formula panel · [[EQ]]']]} value={mode} onPick={setMode} />
        <span style={{ fontSize: 12, color: check.state === 'ok' ? C.ok : check.state === 'bad' ? C.bad : T.muted }}>
          {check.state === 'ok' ? '✓ the engine accepts it' : check.state === 'bad' ? '✗ ' + check.msg : check.state === 'checking' ? '… checking with the engine' : 'type a formula'}</span>
      </div>

      <div style={{ minHeight: 84, border: `1px solid ${T.hair}`, borderRadius: 6, background: '#fff', display: 'grid', placeItems: 'center', padding: 10 }}>
        {pic.state === 'ok' && pic.src ? <img alt="how the formula prints" src={pic.src} style={{ maxWidth: '100%', imageRendering: 'auto' }} />
          : pic.state === 'loading' ? <span style={{ color: '#64748b', fontSize: 12 }}>drawing it the way the PDF will…</span>
          : pic.state === 'unavailable' ? <span style={{ color: '#64748b', fontSize: 12 }}>The picture is drawn by the server's PDF renderer; this mode has none. The check above is still the engine's.</span>
          : pic.state === 'bad' ? <span style={{ color: C.bad, fontSize: 12 }}>{pic.msg}</span>
          : <span style={{ color: '#94a3b8', fontSize: 12 }}>preview</span>}
      </div>

      <Banner kind="info">Names upright: <code style={{ fontFamily: MONO }}>\text{'{THC}'}</code>, <code style={{ fontFamily: MONO }}>\mathrm{'{RSD}'}</code> · decimal comma <code style={{ fontFamily: MONO }}>0{'{,}'}877</code> · a dollar sign in text is <code style={{ fontFamily: MONO }}>\$</code> · an unknown command stops the build instead of printing LaTeX. Terms such as THC, CBD, HPLC stay in English.</Banner>

      <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
        <Btn primary={false} onClick={onClose}>Cancel</Btn>
        <Btn disabled={!ready} onClick={insert} title="Ctrl+Enter">Insert</Btn>
      </div>
    </div>
  </div>;
}
