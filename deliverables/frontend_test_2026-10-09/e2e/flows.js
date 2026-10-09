// Functional flows: wizard build + downloads, Create → new doc, Questionnaire → Jobs, Formatter, Chat, Preview, Reports, Fleet.
const { chromium } = require('playwright');
const OUT = process.argv[2];
const log = [];
(async () => { try {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, acceptDownloads: true });
  const page = await ctx.newPage();
  let where = 'start';
  page.on('pageerror', e => log.push(`[${where}] PAGEERROR ${String(e).slice(0, 200)}`));
  page.on('response', async r => {
    const u = r.url().replace('http://127.0.0.1:8770', '');
    if (r.status() >= 400 && !(where === 'start' && u === '/api/doctypes')) log.push(`[${where}] HTTP ${r.status()} ${r.request().method()} ${u} ${(await r.text().catch(() => '')).slice(0, 160).replace(/\s+/g, ' ')}`);
    else if (/\/(build|workflows)/.test(u) && r.request().method() === 'POST') log.push(`[${where}] HTTP ${r.status()} POST ${u} ${(await r.text().catch(() => '')).slice(0, 220).replace(/\s+/g, ' ')}`);
  });
  const shot = n => page.screenshot({ path: `${OUT}/${n}.png` });
  const nav = async n => { where = n; await page.getByText(n, { exact: true }).first().click(); await page.waitForTimeout(1500); };
  const buttons = async () => (await page.locator('button').allInnerTexts()).map(s => s.trim()).filter(Boolean).join(' | ');
  const body = async () => (await page.locator('body').innerText()).replace(/\s+/g, ' ');

  await page.goto('http://127.0.0.1:8770/?api=live'); await page.waitForTimeout(800);
  await page.locator('input').first().fill('dev-key-test'); await page.keyboard.press('Enter'); await page.waitForTimeout(2000);

  // (a) wizard build of the Builder's document → .docx + .pdf
  await nav('Builder');
  await page.getByText('Blocks · wizard', { exact: true }).click(); await page.waitForTimeout(600);
  await shot('w1_blocks');
  await page.getByText('Build ▸', { exact: true }).click();
  await page.waitForFunction(() => /Gate passed|Rejected and not saved/.test(document.body.innerText), null, { timeout: 180000 }).catch(() => log.push('[wizard] no banner'));
  await page.waitForTimeout(500); await shot('w2_wizard_result');
  log.push('[wizard] banner: ' + ((await body()).match(/(Gate passed|Rejected and not saved)[^⏎]{0,160}/) || ['none'])[0]);
  for (const ext of ['docx', 'pdf']) {
    const a = page.locator(`a[href$=".${ext}"]`).first();
    if (!(await a.count())) { log.push(`[wizard] no .${ext} link`); continue; }
    const href = await a.getAttribute('href');
    const r = await page.request.get('http://127.0.0.1:8770' + href, { timeout: 180000 });
    const buf = await r.body(); require('fs').writeFileSync(`${OUT}/../wizard_build.${ext}`, buf);
    log.push(`[wizard] GET ${href} → ${r.status()} ${buf.length} bytes`);
  }

  // (b) Create → new SOP via the wizard sheet
  where = 'create';
  await page.locator('.pp-create').first().click(); await page.waitForTimeout(600); await shot('c1_menu');
  log.push('[create] menu: ' + (await body()).match(/WHAT TO CREATE.{0,400}/)?.[0]);
  await page.getByText('Write in Markdown', { exact: true }).first().click(); await page.waitForTimeout(800);
  await shot('c2_sheet');
  log.push('[create] sheet text: ' + (await body()).match(/(New|HEADERDATA PREVIEW).{0,500}/)?.[0]);
  const ph = await page.locator('input:visible').evaluateAll(es => es.slice(0, 12).map(e => (e.placeholder || e.value || e.name).slice(0, 30)));
  log.push('[create] first inputs: ' + ph.join(' | '));
  log.push('[create] sheet buttons: ' + await buttons());
  const inputs = page.locator('input:visible');
  log.push('[create] visible inputs: ' + await inputs.count());

  { const c = page.getByText('Cancel', { exact: true }); if (await c.count()) await c.first().click(); else await page.keyboard.press('Escape'); await page.waitForTimeout(500); }
  // (c) Questionnaire → workflow → Jobs
  await nav('Questionnaire'); await shot('q1');
  log.push('[quest] buttons: ' + await buttons());
  log.push('[quest] text: ' + (await body()).slice(0, 300));
  const start = page.locator('button').filter({ hasText: /start|submit|run|generate|POST \/workflows|send/i }).first();
  if (await start.count()) { log.push('[quest] clicking: ' + await start.innerText()); await start.click(); await page.waitForTimeout(4000); await shot('q2_after_start'); }
  await nav('Jobs'); await page.waitForTimeout(3000); await shot('j1');
  log.push('[jobs] text: ' + (await body()).slice(0, 400));

  // (d) Formatter
  await nav('Formatter'); await shot('f1');
  log.push('[format] buttons: ' + await buttons());
  // (e) Chat
  await nav('Agent chat');
  const ta = page.locator('textarea:visible, input[type=text]:visible').last();
  if (await ta.count()) { await ta.fill('Format WHSOP_003 for me'); await page.keyboard.press('Enter'); await page.waitForTimeout(2500); }
  await shot('ch1'); log.push('[chat] tail: ' + (await body()).slice(-300));
  for (const n of ['Reports', 'Preview', 'Verify', 'Fleet & health', 'Library']) { await nav(n); await shot('s_' + n.replace(/\W+/g, '_')); log.push(`[${n}] buttons: ${(await buttons()).slice(0, 300)}`); }
  console.log(log.join('\n'));
  await b.close();
 } catch (e) { console.log(log.join('\n')); console.log(String(e).slice(0,300)); process.exit(1); } })();
