"use strict";
var D = JSON.parse(document.getElementById("qc-data").textContent);
var OV; try { OV = JSON.parse(document.getElementById("qc-overlay").textContent); }
catch (e) { OV = null; }
if (!OV || typeof OV !== "object") OV = {};
OV.v = OV.v || 1;
OV.batches = OV.batches || []; OV.ecoa = OV.ecoa || [];
OV.attach = OV.attach || {}; OV.icoa = OV.icoa || {};
OV.issue = OV.issue || {}; OV.log = OV.log || [];
var DET = {}; D.dets.forEach(function(d){ DET[d.no] = d; });

function esc(s){ return String(s == null ? "" : s)
  .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }
function el(id){ return document.getElementById(id); }
function dash(s){ return (s == null || s === "" || s === "—") ? '<span class="dim">—</span>' : esc(s); }

/* ---------- the desk overlay, applied to the baseline before anything renders ----------
   The baseline JSON is the build's output and is never modified; everything the desk
   records lives in OV and is re-applied here on every load. */
function coqKey(c){ return c.cb + "|" + (c.t.indexOf("additional") === 0 ? "R" : "I"); }
OV.batches.forEach(function(b){
  var due = plusYear(b.date);
  var mkRows = function(reissue){
    return D.dets.map(function(d){
      var st, route = "";
      if (d.src === "upon_request") st = "upon request — not required for release";
      else if (reissue) {
        if (d.no === "1" || d.no === "2" || d.no === "3" || d.no === "7") {
          st = "to be performed — see route";
          route = d.no === "7" ? "Purely Plant laboratory — iCoA covering Foreign matter"
                               : "Farmahem — Ident A + B + C with the Assay, at retest";
        }
        else if (d.no === "4" || d.no === "5" || d.no === "6")
          st = "awaiting the cannabinoid re-analysis — Farmahem, with Ident A + B + C";
        else if (d.no.indexOf("10.") === 0)
          st = "awaiting the mycotoxin re-analysis — Farmahem";
        else st = "outside the retest scope — the release determination stands on the batch's initial CoQ (number assigned on issue)";
      }
      else if (d.no === "1" || d.no === "2" || d.no === "7") {
        st = "to be performed — see route";
        route = d.no === "7" ? "Purely Plant laboratory — iCoA covering Foreign matter"
                             : "Purely Plant laboratory — iCoA covering Ident A + B";
      }
      else if (d.no === "3") {
        st = "to be performed — see route";
        route = "outside laboratory — Ident C (CNP Ident C only, or Farmahem with the retest)";
      }
      else st = "not tested — no certificate covers it";
      return { no: d.no, crit: d.crit, res: "—", doc: "—", dd: "", lab: "",
               fam: "", st: st, route: route, also: "" };
    });
  };
  var base = { pp: b.pn || "", cb: b.cb, strain: b.strain, grade: "", cls: "",
               ic: "(assigned on issue)", thc: "", spec: "", conflict: "",
               reg: false, desk: true };
  D.coqs.push(Object.assign({}, base, { n: "(assigned on issue)",
    t: "initial release — predicted", basis: b.date, issue: "≥ " + laterOf(D.sop_effective, b.date),
    issued: false, rows: mkRows(false) }));
  D.coqs.push(Object.assign({}, base, { n: "(assigned on issue)",
    t: "additional testing (12-month) — predicted", basis: due,
    issue: "≥ " + laterOf(D.sop_effective, due), issued: false, rows: mkRows(true) }));
  D.icoa_plan.push({ pp: b.pn || "", cb: b.cb, strain: b.strain,
    number: "(assigned on issue)", icoa_ref: "(assigned on issue)",
    coq_type: "initial release — predicted", date: "≥ " + laterOf(D.sop_effective, b.date),
    scope: "Ident A + B", determinations: "1, 2", desk: true });
  D.icoa_plan.push({ pp: b.pn || "", cb: b.cb, strain: b.strain,
    number: "(assigned on issue)", icoa_ref: "(assigned on issue)",
    coq_type: "initial release — predicted", date: "≥ " + laterOf(D.sop_effective, b.date),
    scope: "Foreign matter", determinations: "7", desk: true });
  D.icoa_plan.push({ pp: b.pn || "", cb: b.cb, strain: b.strain,
    number: "(assigned on issue)", icoa_ref: "(assigned on issue)",
    coq_type: "additional testing (12-month) — predicted",
    date: "≥ " + laterOf(D.sop_effective, due),
    scope: "Foreign matter", determinations: "7", desk: true });
  D.reg.push({ cb: b.cb, pn: b.pn || "", strain: b.strain, certs: [], desk: true });
});
OV.ecoa.forEach(function(e){
  D.ecoa.push({ date: e.date, lab: e.lab, code: e.code, batch: e.batch, ref: "",
    strain: e.strain || "", pn: "", reported: e.params ? e.params.split("·").map(function(x){ return x.trim(); }) : [],
    flag: "", verified: false, pdf: e.link || "", desk: true });
});
function plusYear(d){
  var m = /^(\d{2})\.(\d{2})\.(\d{4})$/.exec(String(d || "").trim());
  return m ? m[1] + "." + m[2] + "." + (parseInt(m[3], 10) + 1) : String(d || "");
}
function sortDate(d){
  var m = /^(\d{2})\.(\d{2})\.(\d{4})$/.exec(String(d || "").trim());
  return m ? m[3] + m[2] + m[1] : "9999";
}
function laterOf(a, b){ return sortDate(b) > sortDate(a) ? b : a; }

/* ---------- derived per-CoQ facts, computed once ---------- */
var ST = {
  OOS:  "OUT OF SPECIFICATION",
  UND:  "UNDETERMINED",
  ICOA: "to be performed",
  SCAN: "in-house CoA only",
  NONE: "not tested",
  REQ:  "upon request",
  OUT:  "outside the retest scope",
  AWK:  "awaiting the cannabinoid",
  AWM:  "awaiting the mycotoxin",
  BLK:  "BLOCKED",
  OK:   "covered"
};
function stKind(s){
  if (s.indexOf(ST.OOS) === 0 || s.indexOf(ST.BLK) === 0) return "fail";
  if (s.indexOf(ST.UND) === 0) return "warn";
  if (s.indexOf(ST.SCAN) === 0) return "fail";
  if (s.indexOf(ST.AWK) === 0 || s.indexOf(ST.AWM) === 0) return "warn";
  if (s.indexOf(ST.ICOA) === 0) return "info";
  if (s.indexOf(ST.OK) === 0) return "ok";
  return "none";
}
D.coqs.forEach(function(c, i){
  c.i = i;
  c.reissue = c.t.indexOf("additional") === 0;
  c.key = coqKey(c);
  var att = OV.attach[c.key] || {};
  c.rows.forEach(function(r){
    var a = att[r.no];
    if (!a) return;
    r.res = a.res; r.doc = a.doc; r.dd = a.date || ""; r.lab = a.lab || "";
    r.fam = "desk transcription — verify against the page";
    r.st = "covered — recorded at the desk (" + (a.by || "?") + "); verify against the page";
    r.desk = true;
  });
  var iss = OV.issue[c.key];
  if (iss) {
    c.n = iss.number; c.issued = true; c.deskIssued = true;
    c.issue = iss.date; c.issuedBy = iss.by;
  }
  c.codes = [];
  var k = { oos:0, und:0, cov:0, todo:0, none:0, scan:0, await:0 };
  c.rows.forEach(function(r){
    if (r.doc && r.doc !== "—" && c.codes.indexOf(r.doc) < 0) c.codes.push(r.doc);
    var s = r.st;
    if (s.indexOf(ST.OOS) === 0 || s.indexOf(ST.BLK) === 0) k.oos++;
    else if (s.indexOf(ST.UND) === 0) k.und++;
    else if (s.indexOf(ST.SCAN) === 0) k.scan++;
    else if (s.indexOf(ST.ICOA) === 0) k.todo++;
    else if (s.indexOf(ST.AWK) === 0 || s.indexOf(ST.AWM) === 0) k.await++;
    else if (s.indexOf(ST.NONE) === 0) k.none++;
    if (s.indexOf(ST.OK) === 0 || s.indexOf(ST.OOS) === 0 || s.indexOf(ST.UND) === 0) k.cov++;
  });
  c.k = k;
  /* an issued reissue that cites no re-analysis at all */
  c.ghost = c.reissue && c.issued && !c.codes.some(function(x){ return x.indexOf("197-") === 0; });
  /* a reissue whose Farmahem pair is already on file. A lot with no packaged lot and
     a P-number for a batch has no resolved cultivation batch, so it cannot be queued
     for issue however complete its re-analysis is. */
  c.ready = c.reissue && c.codes.some(function(x){ return x.indexOf("197-") === 0; });
  c.unresolved = c.ready && !c.issued && !c.pp && c.cb.indexOf("P0") === 0;
  if (c.unresolved) c.ready = false;
  /* an initial CoQ whose banner potency is the 12-month re-analysis, not the release assay */
  c.banner = false;
  if (!c.reissue && c.thc) {
    var a = c.rows.filter(function(r){ return r.no === "4"; })[0];
    if (a && a.res !== c.thc && a.also &&
        a.also.split("; ").some(function(x){ return x.indexOf(c.thc + " (197-") === 0; })) c.banner = true;
  }
  c.hay = [c.n, c.pp, c.cb, c.strain, c.ic, c.t, c.grade].concat(c.codes).join(" ").toLowerCase();
});
D.icoa_plan.forEach(function(p, i){
  p.i = i;
  p.reissue = p.coq_type.indexOf("additional") === 0;
  p.hay = [p.number, p.pp, p.cb, p.strain, p.icoa_ref, p.scope, p.coq_type].join(" ").toLowerCase();
});
D.ecoa.forEach(function(e, i){
  e.i = i;
  e.hay = [e.code, e.batch, e.strain, e.lab, e.pn].concat(e.reported).join(" ").toLowerCase();
});

var COQ = D.coqs, ICO = D.icoa_plan, ECO = D.ecoa;
var N = {
  init:   COQ.filter(function(c){ return !c.reissue; }).length,
  reis:   COQ.filter(function(c){ return c.reissue; }).length,
  issued: COQ.filter(function(c){ return c.issued; }).length,
  pred:   COQ.filter(function(c){ return !c.issued; }).length,
  oos:    COQ.filter(function(c){ return c.k.oos; }).length,
  und:    COQ.filter(function(c){ return c.k.und; }).length,
  noe:    COQ.filter(function(c){ return !c.reg; }).length,
  ghost:  COQ.filter(function(c){ return c.ghost; }).length,
  ready:  COQ.filter(function(c){ return c.ready && !c.issued; }).length,
  unres:  COQ.filter(function(c){ return c.unresolved; }).length,
  readyAll: COQ.filter(function(c){ return c.ready; }).length,
  banner: COQ.filter(function(c){ return c.banner; }).length,
  ab:     ICO.filter(function(p){ return p.scope.indexOf("Ident") === 0; }).length,
  fm:     ICO.filter(function(p){ return p.scope.indexOf("Foreign") === 0; }).length,
  iini:   ICO.filter(function(p){ return !p.reissue; }).length,
  irei:   ICO.filter(function(p){ return p.reissue; }).length,
  ver:    ECO.filter(function(e){ return e.verified; }).length,
  red:    ECO.filter(function(e){ return e.flag === "red"; }).length,
  amb:    ECO.filter(function(e){ return e.flag === "amber"; }).length
};
function labN(s){ return ECO.filter(function(e){ return e.lab.indexOf(s) === 0; }).length; }

/* ---------- overview ---------- */
el("gen").textContent = D.generated;
el("sop").textContent = D.sop_effective;
el("sop2").textContent = D.sop_effective;
el("n-coq").textContent = COQ.length;
el("n-icoa").textContent = ICO.length;
el("n-ecoa").textContent = ECO.length;
el("n-spec").textContent = D.dets.length;
el("coq-tail").textContent  = COQ.length + " documents · " + N.issued + " numbered, " + N.pred + " predicted";
el("icoa-tail").textContent = ICO.length + " certificates the routing requires";
el("ecoa-tail").textContent = ECO.length + " certificates received";

var SOP_EARLY = COQ.filter(function(c){ return c.issue === "≥ " + D.sop_effective; }).length;
el("kpis").innerHTML = [
  { c:"q", k:"Certificates of Quality", v:COQ.length,
    d:"One initial per batch on record, one 12-month reissue per batch.",
    s:[["numbered",N.issued],["predicted",N.pred],["initial",N.init],["reissue",N.reis]] },
  { c:"",  k:"In-house certificates owed", v:ICO.length,
    d:"What the identity and foreign-matter routing requires.",
    s:[["Ident A + B",N.ab],["foreign matter",N.fm]] },
  { c:"q", k:"Outsourced certificates on file", v:ECO.length,
    d:"Received from accredited laboratories, in issue-date order.",
    s:[["page-verified",N.ver],["red",N.red],["amber",N.amb]] },
  { c:"",  k:"Determinations per certificate", v:D.dets.length,
    d:"QCSP 001 v.03 section 02, verbatim. Ten of them are in the retest scope.",
    s:[["upon request",D.dets.filter(function(d){return d.src==="upon_request";}).length]] },
  { c:"q", k:"Issuable from " + D.sop_effective, v:SOP_EARLY,
    d:"The rest are bound later by a cited document or a 12-month due date.",
    s:[["bound later",COQ.length - SOP_EARLY]] },
  { c:"",  k:"Schedule rows", v:COQ.length * D.dets.length,
    d:"Every determination on every certificate, with the document behind it.",
    s:[["with a certificate", COQ.reduce(function(a,c){ return a + c.k.cov; },0)]] }
].map(function(x){
  return '<div class="kpi ' + x.c + '"><span class="k">' + esc(x.k) + '</span>' +
    '<div class="v">' + x.v.toLocaleString("en-GB") + '</div>' +
    '<div class="d">' + esc(x.d) + '</div><div class="split">' +
    x.s.map(function(p){ return '<span class="sp">' + esc(p[0]) + ' <b>' + p[1] + '</b></span>'; }).join("") +
    '</div></div>';
}).join("");

el("findings").innerHTML = [
  [N.oos, "certificates carry an out-of-specification determination", "fail",
   "All of them TYMC, against ≤ 10⁴ CFU/g read with the pharmacopoeial maximum acceptable count of 20 000. A deviation record is owed on each."],
  [N.und, "carry an undetermined determination", "warn",
   "TYMC between the printed 10⁴ and its maximum acceptable count of 20 000: conforming under Ph. Eur. 5.1.4, over under QCSP 001 read as written, which states no maximum. QA to determine which governs."],
  [N.noe, "have no outsourced certificate on file for the cultivation batch at all", "fail",
   "Their values come from the in-house CoA transcription, whose own footnote attributes the testing to accredited laboratories. Locate the physical certificates, scan and upload."],
  [N.ghost, "issued reissue certificates cite no 12-month re-analysis", "warn",
   "The plan records the retest date; the Farmahem certificate never reached the file. Same defect class, one step later."],
  [N.ready, "predicted reissues already have their Farmahem pair on file", "info",
   "The cannabinoid and mycotoxin half is certified. Identity and foreign matter are still outstanding on every one — first in the queue, not issuable."],
  [N.unres, "re-analysed lot cannot be queued at all: its cultivation batch is unresolved", "fail",
   "P060332 has both Farmahem panels on file, but the batch behind it — CC012601/1, per the certificate table — is in no register and no issue plan, and nothing else exists for it anywhere: no identity, foreign matter, loss on drying, heavy metals, pesticides or microbiology. A certificate of quality cannot be issued for material whose identity is unresolved."],
  [N.banner, "initial certificates would print the 12-month re-analysis as banner potency", "warn",
   "Not the release assay. Defensible only because no CoQ may now issue before " + D.sop_effective + " and a certificate speaks as of its date of issue — but a decision to take knowingly."]
].map(function(f){
  return '<p class="note"><span class="pill p-' + f[2] + '" style="font-family:var(--m);font-weight:700;font-size:11px">' +
    f[0] + '</span> <b>' + esc(f[1]) + '.</b> ' + esc(f[3]) + '</p>';
}).join("");

/* microbiology board */
var MICRO = [
  ["9.1","≤ 10⁵ CFU/g","≤ 10⁵ CFU/g (max 200 000)","correct","0","ok"],
  ["9.2","≤ 10⁴ CFU/g","≤ 10⁴ CFU/g (max 20 000)","correct","9 — 5 over the maximum, 4 undetermined","ok"],
  ["9.3","≤ 10⁴ CFU/g","≤ 10⁴ CFU/g (max 20 000)","correct · unit fixed","0","ok"],
  ["9.4","absence / 25 g","Absent","correct · absolute","0","ok"],
  ["9.5","absence / 1 g","Absent","correct · absolute","0","ok"],
  ["9.6","absence / 1 g","upon request","correct · not a release criterion","—","ok"],
  ["9.7","absence / 1 g","upon request","correct · not a release criterion","—","ok"]
];
document.querySelector("#micro tbody").innerHTML = MICRO.map(function(m){
  var d = DET[m[0]] || {};
  return "<tr><td class=\"c num\">" + m[0] + "</td>" +
    "<td><span class=\"nm\">" + esc(d.en || "") + "</span><span class=\"sub mk\">" + esc(d.mk || "") + "</span></td>" +
    "<td class=\"mono\">" + esc(m[1]) + "</td><td class=\"mono\">" + esc(m[2]) + "</td>" +
    "<td><span class=\"pill p-" + m[5] + "\">" + esc(m[3]) + "</span></td>" +
    "<td class=\"mono\">" + esc(m[4]) + "</td></tr>";
}).join("");

/* ---------- filters ---------- */
var F = { coq:new Set(), icoa:new Set(), ecoa:new Set(), reg:new Set() };
var Q = { coq:"", icoa:"", ecoa:"", reg:"" };
var OPEN = null;

function passCoq(c){
  var f = F.coq;
  if (Q.coq && c.hay.indexOf(Q.coq) < 0) return false;
  if (f.size === 0) return true;
  var any = false;
  f.forEach(function(x){
    if (x === "initial"   && !c.reissue) any = true;
    if (x === "reissue"   &&  c.reissue) any = true;
    if (x === "issued"    &&  c.issued)  any = true;
    if (x === "predicted" && !c.issued)  any = true;
    if (x === "oos"       &&  c.k.oos)   any = true;
    if (x === "undet"     &&  c.k.und)   any = true;
    if (x === "noecoa"    && !c.reg)     any = true;
    if (x === "ghost"     &&  c.ghost)   any = true;
    if (x === "banner"    &&  c.banner)  any = true;
    if (x === "ready"     &&  c.ready)   any = true;
    if (x === "unres"     &&  c.unresolved) any = true;
  });
  return any;
}
function passIcoa(p){
  var f = F.icoa;
  if (Q.icoa && p.hay.indexOf(Q.icoa) < 0) return false;
  if (f.size === 0) return true;
  var any = false;
  f.forEach(function(x){
    if (x === "ab"      && p.scope.indexOf("Ident") === 0)   any = true;
    if (x === "fm"      && p.scope.indexOf("Foreign") === 0) any = true;
    if (x === "initial" && !p.reissue) any = true;
    if (x === "reissue" &&  p.reissue) any = true;
  });
  return any;
}
function passEcoa(e){
  var f = F.ecoa;
  if (Q.ecoa && e.hay.indexOf(Q.ecoa) < 0) return false;
  if (f.size === 0) return true;
  var any = false;
  f.forEach(function(x){
    if (x === "iph" && e.lab.indexOf("IPH") === 0) any = true;
    if (x === "cnp" && e.lab.indexOf("UKIM") === 0) any = true;
    if (x === "fhm" && e.lab.indexOf("Farmahem") === 0) any = true;
    if (x === "pp"  && e.lab.indexOf("Purely") === 0) any = true;
    if (x === "ver" && e.verified) any = true;
    if (x === "red" && e.flag === "red") any = true;
    if (x === "amber" && e.flag === "amber") any = true;
  });
  return any;
}

/* ---------- renderers ---------- */
function coqFlags(c){
  var out = [];
  if (c.k.oos)  out.push('<span class="pill p-fail">' + c.k.oos + ' out of specification</span>');
  if (c.k.und)  out.push('<span class="pill p-warn">' + c.k.und + ' undetermined</span>');
  if (!c.reg)   out.push('<span class="pill p-fail">no eCoA on file</span>');
  if (c.ghost)  out.push('<span class="pill p-warn">retest certificate missing</span>');
  if (c.banner) out.push('<span class="pill p-warn">banner = re-analysis</span>');
  if (c.ready && !c.issued) out.push('<span class="pill p-info">re-analysis on file</span>');
  if (c.unresolved) out.push('<span class="pill p-fail">cultivation batch unresolved</span>');
  if (c.conflict) out.push('<span class="pill p-warn">grade range vs QCSP 001</span>');
  return out.join(" ") || '<span class="dim">—</span>';
}
function renderCoqs(){
  var list = COQ.filter(passCoq);
  document.querySelector("#t-coqs tbody").innerHTML = list.map(function(c){
    return '<tr class="clk' + (OPEN === c.i ? " sel" : "") + '" data-c="' + c.i + '">' +
      '<td class="mono"' + (c.issued ? ' style="font-weight:700;color:var(--navy)"' : ' class="mono dim"') + '>' + esc(c.n) + '</td>' +
      '<td><span class="tag ' + (c.issued ? "t-issued" : "t-pred") + '">' + (c.issued ? "numbered" : "predicted") + '</span>' +
        '<span class="sub">' + (c.reissue ? "12-month reissue" : "initial release") + '</span></td>' +
      '<td class="mono dim">' + esc(c.basis) + '</td>' +
      '<td class="mono">' + esc(c.issue) + '</td>' +
      '<td class="mono">' + dash(c.pp) + '</td><td class="mono">' + esc(c.cb) + '</td>' +
      '<td><span class="nm">' + esc(c.strain) + '</span><span class="sub">' +
        (c.grade ? '<span class="grade">' + esc(c.grade) + '</span> ' : "") +
        (c.thc ? esc(c.thc) + ' % Δ⁹-THC' : '<span class="dim">no grade assigned yet</span>') + '</span></td>' +
      '<td class="mono dim">' + esc(c.ic) + '</td>' +
      '<td class="c num">' + c.k.cov + '</td>' +
      '<td class="c num">' + (c.k.todo + c.k.await + c.k.scan) + '</td>' +
      '<td>' + coqFlags(c) + '</td></tr>';
  }).join("");
  el("cnt-coq").textContent = list.length + " of " + COQ.length + " certificates";
  el("e-coq").classList.toggle("hide", list.length > 0);
}
function renderDetail(){
  var box = el("coq-detail");
  if (OPEN == null) { box.innerHTML = ""; return; }
  var c = COQ[OPEN];
  var lastGroup = "";
  var body = c.rows.map(function(r){
    var d = DET[r.no] || {};
    var head = "";
    if (d.group && d.group !== lastGroup) {
      lastGroup = d.group;
      head = '<tr class="grp"><td colspan="7">' + esc(d.group) + '</td></tr>';
    }
    var kind = stKind(r.st);
    return head + '<tr><td class="c num">' + esc(r.no) + '</td>' +
      '<td><span class="nm">' + esc(d.en || "") + '</span><span class="sub mk">' + esc(d.mk || "") + '</span></td>' +
      '<td class="mono dim" style="white-space:normal">' + esc(d.method || "") + '</td>' +
      '<td class="mono" style="white-space:normal">' + esc(r.crit) + '</td>' +
      '<td class="num c">' + dash(r.res) + '</td>' +
      '<td>' + (r.doc && r.doc !== "—"
        ? '<span class="src' + (r.fam && r.fam.indexOf("Farmahem") >= 0 ? " q" : "") + '">' + esc(r.doc) + '</span>' +
          '<span class="sub">' + esc(r.dd) + (r.lab ? ' · ' + esc(r.lab.split(" — ")[0]) : "") + '</span>'
        : '<span class="dim">—</span>') + '</td>' +
      '<td><span class="pill p-' + kind + '">' + esc(r.st) + '</span>' +
        (r.route ? '<span class="sub">' + esc(r.route) + '</span>' : "") +
        (r.also ? '<span class="sub dim">also on file: ' + esc(r.also) + '</span>' : "") + '</td></tr>';
  }).join("");
  var notes = [];
  if (!c.reg) notes.push("<b>No outsourced certificate is on file for this cultivation batch.</b> Every value shown comes from the in-house CoA transcription, whose footnote attributes the testing to accredited laboratories. Locate the physical certificates, scan and upload.");
  if (c.ghost) notes.push("<b>This certificate is numbered and its retest date recorded, but no 197-series re-analysis is on file.</b> Locate and scan it before issue.");
  if (c.banner) notes.push("<b>The banner potency is the 12-month re-analysis, not the release assay.</b> The master spec carries the newest result; the certificate speaks as of its date of issue, which cannot precede " + D.sop_effective + ". A decision to take knowingly.");
  if (c.unresolved) notes.push("<b>The Farmahem pair is on file, but this lot cannot be queued for issue.</b> The batch behind it — CC012601/1, per the certificate table — is in no register and no issue plan, and nothing else exists for it anywhere: no identity, foreign matter, loss on drying, heavy metals, pesticides or microbiology. Resolve the identity first.");
  if (c.ready && !c.issued) notes.push("<b>The Farmahem pair is on file ahead of the 12-month date</b> — the cannabinoid and mycotoxin half is certified. Identity and foreign matter are still to perform, so this is first in the queue, not issuable.");
  if (c.conflict) notes.push("<b>Grade range conflict.</b> " + c.conflict);
  if (c.reissue) notes.push("Ten determinations are in the retest scope; the other eleven read <i>outside the retest scope</i> and stand on this batch's initial certificate.");
  /* determinations still uncertified, in this CoQ's scope */
  var open_dets = c.rows.filter(function(r){
    return r.st.indexOf("to be performed") === 0 || r.st.indexOf("not tested") === 0 ||
           r.st.indexOf("awaiting") === 0 || r.st.indexOf("in-house CoA only") === 0;
  }).map(function(r){ return r.no; });
  var deskHtml = "";
  if (!c.deskIssued) {
    deskHtml = '<div class="desk" style="margin:12px;max-width:none" data-desk="1">' +
      '<h3>Compile — attach a received certificate to a determination</h3><div class="frm">' +
      '<span class="fld"><label>Determination</label><select id="att-no">' +
      open_dets.map(function(no){
        var d = DET[no] || {};
        return '<option value="' + esc(no) + '">' + esc(no + " — " + (d.en || "")) + '</option>';
      }).join("") + '</select></span>' +
      '<span class="fld"><label>Certificate code (from the receipt register)</label>' +
      '<input id="att-doc" list="ecoa-codes" placeholder="ППК… / nnn/nnnn/nn / 197-…"></span>' +
      '<span class="fld"><label>Result, exactly as printed</label><input id="att-res" placeholder="verbatim"></span>' +
      '<button class="btn att-go" ' + (open_dets.length ? "" : "disabled ") + 'id="att-save">Attach</button></div>' +
      '<div class="deskmsg" id="att-msg">' + (open_dets.length
        ? "The value is a desk transcription until verified against the page."
        : "Every determination in scope is certified.") + '</div>' +
      '<datalist id="ecoa-codes">' + ECO.map(function(e){
        return '<option value="' + esc(e.code) + '">' + esc((e.batch || "") + " · " + e.lab.split(" — ")[0]) + '</option>';
      }).join("") + '</datalist></div>' +
      '<div class="desk" style="margin:12px;max-width:none" data-desk="1">' +
      '<h3>Issue — assign the number and date</h3><div class="frm">' +
      '<span class="fld"><label>CoQ number</label><input id="iss-num" placeholder="CoQ-PP-2026-NNNN"' +
        (c.issued ? ' value="' + esc(c.n) + '" readonly' : '') + '></span>' +
      '<span class="fld"><label>Date of issue</label><input id="iss-date" placeholder="dd.mm.yyyy"></span>' +
      '<button class="btn gold iss-go" id="iss-save"' + (open_dets.length ? " disabled" : "") + '>Record issuance</button></div>' +
      '<div class="deskmsg" id="iss-msg">' + (open_dets.length
        ? open_dets.length + " determination" + (open_dets.length === 1 ? " is" : "s are") +
          " still uncertified (" + open_dets.join(", ") + ") — a CoQ must never carry a conformity assertion that has not been certified, so issuance is locked until each is covered."
        : "All in scope certified. The printed date may be no earlier than " + c.issue.replace("≥ ", "") + ".") + '</div></div>';
  } else {
    deskHtml = '<div class="d-note"><b>Issued at this desk</b> as ' + esc(c.n) + " on " + esc(c.issue) +
      (c.issuedBy ? " by " + esc(c.issuedBy) : "") + ". An issued certificate is final: a correction is a new document.</div>";
  }
  box.innerHTML = '<div class="detail"><div class="d-head"><div>' +
    '<div class="d-name">' + esc(c.strain) + (c.thc ? '<span class="d-pot">' + esc(c.thc) + ' %</span>' : "") + '</div>' +
    '<div class="d-meta">' +
      lk("CoQ number", c.n) + lk("Series", c.reissue ? "12-month reissue" : "initial release") +
      lk("Basis date", c.basis) + lk("Issue no earlier than", c.issue) +
      lk("Packaged lot", c.pp || "—") + lk("Cultivation batch", c.cb) +
      lk("Grade", c.grade ? c.grade + " · THC " + c.cls : "—") +
      lk("iCoA reference", c.ic) + lk("Spec. ref.", c.spec || "—") +
    '</div></div><button class="close" id="cl">Close</button></div>' +
    (notes.length ? '<div class="d-note">' + notes.join("<br>") + '</div>' : "") +
    '<div class="scroll"><table><thead><tr>' +
    '<th style="width:44px">№</th><th style="width:190px">Parameter<span class="mk">Параметар</span></th>' +
    '<th style="width:170px">Method / reference</th><th style="width:190px">Acceptance criterion<span class="mk">Критериум</span></th>' +
    '<th style="width:96px" class="c">Result<span class="mk">Резултат</span></th>' +
    '<th style="width:170px">Source document</th><th>Status · route</th>' +
    '</tr></thead><tbody>' + body + '</tbody></table></div>' + deskHtml + '</div>';
  el("cl").addEventListener("click", function(){ OPEN = null; renderDetail(); renderCoqs(); });
  var att = el("att-save");
  if (att) att.addEventListener("click", function(){
    var no = el("att-no").value, doc = el("att-doc").value.trim(), res = el("att-res").value.trim();
    if (!operator()) return msgIn("att-msg", "Enter your initials on the Desk log tab first.", false);
    if (!no || !doc || !res) return msgIn("att-msg", "Determination, certificate code and result are all required.", false);
    var e = ECO.filter(function(x){ return x.code === doc; })[0];
    if (!e) return msgIn("att-msg", "That code is not in the receipt register — record the certificate on the eCoA tab first.", false);
    OV.attach[c.key] = OV.attach[c.key] || {};
    if (OV.attach[c.key][no]) return msgIn("att-msg", "That determination already carries a desk attachment.", false);
    OV.attach[c.key][no] = { doc: doc, res: res, date: e.date, lab: e.lab, by: operator(), at: stamp() };
    msgIn("att-msg", "Publishing the attachment…", true);
    saveState("attach certificate", doc + " -> " + c.cb + " det " + no + " = " + res,
      null, function(m){ delete OV.attach[c.key][no]; msgIn("att-msg", m, false); });
  });
  var iss = el("iss-save");
  if (iss) iss.addEventListener("click", function(){
    var num = el("iss-num").value.trim(), date = el("iss-date").value.trim();
    if (!operator()) return msgIn("iss-msg", "Enter your initials on the Desk log tab first.", false);
    if (!/^CoQ-PP-\d{4}-\d{4}$/.test(num)) return msgIn("iss-msg", "Number must read CoQ-PP-YYYY-NNNN.", false);
    if (!DATE_RX.test(date)) return msgIn("iss-msg", "Date must be dd.mm.yyyy.", false);
    var bound = c.issue.replace("≥ ", "");
    if (sortDate(date) < sortDate(bound)) return msgIn("iss-msg", "The printed date may be no earlier than " + bound + " — the SOP floor, the newest cited document, or the 12-month due date.", false);
    var clash = COQ.some(function(x){ return x !== c && x.n === num; }) ||
      Object.keys(OV.issue).some(function(k){ return k !== c.key && OV.issue[k].number === num; });
    if (clash) return msgIn("iss-msg", "That CoQ number is already taken. One number, one document, forever.", false);
    OV.issue[c.key] = { number: num, date: date, by: operator(), at: stamp() };
    msgIn("iss-msg", "Publishing the issuance…", true);
    saveState("CoQ issuance", num + " issued " + date + " for " + c.cb +
      (c.reissue ? " (12-month reissue)" : " (initial release)"),
      null, function(m){ delete OV.issue[c.key]; msgIn("iss-msg", m, false); });
  });
  box.scrollIntoView({ block:"nearest" });
}
function lk(l, v){
  return '<span class="lk"><span class="l">' + esc(l) + '</span><span class="v">' + esc(v) + '</span></span>';
}
function icoaKey(p){
  return p.cb + "|" + p.scope + "|" + (p.coq_type.indexOf("additional") === 0 ? "R" : "I");
}
function renderIcoa(){
  var list = ICO.filter(passIcoa);
  document.querySelector("#t-icoas tbody").innerHTML = list.map(function(p, n){
    var asn = OV.icoa[icoaKey(p)];
    var coq = COQ.filter(function(c){ return c.cb === p.cb && c.reissue === p.reissue; })[0];
    var num = coq ? coq.n : p.number;
    return '<tr><td class="c dim mono">' + (n + 1) + '</td>' +
      '<td class="mono">' + esc(num) + '</td>' +
      '<td><span class="tag ' + (p.number.indexOf("CoQ-") === 0 ? "t-issued" : "t-pred") + '">' +
        (p.number.indexOf("CoQ-") === 0 ? "numbered" : "predicted") + '</span>' +
        '<span class="sub">' + (p.reissue ? "12-month reissue" : "initial release") + '</span></td>' +
      '<td class="mono">' + esc(p.date) + '</td>' +
      '<td class="mono">' + dash(p.pp) + '</td><td class="mono">' + esc(p.cb) + '</td>' +
      '<td>' + esc(p.strain) + '</td>' +
      '<td><span class="pill p-' + (p.scope.indexOf("Ident") === 0 ? "info" : "warn") + '">' + esc(p.scope) + '</span></td>' +
      '<td class="c mono">' + esc(p.determinations) + '</td>' +
      '<td class="mono' + (asn ? '" style="font-weight:700;color:var(--navy)' : ' dim') + '">' +
        esc(asn ? asn.ref : p.icoa_ref) + '</td>' +
      (asn
        ? '<td class="mono">' + esc(asn.date) + '</td><td>' + esc(asn.analyst) +
          ' <span class="desk-entry">' + esc(asn.by || "") + '</span></td>'
        : '<td colspan="2"><button class="btn sm ic-go" data-ik="' + esc(icoaKey(p)) +
          '" data-lbl="' + esc(p.scope + " — " + p.cb + " (" + num + ")") + '">Assign at the desk</button></td>') +
      '</tr>';
  }).join("");
  el("cnt-icoa").textContent = list.length + " of " + ICO.length + " in-house certificates";
  el("e-icoa").classList.toggle("hide", list.length > 0);
}
function renderEcoa(){
  var list = ECO.filter(passEcoa);
  document.querySelector("#t-ecoas tbody").innerHTML = list.map(function(e, n){
    var fam = e.lab.indexOf("Farmahem") === 0;
    return '<tr><td class="c dim mono">' + (n + 1) + '</td>' +
      '<td class="mono">' + esc(e.date || "no date") + '</td>' +
      '<td><span class="src' + (fam ? " q" : "") + '">' + esc(e.code.length > 42 ? e.code.slice(0, 40) + "…" : e.code) + '</span>' +
        '<span class="sub">' + esc(e.lab.split(" — ")[0]) + '</span></td>' +
      '<td class="mono">' + dash(e.batch) + '</td><td class="mono dim">' + dash(e.pn) + '</td>' +
      '<td>' + dash(e.strain) + '</td>' +
      '<td style="font-size:10.6px;color:var(--text-sec)">' + (e.reported.length ? esc(e.reported.join(" · ")) : '<span class="dim">—</span>') + '</td>' +
      '<td class="c">' + (e.verified ? '<span class="pill p-ok">page-read</span>' : '<span class="pill p-none">not read</span>') + '</td>' +
      '<td class="c">' + (e.flag === "red" ? '<span class="pill p-fail">red</span>'
        : e.flag === "amber" ? '<span class="pill p-warn">amber</span>' : '<span class="dim">—</span>') + '</td>' +
      '<td class="c">' + (e.pdf ? '<a href="' + esc(e.pdf) + '" target="_blank" rel="noopener">open</a>' : '<span class="dim">—</span>') + '</td></tr>';
  }).join("");
  el("cnt-ecoa").textContent = list.length + " of " + ECO.length + " certificates";
  el("e-ecoa").classList.toggle("hide", list.length > 0);
}
var SUPPLY = { outsourced_certificate:"outsourced laboratory",
               in_house_icoa:"in-house iCoA", upon_request:"upon request only" };
document.querySelector("#t-spec tbody").innerHTML = D.dets.map(function(d){
  return '<tr><td class="c num">' + esc(d.no) + '</td>' +
    '<td style="font-size:10.8px;color:var(--text-sec)">' + esc(d.group) + '</td>' +
    '<td><span class="nm">' + esc(d.en) + '</span><span class="sub mk">' + esc(d.mk) + '</span></td>' +
    '<td class="mono" style="white-space:normal">' + esc(d.method) + '</td>' +
    '<td class="mono" style="white-space:normal">' + esc(d.crit) + '</td>' +
    '<td class="c mono">' + (d.col || '<span class="dim">—</span>') + '</td>' +
    '<td><span class="pill p-' + (d.src === "in_house_icoa" ? "info" : d.src === "upon_request" ? "none" : "ok") + '">' +
      esc(SUPPLY[d.src]) + '</span></td></tr>';
}).join("");

[["c-init",N.init],["c-reis",N.reis],["c-num",N.issued],["c-pred",N.pred],["c-oos",N.oos],
 ["c-und",N.und],["c-noe",N.noe],["c-gh",N.ghost],["c-ban",N.banner],["c-rdy",N.readyAll],
 ["c-unr",N.unres], ["c-ab",N.ab],["c-fm",N.fm],["c-iini",N.iini],["c-irei",N.irei],
 ["c-iph",labN("IPH")],["c-cnp",labN("UKIM")],["c-fhm",labN("Farmahem")],["c-pp",labN("Purely")],
 ["c-ver",N.ver],["c-red",N.red],["c-amb",N.amb]
].forEach(function(p){ var n = el(p[0]); if (n) n.textContent = p[1]; });

/* ---------- wiring ---------- */
document.querySelectorAll(".tab").forEach(function(t){
  t.addEventListener("click", function(){
    document.querySelectorAll(".tab").forEach(function(x){
      var on = x === t;
      x.setAttribute("aria-selected", on ? "true" : "false");
      el("p-" + x.dataset.p).classList.toggle("hide", !on);
    });
  });
});
document.querySelectorAll(".chip[data-f]").forEach(function(b){
  b.addEventListener("click", function(){
    var parts = b.dataset.f.split(":"), set = F[parts[0]], key = parts[1];
    if (set.has(key)) set.delete(key); else set.add(key);
    b.setAttribute("aria-pressed", set.has(key) ? "true" : "false");
    if (parts[0] === "coq") { OPEN = null; renderDetail(); renderCoqs(); }
    else if (parts[0] === "icoa") renderIcoa();
    else if (parts[0] === "reg") renderReg();
    else renderEcoa();
  });
});
document.querySelectorAll("[data-clear]").forEach(function(b){
  b.addEventListener("click", function(){
    var p = b.dataset.clear;
    F[p].clear(); Q[p] = "";
    var s = el("q-" + p); if (s) s.value = "";
    document.querySelectorAll('.chip[data-f^="' + p + ':"]').forEach(function(c){
      c.setAttribute("aria-pressed", "false");
    });
    if (p === "coq") { OPEN = null; renderDetail(); renderCoqs(); }
    else if (p === "icoa") renderIcoa();
    else if (p === "reg") renderReg();
    else renderEcoa();
  });
});
[["q-coq","coq",function(){ OPEN = null; renderDetail(); renderCoqs(); }],
 ["q-icoa","icoa",renderIcoa], ["q-ecoa","ecoa",renderEcoa],
 ["q-reg","reg",renderReg]].forEach(function(p){
  el(p[0]).addEventListener("input", function(e){
    Q[p[1]] = e.target.value.trim().toLowerCase(); p[2]();
  });
});
document.querySelector("#t-coqs tbody").addEventListener("click", function(e){
  var tr = e.target.closest("tr[data-c]");
  if (!tr) return;
  var i = +tr.dataset.c;
  OPEN = (OPEN === i) ? null : i;
  renderDetail(); renderCoqs();
});

/* ---- iCoA assignment ---- */
var IC_TARGET = null;
document.querySelector("#p-icoa .controls").insertAdjacentHTML("afterend",
  '<div class="desk" id="ic-desk" data-desk="1"><h3>iCoA assignment — <span id="ic-what">pick a row below</span></h3>' +
  '<div class="frm">' +
  '<span class="fld"><label>iCoA reference</label><input id="ic-ref" placeholder="iCoA-PP-2026-NNNN"></span>' +
  '<span class="fld"><label>Date of issue</label><input id="ic-date" placeholder="dd.mm.yyyy"></span>' +
  '<span class="fld"><label>Analyst</label><input id="ic-analyst" placeholder="name"></span>' +
  '<button class="btn" id="ic-save" disabled>Record assignment</button></div>' +
  '<div class="deskmsg" id="ic-msg">Numbers are copied from this issuance record — assigning here IS the record.</div></div>');
document.querySelector("#t-icoas tbody").addEventListener("click", function(e){
  var b = e.target.closest(".ic-go");
  if (!b) return;
  IC_TARGET = b.dataset.ik;
  el("ic-what").textContent = b.dataset.lbl;
  el("ic-save").disabled = false;
  el("ic-desk").scrollIntoView({ block: "nearest" });
});
el("ic-save").addEventListener("click", function(){
  if (!IC_TARGET) return;
  var ref = el("ic-ref").value.trim(), date = el("ic-date").value.trim(),
      analyst = el("ic-analyst").value.trim();
  if (!operator()) return msgIn("ic-msg", "Enter your initials on the Desk log tab first.", false);
  if (!/^iCoA-PP-\d{4}-\d{4}$/.test(ref)) return msgIn("ic-msg", "Reference must read iCoA-PP-YYYY-NNNN.", false);
  if (!DATE_RX.test(date)) return msgIn("ic-msg", "Date must be dd.mm.yyyy.", false);
  if (sortDate(date) < sortDate(D.sop_effective)) return msgIn("ic-msg", "No document is issued before the SOP came into use, " + D.sop_effective + ".", false);
  if (!analyst) return msgIn("ic-msg", "Analyst is required.", false);
  var taken = Object.keys(OV.icoa).some(function(k){ return OV.icoa[k].ref === ref; });
  if (taken) return msgIn("ic-msg", "That iCoA number is already assigned. One number, one document, forever.", false);
  OV.icoa[IC_TARGET] = { ref: ref, date: date, analyst: analyst, by: operator(), at: stamp() };
  msgIn("ic-msg", "Publishing the assignment…", true);
  saveState("iCoA assignment", ref + " -> " + IC_TARGET.split("|").slice(0, 2).join(" "),
    null, function(m){ delete OV.icoa[IC_TARGET]; msgIn("ic-msg", m, false); });
});

renderCoqs(); renderIcoa(); renderEcoa();

/* ================= release register view =================
   The value-judging rules are ported verbatim from the published release-register
   artifact: magnitude() answers "what number is this measurement"; acceptanceLimit()
   answers "what is the largest conforming result" — for a microbial enumeration
   criterion written as a bare power of ten those are different numbers (Ph. Eur.
   5.1.4 / USP <1111>: x2 per decade). Absence criteria are absolute. */
var SUP = {"⁰":"0","¹":"1","²":"2","³":"3","⁴":"4","⁵":"5","⁶":"6","⁷":"7","⁸":"8","⁹":"9"};
function magnitude(v){
  var s = String(v == null ? "" : v).trim();
  if (!s || s === "/" || s === "—") return null;
  s = s.replace(/[⁰¹²³⁴-⁹]/g, function(c){ return "^" + SUP[c]; })
       .replace(/[хХ×✕·]/g, "x").replace(/≤/g, "<=").replace(/≥/g, ">=")
       .replace(/(\d),(\d)/g, "$1.$2");
  var m = s.match(/(\d+(?:\.\d+)?)\s*x\s*10\s*\^?\s*(\d+)/i);
  if (m) return parseFloat(m[1]) * Math.pow(10, parseInt(m[2], 10));
  m = s.match(/(?:^|[^\d.])10\s*\^\s*(\d+)/);
  if (m) return Math.pow(10, parseInt(m[1], 10));
  m = s.match(/(\d+(?:\.\d+)?)/);
  if (m && !/and|и/i.test(s)) return parseFloat(m[1]);
  return null;
}
var PH_EUR_FACTOR = 2;
var COUNTED = /tamc|tymc|cfu|gnb|gram-negative|aerobic|yeast|mould|mold/i;
function acceptanceLimit(lim, colName){
  if (lim == null) return null;
  var s = String(lim).trim();
  if (!s) return null;
  var norm = s.replace(/[⁰¹²³⁴-⁹]/g, function(c){ return "^" + SUP[c]; })
              .replace(/[хХ×✕]/g, "x").replace(/\s+/g, "");
  var m = norm.match(/^[<≤]?10\^(\d)(?!\d)/);
  if (m && COUNTED.test(String(colName || "") + " " + s))
    return PH_EUR_FACTOR * Math.pow(10, parseInt(m[1], 10));
  return magnitude(s);
}
function isProse(sv){
  /* a measurement is digits and short unit tokens; four letters running in any
     script means an annotation ("COMPLIES (numeric value not present …)"), and
     an annotation is never judged against a limit */
  return /[A-Za-zА-Яа-я]{4}/.test(sv);
}
function overLimit(v, lim, colName){
  if (!v || !lim) return false;
  var sv = String(v).trim();
  if (/^[<≤]/.test(sv)) return false;
  if (/and|и/i.test(sv)) return false;
  if (/^(n\.?d\.?|blq|absent|одговара|н\.д)/i.test(sv)) return false;
  if (isProse(sv)) return false;
  var a = magnitude(sv), b = acceptanceLimit(lim, colName);
  if (a == null || b == null) return false;
  if (!/[<≤]/.test(String(lim)) && !/max/i.test(String(lim))) return false;
  return a > b * 1.0000001;
}
function undetBand(v, lim, colName){
  if (!v || !lim) return false;
  var norm = String(lim).trim().replace(/[⁰¹²³⁴-⁹]/g, function(c){ return "^" + SUP[c]; })
    .replace(/[хХ×✕]/g, "x").replace(/\s+/g, "");
  var m = norm.match(/^[<≤]?10\^(\d)(?!\d)/);
  if (!m || !COUNTED.test(String(colName || "") + " " + String(lim))) return false;
  if (/max/i.test(String(lim))) { /* an explicit max settles the band */ }
  var printed = Math.pow(10, parseInt(m[1], 10));
  var a = magnitude(String(v).trim());
  if (a == null || /^[<≤]/.test(String(v).trim()) || isProse(String(v).trim())) return false;
  return a > printed * 1.0000001 && a <= printed * PH_EUR_FACTOR * 1.0000001;
}
D.reg.forEach(function(b, i){
  b.i = i;
  b.oos = 0; b.undet = 0; b.flags = 0;
  b.certs.forEach(function(ct){
    ct.oos = {}; ct.undet = {};
    Object.keys(ct.vals).forEach(function(L){
      var col = D.reg_columns[L] || {};
      if (ct.stab) return;
      if (overLimit(ct.vals[L], col.crit, col.name)) { ct.oos[L] = 1; b.oos++; }
      else if (undetBand(ct.vals[L], col.crit, col.name)) { ct.undet[L] = 1; b.undet++; }
    });
    b.flags += Object.keys(ct.flags).length;
  });
  b.hay = [b.cb, b.pn, b.strain].concat(b.certs.map(function(c){ return c.code; }))
    .join(" ").toLowerCase();
});
var OPENB = {};
function passReg(b){
  var f = F.reg;
  if (Q.reg && b.hay.indexOf(Q.reg) < 0) return false;
  if (f.size === 0) return true;
  var any = false;
  f.forEach(function(x){
    if (x === "oos" && b.oos) any = true;
    if (x === "undet" && b.undet) any = true;
    if (x === "flag" && b.flags) any = true;
    if (x === "desk" && b.desk) any = true;
  });
  return any;
}
function renderReg(){
  var list = D.reg.filter(passReg);
  el("bcards").innerHTML = list.map(function(b){
    var open = OPENB[b.i];
    var body = "";
    if (open) {
      body = '<div class="bc-body"><div class="scroll"><table><thead><tr>' +
        '<th style="width:170px">Certificate</th><th style="width:86px">Issued</th>' +
        '<th>Results — value against the release criterion</th></tr></thead><tbody>' +
        (b.certs.length ? b.certs.map(function(ct){
          return '<tr><td><span class="src' + (ct.fam && ct.fam.indexOf("Farmahem") >= 0 ? " q" : "") + '">' + esc(ct.code.length > 30 ? ct.code.slice(0, 28) + "…" : ct.code) + '</span>' +
            '<span class="sub">' + esc((ct.lab || "").split(" — ")[0]) + (ct.stab ? " · stability timepoint" : "") + '</span></td>' +
            '<td class="mono dim">' + esc(ct.date || "") + '</td><td>' +
            Object.keys(ct.vals).map(function(L){
              var col = D.reg_columns[L] || { name: L };
              var cls = ct.oos[L] ? " over" : (ct.undet[L] ? " undet" :
                (ct.flags[L] === "red" ? " flagR" : ct.flags[L] === "amber" ? " flagA" : ""));
              return '<span class="vchip' + cls + (ct.stab ? " stab" : "") + '"><b>' +
                esc(col.name.replace(/ CFU\/g| %| µg\/kg| mg\/kg|\/1 g|\/25 g/g, "")) + '</b>' +
                esc(ct.vals[L]) + '</span>';
            }).join("") + '</td></tr>';
        }).join("") : '<tr><td colspan="3" class="dim" style="padding:10px">No certificate recorded for this batch yet.</td></tr>') +
        '</tbody></table></div></div>';
    }
    return '<div class="bcard' + (b.oos ? " oos" : (b.undet || b.flags ? " warned" : "")) + '">' +
      '<div class="bc-head" data-b="' + b.i + '"><span class="bc-name">' + esc(b.cb) + '</span>' +
      (b.pn && b.pn !== b.cb ? '<span class="bc-pn">' + esc(b.pn) + '</span>' : "") +
      '<span class="bc-strain">' + esc(b.strain) + '</span>' +
      (b.desk ? '<span class="desk-entry">recorded at this desk</span>' : "") +
      '<span class="bc-right">' +
      (b.oos ? '<span class="pill p-fail">' + b.oos + ' over limit</span>' : "") +
      (b.undet ? '<span class="pill p-warn">' + b.undet + ' undetermined</span>' : "") +
      (b.flags ? '<span class="pill p-warn">' + b.flags + ' flagged</span>' : "") +
      '<span class="pill p-none">' + b.certs.length + ' certificate' + (b.certs.length === 1 ? "" : "s") + '</span>' +
      '</span></div>' + body + '</div>';
  }).join("");
  el("cnt-reg").textContent = list.length + " of " + D.reg.length + " batches";
  el("e-reg").classList.toggle("hide", list.length > 0);
  el("reg-tail").textContent = D.reg.length + " batches on record";
  el("n-reg").textContent = D.reg.length;
  var o = 0, u = 0, fl = 0, dk = 0;
  D.reg.forEach(function(b){ if (b.oos) o++; if (b.undet) u++; if (b.flags) fl++; if (b.desk) dk++; });
  [["c-roos", o], ["c-rund", u], ["c-rflag", fl], ["c-rdesk", dk]].forEach(function(p){
    var n = el(p[0]); if (n) n.textContent = p[1];
  });
}
el("bcards").addEventListener("click", function(e){
  var h = e.target.closest(".bc-head");
  if (!h) return;
  OPENB[+h.dataset.b] = !OPENB[+h.dataset.b];
  renderReg();
});

/* ================= the desk: persistence ================= */
var ART = null, ART_READY = false, RO_REASON = "";
if (typeof window.claude === "object" && window.claude && typeof window.claude.use === "function") {
  window.claude.use("artifact").then(function(a){
    ART = a; ART_READY = true;
    if (!a) setRO("This view cannot save — the runtime did not grant the page its publish capability. The registers are fully browsable; the desks are read-only.");
  });
} else {
  ART_READY = true;
  setRO("This copy is outside the artifact viewer, so the desks are read-only. Open the published artifact to record entries.");
}
function setRO(msg){
  RO_REASON = msg;
  document.querySelectorAll(".desk .btn, .att-go, .iss-go, .ic-go").forEach(function(b){ b.disabled = true; });
  document.querySelectorAll(".deskmsg").forEach(function(d){ d.textContent = msg; d.className = "deskmsg bad"; });
}
function stamp(){
  var d = new Date(), p = function(n){ return (n < 10 ? "0" : "") + n; };
  return p(d.getDate()) + "." + p(d.getMonth() + 1) + "." + d.getFullYear() + " " +
         p(d.getHours()) + ":" + p(d.getMinutes());
}
function operator(){
  var v = (el("op-init").value || "").trim();
  return v || null;
}
function buildDoc(){
  var b64 = document.getElementById("qc-shell").textContent.trim();
  var bytes = atob(b64), arr = new Uint8Array(bytes.length);
  for (var i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
  var tpl = new TextDecoder("utf-8").decode(arr);
  var dataText = document.getElementById("qc-data").textContent;
  var ovText = JSON.stringify(OV).replace(/</g, "\\u003c");
  /* the placeholder tokens are composed at run time so the builder's own
     substitution pass can never touch these lines */
  var AT = "@" + "@";
  return tpl.split(AT + "DATA" + AT).join(dataText)
            .split(AT + "OVERLAY" + AT).join(ovText)
            .split(AT + "SHELL" + AT).join(b64);
}
var SAVING = false;
function saveState(action, detail, done, fail){
  if (!ART) {
    (fail || function(){})("This view cannot save — " + (RO_REASON || "no publish capability."));
    return;
  }
  if (SAVING) { (fail || function(){})("A save is already in flight — wait for the reload."); return; }
  OV.log.push({ at: stamp(), by: operator() || "—", action: action, detail: detail });
  var badge = document.createElement("div");
  badge.className = "saving"; badge.textContent = "Publishing…";
  document.body.appendChild(badge);
  SAVING = true;
  ART.publish(buildDoc()).then(function(){
    /* the shell reloads every view, this one included — nothing else to do */
  }).catch(function(err){
    SAVING = false; OV.log.pop(); badge.remove();
    var code = err && err.code;
    if (code === "conflict") {
      (fail || function(){})("Someone else published first — this view is reloading to the newer version.");
    } else if (code === "not_writer" || code === "not_granted" || code === "consent_required") {
      setRO("This view is read-only — entries here cannot be published.");
      (fail || function(){})("Read-only: this viewer cannot write the document.");
    } else if (code === "rate_limited") {
      (fail || function(){})("Publishing too often — wait a moment and try once more.");
    } else {
      (fail || function(){})("Save failed (" + (code || "unknown") + "). Nothing was recorded.");
    }
  });
}
function msgIn(id, text, ok){
  var n = el(id); if (!n) return;
  n.textContent = text; n.className = "deskmsg " + (ok ? "ok" : "bad");
}
var DATE_RX = /^\d{2}\.\d{2}\.\d{4}$/;

/* ---- batch intake ---- */
el("nb-go").addEventListener("click", function(){
  var cb = el("nb-cb").value.trim(), strain = el("nb-strain").value.trim(),
      date = el("nb-date").value.trim(), pn = el("nb-pn").value.trim();
  if (!operator()) return msgIn("nb-msg", "Enter your initials on the Desk log tab first — every entry is attributed.", false);
  if (!cb || !strain) return msgIn("nb-msg", "Batch code and strain are required.", false);
  if (!DATE_RX.test(date)) return msgIn("nb-msg", "Release date must be dd.mm.yyyy.", false);
  var clash = D.coqs.some(function(c){ return c.cb.toUpperCase() === cb.toUpperCase(); }) ||
              OV.batches.some(function(b){ return b.cb.toUpperCase() === cb.toUpperCase(); });
  if (clash) return msgIn("nb-msg", "That batch is already on record.", false);
  OV.batches.push({ cb: cb, strain: strain, date: date, pn: pn, by: operator(), at: stamp() });
  msgIn("nb-msg", "Publishing the batch record…", true);
  saveState("batch intake", cb + " (" + strain + "), released " + date + (pn ? ", lot " + pn : ""),
    null, function(m){ OV.batches.pop(); msgIn("nb-msg", m, false); });
});

/* ---- eCoA receipt ---- */
el("ne-go").addEventListener("click", function(){
  var code = el("ne-code").value.trim(), date = el("ne-date").value.trim(),
      lab = el("ne-lab").value, batch = el("ne-batch").value.trim(),
      params = el("ne-params").value.trim(), link = el("ne-link").value.trim();
  if (!operator()) return msgIn("ne-msg", "Enter your initials on the Desk log tab first.", false);
  if (!code || !batch) return msgIn("ne-msg", "Certificate code and batch are required.", false);
  if (!DATE_RX.test(date)) return msgIn("ne-msg", "Date of issue must be dd.mm.yyyy.", false);
  if (link && !/^https:\/\//.test(link)) return msgIn("ne-msg", "A document link must start with https://", false);
  var dup = D.ecoa.some(function(e){ return e.code === code; });
  if (dup) return msgIn("ne-msg", "That certificate code is already in the receipt register.", false);
  OV.ecoa.push({ code: code, date: date, lab: lab, batch: batch, params: params,
                 link: link, by: operator(), at: stamp() });
  msgIn("ne-msg", "Publishing the receipt…", true);
  saveState("certificate receipt", code + " (" + lab.split(" — ")[0] + ") for " + batch,
    null, function(m){ OV.ecoa.pop(); msgIn("ne-msg", m, false); });
});

/* ---- desk log ---- */
try { el("op-init").value = localStorage.getItem("cox-op") || ""; } catch (e) {}
el("op-init").addEventListener("input", function(){
  try { localStorage.setItem("cox-op", el("op-init").value.trim()); } catch (e) {}
});
function renderLog(){
  var list = OV.log.slice().reverse();
  document.querySelector("#t-log tbody").innerHTML = list.map(function(l){
    return "<tr><td class=\"mono dim\">" + esc(l.at) + "</td><td class=\"mono\">" + esc(l.by) + "</td>" +
      "<td><span class=\"pill p-info\">" + esc(l.action) + "</span></td><td>" + esc(l.detail) + "</td></tr>";
  }).join("");
  el("n-log").textContent = OV.log.length;
  el("log-tail").textContent = OV.log.length + " entries recorded at the desk";
  el("e-log").classList.toggle("hide", OV.log.length > 0);
}
renderLog(); renderReg();
