import { create } from 'zustand';
import type { Api } from '../api/client';
import { liveApi } from '../api/live';
import { mockApi } from '../api/mock';
import type { WizardPayload } from '../api/types';
import { SAMPLE_ANNEX } from '../data/samples';
import type { Status } from '../theme';

export type Screen = 'builder' | 'chat' | 'quest' | 'format' | 'report' | 'library' | 'jobs' | 'verify' | 'preview' | 'fleet';
export const SCREENS: Screen[] = ['builder', 'chat', 'quest', 'format', 'report', 'library', 'jobs', 'verify', 'preview', 'fleet'];

export interface Sheet {
  doctype: 'SOP' | 'ANNEX' | 'FORM' | 'LOG' | 'CHECKLIST' | 'REPORT';
  path: Screen; extra: Partial<AppState>;
  code: string; title_mk: string; title_en: string; version: string; parent: string; supersedes: string; orient: 'portrait' | 'landscape';
}

export interface Tweaks { createPlacement: 'topbar' | 'sidebar'; createStyle: 'pill' | 'button'; submenuOpenOn: 'hover' | 'click' }

const LS = { screen: 'ppsuite.screen', api: 'ppsuite.api', tweaks: 'ppsuite.tweaks' };
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

export interface AppState {
  api: Api;
  /** bumps whenever the mock's in-memory data changes, so polling screens re-read */
  dataRev: number;
  screen: Screen;
  authed: boolean | null;
  tweaks: Tweaks;
  // pipeline bar
  pipe: Status[]; pipeDoc: string; pipeMsg: string; pipeOk: boolean; busy: boolean;
  toast: string;
  // create flow
  createOpen: boolean; createCat: string; menuX: number; menuY: number; sheet: Sheet | null;
  // cross-screen document state
  bdoc: WizardPayload; bdocIsSample: boolean; builderMode: 'src' | 'page' | 'blocks'; hlLine: number;
  chatDraft: string; chatAgent: string;
  qKey: string; qRound: number; metas: Record<string, { title_mk: string; title_en: string; code: string; version: string; orient: 'portrait' | 'landscape' }>;
  jobSel: string | null; libSel: string | null;
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
    tweaks,
    // mock opens on the prototype's last-run state; live starts idle until something actually builds
    ...(mode === 'mock' ? { pipe: ['ok', 'ok', 'ok', 'ok'] as Status[], pipeDoc: 'WHSOP_002_A02', pipeMsg: 'RESULT: PASS · 1.84 s' } : { pipe: ['idle', 'idle', 'idle', 'idle'] as Status[], pipeDoc: '—', pipeMsg: 'no build yet' }),
    pipeOk: true, busy: false,
    toast: '',
    createOpen: false, createCat: 'sop', menuX: 0, menuY: 0, sheet: null,
    bdoc: structuredClone(SAMPLE_ANNEX), bdocIsSample: true, builderMode: 'src', hlLine: 0,
    chatDraft: '', chatAgent: 'qms_docx_formatter',
    qKey: 'sop_qc', qRound: 1,
    metas: {
      sop_qc: { title_mk: 'Определување потентност', title_en: 'Potency determination', code: 'QCSOP_031', version: '01', orient: 'portrait' },
      annex_form: { title_mk: 'Дневник на прием', title_en: 'Receipt log', code: 'WHSOP_002_A03', version: '01', orient: 'portrait' },
    },
    jobSel: null, libSel: null, fmt: 'B', repMeta: null, repSel: 'b5',
    primary: null,
    svc: { letta: 'idle', docengine: 'idle', pdf: 'idle', note: {} },
    set: p => set(p as never),
    go: (screen, extra) => { write(LS.screen, screen); set({ screen, createOpen: false, ...(extra || {}) }); },
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
