#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the two execution packages of PP-QC-SP-002/26 with the Purely Plant document engine.

Head of QC, 06.10.2026: the sampling of the bags and the loss-on-drying analysis are two separate
documentation packages, each on the company's own forms:

  Package 2 — sampling execution, per sampling day (out/2_SAMPLING_EXECUTION/):
    QCT 024        transfer, secure warehouse -> sampling room (receipt of the selected bags)
    QCSOP 011_A03  visual inspection on opening, one form per batch
    QCT 021        material quantity review: before / sampled / after, per bag
    QASOP_031_A05  "SAMPLED" bag labels and QASOP_031_A07 sample labels (build_labels.py)
    QCT 024        transfer, sampling room -> secure warehouse (return of the sampled bags)
    QCT 024        transfer, sampling room -> QC laboratory (the composite samples)
  Package 3 — loss-on-drying analysis execution, one record per group of samples analysed
    together (out/3_LOD_ANALYSIS_EXECUTION/): receipt, equipment, homogenisation and test
    portions, weighings to constant mass, results, deviations, sign-offs.

The forms reproduce the July 2026 layouts field for field (QCT 024 v01, QCSOP 011_A03 v7.0,
QCT 021 v01); only the values are prefilled. Every number comes from SAMPLING_PLAN_T1_T2_2026-10.tsv
and bag_selection.tsv (campaign_data.py). Each DOCX must pass pp_verify.py.

    python3 build_execution_packages.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_campaign_docs as bc                       # noqa: E402  (engine on sys.path, helpers, constants)
from build_campaign_docs import pf, pr, num, ranges, BLANK  # noqa: E402
from docx.enum.table import WD_TABLE_ALIGNMENT          # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH           # noqa: E402
from docx.oxml import OxmlElement                       # noqa: E402
from docx.oxml.ns import qn                             # noqa: E402
from docx.table import _Cell                            # noqa: E402

OUT_S = os.path.join(bc.OUT, "2_SAMPLING_EXECUTION")
OUT_L = os.path.join(bc.OUT, "3_LOD_ANALYSIS_EXECUTION")
CODE = bc.CODE
PORTRAIT_W, LANDSCAPE_W = 18.46, 27.16

WAREHOUSE = "Сеф-магацин | Secure warehouse"
QC = "Контрола на квалитет | QC"
SAMPLING_ROOM = "Просторија за земање примероци | Sampling room"
QC_LAB = "КК лабораторија | QC laboratory"
SID = "____/26_SFR-PC-___"          # QCSOP 011 v03 §6.2.1 sample code, written at sampling


def rec(day, kind):
    return "%s-D%d-%s" % (CODE, day, kind)


def lod_code(day):
    return "%s-LOD-%02d" % (CODE, day)


def day_lots(lots, day):
    return [l for l in lots if l["day"] == day]


def batch_lot(l):
    """Batch with its P lot; a lot with no P lot on record prints the batch alone."""
    return l["batch"] if l["p_lot"] in ("", "—", None) else "%s · %s" % (l["batch"], l["p_lot"])


def chapter(d, num_, mk, en):
    """Engine chapter heading kept on the page of the table or text that follows it."""
    p = pr.chapter(d, num_, mk, en)
    p.paragraph_format.keep_with_next = True
    return p


def warehouses(ls):
    out = []
    for l in ls:
        if l["warehouse"] not in out:
            out.append(l["warehouse"])
    return out


# ----------------------------------------------------------------------------- table helpers
KIND = {
    "h": (pr.NAVYF, pr.WHITE, True, False),     # navy header
    "l": (pr.LBL, pr.BLACK, True, False),       # label
    "v": (None, pr.BLACK, False, False),        # value / write-in
    "b": (None, pr.BLACK, True, False),         # bold value
    "s": ("DDE7F1", pr.BLACK, True, False),     # batch sub-header
    "t": (pr.LBL, pr.BLACK, True, False),       # total
    "n": (None, pr.BLACK, False, True),         # left-aligned note
}


def grid(d, widths, rows, sz=8, head=0, mode="full", heights=None):
    """A table from row specs. A cell is 'text', (text, span) or (text, span, kind); spans of a row
    must add up to the column count. `head` rows repeat on every page the table spans."""
    ncol = len(widths)
    t = d.add_table(rows=len(rows), cols=ncol)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        tr = t._tbl.tr_lst[i]
        tcs = list(tr.tc_lst)            # direct row access: table.cell() rescans the whole table per call
        j = 0
        for c in row:
            if isinstance(c, str):
                c = (c, 1, "v")
            elif len(c) == 2:
                c = (c[0], c[1], "v")
            text, span, kind = c
            tc = tcs[j]
            if span > 1:                 # horizontal merge: one cell spanning `span` grid columns
                for extra in tcs[j + 1:j + span]:
                    tr.remove(extra)
                tc.grid_span = span
            cell = _Cell(tc, t)
            fill, col, bold, left = KIND[kind]
            pr.cellfmt(cell, text, None, sz, col, bold=bold, fill=fill)
            if left:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
            j += span
        if j != ncol:
            raise ValueError("row %d spans %d of %d columns: %r" % (i, j, ncol, row))
    pr.fixed(t, widths, mode=mode, header_repeat=False)
    if head:
        pr._repeat_header(t, head)
    pr.borders(t)
    for i, h in (heights or {}).items():
        row_height(t.rows[i], h)
    return t


def row_height(row, cm):
    trPr = row._tr.get_or_add_trPr()
    e = OxmlElement("w:trHeight")
    e.set(qn("w:val"), str(int(cm * 567)))
    e.set(qn("w:hRule"), "atLeast")
    trPr.append(e)


def new_form(code, version, mk, en, orient="portrait"):
    pr.PAGE_W = PORTRAIT_W if orient == "portrait" else LANDSCAPE_W
    return pf.new_annex(code=code, version=version, mk_title=mk, en_title=en, orient=orient, status=bc.STATUS)


def caption(d, mk, en):
    """One small line naming which movement or day this copy of the form records."""
    p = d.add_paragraph()
    pr.sp(p, 2, 4)
    pr.rin(p, mk, 10, pr.NAVY, bold=True)
    pr.rin(p, "  |  ", 9, pr.GREY)
    pr.rin(p, en, 9, pr.GREY, ital=True)


def page_break(d):
    d.add_page_break()


# ----------------------------------------------------------------------------- QCT 024 (July layout)
def qct024(record, caption_mk, caption_en, frm, to, ref, batch_lot, note, items, total,
           operator=("Оператор | Operator", "Супервизор | Supervised by"),
           confirm=("Доставено од | Delivered by", "Прием од | Receipt by")):
    d = new_form("QCT 024", "01", "Запис за пренос на материјал", "Material transfer record")
    caption(d, caption_mk, caption_en)
    w6 = [PORTRAIT_W / 6] * 6
    grid(d, w6, [
        [("Запис број | Record Number", 2, "l"), (record, 4, "b")],
        [("ПРЕДАВАЊЕ ОД | HANDOVER FROM", 3, "h"), ("ПРИЕМ ВО | HANDOVER TO", 3, "h")],
        [("Оддел | Department", 1, "l"), ("Просторија | Room", 1, "l"), ("Процес | Process", 1, "l")] * 2,
        list(frm) + list(to),
    ])
    pr.gap(d, 6)
    grid(d, [2.3, 2.9, 2.9, 4.86, 2.3, 3.2], [
        [("Информации за преносот | Transfer information", 6, "h")],
        [("Датум | Date", 1, "l"), BLANK, ("Референтен документ | Reference document", 1, "l"), ref,
         ("Серија / Лот | Batch / Lot", 1, "l"), batch_lot],
        [("Забелешка | Note", 1, "l"), (note, 5, "n")],
    ])
    pr.gap(d, 6)
    grid(d, [4.6, 4.63, 4.6, 4.63], [
        [(operator[0], 2, "h"), (operator[1], 2, "h")],
        [("Име Презиме | Name Surname", 1, "l"), ("Датум и потпис | Date and signature", 1, "l")] * 2,
        ["", "", "", ""],
    ], heights={2: 0.9})
    pr.gap(d, 6)
    rows = [[("Попис на контејнери/кутии/кеси — нето/бруто | Container/box/bag inventory — net/gross", 5, "h")],
            [("№", 1, "l"), ("Контејнер/Кутија/Кеса бр. | Container/Box/Bag No.", 1, "l"),
             ("Нето (g) | Net (g)", 1, "l"), ("Бруто (g) | Gross (g)", 1, "l"), ("Забелешка | Remark", 1, "l")]]
    rows += items
    rows.append(total)
    grid(d, [1.0, 6.2, 2.8, 2.8, 5.66], rows, sz=8, head=2)
    pr.gap(d, 6)
    grid(d, [3.1, 3.1, 3.03, 3.1, 3.1, 3.03], [
        [("Потврда | Confirmation", 6, "h")],
        [(confirm[0], 3, "l"), (confirm[1], 3, "l")],
        [("Име Презиме | Name Surname", 1, "l"), ("Потпис | Signature", 1, "l"), ("Датум | Date", 1, "l")] * 2,
        ["", "", "", "", "", ""],
    ], heights={3: 0.9})
    return d


def bag_items(ls, bags, day, net, remark=""):
    """One row per bag. Since the 06.10.2026 amendment each batch has one bag, chosen at sampling, so the
    row carries the batch and the bag number is a write-in."""
    items, i = [], 0
    for l in ls:
        bl = [x for x in bags if int(x["day"]) == day and x["batch"] == l["batch"]]
        if len(bl) == 1:
            i += 1
            items.append([str(i), ("%s · %s · %s · магацин/store %s · кеса/bag %s"
                                   % (batch_lot(l), l["strain"], l["grade"] or "—", l["warehouse"], bl[0]["bag_id"]), 1, "n"),
                          net, "", remark])
            continue
        items.append([("%s · %s · %s · магацин/store %s · картони/cartons %s · n = %d"
                       % (batch_lot(l), l["strain"], l["grade"] or "—", l["warehouse"],
                          ranges(l["carton_list"]), l["n"]), 5, "s")])
        for b in bl:
            i += 1
            items.append([str(i), b["bag_id"], net, "", remark])
    return items, i


def build_receipt(day, lots, bags):
    ls = day_lots(lots, day)
    items, nb = bag_items(ls, bags, day, "400,0")
    whs = " · ".join(warehouses(ls))
    return qct024(
        rec(day, "RCPT"),
        "ПРИЕМ — Ден %d: сеф-магацин → просторија за земање примероци" % day,
        "RECEIPT — Day %d: secure warehouse → sampling room" % day,
        (WAREHOUSE, "Магацин | Store %s" % whs, "Складирање | Storage"),
        (QC, SAMPLING_ROOM, "Земање примероци | Sampling"),
        "%s · PP-QC-MHR-___/26" % CODE,
        "%d серии | %d batches" % (len(ls), len(ls)),
        "Една кеса по серија (Раководител на КК, 06.10.2026); бројот на кесата K{картон}B{кеса} се запишува при "
        "повлекувањето. Нето = етикетата на примарното пакување (400,0 g); бруто го мери КК при прием. | One bag per "
        "batch (Head of QC, 06.10.2026); the bag number K{carton}B{bag} is written at retrieval. Net = the primary-pack "
        "label (400.0 g); gross is weighed by QC at receipt.",
        items,
        [("ВКУПНО | TOTAL", 2, "t"), (num(nb * 400, 1), 1, "t"), ("", 1, "t"), ("%d кеси / bags" % nb, 1, "t")],
        confirm=("Доставено од (магацин) | Delivered by (warehouse)", "Прием од (КК) | Receipt by (QC)"))


def build_return(day, lots, bags):
    ls = day_lots(lots, day)
    items, nb = bag_items(ls, bags, day, "")
    return qct024(
        rec(day, "RET"),
        "ВРАЌАЊЕ — Ден %d: просторија за земање примероци → сеф-магацин" % day,
        "RETURN — Day %d: sampling room → secure warehouse" % day,
        (QC, SAMPLING_ROOM, "Земање примероци | Sampling"),
        (WAREHOUSE, "Магацин | Store %s" % " · ".join(warehouses(ls)), "Складирање | Storage"),
        "%s · QCT 021 Ден | Day %d" % (CODE, day),
        "%d серии | %d batches" % (len(ls), len(ls)),
        "Враќање: ново нето и бруто по кеса од QCT 021 (после мострирање); кесите се затворени и означени „МОСТРИРАНО“ "
        "(QASOP_031_A05_v1). Картоните се враќаат на истата позиција. | Return: new net and gross per bag from "
        "QCT 021 (after sampling); the bags are closed and labelled “SAMPLED” (QASOP_031_A05_v1). The cartons go back to "
        "the same position.",
        items,
        [("ВКУПНО | TOTAL", 2, "t"), ("", 1, "t"), ("", 1, "t"), ("%d кеси / bags" % nb, 1, "t")],
        confirm=("Доставено од (КК) | Delivered by (QC)", "Прием од (магацин) | Receipt by (warehouse)"))


def build_sample_transfer(day, lots):
    ls = day_lots(lots, day)
    items = []
    for i, l in enumerate(ls, start=1):
        items.append([str(i), "%s · %s" % (l["batch"], SID), "", "",
                      "k = %d · %d кеса / bag" % (l["k"], l["n"])])
    return qct024(
        rec(day, "SMP"),
        "ПРИМЕРОЦИ — Ден %d: просторија за земање примероци → КК лабораторија" % day,
        "SAMPLES — Day %d: sampling room → QC laboratory" % day,
        (QC, SAMPLING_ROOM, "Земање примероци | Sampling"),
        (QC, QC_LAB, "Губиток при сушење | Loss on drying"),
        "%s · QCT 021 Ден | Day %d → %s" % (CODE, day, lod_code(day)),
        "%d серии | %d batches" % (len(ls), len(ls)),
        "Примероци, по еден за серија (од една кеса), во затворени чисти сади означени по QASOP_031_A07; нето = "
        "мострирано од QCT 021. Се анализираат заедно на %s. | Samples, one per batch (from one bag), in closed clean "
        "containers labelled per QASOP_031_A07; net = sampled from QCT 021. They are analysed together on %s."
        % (lod_code(day), lod_code(day)),
        items,
        [("ВКУПНО | TOTAL", 2, "t"), ("", 1, "t"), ("", 1, "t"), ("%d примероци / samples" % len(ls), 1, "t")],
        confirm=("Доставено од (земање) | Delivered by (sampling)", "Прием од (КК лабораторија) | Receipt by (QC laboratory)"))


# ----------------------------------------------------------------------------- QCSOP 011_A03 (v7.0 layout)
CRITERIA = [
    ("Боја и изглед | Color & Appearance", "Здрава, без дисколорација | Healthy, no discoloration"),
    ("Мирис | Odor", "Карактеристичен, без непријатни | Characteristic, no off-odors"),
    ("Структура | Flower Structure", "Густи, добро формирани | Dense, well-formed buds"),
    ("Трихоми | Trichome Integrity", "Целосни и видливи | Intact and visible"),
    ("Мувла/Пепелница | Mold/Mildew", "Не е детектирано | None detected"),
    ("Штетници | Pests", "Не е детектирано | None detected"),
    ("Семки | Seeds", "Не е детектирано (ако е лек) | None (if medicine)"),
    ("Страни материи | Foreign Matter", "≤ 2% (Ph. Eur. 2.8.2) | ≤ 2% (Ph. Eur. 2.8.2)"),
    ("Контаминација | Contamination", "Без прашина, влакна, честички | No dust, fibers, particles"),
]


def build_a03(day, lots, bags):
    ls = day_lots(lots, day)
    d = new_form("QCSOP 011_A03", "7.0", "Формулар за визуелна инспекција на канабис цвет",
                 "Cannabis flower visual inspection form")
    for idx, l in enumerate(ls):
        if idx:
            page_break(d)
        caption(d, "Ден %d · серија %d од %d · %s" % (day, idx + 1, len(ls), CODE),
                "Day %d · batch %d of %d · %s" % (day, idx + 1, len(ls), CODE))
        grid(d, [2.6, 3.6, 2.2, 4.06, 2.0, 4.0], [
            [("Идентификација на инспекцијата | Inspection Identification", 6, "h")],
            [("Запис бр. | Record No.", 1, "l"), ("QCSOP 011_A03-___/26", 5, "v")],
            [("Серија | Batch", 1, "l"), (batch_lot(l), 1, "b"), ("Сорта | Strain", 1, "l"),
             "%s · %s" % (l["strain"], l["grade"] or "—"), ("Датум | Date", 1, "l"), BLANK],
            [("Просторија | Room", 1, "l"), SAMPLING_ROOM, ("Инспектирал | Inspector", 1, "l"), ("", 3, "v")],
            [("Фаза на инспекција | Inspection stage", 6, "h")],
            [("[ ] Берба   [ ] Триминг   [ ] Пред пакување   [X] По отворање на секоја кеса (SP-12) | "
              "[ ] Harvest   [ ] Trimming   [ ] Pre-packaging   [X] Post-opening of each bag (SP-12)", 6, "v")],
        ])
        pr.gap(d, 5)
        rows = [[("Критериуми на инспекција (ниво на серија) | Inspection criteria (batch level)", 3, "h")],
                [("Параметар | Parameter", 1, "l"), ("Критериум | Criteria", 1, "l"), ("Резултат | Result", 1, "l")]]
        rows += [[(p, 1, "l"), c, "[ ] Одговара | Conforms"] for p, c in CRITERIA]
        grid(d, [5.2, 8.26, 5.0], rows, sz=8)
        pr.note(d, "За секоја избрана кеса, пред земање, изврши и евидентирај визуелна инспекција. Кое било „Не одговара“ → "
                   "карантин и отстапување (PP-QA-SOP-003).",
                "For each selected bag, before sampling, perform and record a visual inspection. Any “Does not conform” → "
                "quarantine and deviation (PP-QA-SOP-003).")
        rows = [[("Поединечна инспекција при отворање — по кеса (SP-12) | Per-bag inspection on opening (SP-12)", 9, "h")],
                [("№", 1, "l"), ("Кеса бр. | Bag No.", 1, "l"), ("Боја/мирис | Color/Odor", 1, "l"),
                 ("Мувла | Mould", 1, "l"), ("Штетници | Pests", 1, "l"), ("Страни м./семки | FM/Seeds", 1, "l"),
                 ("Оштет. пак. | Pack dmg", 1, "l"), ("Севкупно | Overall", 1, "l"), ("Инсп. | Init.", 1, "l")]]
        bl = [b for b in bags if int(b["day"]) == day and b["batch"] == l["batch"]]
        rows += [[str(i), (b["bag_id"], 1, "b"), "", "", "", "", "", "", ""] for i, b in enumerate(bl, start=1)]
        rows.append([("Одлука | Decision", 2, "l"),
                     ("[ ] Одобрено за следна фаза   [ ] Потребна доработка   [ ] Одбиено | "
                      "[ ] Approved for next stage   [ ] Requires rework   [ ] Rejected", 7, "v")])
        grid(d, [1.0, 2.2, 2.3, 1.9, 2.0, 2.5, 2.2, 2.3, 2.06], rows, sz=8, head=2)
        pr.gap(d, 5)
        grid(d, [5.0, 6.06, 3.4, 4.0], [
            [("Улога | Role", 1, "h"), ("Име/Позиција | Name/Position", 1, "h"), ("Датум | Date", 1, "h"),
             ("Потпис | Signature", 1, "h")],
            [("Инспектирал | Inspected by", 1, "l"), "", "", ""],
            [("Одобрил (КК) | Approved by (QC)", 1, "l"), "", "", ""],
        ], heights={1: 0.8, 2: 0.8})
    return d


# ----------------------------------------------------------------------------- QCT 021 (v01 layout)
def build_qct021(day, lots, bags):
    ls = day_lots(lots, day)
    d = new_form("QCT 021", "01", "Преглед на количини на материјали и дневно усогласување на магацинската состојба",
                 "Material quantity review & daily warehouse reconciliation", orient="landscape")
    caption(d, "ПРЕД И ПОСЛЕ МОСТРИРАЊЕ — Ден %d · %d серии · %s" % (day, len(ls), CODE),
            "BEFORE AND AFTER SAMPLING — Day %d · %d batches · %s" % (day, len(ls), CODE))
    grid(d, [2.6, 4.0, 3.6, 10.36, 2.6, 4.0], [
        [("MLR №", 1, "l"), "", ("Референтен документ | Reference document", 1, "l"),
         "%s · QCT 024 %s" % (CODE, rec(day, "RCPT")), ("Датум | Date", 1, "l"), BLANK],
    ], heights={0: 0.8})
    pr.gap(d, 5)
    W = [3.0, 2.0, 2.2, 2.2, 4.6, 2.2, 2.2, 2.36, 2.0, 2.2, 2.2]
    rows = [[("№", 1, "h"), ("Пред мострирање (g) | Before sampling", 3, "h"), ("Мострирано (g) | Sampled", 4, "h"),
             ("После мострирање (g) | After sampling", 3, "h")],
            [("Серија | Batch", 1, "l"), ("Кеса бр. / ID код | Bag No. / ID code", 1, "l"), ("Нето | Net (g)", 1, "l"),
             ("Бруто | Gross (g)", 1, "l"), ("ID код на мостра | Sample ID Code (sID)", 1, "l"), ("Нето | Net (g)", 1, "l"),
             ("Бруто | Gross (g)", 1, "l"), ("Намена | Use", 1, "l"), ("Кеса бр. / ID код | Bag No. / ID code", 1, "l"),
             ("Нето | Net (g)", 1, "l"), ("Бруто | Gross (g)", 1, "l")]]
    nb = 0
    for l in ls:
        bl = [b for b in bags if int(b["day"]) == day and b["batch"] == l["batch"]]
        if len(bl) == 1:                 # one bag per batch (06.10.2026): the sample code sits on the bag's row
            nb += 1
            rows.append([batch_lot(l), (bl[0]["bag_id"], 1, "b"), "400,0", "", SID, "", "", "ГпС / LoD",
                         (bl[0]["bag_id"], 1, "b"), "", ""])
            continue
        for b in bl:
            nb += 1
            rows.append([l["batch"], (b["bag_id"], 1, "b"), "400,0", "", "→ збирен / composite", "", "", "ГпС / LoD",
                         (b["bag_id"], 1, "b"), "", ""])
        rows.append([("ВКУПНО / TOTAL %s" % l["batch"], 1, "t"), ("%d кеси / bags" % len(bl), 1, "t"),
                     (num(len(bl) * 400, 1), 1, "t"), ("", 1, "t"), (SID, 1, "t"), ("", 1, "t"), ("", 1, "t"),
                     ("ГпС / LoD · k = %d" % l["k"], 1, "t"), ("%d кеси / bags" % len(bl), 1, "t"), ("", 1, "t"),
                     ("", 1, "t")])
    rows.append([("ВКУПНО (g) | TOTAL (g)", 2, "t"), (num(nb * 400, 1), 1, "t"), ("", 1, "t"),
                 ("%d примероци / samples" % len(ls), 1, "t"), ("", 1, "t"), ("", 1, "t"), ("", 1, "t"),
                 ("%d кеси / bags" % nb, 1, "t"), ("", 1, "t"), ("", 1, "t")])
    grid(d, W, rows, sz=7, head=2)
    pr.note(d, "Една кеса по серија (Раководител на КК, 06.10.2026); бројот на кесата K{картон}B{кеса} се запишува. Пред: нето "
               "и бруто се препишуваат од QCT 024 (прием). Мострирано: примерокот на серијата од таа кеса, во затворен означен сад "
               "(шифра на примерок). После: бруто се мери по затворање на кесата; нето после = нето пред − мострирано. Каде кесата "
               "има картон за кеса (PO_SOP_007_A14-02), мострирањето се запишува и таму (дејство 01).",
            "One bag per batch (Head of QC, 06.10.2026); the bag number K{carton}B{bag} is written. Before: net and gross "
            "transcribed from QCT 024 (receipt). Sampled: the batch sample from that bag, in a closed labelled container "
            "(sample code). After: gross weighed after the bag is closed; net after = net before − sampled. Where the bag "
            "carries its bag card (PO_SOP_007_A14-02), the sampling is entered there too (action 01).")
    grid(d, [7.0, 4.0, 6.0], [
        [("Параметар | Parameter", 1, "l"), ("m (g)", 1, "l"), ("Потпис | Signature", 1, "l")],
        [("Отпад | Waste", 1, "l"), "", ""],
        [("Изгубено во процес | Lost in process", 1, "l"), "", ""],
        [("Добиено во процес | Gained in process", 1, "l"), "", ""],
    ], mode="compact")
    pr.gap(d, 6)
    grid(d, [3.2, 2.7, 3.0, 2.0, 2.68, 3.2, 2.7, 3.0, 2.0, 2.68], [
        [("Подготвено од | Prepared by:", 1, "l"), ("Функција | Function:", 1, "l"), ("Име и Презиме | Name & Surname", 1, "l"),
         ("Датум | Date:", 1, "l"), ("Потпис | Signature", 1, "l"), ("Проверено и Одобрено од | Checked & Approved by:", 1, "l"),
         ("Функција | Function:", 1, "l"), ("Име и Презиме | Name & Surname", 1, "l"), ("Датум | Date:", 1, "l"),
         ("Потпис | Signature", 1, "l")],
        ["", "QC персонал | QC Personnel", "", "", "", "", "QC Менаџер | QC Manager", "", "", ""],
    ], heights={1: 0.9})
    return d


# ----------------------------------------------------------------------------- package index
def build_index(lots):
    ls = day_lots(lots, 1)
    d = new_form(CODE + "-SMP", bc.VERSION, "Пакет за извршување — земање примероци",
                 "Execution package — sampling")
    chapter(d, "1", "СОДРЖИНА НА ПАКЕТОТ", "Package Contents")
    pr.body(d, "Овој пакет го документира земањето примероци на Транша 1 и 2 според %s, на обрасците на QCSOP 011 и "
               "QASOP_031: сите %d серии во еден ден, една кеса по серија (Раководител на КК, 06.10.2026). Анализата за "
               "губиток при сушење е посебен пакет (%s)." % (CODE, len(ls), lod_code(1)),
            "This package documents the sampling of Tranches 1 and 2 under %s, on the QCSOP 011 and QASOP_031 forms: all "
            "%d batches on one day, one bag per batch (Head of QC, 06.10.2026). The loss-on-drying analysis is a separate "
            "package (%s)." % (CODE, len(ls), lod_code(1)))
    rows = [[("Чекор | Step", 1, "h"), ("Документ | Document", 1, "h"), ("Образец | Form", 1, "h"),
             ("Запис бр. | Record No.", 1, "h")]]
    steps = [
        ("1", "Пренос сеф-магацин → просторија за земање | Transfer secure warehouse → sampling room", "QCT 024 v01",
         rec(1, "RCPT")),
        ("2", "Визуелна инспекција при отворање, по серија | Visual inspection on opening, per batch", "QCSOP 011_A03 v7.0",
         "QCSOP 011_A03-___/26 × %d" % len(ls)),
        ("3", "Мерење пред и после мострирање, по кеса | Weighing before and after sampling, per bag", "QCT 021 v01",
         "MLR № ___"),
        ("4", "Етикети „МОСТРИРАНО“ на кесите | “SAMPLED” labels on the bags", "QASOP_031_A05_v1",
         "%d" % sum(l["n"] for l in ls)),
        ("5", "Етикети на примероците | Labels on the samples", "QASOP_031_A07", "%d" % len(ls)),
        ("6", "Враќање на кесите во сеф-магацин | Return of the bags to the secure warehouse", "QCT 024 v01",
         rec(1, "RET")),
        ("7", "Пренос на примероците во КК лабораторија | Transfer of the samples to the QC laboratory", "QCT 024 v01",
         rec(1, "SMP")),
    ]
    rows += [[s_, (doc, 1, "n"), f, r1] for s_, doc, f, r1 in steps]
    grid(d, [1.3, 8.4, 3.4, 5.36], rows, sz=8, head=1)
    chapter(d, "2", "РЕДОСЛЕД НА РАБОТА", "Order of Work")
    for mk, en in [
        ("Пред земање: RQS е регистриран (QCSOP 011 v03 §6.1.1); просторијата и приборот се чисти и суви; вагата е проверена.",
         "Before sampling: the RQS is registered (QCSOP 011 v03 §6.1.1); the room and tools are clean and dry; the balance is checked."),
        ("За секоја серија се повлекува една кеса и се прима на QCT 024 (прием) со бројот K{картон}B{кеса} и бруто. Кесата се "
         "отвора, се прегледува на A03, примерокот се зема во затворен сад, кесата се затвора и се мери (QCT 021).",
         "For each batch one bag is retrieved and received on QCT 024 (receipt) with its number K{carton}B{bag} and gross. "
         "The bag is opened, inspected on A03, the sample goes into a closed container, and the bag is closed and weighed "
         "(QCT 021)."),
        ("Секоја мострирана кеса добива етикета „МОСТРИРАНО“; садот со примерокот добива етикета QASOP_031_A07 со шифрата "
         "на примерокот. Кесите се враќаат на QCT 024 (враќање), примероците одат во КК лабораторија на QCT 024 (примероци).",
         "Each sampled bag gets a “SAMPLED” label; the sample container gets a QASOP_031_A07 label with the sample code. "
         "The bags go back on QCT 024 (return); the samples go to the QC laboratory on QCT 024 (samples)."),
        ("Истиот ден примероците влегуваат во анализата %s, сите во едно сушење." % lod_code(1),
         "The same day the samples enter analysis %s, all in one oven run." % lod_code(1)),
        ("Документација: истовремено, трајно сино мастило, без празни полиња („N/A“), поправка со една линија, иницијали и "
         "датум (ALCOA+).",
         "Documentation: contemporaneous, permanent blue ink, no blank fields (“N/A”), single-line corrections with initials "
         "and date (ALCOA+)."),
    ]:
        pr.bullet(d, mk, en)
    return d


# ----------------------------------------------------------------------------- LoD execution record
def analysis_id(l):
    """AM02.2 analysis ID as on the July AM02.2 moisture record: ddmmyy_AM02.2_<P lot>, the batch where
    there is no P lot; the date is written at receipt."""
    return "______ _AM02.2_%s" % (l["batch"] if l["p_lot"] in ("", "—", None) else l["p_lot"])


def build_lod(day, lots):
    ls = day_lots(lots, day)
    code = lod_code(day)
    sum_k = sum(l["k"] for l in ls)
    d = bc.new_doc(code, "ИЗВРШЕН ЗАПИС — ГУБИТОК ПРИ СУШЕЊЕ — ТРАНША 1 И 2",
                   "EXECUTION RECORD — LOSS ON DRYING — TRANCHES 1 AND 2")
    bc.cover(d, "Извршен запис — губиток при сушење, Транша 1 и 2, едно сушење",
             "Execution record — loss on drying, Tranches 1 and 2, one oven run",
             [("Запис бр. | Record No.", code),
              ("План | Plan", CODE + " · Транша 1 и 2 | Tranches 1 and 2"),
              ("Примероци | Samples", "QCT 024 %s · %d примероци, по еден за серија | %d samples, one per batch" % (rec(day, "SMP"), len(ls), len(ls))),
              ("Тест порции | Test portions", "%d — по една за серија, сите во едно сушење | one per batch, all in one oven run" % sum_k),
              ("Метод | Method", "Ph. Eur. 2.2.32 (3028) · a02.2 · 40 °C · 20 ± 2 mbar · 24 h · молекуларно сито R | molecular sieve R"),
              ("Критериум | Criterion", "≤ 12,0 % w/w (QCSP 001) | ≤ 12.0 % w/w (QCSP 001)"),
              ("Влез во печка / мерење 24 h / второ мерење | Oven in / 24-h weighing / second weighing",
               "%s / %s / %s" % (BLANK, BLANK, BLANK)),
              ("Аналитичар | Analyst", bc.ANALYST)],
             "ИЗВРШЕН ЗАПИС | EXECUTION RECORD", "Loss on Drying — Tranches 1 and 2",
             "Сите 46 серии анализирани заедно", "All 46 batches analysed together")

    chapter(d, "A", "ПРИЕМ НА ПРИМЕРОЦИТЕ", "Receipt of the Samples")
    rows = [["№", "Серија | Batch", "P лот | P lot", "Сорта | Strain", "Шифра на примерок | Sample code",
             "AM02.2 ознака | AM02.2 analysis ID", "Примерок g (QCT 021) | Sample g", "k", "Состојба | Condition",
             "Иниц./час | Init./time"]]
    rows = [[(x, 1, "h") for x in rows[0]]]
    for i, l in enumerate(ls, start=1):
        rows.append([str(i), (l["batch"], 1, "b"), l["p_lot"], l["strain"], SID, analysis_id(l), "", str(l["k"]),
                     "[ ] затворен, означен | closed, labelled", ""])
    grid(d, [0.7, 2.2, 1.5, 2.0, 2.4, 2.9, 1.6, 0.7, 2.6, 1.86], rows, sz=7, head=1)
    pr.note(d, "Примероците се примени на QCT 024 %s. Масата на примерокот се препишува од QCT 021. "
               "Шифрата на примерокот е од етикетата (QCSOP 011); AM02.2 ознаката е аналитичката ознака на записите за AM02.2, "
               "со датумот на прием (ддммгг)." % rec(day, "SMP"),
            "The samples are received on QCT 024 %s. The sample mass is transcribed from QCT 021. The "
            "sample code is the label's (QCSOP 011); the AM02.2 analysis ID is the analytical ID of the AM02.2 records, with the "
            "date of receipt (ddmmyy)." % rec(day, "SMP"))
    pr.step_signoff(d, "Потпис за делот A (прием) | Sign-off for section A (receipt)", None)

    chapter(d, "B", "ОПРЕМА, МАТЕРИЈАЛИ И УСЛОВИ", "Equipment, Materials and Conditions")
    bc.kv_table(d, [
        ("Вакуумска печка — ID / статус на квалификација | Vacuum oven — ID / qualification status",
         "VO29 (QCWI 018 · дневник | logbook QCLB 017) / " + BLANK),
        ("Поставени услови | Set conditions", "40 °C · 20 ± 2 mbar · 24 h   (постигнато | achieved: ____ °C · ____ mbar)"),
        ("Молекуларно сито R во печката, околу 100 g, активно | Molecular sieve R in the oven, about 100 g, active", "[ ]"),
        ("Аналитичка вага — ID / калибрација до / дневна проверка | Analytical balance — ID / calibration until / daily check",
         "Shimadzu AUW220D, d = 0,01 mg (QCWI 016 · дневник | logbook QCLB 008) / " + BLANK + " / [ ]"),
        ("Контролен тег — номинално / измерено | Check weight — nominal / found", BLANK + " / " + BLANK),
        ("Ексикатор / сушач | Desiccator / desiccant", BLANK + " / молекуларно сито [ ] активно | molecular sieve [ ] active"),
        ("Ладење во ексикатор пред секое мерење, најмалку 30 min | Cooling in the desiccator before every weighing, at least 30 min",
         "[ ]"),
        ("Садови за мерење — бр. / претходно исушени под условите на методот | Weighing bottles — nos. / previously dried "
         "under the method conditions", BLANK + " / [ ]"),
        ("Прибор за сечење / подлога | Cutting tools / tray", "нерѓосувачки челик, чисти и суви [ ] | stainless steel, clean and dry [ ]"),
        ("Амбиентални услови (°C, % RH) | Ambient conditions (°C, % RH)", BLANK),
    ])
    pr.step_signoff(d, "Потпис за делот B | Sign-off for section B", None)

    chapter(d, "C", "ХОМОГЕНИЗАЦИЈА И ТЕСТ ПОРЦИИ", "Homogenisation and Test Portions")
    for mk, en in [
        ("Примерокот на серијата (од една кеса) се сече грубо со чисти ножици на чиста подлога и се меша.",
         "The batch sample (from one bag) is coarsely cut with clean scissors on a clean tray and mixed."),
        ("Се зема една тест порција од 1,000 g сецкана, несеана дрога во претходно исушен тариран сад (m_B) и веднаш "
         "се мери (G1).",
         "One test portion of 1.000 g of the cut, unsieved drug is taken into a previously dried, tared bottle (m_B) and "
         "weighed at once (G1)."),
        ("Остатокот се чува затворен и означен до одобрувањето на овој запис.",
         "The remainder is kept closed and labelled until this record is approved."),
    ]:
        pr.bullet(d, mk, en)
    rows = [[(x, 1, "h") for x in ["№", "Серија | Batch", "Сечење и мешање | Cut and mixed",
                                   "Сад бр. | Bottle No.", "Остаток затворен, означен | Remainder closed, labelled",
                                   "Иниц./час | Init./time"]]]
    for i, l in enumerate(ls, start=1):
        rows.append([str(i), (l["batch"], 1, "b"), "[ ]", "", "[ ]", ""])
    grid(d, [0.8, 3.2, 3.4, 2.8, 4.8, 3.46], rows, sz=8, head=1)
    pr.step_signoff(d, "Потпис за делот C | Sign-off for section C", None)

    chapter(d, "D", "МЕРЕЊА И РЕЗУЛТАТИ ПО ТЕСТ ПОРЦИЈА", "Weighings and Results per Test Portion")
    rows = [[(x, 1, "h") for x in ["№", "Серија | Batch", "Сад бр. | Bottle No.", "m_B g", "G1 g",
                                   "m₀ g", "G2 (24 h) g", "G2 (следно) | G2 (next) g", "Δ mg", "m₁ g", "ГпС % | LoD %"]]]
    for r, l in enumerate(ls, start=1):
        rows.append([str(r), (l["batch"], 1, "b"), "", "", "", "", "", "", "", "", ""])
    grid(d, [0.7, 2.4, 1.3, 1.65, 1.65, 1.65, 1.8, 1.8, 1.2, 1.65, 2.66], rows, sz=7, head=1)
    pr.note(d, "m_B = празен претходно исушен сад; G1 = сад + примерок пред сушење; m₀ = G1 − m_B; G2 = сад + примерок по сушење "
               "(40 °C · 20 ± 2 mbar над молекуларно сито R, ладење најмалку 30 min во ексикатор пред секое мерење); "
               "m₁ = G2 − m_B со последното G2; ГпС % = (m₀ − m₁) ÷ m₀ × 100. Константна маса: две последователни мерења се "
               "разликуваат за не повеќе од 0,5 mg (Δ); ако не, сушењето продолжува и мерењата се внесуваат во табелата подолу. "
               "Една порција по серија: нејзиниот ГпС е резултатот на серијата. Резултат надвор од спецификација → QCSOP 014 и дел F.",
            "m_B = empty, previously dried bottle; G1 = bottle + sample before drying; m₀ = G1 − m_B; G2 = bottle + sample after "
            "drying (40 °C · 20 ± 2 mbar over molecular sieve R, cooled at least 30 min in the desiccator before every weighing); "
            "m₁ = G2 − m_B with the last G2; LoD % = (m₀ − m₁) ÷ m₀ × 100. Constant mass: two consecutive weighings differ by "
            "not more than 0.5 mg (Δ); if not, drying continues and the weighings go in the table below. One portion per batch: "
            "its LoD is the batch result. An out-of-specification result → QCSOP 014 and section F.")
    rows = [[("Дополнителни мерења до константна маса | Further weighings to constant mass", 6, "h")],
            [(x, 1, "l") for x in ["№", "Ред № во табела D | Row No. in table D", "G2 g", "Δ mg",
                                   "Датум и час | Date and time", "Иниц. | Init."]]]
    rows += [[str(i), "", "", "", "", ""] for i in range(1, 21)]
    grid(d, [0.8, 4.0, 3.4, 2.6, 4.4, 3.26], rows, sz=8, head=2)
    pr.step_signoff(d, "Потпис за делот D (определување) | Sign-off for section D (determination)", None)

    chapter(d, "E", "РЕЗУЛТАТИ ПО СЕРИЈА", "Results per Batch")
    rows = [[(x, 1, "h") for x in ["№", "Серија | Batch", "P лот | P lot", "k", "ГпС % | LoD %",
                                   "Критериум | Criterion", "Одговара | Conforms", "Сушење од–до | Drying from–to",
                                   "Иниц. | Init."]]]
    for i, l in enumerate(ls, start=1):
        rows.append([str(i), (l["batch"], 1, "b"), l["p_lot"], str(l["k"]), "", "≤ 12,0 %", "[ ] да | yes  [ ] не | no", "", ""])
    grid(d, [0.8, 2.6, 1.8, 0.8, 2.3, 2.0, 3.0, 3.3, 1.86], rows, sz=7, head=1)
    pr.note(d, "Резултатот и датумите на сушење влегуваат во регистарот на сертификати по правилата на бирото за сертификати.",
            "The result and the drying dates enter the certificate register under the certificate desk's rules.")

    chapter(d, "F", "ОТСТАПУВАЊА / OOS", "Deviations / OOS")
    rows = [[(x, 1, "h") for x in ["№", "Серија / порција | Batch / portion", "Опис | Description", "Дејство | Action",
                                   "Иниц./датум | Init./date"]]]
    rows += [[str(i), "", "", "", ""] for i in range(1, 7)]
    grid(d, [0.8, 3.4, 6.4, 5.0, 2.86], rows, sz=8, head=1)
    pr.note(d, "„Нема отстапувања | No deviations“ се запишува ако табелата останува празна. Отстапувањата се водат по "
               "PP-QA-SOP-003; OOS по QCSOP 014.",
            "“No deviations” is written if the table stays empty. Deviations follow PP-QA-SOP-003; OOS follows QCSOP 014.")

    d.add_page_break()
    chapter(d, "G", "ЗАКЛУЧНИ ПОТПИСИ", "Closing Sign-offs")
    pr.execution_signoff(d, mk_exec="Извршил (КК аналитичар) | Executed (QC Analyst)", reviewer="J. Romevska",
                         approver="B. Nikolov, M.Pharm. (Раководител на КК оддел | QC Department Manager)")
    return d


# ----------------------------------------------------------------------------- main
SAMPLING_DOCS = [  # (step, stem template, builder)
    ("1", "S%d-1_QCT024_Transfer_Warehouse_to_Sampling_Day%d", lambda day, lots, bags: build_receipt(day, lots, bags)),
    ("2", "S%d-2_QCSOP011_A03_Visual_Inspection_Day%d", lambda day, lots, bags: build_a03(day, lots, bags)),
    ("3", "S%d-3_QCT021_Before_After_Sampling_Day%d", lambda day, lots, bags: build_qct021(day, lots, bags)),
    ("6", "S%d-6_QCT024_Transfer_Return_to_Warehouse_Day%d", lambda day, lots, bags: build_return(day, lots, bags)),
    ("7", "S%d-7_QCT024_Transfer_Samples_to_QC_Lab_Day%d", lambda day, lots, bags: build_sample_transfer(day, lots)),
]
INDEX_STEM = "S0_Package_Index_Sampling_Execution"
LOD_STEM = "PP-QC-SP-002_26-LOD-01_LoD_Execution_Record_T1_T2"
DAYS = (1,)          # Head of QC, 06.10.2026: all 46 batches sampled on one day, one oven run


def main():
    os.makedirs(OUT_S, exist_ok=True)
    os.makedirs(OUT_L, exist_ok=True)
    lots, bags = bc.load()
    lod_only = "--lod-only" in sys.argv
    docs = [(os.path.join(OUT_L, LOD_STEM + ".docx"), build_lod(1, lots))]
    if not lod_only:
        docs.append((os.path.join(OUT_S, INDEX_STEM + ".docx"), build_index(lots)))
        for day in DAYS:
            for _, stem, fn in SAMPLING_DOCS:
                docs.append((os.path.join(OUT_S, (stem % (day, day)) + ".docx"), fn(day, lots, bags)))
    ok = True
    for path, d in docs:
        bc.glyph_audit(d)
        pf.save(d, path)
        ok = bc.verify(path) and ok
    if not ok:
        raise SystemExit("pp_verify FAIL")
    print("written:", OUT_L if lod_only else (OUT_S, OUT_L))


if __name__ == "__main__":
    main()
