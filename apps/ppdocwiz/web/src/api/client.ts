import type {
  BuildResult, ChatResult, DeHealth, DocumentRow, DoctypeInfo, Health, Job, Questionnaire,
  Brief, BriefEvent, BriefPatch, BriefSuggestion, BriefPackage, Me, Account, AuthEvent, LibraryShelves, Package, QuestionnaireIndexRow, ReferenceDoc, WizardPayload,
} from './types';

export interface WorkflowIn {
  questionnaire: string;
  answers: Record<string, string | string[]>;
  meta: { title_mk: string; title_en: string; code: string; version?: string; orient?: string };
  /** The requester's own brief and the sources they name (DocEngine adds both to the content brief). */
  instructions?: string;
  sources?: string[];
  /** Annex jobs: the code of the SOP the form serves; DocEngine reads its sections 6 and 7. */
  parent_sop?: string;
  requested_by: string;
}

export interface EngineEnv {
  canon: string; version: string; synced: boolean; hash: string; hashExpected: string;
  fonts: { face: string; file: string; ok: boolean; missing: string }[];
  glyphAudit: { run: string; ok: boolean; note: string }[];
  manifestDrift: { key: string; manifest: string; live: string }[];
}

export interface DataSet { name: string; columns: string[]; rows: Record<string, string>[] }

/**
 * Everything the suite reads or writes. Two implementations:
 *   live — fetch() against ppdocwiz (/api/*) and DocEngine (`docengineBase`)
 *   mock — in-browser sample data and timers, the same behaviour the prototype showed
 * Screens only ever see this interface, so switching is a one-line change.
 */
export interface Api {
  readonly mode: 'live' | 'mock';
  // ppdocwiz
  openSession(key: string, username?: string): Promise<void>;
  /** Named accounts: who is signed in; administration (admins only). */
  me(): Promise<Me>;
  users(): Promise<Account[]>;
  addUser(u: { username: string; role: 'admin' | 'user'; temporary_password: string }): Promise<Account>;
  changeUser(username: string, c: { role?: 'admin' | 'user'; disabled?: boolean; reset_password?: string }): Promise<Account>;
  authLog(): Promise<AuthEvent[]>;
  /** The shared password (Head of QC, 19.10.2026): whether the initial one is still in use, and changing it. */
  passwordState(): Promise<{ enabled: boolean; must_change: boolean }>;
  changePassword(current: string, next: string): Promise<void>;
  closeSession(): Promise<void>;
  health(): Promise<Health>;
  doctypes(): Promise<DoctypeInfo[]>;
  example(): Promise<{ payload: WizardPayload; markdown: string }>;
  preview(payload: WizardPayload): Promise<string>;
  build(payload: WizardPayload): Promise<BuildResult>;
  chat(message: string, agent: string): Promise<ChatResult>;
  downloadHref(docId: string, ext: 'docx' | 'pdf'): string;
  // docengine
  deHealth(): Promise<DeHealth>;
  questionnaires(): Promise<QuestionnaireIndexRow[]>;
  questionnaire(key: string): Promise<Questionnaire>;
  startWorkflow(body: WorkflowIn): Promise<{ job_id: string; status: string }>;
  job(id: string): Promise<Job>;
  /** DocEngine has no list endpoint; live mode lists the ids this browser started. */
  jobs(): Promise<Job[]>;
  /** Not in DocEngine yet (status awaiting_review exists, no transition route). */
  reviewJob(id: string, decision: 'approve' | 'return', note: string): Promise<Job>;
  /** Builder Source view → ppdocwiz POST /api/build: the same engine as the wizard path; 422 on a FAIL. */
  rawBuild(markdown: string, outName: string): Promise<BuildResult>;
  directBuild(markdown: string, outName: string, meta: Record<string, string>): Promise<{ ok: true; document_id: string | null; bytes: number; verify: string }>;
  documents(): Promise<DocumentRow[]>;
  document(id: string): Promise<DocumentRow>;
  documentHref(id: string, kind: 'download' | 'pdf'): string;
  /** Probes /documents/{id}/download without downloading, to surface 410 before the click. */
  documentAvailable(id: string): Promise<number>;
  /** pp_report composer → .docx. pp_report is a Python library with no HTTP route yet. */
  buildReport(spec: { code: string; blocks: unknown[]; dataset?: { name: string; sha256: string } }): Promise<{ ok: boolean; verify: string }>;
  /** DocEngine GET /register/next: the next free house code of a family (QCSOP → QCSOP026) or of a parent's annexes. */
  nextCode(q: { family?: string; parent?: string }): Promise<string>;
  /** DocEngine GET /library: every code on its shelf (approved, revision, drafts, numbers, retired). */
  library(): Promise<LibraryShelves>;
  /** DocEngine GET /reference/{id}: an approved or work-in-progress document with its text. */
  reference(id: string): Promise<ReferenceDoc>;
  /** DocEngine Document Brief: the one workflow. */
  briefs(): Promise<Pick<Brief, 'id' | 'rev' | 'status' | 'package' | 'meta' | 'updated_at' | 'job_ids'>[]>;
  brief(id: string): Promise<Brief>;
  createBrief(b: { package: Package; meta?: Record<string, string>; questionnaire?: string; parent_sop?: string; from_reference?: string; requested_by?: string }): Promise<Brief>;
  patchBrief(id: string, p: BriefPatch): Promise<Brief>;
  briefEvents(id: string): Promise<BriefEvent[]>;
  addBriefSource(id: string, name: string, content_b64: string): Promise<{ id: string; chars: number; note: string; brief: Brief }>;
  removeBriefSource(id: string, sourceId: string): Promise<Brief>;
  /** The advisor's options with reasons and sources for open questions (all of them when `keys` is empty). */
  suggestBrief(id: string, rev: number, keys?: string[]): Promise<BriefSuggestion>;
  /** The latest build of the brief as one package (SOP + annexes), and the link to it as one merged PDF. */
  briefPackage(id: string): Promise<BriefPackage>;
  packagePdfHref(id: string): string;
  buildBrief(id: string, rev: number): Promise<{ job_id: string; status: string; code: string; assumed: string[] }>;
  /** DocEngine GET /engine/environment: engine hash vs manifest, renderer font probe, last pp_verify results, fleet drift. */
  engineEnv(): Promise<EngineEnv>;
}
