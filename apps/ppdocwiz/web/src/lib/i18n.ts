// Interface language (EN default, MK). Only the interface: documents stay bilingual MK | EN, and
// questionnaire option values stay as DocEngine sends them, because they go into the brief verbatim.
export type Lang = 'en' | 'mk';

const MK: Record<string, string> = {
  'Workflow': 'Работен тек', 'Users': 'Корисници', 'Builder': 'Уредувач', 'Agent chat': 'Разговор со агент', 'Questionnaire': 'Прашалник', 'Formatter': 'Форматирање',
  'Reports': 'Извештаи', 'Library': 'Библиотека', 'Jobs': 'Задачи', 'Canvas': 'Уредувач', 'Verify': 'Верификација', 'Preview': 'Преглед',
  'Fleet & health': 'Агенти и состојба', 'CREATE': 'КРЕИРАЈ', 'CONTROL': 'КОНТРОЛА', 'Sign out': 'Одјава', 'Create': 'Креирај',
  'Document meta': 'Податоци за документот', 'Content brief': 'Содржина на барањето',
  '← Previous round': '← Претходен круг', 'Next round →': 'Следен круг →',
  'Instructions': 'Упатства', 'your prompt to the authors': 'вашето барање до авторите',
  'Sources': 'Извори', 'one per line; the authors may cite them': 'по еден во ред; авторите смеат да ги цитираат',
  'Creates a job and opens it in Jobs': 'Создава задача и ја отвора во Задачи',
  'the SOP this form serves — DocEngine reads its sections 6 and 7': 'СОП-от на кој му служи овој образец — DocEngine ги чита неговите делови 6 и 7',
  'answered': 'одговорено', 'selected': 'избрано', 'unanswered → default:': 'неодговорено → стандардно:',
  'unanswered → no default exists; stays open in the brief': 'неодговорено → нема стандардна опција; останува отворено',
  'by default': 'стандардно', 'open': 'отворено', 'default': 'стандардно', 'Start workflow ▸': 'Започни работен тек ▸',
  // Sign-in and passwords (19.10.2026)
  'Username': 'Корисничко име', 'Password': 'Лозинка', 'Sign in ▸': 'Најава ▸', 'Signing in…': 'Најавување…',
  'signin_intro': 'Најавете се со вашето корисничко име и лозинка. Останувате најавени 8 часа; сè што менувате се запишува под вашето име.',
  'signin_intro_pw': 'Внесете ја лозинката. Останувате најавени 8 часа.',
  'tagline': 'СОП, анекси и записи во куќниот стил — двојазично МК | EN',
  'Wrong username or password.': 'Погрешно корисничко име или лозинка.', 'Wrong password.': 'Погрешна лозинка.',
  'Too many failed sign-ins. Wait 15 minutes and try again.': 'Премногу неуспешни обиди. Обидете се повторно за 15 минути.',
  'Set your own password': 'Поставете своја лозинка', 'Change password': 'Промени лозинка',
  'forced_change': 'Се најавивте со привремена лозинка. Пред да продолжите, изберете своја: најмалку 12 знаци (неколку неповрзани зборови се добар избор).',
  'Current password': 'Тековна лозинка', 'New password': 'Нова лозинка', 'New password again': 'Повторете ја новата лозинка',
  'Set password ▸': 'Постави лозинка ▸', 'Saving…': 'Се зачувува…', 'Cancel': 'Откажи',
  'At least 12 characters.': 'Најмалку 12 знаци.', 'The two new passwords differ.': 'Двете нови лозинки се разликуваат.',
  'The current password is wrong.': 'Тековната лозинка е погрешна.', 'Too many failed attempts. Wait 15 minutes.': 'Премногу неуспешни обиди. Почекајте 15 минути.',
  'Password changed': 'Лозинката е променета', 'signed in as': 'најавен како',
  'defaults_note': 'го пополнува секое неодговорено прашање со најусогласената опција. Опциите се претходно проверени според регулативата; никој не пишува регулаторен текст.',
};
const EN: Record<string, string> = {
  'signin_intro': 'Sign in with your username and password. You stay signed in for 8 hours; everything you change is recorded under your name.',
  'signin_intro_pw': 'Enter the password. You stay signed in for 8 hours.',
  'tagline': 'SOPs, annexes and records in the house style — bilingual MK | EN',
  'forced_change': 'You signed in with a temporary password. Choose your own before continuing: at least 12 characters (a few unrelated words work well).',
  'defaults_note': 'fills every unanswered question with its most-compliant option. Options are pre-verified against the regulatory hierarchy; nobody types regulation text.',
};

export const tr = (lang: Lang, s: string) => (lang === 'mk' ? MK[s] : EN[s]) ?? s;
/** The primary and secondary halves of a bilingual {mk, en} label for the chosen language. */
export const pick = (lang: Lang, l: { mk: string; en: string }) => (lang === 'mk' ? [l.mk, l.en] : [l.en, l.mk]);
