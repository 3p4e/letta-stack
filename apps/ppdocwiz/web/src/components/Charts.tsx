// SVG previews of the seven pp_charts.py figure types. The build embeds the matplotlib PNG;
// these exist so the author can pick the right chart and see it bound to the data.
import { mean, ols } from '../lib/stats';

export const CHARTS = [
  ['horrat_bar', 'HorRat per level', 'bars vs limit 2.0'],
  ['horwitz_plot', 'Horwitz curve', 'RSDr vs concentration'],
  ['guardband', 'Guard band', 'spec ± expanded U'],
  ['regression_scatter', 'Regression', 'x vs y, OLS fit, r'],
  ['bland_altman', 'Bland–Altman', 'diff vs mean, bias ± LoA'],
  ['bias_bar', 'Bias per level', 'signed bars'],
  ['qratio_bar', 'Q-ratio per level', 'bars vs limit 2.0'],
] as const;
export type ChartKind = typeof CHARTS[number][0];

const W = 300, H = 170, P = { l: 30, r: 10, t: 12, b: 22 };
const NAVY = '#2B547E', RED = '#C00000', GREY = '#8a96a3';

function scale(v: number[], lo: number, hi: number, a: number, b: number) { const min = Math.min(...v), max = Math.max(...v); const span = max - min || 1; return (x: number) => a + (x - min) / span * (b - a) * (hi - lo) / (hi - lo); }

export function Chart({ kind, values, x, width = W, height = H }: { kind: ChartKind; values: number[]; x?: number[]; width?: number; height?: number }) {
  const v = values.length ? values : [1.1, 0.8, 1.4, 0.9, 1.6, 1.2];
  const iw = width - P.l - P.r, ih = height - P.t - P.b;
  const axes = <g stroke="#555" strokeWidth={1}><line x1={P.l} y1={P.t} x2={P.l} y2={P.t + ih} /><line x1={P.l} y1={P.t + ih} x2={P.l + iw} y2={P.t + ih} /></g>;
  let body: JSX.Element;
  if (kind === 'horrat_bar' || kind === 'qratio_bar' || kind === 'bias_bar') {
    const signed = kind === 'bias_bar', max = Math.max(2.2, ...v.map(Math.abs)) * 1.1, bw = iw / v.length * .6;
    const y = (n: number) => signed ? P.t + ih / 2 - n / max * ih / 2 : P.t + ih - n / max * ih;
    body = <g>{v.map((n, i) => { const x0 = P.l + (i + .2) * iw / v.length; const y0 = y(Math.max(0, n)), y1 = y(Math.min(0, n));
      return <rect key={i} x={x0} y={signed ? y0 : y(n)} width={bw} height={signed ? Math.abs(y1 - y0) : P.t + ih - y(n)} fill={!signed && n > 2 ? RED : NAVY} />; })}
      {!signed && <line x1={P.l} x2={P.l + iw} y1={y(2)} y2={y(2)} stroke={RED} strokeDasharray="4 3" />}
      {signed && <line x1={P.l} x2={P.l + iw} y1={y(0)} y2={y(0)} stroke="#555" />}</g>;
  } else if (kind === 'horwitz_plot') {
    const pts = v.map((n, i) => ({ c: 10 ** (-1 - i * .6), r: n * 4 }));
    const hz = (c: number) => 2 ** (1 - .5 * Math.log10(c)); const xs = (c: number) => P.l + (-Math.log10(c) - 1) / 4 * iw, ys = (r: number) => P.t + ih - r / 20 * ih;
    const curve = Array.from({ length: 40 }, (_, i) => { const c = 10 ** (-1 - i / 10); return `${xs(c)},${ys(hz(c))}`; }).join(' ');
    body = <g><polyline points={curve} fill="none" stroke={GREY} strokeWidth={1.5} />{pts.map((p, i) => <circle key={i} cx={xs(p.c)} cy={ys(p.r)} r={3} fill={NAVY} />)}</g>;
  } else if (kind === 'guardband') {
    const spec = 12, U = 0.6, m = mean(v), lo = spec - 3, hi = spec + 1, ys = (n: number) => P.t + ih - (n - lo) / (hi - lo) * ih;
    body = <g><rect x={P.l} width={iw} y={ys(spec)} height={ys(spec - U) - ys(spec)} fill="rgba(192,0,0,.12)" /><line x1={P.l} x2={P.l + iw} y1={ys(spec)} y2={ys(spec)} stroke={RED} /><line x1={P.l} x2={P.l + iw} y1={ys(spec - U)} y2={ys(spec - U)} stroke={RED} strokeDasharray="4 3" />
      {v.map((n, i) => <circle key={i} cx={P.l + (i + .5) * iw / v.length} cy={ys(n)} r={3} fill={NAVY} />)}<line x1={P.l} x2={P.l + iw} y1={ys(m)} y2={ys(m)} stroke={NAVY} strokeDasharray="2 2" /></g>;
  } else {
    const xv = x && x.length === v.length ? x : v.map((_, i) => i + 1);
    if (kind === 'regression_scatter') { const { slope, intercept } = ols(xv, v), sx = scale(xv, 0, 1, P.l, P.l + iw), sy = (n: number) => P.t + ih - (n - Math.min(...v)) / ((Math.max(...v) - Math.min(...v)) || 1) * ih;
      const x0 = Math.min(...xv), x1 = Math.max(...xv);
      body = <g>{xv.map((xi, i) => <circle key={i} cx={sx(xi)} cy={sy(v[i])} r={3} fill={NAVY} />)}<line x1={sx(x0)} y1={sy(slope * x0 + intercept)} x2={sx(x1)} y2={sy(slope * x1 + intercept)} stroke={RED} /></g>; }
    else { const means = v.map((n, i) => (n + xv[i]) / 2), diffs = v.map((n, i) => n - xv[i]), b = mean(diffs), s = Math.sqrt(diffs.reduce((a, d) => a + (d - b) ** 2, 0) / Math.max(1, diffs.length - 1));
      const lim = Math.max(...diffs.map(Math.abs), Math.abs(b) + 2 * s) * 1.2 || 1, sx = scale(means, 0, 1, P.l, P.l + iw), sy = (d: number) => P.t + ih / 2 - d / lim * ih / 2;
      body = <g>{[b, b + 1.96 * s, b - 1.96 * s].map((l, i) => <line key={i} x1={P.l} x2={P.l + iw} y1={sy(l)} y2={sy(l)} stroke={i ? RED : NAVY} strokeDasharray={i ? '4 3' : undefined} />)}{means.map((m, i) => <circle key={i} cx={sx(m)} cy={sy(diffs[i])} r={3} fill={NAVY} />)}</g>; }
  }
  return <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ background: '#fff', display: 'block' }}>{axes}{body}</svg>;
}
