// Verbatim copy of apps/wwf-docengine/app/questionnaires.py QUESTIONNAIRES, for the mock adapter.
import type { RawQuestionnaire } from '../api/normalize';

const d = (v: string) => ({ v, default: true });

export const RAW_QUESTIONNAIRES: Record<string, RawQuestionnaire> = {
  sop_qc: {
    title: { en: 'QC SOP questionnaire', mk: 'Прашалник за СОП — Контрола на квалитет' }, doctype: 'SOP',
    rounds: [
      { key: 'r1_scope', title: { en: 'R1 — Scope', mk: 'Р1 — Опсег' }, questions: [
        { key: 'focus', multi: false, label: { en: 'Primary testing focus', mk: 'Примарен фокус на тестирање' }, options: ['Identity (Annex 8 §2 — ALL containers)', 'Potency', 'Purity', 'Contaminants', 'Microbiology', 'Water', 'Sample management'] },
        { key: 'sample_types', multi: true, label: { en: 'Sample types', mk: 'Типови мостри' }, options: ['Raw material', 'In-process', 'Bulk', 'Finished product', 'Water', 'Environmental', 'Stability'] },
        { key: 'purpose', multi: false, label: { en: 'Batch-release vs monitoring', mk: 'Пуштање на серија или мониторинг' }, options: [d('Internal QC / IPQC / trending (release stays with accredited lab)'), 'Monitoring only'] },
        { key: 'method_source', multi: false, label: { en: 'Method source', mk: 'Извор на метод' }, options: [d('Ph. Eur. (preferred)'), 'USP', 'In-house', 'ISO', 'Contract lab'] },
      ] },
      { key: 'r2_technical', title: { en: 'R2 — Technical', mk: 'Р2 — Технички' }, questions: [
        { key: 'techniques', multi: true, label: { en: 'Techniques', mk: 'Техники' }, options: ['HPLC-DAD', 'GC-MS', 'ICP-MS', 'LC-MS/MS', 'Microscopy', 'LOD', 'Karl Fischer', 'Microbiological'] },
        { key: 'acceptance', multi: true, label: { en: 'Acceptance criteria', mk: 'Критериуми за прифатливост' }, options: ['Cannabinoid ±10 % (Ph. Eur. 3028)', 'LOD NMT 12 %', 'Foreign matter NMT 2 %', 'Heavy metals', 'Pesticides (Ph. Eur. 2.8.13)', 'Mycotoxins', 'Microbial limits'] },
        { key: 'reference_standards', multi: true, label: { en: 'Reference standards', mk: 'Референтни стандарди' }, options: ['CRS', 'Secondary standard', 'SST', 'Internal'] },
      ] },
      { key: 'r3_responsibilities', title: { en: 'R3 — Responsibilities', mk: 'Р3 — Одговорности' }, questions: [
        { key: 'performer', multi: false, label: { en: 'Primary performer', mk: 'Примарен извршител' }, options: [d('QC Analyst'), 'QC Department Manager', 'External lab'] },
        { key: 'review_chain', multi: false, label: { en: 'Review chain', mk: 'Синџир на преглед' }, options: ['Single', d('Two-tier (Analyst + QC Manager)'), 'Three-tier + QP', 'Cross-functional'] },
      ] },
      { key: 'r4_records', title: { en: 'R4 — Records', mk: 'Р4 — Записи' }, questions: [
        { key: 'records', multi: true, label: { en: 'Records generated', mk: 'Генерирани записи' }, options: ['Worksheets (EU GMP 6.17)', 'Instrument printouts', 'Sample-prep records', 'SST records', 'CoA', 'OOS records'] },
        { key: 'retention', multi: false, label: { en: 'Retention', mk: 'Чување' }, options: [d('Batch docs: 1 y after expiry / min 5 y (EU GMP 4.11)'), 'Other (state in §7)'] },
      ] },
    ],
  },
  sop_transport: {
    title: { en: 'Transport SOP questionnaire', mk: 'Прашалник за СОП — Транспорт' }, doctype: 'SOP',
    rounds: [
      { key: 'r1_scope', title: { en: 'R1 — Scope', mk: 'Р1 — Опсег' }, questions: [
        { key: 'movements', multi: true, label: { en: 'Movements covered', mk: 'Опфатени движења' }, options: [d('Intermediate (bulk in bags) and finished product to licensed domestic consignees'), d('Propagation material (clones, seeds) between sites'), d('Final leg after customs clearance to the site'), d('Cannabis waste to an authorised destruction site')] },
        { key: 'carrier', multi: false, label: { en: 'Who transports', mk: 'Кој превезува' }, options: [d('Contracted, qualified and licensed carrier under a Quality Agreement')] },
        { key: 'records_system', multi: false, label: { en: 'Record system', mk: 'Систем на записи' }, options: [d('Paper-based'), 'Electronic tracking system (after change control, §2.3)'] },
      ] },
      { key: 'r2_security', title: { en: 'R2 — Security and authorities', mk: 'Р2 — Безбедност и органи' }, questions: [
        { key: 'authorities', multi: true, label: { en: 'Authority steps', mk: 'Чекори кон органите' }, options: [d('Police escort requested from the MoIA at least 24 h before dispatch (Law on Control of Narcotic Drugs, Off. Gazette 37/16)'), d('Written MoIA confirmation mandatory before dispatch'), d('Post-transport notification to the Ministry of Health')] },
        { key: 'lane', multi: false, label: { en: 'Lane status before dispatch', mk: 'Статус на рутата пред отпрема' }, options: [d('Lane QUALIFIED per QASOP_0XX, same vehicle and pallet configuration')] },
        { key: 'references', multi: true, label: { en: 'GMP / GDP references', mk: 'GMP / GDP референци' }, options: [d('EU GDP 2013/C 343/01 Ch. 7 and Ch. 9'), d('EudraLex Vol. 4 Part I Ch. 4, Ch. 5 §5.10, Ch. 7'), d('WHO TRS 961 Annex 9'), d('ICH Q9(R1)')] },
      ] },
      { key: 'r3_conditions', title: { en: 'R3 — Packaging and conditions', mk: 'Р3 — Пакување и услови' }, questions: [
        { key: 'packaging', multi: true, label: { en: 'Packaging', mk: 'Пакување' }, options: [d('10 bags/carton; pallet L 8 or S 4 cartons; stretch film and thermal blanket'), d('Qualified cool box (propagation material)'), d('Airtight container'), d('Sealed sacks with a record (waste)')] },
        { key: 'conditions', multi: true, label: { en: 'Conditions and monitoring', mk: 'Услови и следење' }, options: [d('15–25 °C, RH ≤ 60 %, protect from moisture'), d('Data loggers placed per the QA-approved plan')] },
      ] },
      { key: 'r4_records', title: { en: 'R4 — Responsibilities and records', mk: 'Р4 — Одговорности и записи' }, questions: [
        { key: 'roles', multi: true, label: { en: 'Roles in the RACI', mk: 'Улоги во RACI' }, options: [d('QC'), d('QA'), d('Security'), d('Logistics'), d('Carrier (driver)'), d('Consignee'), d('QP')] },
        { key: 'records', multi: true, label: { en: 'Records (annexes)', mk: 'Записи (анекси)' }, options: [d('Transport Risk Assessment (TRA)'), d('Request for police escort and notification to the MoIA'), d('Pallet and carton labels and packing lists'), d('Transport manifest and chain of custody'), d('Pre-dispatch and receipt checklist'), d('Post-transport notification to the Ministry of Health'), d('Transport file review and disposition')] },
        { key: 'retention', multi: false, label: { en: 'Retention', mk: 'Чување' }, options: [d('At least 5 y or 1 y after batch expiry, whichever is longer (EU GMP 4.11)')] },
      ] },
    ],
  },
  annex_form: {
    title: { en: 'Annex / Form questionnaire', mk: 'Прашалник за анекс / образец' }, doctype: 'FORM',
    rounds: [
      { key: 'r1_purpose', title: { en: 'R1 — Purpose', mk: 'Р1 — Намена' }, questions: [
        { key: 'purpose', multi: false, label: { en: 'Form purpose', mk: 'Намена на образецот' }, options: ['Request', 'Recording', 'Verification', 'Approval'] },
        { key: 'initiator', multi: false, label: { en: 'Who initiates', mk: 'Кој иницира' }, options: ['Operator', 'Analyst', 'Department manager', 'QA', 'QP'] },
      ] },
      { key: 'r2_content', title: { en: 'R2 — Content', mk: 'Р2 — Содржина' }, questions: [
        { key: 'id_fields', multi: true, label: { en: 'Identification fields', mk: 'Полиња за идентификација' }, options: [d('Doc ID (EU GMP 4.2)'), d('Version (4.3)'), d('Date (4.8)'), 'Batch'] },
        { key: 'main_content', multi: true, label: { en: 'Main content', mk: 'Главна содржина' }, options: ['Item list', 'Quantities', 'Description', 'Priority', 'Sign-off rows'] },
      ] },
    ],
  },
};
