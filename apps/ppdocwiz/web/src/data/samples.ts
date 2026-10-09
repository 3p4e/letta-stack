// Sample data for the mock adapter and the demo states. Content mirrors the
// Hybrid v2 prototype, which was itself drawn from the letta-stack repo
// (fleet.yaml, questionnaires.py, pipeline.py). Nothing here reaches a document.
import type { WizardPayload } from '../api/types';

export const SOP_SEC: [string, string, string][] = [
  ['1.0', 'ЦЕЛ', 'PURPOSE'], ['2.0', 'ПОДРАЧЈЕ НА ПРИМЕНА', 'SCOPE'], ['3.0', 'ОДГОВОРНОСТИ', 'RESPONSIBILITIES'],
  ['4.0', 'РЕФЕРЕНТНИ ДОКУМЕНТИ', 'REFERENCE DOCUMENTS'], ['5.0', 'ДЕФИНИЦИИ', 'DEFINITIONS'], ['6.0', 'ПОСТАПКА', 'PROCEDURE'],
  ['7.0', 'ЗАПИСИ', 'RECORDS'], ['8.0', 'ПОВРЗАНИ ДОКУМЕНТИ', 'RELATED DOCUMENTS'], ['9.0', 'РЕВИЗИЈА', 'REVISION'],
];
export const ANX_SEC: [string, string, string][] = [['1.0', 'СОДРЖИНА', 'CONTENT']];

/** wizard.EXAMPLE, with the EN half of table 2 row 2 left empty so the lint and suggestion have work to do. */
export const SAMPLE_ANNEX: WizardPayload = {
  doctype: 'ANNEX',
  mk_title: 'Записник за ослободување — пропагационен материјал (клонови)',
  en_title: 'Release Record — Propagation Material (Clones)',
  code: 'WHSOP_002_A02', version: '01', parent: 'WHSOP 002', supersedes: '', orient: 'portrait',
  status: 'draft', effective_date: '', review_date: '',
  sections: [
    { num: '1', mk: 'Пратка', en: 'Consignment', level: 1, blocks: [{ type: 'form', rows: [
      { label_mk: 'MRN на царинска декларација', label_en: 'Customs declaration MRN', value: '' },
      { label_mk: 'Датум/време на пристигнување', label_en: 'Arrival date/time', value: '' },
      { label_mk: 'Температура при пристигнување', label_en: 'Arrival temperature', value: '' },
    ] }] },
    { num: '2', mk: 'Фитосанитарно и ослободување', en: 'Phytosanitary & release', level: 1, blocks: [{ type: 'table',
      cols: [{ mk: '№', en: '' }, { mk: 'Проверка', en: 'Check' }, { mk: 'Реф.', en: 'Ref.' }, { mk: 'Статус', en: 'Status' }],
      rows: [
        [{ mk: '1', en: '' }, { mk: 'Фитосанитарна инспекција', en: 'Phytosanitary inspection' }, { mk: '', en: '' }, { mk: '', en: '' }],
        [{ mk: '2', en: '' }, { mk: 'SPL земање мостра', en: '' }, { mk: '', en: '' }, { mk: '', en: '' }],
        [{ mk: '3', en: '' }, { mk: 'Сертификат за сообразност (CoC)', en: 'Certificate of Conformity (CoC)' }, { mk: '', en: '' }, { mk: '', en: '' }],
      ] }] },
    { num: '3', mk: 'Одобрување', en: 'Approval', level: 1, blocks: [{ type: 'table',
      cols: [{ mk: 'Име и презиме', en: 'Name' }, { mk: 'Датум', en: 'Date' }, { mk: 'Потпис', en: 'Signature' }],
      rows: [[{ mk: '', en: '' }, { mk: '', en: '' }, { mk: '', en: '' }]] }] },
  ],
};

export const SAMPLE_SOP: WizardPayload = {
  doctype: 'SOP', mk_title: 'Земање мостри за LOD', en_title: 'Sampling for loss on drying',
  code: 'QCSOP_031', version: '01', parent: '', supersedes: '', orient: 'portrait',
  status: 'draft', effective_date: '', review_date: '',
  sections: [
    { num: '1.0', mk: 'ЦЕЛ', en: 'PURPOSE', level: 2, blocks: [{ type: 'text', paras: [{ mk: 'Оваа постапка ги дефинира барањата за земање мостри од суви цветови од канабис за тестирање на содржина на влага (LOD) во согласност со Ph. Eur. 2.2.32.', en: 'This procedure defines the requirements for sampling dried cannabis flowers for loss-on-drying (LOD) testing in accordance with Ph. Eur. 2.2.32.' }] }] },
    { num: '2.0', mk: 'ПОДРАЧЈЕ НА ПРИМЕНА', en: 'SCOPE', level: 2, blocks: [{ type: 'text', paras: [{ mk: 'Се применува на сите серии во карантин пред пуштање од страна на QP.', en: 'Applies to all batches in quarantine prior to QP release.' }] }] },
    { num: '3.0', mk: 'ОДГОВОРНОСТИ', en: 'RESPONSIBILITIES', level: 2, blocks: [{ type: 'table',
      cols: [{ mk: 'Улога', en: 'Role' }, { mk: 'Одговорност', en: 'Responsibility' }],
      rows: [[{ mk: 'QC Analyst', en: '' }, { mk: 'Земање и подготовка на мостри', en: 'Sampling and sample prep' }], [{ mk: 'QC Manager', en: '' }, { mk: 'Преглед и одобрување', en: 'Review and approval' }]] }] },
    { num: '4.0', mk: 'РЕФЕРЕНТНИ ДОКУМЕНТИ', en: 'REFERENCE DOCUMENTS', level: 2, blocks: [{ type: 'text', paras: [{ mk: 'EU GMP Поглавје 6; Ph. Eur. 3028; EU GMP Анекс 8.', en: 'EU GMP Chapter 6; Ph. Eur. 3028; EU GMP Annex 8.' }] }] },
  ],
};

export const SAMPLE_PEST: WizardPayload = {
  ...SAMPLE_ANNEX, code: 'WHSOP_009_A01', mk_title: 'Контролна листа за извидување на штетници', en_title: 'Pest scouting checklist', parent: 'WHSOP 009', version: '02',
};

/** Tiny terminology memory for the mock "suggest EN half" agent (DB3_PP_CURRENT_unified in production). */
export const TERMS: Record<string, string> = {
  'SPL земање мостра': 'SPL sampling', 'Пратка': 'Consignment', 'Одобрување': 'Approval', 'Датум': 'Date', 'Потпис': 'Signature',
  'Име и презиме': 'Name', 'Проверка': 'Check', 'Статус': 'Status', 'Содржина': 'Content', 'Забелешка': 'Note',
};

export const AGENTS = [
  { n: 'gf_doc_orchestrator', d: 'Routes document requests (TYPE+MODE per SKILL §0) and sequences the pipeline.', p: 'Resolve the master router FIRST: TYPE (SOP | Annex/Form/Checklist/Log | Report/Record) and MODE (A develop content, B format, C restyle). Never guess TYPE — ask. Then hand off per pipeline stage. You never write final content yourself.', src: [] as string[], runs: 4 as number | string, legacy: false },
  { n: 'gf_sop_author', d: 'Drafts SOP sections (9-section structure) as bilingual Markdown.', p: "Write SOP section content in bilingual Macedonian|English Markdown (MK first, '|' separated headings, '|||' table cells). Produce ONLY the requested section, complete and GMP-correct. Procedure content goes in 6.x subsections. Leave unknown facility specifics as blank fields, never invent.", src: ['DB3_PP_CURRENT_unified'], runs: 38, legacy: false },
  { n: 'gf_annex_author', d: 'Drafts annex/form/log/checklist content with [[FORM]]/[[TABLE]] blocks.', p: 'Design annex/form/log/checklist content as bilingual Markdown. Use [[FORM:grid]] for packed label|value metadata (short fields pack, long values span, write-ins stay blank), [[TABLE]] with a header row for data grids. Structure from any sample, style NEVER (§6D D6).', src: ['DB3_PP_CURRENT_unified'], runs: 22, legacy: false },
  { n: 'gf_translator_mk_en', d: 'Ensures MK⇄EN parity of drafted content.', p: 'Macedonian is primary. Keep terminology consistent with the facility QMS; do not translate abbreviations; use decimal commas in Macedonian numbers. Return corrected bilingual Markdown only.', src: [], runs: 31, legacy: false },
  { n: 'gf_reg_checker', d: 'Verifies drafted sections against the regulatory corpus; cites real passages.', p: 'For each drafted section, search attached sources (EU GMP, Ph. Eur., ICH, MALMED, facility QMS) and return {section, verdict OK|GAP|CONFLICT, citation, note}. Only cite passages you actually retrieved. If nothing applies say NO-FINDING — never invent a clause.', src: ['DB1_REGULATORY', 'DB3_PP_CURRENT_unified'], runs: 'clones', legacy: false },
  { n: 'gf_raci_specialist', d: 'Builds §3 responsibilities / RACI content.', p: 'Produce §3 ОДГОВОРНОСТИ/RESPONSIBILITIES — role-by-role bilingual tables (RACI where asked). Roles come from the questionnaire answers and facility role model; personnel NAMES are never hardcoded.', src: ['DB3_PP_CURRENT_unified'], runs: 5, legacy: false },
  { n: 'gf_qa_auditor', d: 'Runs the §6A post-generation review on assembled Markdown before formatting.', p: 'Check the assembled Markdown against the house rules: 9-section completeness (SOP), bilingual parity, §6D layout intent, no invented data, no invented citations. Return {verdict PASS|FIX, issues: [...]} with concrete fixes.', src: [], runs: 9, legacy: false },
  { n: 'gf_app_assistant', d: 'General GrowFlow in-app assistant (non-document AI features).', p: 'Bilingual MK/EN, concise, practical. Helps with task drafting, summaries and app questions. Has no authority over controlled documents.', src: ['DB3_PP_CURRENT_unified', 'GrowFlow_Weekly_Snapshots'], runs: 57, legacy: false },
  { n: 'qms_docx_formatter', legacy: true, d: 'Pre-existing formatter agent. Chat default (first in the LETTA_AGENT allowlist).', p: 'Holds build_pp_document / fetch_pp_document tools and the pp_house_rules block. Created outside the fleet; ensure_fleet skips it by name.', src: ['DB3_PP_CURRENT_unified'], runs: 14 },
  { n: 'pharma_docx_formatter', legacy: true, d: 'Pre-existing formatter agent with the in-process build tool attached.', p: 'Mode A in-process tool (python-docx in the Letta sandbox). Kept for compatibility; Mode B via the QMS service is preferred.', src: [], runs: 2 },
  { n: 'qms_pipeline_orchestrator', legacy: true, d: 'Legacy pipeline orchestrator from qms-creator-framework.', p: 'Calls the formatter agents as a step. Its per-worker in-memory job state is the bug class DocEngine replaced with Postgres.', src: [], runs: 0 },
];

export const HOUSE_RULES = [
  'Bilingual Macedonian-first (MK | EN inline); decimal commas in MK; abbreviations untranslated.',
  "One house navy #2B547E; Calibri; font floor 6 pt; shading always 'clear'.",
  'SOP = mandatory 9 sections, two-column; Annex/Form = inline full-page, navy banners, packed label|value metadata (§6D).',
  'NEVER fabricate pharmaceutical data: unknown values stay blank. Never invent regulation citations — cite only retrieved passages.',
  "Formatter input = bilingual Markdown: '#' headings 'MK|EN', [[TABLE]]/[[FORM]]/[[FORM:grid]], '|||' columns, '~~' inside a cell, <!--HEADERDATA--> front block.",
  'SOP revisions are REGENERATED whole (never patched); from samples take structure, not style.',
];

// Per-section sample telemetry for the Jobs inspector (generate chars, Cyrillic/Latin counts, reg-check findings).
export const CH = [612, 488, 1240, 702, 934, 3208, 816, 92, 344], CH_A = [2114];
export const CY: [number, number][] = [[318, 201], [256, 170], [640, 402], [388, 261], [512, 330], [1720, 1104], [430, 288], [52, 40], [180, 121]], CY_A: [number, number][] = [[1180, 742]];
export const FIND: [string, string, string][] = [['OK', 'EU GMP Part I, Ch. 6 §6.1', ''], ['NO-FINDING', '—', ''], ['OK', 'EU GMP Part I, Ch. 2 §2.1', 'roles only, no names'], ['OK', 'Ph. Eur. 3028 Cannabis flos', ''], ['NO-FINDING', '—', ''], ['GAP', 'Ph. Eur. 2.2.32', 'drying temperature/time not in the brief; left blank for QC'], ['OK', 'EU GMP Part I, Ch. 4 §4.11', 'retention matches R4 answer'], ['NO-FINDING', '—', ''], ['OK', 'EU GMP Part I, Ch. 4 §4.3', '']];
export const FIND_A: [string, string, string][] = [['OK', 'EU GMP Part I, Ch. 4 §4.8', 'date fields present']];
export const QA_FIX = ['FIX', 'issues:', '1. Metadata block uses [[TABLE]]; §6D wants [[FORM:grid]] for packed label|value metadata.', '2. Sign-off is missing the "Одобрил QP | Approved QP" row.', '3. "2–8 °C" is pre-filled in a write-in cell. Write-ins stay blank for a human.'];
export const QA_PASS = ['PASS', '9/9 sections present · bilingual parity OK · every table has a header row', 'no invented data · every citation traced to a retrieved passage'];

export const LOG_LINES = ['06:44:02 docengine POST /build 200 1.84s', '06:44:02 verify    WHSOP_002_A02 PASS', '06:43:58 letta     qms_docx_formatter tool_call', '06:39:40 docengine POST /build 422 verify FAILED', '06:12:31 pipeline  job 7b21d0aa bilingual gap 5.0', '05:51:09 pipeline  job c04e88f3 §6A audit FIX', '05:50:12 fleet     delete gf_reg_checker_tmp_c04e88f3_10', '04:58:00 docengine reaped 1 stale job(s)', '04:58:00 docengine startup · db ok · letta ok', '04:02:17 pipeline  job 19d5e7b0 regulatory-check 6.0'];

// pp_report.execution_signoff() defaults — the engine hard-codes these; the UI makes them editable (COVERAGE #9).
export const SIGNOFF_DEFAULTS = { mk_exec: 'Извршил (КК) | Executed (QC)', reviewer: 'J. Romevska', approver: 'B. Nikolov, M.Pharm. (Раководител КК | QC Manager)' };
