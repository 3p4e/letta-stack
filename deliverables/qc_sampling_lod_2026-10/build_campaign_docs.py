#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build PP-QC-SP-002/26 — the sampling plan (package 1) — with the Purely Plant document engine
(pp-document-suite, python-docx), and hold the helpers the execution packages share
(build_execution_packages.py, build_labels.py). Every number printed here is read from
SAMPLING_PLAN_T1_T2_2026-10.tsv and bag_selection.tsv (campaign_data.py); the engine owns the
appearance. Each output is passed through pp_verify.py and the build fails on anything but PASS.

    python3 build_campaign_docs.py            # -> out/1_PLAN/*.docx
"""
import csv
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
ENGINE = os.path.join(REPO, "pp-document-suite", "scripts")
sys.path.insert(0, ENGINE)
import pp_format as pf      # noqa: E402
import pp_report as pr      # noqa: E402
import pp_assets            # noqa: E402
from docx.enum.table import WD_TABLE_ALIGNMENT  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402

OUT = os.path.join(HERE, "out")
OUT_P = os.path.join(OUT, "1_PLAN")
PLAN_TSV = os.path.join(HERE, "SAMPLING_PLAN_T1_T2_2026-10.tsv")
BAGS_TSV = os.path.join(HERE, "bag_selection.tsv")

CODE = "PP-QC-SP-002/26"
STATUS = "in_review"          # becomes "approved" + effective date only on the Head of QC's word
VERSION = "1.0"
PREPARED = ("Изготвил | Prepared (Раководител КК | QC Head)", "B. Nikolov, M.Pharm.")
CHECKED = ("Проверил | Checked (QA)", "J. Romevska")
APPROVED = ("Одобрил | Approved (Раководител на КК оддел | QC Department Manager)", "B. Nikolov, M.Pharm.")
ANALYST = "Hristina Cekic (КК аналитичар | QC Analyst)"
ZEBRA = "F7FAFC"
BLANK = "____________"


# ----------------------------------------------------------------------------- data
def load():
    lots = list(csv.DictReader(open(PLAN_TSV, encoding="utf-8"), delimiter="\t"))
    for l in lots:
        for k in ("day", "seq", "tranche", "N", "n", "k"):
            l[k] = int(l[k])
        for k in ("interval", "start"):            # empty since the 06.10.2026 amendment (one bag per batch)
            l[k] = int(l[k]) if l[k] else None
        for k in ("kg_master", "kg_stock", "kg_used", "composite_g_low", "composite_g_high", "test_portions_g"):
            l[k] = float(l[k]) if l[k] not in ("", None) else None
        l["bag_list"] = l["bags"].split()
        l["carton_list"] = [int(c) for c in l["cartons"].split()]
    bags = list(csv.DictReader(open(BAGS_TSV, encoding="utf-8"), delimiter="\t"))
    return lots, bags


def num(x, dec=2):
    s = ("%." + str(dec) + "f") % x
    return s.replace(".", ",")


def lod_text(l):
    if not l["last_lod_res"]:
        return "—"
    v = l["last_lod_res"].replace("%", "").strip().replace(".", ",")
    return "%s %% · %s · %s" % (v, l["last_lod_lab"], l["last_lod_date"])


def ranges(nums):
    """1 2 3 5 7 8 -> '1–3, 5, 7–8' (the CoQ section-03 convention for runs of three or more)."""
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append("%d–%d" % (nums[i], nums[j]) if j - i >= 2 else ", ".join(str(x) for x in nums[i:j + 1]))
        i = j + 1
    return ", ".join(out)


# ----------------------------------------------------------------------------- engine helpers
def table(d, header, rows, weights=None, sz=8, label_first=False, mode=None):
    t = d.add_table(rows=len(rows) + 1, cols=len(header))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(header):
        pr.cellfmt(t.cell(0, j), h, None, sz, pr.WHITE, bold=True, fill=pr.NAVYF)
    for i, row in enumerate(rows, start=1):
        for j, v in enumerate(row):
            fill = pr.LBL if (label_first and j == 0) else (ZEBRA if i % 2 == 0 else None)
            pr.cellfmt(t.cell(i, j), "" if v is None else str(v), None, sz, pr.BLACK, fill=fill)
    pr.fixed(t, weights, mode=mode)
    pr.borders(t)
    for r in t.rows:                 # a row never breaks across a page
        r._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    return t


def kv_table(d, rows, sz=9):
    """label | value pairs (value may be a blank write-in)."""
    t = d.add_table(rows=len(rows), cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, (k, v) in enumerate(rows):
        pr.cellfmt(t.cell(i, 0), k, None, sz, pr.BLACK, bold=True, fill=pr.LBL)
        pr.cellfmt(t.cell(i, 1), v, None, sz, pr.BLACK)
    pr.fixed(t, [6.2, pr.PAGE_W - 6.2])
    pr.borders(t)
    return t


def sign_table(d, roles, sz=9):
    h = ["Улога | Role", "Име/Позиција | Name/Position", "Датум | Date", "Потпис | Signature"]
    t = d.add_table(rows=len(roles) + 1, cols=4)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, x in enumerate(h):
        pr.cellfmt(t.cell(0, j), x, None, sz, pr.WHITE, bold=True, fill=pr.NAVYF)
    for i, role in enumerate(roles, start=1):
        pr.cellfmt(t.cell(i, 0), role, None, sz, pr.BLACK, fill=pr.LBL)
        for j in (1, 2, 3):
            pr.cellfmt(t.cell(i, j), "", None, sz, pr.BLACK)
    pr.fixed(t, [7.26, 5.2, 2.6, 3.4])
    pr.borders(t)
    return t


def new_doc(code, mk_title, en_title):
    pr.PAGE_W = 18.46
    return pf.new_annex(code=code, version=VERSION, mk_title=mk_title, en_title=en_title,
                        orient="portrait", status=STATUS)


def cover(d, title_mk, title_en, info_rows, kind_mk, kind_en, study_mk, study_en):
    pr.cover_page(d, title_mk, title_en, info_rows, kind_mk=kind_mk, kind_en=kind_en,
                  study_mk=study_mk, study_en=study_en,
                  approval_rows=[PREPARED, CHECKED, APPROVED], status=STATUS, version=VERSION)
    pr.fixed(d.tables[-3], [pr.PAGE_W])      # the status band otherwise collapses to the "date" width


def glyph_audit(d):
    text = "".join(t.text or "" for t in d.element.body.iter() if t.tag.endswith("}t"))
    missing = sorted({ch for ch in set(text) if pp_assets.missing_glyphs("Calibri", ch)})
    if missing:
        raise SystemExit("glyphs missing from the house face: %r" % missing)


def verify(path):
    v = subprocess.run([sys.executable, os.path.join(ENGINE, "pp_verify.py"), path],
                       capture_output=True, text=True)
    ok = "RESULT: PASS" in v.stdout
    print(("PASS " if ok else "FAIL ") + os.path.basename(path))
    if not ok:
        print(v.stdout, v.stderr)
    return ok


def chapter(d, num_, mk, en):
    """Engine chapter heading kept on the page of what follows it (no heading alone at a page foot)."""
    p = pr.chapter(d, num_, mk, en)
    p.paragraph_format.keep_with_next = True
    return p


def contents_page(d, chapters):
    """Static contents list. A native TOC field stays empty under headless LibreOffice (fields are
    not updated on conversion), so the chapter list is printed as text."""
    p = d.add_paragraph(); pr.sp(p, 6, 8)
    pr.rin(p, "СОДРЖИНА", 16, pr.NAVY, bold=True); pr.rin(p, "  |  ", 12, pr.GREY); pr.rin(p, "Table of Contents", 12, pr.GREY)
    for num_, mk, en in chapters:
        q = d.add_paragraph(); pr.sp(q, 1, 1)
        pr.rin(q, "%s  %s" % (num_, mk), 11, pr.BLACK); pr.rin(q, "  |  ", 9, pr.GREY); pr.rin(q, en, 9, pr.GREY, ital=True)
    d.add_page_break()


PLAN_CHAPTERS = [
    ("1", "ЦЕЛ И ОПФАТ", "Purpose & Scope"), ("2", "ПРИНЦИП И ОСНОВА", "Principle & Basis"),
    ("3", "ФОРМУЛИ", "Formulas"), ("4", "ПЛАН ПО СЕРИЈА (4a, 4b, 4.1)", "Per-Batch Plan (4a, 4b, 4.1)"),
    ("5", "УСЛОВИ, ИЗБОР НА КЕСИ И СЛЕДЛИВОСТ", "Conditions, Bag Selection & Traceability"),
    ("6", "ПРИМЕРОК И ТЕСТ ПОРЦИЈА", "Sample and Test Portion"),
    ("7", "ОПРЕДЕЛУВАЊЕ НА ГУБИТОК ПРИ СУШЕЊЕ (a02.2)", "Loss on Drying Determination (a02.2)"),
    ("8", "РАСПОРЕД", "Schedule"), ("9", "ЗАПИСИ", "Records"), ("10", "РЕФЕРЕНТНИ ДОКУМЕНТИ", "References"),
    ("11", "ОТВОРЕНИ ТОЧКИ ЗА РАКОВОДИТЕЛОТ НА КК", "Open Items for the Head of QC"),
]


# ----------------------------------------------------------------------------- the plan
def build_plan(lots):
    by_day = {1: [l for l in lots if l["day"] == 1], 2: [l for l in lots if l["day"] == 2]}
    tot_n = sum(l["n"] for l in lots)
    tot_k = sum(l["k"] for l in lots)
    tot_kg = sum(l["kg_used"] for l in lots)
    tot_N = sum(l["N"] for l in lots)
    seed = 20261005

    d = new_doc(CODE, "ПЛАН ЗА ЗЕМАЊЕ ПРИМЕРОЦИ И ГУБИТОК ПРИ СУШЕЊЕ — ТРАНША 1 И 2",
                "SAMPLING PLAN AND LOSS ON DRYING — TRANCHES 1 AND 2")
    cover(d, "План за земање примероци и интерно определување на губиток при сушење пред испорака",
          "Sampling plan and in-house loss-on-drying determination before shipment",
          [("Документ бр. | Document No.", CODE),
           ("Локација | Location", "Сеф-магацин · КК лабораторија | Secure warehouse · QC laboratory"),
           ("Производ | Product", "Сув цвет од канабис, готов производ · кеса 400 g (10 кеси/картон) | "
                                  "Dry cannabis flower, finished product · 400 g bag (10 bags/carton)"),
           ("Серии | Batches", "46 — Транша 1: 20 · Транша 2: 26 | 46 — Tranche 1: 20 · Tranche 2: 26"),
           ("Намена | Purpose", "Губиток при сушење, Ph. Eur. 2.2.32 (3028), метод a02.2 · критериум ≤ 12,0 % w/w | "
                                "Loss on drying, Ph. Eur. 2.2.32 (3028), method a02.2 · criterion ≤ 12.0 % w/w"),
           ("Основа | Basis", "QCSOP 011 v03 (SP-12) · една кеса и една тест порција по серија (Раководител на КК, 06.10.2026) | one bag and one test portion per batch (Head of QC, 06.10.2026)"),
           ("Земање | Sampling", "1 ден · %d кеси · 1 примерок по серија | 1 day · %d bags · 1 sample per batch" % (tot_n, tot_n)),
           ("Резултати | Results", "Ден 2: %d порции во едно сушење (24 h + второ мерење до константна маса) | "
                                   "Day 2: %d portions in one oven run (24 h + second weighing to constant mass)" % (tot_k, tot_k))],
          "ПЛАН И ИЗВРШЕН ПРОТОКОЛ ЗА ЗЕМАЊЕ ПРИМЕРОЦИ", "Sampling Plan & Execution Protocol",
          "Производни серии во сеф-магацин · 46 серии · %s kg" % num(tot_kg),
          "Production batches in secure storage · 46 batches · %s kg" % ("%.2f" % tot_kg))
    contents_page(d, PLAN_CHAPTERS)

    # 1
    chapter(d, "1", "ЦЕЛ И ОПФАТ", "Purpose & Scope")
    pr.body(d, "Овој документ го пропишува земањето репрезентативен примерок од секоја од 46-те производни серии "
               "од Транша 1 (20 серии) и Транша 2 (26 серии), складирани во сеф-магацинот како готов производ во троен "
               "фолиски кеси од 400 g (10 кеси по нумериран картон), и интерното определување на губиток при сушење "
               "(Ph. Eur. 2.2.32; монографија 3028 Cannabis flos; метод a02.2) пред испорака, за да се потврди "
               "дека нивото на влага на производот одговара на спецификацијата QCSP 001 (≤ 12,0 % w/w).",
            "This document prescribes the representative sampling of each of the 46 production batches of Tranche 1 "
            "(20 batches) and Tranche 2 (26 batches), stored in the secure warehouse as finished product in 400 g "
            "triple-foil bags (10 bags per numbered carton), and the in-house determination of loss on drying "
            "(Ph. Eur. 2.2.32; monograph 3028 Cannabis flos; method a02.2) before shipment, to confirm "
            "that the product's moisture level meets specification QCSP 001 (≤ 12.0 % w/w).")
    pr.body(d, "Точка на земање: SP-12 — готов производ во магацин (QCSOP 011 v03). Крајната точка е физичко-хемиска, "
               "па не се бара асептична техника. Сите 46 серии се земаат во еден ден, по една кеса од серија; по една тест "
               "порција од секоја серија оди во едно сушење, а резултатите се читаат следниот ден. Транша 3 (31 серии) следи "
               "со PP-QC-SP-003/26.",
            "Sampling point: SP-12 — finished product in the warehouse (QCSOP 011 v03). The endpoint is physico-chemical, "
            "so no aseptic technique is required. All 46 batches are sampled on one day, one bag per batch; one test portion "
            "per batch goes into one oven run, and the results are read the next day. Tranche 3 (31 batches) follows as "
            "PP-QC-SP-003/26.")
    pr.note(d, "Измена од 06.10.2026 (Раководител на КК): една кеса и една тест порција по серија, сите серии во еден ден и "
               "едно сушење, како што е извршено. Ги заменува r-планот (n = 1,5·√N кеси), правилото k = 1/2/3 и поделбата во "
               "два дена од нацртот од 05.10.2026.",
            "Amendment of 06.10.2026 (Head of QC): one bag and one test portion per batch, all batches on one day and in one "
            "oven run, as executed. It replaces the r-plan (n = 1.5·√N bags), the k = 1/2/3 rule and the two-day split of "
            "the draft of 05.10.2026.")

    # 2
    chapter(d, "2", "ПРИНЦИП И ОСНОВА", "Principle & Basis")
    pr.bullet(d, "Единица за земање е фолиската кеса од 400 g (примарен затворен сад); картонот со 10 кеси е секундарно "
                 "пакување и не е единица за земање.",
              "The sampling unit is the 400 g foil bag (primary sealed container); the 10-bag carton is secondary "
              "packaging and not the sampling unit.")
    pr.bullet(d, "Од секоја серија се отвора ЕДНА кеса (Раководител на КК, 06.10.2026), избрана при земањето; нејзиниот "
                 "број K{картон}B{кеса} се запишува на обрасците.",
              "ONE bag is opened per batch (Head of QC, 06.10.2026), chosen at sampling; its number K{carton}B{bag} is "
              "written on the forms.")
    pr.bullet(d, "Од кесата се зема примерокот на серијата во еден затворен означен сад; кесата се затвора веднаш.",
              "The batch sample is taken from that bag into one closed, labelled container; the bag is closed at once.")
    pr.bullet(d, "Се определува ЕДНА тест порција по серија (Раководител на КК, 06.10.2026); нејзиниот резултат е "
                 "резултатот на серијата; критериум ≤ 12,0 % w/w.",
              "ONE test portion is determined per batch (Head of QC, 06.10.2026); its result is the batch result; "
              "criterion ≤ 12.0 % w/w.")
    pr.note(d, "QCSOP 011 v03 (§5) дефинира дупликат за губиток при сушење при SP-06 (пред пакување). За SP-12 важи "
               "одлуката на Раководителот на КК од 06.10.2026 (поглавје 11).",
            "QCSOP 011 v03 (§5) defines a duplicate for loss on drying at SP-06 (pre-packaging). For SP-12 the Head of "
            "QC's decision of 06.10.2026 applies (section 11).")

    # 3
    chapter(d, "3", "ФОРМУЛИ", "Formulas")
    table(d, ["Величина | Quantity", "Формула | Formula", "Забелешка | Note"], [
        ["Број на кеси во серијата | Bags in the batch", "N = kg ÷ 0,400, заокружено нагоре | N = kg ÷ 0.400, rounded up",
         "информативно; kg од мастер v57 (Reference, „DELIVERY T1–T3“) | informative; kg from master v57 (Reference, “DELIVERY T1–T3”)"],
        ["Кеси за отворање | Bags to open", "n = 1", "една кеса по серија, избрана при земањето, ознака K{картон}B{кеса} | "
         "one bag per batch, chosen at sampling, key K{carton}B{bag}"],
        ["Определувања | Determinations", "k = 1", "една тест порција по серија | one test portion per batch"],
        ["Тест порција | Test portion", "1,000 g во претходно исушен тариран сад (m_B) | 1.000 g in a previously dried tared bottle (m_B)", "a02.2"],
        ["Губиток при сушење | Loss on drying", "ГпС % = (m₀ − m₁) ÷ m₀ × 100 | LoD % = (m₀ − m₁) ÷ m₀ × 100",
         "m₀ = G1 − m_B пред сушење | before drying; m₁ = G2 − m_B по сушење до константна маса | after drying to constant mass"],
        ["Резултат на серија | Batch result", "резултатот од едната порција | the result of the one portion",
         "критериум ≤ 12,0 % w/w | criterion ≤ 12.0 % w/w"],
    ], sz=8)

    # 4
    chapter(d, "4", "ПЛАН ПО СЕРИЈА", "Per-Batch Plan")
    ordered = sorted(lots, key=lambda l: (l["tranche"], l["batch"]))
    idx = {l["batch"]: i for i, l in enumerate(ordered, start=1)}
    pr.subsec(d, "4a", "Идентитет и количина", "Identity and quantity")
    rows = []
    for i, l in enumerate(ordered, start=1):
        rows.append([i, "T%d" % l["tranche"], l["batch"], l["p_lot"], l["strain"], l["grade"] or "—", l["warehouse"],
                     num(l["kg_master"]), num(l["kg_stock"]) if l["kg_stock"] is not None else "—",
                     l["packaging_date"] or "—"])
    rows.append(["", "", "ВКУПНО | TOTAL", "", "46 серии | batches", "", "", num(sum(l["kg_master"] for l in lots)),
                 num(sum(l["kg_stock"] or 0 for l in lots)), ""])
    table(d, ["№", "Т | T", "Серија | Batch", "P лот | P lot", "Сорта | Strain", "Класа | Grade",
              "Магацин | Warehouse", "kg (мастер v57) | kg (master v57)", "kg (залиха 08/2026) | kg (stock 08/2026)",
              "Пакување | Packaging"], rows, sz=7)
    pr.note(d, "GG1024_01 (P050092): мастер v57, Reference E216 чита 0,87 kg наспроти 223,734 kg на табелата за залиха "
               "и 560 кеси во PP-QC-SP-001/26; планот користи 223,73 kg (N 560), а ќелијата во мастерот бара поправка. "
               "KC102501 (P060172): мастер 21,67 kg наспроти 16,000 kg залиха — планот го користи мастерот, како што е одлучено.",
            "GG1024_01 (P050092): master v57, Reference E216 reads 0.87 kg against 223.734 kg on the stock table and 560 bags "
            "in PP-QC-SP-001/26; the plan uses 223.73 kg (N 560) and the master cell needs correction. KC102501 (P060172): "
            "master 21.67 kg against 16.000 kg stock — the plan uses the master, as decided.")
    pr.subsec(d, "4b", "Земање и определување", "Sampling and determination")
    rows = []
    for i, l in enumerate(ordered, start=1):
        rows.append([i, l["batch"], l["p_lot"], l["N"], l["n"], l["k"], "K___B___", lod_text(l),
                     "Ден %d | Day %d" % (l["day"], l["day"])])
    rows.append(["", "ВКУПНО | TOTAL", "", tot_N, tot_n, tot_k, "", "", ""])
    table(d, ["№", "Серија | Batch", "P лот | P lot", "N", "n", "k", "Кеса | Bag", "Последен ГпС на запис | Last LoD on record",
              "Ден | Day"], rows, sz=7)
    pr.note(d, "N е изведено од kg (кеси од 400 g) и е информативно. Бројот на кесата се запишува при земањето. "
               "„Последен ГпС на запис“ е информативен: вредноста, лабораторијата и датумот од регистарот на сертификати "
               "(coq_artifact_data.json).",
            "N is derived from kg (400 g bags) and is informative. The bag number is written at sampling. “Last LoD on "
            "record” is informative: value, laboratory and date from the certificate register (coq_artifact_data.json).")

    pr.subsec(d, "4.1", "Еден ден на земање, едно сушење", "One sampling day, one oven run")
    rows = [["Ден 1 | Day 1", BLANK, "земање, примероци во КК, во печката | sampling, samples to QC, into the oven",
             len(lots), tot_n, tot_k],
            ["Ден 2 | Day 2", BLANK, "мерење по 24 h, константна маса, резултати | 24-h weighing, constant mass, results",
             len(lots), "—", tot_k]]
    table(d, ["Ден | Day", "Датум | Date", "Активност | Activity", "Серии | Batches", "Кеси | Bags", "Порции | Portions"],
          rows, weights=[2.2, 2.6, 6.4, 1.9, 1.9, 1.9], sz=8)
    pr.body(d, "Редоследот на повлекување следи по магацин (E66 → E46/47 → F131 → Sec.Pack), па по транша и серија. "
               "Сите %d тест порции влегуваат во печката во едно сушење." % tot_k,
            "The retrieval order follows the warehouse (E66 → E46/47 → F131 → Sec.Pack), then tranche and batch. All %d "
            "test portions go into the oven in one run." % tot_k)

    # 5
    chapter(d, "5", "УСЛОВИ, ИЗБОР НА КЕСИ И СЛЕДЛИВОСТ", "Conditions, Bag Selection & Traceability")
    for mk, en in [
        ("Чист и сув прибор од нерѓосувачки челик, ракавици; нема барање за асептична техника (физичко-хемиска крајна "
         "точка). Времето надвор од складиште се минимизира; кесата се затвора веднаш по земањето.",
         "Clean, dry stainless-steel tools and gloves; no aseptic requirement (physico-chemical endpoint). Time out of "
         "storage is minimised; the bag is closed immediately after sampling."),
        ("Една кеса по серија, избрана при земањето; нејзиниот број K{картон}B{кеса} се запишува на QCT 024 (прием) и "
         "истата ознака се користи на секој запис и етикета за таа кеса.",
         "One bag per batch, chosen at sampling; its number K{carton}B{bag} is written on QCT 024 (receipt) and the same key "
         "is used on every record and label for that bag."),
        ("Визуелна инспекција при отворање според критериумите на QCSOP 011_A03 (боја/мирис, мувла, штетници, страни "
         "материи/семки, оштетено пакување) — „не одговара“ → карантин и отстапување; бруто се мери при прием (QCT 024); "
         "се зема примерокот на серијата; бруто се мери по затворање; пред, мострирано и после се на QCT 021.",
         "Visual inspection on opening against the QCSOP 011_A03 criteria (colour/odour, mould, pests, foreign matter/seeds, "
         "pack damage) — “does not conform” → quarantine and deviation; gross weighed at receipt (QCT 024); the batch "
         "sample is taken; gross weighed after closing; before, sampled and after are on QCT 021."),
        ("Извор на вистина за масите: нето = етикетата на примарното пакување (400,0 g, се препишува); бруто = го мери КК; "
         "мострирано = пред − после (QCT 021). Отворената кеса се означува „МОСТРИРАНО“ (QASOP_031_A05_v1); примерокот "
         "добива етикета QASOP_031_A07; новото нето/бруто е на QCT 021 и QCT 024 (враќање).",
         "Mass source of truth: net = the primary-pack label (400.0 g, transcribed); gross = weighed by QC; sampled = gross "
         "before − after (QCT 021). The opened bag is labelled “SAMPLED” (QASOP_031_A05_v1); the sample gets a QASOP_031_A07 "
         "label; the new net/gross is on QCT 021 and QCT 024 (return)."),
        ("Примерокот на секоја серија е во еден чист затворен сад означен со шифрата на примерокот "
         "([NNN/26_SFR]-PC-[бр.], QCSOP 011 v03 §6.2.1) и се пренесува во КК лабораторијата истиот ден на QCT 024 "
         "(примероци).",
         "Each batch's sample is in one clean closed container labelled with the sample code "
         "([NNN/26_SFR]-PC-[no.], QCSOP 011 v03 §6.2.1) and taken to the QC laboratory the same day on QCT 024 "
         "(samples)."),
        ("Документација: истовремено, со трајно сино мастило, без празни полиња („N/A“), поправки со една линија, "
         "иницијали и датум (ALCOA+; EU GMP Annex 11; СОП за работа со аналитичка документација).",
         "Documentation: contemporaneous, permanent blue ink, no blank fields (“N/A”), single-line corrections with "
         "initials and date (ALCOA+; EU GMP Annex 11; the SOP for working with analytical documentation)."),
    ]:
        pr.bullet(d, mk, en)

    # 6
    chapter(d, "6", "ПРИМЕРОК И ТЕСТ ПОРЦИЈА", "Sample and Test Portion")
    for mk, en in [
        ("Истиот ден, во КК лабораторијата, на записот за анализа (LOD-01, делови A и C): масата на примерокот се "
         "препишува од QCT 021.",
         "The same day, in the QC laboratory, on the analysis record (LOD-01, sections A and C): the sample mass is "
         "transcribed from QCT 021."),
        ("Примерокот се сече грубо со чисти ножици од нерѓосувачки челик на чиста подлога и се меша.",
         "The sample is coarsely cut with clean stainless-steel scissors on a clean tray and mixed."),
        ("Се зема една тест порција од 1,000 g сецкана, несеана дрога во тариран, претходно исушен сад за мерење (m_B) "
         "и веднаш се мери (G1), за да се ограничи размената на влага.",
         "One test portion of 1.000 g of the cut, unsieved drug is taken into a tared, pre-dried weighing bottle (m_B) and "
         "weighed immediately (G1), to limit moisture exchange."),
        ("Остатокот од примерокот се чува затворен и означен до одобрувањето на записот.",
         "The remainder of the sample is kept closed and labelled until the record is approved."),
    ]:
        pr.bullet(d, mk, en)

    # 7
    chapter(d, "7", "ОПРЕДЕЛУВАЊЕ НА ГУБИТОК ПРИ СУШЕЊЕ (a02.2)", "Loss on Drying Determination (a02.2)")
    table(d, ["Параметар | Parameter", "Вредност | Value"], [
        ["Метод | Method", "Ph. Eur. 2.2.32 (монографија 3028) · метод a02.2 (вакуумска печка) | Ph. Eur. 2.2.32 (monograph 3028) · method a02.2 (vacuum oven)"],
        ["Опрема | Equipment", "вакуумска печка VO29 (QCWI 018, QCLB 017) · аналитичка вага Shimadzu AUW220D, d = 0,01 mg (QCWI 016, QCLB 008) · ексикатор со активен сушач | vacuum oven VO29 (QCWI 018, QCLB 017) · analytical balance Shimadzu AUW220D, d = 0.01 mg (QCWI 016, QCLB 008) · desiccator with active desiccant"],
        ["Услови | Conditions", "40 °C · 20 ± 2 mbar · 24 h · над околу 100 g молекуларно сито R | 40 °C · 20 ± 2 mbar · 24 h · over about 100 g molecular sieve R"],
        ["Тест порција | Test portion", "1,000 g сецкана, несеана дрога во претходно исушен тариран сад (m_B); G1 пред сушење | 1.000 g of the cut, unsieved drug in a previously dried tared bottle (m_B); G1 before drying"],
        ["Мерење по 24 h | Weighing after 24 h", "ладење најмалку 30 min во ексикатор, мерење G2 | cool at least 30 min in a desiccator, weigh G2"],
        ["Константна маса | Constant mass", "садовите се враќаат во печката за дополнителен период (поглавје 11) и се мерат повторно по ладење; две последователни мерења се разликуваат за не повеќе од 0,5 mg; инаку сушењето продолжува | "
         "the bottles return to the oven for an additional period (section 11) and are weighed again after cooling; two consecutive weighings differ by not more than 0.5 mg; otherwise drying continues"],
        ["Пресметка | Calculation", "m₀ = G1 − m_B; m₁ = G2 − m_B со последното G2; ГпС % = (m₀ − m₁) ÷ m₀ × 100; резултат на серија = резултатот од едната порција | m₀ = G1 − m_B; m₁ = G2 − m_B with the last G2; LoD % = (m₀ − m₁) ÷ m₀ × 100; batch result = the result of the one portion"],
        ["Критериум | Criterion", "≤ 12,0 % w/w (QCSP 001) | ≤ 12.0 % w/w (QCSP 001)"],
        ["Надвор од спецификација | Out of specification", "QCSOP 014 (OOS); резултатот не се заменува со подоцнежна вредност | QCSOP 014 (OOS); the result is never papered over by a later value"],
        ["Известување | Reporting", "резултатот и датумите на сушење влегуваат во регистарот на сертификати по правилата на бирото за сертификати | the result and the drying dates enter the certificate register under the certificate desk's rules"],
    ], sz=8, label_first=True)

    # 8
    chapter(d, "8", "РАСПОРЕД", "Schedule")
    table(d, ["Ден | Day", "Активности | Activities"], [
        ["Ден 1 | Day 1", "Пакет 2: прием (QCT 024 D1-RCPT) · инспекција (A03) и мерење пред/после (QCT 021) · етикети · враќање (D1-RET) · примероци во КК (D1-SMP) — Пакет 3: LOD-01 делови A–C, сите порции во печка | "
         "Package 2: receipt (QCT 024 D1-RCPT) · inspection (A03) and before/after weighing (QCT 021) · labels · return (D1-RET) · samples to QC (D1-SMP) — Package 3: LOD-01 sections A–C, all portions into the oven"],
        ["Ден 2 | Day 2", "LOD-01: ладење најмалку 30 min, мерење по 24 h, дополнителен период и второ мерење до константна маса, резултати (делови D–E) · проверка од второ лице и одобрување | "
         "LOD-01: cooling at least 30 min, weighing after 24 h, additional period and second weighing to constant mass, results (sections D–E) · second-person check and approval"],
    ], sz=8, label_first=True)
    pr.note(d, "Датумите се внесуваат ex tempore на записите; деновите не се фиксирани во овој протокол.",
            "Dates are entered ex tempore on the records; the days are not fixed in this protocol.")

    # 9
    chapter(d, "9", "ЗАПИСИ", "Records")
    pr.body(d, "Извршувањето е во два посебни пакети (Раководител на КК, 06.10.2026), на контролираните обрасци на QCSOP 011 и "
               "QASOP_031: Пакет 2 — земање примероци, еден комплет за денот на земање, сите серии на секој образец; "
               "Пакет 3 — анализа на губиток при сушење, еден извршен запис (LOD-01) за сите серии "
               "анализирани заедно. Секој податок се внесува еднаш, на неговиот изворен образец.",
            "Execution is in two separate packages (Head of QC, 06.10.2026), on the controlled QCSOP 011 and QASOP_031 forms: "
            "Package 2 — sampling, one set for the sampling day, every batch on each form; "
            "Package 3 — loss-on-drying analysis, one execution record (LOD-01) for all batches analysed together. Each data point is "
            "entered once, on its source form.")
    table(d, ["Чекор | Step", "Образец | Form", "Запис | Record"], [
        ["Пренос сеф-магацин → просторија за земање | Transfer secure warehouse → sampling room", "QCT 024 v01", CODE + "-D1-RCPT"],
        ["Визуелна инспекција при отворање, по серија | Visual inspection on opening, per batch", "QCSOP 011_A03 v7.0", "QCSOP 011_A03-___/26"],
        ["Пред, мострирано и после, по кеса | Before, sampled and after, per bag", "QCT 021 v01", "MLR № ___"],
        ["Етикета „МОСТРИРАНО“ по кеса | “SAMPLED” label per bag", "QASOP_031_A05_v1", "—"],
        ["Етикета на примерокот | Sample label", "QASOP_031_A07", "—"],
        ["Враќање во сеф-магацин | Return to the secure warehouse", "QCT 024 v01", CODE + "-D1-RET"],
        ["Примероци → КК лабораторија | Samples → QC laboratory", "QCT 024 v01", CODE + "-D1-SMP"],
        ["Губиток при сушење: прием, опрема, тест порција, мерења, резултати | Loss on drying: receipt, equipment, test portion, weighings, results",
         "Пакет 3 | Package 3", CODE + "-LOD-01"],
    ], sz=8, label_first=True)

    # 10
    chapter(d, "10", "РЕФЕРЕНТНИ ДОКУМЕНТИ", "References")
    for mk, en in [
        ("QCSOP 011 v03 — Мострирање на примероци, ракување и документација (SP-12; §5 r-план; §6.2.1 шифра на примерок).",
         "QCSOP 011 v03 — QC Sampling, Handling and Documentation (SP-12; §5 r-plan; §6.2.1 sample code)."),
        ("PP-QC-SP-001/26 — План и извршен протокол за земање примероци (микробиолошка чистота), јули 2026 — истата основа и ознаки.",
         "PP-QC-SP-001/26 — Sampling Plan & Execution Protocol (microbiological purity), July 2026 — the same basis and keys."),
        ("WHO Technical Report Series No. 929 (2005), Annex 4 — Guidelines for sampling of pharmaceutical products and related materials (r-план, r = 1,5·√N; заменет со една кеса по серија, 06.10.2026).",
         "WHO Technical Report Series No. 929 (2005), Annex 4 — Guidelines for sampling of pharmaceutical products and related materials (r-plan, r = 1.5·√N; replaced by one bag per batch, 06.10.2026)."),
        ("European Pharmacopoeia: 2.2.32 Loss on drying; 2.8.20 Herbal drugs: sampling and sample preparation; монографија 3028 Cannabis flos; Општи одредби (константна маса).",
         "European Pharmacopoeia: 2.2.32 Loss on drying; 2.8.20 Herbal drugs: sampling and sample preparation; monograph 3028 Cannabis flos; General Notices (constant mass)."),
        ("a02.2 — губиток при сушење, Ph. Eur. 2.2.32 во вакуумска печка VO29 (40 °C, 20 ± 2 mbar, 24 h, над молекуларно сито R), STPa02 според QCSOP 009.",
         "a02.2 — loss on drying, Ph. Eur. 2.2.32 in vacuum oven VO29 (40 °C, 20 ± 2 mbar, 24 h, over molecular sieve R), STPa02 under QCSOP 009."),
        ("QCSP 001 — спецификација на производот (губиток при сушење ≤ 12,0 % w/w); QCSP-RMI-P0005 — спецификација на кесата (нето 400,0 g ± 3 %).",
         "QCSP 001 — product specification (loss on drying ≤ 12.0 % w/w); QCSP-RMI-P0005 — bag specification (net 400.0 g ± 3 %)."),
        ("EudraLex Vol. 4: Поглавје 6 (контрола на квалитет), Annex 8 (земање примероци), Annex 11 (ALCOA+); ICH Q9(R1).",
         "EudraLex Vol. 4: Chapter 6 (quality control), Annex 8 (sampling), Annex 11 (ALCOA+); ICH Q9(R1)."),
        ("QCSOP 014 (OOS); QASOP_031_A05_v1 и A07 (етикети); QCSOP 011_A03 v7.0 (визуелна инспекција); QCT 024 v01 (пренос); QCT 021 v01 (преглед на количини пред и после мострирање).",
         "QCSOP 014 (OOS); QASOP_031_A05_v1 and A07 (labels); QCSOP 011_A03 v7.0 (visual inspection); QCT 024 v01 (transfer); QCT 021 v01 (quantity review before and after sampling)."),
        ("Извори на податоци: tranche_assignment_2026-09-18.csv; CoQ_Analysis_Master_v57.xlsx (Reference); quantities_table.tsv (10–11.08.2026); coq_artifact_data.json; batch_dates_2026-09-10.csv.",
         "Data sources: tranche_assignment_2026-09-18.csv; CoQ_Analysis_Master_v57.xlsx (Reference); quantities_table.tsv (10–11.08.2026); coq_artifact_data.json; batch_dates_2026-09-10.csv."),
    ]:
        pr.bullet(d, mk, en)

    # 11
    chapter(d, "11", "ОТВОРЕНИ ТОЧКИ ЗА РАКОВОДИТЕЛОТ НА КК", "Open Items for the Head of QC")
    for mk, en in [
        ("Мастер v57, Reference E216 (GG1024_01 = 0,87 kg) бара поправка; KC102501 — 21,67 kg (мастер) наспроти 16,000 kg (залиха).",
         "Master v57, Reference E216 (GG1024_01 = 0.87 kg) needs correction; KC102501 — 21.67 kg (master) vs 16.000 kg (stock)."),
        ("Една тест порција по серија (06.10.2026) наспроти дупликатот од QCSOP 011 v03 §5 (SP-06).",
         "One test portion per batch (06.10.2026) against the duplicate in QCSOP 011 v03 §5 (SP-06)."),
        ("Дополнителниот период на сушење за второто мерење (според a02.2 или по негова одлука).",
         "The additional drying period for the second weighing (per a02.2 or by his decision)."),
        ("Ознаки: PP-QC-SP-002/26-D1-RCPT/-RET/-SMP за преносите на QCT 024 и PP-QC-SP-002/26-LOD-01 за анализата (или QCT 025, следната слободна QC ознака); броевите на A03 и QCT 021 се од нивните регистри; регистрација на RQS пред земање (QCSOP 011 v03 §6.1.1).",
         "Codes: PP-QC-SP-002/26-D1-RCPT/-RET/-SMP for the QCT 024 transfers and PP-QC-SP-002/26-LOD-01 for the analysis (or QCT 025, the next free QC template code); the A03 and QCT 021 numbers come from their registers; RQS registration before sampling (QCSOP 011 v03 §6.1.1)."),
        ("Спарување со халогенскиот анализатор (SAM_a02.1) на истите примероци за верификација на методот во опсегот 5–12 % — ако верификацијата побара HMA мерења на остатокот од примероците, се внесува пред одобрување.",
         "Pairing with the halogen moisture analyser (SAM_a02.1) on the same samples for the method verification in the 5–12 % range — if the verification asks for HMA runs on the sample remainders, it is entered before approval."),
        ("Транша 3 (31 серии) како PP-QC-SP-003/26 по истата постапка; по одобрување овој документ се издава како v1.0 со датум на важност.",
         "Tranche 3 (31 batches) as PP-QC-SP-003/26 on the same procedure; on approval this document is issued as v1.0 with an effective date."),
    ]:
        pr.bullet(d, mk, en)
    pr.gap(d, 8)
    pr.execution_signoff(d, mk_exec="Изготвил (Раководител КК) | Prepared (QC Head)", reviewer="J. Romevska",
                         approver="B. Nikolov, M.Pharm. (Раководител на КК оддел | QC Department Manager)")
    return d


# ----------------------------------------------------------------------------- main
def main():
    os.makedirs(OUT_P, exist_ok=True)
    lots, bags = load()
    docs = [
        ("PP-QC-SP-002_26_Sampling_Plan_LoD_T1_T2.docx", build_plan(lots)),
    ]
    ok = True
    for name, d in docs:
        glyph_audit(d)
        path = os.path.join(OUT_P, name)
        pf.save(d, path)
        ok = verify(path) and ok
    if not ok:
        raise SystemExit("pp_verify FAIL")
    print("written:", OUT)


if __name__ == "__main__":
    main()
