import type { Doctype, WizardPayload } from '../api/types';
import { SOP_SEC } from '../data/samples';

// House form of QALI 001 (Head of QC, 18.10.2026). An SOP is DEPTSOPnnn; an annex is its SOP's code + Ann, or a
// controlled form of its own family (QCT, QCLB, QCPL, QCSP, QCSPW, QCCoA). Reports take any house code.
export const CODE_PATTERN = {
  SOP: /^[A-Z]{2}SOP\d{3}$/,
  REPORT: /^(?:[A-Z]{2,8}|[A-Z]{2}CoA)\d{3}(?:A\d{2})?$/,
  ANNEX: /^(?:[A-Z]{2}SOP\d{3}A\d{2}|[A-Z]{2}(?:T|LB|PL|SPW?|CoA|LI)\d{3})$/,
};
/** The family a new document of this doctype is numbered in when it has no parent SOP. */
export const DEFAULT_FAMILY: Record<string, string> = { SOP: 'QCSOP', LOG: 'QCLB', FORM: 'QCT', CHECKLIST: 'QCT' };
export const codePattern = (dt: Doctype) => dt === 'SOP' ? CODE_PATTERN.SOP : dt === 'REPORT' ? CODE_PATTERN.REPORT : CODE_PATTERN.ANNEX;

/** Empty skeleton for a new draft: the 9 mandatory SOP sections, or one form block + sign-off for an annex. */
export function skeleton(m: { doctype: Doctype; code: string; title_mk: string; title_en: string; version: string; parent: string; supersedes: string; orient: 'portrait' | 'landscape' }): WizardPayload {
  const base = {
    doctype: (m.doctype === 'REPORT' ? 'ANNEX' : m.doctype) as Doctype, code: m.code.trim(), mk_title: m.title_mk, en_title: m.title_en,
    version: m.version || '01', parent: m.parent, supersedes: m.supersedes, orient: m.orient,
    status: 'draft' as const, effective_date: '', review_date: '',
  };
  if (m.doctype === 'SOP') return { ...base, sections: SOP_SEC.map(([num, mk, en]) => ({ num, mk, en, level: 2 as const, blocks: [{ type: 'text' as const, paras: [{ mk: '', en: '' }] }] })) };
  return { ...base, sections: [
    { num: '1', mk: 'Содржина', en: 'Content', level: 1, blocks: [{ type: 'form', rows: [{ label_mk: '', label_en: '', value: '' }] }] },
    { num: '2', mk: 'Одобрување', en: 'Approval', level: 1, blocks: [{ type: 'table', cols: [{ mk: 'Име и презиме', en: 'Name' }, { mk: 'Датум', en: 'Date' }, { mk: 'Потпис', en: 'Signature' }], rows: [[{ mk: '', en: '' }, { mk: '', en: '' }, { mk: '', en: '' }]] }] },
  ] };
}
