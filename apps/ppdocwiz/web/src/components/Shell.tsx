import { useEffect, useState, type ReactNode } from 'react';
import { ApiError } from '../api/types';
import { useApp, type Screen } from '../store/store';
import { C, DISPLAY, G, MONO, T, UI } from '../theme';
import { CreateMenu, NewDocSheet } from './Create';
import { Dot } from './ui';

const NAV: [Screen, string, 'c' | 'k'][] = [['builder', 'Builder', 'c'], ['chat', 'Agent chat', 'c'], ['quest', 'Questionnaire', 'c'], ['format', 'Formatter', 'c'], ['report', 'Reports', 'c'], ['library', 'Library', 'k'], ['jobs', 'Jobs', 'k'], ['verify', 'Verify', 'k'], ['preview', 'Preview', 'k'], ['fleet', 'Fleet & health', 'k']];
const CRUMB: Record<Screen, string> = { builder: '', chat: 'chat › allowlist › WHSOP_002_A02', quest: 'questionnaire › POST /workflows', format: 'formatter › labels_raw.docx → house style', library: 'library › docengine.documents', jobs: 'jobs › docengine.jobs', report: 'reports › QCSOP_031_A02 · pp_report', verify: 'verify › POST /build 422 · WHSOP_009_A01', preview: 'preview › QCSOP_031 · page 3 / 9', fleet: 'admin › gf_ fleet & health' };

function useViewport() {
  const [v, setV] = useState({ w: window.innerWidth, h: window.innerHeight });
  useEffect(() => { const f = () => setV({ w: window.innerWidth, h: window.innerHeight }); window.addEventListener('resize', f); return () => window.removeEventListener('resize', f); }, []);
  return v;
}

/** Polls both health routes and turns them into the three top-bar dots. */
function useHealth() {
  const { api, set, dataRev } = useApp();
  useEffect(() => {
    let live = true;
    const probe = async () => {
      const note: Record<string, string> = {};
      let h: { letta: boolean; pdf: boolean } | null = null, de: { db: boolean; letta: boolean } | null = null;
      try { h = await api.health(); } catch (e) { note.ppdocwiz = String((e as Error).message); }
      try { de = await api.deHealth(); } catch (e) { note.docengine = (e as ApiError).status ? `${(e as ApiError).status} · ${(e as Error).message}` : String((e as Error).message); }
      if (!live) return;
      if (h && !h.letta) note.letta = 'chat disabled: LETTA_BASE_URL not set';
      if (de && !de.letta) note.letta = 'DocEngine: Letta unavailable';
      if (de && !de.db) note.docengine = 'DocEngine storage unavailable';
      if (h && !h.pdf) note.pdf = 'no LibreOffice in ppdocwiz → PDF 501';
      set({ svc: {
        letta: !h ? 'idle' : h.letta && (!de || de.letta) ? 'ok' : 'bad',
        docengine: !de ? 'bad' : de.db ? 'ok' : 'warn',
        pdf: !h ? 'idle' : h.pdf ? 'ok' : 'warn', note,
      } });
    };
    probe(); const t = setInterval(probe, 15000);
    return () => { live = false; clearInterval(t); };
  }, [api, dataRev, set]);
}

export function Shell({ children }: { children: ReactNode }) {
  const s = useApp();
  const vp = useViewport();
  useHealth();
  const zoom = Math.min(1, vp.w / 1280, vp.h / 760);
  const crumb = s.screen === 'builder' ? `builder › ${s.bdoc.code || 'untitled'} · ${s.bdoc.status.replace('_', ' ')} v${s.bdoc.version}` : CRUMB[s.screen];
  const radius = s.tweaks.createStyle === 'pill' ? 999 : 6;
  const toggleCreate = (e: React.MouseEvent<HTMLButtonElement>) => {
    const el = e.currentTarget, root = el.closest('[data-pp-root]') as HTMLElement, rr = root.getBoundingClientRect(), r = el.getBoundingClientRect(), k = rr.width / root.offsetWidth || 1;
    const side = s.tweaks.createPlacement === 'sidebar';
    s.set({ createOpen: !s.createOpen, menuX: ((side ? r.right + 8 : r.left) - rr.left) / k, menuY: ((side ? r.top : r.bottom + 6) - rr.top) / k });
  };
  const createBtn = (side: boolean) => <button onClick={toggleCreate} className="pp-create" style={{ display: 'flex', gap: 7, alignItems: 'center', justifyContent: side ? 'center' : undefined, width: side ? '100%' : undefined, marginBottom: side ? 10 : 0, background: T.surface, color: '#fff', border: `1px solid ${T.focus}`, borderRadius: radius, padding: side ? '8px 12px' : '6px 14px', font: 'inherit', fontSize: 13, fontWeight: 700, cursor: 'pointer', whiteSpace: 'nowrap' }}>
    <span style={{ fontSize: 15, lineHeight: 1, color: C.run }}>＋</span>Create<span style={{ fontSize: 10, color: T.muted }}>{side ? '›' : '▾'}</span></button>;
  const dot = (label: string, st: keyof typeof s.svc & string) => <span title={s.svc.note[st] || (s.svc[st as 'letta'] === 'ok' ? 'ok' : 'probing…')} style={{ display: 'flex', gap: 5, alignItems: 'center' }}><Dot c={C[s.svc[st as 'letta']]} />{label}</span>;
  const pipeMsgC = s.busy ? C.run : s.pipeOk ? C.ok : C.bad;
  const STEPS = ['compose', 'build_from_md', 'pp_verify', 'gotenberg'];
  return (
    <div data-pp-root="1" style={{ width: vp.w / zoom, height: vp.h / zoom, zoom, overflow: 'hidden', position: 'relative', display: 'flex', flexDirection: 'column', background: T.bg, color: T.text, fontFamily: UI, fontSize: 14 }}>
      <div style={{ height: 48, flex: 'none', display: 'flex', alignItems: 'center', gap: 14, padding: '0 16px', borderBottom: `1px solid ${T.hair}` }}>
        <span style={{ fontFamily: DISPLAY, fontWeight: 700, letterSpacing: '.06em', color: '#fff', fontSize: 13 }}>PP/SUITE</span>
        {s.tweaks.createPlacement === 'topbar' && createBtn(false)}
        <span style={{ fontFamily: MONO, fontSize: 12, color: T.muted, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{crumb}</span>
        <span style={{ marginLeft: 12, background: T.surface, border: `1px solid ${T.control}`, borderRadius: 6, padding: '6px 12px', width: 300, flex: 'none', color: T.muted, fontFamily: MONO, fontSize: 12, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>⌘K  build · verify · open … · ask agent</span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 14, fontFamily: MONO, fontSize: 12, color: T.muted }}>
          {s.api.mode === 'mock' && <span title="All data is sample data; switch in Fleet & health" style={{ color: C.warn, border: `1px solid ${C.warn}`, borderRadius: 3, padding: '0 6px' }}>mock</span>}
          {dot('letta', 'letta')}{dot('docengine', 'docengine')}{dot('pdf', 'pdf')}
        </div>
        <button onClick={s.primary?.run} disabled={s.busy || s.primary?.disabled} className="pp-primary" style={{ background: T.navy, color: '#fff', border: `1px solid ${T.focus}`, borderRadius: 6, padding: '7px 16px', font: 'inherit', fontWeight: 700, cursor: 'pointer', opacity: s.primary ? 1 : .5 }}>{s.busy ? 'Running…' : s.primary?.label || 'Build ▸'}</button>
      </div>
      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        <nav style={{ width: 184, flex: 'none', borderRight: `1px solid ${T.hair}`, padding: '14px 10px', display: 'flex', flexDirection: 'column', gap: 2 }}>
          {s.tweaks.createPlacement === 'sidebar' && createBtn(true)}
          {(['c', 'k'] as const).map(g => <div key={g} style={{ display: 'contents' }}>
            <div style={{ fontFamily: MONO, fontSize: 10.5, letterSpacing: '.1em', color: T.faint, padding: g === 'c' ? '4px 10px 6px' : '16px 10px 6px' }}>{g === 'c' ? 'CREATE' : 'CONTROL'}</div>
            {NAV.filter(n => n[2] === g).map(([k, label]) => <div key={k} onClick={() => s.go(k)} className="pp-nav" style={{ padding: '8px 10px', borderRadius: 6, cursor: 'pointer', background: s.screen === k ? T.selected : 'transparent', color: s.screen === k ? '#fff' : T.secondary, fontWeight: s.screen === k ? 700 : 400 }}>{label}</div>)}
          </div>)}
          <div style={{ marginTop: 'auto', padding: 10, fontSize: 12, color: T.faint, lineHeight: 1.5 }}>Engine 1.6.2<br />{s.api.mode === 'mock' ? 'darko.s · QA' : 'session · cookie'}
            <div onClick={() => s.api.closeSession().then(() => s.set({ authed: false })).catch(e => s.flash(String(e.message)))} style={{ cursor: 'pointer', color: T.muted, marginTop: 4 }}>Sign out</div></div>
        </nav>
        <main style={{ flex: 1, minWidth: 0, display: 'flex', minHeight: 0 }}>{children}</main>
      </div>
      <div style={{ height: 40, flex: 'none', borderTop: `1px solid ${T.hair}`, background: T.deeper, display: 'flex', alignItems: 'center', gap: 6, padding: '0 16px', fontFamily: MONO, fontSize: 12 }}>
        <span style={{ color: T.faint, marginRight: 6 }}>PIPELINE</span><span style={{ color: '#fff', marginRight: 10 }}>{s.pipeDoc}</span>
        {s.pipe.map((st, i) => <span key={i} style={{ display: 'contents' }}>
          <span style={{ display: 'flex', gap: 6, alignItems: 'center', padding: '3px 10px', borderRadius: 4, border: `1px solid ${st === 'run' ? T.focus : st === 'bad' ? T.errBorder : T.hair}`, color: C[st] }}>{G[st]} {STEPS[i]}</span>
          <span style={{ color: T.control }}>→</span></span>)}
        <span style={{ color: pipeMsgC, marginLeft: 4, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.pipeMsg}</span>
        <span style={{ marginLeft: 'auto', color: T.muted, whiteSpace: 'nowrap' }}>agent {s.chatAgent} · <span style={{ color: s.busy ? C.run : T.secondary }}>{s.busy ? 'working' : 'idle'}</span></span>
      </div>
      <CreateMenu />
      <NewDocSheet />
      {s.toast && <div style={{ position: 'fixed', zIndex: 70, left: '50%', top: 8, transform: 'translateX(-50%)', whiteSpace: 'nowrap', background: T.okSurface, border: `1px solid ${T.okBorder}`, color: T.okText, borderRadius: 8, padding: '9px 16px', fontSize: 13, boxShadow: '0 10px 30px rgba(0,0,0,.4)' }}>{s.toast}</div>}
    </div>);
}

/** COVERAGE #1 — POST /api/session exchanges the key for an HttpOnly cookie; 401 bad key, 503 not configured. */
export function SignIn({ unconfigured }: { unconfigured?: boolean }) {
  const { api, set } = useApp();
  const [key, setKey] = useState(''), [err, setErr] = useState(''), [busy, setBusy] = useState(false);
  const submit = async () => {
    setBusy(true); setErr('');
    try { await api.openSession(key); set({ authed: true }); }
    catch (e) { const st = (e as ApiError).status; setErr(st === 401 ? '401 · bad key. The key is the PPDOCWIZ_API_KEY of this deployment.' : st === 503 ? '503 · PP Doc Wiz is not configured: PPDOCWIZ_API_KEY is unset on the server, so every route refuses.' : String((e as Error).message)); }
    finally { setBusy(false); }
  };
  return (
    <div style={{ height: '100vh', background: T.bg, color: T.text, fontFamily: UI, display: 'grid', placeItems: 'center' }}>
      <div style={{ width: 420, background: T.pane, border: `1px solid ${T.control}`, borderRadius: 12, boxShadow: '0 30px 70px rgba(0,0,0,.55)', padding: '26px 28px', display: 'flex', flexDirection: 'column', gap: 14 }}>
        <span style={{ fontFamily: DISPLAY, fontWeight: 700, letterSpacing: '.06em', color: '#fff', fontSize: 15 }}>PP/SUITE</span>
        <div style={{ color: T.secondary, fontSize: 13, lineHeight: 1.5 }}>Enter this deployment's API key. It is exchanged once for an HttpOnly session cookie (8 h); the key itself is never stored in the browser.</div>
        {unconfigured && <div style={{ background: T.errSurface, border: `1px solid ${T.errBorder}`, borderRadius: 6, padding: '8px 12px', color: T.errText, fontSize: 12.5 }}>503 · server not configured. Set PPDOCWIZ_API_KEY in /opt/stacks/ppdocwiz/.env and restart; until then every gated route refuses.</div>}
        <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}><span style={{ fontFamily: MONO, fontSize: 11.5, color: T.muted }}>PPDOCWIZ_API_KEY</span>
          <input type="password" autoFocus value={key} onChange={e => setKey(e.target.value)} onKeyDown={e => e.key === 'Enter' && submit()} style={{ background: T.deeper, border: `1px solid ${err ? C.bad : T.control}`, borderRadius: 6, padding: '9px 11px', color: '#fff', outline: 'none', fontFamily: MONO }} /></label>
        {err && <div style={{ fontFamily: MONO, fontSize: 12, color: C.bad, lineHeight: 1.45 }}>{err}</div>}
        <button onClick={submit} disabled={busy || !key} style={{ background: key ? T.navy : T.control, color: '#fff', border: 0, borderRadius: 6, padding: 10, font: 'inherit', fontWeight: 700, cursor: 'pointer' }}>{busy ? 'Signing in…' : 'POST /api/session ▸'}</button>
        <div style={{ fontSize: 11.5, color: T.faint, textAlign: 'center' }}>{api.mode === 'mock' ? 'mock mode: any key works except "bad"' : 'loopback / Traefik only · SameSite=Strict cookie'}</div>
      </div>
    </div>);
}
