// ＋ Create two-level menu and the New-document sheet (handoff README · Create flow).
import { useEffect, useState } from 'react';
import type { Doctype } from '../api/types';
import { codePattern, skeleton } from '../lib/newdoc';
import { useApp, type AppState, type Screen, type Sheet } from '../store/store';
import { C, DISPLAY, MONO, T } from '../theme';
import { Caps } from './ui';

type Item = [string, string, Screen, Partial<AppState> | null];
const CATS: { k: string; label: string; sub: string; items: Item[] }[] = [
  { k: 'sop', label: 'SOP', sub: '9 sections · two-column MK | EN', items: [['From questionnaire', 'sop_qc · 4 rounds, apply_defaults', 'quest', { qKey: 'sop_qc', qRound: 0 }], ['Write in Markdown', 'HEADERDATA + sections, live page', 'builder', { builderMode: 'src' }], ['Ask an agent', 'gf_sop_author drafts, you review', 'chat', null]] },
  { k: 'annex', label: 'Annex / Form', sub: 'inline full page · navy banners', items: [['Wizard', 'deterministic, no LLM · form & table blocks', 'builder', { builderMode: 'blocks' }], ['From questionnaire', 'annex_form · 2 rounds', 'quest', { qKey: 'annex_form', qRound: 0 }], ['Ask an agent', 'gf_annex_author · [[FORM:grid]]', 'chat', null]] },
  { k: 'log', label: 'Log / Checklist', sub: 'registers, rows per page', items: [['Log / register', 'Seq No. · Date-Time · Issued by · Page X of Y', 'builder', { builderMode: 'src' }], ['Checklist', 'Yes / No / N-A · fail → deviation', 'builder', { builderMode: 'src' }]] },
  { k: 'report', label: 'Report / Record', sub: 'equations, charts, entry tables', items: [['Computational record', 'native Word equations · worked calc steps', 'report', null], ['Execution package', 'entry tables + execution sign-off', 'report', null], ['Validation report', 'statistical charts · figure captions', 'report', null]] },
  { k: 'format', label: 'Format existing', sub: 'bring a .docx into house style', items: [['Mode B · format', 'parse → Markdown → build', 'format', { fmt: 'B' }], ['Mode C · restyle', 'restyle in place · every w:t kept', 'format', { fmt: 'C' }]] },
];
const WHERE: Partial<Record<Screen, string>> = { quest: 'Questionnaire', builder: 'Builder', chat: 'Agent chat', format: 'Formatter', report: 'Reports' };

export function CreateMenu() {
  const { createOpen, createCat, menuX, menuY, tweaks, set, go } = useApp();
  if (!createOpen) return null;
  const cat = CATS.find(c => c.k === createCat) || CATS[0];
  const openSheet = (path: Screen, extra: Partial<AppState> | null) => {
    const DT: Record<string, Sheet['doctype']> = { sop: 'SOP', annex: 'ANNEX', log: 'LOG',report: 'REPORT' };
    set({ createOpen: false, sheet: { doctype: DT[cat.k] || 'ANNEX', path, extra: extra || {}, code: '', title_mk: '', title_en: '', version: '01', parent: '', supersedes: '', orient: 'portrait' } });
  };
  return <>
    <div onClick={() => set({ createOpen: false })} style={{ position: 'fixed', inset: 0, zIndex: 50 }} />
    <div style={{ position: 'absolute', zIndex: 51, left: menuX, top: menuY, display: 'flex', background: T.pane, border: `1px solid ${T.control}`, borderRadius: 10, boxShadow: '0 20px 50px rgba(0,0,0,.5)', overflow: 'hidden' }}>
      <div style={{ width: 270, padding: 6, borderRight: `1px solid ${T.hair}`, display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Caps style={{ padding: '6px 10px 4px' }}>WHAT TO CREATE</Caps>
        {CATS.map(c => <div key={c.k} onClick={() => set({ createCat: c.k })} onMouseEnter={() => tweaks.submenuOpenOn === 'hover' && set({ createCat: c.k })}
          style={{ padding: '8px 10px', borderRadius: 6, cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, background: c.k === cat.k ? T.selected : 'transparent' }}>
          <div style={{ minWidth: 0 }}><div style={{ color: '#fff', fontWeight: 700 }}>{c.label}</div><div style={{ fontSize: 11.5, color: T.muted, whiteSpace: 'nowrap' }}>{c.sub}</div></div><span style={{ color: T.muted }}>›</span>
        </div>)}
      </div>
      <div style={{ width: 340, padding: 6, display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Caps style={{ padding: '6px 10px 4px' }}>{cat.label.toUpperCase()} · START FROM</Caps>
        {cat.items.map(([label, desc, screen, extra]) => <div key={label} className="pp-hover-sel" onClick={() => {
          if (screen === 'format') go('format', { ...(extra || {}) }); else openSheet(screen, extra);
          if (cat.k === 'log') set(s => s.sheet ? { sheet: { ...s.sheet, doctype: label === 'Checklist' ? 'CHECKLIST' : 'LOG' } } : {});
        }} style={{ padding: '9px 10px', borderRadius: 6, cursor: 'pointer', display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'center' }}>
          <div style={{ minWidth: 0 }}><div style={{ color: '#fff' }}>{label}</div><div style={{ fontSize: 11.5, color: T.muted }}>{desc}</div></div>
          <span style={{ fontFamily: MONO, fontSize: 10.5, color: T.faint, whiteSpace: 'nowrap' }}>{WHERE[screen]}</span>
        </div>)}
      </div>
    </div>
  </>;
}

const PATHS: Record<Sheet['doctype'], [Screen, string][]> = {
  SOP: [['quest', 'Questionnaire'], ['builder', 'Markdown'], ['chat', 'Agent']], ANNEX: [['builder', 'Wizard'], ['quest', 'Questionnaire'], ['chat', 'Agent']],
  FORM: [['builder', 'Wizard'], ['quest', 'Questionnaire'], ['chat', 'Agent']], LOG: [['builder', 'Wizard'], ['chat', 'Agent']],
  CHECKLIST: [['builder', 'Wizard'], ['chat', 'Agent']], REPORT: [['report', 'Report composer'], ['chat', 'Agent']],
};
const LABEL: Record<Sheet['doctype'], string> = { SOP: 'SOP', ANNEX: 'annex', FORM: 'form', LOG: 'log', CHECKLIST: 'checklist', REPORT: 'report / record' };

export function NewDocSheet() {
  const { sheet: sh, set, go, flash, api } = useApp();
  const [registered, setRegistered] = useState<string[]>([]);
  useEffect(() => { if (sh) api.documents().then(d => setRegistered(d.map(x => x.code))).catch(() => setRegistered([])); }, [!!sh]); // eslint-disable-line react-hooks/exhaustive-deps
  if (!sh) return null;
  const upd = (k: keyof Sheet, v: string) => set(s => ({ sheet: { ...s.sheet!, [k]: v } }));
  const isSop = sh.doctype === 'SOP', isRep = sh.doctype === 'REPORT';
  const codeOk = codePattern(sh.doctype as Doctype).test(sh.code.trim()), taken = registered.includes(sh.code.trim());
  const arrow = (['code', 'title_mk', 'title_en', 'version', 'parent', 'supersedes'] as const).some(k => (sh[k] || '').includes('-->'));
  const cyr = /[Ѐ-ӿ]/.test(sh.title_mk), lat = /[A-Za-z]/.test(sh.title_en);
  const parentOk = isSop || isRep || !!sh.parent.trim();
  const ok = codeOk && cyr && lat && !arrow && parentOk;
  const FIELDS: [keyof Sheet, string, string, string, string][] = [
    ['code', '*', isSop ? 'QCSOP_031' : 'QCSOP_031_A03', !sh.code ? (isSop ? 'Pattern DEPTSOP_NNN' : 'Pattern DEPTSOP_NNN_ANN') : codeOk ? (taken ? 'Exists in the registry → this becomes a new version' : 'Code format OK') : 'Does not match the code pattern', !sh.code ? T.muted : codeOk ? (taken ? C.warn : C.ok) : C.bad],
    ['title_mk', '*', 'Наслов на македонски', sh.title_mk && !cyr ? 'Needs Cyrillic — Macedonian comes first' : 'Macedonian first', sh.title_mk && !cyr ? C.bad : T.muted],
    ['title_en', '*', 'English title', '', T.muted], ['version', '', '01', '', T.muted],
    ['parent', isSop || isRep ? '' : '*', isSop ? '—' : 'QCSOP 031', isSop ? 'SOPs have no parent' : 'The SOP this ' + sh.doctype.toLowerCase() + ' belongs to', T.muted],
    ['supersedes', '', '—', 'Rendered as Заменува | Supersedes under the title block', T.muted],
  ];
  const paths = PATHS[sh.doctype], pathLabel = (paths.find(p => p[0] === sh.path) || paths[0])[1];
  const hd: [string, string][] = ([['mk_title', sh.title_mk || '…'], ['en_title', sh.title_en || '…'], ['code', sh.code || '…'], ['version', sh.version || '01'], ['doctype', sh.doctype], ['status', 'draft']] as [string, string][])
    .concat(sh.parent ? [['parent', sh.parent]] : []).concat(sh.supersedes ? [['supersedes', sh.supersedes]] : []).concat([['orient', sh.orient]]);
  const checks: [boolean | null, string][] = [[codeOk, codeOk ? 'Code matches the house pattern' : 'Code pattern not met yet'], [cyr && lat, 'Title in both languages (MK Cyrillic, EN Latin)'], [!arrow, 'No "-->" in any field (it would end HEADERDATA early)'], [parentOk, isSop || isRep ? 'No parent needed' : 'Parent SOP given']];
  if (taken) checks.push([null, 'Code already registered; the old version stays effective until this one is approved']);
  const close = () => set({ sheet: null });
  const create = () => {
    if (!ok) return;
    const path = paths.some(p => p[0] === sh.path) ? sh.path : paths[0][0];
    if (path === 'quest') { const qk = isSop ? 'sop_qc' : 'annex_form'; set(st => ({ sheet: null, qKey: qk, qRound: 0, metas: { ...st.metas, [qk]: { title_mk: sh.title_mk, title_en: sh.title_en, code: sh.code, version: sh.version, orient: sh.orient } } })); go('quest'); }
    else if (path === 'chat') { set({ sheet: null, chatDraft: `Draft ${sh.doctype} ${sh.code} "${sh.title_mk} | ${sh.title_en}"${sh.parent ? ', parent ' + sh.parent : ''}. Leave unknown values blank.` }); go('chat'); }
    else if (path === 'report') { set({ sheet: null, repMeta: { code: sh.code, mk: sh.title_mk, en: sh.title_en, ver: sh.version }, repSel: 'b1' }); go('report'); }
    else { set({ sheet: null, hlLine: 0, bdocIsSample: false, bdoc: skeleton({ ...sh, doctype: sh.doctype as Doctype }), ...sh.extra }); go('builder'); }
    flash('Draft ' + sh.code + ' created · status draft · not for use');
  };
  const pickDt = (d: Sheet['doctype']) => set(st => { const keep = PATHS[d].map(p => p[0]); return { sheet: { ...st.sheet!, doctype: d, path: keep.includes(st.sheet!.path) ? st.sheet!.path : keep[0] } }; });
  const mono = { fontFamily: MONO, fontSize: 11.5, color: T.muted } as const;
  return <>
    <div onClick={close} style={{ position: 'fixed', inset: 0, zIndex: 60, background: 'rgba(5,10,16,.6)' }} />
    <div style={{ position: 'fixed', zIndex: 61, left: '50%', top: '50%', transform: 'translate(-50%,-50%)', width: 900, maxWidth: 'calc(100vw - 40px)', maxHeight: 'calc(100vh - 40px)', overflow: 'hidden', background: T.pane, border: `1px solid ${T.control}`, borderRadius: 12, boxShadow: '0 30px 70px rgba(0,0,0,.55)', display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 'none', padding: '16px 20px', borderBottom: `1px solid ${T.hair}`, display: 'flex', alignItems: 'baseline', gap: 12 }}>
        <span style={{ fontFamily: DISPLAY, fontWeight: 700, fontSize: 17, color: '#fff', whiteSpace: 'nowrap' }}>New {LABEL[sh.doctype]}</span>
        <span style={{ fontSize: 13, color: T.secondary, whiteSpace: 'nowrap' }}>starts in {pathLabel}</span>
        <span onClick={close} style={{ marginLeft: 'auto', cursor: 'pointer', color: T.muted, fontSize: 18 }}>×</span>
      </div>
      <div style={{ display: 'flex', flex: '1 1 auto', minHeight: 0, overflow: 'auto' }}>
        <div style={{ flex: 1, minWidth: 0, padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}><span style={{ ...mono, width: 96 }}>doctype</span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, fontSize: 12 }}>{(['SOP', 'ANNEX', 'FORM', 'LOG', 'CHECKLIST', 'REPORT'] as const).map(d =>
              <span key={d} onClick={() => pickDt(d)} style={{ padding: '5px 10px', borderRadius: 4, border: `1px solid ${T.control}`, cursor: 'pointer', whiteSpace: 'nowrap', background: sh.doctype === d ? T.navy : 'transparent', color: sh.doctype === d ? '#fff' : T.secondary }}>{d}</span>)}</div></div>
          {FIELDS.map(([k, req, ph, hint, hc]) => <label key={k} style={{ display: 'grid', gridTemplateColumns: '96px 1fr', gap: 10, alignItems: 'center' }}>
            <span style={mono}>{k}<span style={{ color: C.bad }}>{req}</span></span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <input value={String(sh[k] || '')} onChange={e => upd(k, e.target.value)} placeholder={ph} style={{ background: T.deeper, border: `1px solid ${hc === C.bad ? C.bad : T.control}`, borderRadius: 5, padding: '7px 9px', color: '#fff', outline: 'none', minWidth: 0 }} />
              {hint ? <span style={{ fontSize: 11.5, color: hc }}>{hint}</span> : null}
            </div></label>)}
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}><span style={{ ...mono, width: 96 }}>orient</span>
            <div style={{ display: 'flex', background: T.deeper, border: `1px solid ${T.control}`, borderRadius: 5, padding: 2, fontSize: 12 }}>{(['portrait', 'landscape'] as const).map(o =>
              <span key={o} onClick={() => upd('orient', o)} style={{ padding: '5px 12px', borderRadius: 3, cursor: 'pointer', background: sh.orient === o ? T.navy : 'transparent', color: sh.orient === o ? '#fff' : T.secondary }}>{o}</span>)}</div></div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}><span style={{ ...mono, width: 96 }}>start in</span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, fontSize: 12.5 }}>{paths.map(([k, label]) =>
              <span key={k} onClick={() => upd('path', k)} style={{ padding: '5px 11px', borderRadius: 999, cursor: 'pointer', border: `1px solid ${sh.path === k ? T.focus : T.control}`, background: sh.path === k ? T.selected : 'transparent', color: sh.path === k ? '#fff' : T.secondary }}>{label}</span>)}</div></div>
        </div>
        <div style={{ width: 330, flex: 'none', borderLeft: `1px solid ${T.hair}`, background: T.bg, padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <Caps>HEADERDATA PREVIEW</Caps>
          <div style={{ background: T.deeper, border: `1px solid ${T.hair}`, borderRadius: 6, padding: '10px 12px', fontFamily: MONO, fontSize: 11.5, lineHeight: 1.7 }}>
            <div style={{ color: T.comment }}>&lt;!--HEADERDATA</div>
            {hd.map(([k, v]) => <div key={k} style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}><span style={{ color: T.secondary }}>{k}:</span> <span style={{ color: T.text }}>{v}</span></div>)}
            <div style={{ color: T.comment }}>--&gt;</div>
          </div>
          <Caps style={{ marginTop: 4 }}>PRE-CHECKS</Caps>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12.5 }}>{checks.map(([v, t], i) =>
            <div key={i} style={{ display: 'grid', gridTemplateColumns: '16px 1fr', gap: 8, lineHeight: 1.35 }}><span style={{ color: v === null ? C.warn : v ? C.ok : T.faint, fontWeight: 700 }}>{v === null ? '!' : v ? '✓' : '○'}</span><span style={{ color: T.text }}>{t}</span></div>)}</div>
        </div>
      </div>
      <div style={{ flex: 'none', padding: '12px 20px', borderTop: `1px solid ${T.hair}`, display: 'flex', gap: 10, alignItems: 'center' }}>
        <span style={{ fontSize: 12, color: T.muted }}>Status starts as draft. Version and effective date become controlled only on approval.</span>
        <span onClick={close} style={{ marginLeft: 'auto', color: T.secondary, cursor: 'pointer', padding: '8px 12px' }}>Cancel</span>
        <button onClick={create} style={{ background: ok ? T.navy : T.control, color: '#fff', border: 0, borderRadius: 6, padding: '9px 18px', font: 'inherit', fontWeight: 700, cursor: ok ? 'pointer' : 'not-allowed' }}>Create draft →</button>
      </div>
    </div>
  </>;
}
