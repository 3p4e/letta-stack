import { describe, expect, it } from 'vitest';
import { byFamily, family, filterLoose, filterPackages, openByDefault } from './packages';
import type { LibraryPackage, ShelfEntry } from '../api/types';

const e = (code: string, title_en: string, title_mk = ''): ShelfEntry => ({ code, parent: '', department: 'QC', title_mk, title_en, status: 'effective', version: '01', effective_date: '', shelf: 'approved', approved: null, wip: [], builds: [], jobs: [], notes: [] });
const pk: LibraryPackage[] = [
  { sop: e('QCSOP001', 'Sampling'), members: [{ ...e('QCT002', 'Sampling record'), relation: 'listed' }, { ...e('QCT003', 'Sample label'), relation: 'listed' }] },
  { sop: e('QCSOP022', 'Chemicals'), members: [] },
];

describe('Library packages (19.10.2026)', () => {
  it('reads the family prefix off a code and groups loose entries by it', () => {
    expect([family('QCSOP001'), family('QCT002'), family('QASOPXXX'), family('qc-t 7'), family('QASOPXXXA01')]).toEqual(['QCSOP', 'QCT', 'QASOP', 'QCT', 'QASOP']);
    expect(byFamily([e('QCT024', 'x'), e('QASOPXXX', 'y'), e('QCT001', 'z')]).map(([f, es]) => [f, es.map(x => x.code)])).toEqual([['QASOP', ['QASOPXXX']], ['QCT', ['QCT024', 'QCT001']]]);
  });
  it('filters by code or title across SOPs and members, and names the packages to expand', () => {
    expect(filterPackages(pk, '')).toEqual({ kept: pk, opened: [] });
    expect(filterPackages(pk, 'chem').kept.map(p => p.sop.code)).toEqual(['QCSOP022']);
    const r = filterPackages(pk, 'label');
    expect(r.kept.map(p => [p.sop.code, p.members.map(m => m.code)])).toEqual([['QCSOP001', ['QCT003']]]);
    expect(r.opened).toEqual(['QCSOP001']);
    expect(filterPackages(pk, 'qcsop001').kept[0].members).toHaveLength(2);
    expect(filterLoose([e('QCSOP020', 'Trend analysis')], 'trend')).toHaveLength(1);
    expect(filterLoose([e('QCSOP020', 'Trend analysis')], 'nope')).toHaveLength(0);
  });
  it('opens small groups by default', () => { expect(openByDefault(8)).toBe(true); expect(openByDefault(9)).toBe(false); });
});
