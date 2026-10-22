// Questionnaire → workflow (handoff §3). Banks come from GET /questionnaires/{key}.
import { useEffect, useRef, useState } from 'react';
import { create } from 'zustand';
import { ApiError, type Questionnaire as Q } from '../api/types';
import { Banner, DefTag, Seg } from '../components/ui';
import { usePrimary } from '../lib/usePrimary';
import { useApp } from '../store/store';
import { pick, tr } from '../lib/i18n';
import { C, DISPLAY, MONO, T } from '../theme';

type Ans = Record<string, string | string[]>;
// The requester's own instructions and sources, per questionnaire, sent with the answers.
type Extra = { instructions: string; sources: string; parent_sop: string };
const useAns = create<{ ans: Record<string, Ans>; setAns: (k: string, a: Ans) => void; extra: Record<string, Extra>; setExtra: (k: string, e: Partial<Extra>) => void }>(set => ({
  ans: { sop_qc: { focus: 'Potency', sample_types: ['Bulk', 'Finished product'], techniques: ['HPLC-DAD', 'LOD'], acceptance: ['Total THC within the strain\'s grade window (official potency specifications)', 'LOD NMT 12 %'] }, annex_form: { purpose: 'Recording' } },
  setAns: (k, a) => set(s => ({ ans: { ...s.ans, [k]: a } })),
  extra: {},
  setExtra: (k, e) => set(s => ({ extra: { ...s.extra, [k]: { ...{ instructions: '', sources: '', parent_sop: '' }, ...s.extra[k], ...e } } })),
}));

export function Questionnaire() {
  const { api, qKey, qRound, metas, set, go, busy, flash, lang } = useApp();
  const { ans: all, setAns, extra: allExtra, setExtra } = useAns();
  const extra = allExtra[qKey] || { instructions: '', sources: '', parent_sop: '' };
  const [bank, setBank] = useState<Q | null>(null);
  const [err, setErr] = useState('');
  // The questionnaire list comes from DocEngine; the two original banks stay as the fallback.
  const [keys, setKeys] = useState<[string, string][]>([['sop_qc', 'sop_qc · SOP'], ['annex_form', 'annex_form']]);
  useEffect(() => { api.questionnaires().then(l => { if (l.length) setKeys(l.map(q => [q.key, q.doctype === 'SOP' ? `${q.key} · SOP` : q.key])); }).catch(() => {}); }, [api]);
  useEffect(() => { setBank(null); setErr(''); api.questionnaire(qKey).then(setBank).catch((e: ApiError) => setErr(`${e.status} · ${e.message}`)); }, [api, qKey]);
  const ans = all[qKey] || {}, meta = metas[qKey] || { title_mk: '', title_en: '', code: '', version: '01', orient: 'portrait' as const };
  const missing = (['title_mk', 'title_en', 'code'] as const).filter(k => !(meta[k] || '').trim());
  // One start per click: a double click or Enter used to start two full pipelines for one code (review 14.10.2026).
  const starting = useRef(false);
  const start = async () => {
    if (missing.length || busy || starting.current) return;
    starting.current = true;
    try {
      const sources = extra.sources.split('\n').map(x => x.trim()).filter(Boolean);
      const r = await api.startWorkflow({ questionnaire: qKey, answers: ans, meta, requested_by: api.mode === 'live' ? 'ppdocwiz-session' : 'darko.s', instructions: extra.instructions.trim(), sources, parent_sop: extra.parent_sop.trim() });
      go('jobs', { jobSel: r.job_id }); flash(`job ${r.job_id.slice(0, 8)} queued · polling every 1 s`);
    } catch (e) { setErr(`${(e as ApiError).status} · ${(e as Error).message}`); }
    finally { starting.current = false; }
  };
  usePrimary(tr(lang, 'Start workflow ▸'), start, missing.length > 0);
  if (!bank) return <div style={{ padding: 22, color: err ? C.bad : T.muted, fontFamily: MONO, fontSize: 12 }}>{err ? `GET /questionnaires/${qKey} → ${err}` : 'loading…'}</div>;

  const answered = (k: string) => { const v = ans[k]; return Array.isArray(v) ? v.length > 0 : !!v; };
  const rnd = bank.rounds[Math.min(qRound, bank.rounds.length - 1)];
  const toggle = (key: string, multi: boolean, v: string) => {
    const a = { ...ans };
    if (multi) { const cur = (a[key] as string[]) || []; a[key] = cur.includes(v) ? cur.filter(x => x !== v) : [...cur, v]; } else a[key] = a[key] === v ? '' : v;
    setAns(qKey, a);
  };
  const brief = bank.rounds.flatMap(r => r.questions).map(q => {
    const defs = q.options.filter(o => o.isDefault).map(o => o.v);
    if (answered(q.key)) return { k: q.key, v: Array.isArray(ans[q.key]) ? (ans[q.key] as string[]).join(', ') : String(ans[q.key]), def: false, c: T.text };
    if (defs.length) return { k: q.key, v: defs.join(', '), def: true, c: T.text };
    return { k: q.key, v: '— open', def: false, c: C.warn };
  });
  const setMeta = (k: string, v: string) => set(s => ({ metas: { ...s.metas, [qKey]: { ...s.metas[qKey], [k]: v } } }));
  const mono = { fontFamily: MONO, fontSize: 11.5, color: T.muted } as const;

  return <>
    <div style={{ width: 236, flex: 'none', borderRight: `1px solid ${T.hair}`, background: T.pane, padding: '14px 10px', display: 'flex', flexDirection: 'column', gap: 6 }}>
      <Seg items={keys} value={qKey} onPick={k => set({ qKey: k, qRound: 0 })} size={12} pad="5px 6px" fill style={{ marginBottom: 6, flexWrap: 'wrap', rowGap: 2 }} />
      <div style={{ padding: '0 4px 8px' }}><b style={{ color: '#fff' }}>{pick(lang, bank)[0]}</b><div style={{ fontSize: 12, color: T.muted }}>{pick(lang, bank)[1]} · doctype {bank.doctype}</div></div>
      {bank.rounds.map((r, i) => {
        const done = r.questions.filter(q => answered(q.key)).length, cur = i === Math.min(qRound, bank.rounds.length - 1), allDone = done === r.questions.length;
        return <div key={i} onClick={() => set({ qRound: i })} style={{ padding: '8px 10px', borderRadius: 6, display: 'flex', gap: 9, alignItems: 'center', cursor: 'pointer', background: cur ? T.selected : 'transparent' }}>
          <span style={{ width: 20, height: 20, borderRadius: '50%', display: 'grid', placeItems: 'center', fontSize: 11, fontWeight: 700, flex: 'none', background: cur ? C.run : allDone ? C.ok : 'transparent', color: cur || allDone ? T.bg : T.secondary, border: `1px solid ${cur ? C.run : allDone ? C.ok : T.faint}` }}>{allDone && !cur ? '✓' : i + 1}</span>
          <div style={{ minWidth: 0 }}><div style={{ color: cur ? '#fff' : T.secondary, fontWeight: cur ? 700 : 400 }}>{pick(lang, r)[0]}</div><div style={{ fontSize: 11.5, color: T.muted, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{pick(lang, r)[1].replace(/^[RР]\d — /, '')} · {done}/{r.questions.length}</div></div></div>;
      })}
      <div style={{ marginTop: 'auto', background: T.surface, border: `1px solid ${T.control}`, borderRadius: 6, padding: 10, fontSize: 12, color: T.secondary, lineHeight: 1.45 }}><span style={{ fontFamily: MONO, color: C.run }}>apply_defaults()</span> {tr(lang, 'defaults_note')}</div>
    </div>
    <div style={{ flex: 1, minWidth: 0, padding: '18px 22px', display: 'flex', flexDirection: 'column', gap: 12, overflow: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 12 }}><div style={{ fontFamily: DISPLAY, fontWeight: 700, fontSize: 18, color: '#fff', whiteSpace: 'nowrap' }}>{pick(lang, rnd)[0]} <span style={{ fontFamily: 'Carlito', fontWeight: 400, fontSize: 14, color: T.secondary }}>| {pick(lang, rnd)[1]}</span></div><span style={{ fontFamily: MONO, fontSize: 11.5, color: T.faint, whiteSpace: 'nowrap' }}>GET /questionnaires/{qKey}</span></div>
      {rnd.questions.map(q => {
        const defs = q.options.filter(o => o.isDefault).map(o => o.v), sel = q.multi ? (ans[q.key] as string[] || []) : [ans[q.key]];
        const note = answered(q.key) ? tr(lang, 'answered') + (q.multi ? ' · ' + sel.length + ' ' + tr(lang, 'selected') : '') : defs.length ? tr(lang, 'unanswered → default:') + ' ' + defs.join(', ') : tr(lang, 'unanswered → no default exists; stays open in the brief');
        return <div key={q.key} style={{ background: T.surface, border: `1px solid ${T.control}`, borderRadius: 8, padding: '13px 15px', display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 10 }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#fff', display: 'flex', flexWrap: 'wrap', columnGap: 6, alignItems: 'baseline' }}><span>{pick(lang, q)[0]}</span><span style={{ fontWeight: 400, color: T.secondary, fontSize: 13, whiteSpace: 'nowrap' }}>| {pick(lang, q)[1]}</span></div>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center', flex: 'none' }}><span style={{ fontFamily: MONO, fontSize: 11, color: T.faint }}>{q.key}</span><span style={{ fontSize: 11, border: `1px solid ${T.control}`, borderRadius: 3, padding: '1px 6px', color: T.secondary }}>{q.multi ? 'multi' : 'single'}</span></div>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7, fontSize: 13 }}>{q.options.map(o => { const on = sel.includes(o.v);
            return <span key={o.v} onClick={() => toggle(q.key, q.multi, o.v)} style={{ cursor: 'pointer', whiteSpace: 'normal', maxWidth: '100%', borderRadius: 6, padding: '6px 11px', display: 'flex', gap: 6, alignItems: 'center', background: on ? T.navy : 'transparent', color: on ? '#fff' : T.text, border: `1px solid ${on ? T.focus : T.control}` }}>{on ? '✓ ' : ''}{o.v}{o.isDefault && <DefTag />}</span>; })}</div>
          <div style={{ fontSize: 12, color: answered(q.key) ? T.muted : defs.length ? C.ok : C.warn }}>{note}</div>
        </div>;
      })}
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
        <span onClick={() => set({ qRound: Math.max(0, qRound - 1) })} style={{ cursor: 'pointer', color: qRound > 0 ? C.run : T.faint }}>{tr(lang, '← Previous round')}</span>
        <span onClick={() => set({ qRound: Math.min(bank.rounds.length - 1, qRound + 1) })} style={{ cursor: 'pointer', color: qRound < bank.rounds.length - 1 ? C.run : T.faint }}>{tr(lang, 'Next round →')}</span></div>
    </div>
    <div style={{ width: 360, flex: 'none', borderLeft: `1px solid ${T.hair}`, background: T.pane, padding: 16, display: 'flex', flexDirection: 'column', gap: 10, fontSize: 13, overflow: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}><b style={{ color: '#fff', fontSize: 14 }}>{tr(lang, 'Document meta')}</b><span style={{ fontFamily: MONO, fontSize: 11, color: T.faint }}>body.meta</span></div>
      {([['title_mk', '*'], ['title_en', '*'], ['code', '*'], ['version', '']] as const).map(([k, req]) => <label key={k} style={{ display: 'grid', gridTemplateColumns: '76px 1fr', gap: 8, alignItems: 'center' }}>
        <span style={mono}>{k}<span style={{ color: C.bad }}>{req}</span></span>
        <input value={meta[k] || ''} onChange={e => setMeta(k, e.target.value)} style={{ background: T.deeper, border: `1px solid ${req && !(meta[k] || '').trim() ? C.bad : T.control}`, borderRadius: 5, padding: '6px 8px', color: '#fff', outline: 'none', minWidth: 0 }} /></label>)}
      <div style={{ display: 'grid', gridTemplateColumns: '76px 1fr', gap: 8, alignItems: 'center' }}><span style={mono}>orient</span>
        <Seg items={[['portrait', 'portrait'], ['landscape', 'landscape']]} value={meta.orient} onPick={o => setMeta('orient', o)} size={12} pad="4px" fill /></div>
      <div style={{ height: 1, background: T.hair, margin: '4px 0' }} />
      <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}><span><b style={{ color: '#fff', fontSize: 14 }}>{tr(lang, 'Instructions')}</b> <span style={{ fontSize: 11.5, color: T.muted }}>· {tr(lang, 'your prompt to the authors')}</span></span>
        <textarea data-field="instructions" value={extra.instructions} onChange={e => setExtra(qKey, { instructions: e.target.value })} rows={6} style={{ background: T.deeper, border: `1px solid ${T.control}`, borderRadius: 5, padding: '6px 8px', color: '#fff', outline: 'none', resize: 'vertical', font: 'inherit', fontSize: 12.5, lineHeight: 1.4 }} /></label>
      <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}><span><b style={{ color: '#fff', fontSize: 14 }}>{tr(lang, 'Sources')}</b> <span style={{ fontSize: 11.5, color: T.muted }}>· {tr(lang, 'one per line; the authors may cite them')}</span></span>
        <textarea data-field="sources" value={extra.sources} onChange={e => setExtra(qKey, { sources: e.target.value })} rows={4} style={{ background: T.deeper, border: `1px solid ${T.control}`, borderRadius: 5, padding: '6px 8px', color: '#fff', outline: 'none', resize: 'vertical', font: 'inherit', fontSize: 12.5, lineHeight: 1.4 }} /></label>
      {bank.doctype !== 'SOP' && <label style={{ display: 'grid', gridTemplateColumns: '76px 1fr', gap: 8, alignItems: 'center' }}><span style={mono} title={tr(lang, 'the SOP this form serves — DocEngine reads its sections 6 and 7')}>parent</span>
        <input data-field="parent_sop" value={extra.parent_sop} onChange={e => setExtra(qKey, { parent_sop: e.target.value })} placeholder="WHSOP_003" style={{ background: T.deeper, border: `1px solid ${T.control}`, borderRadius: 5, padding: '6px 8px', color: '#fff', outline: 'none', minWidth: 0 }} /></label>}
      <div style={{ height: 1, background: T.hair, margin: '4px 0' }} />
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}><b style={{ color: '#fff', fontSize: 14 }}>{tr(lang, 'Content brief')}</b><span style={{ fontSize: 11.5, color: T.muted }}>{brief.filter(b => b.def).length} {tr(lang, 'by default')} · {brief.filter(b => b.v === '— open').length} {tr(lang, 'open')}</span></div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12.5 }}>{brief.map(b => <div key={b.k} style={{ display: 'grid', gridTemplateColumns: '118px 1fr', gap: 8, lineHeight: 1.35 }}><span style={{ fontFamily: MONO, fontSize: 11.5, color: T.muted }}>{b.k}</span><span style={{ color: b.c }}>{b.v}{b.def && <span style={{ marginLeft: 6 }}><DefTag /></span>}</span></div>)}</div>
      <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: 6, paddingTop: 8 }}>
        {missing.length > 0 && <div style={{ fontFamily: MONO, fontSize: 12, color: C.bad }}>400 · meta.{missing[0]} required</div>}
        {err && <Banner kind="err">POST /workflows → {err}</Banner>}
        <button onClick={start} style={{ background: missing.length || busy ? T.control : T.navy, color: '#fff', border: 0, borderRadius: 6, padding: '10px 16px', font: 'inherit', fontWeight: 700, cursor: 'pointer' }}>POST /workflows ▸</button>
        <div style={{ fontSize: 11.5, color: T.muted, textAlign: 'center' }}>{tr(lang, 'Creates a job and opens it in Jobs')}</div>
      </div>
    </div>
  </>;
}
