// Builder → Source → Edit raw Markdown → paste a real controlled document → Build ▸ (DocEngine POST /build).
const { chromium } = require('playwright');
const fs = require('fs');
const [OUT, ...SRCS] = process.argv.slice(2);

(async () => {
  const b = await chromium.launch();
  const page = await b.newPage({ viewport: { width: 1440, height: 900 } });
  const log = []; let where = 'start';
  page.on('pageerror', e => log.push(`[${where}] PAGEERROR ${String(e).slice(0, 200)}`));
  page.on('response', async r => {
    const u = r.url();
    if (u.includes('/api/docengine/build') || u.includes('/api/wizard/build') || r.status() >= 400)
      log.push(`[${where}] HTTP ${r.status()} ${r.request().method()} ${u.replace('http://127.0.0.1:8770', '')}${u.includes('/build') ? ' ' + (await r.text().catch(() => '')).slice(0, 400).replace(/\s+/g, ' ') : ''}`);
  });
  await page.goto('http://127.0.0.1:8770/?api=live'); await page.waitForTimeout(800);
  await page.locator('input').first().fill('dev-key-test'); await page.keyboard.press('Enter'); await page.waitForTimeout(2000);

  for (const src of SRCS) {
    const name = src.split('/').pop().replace('.md', ''); where = name;
    await page.getByText('Builder', { exact: true }).first().click(); await page.waitForTimeout(500);
    await page.getByText('Source · Markdown', { exact: true }).click(); await page.waitForTimeout(400);
    const discard = page.getByText('Discard raw edits, back to blocks');
    if (await discard.count()) { await discard.click(); await page.waitForTimeout(300); }
    await page.getByText('Edit raw Markdown', { exact: true }).click(); await page.waitForTimeout(400);
    await page.locator('textarea').fill(fs.readFileSync(src, 'utf8'));
    await page.screenshot({ path: `${OUT}/raw_${name}_1_pasted.png` });
    const t0 = Date.now();
    await page.getByText('Build ▸', { exact: true }).click();
    await page.waitForFunction(() => /Gate passed|Rejected and not saved/.test(document.body.innerText), null, { timeout: 240000 }).catch(() => log.push(`[${name}] NO RESULT BANNER in 240 s`));
    log.push(`[${name}] build took ${((Date.now() - t0) / 1000).toFixed(1)} s`);
    await page.waitForTimeout(800);
    await page.screenshot({ path: `${OUT}/raw_${name}_2_result.png` });
    const banner = (await page.locator('body').innerText()).match(/(Gate passed[^\n]*|Rejected and not saved[^\n]*)(\n[^\n]*){0,3}/);
    log.push(`[${name}] banner: ${banner ? banner[0].replace(/\n/g, ' ⏎ ') : 'none'}`);
    for (const ext of ['docx', 'pdf']) {
      const a = page.locator(`a[href$=".${ext}"]`).first();
      if (!(await a.count())) { log.push(`[${name}] no .${ext} link`); continue; }
      const r = await page.request.get('http://127.0.0.1:8770' + await a.getAttribute('href'), { timeout: 180000 });
      fs.writeFileSync(`${OUT}/../ui_${name}.${ext}`, await r.body()); log.push(`[${name}] .${ext} → ${r.status()}`);
    }
    log.push(`[${name}] crumb: ${(await page.locator('body').innerText()).match(/builder › [^\n]*/)?.[0]}`);
  }
  where = 'library';
  await page.getByText('Library', { exact: true }).first().click(); await page.waitForTimeout(2500);
  await page.screenshot({ path: `${OUT}/raw_library.png` });
  console.log(log.join('\n'));
  await b.close();
})();
