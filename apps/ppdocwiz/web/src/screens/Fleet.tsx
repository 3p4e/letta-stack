// Fleet & health (handoff §10) + engine environment (COVERAGE #10) + degraded-state switches (COVERAGE #6).
import { useEffect, useState } from 'react';
import type { EngineEnv } from '../api/client';
import type { Faults, MockApi } from '../api/mock';
import { ApiError, type DeHealth, type Health } from '../api/types';
import { Banner, Caps, Dot, Seg, Tag } from '../components/ui';
import { AGENTS, HOUSE_RULES, LOG_LINES } from '../data/samples';
import { usePrimary } from '../lib/usePrimary';
import { useApp } from '../store/store';
import { C, MONO, T } from '../theme';
import { WithRibbon } from '../components/LiveViews';

export function Fleet() {
  const { api } = useApp();
  return <WithRibbon on={api.mode === 'live'} why="The agent list and the log tail have no endpoint yet. The two health panels (GET /api/health, DocEngine /health) are live."><FleetBody /></WithRibbon>;
}

function FleetBody() {
  const { api, svc, run, dataRev, tweaks, setTweaks, setMode } = useApp();
  const [agSel, setAgSel] = useState('gf_sop_author');
  const [tab, setTab] = useState<'agent' | 'engine' | 'settings'>('agent');
  const [h, setH] = useState<{ pw?: Health; de?: DeHealth; err?: string; code: number }>({ code: 0 });
  const [env, setEnv] = useState<EngineEnv | null>(null), [envErr, setEnvErr] = useState('');
  const [faults, setFaults] = useState<Faults | null>(api.mode === 'mock' ? { ...(api as MockApi).faults } : null);
  useEffect(() => {
    Promise.all([api.health().catch(() => undefined), api.deHealth().then(d => ({ d, code: 200 })).catch((e: ApiError) => ({ d: undefined, code: e.status, err: e.message }))])
      .then(([pw, r]) => setH({ pw, de: r.d, code: r.code, err: (r as { err?: string }).err }));
  }, [api, dataRev]);
  useEffect(() => { if (tab === 'engine') api.engineEnv().then(setEnv).catch((e: ApiError) => setEnvErr(`${e.status} · ${e.message}`)); }, [api, tab]);
  usePrimary('Build ▸', () => run('WHSOP_002_A02', async () => ({ ok: true })));

  const A = AGENTS.find(a => a.n === agSel) || AGENTS[1];
  const agv = (a: typeof AGENTS[number]) => <div key={a.n} onClick={() => { setAgSel(a.n); setTab('agent'); }} style={{ padding: '7px 9px', borderRadius: 6, cursor: 'pointer', display: 'flex', justifyContent: 'space-between', gap: 6, alignItems: 'center', background: agSel === a.n ? T.selected : 'transparent' }}>
    <span style={{ fontFamily: MONO, fontSize: 12, color: agSel === a.n ? '#fff' : T.secondary, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{a.n}</span><span style={{ fontFamily: MONO, fontSize: 11, color: T.muted }}>{a.runs}</span></div>;
  const flip = (k: keyof Faults) => { const m = api as MockApi; m.setFaults({ [k]: !m.faults[k] }); setFaults({ ...m.faults }); };
  const de = h.de, deOk = h.code === 200;
  const services: [string, string, string, string][] = [['letta', ':8283', de?.letta === false ? 'unavailable' : 'v0.16.8 · 11 agents', svc.letta], ['docengine', 'internal', deOk ? (de?.db ? 'db ok' : 'storage down') : `${h.code || 'unreachable'}`, svc.docengine], ['qms-api', ':8500', 'p95 1.9 s', 'ok'], ['gotenberg', ':3000', faults?.gotenberg ? 'PDF 502' : 'LibreOffice', faults?.gotenberg ? 'bad' : 'ok'], ['postgres', ':5432', de?.db === false ? 'not ready' : 'schema docengine', de?.db === false ? 'bad' : 'ok'], ['ppdocwiz', ':8770', h.pw ? `wizard + ${h.pw.letta ? 'chat' : 'no chat'}${h.pw.pdf ? '' : ' · no PDF'}` : '—', h.pw ? 'ok' : 'idle']];
  const hl = (v: unknown) => <span style={{ color: v === true ? C.ok : v === false ? C.bad : C.warn }}>{JSON.stringify(v)}</span>;
  return <>
    <div style={{ width: 250, flex: 'none', borderRight: `1px solid ${T.hair}`, background: T.pane, padding: '14px 10px', display: 'flex', flexDirection: 'column', gap: 3, overflow: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', padding: '0 4px 6px' }}><b style={{ color: '#fff' }}>Agents</b><span style={{ fontFamily: MONO, fontSize: 11, color: T.faint }}>fleet.yaml</span></div>
      <Caps style={{ padding: '6px 6px 4px' }}>GF_* · MANAGED</Caps>{AGENTS.filter(a => !a.legacy).map(agv)}
      <Caps style={{ padding: '12px 6px 4px' }}>EXISTING · NEVER MODIFIED</Caps>{AGENTS.filter(a => a.legacy).map(agv)}
      <Caps style={{ padding: '12px 6px 4px' }}>EPHEMERAL CLONES</Caps><div style={{ padding: '5px 9px', fontFamily: MONO, fontSize: 11, color: T.faint }}>none alive · last sweep 06:20</div>
      <Caps style={{ padding: '12px 6px 4px' }}>ADMIN</Caps>
      {([['engine', 'Engine environment'], ['settings', 'Settings & degraded states']] as const).map(([k, l]) => <div key={k} onClick={() => setTab(k)} style={{ padding: '7px 9px', borderRadius: 6, cursor: 'pointer', background: tab === k ? T.selected : 'transparent', color: tab === k ? '#fff' : T.secondary, fontSize: 12.5 }}>{l}</div>)}
    </div>
    <div style={{ flex: 1, minWidth: 0, padding: '18px 22px', display: 'flex', flexDirection: 'column', gap: 14, overflow: 'auto' }}>
      {tab === 'agent' && <>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}><div style={{ display: 'flex', gap: 10, alignItems: 'baseline', flexWrap: 'wrap' }}><span style={{ fontFamily: MONO, fontWeight: 700, fontSize: 16, color: '#fff' }}>{A.n}</span><Tag c={A.legacy ? T.secondary : C.ok}>{A.legacy ? 'existing · skipped by ensure_fleet' : 'managed · create-if-missing'}</Tag></div><div style={{ color: T.secondary }}>{A.d}</div></div>
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1.1fr) minmax(0,1.5fr) minmax(0,.6fr)', gap: 10, fontSize: 12.5 }}>
          <div style={{ background: T.surface, border: `1px solid ${T.control}`, borderRadius: 6, padding: '9px 11px' }}><div style={{ color: T.muted, fontSize: 11.5 }}>model</div><div style={{ fontFamily: MONO, color: '#fff', fontSize: 12, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>openai/gpt-4o-mini</div><div style={{ fontSize: 11, color: T.muted }}>{A.legacy ? 'own config, untouched' : 'adopted from the server, not fleet.yaml'}</div></div>
          <div style={{ background: T.surface, border: `1px solid ${T.control}`, borderRadius: 6, padding: '9px 11px' }}><div style={{ color: T.muted, fontSize: 11.5 }}>sources</div><div style={{ fontFamily: MONO, color: '#fff', fontSize: 12, wordBreak: 'break-word' }}>{A.src.length ? A.src.join(', ') : '—'}</div></div>
          <div style={{ background: T.surface, border: `1px solid ${T.control}`, borderRadius: 6, padding: '9px 11px' }}><div style={{ color: T.muted, fontSize: 11.5 }}>runs · 24 h</div><div style={{ fontFamily: MONO, color: '#fff', fontSize: 12 }}>{A.runs}</div></div></div>
        <Caps>CORE MEMORY · persona</Caps>
        <div style={{ background: T.surface, border: `1px solid ${T.control}`, borderRadius: 6, padding: '11px 13px', lineHeight: 1.55, fontSize: 13 }}>{A.p}</div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}><Caps style={{ whiteSpace: 'nowrap' }}>CORE MEMORY · gf_house_rules · shared</Caps><span style={{ fontSize: 11.5, color: T.muted, whiteSpace: 'nowrap' }}>{A.legacy ? 'uses its own pp_house_rules block' : 'seeded at create time'}</span></div>
        <div style={{ background: T.deeper, border: `1px solid ${T.hair}`, borderRadius: 6, padding: '11px 13px', display: 'flex', flexDirection: 'column', gap: 5, fontSize: 12.5, lineHeight: 1.45 }}>{HOUSE_RULES.map((r, i) => <div key={i} style={{ display: 'grid', gridTemplateColumns: '12px 1fr', gap: 6, color: T.text }}><span style={{ color: T.faint }}>–</span><span>{r}</span></div>)}</div>
      </>}
      {tab === 'engine' && <>
        <div style={{ display: 'flex', gap: 10, alignItems: 'baseline' }}><b style={{ color: '#fff', fontSize: 16 }}>Engine environment</b><span style={{ fontFamily: MONO, fontSize: 11.5, color: T.faint }}>pp_assets.check_environment · canon sync · manifest</span></div>
        {envErr && <Banner kind="warn">{envErr}. Until a route exists, run <span style={{ fontFamily: MONO }}>python3 -c "import pp_assets; print(pp_assets.check_environment())"</span> in the container.</Banner>}
        {env && <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,minmax(0,1fr))', gap: 10, fontSize: 12.5 }}>
            {([['engine', 'pp-document-suite ' + env.version, T.text], ['canon', env.canon, T.text], ['sync', env.synced && env.hash === env.hashExpected ? `hash ${env.hash} = manifest` : `hash ${env.hash} ≠ ${env.hashExpected}`, env.synced && env.hash === env.hashExpected ? C.ok : C.bad]] as const).map(([k, v, c]) =>
              <div key={k} style={{ background: T.surface, border: `1px solid ${T.control}`, borderRadius: 6, padding: '9px 11px' }}><div style={{ color: T.muted, fontSize: 11.5 }}>{k}</div><div style={{ fontFamily: MONO, color: c, fontSize: 12 }}>{v}</div></div>)}</div>
          <Caps>FONTS · subset-webfont shadowing</Caps>
          <div style={{ background: T.deeper, border: `1px solid ${T.hair}`, borderRadius: 6, padding: '9px 11px', fontFamily: MONO, fontSize: 11.5, display: 'flex', flexDirection: 'column', gap: 5 }}>{env.fonts.map(f => <div key={f.face} style={{ display: 'grid', gridTemplateColumns: '16px 150px 1fr', gap: 8 }}><span style={{ color: f.ok ? C.ok : C.bad }}>{f.ok ? '✓' : '✗'}</span><span style={{ color: '#fff' }}>{f.face}</span><span style={{ color: f.ok ? T.secondary : T.errText }}>{f.file}{f.missing ? ` · missing Macedonian letters: ${f.missing}` : ''}</span></div>)}</div>
          {env.fonts.some(f => !f.ok) && <Banner kind="err">A cut-down font is shadowing the full face. Builds will pass on this machine's view but print boxes for the missing letters; pp_verify's render-environment check FAILs while this is present.</Banner>}
          <Caps>GLYPH AUDIT · last runs</Caps>
          <div style={{ background: T.deeper, border: `1px solid ${T.hair}`, borderRadius: 6, padding: '9px 11px', fontFamily: MONO, fontSize: 11.5, display: 'flex', flexDirection: 'column', gap: 5 }}>{env.glyphAudit.map(g => <div key={g.run} style={{ display: 'grid', gridTemplateColumns: '16px 170px 1fr', gap: 8 }}><span style={{ color: g.ok ? C.ok : C.warn }}>{g.ok ? '✓' : '!'}</span><span style={{ color: '#fff' }}>{g.run}</span><span style={{ color: g.ok ? T.secondary : C.warn }}>{g.note}</span></div>)}</div>
          <Caps>MANIFEST DRIFT · live config vs committed manifest</Caps>
          <div style={{ border: `1px solid ${T.hair}`, borderRadius: 6, overflow: 'hidden', fontFamily: MONO, fontSize: 11.5 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 120px 120px', gap: 8, padding: '6px 10px', background: T.pane, color: T.muted }}><span>key</span><span>manifest</span><span>live</span></div>
            {env.manifestDrift.map(d => <div key={d.key} style={{ display: 'grid', gridTemplateColumns: '1fr 120px 120px', gap: 8, padding: '6px 10px', borderTop: `1px solid ${T.hair}`, color: d.manifest === d.live ? T.secondary : C.warn }}><span>{d.key}</span><span>{d.manifest}</span><span>{d.live}{d.manifest !== d.live ? '  ≠' : ''}</span></div>)}</div>
        </>}
      </>}
      {tab === 'settings' && <>
        <b style={{ color: '#fff', fontSize: 16 }}>Settings</b>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}><span style={{ width: 160, fontFamily: MONO, fontSize: 11.5, color: T.muted }}>API</span><Seg items={[['live', 'live · ppdocwiz + DocEngine'], ['mock', 'mock · sample data']]} value={api.mode} onPick={m => m !== api.mode && setMode(m)} size={12.5} /></div>
        <div style={{ fontSize: 12, color: T.muted, lineHeight: 1.5, paddingLeft: 172 }}>Live calls /api/* on this origin and DocEngine at <span style={{ fontFamily: MONO }}>{window.PP_SUITE_CONFIG?.docengineBase || '/api/docengine'}</span> (set window.PP_SUITE_CONFIG.docengineBase; DocEngine has no public port, so it needs a same-origin proxy).</div>
        <Caps style={{ marginTop: 6 }}>TWEAKS · Create menu</Caps>
        {([['Placement', 'createPlacement', [['topbar', 'top bar'], ['sidebar', 'sidebar']]], ['Style', 'createStyle', [['pill', 'pill'], ['button', 'button']]], ['Second menu opens on', 'submenuOpenOn', [['hover', 'hover'], ['click', 'click']]]] as const).map(([label, k, items]) =>
          <div key={k} style={{ display: 'flex', gap: 12, alignItems: 'center' }}><span style={{ width: 160, fontSize: 12.5, color: T.secondary }}>{label}</span><Seg items={items as never} value={tweaks[k] as never} onPick={v => setTweaks({ [k]: v })} size={12.5} /></div>)}
        <Caps style={{ marginTop: 6 }}>DEGRADED STATES {api.mode === 'mock' ? '· simulate' : ''}</Caps>
        {faults ? ([['storage', 'DocEngine storage down', '503 on /workflows, /documents · Jobs and Library show the outage'], ['letta', 'Letta unavailable', '503 on POST /workflows · 502 on chat'], ['chatDisabled', 'Chat disabled', 'no LETTA_BASE_URL on ppdocwiz · /api/chat 503'], ['gotenberg', 'Gotenberg down', 'PDF 502 from DocEngine'], ['libreoffice', 'No LibreOffice in ppdocwiz', '/api/download/*.pdf → 501'], ['badKey', 'Reject the key', 'next sign-in gets 401']] as const).map(([k, label, d]) =>
          <label key={k} style={{ display: 'grid', gridTemplateColumns: '20px 220px 1fr', gap: 8, alignItems: 'center', cursor: 'pointer', fontSize: 12.5 }}><input type="checkbox" checked={faults[k]} onChange={() => flip(k)} /><span style={{ color: faults[k] ? C.bad : T.text }}>{label}</span><span style={{ color: T.muted, fontSize: 12 }}>{d}</span></label>)
          : <div style={{ fontSize: 12.5, color: T.muted }}>Live mode reports the real state: the top-bar dots, this page's /health panel and every screen's own error banner (401, 410, 422, 501, 502, 503).</div>}
      </>}
    </div>
    <div style={{ width: 380, flex: 'none', borderLeft: `1px solid ${T.hair}`, background: T.deeper, padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between' }}><b style={{ color: '#fff' }}>GET /health</b><span style={{ fontFamily: MONO, fontSize: 11.5, color: deOk ? C.ok : C.bad }}>{h.code || '…'}</span></div>
      <div style={{ fontFamily: MONO, fontSize: 11.5, lineHeight: 1.6, color: T.secondary, background: T.bg, border: `1px solid ${T.hair}`, borderRadius: 6, padding: '9px 11px' }}>
        {de ? <><div>{'{'}</div><div>  "ok": {hl(de.ok)}, "db": {hl(de.db)},</div><div>  "letta": {hl(de.letta)},</div><div>  "engine": <span style={{ color: C.warn }}>"{de.engine}"</span></div><div>{'}'}</div></> : <span style={{ color: C.bad }}>{h.err || 'unreachable'}</span>}</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>{services.map(([name, port, meta, st]) => <div key={name} style={{ background: T.surface, border: `1px solid ${T.control}`, borderRadius: 6, padding: '7px 9px' }}>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}><Dot c={C[st as 'ok']} /><b style={{ color: '#fff', fontSize: 12 }}>{name}</b><span style={{ marginLeft: 'auto', fontFamily: MONO, fontSize: 10.5, color: T.muted }}>{port}</span></div>
        <div style={{ fontSize: 11, color: st === 'bad' ? C.bad : T.secondary, marginTop: 3 }}>{meta}</div></div>)}</div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}><b style={{ color: '#fff' }}>Log tail</b><span style={{ fontFamily: MONO, fontSize: 11.5, color: api.mode === 'mock' ? T.muted : C.ok }}>{api.mode === 'mock' ? 'sample' : '● live'}</span></div>
      <div style={{ fontFamily: MONO, fontSize: 11, lineHeight: 1.7, color: T.secondary, overflow: 'hidden' }}>{LOG_LINES.map((t, i) => <div key={i} style={{ whiteSpace: 'pre', color: /FAIL|gap|FIX|reaped/.test(t) ? C.warn : /PASS|200/.test(t) ? T.secondary : T.muted }}>{t}</div>)}</div>
    </div>
  </>;
}
