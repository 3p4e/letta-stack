#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render the master eCoA register as a self-contained HTML page.

Layout: a compact one-row-per-batch overview for scanning, then one detail card per
batch where every parameter gets a full-width row. Cramming all parameters into columns
made every cell narrow and unreadable; the parameter is the natural row unit.

Usage:  python3 build_master_register_html.py [input.tsv] [output.html]
"""
import html
import os
import sys
from collections import OrderedDict

import coa_pivot as cp

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(HERE, "exports", "coa_register.html")

# Panels group the parameter rows inside each batch card.
PANELS = OrderedDict([
    ("Identity & physical", ["appearance", "identification", "foreign_matter",
                             "loss_on_drying", "packaging"]),
    ("Potency", ["thc", "cbd", "cbn", "cannabinoid_profile"]),
    ("Contaminants", ["aflatoxins", "ochratoxin", "pb", "cd", "as_", "hg", "cu",
                      "metals_panel", "pesticides"]),
    ("Microbiology", ["tamc", "tymc", "bile", "ecoli", "salmonella", "micro_other"]),
])

# Short indicator set for the overview table — chosen because these are the release-critical
# reads a reviewer scans for, and each renders in a few characters.
OVERVIEW = [("thc", "Total THC"), ("cbd", "Total CBD"), ("loss_on_drying", "LoD"),
            ("aflatoxins", "Aflatox."), ("pesticides", "Pest."), ("pb", "Pb"),
            ("tamc", "TAMC"), ("salmonella", "Salm.")]

STATUS_LABEL = {"complete": "Complete", "flag": "Complete", "partial": "Partial",
                "open": "Open issue"}
STATUS_GROUP = {"complete": "complete", "flag": "complete", "partial": "partial",
                "open": "open"}


def esc(s):
    return html.escape(str(s if s is not None else ""))


def short(value, limit=30):
    """Compact a cell value for the narrow overview grid without inventing meaning."""
    if not value or value == "—":
        return "—"
    v = value.split(" | ")[0].strip()
    if v.startswith("All not detected"):
        return "all N.D."
    if v.startswith("Above LOQ"):
        return "above LOQ"
    return v if len(v) <= limit else v[:limit - 1] + "…"


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else None
    out_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT

    rows, batches = cp.build(src)
    by_seq = cp.group_by_seq(rows)
    n_complete = sum(1 for b in batches if b["status"] in ("complete", "flag"))
    n_partial = sum(1 for b in batches if b["status"] == "partial")
    n_open = sum(1 for b in batches if b["status"] == "open")
    n_labs = cp.count_labs(rows)
    n_batches = len(batches)

    P = []
    P.append("""<style>
:root{
  --paper:#F4F6F5; --surface:#FFFFFF; --surface-2:#EDF1F0; --line:#DBE3E1; --line-2:#C3D0CD;
  --ink:#16232B; --muted:#5A6E75; --faint:#8B9EA3;
  --accent:#0E6E6E; --accent-2:#0A5252;
  --pass:#1B7F4B; --pass-bg:#E3F3E9;
  --warn:#9A6300; --warn-bg:#FAEDD4;
  --crit:#AE2318; --crit-bg:#F9DEDB;
  --serif:Georgia,"Iowan Old Style","Times New Roman",serif;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#0D1618; --surface:#152227; --surface-2:#1C2E34; --line:#2A3E45; --line-2:#37505A;
  --ink:#E3ECEA; --muted:#9FB3B7; --faint:#6C848B;
  --accent:#4FBAB1; --accent-2:#7FD3CB;
  --pass:#6FD79B; --pass-bg:#123322;
  --warn:#E7B45E; --warn-bg:#39290B;
  --crit:#F0938B; --crit-bg:#3D1411;
}}
:root[data-theme="dark"]{
  --paper:#0D1618; --surface:#152227; --surface-2:#1C2E34; --line:#2A3E45; --line-2:#37505A;
  --ink:#E3ECEA; --muted:#9FB3B7; --faint:#6C848B;
  --accent:#4FBAB1; --accent-2:#7FD3CB;
  --pass:#6FD79B; --pass-bg:#123322;
  --warn:#E7B45E; --warn-bg:#39290B;
  --crit:#F0938B; --crit-bg:#3D1411;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
  font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
.page{max-width:1240px;margin:0 auto;padding:44px 24px 80px;display:flex;flex-direction:column;gap:32px}
header{border-bottom:2px solid var(--ink);padding-bottom:20px;display:flex;flex-direction:column;gap:8px}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent)}
h1{font-family:var(--serif);font-weight:600;font-size:clamp(30px,4.4vw,44px);line-height:1.08;
  margin:0;letter-spacing:-.015em;text-wrap:balance}
.standfirst{color:var(--muted);max-width:64ch;margin:0}
.provenance{font-family:var(--mono);font-size:11.5px;color:var(--faint);line-height:1.75}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:1px;
  background:var(--line);border:1px solid var(--line);border-radius:4px;overflow:hidden}
.stat{background:var(--surface);padding:18px 20px}
.stat .n{font-family:var(--mono);font-size:32px;font-weight:600;line-height:1;
  font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.stat .l{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);margin-top:5px}
.stat.pass .n{color:var(--pass)} .stat.warn .n{color:var(--warn)} .stat.crit .n{color:var(--crit)}
h2{font-family:var(--serif);font-size:23px;margin:0 0 4px;font-weight:600}
.sectionnote{color:var(--muted);font-size:13px;margin:0 0 14px}
.bar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;position:sticky;top:0;z-index:20;
  background:var(--paper);padding:10px 0;border-bottom:1px solid var(--line)}
input[type=search]{flex:1;min-width:210px;max-width:330px;padding:9px 12px;border:1px solid var(--line-2);
  border-radius:3px;background:var(--surface);color:var(--ink);font-family:var(--sans);font-size:13.5px}
input[type=search]:focus{outline:2px solid var(--accent);outline-offset:1px}
.seg{display:flex;border:1px solid var(--line-2);border-radius:3px;overflow:hidden}
.seg button{border:0;background:var(--surface);color:var(--muted);padding:9px 15px;font-size:12.5px;
  font-family:var(--sans);cursor:pointer;border-right:1px solid var(--line-2)}
.seg button:last-child{border-right:0}
.seg button[aria-pressed="true"]{background:var(--accent);color:#fff;font-weight:600}
.seg button:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.counter{font-family:var(--mono);font-size:11.5px;color:var(--muted)}
.chip{font-family:var(--mono);font-size:10px;letter-spacing:.07em;text-transform:uppercase;
  padding:3px 8px;border-radius:2px;font-weight:700;white-space:nowrap;display:inline-block}
.chip.complete{background:var(--pass-bg);color:var(--pass)}
.chip.partial{background:var(--warn-bg);color:var(--warn)}
.chip.open{background:var(--crit-bg);color:var(--crit)}
/* ---- overview ---- */
.ovwrap{overflow-x:auto;border:1px solid var(--line);border-radius:4px;background:var(--surface)}
table.ov{border-collapse:collapse;width:100%;font-size:13px;min-width:900px}
table.ov thead th{background:var(--ink);color:var(--paper);font-family:var(--mono);font-size:9.5px;
  letter-spacing:.08em;text-transform:uppercase;font-weight:600;text-align:left;padding:10px 9px;white-space:nowrap}
table.ov td{padding:9px;border-bottom:1px solid var(--line);white-space:nowrap;vertical-align:middle}
table.ov tbody tr:hover{background:var(--surface-2)}
table.ov td.num{font-family:var(--mono);font-variant-numeric:tabular-nums;color:var(--faint);font-size:11.5px}
table.ov td.bat{font-family:var(--mono);font-weight:600;font-size:12.5px}
table.ov td.bat a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--line-2)}
table.ov td.bat a:hover,table.ov td.bat a:focus-visible{color:var(--accent);border-bottom-color:var(--accent)}
table.ov td.v{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:11.5px;color:var(--muted)}
table.ov td.v.crit{color:var(--crit);font-weight:700}
table.ov td.v.na{color:var(--faint)}
table.ov tr.s-open td.num{border-left:3px solid var(--crit)}
table.ov tr.s-partial td.num{border-left:3px solid var(--warn)}
table.ov tr.s-complete td.num{border-left:3px solid var(--pass)}
/* ---- detail cards ---- */
.cards{display:flex;flex-direction:column;gap:20px}
.card{border:1px solid var(--line);border-radius:4px;background:var(--surface);overflow:hidden}
.card.open-issue{border-color:var(--crit);border-width:1.5px}
.cardhead{display:flex;gap:14px;align-items:baseline;flex-wrap:wrap;padding:14px 18px;
  background:var(--surface-2);border-bottom:1px solid var(--line)}
.cardhead .seq{font-family:var(--mono);font-size:11.5px;color:var(--faint);font-variant-numeric:tabular-nums}
.cardhead .name{font-family:var(--mono);font-size:16px;font-weight:700;letter-spacing:-.01em}
.cardhead .strain{font-family:var(--serif);font-size:16px;color:var(--muted);font-style:italic}
.cardhead .pnum{font-family:var(--mono);font-size:12px;color:var(--muted)}
.cardnote{padding:10px 18px;background:var(--warn-bg);color:var(--warn);font-size:12.5px;
  border-bottom:1px solid var(--line)}
.card.open-issue .cardnote{background:var(--crit-bg);color:var(--crit);font-weight:600}
.panel{padding:0}
.panelname{font-family:var(--mono);font-size:9.5px;letter-spacing:.11em;text-transform:uppercase;
  color:var(--accent);padding:12px 18px 5px;font-weight:700}
table.det{border-collapse:collapse;width:100%;font-size:13px;table-layout:fixed}
table.det col.c1{width:31%} table.det col.c2{width:19%} table.det col.c3{width:20%} table.det col.c4{width:30%}
table.det th{font-family:var(--mono);font-size:9.5px;letter-spacing:.07em;text-transform:uppercase;
  color:var(--faint);text-align:left;padding:4px 18px;font-weight:600;border-bottom:1px solid var(--line)}
table.det td{padding:7px 18px;border-bottom:1px solid var(--line);vertical-align:top;
  overflow-wrap:anywhere}
table.det tr:last-child td{border-bottom:0}
td.param{color:var(--ink)}
td.crit-col{color:var(--muted);font-family:var(--mono);font-size:11.5px}
td.result{font-family:var(--mono);font-size:12.5px;font-variant-numeric:tabular-nums;font-weight:600}
td.result.bad{color:var(--crit)}
td.result.flagged{color:var(--warn)}
td.cert{font-family:var(--mono);font-size:11px;color:var(--muted);line-height:1.5}
td.cert a{color:var(--accent);text-decoration:none;border-bottom:1px solid transparent}
td.cert a:hover,td.cert a:focus-visible{border-bottom-color:var(--accent)}
td.cert .lab{display:block;color:var(--faint);font-size:10.5px}
.backlink{font-family:var(--mono);font-size:10.5px;color:var(--faint);text-decoration:none;margin-left:auto}
.backlink:hover,.backlink:focus-visible{color:var(--accent)}
footer{border-top:1px solid var(--line);padding-top:20px;font-size:13px;color:var(--muted);
  max-width:78ch;display:flex;flex-direction:column;gap:11px}
footer b{color:var(--ink)}
code{font-family:var(--mono);font-size:11.5px;background:var(--surface-2);padding:1px 5px;border-radius:2px}
@media (max-width:720px){
  table.det{table-layout:auto}
  table.det col{width:auto!important}
  .cardhead{gap:8px}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>""")

    P.append('<div class="page" id="top">')
    P.append('<header>')
    P.append('<div class="eyebrow">Purely Plant GmbH · Quality Control</div>')
    P.append('<h1>Certificate of Analysis Register</h1>')
    P.append('<p class="standfirst">Every tested batch with its outsourced laboratory results, '
             'acceptance criteria, issuing institution and a link to each source certificate.</p>')
    P.append('<div class="provenance">%d batches · %d parameter records · %d accredited laboratories<br>'
             'Compiled from the ImB_QC_COAs knowledgebase and Drive folder <code>16oMK…kQsn5</code> · '
             'values transcribed verbatim, nothing inferred</div>' % (n_batches, len(rows), n_labs))
    P.append('</header>')

    P.append('<div class="stats">')
    P.append('<div class="stat"><div class="n">%d</div><div class="l">Batches</div></div>' % n_batches)
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
    P.append('<span class="counter" id="count"></span>')
    P.append('</div>')

    # ---------------- overview ----------------
    P.append('<section>')
    P.append('<h2>Overview</h2>')
    P.append('<p class="sectionnote">One row per batch, release-critical reads only. '
             'Select a batch code for its full parameter list and certificates.</p>')
    P.append('<div class="ovwrap"><table class="ov"><thead><tr>')
    for h in ["#", "Status", "Batch", "P-number", "Strain"] + [lbl for _, lbl in OVERVIEW]:
        P.append("<th>%s</th>" % esc(h))
    P.append("</tr></thead><tbody>")
    for b in batches:
        g = STATUS_GROUP[b["status"]]
        key = ("%s %s %s" % (b["batch"], b["p_number"], b["strain"])).lower()
        P.append('<tr class="s-%s" data-st="%s" data-k="%s">' % (g, g, esc(key)))
        P.append('<td class="num">%d</td>' % b["seq"])
        P.append('<td><span class="chip %s">%s</span></td>' % (g, esc(STATUS_LABEL[b["status"]])))
        P.append('<td class="bat"><a href="#b%d">%s</a></td>' % (b["seq"], esc(b["batch"])))
        P.append('<td class="v">%s</td>' % esc(b["p_number"] or "—"))
        P.append('<td>%s</td>' % esc(b["strain"]))
        for key_, _lbl in OVERVIEW:
            v = b["vals"][key_]["value"]
            sev = cp.severity(v)
            P.append('<td class="v %s">%s</td>' % (sev, esc(short(v))))
        P.append("</tr>")
    P.append("</tbody></table></div></section>")

    # ---------------- detail cards ----------------
    P.append('<section>')
    P.append('<h2>Batch detail</h2>')
    P.append('<p class="sectionnote">Every parameter as printed on its certificate, grouped by panel. '
             'Certificate codes link to the source PDF in Drive.</p>')
    P.append('<div class="cards">')

    for b in batches:
        g = STATUS_GROUP[b["status"]]
        key = ("%s %s %s" % (b["batch"], b["p_number"], b["strain"])).lower()
        brows = by_seq[b["seq"]]
        P.append('<article class="card%s" id="b%d" data-st="%s" data-k="%s">'
                 % (" open-issue" if b["status"] == "open" else "", b["seq"], g, esc(key)))
        P.append('<div class="cardhead"><span class="seq">%02d</span>'
                 '<span class="name">%s</span>' % (b["seq"], esc(b["batch"])))
        if b["p_number"]:
            P.append('<span class="pnum">%s</span>' % esc(b["p_number"]))
        P.append('<span class="strain">%s</span>' % esc(b["strain"]))
        P.append('<span class="chip %s">%s</span>' % (g, esc(STATUS_LABEL[b["status"]])))
        P.append('<a class="backlink" href="#top">back to top</a>')
        P.append('</div>')
        if b["notes"]:
            P.append('<div class="cardnote">%s</div>' % esc(b["notes"]))

        # group the batch's own rows by panel, preserving source order within a panel
        buckets = {}
        for r in brows:
            k = cp.classify(r["Parameter"])
            buckets.setdefault(k, []).append(r)

        for panel_name, keys in PANELS.items():
            prows = []
            for k in keys:
                prows.extend(buckets.get(k, []))
            if not prows:
                continue
            P.append('<div class="panel"><div class="panelname">%s</div>' % esc(panel_name))
            P.append('<table class="det"><colgroup><col class="c1"><col class="c2">'
                     '<col class="c3"><col class="c4"></colgroup>')
            P.append('<thead><tr><th>Parameter</th><th>Acceptance criterion</th>'
                     '<th>Result</th><th>Certificate</th></tr></thead><tbody>')
            for r in prows:
                res = r["Result"].strip()
                sev = cp.severity(res)
                rcls = "bad" if sev == "crit" else ("flagged" if sev == "warn" else "")
                P.append("<tr>")
                P.append('<td class="param">%s</td>' % esc(r["Parameter"]))
                P.append('<td class="crit-col">%s</td>' % esc(r["Acceptance Criterion"] or "—"))
                P.append('<td class="result %s">%s</td>' % (rcls, esc(res or "—")))
                link = cp.clean_link(r["Drive File Link"])
                code = r["Certificate Code"].strip()
                date = cp.issue_date(r["Issue Date"])
                lab = r["Issuing Institution"].strip()
                label = " · ".join([x for x in (code, date) if x and x.lower() not in ("n/a", "na")])
                cell = ('<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(link), esc(label or "open"))) \
                    if link else esc(label or "—")
                if lab and lab.lower() not in ("n/a", "na"):
                    cell += '<span class="lab">%s</span>' % esc(lab)
                P.append('<td class="cert">%s</td>' % cell)
                P.append("</tr>")
            P.append("</tbody></table></div>")

        # any rows the panels do not cover (gap notes, conclusions, stability)
        extra = []
        for k in ("gap", "overall", "stability", None):
            extra.extend(buckets.get(k, []))
        if extra:
            P.append('<div class="panel"><div class="panelname">Notes, conclusions &amp; stability</div>')
            P.append('<table class="det"><colgroup><col class="c1"><col class="c2">'
                     '<col class="c3"><col class="c4"></colgroup>')
            P.append('<thead><tr><th>Parameter</th><th>Acceptance criterion</th>'
                     '<th>Result</th><th>Certificate</th></tr></thead><tbody>')
            for r in extra:
                res = r["Result"].strip()
                sev = cp.severity(res)
                rcls = "bad" if sev == "crit" else ("flagged" if sev == "warn" else "")
                link = cp.clean_link(r["Drive File Link"])
                code = r["Certificate Code"].strip()
                date = cp.issue_date(r["Issue Date"])
                label = " · ".join([x for x in (code, date) if x and x.lower() not in ("n/a", "na")])
                cell = ('<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(link), esc(label or "open"))) \
                    if link else esc(label or "—")
                P.append("<tr>")
                P.append('<td class="param">%s</td>' % esc(r["Parameter"]))
                P.append('<td class="crit-col">%s</td>' % esc(r["Acceptance Criterion"] or "—"))
                P.append('<td class="result %s">%s</td>' % (rcls, esc(res or "—")))
                P.append('<td class="cert">%s</td>' % cell)
                P.append("</tr>")
            P.append("</tbody></table></div>")

        P.append("</article>")
    P.append("</div></section>")

    P.append("""<footer>
<div><b>Data integrity.</b> Values appear exactly as printed on each certificate —
<code>N.D.</code>, <code>&lt;LOQ</code>, <code>BLQ</code> and the Macedonian
<code>Одговара / Не одговара</code> verdicts are preserved verbatim. A pass or fail is never
derived from a value: a result is marked as a finding only where the issuing laboratory says so.
Where a certificate contradicts itself the row carries a data-integrity flag rather than a silent
correction. Where a laboratory prints results without a limit column, the acceptance criterion is
drawn from the Purely Plant release specification / Ph. Eur. 3028 and marked as added for review.</div>
<div><b>Stability studies</b> — month 3, 6 and 9 at 25&nbsp;°C/60&nbsp;%&nbsp;RH and
40&nbsp;°C/75&nbsp;%&nbsp;RH — appear under each batch's notes section and are excluded from the
release columns, so they can never be read as release results.</div>
</footer>""")
    P.append("</div>")

    P.append("""<script>
var F='all', TOTAL=%d;
function setf(f){F=f;['all','open','partial','complete'].forEach(function(x){
  document.getElementById('f-'+x).setAttribute('aria-pressed', x===f?'true':'false');});flt();}
function flt(){
  var q=document.getElementById('q').value.toLowerCase().trim(), shown=0;
  var ov=document.querySelectorAll('table.ov tbody tr');
  for(var i=0;i<ov.length;i++){var r=ov[i];
    var ok=((F==='all')||(r.dataset.st===F))&&((!q)||((r.dataset.k||'').indexOf(q)>=0));
    r.style.display=ok?'':'none'; if(ok)shown++;}
  var cards=document.querySelectorAll('article.card');
  for(var j=0;j<cards.length;j++){var c=cards[j];
    var ok2=((F==='all')||(c.dataset.st===F))&&((!q)||((c.dataset.k||'').indexOf(q)>=0));
    c.style.display=ok2?'':'none';}
  document.getElementById('count').textContent=shown+' of '+TOTAL+' batches';
}
document.getElementById('q').addEventListener('input',flt);
flt();
</script>""" % n_batches)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("".join(P))
    print("Wrote %s" % out_path)
    print("batches=%d records=%d complete=%d partial=%d open=%d labs=%d"
          % (n_batches, len(rows), n_complete, n_partial, n_open, n_labs))


if __name__ == "__main__":
    main()
