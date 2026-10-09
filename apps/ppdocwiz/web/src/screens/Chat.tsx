// Agent chat (handoff §2). POST /api/chat → Letta agent; allowlist enforced server-side (400).
import { useEffect, useRef } from 'react';
import { create } from 'zustand';
import { ApiError } from '../api/types';
import { PPPage } from '../components/PPPage';
import { Avatar, Banner, Caps, PaneHead, stamp, StampRail } from '../components/ui';
import { SAMPLE_ANNEX } from '../data/samples';
import { usePrimary } from '../lib/usePrimary';
import { useApp } from '../store/store';
import { C, MONO, T, type Status } from '../theme';

type Msg = { k: 'you' | 'trace' | 'agent' | 'err'; text: string } | { k: 'tool'; args: string; res: string; st: Status; t: string } | { k: 'built'; path: string; docx?: string; pdf?: string };

const INIT: Msg[] = [
  { k: 'you', text: 'Add an acceptance limit to arrival temperature: 2–8 °C. Keep both languages.' },
  { k: 'trace', text: 'reasoning · TYPE=Annex MODE=A · section 1 Пратка, form row 3' },
  { k: 'trace', text: 'archival_memory_search("clone transport temperature") → 3 passages' },
  { k: 'tool', args: '(markdown=<1 486 chars>, out_path="/data/WHSOP_002_A02.docx")', res: 'paragraphs 14 · tables 4 · min font 7.0 pt [OK] · MK+EN OK', st: 'ok', t: '1.84 s' },
  { k: 'built', path: '/data/WHSOP_002_A02_3fa1c2d9.docx' },
  { k: 'agent', text: 'Row 3 now reads "Температура при пристигнување (2–8 °C) ||| Arrival temperature (2–8 °C)". The value cell stays blank for the operator.' },
];
const useChat = create<{ msgs: Msg[]; denied: string[]; push: (...m: Msg[]) => void; patch: (i: number, m: Partial<Msg>) => void; deny: (a: string) => void }>(set => ({
  msgs: INIT, denied: ['gf_reg_checker'],
  push: (...m) => set(s => ({ msgs: [...s.msgs, ...m] })),
  patch: (i, m) => set(s => ({ msgs: s.msgs.map((x, j) => j === i ? { ...x, ...m } as Msg : x) })),
  deny: a => set(s => ({ denied: s.denied.includes(a) ? s.denied : [...s.denied, a] })),
}));

const AGENTS = ['qms_docx_formatter', 'gf_annex_author', 'gf_reg_checker'];
const doc = { ...SAMPLE_ANNEX, sections: SAMPLE_ANNEX.sections.map((s, i) => i === 0 && s.blocks[0].type === 'form' ? { ...s, blocks: [{ ...s.blocks[0], rows: s.blocks[0].rows.map((r, j) => j === 2 ? { ...r, label_mk: r.label_mk + ' (2–8 °C)', label_en: r.label_en + ' (2–8 °C)' } : r) }] } : s) };

export function Chat() {
  const { api, chatAgent, chatDraft: draft, set, run, busy, svc } = useApp();
  const { msgs, denied, push, patch, deny } = useChat();
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { end.current?.scrollIntoView({ block: 'end' }); }, [msgs.length]);
  const disabled = svc.note.letta?.startsWith('chat disabled');
  const live = api.mode === 'live';
  // The opening conversation is a mock-mode sample; live mode starts empty.
  useEffect(() => { if (live && useChat.getState().msgs === INIT) useChat.setState({ msgs: [], denied: [] }); }, [live]);

  const send = async (text: string) => {
    text = text.trim(); if (!text || busy) return;
    const idx = useChat.getState().msgs.length + 2;
    set({ chatDraft: '' });
    // Live mode shows only what the server returns: no simulated reasoning trace or tool row.
    if (live) push({ k: 'you', text });
    else push({ k: 'you', text }, { k: 'trace', text: 'reasoning · resolving target in WHSOP_002_A02' }, { k: 'tool', args: `(markdown=<${text.length * 12} chars>, out_path="/data/WHSOP_002_A02.docx")`, res: 'compose → build_from_md → pp_verify → gotenberg', st: 'run', t: '' });
    const t0 = performance.now();
    await run(live ? 'chat' : 'WHSOP_002_A02', async () => {
      try {
        const r = await api.chat(text, chatAgent);
        if (!live) patch(idx, { st: 'ok', res: r.built ? 'built ' + r.built.path : 'no build in this turn', t: ((performance.now() - t0) / 1000).toFixed(2) + ' s' });
        if (r.built) { const id = String(r.built.path).split('/').pop()!.replace(/\.docx$/, ''); push({ k: 'built', path: r.built.path, docx: api.downloadHref(id, 'docx'), pdf: api.downloadHref(id, 'pdf') }); }
        push({ k: 'agent', text: r.reply });
        return { ok: true };
      } catch (e) {
        const er = e as ApiError;
        if (!live) patch(idx, { st: 'bad', res: `${er.status} · ${er.message}`, t: '' });
        push({ k: 'err', text: `POST /api/chat → ${er.status} · ${er.message}` });
        if (er.status === 400) deny(chatAgent);
        return { ok: false, failAt: 0, msg: `RESULT: FAIL · ${er.status}` };
      }
    });
  };
  usePrimary('Build ▸', () => send('/build'));

  return <>
    <div style={{ width: 236, flex: 'none', borderRight: `1px solid ${T.hair}`, background: T.pane, padding: '14px 12px', display: 'flex', flexDirection: 'column', gap: 10, fontSize: 12.5 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}><b style={{ color: '#fff', fontSize: 14 }}>Agent</b><span style={{ fontFamily: MONO, fontSize: 10.5, color: T.faint, whiteSpace: 'nowrap' }}>allowlist</span></div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>{AGENTS.map(n => { const ok = !denied.includes(n), act = n === chatAgent;
        return <div key={n} onClick={() => ok ? set({ chatAgent: n }) : push({ k: 'err', text: `POST /api/chat → 400 · agent '${n}' is not permitted by this deployment` })}
          style={{ borderRadius: 6, padding: '7px 9px', cursor: 'pointer', background: act ? T.selected : 'transparent', border: `1px solid ${act ? T.focus : T.control}` }}>
          <div style={{ fontFamily: MONO, fontSize: 12, color: ok ? '#fff' : T.faint }}>{n}</div><div style={{ fontSize: 11, color: ok ? T.muted : C.bad }}>{ok ? (act ? 'active' : 'allowed') : 'not in allowlist'}</div></div>; })}</div>
      <Caps style={{ marginTop: 6 }}>CORE MEMORY</Caps>
      <div style={{ background: T.surface, border: `1px solid ${T.control}`, borderRadius: 6, padding: '9px 10px' }}><div style={{ display: 'flex', justifyContent: 'space-between' }}><b style={{ color: '#fff' }}>pp_house_rules</b><span style={{ color: T.muted, whiteSpace: 'nowrap' }}>1 963 / 5k</span></div>
        <div style={{ height: 4, background: T.deeper, borderRadius: 2, margin: '7px 0' }}><div style={{ width: '39%', height: 4, background: C.run, borderRadius: 2 }} /></div>
        <div style={{ color: T.secondary, fontFamily: MONO, fontSize: 11, lineHeight: 1.5 }}>MK-first · navy #2B547E · floor 6 pt · never fabricate data…</div></div>
      <Caps style={{ marginTop: 6 }}>SOURCES</Caps>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 5, fontFamily: MONO, fontSize: 11.5 }}>{['DB3_PP_CURRENT', 'DB1_REGULATORY'].map(s => <div key={s} style={{ display: 'flex', justifyContent: 'space-between' }}><span>{s}</span><span style={{ color: C.ok }}>native</span></div>)}</div>
      <Caps style={{ marginTop: 6 }}>TOOLS</Caps>
      <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', fontFamily: MONO, fontSize: 11 }}>{['build_pp_document', 'fetch_pp_document', 'archival_memory_search'].map(t => <span key={t} style={{ border: `1px solid ${T.control}`, borderRadius: 4, padding: '2px 6px' }}>{t}</span>)}</div>
      <div style={{ marginTop: 'auto', color: T.muted }}>ctx 11.2k / 32k</div>
    </div>
    <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
      {disabled && <div style={{ margin: '12px 22px 0' }}><Banner kind="err">503 · chat disabled: LETTA_BASE_URL is not set on ppdocwiz. The wizard path still builds without Letta.</Banner></div>}
      <div style={{ flex: 1, minHeight: 0, overflow: 'auto', padding: '18px 22px', display: 'flex', flexDirection: 'column', gap: 12, fontSize: 14, lineHeight: 1.5 }}>
        {msgs.map((m, i) => {
          if (m.k === 'you') return <div key={i} style={{ alignSelf: 'flex-end', maxWidth: '76%', background: T.navy, color: '#fff', borderRadius: '10px 10px 2px 10px', padding: '9px 13px' }}>{m.text}</div>;
          if (m.k === 'trace') return <div key={i} style={{ fontFamily: MONO, fontSize: 12, color: T.muted }}>↳ {m.text}</div>;
          if (m.k === 'tool') return <div key={i} style={{ background: T.deeper, border: `1px solid ${T.hair}`, borderLeft: `3px solid ${C[m.st]}`, borderRadius: 6, padding: '9px 12px', fontFamily: MONO, fontSize: 12, lineHeight: 1.6 }}>
            <div><span style={{ color: C.run }}>tool</span> build_pp_document<span style={{ color: T.muted }}>{m.args}</span></div><div style={{ color: T.secondary }}>{m.res}</div>
            <div style={{ color: C[m.st], fontWeight: 700 }}>{m.st === 'run' ? '● running…' : m.st === 'bad' ? 'RESULT: FAIL' : 'RESULT: PASS  ' + m.t}</div></div>;
          if (m.k === 'agent') return <div key={i} style={{ maxWidth: '80%', display: 'flex', gap: 10 }}><Avatar size={26} filled={false} /><div style={{ background: T.surface, border: `1px solid ${T.control}`, borderRadius: '2px 10px 10px 10px', padding: '9px 13px' }}>{m.text}</div></div>;
          if (m.k === 'built') return <div key={i} style={{ marginLeft: 36, maxWidth: '70%', background: T.okSurface, border: `1px solid ${T.okBorder}`, borderRadius: 8, padding: '10px 12px', display: 'flex', gap: 12, alignItems: 'center' }}>
            <div style={{ flex: 1, minWidth: 0 }}><div style={{ fontFamily: MONO, fontSize: 11, color: C.ok }}>tool_return · ok: true</div><div style={{ fontFamily: MONO, fontSize: 12, color: '#fff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{m.path}</div></div>
            <a href={m.docx || '#'} style={{ background: T.navy, color: '#fff', borderRadius: 5, padding: '6px 10px', fontSize: 12, fontWeight: 700, whiteSpace: 'nowrap', textDecoration: 'none' }}>.docx</a>
            <a href={m.pdf || '#'} style={{ border: `1px solid ${T.okBorder}`, color: T.okText, borderRadius: 5, padding: '6px 10px', fontSize: 12, whiteSpace: 'nowrap', textDecoration: 'none' }}>.pdf</a></div>;
          return <div key={i} style={{ background: T.errSurface, border: `1px solid ${T.errBorder}`, borderRadius: 6, padding: '8px 12px', color: T.errText, fontFamily: MONO, fontSize: 12 }}>{m.text}</div>;
        })}
        <div ref={end} />
      </div>
      <div style={{ flex: 'none', padding: '12px 22px 16px', borderTop: `1px solid ${T.hair}`, display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ display: 'flex', gap: 6, fontSize: 12 }}>{['Translate row 3 to EN', 'Add a “received by” row', '/verify'].map(c => <span key={c} className="pp-chip" onClick={() => send(c)} style={{ border: `1px solid ${T.control}`, borderRadius: 999, padding: '4px 11px', color: T.secondary, cursor: 'pointer' }}>{c}</span>)}</div>
        <div style={{ display: 'flex', gap: 8 }}>
          <input value={draft} onChange={e => set({ chatDraft: e.target.value })} onKeyDown={e => e.key === 'Enter' && send(draft)} placeholder={`Message ${chatAgent}, or /build /verify /diff`} style={{ flex: 1, background: T.surface, border: `1px solid ${T.control}`, borderRadius: 6, padding: '9px 12px', color: '#fff', outline: 'none' }} />
          <button onClick={() => send(draft)} style={{ background: T.navy, color: '#fff', border: 0, borderRadius: 6, padding: '0 16px', font: 'inherit', fontWeight: 700, cursor: 'pointer' }}>Send</button>
        </div>
      </div>
    </div>
    <div style={{ width: 452, flex: 'none', borderLeft: `1px solid ${T.hair}`, background: T.deep, display: 'flex', flexDirection: 'column' }}>
      <PaneHead title={live ? 'Sample layout · not this conversation' : 'WHSOP_002_A02 · live'} right={live ? '' : busy ? 'rebuilding…' : 'rebuilt 06:44 · PASS'} />
      <div style={{ flex: 1, position: 'relative', padding: '16px 0 0 14px' }}>
        <div style={{ position: 'relative', width: 318 }}>
          <PPPage doc={doc} zoom={.4} highlights={[{ anchor: 's0b0r2', kind: 'ok' }]} />
          <StampRail width={120} stamps={[stamp('CHANGED', 'row 3 · 2–8 °C added', 'ok', 132, '-2deg'), stamp('BILINGUAL', 'MK ||| EN paired', 'ok', 196, '1deg'), stamp('FONT FLOOR', 'min 7 pt', 'ok', 260, '-1deg')]} />
        </div>
      </div>
    </div>
  </>;
}
