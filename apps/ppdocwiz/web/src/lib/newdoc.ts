import type { Doctype, WizardPayload } from '../api/types';
import { SOP_SEC } from '../data/samples';

export const CODE_PATTERN = {
  SOP: /^(WH|QC|QA|PR|CU|EN|HR)SOP_\d{3}$/,
  REPORT: /^[A-Z]{2}SOP_\d{3}(_A\d{2})?$/,
  ANNEX: /^(WH|QC|QA|PR|CU|EN|HR)SOP_\d{3}_A\d{2}$/,
};
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
