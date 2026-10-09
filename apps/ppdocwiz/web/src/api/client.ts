import type {
  BuildResult, ChatResult, DeHealth, DocumentRow, DoctypeInfo, Health, Job, Questionnaire,
  QuestionnaireIndexRow, WizardPayload,
} from './types';

export interface WorkflowIn {
  questionnaire: string;
  answers: Record<string, string | string[]>;
  meta: { title_mk: string; title_en: string; code: string; version?: string; orient?: string };
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
  openSession(key: string): Promise<void>;
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
  directBuild(markdown: string, outName: string, meta: Record<string, string>): Promise<{ ok: true; document_id: string | null; bytes: number; verify: string }>;
  documents(): Promise<DocumentRow[]>;
  document(id: string): Promise<DocumentRow>;
  documentHref(id: string, kind: 'download' | 'pdf'): string;
  /** Probes /documents/{id}/download without downloading, to surface 410 before the click. */
  documentAvailable(id: string): Promise<number>;
  /** pp_report composer → .docx. pp_report is a Python library with no HTTP route yet. */
  buildReport(spec: { code: string; blocks: unknown[]; dataset?: { name: string; sha256: string } }): Promise<{ ok: boolean; verify: string }>;
  /** pp_assets.check_environment + canon/version sync + manifest drift. No endpoint yet. */
  engineEnv(): Promise<EngineEnv>;
}
