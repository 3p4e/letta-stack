// A4 page preview in house style (PP Page.dc.html, pp_format.py / build_from_md.py).
// An approximation of the Word output for live feedback — production previews the real
// Gotenberg PDF. Every block carries a data-a anchor so overlays and margin stamps are
// placed from measured positions, not by eye.
import { useLayoutEffect, useRef, useState, type CSSProperties, type ReactNode } from 'react';
import type { Block, DocStatus, WizardPayload } from '../api/types';
import { PAGE } from '../theme';

export const PAGE_W = 794, PAGE_H = 1123;
const logo = '/assets/brand/pp_logo_header.jpg';

// pp_format.status_label / header_version / effective_display
export const STATUS_LABEL: Record<DocStatus, [string, string]> = {
  draft: ['РАБОТНА ВЕРЗИЈА — НЕ ЗА УПОТРЕБА', 'DRAFT — NOT FOR USE'],
  in_review: ['ЗА ПРЕГЛЕД И ОДОБРУВАЊЕ — НЕ ЗА УПОТРЕБА', 'IN REVIEW / FOR APPROVAL — NOT FOR USE'],
  approved: ['ОДОБРЕНО ЗА УПОТРЕБА', 'APPROVED FOR USE'],
};
export const headerVersion = (st: DocStatus, v: string) => st === 'approved' ? 'v' + v : st === 'draft' ? 'DRAFT' : 'IN REVIEW';
export const effectiveDisplay = (st: DocStatus, eff: string) => st === 'approved' ? (eff || '____.____.______') : '—';

export interface Highlight { anchor: string; kind: 'sel' | 'warn' | 'bad' | 'ok' | 'hover' }
export type AnchorMap = Record<string, { top: number; height: number }>;

const HL: Record<Highlight['kind'], CSSProperties> = {
  sel: { border: '3px solid #7fb2e5', borderRadius: 3, boxShadow: '0 0 0 6px rgba(127,178,229,.2)' },
  warn: { border: '3px dashed #f0b45a', borderRadius: 3, background: 'rgba(240,180,90,.12)' },
  bad: { border: '4px solid #e07a6f', background: 'rgba(224,122,111,.1)' },
  ok: { border: '3px solid #6fd08c', background: 'rgba(111,208,140,.12)' },
  hover: { border: '3px solid transparent' },
};

const sm = (t: string, size = 9.5, extra: CSSProperties = {}) => t ? <span style={{ fontSize: size, fontWeight: 400, color: PAGE.secondary, ...extra }}> | {t}</span> : null;
const td: CSSProperties = { border: `1px solid ${PAGE.ruleLight}`, padding: '6px 8px' };

function AnnexBlock({ b, a }: { b: Block; a: string }) {
  if (b.type === 'form') return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14, marginBottom: 14 }}><tbody>
      {b.rows.map((r, i) => (
        <tr key={i} data-a={`${a}r${i}`}>
          <td style={{ ...td, background: PAGE.labelCell, fontWeight: 700, textAlign: 'center', width: '46%' }}>{r.label_mk}{sm(r.label_en)}</td>
          <td style={{ ...td, background: i % 2 ? PAGE.zebra : undefined }}>{r.value && r.value !== '_' ? r.value : ''}</td>
        </tr>))}
    </tbody></table>);
  if (b.type === 'table') return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, textAlign: 'center', marginBottom: 14 }}><tbody>
      <tr data-a={`${a}h`} style={{ fontWeight: 700, background: PAGE.labelCell }}>{b.cols.map((c, i) => <td key={i} style={{ ...td, padding: 5 }}>{c.mk}{sm(c.en, 9)}</td>)}</tr>
      {b.rows.map((r, i) => (
        <tr key={i} data-a={`${a}r${i}`} style={{ background: i % 2 ? PAGE.zebra : undefined }}>
          {r.map((c, j) => <td key={j} style={{ ...td, padding: 6, height: 30 }}>{c.mk}{sm(c.en, 9)}</td>)}
        </tr>))}
    </tbody></table>);
  const bullets = b.type === 'bullets';
  return <div style={{ margin: '0 0 12px' }}>{b.paras.map((p, i) => (
    <p key={i} data-a={`${a}r${i}`} style={{ margin: '0 0 6px', fontSize: 14, textAlign: 'justify', lineHeight: 1.4, paddingLeft: bullets ? 18 : 0, textIndent: bullets ? -12 : 0 }}>
      {bullets ? '• ' : ''}{p.mk}{p.en ? <span style={{ fontSize: 10.5, color: PAGE.secondary, fontStyle: 'italic' }}> | {p.en}</span> : null}
    </p>))}</div>;
}

function Header({ mk, en, code, ver }: { mk: string; en: string; code: string; ver: string }) {
  return (
    <table data-a="header" style={{ width: '100%', borderCollapse: 'collapse', borderTop: `2px solid ${PAGE.rule}`, borderBottom: `2px solid ${PAGE.rule}`, fontSize: 11 }}><tbody>
      <tr>
        <td rowSpan={2} style={{ width: 150, padding: '4px 8px', borderRight: `1px solid ${PAGE.ruleLight}` }}><img src={logo} alt="" style={{ width: 130, display: 'block' }} /></td>
        <td rowSpan={2} style={{ padding: '4px 10px', borderRight: `1px solid ${PAGE.ruleLight}`, textAlign: 'center' }}>
          <div style={{ fontSize: 9, color: PAGE.secondary }}>Име на документ | Document name:</div>
          <div style={{ fontFamily: "'Arial Narrow',Arial,sans-serif", fontWeight: 700, fontSize: 15, textTransform: 'uppercase', letterSpacing: '-.2px', lineHeight: 1.1, marginTop: 2 }}>{mk}</div>
          <div style={{ fontFamily: "'Arial Narrow',Arial,sans-serif", fontSize: 10, textTransform: 'uppercase', color: '#333', marginTop: 2 }}>{en}</div>
        </td>
        <td style={{ width: 150, padding: '4px 8px', textAlign: 'center', borderBottom: `1px solid ${PAGE.ruleLight}` }}>
          <div style={{ fontSize: 9, color: PAGE.secondary }}>Код на документ | Code of document:</div>
          <div style={{ fontWeight: 700, fontSize: 14 }}>{code}</div>
        </td>
      </tr>
      <tr><td style={{ padding: '4px 8px', textAlign: 'center', fontSize: 11 }}>Верзија | Ver: <b>{ver}</b></td></tr>
    </tbody></table>);
}

/** pp_format.status_band — used on the SOP title page and the report cover. */
export function StatusBand({ status, version, eff, review }: { status: DocStatus; version: string; eff: string; review?: string }) {
  const [mk, en] = STATUS_LABEL[status], ok = status === 'approved';
  return (
    <div data-a="status" style={{ margin: '28px 0 18px', border: `1px solid ${PAGE.ruleLight}`, background: ok ? PAGE.approvedFill : PAGE.draftFill, textAlign: 'center', padding: 10 }}>
      <div style={{ fontWeight: 700, fontSize: 15, color: ok ? PAGE.green : PAGE.red }}>{mk} | {en}</div>
      <div style={{ fontWeight: 700, fontSize: 13, marginTop: 4 }}>
        Верзија | Version: {headerVersion(status, version)}{'     ·     '}Датум на важност | Effective date: {effectiveDisplay(status, eff)}
        {ok && review ? <span style={{ fontWeight: 400, color: PAGE.secondary }}>{'     ·     '}Датум на преглед | Review date: {review}</span> : null}
      </div>
    </div>);
}

function AnnexBody({ p }: { p: WizardPayload }) {
  const st = p.status || 'draft', [smk, sen] = STATUS_LABEL[st];
  return <>
    <div data-a="title" style={{ textAlign: 'center', margin: '22px 0 14px' }}>
      <div style={{ fontWeight: 700, fontSize: 16, color: PAGE.navy }}>{p.code}</div>
      <div style={{ fontWeight: 700, fontSize: 18, marginTop: 4, lineHeight: 1.25 }}>{p.mk_title}{sm(p.en_title, 12, { fontWeight: 700 })}</div>
      <div style={{ fontSize: 12, marginTop: 4, color: PAGE.secondary, fontStyle: 'italic' }}>({p.parent || p.code})</div>
      <div data-a="status" style={{ fontSize: 11, marginTop: 6 }}>
        <b style={{ color: st === 'approved' ? PAGE.green : PAGE.red }}>{smk} | {sen}</b>
        <span style={{ color: PAGE.secondary, fontSize: 10 }}>{'   —   '}Верзија | Version: {headerVersion(st, p.version)}{'   ·   '}Датум на важност | Effective date: {effectiveDisplay(st, p.effective_date)}</span>
      </div>
      {p.supersedes ? <div style={{ fontSize: 11, marginTop: 4 }}>Заменува: {p.supersedes}<span style={{ fontSize: 9, color: PAGE.secondary }}> | Supersedes: {p.supersedes}</span></div> : null}
    </div>
    {p.sections.map((s, si) => (
      <div key={si} data-a={`s${si}`}>
        <div data-a={`s${si}t`} style={s.level === 1
          ? { background: PAGE.navy, color: '#fff', fontWeight: 700, padding: '5px 8px', border: `1px solid ${PAGE.ruleLight}`, textAlign: 'center', fontSize: 14 }
          : { borderBottom: `1.5px solid ${PAGE.navy}`, color: PAGE.navy, fontWeight: 700, padding: '4px 2px', fontSize: 13, marginTop: 4 }}>
          {s.num ? s.num + ' ' : ''}{s.mk}{s.en ? <span style={{ fontSize: 9.5, fontWeight: 400 }}> | {s.en}</span> : null}
        </div>
        {s.blocks.map((b, bi) => <div key={bi} data-a={`s${si}b${bi}`}><AnnexBlock b={b} a={`s${si}b${bi}`} /></div>)}
      </div>))}
  </>;
}

function SopBody({ p }: { p: WizardPayload }) {
  const H: CSSProperties = { background: PAGE.shading, fontWeight: 700, padding: '5px 8px', fontSize: 15 };
  const L: CSSProperties = { padding: '6px 10px 10px 0', borderRight: '.5px solid #000', verticalAlign: 'top', width: '50%' };
  const R: CSSProperties = { padding: '6px 0 10px 10px', verticalAlign: 'top' };
  const rows: ReactNode[] = [];
  p.sections.forEach((s, si) => {
    const num = s.num ? s.num.replace(/\.0$/, '') + ' ' : '';
    rows.push(<tr key={'h' + si} data-a={`s${si}t`}><td style={{ ...H, borderRight: '.5px solid #000' }}>{num}{s.mk}</td><td style={H}>{num}{s.en}</td></tr>);
    s.blocks.forEach((b, bi) => {
      const a = `s${si}b${bi}`;
      if (b.type === 'text' || b.type === 'bullets') b.paras.forEach((pa, i) => rows.push(
        <tr key={a + i} data-a={`${a}r${i}`}><td style={L}>{b.type === 'bullets' ? '• ' : ''}{pa.mk}</td><td style={R}>{b.type === 'bullets' ? '• ' : ''}{pa.en}</td></tr>));
      else if (b.type === 'form') b.rows.forEach((r, i) => rows.push(
        <tr key={a + i} data-a={`${a}r${i}`}><td style={L}><b>{r.label_mk}:</b> {r.value !== '_' ? r.value : ''}</td><td style={R}><b>{r.label_en}:</b> {r.value !== '_' ? r.value : ''}</td></tr>));
      else rows.push(<tr key={a} data-a={a}><td colSpan={2} style={{ padding: '8px 0' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, textAlign: 'center' }}><tbody>
          <tr data-a={`${a}h`} style={{ background: PAGE.navy, color: '#fff', fontWeight: 700 }}>{b.cols.map((c, i) => <td key={i} style={{ border: `1px solid ${PAGE.ruleLight}`, padding: 5 }}>{c.mk}{c.en ? <span style={{ fontSize: 9, fontWeight: 400 }}> | {c.en}</span> : null}</td>)}</tr>
          {b.rows.map((r, i) => <tr key={i} data-a={`${a}r${i}`} style={{ background: i % 2 ? PAGE.zebra : undefined }}>{r.map((c, j) => <td key={j} style={{ border: `1px solid ${PAGE.ruleLight}`, padding: 5, ...(j === 0 ? { background: PAGE.labelCell, fontWeight: 700 } : {}) }}>{c.mk}{c.en ? <span style={{ fontSize: 9, color: PAGE.secondary }}> | {c.en}</span> : null}</td>)}</tr>)}
        </tbody></table></td></tr>);
    });
  });
  return <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14, marginTop: 22, textAlign: 'justify' }}><tbody>{rows}</tbody></table>;
}

function SopTitle({ p }: { p: WizardPayload }) {
  return <div style={{ textAlign: 'center', marginTop: 120 }}>
    <div style={{ fontSize: 17, color: PAGE.secondary, fontWeight: 700 }}>{p.code} · {headerVersion(p.status, p.version)}</div>
    <div style={{ marginTop: 18, fontSize: 30, color: PAGE.navy, fontWeight: 700, lineHeight: 1.2 }}>{p.mk_title}</div>
    <div style={{ fontSize: 18, color: PAGE.navy, marginTop: 6 }}>{p.en_title}</div>
    <StatusBand status={p.status} version={p.version} eff={p.effective_date} review={p.review_date} />
    {p.supersedes ? <div style={{ fontSize: 12, color: PAGE.secondary }}>Заменува | Supersedes: {p.supersedes}</div> : null}
  </div>;
}

function RawSample() {
  return <div style={{ fontFamily: "'Times New Roman',serif", fontSize: 15, lineHeight: 1.5, marginTop: 24, color: '#222' }}>
    <p style={{ margin: '0 0 10px', fontWeight: 700, fontSize: 18 }}>Release record clones</p>
    <p style={{ margin: '0 0 10px' }}>1. Consignment — Пратка</p>
    <p style={{ margin: '0 0 10px' }}>Customs declaration MRN / MRN на царинска декларација: ________</p>
    <p style={{ margin: '0 0 10px' }}>Arrival date/time / Датум/време на пристигнување: ________</p>
    <p style={{ margin: '0 0 10px', fontFamily: "'Comic Sans MS',cursive", color: '#c00' }}>Arrival temp:  ____ (check!!)</p>
    <p style={{ margin: '0 0 10px' }}>2. Phytosanitary and release</p>
    <p style={{ margin: '0 0 10px' }}>- phytosanitary inspection   ref ___   status ___</p>
    <p style={{ margin: '0 0 10px' }}>- SPL sampling   ref ___   status ___</p>
    <p style={{ margin: '0 0 10px' }}>- CoC   ref ___   status ___</p>
  </div>;
}

export interface PPPageProps {
  doc?: WizardPayload;
  raw?: boolean;
  zoom: number;
  page?: number; pages?: number;
  sopPage?: 'title' | 'body';
  highlights?: Highlight[];
  onPick?: (anchor: string) => void;
  onLayout?: (m: AnchorMap) => void;
  shadow?: boolean;
  children?: ReactNode;
  /** Block-level clickable zones (Preview): anchors that become hoverable/clickable overlays. */
  zones?: string[];
  /** Extra boxes (e.g. a whole SOP section grouped from its rows) usable as zone / highlight anchors. */
  extraBoxes?: AnchorMap;
}

export function PPPage({ doc, raw, zoom, page, pages, sopPage = 'body', highlights = [], onPick, onLayout, shadow = true, zones, extraBoxes, children }: PPPageProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<AnchorMap>({});
  const sop = doc?.doctype === 'SOP';
  useLayoutEffect(() => {
    const root = ref.current; if (!root) return;
    const m: AnchorMap = {};
    root.querySelectorAll<HTMLElement>('[data-a]').forEach(el => {
      let top = 0, n: HTMLElement | null = el;
      while (n && n !== root) { top += n.offsetTop; n = n.offsetParent as HTMLElement | null; }
      m[el.dataset.a!] = { top, height: el.offsetHeight };
    });
    setMap(prev => JSON.stringify(prev) === JSON.stringify(m) ? prev : m);
  });
  useLayoutEffect(() => { onLayout?.(map); }, [map]); // eslint-disable-line react-hooks/exhaustive-deps
  const box = (a: string) => extraBoxes?.[a] || map[a];
  return (
    <div style={{ width: PAGE_W * zoom, height: PAGE_H * zoom, overflow: 'hidden', flex: 'none', position: 'relative' }}>
      <div ref={ref} onClick={e => {
        if (!onPick) return;
        const el = (e.target as HTMLElement).closest('[data-z],[data-a]') as HTMLElement | null;
        if (el) onPick(el.dataset.z || el.dataset.a!);
      }} style={{
        width: PAGE_W, height: PAGE_H, transform: `scale(${zoom})`, transformOrigin: '0 0', background: '#fff',
        fontFamily: 'Calibri,Carlito,sans-serif', color: '#000', padding: '36px 48px', boxSizing: 'border-box', position: 'relative',
        boxShadow: shadow ? '0 1px 2px rgba(0,0,0,.12),0 8px 28px rgba(15,26,38,.14)' : undefined, cursor: onPick ? 'pointer' : undefined, overflow: 'hidden',
      }}>
        {raw || !doc ? <><Header mk="" en="" code="" ver="" /><RawSample /></> : <>
          <Header mk={doc.mk_title} en={doc.en_title} code={doc.code} ver={headerVersion(doc.status || 'draft', doc.version)} />
          {sop ? (sopPage === 'title' ? <SopTitle p={doc} /> : <SopBody p={doc} />) : <AnnexBody p={doc} />}
        </>}
        <div style={{ position: 'absolute', right: 48, bottom: 22, fontSize: 15 }}>Page {page ?? (sop ? (sopPage === 'title' ? 1 : 3) : 1)} of {pages ?? (sop ? 9 : 1)}</div>
        {zones?.map(a => box(a) && <div key={'z' + a} className="pp-zone" data-z={a} style={{ position: 'absolute', left: 44, right: 44, top: box(a).top - 4, height: box(a).height + 8, borderRadius: 3 }} />)}
        {highlights.map((h, i) => box(h.anchor) && <div key={i} style={{ position: 'absolute', left: 44, right: 44, top: box(h.anchor).top - 4, height: box(h.anchor).height + 8, pointerEvents: 'none', ...HL[h.kind] }} />)}
        {children}
      </div>
    </div>);
}
