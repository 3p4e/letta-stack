import { useEffect, useRef, useState, type ReactNode } from 'react';
import { ApiError } from '../api/types';
import { useApp, type Screen } from '../store/store';
import { C, DISPLAY, G, MONO, T, UI } from '../theme';
import { CreateMenu, NewDocSheet } from './Create';
import { Dot, Seg, press } from './ui';
import { tr } from '../lib/i18n';

const NAV: [Screen, string, 'c' | 'k'][] = [['flow', 'Workflow', 'c'], ['builder', 'Builder', 'c'], ['chat', 'Agent chat', 'c'], ['format', 'Formatter', 'c'], ['report', 'Reports', 'c'], ['library', 'Library', 'k'], ['jobs', 'Jobs', 'k'], ['verify', 'Verify', 'k'], ['preview', 'Preview', 'k'], ['fleet', 'Fleet & health', 'k'], ['users', 'Users', 'k']];
const CRUMB: Record<Screen, string> = { flow: 'workflow › document brief', builder: '', chat: 'chat › allowlist › WHSOP_002_A02', quest: 'questionnaire › POST /workflows', format: 'formatter › labels_raw.docx → house style', library: 'library › docengine.documents', jobs: 'jobs › docengine.jobs', report: 'reports › QCSOP_031_A02 · pp_report', verify: 'verify › POST /build 422 · WHSOP_009_A01', preview: 'preview › QCSOP_031 · page 3 / 9', fleet: 'admin › gf_ fleet & health', users: 'admin › users' };

// CRUMB names the mock-mode sample documents; live mode must not show them as if they were real.
const LIVE_CRUMB: Record<Screen, string> = { flow: 'workflow › /briefs', builder: '', chat: 'chat › POST /api/chat', quest: 'questionnaire › POST /workflows', format: 'formatter › Mode B · POST /build', library: 'library › shelves · GET /library', jobs: 'jobs › docengine.jobs', report: 'reports › not connected', verify: 'verify › last build in this session', preview: 'preview › last build in this session', fleet: 'fleet & health', users: 'users › /api/users' };

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
  // The engine the server reports, not a version number typed into the page.
  const [engine, setEngine] = useState('');
  useEffect(() => { s.api.deHealth().then(h => setEngine((h.engine.match(/canon revision ([\d-]+)/) || [])[1] || '')).catch(() => setEngine('')); }, [s.api]);
  // No sign-in on this server (PPDOCWIZ_AUTH=off): nothing to sign out of.
  const [open, setOpen] = useState(false), [pwLogin, setPwLogin] = useState(false), [changing, setChanging] = useState(false);
  useEffect(() => { s.api.health().then(h => { setOpen(h.auth === false); setPwLogin(h.login === 'password' || h.login === 'accounts'); }).catch(() => setOpen(false)); }, [s.api]);
  const zoom = Math.min(1, vp.w / 1280, vp.h / 760);
  const crumb = s.screen === 'builder' ? `builder › ${s.bdoc.code || 'untitled'} · ${s.bdoc.status.replace('_', ' ')} v${s.bdoc.version}` : (s.api.mode === 'live' ? LIVE_CRUMB : CRUMB)[s.screen];
  const radius = s.tweaks.createStyle === 'pill' ? 999 : 6;
  // One workflow (Head of QC, 18.10.2026): New opens it; the package (SOP, SOP + annexes, annex, form, report) is its first page.
  const toggleCreate = () => s.go('flow');
  const createBtn = (side: boolean) => <button onClick={toggleCreate} className="pp-create" style={{ display: 'flex', gap: 7, alignItems: 'center', justifyContent: side ? 'center' : undefined, width: side ? '100%' : undefined, marginBottom: side ? 10 : 0, background: T.surface, color: '#fff', border: `1px solid ${T.focus}`, borderRadius: radius, padding: side ? '8px 12px' : '6px 14px', font: 'inherit', fontSize: 13, fontWeight: 700, cursor: 'pointer', whiteSpace: 'nowrap' }}>
    <span style={{ fontSize: 15, lineHeight: 1, color: C.run }}>＋</span>{tr(s.lang, 'Create')}<span style={{ fontSize: 10, color: T.muted }}>{side ? '›' : '▾'}</span></button>;
  const dot = (label: string, st: keyof typeof s.svc & string) => <span title={s.svc.note[st] || (s.svc[st as 'letta'] === 'ok' ? 'ok' : 'probing…')} style={{ display: 'flex', gap: 5, alignItems: 'center' }}><Dot c={C[s.svc[st as 'letta']]} />{label}</span>;
  const pipeMsgC = s.busy ? C.run : s.pipeOk ? C.ok : C.bad;
  // The brief and the job list this browser worked on are the person's, not the machine's: gone at sign-out (review 19.10.2026).
  const signOut = () => s.api.closeSession().then(() => { try { localStorage.removeItem('ppsuite.brief'); localStorage.removeItem('ppsuite.jobs'); } catch { /* storage blocked */ } s.set({ authed: false, me: null }); }).catch(e => s.flash(String(e.message)));
  const STEPS = ['compose', 'build_from_md', 'pp_verify', 'gotenberg'];
  return (
    <div data-pp-root="1" style={{ width: vp.w / zoom, height: vp.h / zoom, zoom, overflow: 'hidden', position: 'relative', display: 'flex', flexDirection: 'column', background: T.bg, color: T.text, fontFamily: UI, fontSize: 14 }}>
      <div style={{ height: 48, flex: 'none', display: 'flex', alignItems: 'center', gap: 14, padding: '0 16px', borderBottom: `1px solid ${T.hair}` }}>
        <span style={{ fontFamily: DISPLAY, fontWeight: 700, letterSpacing: '.04em', color: '#fff', fontSize: 13, whiteSpace: 'nowrap' }}>PP · Document Engine</span>
        {s.tweaks.createPlacement === 'topbar' && createBtn(false)}
        <span style={{ fontFamily: MONO, fontSize: 12, color: T.muted, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{crumb}</span>
        <span style={{ marginLeft: 12, background: T.surface, border: `1px solid ${T.control}`, borderRadius: 6, padding: '6px 12px', width: 300, flex: 'none', color: T.muted, fontFamily: MONO, fontSize: 12, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>⌘K  build · verify · open … · ask agent</span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 14, fontFamily: MONO, fontSize: 12, color: T.muted }}>
          {s.api.mode === 'mock' && <span title="All data is sample data; switch in Fleet & health" style={{ color: C.warn, border: `1px solid ${C.warn}`, borderRadius: 3, padding: '0 6px' }}>mock</span>}
          {dot('letta', 'letta')}{dot('docengine', 'docengine')}{dot('pdf', 'pdf')}
          <span title="Interface language — documents stay bilingual MK | EN"><Seg items={[['en', 'EN'], ['mk', 'MK']]} value={s.lang} onPick={l => s.setLang(l)} size={11.5} pad="1px 8px" /></span>
        </div>
        <button onClick={s.primary?.run} disabled={s.busy || s.primary?.disabled} className="pp-primary" style={{ background: T.navy, color: '#fff', border: `1px solid ${T.focus}`, borderRadius: 6, padding: '7px 16px', font: 'inherit', fontWeight: 700, cursor: 'pointer', opacity: s.primary ? 1 : .5 }}>{s.busy ? 'Running…' : s.primary?.label || 'Build ▸'}</button>
      </div>
      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        <nav style={{ width: 184, flex: 'none', borderRight: `1px solid ${T.hair}`, padding: '14px 10px', display: 'flex', flexDirection: 'column', gap: 2 }}>
          {s.tweaks.createPlacement === 'sidebar' && createBtn(true)}
          {(['c', 'k'] as const).map(g => <div key={g} style={{ display: 'contents' }}>
            <div style={{ fontFamily: MONO, fontSize: 10.5, letterSpacing: '.1em', color: T.faint, padding: g === 'c' ? '4px 10px 6px' : '16px 10px 6px' }}>{tr(s.lang, g === 'c' ? 'CREATE' : 'CONTROL')}</div>
            {NAV.filter(n => n[2] === g && (n[0] !== 'users' || s.me?.role === 'admin')).map(([k, label]) => <div key={k} onClick={() => s.go(k)} {...press(() => s.go(k))} aria-current={s.screen === k ? 'page' : undefined} className="pp-nav" style={{ padding: '8px 10px', borderRadius: 6, cursor: 'pointer', background: s.screen === k ? T.selected : 'transparent', color: s.screen === k ? '#fff' : T.secondary, fontWeight: s.screen === k ? 700 : 400 }}>{tr(s.lang, label)}</div>)}
          </div>)}
          <div style={{ marginTop: 'auto', padding: 10, fontSize: 12, color: T.faint, lineHeight: 1.5 }}>{s.api.mode === 'mock' ? 'Engine 1.6.2' : engine ? `Engine · canon ${engine}` : 'Engine · not reachable'}<br />{s.me?.accounts ? <>{tr(s.lang, 'signed in as')} <b style={{ color: T.secondary }}>{s.me.user}</b>{s.me.role === 'admin' ? ' · admin' : ''}</> : s.api.mode === 'mock' ? 'darko.s · QA' : open ? 'open access · no sign-in' : 'session · cookie'}
            {pwLogin && <div onClick={() => setChanging(true)} {...press(() => setChanging(true))} style={{ cursor: 'pointer', color: T.muted, marginTop: 4 }}>{tr(s.lang, 'Change password')}</div>}
            {changing && <ChangePassword onDone={() => setChanging(false)} />}
            {!open && <div onClick={signOut} {...press(signOut)} style={{ cursor: 'pointer', color: T.muted, marginTop: 4 }}>{tr(s.lang, 'Sign out')}</div>}</div>
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

/** The Document Engine's own sign-in (19.10.2026): the house logo and name, EN | MK, a phone-width card. POST
 *  /api/session exchanges the username and password (or, before named accounts, the password or the key) for an
 *  HttpOnly session cookie; nothing secret is kept in the browser. */
function AuthCard({ children }: { children: ReactNode }) {
  const { lang, setLang } = useApp();
  return (
    <div style={{ minHeight: '100vh', background: T.bg, color: T.text, fontFamily: UI, display: 'grid', placeItems: 'center', padding: 16, boxSizing: 'border-box' }}>
      <div style={{ width: '100%', maxWidth: 420, boxSizing: 'border-box', background: T.pane, border: `1px solid ${T.control}`, borderRadius: 12, boxShadow: '0 30px 70px rgba(0,0,0,.55)', padding: '24px 26px', display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', rowGap: 10, minWidth: 0 }}>
          <span style={{ background: '#fff', borderRadius: 8, padding: '6px 8px', display: 'flex', flex: 'none' }}><img src="/assets/brand/pp_logo_header.jpg" alt="Purely Plant" style={{ height: 'clamp(26px, 7vw, 34px)', display: 'block' }} /></span>
          <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
            <span style={{ fontFamily: DISPLAY, fontWeight: 700, letterSpacing: '.04em', color: '#fff', fontSize: 'clamp(14px, 4.2vw, 17px)', whiteSpace: 'nowrap' }}>Document Engine</span>
            <span style={{ fontSize: 11.5, color: T.muted }}>Purely Plant · Пјурли Плант</span>
          </div>
          <span style={{ marginLeft: 'auto' }}><Seg items={[['en', 'EN'], ['mk', 'MK']]} value={lang} onPick={setLang} size={11} pad="2px 8px" /></span>
        </div>
        <div style={{ fontSize: 12, color: T.faint, lineHeight: 1.45 }}>{tr(lang, 'tagline')}</div>
        {children}
      </div>
    </div>);
}

const authInput = (bad = false) => ({ background: T.deeper, border: `1px solid ${bad ? C.bad : T.control}`, borderRadius: 6, padding: '10px 11px', color: '#fff', outline: 'none', fontFamily: MONO, fontSize: 14, width: '100%', boxSizing: 'border-box' as const });
const authLabel = { fontSize: 12, color: T.muted };

export function SignIn({ unconfigured }: { unconfigured?: boolean }) {
  const { api, set, lang } = useApp();
  const [key, setKey] = useState(''), [err, setErr] = useState(''), [busy, setBusy] = useState(false);
  // The server says what it asks for: named accounts, the shared password, or the deployment's API key.
  const [pw, setPw] = useState(true), [named, setNamed] = useState(false), [user, setUser] = useState('');
  useEffect(() => { api.health().then(h => { setPw(h.login !== 'key'); setNamed(h.login === 'accounts'); }).catch(() => {}); }, [api]);
  const ready = !!key && (!named || !!user.trim());
  const submit = async () => {
    if (!ready || busy) return;
    setBusy(true); setErr('');
    try { await api.openSession(key, named ? user.trim() : ''); set({ authed: true }); }
    catch (e) {
      const st = (e as ApiError).status;
      setErr(st === 401 ? tr(lang, named ? 'Wrong username or password.' : pw ? 'Wrong password.' : '401 · bad key. The key is the PPDOCWIZ_API_KEY of this deployment.')
        : st === 429 ? tr(lang, 'Too many failed sign-ins. Wait 15 minutes and try again.')
        : st === 503 ? '503 · the server is not configured (PPDOCWIZ_API_KEY is unset).' : String((e as Error).message));
    }
    finally { setBusy(false); }
  };
  return (
    <AuthCard>
      <div style={{ color: T.secondary, fontSize: 13, lineHeight: 1.5 }}>{tr(lang, named ? 'signin_intro' : 'signin_intro_pw')}</div>
      {unconfigured && <div style={{ background: T.errSurface, border: `1px solid ${T.errBorder}`, borderRadius: 6, padding: '8px 12px', color: T.errText, fontSize: 12.5 }}>503 · server not configured. Set PPDOCWIZ_API_KEY in /opt/stacks/ppdocwiz and restart.</div>}
      <form onSubmit={e => { e.preventDefault(); submit(); }} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {named && <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}><span style={authLabel}>{tr(lang, 'Username')}</span>
          <input name="username" autoFocus autoComplete="username" autoCapitalize="none" spellCheck={false} value={user} onChange={e => setUser(e.target.value)} style={authInput()} /></label>}
        <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}><span style={authLabel}>{pw ? tr(lang, 'Password') : 'PPDOCWIZ_API_KEY'}</span>
          <input name="password" type="password" autoComplete="current-password" autoFocus={!named} value={key} onChange={e => setKey(e.target.value)} style={authInput(!!err)} /></label>
        {err && <div role="alert" style={{ fontSize: 12.5, color: C.bad, lineHeight: 1.45 }}>{err}</div>}
        <button type="submit" disabled={busy || !ready} style={{ background: ready ? T.navy : T.control, color: '#fff', border: 0, borderRadius: 6, padding: 11, font: 'inherit', fontWeight: 700, cursor: ready ? 'pointer' : 'default' }}>{busy ? tr(lang, 'Signing in…') : tr(lang, 'Sign in ▸')}</button>
      </form>
      {api.mode === 'mock' && <div style={{ fontSize: 11.5, color: T.faint, textAlign: 'center' }}>demo mode: any password works except "bad"</div>}
    </AuthCard>);
}

/** Set your password: the current one, then a new one of at least 12 characters (stored on the server as a hash).
 *  `forced` after a sign-in with a temporary password. */
export function ChangePassword({ forced, onDone }: { forced?: boolean; onDone: () => void }) {
  const { api, flash, lang, set } = useApp();
  const [cur, setCur] = useState(''), [next, setNext] = useState(''), [again, setAgain] = useState('');
  const [err, setErr] = useState(''), [busy, setBusy] = useState(false);
  const first = useRef<HTMLInputElement>(null);
  // A dialog: focus lands on its first field, Escape closes it unless the change is forced (review 19.10.2026).
  useEffect(() => { first.current?.focus(); }, []);
  useEffect(() => { if (forced) return; const k = (e: globalThis.KeyboardEvent) => { if (e.key === 'Escape') onDone(); }; window.addEventListener('keydown', k); return () => window.removeEventListener('keydown', k); }, [forced, onDone]);
  const problem = next && next.length < 12 ? tr(lang, 'At least 12 characters.') : again && next !== again ? tr(lang, 'The two new passwords differ.') : '';
  const ready = !problem && !!cur && !!next && next === again;
  const submit = async () => {
    if (!ready || busy) return;
    setBusy(true); setErr('');
    try {
      await api.changePassword(cur, next); flash(tr(lang, 'Password changed'));
      // After a forced change `me.must_change` is stale until re-read; otherwise the forced card can come back.
      if (forced) await api.me().then(m => set({ me: m })).catch(() => {});
      onDone();
    }
    catch (e) { const st = (e as ApiError).status; setErr(st === 401 ? tr(lang, 'The current password is wrong.') : st === 429 ? tr(lang, 'Too many failed attempts. Wait 15 minutes.') : String((e as Error).message)); }
    finally { setBusy(false); }
  };
  const field = (label: string, v: string, on: (x: string) => void, auto: string, focus = false) =>
    <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}><span style={authLabel}>{tr(lang, label)}</span>
      <input ref={focus ? first : undefined} type="password" autoComplete={auto} value={v} onChange={e => on(e.target.value)} style={authInput()} /></label>;
  const form = <>
    {forced && <div style={{ color: T.secondary, fontSize: 13, lineHeight: 1.5 }}>{tr(lang, 'forced_change')}</div>}
    {!forced && <span style={{ fontFamily: DISPLAY, fontWeight: 700, color: '#fff', fontSize: 15 }}>{tr(lang, 'Change password')}</span>}
    <form onSubmit={e => { e.preventDefault(); submit(); }} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {field('Current password', cur, setCur, 'current-password', true)}
      {field('New password', next, setNext, 'new-password')}
      {field('New password again', again, setAgain, 'new-password')}
      {(problem || err) && <div role="alert" style={{ fontSize: 12.5, color: C.bad }}>{problem || err}</div>}
      <button type="submit" disabled={busy || !ready} style={{ background: ready ? T.navy : T.control, color: '#fff', border: 0, borderRadius: 6, padding: 11, font: 'inherit', fontWeight: 700, cursor: ready ? 'pointer' : 'default' }}>{busy ? tr(lang, 'Saving…') : tr(lang, 'Set password ▸')}</button>
    </form>
    {!forced && <span onClick={onDone} style={{ cursor: 'pointer', color: T.muted, fontSize: 12, textAlign: 'center' }}>{tr(lang, 'Cancel')}</span>}
  </>;
  if (forced) return <AuthCard><span style={{ fontWeight: 700, color: '#fff', fontSize: 15 }}>{tr(lang, 'Set your own password')}</span>{form}</AuthCard>;
  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 80, background: 'rgba(0,0,0,.55)', display: 'grid', placeItems: 'center', padding: 16 }}>
      <div role="dialog" aria-modal="true" aria-label={tr(lang, 'Change password')} style={{ width: '100%', maxWidth: 420, boxSizing: 'border-box', background: T.pane, border: `1px solid ${T.control}`, borderRadius: 12, boxShadow: '0 30px 70px rgba(0,0,0,.55)', padding: '24px 26px', display: 'flex', flexDirection: 'column', gap: 14, color: T.text, fontFamily: UI }}>{form}</div>
    </div>);
}
