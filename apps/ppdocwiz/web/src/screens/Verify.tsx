// Verify gate FAIL (handoff §8). The sample annex has a 9-column table whose EN halves shrink below
// the 6 pt floor; the fixes really rewrite the Markdown and rebuild through POST /build.
import { create } from 'zustand';
import { ApiError, type WizardPayload } from '../api/types';
import { PPPage } from '../components/PPPage';
import { Banner, Btn, PaneHead } from '../components/ui';
import { SAMPLE_PEST } from '../data/samples';
import { composeMarkdown } from '../lib/compose';
import { usePrimary } from '../lib/usePrimary';
import { lineColor, verifyReport } from '../lib/verify';
import { useApp } from '../store/store';
import { C, DISPLAY, G, MONO, T } from '../theme';
import { VerifyLive } from '../components/LiveViews';

const COLS = ['№', 'Култура~~Crop', 'Зона~~Zone', 'Штетник~~Pest', 'Праг~~Threshold', 'Наод~~Finding', 'Мерка~~Action', 'Датум~~Date', 'Потпис~~Signature'];
const cell = (s: string) => { const [mk, en = ''] = s.split('~~'); return { mk, en }; };
const WIDE: WizardPayload = { ...SAMPLE_PEST, sections: [
  { num: '1', mk: 'Општо', en: 'General', level: 1, blocks: [{ type: 'form', rows: [{ label_mk: 'Просторија', label_en: 'Room', value: '' }, { label_mk: 'Датум', label_en: 'Date', value: '' }] }] },
  { num: '2', mk: 'Опрема', en: 'Equipment', level: 1, blocks: [{ type: 'table', cols: [cell('№'), cell('Опрема~~Equipment'), cell('Статус~~Status')], rows: [[cell('1'), cell('Лупа~~Magnifier'), cell('')]] }] },
  { num: '3', mk: 'Извидување', en: 'Scouting', level: 1, blocks: [{ type: 'table', cols: COLS.map(cell), rows: [1, 2, 3].map(i => COLS.map((_, j) => cell(j ? '' : String(i)))) }] },
] };
const split = (p: WizardPayload): WizardPayload => { const t = p.sections[2].blocks[0]; if (t.type !== 'table') return p;
  const a = [0, 1, 2, 3, 4], b = [0, 5, 6, 7, 8];
  return { ...p, version: '02', sections: [...p.sections.slice(0, 2), { ...p.sections[2], blocks: [{ type: 'table', cols: a.map(i => t.cols[i]), rows: t.rows.map(r => a.map(i => r[i])) }, { type: 'table', cols: b.map(i => t.cols[i]), rows: t.rows.map(r => b.map(i => r[i])) }] }] }; };
const minFont = (p: WizardPayload) => p.sections.some(s => s.blocks.some(b => b.type === 'table' && b.cols.length >= 9)) && p.orient === 'portrait' ? 5.5 : 6.5;
const FAIL0 = verifyReport('/data/WHSOP_009_A01.docx', { paras: 22, tables: 3, words: 402, chars: 2894, minFont: 5.5 });

const useV = create<{ doc: WizardPayload; report: string; fixed: boolean; how: string }>(() => ({ doc: WIDE, report: FAIL0, fixed: false, how: '' }));

export function Verify() {
  const { api } = useApp();
  return api.mode === 'live' ? <VerifyLive /> : <VerifySample />;
}

/** The scripted mock-mode screen (sample document). */
function VerifySample() {
  const { api, run } = useApp();
  const { doc, report, fixed, how } = useV();
  const rebuild = async (next: WizardPayload, label: string) => {
    useV.setState({ doc: next });
    await run(next.code, async () => {
      try {
        const r = await api.directBuild(composeMarkdown(next), next.code, { code: next.code, title_mk: next.mk_title, title_en: next.en_title, version: next.version, doctype: 'ANNEX', parent: next.parent, source: 'build · after ' + label, supersedes: '', minFont: String(minFont(next)) });
        useV.setState({ report: r.verify, fixed: true, how: label }); return { ok: true };
      } catch (e) {
        const er = e as ApiError, v = (er.body as { detail?: { verify?: string } })?.detail?.verify;
        useV.setState({ report: v || verifyReport(`/data/${next.code}.docx`, { paras: 22, tables: 3, words: 402, chars: 2894, minFont: minFont(next) }), fixed: false });
        return { ok: false, failAt: 2, msg: `RESULT: FAIL · ${er.status || 422}` };
      }
    });
  };
  const fail = !fixed;
  usePrimary(fail ? 'Re-verify ▸' : 'Build ▸', () => rebuild(doc, how || 'rebuild'));
  const vc = fail ? C.bad : C.ok;
  const lines = report.split('\n');
  const fontLine = lines.find(l => l.includes('min font')) || '';
  const checks: [string, boolean][] = [['Structure', true], ['Font floor', !/FAIL/.test(fontLine)], ['Render env', !/render environment FAIL/.test(report)], ['Glyph coverage', !/glyph coverage FAIL/.test(report)], ['Bilingual MK+EN', !/WARN/.test(report)], ['Fidelity §5A', !/FIDELITY.*FAIL/.test(report)]];
  const tableA = doc.sections[2].blocks.length > 1 ? 's2b1' : 's2b0';
  return <>
    <div style={{ width: 236, flex: 'none', borderRight: `1px solid ${T.hair}`, background: T.pane, padding: '14px 10px', display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
      <div style={{ padding: '0 6px 8px' }}><b style={{ color: '#fff' }}>Gate checks</b><div style={{ fontSize: 12, color: T.muted }}>{doc.code} · v{doc.version}</div></div>
      {checks.map(([label, ok]) => <div key={label} style={{ padding: '8px 10px', borderRadius: 6, display: 'grid', gridTemplateColumns: '16px 1fr auto', gap: 8, background: ok ? 'transparent' : 'rgba(224,122,111,.12)' }}>
        <span style={{ color: ok ? C.ok : C.bad, fontWeight: 700 }}>{ok ? G.ok : G.bad}</span><span>{label}</span><span style={{ color: ok ? C.ok : C.bad, fontFamily: MONO, fontSize: 11 }}>{ok ? 'OK' : 'FAIL'}</span></div>)}
      <div style={{ marginTop: 'auto', fontFamily: MONO, fontSize: 11.5, color: T.muted, lineHeight: 1.6 }}>Pass rate 24 h: 83 %<br />Top cause: font floor</div>
    </div>
    <div style={{ flex: 1, minWidth: 0, padding: '18px 22px', display: 'flex', flexDirection: 'column', gap: 14, overflow: 'auto' }}>
      {fail ? <div style={{ background: T.errSurface, border: `1px solid ${T.errBorder}`, borderRadius: 8, padding: '11px 14px', color: T.errText, lineHeight: 1.45 }}>Rejected and <b style={{ color: '#fff' }}>not saved</b> to the library. Nothing reaches a user unless the gate prints RESULT: PASS.</div>
        : <Banner kind="ok" style={{ borderRadius: 8, padding: '11px 14px', fontSize: 14 }}>Rebuilt {how === 'split' ? 'with table 3 split in two' : 'in landscape'}. Gate passed; v{doc.version} registered and the PDF renders on demand.</Banner>}
      <div style={{ background: T.deeper, border: `1px solid ${T.hair}`, borderRadius: 8, padding: '14px 16px', fontFamily: MONO, fontSize: 12.5, lineHeight: 1.75, color: T.secondary, overflow: 'auto' }}>
        <div style={{ whiteSpace: 'pre' }}>$ python3 pp_verify.py /data/{doc.code}.docx</div>
        {lines.map((l, i) => <div key={i} style={{ whiteSpace: 'pre', color: l.startsWith('RESULT') ? vc : /FAIL/.test(l) ? C.bad : lineColor(l), fontWeight: l.startsWith('RESULT') ? 700 : 400 }}>{l}{l.startsWith('RESULT') ? (fail ? '  → 422 · .partial.docx deleted, never published' : `  → registered v${doc.version}`) : ''}</div>)}
      </div>
      {fail && <div style={{ background: T.surface, border: `1px solid ${T.errBorder}`, borderRadius: 8, padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div style={{ fontFamily: MONO, fontSize: 12, color: C.bad }}>FONT FLOOR · table 3, header row, EN halves (w:sz=11) · 9 cells</div>
        <div style={{ lineHeight: 1.45 }}>The table has 9 columns, so the EN text shrank to 5.5 pt to fit. Split it into two tables, or switch the annex to landscape.</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Btn onClick={() => rebuild(split(doc), 'split')}>Split table &amp; rebuild</Btn>
          <Btn primary={false} onClick={() => rebuild({ ...doc, orient: 'landscape', version: '02' }, 'landscape')}>Landscape &amp; rebuild</Btn>
          <span style={{ alignSelf: 'center', fontSize: 12, color: T.muted }}>or ask gf_annex_author in the margin</span></div>
      </div>}
    </div>
    <div style={{ width: 400, flex: 'none', borderLeft: `1px solid ${T.hair}`, background: T.deep, display: 'flex', flexDirection: 'column' }}>
      <PaneHead title="Located on page" right={`page 1 · table ${doc.sections[2].blocks.length > 1 ? '3b' : '3'}`} />
      <div style={{ flex: 1, position: 'relative', padding: '16px 0 0 14px' }}>
        <div style={{ position: 'relative', width: 270 }}>
          <PPPage doc={doc} zoom={.34} highlights={[{ anchor: tableA, kind: fail ? 'bad' : 'ok' }]} />
          <div style={{ position: 'absolute', left: 26, top: 100, border: `4px solid ${vc}`, color: vc, background: 'rgba(15,26,38,.82)', fontFamily: DISPLAY, fontWeight: 700, fontSize: 24, letterSpacing: '.08em', padding: '6px 16px', transform: 'rotate(-9deg)', borderRadius: 5, textAlign: 'center', lineHeight: 1 }}>
            {fail ? 'REJECTED' : 'PASSED'}<div style={{ fontSize: 10, letterSpacing: '.18em', marginTop: 5 }}>{fail ? 'НЕ Е ОДОБРЕНО · GATE 422' : `ОДОБРЕНО · REGISTERED v${doc.version}`}</div></div>
          <div style={{ position: 'absolute', left: '100%', top: 155, display: 'flex', alignItems: 'center' }}><span style={{ width: 10, height: 1.5, background: vc }} />
            <div style={{ border: `1.5px solid ${vc}`, color: vc, borderRadius: 4, padding: '4px 6px', width: 100, transform: 'rotate(-1.5deg)' }}><div style={{ fontFamily: DISPLAY, fontWeight: 700, fontSize: 9.5, letterSpacing: '.05em' }}>FONT FLOOR</div><div style={{ fontSize: 11, lineHeight: 1.25 }}>{fail ? '5.5 pt EN halves, 9 columns' : '6.5 pt after ' + how}</div></div></div>
        </div>
      </div>
    </div>
  </>;
}
