#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the internal certificates of analysis in the certificate-of-quality design system.

    python3 icoa_handoff/build_icoa_v2.py                  # the whole set, into out/
    python3 icoa_handoff/build_icoa_v2.py --only 26-013    # one, into out/_preview/

The Head of QC, 17.09.2026:

> "For all internal certificates of analysis inside this folder, I want you to redesign,
> rethink the logic and the execution of the certificates that will contain the analysis
> results from identification A, identification B and foreign matter, which are performed
> prior of beginning of packaging process for the current batch … and issued a couple of
> days after or at the corresponding time as it is stated in the CoQ analysis master
> document inside the internal CoA register … I want you to restructure the parts that
> describe the findings … with pre-given options for checking … Also, I want you to adopt
> the complete design system and formatting rules that we set up for the certificates of
> quality documents and include them completely in full here."

## The design system, entire

There is no second visual layer. This builder opens the certificate of quality the desk
prints — `design_handoff/base/CoQ-PP_26-013…html`, the Claude Design package — takes its
`<head>` and the whole trailing stack of correction layers unaltered, and writes a new
`<div class="page">` between them. Every class the page uses is the certificate's own:
`header-bar`, `sec-label`, `pb-main`, `goldrule`, `selrow` with its chips, `gridrow
lk-inline`, `tbl-wrap` with `table.results`, `disp-row`, `approval-grid`, `footer`. The
A4 frame, the two gradients, the gold rules, the Orbitron headings, the navy result ink
and the bilingual `.mk` convention therefore arrive with the file rather than being
re-drawn, and any future correction layer the certificate receives lands here too.

One layer is added, `__icoa-v2`, at the end of the body where the package's own
corrections sit. It does two things and nothing else: it fits the longer title into the
header bar, and it styles the five structures the certificate of quality has no use for —
the timeline band, the option cards, the option rows, the fill-in rules and the three-way
approval grid. Every colour in it is a token of the package's `:root`.

## The logic the page now states

The old drawing asserted a laboratory sample number, a receipt condition, a sample mass
and a storage condition, and printed an em dash in each because the desk holds none of
them. Nine fields of nothing tell the reader nothing. In their place the page carries the
one thing the record really does have and the old one never showed — **when the work
happened and why it happens then**:

    harvest  ->  analysis (in-house, before packaging starts)  ->  packaging window
             ->  record issued  ->  the certificate of quality that cites it

taken from the standing register (`icoa_register_2026-09-10.csv`) and the batch date list.
For a release round that analysis date is the first day of packaging — the owner's ruling
of 11.09.2026 — and the record issues once packaging is complete; for a retest it is the
day the campaign drew its sample, and the record issues on the campaign's own issue day.

## The findings

`findings_options.py` holds the menu — 75 checkable options over eleven groups — and says
why it prints unticked: the desk has one word per determination, `Conforms`, and no
observation beneath it. The verdict is printed as the certificate of quality prints it;
the menu is the completable bench record beside the wet signature. The page says so in
its own legend, so an unticked menu cannot be read as an absent analysis.
"""
import argparse
import collections
import csv
import html
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
BASE = os.path.join(GAP, "design_handoff", "base",
                    "CoQ-PP_26-013_P050072_GP_Grape_Pie_Grade_II.html")
OUT = os.path.join(HERE, "out")
sys.path.insert(0, HERE)
import findings_options as FO                                        # noqa: E402

DASH = "—"
BOX = "☐"
RED = "color:#B91C1C;font-weight:700"
# The criterion in the short form the certificate of quality itself prints in its
# `p-spec` cell. The register carries the long monograph sentence, which wrapped each
# of these three rows onto three lines and cost the page the foot it needs for the
# approval grid; on a page whose whole subject is these three determinations the short
# form says the same thing in one line, and says it in the same words as the CoQ.
SHORT_CRIT = {
    "1": "Conforms to monograph",
    "2": "Conforms to monograph",
    "7": "≤ 2.0% / 25–50 g · < 1 cm leaves, no seeds",
}


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=False)


def en(s):
    return (s or "").split("|")[0].strip()


def mk(s):
    p = (s or "").split("|")
    return p[1].strip() if len(p) > 1 else ""


def dnum(n):
    return [int(p) for p in str(n).split(".")]


def mmyyyy(d):
    m = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", str(d or ""))
    return m.group(2) + "." + m.group(3) if m else DASH


def window(a, b):
    """A date window as the register writes it: one day, or `dd – dd.mm.yyyy`."""
    a, b = (a or "").strip(), (b or "").strip()
    if not a:
        return DASH
    if not b or a == b:
        return a
    if a[3:] == b[3:]:
        return a[:2] + "–" + b
    return a + " – " + b


# --------------------------------------------------------------------------- the frame
def frame():
    """The certificate of quality's own head, logo and trailing correction layers."""
    tpl = io.open(BASE, encoding="utf-8").read()
    i = tpl.index("<body>") + len("<body>")
    j = tpl.index('<style id="__coq-title-size">')
    k = tpl.rindex("</div>", 0, j)                      # the closing tag of .page
    logo = re.search(r'<img class="hb-logo" src="([^"]+)"', tpl).group(1)
    return tpl[:i], tpl[k:], logo


# ------------------------------------------------------------------- the option markup
def chip(o):
    """One unticked option of the menu, in the certificate's own chip."""
    cls = "opt dev" if o.dev else "opt"
    return ('<span class="chip-un %s"><span class="bx">%s</span> %s'
            '<span class="mk">%s</span></span>' % (cls, BOX, esc(o.en), esc(o.mk)))


def optline(en_, mk_, opts):
    return ('<div class="optline"><span class="opt-lbl">%s<span class="mk">%s</span></span>'
            '<span class="opts">%s</span></div>'
            % (esc(en_), esc(mk_), "".join(chip(o) for o in opts)))


def itemline(en_, mk_, opts, result):
    """A determination whose every item carries a result of its own.

    Foreign matter is the one: each category of Ph. Eur. 2.8.2 is either found or it is
    not. The Head of QC, 18.09.2026 — each is absent, which is what makes the
    determination conform. So the category is not a box to tick but a line that states
    what the examination found against it.
    """
    en_r, mk_r = result
    cells = "".join(
        '<span class="fm-item"><span class="fm-n">%s<span class="mk">%s</span></span>'
        '<span class="fm-r">%s<span class="mk">%s</span></span></span>'
        % (esc(o.en), esc(o.mk), esc(en_r), esc(mk_r)) for o in opts)
    return ('<div class="optline"><span class="opt-lbl">%s<span class="mk">%s</span></span>'
            '<span class="fm-list">%s</span></div>'
            % (esc(en_), esc(mk_), cells))


def fill(width=58, unit=""):
    return ('<span class="fillin" style="min-width:%dpx"></span>%s'
            % (width, ('<span class="fu">%s</span>' % esc(unit)) if unit else ""))


def fm_measure():
    cells = []
    for en_, mk_, unit, pre in FO.FM_MEASURE:
        val = ('<span class="fm-pre">%s</span>' % esc(pre)) if pre else fill(46, unit)
        cells.append('<span class="fm-cell"><span class="opt-lbl">%s<span class="mk">%s</span>'
                     '</span>%s</span>' % (esc(en_), esc(mk_), val))
    return '<div class="fm-row">%s</div>' % "".join(cells)


def dispo(det, rows):
    """The two sentences an analysis states about itself: what it found, and what that
    means against the specification.

    The Head of QC, 18.09.2026, gave the words — `Absent` then `Conforms` on foreign
    matter, `Conforms` on both identifications. Whether this determination happened at
    all is the certificate of quality's word, not the ruling's, so where the certificate
    carries no result for it the record says so rather than asserting a verdict over an
    analysis nobody performed.
    """
    res = str((rows.get(det) or {}).get("res") or "").strip()
    if not res or res == DASH or "not tested" in res.lower():
        held = '<span class="dp-v" style="%s">[ %s ]</span>' % (RED, DASH)
        return ('<span class="dp"><span class="dp-k">Analysis Result<span class="mk">'
                '\u0420\u0435\u0437\u0443\u043b\u0442\u0430\u0442</span></span>%s</span>'
                '<span class="dp"><span class="dp-k">Disposition<span class="mk">'
                '\u0414\u0438\u0441\u043f\u043e\u0437\u0438\u0446\u0438\u0458\u0430</span></span>%s</span>'
                % (held, held))
    ar, dp = FO.ANALYSIS_RESULT[det], FO.DISPOSITION[det]
    return ('<span class="dp"><span class="dp-k">Analysis Result<span class="mk">'
            '\u0420\u0435\u0437\u0443\u043b\u0442\u0430\u0442</span></span>'
            '<span class="dp-v">%s<span class="mk">%s</span></span></span>'
            '<span class="dp"><span class="dp-k">Disposition<span class="mk">'
            '\u0414\u0438\u0441\u043f\u043e\u0437\u0438\u0446\u0438\u0458\u0430</span></span>'
            '<span class="dp-v ok">%s<span class="mk">%s</span></span></span>'
            % (esc(ar[0]), esc(ar[1]), esc(dp[0]), esc(dp[1])))


def card(det, rows, extra=""):
    ttl_en, ttl_mk, meth = FO.TITLES[det]
    stated = FO.ITEM_RESULT.get(det)
    res = str((rows.get(det) or {}).get("res") or "").strip()
    live = bool(res) and res != DASH and "not tested" not in res.lower()
    body = "".join(
        (itemline(a, b, opts, stated) if (stated and live) else optline(a, b, opts))
        for a, b, opts in FO.BY_DET[det]) + extra
    return ('<div class="ic-card">\n'
            '    <div class="ic-title"><span>%s <span class="ic-no">#%s</span>'
            '<span class="mk">%s</span></span><span class="ic-dispo">%s</span>'
            '<span class="ic-meth">%s</span></div>\n'
            '    %s\n  </div>' % (esc(ttl_en), det, esc(ttl_mk), dispo(det, rows),
                                  esc(meth), body))


# ------------------------------------------------------------------- the results table
def result_cell(res):
    v = (res or "").strip()
    if not v or v == DASH:
        return '<td class="r-cell"><span class="r-val" style="%s">[ %s ]</span></td>' % (RED, DASH)
    e, m = en(v), mk(v)
    conform = bool(re.match(r"^(conforms|absent)", e, re.I))
    return ('<td class="r-cell"><span class="r-val%s">%s%s</span></td>'
            % (" r-conform" if conform else "", esc(e),
               ('<span class="mk">%s</span>' % esc(m)) if m else ""))


def results_table(det_by_no, rows, scope):
    body = []
    for n in scope:
        d, r = det_by_no.get(n), rows.get(n)
        if not d or not r:
            continue
        name_en, _, name_tail = d["en"].partition("·")
        meth = (r.get("mth") or d.get("method") or "").split("·")
        crit = SHORT_CRIT.get(n) or en(r.get("crit") or d.get("crit") or "")
        body.append(
            '        <tr><td>%s</td><td><span class="p-name">%s <span class="mk">%s</span>'
            '</span></td><td><span class="p-method">%s%s</span></td>'
            '<td><span class="p-spec">%s</span></td>%s</tr>'
            % (esc(n), esc(name_en.strip()), esc(d.get("mk") or ""), esc(meth[0].strip()),
               ('<span class="p-meth-eq">%s</span>' % esc("·".join(meth[1:]).strip()))
               if len(meth) > 1 else "",
               esc(crit), result_cell(r.get("res"))))
    return ('<div class="tbl-wrap">\n    <table class="results">\n'
            '      <colgroup><col style="width:30px"><col style="width:266px">'
            '<col style="width:146px"><col style="width:158px"><col></colgroup>\n'
            '      <thead><tr><th>№</th><th>Parameter <i class="bisep">|</i> '
            '<span class="mk">Параметар</span></th>'
            '<th>Method <i class="bisep">|</i> <span class="mk">Метод</span></th>'
            '<th>Acc. Criteria <i class="bisep">|</i> <span class="mk">Критериум</span></th>'
            '<th style="text-align:right">Result <i class="bisep">|</i> '
            '<span class="mk">Резултат</span></th></tr></thead>\n'
            '      <tbody>\n%s\n      </tbody>\n    </table>\n  </div>' % "\n".join(body))


# ------------------------------------------------------------------------- the timeline
def flow(reg, dates, coqs):
    tested = window(reg.get("tested_from"), reg.get("tested_to"))
    pk = dates.get("packaging_from"), dates.get("packaging_to")
    retest = reg.get("round", "").startswith("retest")
    steps = [
        ("Harvest", "Берба",
         window(dates.get("harvest_from"), dates.get("harvest_to")), "cultivation"),
        ("Analysis · In-house", "Анализа · интерна",
         tested, "campaign sampling day" if retest else "first day of packaging"),
        ("Packaging", "Пакување",
         window(*pk), "batch packed"),
        ("Record issued", "Издаден",
         reg.get("issued") or DASH, "this document"),
        ("Cited by CoQ", "Цитиран во СзК",
         ", ".join(sorted(c["regcode"] for c in coqs)), "batch release"),
    ]
    out = []
    for i, (a, b, v, note) in enumerate(steps):
        v = (v or "").strip() or DASH
        cls = "fl-step" + (" fl-here" if i == 1 else "") + (" fl-wide" if i == 4 else "")
        out.append('<div class="%s"><span class="fl-k">%s<span class="mk">%s</span></span>'
                   '<span class="fl-v">%s</span><span class="fl-n">%s</span></div>'
                   % (cls, esc(a), esc(b), esc(v), esc(note)))
    return '<div class="flow">%s</div>' % "".join(out)


# ----------------------------------------------------------------------------- the page
def chips_sel(on, label, mkl=""):
    return ('<span class="chip-%s"><span class="bx">%s</span> %s%s</span>'
            % ("sel" if on else "un", "☒" if on else BOX, label,
               ('<span class="mk">%s</span>' % esc(mkl)) if mkl else ""))


def section01(rep, scope):
    spc = rep.get("spc") or {}
    ph = (spc.get("pheno") or "").upper()
    pheno = (chips_sel(ph == "HYBRID", "Hybrid") +
             '<span class="stack">' + chips_sel(ph == "INDICA", "Indica") +
             chips_sel(ph == "SATIVA", "Sativa") + "</span>")
    chem = ('<span class="stack">' + chips_sel(spc.get("chemo") == "THC", "THC") +
            chips_sel(spc.get("chemo") == "CBD", "CBD") + "</span>")
    proc = (spc.get("proc") or "").upper()
    prc = ('<span class="stack">' +
           chips_sel("MACHINE" in proc, "Machine", "Машинска") +
           chips_sel("HAND" in proc, "Hand") + "</span>")
    badge = ('<span class="pbp-lbl">Scope</span>'
             + " ".join("#" + n for n in scope))
    return (
        '<div class="pb-main">\n'
        '    <span class="pb-name"><span style="font-family:\'Roboto Mono\',monospace">%s</span> '
        '<i class="bisep" style="font-size:.7em">|</i> '
        '<span style="font-weight:800;text-transform:uppercase">%s</span></span>\n'
        '    <span class="pb-potency"><span class="pbp-val">%s</span></span>\n'
        '  </div>\n'
        '  <div class="goldrule"></div>\n'
        '  <div class="selrow">\n'
        '    <span class="grp"><span class="lk-lbl">Phenotype <span class="mk">'
        'Фенотип</span></span>%s</span>\n'
        '    <span class="grp"><span class="lk-lbl">Chemotype <span class="mk">'
        'Хемотип</span></span>%s</span>\n'
        '    <span class="grp"><span class="lk-lbl">Processing <span class="mk">'
        'Обработка</span></span>%s</span>\n'
        '  </div>\n'
        '  <div class="goldrule"></div>\n'
        '  <div class="gridrow lk-inline" style="padding-top:6px">\n'
        '    <span class="lk"><span class="lk-lbl">Production Batch №<span class="mk">'
        'Производна серија №</span></span>'
        '<span class="lk-val">%s</span></span>\n'
        '    <span class="lk"><span class="lk-lbl">Cultivation Batch №<span class="mk">'
        'Серија од одгледување №</span></span>'
        '<span class="lk-val">%s</span></span>\n'
        '    <span class="lk"><span class="lk-lbl">Product Code<span class="mk">'
        'Код на производ</span></span>'
        '<span class="lk-val sm">%s</span></span>\n'
        '    <span class="lk"><span class="lk-lbl">Specification Ref.<span class="mk">'
        'Референца на спецификација</span></span>'
        '<span class="lk-val sm">%s</span></span>\n'
        '  </div>\n'
        '  <div class="goldrule"></div>'
        % (esc(rep.get("pp") or rep.get("cb") or DASH), esc(rep.get("strain") or DASH),
           badge,
           pheno, chem, prc,
           esc(rep.get("pp") or DASH), esc(rep.get("cb") or DASH),
           esc((rep.get("pcode") or DASH) + (" · Grade %s" % rep["grade"] if rep.get("grade") else "")),
           esc(rep.get("spec") or DASH)))


LEGEND = (
    '<div class="pot-note"><strong>How to read this record.</strong> Each analysis in '
    'Section 04 states two things of its own: the <b>analysis result</b>, which is what '
    'the examination found, and the <b>disposition</b>, which is what that means against '
    'the specification. On foreign matter they are not the same word \u2014 every category of '
    'Ph. Eur. 2.8.2 is reported <b>Absent</b>, and because none was found the '
    'determination <b>conforms</b>. The option menus under the two identifications '
    'describe rather than detect, so they are printed unticked and are marked and '
    'initialled by hand at the time of analysis, beside the signature lines; a deviation '
    'from the expected finding carries the warning tint. The determinations are performed '
    'in-house prior to final release sampling, before packaging starts (QCSOP 005 v.02). '
    '<i class="bisep">|</i> <span class="mk">\u041c\u0435\u043d\u0438\u0442\u0435 '
    '\u0441\u043e \u043e\u043f\u0446\u0438\u0438 \u0441\u0435 '
    '\u043f\u043e\u043f\u043e\u043b\u043d\u0443\u0432\u0430\u0430\u0442 '
    '\u0440\u0430\u0447\u043d\u043e \u043f\u0440\u0438 '
    '\u0430\u043d\u0430\u043b\u0438\u0437\u0430\u0442\u0430.</span></div>')


def dispo(det, rows):
    """The two sentences an analysis states about itself: what it found, and what that
    means against the specification.

    The Head of QC, 18.09.2026, gave the words — `Absent` then `Conforms` on foreign
    matter, `Conforms` on both identifications. Whether this determination happened at
    all is the certificate of quality's word, not the ruling's, so where the certificate
    carries no result for it the record says so rather than asserting a verdict over an
    analysis nobody performed.
    """
    res = str((rows.get(det) or {}).get("res") or "").strip()
    if not res or res == DASH or "not tested" in res.lower():
        held = '<span class="dp-v" style="%s">[ %s ]</span>' % (RED, DASH)
        return ('<span class="dp"><span class="dp-k">Analysis Result<span class="mk">'
                '\u0420\u0435\u0437\u0443\u043b\u0442\u0430\u0442</span></span>%s</span>'
                '<span class="dp"><span class="dp-k">Disposition<span class="mk">'
                '\u0414\u0438\u0441\u043f\u043e\u0437\u0438\u0446\u0438\u0458\u0430</span></span>%s</span>'
                % (held, held))
    ar, dp = FO.ANALYSIS_RESULT[det], FO.DISPOSITION[det]
    return ('<span class="dp"><span class="dp-k">Analysis Result<span class="mk">'
            '\u0420\u0435\u0437\u0443\u043b\u0442\u0430\u0442</span></span>'
            '<span class="dp-v">%s<span class="mk">%s</span></span></span>'
            '<span class="dp"><span class="dp-k">Disposition<span class="mk">'
            '\u0414\u0438\u0441\u043f\u043e\u0437\u0438\u0446\u0438\u0458\u0430</span></span>'
            '<span class="dp-v ok">%s<span class="mk">%s</span></span></span>'
            % (esc(ar[0]), esc(ar[1]), esc(dp[0]), esc(dp[1])))


def card(det, rows, extra=""):
    ttl_en, ttl_mk, meth = FO.TITLES[det]
    stated = FO.ITEM_RESULT.get(det)
    res = str((rows.get(det) or {}).get("res") or "").strip()
    live = bool(res) and res != DASH and "not tested" not in res.lower()
    body = "".join(
        (itemline(a, b, opts, stated) if (stated and live) else optline(a, b, opts))
        for a, b, opts in FO.BY_DET[det]) + extra
    return ('<div class="ic-card">\n'
            '    <div class="ic-title"><span>%s <span class="ic-no">#%s</span>'
            '<span class="mk">%s</span></span><span class="ic-dispo">%s</span>'
            '<span class="ic-meth">%s</span></div>\n'
            '    %s\n  </div>' % (esc(ttl_en), det, esc(ttl_mk), dispo(det, rows),
                                  esc(meth), body))


# ------------------------------------------------------------------- the results table
def result_cell(res):
    v = (res or "").strip()
    if not v or v == DASH:
        return '<td class="r-cell"><span class="r-val" style="%s">[ %s ]</span></td>' % (RED, DASH)
    e, m = en(v), mk(v)
    conform = bool(re.match(r"^(conforms|absent)", e, re.I))
    return ('<td class="r-cell"><span class="r-val%s">%s%s</span></td>'
            % (" r-conform" if conform else "", esc(e),
               ('<span class="mk">%s</span>' % esc(m)) if m else ""))


def results_table(det_by_no, rows, scope):
    body = []
    for n in scope:
        d, r = det_by_no.get(n), rows.get(n)
        if not d or not r:
            continue
        name_en, _, name_tail = d["en"].partition("·")
        meth = (r.get("mth") or d.get("method") or "").split("·")
        crit = SHORT_CRIT.get(n) or en(r.get("crit") or d.get("crit") or "")
        body.append(
            '        <tr><td>%s</td><td><span class="p-name">%s <span class="mk">%s</span>'
            '</span></td><td><span class="p-method">%s%s</span></td>'
            '<td><span class="p-spec">%s</span></td>%s</tr>'
            % (esc(n), esc(name_en.strip()), esc(d.get("mk") or ""), esc(meth[0].strip()),
               ('<span class="p-meth-eq">%s</span>' % esc("·".join(meth[1:]).strip()))
               if len(meth) > 1 else "",
               esc(crit), result_cell(r.get("res"))))
    return ('<div class="tbl-wrap">\n    <table class="results">\n'
            '      <colgroup><col style="width:30px"><col style="width:266px">'
            '<col style="width:146px"><col style="width:158px"><col></colgroup>\n'
            '      <thead><tr><th>№</th><th>Parameter <i class="bisep">|</i> '
            '<span class="mk">Параметар</span></th>'
            '<th>Method <i class="bisep">|</i> <span class="mk">Метод</span></th>'
            '<th>Acc. Criteria <i class="bisep">|</i> <span class="mk">Критериум</span></th>'
            '<th style="text-align:right">Result <i class="bisep">|</i> '
            '<span class="mk">Резултат</span></th></tr></thead>\n'
            '      <tbody>\n%s\n      </tbody>\n    </table>\n  </div>' % "\n".join(body))


# ------------------------------------------------------------------------- the timeline
def flow(reg, dates, coqs):
    tested = window(reg.get("tested_from"), reg.get("tested_to"))
    pk = dates.get("packaging_from"), dates.get("packaging_to")
    retest = reg.get("round", "").startswith("retest")
    steps = [
        ("Harvest", "Берба",
         window(dates.get("harvest_from"), dates.get("harvest_to")), "cultivation"),
        ("Analysis · In-house", "Анализа · интерна",
         tested, "campaign sampling day" if retest else "first day of packaging"),
        ("Packaging", "Пакување",
         window(*pk), "batch packed"),
        ("Record issued", "Издаден",
         reg.get("issued") or DASH, "this document"),
        ("Cited by CoQ", "Цитиран во СзК",
         ", ".join(sorted(c["regcode"] for c in coqs)), "batch release"),
    ]
    out = []
    for i, (a, b, v, note) in enumerate(steps):
        v = (v or "").strip() or DASH
        cls = "fl-step" + (" fl-here" if i == 1 else "") + (" fl-wide" if i == 4 else "")
        out.append('<div class="%s"><span class="fl-k">%s<span class="mk">%s</span></span>'
                   '<span class="fl-v">%s</span><span class="fl-n">%s</span></div>'
                   % (cls, esc(a), esc(b), esc(v), esc(note)))
    return '<div class="flow">%s</div>' % "".join(out)


# ----------------------------------------------------------------------------- the page
def chips_sel(on, label, mkl=""):
    return ('<span class="chip-%s"><span class="bx">%s</span> %s%s</span>'
            % ("sel" if on else "un", "☒" if on else BOX, label,
               ('<span class="mk">%s</span>' % esc(mkl)) if mkl else ""))


def section01(rep, scope):
    spc = rep.get("spc") or {}
    ph = (spc.get("pheno") or "").upper()
    pheno = (chips_sel(ph == "HYBRID", "Hybrid") +
             '<span class="stack">' + chips_sel(ph == "INDICA", "Indica") +
             chips_sel(ph == "SATIVA", "Sativa") + "</span>")
    chem = ('<span class="stack">' + chips_sel(spc.get("chemo") == "THC", "THC") +
            chips_sel(spc.get("chemo") == "CBD", "CBD") + "</span>")
    proc = (spc.get("proc") or "").upper()
    prc = ('<span class="stack">' +
           chips_sel("MACHINE" in proc, "Machine", "Машинска") +
           chips_sel("HAND" in proc, "Hand") + "</span>")
    badge = ('<span class="pbp-lbl">Scope</span>'
             + " ".join("#" + n for n in scope))
    return (
        '<div class="pb-main">\n'
        '    <span class="pb-name"><span style="font-family:\'Roboto Mono\',monospace">%s</span> '
        '<i class="bisep" style="font-size:.7em">|</i> '
        '<span style="font-weight:800;text-transform:uppercase">%s</span></span>\n'
        '    <span class="pb-potency"><span class="pbp-val">%s</span></span>\n'
        '  </div>\n'
        '  <div class="goldrule"></div>\n'
        '  <div class="selrow">\n'
        '    <span class="grp"><span class="lk-lbl">Phenotype <span class="mk">'
        'Фенотип</span></span>%s</span>\n'
        '    <span class="grp"><span class="lk-lbl">Chemotype <span class="mk">'
        'Хемотип</span></span>%s</span>\n'
        '    <span class="grp"><span class="lk-lbl">Processing <span class="mk">'
        'Обработка</span></span>%s</span>\n'
        '  </div>\n'
        '  <div class="goldrule"></div>\n'
        '  <div class="gridrow lk-inline" style="padding-top:6px">\n'
        '    <span class="lk"><span class="lk-lbl">Production Batch №<span class="mk">'
        'Производна серија №</span></span>'
        '<span class="lk-val">%s</span></span>\n'
        '    <span class="lk"><span class="lk-lbl">Cultivation Batch №<span class="mk">'
        'Серија од одгледување №</span></span>'
        '<span class="lk-val">%s</span></span>\n'
        '    <span class="lk"><span class="lk-lbl">Product Code<span class="mk">'
        'Код на производ</span></span>'
        '<span class="lk-val sm">%s</span></span>\n'
        '    <span class="lk"><span class="lk-lbl">Specification Ref.<span class="mk">'
        'Референца на спецификација</span></span>'
        '<span class="lk-val sm">%s</span></span>\n'
        '  </div>\n'
        '  <div class="goldrule"></div>'
        % (esc(rep.get("pp") or rep.get("cb") or DASH), esc(rep.get("strain") or DASH),
           badge,
           pheno, chem, prc,
           esc(rep.get("pp") or DASH), esc(rep.get("cb") or DASH),
           esc((rep.get("pcode") or DASH) + (" · Grade %s" % rep["grade"] if rep.get("grade") else "")),
           esc(rep.get("spec") or DASH)))


LEGEND = (
    '<div class="pot-note"><strong>How to read this record.</strong> The <b>Result</b> '
    'column is the verdict as it is certified on the linked certificate of quality; the '
    'menus in Section 04 are the <b>bench observation record</b>, printed unticked and '
    'marked and initialled by hand at the time of analysis, beside the signature lines. An '
    'unticked menu records that the observation detail is entered on the signed paper copy, '
    'not that the determination was not performed; a deviation from the expected finding '
    'carries the warning tint. The determinations are performed in-house prior to final '
    'release sampling, before packaging starts (QCSOP 005 v.02). <i class="bisep">|</i> '
    '<span class="mk">Мените со опции '
    'се пополнуваат рачно '
    'при анализата.</span></div>')


def approval(reg, retest):
    who = [
        ("Analysis Performed by", "Извршил анализа",
         "Analyst · QC Laboratory", "Аналитичар · Лабораторија за КК",
         "", ""),
        ("Reviewed &amp; Approved by", "Прегледал и одобрил",
         "QC Manager", "Менаџер за КК",
         "Blagoj Nikolov", "M.Pharm · Drug Quality Control Specialist"),
        ("Verified by", "Верификувал",
         "QA Manager", "Менаџер за ОК",
         "Jovana Romevska Cvetkovski", "Master Pharmacist"),
    ]
    out = []
    for role_en, role_mk, title_en, title_mk, name, cred in who:
        out.append(
            '<div><div class="ap-role">%s <span class="mk">%s</span></div>'
            '<div class="ap-sign"><div class="ap-line"></div></div>'
            '<div class="ap-title">%s <span class="mk">%s</span></div>'
            '<div class="ap-name">%s</div><div class="ap-cred">%s</div>'
            '<div class="ap-date-row"><span class="ap-date-label">Date · '
            'Датум</span><span class="ap-date-val">%s</span></div></div>'
            % (role_en, role_mk, title_en, title_mk,
               esc(name) if name else "&nbsp;", esc(cred) if cred else "&nbsp;",
               esc(reg.get("issued") or DASH) if name else ""))
    return '<div class="approval-grid cols-3">\n    %s\n  </div>' % "\n    ".join(out)


LAYER = """<style id="__icoa-v2">
/* The internal certificate of analysis, 17.09.2026. The page is the certificate of
   quality's own: its head, its 55 correction layers, its classes. This layer fits the
   longer title into the header bar and styles the five structures the certificate of
   quality has no use for — the timeline band, the option cards, the option rows, the
   fill-in rules and the three-column approval grid. Every colour is a :root token. */
html body div.page div.header-bar div.hb-center div.hb-title{font-size:15.4px !important;letter-spacing:1.5px !important;line-height:17px !important}
html body div.page div.header-bar{height:96px !important}
html body div.page div.pb-main .pbp-val{font-size:13px;letter-spacing:.6px}
html body div.page div.pb-main .pbp-val{font-family:'Roboto Mono',monospace;font-weight:700}
html body div.page div.pb-main .pbp-lbl{font-family:'Orbitron',sans-serif;font-size:7px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--gold-label);margin-right:7px}

/* the band that states when the work happened, and why it happens then */
html body div.page div.flow{display:flex;align-items:stretch;padding:5px var(--MARGIN-H) 6px;background:linear-gradient(180deg,#FCFDFE 0%,#F7FAFD 100%)}
html body div.page div.flow .fl-step{flex:1 1 0;min-width:0;display:flex;flex-direction:column;gap:1px;padding:2px 9px;border-left:1px solid var(--border);position:relative}
html body div.page div.flow .fl-step:first-child{border-left:0;padding-left:0}
html body div.page div.flow .fl-step.fl-wide{flex:1.35 1 0}
html body div.page div.flow .fl-step.fl-here{background:linear-gradient(180deg,rgba(253,251,244,.95),rgba(248,241,223,.75));border-radius:3px}
html body div.page div.flow .fl-k{font-family:'Orbitron',sans-serif;font-size:6.4px;font-weight:700;letter-spacing:.45px;text-transform:uppercase;color:var(--gold-deep);line-height:7.6px}
html body div.page div.flow .fl-k .mk{display:block;font-size:5.4px;line-height:6.4px;letter-spacing:normal}
html body div.page div.flow .fl-v{font-family:'Roboto Mono',monospace;font-size:9.2px;font-weight:700;color:var(--navy);line-height:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
html body div.page div.flow .fl-step.fl-wide .fl-v{font-size:8.2px;white-space:normal;line-height:9.4px}
html body div.page div.flow .fl-n{font-size:5.8px;font-style:italic;color:var(--text-ter);line-height:7px}

/* the option cards — the template's Section 02 text boxes, in the certificate's palette */
html body div.page div.ic-cards{padding:5px var(--MARGIN-H) 2px;display:flex;flex-direction:column;gap:5px}
html body div.page div.ic-card{border:1px solid var(--border);border-radius:4px;background:linear-gradient(180deg,#FCFDFE 0%,#F8FAFD 100%);padding:4px 8px 5px}
html body div.page div.ic-card .ic-title{display:flex;justify-content:space-between;align-items:baseline;gap:8px;border-bottom:1px solid rgba(166,124,46,.3);padding-bottom:2px;margin-bottom:3px}
html body div.page div.ic-card .ic-title>span:first-child{font-family:'Orbitron',sans-serif;font-size:8.4px;font-weight:800;letter-spacing:.8px;text-transform:uppercase;color:var(--navy)}
html body div.page div.ic-card .ic-title .ic-no{font-family:'Roboto Mono',monospace;font-size:8px;font-weight:700;color:#8A5E12;margin-left:5px}
html body div.page div.ic-card .ic-title .mk{display:inline;font-size:6.2px;margin-left:6px;letter-spacing:normal;text-transform:none}
/* the two sentences each analysis states about itself (Head of QC, 18.09.2026) */
html body div.page div.ic-card .ic-title{gap:6px}
html body div.page div.ic-card .ic-dispo{margin-left:auto;display:inline-flex;align-items:baseline;gap:10px}
html body div.page div.ic-card .dp{display:inline-flex;align-items:baseline;gap:4px}
html body div.page div.ic-card .dp-k{font-family:'Orbitron',sans-serif;font-size:5.8px;font-weight:700;letter-spacing:.35px;text-transform:uppercase;color:var(--gold-deep)}
html body div.page div.ic-card .dp-k .mk{display:inline;font-size:5px;margin-left:3px;letter-spacing:normal;text-transform:none}
html body div.page div.ic-card .dp-v{font-size:7.6px;font-weight:800;letter-spacing:.2px;color:var(--navy)}
html body div.page div.ic-card .dp-v.ok{color:var(--green)}
html body div.page div.ic-card .dp-v .mk{display:inline;font-size:5.4px;margin-left:3px}
/* foreign matter: a category is a line with a result, not a box to tick */
html body div.page div.ic-card .fm-list{display:grid;grid-template-columns:repeat(3,1fr);column-gap:8px;row-gap:1px}
html body div.page div.ic-card .fm-item{display:flex;align-items:baseline;justify-content:space-between;gap:6px;border-bottom:1px dotted #E1E8F0;padding:.6px 0}
html body div.page div.ic-card .fm-n{font-family:'Montserrat',sans-serif;font-size:6.3px;font-weight:600;color:#5D7186}
html body div.page div.ic-card .fm-n .mk{display:inline;font-size:5.2px;margin-left:3px;color:#93A3B6}
html body div.page div.ic-card .fm-r{font-family:'Montserrat',sans-serif;font-size:6.4px;font-weight:800;color:var(--navy);white-space:nowrap}
html body div.page div.ic-card .fm-r .mk{display:inline;font-size:5.2px;margin-left:2px;color:#6E7F94}
html body div.page div.ic-card .ic-meth{font-family:'Roboto Mono',monospace;font-size:6.4px;font-weight:600;letter-spacing:.2px;color:var(--gold-deep);white-space:nowrap}
html body div.page div.ic-card .optline{display:grid;grid-template-columns:78px 1fr;column-gap:7px;align-items:start;padding:1.2px 0}
html body div.page div.ic-card .optline + .optline{border-top:1px solid var(--border-light)}
html body div.page div.ic-card .opt-lbl{font-family:'Orbitron',sans-serif;font-size:6.2px;font-weight:700;letter-spacing:.3px;text-transform:uppercase;color:var(--gold-deep);line-height:7.4px;padding-top:2px}
html body div.page div.ic-card .opt-lbl .mk{display:block;font-size:5.2px;line-height:6px;letter-spacing:normal;text-transform:none}
html body div.page div.ic-card .opts{display:flex;flex-wrap:wrap;gap:2.5px}
html body div.page div.ic-card .opts .chip-un{font-family:'Montserrat',sans-serif;font-size:6.3px;font-weight:600;text-transform:none;letter-spacing:.05px;padding:.8px 5px .8px 3.5px;gap:2.5px;color:#5D7186;border-color:#D4DFEA}
html body div.page div.ic-card .opts .chip-un .bx{font-size:7.4px;color:#8FA6BC;text-shadow:none}
html body div.page div.ic-card .opts .chip-un .mk{display:inline;font-size:5.2px;margin-left:3px;color:#93A3B6;font-style:italic;line-height:1}
html body div.page div.ic-card .opts .chip-un.dev{border-color:#E4CDBE;background:linear-gradient(180deg,#FBF4F1 0%,#FDF9F7 60%,#FEFCFB 100%);color:#8A5A45}
html body div.page div.ic-card .opts .chip-un.dev .bx{color:#C08A6B}
html body div.page div.ic-card .opts .chip-un.dev .mk{color:#A98470}
html body div.page div.pot-note .opt.dev.leg{color:#C08A6B;font-size:7px}

/* the fill-in rules — what the bench writes, never what the desk asserts */
html body div.page div.page-fill,html body div.page .fillin{display:inline-block;border-bottom:1px dotted #B3C3D3;height:8px;margin:0 3px -1px 2px}
html body div.page .fu{font-family:'Roboto Mono',monospace;font-size:6.4px;font-weight:600;color:var(--text-ter)}
html body div.page div.fm-row{display:flex;gap:14px;align-items:flex-end;padding:3px 0 0;margin-top:2px;border-top:1px solid var(--border-light)}
html body div.page div.fm-row .fm-cell{display:flex;align-items:baseline;gap:5px}
html body div.page div.fm-row .fm-pre{font-family:'Roboto Mono',monospace;font-size:8.6px;font-weight:700;color:var(--navy)}
html body div.page div.ident-row{display:flex;gap:16px;align-items:baseline;padding:2px var(--MARGIN-H) 0}
html body div.page div.ident-row .opt-lbl{font-family:'Orbitron',sans-serif;font-size:6.4px;font-weight:700;letter-spacing:.35px;text-transform:uppercase;color:var(--gold-deep)}
html body div.page div.ident-row .opt-lbl .mk{display:inline;font-size:5.4px;margin-left:4px;letter-spacing:normal;text-transform:none}
/* the identification strip borrowed .fl-v and .fl-n from the timeline band, where they
   are sized for a date and a three-word note; here they carry a round name and a
   sentence, and at the band's size the strip alone took 60px of the foot the approval
   grid needs. Sized for this strip's own content. */
html body div.page div.ident-row .fl-v{font-size:8.4px;line-height:10px;white-space:nowrap}
html body div.page div.ident-row .fl-n{font-size:6.6px;line-height:8px;font-style:italic}
/* a batch number is one token: the package's __h01-shrink-fit lets a cell shrink below
   its content and P050082 broke as 'P050 082'. The values of this row never wrap. */
html body div.page div.gridrow.lk-inline{flex-wrap:wrap !important;row-gap:3px !important}
html body div.page div.gridrow.lk-inline>*{flex:0 0 auto !important}
html body div.page div.gridrow.lk-inline .lk-val,html body div.page div.gridrow.lk-inline .lk-val.sm{white-space:nowrap !important;max-width:none !important}

/* three signatories, the in-house laboratory's own chain */
html body div.page div.approval-grid.cols-3{grid-template-columns:repeat(3,1fr);column-gap:16px}
html body div.page div.approval-grid.cols-3 .ap-role{font-size:8.4px;letter-spacing:.8px}
html body div.page div.approval-grid.cols-3 .ap-role .mk{display:block;font-size:5.8px;letter-spacing:normal}
html body div.page div.approval-grid.cols-3 .ap-title .mk{display:inline;font-size:5.8px;margin-left:4px}
html body div.page div.approval-grid.cols-3 .ap-name{font-size:9.6px}
html body div.page div.approval-grid.cols-3 .ap-cred{font-size:7px}
html body div.page div.results tbody td{padding-top:1.5px !important;padding-bottom:1.5px !important}
</style>"""


def build(only=None):
    head, tail, logo = frame()
    data = json.load(io.open(os.path.join(GAP, "coq_artifact_data.json"), encoding="utf-8"))
    det_by_no = {d["no"]: d for d in data["dets"]}
    reg = {r["code"]: r for r in csv.DictReader(
        io.open(os.path.join(GAP, "icoa_register_2026-09-10.csv"), encoding="utf-8"))}
    dates = {}
    for row in csv.DictReader(io.open(os.path.join(GAP, "batch_dates_2026-09-10.csv"),
                                      encoding="utf-8")):
        for key in ((row.get("batch") or "").strip(), (row.get("p_batch") or "").strip()):
            if key and not key.startswith(("N/A", DASH)):
                dates.setdefault(key, row)

    cited = {}
    for c in data["coqs"]:
        for r in c["rows"]:
            doc = (r.get("doc") or "").strip()
            if not doc.startswith("iCoA"):
                continue
            e = cited.setdefault(doc, {"coqs": [], "rows": {}})
            if c["regcode"] not in [x["regcode"] for x in e["coqs"]]:
                e["coqs"].append(c)
            e["rows"].setdefault(r["no"], r)

    dest_root = OUT
    if only:
        dest_root = os.path.join(OUT, "_preview")
    else:
        for f in ("INITIAL", "RETEST"):
            d = os.path.join(OUT, f)
            if os.path.isdir(d):
                for name in os.listdir(d):
                    os.remove(os.path.join(d, name))

    stats, report = collections.Counter(), []
    for code in sorted(cited, key=lambda c: (len(c), c)):
        if only and only.lower() not in code.lower():
            continue
        info = cited[code]
        rep = next((c for c in info["coqs"] if "initial" in (c["t"] or "")), info["coqs"][0])
        r = reg.get(code, {})
        retest = (r.get("round") or "").startswith("retest")
        folder = "RETEST" if retest else "INITIAL"
        scope = sorted(info["rows"].keys(), key=dnum)
        lot = rep.get("pp") or rep.get("cb") or DASH
        bd = dates.get(rep.get("pp") or "") or dates.get(rep.get("cb") or "") or {}

        series = ("%s · %s" % (r.get("round", "").title(), r["tranche"])
                  if r.get("tranche") else (r.get("round") or "release round").title())
        cards = "".join(card(d, info["rows"], fm_measure() if d == "7" else "")
                        for d in ("1", "2", "7") if d in scope)
        extra = [n for n in scope if n not in ("1", "2", "7")]

        page = "\n".join([
            '<div class="page">',
            '',
            '  <div class="header-bar">',
            '    <img class="hb-logo" src="%s">' % logo,
            '    <div class="hb-center"><div class="hb-title">Internal Certificate of Analysis'
            '</div><div class="hb-mk-title">Интерен '
            'сертификат за '
            'анализа</div>'
            '<div class="hb-sub">In-house QC Laboratory · Identity and Foreign Matter '
            '· Dry Cannabis Flower</div>'
            '<div class="hb-mk-sub">Интерна '
            'лабораторија за '
            'КК · Идентификација '
            'и страни материи</div></div>',
            '    <div class="hb-right"><div class="hb-code-lbl">Document ID <span class="mk">'
            'Код на документ</span></div>'
            '<div class="hb-code">%s</div>'
            '<div class="hb-issue">Issued · Издаден '
            '<b>%s</b></div></div>' % (esc(code), esc(r.get("issued") or DASH)),
            '  </div>',
            '',
            '  <div class="sec-label"><span class="sec-no">01</span> Batch &amp; Sample '
            'Identification <span class="mk">Серија и '
            'идентификација '
            'на примерокот</span></div>',
            '  ' + section01(rep, scope),
            '',
            '  <div class="sec-label" style="margin-top:8px"><span class="sec-no">02</span> '
            'Analysis Basis &amp; Issue <span class="mk">Основа '
            'на анализата и '
            'издавање</span></div>',
            '  ' + flow(r, bd, info["coqs"]),
            '  <div class="ident-row"><span class="opt-lbl">Round <span class="mk">'
            'Круг</span></span><span class="fl-v">%s</span>'
            '<span class="opt-lbl">Lab Sample ID <span class="mk">ИД на '
            'примерок</span></span>%s'
            '<span class="opt-lbl">Sample <span class="mk">Примерок'
            '</span></span><span class="fl-n">Dried cannabis inflorescence, drawn in-house '
            'by Purely Plant QC</span></div>' % (esc(series), fill(62)),
            '  <div class="goldrule"></div>',
            '',
            '  <div class="sec-label" style="margin-top:8px"><span class="sec-no">03</span> '
            'Determinations &amp; Results <span class="mk">Испитувања '
            'и резултати</span></div>',
            '  ' + results_table(det_by_no, info["rows"], scope),
            '  ' + LEGEND,
            '',
            '  <div class="sec-label" style="margin-top:6px"><span class="sec-no">04</span> '
            'Observation Record <span class="mk">Запис на '
            'наодите</span></div>',
            '  <div class="ic-cards">\n    %s\n  </div>' % cards,
            '',
            '  <div class="disp-row" style="margin-top:2px">',
            '    <span class="grp"><span class="lk-lbl">In-house Testing for Batch № '
            '<i class="bisep">|</i><span class="mk">Интерно '
            'испитување на '
            'Серија бр.</span></span>'
            '<span class="disp-batch">%s</span>%s%s</span>'
            % (esc(lot),
               chips_sel(False, "Conforms to Specification",
                         "Одговара на "
                         "спецификацијата"),
               chips_sel(False, "Does not conform")),
            '  </div>',
            '  <div class="goldrule"></div>',
            '',
            '  ' + approval(r, retest),
            '',
            '  <div class="footer">',
            '    <div class="foot-left">Purely Plant DOOEL · Industriska ulica 9, br. 9,<br>'
            'Kojlija 1043 · Petrovec-Skopje, North Macedonia</div>',
            '    <div class="foot-center-num">1 <span style="opacity:.6">|</span> 1</div>',
            '    <div class="foot-right">%s</div>' % esc(code),
            '  </div>',
            '',
        ])
        doc = head + "\n" + page + tail
        doc = doc.replace(
            "<title>Purely Plant — Certificate of Quality — "
            "P050072 Grape Pie (Grade II)</title>",
            "<title>%s · %s · %s</title>"
            % (esc(code), esc(lot), esc(rep.get("strain") or "")), 1)
        doc = doc.replace("</body>", LAYER + "\n</body>", 1)

        def slug(x):
            return re.sub(r"[^A-Za-z0-9]+", "_", str(x or "")).strip("_") or "NA"
        name = "%s_%s_%s.html" % (code, slug(lot), slug(rep.get("strain")))
        dd = os.path.join(dest_root, folder)
        os.makedirs(dd, exist_ok=True)
        io.open(os.path.join(dd, name), "w", encoding="utf-8").write(doc)
        stats[folder] += 1
        if extra:
            stats["wide-scope"] += 1
        report.append("%s\t%s\t%s\t%s\t%s\t%s"
                      % (code, folder.lower(), lot, " ".join(scope),
                         r.get("issued") or "", ",".join(sorted(
                             x["regcode"] for x in info["coqs"]))))

    if not only:
        io.open(os.path.join(OUT, "_build_report.tsv"), "w", encoding="utf-8").write(
            "code\tround\tp_lot\tscope\tissued\tciting_coqs\n" + "\n".join(report) + "\n")
    print("documents written: %d  {INITIAL: %d, RETEST: %d}  wide-scope: %d"
          % (stats["INITIAL"] + stats["RETEST"], stats["INITIAL"], stats["RETEST"],
             stats["wide-scope"]))
    print("into: %s" % os.path.relpath(dest_root, GAP))
    return stats


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="substring of one iCoA code")
    a = ap.parse_args(argv[1:])
    build(a.only)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
