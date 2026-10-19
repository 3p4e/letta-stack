// Create → new SOP draft → wizard build; Chat send; Formatter build; Verify re-verify; Library downloads.
const { chromium } = require('playwright');
const OUT = process.argv[2];
const log = []; let where = 'start';
(async () => { try {
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 1440, height: 900 }, acceptDownloads: true })).newPage();
  page.on('pageerror', e => log.push(`[${where}] PAGEERROR ${String(e).slice(0, 200)}`));
  page.on('response', async r => {
    const u = r.url().replace('http://127.0.0.1:8770', ''), m = r.request().method();
    if ((r.status() >= 400 && u !== '/api/doctypes') || (m === 'POST' && /build|chat|workflows/.test(u)))
      log.push(`[${where}] HTTP ${r.status()} ${m} ${u} ${(await r.text().catch(() => '')).slice(0, 200).replace(/\s+/g, ' ')}`);
  });
  const shot = n => page.screenshot({ path: `${OUT}/${n}.png` });
  const nav = async n => { where = n; await page.locator('.pp-nav', { hasText: n }).first().click(); await page.waitForTimeout(1500); };
  const body = async () => (await page.locator('body').innerText()).replace(/\s+/g, ' ');
  const banner = async () => ((await body()).match(/(Gate passed|Rejected and not saved)[^×]{0,200}/) || ['no banner'])[0];

  await page.goto('http://127.0.0.1:8770/?api=live'); await page.waitForTimeout(800);
  await page.locator('input').first().fill('dev-key-test'); await page.keyboard.press('Enter'); await page.waitForTimeout(2000);

  // 1. Create → SOP → Write in Markdown → fill → Create draft
  where = 'create';
  await page.locator('.pp-create').first().click(); await page.waitForTimeout(500);
  await page.getByText('Write in Markdown', { exact: true }).first().click(); await page.waitForTimeout(800);
  const sheet = page.locator('text=New SOP starts in Markdown').locator('xpath=ancestor::div[.//input][1]');
  const fill = async (k, v) => { const i = page.locator('label').filter({ has: page.locator('span', { hasText: new RegExp('^' + k) }) }).locator('input').first(); if (await i.count()) { await i.fill(v); return true; } log.push(`[create] no input for "${k}"`); return false; };
  await fill('code', 'WHSOP_003');
  await fill('title_mk', 'Внатрешен транспорт на наркотични супстанции');
  await fill('title_en', 'Inland Transport of Narcotic Substances');
  await page.waitForTimeout(400); await shot('n1_sheet_filled');
  log.push('[create] pre-checks: ' + ((await body()).match(/PRE-CHECKS.{0,260}/) || [''])[0]);
  await page.getByText('Create draft →').click(); await page.waitForTimeout(1500); await shot('n2_after_create');
  log.push('[create] crumb: ' + ((await body()).match(/builder › [^ ]+ · [a-z ]+ v\d+/) || ['?'])[0]);
  // add text into the first section via Blocks, then build
  await page.getByText('Blocks · wizard', { exact: true }).click(); await page.waitForTimeout(600); await shot('n3_blocks');
  const tas = page.locator('textarea:visible');
  log.push('[create] textareas in blocks: ' + await tas.count());
  if (await tas.count() >= 2) { await tas.nth(0).fill('Оваа постапка ги дефинира барањата за внатрешен транспорт.'); await tas.nth(1).fill('This procedure defines the requirements for inland transport.'); }
  where = 'create-build';
  await page.getByText('Build ▸', { exact: true }).click();
  await page.waitForFunction(() => /Gate passed|Rejected and not saved/.test(document.body.innerText), null, { timeout: 180000 }).catch(() => {});
  await page.waitForTimeout(500); await shot('n4_built'); log.push('[create-build] ' + await banner());

  // 2. Chat send
  await nav('Agent chat');
  const ci = page.locator('input[placeholder*="Message"], textarea[placeholder*="Message"]').first();
  if (await ci.count()) { await ci.fill('Format WHSOP_003 for me'); await page.getByText('Send', { exact: true }).click(); await page.waitForTimeout(2500); }
  else log.push('[chat] no message box');
  await shot('ch2_sent'); log.push('[chat] after send: ' + ((await body()).match(/.{0,40}(503|disabled|LETTA|error).{0,120}/i) || ['no error shown'])[0]);

  // 3. Formatter → Build
  await nav('Formatter'); await page.getByText('Build ▸', { exact: true }).click(); await page.waitForTimeout(4000);
  await shot('f2_build'); log.push('[format] after build: ' + ((await body()).match(/.{0,60}(PASS|FAIL|registered|Rejected|error).{0,120}/i) || ['no result shown'])[0]);

  // 4. Verify and Preview show the last real build
  await nav('Verify'); await shot('v3_live'); log.push('[verify] ' + ((await body()).match(/Gate checks.{0,300}/) || ['no gate panel'])[0]);
  await nav('Preview'); await page.waitForTimeout(2000); await shot('p3_live'); log.push('[preview] iframe src: ' + await page.locator('iframe').first().getAttribute('src').catch(() => 'none'));
  await nav('Reports'); await shot('r3_live'); log.push('[reports] ' + ((await body()).match(/Sample content, not connected.{0,80}/) || ['no ribbon'])[0]);
  await nav('Fleet & health'); await shot('fl3_live'); log.push('[fleet] ' + ((await body()).match(/Sample content, not connected.{0,80}/) || ['no ribbon'])[0]);
  // 5. Library downloads
  await nav('Library'); await page.waitForTimeout(1500); await shot('l2');
  log.push('[library] rows: ' + ((await body()).match(/CODE TITLE.{0,600}/) || [''])[0]);
  for (const t of ['Download .docx', 'PDF · Gotenberg']) {
    const el = page.getByText(t, { exact: true }).first();
    if (!(await el.count())) { log.push(`[library] no "${t}"`); continue; }
    const dl = page.waitForEvent('download', { timeout: 15000 }).catch(() => null);
    await el.click(); const d = await dl; await page.waitForTimeout(1500);
    log.push(`[library] ${t}: ${d ? 'downloaded ' + d.suggestedFilename() : 'no download'} ${((await body()).match(/.{0,30}(501|502|503|404|Gotenberg[^.]{0,60}unavailable|not configured).{0,80}/i) || [''])[0]}`);
  }
  await shot('l3');
  console.log(log.join('\n')); await b.close();
} catch (e) { console.log(log.join('\n')); console.log('ERR ' + String(e).slice(0, 400)); process.exit(1); } })();
