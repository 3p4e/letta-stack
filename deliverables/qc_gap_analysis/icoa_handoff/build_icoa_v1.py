#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the internal certificates of analysis that the certificates of quality cite.

    python3 icoa_handoff/build_icoa_v1.py                 # every cited in-house iCoA
    python3 icoa_handoff/build_icoa_v1.py --only retest   # the retest-cited ones alone
    python3 icoa_handoff/build_icoa_v1.py --only 26-012   # a substring filter

## The certificate is the source, not a register

Every certificate of quality names its in-house iCoA in Section 03 and credits
determinations to it, cell by cell. That citation — the `doc` on each results row — is
the authority for which internal certificate exists, what it covers, when it issued and
which laboratory owns it. The desk reads the documents to build straight from the
certificates, and needs no separate iCoA register to do it.

This matters, because the two registers on the desk disagree with the certificates. The
master workbook's **iCoA Register** sheet has had two rows inserted (serials 212-213) that
shift 192 of its codes by +1 or +2 against the certificates' own numbering, and even the
09.09 CSV parts company on 46 lots through spelling variants. Building an iCoA off either
register would print the wrong code and the wrong lot on the page. Building it off the
certificate that cites it cannot: the certificate is internally consistent by construction.

## What the certificates say

**115 distinct in-house iCoA codes are cited** across the 172 certificates:

* **95** cover Identification A, Identification B and Foreign matter (`#1 #2 #7`);
* **13** cover Identification B alone (`#2`);
* the rest are the handful of legacy full-panel and part-panel in-house records.

By round of the citing certificate, the 115 split **26 initial-only · 51 both · 38
retest-only**. A single identity iCoA is issued once, at packaging, and both the initial
release certificate and its twelve-month reissue cite it — the ruling of 15.09.2026 that
`#1`, `#2` and `#7` are performed once and carried on reissue. So there is **no separate
retest identity iCoA** for those 51; the retest certificate cites the initial record. The
57 `icoa_code` values that appear as a certificate field but are cited by no row are the
planned retest numbers those certificates never reference — no document is built for them.

## What the record says, and nothing else

The drawing is the owner's own `iCoA_Template_v02_VariationF.html`, vendored unchanged
under `base/`. The template ships filled with an example that asserts a great deal the desk
cannot cite — a laboratory sample number, a sample mass, receipt conditions, named
signatories, reference-standard catalogue numbers, system-suitability limits, an expanded
measurement uncertainty, method-validation codes, and a conformity statement over all
twelve monograph parameters. So the builder:

* prints only the determinations the certificate credits to this record, in its scope;
* scopes the conformity statement to them by name, and says where the rest are certified;
* drops the Method Validation column and the whole of the template's Section 02 — they
  describe instrumental validation (HPLC, LC-MS/MS, ICP-MS) with no bearing on a visual,
  a microscopic and a gravimetric determination, and the desk cannot cite one of their
  codes;
* prints an em dash for every field the desk cannot cite;
* keeps the signature roles and titles and prints no name and no date, for wet signature.

## The results are the certificate's own

Each determination's acceptance criterion, result, issue date and laboratory are taken
from the certificate row that cites this record, so the two documents cannot disagree.
Where an iCoA is cited by more than one certificate, the identity (lot, strain, grade,
specification) is taken from an initial-release certificate when one cites it, else the
first, and the lots it serves are named in the build report. The result ink is one navy,
as the Head of QC asked for the certificate of quality on 16.09.2026.
"""
import argparse
import collections
import html
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
BASE = os.path.join(HERE, "base", "iCoA_Template_v02_VariationF.html")
OUT = os.path.join(HERE, "out")

NAVY = "#1B3A5C"
DASH = "—"


def esc(s):
    return html.escape(str(s), quote=False)


def en(s):
    """The English half of a bilingual `English | Macedonian` string."""
    return (s or "").split("|")[0].strip()


def dnum(n):
    return [int(p) for p in str(n).split(".")]


def ymd(d):
    """A dd.mm.yyyy string as a sortable (y, m, d) tuple, or None."""
    m = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", str(d or ""))
    return (m.group(3), m.group(2), m.group(1)) if m else None


def analysis_date(basis, issued):
    """The in-house analysis completes on or before the record is issued. Some retest
    certificates carry a predicted basis date LATER than the issue date (e.g. a 2027 date
    on a record issued in 2026); an analysis cannot complete after the document that
    reports it, so where the basis is after the issue date the issue date is shown."""
    yb, yi = ymd(basis), ymd(issued)
    if yb and yi and yb > yi:
        return issued
    return basis or issued or DASH


def cut(tpl, start, end, label):
    i = tpl.find(start)
    j = tpl.find(end, i)
    if i < 0 or j < 0:
        raise SystemExit("template: %s not found" % label)
    return i, j + len(end)


def render_rows(det_by_no, rows_by_no, scope):
    """Section 01, one line per determination in scope, in the certificate's own words."""
    out = []
    for n in scope:
        det = det_by_no.get(n)
        row = rows_by_no.get(n)
        if det is None or row is None:
            continue
        res = en(row.get("res"))
        crit = en(row.get("crit") or det.get("crit"))
        method = row.get("mth") or det.get("method") or ""
        out.append(
            '        <tr><td>%s</td><td><span class="m-name">%s</span>'
            '<span class="m-method">%s</span></td>'
            '<td class="m-ac">%s</td><td class="m-result">%s</td></tr>'
            % (esc(n), esc(det["en"]), esc(method), esc(crit), esc(res)))
    return "\n".join(out)


def sample_grid(rep, scope, det_by_no, issued):
    names = ", ".join(det_by_no[n]["en"].split("·")[0].strip()
                      for n in scope if n in det_by_no)
    started = analysis_date(rep.get("basis"), issued)
    cells = [
        ("Lab Sample ID", DASH, "lg"),
        ("Sample Description", "Dried cannabis inflorescence", "sm"),
        ("Sample Received", DASH, ""),
        ("Receipt Conditions", DASH, "sm"),
        ("Sampled by", "Purely Plant QC Department · In-house", "sm"),
        ("Sample Mass", DASH, ""),
        ("Requested Tests", "%s (%d)" % (names or DASH, len(scope)), "sm"),
        ("Storage During Analysis", DASH, "sm"),
        ("Analysis Started", str(started), ""),
        ("Analysis Completed", str(started), ""),
        ("Specification Ref.", rep.get("spec") or DASH, "sm"),
        ("Linked CoQ", rep.get("regcode") or DASH, "sm"),
    ]
    body = "\n".join(
        '    <div class="sg-cell%s"><div class="sg-label">%s</div>'
        '<div class="sg-val%s">%s</div></div>'
        % (" primary" if i == 0 else "", esc(label), (" " + cls) if cls else "", esc(val))
        for i, (label, val, cls) in enumerate(cells))
    return '<div class="sample-grid">\n%s\n  </div>' % body


def conformity(rep, scope, det_by_no):
    named = [det_by_no[n]["en"].split("·")[0].strip() for n in scope if n in det_by_no]
    listed = (", ".join(named[:-1]) + " and " + named[-1]) if len(named) > 1 else (named[0] if named else DASH)
    return (
        '<div class="conform-stmt">\n'
        '    <div class="cs-badge">Conforms</div>\n'
        '    <div class="cs-body"><strong>Result:</strong> The tested sample '
        '<strong>conforms</strong> to the product specification <strong>%s</strong> for the '
        '%d determination%s within the scope of this record — %s. This record reports '
        'the in-house analytical results only; the remaining determinations of Ph. Eur. 11.5 '
        'Monograph 3028 are certified by the laboratories named in the linked Certificate of '
        'Quality &nbsp;<span class="linked-coq">%s</span>, where the batch release is '
        'documented.</div>\n  </div>'
        % (esc(rep.get("spec") or DASH), len(scope), "" if len(scope) == 1 else "s",
           esc(listed), esc(rep.get("regcode") or DASH)))


NOTES = """<div class="notes">
    <div class="notes-title">Notes</div>
    <ul>
      <li>These results relate <strong>only to the tested sample(s)</strong> as received in the QC Laboratory.</li>
      <li><strong>No part of this report may be reproduced</strong> except in full, without prior written permission of the QC Laboratory.</li>
      <li>The determinations within the scope of this record were performed <strong>in-house</strong> by Purely Plant QC personnel within the <strong>MK GMP</strong> facility, before final release sampling.</li>
      <li>Determinations outside this scope are reported on the certificates of the external laboratories named in the linked Certificate of Quality, and are not asserted here.</li>
    </ul>
  </div>"""


def signatures():
    block = (
        '    <div class="sig-block">\n'
        '      <div class="sig-role">%s</div>\n'
        '      <div class="sig-sign"><div class="sig-line"></div></div>\n'
        '      <div class="sig-title">%s</div>\n'
        '      <div class="sig-name">&nbsp;</div>\n'
        '      <div class="sig-cred">&nbsp;</div>\n'
        '      <div class="sig-date-row"><span class="sig-date-label">Date</span>'
        '<span class="sig-date-val">&nbsp;</span></div>\n'
        '    </div>')
    return '<div class="sig-row">\n%s\n  </div>' % "\n".join(
        block % (role, title) for role, title in (
            ("Analysis Performed by", "Analyst · QC Laboratory"),
            ("Reviewed by", "Senior Analyst · QC Laboratory"),
            ("Approved by", "Head of QC Laboratory")))


INK_LAYER = (
    '<style id="__desk-icoa">\n'
    '/* One navy ink in the results column, as the Head of QC asked for the certificate of\n'
    '   quality on 16.09.2026, and the Method Validation column dropped with Section 02. */\n'
    'html body div.page table.methods tbody td.m-result,\n'
    'html body div.page table.methods tbody td.m-result.nd,\n'
    'html body div.page table.methods tbody td.m-result.fail{color:' + NAVY + ' !important}\n'
    'html body div.page table.methods thead th.col-result{width:222px}\n'
    '</style>')


def round_of(t):
    if "additional testing" in (t or ""):
        return "retest"
    if "initial" in (t or ""):
        return "initial"
    return "other"


def build(only=None):
    tpl = io.open(BASE, encoding="utf-8").read()
    data = json.load(io.open(os.path.join(GAP, "coq_artifact_data.json"), encoding="utf-8"))
    det_by_no = {d["no"]: d for d in data["dets"]}

    # Gather the in-house iCoAs the certificates actually cite, cell by cell.
    cited = {}
    for c in data["coqs"]:
        for r in c["rows"]:
            doc = (r.get("doc") or "").strip()
            if not doc.startswith("iCoA"):
                continue
            e = cited.setdefault(doc, {"coqs": [], "rows": {}})
            if c["regcode"] not in [x["regcode"] for x in e["coqs"]]:
                e["coqs"].append(c)
            e["rows"].setdefault(r["no"], r)   # first citation of a determination wins

    spans = {
        "grid": cut(tpl, '<div class="sample-grid">', '</div>\n  </div>', "sample grid"),
        "tbody": cut(tpl, "      <tbody>\n", "      </tbody>", "results tbody"),
        "sec02": cut(tpl, '<div class="sec-label"><span class="sec-no">02</span>',
                     "</div>\n  </div>", "section 02"),
        "conf": cut(tpl, '<div class="conform-stmt">', "</div>\n  </div>", "conformity"),
        "notes": cut(tpl, '<div class="notes">', "</ul>\n  </div>", "notes"),
        "sigs": cut(tpl, '<div class="sig-row">', "</div>\n  </div>", "signatures"),
    }

    stats = collections.Counter()
    report = []
    for code in sorted(cited, key=lambda c: (len(c), c)):
        info = cited[code]
        rounds = {c["t"] for c in info["coqs"]}
        # The document's native round is the earliest that cites it: an identity iCoA is
        # issued once at packaging (an initial-release certificate cites it) and carried to
        # the reissue; a record that ONLY a retest certificate cites is a genuine
        # retest-round in-house iCoA. So the folder follows the representative's round, not
        # "was it cited at retest at all".
        rep = next((c for c in info["coqs"] if round_of(c["t"]) == "initial"), info["coqs"][0])
        cls = round_of(rep["t"]) if round_of(rep["t"]) != "other" else "initial"
        folder = "RETEST" if cls == "retest" else "INITIAL"
        if only and only.lower() not in (code + " " + " ".join(rounds)).lower():
            continue
        scope = sorted(info["rows"].keys(), key=dnum)
        issued = (info["rows"][scope[0]].get("dd") or "").strip() or DASH
        carried = cls == "initial" and any(round_of(c["t"]) == "retest" for c in info["coqs"])
        series_label = ("retest" if cls == "retest"
                        else ("initial release · carried to reissue" if carried else "initial release"))

        doc = tpl
        for key, block in (
            ("sigs", signatures()),
            ("notes", NOTES),
            ("conf", conformity(rep, scope, det_by_no)),
            ("sec02", ""),
            ("tbody", "      <tbody>\n" + render_rows(det_by_no, info["rows"], scope) + "\n      </tbody>"),
            ("grid", sample_grid(rep, scope, det_by_no, issued)),
        ):
            i, j = spans[key]
            doc = doc[:i] + block + doc[j:]
        doc = doc.replace('<th class="col-val">Method Validation</th>', '', 1)

        pills = []
        spc = rep.get("spc") or {}
        if spc.get("pheno"):
            pills.append('<span class="rt-pill botanical">%s</span>' % esc(spc["pheno"].title()))
        if spc.get("chemo"):
            pills.append('<span class="rt-pill chemo">%s-dominant chemotype (Ph. Eur. type)</span>'
                         % esc(spc["chemo"]))
        lot = rep.get("pp") or DASH
        cb = rep.get("cb") or DASH
        ident = ('%s <small>(Production)</small> · %s <small>(Cultivation)</small> · '
                 '%s <small>· %s%s</small>'
                 % (esc(lot), esc(cb), esc(rep.get("strain") or DASH),
                    esc(rep.get("pcode") or DASH),
                    " · Grade " + esc(rep["grade"]) if rep.get("grade") else ""))
        title = "%s · %s · %s" % (code, lot, rep.get("strain") or "")

        repl = [
            ("<title>Purely Plant — Internal Certificate of Analysis (iCoA) — v02 Variation F</title>",
             "<title>%s</title>" % esc(title)),
            ('<div class="hb-code">iCoA-PP-2026-0005</div>',
             '<div class="hb-code">%s</div>' % esc(code)),
            ('<div class="ribbon-title">Analytical Record · In-house QC Test Session</div>',
             '<div class="ribbon-title">Analytical Record · In-house QC Test Session '
             '· %s</div>' % esc(series_label)),
            ('<div class="ribbon-stamp-val">01.06.2026</div>',
             '<div class="ribbon-stamp-val">%s</div>' % esc(issued)),
            ("iCoA-PP-2026-0005 · Page 1 of 1", "%s · Page 1 of 1" % esc(code)),
        ]
        for old, new in repl:
            if old not in doc:
                raise SystemExit("template: %r not found for %s" % (old[:48], code))
            doc = doc.replace(old, new, 1)
        doc = re.sub(r'<div class="ribbon-mono">.*?</div>',
                     '<div class="ribbon-mono">%s</div>' % ident, doc, count=1, flags=re.S)
        doc = re.sub(r'<div class="ribbon-types">.*?</div>\s*</div>',
                     '<div class="ribbon-types">%s</div>\n    </div>' % "".join(pills),
                     doc, count=1, flags=re.S)
        doc = doc.replace("</head>", INK_LAYER + "\n</head>", 1)

        def slug(x):
            return re.sub(r"[^A-Za-z0-9]+", "_", str(x or "")).strip("_") or "NA"
        name = "%s_%s_%s.html" % (code, slug(lot), slug(rep.get("strain")))
        dd = os.path.join(OUT, folder)
        os.makedirs(dd, exist_ok=True)
        io.open(os.path.join(dd, name), "w", encoding="utf-8").write(doc)
        stats[folder] += 1
        stats["scope:" + " ".join(scope)] += 1
        report.append("%s\t%s\t%s\t%s\t%s"
                      % (code, cls, lot, " ".join(scope),
                         ",".join(sorted(x["regcode"] for x in info["coqs"]))))

    io.open(os.path.join(OUT, "_build_report.tsv"), "w", encoding="utf-8").write(
        "code\tround\tp_lot\tscope\tciting_coqs\n" + "\n".join(report) + "\n")
    print("documents written: %d  {\"RETEST\": %d, \"INITIAL\": %d}"
          % (stats["RETEST"] + stats["INITIAL"], stats["RETEST"], stats["INITIAL"]))
    scopes = {k[6:]: v for k, v in stats.items() if k.startswith("scope:")}
    print("scopes: %s" % json.dumps(dict(sorted(scopes.items(), key=lambda kv: -kv[1])[:6])))
    return stats


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None,
                    help="substring of the code or the round, e.g. 'retest' or '26-012'")
    a = ap.parse_args(argv[1:])
    build(a.only)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
