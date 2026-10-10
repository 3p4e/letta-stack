#!/usr/bin/env node
/**
 * Deterministic frame capture: Chromium renders film1.html at explicit
 * timestamps; JPEG buffers are piped straight into ffmpeg (no disk spill).
 *
 *   node capture.js stills 0.8 14 40 62 90 108 124 137
 *   node capture.js render
 */
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const DIR = __dirname;
const TL = JSON.parse(fs.readFileSync(path.join(DIR, 'film1_timeline.json'), 'utf8'));
const FFMPEG = process.env.FFMPEG_BIN;
const FPS = 24, W = 1920, H = 1080;

async function boot() {
  const browser = await chromium.launch({
    args: ['--force-device-scale-factor=1', '--hide-scrollbars',
           '--disable-lcd-text', '--font-render-hinting=none'],
  });
  const page = await browser.newPage({ viewport: { width: W, height: H },
                                       deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(DIR, 'film1.html'));
  await page.evaluate(() => document.fonts.ready);
  const n = await page.evaluate(tl => window.setTimeline(tl), TL);
  console.log(`  scenes wired: ${n}, runtime ${TL.total}s`);
  return { browser, page };
}

(async () => {
  const mode = process.argv[2] || 'render';
  const { browser, page } = await boot();

  if (mode === 'stills') {
    const times = process.argv.slice(3).map(Number);
    fs.mkdirSync(path.join(DIR, 'stills'), { recursive: true });
    for (const t of times) {
      await page.evaluate(t => window.render(t), t);
      const f = path.join(DIR, 'stills', `f_${String(t).padStart(6, '0')}.png`);
      await page.screenshot({ path: f, type: 'png' });
      console.log('  still', t + 's', '->', path.basename(f));
    }
    await browser.close();
    return;
  }

  const out = path.join(DIR, 'out', 'film1_izvrsen_brifing.mp4');
  fs.mkdirSync(path.dirname(out), { recursive: true });
  const audio = path.join(DIR, 'audio', 'film1_master.m4a');
  const total = Math.ceil(TL.total * FPS);

  const ff = spawn(FFMPEG, [
    '-y', '-hide_banner', '-loglevel', 'error',
    '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(FPS), '-i', 'pipe:0',
    '-i', audio,
    '-map', '0:v', '-map', '1:a',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '19',
    '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.2',
    '-r', String(FPS), '-g', String(FPS * 2),
    '-c:a', 'aac', '-b:a', '192k', '-ar', '44100',
    '-movflags', '+faststart', '-shortest', out,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });

  const write = buf => new Promise(res => {
    if (ff.stdin.write(buf)) res(); else ff.stdin.once('drain', res);
  });

  const t0 = Date.now();
  for (let i = 0; i < total; i++) {
    const t = i / FPS;
    await page.evaluate(t => window.render(t), t);
    await write(await page.screenshot({ type: 'jpeg', quality: 94 }));
    if (i % 240 === 0 || i === total - 1) {
      const el = (Date.now() - t0) / 1000;
      const pct = ((i + 1) / total * 100).toFixed(1);
      const eta = el / (i + 1) * (total - i - 1);
      console.log(`  frame ${i + 1}/${total}  ${pct}%  ${el.toFixed(0)}s elapsed  ~${eta.toFixed(0)}s left`);
    }
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error('ffmpeg exit ' + c))));
  await browser.close();
  const mb = (fs.statSync(out).size / 1048576).toFixed(1);
  console.log(`\n  ✔ ${out}  (${mb} MB, ${TL.total.toFixed(1)}s)`);
})().catch(e => { console.error(e); process.exit(1); });
