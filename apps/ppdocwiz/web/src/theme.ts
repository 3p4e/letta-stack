// Design tokens from the Hybrid v2 handoff (design_handoff_pp_suite/README.md · Design tokens).
export const T = {
  bg: '#0f1a26',
  pane: '#132131',
  deep: '#0c1621',
  deeper: '#0a131c',
  surface: '#16253a',
  selected: '#1d3550',
  hair: '#1f2e3d',
  control: '#2a3c50',
  focus: '#3d6a99',
  text: '#d6e2f0',
  strong: '#fff',
  secondary: '#9fb6cc',
  muted: '#7f93a8',
  faint: '#4b6077',
  navy: '#2B547E',
  purple: '#c59fe0',
  comment: '#6f8399',
  okSurface: '#123524',
  okBorder: '#2f6b45',
  okText: '#bfe8cb',
  errSurface: '#3a1a16',
  errBorder: '#5a2a2a',
  errText: '#f3c1ba',
  warnSurface: '#3a2a12',
} as const;

export type Status = 'ok' | 'warn' | 'bad' | 'run' | 'idle';

export const C: Record<Status, string> = { ok: '#6fd08c', warn: '#f0b45a', bad: '#e07a6f', run: '#7fb2e5', idle: '#4b6077' };
export const G: Record<Status, string> = { ok: '✓', warn: '!', bad: '✗', run: '●', idle: '○' };
export const TINT: Record<Status, string> = {
  ok: 'rgba(111,208,140,.1)', warn: 'rgba(240,180,90,.1)', bad: 'rgba(224,122,111,.12)', run: 'rgba(127,178,229,.1)', idle: 'transparent',
};

export const MONO = 'ui-monospace,Menlo,monospace';
export const UI = 'Carlito,Calibri,system-ui,sans-serif';
export const DISPLAY = 'Montserrat';

// Document (page) colours — pp_theme.py / pp_format.py.
export const PAGE = {
  navy: '#2B547E', rule: '#7F7F7F', ruleLight: '#B0BEC5', label: '#F2F2F2', shading: '#E8E8E8', secondary: '#595959',
  labelCell: '#EDF2F7', zebra: '#F7FAFC',
  // pp_format.status_band fills and text colours
  draftFill: '#FDEDEC', approvedFill: '#EAFAF1', red: '#C00000', green: '#375623',
} as const;
