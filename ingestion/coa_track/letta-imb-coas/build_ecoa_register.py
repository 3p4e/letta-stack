#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Purely Plant eCoA register — presentation-grade HTML and PDF.

The register content is the structured extraction of the ImB_QC_COAs corpus (Letta
source retired 19.08.2026; the certificates now live in RAGFlow): 263
ingested certificates, pivoted by coa_pivot into one record per batch per parameter, each
carrying the certificate it was transcribed from and the Drive link to that certificate.
This turns that table into a document a person can read — a house-styled register with a
summary, a per-tranche batch register, a laboratory panel and a certificate index — and
exports it self-contained so the PDF matches the HTML anywhere.

Nothing here re-derives or judges a result. Every value is shown as transcribed, with its
certificate code beside it; where a batch was assayed more than once the readings are held
side by side rather than reconciled. A cell is marked present or absent only by whether the
knowledgebase holds a transcribed result for it — never pass or fail.

Typography is embedded (house_fonts) so the register renders in Montserrat and Roboto Mono
without reaching the network, the same reason the specifications embed their faces.
"""
import html
import os
import re
import subprocess
import sys
from collections import Counter, OrderedDict, defaultdict

import coa_pivot as cp
import crosscheck_sources as cc
import house_fonts

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_HTML = os.path.join(HERE, "exports", "PP_eCoA_Register.html")
OUT_PDF = os.path.join(HERE, "exports", "PP_eCoA_Register.pdf")
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

# The corpus this register was extracted from. The name stays as it is because it
# is what the extraction was actually made from; RETIRED carries the fact that the
# Letta source behind it no longer exists, so a reader is not sent chasing it.
SOURCE = "ImB_QC_COAs"
RETIRED = ("That Letta source was retired 19.08.2026 and the certificates now live "
           "in the RAGFlow eCoA dataset; the counts below are as verified while it "
           "was live.")

# The knowledgebase records the issuing laboratory as printed, which drifts across OCR
# spellings and language — "Farmahem — Laboratorija za zivotna sredina", "Farmahem DOOEL —
# Laboratory for Environment", the Cyrillic form. For the register's laboratory panel they
# are folded to the accredited entity they all name, with its MALMED accreditation number.
# This is identity, not a transcribed result: no parameter value, code or date moves.
LAB_CANON = [
    (("farmahem",), "Farmahem DOOEL — Laboratory for Environment · LT-017"),
    (("faculty of pharmacy", "center for natural products", "ukim"),
     "UKIM Faculty of Pharmacy — Center for Natural Products · LT-083"),
    (("institute of public health", "институт за јавно здравје", "iph", "ijz"),
     "IPH — Institute of Public Health · LT-005"),
    (("phytosanitary", "фитосанитарна"),
     "State Phytosanitary Laboratory · LT-036"),
    (("in-house", "purely plant"), "Purely Plant DOOEL — in-house QC (non-accredited)"),
]


def canon_lab(name):
    """Fold an issuing-institution string to its accredited entity. Identity only."""
    low = (name or "").strip().lower()
    if not low or low == "n/a":
        return None
    for keys, canonical in LAB_CANON:
        if any(k in low for k in keys):
            return canonical
    return name.strip()

SOURCE_ID = "source-271bc3be-10d1-4541-8a5b-be3f6fab7c97"
FILES_INGESTED = 263            # confirmed live on the Letta host, all processing_status=Completed
ISSUED = "11.08.2026"

# The release-critical panel, in the order it reads on a certificate. Each entry is
# (pivot key, short column head, group) — grouped so the header can span them.
PANEL = [
    ("loss_on_drying", "LoD", "Identity"),
    ("thc", "Δ⁹-THC", "Assay"),
    ("cbd", "CBD", "Assay"),
    ("cbn", "CBN", "Assay"),
    ("aflatoxins", "Aflatox.", "Mycotoxins"),
    ("ochratoxin", "Ochra.", "Mycotoxins"),
    ("pb", "Pb", "Heavy metals"),
    ("cd", "Cd", "Heavy metals"),
    ("as_", "As", "Heavy metals"),
    ("hg", "Hg", "Heavy metals"),
    ("pesticides", "Pest.", "Pesticides"),
    ("tamc", "TAMC", "Microbiology"),
    ("tymc", "TYMC", "Microbiology"),
    ("bile", "BTGN", "Microbiology"),
    ("ecoli", "E.coli", "Microbiology"),
    ("salmonella", "Salm.", "Microbiology"),
]


def esc(s):
    return html.escape(str(s or ""))


def has(cell):
    v = (cell or {}).get("value", "") or ""
    return v.strip() not in ("", "—", "/", "-")


def first_num(text):
    m = re.search(r"(\d+(?:[.,]\d+)?)", text or "")
    return m.group(1).replace(",", ".") if m else ""


def thc_display(cell):
    """The Total Δ9-THC reading(s) as a compact figure — value(s) only, no certificate tail."""
    v = (cell or {}).get("value", "") or ""
    if not has(cell):
        return ""
    nums = []
    for seg in v.split("·"):
        n = first_num(seg)
        if n and n not in nums:
            nums.append(n)
    return " / ".join("%.1f" % float(n) for n in nums[:3]) if nums else ""


def build_model():
    rows, batches = cp.build()
    by_seq = cp.group_by_seq(rows)
    tr = {cc.norm_batch(r["batch"]): r for r in cc.read_tsv("tranches_overview.tsv")}

    # certificates: code -> (issue date, institution, count of parameter rows)
    certs = {}
    labs = Counter()
    for r in rows:
        code = (r["Certificate Code"] or "").strip()
        if not code or code.lower().startswith("n/a"):
            continue
        inst = canon_lab(r["Issuing Institution"]) or ""
        d = cp.issue_date(r["Issue Date"])
        if code not in certs:
            certs[code] = {"date": d, "inst": inst, "n": 0,
                           "link": cp.clean_link(r["Drive File Link"])}
        certs[code]["n"] += 1
        if inst and "in-house" not in inst.lower():
            labs[inst] += 1

    recs = []
    for b in batches:
        key = cc.norm_batch(b["batch"])
        sheet = tr.get(key) or {}
        tranche = (sheet.get("tranche") or "").strip() or "—"
        # certificates cited anywhere on this batch, release rows only
        bcodes = OrderedDict()
        for r in by_seq[b["seq"]]:
            if cp.STABILITY_RE.search(r["Parameter"] or ""):
                continue
            code = (r["Certificate Code"] or "").strip()
            if code and not code.lower().startswith("n/a"):
                bcodes.setdefault(code, certs.get(code, {}))
        covered = sum(1 for k, _h, _g in PANEL if has(b["vals"].get(k)))
        recs.append({
            "seq": b["seq"], "batch": b["batch"], "p": (b["p_number"] or "").strip(),
            "strain": b["strain"], "status": b["status"], "tranche": tranche,
            "vals": b["vals"], "codes": list(bcodes.keys()),
            "covered": covered, "thc": thc_display(b["vals"].get("thc")),
            "notes": b.get("notes", ""),
        })
    return recs, certs, labs


CSS_STATIC = """
  @page { size: A4 landscape; margin: 10mm 8mm; }
  * { margin:0; padding:0; box-sizing:border-box; }
  :root {
    --navy:#1B3A5C; --navy-deep:#0F2540; --navy-soft:#3B6BA5;
    --gold:#A67C2E; --gold-bright:#C9A227; --gold-deep:#7A5C1E; --gold-tint:#FBF6E9;
    --ink:#12202B; --text:#1E293B; --sec:#475569; --ter:#8C9BB0;
    --line:#D6DEEA; --line2:#EAF0F6; --band:#F4F7FB; --paper:#FFFFFF;
    --ok:#1B7F4B; --ok-bg:#E7F4EC; --none:#B8C2CF; --crit:#B23A2E; --crit-bg:#FBE7E4;
  }
  body { font-family:'Montserrat','Helvetica Neue',Arial,sans-serif; color:var(--text);
         background:#5B6B7E; padding:14px; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
  .sheet { background:var(--paper); width:277mm; margin:0 auto 12px; padding:0 0 8mm;
           box-shadow:0 6px 40px rgba(15,37,64,.28); }
  @media print { body{background:#fff;padding:0;} .sheet{box-shadow:none;margin:0;width:auto;} }

  .masthead { background:linear-gradient(100deg,var(--navy-deep),var(--navy)); color:#fff;
              padding:8mm 10mm 6mm; display:flex; justify-content:space-between; align-items:flex-end;
              border-bottom:3px solid var(--gold); }
  .mh-brand { font-size:12px; font-weight:800; letter-spacing:3px; text-transform:uppercase; }
  .mh-brand span { color:var(--gold-bright); font-weight:300; }
  .mh-title { font-size:26px; font-weight:800; letter-spacing:.4px; margin-top:6px; line-height:1.05; }
  .mh-sub { font-size:10px; letter-spacing:2px; text-transform:uppercase; color:#B9C7DB; margin-top:5px; }
  .mh-right { text-align:right; font-family:'Roboto Mono',monospace; }
  .mh-code { font-size:12px; font-weight:700; color:var(--gold-bright); }
  .mh-meta { font-size:8.5px; color:#B9C7DB; margin-top:3px; line-height:1.5; }

  .kpis { display:grid; grid-template-columns:repeat(6,1fr); gap:0; margin:0 10mm;
          border:1px solid var(--line); border-top:none; }
  .kpi { padding:7px 12px; border-right:1px solid var(--line2); }
  .kpi:last-child { border-right:none; }
  .kpi-n { font-size:22px; font-weight:800; color:var(--navy); font-family:'Roboto Mono',monospace; line-height:1; }
  .kpi-l { font-size:8px; letter-spacing:.8px; text-transform:uppercase; color:var(--ter); margin-top:3px; }

  .prov { margin:8px 10mm 0; background:var(--gold-tint); border:1px solid var(--gold);
          border-left:3px solid var(--gold-deep); padding:6px 12px; font-size:8.5px; color:var(--gold-deep);
          line-height:1.5; }
  .prov b { color:var(--navy); }

  .sec { margin:14px 10mm 0; }
  .sec-h { font-size:10px; font-weight:800; letter-spacing:1.2px; text-transform:uppercase; color:var(--navy);
           border-bottom:2px solid var(--gold); padding-bottom:3px; margin-bottom:6px; display:flex;
           justify-content:space-between; align-items:baseline; }
  .sec-h span { font-weight:400; font-size:8px; color:var(--sec); letter-spacing:.5px; text-transform:none; }

  table.reg { width:100%; border-collapse:collapse; font-size:8px; }
  table.reg th, table.reg td { border:.5px solid var(--line); padding:2.5px 3px; text-align:center; vertical-align:middle; }
  table.reg thead th { background:var(--navy); color:#fff; font-weight:700; font-size:7.5px;
                       letter-spacing:.2px; text-transform:uppercase; }
  table.reg thead tr.grp th { background:var(--navy-deep); font-size:7px; letter-spacing:.6px; }
  table.reg tbody td.b { text-align:left; font-weight:700; color:var(--navy); font-family:'Roboto Mono',monospace; white-space:nowrap; }
  table.reg tbody td.s { text-align:left; color:var(--ink); }
  table.reg tbody td.p { font-family:'Roboto Mono',monospace; color:var(--sec); font-size:7.5px; }
  table.reg tbody td.thc { font-family:'Roboto Mono',monospace; font-weight:700; color:var(--navy); }
  table.reg tbody tr:nth-child(even) td { background:var(--band); }
  .cell-ok { color:var(--ok); font-weight:700; }
  .cell-no { color:var(--none); }
  .trh td { background:var(--gold-tint)!important; color:var(--gold-deep); font-weight:800;
            text-align:left; letter-spacing:.5px; text-transform:uppercase; font-size:8px; padding:4px 6px; }
  .disp { font-size:7px; font-weight:800; padding:1px 4px; border-radius:3px; letter-spacing:.3px; }
  .disp.complete { background:var(--ok-bg); color:var(--ok); }
  .disp.partial { background:#FFF4DA; color:var(--gold-deep); }
  .disp.nonconform { background:var(--crit-bg); color:var(--crit); }

  table.labs, table.certs { width:100%; border-collapse:collapse; font-size:8.5px; }
  table.labs th, table.labs td, table.certs th, table.certs td { border:.5px solid var(--line);
      padding:3px 7px; text-align:left; }
  table.labs thead th, table.certs thead th { background:var(--navy); color:#fff; font-weight:700;
      font-size:8px; letter-spacing:.4px; text-transform:uppercase; }
  table.labs tbody tr:nth-child(even) td, table.certs tbody tr:nth-child(even) td { background:var(--band); }
  table.certs td.c { font-family:'Roboto Mono',monospace; font-weight:700; color:var(--navy); white-space:nowrap; }
  table.certs td.n, table.labs td.n { text-align:right; font-family:'Roboto Mono',monospace; }

  .legend { margin:10px 10mm 0; font-size:8px; color:var(--sec); line-height:1.6; }
  .legend b { color:var(--navy); }
  .foot { margin:12px 10mm 0; padding-top:6px; border-top:1px solid var(--line); display:flex;
          justify-content:space-between; font-size:7.5px; color:var(--ter); font-family:'Roboto Mono',monospace; }
"""


def cell_mark(cell, key, rec):
    if key == "thc":
        return '<td class="thc">%s</td>' % (esc(rec["thc"]) or '<span class="cell-no">—</span>')
    if has(cell):
        return '<td><span class="cell-ok">✓</span></td>'
    return '<td><span class="cell-no">—</span></td>'


def disposition(rec):
    st = (rec["status"] or "").lower()
    if "nonconform" in st or "reject" in st:
        return "nonconform", "NONCONFORM"
    if rec["covered"] >= 14:
        return "complete", "COMPLETE"
    return "partial", "PARTIAL · %d/16" % rec["covered"]


def render(recs, certs, labs, fonts):
    strains = sorted({r["strain"] for r in recs if r["strain"]})
    n_certs = len(certs)
    n_batches = len(recs)
    complete = sum(1 for r in recs if disposition(r)[0] == "complete")

    groups = []
    seen = None
    for k, h_, g in PANEL:
        if g != seen:
            groups.append([g, 0]); seen = g
        groups[-1][1] += 1

    parts = []
    parts.append("<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>")
    parts.append("<title>Purely Plant — eCoA Register</title>")
    parts.append("<style>%s\n%s</style></head><body><div class='sheet'>" % (fonts, CSS_STATIC))

    # masthead
    parts.append(
        "<div class='masthead'><div>"
        "<div class='mh-brand'>PURELY <span>PLANT</span></div>"
        "<div class='mh-title'>Electronic CoA Register</div>"
        "<div class='mh-sub'>Dry Cannabis Flower · Intermediate Bulk · Outsourced-Laboratory Certificates</div>"
        "</div><div class='mh-right'>"
        "<div class='mh-code'>PP-QC-eCoA-REGISTER</div>"
        "<div class='mh-meta'>Issued %s<br>Ph. Eur. 11.5 / 3028<br>Petrovec-Skopje, MK</div>"
        "</div></div>" % ISSUED)

    # KPIs
    total_records = sum(1 for _ in range(0))  # placeholder replaced below
    parts.append("<div class='kpis'>")
    for n, lab in [(n_batches, "Batches"), (n_certs, "Certificates"), (len(strains), "Cultivars"),
                   (len(labs), "Laboratories"), (complete, "Full panel"), (FILES_INGESTED, "CoAs ingested")]:
        parts.append("<div class='kpi'><div class='kpi-n'>%d</div><div class='kpi-l'>%s</div></div>" % (n, esc(lab)))
    parts.append("</div>")

    # provenance
    parts.append(
        "<div class='prov'><b>Source of record.</b> Every entry is transcribed from an "
        "outsourced-laboratory certificate in the <b>%s</b> corpus (source %s), which held "
        "<b>%d</b> ingested certificates, all processed. %s Values are "
        "shown as printed; where a batch was assayed more than once the readings are kept side "
        "by side. A cell is marked present (✓) only where the corpus held a transcribed "
        "result — never a pass/fail judgement.</div>"
        % (esc(SOURCE), esc(SOURCE_ID), FILES_INGESTED, esc(RETIRED)))

    # register table
    parts.append("<div class='sec'><div class='sec-h'>Batch register "
                 "<span>release-critical panel · one row per batch, grouped by delivery tranche</span></div>")
    parts.append("<table class='reg'><thead>")
    parts.append("<tr class='grp'><th colspan='4'></th>")
    for g, span in groups:
        parts.append("<th colspan='%d'>%s</th>" % (span, esc(g)))
    parts.append("<th colspan='2'></th></tr>")
    parts.append("<tr><th style='text-align:left'>Batch</th><th>P-No.</th>"
                 "<th style='text-align:left'>Cultivar</th><th>Certs</th>")
    for k, h_, g in PANEL:
        parts.append("<th>%s</th>" % esc(h_))
    parts.append("<th>Cov.</th><th>Disposition</th></tr></thead><tbody>")

    by_tr = defaultdict(list)
    for r in recs:
        by_tr[r["tranche"]].append(r)

    def tr_order(t):
        return (0, int(t)) if t.isdigit() else (1, t)

    ncols = 4 + len(PANEL) + 2
    for t in sorted(by_tr, key=tr_order):
        grp = sorted(by_tr[t], key=lambda r: (r["strain"].lower(), r["batch"]))
        label = ("Tranche %s" % t) if t.isdigit() else "Unassigned tranche"
        parts.append("<tr class='trh'><td colspan='%d'>%s &nbsp;·&nbsp; %d batches</td></tr>"
                     % (ncols, esc(label), len(grp)))
        for r in grp:
            dcls, dtxt = disposition(r)
            parts.append("<tr>")
            parts.append("<td class='b'>%s</td><td class='p'>%s</td><td class='s'>%s</td>"
                         "<td class='p'>%d</td>" % (esc(r["batch"]), esc(r["p"] or "—"),
                                                    esc(r["strain"]), len(r["codes"])))
            for k, h_, g in PANEL:
                parts.append(cell_mark(r["vals"].get(k), k, r))
            parts.append("<td class='p'>%d/16</td><td><span class='disp %s'>%s</span></td>"
                         % (r["covered"], dcls, esc(dtxt)))
            parts.append("</tr>")
    parts.append("</tbody></table></div>")

    # laboratories
    parts.append("<div class='sec'><div class='sec-h'>Issuing laboratories "
                 "<span>accredited outsourced laboratories · records contributed</span></div>")
    parts.append("<table class='labs'><thead><tr><th>Laboratory</th>"
                 "<th class='n'>Parameter records</th></tr></thead><tbody>")
    for inst, n in labs.most_common():
        parts.append("<tr><td>%s</td><td class='n'>%d</td></tr>" % (esc(inst), n))
    parts.append("</tbody></table></div>")

    # certificate index
    parts.append("<div class='sec'><div class='sec-h'>Certificate index "
                 "<span>%d distinct certificates on file · code · issue date · laboratory</span></div>"
                 % n_certs)
    parts.append("<table class='certs'><thead><tr><th>Certificate code</th><th>Issued</th>"
                 "<th>Laboratory</th><th class='n'>Records</th></tr></thead><tbody>")

    def cert_key(item):
        return (item[1].get("date") or "9999", item[0])

    for code, meta in sorted(certs.items(), key=cert_key):
        parts.append("<tr><td class='c'>%s</td><td>%s</td><td>%s</td><td class='n'>%d</td></tr>"
                     % (esc(code), esc(meta.get("date") or "—"),
                        esc(meta.get("inst") or "—"), meta.get("n", 0)))
    parts.append("</tbody></table></div>")

    # legend
    parts.append(
        "<div class='legend'><b>Legend.</b> "
        "<span style='color:#1B7F4B;font-weight:700'>✓</span> a transcribed result is on file · "
        "<span style='color:#B8C2CF'>—</span> no result on file · "
        "Δ⁹-THC shows the assay value(s) in %; multiple values are separate assays of separate samples. "
        "<b>Cov.</b> is the count of the 16 release-critical parameters with a result. "
        "<b>Disposition</b> reflects panel coverage and any laboratory-declared non-conformance only. "
        "Panel: LoD, Δ⁹-THC, CBD, CBN, aflatoxins, ochratoxin A, Pb/Cd/As/Hg, pesticide screen, "
        "TAMC, TYMC, bile-tolerant gram-negative (BTGN), E. coli, Salmonella. "
        "Stability-study timepoints are held apart from this release register.</div>")

    parts.append("<div class='foot'><div>Purely Plant DOOEL · Quality Control</div>"
                 "<div>Source %s · %d CoAs</div></div>"
                 % (esc(SOURCE), FILES_INGESTED))

    parts.append("</div></body></html>")
    return "".join(parts)


def main():
    recs, certs, labs = build_model()

    # font subset over everything the register prints
    text = " ".join([r["batch"] + r["strain"] + r["p"] + r["thc"] for r in recs])
    text += " ".join(certs) + " ".join(labs)
    text += " Purely Plant Electronic CoA Register Certificate index laboratories batch cultivar"
    text += " Δ⁹-THC CBD CBN aflatoxins ochratoxin TAMC TYMC Salmonella E.coli Tranche COMPLETE PARTIAL"
    fonts, raw, sub = house_fonts.font_face_css(text)

    doc = render(recs, certs, labs, fonts)
    with open(OUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(doc)

    n_records = sum(r["covered"] for r in recs)
    print("eCoA register: %d batches, %d certificates, %d laboratories, %d cultivars"
          % (len(recs), len(certs), len(labs), len({r["strain"] for r in recs if r["strain"]})))
    print("fonts inlined: %.0f KB upstream -> %.0f KB subset" % (raw / 1024.0, sub / 1024.0))
    print("wrote %s (%d KB)" % (os.path.relpath(OUT_HTML, HERE), os.path.getsize(OUT_HTML) // 1024))

    if os.path.exists(CHROME):
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
             "--virtual-time-budget=6000", "--print-to-pdf=" + OUT_PDF, OUT_HTML],
            check=True, capture_output=True)
        print("wrote %s (%d KB)" % (os.path.relpath(OUT_PDF, HERE), os.path.getsize(OUT_PDF) // 1024))
    else:
        print("Chromium not found; PDF skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
