import { describe, expect, it } from 'vitest';
import { CODE_RE, guessMeta, metaProblems, rankVersions } from './registry';

describe('registry rules', () => {
  it('accepts house codes and refuses file names', () => {
    for (const c of ['WHSOP_003', 'QCSOP_025_A01', 'QCLB_021', 'PP-QC-SOP-025', 'QASOP_0XX', 'T-1']) expect(CODE_RE.test(c)).toBe(true);
    for (const c of ['labels_raw (final) v3', 'WHSOP 003', 'whsop_003', 'pasted', '']) expect(CODE_RE.test(c)).toBe(false);
  });
  it('takes the code from the header, else from the text, never the file name', () => {
    expect(guessMeta({ code: 'WHSOP_003_A04', mk_title: 'Манифест', en_title: 'Manifest' }, '').code).toBe('WHSOP_003_A04');
    expect(guessMeta({}, 'Код на документот: QCSOP_025_A01 · Верзија 01').code).toBe('QCSOP_025_A01');
    expect(guessMeta({ code: 'labels_raw (final) v3' }, 'no code here').code).toBe('');
  });
  it('names what is missing', () => {
    expect(metaProblems({ code: 'x', title_mk: '', title_en: 'T', version: '01' })).toHaveLength(2);
    expect(metaProblems({ code: 'WHSOP_003', title_mk: 'Т', title_en: 'T', version: '01' })).toEqual([]);
  });
  it('never ranks a format-only copy above a controlled version', () => {
    const rows = [
      { id: 'copy', job_id: null, version: '1.0', created_at: '2026-10-14T09:00:00Z' },
      { id: 'v01', job_id: 'j1', version: '01', created_at: '2026-10-10T09:00:00Z' },
    ];
    expect(rankVersions(rows).map(r => r.id)).toEqual(['v01', 'copy']);
  });
});
