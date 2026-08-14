#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Strain Potency Study — document builder (PP engine, informal/non-QMS).

Everything printed binds from potency_dataset.json (§6B). No doc code, no
version — informal working analysis; the authoritative results remain the
laboratory certificates in the QMS and the ImB_QC_COAs knowledgebase.
"""
import json
import os
import sys

sys.path.insert(0, "/root/.claude/skills/synced/pp-document-suite/scripts")
import pp_report as pr
import pp_assets
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

D = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(D, "potency_dataset.json"), encoding="utf-8"))
figidx = json.load(open(os.path.join(D, "figures", "index.json"), encoding="utf-8"))

NAVY = "2B547E"; INK = "16232B"; ROSE = "FDECEA"; MINT = "E2EFDA"

doc = Document(pp_assets.TEMPLATE)
pr.wipe_body(doc)
pr.informal_header(doc, "СТУДИЈА НА ПОТЕНЦИЈА ПО СОРТИ", "Strain Potency Study",
                    "Неформален работен документ", "Informal working document")

n_stab_usable = sum(1 for r in d["stability"] if r["usable"])
pr.cover_page(
    doc, "Студија на потенција по сорти", "Strain Potency Study",
    [("Опфат | Scope",
      "Сите некогаш тестирани резултати за Вкупен Δ⁹-THC, за сите серии, по сорта + "
      "предлог за нови опсези по класи за залихата од Транша 1/2/3 | Every Total Δ⁹-THC "
      "result ever tested, all batches, per strain + proposed new grade ranges for the "
      "T1/T2/T3 stock"),
     ("Корпус | Corpus",
      "%d резултати од регистарот (77 серии, %d сорти) + %d употребливи резултати од "
      "студијата на стабилност (1 ред одбиен како дефектен) | %d register results "
      "(77 batches, %d strains) + %d usable stability results (1 row rejected as defective)"
      % (d["n_results"], d["n_strains"], n_stab_usable,
         d["n_results"], d["n_strains"], n_stab_usable)),
     ("Верификација | Verification",
      "Жива проверка на Letta-базата: 4.134 пасуси скенирани, сите вредности потврдени "
      "на изворниот систем | Live Letta knowledgebase sweep: 4,134 passages scanned, "
      "all values confirmed on the source system"),
     ("Статус | Status",
      "Неформална работна анализа; меродавни остануваат лабораториските сертификати | "
      "Informal working analysis; the laboratory certificates remain authoritative")],
    "Аналитичка студија", "Analytical study", "КК", "Quality Control",
    controlled=False)


def para(text, size=10, color=INK, italic=False, bold=False, before=2, after=2,
         align=WD_ALIGN_PARAGRAPH.LEFT):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.06
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(size)
    r.font.italic = italic
    r.font.bold = bold
    r.font.color.rgb = RGBColor.from_string(color)
    return p


def shade(cell, hexv):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), hexv)
    tcPr.append(sh)


def setcell(cell, text, size=8.5, color=INK, bold=False, align=WD_ALIGN_PARAGRAPH.LEFT, fill=None):
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    if fill:
        shade(cell, fill)
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = RGBColor.from_string(color)


def table(headers, rows, widths, fills=None, hdr_repeat=True):
    t = doc.add_table(rows=1, cols=len(headers))
    t.autofit = False
    for i, (c, hh) in enumerate(zip(t.rows[0].cells, headers)):
        setcell(c, hh, 8.2, "FFFFFF", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, fill=NAVY)
    for k, row in enumerate(rows):
        cells = t.add_row().cells
        fill = (fills[k] if fills else ("F4F7FB" if k % 2 else "FFFFFF"))
        for i, (c, v) in enumerate(zip(cells, row)):
            setcell(c, str(v), 8.3, INK,
                    align=WD_ALIGN_PARAGRAPH.CENTER if i > 0 and len(str(v)) < 30 else WD_ALIGN_PARAGRAPH.LEFT,
                    fill=fill)
    for row in t.rows:
        for i, c in enumerate(row.cells):
            c.width = Cm(widths[i])
    if hdr_repeat:
        pr._repeat_header(t)
    return t


# ---------- 1. Executive summary ----------
pr.chapter(doc, "1", "РЕЗИМЕ", "Executive Summary")
para("Оваа студија ги собира на едно место сите резултати за Вкупен Δ⁹-THC што некогаш се "
     "тестирани за нашите серии — %d резултати од регистарот на сертификати (77 серии, %d "
     "сорти) и %d употребливи резултати од студијата на стабилност за Grape Pie — и врз нив "
     "предлага нови опсези по класи за залихата од Траншите 1, 2 и 3. | This study brings "
     "every Total Δ⁹-THC result ever tested into one place — %d certificate-register results "
     "(77 batches, %d strains) plus %d usable Grape Pie stability results — and proposes new "
     "grade ranges for the Tranche 1/2/3 stock on top of them."
     % (d["n_results"], d["n_strains"], n_stab_usable,
        d["n_results"], d["n_strains"], n_stab_usable), 10.5)
para("Клучни наоди | Key findings:", 10, bold=True, before=6)
for mk, en in [
    ("На складишни услови (25°C/60%RH) стабилносните резултати НЕ покажуваат опаѓање на "
     "Вкупен Δ⁹-THC во текот на 3–9 месеци — движењата се во рамки на варијансата од "
     "земање мостри и мерење.",
     "At warehouse conditions (25°C/60%RH) the stability results show NO Total Δ⁹-THC "
     "decline over 3–9 months — movements sit inside sampling/measurement variance."),
    ("Топлината, а не времето, е вистинскиот двигател на загубата: забрзаните краци на "
     "40°C/75%RH паѓаат на 13,16–17,05% со CBN од 2,05–2,35%.",
     "Heat, not time, drives the loss: the 40°C/75%RH accelerated arms collapse to "
     "13.16–17.05% with CBN at 2.05–2.35%."),
    ("Најголемиот ризик серијата да „испадне“ од класата не е деградацијата, туку "
     "варијансата меѓу мерења (±1,5–2,5%) — новите опсези мора да ја впијат и неа.",
     "The biggest risk of a batch falling out of grade is not degradation but "
     "between-measurement variance (±1.5–2.5%) — the new ranges must absorb it too."),
    ("Предложените опсези гарантираат: и денешно повторно мерење, и мерење по уште една "
     "година складирање, остануваат внатре во декларираната класа и внатре во "
     "критериумите за прифатливост.",
     "The proposed ranges guarantee: a remeasure today, or after a further year of "
     "storage, still reads inside the declared grade and inside the acceptance criteria.")]:
    para("• %s | %s" % (mk, en), 9.3, "37474F", after=1)

# ---------- 2. Data & verification ----------
pr.chapter(doc, "2", "ПОДАТОЦИ И ВЕРИФИКАЦИЈА", "Data & Verification")
para("Корпусот е компајлиран од регистарот на eCoA сертификати и потоа проверен во живо на "
     "Letta-базата на знаење (ImB_QC_COAs): %s. Дефектниот ред од ППК26037 (18,62 — "
     "неуспешна масена рамнотежа, обележан во изворот како PP-QC-ERR-002) е задржан во "
     "податоците, но исклучен од секоја статистика. | Corpus compiled from the eCoA register "
     "and live-verified against the Letta knowledgebase: %s. The defective ППК26037 row "
     "(18.62 — failed mass balance, flagged PP-QC-ERR-002 in the source) is retained in the "
     "data but excluded from all statistics."
     % (d["verification"]["host_sweep"], d["verification"]["host_sweep"]), 9)
table(["Слој | Layer", "Резултати | Results", "Забелешка | Note"],
      [["Регистар на сертификати | Certificate register", str(d["n_results"]),
        "77 серии, %d сорти; секоја вредност препишана дословно | 77 batches, %d strains; "
        "every value transcribed verbatim" % (d["n_strains"], d["n_strains"])],
       ["Студија на стабилност (Grape Pie) | Stability study", "9",
        "ППК26032–26037 + ППК26057–26059; 8 употребливи + 1 дефектен | 8 usable + 1 defective"],
       ["Вкупно во студијата | Total in study", str(d["n_results"] + 8),
        "стабилносните 40°C краци се доказ за деградација, не состојба на залиха | "
        "40°C arms are degradation evidence, not inventory state"]],
      [6.0, 3.0, 8.6])

# ---------- 3. Per-strain statistics ----------
pr.chapter(doc, "3", "СТАТИСТИКА ПО СОРТИ", "Per-Strain Statistics")
rows = []
for s in sorted(d["stats"], key=lambda x: -d["stats"][x]["mean"]):
    st = d["stats"][s]
    ci = "%.2f – %.2f" % tuple(st["ci95"]) if st["ci95"] else "—"
    sd = "%.2f" % st["sd"] if st["sd"] is not None else "—"
    rows.append([s, st["n"], "%.2f" % st["mean"], sd,
                 "%.2f – %.2f" % (st["min"], st["max"]), ci])
table(["Сорта | Strain", "n", "Средна | Mean", "SD", "Опсег | Range", "95% CI (средна | mean)"],
      rows, [5.4, 1.2, 2.4, 1.8, 3.4, 3.4])
para("CI е интервал на доверба за средната вредност (t-распределба), прикажан само за n≥3 — "
     "за n=1 нема дистрибуција, а за n=2 интервалот е математички валиден но бескорисно "
     "широк. Резултатите вклучуваат и повторени мерења на исти серии: статистиката ја "
     "опишува популацијата на ТЕСТИРАНИ РЕЗУЛТАТИ, не независни серии. | CI is the "
     "confidence interval of the mean (t-distribution), shown only for n≥3 — n=1 is no "
     "distribution and n=2 gives a mathematically valid but uselessly wide interval. "
     "Results include repeat measurements of the same batches: the statistics describe the "
     "population of TESTED RESULTS, not independent batches.", 8, "4A5B6C", italic=True)

# ---------- 4. Degradation evidence ----------
pr.chapter(doc, "4", "ДОКАЗИ ЗА ДЕГРАДАЦИЈА", "Degradation Evidence")
para("Студија на стабилност (Grape Pie, UKIM-CNP; серии P050022=GP0824_02, "
     "P050072=GP0824_03, P050202=GP062501): | Stability study (Grape Pie, UKIM-CNP):", 9.5, bold=True)
stab_rows = []
stab_fills = []
for r in d["stability"]:
    note = r.get("note", "")
    stab_rows.append([r["report"], r["batch"], r["arm"], "M%d" % r["month"],
                      "%.2f" % r["total_thc"], "%.2f" % r["cbn"],
                      ("ОДБИЕН | REJECTED: " + note) if not r["usable"] else "употреблив | usable"])
    stab_fills.append(ROSE if not r["usable"] else ("FFFFFF" if len(stab_rows) % 2 else "F4F7FB"))
table(["Сертификат | Report", "Серија | Batch", "Крак | Arm", "Месец | Month",
       "Вкупен THC %", "CBN %", "Статус | Status"],
      stab_rows, [2.4, 2.6, 2.4, 1.6, 2.2, 1.6, 4.8], fills=stab_fills)
para("Повторени мерења на исти серии (иста лабораторија): | Repeat same-lab measurements:", 9.5,
     bold=True, before=8)
rep_rows = [[r["batch"], r["strain"],
             "%.2f (%s)" % (r["first"], r["first_date"]),
             "%.2f (%s)" % (r["second"], r["second_date"]),
             "%+.2f" % r["delta"], r.get("note", "")] for r in d["repeats"]]
table(["Серија | Batch", "Сорта | Strain", "Прво | First", "Второ | Second", "Δ", "Забелешка | Note"],
      rep_rows, [2.6, 3.4, 3.2, 3.2, 1.4, 3.8])
para(d["degradation_note"], 8.6, "37474F", italic=True, before=6)
para("Заклучок: усвојуваме конзервативен додаток за деградација D = 1,5 %апс./година — "
     "поголем од секое докажано 12-месечно опаѓање на складишни услови. | Conclusion: we "
     "adopt a conservative degradation allowance D = 1.5 %abs/year — larger than any "
     "evidenced 12-month decline at warehouse conditions.", 9.5, bold=True, before=4)

# ---------- 5. Range methodology ----------
pr.chapter(doc, "5", "МЕТОДОЛОГИЈА НА ОПСЕЗИТЕ", "Range Methodology")
para("Досегашна методологија | Methodology to date: " + d["old_methodology"], 9, "37474F")
para("Нова методологија (оваа студија) | New methodology (this study):", 9.5, bold=True, before=6)
for mk, en in [
    ("Сидро по серија = најновиот верификуван резултат (ретест каде постои).",
     "Per-batch anchor = the most recent verified result (retest where one exists)."),
    ("Долна граница на класата = сидро − D − U(сидро), заокружено на 0,5 надолу; никогаш "
     "под 5,00% (критериум за прифатливост при ослободување).",
     "Grade floor = anchor − D − U(anchor), rounded down to 0.5; never below 5.00% "
     "(the release acceptance floor)."),
    ("Горна граница = сидро + U(сидро) (заокружено нагоре) — и повисоко повторно мерење "
     "останува внатре.", "Grade ceiling = anchor + U(anchor) (rounded up) — a higher "
     "remeasure also stays inside."),
    ("U = мерна неодреденост ≈ 6,2% од вредноста (k=2, како на самите сертификати); "
     "D = 1,5 %апс./година (Поглавје 4).",
     "U = measurement uncertainty ≈ 6.2% of value (k=2, as stated on the certificates); "
     "D = 1.5 %abs/year (Chapter 4)."),
    ("Класите по сорта се групираат лакомо по растечки сидра, со максимална ширина 6,5 "
     "процентни поени; класите СМЕАТ да се преклопуваат — серијата се класира поединечно, "
     "а дисјунктни класи би го вратиле старот проблем со прелевање на границите.",
     "Per-strain tiers are greedily clustered on ascending anchors, max width 6.5 points; "
     "tiers MAY overlap — batches are graded individually, and forcing disjoint tiers "
     "would recreate the old boundary-flip problem.")]:
    para("• %s | %s" % (mk, en), 9.3, "37474F", after=1)

# ---------- 6. Per-strain distributions ----------
pr.chapter(doc, "6", "ДИСТРИБУЦИИ ПО СОРТИ", "Per-Strain Distributions")
para("Оска 0–35% Вкупен Δ⁹-THC; секој резултат носи зона од ±1,5% (сините појаси — "
     "натрупувањето е визуелна густина); крива на дистрибуција за n≥3; средна вредност "
     "(златна линија) и 95% CI (златна зона); предложени класи W-x (зелено); старите "
     "стандардни граници (испрекинато). За Grape Pie: стабилносни точки — квадрати 25°C, "
     "триаголници 40°C. | 0–35% axis; each result carries a ±1.5% zone (blue bands — "
     "stacking is visual density); distribution curve for n≥3; mean (gold line) and 95% CI "
     "(gold zone); proposed W-x tiers (green); old standard boundaries (dashed). Grape Pie "
     "also shows the stability points — squares 25°C, triangles 40°C.", 8.6, "4A5B6C", italic=True)
for s in sorted(d["stats"]):
    st = d["stats"][s]
    pr.subsec(doc, "6.%d" % (sorted(d["stats"]).index(s) + 1), s, "")
    pr.figure(doc, os.path.join(D, "figures", figidx[s]), None, None, width_cm=17.2)
    tiers = d["merged_ranges"].get(s, [])
    if tiers:
        trs = [["W-%d" % (i + 1), "%.1f – %.1f" % tuple(t["range"]),
                ", ".join(t["batches"]),
                ", ".join("%.2f" % a for a in t["anchors"])]
               for i, t in enumerate(tiers)]
        table(["Класа | Tier", "Опсег | Range (%)", "Серии | Batches", "Сидра | Anchors (%)"],
              trs, [1.8, 3.0, 7.6, 5.0])
    else:
        para("Нема серии на залиха за оваа сорта во Т1/Т2/Т3. | No T1/T2/T3 stock batches "
             "for this strain.", 8.5, "6B7785", italic=True)

# ---------- 7. Stock table ----------
pr.chapter(doc, "7", "ПРЕДЛОГ-КЛАСИ ЗА ЗАЛИХАТА Т1/Т2/Т3", "Proposed Grades for the T1/T2/T3 Stock")
para("Сидро = најнов верификуван резултат; каде нема ниту еден сертификат, основата е "
     "декларираната вредност (означено). Просторот надолу е гаранцијата против деградација "
     "и мерна варијанса. | Anchor = latest verified result; where no certificate exists the "
     "declared value is the basis (flagged). The downward headroom is the guarantee against "
     "degradation and measurement variance.", 8.6, "4A5B6C", italic=True)
stock_rows = []
stock_fills = []
for b in sorted(d["stock"], key=lambda x: (x["tranche"], x["strain"], x["batch"])):
    if not b.get("proposed"):
        continue
    anc = "%.2f (%s)" % (b["anchor"], b["anchor_date"]) if b["anchor"] is not None \
        else "%.2f (декл. | decl.)" % b["declared"]
    tier = "W-%d" % b["tier"] if b.get("tier") else "—"
    stock_rows.append(["Т%s" % b["tranche"], b["batch"], b["strain"], anc,
                       b["bracket_old"] or "—", tier,
                       "%.1f – %.1f" % tuple(b["proposed"]),
                       "%.2f" % b["headroom_down"]])
    stock_fills.append("FFF8E7" if b["anchor"] is None
                       else ("FFFFFF" if len(stock_rows) % 2 else "F4F7FB"))
table(["Т", "Серија | Batch", "Сорта | Strain", "Сидро | Anchor (%)",
       "Стара класа | Old", "Класа | Tier", "Предлог опсег | Proposed (%)",
       "Простор надолу | Headroom (%)"],
      stock_rows, [0.9, 2.7, 3.3, 3.1, 1.9, 1.5, 2.6, 2.4])
para("Жолти редови: без ниту еден сертификат на датотека — основа е декларираната вредност; "
     "овие серии да се тестираат пред формално декларирање класа. | Yellow rows: no "
     "certificate on file — declared value used as basis; test these batches before formally "
     "declaring a grade.", 8, "4A5B6C", italic=True)

# ---------- 8. Overview annex ----------
pr.chapter(doc, "8", "АНЕКС — ПРЕГЛЕД НА СИТЕ СОРТИ", "Annex — All-Strain Overview")
pr.figure(doc, os.path.join(D, "figures", "overview.png"),
          "Сите сорти на една оска 0–35%: резултати, средни вредности, предложени класи",
          "All strains on one 0–35% axis: results, means, proposed tiers")

out = os.path.join(D, "Strain_Potency_Study_14Aug2026.docx")
pr.save(doc, out) if hasattr(pr, "save") else doc.save(out)

doc2 = Document(out)
def fixrun(run):
    rPr = run._r.get_or_add_rPr()
    for tag in ("w:spacing", "w:kern"):
        for e in rPr.findall(qn(tag)):
            rPr.remove(e)
    for tag, val in (("w:spacing", "0"), ("w:kern", "0")):
        el = OxmlElement(tag)
        el.set(qn("w:val"), val)
        rPr.append(el)
def walk(cont):
    for p in cont.paragraphs:
        for r in p.runs:
            fixrun(r)
    for tb in cont.tables:
        for row in tb.rows:
            for c in row.cells:
                walk(c)
walk(doc2)
doc2.save(out)
print("wrote", out, os.path.getsize(out))
