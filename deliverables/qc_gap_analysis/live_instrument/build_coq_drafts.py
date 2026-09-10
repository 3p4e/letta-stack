#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compile draft Certificates of Quality in bulk — with the desk's own compiler.

    python3 deliverables/qc_gap_analysis/live_instrument/build_coq_drafts.py \
        --scope deliverables/qc_gap_analysis/tracker/coq_draft_scope_2026-09-10.csv

The Quality Desk already compiles a CoQ: fillCoq() in script.js clones the
owner's master (_CoQ_MASTER_Template.html) and fills it from the desk record.
Nothing here re-implements that. The page is opened in headless Chromium and
fillCoq() is called once per lot, so a document produced in bulk is the same
document a person gets by clicking the batch on the desk — same master, same
verbatim results, same controlled blanks, same DRAFT watermark.

Three things come back out of the browser, and the last two are read off the
compiled page itself rather than predicted from the record: the documents;
every printed line that came out blank; and every result that does not fit the
column the master gives it and runs off the sheet. A blank line is not a defect
in the compiler — it is the desk saying it holds no transcribed result for that
determination — so the report is the list of transcriptions a person must make
before any of these drafts can be signed, and of the lines a reader would not
be able to read if they were printed today.

Outputs, under deliverables/qc_gap_analysis/drafts/:
  DRAFT_CoQ_<P lot>.html            one A4 document per lot
  Tranche_1_2_CoQ_Draft_Set.html    all of them, one page each, print-ready
  coq_draft_gaps.csv                every blank and every over-running result
"""
import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)

# Read off the compiled document: for each lot, the documents and their blanks.
# DOMParser is used on fillCoq's own output so what is measured is what prints.
EXTRACT = r"""
(lots) => {
  const out = [];
  const host = document.createElement("iframe");
  host.setAttribute("style", "position:fixed;left:-9999px;width:794px;height:1123px;border:0");
  document.body.appendChild(host);
  for (const lot of lots) {
    const i = COQ.findIndex(c => c.pp === lot.p_lot && c.t === "initial release");
    if (i < 0) { out.push({ p_lot: lot.p_lot, error: "no initial-release record" }); continue; }
    const c = COQ[i];
    const html = fillCoq(c);
    host.contentDocument.open(); host.contentDocument.write(html); host.contentDocument.close();
    const doc = host.contentDocument;
    const sheet = doc.querySelector("div.page").getBoundingClientRect();
    const num = t => parseFloat(String(t).replace(",", "."));
    /* The acceptance criterion as a numeric band, or null where it is not one.
       Superscripts, ^ and LOQ mark a criterion this cannot read as a number —
       "≤ 10⁴ CFU/g" would otherwise read as a limit of ten. */
    const critBand = c => {
      const s = (c || "").replace(/\s+/g, " ").trim();
      if (!s || /[\u2070-\u209f^]|LOQ/i.test(s)) return null;
      let m = s.match(/(\d+(?:[.,]\d+)?)\s*[\u2013\u2014-]\s*(\d+(?:[.,]\d+)?)/);
      if (m) return { lo: num(m[1]), hi: num(m[2]) };
      m = s.match(/^(\u2264|<=|<|\u2265|>=|>)\s*(\d+(?:[.,]\d+)?)/);
      if (!m) return null;
      return /[\u2264<]/.test(m[1]) ? { lo: null, hi: num(m[2]) }
                                     : { lo: num(m[2]), hi: null };
    };
    /* A result that is a plain measured number, with or without its unit. A
       result that is itself a bound, a non-detection or a conformity word is
       not one, and returns null. */
    const plainNum = t => {
      const m = String(t || "").replace(/\s+/g, "").replace(/\*+$/, "")
        .match(/^(\d+(?:[.,]\d+)?)(%|mg\/kg|\u00b5g\/kg|%w\/w)?$/i);
      return m ? num(m[1]) : null;
    };
    const blanks = [], over = [], band = [];
    let head = null, sub = 0;
    doc.querySelectorAll("table.results tbody tr").forEach(tr => {
      const tds = tr.querySelectorAll("td");
      if (tr.classList.contains("row-group")) {
        head = { no: tds[0].textContent.trim(), name: tr.querySelector(".p-name").textContent.trim() };
        sub = 0; return;
      }
      /* a blank result now prints as the bracketed marker rather than a bare
         em dash; the report follows the compiler, or it would read "0 gaps" */
      /* only inside the result cell: row 4's acceptance criterion now carries a
         bracketed placeholder too, and it comes first in document order */
      const val = tr.querySelector("td.r-cell .r-val, td.r-cell .todo");
      if (!val) return;
      const nm = tr.querySelector(".p-name, .p-sub");
      let no = tds[0].textContent.trim();
      let name = nm ? nm.textContent.trim() : "";
      /* a sub-row prints no number of its own: it belongs to the group above,
         and the desk numbers those 9.1, 10.2 and so on. Count within the group
         so the gap report names the line the way the schedule names it. */
      if (!no && head) { sub += 1; no = head.no + "." + sub; name = head.name + " · " + name; }
      const txt = val.textContent.trim();
      /* a blank prints as the bracketed marker; [—] is the one that means the
         desk holds nothing for this line. */
      if (txt === "—" || txt === "[—]") { blanks.push({ no: no, name: name }); return; }
      if (val.classList.contains("todo")) return;      /* a placeholder, not a result */
      /* the master sets the result column at a fixed width and .r-val nowrap,
         so a long verbatim result does not wrap. The result column is the last
         one, so what it overflows into is the page margin and then the edge of
         the sheet. Measured on the compiled page at A4 width, not guessed.
         Geometry, so it is measured on every result — before any question
         about the criterion beside it, which some rows decline to answer. */
      const px = Math.round(val.getBoundingClientRect().right - sheet.right);
      if (px > 0) over.push({ no: no, name: name, text: txt, px: px });
      /* Whether a result sits inside the criterion the certificate prints next
         to it is decided HERE, in the report, and never on the document: the
         master's acceptance-criteria column is the master's. The comparison is
         attempted only where both sides are plainly numeric — an absence test,
         a limit of detection, or a result that is itself a bound ("< 10") is
         left alone rather than guessed at, so a finding here is a real one. */
      const cel = tr.querySelector(".p-spec");
      /* Two criteria this must not read as numbers, and textContent hides both:
         the master marks its powers of ten up as <sup>, so "≤ 10⁵ CFU/g" comes
         out "≤ 105 CFU/g" and every microbiological count would read as a
         failure; and the row-4 range is the bracketed placeholder the owner
         supplies separately, so there is no band to be outside of yet. */
      if (!cel || cel.querySelector("sup") || cel.querySelector(".todo")) return;
      const crit = cel.textContent;
      const b = critBand(crit), v = plainNum(txt);
      if (b && v !== null &&
          ((b.lo !== null && v < b.lo) || (b.hi !== null && v > b.hi))) {
        band.push({ no: no, name: name, text: txt, crit: crit.replace(/\s+/g, " ").trim() });
      }
    });
    const lk = {};
    doc.querySelectorAll(".lk").forEach(s => {
      const l = s.querySelector(".l"), v = s.querySelector(".v");
      if (l && v) lk[l.textContent.trim()] = v.textContent.trim();
    });
    const pot = doc.querySelector(".pbp-val");
    out.push({
      p_lot: c.pp, cb: c.cb, strain: c.strain, thc: pot ? pot.textContent.trim() : "",
      name: coqDocName(c), lk: lk, blanks: blanks, over: over, band: band, html: html,
      labs: doc.querySelectorAll("table.labref tbody tr").length,
    });
  }
  return out;
}
"""


def page_body(html):
    """The <div class="page"> of one compiled document, and the head it needs."""
    a = html.index('<div class="page">')
    b = html.rindex("</body>")
    return html[a:b]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", required=True, help="CSV with tranche, p_lot and draftable columns")
    ap.add_argument("--artifact", default=os.path.join(GAP, "qc_quality_desk_artifact.html"))
    ap.add_argument("--out", default=os.path.join(GAP, "drafts"))
    ap.add_argument("--chromium", default=os.environ.get("CHROMIUM_PATH", ""),
                    help="browser executable; defaults to whatever Playwright resolves")
    ap.add_argument("--title", default="Tranche 1 &amp; 2 — Certificates of Quality (DRAFT)")
    args = ap.parse_args()

    rows = [r for r in csv.DictReader(open(args.scope, encoding="utf-8"))
            if r["draftable"].strip() == "yes"]
    if not rows:
        print("nothing marked draftable in " + args.scope, file=sys.stderr)
        return 1
    os.makedirs(args.out, exist_ok=True)

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=args.chromium or None)
        pg = br.new_page()
        pg.goto("file://" + os.path.abspath(args.artifact))
        pg.wait_for_function("typeof COQ !== 'undefined' && typeof fillCoq === 'function'")
        docs = pg.evaluate(EXTRACT, [{"p_lot": r["p_lot"]} for r in rows])
        br.close()

    tranche = {r["p_lot"]: r["tranche"] for r in rows}
    bad = [d for d in docs if d.get("error")]
    for d in bad:
        print("!! " + d["p_lot"] + ": " + d["error"], file=sys.stderr)
    docs = [d for d in docs if not d.get("error")]

    gaps = [["tranche", "p_lot", "cultivation batch", "strain", "determination",
             "printed line", "finding", "detail"]]
    for d in docs:
        with open(os.path.join(args.out, d["name"]), "w", encoding="utf-8") as fh:
            fh.write(d["html"])
        for b in d["blanks"]:
            gaps.append([tranche[d["p_lot"]], d["p_lot"], d["cb"], d["strain"],
                         b["no"] or "—", b["name"], "blank",
                         "no transcribed result on the desk for this line"])
        for b in d["band"]:
            gaps.append([tranche[d["p_lot"]], d["p_lot"], d["cb"], d["strain"],
                         b["no"] or "—", b["name"], "outside its printed band",
                         "the result %s falls outside the acceptance criterion printed "
                         "beside it: %s" % (b["text"], " ".join(b["crit"].split())[:90])])
        for o in d["over"]:
            gaps.append([tranche[d["p_lot"]], d["p_lot"], d["cb"], d["strain"],
                         o["no"] or "—", o["name"], "runs off the sheet",
                         "the result runs %d px past the edge of the sheet and "
                         "is cut off in print: %s" % (o["px"], o["text"])])
    with open(os.path.join(args.out, "coq_draft_gaps.csv"), "w", newline="",
              encoding="utf-8") as fh:
        csv.writer(fh).writerows(gaps)

    # The combined set: one head, then every page. Every document comes off the
    # same master, so the stylesheet is the same stylesheet — carried once.
    first = docs[0]["html"]
    head = first[:first.index("<body>")] + "<body>\n"
    head += ('<style>div.page{page-break-after:always;break-after:page}'
             'div.page:last-of-type{page-break-after:auto;break-after:auto}</style>\n')
    parts = [head]
    for d in sorted(docs, key=lambda x: (tranche[x["p_lot"]], x["p_lot"])):
        parts.append(page_body(d["html"]))
    parts.append("</body>\n</html>\n")
    combined = os.path.join(args.out, "Tranche_1_2_CoQ_Draft_Set.html")
    with open(combined, "w", encoding="utf-8") as fh:
        fh.write("".join(parts))

    n1 = sum(1 for d in docs if tranche[d["p_lot"]] == "1")
    print("%d documents (%d Tranche 1, %d Tranche 2) -> %s"
          % (len(docs), n1, len(docs) - n1, args.out))
    print("%s: %.0f KiB" % (combined, os.path.getsize(combined) / 1024))
    nb = sum(len(d["blanks"]) for d in docs)
    no = sum(len(d["over"]) for d in docs)
    nd = sum(len(d["band"]) for d in docs)
    print("%d blank printed lines, %d results outside their printed band and %d that "
          "run off the sheet, across %d documents" % (nb, nd, no, len(docs)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
