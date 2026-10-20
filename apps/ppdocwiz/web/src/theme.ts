// Design tokens from the Hybrid v2 handoff (design_handoff_pp_suite/README.md · Design tokens).
export const T = {
  // Light theme (Head of QC, 20.10.2026: "much lighter background on the platform altogether"). The names are the
  // dark theme's, so every screen moved with the tokens: bg the page, pane the side columns, deep the work area,
  // deeper the inputs and code blocks, surface the cards.
  bg: '#f4f7fb',
  pane: '#ffffff',
  deep: '#eef3f8',
  deeper: '#ffffff',
  surface: '#f7f9fc',
  selected: '#e3edf8',
  hair: '#e1e7ef',
  control: '#c9d4e1',
  focus: '#3d6a99',
  text: '#1f2d3d',
  strong: '#0f1f33',
  /** Text on the navy and status fills (buttons, heading bars). */
  onAccent: '#ffffff',
  secondary: '#4a5d72',
  muted: '#66788d',
  faint: '#8696a8',
  navy: '#2B547E',
  purple: '#7b4fa6',
  comment: '#66788d',
  okSurface: '#e9f7ee',
  okBorder: '#9fd3b0',
  okText: '#1e6b3a',
  errSurface: '#fdecea',
  errBorder: '#f1b0a8',
  errText: '#9b2c22',
  warnSurface: '#fff6e5',
  warnBorder: '#f0cf8e',
  warnText: '#7a5410',
} as const;

export type Status = 'ok' | 'warn' | 'bad' | 'run' | 'idle';

export const C: Record<Status, string> = { ok: '#2e8b57', warn: '#b7791f', bad: '#c0392b', run: '#2b6cb0', idle: '#94a3b8' };
export const G: Record<Status, string> = { ok: '✓', warn: '!', bad: '✗', run: '●', idle: '○' };
export const TINT: Record<Status, string> = {
  ok: 'rgba(46,139,87,.1)', warn: 'rgba(183,121,31,.1)', bad: 'rgba(192,57,43,.1)', run: 'rgba(43,108,176,.1)', idle: 'transparent',
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
