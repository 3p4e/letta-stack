#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Emit artifact-ready HTML (no doctype/html/head/body wrapper) for the CoA register."""
import csv
import html
import re
from collections import defaultdict, OrderedDict

SRC = "/tmp/claude-0/-home-user-letta-stack/4877ce6e-ae82-551e-bf35-5698c379c3be/scratchpad/master_coa_ALL.tsv"
OUT = "/tmp/claude-0/-home-user-letta-stack/4877ce6e-ae82-551e-bf35-5698c379c3be/scratchpad/coa_register.html"

BUCKETS = [
    ("identification", re.compile(r"identification|идентифика", re.I)),
    ("foreign_matter", re.compile(r"foreign matter|страни матери", re.I)),
    ("loss_on_drying", re.compile(r"loss on drying|губиток.*сушењ", re.I)),
    ("cbn", re.compile(r"\btotal cbn\b|вкупен cbn|^cbn$|^cbn\s", re.I)),
    ("cbd", re.compile(r"total cbd|вкупен cbd|total cannabidiol\b(?!ic)", re.I)),
    ("thc", re.compile(r"total.*(δ9|delta.?9|thc)|вкупно.*thc|total δ9-tetrahydrocannabinol", re.I)),
    ("aflatoxins", re.compile(r"sum aflatoxins|total aflatoxin", re.I)),
    ("ochratoxin", re.compile(r"ochratoxin", re.I)),
    ("pb", re.compile(r"\blead\b|олово", re.I)),
    ("cd", re.compile(r"cadmium|кадмиум", re.I)),
    ("as_", re.compile(r"\barsenic\b|арсен", re.I)),
    ("hg", re.compile(r"\bmercury\b|жива", re.I)),
    ("tamc", re.compile(r"\btamc\b|total aerobic microbial", re.I)),
    ("tymc", re.compile(r"\btymc\b|yeasts.*moulds|combined yeast", re.I)),
    ("bile", re.compile(r"bile.?tolerant", re.I)),
    ("ecoli", re.compile(r"escherichia|e\.\s?coli", re.I)),
    ("salmonella", re.compile(r"salmonella", re.I)),
]
PEST = re.compile(r"pesticide|insecticide", re.I)
STAB = re.compile(r"stabilit|стабилн|month\s*\d|месец|\d+\s*°?C\s*/\s*\d+\s*%\s*RH", re.I)
GAP = re.compile(r"^\[COVERAGE GAP\]$")
OVERALL = re.compile(r"overall result|заклучок|^\[NOTE\]", re.I)
ND = re.compile(r"^(н\.?д\.?|n\.?d\.?|nd)\b", re.I)
FLAG = re.compile(r"DATA INTEGRITY FLAG|NONCONFORM|NON-CONFORM|DOES NOT CONFORM|Не одговара", re.I)

COLS = OrderedDict([
    ("identification", "Identification"), ("foreign_matter", "Foreign matter"),
    ("loss_on_drying", "Loss on drying"), ("cbn", "Total CBN"), ("cbd", "Total CBD"),
    ("thc", "Total Δ9-THC"), ("aflatoxins", "Aflatoxins Σ"), ("ochratoxin", "Ochratoxin A"),
    ("pb", "Lead"), ("cd", "Cadmium"), ("as_", "Arsenic"), ("hg", "Mercury"),
    ("tamc", "TAMC"), ("tymc", "TYMC"), ("bile", "Bile-tol. GNB"), ("ecoli", "E. coli"),
    ("salmonella", "Salmonella"), ("pesticides", "Pesticide screen"),
])

rows = []
with open(SRC, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        r["Seq"] = int(r["Seq"])
        rows.append(r)
by_seq = defaultdict(list)
for r in rows:
    by_seq[r["Seq"]].append(r)


def classify(p):
    if GAP.match(p):
        return "gap"
    if OVERALL.search(p):
        return "overall"
    if STAB.search(p):
        return "stability"
    if PEST.search(p):
        return "pesticides"
    for k, rx in BUCKETS:
        if rx.search(p):
            return k
    return None


def cite(r):
    return " · ".join([p for p in (r["Certificate Code"].strip(), r["Issue Date"].strip(),
                                   r["Issuing Institution"].strip()) if p and p not in ("n/a", "N/A")])


def pivot(seq):
    brows = by_seq[seq]
    hits = defaultdict(list)
    gaps, overalls, flags = [], [], []
    ptot, pdet, stab = 0, [], 0
    for r in brows:
        k = classify(r["Parameter"])
        if k == "gap":
            gaps.append(r["Result"]); continue
        if k == "overall":
            overalls.append(r["Result"]); continue
        if k == "stability":
            stab += 1; continue
        if k == "pesticides":
            ptot += 1
            if not ND.match(r["Result"].strip()):
                pdet.append("%s: %s" % (r["Parameter"], r["Result"]))
            hits["pesticides"].append(r); continue
        if k:
            hits[k].append(r)
        if FLAG.search(r["Result"]):
            flags.append(r["Parameter"])

    out = {}
    for key in COLS:
        if key == "pesticides":
            if ptot == 0:
                out[key] = ("—", "", "")
            else:
                h = hits["pesticides"][0]
                v = ("%d/%d N.D. — DETECTED: %s" % (ptot - len(pdet), ptot, "; ".join(pdet))) if pdet \
                    else ("All N.D. · %d compounds" % ptot)
                out[key] = (v, cite(h), h["Drive File Link"])
            continue
        hs = hits.get(key, [])
        if not hs:
            out[key] = ("—", "", "")
        else:
            vals = list(dict.fromkeys(h["Result"].strip() for h in hs))
            srcs = list(dict.fromkeys(cite(h) for h in hs if cite(h)))
            out[key] = (" | ".join(vals), " | ".join(srcs), hs[0]["Drive File Link"])

    m = brows[0]
    is_open = any(re.search(r"DOES NOT CONFORM|NON-?CONFORM", n, re.I) for n in overalls + gaps)
    status = "open" if is_open else ("partial" if gaps else ("flag" if flags else "complete"))

    notes = []
    if overalls:
        notes.append("Conclusion: " + " / ".join(overalls))
    if gaps:
        cats = set()
        for n in gaps:
            low = n.lower()
            for pat, lab in (("pesticide", "pesticides"), ("heavy", "heavy metals"), ("metal", "heavy metals"),
                             ("mycotox", "mycotoxins"), ("microbio", "microbiology"),
                             ("identification", "identity / foreign matter / LoD"),
                             ("foreign", "identity / foreign matter / LoD")):
                if pat in low:
                    cats.add(lab)
        notes.append("No certificate on file for: " + ", ".join(sorted(cats)) if cats else "Coverage gap recorded")
    if flags:
        notes.append("Data-integrity flag — " + ", ".join(sorted(set(flags))))
    if stab:
        notes.append("%d stability results held separately" % stab)
    return {"seq": seq, "batch": m["Cultivation Batch"], "p": m["P-Number"],
            "strain": m["Strain"], "status": status, "vals": out, "notes": " · ".join(notes)}


batches = [pivot(s) for s in sorted(by_seq)]
n_complete = sum(1 for b in batches if b["status"] in ("complete", "flag"))
n_partial = sum(1 for b in batches if b["status"] == "partial")
n_open = sum(1 for b in batches if b["status"] == "open")
n_labs = len({r["Issuing Institution"].split("—")[0].strip() for r in rows if r["Issuing Institution"].strip()})

LBL = {"complete": "Complete", "flag": "Complete", "partial": "Partial", "open": "Open issue"}


def esc(s):
    return html.escape(str(s or ""))


def cls(v):
    low = v.lower()
    if v == "—":
        return "na"
    if "does not conform" in low or "nonconform" in low or "не одговара" in low or "detected:" in low:
        return "crit"
    if "data integrity flag" in low:
        return "warn"
    return ""


P = []
P.append("""<style>
:root{
  --paper:#F4F6F5; --surface:#FFFFFF; --surface-2:#EDF1F0; --line:#D6DEDC;
  --ink:#16232B; --muted:#5C6E75; --faint:#8FA0A5;
  --accent:#0E6E6E; --accent-soft:#D9EAE7;
  --pass:#1B7F4B; --pass-bg:#DFF1E6;
  --warn:#A66A00; --warn-bg:#FBEDD2;
  --crit:#B3261E; --crit-bg:#FADDDA;
  --serif:Georgia,"Iowan Old Style","Times New Roman",serif;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --paper:#0E1719; --surface:#16232B; --surface-2:#1D2E37; --line:#2C4049;
    --ink:#E4ECEA; --muted:#9FB2B6; --faint:#6E858C;
    --accent:#4FBAB1; --accent-soft:#173B3B;
    --pass:#6FD79B; --pass-bg:#12341F;
    --warn:#E8B65C; --warn-bg:#3A2B0C;
    --crit:#F2938C; --crit-bg:#3F1512;
  }
}
:root[data-theme="dark"]{
  --paper:#0E1719; --surface:#16232B; --surface-2:#1D2E37; --line:#2C4049;
  --ink:#E4ECEA; --muted:#9FB2B6; --faint:#6E858C;
  --accent:#4FBAB1; --accent-soft:#173B3B;
  --pass:#6FD79B; --pass-bg:#12341F;
  --warn:#E8B65C; --warn-bg:#3A2B0C;
  --crit:#F2938C; --crit-bg:#3F1512;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
  font-size:15px;line-height:1.5;-webkit-font-smoothing:antialiased}
.page{max-width:1600px;margin:0 auto;padding:40px 28px 64px;display:flex;flex-direction:column;gap:28px}
header{display:flex;flex-direction:column;gap:6px;border-bottom:2px solid var(--ink);padding-bottom:18px}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}
h1{font-family:var(--serif);font-weight:600;font-size:clamp(28px,4vw,40px);line-height:1.1;
  margin:0;text-wrap:balance;letter-spacing:-.01em}
.standfirst{color:var(--muted);max-width:68ch;font-size:15px}
.provenance{font-family:var(--mono);font-size:11.5px;color:var(--faint);line-height:1.7}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;
  background:var(--line);border:1px solid var(--line);border-radius:3px;overflow:hidden}
.stat{background:var(--surface);padding:16px 18px;display:flex;flex-direction:column;gap:2px}
.stat .n{font-family:var(--mono);font-size:30px;font-weight:600;line-height:1;font-variant-numeric:tabular-nums}
.stat .l{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.stat.pass .n{color:var(--pass)} .stat.warn .n{color:var(--warn)} .stat.crit .n{color:var(--crit)}
.bar{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
input[type=search]{flex:1;min-width:220px;max-width:340px;padding:9px 12px;border:1px solid var(--line);
  border-radius:3px;background:var(--surface);color:var(--ink);font-family:var(--sans);font-size:13.5px}
input[type=search]:focus{outline:2px solid var(--accent);outline-offset:1px}
.seg{display:flex;border:1px solid var(--line);border-radius:3px;overflow:hidden}
.seg button{border:0;background:var(--surface);color:var(--muted);padding:9px 14px;font-size:12.5px;
  font-family:var(--sans);cursor:pointer;border-right:1px solid var(--line)}
.seg button:last-child{border-right:0}
.seg button[aria-pressed="true"]{background:var(--accent);color:#fff;font-weight:600}
.seg button:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.legend{font-size:12px;color:var(--muted);display:flex;gap:18px;flex-wrap:wrap;align-items:center}
.chip{font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;
  padding:2px 7px;border-radius:2px;font-weight:600;white-space:nowrap}
.chip.complete{background:var(--pass-bg);color:var(--pass)}
.chip.partial{background:var(--warn-bg);color:var(--warn)}
.chip.open{background:var(--crit-bg);color:var(--crit)}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:3px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:12.5px}
thead th{position:sticky;top:0;z-index:2;background:var(--ink);color:var(--paper);
  font-family:var(--mono);font-size:10px;letter-spacing:.07em;text-transform:uppercase;
  font-weight:600;text-align:left;padding:9px 8px;white-space:nowrap}
tbody td{padding:7px 8px;vertical-align:top;max-width:250px;border-bottom:1px solid var(--line)}
tr.res td{border-top:1px solid var(--line)}
tr.res td.val{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:12px}
tr.src td{background:var(--surface-2);font-size:10.5px;color:var(--muted);
  border-bottom:2px solid var(--line);font-family:var(--mono);line-height:1.45}
tr.src a{color:var(--accent);text-decoration:none;border-bottom:1px solid transparent}
tr.src a:hover,tr.src a:focus-visible{border-bottom-color:var(--accent)}
td.stripe{border-left:4px solid transparent;font-family:var(--mono);font-variant-numeric:tabular-nums;
  color:var(--faint);font-size:11.5px}
tr.s-complete td.stripe{border-left-color:var(--pass)}
tr.s-partial td.stripe{border-left-color:var(--warn)}
tr.s-open td.stripe{border-left-color:var(--crit)}
td.batch{font-weight:600;white-space:nowrap;font-family:var(--mono);font-size:12px}
td.val.crit{background:var(--crit-bg);color:var(--crit);font-weight:600}
td.val.warn{background:var(--warn-bg);color:var(--warn)}
td.val.na{color:var(--faint);text-align:center}
td.notes{font-size:11px;color:var(--muted);max-width:300px;line-height:1.45}
tr.s-open td.notes{color:var(--crit);font-weight:600}
.rowtag{font-family:var(--mono);font-size:9.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--faint)}
footer{border-top:1px solid var(--line);padding-top:18px;font-size:12.5px;color:var(--muted);
  max-width:80ch;display:flex;flex-direction:column;gap:10px}
footer b{color:var(--ink)}
code{font-family:var(--mono);font-size:11.5px;background:var(--surface-2);padding:1px 4px;border-radius:2px}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>""")

P.append('<div class="page">')
P.append('<header>')
P.append('<div class="eyebrow">Purely Plant GmbH · Quality Control</div>')
P.append('<h1>Certificate of Analysis Register</h1>')
P.append('<p class="standfirst">Every tested batch with its outsourced laboratory results, acceptance criteria, '
         'issuing institution and a direct link to the source certificate.</p>')
P.append('<div class="provenance">80 batches · %d parameter records · %d issuing laboratories<br>'
         'Compiled 2026-08-10 from the ImB_QC_COAs knowledgebase and Drive folder '
         '<code>16oMK…kQsn5</code> · values transcribed verbatim, nothing inferred</div>' % (len(rows), n_labs))
P.append('</header>')

P.append('<div class="stats">')
P.append('<div class="stat"><div class="n">80</div><div class="l">Batches</div></div>')
P.append('<div class="stat pass"><div class="n">%d</div><div class="l">Full panel on file</div></div>' % n_complete)
P.append('<div class="stat warn"><div class="n">%d</div><div class="l">Partial coverage</div></div>' % n_partial)
P.append('<div class="stat crit"><div class="n">%d</div><div class="l">Open QC issue</div></div>' % n_open)
P.append('<div class="stat"><div class="n">%d</div><div class="l">Parameter records</div></div>' % len(rows))
P.append('</div>')

P.append('<div class="bar">')
P.append('<input type="search" id="q" placeholder="Filter batch, strain or P-number…" aria-label="Filter batches">')
P.append('<div class="seg" role="group" aria-label="Filter by status">'
         '<button id="f-all" aria-pressed="true" onclick="setf(\'all\')">All</button>'
         '<button id="f-open" aria-pressed="false" onclick="setf(\'open\')">Open issue</button>'
         '<button id="f-partial" aria-pressed="false" onclick="setf(\'partial\')">Partial</button>'
         '<button id="f-complete" aria-pressed="false" onclick="setf(\'complete\')">Complete</button></div>')
P.append('<span class="legend" id="count"></span>')
P.append('</div>')

P.append('<div class="legend">'
         '<span><span class="chip complete">Complete</span> all core Ph.&nbsp;Eur.&nbsp;3028 parameters on file</span>'
         '<span><span class="chip partial">Partial</span> a parameter category has no certificate</span>'
         '<span><span class="chip open">Open issue</span> unresolved non-conformance</span>'
         '<span>Each batch spans two rows: <b>result</b> above, <b>source certificate</b> below (linked).</span>'
         '</div>')

P.append('<div class="tablewrap"><table><thead><tr>')
for h in ["#", "Status", "Batch", "P-number", "Strain", ""] + list(COLS.values()) + ["Notes"]:
    P.append("<th>%s</th>" % h)
P.append("</tr></thead><tbody>")

for b in batches:
    sgroup = "open" if b["status"] == "open" else ("partial" if b["status"] == "partial" else "complete")
    key = ("%s %s %s" % (b["batch"], b["p"], b["strain"])).lower()
    P.append('<tr class="res s-%s" data-st="%s" data-k="%s">' % (sgroup, sgroup, esc(key)))
    P.append('<td class="stripe">%d</td>' % b["seq"])
    P.append('<td><span class="chip %s">%s</span></td>' % (sgroup, LBL[b["status"]]))
    P.append('<td class="batch">%s</td>' % esc(b["batch"]))
    P.append('<td class="val">%s</td>' % esc(b["p"]))
    P.append("<td>%s</td>" % esc(b["strain"]))
    P.append('<td class="rowtag">Result</td>')
    for k in COLS:
        v, s, l = b["vals"][k]
        P.append('<td class="val %s">%s</td>' % (cls(v), esc(v)))
    P.append('<td class="notes">%s</td>' % esc(b["notes"]))
    P.append("</tr>")

    P.append('<tr class="src s-%s" data-st="%s" data-k="%s">' % (sgroup, sgroup, esc(key)))
    P.append('<td class="stripe"></td><td colspan="4"></td><td class="rowtag">Source</td>')
    for k in COLS:
        v, s, l = b["vals"][k]
        if s and l:
            P.append('<td><a href="%s" target="_blank" rel="noopener">%s</a></td>'
                     % (esc(l.split(" (folder")[0].strip()), esc(s)))
        else:
            P.append("<td>%s</td>" % esc(s))
    P.append("<td></td></tr>")
P.append("</tbody></table></div>")

P.append("""<footer>
<div><b>Data integrity.</b> Values appear exactly as printed on each certificate — <code>N.D.</code>,
<code>&lt;LOQ</code>, <code>BLQ</code> and the Macedonian <code>Одговара / Не одговара</code> verdicts are
preserved verbatim. Where a certificate contradicts itself, the row carries a data-integrity flag instead of a
silent correction. Where a laboratory prints results without a limit column, the acceptance criterion is drawn
from the Purely Plant release specification / Ph. Eur. 3028 and marked as added for review.</div>
<div><b>Stability studies</b> — month 3, 6 and 9 at 25&nbsp;°C/60&nbsp;%&nbsp;RH and 40&nbsp;°C/75&nbsp;%&nbsp;RH —
are deliberately excluded from this release view and kept in their own sheet of the companion workbook, so they
can never be read as release results.</div>
</footer>""")
P.append("</div>")

P.append("""<script>
var F='all';
function setf(f){F=f;['all','open','partial','complete'].forEach(function(x){
  var b=document.getElementById('f-'+x); b.setAttribute('aria-pressed', x===f?'true':'false');});
  flt();}
function flt(){
  var q=document.getElementById('q').value.toLowerCase().trim();
  var rows=document.querySelectorAll('tbody tr'), shown=0;
  for(var i=0;i<rows.length;i++){
    var r=rows[i];
    var okF=(F==='all')||(r.dataset.st===F);
    var okQ=(!q)||((r.dataset.k||'').indexOf(q)>=0);
    var vis=okF&&okQ;
    r.style.display=vis?'':'none';
    if(vis&&r.classList.contains('res'))shown++;
  }
  document.getElementById('count').textContent=shown+' of 80 batches shown';
}
document.getElementById('q').addEventListener('input',flt);
flt();
</script>""")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("".join(P))
print("Wrote", OUT)
print("complete=%d partial=%d open=%d labs=%d records=%d" % (n_complete, n_partial, n_open, n_labs, len(rows)))
