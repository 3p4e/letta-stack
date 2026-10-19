// PP Doc Wiz frontend survey: sign-in (bad + good key), every nav screen, errors and failed calls.
const { chromium } = require('playwright');
const OUT = process.argv[2];
const BASE = 'http://127.0.0.1:8770/?api=live';
const NAV = ['Builder', 'Agent chat', 'Questionnaire', 'Formatter', 'Reports', 'Library', 'Jobs', 'Verify', 'Preview', 'Fleet & health'];

(async () => {
  const b = await chromium.launch();
  const page = await b.newPage({ viewport: { width: 1440, height: 900 } });
  const log = [];
  let where = 'start';
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') log.push(`[${where}] console.${m.type()}: ${m.text().slice(0, 300)}`); });
  page.on('pageerror', e => log.push(`[${where}] PAGEERROR: ${String(e).slice(0, 300)}`));
  page.on('response', r => { if (r.status() >= 400) log.push(`[${where}] HTTP ${r.status()} ${r.request().method()} ${r.url().replace('http://127.0.0.1:8770', '')}`); });

  await page.goto(BASE); await page.waitForTimeout(1200);
  where = 'signin';
  await page.screenshot({ path: `${OUT}/00_signin.png` });
  const inp = page.locator('input').first();
  await inp.fill('wrong-key'); await page.keyboard.press('Enter'); await page.waitForTimeout(800);
  await page.screenshot({ path: `${OUT}/01_signin_badkey.png` });
  log.push('[signin] text after bad key: ' + (await page.locator('body').innerText()).replace(/\s+/g, ' ').slice(0, 200));
  await inp.fill('dev-key-test'); await page.keyboard.press('Enter'); await page.waitForTimeout(2500);

  for (const [i, n] of NAV.entries()) {
    where = n;
    const el = page.getByText(n, { exact: true }).first();
    if (!(await el.count())) { log.push(`[${n}] NAV ITEM NOT FOUND`); continue; }
    await el.click(); await page.waitForTimeout(2000);
    await page.screenshot({ path: `${OUT}/${String(i + 2).padStart(2, '0')}_${n.replace(/\W+/g, '_')}.png` });
    const t = (await page.locator('body').innerText()).replace(/\s+/g, ' ');
    const flags = t.match(/(\b[45]\d\d\b[^.]{0,80}|error[^.]{0,80}|unreachable[^.]{0,60}|not found[^.]{0,60})/gi) || [];
    if (flags.length) log.push(`[${n}] on-screen: ${[...new Set(flags)].slice(0, 6).join(' | ')}`);
  }
  console.log(log.join('\n'));
  await b.close();
})();
