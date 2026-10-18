import { describe, expect, it } from 'vitest';
import { CODE_RE, guessMeta, metaProblems, normalizeCode, rankVersions } from './registry';
import { CODE_PATTERN } from './newdoc';

describe('registry rules', () => {
  it('accepts the house form of QALI 001 and refuses everything else', () => {
    for (const c of ['QCSOP011', 'QCSOP011A01', 'QCT017', 'QCLB021', 'QCSPW005', 'QCCoA001', 'WHSOP003A04', 'SSP001']) expect(CODE_RE.test(c)).toBe(true);
    for (const c of ['WHSOP_003', 'QCSOP 011', 'labels_raw (final) v3', 'QASOP_0XX', 'T-1', 'pasted', '']) expect(CODE_RE.test(c)).toBe(false);
  });
  it('normalises the forms in circulation, Cyrillic look-alikes included', () => {
    const cases: [string, string][] = [['QCSOP 011', 'QCSOP011'], ['QCSOP_025_A01', 'QCSOP025A01'], ['WHSOP_003', 'WHSOP003'],
      ['QCSOP011А01', 'QCSOP011A01'], ['qclb 21', 'QCLB021'], ['QCCOA 001', 'QCCoA001'], ['SSP-001', 'SSP001']];
    for (const [raw, house] of cases) expect(normalizeCode(raw)).toBe(house);
    for (const raw of ['labels_raw (final) v3', 'QASOP_0XX', 'T-1', '']) expect(normalizeCode(raw)).toBe('');
  });
  it('knows what each doctype may be called', () => {
    expect(CODE_PATTERN.SOP.test('QCSOP025')).toBe(true);
    expect(CODE_PATTERN.SOP.test('QCSOP011A01')).toBe(false);
    for (const c of ['QCSOP011A02', 'QCT017', 'QCLB021', 'QCCoA002']) expect(CODE_PATTERN.ANNEX.test(c)).toBe(true);
    expect(CODE_PATTERN.ANNEX.test('QCSOP025')).toBe(false);
  });
  it('takes the code from the header, else from the text, never the file name', () => {
    expect(guessMeta({ code: 'WHSOP_003_A04', mk_title: 'Манифест', en_title: 'Manifest' }, '').code).toBe('WHSOP003A04');
    expect(guessMeta({}, 'Код на документот: QCSOP 011 · Верзија 01').code).toBe('QCSOP011');
    expect(guessMeta({}, 'Документ бр. QCSOP011А01').code).toBe('QCSOP011A01');
    expect(guessMeta({ code: 'labels_raw (final) v3' }, 'no code here').code).toBe('');
  });
  it('names what is missing', () => {
    expect(metaProblems({ code: 'x', title_mk: '', title_en: 'T', version: '01' })).toHaveLength(2);
    expect(metaProblems({ code: 'WHSOP003', title_mk: 'Т', title_en: 'T', version: '01' })).toEqual([]);
  });
  it('never ranks a format-only copy above a controlled version', () => {
    const rows = [
      { id: 'copy', job_id: null, version: '1.0', created_at: '2026-10-14T09:00:00Z' },
      { id: 'v01', job_id: 'j1', version: '01', created_at: '2026-10-10T09:00:00Z' },
    ];
    expect(rankVersions(rows).map(r => r.id)).toEqual(['v01', 'copy']);
  });
});
