import { describe, expect, it } from 'vitest';
import { similarTitles, words } from './related';
import type { RelatedDoc } from '../api/types';

const rel = (code: string, title_en: string, title_mk = ''): RelatedDoc => ({ code, version: '01', title_en, title_mk, relation: 'listed', chars: 100 });

describe('parent SOP: a brief that reads like a document already in use (19.10.2026)', () => {
  it('drops stop words, short words and the generic document nouns', () => {
    expect([...words('Record of the sampling of raw materials')].sort()).toEqual(['materials', 'raw', 'sampling']);
  });
  it('flags a title sharing 3+ significant words, in EN or MK, and nothing less', () => {
    const related = [rel('QCT002', 'Sampling record for raw materials', 'Запис за земање мостри од суровини'), rel('QCT003', 'Sample label'), rel('QCLB001', 'Sample reception logbook')];
    expect(similarTitles('Raw materials sampling form', '', related).map(r => r.code)).toEqual(['QCT002']);
    expect(similarTitles('', 'Образец за земање мостри од суровини', related).map(r => r.code)).toEqual(['QCT002']);
    expect(similarTitles('Sample label', '', related)).toEqual([]);
    expect(similarTitles('', '', related)).toEqual([]);
  });
});
