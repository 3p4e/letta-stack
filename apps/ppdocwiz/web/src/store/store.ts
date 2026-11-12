import type { Lang } from '../lib/i18n';
import { create } from 'zustand';
import type { Api } from '../api/client';
import { liveApi } from '../api/live';
import { mockApi } from '../api/mock';
import type { Me, WizardPayload } from '../api/types';
import { SAMPLE_ANNEX } from '../data/samples';
import { skeleton } from '../lib/newdoc';
import type { Status } from '../theme';

export type Screen = 'flow' | 'builder' | 'chat' | 'quest' | 'format' | 'report' | 'library' | 'jobs' | 'canvas' | 'verify' | 'preview' | 'fleet' | 'users';
export const SCREENS: Screen[] = ['flow', 'builder', 'chat', 'quest', 'format', 'report', 'library', 'jobs', 'canvas', 'verify', 'preview', 'fleet', 'users'];

export interface Sheet {
  doctype: 'SOP' | 'ANNEX' | 'FORM' | 'LOG' | 'CHECKLIST' | 'REPORT';
  path: Screen; extra: Partial<AppState>;
  code: string; title_mk: string; title_en: string; version: string; parent: string; supersedes: string; orient: 'portrait' | 'landscape';
}

export interface Tweaks { createPlacement: 'topbar' | 'sidebar'; createStyle: 'pill' | 'button'; submenuOpenOn: 'hover' | 'click' }

const LS = { screen: 'ppsuite.screen', api: 'ppsuite.api', tweaks: 'ppsuite.tweaks', lang: 'ppsuite.lang' };
const read = (k: string) => { try { return localStorage.getItem(k); } catch { return null; } };
const write = (k: string, v: string) => { try { localStorage.setItem(k, v); } catch { /* blocked */ } };

function initialMode(): 'live' | 'mock' {
  const q = new URLSearchParams(location.search).get('api');
  if (q === 'live' || q === 'mock') { write(LS.api, q); return q; }
  const saved = read(LS.api);
  if (saved === 'live' || saved === 'mock') return saved;
  // Served by the backend → live; `npm run dev` without a backend → mock.
  return import.meta.env.DEV ? 'mock' : 'live';
}

export interface LastBuild { code: string; ok: boolean; verify: string; docx?: string; pdf?: string; at: string }

export interface AppState {
  api: Api;
  /** bumps whenever the mock's in-memory data changes, so polling screens re-read */
  dataRev: number;
  screen: Screen;
  authed: boolean | null;
  /** Who is signed in (named accounts, phase 5); null until known. */
  me: Me | null;
  tweaks: Tweaks;
  /** The last real build in this session (Builder wizard or Source view). Verify and Preview show it in live mode. */
  lastBuild: LastBuild | null;
  // pipeline bar
  pipe: Status[]; pipeDoc: string; pipeMsg: string; pipeOk: boolean; busy: boolean;
  toast: string;
  // create flow
  createOpen: boolean; createCat: string; menuX: number; menuY: number; sheet: Sheet | null;
  // cross-screen document state
  bdoc: WizardPayload; bdocIsSample: boolean; builderMode: 'src' | 'page' | 'blocks'; hlLine: number;
  /** Markdown handed to the Builder's raw view by another screen (Jobs "Open Markdown in Builder"); the Builder takes it once and clears it. */
  builderRaw: string | null;
  chatDraft: string; chatAgent: string;
  /** Interface language; documents stay bilingual whatever it is. */
  lang: Lang; setLang: (l: Lang) => void;
  qKey: string; qRound: number; metas: Record<string, { title_mk: string; title_en: string; code: string; version: string; orient: 'portrait' | 'landscape' }>;
  jobSel: string | null; libSel: string | null;
  /** The job whose draft the canvas holds (20.10.2026). */
  canvasJob: string | null;
  fmt: 'B' | 'C';
  repMeta: { code: string; mk: string; en: string; ver: string } | null; repSel: string;
  /** The top-bar primary button: each screen registers its own label and action. */
  primary: { label: string; run: () => void; disabled?: boolean } | null;
  /** Service dots: null = unknown / probing */
  svc: { letta: Status; docengine: Status; pdf: Status; note: Record<string, string> };
  set: (p: Partial<AppState> | ((s: AppState) => Partial<AppState>)) => void;
  go: (s: Screen, extra?: Partial<AppState>) => void;
  setMode: (m: 'live' | 'mock') => void;
  setTweaks: (t: Partial<Tweaks>) => void;
  flash: (t: string) => void;
  /** Animate the bottom pipeline bar around a real call. `task` resolves to pass/fail and the failing step. */
  run: (doc: string, task: () => Promise<{ ok: boolean; failAt?: number; msg?: string }>) => Promise<boolean>;
}

let toastTimer = 0;

export const useApp = create<AppState>((set, get) => {
  const mode = initialMode();
  const bump = () => set(s => ({ dataRev: s.dataRev + 1 }));
  const savedScreen = read(LS.screen) as Screen | null;
  let tweaks: Tweaks = { createPlacement: 'topbar', createStyle: 'pill', submenuOpenOn: 'hover' };
  try { tweaks = { ...tweaks, ...JSON.parse(read(LS.tweaks) || '{}') }; } catch { /* default */ }
  return {
    api: mode === 'mock' ? mockApi(bump) : liveApi(),
    dataRev: 0,
    screen: savedScreen && SCREENS.includes(savedScreen) ? savedScreen : 'jobs',
    authed: mode === 'mock' ? true : null,
    me: null,
    tweaks,
    // mock opens on the prototype's last-run state; live starts idle until something actually builds
    ...(mode === 'mock' ? { pipe: ['ok', 'ok', 'ok', 'ok'] as Status[], pipeDoc: 'WHSOP_002_A02', pipeMsg: 'RESULT: PASS · 1.84 s' } : { pipe: ['idle', 'idle', 'idle', 'idle'] as Status[], pipeDoc: '—', pipeMsg: 'no build yet' }),
    pipeOk: true, busy: false, lastBuild: null,
    toast: '',
    createOpen: false, createCat: 'sop', menuX: 0, menuY: 0, sheet: null,
    // Live mode opens on nothing: the sample annex (WHSOP_002_A02) used to be loaded as if it were the user's draft,
    // and Build turned it into a real registered file (review 18.10.2026). Mock mode keeps the demo document.
    bdoc: mode === 'mock' ? structuredClone(SAMPLE_ANNEX) : skeleton({ doctype: 'ANNEX', code: '', title_mk: '', title_en: '', version: '01', parent: '', supersedes: '', orient: 'portrait' }),
    bdocIsSample: mode === 'mock', builderMode: 'src', hlLine: 0, builderRaw: null,
    chatDraft: '', chatAgent: 'qms_docx_formatter',
    lang: read(LS.lang) === 'mk' ? 'mk' : 'en',
    setLang: l => { write(LS.lang, l); set({ lang: l }); },
    qKey: 'sop_qc', qRound: 0,
    metas: {
      sop_qc: { title_mk: 'Определување потентност', title_en: 'Potency determination', code: '', version: '01', orient: 'portrait' },
      sop_transport: { title_mk: 'Внатрешен (копнен) транспорт на опојни дроги — медицински канабис', title_en: 'Inland Transport of Narcotic Drugs — Medical Cannabis', code: 'WHSOP003', version: '01', orient: 'portrait' },
      annex_form: { title_mk: 'Дневник на прием', title_en: 'Receipt log', code: '', version: '01', orient: 'portrait' },
    },
    jobSel: null, libSel: null, canvasJob: read('ppsuite.canvas') || null, fmt: 'B', repMeta: null, repSel: 'b5',
    primary: null,
    svc: { letta: 'idle', docengine: 'idle', pdf: 'idle', note: {} },
    set: p => set(p as never),
    go: (screen, extra) => { write(LS.screen, screen); if (extra?.canvasJob) write('ppsuite.canvas', extra.canvasJob); set({ screen, createOpen: false, ...(extra || {}) }); },
    setMode: m => { write(LS.api, m); location.reload(); },
    setTweaks: t => { const next = { ...get().tweaks, ...t }; write(LS.tweaks, JSON.stringify(next)); set({ tweaks: next }); },
    flash: t => { clearTimeout(toastTimer); set({ toast: t }); toastTimer = window.setTimeout(() => set({ toast: '' }), 3200); },
    run: async (doc, task) => {
      if (get().busy) return false;
      const t0 = performance.now();
      const pipe: Status[] = ['run', 'idle', 'idle', 'idle'];
      set({ busy: true, pipeDoc: doc, pipe: [...pipe], pipeMsg: 'running…', pipeOk: true });
      // Steps advance on a ~520 ms cadence while the call is in flight; production
      // would drive them from job/stage events instead (handoff README · Pipeline bar).
      let step = 0;
      const tick = window.setInterval(() => {
        if (step < 2) { pipe[step] = 'ok'; step++; pipe[step] = 'run'; set({ pipe: [...pipe] }); }
      }, 520);
      let r: { ok: boolean; failAt?: number; msg?: string };
      try { r = await task(); } catch (e) { r = { ok: false, failAt: 2, msg: String((e as Error).message || e) }; }
      clearInterval(tick);
      const min = 4 * 520 - (performance.now() - t0);
      if (min > 0) await new Promise(res => setTimeout(res, Math.min(min, 1200)));
      const failAt = r.ok ? -1 : (r.failAt ?? 2);
      const final: Status[] = [0, 1, 2, 3].map(i => failAt < 0 ? 'ok' : i < failAt ? 'ok' : i === failAt ? 'bad' : 'idle');
      set({
        busy: false, pipe: final, pipeOk: r.ok,
        pipeMsg: r.ok ? 'RESULT: PASS · ' + ((performance.now() - t0) / 1000).toFixed(2) + ' s' : (r.msg || 'RESULT: FAIL · 422'),
      });
      return r.ok;
    },
  };
});
