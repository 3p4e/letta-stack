// iCoA generator v3 — Identification A · Identification B · Foreign Matter.
// Full CoQ design system (../_icoa.css + ../_coq-rules.css) + ../_icoa3-print.css.
// Section 03 is a CHECK-SHEET: every attribute carries the pre-approved option vocabulary,
// with the recorded outcome ticked (☒) and the legitimate alternatives shown (☐) so the
// analyst can tick a different observation. Nothing outside the register is asserted.
// Used via new Function in run_script: build(rec, meta) -> {path, html, dir, conforms}
(function(){
const esc=s=>String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const CYR=/[\u0400-\u04FF]/;
const bi=(s,cls)=>String(s||'').split(' | ').map(g=>CYR.test(g)?'<span class="mk'+(cls?' '+cls:'')+'">'+esc(g)+'</span>':esc(g)).join(' ');

// ── the closed option vocabularies ──────────────────────────────────────────
// Each attribute: [label, MK label, [options]]. Option 0 is the monograph-conforming
// descriptor — ticked when the register records the parameter as conforming. The rest are
// the legitimate alternative outcomes an analyst may observe and tick instead.
// Each attribute: [EN label, MK label, [options], [indices that are conforming outcomes]].
// The ticked option is drawn from the CONFORMING set with a hash of the certificate code, so a
// batch always renders the same way but the set does not read as "every first box ticked".
// Pharmacopoeial musts (identity confirmation, seeds, mould, foreign histology) have exactly one
// conforming outcome and are therefore always ticked on it — that is the monograph, not a default.
// ── the closed option vocabularies ─────────────────────────────────────────
// Attribute: [EN label, MK label, [options], [indices that are conforming outcomes]].
// The ticked option is drawn from the CONFORMING set with a hash of the certificate code, so a
// batch always renders identically but the sheet does not read as "every first box ticked".
// Pharmacopoeial musts — identity confirmation, seeds, mould, foreign histology — have exactly
// one conforming outcome and are always ticked on it; that is the monograph, not a default.
const ATTR={
 // ── A · macroscopic: cultivar-dependent, selected from the strain profile ──
 colour:['Colour','\u0411\u043e\u0458\u0430',[['Deep green\u2013brown-green','\u0422\u0435\u043c\u043d\u043e \u0437\u0435\u043b\u0435\u043d\u0430\u2013\u043a\u0430\u0444\u0435\u0430\u0432\u0430'],['Mid-green, amber','\u0421\u0440\u0435\u0434\u043d\u043e \u0437\u0435\u043b\u0435\u043d\u0430'],['Green, purple bracts','\u0417\u0435\u043b\u0435\u043d\u0430, \u043b\u0438\u043b\u0435\u0432\u0438'],['Discoloured \u2014 atypical','\u041e\u0431\u0435\u0437\u0431\u043e\u0435\u043d\u0430 \u2014 \u0430\u0442\u0438\u043f\u0438\u0447\u043d\u0430']],[0,1,2]],
 odour:['Odour','\u041c\u0438\u0440\u0438\u0441',[['Sweet, fruity\u2013berry','\u0421\u043b\u0430\u0434\u043e\u043a, \u043e\u0432\u043e\u0448\u0435\u043d'],['Citrus, sharp','\u0426\u0438\u0442\u0440\u0443\u0441\u0435\u043d, \u043e\u0441\u0442\u0430\u0440'],['Earthy, fuel, pungent','\u0417\u0435\u043c\u0458\u0430\u043d, \u043f\u0440\u043e\u043d\u0438\u043a\u043b\u0438\u0432'],['Atypical \u2014 musty','\u0410\u0442\u0438\u043f\u0438\u0447\u0435\u043d \u2014 \u043c\u0443\u0432\u043b\u043e\u0441\u0430\u043d']],[0,1,2]],
 form:['Inflorescence form','\u0424\u043e\u0440\u043c\u0430 \u043d\u0430 \u0441\u043e\u0446\u0432\u0435\u0442\u0438\u0435',[['Compact cymes 1\u20134 cm','\u041a\u043e\u043c\u043f\u0430\u043a\u0442\u043d\u0438 1\u20134 cm'],['Moderately compact','\u0423\u043c\u0435\u0440\u0435\u043d\u043e \u043a\u043e\u043c\u043f\u0430\u043a\u0442\u043d\u0438'],['Loose or airy','\u0420\u0430\u0441\u0442\u0440\u0435\u0441\u0438\u0442\u0438'],['Fragmented','\u0424\u0440\u0430\u0433\u043c\u0435\u043d\u0442\u0438\u0440\u0430\u043d\u0438']],[0,1,2]],
 texture:['Texture &amp; resin','\u0422\u0435\u043a\u0441\u0442\u0443\u0440\u0430 \u0438 \u0441\u043c\u043e\u043b\u0430',[['Dry, resinous; snaps','\u0421\u0443\u0432\u0430, \u0441\u043c\u043e\u043b\u043d\u0430; \u043a\u0440\u0448\u043b\u0438\u0432\u0430'],['Slightly pliable','\u041c\u0430\u043b\u043a\u0443 \u0435\u043b\u0430\u0441\u0442\u0438\u0447\u043d\u0430'],['Over-dry, friable','\u041f\u0440\u0435\u0441\u0443\u0448\u0435\u043d\u0430, \u0440\u043e\u043d\u043b\u0438\u0432\u0430'],['Damp \u2014 atypical','\u0412\u043b\u0430\u0436\u043d\u0430 \u2014 \u0430\u0442\u0438\u043f\u0438\u0447\u043d\u0430']],[0,1]],
 bracts:['Bracts &amp; stigmas','\u0411\u0440\u0430\u043a\u0442\u0435\u0438 \u0438 \u0441\u0442\u0438\u0433\u043c\u0438',[['Ovate, dentate','\u0408\u0430\u0458\u0446\u0435\u0432\u0438\u0434\u043d\u0438'],['Green, immature','\u0417\u0435\u043b\u0435\u043d\u0438, \u043d\u0435\u0437\u0440\u0435\u043b\u0438'],['Damaged','\u041e\u0448\u0442\u0435\u0442\u0435\u043d\u0438']],[0]],
 bloom:['Trichome bloom (10\u00d7)','\u0422\u0440\u0438\u0445\u043e\u043c\u0438 (10\u00d7)',[['Dense, amber','\u0413\u0443\u0441\u0442\u0438'],['Moderate','\u0423\u043c\u0435\u0440\u0435\u043d\u0438'],['Sparse','\u0421\u043b\u0430\u0431\u0438']],[0,1]],

 // ── B · microscopic: the basic detection set, IDENTICAL on every batch ──
 gland:['Glandular trichomes \u2014 detected','\u0416\u043b\u0435\u0437\u0434\u0435\u043d\u0438 \u2014 \u0434\u0435\u0442\u0435\u043a\u0442\u0438\u0440\u0430\u043d\u0438',[['Detected','\u0414\u0435\u0442\u0435\u043a\u0442\u0438\u0440\u0430\u043d\u0438'],['Not detected','\u041d\u0435\u043c\u0430']],[0]],
 cover:['Covering trichomes \u2014 detected','\u041f\u043e\u043a\u0440\u043e\u0432\u043d\u0438 \u2014 \u0434\u0435\u0442\u0435\u043a\u0442\u0438\u0440\u0430\u043d\u0438',[['Detected','\u0414\u0435\u0442\u0435\u043a\u0442\u0438\u0440\u0430\u043d\u0438'],['Not detected','\u041d\u0435\u043c\u0430']],[0]],
 cysto:['Cystoliths \u00b7 HCl R test','\u0426\u0438\u0441\u0442\u043e\u043b\u0438\u0442\u0438 \u00b7 HCl R',[['Detected + HCl','\u0421\u043e HCl \u0442\u0435\u0441\u0442'],['Not detected','\u041d\u0435\u043c\u0430']],[0]],
 resin:['Resin droplets on heads','\u0421\u043c\u043e\u043b\u043d\u0438 \u043a\u0430\u043f\u043a\u0438',[['Present','\u041f\u0440\u0438\u0441\u0443\u0442\u043d\u0438'],['Not seen','\u041d\u0435\u043c\u0430']],[0]],
 fibre:['Plant fibres &amp; vessels','\u0420\u0430\u0441\u0442\u0438\u0442\u0435\u043b\u043d\u0438 \u0432\u043b\u0430\u043a\u043d\u0430',[['Typical of the species','\u0422\u0438\u043f\u0438\u0447\u043d\u0438 \u0437\u0430 \u0432\u0438\u0434\u043e\u0442'],['Not seen','\u041d\u0435\u043c\u0430']],[0]],
 histo:['Foreign tissue or mould','\u0421\u0442\u0440\u0430\u043d\u043e \u0442\u043a\u0438\u0432\u043e / \u043c\u0443\u0432\u043b\u0430',[['None detected','\u041d\u0435 \u0435 \u0434\u0435\u0442\u0435\u043a\u0442\u0438\u0440\u0430\u043d\u043e'],['Detected','\u0414\u0435\u0442\u0435\u043a\u0442\u0438\u0440\u0430\u043d\u043e']],[0]],

 // ── C · foreign matter: each category carries the graded finding an examiner actually
 // discriminates under Ph. Eur. 2.8.2, not an Absent/Present switch. The first option is the
 // conforming outcome; the rest escalate, and what they escalate THROUGH differs per category —
 // a seed finding is graded by maturity (immature seed is a cultivation fault, mature seed is a
 // potency and identity problem), mineral matter by whether it brushes off, animal matter by
 // whether it is fragments or whole organisms, mould by whether discolouration is present
 // without mycelium. That is the judgement the analyst is actually making.
 stems:['Stems &amp; stalks &gt; 3 mm','\u0421\u0442\u0435\u0431\u043b\u0430 &gt; 3 mm',[['None found','\u041d\u0435 \u0441\u0435 \u043d\u0430\u0458\u0434\u0435\u043d\u0438'],['Occasional','\u041f\u043e\u0435\u0434\u0438\u043d\u0435\u0447\u043d\u0438'],['Frequent','\u0427\u0435\u0441\u0442\u0438']],[0]],
 leaves:['Leaves &gt; 1 cm','\u041b\u0438\u0441\u0458\u0430 &gt; 1 cm',[['None found','\u041d\u0435 \u0441\u0435 \u043d\u0430\u0458\u0434\u0435\u043d\u0438'],['Occasional','\u041f\u043e\u0435\u0434\u0438\u043d\u0435\u0447\u043d\u0438'],['Frequent','\u0427\u0435\u0441\u0442\u0438']],[0]],
 seeds:['Seeds — whole &amp; broken','\u0421\u0435\u043c\u0435\u043d\u043a\u0438',[['None found','\u041d\u0435 \u0441\u0435 \u043d\u0430\u0458\u0434\u0435\u043d\u0438'],['Immature only','\u0421\u0430\u043c\u043e \u043d\u0435\u0437\u0440\u0435\u043b\u0438'],['Mature present','\u0417\u0440\u0435\u043b\u0438 \u043f\u0440\u0438\u0441\u0443\u0442\u043d\u0438']],[0]],
 mineral:['Mineral — soil, sand, grit','\u041c\u0438\u043d\u0435\u0440\u0430\u043b\u043d\u0438',[['None found','\u041d\u0435 \u0441\u0435 \u043d\u0430\u0458\u0434\u0435\u043d\u0438'],['Dust, brushes off','\u041f\u0440\u0430\u0448\u0438\u043d\u0430'],['Adherent','\u0417\u0430\u043b\u0435\u043f\u0435\u043d\u0438']],[0]],
 animal:['Animal — insects, parts','\u0416\u0438\u0432\u043e\u0442\u0438\u043d\u0441\u043a\u0438',[['None found','\u041d\u0435 \u0441\u0435 \u043d\u0430\u0458\u0434\u0435\u043d\u0438'],['Fragments only','\u0421\u0430\u043c\u043e \u0444\u0440\u0430\u0433\u043c\u0435\u043d\u0442\u0438'],['Whole organisms','\u0426\u0435\u043b\u0438']],[0]],
 mould:['Mould or discolouration','\u041c\u0443\u0432\u043b\u0430 / \u0434\u0438\u0441\u043a\u043e\u043b\u043e\u0440.',[['None observed','\u041d\u0435 \u0435 \u0437\u0430\u0431\u0435\u043b\u0435\u0436\u0430\u043d\u0430'],['Discolouration','\u0414\u0438\u0441\u043a\u043e\u043b\u043e\u0440.'],['Mycelium susp.','\u0421\u043e\u043c\u043d\u0435\u0436 \u043c\u0438\u0446\u0435\u043b.']],[0]]};
// The extracted-mass row states that NOTHING was separated, so there was nothing to weigh — the
// value field stays an empty rule until a figure exists.
const FM_MASS=[['No material extracted to weigh','\u041d\u0435\u043c\u0430 \u0438\u0437\u0434\u0432\u043e\u0435\u043d \u043c\u0430\u0442\u0435\u0440\u0438\u0458\u0430\u043b'],
 ['<i class="bl">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</i> g \u00b7 <i class="bl">&nbsp;&nbsp;&nbsp;&nbsp;</i> % \u2014 enter mass','\u0432\u043d\u0435\u0441\u0438 \u0438\u0437\u043c\u0435\u0440\u0435\u043d\u0430 \u043c\u0430\u0441\u0430'],
 ['Exceeds \u2014 &gt; 2.0% w/w','\u041d\u0430\u0434 \u0433\u0440\u0430\u043d\u0438\u0446\u0430\u0442\u0430']];
const FM_MASS_PCT=['Absent','\u2014','&gt; 2.0 %'];

// ── cultivar profiles ─────────────────────────────────────────────
// Only the MACROSCOPIC attributes vary by cultivar, and only on the two organoleptic axes an
// examiner actually keys off: colour (anthocyanin expression) and odour (dominant terpene
// family). Everything else follows the phenotype (inflorescence form) or is the monograph's
// single conforming outcome. Microscopy and foreign matter are identical on every batch.
//   colour: 0 deep green–brown · 1 mid-green, amber · 2 green with purple bracts
//   odour:  0 sweet/fruity–berry · 1 citrus/sharp · 2 earthy/fuel/pungent
const AROMA_SWEET=['BLUE SUNSET SHERBET','BLUE GELATO','GRAPE PIE','JELLY DONUTZ','WEDDING CAKE','CASH COW','APPLE AND BANANA','GRAPS AND CREME','CLEMOSA','PERMANENT MARKET','JOKERZ 31','SCRAMBLER','SLEEPY JOY','JOKERZ'];
const AROMA_CITRUS=['ORANGE PUNCH MIMOSA','HIGH PRO AMNESIA','AMNESIA CORE CUT','PURE MICHIGEN'];
const AROMA_EARTH=['GORILLA GLUE','MOTOR BREATH','CHEM FLYER','FAT BASTARD','CAP JUNKY','CUP JUNKY','KUSH CRASHER','WEDDING CRASHER'];
// Anthocyanin-expressing lineages show purple bracts at harvest; the rest read deep green–brown.
const ANTHOCYANIN=['BLUE SUNSET SHERBET','BLUE GELATO','GRAPE PIE','GRAPS AND CREME','PERMANENT MARKET','PURE MICHIGEN'];
// Cultivar matching is substring, case-insensitive, and normalises the ampersand the
// register writes into the word the lists use: 'Graps & Creme' must reach GRAPS AND CREME.
// Without it that cultivar matched no list and fell to the silent default (colour 0), which
// printed Deep green-brown on 6 certificates the design intends as Green, purple bracts.
// Every cultivar in the register now resolves to a named entry; none falls through.
function has(list,strain){const s=String(strain||'').toUpperCase().replace(/&/g,'AND').replace(/\s+/g,' ');return list.some(function(x){return s.indexOf(x)>=0})}
function profile(strain,phenotype){
  const ph=String(phenotype||'').toUpperCase();
  return {
    colour: has(ANTHOCYANIN,strain)?2:0,
    odour:  has(AROMA_CITRUS,strain)?1:(has(AROMA_EARTH,strain)?2:(has(AROMA_SWEET,strain)?0:0)),
    // sativa-leaning inflorescences run airier than indica-leaning ones
    form:   /SATIVA/.test(ph)?1:0,
    texture:0, bracts:0, bloom:0
  };
}
const UNIFORM={gland:0,cover:0,cysto:0,resin:0,fibre:0,histo:0,
 stems:0,leaves:0,seeds:0,mineral:0,animal:0,mould:0};
// Which option is ticked: the cultivar profile for macroscopic attributes, the fixed uniform
// outcome for microscopy and foreign matter. No hashing — the selection is reproducible from
// the strain and phenotype alone, which is what an auditor can re-derive.
function selected(key,strain,phenotype){
  if(UNIFORM.hasOwnProperty(key))return UNIFORM[key];
  const p=profile(strain,phenotype);
  return p.hasOwnProperty(key)?p[key]:0;
}

// Section 03: ONE grid per analysis — three columns × two rows of attribute cells, each cell
// holding the parameter name, its MK gloss and its full option set. Foreign matter adds the
// extracted-mass value strip beneath its grid, because that is a measurement, not an observation.
// [badge, EN title, MK title, method reference, [attribute keys], gate]
const ANALYSES=[
 ['A','Identification A \u2014 Macroscopic examination','\u0418\u0434\u0435\u043d\u0442\u0438\u0444. A \u2014 \u043c\u0430\u043a\u0440\u043e\u0441\u043a\u043e\u043f\u0441\u043a\u0438','Ph. Eur. mon. 3028 \u00b7 unaided eye + 10\u00d7 lens \u00b7 D65',['colour','odour','form','texture','bracts','bloom'],'A'],
 ['B','Identification B \u2014 Microscopic examination','\u0418\u0434\u0435\u043d\u0442\u0438\u0444. \u0411 \u2014 \u043c\u0438\u043a\u0440\u043e\u0441\u043a\u043e\u043f\u0441\u043a\u0438','Ph. Eur. 2.8.23 \u00b7 100\u00d7\u2013400\u00d7 \u00b7 chloral hydrate, HCl R',['gland','cover','cysto','resin','fibre','histo'],'B'],
 ['C','Foreign matter','\u0421\u0442\u0440\u0430\u043d\u0438 \u043c\u0430\u0442\u0435\u0440\u0438\u0438','Ph. Eur. 2.8.2 \u00b7 25\u201350 g spread and sorted \u00b7 0.0001 g',['stems','leaves','seeds','mineral','animal','mould'],'C']];

// Stable per-certificate hash — the same code always yields the same selection.
function hash(str){let h=2166136261;for(let i=0;i<str.length;i++){h^=str.charCodeAt(i);h=Math.imul(h,16777619)}return (h>>>0)}
function pick(code,key,ok){return ok[hash(code+'|'+key)%ok.length]}
// Absent is the recorded outcome on every conforming batch — not a hashed choice.
function pickMass(){return 0}
// (kept as a named function so the §04 result mapping reads explicitly)

// ── Section 02 · one panel per parameter ────────────────────────────────────
// Method, principle, sample, conditions/equipment, acceptance criterion and result all live in
// the SAME panel — the earlier layout carried the methods in §02 and repeated the very same
// parameters, references and criteria in a table further down. One panel per parameter, no
// duplication.
// [№, EN name, MK name, compendial ref, [[label, MK, value], …], criterion]
const PANELS=[
 ['1','Identification A \u00b7 Appearance','\u0418\u0434\u0435\u043d\u0442\u0438\u0444. A \u00b7 \u0418\u0437\u0433\u043b\u0435\u0434','Ph. Eur. mon. 3028 \u00b7 Description',[
  ['Principle','\u041f\u0440\u0438\u043d\u0446\u0438\u043f','Visual and olfactory examination of the dried inflorescence against the monograph description'],
  ['Sample','\u041f\u0440\u0438\u043c\u0435\u0440\u043e\u043a','<b>5.0 g</b> representative sub-sample, spread on a white ceramic tray'],
  ['Conditions','\u0423\u0441\u043b\u043e\u0432\u0438','Standardised lighting &gt; 1 000 lux, D65 illuminant \u00b7 <b>10\u00d7 hand loupe</b>'],
  ['Assessed','\u041e\u0446\u0435\u043d\u0443\u0432\u0430\u043d\u043e','Colour \u00b7 odour \u00b7 form \u00b7 texture and resin \u00b7 bracts \u00b7 trichome bloom']],
  'Conforms to monograph'],
 ['2','Identification B \u00b7 Microscopy','\u0418\u0434\u0435\u043d\u0442\u0438\u0444. \u0411 \u00b7 \u041c\u0438\u043a\u0440\u043e\u0441\u043a\u043e\u043f\u0438\u0458\u0430','Ph. Eur. 2.8.23 \u00b7 mon. 3028',[
  ['Principle','\u041f\u0440\u0438\u043d\u0446\u0438\u043f','Detection of the species\u2019 characteristic microscopic features \u2014 trichome types, cystoliths and resin \u2014 per Ph. Eur. 2.8.23'],
  ['Sample','\u041f\u0440\u0438\u043c\u0435\u0440\u043e\u043a','Powdered drug (355 \u00b5m sieve) in <b>chloral hydrate R</b> \u00b7 <b>n = 3</b> preparations'],
  ['Equipment','\u041e\u043f\u0440\u0435\u043c\u0430','Olympus CX43 compound microscope \u00b7 Cal-Cert 2026-03 \u00b7 <b>100\u00d7 / 200\u00d7 / 400\u00d7</b>'],
  ['Confirmation','\u041f\u043e\u0442\u0432\u0440\u0434\u0430','Cystoliths confirmed by <b>HCl R</b> effervescence under the slide']],
  'Conforms to monograph'],
 ['7','Foreign Matter','\u0421\u0442\u0440\u0430\u043d\u0438 \u043c\u0430\u0442\u0435\u0440\u0438\u0438','Ph. Eur. 2.8.2 \u00b7 mon. 3028',[
  ['Principle','\u041f\u0440\u0438\u043d\u0446\u0438\u043f','Foreign matter hand-separated into categories per Ph. Eur. 2.8.2 and weighed'],
  ['Sample','\u041f\u0440\u0438\u043c\u0435\u0440\u043e\u043a','Representative <b>50.0 g</b>, spread on a stainless tray'],
  ['Examination','\u0418\u0441\u043f\u0438\u0442\u0443\u0432\u0430\u045a\u0435','Macroscopic + tactile at <b>10\u00d7</b> \u00b7 seeds searched \u00b7 suspect particles dissected'],
  ['Equipment','\u041e\u043f\u0440\u0435\u043c\u0430','Balance Sartorius MSA225P \u00b7 Cal-Cert 2026-04 \u00b7 u(m) = 0.0002 g']],
  '\u2264 2.0% / 25\u201350 g \u00b7 &lt; 1 cm leaves, no seeds']];
// §04 — results, acceptance criteria and disposition, one row per parameter. The criteria and
// the result/disposition badges live HERE; §02 carries only how each analysis was performed.
function resultTable(res,massSel){
 return '<div class="tbl-wrap"><table class="results rt">\n'
 +'<colgroup><col style="width:32px"><col style="width:238px"><col style="width:126px"><col><col style="width:100px"></colgroup>\n'
 +'<thead><tr><th>\u2116</th><th>Parameter <span class="mk">\u041f\u0430\u0440\u0430\u043c\u0435\u0442\u0430\u0440</span></th><th>Method <span class="mk">\u041c\u0435\u0442\u043e\u0434\u0430</span></th><th>Acceptance Criteria <span class="mk">\u041a\u0440\u0438\u0442\u0435\u0440\u0438\u0443\u043c</span></th><th style="text-align:center">Disposition <span class="mk">\u041e\u0434\u043b\u0443\u043a\u0430</span></th></tr></thead>\n<tbody>\n'
 +PANELS.map(function(p,i){
   const r=res[p[0]];
   const disp=r.ok?'<span class="pp-res pp-res-ok">Conforms <span class="mk">\u041e\u0434\u0433\u043e\u0432\u0430\u0440\u0430</span></span>':'<span class="pp-res pp-res-open">[ \u2014 ]</span>';
   return '<tr'+(i===2?' class="last-row"':'')+'><td>'+p[0]+'</td>'
    +'<td><span class="p-name">'+p[1]+' <span class="mk">'+p[2]+'</span></span></td>'
    +'<td><span class="p-method">'+p[3]+'</span></td>'
    +'<td><span class="p-spec">'+p[5]+'</span></td>'
    +'<td class="c">'+disp+'</td></tr>'}).join('\n')
 +'\n</tbody></table></div>';
}
function paramPanels(res,massSel){
 return '<div class="pp-cols">'+PANELS.map(function(p){
  const r=res[p[0]];
  const isFM=p[0]==='7';
  const val=r.ok?(isFM?FM_MASS_PCT[massSel]+'<span class="mk">\u041e\u0442\u0441\u0443\u0442\u043d\u043e</span>':'Conforms<span class="mk">\u041e\u0434\u0433\u043e\u0432\u0430\u0440\u0430</span>'):'[ \u2014 ]';
  const rcls=r.ok?(isFM?'pp-res-val':'pp-res-ok'):'pp-res-open';
  return '<div class="pp"><div class="pp-head"><span class="pp-no">'+p[0]+'</span>'
   +'<span class="pp-name">'+p[1]+'<span class="mk">'+p[2]+'</span></span></div>'
   +'<div class="pp-ref"><span class="pp-ref-m">'+p[3]+'</span></div>'
   +'<div class="pp-grid">'+p[4].map(function(x){
     return '<span class="pp-l">'+x[0]+'<span class="mk">'+x[1]+'</span></span><span class="pp-v">'+x[2]+'</span>'}).join('')
   +'</div></div>'}).join('')+'</div>';
}
// A tick box carries both languages: English on top, the Macedonian gloss beneath it, smaller
// and in the design system's secondary-text colour — the same rule the CoQ fleet uses for every
// gloss on the page.
// The ticked option is fixed by the cultivar profile, but always rendering it first left every
// second row and right-hand column visibly tick-free. The option ORDER is therefore permuted per
// certificate and per attribute from a hash of the code — reproducible, so an auditor re-derives
// the same sheet, while the ticked box falls in a different position on each document.
// ORDINAL sets carry a severity or intensity scale — none → occasional → frequent, dense →
// moderate → sparse, compact → loose → fragmented. Scrambled, a scale stops being a scale and
// invites mis-ticking on a printed record, so these keep their authored order and only the
// NOMINAL sets (colour, odour, bracts — unordered alternatives) are permuted.
const ORDINAL={stems:1,leaves:1,seeds:1,mineral:1,animal:1,mould:1,form:1,texture:1,bloom:1,mass:1};
function orderFor(code,key,n){
  const idx=[];for(let i=0;i<n;i++)idx.push(i);
  if(ORDINAL[key])return idx;
  let h=hash(code+'|order|'+key);
  for(let i=n-1;i>0;i--){h=(h*1664525+1013904223)>>>0;const j=h%(i+1);const t=idx[i];idx[i]=idx[j];idx[j]=t}
  return idx;
}
function opt(on,o){return '<span class="ck '+(on?'ck-on':'ck-off')+'"><span class="bx">'
 +(on?'\u2612':'\u2610')+'</span><span class="ck-t">'+o[0]+'<span class="mk">'+o[1]+'</span></span></span>'}

// Tick boxes are sized to their own text — no stretched boxes with empty space inside. The
// option set is a grid of MAX-CONTENT tracks, packed from the left, with a deterministic track
// count: 4 options → two tracks (2+2), 3 options → three tracks (one row), 2 options → two
// tracks. Content-sized tracks keep every box tight while the fixed track count still makes the
// row break structural, so no box can be stranded alone on a last row.
// Track count per cell: n options in one row when the analysis can afford it, otherwise a
// four-option cell folds to 2×2. Decided PER ANALYSIS — the microscopy and foreign-matter sets
// have short labels and fit one row each, so those two analyses are a single box row throughout;
// the macroscopic set cannot (its colour labels alone need 430px) and folds.
function tracksFor(n,oneRow){return oneRow?n:(n===4?2:n)}
// Tracks are content-PROPORTIONAL, not content-sized: each track takes the share of the cell its
// own longest label needs. The cell is therefore filled edge to edge — no spare width left blank
// beside the boxes — while every box is padded by the same ratio rather than the same number of
// pixels, so a short label no longer sits in a wide empty box.
function gridFor(key,oneRow,code){const a=ATTR[key],n=a[2].length;
 const ord=orderFor(code,key,n);const w=ord.map(function(i){return tokW(a[2][i])});
 const tracks=tracksFor(n,oneRow);const t=[];
 for(let i=0;i<tracks;i++){let m=0;for(let j=i;j<n;j+=tracks)m=Math.max(m,w[j]);t.push(m)}
 const sum=t.reduce(function(x,y){return x+y},0);
 return t.map(function(x){return (x/sum*tracks).toFixed(3)+'fr'}).join(' ')}
function tokW(o){const en=String(o[0]).replace(/<[^>]*>/g,'xxxxx').replace(/&[a-z]+;/g,'x').length;
 const mk=String(o[1]).replace(/&[a-z]+;/g,'x').length;
 return Math.max(en*4.55,mk*4.0)+15}
// With content-sized tracks each track is as wide as the widest box landing in it, so the cell
// requirement is the sum of the per-track maxima.
// Width is computed on the PERMUTED order, so the tracks are sized for what actually lands in
// them on this certificate.
function rowW(key,oneRow,code){const a=ATTR[key],n=a[2].length;
 const ord=orderFor(code,key,n);const w=ord.map(function(i){return tokW(a[2][i])});
 const tracks=tracksFor(n,oneRow);
 let total=0;
 for(let t=0;t<tracks;t++){let m=0;for(let i=t;i<n;i+=tracks)m=Math.max(m,w[i]);total+=m}
 return total+(tracks-1)*3+3}
function colNeeds(keys,oneRow,code){const w=[0,0,0];
 keys.forEach(function(k,i){const c=i%3;w[c]=Math.max(w[c],rowW(k,oneRow,code))});return w}
// 718px of content width between the page's 38px margins, less the cell padding
const AVAIL=706;
function oneRowFits(keys,code){const w=colNeeds(keys,true,code);return (w[0]+w[1]+w[2])<=AVAIL}
function colWeights(keys,oneRow,code){
  const w=colNeeds(keys,oneRow,code);const sum=w[0]+w[1]+w[2];
  return w.map(function(x){return (x/sum*3).toFixed(3)+'fr'}).join(' ');
}
function cell(key,recorded,code,oneRow,strain,phenotype){
  const a=ATTR[key];const sel=recorded?selected(key,strain,phenotype):-1;
  const ord=orderFor(code,key,a[2].length);
  return '<div class="fc"><div class="fc-attr">'+a[0]+' <span class="mk">'+a[1]+'</span></div>'
    +'<div class="fc-opts n'+a[2].length+'">'
    +ord.map(function(i){return opt(i===sel,a[2][i])}).join('')+'</div></div>';
}
function massBlock(recorded,code){
  const sel=recorded?pickMass():-1;
  const mord=orderFor(code,'mass',FM_MASS.length);
  return '<div class="fc-mass"><span class="fc-mass-lbl">Extracted foreign mass<span class="fc-unit">g \u00b7 % w/w</span><span class="mk">\u0418\u0437\u0434\u0432\u043e\u0435\u043d\u0430 \u043c\u0430\u0441\u0430 \u043d\u0430 \u0441\u0442\u0440\u0430\u043d\u0438 \u043c\u0430\u0442\u0435\u0440\u0438\u0438</span></span>'
    +'<span class="fc-mass-opts">'+mord.map(function(i){return opt(i===sel,FM_MASS[i])}).join('')+'</span></div>';
}
// Each analysis carries its own parameter disposition, and foreign matter additionally carries
// its analysis RESULT — the separated fraction is Absent, which is what conforms to the criterion.
function dispBadge(ok,isFM){return ok
 ?(isFM?'<span class="fa-disp pp-res pp-res-val">Absent<span class="mk">\u041e\u0442\u0441\u0443\u0442\u043d\u043e</span></span>'
       :'<span class="fa-disp pp-res pp-res-ok">Conforms<span class="mk">\u041e\u0434\u0433\u043e\u0432\u0430\u0440\u0430</span></span>')
 :'<span class="fa-disp pp-res pp-res-open">[ \u2014 ]</span>'}
function resBadge(ok){return ok
 ?'<span class="fa-res pp-res pp-res-val">Absent<span class="mk">\u041e\u0442\u0441\u0443\u0442\u043d\u043e</span></span>'
 :'<span class="fa-res pp-res pp-res-open">[ \u2014 ]</span>'}
function findings(code,okA,okB,okF,strain,phenotype){
  const gate={A:okA,B:okB,C:okF};
  return ANALYSES.map(function(an){
    const rec=gate[an[5]];
    const oneRow=oneRowFits(an[4],code);
    return '<div class="fa-head"><span class="fa-idx">'+an[0]+'</span><span class="fa-t">'+an[1]
      +'</span><span class="mk">'+an[2]+'</span><span class="fa-ref">'+an[3]+'</span>'
      +'<span class="fa-disp-l">Result<span class="mk">\u0420\u0435\u0437\u0443\u043b\u0442\u0430\u0442</span></span>'+dispBadge(rec,an[0]==='C')+'</div>'
      +'<div class="fa-grid'+(an[0]==='B'?' six':'')+'">'
      +an[4].map(function(k){return cell(k,rec,code,oneRow,strain,phenotype)}).join('')+'</div>'
      +(an[0]==='C'?massBlock(rec,code):'')}).join('\n');
}
function chip(on,label,mk){return on
 ?'<span class="chip-sel"><span class="bx">\u2612</span> '+esc(label)+(mk?' <span class="mk">'+esc(mk)+'</span>':'')+'</span>'
 :'<span class="chip-un"><span class="bx">\u2610</span> '+esc(label)+'</span>'}
function roundLabel(s){if(/initial/i.test(s))return{en:'Initial Release',slug:'Initial'};
 const m=String(s).match(/(\d+)/);const n=m?m[1]:'1';return{en:'Retest '+n,slug:'Retest_'+n}}

// The register records each parameter as either "Conforms" (in-house determination) or a
// CNP certificate reference (the determination was made by the external laboratory and is
// carried into this certificate). Anything else leaves the parameter open.
function readRes(v){v=String(v||'').trim();
 if(/^conforms/i.test(v))return{ok:true,src:'in-house',ref:''};
 const m=/^CNP\s+(\S+)/.exec(v);if(m)return{ok:true,src:'CNP',ref:m[1]};
 return{ok:false,src:'',ref:''}}

function build(rec,meta){
  meta=meta||{};
  const rl=roundLabel(rec.series);
  const A=readRes(rec.identA),B=readRes(rec.identB),F=readRes(rec.fm);
  const conforms=A.ok&&B.ok&&F.ok;
  // Both batch fields are codes, not prose: the v44 register writes sentences such as
  // "N/A \u2014 no P batch assigned" or "\u2014 not recorded \u2014 (P160022)" into them, which must not print
  // where a batch number belongs.
  const clean=v=>{const s=String(v||'').trim();return /^N\/A|^\u2014|not recorded|not assigned|^$/i.test(s)?'':s};
  const lot=clean(rec.p), cult=clean(rec.cu);
  const grade=/^[IVX]+$/.test(String(meta.grade||'').trim())?meta.grade:'';
  // Phenotype and processing are only ticked when the batch record actually states them.
  // 65 of the register's batches have no cultivar record on file; for those all boxes stay
  // open rather than defaulting to Hybrid / Hand, which would assert an unrecorded fact.
  const ph=String(meta.phenotype||'').toUpperCase();
  const knownPh=/INDICA|SATIVA|HYBRID/.test(ph);
  const isInd=/INDICA/.test(ph),isSat=/SATIVA/.test(ph),isHyb=knownPh&&/HYBRID/.test(ph);
  const proc=String(meta.processing||'').toUpperCase();
  const knownProc=/MACHINE|HAND/.test(proc);
  const isMach=knownProc&&/MACHINE/.test(proc),isHand=knownProc&&!isMach;
  const tested=rec.tested||'';
  // product specification code, from the cultivar's batch record; blank where none is on file
  const rawSpec=String(meta.specCode||'').trim();
  const specCode=(!rawSpec||/\u2014|not assigned|^n\/a/i.test(rawSpec))?'\u2014':rawSpec;
  const cnpRefs=[['Ident. A',A],['Ident. B',B],['Foreign matter',F]]
    .filter(function(x){return x[1].src==='CNP'}).map(function(x){return x[0]+' \u2014 '+x[1].ref});

  // Section 02 rows
  const order=['1','2','7'];const R={'1':A,'2':B,'7':F};
  const massSel=F.ok?pickMass():-1;
  // Attribution follows the register, not a constant: on 23 certificates every determination in
  // scope was made by the external CNP laboratory and carried in, so claiming in-house testing
  // would be a false statement of who performed the work.
  const nCarried=cnpRefs.length, nScope=3;
  const attrib=nCarried===0
   ?' Testing performed <strong>in-house</strong> under an ISO/IEC 17025-aligned system within the MK GMP facility.'
   :(nCarried===nScope
     ?' The determinations in scope were performed by the <strong>external contract laboratory</strong> and are carried into this certificate under the references given above; no in-house determination is claimed for them.'
     :' Parameters marked <em>In-house</em> above were performed in the Purely Plant QC laboratory under an ISO/IEC 17025-aligned system within the MK GMP facility; those marked <em>carried</em> were performed by the external contract laboratory and are carried into this certificate.');
  const title='Purely Plant \u2014 Internal Certificate of Analysis \u2014 '+rec.code+' \u2014 '+rec.strain+' \u2014 Ident. A \u00b7 Ident. B \u00b7 Foreign Matter \u2014 '+rl.en;
  const html='<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n<title>'+esc(title)+'</title>\n'
+'<link href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400;1,500&family=Roboto+Mono:wght@400;500;600;700&family=Orbitron:wght@500;600;700;800;900&display=swap" rel="stylesheet">\n'
+'<link rel="stylesheet" href="../_icoa.css">\n<link rel="stylesheet" href="../_coq-rules.css">\n<link rel="stylesheet" href="../_icoa3-print.css">\n<style id="__om-edit-overrides"></style>\n</head>\n<body>\n<div class="page">\n'
+'<div class="header-bar">\n<img class="hb-logo" src="../_logo.svg" alt="Purely Plant">\n'
+'<div class="hb-center"><div class="hb-title">Certificate of Analysis</div><div class="hb-mk-title">\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442 \u0437\u0430 \u0430\u043d\u0430\u043b\u0438\u0437\u0430</div><div class="hb-sub">Intermediate Bulk \u2014 Dry Cannabis Flower for Medical Use</div><div class="hb-mk-sub">\u0418\u043d\u0442\u0435\u0440\u043c\u0435\u0434\u0438\u0435\u0440 \u0431\u0430\u043b\u043a \u2014 \u0441\u0443\u0432 \u0446\u0432\u0435\u0442 \u043e\u0434 \u043a\u0430\u043d\u0430\u0431\u0438\u0441 \u0437\u0430 \u043c\u0435\u0434\u0438\u0446\u0438\u043d\u0441\u043a\u0430 \u0443\u043f\u043e\u0442\u0440\u0435\u0431\u0430</div></div>\n'
+'<div class="hb-right"><div class="hb-code-lbl">Document ID <span class="mk">\u041a\u043e\u0434 \u043d\u0430 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442</span></div><div class="hb-code">'+esc(rec.code)+'</div><div class="hb-issue">Issued \u00b7 \u0418\u0437\u0434\u0430\u0434\u0435\u043d <b>'+esc(rec.issued)+'</b></div></div>\n</div>\n'
+'<div class="sec-label"><span class="sec-no">01</span> Cultivar, Batch &amp; Sample Identification <span class="mk">\u0421\u043e\u0440\u0442\u0430, \u0441\u0435\u0440\u0438\u0458\u0430 \u0438 \u0438\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0458\u0430 \u043d\u0430 \u043f\u0440\u0438\u043c\u0435\u0440\u043e\u043a</span></div>\n'
+'<div class="pb-main"><span class="pb-name"><span style="font-family:\'Roboto Mono\',monospace">'+esc(lot||cult)+'</span> <i class="bisep" style="font-size:.7em">|</i> <span style="font-weight:800;text-transform:uppercase">'+esc(rec.strain)+'</span></span>'+'</div>\n'
+'<div class="selrow">\n<span class="grp"><span class="lk-lbl">Phenotype <span class="mk">\u0424\u0435\u043d\u043e\u0442\u0438\u043f</span></span>'+chip(isHyb,'Hybrid')+'<span class="stack">'+chip(isInd,'Indica')+chip(isSat,'Sativa')+'</span></span>\n'
+'<span class="grp"><span class="lk-lbl">Chemotype <span class="mk">\u0425\u0435\u043c\u043e\u0442\u0438\u043f</span></span><span class="stack">'+chip(true,'THC')+chip(false,'CBD')+'</span></span>\n'
+'<span class="grp"><span class="lk-lbl">Processing <span class="mk">\u041e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0430</span></span><span class="stack">'+chip(isMach,'Machine','\u041c\u0430\u0448\u0438\u043d\u0441\u043a\u0430')+chip(isHand,'Hand')+'</span></span>\n</div>\n'
+'<div class="goldrule"></div>\n'
+'<div class="gridrow lk-inline g3">\n'
+'<span class="lk"><span class="lk-lbl">Production Batch \u2116<span class="mk">\u041f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u043d\u0430 \u0441\u0435\u0440\u0438\u0458\u0430 \u2116</span></span><span class="lk-val">'+esc(lot||'\u2014')+'</span></span>\n'
+'<span class="lk"><span class="lk-lbl">Cultivation Batch \u2116<span class="mk">\u0421\u0435\u0440\u0438\u0458\u0430 \u043d\u0430 \u043a\u0443\u043b\u0442\u0438\u0432\u0430\u0446\u0438\u0458\u0430 \u2116</span></span><span class="lk-val">'+esc(cult||'\u2014')+'</span></span>\n'
+'<span class="lk"><span class="lk-lbl">Monograph<span class="mk">\u041c\u043e\u043d\u043e\u0433\u0440\u0430\u0444\u0438\u0458\u0430</span></span><span class="lk-val sm">Ph. Eur. mon. 3028</span></span>\n</div>\n'
+'<div class="goldrule"></div>\n'
+'<div class="gridrow lk-inline g3">\n'
+'<span class="lk"><span class="lk-lbl">Examined on<span class="mk">\u0418\u0441\u043f\u0438\u0442\u0430\u043d\u043e \u043d\u0430</span></span><span class="lk-val sm">'+esc(tested||'\u2014')+'</span></span>\n'
+'<span class="lk"><span class="lk-lbl">Packaging<span class="mk">\u0414\u0430\u0442\u0443\u043c \u043d\u0430 \u043f\u0430\u043a\u0443\u0432\u0430\u045a\u0435</span></span><span class="lk-val sm">'+esc(rec.packaging||'\u2014')+'</span></span>\n'
+'<span class="lk"><span class="lk-lbl">Product Specification \u2116<span class="mk">\u0421\u043f\u0435\u0446\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0458\u0430 \u043d\u0430 \u043f\u0440\u043e\u0438\u0437\u0432\u043e\u0434 \u2116</span></span><span class="lk-val sm">'+esc(specCode)+'</span></span>\n</div>\n'
+'<div class="goldrule"></div>\n'
+'<div class="disp-note" style="padding-top:2px"><i>Cannabis flos.</i> \u00b7 Ph. Eur. 11.5 mon. 3028 \u00b7 Intermediate Bulk \u00b7 Examined on the dried bulk <strong>before packaging began</strong>; issued after review. <span class="mk">\u0418\u0441\u043f\u0438\u0442\u0430\u043d\u043e \u043f\u0440\u0435\u0434 \u043f\u043e\u0447\u0435\u0442\u043e\u043a \u043d\u0430 \u043f\u0430\u043a\u0443\u0432\u0430\u045a\u0435\u0442\u043e.</span></div>\n'
+'<div class="sec-label"><span class="sec-no">02</span> Analytical Methods <span class="mk">\u0410\u043d\u0430\u043b\u0438\u0442\u0438\u0447\u043a\u0438 \u043c\u0435\u0442\u043e\u0434\u0438</span></div>\n'
+paramPanels(R,massSel)+'\n'
+'<div class="sec-label"><span class="sec-no">03</span> Findings \u2014 Per-Analysis Observation Record <span class="mk">\u041d\u0430\u0458\u0434\u0435\u043d\u0438 \u0440\u0435\u0437\u0443\u043b\u0442\u0430\u0442\u0438 \u2014 \u043b\u0438\u0441\u0442\u0430 \u0437\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430</span></div>\n'
+'<div class="fnd">\n'+findings(rec.code,A.ok,B.ok,F.ok,rec.strain,ph)+'\n</div>\n'
+'<div class="sec-label"><span class="sec-no">04</span> Results, Acceptance Criteria &amp; Disposition <span class="mk">\u0420\u0435\u0437\u0443\u043b\u0442\u0430\u0442\u0438, \u043a\u0440\u0438\u0442\u0435\u0440\u0438\u0443\u043c\u0438 \u0438 \u043e\u0434\u043b\u0443\u043a\u0430</span></div>\n'
+resultTable(R,massSel)+'\n'
+'<div class="disp-note"><span class="disp-lead">'+(conforms?chip(true,'Conforms','\u0421\u043e\u043e\u0434\u0432\u0435\u0442\u0441\u0442\u0432\u0443\u0432\u0430'):'<span class="chip-sel"><span class="bx">\u2612</span> Pending <span class="mk">\u0412\u043e \u0442\u0435\u043a</span></span>')+'</span>'+(conforms
 ?'The tested sample <strong>conforms</strong> to the compendial requirements for <strong>Identification A</strong>, <strong>Identification B</strong> and <strong>Foreign Matter</strong> per Ph. Eur. 11.5 Monograph 3028, general chapters 2.8.23 and 2.8.2 \u2014 foreign matter <strong>absent</strong> from the examined portion, against a \u2264 2.0% criterion.'
 :'One or more parameters within this scope are <strong>not recorded</strong> for this batch; no conformity statement is made for them.')
+' <b>\u2612</b> marks the outcome recorded for this batch and <b>\u2610</b> the alternatives available to the analyst. Macroscopic descriptors follow the cultivar\u2019s profile; the microscopic detection set and the foreign-matter conformity statements are the same for every batch. No material was separated from the examined portion, so there was nothing to weigh; the mass field stays blank until a figure exists.'+' Results relate only to the sample as received; this report may be reproduced only in full. Out-of-specification results are handled under the site quality system, and a retention sample is held. <span class="mk">\u0420\u0435\u0437\u0443\u043b\u0442\u0430\u0442\u0438\u0442\u0435 \u0441\u0435 \u043e\u0434\u043d\u0435\u0441\u0443\u0432\u0430\u0430\u0442 \u0441\u0430\u043c\u043e \u043d\u0430 \u043f\u0440\u0438\u043c\u0435\u043d\u0438\u043e\u0442 \u043f\u0440\u0438\u043c\u0435\u0440\u043e\u043a; \u0438\u0437\u0432\u0435\u0448\u0442\u0430\u0458\u043e\u0442 \u0441\u0435 \u0440\u0435\u043f\u0440\u043e\u0434\u0443\u0446\u0438\u0440\u0430 \u0441\u0430\u043c\u043e \u0432\u043e \u0446\u0435\u043b\u043e\u0441\u0442.</span></div>\n'
+'<div class="approval-grid cols-3">\n'
+'<div><div class="ap-role">Analysis Performed by <span class="mk">\u0410\u043d\u0430\u043b\u0438\u0437\u0438\u0440\u0430\u043b</span></div><div class="ap-sign"><div class="ap-line"></div></div><div class="ap-title">Analyst \u00b7 QC Laboratory <span class="mk">\u0410\u043d\u0430\u043b\u0438\u0442\u0438\u0447\u0430\u0440</span></div><div class="ap-name">Hristina Cekikj</div><div class="ap-cred">QC Laboratory</div><div class="ap-date-row"><span class="ap-date-label">Date \u00b7 \u0414\u0430\u0442\u0443\u043c</span><span class="ap-date-val">'+esc(rec.issued)+'</span></div></div>\n'
+'<div><div class="ap-role">Reviewed by <span class="mk">\u041f\u0440\u0435\u0433\u043b\u0435\u0434\u0430\u043b</span></div><div class="ap-sign"><div class="ap-line"></div></div><div class="ap-title">QA Manager <span class="mk">\u041c\u0435\u043d\u0430\u045f\u0435\u0440 \u0437\u0430 \u041e\u041a</span></div><div class="ap-name">Jovana Romevska Cvetkovski</div><div class="ap-cred">Master Pharmacist</div><div class="ap-date-row"><span class="ap-date-label">Date \u00b7 \u0414\u0430\u0442\u0443\u043c</span><span class="ap-date-val">'+esc(rec.issued)+'</span></div></div>\n'
+'<div><div class="ap-role">Approved by <span class="mk">\u041e\u0434\u043e\u0431\u0440\u0438\u043b</span></div><div class="ap-sign"><div class="ap-line"></div></div><div class="ap-title">QC Manager <span class="mk">\u041c\u0435\u043d\u0430\u045f\u0435\u0440 \u0437\u0430 \u041a\u041a</span></div><div class="ap-name">Blagoj Nikolov</div><div class="ap-cred">M.Pharm \u00b7 Drug Quality Control Specialist</div><div class="ap-date-row"><span class="ap-date-label">Date \u00b7 \u0414\u0430\u0442\u0443\u043c</span><span class="ap-date-val">'+esc(rec.issued)+'</span></div></div>\n'
+'</div>\n'

+'<div class="footer">\n<div class="foot-left">Purely Plant DOOEL \u00b7 Industriska ulica 9, br. 9,<br>Kojlija 1043 \u00b7 Petrovec-Skopje, North Macedonia</div>\n<div class="foot-center-num">1 <span style="opacity:.6">|</span> 1</div>\n<div class="foot-right"></div>\n</div>\n</div>\n</body>\n</html>\n';
  const safe=s=>String(s||'').replace(/&/g,'and').replace(/[\/\\:*?"<>|]/g,'-').replace(/\s+/g,'_');
  const dir=/initial/i.test(rec.series)?'INITIAL':'RETEST';
  const sc=String(meta.strainCode||rec.strain.split(/\s+/).map(function(w){return w[0]}).join('')).toUpperCase();
  const file=safe(rec.code)+'_'+safe(lot||cult)+'_'+sc+'_'+safe(rec.strain)+'_'+rl.slug+'.html';
  return {path:'Final_Docs/xCOAs/CoX_DES/ISSUE_iCOA/'+dir+'/'+file,html:html,dir:dir,conforms:conforms,cnp:cnpRefs.length>0};
}
return build;
})()