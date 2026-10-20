// Named accounts (phase 5, Head of QC 19.10.2026): administrators add people with a temporary password (changed at
// their first sign-in), reset a password, change a role, or disable an account. Nobody is deleted, so a disabled
// account keeps its name on everything it did. The sign-in record lists sign-ins, failures and every account change.
import { useEffect, useState } from 'react';
import { ApiError, type Account, type AuthEvent } from '../api/types';
import { Banner, Caps, Seg, press } from '../components/ui';
import { useApp } from '../store/store';
import { C, MONO, T } from '../theme';

const field = { background: T.deeper, border: `1px solid ${T.control}`, borderRadius: 5, padding: '7px 9px', color: T.strong, outline: 'none', fontFamily: MONO, fontSize: 12.5 } as const;
const EVENT: Record<string, string> = { signed_in: 'signed in', sign_in_failed: 'failed sign-in', password_changed: 'changed own password', account_created: 'account created', account_changed: 'account changed', migrated: 'admin created from the shared password' };

export function Users() {
  const { api, me, flash, set } = useApp();
  const [users, setUsers] = useState<Account[]>([]), [log, setLog] = useState<AuthEvent[]>([]);
  const [tab, setTab] = useState<'people' | 'log'>('people');
  const [err, setErr] = useState('');
  const [name, setName] = useState(''), [role, setRole] = useState<'user' | 'admin'>('user'), [temp, setTemp] = useState('');
  // The temporary password for a reset is typed into a password field in the row, not a window.prompt that shows it (review 19.10.2026).
  const [resetting, setResetting] = useState<{ user: string; pw: string } | null>(null);
  const load = () => { api.users().then(setUsers).catch(e => setErr(String((e as Error).message))); api.authLog().then(setLog).catch(() => {}); };
  useEffect(load, [api]); // eslint-disable-line react-hooks/exhaustive-deps
  if (me && me.role !== 'admin') return <div style={{ padding: 24 }}><Banner kind="warn">Only administrators manage accounts.</Banner></div>;
  const fail = (e: unknown) => setErr(`${(e as ApiError).status || ''} ${(e as Error).message}`.trim());
  const add = async () => {
    setErr('');
    try { await api.addUser({ username: name.trim(), role, temporary_password: temp }); flash(`${name.trim().toLowerCase()} added: give them the temporary password; they change it at their first sign-in`); setName(''); setTemp(''); load(); }
    catch (e) { fail(e); }
  };
  const change = async (u: Account, c: Parameters<typeof api.changeUser>[1], msg: string) => {
    setErr('');
    // Disabling or demoting yourself ends your own session or your access to this page: asked first.
    if (u.username === me?.user && (c.disabled || c.role === 'user') && !window.confirm(c.disabled ? 'Disable your own account? You are signed out at once.' : 'Make yourself a user? You lose this page.')) return;
    try { await api.changeUser(u.username, c); flash(msg); load(); if (u.username === me?.user) api.me().then(m => set({ me: m })).catch(() => {}); } catch (e) { fail(e); }
  };
  const reset = (u: Account) => { if (resetting?.user !== u.username) setResetting({ user: u.username, pw: '' }); };
  const confirmReset = (u: Account) => { if (!resetting || resetting.pw.length < 12) return; change(u, { reset_password: resetting.pw }, `${u.username}: password reset; they set their own at the next sign-in`); setResetting(null); };
  return <div style={{ flex: 1, minWidth: 0, padding: '18px 24px', display: 'flex', flexDirection: 'column', gap: 14, overflow: 'auto' }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
      <span style={{ color: T.strong, fontSize: 16, fontWeight: 700 }}>Users</span>
      <Seg items={[['people', 'People'], ['log', 'Sign-in record']]} value={tab} onPick={setTab} size={12} pad="4px 10px" />
    </div>
    {err && <Banner kind="err">{err}</Banner>}
    {tab === 'people' ? <>
      <div style={{ border: `1px solid ${T.hair}`, borderRadius: 8, maxWidth: 980 }}>
        {users.map((u, i) => <div key={u.username} style={{ display: 'grid', gridTemplateColumns: '170px 90px 150px minmax(0,1fr) auto', gap: 12, padding: '8px 12px', borderTop: i ? `1px solid ${T.hair}` : 'none', alignItems: 'center', fontSize: 12.5, opacity: u.disabled ? 0.55 : 1 }}>
          <b style={{ fontFamily: MONO, color: T.strong }}>{u.username}{u.username === me?.user ? ' (you)' : ''}</b>
          <span style={{ color: u.role === 'admin' ? C.warn : T.secondary }}>{u.role}</span>
          <span style={{ color: u.disabled ? C.bad : u.must_change ? C.warn : C.ok, fontSize: 12 }}>{u.disabled ? 'disabled' : u.must_change ? 'temporary password' : 'active'}</span>
          <span style={{ color: T.faint, fontSize: 11.5 }}>added {u.created.slice(0, 10)} by {u.by}</span>
          <span style={{ display: 'flex', gap: 10, fontSize: 12, alignItems: 'center' }}>
            {resetting?.user === u.username ? <>
              <input type="password" autoFocus value={resetting.pw} onChange={e => setResetting({ user: u.username, pw: e.target.value })} onKeyDown={e => { if (e.key === 'Enter') confirmReset(u); if (e.key === 'Escape') setResetting(null); }} placeholder="temporary password (12+)" aria-label={`temporary password for ${u.username}`} style={{ ...field, width: 190, padding: '4px 8px' }} />
              <button onClick={() => confirmReset(u)} disabled={resetting.pw.length < 12} style={{ background: resetting.pw.length < 12 ? T.control : T.navy, color: T.strong, border: 0, borderRadius: 5, padding: '4px 10px', cursor: 'pointer', fontWeight: 700, fontSize: 12 }}>Reset ▸</button>
              <span onClick={() => setResetting(null)} {...press(() => setResetting(null))} style={{ cursor: 'pointer', color: T.muted }}>cancel</span>
            </> : <span onClick={() => reset(u)} {...press(() => reset(u))} style={{ cursor: 'pointer', color: C.run }}>reset password</span>}
            {(() => { const f = () => change(u, { role: u.role === 'admin' ? 'user' : 'admin' }, `${u.username} is now ${u.role === 'admin' ? 'a user' : 'an admin'}`); return <span onClick={f} {...press(f)} style={{ cursor: 'pointer', color: C.run }}>{u.role === 'admin' ? 'make user' : 'make admin'}</span>; })()}
            {(() => { const f = () => change(u, { disabled: !u.disabled }, `${u.username} ${u.disabled ? 'enabled' : 'disabled: signed out at once'}`); return <span onClick={f} {...press(f)} style={{ cursor: 'pointer', color: u.disabled ? C.ok : C.bad }}>{u.disabled ? 'enable' : 'disable'}</span>; })()}
          </span>
        </div>)}
      </div>
      <Caps>ADD A PERSON</Caps>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', maxWidth: 980 }}>
        <input value={name} onChange={e => setName(e.target.value)} placeholder="username, e.g. c.cekic" style={{ ...field, width: 200 }} />
        <Seg items={[['user', 'user'], ['admin', 'admin']]} value={role} onPick={setRole} size={12} pad="4px 10px" />
        <input type="password" value={temp} onChange={e => setTemp(e.target.value)} placeholder="temporary password (12+)" style={{ ...field, width: 230 }} />
        <button onClick={add} disabled={!name.trim() || temp.length < 12} style={{ background: T.navy, color: T.onAccent, border: 0, borderRadius: 6, padding: '8px 14px', cursor: 'pointer', fontWeight: 700 }}>Add ▸</button>
      </div>
      <div style={{ fontSize: 12, color: T.faint, maxWidth: 820, lineHeight: 1.5 }}>Each person signs in with their own username; everything they change in a brief, every build, suggestion and approve/return is recorded under their name. A disabled account is signed out at once and keeps its name on what it did; nobody is deleted. At least one administrator always stays enabled.</div>
    </> : <div style={{ border: `1px solid ${T.hair}`, borderRadius: 8, maxWidth: 980 }}>
      {log.length === 0 && <div style={{ padding: 12, color: T.faint, fontSize: 12.5 }}>No sign-ins recorded yet.</div>}
      {log.map((e, i) => <div key={i} style={{ display: 'grid', gridTemplateColumns: '165px 150px 220px minmax(0,1fr)', gap: 12, padding: '6px 12px', borderTop: i ? `1px solid ${T.hair}` : 'none', fontSize: 12, fontFamily: MONO }}>
        <span style={{ color: T.muted }}>{e.at.replace('T', ' ').slice(0, 19)}</span>
        <span style={{ color: T.strong }}>{e.user || '—'}</span>
        <span style={{ color: e.event === 'sign_in_failed' ? C.bad : T.secondary }}>{EVENT[e.event] || e.event}</span>
        <span style={{ color: T.faint }}>{[e.by && `by ${e.by}`, e.role && `role ${e.role}`, e.disabled !== undefined && e.disabled !== null && (e.disabled ? 'disabled' : 'enabled'), e.password_reset && 'password reset', e.client].filter(Boolean).join(' · ')}</span>
      </div>)}
    </div>}
  </div>;
}
