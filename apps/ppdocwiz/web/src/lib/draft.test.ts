import { describe, expect, it } from 'vitest';
import { bilingual, columnChanges, headField, joinDraft, lineDiff, sectionTitle, splitDraft } from './draft';

const MD = '<!--HEADERDATA\nmk_title: Барање\nen_title: Request\ncode: QCT002\nversion: 03\ndoctype: FORM\n-->\n'
  + '# 1. ЦЕЛ | PURPOSE\nЦел. ||| Purpose.\n\n# 2. ПОДАТОЦИ | DATA\nПодатоци. ||| Data.\n## 2.1 Под | Sub\nа ||| b\n';

describe('draft', () => {
  it('splits at level-1 headings only and joins back to the same text', () => {
    const d = splitDraft(MD);
    expect(d.sections.map(sectionTitle)).toEqual(['1. ЦЕЛ | PURPOSE', '2. ПОДАТОЦИ | DATA']);
    expect(joinDraft(d.head, d.sections)).toBe(MD);
    expect(headField(d.head, 'code')).toBe('QCT002');
    expect(headField(d.head, 'version')).toBe('03');
  });
  it('splits a form at its level-2 sections, the title first', () => {
    const form = '<!--HEADERDATA\ncode: QCT002\ndoctype: FORM\n-->\n# БАРАЊЕ | REQUEST\nУвод. ||| Intro.\n\n## 1. Мостра | Sample\nа ||| b\n\n## 2. Анализа | Analysis\nв ||| c\n';
    const d = splitDraft(form);
    expect(d.sections.map(sectionTitle)).toEqual(['БАРАЊЕ | REQUEST', '1. Мостра | Sample', '2. Анализа | Analysis']);
    expect(joinDraft(d.head, d.sections)).toBe(form);
  });
  it('reads a bilingual line', () => {
    expect(bilingual('Цел. ||| Purpose.')).toEqual(['Цел.', 'Purpose.']);
    expect(bilingual('[[FORM:grid]]')).toBeNull();
  });
  it('diffs lines', () => {
    expect(lineDiff('a\nb\nc', 'a\nx\nc')).toEqual([['=', 'a'], ['-', 'b'], ['+', 'x'], ['=', 'c']]);
  });
});

describe('columnChanges', () => {
  it('names the columns a revision added and keeps the rest out', () => {
    const a = 'A~~a ||| B~~b ||| C~~c\n|||||||||', b = 'A~~a ||| B~~b ||| L~~logger ||| C~~c\n||||||||||||';
    expect(columnChanges(lineDiff(a, b))).toEqual({ added: ['L~~logger'], removed: [] });
  });
});
