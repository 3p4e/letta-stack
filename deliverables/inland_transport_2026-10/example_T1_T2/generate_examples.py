"""Worked EXAMPLE of the inland-transport and transport-validation records for Tranche 1 and
Tranche 2, filled from the data on file and the calculations below.

Sources (repository):
  deliverables/qc_gap_analysis/tranche_assignment_2026-09-18.csv   which lots are in T1 / T2 (18.09 decision)
  deliverables/qc_gap_analysis/tracker/tranches_raw_2026-09-07.csv  kg per batch (owner's delivery list)
  deliverables/qc_gap_analysis/tracker/batch_dates.csv              P lot -> cultivation batch (sub-lots)

Nothing measured, signed or decided on the day is filled in. Dates, carrier and the bag mass are
EXAMPLE PARAMETERS, set once below and printed on the calculation sheet.

Usage: python3 generate_examples.py      (writes md/, docx/, pdf/ and the two merged PDFs here)
"""
import csv, math, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
QC = os.path.join(ROOT, "deliverables", "qc_gap_analysis")
TPL = os.path.join(HERE, "..", "md")
ENGINE = os.path.join(ROOT, "pp-document-suite", "scripts")
MD, DOCX, PDF = (os.path.join(HERE, x) for x in ("md", "docx", "pdf"))

# ------------------------------------------------------------------ example parameters
BAG_G = 1000            # nominal net mass per bag (g) — ASSUMPTION, not on file
BAGS_PER_CARTON = 10    # WHSOP_003 §6.4.2
L_CARTONS, S_CARTONS = 8, 4
TRAILER_PALLETS = 33    # Euro pallets, single-stacked, 13.6 m trailer
CARRIER = "Kuehne + Nagel (предвиден, да се потврди) | Kuehne + Nagel (provisional, to be confirmed)"
CONSIGNEE = "Versa (купувач според листата за продажба) | Versa (buyer per the sale list)"
CONSIGNEE_ADDR = "[адреса — да се внесе | address — to be entered]"
LANE = "L01"
PROTOCOL = "TVP-L01-26"
T = {
    "1": dict(utid="TR-20261020-001", date="20.10.2026", moia="16.10.2026", moh="23.10.2026", pq="1"),
    "2": dict(utid="TR-20261027-001", date="27.10.2026", moia="23.10.2026", moh="30.10.2026", pq="2"),
}
OQ_DATES = "13.10.2026 – 15.10.2026"
EX_NOTE = ("ПРИМЕР / СИМУЛАЦИЈА — пополнето со податоците што ги имаме и со пресметките од листот за "
           "калкулација; не е запис. Мерењата, потписите, броевите на пломби и логери и податоците што "
           "се дознаваат на денот се оставени празни. ||| EXAMPLE / SIMULATION — filled with the data we "
           "hold and the calculations on the calculation sheet; not a record. Measurements, signatures, "
           "seal and logger numbers and data known only on the day are left blank.")

# ------------------------------------------------------------------ data
def key(b): return b.replace("_", "").replace("/", "").upper()

def load():
    asg = [r for r in csv.DictReader(open(os.path.join(QC, "tranche_assignment_2026-09-18.csv"), encoding="utf-8"))
           if r["tranche"] in ("1", "2")]
    raw = {key(r["batch_printed"]): r for r in csv.DictReader(open(os.path.join(QC, "tracker", "tranches_raw_2026-09-07.csv"), encoding="utf-8"))}
    p2cu = {r["p_batch"]: r["cu_batch"] for r in csv.DictReader(open(os.path.join(QC, "tracker", "batch_dates.csv"), encoding="utf-8")) if r["p_batch"]}
    out = {"1": [], "2": []}
    for r in asg:
        cu = p2cu.get(r["p_lot"], r["batch"]) if r["p_lot"] else r["batch"]
        m = raw.get(key(cu)) or raw.get(key(r["batch"]))
        if m is None:
            sys.exit("no volume for " + r["batch"])
        g = round(float(m["volume_kg"]) * 1000)
        out[r["tranche"]].append(dict(p=r["p_lot"], cu=cu, strain=m["strain"], g=g))
    return out

def plan(lots, utid, two_vehicles):
    """Bags -> cartons (one batch per carton) -> pallets (8 cartons; remainder <=4 on a small pallet)."""
    cartons = []
    for lot in lots:
        nb = math.ceil(lot["g"] / BAG_G)
        masses = [BAG_G] * (nb - 1) + [lot["g"] - BAG_G * (nb - 1)]
        lot["bags"], lot["cartons"] = nb, math.ceil(nb / BAGS_PER_CARTON)
        for c in range(lot["cartons"]):
            seg = masses[c * 10:(c + 1) * 10]
            cartons.append(dict(lot=lot, first=c * 10 + 1, last=c * 10 + len(seg), bags=len(seg), g=sum(seg), masses=seg))
    pallets, i = [], 0
    while i < len(cartons):
        rest = len(cartons) - i
        n = L_CARTONS if rest > S_CARTONS else rest
        typ = "G" if (n > S_CARTONS or rest > S_CARTONS) else "M"
        chunk = cartons[i:i + n]; i += n
        pid = "%s-P%02d" % (utid, len(pallets) + 1)
        for j, c in enumerate(chunk, 1):
            c["id"] = "%s-C%02d" % (pid, j); c["pallet"] = pid
        pallets.append(dict(id=pid, type=typ, cartons=chunk, bags=sum(c["bags"] for c in chunk), g=sum(c["g"] for c in chunk)))
    if two_vehicles:
        half = math.ceil(len(pallets) / 2)
        for k, p in enumerate(pallets): p["veh"] = "V1" if k < half else "V2"
    else:
        for p in pallets: p["veh"] = "V1"
    return cartons, pallets

def fmt_g(g): return f"{g:,}".replace(",", " ")
def fmt_kg(g): return f"{g/1000:,.2f}".replace(",", " ").replace(".", ",") + " kg"
def lotname(l): return (l["p"] + " / " + l["cu"]) if l["p"] else l["cu"]
def lotbatches(p): return ", ".join(dict.fromkeys(lotname(c["lot"]) for c in p["cartons"]))

# ------------------------------------------------------------------ template filling
def tpl(name): return open(os.path.join(TPL, name + ".md"), encoding="utf-8").read()

def head(md, mk_suffix, en_suffix):
    md = re.sub(r"(mk_title: .*)", lambda m: m.group(1) + mk_suffix, md, 1)
    md = re.sub(r"(en_title: .*)", lambda m: m.group(1) + en_suffix, md, 1)
    return md.replace("-->\n", "-->\n\n" + EX_NOTE + "\n", 1)

def field(md, label, value, n=1):
    pat = re.compile(r"^(" + re.escape(label) + r" \|\|\| [^\n]*?\|\|\| )[^\n]*$", re.M)
    ms = list(pat.finditer(md))
    if len(ms) < n: raise KeyError(label)
    m = ms[n - 1]
    return md[:m.start()] + m.group(1) + value + md[m.end():]

def table(md, header_prefix, rows):
    i = md.index("\n" + header_prefix) + 1
    j = md.index("\n", i)
    k = md.index("[[/TABLE]]", j)
    body = "\n".join(" ||| ".join(str(c) for c in r) for r in rows)
    return md[:j + 1] + body + "\n" + md[k:]

def tick(md, option):
    if ("☐ " + option) not in md: raise KeyError(option)
    return md.replace("☐ " + option, "☒ " + option, 1)

def write(name, md):
    open(os.path.join(MD, name + ".md"), "w", encoding="utf-8").write(md)

MATERIAL = "Сув цвет од канабис, ринфуз~~Dried cannabis flower, bulk"

# ------------------------------------------------------------------ transport records (WHSOP_003)
def transport_set(tr, lots, cartons, pallets):
    P = T[tr]; nL = sum(p["type"] == "G" for p in pallets); nS = len(pallets) - nL
    veh = sorted(set(p["veh"] for p in pallets))
    vtxt = ("V1: " + pallets[0]["id"][-3:] + "–" + [p for p in pallets if p["veh"] == "V1"][-1]["id"][-3:] +
            ("; V2: " + [p for p in pallets if p["veh"] == "V2"][0]["id"][-3:] + "–" + pallets[-1]["id"][-3:] if "V2" in veh else ""))
    tot_bags = sum(l["bags"] for l in lots); tot_c = len(cartons); tot_g = sum(l["g"] for l in lots)
    sfx = (" — Т%s (пример)" % tr, " — T%s (example)" % tr)
    lot_rows = [[i, lotname(l), l["bags"], l["cartons"], fmt_g(l["g"]), "15–25 °C, RH ≤ 60 %"] for i, l in enumerate(lots, 1)]
    lot_rows.append(["Вкупно~~Total", "%d серии~~%d batches" % (len(lots), len(lots)), tot_bags, tot_c, fmt_g(tot_g), ""])

    # A01 TRA
    md = head(tpl("WHSOP_003_A01"), *sfx)
    for lab, val in [("UTID", P["utid"]), ("Датум на транспорт", P["date"]), ("Иницијатор", "Логистика | Logistics"),
                     ("Рута (код од QASOP_0XX_A06)", LANE), ("Статус на рутата", "IN QUALIFICATION — PQ-%s; исклучителна мерка преку контрола на промени | exceptional measure via change control" % P["pq"]),
                     ("Важи до", "— (во квалификација | in qualification)"),
                     ("Место на испраќање", "Пјурли Плант, Којлија 1043, Петровец | Purely Plant, Kojlija 1043, Petrovec"),
                     ("Примач и адреса", CONSIGNEE + "; " + CONSIGNEE_ADDR), ("Превозник", CARRIER),
                     ("Палети G (8 картони)", str(nL)), ("Палети M (4 картони)", str(nS)),
                     ("Логери за еднократна употреба", "%d (PQ: 2 по палета, Е1 + Е2) | %d (PQ: 2 per pallet, E1 + E2)" % (2 * len(pallets), 2 * len(pallets))),
                     ("USB логер (сериски број)", "%d USB по возило (PQ: жешка, студена точка, амбиент); броеви при извршување | %d USB per vehicle (PQ: hot, cold spot, ambient); numbers at execution" % (3, 3)),
                     ("Распоред на палетите во возилото (скица или опис; позиција на USB логерот)",
                      "%d палети на подот, во еден слој, без допир со ѕидовите и вратите; %s; USB логери на жешката и студената точка од OQ | %d pallets on the floor, single layer, clear of walls and doors; %s; USB loggers at the OQ hot and cold spots" % (len(pallets), vtxt, len(pallets), vtxt)),
                     ("Место и време на почеток на придружувањето", "Којлија 1043, Петровец, %s, 07:30 (предлог) | Kojlija 1043, Petrovec, %s, 07:30 (proposed)" % (P["date"], P["date"]))]:
        md = field(md, lab, val)
    if len(veh) > 1:
        md = field(md, "Возило (регистарски број)", "2 возила (V1, V2), во иста колона под исто придружување | 2 vehicles (V1, V2), one convoy under one escort")
    md = tick(md, "Меѓупроизвод | Intermediate")
    md = table(md, "№ ||| Серија~~Batch ||| Кеси~~Bags", lot_rows)
    score = {1: (1, 3), 2: (1, 2), 3: (2, 2), 4: (2, 3), 5: (1, 2), 6: (2, 2), 7: (1, 2), 8: (2, 3), 9: (2, 2), 10: (1, 3)}
    def rsk(m):
        n = int(m.group(1)); L, C = score.get(n, (None, None))
        if L is None: return m.group(0)
        res = "Низок | Low" if L * C < 6 else "Низок по мерката | Low after the measure"
        return "%d ||| %s ||| %d ||| %d ||| %d ||| %s ||| %s" % (n, m.group(2), L, C, L * C, m.group(3), res)
    md = re.sub(r"^(\d+) \|\|\| ([^\n|]+?) \|\|\|  \|\|\|  \|\|\|  \|\|\| ([^\n]+?) \|\|\| $", rsk, md, flags=re.M)
    md = md.replace("Секој ризик се оценува", "Оценките се предлог за обука; ги потврдува QA. Секој ризик се оценува", 1)
    md = md.replace("Each risk is scored", "The scores are a proposal for training; QA confirms them. Each risk is scored", 1)
    write("T%s_WHSOP_003_A01" % tr, md)

    # A02 MoIA escort request
    md = head(tpl("WHSOP_003_A02"), *sfx)
    for lab, val in [("Наш број / UTID", P["utid"]), ("Датум на поднесување (≥ 24 h пред поаѓање)", P["moia"] + " (планирано | planned)"),
                     ("Датум на поаѓање", P["date"]), ("Време на поаѓање", "08:00 (планирано | planned)"),
                     ("Место на прием", CONSIGNEE_ADDR), ("Примач", CONSIGNEE), ("Адреса на примачот", CONSIGNEE_ADDR),
                     ("Намена", "Испорака на меѓупроизвод според договорот за продажба — Транша %s | Delivery of intermediate under the sales contract — Tranche %s" % (tr, tr)),
                     ("Предложено место и време на почеток на придружувањето", "Којлија 1043, Петровец, %s, 07:30 | Kojlija 1043, Petrovec, %s, 07:30" % (P["date"], P["date"])),
                     ("Број на палети (G / M)", "%d (G %d / M %d)" % (len(pallets), nL, nS)),
                     ("Превозник (назив, седиште)", CARRIER)]:
        md = field(md, lab, val)
    if len(veh) > 1:
        md = field(md, "Возило (марка, тип)", "2 возила во колона (V1, V2) | 2 vehicles in convoy (V1, V2)")
    md = tick(md, "лично | in person")
    md = table(md, "№ ||| Вид на материјал~~Material ||| Серија~~Batch ||| Кеси",
               [[i, MATERIAL, lotname(l), l["bags"], l["cartons"], fmt_g(l["g"])] for i, l in enumerate(lots, 1)] +
               [["Вкупно~~Total", "", "%d серии~~%d batches" % (len(lots), len(lots)), tot_bags, tot_c, fmt_g(tot_g)]])
    write("T%s_WHSOP_003_A02" % tr, md)

    # A03 labels and packing lists (one worked example of each + allocation of every carton)
    md = head(tpl("WHSOP_003_A03"), *sfx)
    p1, c1 = pallets[0], pallets[0]["cartons"][0]
    md = field(md, "UTID", P["utid"])
    md = field(md, "ID на палета", p1["id"])
    md = md.replace("☐ G — 8 картони | L — 8 cartons", "☒ G — 8 картони | L — 8 cartons", 1) if p1["type"] == "G" else md
    md = field(md, "Палета", "1 од | of %d" % len(pallets))
    md = field(md, "Број на картони / кеси", "%d / %d" % (len(p1["cartons"]), p1["bags"]))
    md = field(md, "Примач", CONSIGNEE + "; " + CONSIGNEE_ADDR)
    md = field(md, "ID на картон", c1["id"])
    md = field(md, "Картон", "1 од | of %d (на палетата | on the pallet)" % len(p1["cartons"]))
    md = field(md, "Серија", lotname(c1["lot"]))
    md = field(md, "Број на кеси", str(c1["bags"]))
    md = field(md, "Кеси бр. (од–до)", "%d–%d" % (c1["first"], c1["last"]))
    md = field(md, "Нето маса (g)", fmt_g(c1["g"]))
    md = re.sub(r"(# 4 Листа на пакување на картон[^\n]*\n\[\[FORM:grid\]\]\nID на картон \|\|\| Carton ID \|\|\| )[^\n]*", lambda m: m.group(1) + c1["id"], md)
    md = re.sub(r"(Датум \|\|\| Date \|\|\| )_", lambda m: m.group(1) + P["date"] + " (пакување | packing)", md, count=1)
    md = table(md, "№ ||| Серија~~Batch ||| Број на кеса~~Bag No.",
               [[k, lotname(c1["lot"]), c1["first"] + k - 1, fmt_g(gm), ""] for k, gm in enumerate(c1["masses"], 1)] +
               [["Вкупно~~Total", "", "%d кеси~~%d bags" % (c1["bags"], c1["bags"]), fmt_g(c1["g"]), ""]])
    md = re.sub(r"(# 5 Листа на пакување на палета[^\n]*\n\[\[FORM:grid\]\]\nID на палета \|\|\| Pallet ID \|\|\| )[^\n]*", lambda m: m.group(1) + p1["id"], md)
    md = table(md, "№ ||| ID на картон~~Carton ID ||| Серија~~Batch ||| Кеси~~Bags",
               [[c["id"][-3:], c["id"], lotname(c["lot"]), c["bags"], fmt_g(c["g"]), ""] for c in p1["cartons"]] +
               [["Вкупно~~Total", "", "", p1["bags"], fmt_g(p1["g"]), ""]])
    alloc = ["", "# 7 Распределба на сите картони | Allocation of all cartons",
             "Пресметана распределба (една серија по картон; G = 8 картони, остаток ≤ 4 на мала палета). Секој ред е еден картон со своја етикета и листа на пакување. ||| Calculated allocation (one batch per carton; L = 8 cartons, a remainder of ≤ 4 on a small pallet). Each row is one carton with its own label and packing list.",
             "[[TABLE]]", "ID на картон~~Carton ID ||| Возило~~Vehicle ||| Серија~~Batch ||| Кеси бр.~~Bags No. ||| Кеси~~Bags ||| Нето маса (g)~~Net mass (g)"]
    alloc += [" ||| ".join(map(str, [c["id"], next(p["veh"] for p in pallets if p["id"] == c["pallet"]), lotname(c["lot"]),
                                     "%d–%d" % (c["first"], c["last"]), c["bags"], fmt_g(c["g"])])) for c in cartons]
    alloc += [" ||| ".join(map(str, ["Вкупно~~Total", "", "%d картони~~%d cartons" % (tot_c, tot_c), "", tot_bags, fmt_g(tot_g)])), "[[/TABLE]]", ""]
    md = md.rstrip("\n") + "\n" + "\n".join(alloc)
    write("T%s_WHSOP_003_A03" % tr, md)

    # A04 manifest
    md = head(tpl("WHSOP_003_A04"), *sfx)
    for lab, val in [("UTID", P["utid"]), ("Датум", P["date"]), ("Рута (код)", LANE), ("TRA (референца)", "WHSOP_003_A01 — " + P["utid"]),
                     ("Примач", CONSIGNEE + "; " + CONSIGNEE_ADDR), ("Превозник", CARRIER),
                     ("Логери за еднократна употреба (број)", "%d (PQ-%s: Е1 + Е2 во секоја палета) | %d (PQ-%s: E1 + E2 in every pallet)" % (2 * len(pallets), P["pq"], 2 * len(pallets), P["pq"]))]:
        md = field(md, lab, val)
    if len(veh) > 1:
        md = field(md, "Возило (регистарски број)", "V1: ______ (%s) · V2: ______ (%s)" % (vtxt.split(";")[0][4:], vtxt.split(";")[1].strip()[4:]))
    md = table(md, "№ ||| ID на палета~~Pallet ID",
               [[k, p["id"] + (" (" + p["veh"] + ")" if len(veh) > 1 else ""), p["type"], len(p["cartons"]), p["bags"], fmt_g(p["g"]), "", "", ""] for k, p in enumerate(pallets, 1)] +
               [["Вкупно~~Total", "%d палети~~%d pallets" % (len(pallets), len(pallets)), "G %d / M %d" % (nL, nS), tot_c, tot_bags, fmt_g(tot_g), "", "", ""]])
    write("T%s_WHSOP_003_A04" % tr, md)

    # A05 checklist — executed on the day; only the identification is filled
    md = head(tpl("WHSOP_003_A05"), *sfx)
    for lab, val in [("UTID", P["utid"]), ("Датум", P["date"]), ("Рута (код)", LANE), ("Примач", CONSIGNEE)]:
        md = field(md, lab, val)
    write("T%s_WHSOP_003_A05" % tr, md)

    # A06 MoH report
    md = head(tpl("WHSOP_003_A06"), *sfx)
    for lab, val in [("Наш број / UTID", P["utid"]), ("Датум на поднесување (≤ 3 работни дена по транспортот)", "до | by " + P["moh"]),
                     ("Датум на извршен транспорт", P["date"]), ("Примач (назив и адреса)", CONSIGNEE + "; " + CONSIGNEE_ADDR),
                     ("Намена", "Испорака на меѓупроизвод — Транша %s | Delivery of intermediate — Tranche %s" % (tr, tr)),
                     ("Превозник, возило и возач", CARRIER)]:
        md = field(md, lab, val)
    md = table(md, "№ ||| Вид на материјал~~Material ||| Серија~~Batch ||| Палети",
               [[i, MATERIAL, lotname(l), "— / %d / %d" % (l["cartons"], l["bags"]), fmt_g(l["g"]), ""] for i, l in enumerate(lots, 1)] +
               [["Вкупно~~Total", "", "%d серии~~%d batches" % (len(lots), len(lots)), "%d / %d / %d" % (len(pallets), tot_c, tot_bags), fmt_g(tot_g), ""]])
    write("T%s_WHSOP_003_A06" % tr, md)

    # A07 QA review — identification only
    md = head(tpl("WHSOP_003_A07"), *sfx)
    for lab, val in [("UTID", P["utid"]), ("Датум на транспорт", P["date"]), ("Рута (код)", LANE)]:
        md = field(md, lab, val)
    write("T%s_WHSOP_003_A07" % tr, md)
    return dict(lots=len(lots), g=tot_g, bags=tot_bags, cartons=tot_c, pallets=len(pallets), L=nL, S=nS, veh=len(veh))

# ------------------------------------------------------------------ calculation sheet (front of the transport set)
def calc_sheet(data, summ):
    rows = []
    for tr in ("1", "2"):
        s = summ[tr]
        rows.append([("Т%s~~T%s" % (tr, tr)), T[tr]["utid"], T[tr]["date"], s["lots"], fmt_kg(s["g"]), s["bags"], s["cartons"],
                     "%d (G %d / M %d)" % (s["pallets"], s["L"], s["S"]), s["veh"], s["pallets"], 2 * s["pallets"], 3 * s["veh"]])
    md = ["<!--HEADERDATA", "mk_title: Калкулација на пратките — Транша 1 и Транша 2 (пример)",
          "en_title: Shipment Calculation — Tranche 1 and Tranche 2 (example)", "code: EX_T1T2_CALC", "version: 01",
          "doctype: FORM", "parent: WHSOP_003", "orient: landscape", "-->", "", EX_NOTE, "",
          "# 1 Параметри и претпоставки | Parameters and assumptions", "[[FORM]]",
          "Извор на сериите ||| Source of the batches ||| Транши T1 и T2 според одлуката од 18.09.2026 (tranche_assignment_2026-09-18.csv); маса по серија од листата на испораки (tranches_raw_2026-09-07.csv); подсериите се посебни серии | Tranches T1 and T2 per the decision of 18.09.2026; mass per batch from the delivery list; sub-lots are separate batches",
          "Нето маса на една кеса ||| Net mass of one bag ||| %d g — ПРЕТПОСТАВКА, не е на досие; ја менува пресметката на кеси, картони и палети | %d g — ASSUMPTION, not on file; it drives the bag, carton and pallet counts" % (BAG_G, BAG_G),
          "Пакување ||| Packaging ||| 10 кеси по картон; голема палета 8 картони, мала 4; една серија по картон | 10 bags per carton; large pallet 8 cartons, small 4; one batch per carton",
          "Капацитет на возило ||| Vehicle capacity ||| %d евро-палети во еден слој (приколка 13,6 m) | %d Euro pallets single-stacked (13.6 m trailer)" % (TRAILER_PALLETS, TRAILER_PALLETS),
          "Датуми ||| Dates ||| пример: OQ %s; Т1 %s; Т2 %s | example: OQ %s; T1 %s; T2 %s" % (OQ_DATES, T["1"]["date"], T["2"]["date"], OQ_DATES, T["1"]["date"], T["2"]["date"]),
          "Превозник и примач ||| Carrier and consignee ||| %s; %s" % (CARRIER.split(" | ")[1], CONSIGNEE.split(" | ")[1]),
          "[[/FORM]]", "", "# 2 Преглед | Overview", "[[TABLE]]",
          "Транша~~Tranche ||| UTID ||| Датум~~Date ||| Серии~~Batches ||| Нето маса~~Net mass ||| Кеси~~Bags ||| Картони~~Cartons ||| Палети~~Pallets ||| Возила~~Vehicles ||| Логери рутина~~Loggers routine ||| Логери PQ (Е1+Е2)~~Loggers PQ (E1+E2) ||| USB логери PQ~~USB loggers PQ"]
    md += [" ||| ".join(map(str, r)) for r in rows]
    tg = summ["1"]["g"] + summ["2"]["g"]
    md += [" ||| ".join(map(str, ["Вкупно~~Total", "", "", summ["1"]["lots"] + summ["2"]["lots"], fmt_kg(tg), summ["1"]["bags"] + summ["2"]["bags"],
                                   summ["1"]["cartons"] + summ["2"]["cartons"], summ["1"]["pallets"] + summ["2"]["pallets"], "", summ["1"]["pallets"] + summ["2"]["pallets"],
                                   2 * (summ["1"]["pallets"] + summ["2"]["pallets"]), ""])), "[[/TABLE]]", ""]
    for tr in ("1", "2"):
        lots = data[tr]
        md += ["# %d Серии во Т%s | Batches in T%s" % (2 + int(tr), tr, tr), "[[TABLE]]",
               "№ ||| P серија~~P lot ||| Културна серија~~Cultivation batch ||| Сорта~~Strain ||| Нето маса (g)~~Net mass (g) ||| Кеси~~Bags ||| Картони~~Cartons ||| Последен картон (кеси)~~Last carton (bags)"]
        md += [" ||| ".join(map(str, [i, l["p"] or "—", l["cu"], l["strain"], fmt_g(l["g"]), l["bags"], l["cartons"], l["bags"] - 10 * (l["cartons"] - 1)])) for i, l in enumerate(lots, 1)]
        md += [" ||| ".join(map(str, ["Вкупно~~Total", "", "", "", fmt_g(sum(l["g"] for l in lots)), sum(l["bags"] for l in lots), sum(l["cartons"] for l in lots), ""])), "[[/TABLE]]", ""]
    md += ["# 5 Што треба да се одлучи | What must be decided", "[[TABLE]]", "№ ||| Прашање~~Question ||| Зошто~~Why",
           "1 ||| Вистинската нето маса по кеса~~The actual net mass per bag ||| ги менува сите бројки на картони, палети и логери~~it changes every carton, pallet and logger count",
           "2 ||| Т2 бара %d палети — две возила~~T2 needs %d pallets — two vehicles ||| над %d палети во едно возило~~more than %d pallets in one vehicle" % (summ["2"]["pallets"], summ["2"]["pallets"], TRAILER_PALLETS, TRAILER_PALLETS),
           "3 ||| Логери за PQ: %d за еднократна употреба~~PQ loggers: %d single-use ||| располагаме со нешто над 100~~we hold a little over 100" % (2 * (summ["1"]["pallets"] + summ["2"]["pallets"]), 2 * (summ["1"]["pallets"] + summ["2"]["pallets"])),
           "4 ||| OQ пред Т1~~OQ before T1 ||| PQ не смее да почне без одобрена OQ (QASOP_0XX §6.1)~~PQ must not start without an approved OQ (QASOP_0XX §6.1)",
           "5 ||| Последните картони на серијата не се полни~~The last carton of a batch is not full ||| една серија по картон; бројот на кеси е на етикетата~~one batch per carton; the bag count is on the label",
           "6 ||| Адреса на примачот и рута~~Consignee address and route ||| потребни за барањето до МВР и за TRA~~needed for the MoIA request and the TRA",
           "[[/TABLE]]", ""]
    write("T0_CALCULATION", "\n".join(md))

# ------------------------------------------------------------------ validation records (QASOP_0XX)
def validation_set(data, plans, summ):
    md = head(tpl("QASOP_0XX_A01"), " — L01 (пример)", " — L01 (example)")
    for lab, val in [("Код на рутата", LANE), ("Број на проект за валидација", PROTOCOL), ("Место на прием", CONSIGNEE + "; " + CONSIGNEE_ADDR),
                     ("Превозник", CARRIER), ("Максимален товар: палети G / M", "%d по возило (Т1); Т2 во две возила | %d per vehicle (T1); T2 in two vehicles" % (summ["1"]["pallets"], summ["1"]["pallets"])),
                     ("Картони / кеси / маса (kg)", "Т1: %d / %d / %s; Т2: %d / %d / %s" % (summ["1"]["cartons"], summ["1"]["bags"], fmt_kg(summ["1"]["g"]), summ["2"]["cartons"], summ["2"]["bags"], fmt_kg(summ["2"]["g"]))),
                     ("Симулиран товар (кеси со иста маса и материјал)", "OQ: %d G-палети со кеси од %d g во картони, завиткани како во рутина | OQ: %d L pallets with %d g bags in cartons, wrapped as in routine" % (summ["1"]["pallets"], BAG_G, summ["1"]["pallets"], BAG_G)),
                     ("Логери: USB (10) / за еднократна употреба (број)", "10 / OQ %d, PQ-1 %d, PQ-2 %d" % (2 * summ["1"]["pallets"], 2 * summ["1"]["pallets"], 2 * summ["2"]["pallets"])),
                     ("Извор на климатските податоци", "Управа за хидрометеоролошки работи (УХМР), Скопје | National Hydrometeorological Service, Skopje"),
                     ("Образложение за групирање / обем", "Целосна OQ + PQ. OQ (%s) на возилото на превозникот пред Т1; PQ-1 = Т1 (%s), PQ-2 = Т2 (%s), PQ-3 = следната пратка. Т1 и Т2 се изведуваат додека рутата е во квалификација, по исклучителна мерка одобрена од QA (WHSOP_003 §6.2.2) | Full OQ + PQ. OQ (%s) on the carrier's vehicle before T1; PQ-1 = T1 (%s), PQ-2 = T2 (%s), PQ-3 = the next shipment. T1 and T2 run while the lane is in qualification, under a QA-approved exceptional measure (WHSOP_003 §6.2.2)" % (OQ_DATES, T["1"]["date"], T["2"]["date"], OQ_DATES, T["1"]["date"], T["2"]["date"])),
                     ("Планиран почеток и крај", "%s — PQ-3 | %s — PQ-3" % (OQ_DATES.split(" – ")[0], OQ_DATES.split(" – ")[0]))]:
        md = field(md, lab, val)
    md = tick(md, "Готов производ / меѓупроизвод (15–25 °C, RH ≤ 60 %) | Finished product / intermediate (15–25 °C, RH ≤ 60 %)")
    md = tick(md, "Целосна OQ + PQ | Full OQ + PQ")
    write("V1_QASOP_0XX_A01", md)

    # A03 OQ record — prepared before T1 (configuration filled, results blank)
    md = head(tpl("QASOP_0XX_A03"), " — L01 (пример)", " — L01 (example)")
    for lab, val in [("Код на рутата", LANE), ("Протокол (QASOP_0XX_A02) бр.", PROTOCOL), ("Превозник / возило (регистарски број)", CARRIER.split(" | ")[0] + " / ______"),
                     ("Палети G / M", "%d / 0 (симулиран товар | simulated load)" % summ["1"]["pallets"]), ("Сезона", "есен (октомври) | autumn (October)"),
                     ("Опсег", "15–25 °C, RH ≤ 60 %"), ("Датум на извршување", OQ_DATES)]:
        md = field(md, lab, val)
    md = table(md, "ID на палета~~Pallet ID ||| Тип G/M",
               [["OQ-P%02d" % k, "G", "ред %d, %s | row %d, %s" % ((k + 1) // 2, "лево" if k % 2 else "десно", (k + 1) // 2, "left" if k % 2 else "right"), "", "", ""] for k in range(1, summ["1"]["pallets"] + 1)])
    write("V2_QASOP_0XX_A03", md)

    # A04 PQ shipment records — T1 = PQ-1, T2 = PQ-2
    for tr, n in (("1", "1"), ("2", "2")):
        P = T[tr]; pallets = plans[tr][1]; s = summ[tr]
        md = head(tpl("QASOP_0XX_A04"), " — PQ-%s = Т%s (пример)" % (n, tr), " — PQ-%s = T%s (example)" % (n, tr))
        for lab, val in [("Код на рутата", LANE), ("Протокол бр.", PROTOCOL), ("UTID (WHSOP_003)", P["utid"]), ("Датум", P["date"]),
                         ("Сезона", "есен (октомври) | autumn (October)"), ("Палети G / M", "%d / %d" % (s["L"], s["S"])),
                         ("Превозник / возило", CARRIER.split(" | ")[0] + (" / V1, V2" if s["veh"] > 1 else " / ______"))]:
            md = field(md, lab, val)
        md = md.replace("☐ 1   ☐ 2   ☐ 3", "☐ 1   ☐ 2   ☐ 3".replace("☐ " + n, "☒ " + n), 1)
        md = tick(md, "Реален производ | Real product")
        md = table(md, "ID на палета~~Pallet ID ||| Тип G/M",
                   [[p["id"] + (" (" + p["veh"] + ")" if s["veh"] > 1 else ""), p["type"], "", "", "", "", "", ""] for p in pallets])
        write("V%d_QASOP_0XX_A04_PQ%s" % (2 + int(n), n), md)

    # A06 lane register — L01 row
    md = head(tpl("QASOP_0XX_A06"), " (пример)", " (example)")
    md = re.sub(r"^L01 \|\|\| [^\n]*$", lambda m: " ||| ".join([
        "L01", "Versa — " + CONSIGNEE_ADDR.split(" | ")[0], "меѓупроизвод 15–25 °C~~intermediate 15–25 °C",
        "Kuehne + Nagel (предв.) / G-палети~~Kuehne + Nagel (prov.) / L pallets", "", "", "", "IN QUALIFICATION", "—",
        "PQ-1 = Т1, PQ-2 = Т2~~PQ-1 = T1, PQ-2 = T2"]), md, count=1, flags=re.M)
    write("V5_QASOP_0XX_A06", md)

def protocol_docx():
    """Protocol A02 with its document-information block filled, built by the controlled builder."""
    sys.path.insert(0, os.path.join(HERE, ".."))
    sys.argv = [sys.argv[0], DOCX]
    import build_validation as bv
    bv.OUT = DOCX
    bv.info = lambda label: [
        ("Код на рутата | Lane code", LANE),
        ("Место на испраќање | Dispatch point", "Којлија 1043, Петровец | Kojlija 1043, Petrovec"),
        ("Место на прием | Receipt point", "Versa — " + CONSIGNEE_ADDR),
        ("Превозник / возило | Carrier / vehicle", "Kuehne + Nagel (предвиден | provisional) / ______"),
        ("Контрола на температура | Temperature control", "☐ Активна | Active   ☐ Пасивна | Passive"),
        ("Конфигурација на палети | Pallet configuration", "G 8 / M 4 картони × 10 кеси | L 8 / S 4 cartons × 10 bags"),
        ("Опсег | Range", "15–25 °C, RH ≤ 60 %"),
        ("План за валидација | Validation plan", "QASOP_0XX_A01 — " + PROTOCOL),
        ("Поврзана СОП | Governing SOP", "QASOP_0XX; WHSOP_003"),
        (label, PROTOCOL)]
    bv.protocol()
    os.replace(os.path.join(DOCX, "QASOP_0XX_A02.docx"), os.path.join(DOCX, "V1b_QASOP_0XX_A02.docx"))

# ------------------------------------------------------------------ build
def main():
    for d in (MD, DOCX, PDF): os.makedirs(d, exist_ok=True)
    data = load()
    plans, summ = {}, {}
    for tr in ("1", "2"):
        cartons, pallets = plan(data[tr], T[tr]["utid"], two_vehicles=False)
        if len(pallets) > TRAILER_PALLETS:
            cartons, pallets = plan(data[tr], T[tr]["utid"], two_vehicles=True)
        plans[tr] = (cartons, pallets)
        summ[tr] = transport_set(tr, data[tr], cartons, pallets)
    calc_sheet(data, summ)
    validation_set(data, plans, summ)
    eng = [sys.executable, os.path.join(ENGINE, "build_from_md.py")]
    for f in sorted(os.listdir(MD)):
        subprocess.run(eng + [os.path.join(MD, f), os.path.join(DOCX, f[:-3] + ".docx")], check=True, stdout=subprocess.DEVNULL)
    protocol_docx()
    for f in sorted(os.listdir(DOCX)):
        r = subprocess.run([sys.executable, os.path.join(ENGINE, "pp_verify.py"), os.path.join(DOCX, f)], capture_output=True, text=True)
        print(f, r.stdout.strip().splitlines()[-1])
    print({k: v for k, v in summ.items()})

if __name__ == "__main__":
    main()
