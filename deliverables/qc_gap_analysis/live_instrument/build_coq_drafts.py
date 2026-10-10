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

With --series reissue and the reissue scope (tracker/coq_reissue_scope_2026-09-15.csv)
the same compiler produces the 12-month reissues instead — DRAFT_CoQ_<lot>_reissue.html,
Tranche_1_2_CoQ_Reissue_Draft_Set.html and coq_reissue_draft_gaps.csv. A reissue
prints, under its date of issue, the small bracketed line "(supersedes <code> of
<date>)" naming the initial certificate it replaces (owner, 15.09.2026); the build
reads that line back off every compiled page and names any reissue without one.
"""
import argparse
import csv
import json
import os
import re
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
    /* the initial certificate of a lot, or — series "reissue" — its 12-month
       reissue. A lot with no packaged-lot number is carried under its
       cultivation batch, so a reissue is matched on either name. */
    const reissue = lot.series === "reissue";
    const i = COQ.findIndex(c => reissue
      ? (c.t.indexOf("retest") === 0 && (c.pp === lot.p_lot || (!c.pp && c.cb === lot.p_lot)))
      : (c.pp === lot.p_lot && c.t === "initial release"));
    if (i < 0) { out.push({ p_lot: lot.p_lot, error: reissue ? "no reissue record" : "no initial-release record" }); continue; }
    const c = COQ[i];
    let html = fillCoq(c);
    host.contentDocument.open(); host.contentDocument.write(html); host.contentDocument.close();
    const doc = host.contentDocument;
    const pageEl = doc.querySelector("div.page");
    const sheet = pageEl.getBoundingClientRect();
    /* Does the document still fit one A4 page? The master sets div.page to A4
       and clips with overflow:hidden, so content past the bottom edge does not
       announce itself — it is simply gone from the printed sheet. Every change
       that adds a line risks it: the 11.09 rulings removed 36 rows for untested
       analytes and then added a second line to the conformity results.

       Two things make this an EARLY WARNING and not the verdict. It must be
       measured inside this A4 iframe, because reading scrollHeight on a page
       that is itself clipped returns the clipped height and always says zero —
       the overflow is invisible to the element that is hiding it. And the HTML
       drafts carry no embedded fonts (only print_coq_pdfs.py inlines them), so
       what is measured here is the FALLBACK metric, which runs taller than
       Montserrat. A document named here needs checking against the rendered
       PDF, which is the sheet a person actually holds. */
    const tall = Math.round(pageEl.scrollHeight - pageEl.clientHeight);
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
    /* Section 01 read back off the printed page: the master's lockups are
       .lk-lbl / .lk-val (and .attr-val for the three attribute blocks), the
       label carrying its Macedonian twin in a .mk child. Until 16.09.2026 this
       queried .l / .v, which the master has never had, so it read nothing and
       nothing downstream noticed — the same gap that let the title survive. */
    const lk = {};
    doc.querySelectorAll(".lk").forEach(s => {
      const l = s.querySelector(".lk-lbl"), v = s.querySelector(".lk-val, .attr-val");
      if (!l || !v) return;
      const lbl = Array.from(l.childNodes).filter(n => n.nodeType === 3).map(n => n.textContent).join("").trim();
      if (lbl) lk[lbl] = v.textContent.replace(/\s+/g, " ").trim();
    });
    const pot = doc.querySelector(".pbp-val");
    /* the header band: the document code, the date of issue and — on a reissue
       — the small bracketed line naming the certificate it supersedes. The
       line is measured against the sheet like any result: nowrap text that
       outgrows the header's right column would run off the page unannounced. */
    const codeEl = doc.querySelector(".hb-code"), issEl = doc.querySelector(".hb-issue b");
    const supEl = doc.querySelector(".hb-supersedes");
    if (supEl) {
      const r = supEl.getBoundingClientRect();
      const px = Math.max(Math.round(r.right - sheet.right), Math.round(sheet.left - r.left));
      if (px > 0) over.push({ no: "—", name: "header · supersedes line", text: supEl.textContent.trim(), px: px });
    }
    /* The document must name ITSELF in its title. The master carries a literal
       <title> from the lot it was authored on, and until 16.09.2026 fillCoq never
       rewrote it, so every draft the desk had produced went out carrying another
       lot's code, strain, grade and batch in the browser tab and in the PDF
       metadata — 73 of 73 said "CoQ-PP-2026-0005 — Amsterdam Amnesia (AA) —
       Grade I — Batch P060052". The compiler writes the title now (fillCoq, so
       the desk's own Print and Save HTML carry it as well as this build); this
       build only READS it back, like every other field, and the Python side
       refuses a document whose title does not name its own lot and code. */
    const titleEl = doc.querySelector("title");
    const titleText = titleEl ? titleEl.textContent.trim() : "";

    out.push({
      title: titleText,
      p_lot: lot.p_lot, cb: c.cb, strain: c.strain, thc: pot ? pot.textContent.trim() : "",
      code: codeEl ? codeEl.textContent.trim() : "",
      issue: issEl ? issEl.textContent.trim() : "",
      supersedes: supEl ? supEl.textContent.trim() : "",
      name: coqDocName(c).replace(/\.html$/, reissue ? "_reissue.html" : ".html"),
      lk: lk, blanks: blanks, over: over, band: band, html: html,
      tall: tall,
      labs: doc.querySelectorAll("table.labref tbody tr").length,
      /* Section 03 read back as printed: the laboratory name of every row, so a
         laboratory that appears twice — one institution the export spells two
         ways, its parameters split between the rows — is reported at build time
         rather than shipped on 20 of 73 certificates unnoticed. */
      labrows: Array.from(doc.querySelectorAll("table.labref tbody tr")).map(tr => {
        const td = tr.querySelectorAll("td");
        const nm = tr.querySelector(".lr-lab");
        return { lab: nm ? (nm.firstChild ? nm.firstChild.textContent : nm.textContent).trim() : "",
                 codes: td[1] ? td[1].textContent.trim() : "",
                 nos: td[2] ? td[2].textContent.trim() : "" };
      }),
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
    ap.add_argument("--title", default=None)
    ap.add_argument("--series", choices=("initial", "reissue"), default="initial",
                    help="initial: the lot's initial-release certificate (default); "
                         "reissue: its 12-month reissue, which names the certificate it supersedes")
    args = ap.parse_args()
    reissue = args.series == "reissue"
    if args.title is None:
        args.title = ("Tranche 1 &amp; 2 — Reissued Certificates of Quality (DRAFT)" if reissue
                      else "Tranche 1 &amp; 2 — Certificates of Quality (DRAFT)")
    set_name = "Tranche_1_2_CoQ_Reissue_Draft_Set.html" if reissue else "Tranche_1_2_CoQ_Draft_Set.html"
    gaps_name = "coq_reissue_draft_gaps.csv" if reissue else "coq_draft_gaps.csv"

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
        docs = pg.evaluate(EXTRACT, [{"p_lot": r["p_lot"], "series": args.series} for r in rows])
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
    with open(os.path.join(args.out, gaps_name), "w", newline="",
              encoding="utf-8") as fh:
        csv.writer(fh).writerows(gaps)

    # The combined set: one head, then every page. Every document comes off the
    # same master, so the stylesheet is the same stylesheet — carried once.
    first = docs[0]["html"]
    # <body> carries attributes now — data-untested names the sub-determinations
    # the compiler removed because the laboratory never tested them — so the head
    # is split on the tag, not on a literal string. The combined set opens its own
    # <body> and each page is spliced in beneath it.
    _m = re.search(r"<body\b[^>]*>", first)
    if _m is None:
        raise SystemExit("compiled document has no <body>: " + docs[0]["p_lot"])
    head = first[:_m.start()] + "<body>\n"
    head += ('<style>div.page{page-break-after:always;break-after:page}'
             'div.page:last-of-type{page-break-after:auto;break-after:auto}</style>\n')
    parts = [head]
    for d in sorted(docs, key=lambda x: (tranche[x["p_lot"]], x["p_lot"])):
        parts.append(page_body(d["html"]))
    parts.append("</body>\n</html>\n")
    combined = os.path.join(args.out, set_name)
    with open(combined, "w", encoding="utf-8") as fh:
        fh.write("".join(parts))

    n1 = sum(1 for d in docs if tranche[d["p_lot"]] == "1")
    print("%d %sdocuments (%d Tranche 1, %d Tranche 2) -> %s"
          % (len(docs), "reissued " if reissue else "", n1, len(docs) - n1, args.out))
    # What the header band prints, read off the compiled page: the register's
    # code and date, and — on a reissue — the supersedes line. A reissue that
    # prints no supersedes line, or no code, is named: it is not a defect of the
    # compiler but a certificate the register has not numbered.
    nocode = [d for d in docs if not d.get("code", "").startswith("CoQ-PP_26-")]
    print("%d of %d print a CoQ Register code in the header; %d print the register's date of issue"
          % (len(docs) - len(nocode), len(docs), sum(1 for d in docs if re.match(r"^\d\d\.\d\d\.\d{4}$", d.get("issue", "")))))
    for d in nocode:
        print("    %-12s header code reads %r" % (d["p_lot"], d.get("code", "")))
    # Every document must name ITSELF in its title, read back off the compiled
    # page. Until 16.09.2026 none did: the master's literal <title> named the lot
    # it was authored on and fillCoq never replaced it, so all 73 drafts carried
    # "CoQ-PP-2026-0005 — Amsterdam Amnesia (AA) — Grade I — Batch P060052".
    # Nothing on the desk was reading the title, which is why it survived every
    # verification pass, so it is read back here beside the header band.
    badtitle = [d for d in docs
                if (d.get("p_lot") or "") not in (d.get("title") or "")
                or (d.get("code") or "") not in (d.get("title") or "")]
    print("%d of %d print their own lot and document code in the title"
          % (len(docs) - len(badtitle), len(docs)))
    for d in badtitle:
        print("    %-12s title reads %r" % (d["p_lot"], d.get("title", "")))
    # Section 03 read back: one laboratory, one row. The export spells an
    # institution more than one way and the compiler used to key on the spelling,
    # so 20 of 73 certificates printed the same laboratory twice — 14 of them with
    # the identical code and date on both rows and the parameters it covers split
    # between them.
    duplab = []
    for d in docs:
        names = [r.get("lab", "") for r in (d.get("labrows") or []) if r.get("lab")]
        for n in sorted(set(names)):
            if names.count(n) > 1:
                duplab.append((d.get("p_lot"), n, names.count(n)))
    print("%d of %d print each laboratory on one row of Section 03"
          % (len(docs) - len({x[0] for x in duplab}), len(docs)))
    for lot, n, k in duplab:
        print("    %-12s %s on %d rows" % (lot, n[:56], k))

    # Section 01, read back off the page the same way: the production batch the
    # lockup prints must be the document's own P lot, and the potency and the
    # specification reference must be there at all. Until 16.09.2026 this read-back
    # queried classes the master does not have and so read nothing.
    bad01 = [d for d in docs
             if (d.get("p_lot") or "").startswith("P")
             and ((d.get("lk") or {}).get("Prod. Batch №") != d["p_lot"]
                  or not (d.get("lk") or {}).get("Potency") or not (d.get("lk") or {}).get("Spec. Ref."))]
    print("%d of %d print their own P lot, a potency and a specification reference in Section 01"
          % (len(docs) - len(bad01), len(docs)))
    for d in bad01:
        print("    %-12s Section 01 reads %r" % (d["p_lot"], d.get("lk", {})))
    if reissue:
        nosup = [d for d in docs if not d.get("supersedes", "").startswith("(supersedes CoQ-PP_26-")]
        print("%d of %d reissues print a supersedes line naming the initial certificate's register code"
              % (len(docs) - len(nosup), len(docs)))
        for d in nosup:
            print("    %-12s supersedes line reads %r" % (d["p_lot"], d.get("supersedes", "")))
    print("%s: %.0f KiB" % (combined, os.path.getsize(combined) / 1024))
    nb = sum(len(d["blanks"]) for d in docs)
    no = sum(len(d["over"]) for d in docs)
    nd = sum(len(d["band"]) for d in docs)
    print("%d blank printed lines, %d results outside their printed band and %d that "
          "run off the sheet, across %d documents" % (nb, nd, no, len(docs)))
    # One A4 page is a requirement of the document, not a preference, and
    # div.page clips with overflow:hidden — content past the bottom edge is
    # simply absent from the printed sheet, silently. So it is reported on every
    # build, and a document that no longer fits is named.
    tall = [d for d in docs if d.get("tall", 0) > 0]
    if tall:
        print("PAST THE BOTTOM OF THE SHEET in fallback fonts — %d document(s), "
              "check against the rendered PDF:" % len(tall))
        for d in sorted(tall, key=lambda x: -x["tall"]):
            print("    %-10s %d px past the page" % (d["p_lot"], d["tall"]))
    else:
        print("every document fits one A4 page, even in fallback fonts")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
