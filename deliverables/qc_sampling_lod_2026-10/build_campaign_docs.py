#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build PP-QC-SP-002/26 — the sampling plan and the two daily execution records — with the
Purely Plant document engine (pp-document-suite, python-docx). Every number printed here is read
from SAMPLING_PLAN_T1_T2_2026-10.tsv and bag_selection.tsv (campaign_data.py); the engine owns the
appearance. Each output is passed through pp_verify.py and the build fails on anything but PASS.

    python3 build_campaign_docs.py            # -> out/*.docx
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

OUT = os.path.join(HERE, "out")
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
        for k in ("day", "seq", "tranche", "N", "n", "k", "interval", "start"):
            l[k] = int(l[k])
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
    ("6", "ЗБИРЕН ПРИМЕРОК, ХОМОГЕНИЗАЦИЈА И ТЕСТ ПОРЦИИ", "Composite, Homogenisation & Test Portions"),
    ("7", "ОПРЕДЕЛУВАЊЕ НА ГУБИТОК ПРИ СУШЕЊЕ (SAM_a02.2)", "Loss on Drying Determination (SAM_a02.2)"),
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
           ("Намена | Purpose", "Губиток при сушење, Ph. Eur. 2.2.32 (3028), интерен метод SAM_a02.2 · критериум ≤ 12,0 % w/w | "
                                "Loss on drying, Ph. Eur. 2.2.32 (3028), in-house method SAM_a02.2 · criterion ≤ 12.0 % w/w"),
           ("Основа | Basis", "QCSOP 011 v03 (SP-12) · WHO TRS 929 Annex 4, r-план n = 1,5·√N | r-plan n = 1.5·√N"),
           ("Земање | Sampling", "2 дена · %d кеси · 1 цвет по кеса | 2 days · %d bags · 1 flower per bag" % (tot_n, tot_n)),
           ("Резултати | Results", "Ден 2 и Ден 3 (24 h сушење + второ мерење до константна маса) | "
                                   "Day 2 and Day 3 (24 h drying + second weighing to constant mass)")],
          "ПЛАН И ИЗВРШЕН ПРОТОКОЛ ЗА ЗЕМАЊЕ ПРИМЕРОЦИ", "Sampling Plan & Execution Protocol",
          "Производни серии во сеф-магацин · 46 серии · %s kg" % num(tot_kg),
          "Production batches in secure storage · 46 batches · %s kg" % ("%.2f" % tot_kg))
    contents_page(d, PLAN_CHAPTERS)

    # 1
    pr.chapter(d, "1", "ЦЕЛ И ОПФАТ", "Purpose & Scope")
    pr.body(d, "Овој документ го пропишува земањето репрезентативен примерок од секоја од 46-те производни серии "
               "од Транша 1 (20 серии) и Транша 2 (26 серии), складирани во сеф-магацинот како готов производ во троен "
               "фолиски кеси од 400 g (10 кеси по нумериран картон), и интерното определување на губиток при сушење "
               "(Ph. Eur. 2.2.32; монографија 3028 Cannabis flos; интерен метод SAM_a02.2) пред испорака, за да се потврди "
               "дека нивото на влага на производот одговара на спецификацијата QCSP 001 (≤ 12,0 % w/w).",
            "This document prescribes the representative sampling of each of the 46 production batches of Tranche 1 "
            "(20 batches) and Tranche 2 (26 batches), stored in the secure warehouse as finished product in 400 g "
            "triple-foil bags (10 bags per numbered carton), and the in-house determination of loss on drying "
            "(Ph. Eur. 2.2.32; monograph 3028 Cannabis flos; in-house method SAM_a02.2) before shipment, to confirm "
            "that the product's moisture level meets specification QCSP 001 (≤ 12.0 % w/w).")
    pr.body(d, "Точка на земање: SP-12 — готов производ во магацин (QCSOP 011 v03). Крајната точка е физичко-хемиска, "
               "па не се бара асептична техника. Земањето се изведува во два дена со по околу половина од кесите за "
               "отворање; резултатите од првиот ден се читаат на вториот ден, од вториот на третиот. Транша 3 (31 "
               "серии) следи со PP-QC-SP-003/26 по истата постапка.",
            "Sampling point: SP-12 — finished product in the warehouse (QCSOP 011 v03). The endpoint is physico-chemical, "
            "so no aseptic technique is required. Sampling runs over two days with about half of the bags to open on "
            "each; Day-1 results are read on Day 2, Day-2 results on Day 3. Tranche 3 (31 batches) follows as "
            "PP-QC-SP-003/26 on the same procedure.")

    # 2
    pr.chapter(d, "2", "ПРИНЦИП И ОСНОВА", "Principle & Basis")
    pr.bullet(d, "Единица за земање е фолиската кеса од 400 g (примарен затворен сад); картонот со 10 кеси е секундарно "
                 "пакување и не е единица за земање.",
              "The sampling unit is the 400 g foil bag (primary sealed container); the 10-bag carton is secondary "
              "packaging and not the sampling unit.")
    pr.bullet(d, "Бројот на кеси за отворање се определува според WHO TRS 929, Annex 4, r-план: n = 1,5·√N заокружено "
                 "нагоре (QCSOP 011 v03, §5), избран наместо подот на Ph. Eur. 2.8.20 (√N + 1) врз основа на ризик "
                 "(ICH Q9): хетероген материјал од земјоделско потекло, а резултатот ја носи одлуката за испорака.",
              "The number of bags to open follows WHO TRS 929, Annex 4, r-plan: n = 1.5·√N rounded up (QCSOP 011 v03, "
              "§5), chosen over the Ph. Eur. 2.8.20 floor (√N + 1) on quality-risk grounds (ICH Q9): heterogeneous "
              "material of agricultural origin, and the result carries the shipment decision.")
    pr.bullet(d, "Од секоја избрана кеса се зема ЕДЕН цвет — најголемиот (Раководител на КК, 05.10.2026), така што "
                 "збирниот примерок носи доволно материјал за определувањата, а содржината на кесата останува "
                 "недопрена. Сите n цветови од една серија образуваат ЕДЕН збирен примерок; цветовите не се испитуваат "
                 "поединечно.",
              "From each selected bag ONE flower is taken — the largest (Head of QC, 05.10.2026), so the composite holds "
              "enough material for the determinations while the bag's content is otherwise undisturbed. The n flowers "
              "of a batch form ONE composite sample; flowers are not tested individually.")
    pr.bullet(d, "Бројот на определувања k по збирен примерок зависи од големината на серијата: N ≤ 100 кеси → 1; "
                 "101–400 → 2; над 400 → 3 (Раководител на КК, 05.10.2026). Резултатот на серијата е средната вредност "
                 "од k; критериум ≤ 12,0 % w/w.",
              "The number of determinations k per composite follows batch size: N ≤ 100 bags → 1; 101–400 → 2; "
              "above 400 → 3 (Head of QC, 05.10.2026). The batch result is the mean of k; criterion ≤ 12.0 % w/w.")
    pr.note(d, "QCSOP 011 v03 (§5) дефинира дупликат за губиток при сушење при SP-06 (пред пакување). За SP-12 важи "
               "правилото на Раководителот на КК од 05.10.2026 (поглавје 11).",
            "QCSOP 011 v03 (§5) defines a duplicate for loss on drying at SP-06 (pre-packaging). For SP-12 the Head of "
            "QC's rule of 05.10.2026 applies (section 11).")

    # 3
    pr.chapter(d, "3", "ФОРМУЛИ", "Formulas")
    table(d, ["Величина | Quantity", "Формула | Formula", "Забелешка | Note"], [
        ["Број на кеси во серијата | Bags in the batch", "N = kg ÷ 0,400, заокружено нагоре | N = kg ÷ 0.400, rounded up",
         "kg од мастер v57 (Reference, „DELIVERY T1–T3“); документираниот број кеси во магацинот има предност | "
         "kg from master v57 (Reference, “DELIVERY T1–T3”); the warehouse's documented bag count governs"],
        ["Кеси за отворање | Bags to open", "n = 1,5 × √N, заокружено нагоре | n = 1.5 × √N, rounded up",
         "WHO TRS 929 Annex 4, r-план | r-plan"],
        ["Интервал на избор | Selection interval", "i = N ÷ n заокружено нагоре; ако n кеси не се сместуваат во N, заокружено надолу | "
         "i = N ÷ n rounded up; rounded down where n bags do not fit within N",
         "систематски избор | systematic selection"],
        ["Случаен почеток | Random start", "r од 1 до N − i·(n − 1) | r from 1 to N − i·(n − 1)",
         "генериран со seed %d и отпечатен во 4b | generated with seed %d and printed in 4b" % (seed, seed)],
        ["Избрани кеси | Selected bags", "r, r + i, r + 2i, … (n кеси) · ознака K{картон}B{кеса} | "
         "r, r + i, r + 2i, … (n bags) · key K{carton}B{bag}", "K1B1 = картон 1, кеса 1 | carton 1, bag 1"],
        ["Определувања | Determinations", "k = 1 (N ≤ 100) · 2 (101–400) · 3 (> 400)", "по збирен примерок | per composite"],
        ["Тест порција | Test portion", "≈ 1,000 g во таран сад за мерење | ≈ 1.000 g in a tared weighing bottle", "SAM_a02.2"],
        ["Губиток при сушење | Loss on drying", "ГпС % = (G1 − G2) ÷ (G1 − m0) × 100 | LoD % = (G1 − G2) ÷ (G1 − m0) × 100",
         "m0 = сад | bottle; G1 = пред | before; G2 = по сушење до константна маса | after drying to constant mass"],
        ["Резултат на серија | Batch result", "средна вредност од k определувања | mean of k determinations",
         "критериум ≤ 12,0 % w/w | criterion ≤ 12.0 % w/w"],
    ], sz=8)
    pr.note(d, "Масата на збирниот примерок е приближно n × (1–3 g) по цвет; потребни се k × 1,000 g тест порции.",
            "The composite mass is approximately n × (1–3 g) per flower; k × 1.000 g test portions are needed.")

    # 4
    pr.chapter(d, "4", "ПЛАН ПО СЕРИЈА", "Per-Batch Plan")
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
        rows.append([i, l["batch"], l["N"], l["n"], l["k"], l["interval"], l["start"], len(l["carton_list"]),
                     "%s–%s" % (num(l["composite_g_low"], 0), num(l["composite_g_high"], 0)),
                     num(l["test_portions_g"], 3), lod_text(l), "Ден %d | Day %d" % (l["day"], l["day"])])
    rows.append(["", "ВКУПНО | TOTAL", tot_N, tot_n, tot_k, "", "", sum(len(l["carton_list"]) for l in lots), "", "", "", ""])
    table(d, ["№", "Серија | Batch", "N", "n", "k", "i", "r", "Картони | Cartons", "Збирен g | Composite g",
              "Порции g | Portions g", "Последен ГпС на запис | Last LoD on record", "Ден | Day"], rows, sz=7)
    pr.note(d, "N е изведено од kg (кеси од 400 g); ако документираниот број кеси во магацинот се разликува, тој важи и n се "
               "пресметува повторно на извршниот запис. „Последен ГпС на запис“ е информативен: вредноста, лабораторијата и "
               "датумот од регистарот на сертификати (coq_artifact_data.json).",
            "N is derived from kg (400 g bags); if the warehouse's documented bag count differs, it governs and n is recomputed "
            "on the execution record. “Last LoD on record” is informative: value, laboratory and date from the certificate "
            "register (coq_artifact_data.json).")

    pr.subsec(d, "4.1", "Групирање по ден на земање", "Grouping by sampling day")
    rows = []
    for dd in (1, 2):
        ls = by_day[dd]
        rows.append(["Ден %d | Day %d" % (dd, dd), BLANK + " – " + BLANK, ", ".join(l["batch"] for l in ls), len(ls),
                     sum(l["n"] for l in ls), sum(l["k"] for l in ls), sum(len(l["carton_list"]) for l in ls)])
    rows.append(["ВКУПНО | TOTAL", "Почеток | Start: %s · Крај | End: %s" % (BLANK, BLANK), "", 46, tot_n, tot_k,
                 sum(len(l["carton_list"]) for l in lots)])
    table(d, ["Ден | Day", "Датум (од–до) | Date (from–to)", "Серии | Batches", "Σ серии | Σ batches",
              "Σn кеси | Σn bags", "Σk порции | Σk portions", "Картони | Cartons"], rows, sz=7)
    pr.body(d, "Балансот е по Σn (кеси за отворање — кесата е единицата на работа), со цели серии; поголемите серии се "
               "распоредуваат први. Во рамки на денот редоследот на повлекување следи по магацин (E66 → E46/47 → F131 → "
               "Sec.Pack), па по транша и серија. Групирањето е индикативно — серија што не е подготвена се одложува за "
               "наредниот ден и се забележува на извршниот запис.",
            "Balance is by Σn (bags to open — the bag is the unit of work), with whole batches; larger batches are placed "
            "first. Within a day the retrieval order follows the warehouse (E66 → E46/47 → F131 → Sec.Pack), then tranche "
            "and batch. The grouping is indicative — a batch that is not ready is deferred to the next day and noted on "
            "the execution record.")
    pr.note(d, "Предлог за работна сила (не е правило): околу 490 кеси на ден со три лица и околу 2,5 минути по кеса "
               "(отворање, инспекција, мерење пред/по, еден цвет, етикета) се околу 7 работни часа. Оптоварување на "
               "печката: %d сада за мерење првата ноќ, %d втората." % (sum(l["k"] for l in by_day[1]), sum(l["k"] for l in by_day[2])),
            "Staffing proposal (not a rule): about 490 bags a day with three persons and about 2.5 minutes per bag "
            "(opening, inspection, weighing before/after, one flower, label) is about 7 working hours. Oven load: "
            "%d weighing bottles the first night, %d the second." % (sum(l["k"] for l in by_day[1]), sum(l["k"] for l in by_day[2])))

    # 5
    pr.chapter(d, "5", "УСЛОВИ, ИЗБОР НА КЕСИ И СЛЕДЛИВОСТ", "Conditions, Bag Selection & Traceability")
    for mk, en in [
        ("Чист и сув прибор од нерѓосувачки челик, ракавици; нема барање за асептична техника (физичко-хемиска крајна "
         "точка). Времето надвор од складиште се минимизира; кесата се затвора веднаш по земањето.",
         "Clean, dry stainless-steel tools and gloves; no aseptic requirement (physico-chemical endpoint). Time out of "
         "storage is minimised; the bag is closed immediately after sampling."),
        ("Систематски избор со случаен почеток r (поглавје 3), генериран со seed 20261005 и отпечатен во 4b; избраните "
         "кеси се однапред внесени во извршниот запис со ознаката K{картон}B{кеса}. Истата ознака се користи на секој запис "
         "и етикета за таа кеса (единствен клуч по кеса, како во PP-QC-SP-001/26).",
         "Systematic selection with a random start r (section 3), generated with seed 20261005 and printed in 4b; the "
         "selected bags are pre-entered on the execution record with the key K{carton}B{bag}. The same key is used on "
         "every record and label for that bag (single per-bag key, as in PP-QC-SP-001/26)."),
        ("По кеса: визуелна инспекција при отворање според критериумите на QCSOP 011_A03 (боја/мирис, мувла, штетници, "
         "страни материи/семки, оштетено пакување) — „не одговара“ → карантин и отстапување; мерење бруто пред отворање; "
         "земање на ЕДЕН цвет, најголемиот видлив; мерење бруто по затворање; двете маси се внесуваат во записот (дел D).",
         "Per bag: visual inspection on opening against the QCSOP 011_A03 criteria (colour/odour, mould, pests, foreign "
         "matter/seeds, pack damage) — “does not conform” → quarantine and deviation; gross weighed before opening; ONE "
         "flower taken, the largest visible; gross weighed after closing; both masses entered on the record (section D)."),
        ("Извор на вистина за масите: нето = етикетата на примарното пакување (400,0 g, се препишува); бруто = го мери КК; "
         "земено = бруто пред − бруто по. Отворените кеси се ре-етикетираат „ЗЕМЕН ПРИМЕРОК | SAMPLED“ со ново нето/бруто "
         "(етикети по QASOP_031; по серија се потребни n етикети ЗЕМЕН, n етикети нето/бруто и 1 етикета за збирниот примерок).",
         "Mass source of truth: net = the primary-pack label (400.0 g, transcribed); gross = weighed by QC; sampled = gross "
         "before − gross after. Opened bags are re-labelled “SAMPLED” with the new net/gross (labels per QASOP_031; per batch "
         "n SAMPLED labels, n net/gross labels and 1 composite-sample label are needed)."),
        ("Збирниот примерок на секоја серија се собира во еден чист затворен сад означен со шифрата на примерокот "
         "([NNN/26_SFR]-PC-[бр.], QCSOP 011 v03 §6.2.1) и се пренесува во КК лабораторијата истиот ден; преносот се "
         "потпишува во делот B/E на извршниот запис.",
         "Each batch's composite is collected in one clean closed container labelled with the sample code "
         "([NNN/26_SFR]-PC-[no.], QCSOP 011 v03 §6.2.1) and taken to the QC laboratory the same day; the transfer is signed "
         "in sections B/E of the execution record."),
        ("Документација: истовремено, со трајно сино мастило, без празни полиња („N/A“), поправки со една линија, "
         "иницијали и датум (ALCOA+; EU GMP Annex 11; СОП за работа со аналитичка документација).",
         "Documentation: contemporaneous, permanent blue ink, no blank fields (“N/A”), single-line corrections with "
         "initials and date (ALCOA+; EU GMP Annex 11; the SOP for working with analytical documentation)."),
    ]:
        pr.bullet(d, mk, en)

    # 6
    pr.chapter(d, "6", "ЗБИРЕН ПРИМЕРОК, ХОМОГЕНИЗАЦИЈА И ТЕСТ ПОРЦИИ", "Composite, Homogenisation & Test Portions")
    for mk, en in [
        ("Истиот ден, во КК лабораторијата: збирниот примерок се мери (маса на збирен примерок, дел C).",
         "The same day, in the QC laboratory: the composite is weighed (composite mass, section C)."),
        ("Сите цветови се сечат грубо со чисти ножици од нерѓосувачки челик на чиста подлога и се мешаат со "
         "четвртирање (материјалот се израмнува, се дели на четири четвртини, спротивните четвртини се спојуваат; "
         "двапати).",
         "All flowers are coarsely cut with clean stainless-steel scissors on a clean tray and mixed by quartering (the "
         "material is flattened, divided into four quarters, opposite quarters recombined; twice)."),
        ("Од различни четвртини се земаат k тест порции од околу 1,000 g во тарирани, претходно исушени садови за "
         "мерење (m0) и веднаш се мерат (G1), за да се ограничи размената на влага.",
         "From different quarters, k test portions of about 1.000 g are taken into tared, pre-dried weighing bottles "
         "(m0) and weighed immediately (G1), to limit moisture exchange."),
        ("Остатокот од збирниот примерок се чува затворен и означен до одобрувањето на извршниот запис.",
         "The remainder of the composite is kept closed and labelled until the execution record is approved."),
    ]:
        pr.bullet(d, mk, en)

    # 7
    pr.chapter(d, "7", "ОПРЕДЕЛУВАЊЕ НА ГУБИТОК ПРИ СУШЕЊЕ (SAM_a02.2)", "Loss on Drying Determination (SAM_a02.2)")
    table(d, ["Параметар | Parameter", "Вредност | Value"], [
        ["Метод | Method", "Ph. Eur. 2.2.32 (монографија 3028) · интерен метод SAM_a02.2 | Ph. Eur. 2.2.32 (monograph 3028) · in-house method SAM_a02.2"],
        ["Опрема | Equipment", "вакуумска печка · аналитичка вага (читливост според квалификацијата) · ексикатор | vacuum oven · analytical balance (readability as qualified) · desiccator"],
        ["Услови | Conditions", "40 °C · 15–25 mbar · 24 h"],
        ["Тест порција | Test portion", "≈ 1,000 g во таран сад (m0); G1 пред сушење | ≈ 1.000 g in a tared bottle (m0); G1 before drying"],
        ["Мерење по 24 h | Weighing after 24 h", "ладење во ексикатор, мерење G2 | cool in a desiccator, weigh G2"],
        ["Константна маса | Constant mass", "садовите се враќаат во печката за дополнителен период (SAM_a02.2 / Раководител на КК, поглавје 11) и се мерат повторно; две последователни мерења се разликуваат за не повеќе од 0,5 mg (Ph. Eur. Општи одредби — формулацијата да се потврди во контролираното издание); инаку сушењето продолжува | "
         "the bottles return to the oven for an additional period (SAM_a02.2 / Head of QC, section 11) and are weighed again; two consecutive weighings differ by not more than 0.5 mg (Ph. Eur. General Notices — wording to be confirmed in the controlled edition); otherwise drying continues"],
        ["Пресметка | Calculation", "ГпС % = (G1 − G2) ÷ (G1 − m0) × 100 по порција; резултат на серија = средна вредност од k | LoD % = (G1 − G2) ÷ (G1 − m0) × 100 per portion; batch result = mean of k"],
        ["Критериум | Criterion", "≤ 12,0 % w/w (QCSP 001) | ≤ 12.0 % w/w (QCSP 001)"],
        ["Надвор од спецификација | Out of specification", "QCSOP 014 (OOS); резултатот не се заменува со подоцнежна вредност | QCSOP 014 (OOS); the result is never papered over by a later value"],
        ["Известување | Reporting", "резултатот и датумите на сушење влегуваат во регистарот на сертификати по правилата на бирото за сертификати | the result and the drying dates enter the certificate register under the certificate desk's rules"],
    ], sz=8, label_first=True)

    # 8
    pr.chapter(d, "8", "РАСПОРЕД", "Schedule")
    table(d, ["Ден | Day", "Активности | Activities"], [
        ["Ден 1 | Day 1", "Повлекување на картоните за групата Ден 1 (дел B) · отворање, инспекција, мерење и земање по кеса (дел D) · враќање (дел E) · збирни примероци, хомогенизација, k тест порции · влез во печка (дел F, време на влез) | "
         "Retrieval of the Day-1 cartons (section B) · opening, inspection, weighing and sampling per bag (section D) · return (section E) · composites, homogenisation, k test portions · into the oven (section F, time in)"],
        ["Ден 2 | Day 2", "Мерење на порциите од Ден 1 по 24 h, дополнителен период и второ мерење до константна маса, пресметка и резултати (дел F на ER-01) · повлекување, земање и влез во печка за групата Ден 2 (ER-02) | "
         "Weighing of the Day-1 portions after 24 h, additional period and second weighing to constant mass, calculation and results (section F of ER-01) · retrieval, sampling and oven-in for the Day-2 group (ER-02)"],
        ["Ден 3 | Day 3", "Мерење на порциите од Ден 2 по 24 h, второ мерење до константна маса, резултати (дел F на ER-02) · комплетирање, проверка од второ лице и одобрување на двата записа | "
         "Weighing of the Day-2 portions after 24 h, second weighing to constant mass, results (section F of ER-02) · completion, second-person check and approval of both records"],
    ], sz=8, label_first=True)
    pr.note(d, "Датумите се внесуваат ex tempore на извршните записи; деновите не се фиксирани во овој протокол.",
            "Dates are entered ex tempore on the execution records; the days are not fixed in this protocol.")

    # 9
    pr.chapter(d, "9", "ЗАПИСИ", "Records")
    pr.body(d, "Извршувањето се документира на ЕДЕН извршен запис по ден на земање — PP-QC-SP-002/26-ER-01 (Ден 1) и "
               "-ER-02 (Ден 2) — кој ги носи сите серии од тој ден (Раководител на КК, 05.10.2026). Полињата на обрасците "
               "за пренос (QCT 024), визуелна инспекција (QCSOP 011_A03) и порамнување на количини (QCT 021) се вградени во "
               "неговите делови, така што постои еден извор на вистина по податок.",
            "Execution is documented on ONE execution record per sampling day — PP-QC-SP-002/26-ER-01 (Day 1) and -ER-02 "
            "(Day 2) — carrying every batch of that day (Head of QC, 05.10.2026). The fields of the transfer record "
            "(QCT 024), the visual inspection form (QCSOP 011_A03) and the quantity reconciliation (QCT 021) are embedded "
            "in its sections, so there is one source of truth per data point.")
    table(d, ["Чекор | Step", "Дел од записот | Record section"], [
        ["Серии на денот (N, n, k, картони) | Batches of the day (N, n, k, cartons)", "A"],
        ["Повлекување и предавање магацин → КК | Retrieval and handover warehouse → QC", "B"],
        ["Извршување по серија: картони, инспекција, збирен примерок, шифра | Per-batch execution: cartons, inspection, composite, sample code", "C"],
        ["Попис по кеса: ID, нето, бруто пред/по, земено, инспекција | Per-bag inventory: ID, net, gross before/after, sampled, inspection", "D"],
        ["Враќање КК → магацин, ре-етикетирање ЗЕМЕН | Return QC → warehouse, SAMPLED re-labelling", "E"],
        ["Губиток при сушење: опрема, услови, мерења, резултати | Loss on drying: equipment, conditions, weighings, results", "F"],
        ["Отстапувања / OOS | Deviations / OOS", "G"],
        ["Потписи по чекор и заклучни потписи | Per-step and closing sign-offs", "H"],
    ], sz=8, label_first=True)

    # 10
    pr.chapter(d, "10", "РЕФЕРЕНТНИ ДОКУМЕНТИ", "References")
    for mk, en in [
        ("QCSOP 011 v03 — Мострирање на примероци, ракување и документација (SP-12; §5 r-план; §6.2.1 шифра на примерок).",
         "QCSOP 011 v03 — QC Sampling, Handling and Documentation (SP-12; §5 r-plan; §6.2.1 sample code)."),
        ("PP-QC-SP-001/26 — План и извршен протокол за земање примероци (микробиолошка чистота), јули 2026 — истата основа и ознаки.",
         "PP-QC-SP-001/26 — Sampling Plan & Execution Protocol (microbiological purity), July 2026 — the same basis and keys."),
        ("WHO Technical Report Series No. 929 (2005), Annex 4 — Guidelines for sampling of pharmaceutical products and related materials (r-план, r = 1,5·√N).",
         "WHO Technical Report Series No. 929 (2005), Annex 4 — Guidelines for sampling of pharmaceutical products and related materials (r-plan, r = 1.5·√N)."),
        ("European Pharmacopoeia: 2.2.32 Loss on drying; 2.8.20 Herbal drugs: sampling and sample preparation; монографија 3028 Cannabis flos; Општи одредби (константна маса).",
         "European Pharmacopoeia: 2.2.32 Loss on drying; 2.8.20 Herbal drugs: sampling and sample preparation; monograph 3028 Cannabis flos; General Notices (constant mass)."),
        ("SAM_a02.2 — интерен метод за губиток при сушење (вакуумска печка 40 °C, 15–25 mbar, 24 h); PP AMVR a02.1-001/2026 (студија за споредба HMA наспроти Ph. Eur. 2.2.32).",
         "SAM_a02.2 — in-house loss-on-drying method (vacuum oven 40 °C, 15–25 mbar, 24 h); PP AMVR a02.1-001/2026 (HMA vs Ph. Eur. 2.2.32 comparison study)."),
        ("QCSP 001 — спецификација на производот (губиток при сушење ≤ 12,0 % w/w); QCSP-RMI-P0005 — спецификација на кесата (нето 400,0 g ± 3 %).",
         "QCSP 001 — product specification (loss on drying ≤ 12.0 % w/w); QCSP-RMI-P0005 — bag specification (net 400.0 g ± 3 %)."),
        ("EudraLex Vol. 4: Поглавје 6 (контрола на квалитет), Annex 8 (земање примероци), Annex 11 (ALCOA+); ICH Q9(R1).",
         "EudraLex Vol. 4: Chapter 6 (quality control), Annex 8 (sampling), Annex 11 (ALCOA+); ICH Q9(R1)."),
        ("QCSOP 014 (OOS); QASOP_031 (етикети); QCSOP 011_A03 (визуелна инспекција); QCT 024 / QCT 021 (пренос и порамнување — полиња вградени во извршниот запис).",
         "QCSOP 014 (OOS); QASOP_031 (labels); QCSOP 011_A03 (visual inspection); QCT 024 / QCT 021 (transfer and reconciliation — fields embedded in the execution record)."),
        ("Извори на податоци: tranche_assignment_2026-09-18.csv; CoQ_Analysis_Master_v57.xlsx (Reference); quantities_table.tsv (10–11.08.2026); coq_artifact_data.json; batch_dates_2026-09-10.csv.",
         "Data sources: tranche_assignment_2026-09-18.csv; CoQ_Analysis_Master_v57.xlsx (Reference); quantities_table.tsv (10–11.08.2026); coq_artifact_data.json; batch_dates_2026-09-10.csv."),
    ]:
        pr.bullet(d, mk, en)

    # 11
    pr.chapter(d, "11", "ОТВОРЕНИ ТОЧКИ ЗА РАКОВОДИТЕЛОТ НА КК", "Open Items for the Head of QC")
    for mk, en in [
        ("Мастер v57, Reference E216 (GG1024_01 = 0,87 kg) бара поправка; KC102501 — 21,67 kg (мастер) наспроти 16,000 kg (залиха); документираниот број кеси по серија при повлекувањето.",
         "Master v57, Reference E216 (GG1024_01 = 0.87 kg) needs correction; KC102501 — 21.67 kg (master) vs 16.000 kg (stock); the documented bag count per batch at retrieval."),
        ("Правилото k = 1/2/3 по број на кеси наспроти дупликатот од QCSOP 011 v03 §5; капацитет на печката за %d и %d сада на ноќ." % (sum(l["k"] for l in by_day[1]), sum(l["k"] for l in by_day[2])),
         "The k = 1/2/3 rule by bag count against the duplicate in QCSOP 011 v03 §5; oven capacity for %d and %d bottles per night." % (sum(l["k"] for l in by_day[1]), sum(l["k"] for l in by_day[2]))),
        ("Дополнителниот период на сушење за второто мерење (според SAM_a02.2 или по негова одлука).",
         "The additional drying period for the second weighing (per SAM_a02.2 or by his decision)."),
        ("Ознаки: PP-QC-SP-002/26-ER-01/-02 за дневните извршни записи (или QCT 025, следната слободна QC ознака); регистрација на RQS пред земање (QCSOP 011 v03 §6.1.1).",
         "Codes: PP-QC-SP-002/26-ER-01/-02 for the daily execution records (or QCT 025, the next free QC template code); RQS registration before sampling (QCSOP 011 v03 §6.1.1)."),
        ("Спарување со халогенскиот анализатор (SAM_a02.1) на истите збирни примероци за верификација на методот во опсегот 5–12 % — ако агентот за верификација побара дупликатни HMA мерења или k = 2 на подгрупа, се внесува пред одобрување.",
         "Pairing with the halogen moisture analyser (SAM_a02.1) on the same composites for the method verification in the 5–12 % range — if the verification agent asks for duplicate HMA runs or k = 2 on a subset, it is entered before approval."),
        ("Транша 3 (31 серии) како PP-QC-SP-003/26 по истата постапка; по одобрување овој документ се издава како v1.0 со датум на важност.",
         "Tranche 3 (31 batches) as PP-QC-SP-003/26 on the same procedure; on approval this document is issued as v1.0 with an effective date."),
    ]:
        pr.bullet(d, mk, en)
    pr.gap(d, 8)
    pr.execution_signoff(d, mk_exec="Изготвил (Раководител КК) | Prepared (QC Head)", reviewer="J. Romevska",
                         approver="B. Nikolov, M.Pharm. (Раководител на КК оддел | QC Department Manager)")
    return d


# ----------------------------------------------------------------------------- the daily records
def build_record(day, lots, bags):
    ls = [l for l in lots if l["day"] == day]
    bs = [b for b in bags if int(b["day"]) == day]
    sum_n = sum(l["n"] for l in ls)
    sum_k = sum(l["k"] for l in ls)
    code = "%s-ER-%02d" % (CODE, day)
    whs = []
    for l in ls:
        if l["warehouse"] not in whs:
            whs.append(l["warehouse"])

    d = new_doc(code, "ИЗВРШЕН ЗАПИС — ЗЕМАЊЕ ПРИМЕРОЦИ И ГУБИТОК ПРИ СУШЕЊЕ — ДЕН %d" % day,
                "EXECUTION RECORD — SAMPLING AND LOSS ON DRYING — DAY %d" % day)
    cover(d, "Извршен запис — земање примероци и губиток при сушење, Ден %d" % day,
          "Execution record — sampling and loss on drying, Day %d" % day,
          [("Запис бр. | Record No.", code),
           ("План | Plan", CODE + " · Транша 1 и 2 | Tranches 1 and 2"),
           ("Серии на денот | Batches of the day", "%d" % len(ls)),
           ("Кеси за отворање Σn | Bags to open Σn", "%d" % sum_n),
           ("Тест порции Σk | Test portions Σk", "%d" % sum_k),
           ("Магацини | Warehouses", " · ".join(whs)),
           ("Датум на земање (од–до) | Sampling date (from–to)", "%s – %s" % (BLANK, BLANK)),
           ("Влез во печка / мерење 24 h / второ мерење | Oven in / 24-h weighing / second weighing", "%s / %s / %s" % (BLANK, BLANK, BLANK)),
           ("Аналитичар | Analyst", ANALYST),
           ("RQS бр. | RQS No.", BLANK)],
          "ИЗВРШЕН ЗАПИС | EXECUTION RECORD", "Sampling & Loss on Drying — Day %d" % day,
          "Еден запис за сите серии на денот", "One record for all batches of the day")

    # A
    pr.chapter(d, "A", "СЕРИИ НА ДЕНОТ", "Batches of the Day")
    rows = []
    for l in ls:
        rows.append([l["seq"], "T%d" % l["tranche"], l["batch"], l["p_lot"], "%s · %s" % (l["strain"], l["grade"] or "—"),
                     l["warehouse"], num(l["kg_used"]), l["N"], l["n"], l["k"], len(l["carton_list"])])
    rows.append(["", "", "ВКУПНО | TOTAL", "", "%d серии | batches" % len(ls), "", num(sum(l["kg_used"] for l in ls)),
                 sum(l["N"] for l in ls), sum_n, sum_k, sum(len(l["carton_list"]) for l in ls)])
    table(d, ["№", "Т | T", "Серија | Batch", "P лот | P lot", "Сорта · класа | Strain · grade", "Магацин | Warehouse",
              "kg", "N", "n", "k", "Картони | Cartons"], rows, sz=7)
    pr.note(d, "N од kg на планот; ако документираниот број кеси во магацинот се разликува, се внесува тука и n = 1,5·√N "
               "(заокружено нагоре) се пресметува повторно пред изборот на кесите. Серија што не е подготвена се одложува "
               "(забелешка во дел G).",
            "N from the plan's kg; if the warehouse's documented bag count differs, it is entered here and n = 1.5·√N "
            "(rounded up) is recomputed before the bags are selected. A batch that is not ready is deferred (note in section G).")

    # B
    pr.chapter(d, "B", "ПОВЛЕКУВАЊЕ И ПРЕДАВАЊЕ: СЕФ-МАГАЦИН → КК", "Retrieval and Handover: Secure Warehouse → QC")
    pr.body(d, "Картоните наведени по серија во дел C се повлекуваат од сеф-магацинот и се предаваат на КК за земање "
               "примероци на еден датум (референца: %s, овој запис). Нето по кеса = етикетата на примарното пакување "
               "(400,0 g); бруто го мери КК при отворање (дел D)." % CODE,
            "The cartons listed per batch in section C are retrieved from the secure warehouse and handed over to QC for "
            "sampling on a single date (reference: %s, this record). Net per bag = the primary-pack label (400.0 g); gross "
            "is weighed by QC on opening (section D)." % CODE)
    kv_table(d, [("Од | From", "Сеф-магацин · Магацин · Складирање | Secure warehouse · Store · Storage"),
                 ("До | To", "Контрола на квалитет · Просторија за земање примероци · Земање | Quality Control · Sampling room · Sampling"),
                 ("Датум и час на предавање | Handover date and time", BLANK),
                 ("Вкупно картони / кеси за отворање | Total cartons / bags to open", "%d / %d" % (sum(len(l["carton_list"]) for l in ls), sum_n)),
                 ("Забелешка | Note", "")])
    sign_table(d, ["Издал — сеф-магацин | Issued — warehouse", "Примил — КК | Received — QC"])

    # C
    pr.chapter(d, "C", "ИЗВРШУВАЊЕ ПО СЕРИЈА", "Per-Batch Execution")
    rows = []
    for i, l in enumerate(ls, start=1):
        rows.append([l["seq"], l["batch"], l["p_lot"], ranges(l["carton_list"]), l["n"],
                     "[ ] сите одговараат | all conform   [ ] отстапување → G | deviation → G",
                     "", "____/26_SFR-PC-%d%02d" % (day, i), ""])
    table(d, ["№", "Серија | Batch", "P лот | P lot", "Картони (бр.) | Cartons (nos.)", "n",
              "Инспекција при отворање | Inspection on opening", "Збирен примерок g | Composite g",
              "Шифра на примерок | Sample code", "Иниц./час | Init./time"], rows, sz=7)
    pr.note(d, "Избраните кеси по серија се во дел D (ознака K{картон}B{кеса}). Шифрата на примерокот го носи бројот на "
               "регистрираниот SFR (QCSOP 011 v03 §6.2.1); PC = физичко-хемиски примерок.",
            "The selected bags per batch are in section D (key K{carton}B{bag}). The sample code carries the registered "
            "SFR number (QCSOP 011 v03 §6.2.1); PC = physico-chemical sample.")
    pr.step_signoff(d, "Потпис за делови A–C | Sign-off for sections A–C", None)

    # D
    pr.chapter(d, "D", "ПОПИС ПО КЕСА — ИНСПЕКЦИЈА, МЕРЕЊЕ, ЗЕМАЊЕ", "Per-Bag Inventory — Inspection, Weighing, Sampling")
    pr.note(d, "Еден ред по избрана кеса, однапред внесен. Бруто пред отворање и бруто по затворање ги мери КК; "
               "земено = разлика. Инспекција: [ ] = одговара по сите критериуми на QCSOP 011_A03; „не одговара“ → карантин, "
               "запис во дел G. Кесата се ре-етикетира ЗЕМЕН ПРИМЕРОК со новото нето (= 400,0 g − земено) и новото бруто.",
            "One row per selected bag, pre-entered. Gross before opening and gross after closing are weighed by QC; sampled = "
            "difference. Inspection: [ ] = conforms to all QCSOP 011_A03 criteria; “does not conform” → quarantine, entry in "
            "section G. The bag is re-labelled SAMPLED with the new net (= 400.0 g − sampled) and the new gross.")
    rows = []
    r = 0
    for l in ls:
        for b in [x for x in bs if x["batch"] == l["batch"]]:
            r += 1
            rows.append([r, l["batch"], b["bag_id"], "400,0", "", "", "", "[ ]", ""])
    table(d, ["№", "Серија | Batch", "Кеса | Bag", "Нето етикета g | Net label g", "Бруто пред g | Gross before g",
              "Бруто по g | Gross after g", "Земено g | Sampled g", "Инсп. | Insp.", "Иниц. | Init."], rows, sz=7,
          weights=[0.9, 2.6, 1.7, 2.0, 2.4, 2.4, 2.2, 1.6, 2.66])
    pr.step_signoff(d, "Потпис за делот D (земање примероци) | Sign-off for section D (sampling)", None)

    # E
    pr.chapter(d, "E", "ВРАЌАЊЕ: КК → СЕФ-МАГАЦИН", "Return: QC → Secure Warehouse")
    rows = [[l["seq"], l["batch"], l["n"], "", ""] for l in ls]
    rows.append(["", "ВКУПНО | TOTAL", sum_n, "", ""])
    table(d, ["№", "Серија | Batch", "Кеси вратени (ре-етикетирани ЗЕМЕН) | Bags returned (re-labelled SAMPLED)",
              "Σ земено g | Σ sampled g", "Забелешка | Remark"], rows, sz=8)
    kv_table(d, [("Од | From", "Контрола на квалитет · Просторија за земање примероци | Quality Control · Sampling room"),
                 ("До | To", "Сеф-магацин · Магацин · Складирање | Secure warehouse · Store · Storage"),
                 ("Датум и час на враќање | Return date and time", BLANK),
                 ("Етикети | Labels", "ЗЕМЕН ПРИМЕРОК + ново нето/бруто по кеса (QASOP_031); ново нето од дел D | "
                                      "SAMPLED + new net/gross per bag (QASOP_031); new net from section D")])
    sign_table(d, ["Вратил — КК | Returned — QC", "Примил назад — магацин | Received back — warehouse"])

    # F
    pr.chapter(d, "F", "ГУБИТОК ПРИ СУШЕЊЕ (SAM_a02.2)", "Loss on Drying (SAM_a02.2)")
    pr.subsec(d, "F.1", "Опрема и услови", "Equipment and conditions")
    kv_table(d, [("Вакуумска печка — ID / статус на квалификација | Vacuum oven — ID / qualification status", BLANK + " / " + BLANK),
                 ("Поставени услови | Set conditions", "40 °C · 15–25 mbar · 24 h   (постигнато | achieved: ____ °C · ____ mbar)"),
                 ("Аналитичка вага — ID / калибрација важи до / дневна проверка | Analytical balance — ID / calibration valid until / daily check", BLANK + " / " + BLANK + " / [ ]"),
                 ("Ексикатор / садови за мерење | Desiccator / weighing bottles", BLANK),
                 ("Влез во печка (датум, час) | Oven in (date, time)", BLANK),
                 ("Мерење по 24 h (датум, час) | Weighing after 24 h (date, time)", BLANK),
                 ("Дополнителен период до константна маса (h) | Additional period to constant mass (h)", BLANK + "  (SAM_a02.2 / Раководител на КК | Head of QC)"),
                 ("Второ мерење (датум, час) | Second weighing (date, time)", BLANK),
                 ("Амбиентални услови (°C, % RH) | Ambient conditions (°C, % RH)", BLANK)])
    pr.subsec(d, "F.2", "Мерења и резултати по тест порција", "Weighings and results per test portion")
    rows = []
    r = 0
    for l in ls:
        for p in range(1, l["k"] + 1):
            r += 1
            rows.append([r, l["batch"], "%d/%d" % (p, l["k"]), "", "", "", "", "", "", "", "" if p < l["k"] else "", "[ ]"])
    table(d, ["№", "Серија | Batch", "Порција | Portion", "Сад бр. | Bottle No.", "m0 g", "G1 g", "G2 (24 h) g",
              "G2 (второ) g | G2 (second) g", "Δ mg", "ГпС % | LoD %", "Средно % | Mean %", "≤ 12,0 % | ≤ 12.0 %"],
          rows, sz=7, weights=[0.8, 2.3, 1.3, 1.3, 1.6, 1.6, 1.7, 1.9, 1.2, 1.6, 1.6, 1.56])
    pr.note(d, "ГпС % = (G1 − G2) ÷ (G1 − m0) × 100 по порција, со G2 = последното мерење до константна маса "
               "(две последователни мерења се разликуваат за не повеќе од 0,5 mg; Δ = разлика помеѓу 24-часовното и "
               "второто мерење). Средната вредност од k порции е резултатот на серијата; критериум ≤ 12,0 % w/w (QCSP 001). "
               "Резултат надвор од спецификација → QCSOP 014 и дел G.",
            "LoD % = (G1 − G2) ÷ (G1 − m0) × 100 per portion, with G2 = the last weighing to constant mass (two consecutive "
            "weighings differ by not more than 0.5 mg; Δ = difference between the 24-h and the second weighing). The mean of k "
            "portions is the batch result; criterion ≤ 12.0 % w/w (QCSP 001). An out-of-specification result → QCSOP 014 and "
            "section G.")
    pr.step_signoff(d, "Потпис за делот F (определување) | Sign-off for section F (determination)", None)

    # G
    pr.chapter(d, "G", "ОТСТАПУВАЊА / OOS", "Deviations / OOS")
    table(d, ["№", "Серија / кеса | Batch / bag", "Опис | Description", "Дејство | Action", "Иниц./датум | Init./date"],
          [[i, "", "", "", ""] for i in range(1, 7)], sz=8)
    pr.note(d, "„Нема отстапувања | No deviations“ се запишува ако табелата останува празна. Отстапувањата се водат по "
               "PP-QA-SOP-003; OOS по QCSOP 014.",
            "“No deviations” is written if the table stays empty. Deviations follow PP-QA-SOP-003; OOS follows QCSOP 014.")

    # H
    d.add_page_break()
    pr.chapter(d, "H", "ЗАКЛУЧНИ ПОТПИСИ", "Closing Sign-offs")
    pr.execution_signoff(d, mk_exec="Извршил (КК аналитичар) | Executed (QC Analyst)", reviewer="J. Romevska",
                         approver="B. Nikolov, M.Pharm. (Раководител на КК оддел | QC Department Manager)")
    return d


# ----------------------------------------------------------------------------- main
def main():
    os.makedirs(OUT, exist_ok=True)
    lots, bags = load()
    docs = [
        ("PP-QC-SP-002_26_Sampling_Plan_LoD_T1_T2.docx", build_plan(lots)),
        ("PP-QC-SP-002_26-ER-01_Execution_Record_Day1.docx", build_record(1, lots, bags)),
        ("PP-QC-SP-002_26-ER-02_Execution_Record_Day2.docx", build_record(2, lots, bags)),
    ]
    ok = True
    for name, d in docs:
        glyph_audit(d)
        path = os.path.join(OUT, name)
        pf.save(d, path)
        ok = verify(path) and ok
    if not ok:
        raise SystemExit("pp_verify FAIL")
    print("written:", OUT)


if __name__ == "__main__":
    main()
