#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QCSP 001 v.04 — the product specification, restated against the potency decision.

    python3 deliverables/qc_gap_analysis/specs/build_qcsp004.py

The Head of QC, 18.09.2026: "after you finish this, I want you to update the actual product
specification that we built according to this new and latest decisions regarding ranges."

Why it was needed. QCSP 001 v.03, signed 01.06.2026, states a Total Δ⁹-THC target and window
per lot. The potency decision of 17.09.2026 (specs/Potency_specifications_25_2026-09-17.pdf)
moved them. The certificates of quality already print the decision's windows — all 172 of
them agree with it — so since 17.09.2026 a certificate and the specification it cites have
been stating different windows under the same code: CoQ-PP_26-013 (P050072) cites
QCSP_001_GP-I_v.01 and prints 26.00 – 29.99 %, where the v.03 sheet under that code says
26.61 – 29.39 %. Forty-five of the forty-eight v.03 sheets are in that position.

What this builds. One sheet per SPECIFICATION CODE rather than per lot — fifty-seven of them,
which is what the two fleets actually cite — carrying the decision's nominal, tolerance and
window, and the same twenty-three determinations, methods and acceptance criteria the signed
v.03 carries (extracted into product_specifications_QCSP001.json; all forty-eight v.03 sheets
share one Section 02 shape, so there is exactly one table to restate).

The sheet's own code keeps its `_v.01` suffix. Every certificate in both fleets cites it, and
a suffix bump would move 387 documents to say nothing new; the revision is carried where a
revision belongs, at document level — QCSP 001 v.04, superseding v.03 of 01.06.2026. If the
Head of QC wants the per-sheet suffix bumped as well, it is one line here and a reprint of
the fleet.

Nothing here reads a laboratory value. The windows come from the owner's own decision
document and the attributes from the certificates that already print them; the build refuses
any code whose lots disagree about an attribute rather than choosing between them.
"""
import html as H
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
OUT = os.path.join(HERE, "QCSP_001_v04")
SHEETS = os.path.join(OUT, "SHEETS")
DOC_VERSION = "QCSP 001 v.04"
ISSUED = "18.09.2026"
SUPERSEDES = "QCSP 001 v.03 of 01.06.2026"
BASIS = "17.09.2026"
ROM = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6}


def esc(s):
    return H.escape(str("" if s is None else s), quote=False)


def bi(s):
    """A house string carries its Macedonian after a pipe."""
    parts = [p.strip() for p in str(s or "").split("|")]
    if len(parts) == 1:
        return esc(parts[0])
    return esc(parts[0]) + ' <span class="mk">' + esc(" | ".join(parts[1:])) + "</span>"


def chips(label, mk, options, chosen):
    out = ['<span class="grp"><span class="lk-lbl">%s <span class="mk">%s</span></span>' % (esc(label), esc(mk))]
    for o in options:
        on = o.upper() == str(chosen or "").upper()
        out.append('<span class="chip-%s"><span class="bx">%s</span> %s</span>'
                   % ("sel" if on else "un", "☒" if on else "☐", esc(o)))
    out.append("</span>")
    return "".join(out)


def lk(label, mk, value, small=True):
    return ('<span class="lk"><span class="lk-lbl">%s<span class="mk">%s</span></span>'
            '<span class="lk-val%s">%s</span></span>'
            % (esc(label), esc(mk), " sm" if small else "", bi(value)))


def rows(dets, window):
    out = []
    for i, d in enumerate(dets):
        crit = d["criterion"]
        if d["no"] == "4":
            crit = ("%s | Според целната "
                    "класа во Погл. 01" % window)
        cls = ' class="last-row"' if i == len(dets) - 1 else ""
        out.append(
            "<tr%s><td>%s</td>"
            '<td><span class="p-name">%s</span></td>'
            '<td><span class="p-method">%s</span></td>'
            '<td><span class="p-spec">%s</span></td></tr>'
            % (cls, esc(d["no"]),
               esc(d["en"]) + (' <span class="mk">%s</span>' % esc(d["mk"]) if d.get("mk") else ""),
               esc(d["method"]), bi(crit)))
    return "\n".join(out)


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Purely Plant — Product Specification — {code} — {strain} — Grade {numeral}</title>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400;1,500&amp;family=Roboto+Mono:wght@400;500;600;700&amp;family=Orbitron:wght@500;600;700;800;900&amp;display=swap" rel="stylesheet">
<link rel="stylesheet" href="../_icoa.css">
<link rel="stylesheet" href="../_coq-rules.css">
<link rel="stylesheet" href="../_icoa3-print.css">
<link rel="stylesheet" href="../_qcsp.css">
</head>
<body>
<div class="page">
<div class="header-bar">
<img class="hb-logo" src="../_logo.svg" alt="Purely Plant">
<div class="hb-center"><div class="hb-title">Product Specification</div><div class="hb-mk-title">Спецификација на производ</div><div class="hb-sub">Intermediate Bulk — Dry Cannabis Flower for Medical Use</div><div class="hb-mk-sub">Интермедиер балк — сув цвет од канабис за медицинска употреба</div></div>
<div class="hb-right"><div class="hb-code-lbl">Document ID <span class="mk">Код на документ</span></div><div class="hb-code">{code}</div><div class="hb-issue">Issued · Издаден <b>{issued}</b></div></div>
</div>
<div class="sec-label"><span class="sec-no">01</span> Product Identification &amp; Potency Grade <span class="mk">Идентификација на производ и класа на јачина</span></div>
<div class="pb-main"><span class="pb-name"><span style="font-family:'Roboto Mono',monospace">{cult}</span> <i class="bisep" style="font-size:.7em">|</i> <span style="font-weight:800;text-transform:uppercase">{strain}</span> <span class="pb-pot">{nominal} %</span></span></div>
<div class="selrow">
{pheno}
{chemo}
</div>
<div class="goldrule"></div>
<div class="gridrow lk-inline g3">
{r1}
</div>
<div class="goldrule"></div>
<div class="gridrow lk-inline g3">
{r2}
</div>
<div class="goldrule"></div>
<div class="gridrow lk-inline g3">
{r3}
</div>
<div class="goldrule"></div>
<div class="gridrow lk-inline">
{r3b}
</div>
<div class="sec-label"><span class="sec-no">02</span> Determinations, Methods &amp; Acceptance Criteria <span class="mk">Определувања, методи и критериуми</span></div>
<div class="tbl-wrap"><table class="results spec4">
<colgroup><col><col><col><col></colgroup>
<thead><tr><th>№</th><th>Parameter <span class="mk">Параметар</span></th><th>Method <span class="mk">Метода</span></th><th>Acceptance Criteria <span class="mk">Критериум</span></th></tr></thead>
<tbody>
{rows}
</tbody></table></div>
<div class="qcsp-note">This specification states the requirements for the grade named in Section 01. The Total Δ⁹-THC window is the grade's own; every other determination is common to the product. <i class="bisep">|</i> <span class="mk">Оваа спецификација ги утврдува барањата за класата наведена во Погл. 01.</span></div>
<div class="sec-label"><span class="sec-no">03</span> Revision &amp; Authorisation <span class="mk">Ревизија и одобрување</span></div>
<div class="gridrow lk-inline g3">
{r4}
</div>
<div class="approval-grid cols-2">
<div><div class="ap-role">Prepared &amp; Approved by <span class="mk">Изготвил и одобрил</span></div><div class="ap-sign"><div class="ap-line"></div></div><div class="ap-title">QC Manager <span class="mk">Менаџер за КК</span></div><div class="ap-name">Blagoj Nikolov</div><div class="ap-cred">M.Pharm · Drug Quality Control Specialist</div><div class="ap-date-row"><span class="ap-date-label">Date · Датум</span><span class="ap-date-val">{issued}</span></div></div>
<div><div class="ap-role">Reviewed by <span class="mk">Прегледал</span></div><div class="ap-sign"><div class="ap-line"></div></div><div class="ap-title">QA Manager <span class="mk">Менаџер за ОК</span></div><div class="ap-name">Jovana Romevska Cvetkovski</div><div class="ap-cred">Master Pharmacist</div><div class="ap-date-row"><span class="ap-date-label">Date · Датум</span><span class="ap-date-val">{issued}</span></div></div>
</div>
<div class="footer">
<div class="foot-left">Purely Plant DOOEL · Industriska ulica 9, br. 9,<br>Kojlija 1043 · Petrovec-Skopje, North Macedonia</div>
<div class="foot-center-num">1 <span style="opacity:.6">|</span> 1</div>
<div class="foot-right">{docv}</div>
</div>
</div>
</body>
</html>
"""


def build():
    spec = json.load(open(os.path.join(HERE, "potency_specifications_25_2026-09-17.json"), encoding="utf-8"))
    qcsp = json.load(open(os.path.join(GAP, "product_specifications_QCSP001.json"), encoding="utf-8"))
    data = json.load(open(os.path.join(GAP, "coq_artifact_data.json"), encoding="utf-8"))
    dets = qcsp["determinations"]

    codes = {}
    for c in data["coqs"]:
        code = (c.get("spec") or "").strip()
        m = re.match(r"QCSP_001_([A-Z0-9]+)-([IVX]+)_v\.(\d+)$", code)
        if not m:
            continue
        cult, num = m.group(1), ROM[m.group(2)]
        s = spec.get(cult)
        if not s:
            raise SystemExit("%s names cultivar %s, which the potency decision does not carry" % (code, cult))
        grades = sorted(s["grades"], key=lambda g: -g[0])
        if num > len(grades):
            raise SystemExit("%s is grade %d and the decision gives %s %d" % (code, num, cult, len(grades)))
        nom, tol, lo, hi = grades[num - 1]
        sp = c.get("spc") or {}
        r = codes.setdefault(code, {"cult": cult, "numeral": m.group(2), "strain": s["strain"],
                                    "nominal": nom, "tol": tol, "lo": lo, "hi": hi,
                                    "pcode": set(), "pheno": set(), "chemo": set(),
                                    "pack": set(), "lots": set()})
        if c.get("pcode"):
            r["pcode"].add(c["pcode"])
        for k in ("pheno", "chemo", "pack"):
            v = (sp.get(k) or "").strip()
            if v:
                r[k].add(v)
        lot = c.get("pp") or c.get("cb")
        if lot:
            r["lots"].add(lot)

    os.makedirs(SHEETS, exist_ok=True)
    made = []
    for code in sorted(codes):
        r = codes[code]
        for k in ("pcode", "pheno", "chemo", "pack"):
            if len(r[k]) > 1:
                raise SystemExit("%s: its lots disagree about %s (%s) — a specification cannot "
                                 "choose between them" % (code, k, sorted(r[k])))
        window = "%.2f – %.2f %%" % (r["lo"], r["hi"])
        one = lambda k, d="—": (sorted(r[k])[0] if r[k] else d)
        page = PAGE.format(
            code=esc(code), strain=esc(r["strain"]), cult=esc(r["cult"]), numeral=esc(r["numeral"]),
            nominal="%.2f" % r["nominal"], issued=ISSUED, docv=esc(DOC_VERSION),
            pheno=chips("Phenotype", "Фенотип",
                        ["Hybrid", "Indica", "Sativa"], one("pheno")),
            chemo=chips("Chemotype", "Хемотип",
                        ["THC", "CBD"], one("chemo")),
            r1="\n".join([
                lk("Product Code", "Код на производ", one("pcode")),
                lk("Potency Grade", "Класа на јачина", "Grade %s | Класа %s" % (r["numeral"], r["numeral"])),
                lk("Monograph", "Монографија", "Ph. Eur. mon. 3028")]),
            r2="\n".join([
                lk("Grade Nominal", "Номинална вредност", "%.2f %%" % r["nominal"]),
                lk("Tolerance", "Толеранција", "± %.2f %%" % r["tol"]),
                lk("Specification Window", "Спецификациски опсег", window)]),
            r3="\n".join([
                lk("Dosage Form", "Дозажна форма", "Dry Cannabis Flower | Сув цвет од канабис"),
                lk("Product State", "Состојба", "Finished | Готов"),
                lk("Applies to Lots", "Се однесува на серии", "%d" % len(r["lots"]))]),
            r3b=lk("Contact Packaging", "Контактно пакување", one("pack")),
            r4="\n".join([
                lk("Document Version", "Верзија на документ", DOC_VERSION),
                lk("Supersedes", "Заменува", SUPERSEDES),
                lk("Potency Basis", "Основа за јачина", BASIS)]),
            rows=rows(dets, window))
        name = "%s_%s_Grade_%s.html" % (code, r["strain"].replace(" ", "_"), r["numeral"])
        open(os.path.join(SHEETS, name), "w", encoding="utf-8").write(page)
        made.append((code, r["strain"], r["numeral"], window, len(r["lots"]), name))

    index = {"document": DOC_VERSION, "issued": ISSUED, "supersedes": SUPERSEDES, "basis": BASIS,
             "sheets": [{"code": c, "strain": s, "grade": g, "window": w, "lots": n, "file": f}
                        for c, s, g, w, n, f in made]}
    json.dump(index, open(os.path.join(OUT, "INDEX.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("sheets written: %d" % len(made))
    return made


if __name__ == "__main__":
    build()
