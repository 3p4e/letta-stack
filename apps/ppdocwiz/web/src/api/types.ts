// Wire types for the two backends this UI talks to.
//   ppdocwiz  (apps/ppdocwiz/backend/app.py)      — /api/*
//   docengine (apps/wwf-docengine/app/main.py)    — reached through `docengineBase`

export type DocStatus = 'draft' | 'in_review' | 'approved';
export type Doctype = 'SOP' | 'ANNEX' | 'FORM' | 'LOG' | 'CHECKLIST' | 'REPORT';

// ---- wizard payload (wizard.py docstring) ----
export interface Para { mk: string; en: string }
export interface FormRow { label_mk: string; label_en: string; value: string }
export interface Cell { mk: string; en: string }
export type Block =
  | { type: 'text'; paras: Para[] }
  | { type: 'bullets'; paras: Para[] }
  | { type: 'form'; rows: FormRow[] }
  | { type: 'table'; cols: Cell[]; rows: Cell[][] };
export interface Section { num: string; mk: string; en: string; level: 1 | 2 | 3; blocks: Block[] }
export interface WizardPayload {
  doctype: Doctype;
  mk_title: string; en_title: string; code: string; version: string;
  parent: string; supersedes: string; orient: 'portrait' | 'landscape';
  status: DocStatus; effective_date: string; review_date: string;
  sections: Section[];
}

export interface Health { ok: boolean; letta: boolean; pdf: boolean }
export interface DoctypeInfo { key: string; mk: string; en: string; desc: string; default_orient: string }
export interface BuildResult {
  ok: boolean; verify: string; doc_id: string; markdown: string;
  download_docx: string; download_pdf: string; error?: string;
}
/** The agent's document, rebuilt by PP Doc Wiz from the Markdown the agent sent to its build tool. */
export interface ChatBuilt { ok: boolean; doc_id: string; verify: string; download_docx?: string; download_pdf?: string }
export interface ChatResult { ok: boolean; agent: string; reply: string; built: ChatBuilt | null }

// ---- docengine ----
export interface DeHealth { ok: boolean; db: boolean; letta: boolean; engine: string }
export interface QuestionnaireIndexRow { key: string; title: string; doctype: string; rounds: number }
export interface Question { key: string; multi: boolean; mk: string; en: string; options: { v: string; isDefault: boolean }[] }
export interface Round { mk: string; en: string; questions: Question[] }
export interface Questionnaire { key: string; mk: string; en: string; doctype: string; rounds: Round[] }
export type JobStatus = 'queued' | 'running' | 'awaiting_review' | 'done' | 'failed';
export interface Job {
  id: string; kind: 'workflow' | 'build'; status: JobStatus; stage: string;
  payload: {
    questionnaire: string; answers: Record<string, string | string[]>; meta: Record<string, string>; requested_by: string;
    instructions?: string; sources?: string[]; parent_sop?: string;
  };
  result: Record<string, unknown>; error: string | null; created_by: string; created_at: string; updated_at: string;
}
export interface DocumentRow {
  id: string; code: string; doctype: string; title_mk: string; title_en: string;
  version: string; bytes: number; created_at: string;
  job_id?: string | null; verify?: string; path?: string;
}

/** An HTTP failure surfaced to the UI with its status, so screens can render 401/410/422/503 states. */
export class ApiError extends Error {
  constructor(public status: number, message: string, public body?: unknown) { super(message); }
}

/** DocEngine GET /library (18.10.2026): every document code on one shelf. */
export type Shelf = 'approved' | 'revision' | 'drafts' | 'numbers' | 'retired';
export interface RefBrief { id: string; version: string; title_en: string; effective_date: string; chars: number | null; ragflow_doc_id: string; package?: string }
export interface ShelfEntry {
  code: string; parent: string; department: string; title_mk: string; title_en: string; status: string; version: string;
  effective_date: string; shelf: Shelf; approved: RefBrief | null; wip: RefBrief[];
  builds: { id: string; version: string; doctype: string; created_at: string; job_id: string | null }[];
  jobs: { id: string; status: string; stage: string; title_en: string; updated_at: string }[]; notes: string[];
}
export interface LibraryShelves { shelves: Record<Shelf, ShelfEntry[]>; counts: Record<Shelf, number> }
export interface ReferenceDoc extends RefBrief { kind: 'approved' | 'wip'; code: string; parent: string; title_mk: string; department: string; source: Record<string, unknown>; markdown: string }

/** DocEngine Document Brief (18.10.2026): the one saved draft the workflow edits. */
export type Package = 'sop' | 'sop_annexes' | 'annex' | 'form' | 'report';
export type FieldState = 'suggested' | 'chosen' | 'locked';
export interface BriefField { value: string | string[]; state: FieldState; stale: boolean; at: string; by: string }
export interface BriefSource { id: string; name: string; kind: string; bytes: number; chars: number; created_at: string }
export interface BriefAnnex { title_en: string; title_mk: string; kind: string }
export interface Brief {
  id: string; rev: number; status: string; package: Package; questionnaire: string; parent_sop: string;
  meta: Record<string, string>; fields: Record<string, BriefField>; annexes: BriefAnnex[]; job_ids: string[];
  sources: BriefSource[]; updated_at: string;
}
export interface BriefPatch {
  rev: number; actor?: string; set?: Record<string, unknown>; suggest?: Record<string, unknown>; lock?: string[]; unlock?: string[];
  meta?: Record<string, string>; package?: Package; questionnaire?: string; parent_sop?: string; annexes?: BriefAnnex[];
}
export interface BriefEvent { rev: number; at: string; actor: string; op: string; key: string; before: unknown; after: unknown }
