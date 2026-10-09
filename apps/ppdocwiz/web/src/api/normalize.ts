import type { Questionnaire } from './types';

type RawOption = string | { v: string; default?: boolean };
export interface RawQuestionnaire {
  title: { en: string; mk: string };
  doctype: string;
  rounds: { key: string; title: { en: string; mk: string }; questions: { key: string; multi: boolean; label: { en: string; mk: string }; options: RawOption[] }[] }[];
}

/** DocEngine's bank shape (questionnaires.py) → what the screen renders. */
export function normalizeQuestionnaire(key: string, q: RawQuestionnaire): Questionnaire {
  return {
    key, mk: q.title.mk, en: q.title.en, doctype: q.doctype,
    rounds: q.rounds.map(r => ({
      mk: r.title.mk, en: r.title.en,
      questions: r.questions.map(x => ({
        key: x.key, multi: !!x.multi, mk: x.label.mk, en: x.label.en,
        options: x.options.map(o => typeof o === 'string' ? { v: o, isDefault: false } : { v: o.v, isDefault: !!o.default }),
      })),
    })),
  };
}

/** apply_defaults() as the DocEngine runs it: unanswered → the default option(s), else left open. */
export function applyDefaults(q: Questionnaire, answers: Record<string, string | string[]>) {
  const out: Record<string, string | string[]> = { ...answers };
  for (const r of q.rounds) for (const x of r.questions) {
    const v = out[x.key];
    if (v !== undefined && v !== '' && !(Array.isArray(v) && !v.length)) continue;
    const defs = x.options.filter(o => o.isDefault).map(o => o.v);
    if (defs.length) out[x.key] = x.multi ? defs : defs[0];
  }
  return out;
}
