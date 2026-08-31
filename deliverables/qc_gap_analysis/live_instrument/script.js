"use strict";
var D = JSON.parse(document.getElementById("qc-data").textContent);
var OV; try { OV = JSON.parse(document.getElementById("qc-overlay").textContent); }
catch (e) { OV = null; }
if (!OV || typeof OV !== "object") OV = {};
OV.v = OV.v || 1;
OV.batches = OV.batches || []; OV.ecoa = OV.ecoa || [];
OV.attach = OV.attach || {}; OV.icoa = OV.icoa || {};
OV.issue = OV.issue || {}; OV.log = OV.log || [];
OV.verify = OV.verify || {};
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
function todayStr(){
  var d = new Date(), p = function(n){ return (n < 10 ? "0" : "") + n; };
  return p(d.getDate()) + "." + p(d.getMonth() + 1) + "." + d.getFullYear();
}
/* The dating window is two-sided: no document before the SOP came into use,
   and none post-dated — a document is dated the day it is signed. */
function dateWindowError(date, floor){
  if (!DATE_RX.test(date)) return "The date must read dd.mm.yyyy.";
  if (sortDate(date) < sortDate(D.sop_effective))
    return "No document is issued before the SOP came into use, " + D.sop_effective + ".";
  if (floor && sortDate(date) < sortDate(floor))
    return "The printed date may be no earlier than " + floor +
           " — the newest cited document, or the 12-month due date.";
  if (sortDate(date) > sortDate(todayStr()))
    return "A document is never post-dated: it is dated the day it is signed, " +
           "so the latest permissible date is today, " + todayStr() + ".";
  return null;
}

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
  e.fix = OV.verify[e.code] || null;
  e.hay = [e.code, e.batch, e.strain, e.lab, e.pn].concat(e.reported)
    .concat(e.fix ? Object.keys(e.fix.params).map(function(k){
      return k + " " + e.fix.params[k].v; }) : [])
    .join(" ").toLowerCase();
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
/* the owner's per-scope masters double as bench worksheets: from any CoQ,
   print the master for a determination filled with this batch's identity */
var BENCH = { "1": "ab", "2": "ab", "3": "c", "7": "fm" };
el("coq-detail").addEventListener("click", function(e){
  var b = e.target.closest(".dm-go");
  if (!b || OPEN == null) return;
  var c = COQ[OPEN], k = b.dataset.k;
  var pseudo = { cb: c.cb, pp: c.pp, strain: c.strain, scope: SCOPE_NAME[k],
                 reissue: c.reissue, coq_type: c.t };
  var asn = OV.icoa[icoaKey(pseudo)] || null;
  openDoc((asn ? asn.ref : "BENCH MASTER") + " \u2014 " + SCOPE_NAME[k] + " \u2014 " + c.cb,
    icoaDocName(pseudo, asn), fillIcoa(pseudo, asn));
});
function openDets(c){
  return c.rows.filter(function(r){
    return r.st.indexOf("to be performed") === 0 || r.st.indexOf("not tested") === 0 ||
           r.st.indexOf("awaiting") === 0 || r.st.indexOf("in-house CoA only") === 0;
  }).map(function(r){ return r.no; });
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
      head = '<tr class="grp"><td colspan="7">' + esc(d.group) +
        (r.no.indexOf("9.") === 0
          ? ' <button class="btn sm dm-go" data-k="mb">Bench master \u00a79</button>' : "") +
        '</td></tr>';
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
        (r.also ? '<span class="sub dim">also on file: ' + esc(r.also) + '</span>' : "") +
        (BENCH[r.no] ? ' <button class="btn sm dm-go" data-k="' + BENCH[r.no] +
          '">Bench master</button>' : "") + '</td></tr>';
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
  var open_dets = openDets(c);
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
        : (sortDate(c.issue.replace("≥ ", "")) > sortDate(todayStr())
           ? "All in scope certified, but the dating window is EMPTY: the earliest permissible date, " +
             c.issue.replace("≥ ", "") + ", lies in the future, and a document is never post-dated. Issue when it arrives."
           : "All in scope certified. The printed date must lie between " +
             c.issue.replace("≥ ", "") + " and today — a document is dated the day it is signed, never post-dated.")) + '</div></div>';
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
    '</div></div><span style="display:flex;gap:8px">' +
    '<button class="btn sm gold" id="d-view">' + (c.issued ? "View certificate" : "Preview draft") + '</button>' +
    '<button class="close" id="cl">Close</button></span></div>' +
    (notes.length ? '<div class="d-note">' + notes.join("<br>") + '</div>' : "") +
    '<div class="scroll"><table><thead><tr>' +
    '<th style="width:44px">№</th><th style="width:190px">Parameter<span class="mk">Параметар</span></th>' +
    '<th style="width:170px">Method / reference</th><th style="width:190px">Acceptance criterion<span class="mk">Критериум</span></th>' +
    '<th style="width:96px" class="c">Result<span class="mk">Резултат</span></th>' +
    '<th style="width:170px">Source document</th><th>Status · route</th>' +
    '</tr></thead><tbody>' + body + '</tbody></table></div>' + deskHtml + '</div>';
  el("cl").addEventListener("click", function(){ OPEN = null; renderDetail(); renderCoqs(); });
  el("d-view").addEventListener("click", function(){
    openDoc((c.issued ? c.n : "DRAFT") + " — Certificate of Quality — " + c.strain,
      coqDocName(c), fillCoq(c));
  });
  var att = el("att-save");
  var attNo = el("att-no");
  if (attNo) {
    var attHint = function(){
      var d2 = DET[attNo.value] || {};
      var ar = el("att-res");
      if (ar) ar.placeholder = d2.crit ? "criterion: " +
        (d2.crit.split(" | ")[0].length > 46 ? d2.crit.split(" | ")[0].slice(0, 44) + "…"
          : d2.crit.split(" | ")[0]) : "verbatim";
    };
    attNo.addEventListener("change", attHint);
    attHint();
  }
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
    var bound = c.issue.replace("≥ ", "");
    var dw = dateWindowError(date, bound);
    if (dw) return msgIn("iss-msg", dw, false);
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
          ' <span class="desk-entry">' + esc(asn.by || "") + '</span>' +
          ' <button class="btn sm ic-view" data-ik="' + esc(icoaKey(p)) + '">View</button></td>'
        : '<td colspan="2"><button class="btn sm ic-go" data-ik="' + esc(icoaKey(p)) +
          '" data-lbl="' + esc(p.scope + " — " + p.cb + " (" + num + ")") + '">Assign at the desk</button>' +
          ' <button class="btn sm ic-view" data-ik="' + esc(icoaKey(p)) + '">Draft</button></td>') +
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
      '<td style="font-size:10.6px;color:var(--text-sec)">' +
        (e.reported.length ? esc(e.reported.join(" · ")) : '<span class="dim">—</span>') +
        ((e.rect || []).length ? "<br>" + e.rect.map(function(rv){
          return '<span class="vchip ' + (rv.t === "T1" ? "pv" : "cv") + '" title="' +
            esc(rv.src) + '"><b>' + esc(rv.k) + '</b>' + esc(rv.v) + '</span>';
        }).join("") : "") +
        (e.fix ? "<br>" + Object.keys(e.fix.params).map(function(k2){
          var pv = e.fix.params[k2];
          return '<span class="vchip" title="transcribed from the opened document at the desk by ' +
            esc(pv.by) + ", " + esc(pv.at) + '"><b>' + esc(k2) + '</b>' + esc(pv.v) + '</span>';
        }).join("") : "") + '</td>' +
      '<td class="c">' + (e.verified
          ? '<span class="pill p-ok" title="the certificate\u2019s values were read off its own page, 31.08.2026">page-verified</span>'
          : '<span class="pill p-none" title="the document is on file (open \u2192) \u2014 its values have not been read off the page; corpus values shown are pre-fill, promoted only through remediation">not page-verified</span>') +
        (e.fix && Object.keys(e.fix.params).length ? '<br><span class="pill p-info">desk-read</span>' : "") +
        ' <button class="btn sm ec-fix" data-code="' + esc(e.code) + '">Remediate</button></td>' +
      '<td class="c">' + (e.flag === "red" ? '<span class="pill p-fail"' + (e.why ? ' title="' + esc(e.why) + '"' : "") + '>red</span>'
        : e.flag === "amber" ? '<span class="pill p-warn"' + (e.why ? ' title="' + esc(e.why) + '"' : "") + '>amber</span>' : '<span class="dim">—</span>') +
        (e.why ? '<span class="sub" style="max-width:150px;white-space:normal">' + esc(e.why.length > 90 ? e.why.slice(0, 88) + "…" : e.why) + '</span>' : "") +
        (e.fix && e.fix.notes.length ? '<span class="sub" style="max-width:130px;white-space:normal">' +
          esc(e.fix.notes[e.fix.notes.length - 1].t) + '</span>' : "") + '</td>' +
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

/* ---- batch issuance ----
   The owner's convention of 31.08.2026: when the parameters missing from the
   outsourced certificates finally arrive, the certificates of quality they
   were holding up are issued together — one date, sequential numbers, in
   chronological order of their basis dates. */
function issueReady(){
  return COQ.filter(function(c){
    if (c.issued || c.unresolved) return false;
    if (openDets(c).length) return false;
    return sortDate(c.issue.replace("\u2265 ", "")) <= sortDate(todayStr());
  }).sort(function(a, b){
    var d = sortDate(a.basis).localeCompare(sortDate(b.basis));
    return d || (a.cb < b.cb ? -1 : a.cb > b.cb ? 1 : 0);
  });
}
function pad4(n){ return ("000" + n).slice(-4); }
document.querySelector("#p-coq .controls").insertAdjacentHTML("afterend",
  '<div class="desk" id="bi-desk" data-desk="1"><h3>Batch issuance \u2014 one date, sequential numbers, chronological order</h3>' +
  '<div class="deskmsg" id="bi-list" style="margin-bottom:8px"></div>' +
  '<div class="frm">' +
  '<span class="fld"><label>First CoQ number of the batch</label><input id="bi-num" placeholder="CoQ-PP-2026-NNNN"></span>' +
  '<span class="fld"><label>Date of issue (all certificates)</label><input id="bi-date" placeholder="dd.mm.yyyy"></span>' +
  '<button class="btn gold" id="bi-go">Issue the batch</button></div>' +
  '<div class="deskmsg" id="bi-msg">A CoQ number is copied from this issuance record at issue \u2014 numbering continues the sequence, in chronological order of the basis dates.</div></div>');
function renderBatchIssue(){
  var list = issueReady();
  el("bi-list").innerHTML = list.length
    ? "<b>" + list.length + " certificate" + (list.length === 1 ? "" : "s") +
      " fully certified and inside the dating window:</b> " +
      list.map(function(c){ return esc(c.cb) + (c.reissue ? " (reissue)" : ""); }).join(" \u00b7 ")
    : "Nothing is ready: no certificate of quality has every determination in scope " +
      "certified with its dating window open. Attach the arriving certificates first \u2014 " +
      "readiness is computed, never asserted.";
  el("bi-go").disabled = !list.length;
}
el("bi-go").addEventListener("click", function(){
  var list = issueReady();
  if (!list.length) return;
  var num = el("bi-num").value.trim(), date = el("bi-date").value.trim();
  if (!operator()) return msgIn("bi-msg", "Enter your initials on the Desk log tab first.", false);
  var m = /^CoQ-PP-(\d{4})-(\d{4})$/.exec(num);
  if (!m) return msgIn("bi-msg", "The first number must read CoQ-PP-YYYY-NNNN.", false);
  var start = parseInt(m[2], 10);
  if (start + list.length - 1 > 9999)
    return msgIn("bi-msg", "The sequence would run past 9999 \u2014 start lower.", false);
  for (var i = 0; i < list.length; i++) {
    var dw = dateWindowError(date, list[i].issue.replace("\u2265 ", ""));
    if (dw) return msgIn("bi-msg", list[i].cb + ": " + dw, false);
  }
  var nums = list.map(function(_, i){ return "CoQ-PP-" + m[1] + "-" + pad4(start + i); });
  var clash = nums.filter(function(n2){
    return COQ.some(function(x){ return x.n === n2; }) ||
      Object.keys(OV.issue).some(function(k){ return OV.issue[k].number === n2; });
  });
  if (clash.length) return msgIn("bi-msg", "Already taken: " + clash.join(", ") +
    ". One number, one document, forever.", false);
  var recorded = [];
  list.forEach(function(c, i){
    OV.issue[c.key] = { number: nums[i], date: date, by: operator(), at: stamp(), batch: true };
    recorded.push(c.key);
  });
  msgIn("bi-msg", "Publishing " + list.length + " issuances\u2026", true);
  saveState("CoQ batch issuance", list.length + " certificates issued " + date + ": " +
    nums[0] + " \u2026 " + nums[nums.length - 1] + " \u2014 " +
    list.map(function(c){ return c.cb; }).join(", "),
    null, function(msg2){
      recorded.forEach(function(k){ delete OV.issue[k]; });
      msgIn("bi-msg", msg2, false);
    });
});
renderBatchIssue();

/* ---- iCoA assignment ---- */
var IC_TARGET = null;
document.querySelector("#p-icoa .controls").insertAdjacentHTML("afterend",
  '<div class="desk" id="ic-desk" data-desk="1"><h3>iCoA assignment — <span id="ic-what">pick a row below</span></h3>' +
  '<div class="frm">' +
  '<span class="fld"><label>iCoA reference</label><input id="ic-ref" placeholder="iCoA-PP-2026-NNNN"></span>' +
  '<span class="fld"><label>Date of issue</label><input id="ic-date" placeholder="dd.mm.yyyy"></span>' +
  '<span class="fld"><label>Analyst</label><input id="ic-analyst" placeholder="name"></span>' +
  '<span class="fld"><label>Result, exactly as printed</label><input id="ic-res" placeholder="pick a row first"></span>' +
  '<button class="btn" id="ic-save" disabled>Record assignment</button></div>' +
  '<div class="deskmsg" id="ic-msg">Numbers are copied from this issuance record — assigning here IS the record.</div></div>');
document.querySelector("#t-icoas tbody").addEventListener("click", function(e){
  var v = e.target.closest(".ic-view");
  if (v) {
    var k = v.dataset.ik;
    var p = ICO.filter(function(x){ return icoaKey(x) === k; })[0];
    if (!p) return;
    var asn = OV.icoa[k] || null;
    openDoc((asn ? asn.ref : "DRAFT") + " — in-house CoA — " + p.scope + " — " + p.cb,
      icoaDocName(p, asn), fillIcoa(p, asn));
    return;
  }
  var b = e.target.closest(".ic-go");
  if (!b) return;
  IC_TARGET = b.dataset.ik;
  el("ic-what").textContent = b.dataset.lbl;
  el("ic-res").placeholder = IC_TARGET.split("|")[1].indexOf("Ident") === 0
    ? "Conforms / Does not conform" : "e.g. 0.4 % w/w";
  el("ic-save").disabled = false;
  el("ic-desk").scrollIntoView({ block: "nearest" });
});
el("ic-save").addEventListener("click", function(){
  if (!IC_TARGET) return;
  var tk = IC_TARGET;
  var ref = el("ic-ref").value.trim(), date = el("ic-date").value.trim(),
      analyst = el("ic-analyst").value.trim(), res = el("ic-res").value.trim();
  if (!operator()) return msgIn("ic-msg", "Enter your initials on the Desk log tab first.", false);
  if (!/^iCoA-PP-\d{4}-\d{4}$/.test(ref)) return msgIn("ic-msg", "Reference must read iCoA-PP-YYYY-NNNN.", false);
  var dwi = dateWindowError(date, null);
  if (dwi) return msgIn("ic-msg", dwi, false);
  if (!analyst) return msgIn("ic-msg", "Analyst is required.", false);
  if (!res) return msgIn("ic-msg", "The result is required — an iCoA without a result certifies nothing.", false);
  var taken = Object.keys(OV.icoa).some(function(k){ return OV.icoa[k].ref === ref; });
  if (taken) return msgIn("ic-msg", "That iCoA number is already assigned. One number, one document, forever.", false);
  /* the assignment IS the certificate: carry its result onto the linked CoQ's
     determinations (1+2 for Ident A+B, 7 for foreign matter) so the CoQ compiles
     from the desk record — never overwriting an attachment already there */
  var parts = tk.split("|");
  var ck = parts[0] + "|" + parts[2];
  var dets = parts[1].indexOf("Ident") === 0 ? ["1", "2"] : ["7"];
  var attached = [];
  if (COQ.some(function(c){ return c.key === ck; })) {
    OV.attach[ck] = OV.attach[ck] || {};
    dets.forEach(function(no){
      if (OV.attach[ck][no]) return;
      OV.attach[ck][no] = { doc: ref, res: res, date: date,
        lab: "Purely Plant — QC Laboratory (in-house iCoA)", by: operator(), at: stamp() };
      attached.push(no);
    });
  }
  OV.icoa[tk] = { ref: ref, date: date, analyst: analyst, res: res, by: operator(), at: stamp() };
  msgIn("ic-msg", "Publishing the assignment…", true);
  saveState("iCoA assignment", ref + " -> " + parts.slice(0, 2).join(" ") + " = " + res +
    (attached.length ? "; carried onto CoQ det " + attached.join(", ") : ""),
    null, function(m){
      delete OV.icoa[tk];
      attached.forEach(function(no){ delete OV.attach[ck][no]; });
      msgIn("ic-msg", m, false);
    });
});

renderCoqs(); renderIcoa(); renderEcoa();

/* ---- known constants as input suggestions ----
   Every CoQ draws on a finite, known set: the specification's determinations,
   the register's columns with their units, the batches and strains on record.
   The desks suggest them instead of asking the operator to remember. */
(function(){
  var params = [];
  D.dets.forEach(function(d2){ if (params.indexOf(d2.en) < 0) params.push(d2.en); });
  Object.keys(D.reg_columns).forEach(function(L){
    var n2 = D.reg_columns[L].name;
    if (params.indexOf(n2) < 0) params.push(n2);
  });
  var strains = {}, batches = {};
  D.coqs.forEach(function(c2){
    strains[c2.strain] = 1; batches[c2.cb] = 1; if (c2.pp) batches[c2.pp] = 1;
  });
  function dl(id, arr){
    return '<datalist id="' + id + '">' +
      arr.map(function(x){ return '<option value="' + esc(x) + '">'; }).join("") + "</datalist>";
  }
  document.body.insertAdjacentHTML("beforeend",
    dl("known-params", params) + dl("known-batches", Object.keys(batches).sort()) +
    dl("known-strains", Object.keys(strains).sort()));
  [["ne-batch", "known-batches"], ["nb-cb", "known-batches"],
   ["nb-strain", "known-strains"], ["ne-params", "known-params"],
   ["ef-param", "known-params"]].forEach(function(pr){
    var n3 = el(pr[0]); if (n3) n3.setAttribute("list", pr[1]);
  });
})();

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
              /* the tooltip answers "against what?": the acceptance criterion,
                 and — for a microbial criterion written as a bare power of ten —
                 the ×2-per-decade maximum acceptable count (Ph. Eur. 5.1.4) */
              var al = acceptanceLimit(col.crit || ""), mg = magnitude(col.crit || "");
              var tip = col.name + (col.crit ? " — A.C. " + col.crit : "") +
                (al != null && mg != null && al !== mg
                  ? " · maximum acceptable count " + al.toLocaleString("en") +
                    " (Ph. Eur. 5.1.4, ×2 per decade)" : "");
              return '<span class="vchip' + cls + (ct.stab ? " stab" : "") + '" title="' + esc(tip) + '"><b>' +
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
  document.querySelectorAll(".desk .btn, .att-go, .iss-go, .ic-go, .ec-fix").forEach(function(b){ b.disabled = true; });
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
      params = el("ne-params").value.trim(), link = el("ne-link").value.trim(),
      vals = el("ne-vals") ? el("ne-vals").value.trim() : "";
  if (!operator()) return msgIn("ne-msg", "Enter your initials on the Desk log tab first.", false);
  if (!code || !batch) return msgIn("ne-msg", "Certificate code and batch are required.", false);
  if (!DATE_RX.test(date)) return msgIn("ne-msg", "Date of issue must be dd.mm.yyyy.", false);
  if (sortDate(date) > sortDate(todayStr())) return msgIn("ne-msg", "A certificate cannot bear a date in the future — check the page.", false);
  if (link && !/^https:\/\//.test(link)) return msgIn("ne-msg", "A document link must start with https://", false);
  var dup = D.ecoa.some(function(e){ return e.code === code; });
  if (dup) return msgIn("ne-msg", "That certificate code is already in the receipt register.", false);
  /* tested values, recorded with the receipt: "name = value" pairs separated
     by · — stored in the same shape the remediation desk writes, so a value
     entered at receipt and a value transcribed later are one kind of record */
  var pairs = [];
  if (vals) {
    var segs = vals.split("·"), bad = null;
    segs.forEach(function(sg){
      sg = sg.trim(); if (!sg) return;
      var eq = sg.indexOf("=");
      var k2 = eq > 0 ? sg.slice(0, eq).trim() : "", v2 = eq > 0 ? sg.slice(eq + 1).trim() : "";
      if (!k2 || !v2) bad = sg; else pairs.push([k2, v2]);
    });
    if (bad) return msgIn("ne-msg", "Values must read \u201cparameter = value\u201d separated by · — could not read \u201c" + bad + "\u201d.", false);
  }
  OV.ecoa.push({ code: code, date: date, lab: lab, batch: batch, params: params,
                 link: link, by: operator(), at: stamp() });
  var hadVerify = !!OV.verify[code];
  if (pairs.length) {
    var v3 = OV.verify[code] = OV.verify[code] || { params: {}, notes: [] };
    pairs.forEach(function(pr){
      if (!v3.params[pr[0]]) v3.params[pr[0]] = { v: pr[1], by: operator(), at: stamp() };
    });
  }
  msgIn("ne-msg", "Publishing the receipt…", true);
  saveState("certificate receipt", code + " (" + lab.split(" — ")[0] + ") for " + batch +
    (pairs.length ? " — " + pairs.map(function(pr){ return pr[0] + " = " + pr[1]; }).join(" · ") : ""),
    null, function(m){
      OV.ecoa.pop();
      if (pairs.length && !hadVerify) delete OV.verify[code];
      else if (pairs.length) pairs.forEach(function(pr){ delete OV.verify[code].params[pr[0]]; });
      msgIn("ne-msg", m, false);
    });
});

/* ---- page remediation ----
   Where ingestion lost or corrupted a value — a certificate standing "not
   read", an amber or red flag, a parameter with no value — the operator
   opens the actual document (the open link on the row), reads the value off
   the page and transcribes it here, exactly as printed. The desk records who
   read it and when; flags are never cleared, a resolution note stands beside
   them. */
var EF_TARGET = null;
(function(){
  var pset = {}, names = [];
  Object.keys(D.reg_columns).forEach(function(L){
    var n2 = D.reg_columns[L].name;
    if (!pset[n2]) { pset[n2] = 1; names.push(n2); }
  });
  document.querySelector("#p-ecoa .desk").insertAdjacentHTML("afterend",
    '<div class="desk" id="ef-desk" data-desk="1"><h3>Remediation — transcribe a value from the opened document · <span id="ef-what" style="font-weight:400">pick a certificate below (Remediate)</span></h3>' +
    '<div class="frm">' +
    '<span class="fld"><label>Parameter</label><input id="ef-param" list="known-params" placeholder="TYMC CFU/g · THC % · …"></span>' +
    '<span class="fld"><label>Value, exactly as printed</label><input id="ef-val" placeholder="verbatim from the page"></span>' +
    '<span class="fld"><label>Resolution note (optional)</label><input id="ef-note" placeholder="e.g. flag resolved — page reads 4,2 x 10⁴"></span>' +
    '<button class="btn" id="ef-go" disabled>Record page reading</button></div>' +
    '<div class="deskmsg" id="ef-msg">Open the document from its row, read the value off the page, transcribe it exactly. A page reading never overwrites the register — it stands beside it, attributed.</div>' +
    '<datalist id="ef-params">' + names.map(function(n2){
      return '<option value="' + esc(n2) + '">'; }).join("") + '</datalist></div>');
})();
document.querySelector("#t-ecoas tbody").addEventListener("click", function(e){
  var b = e.target.closest(".ec-fix");
  if (!b) return;
  EF_TARGET = b.dataset.code;
  el("ef-what").textContent = EF_TARGET;
  el("ef-go").disabled = false;
  el("ef-desk").scrollIntoView({ block: "nearest" });
});
el("ef-go").addEventListener("click", function(){
  if (!EF_TARGET) return;
  var tk = EF_TARGET;
  var param = el("ef-param").value.trim(), val = el("ef-val").value.trim(),
      note = el("ef-note").value.trim();
  if (!operator()) return msgIn("ef-msg", "Enter your initials on the Desk log tab first.", false);
  if (!val && !note) return msgIn("ef-msg", "Transcribe a value, or record a resolution note — an empty reading records nothing.", false);
  if (val && !param) return msgIn("ef-msg", "Name the parameter the value belongs to — a value without its parameter is how registers rot.", false);
  var v = OV.verify[tk] || (OV.verify[tk] = { params: {}, notes: [] });
  if (val && v.params[param])
    return msgIn("ef-msg", "That parameter already carries a page reading (" + v.params[param].v +
      "). One reading, one record — a correction is a new note.", false);
  var hadVal = !!val, hadNote = !!note;
  if (val) v.params[param] = { v: val, by: operator(), at: stamp() };
  if (note) v.notes.push({ t: note, by: operator(), at: stamp() });
  msgIn("ef-msg", "Publishing the page reading…", true);
  saveState("page remediation", tk + (val ? ": " + param + " = " + val : "") +
    (note ? (val ? " — " : ": ") + note : ""),
    null, function(m2){
      if (hadVal) delete v.params[param];
      if (hadNote) v.notes.pop();
      if (!Object.keys(v.params).length && !v.notes.length) delete OV.verify[tk];
      msgIn("ef-msg", m2, false);
    });
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

/* ================= document generation =================
   The owner's own masters — _CoQ_MASTER_Template.html and
   iCoA_Template_v02_VariationF.html — are carried in the page base64-encoded
   and filled from the same data the registers render. Nothing is retyped: a
   generated certificate is the schedule, laid on the approved form. A document
   that is not yet issued renders with a DRAFT watermark and placeholder code. */
function tplDoc(id){
  var b = document.getElementById(id).textContent.trim();
  var bytes = atob(b), arr = new Uint8Array(bytes.length);
  for (var i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
  return new DOMParser().parseFromString(new TextDecoder("utf-8").decode(arr), "text/html");
}
function serializeDoc(doc){ return "<!DOCTYPE html>\n" + doc.documentElement.outerHTML; }
var LAB_META = {
  "Purely": ['Purely Plant — QC Department · In-house QC Laboratory · MK GMP Certified',
             'Пјурли Плант — Оддел за КК · Интерна лабораторија за КК · МК ДПП сертифицирана',
             'Kojlija 1043, Petrovec-Skopje, MK'],
  "UKIM":   ['UKIM Faculty of Pharmacy — Center for Natural Products · ISO/IEC 17025:2017 · LT-083 (IARM)',
             'УКИМ ФФ — Центар за Природни Производи', 'Mother Theresa 47, 1000 Skopje, MK'],
  "IPH":    ['JZU Institute for Public Health (IPH Skopje) · ISO/IEC 17025:2017 · LT-005 (IARM)',
             'ЈЗУ Институт за јавно здравје (ИЈЗ Скопје)', '50ta Divizija 6, 1000 Skopje, MK'],
  "Farmahem": ['Farmahem — Laboratorija za zivotna sredina · ISO/IEC 17025:2017',
             'Фармахем — Лабораторија за животна средина', 'Skopje, MK'],
  "State":  ['State Phytosanitary Laboratory', 'Државна фитосанитарна лабораторија', 'Skopje, MK']
};
function labMeta(lab){
  for (var k in LAB_META) if (lab.indexOf(k) === 0) return LAB_META[k];
  return [lab, "", ""];
}
function groupNo(no){ return no.indexOf(".") > 0 ? no.split(".")[0] : no; }
function condenseNos(list){
  var ns = Array.from(new Set(list)).map(Number).sort(function(a, b){ return a - b; });
  var out = [], run = [ns[0]];
  for (var i = 1; i <= ns.length; i++) {
    if (i < ns.length && ns[i] === ns[i - 1] + 1) { run.push(ns[i]); continue; }
    out.push(run.length > 2 ? run[0] + "–" + run[run.length - 1] : run.join(", "));
    run = [ns[i]];
  }
  return out.join(", ");
}
function rCls(res){
  if (/^(conforms|absent|одговара)/i.test(res)) return " r-conform";
  if (/^(n\.?d\.?|blq|—|—)/i.test(res)) return " r-nd";
  return "";
}
function setLk(doc, label, value){
  var lbls = doc.querySelectorAll(".lk-lbl");
  for (var i = 0; i < lbls.length; i++) {
    if (lbls[i].textContent.indexOf(label) !== 0) continue;
    var v = lbls[i].parentElement.querySelector(".lk-val");
    if (v) v.textContent = value;
    return;
  }
}
/* the reworked FM master keys its identification band on .idb-k/.idb-v
   cells instead of .lk lockups; a fill helper per shape, both no-ops when
   the shape is absent, keeps one filler working across every master */
function setIdb(doc, label, value){
  var lbls = doc.querySelectorAll(".idb-k");
  for (var i = 0; i < lbls.length; i++) {
    if (lbls[i].textContent.indexOf(label) !== 0) continue;
    var v = lbls[i].parentElement.querySelector(".idb-v");
    if (v) v.textContent = value;
    return;
  }
}
function chipRow(label, mk, opts){
  return '<span class="grp"><span class="lk-lbl">' + esc(label) +
    ' <span class="mk">' + esc(mk) + '</span></span><span class="stack">' +
    opts.map(function(o){
      return '<span class="' + (o[1] ? "chip-sel" : "chip-un") + '"><span class="bx">' +
        (o[1] ? "☒" : "☐") + '</span> ' + esc(o[0]) + '</span>';
    }).join("") + '</span></span>';
}
function fillCoq(c){
  var doc = tplDoc("tpl-coq");
  var q = function(s){ return doc.querySelector(s); };
  var draft = !c.issued;
  q(".hb-code").textContent = draft ? "CoQ-PP-····-····" : c.n;
  q(".hb-issue").innerHTML = "Issued · Издаден <b>" +
    esc(draft ? "—" : c.issue.replace("≥ ", "")) + "</b>";
  q(".pb-name").innerHTML = "<span style=\"font-family:'Roboto Mono',monospace\">" +
    esc(c.pp || c.cb) + '</span> <i class="bisep" style="font-size:.7em">|</i> ' +
    '<span style="font-weight:800;text-transform:uppercase">' + esc(c.strain) + "</span>";
  q(".pbp-val").textContent = c.thc ? c.thc + "%" : "··.··%";
  /* phenotype and processing are not held by the desk: controlled blanks QC
     ticks by hand. Chemotype is the product's THC class and stays ticked. */
  q(".selrow").innerHTML =
    chipRow("Phenotype", "Фенотип", [["Hybrid", false], ["Indica", false], ["Sativa", false]]) +
    chipRow("Chemotype", "Хемотип", [["THC", true], ["CBD", false]]) +
    chipRow("Processing", "Обработка", [["Machine", false], ["Hand", false]]);
  var a4 = c.rows.filter(function(r){ return r.no === "4"; })[0];
  setLk(doc, "Prod. Code", c.pcode || "—");
  setLk(doc, "Potency", a4 ? a4.crit.split("(")[0].trim() : "—");
  setLk(doc, "Spec. Ref.", c.spec || "—");
  setLk(doc, "Prod. Batch №", c.pp || c.cb);
  setLk(doc, "Manuf. Date", c.md || "—");
  setLk(doc, "Pack. Date", c.pk || "—");
  /* section 02 — rebuilt row for row from the schedule, criteria verbatim */
  var groups = { "9": [], "10": [], "11": [] };
  var singles = {};
  c.rows.forEach(function(r){
    if (r.no === "9.6" || r.no === "9.7") return;      /* upon request — not printed */
    var g = groupNo(r.no);
    if (r.no.indexOf(".") > 0 && groups[g]) groups[g].push(r); else singles[r.no] = r;
  });
  function res(r){
    var v = (r.res && r.res !== "—") ? r.res : "—";
    return '<td class="r-cell"><span class="r-val' + rCls(v) + '">' + esc(v) + "</span></td>";
  }
  function single(no, last){
    var r = singles[no]; if (!r) return "";
    var d = DET[no] || {};
    return '<tr' + (last ? ' class="last-row"' : "") + '><td>' + no + '</td><td><span class="p-name">' +
      esc(d.en) + ' <span class="mk">' + esc(d.mk) + '</span></span></td><td><span class="p-method">' +
      esc(d.method) + '</span></td><td><span class="p-spec">' + esc(r.crit) + "</span></td>" + res(r) + "</tr>";
  }
  function group(no){
    var rows2 = groups[no]; if (!rows2.length) return "";
    var d0 = DET[rows2[0].no] || {};
    var html = '<tr class="row-group"><td>' + no + '</td><td colspan="4"><span class="p-name">' +
      esc(d0.group) + "</span></td></tr>";
    rows2.forEach(function(r){
      var d = DET[r.no] || {};
      html += '<tr class="sub-row"><td></td><td><span class="p-sub">' + esc(d.en) +
        ' <i class="bisep">|</i> <span class="mk">' + esc(d.mk) + '</span></span></td>' +
        '<td><span class="p-method">' + esc(d.method) + '</span></td>' +
        '<td><span class="p-spec">' + esc(r.crit) + "</span></td>" + res(r) + "</tr>";
    });
    return html;
  }
  q("table.results tbody").innerHTML =
    single("1") + single("2") + single("3") + single("4") + single("5") + single("6") +
    single("7") + single("8") + group("9") + group("10") + group("11") + single("12", true);
  /* section 03 — from the citations themselves */
  var labs = {};
  c.rows.forEach(function(r){
    if (!r.doc || r.doc === "—") return;
    var L = labs[r.lab] || (labs[r.lab] = { codes: {}, nos: [] });
    L.codes[r.doc] = r.dd || "";
    L.nos.push(groupNo(r.no));
  });
  q("table.labref tbody").innerHTML = Object.keys(labs).map(function(lab){
    var m = labMeta(lab), L = labs[lab];
    var codes = Object.keys(L.codes).map(function(cd){
      return esc(cd) + (L.codes[cd] ? ", " + esc(L.codes[cd]) : "");
    }).join(" · ");
    return '<tr><td><span class="lr-lab">' + esc(m[0]) +
      (m[1] ? ' <i class="bisep">|</i> <span class="mk" style="display:inline">' + esc(m[1]) + "</span>" : "") +
      (m[2] ? "<small>" + esc(m[2]) + "</small>" : "") + '</span></td><td class="lr-mono">' + codes +
      '</td><td class="lr-mono">' + condenseNos(L.nos) + "</td></tr>";
  }).join("") || '<tr><td colspan="3" style="padding:8px;color:#8C9BB0">No certificate on file yet — controlled blanks.</td></tr>';
  /* section 04 — disposition follows the dispositions, ticked only at issue */
  var bad = c.k.oos > 0, open2 = c.k.und > 0;
  var disp = q(".disp-row .grp");
  disp.innerHTML = '<span class="lk-lbl">Batch ' + esc(c.pp || c.cb) +
    '<span class="mk">Серија ' + esc(c.pp || c.cb) + "</span></span>" +
    '<span class="' + (!draft && !bad && !open2 ? "chip-sel" : "chip-un") + '"><span class="bx">' +
    (!draft && !bad && !open2 ? "☒" : "☐") + '</span> Conforms to Specification <span class="mk">Одговара на спецификацијата</span></span>' +
    '<span class="' + (!draft && bad ? "chip-sel" : "chip-un") + '"><span class="bx">' +
    (!draft && bad ? "☒" : "☐") + "</span> Does not conform</span>";
  doc.querySelectorAll(".ap-date-val").forEach(function(n){
    n.textContent = draft ? "—" : c.issue.replace("≥ ", "");
  });
  if (draft) addDraftMark(doc);
  return serializeDoc(doc);
}
/* The four per-scope iCoA masters (31.08.2026) supersede the Variation F
   master for compilation. Each is a worked specimen: everything that is the
   worked batch's measurement data is blanked to a controlled "—" — the desk
   holds only the overall disposition, and bench observations belong to the
   analyst's worksheet, never to a compilation. Criterion and method columns
   are specification text and stay as the master prints them. */
var SCOPE_TPL = { ab: "tpl-icoa-ab", c: "tpl-icoa-c", fm: "tpl-icoa-fm", mb: "tpl-icoa-mb" };
var SCOPE_SEC = { ab: "\u00a71\u20132", c: "\u00a73", fm: "\u00a77", mb: "\u00a79" };
var SCOPE_NAME = { ab: "Ident A + B", c: "Ident C \u2014 chromatographic",
                   fm: "Foreign matter", mb: "Microbiological purity" };
function scopeKind(scope){
  if (scope.indexOf("Ident A") === 0) return "ab";
  if (scope.indexOf("Ident C") === 0) return "c";
  if (scope.indexOf("Foreign") === 0) return "fm";
  return "mb";
}
function fillIcoa(p, asn){
  var kind = scopeKind(p.scope);
  var doc = tplDoc(SCOPE_TPL[kind]);
  var q = function(sel){ return doc.querySelector(sel); };
  var draft = !asn;
  var ref = asn ? asn.ref : "iCoA-PP-\u00b7\u00b7\u00b7\u00b7-\u00b7\u00b7\u00b7\u00b7";
  var coq = COQ.filter(function(c){ return c.cb === p.cb && c.reissue === p.reissue; })[0];
  q(".hb-code").textContent = ref;
  q(".hb-issue").innerHTML = "Issued \u00b7 \u0418\u0437\u0434\u0430\u0434\u0435\u043d <b>" +
    esc(draft ? "\u2014" : asn.date) + "</b>";
  q(".pb-name").innerHTML = "<span style=\"font-family:'Roboto Mono',monospace\">" +
    esc(p.pp || p.cb) + '</span> <i class="bisep" style="font-size:.7em">|</i> ' +
    '<span style="font-weight:800;text-transform:uppercase">' + esc(p.strain) + "</span>";
  var pot = q(".pb-potency");
  if (pot) {
    var pv = pot.querySelector(".pbp-val"), pt = pot.querySelector(".pbp-tol");
    if (pv) pv.textContent = (coq && coq.thc) ? coq.thc + "%" : "\u00b7\u00b7.\u00b7\u00b7%";
    if (pt) pt.textContent = "";
  }
  /* phenotype and processing are controlled blanks QC ticks by hand;
     chemotype THC is the product's class and stays ticked */
  doc.querySelectorAll(".selrow .chip-sel").forEach(function(ch){
    if (/THC/.test(ch.textContent)) return;
    ch.className = ch.className.replace("chip-sel", "chip-un");
    var bx = ch.querySelector(".bx"); if (bx) bx.textContent = "\u2610";
  });
  setLk(doc, "Prod. Code", (coq && coq.pcode) || "\u2014");
  setLk(doc, "Spec. Ref.", ((coq && coq.spec) || "QCSP 001 v.03") + " \u00b7 " + SCOPE_SEC[kind]);
  setLk(doc, "Prod. Batch \u2116", p.pp || p.cb);
  setLk(doc, "Proc. Batch \u2116", p.cb);
  setLk(doc, "Sampling Date", "\u2014");
  setLk(doc, "Test Period", "\u2014");
  setIdb(doc, "Prod. Code", (coq && coq.pcode) || "\u2014");
  setIdb(doc, "Spec. Ref.", (coq && coq.spec) || "QCSP 001 v.03");
  setIdb(doc, "Prod. Batch \u2116", p.pp || p.cb);
  setIdb(doc, "Date of Sampling", "\u2014");
  /* results table: which cells are the worked batch's measurements, per master */
  var BLANK = { ab: [3, 4], c: [2, 3, 4, 5, 6], fm: [2, 3, 4, 5], mb: [4, 5] };
  doc.querySelectorAll("table.data tbody tr").forEach(function(tr){
    if (kind === "mb" && /Not requested/.test(tr.textContent)) return;
    var tds = tr.querySelectorAll("td");
    BLANK[kind].forEach(function(ix){
      if (tds[ix]) { tds[ix].textContent = "\u2014"; tds[ix].className = "c"; }
    });
  });
  var res = asn && asn.res ? asn.res : "\u2014";
  var bad = !!(asn && /^does not/i.test(asn.res || ""));
  var tf = doc.querySelectorAll("table.data tfoot td");
  if (tf.length) {
    if (kind === "fm") {
      /* [criterion label, total g, total % w/w, status] */
      tf[1].textContent = "\u2014";
      tf[2].textContent = res;
    } else {
      tf[tf.length - 2].textContent = res;
    }
    var st = tf[tf.length - 1];
    st.textContent = draft ? "\u2014" : (bad ? "FAIL" : "PASS");
    st.className = "c" + (!draft && !bad ? " ok" : "");
    if (bad) st.setAttribute("style", "color:#9B2C2C;font-weight:800");
  }
  var fn2 = q(".fnote");
  if (fn2) fn2.innerHTML = "<b>Seed check</b> <span class=\"mkx\">Проверка на семки</span> — " +
    "whole and fragment counts are recorded by the analyst at the bench; the criterion requires no seeds.";
  var pn = q(".pot-note");
  if (pn) pn.textContent = "Bench observations and raw measurements are recorded by " +
    "the analyst on the printed worksheet and in the laboratory records; this " +
    "compilation carries the desk-recorded overall disposition only.";
  var dr = q(".disp-row .grp");
  if (dr) dr.innerHTML = '<span class="lk-lbl">Result vs Specification' +
    '<span class="mk">\u0420\u0435\u0437\u0443\u043b\u0442\u0430\u0442 \u0441\u043f\u043e\u0440\u0435\u0434 \u0441\u043f\u0435\u0446.</span></span>' +
    '<span class="' + (!draft && !bad ? "chip-sel" : "chip-un") + '"><span class="bx">' +
    (!draft && !bad ? "\u2612" : "\u2610") + '</span> Conforms <span class="mk">\u0421\u043e\u043e\u0434\u0432\u0435\u0442\u0441\u0442\u0432\u0443\u0432\u0430</span></span>' +
    '<span class="' + (!draft && bad ? "chip-sel" : "chip-un") + '"><span class="bx">' +
    (!draft && bad ? "\u2612" : "\u2610") + "</span> Does not conform</span>";
  var dn = q(".disp-note");
  if (dn) dn.innerHTML = "The sample " +
    (draft ? "<strong>is under examination</strong> against"
           : (bad ? "<strong>does not conform</strong> to" : "<strong>conforms</strong> to")) +
    " <strong>" + esc(((coq && coq.spec) || "QCSP 001 v.03") + " " + SCOPE_SEC[kind]) +
    " (" + esc(p.scope) + ")</strong>" +
    (draft ? "" : " \u2014 desk-recorded result: <strong>" + esc(asn.res) + "</strong>") +
    ". Results relate only to the sample(s) as received; the report is reproducible " +
    "only in full. Testing performed <strong>in-house</strong> (ISO/IEC 17025-aligned, " +
    "MK GMP facility); OOS handling per QCSOP 014. Linked Certificate of Quality: " +
    "<strong>" + esc(coq ? coq.n : "\u2014") + "</strong>.";
  var aps = doc.querySelectorAll(".approval-grid > div");
  if (aps[0]) {
    var an = aps[0].querySelector(".ap-name");
    if (an) an.textContent = asn ? asn.analyst : "\u2014";
  }
  doc.querySelectorAll(".ap-date-val").forEach(function(n){
    n.textContent = asn ? asn.date : "\u2014";
  });
  if (draft) addDraftMark(doc);
  return serializeDoc(doc);
}
function addDraftMark(doc){
  var wm = doc.createElement("div");
  wm.setAttribute("style", "position:fixed;inset:0;display:flex;align-items:center;" +
    "justify-content:center;pointer-events:none;z-index:99");
  wm.innerHTML = "<div style=\"font:800 96px 'Montserrat',sans-serif;" +
    "color:rgba(155,44,44,.14);transform:rotate(-28deg);letter-spacing:14px\">DRAFT</div>";
  doc.body.appendChild(wm);
}

/* ---------- the viewer ---------- */
var DL = null;
if (typeof window.claude === "object" && window.claude && typeof window.claude.use === "function") {
  window.claude.use("downloads").then(function(d){ DL = d; });
}
document.body.insertAdjacentHTML("beforeend",
  '<dialog id="dv" style="width:min(940px,96vw);height:92vh;border:1px solid var(--rule);' +
  'border-top:3px solid var(--gold-deep);padding:0;background:#FFF">' +
  '<div style="display:flex;align-items:center;gap:10px;padding:9px 14px;background:var(--heaven);' +
  'border-bottom:1px solid var(--border)"><b id="dv-t" style="font-family:var(--d);font-size:10px;' +
  'letter-spacing:1px;text-transform:uppercase;color:var(--navy)"></b>' +
  '<span style="margin-left:auto"></span>' +
  '<button class="btn sm" id="dv-print">Print</button>' +
  '<button class="btn sm gold" id="dv-save">Save HTML</button>' +
  '<button class="close" id="dv-close">Close</button></div>' +
  '<iframe id="dv-f" style="width:100%;height:calc(92vh - 46px);border:0;background:#B1BAC5"></iframe></dialog>');
var DV_HTML = "", DV_NAME = "";
function openDoc(title, filename, html){
  DV_HTML = html; DV_NAME = filename;
  el("dv-t").textContent = title;
  el("dv-f").srcdoc = html;
  el("dv-save").hidden = !DL;
  el("dv").showModal();
}
el("dv-close").addEventListener("click", function(){ el("dv").close(); });
el("dv-print").addEventListener("click", function(){
  var w = el("dv-f").contentWindow;
  if (w) { w.focus(); w.print(); }
});
el("dv-save").addEventListener("click", function(){
  if (!DL) return;
  DL.save({ filename: DV_NAME, data: DV_HTML }).catch(function(err){
    if (err && err.code === "declined") return;
    el("dv-t").textContent = "Save failed (" + ((err && err.code) || "unknown") + ")";
  });
});
function coqDocName(c){
  return (c.issued ? c.n : "DRAFT_CoQ") + "_" + (c.pp || c.cb).replace(/[^\w-]/g, "_") + ".html";
}
function icoaDocName(p, asn){
  var short = { ab: "IdentAB", c: "IdentC", fm: "FM", mb: "Micro" }[scopeKind(p.scope)];
  return (asn ? asn.ref : "DRAFT_iCoA") + "_" + p.cb.replace(/[^\w-]/g, "_") + "_" + short + ".html";
}
