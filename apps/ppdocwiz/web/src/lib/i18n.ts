// Interface language (EN default, MK). Only the interface: documents stay bilingual MK | EN, and
// questionnaire option values stay as DocEngine sends them, because they go into the brief verbatim.
export type Lang = 'en' | 'mk';

const MK: Record<string, string> = {
  'Builder': 'Уредувач', 'Agent chat': 'Разговор со агент', 'Questionnaire': 'Прашалник', 'Formatter': 'Форматирање',
  'Reports': 'Извештаи', 'Library': 'Библиотека', 'Jobs': 'Задачи', 'Verify': 'Верификација', 'Preview': 'Преглед',
  'Fleet & health': 'Агенти и состојба', 'CREATE': 'КРЕИРАЈ', 'CONTROL': 'КОНТРОЛА', 'Sign out': 'Одјава', 'Create': 'Креирај',
  'Document meta': 'Податоци за документот', 'Content brief': 'Содржина на барањето',
  '← Previous round': '← Претходен круг', 'Next round →': 'Следен круг →',
  'Instructions': 'Упатства', 'your prompt to the authors': 'вашето барање до авторите',
  'Sources': 'Извори', 'one per line; the authors may cite them': 'по еден во ред; авторите смеат да ги цитираат',
  'Creates a job and opens it in Jobs': 'Создава задача и ја отвора во Задачи',
  'answered': 'одговорено', 'selected': 'избрано', 'unanswered → default:': 'неодговорено → стандардно:',
  'unanswered → no default exists; stays open in the brief': 'неодговорено → нема стандардна опција; останува отворено',
  'by default': 'стандардно', 'open': 'отворено',
  'defaults_note': 'го пополнува секое неодговорено прашање со најусогласената опција. Опциите се претходно проверени според регулативата; никој не пишува регулаторен текст.',
};
const EN: Record<string, string> = {
  'defaults_note': 'fills every unanswered question with its most-compliant option. Options are pre-verified against the regulatory hierarchy; nobody types regulation text.',
};

export const tr = (lang: Lang, s: string) => (lang === 'mk' ? MK[s] : EN[s]) ?? s;
/** The primary and secondary halves of a bilingual {mk, en} label for the chosen language. */
export const pick = (lang: Lang, l: { mk: string; en: string }) => (lang === 'mk' ? [l.mk, l.en] : [l.en, l.mk]);
