// The print-opaque conversion, lifted out of build_v40.js so the internal certificates
// can use the same rule the certificates of quality do. Nothing is changed; the
// comments are build_v40.js's own, and build_v40.js now requires this module rather
// than carrying a second copy that could drift from it.
const ALPHA_STOP = /rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([01]?(?:\.\d+)?)\s*\)/g;
// The conversion is "this colour composited over WHITE", which is true of a fill that
// sits on the page and false of anything that sits on top of something else. A
// text-shadow lies under white glyphs on a dark blue chip: .chip-sel authors it as
// rgba(9,22,38,.45), a soft dark shade, and compositing it over white printed it as
// rgb(144,150,157) — an opaque grey haze on a dark chip. Shadows, text colour and border
// colour are carried through as the design wrote them; only what paints the page behind
// them is converted.
const KEEP_AS_AUTHORED = /^\s*(text-shadow|box-shadow|color|border(-[a-z]+)?-color|outline-color|caret-color)\s*:/i;
function overWhite(css) {
  return css.split(';').map(decl => {
    if (!decl.trim() || KEEP_AS_AUTHORED.test(decl)) return decl;
    return decl.replace(ALPHA_STOP, (m, r, g, b, a) => {
      const f = parseFloat(a);
      const mix = c => Math.round(Number(c) + (255 - Number(c)) * (1 - f));
      return 'rgb(' + mix(r) + ',' + mix(g) + ',' + mix(b) + ')';
    });
  }).join(';');
}
function important(body) {                       // the originals carry !important; match it
  return body.split(';').map(d => d.trim()).filter(Boolean)
    .map(d => /!important$/.test(d) ? d : d + ' !important').join(';');
}
function printOpaqueLayer(doc) {
  const seen = new Set(), rules = [];
  const re = /([^{}]+)\{([^{}]*)\}/g;
  let m;
  while ((m = re.exec(doc))) {
    const body = m[2];
    if (body.indexOf('linear-gradient') < 0) continue;
    if (!/rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*0?\.\d+\s*\)/.test(body)) continue;
    if (body.indexOf('mask') >= 0) continue;      // a mask is the package's business
    const sel = m[1].replace(/\/\*[\s\S]*?\*\//g, '').replace(/<[^>]*>/g, '').trim();
    if (!sel || sel.indexOf('@') === 0 || seen.has(sel)) continue;
    seen.add(sel);
    rules.push(sel + '{' + important(overWhite(body)) + '}');
  }
  if (!rules.length) throw new Error('no alpha gradient found to convert');
  return '<style id="__print-opaque-rest">\n@media print{\n' + rules.join('\n') + '\n}</style>';
}

module.exports = { printOpaqueLayer, overWhite, important, ALPHA_STOP, KEEP_AS_AUTHORED };
