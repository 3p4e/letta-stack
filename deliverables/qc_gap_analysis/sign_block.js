// The deposited signatures, applied to the signature boxes of the desk's two
// certificate families.
//
// The Head of QC, 18.09.2026: "we signed the intermediate bulk product specifications
// me and my head of QA colleague ... you have used our deposited transparent background
// signatures ... I want you to apply them to all of the certificates of quality and all
// of the internal certificates of analysis rotating them suitably."
//
// Three people have a deposited signature and only three: the Head of QC (Blagoj
// Nikolov, QC Manager), the QA Manager (Jovana Romevska Cvetkovski) and the Analyst
// (Hristina Cekikj). Nineteen scanned iterations of each of the first two are on file;
// the Analyst's is a single photograph, sent by the Head of QC on 18.09.2026 and lifted
// off its paper here — so her box always carries the same hand, pressed differently.
// A name with no deposit keeps its empty rule: the desk does not draw a signature it was
// not given.
//
// A signature box is matched by the NAME printed beneath it, never by its position in
// the grid: the certificate of quality runs QC then QA, the internal certificate runs
// Analyst, QA, QC, and a third family would run its own order.
//
// Which iteration lands on which certificate is settled by a hash of the document code,
// so the same certificate always prints the same hand — a reprint is identical — while
// the fleet as a whole shows all nineteen. The tilt and the offset come from the same
// hash: a signature pressed by hand does not sit at 90 degrees on the rule.
//
// Signing is opt-in. PP_SIGNATURES=1 in the environment applies them; without it both
// printers produce the unsigned set, which is the set the desk has been issuing and the
// one the guards in the builders continue to police.
const fs = require('fs'), path = require('path');
const STORE = path.join(__dirname, 'bundles', '_signatures', 'print');

// Two whose signature is deposited, by the name the certificate prints.
const DEPOSITED = { 'Blagoj Nikolov': 'qc', 'Jovana Romevska Cvetkovski': 'qa', 'Hristina Cekikj': 'an' };

function enabled() { return process.env.PP_SIGNATURES === '1'; }

const cache = {};
function iterations(who) {
  if (cache[who]) return cache[who];
  const files = fs.readdirSync(STORE).filter(f => f.indexOf(who + '_') === 0 && /\.png$/.test(f)).sort();
  if (!files.length) throw new Error('no deposited signature for ' + who + ' in ' + STORE);
  cache[who] = files.map(f => ({
    name: f,
    uri: 'data:image/png;base64,' + fs.readFileSync(path.join(STORE, f)).toString('base64'),
  }));
  return cache[who];
}

function hash(key) { let x = 0; for (let i = 0; i < key.length; i++) x = (x * 131 + key.charCodeAt(i)) >>> 0; return x; }

// The CSS the boxes need. The box itself is a 1 px rule with clear space above it; the
// scan is absolutely placed against that rule and allowed out of the box, because a
// signature that stays inside its box is a stamp, not a signature.
const CSS = '<style id="__sig-ink">\n' +
  'html body div.page div.approval-grid div.ap-sign{position:relative !important;overflow:visible !important}\n' +
  'html body div.page div.approval-grid div.ap-sign img.ap-img{position:absolute !important;' +
  'z-index:6;pointer-events:none;mix-blend-mode:multiply;transform-origin:50% 100%;' +
  'max-width:none !important;max-height:none !important;-webkit-print-color-adjust:exact;print-color-adjust:exact}\n' +
  '</style>';

// spec: { h: nominal height in page px, dy: how far the pen rests below the rule }
function sign(html, key, spec) {
  if (!enabled()) return html;
  const h = spec.h, dy = spec.dy;
  let placed = 0;
  const out = html.replace(
    /<div class="ap-sign">\s*<div class="ap-line"><\/div>\s*<\/div>([\s\S]{0,800}?)<div class="ap-name">([^<]*)<\/div>/g,
    function (m, mid, name) {
      const who = DEPOSITED[name.trim()];
      if (!who) return m;                              // no deposit — the rule stays empty
      const set = iterations(who);
      const x = hash(who + '|' + key);
      const f = n => (((x >>> n) & 0xFFFF) / 0xFFFF) * 2 - 1;   // -1 .. +1
      const pick = set[x % set.length];
      const tilt = (f(3) * 7.0).toFixed(2);            // degrees off the rule
      const dx = (f(9) * 9).toFixed(1);                // along the rule
      const dyy = (dy + f(17) * 3.0).toFixed(1);       // how deep the pen sat
      const hh = (h * (1 + f(23) * 0.09)).toFixed(1);  // how big the hand wrote
      placed++;
      return '<div class="ap-sign"><div class="ap-line"></div>' +
        '<img class="ap-img handwritten" alt="" src="' + pick.uri + '" ' +
        'style="height:' + hh + 'px;left:calc(50% + ' + dx + 'px);bottom:' + dyy + 'px;' +
        'transform:translateX(-50%) rotate(' + tilt + 'deg)">' +
        '</div>' + mid + '<div class="ap-name">' + name + '</div>';
    });
  if (!placed) throw new Error('no signature box took a signature on ' + key);
  if (out.indexOf('id="__sig-ink"') >= 0) return out;
  if (out.indexOf('</body>') < 0) throw new Error('no </body> to append the signature layer before: ' + key);
  return out.replace('</body>', CSS + '\n</body>');
}

module.exports = { enabled, sign, iterations, DEPOSITED };
