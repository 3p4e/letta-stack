"""Worked EXAMPLE of the inland-transport and transport-validation records for Tranche 1 and
Tranche 2, filled from the data on file and the calculations below.

Sources (repository):
  deliverables/qc_gap_analysis/tranche_assignment_2026-09-18.csv   which lots are in T1 / T2 (18.09 decision)
  deliverables/qc_gap_analysis/tracker/tranches_raw_2026-09-07.csv  kg per batch (owner's delivery list)
  deliverables/qc_gap_analysis/tracker/batch_dates.csv              P lot -> cultivation batch (sub-lots)
  Head of QC, 09.10.2026: IMB bags are 401.0 g ± 3 %.

Every entry is written in brackets and coloured (legend on the calculation sheet):
  blue   [ ... ]  data from our records or calculated from them
  purple [ ... ]  example value — to be confirmed
  orange [   ]    to be entered on the day (measurements, signatures, seal and logger numbers ...)

Usage: python3 generate_examples.py      (writes md/ and docx/; the docx are coloured in place)
"""
import copy, csv, math, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
QC = os.path.join(ROOT, "deliverables", "qc_gap_analysis")
TPL = os.path.join(HERE, "..", "md")
ENGINE = os.path.join(ROOT, "pp-document-suite", "scripts")
MD, DOCX, PDF = (os.path.join(HERE, x) for x in ("md", "docx", "pdf"))

# ------------------------------------------------------------------ parameters
BAG_G, BAG_TOL = 401.0, 0.03          # IMB bag, Head of QC 09.10.2026
BAGS_PER_CARTON = 10                  # WHSOP_003 §6.4.2
L_CARTONS, S_CARTONS = 8, 4
TRAILER_PALLETS = 33                  # Euro pallets, single-stacked, 13.6 m trailer
SAMPLES_PER_LOT = (("купувач", "buyer"), ("продавач на мало", "retailer"))
LANE, PROTOCOL = "L01", "TVP-L01-26"
T = {"1": dict(utid="TR-20261020-001", date="20.10.2026", moia="16.10.2026", moh="23.10.2026", pq="1"),
     "2": dict(utid="TR-20261027-001", date="27.10.2026", moia="23.10.2026", moh="30.10.2026", pq="2")}
OQ_DATES = "13.10.2026 – 15.10.2026"
EX_NOTE = ("ПРИМЕР / СИМУЛАЦИЈА — не е запис. Сите внесени податоци се во загради: сино — од нашите записи "
           "или пресметани; виолетово — пример, да се потврди; портокалово — се внесува на денот. "
           "||| EXAMPLE / SIMULATION — not a record. Every entry is in brackets: blue — from our records or "
           "calculated; purple — example, to be confirmed; orange — entered on the day.")

# ------------------------------------------------------------------ bracketing
ASSUME = set()
def _wrap(v):
    v = str(v)
    if "~~" in v:
        a, b = v.split("~~", 1); return "[%s]~~[%s]" % (a, b)
    return "[%s]" % v
def B(v):                                   # data from records / calculation (blue)
    return _wrap(v)
def A(v):                                   # example value to confirm (purple)
    v = str(v)
    for part in v.split("~~"): ASSUME.add(part.strip())
    return _wrap(v)
TBE = "[ ]"                                 # to be entered on the day (orange)

CARRIER = "Kuehne + Nagel (предвиден) | Kuehne + Nagel (provisional)"
CONSIGNEE = "Versa (купувач според листата за продажба) | Versa (buyer per the sale list)"

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
        m = raw.get(key(cu)) or raw.get(key(cu.rstrip("*")))   # recorded star alias of the same lot only; never the parent lot
        if m is None: sys.exit("no volume for " + r["batch"])
        out[r["tranche"]].append(dict(p=r["p_lot"], cu=cu, strain=m["strain"], g=round(float(m["volume_kg"]) * 1000)))
    return out

def plan(lots, utid):
    """Bags of 401.0 g -> cartons (one batch per carton) -> pallets (8 cartons; a remainder of <=4 on a
    small pallet) -> vehicles of at most 33 pallets, balanced."""
    cartons = []
    for lot in lots:
        n = max(1, round(lot["g"] / BAG_G))
        lot["avg"] = lot["g"] / n
        lot["in_tol"] = abs(lot["avg"] - BAG_G) <= BAG_G * BAG_TOL
        if lot["in_tol"]:
            masses = [lot["avg"]] * n
        else:   # full 401.0 g bags and one partial last bag, never a bag outside 401.0 g ± 3 %
            full = int(lot["g"] // BAG_G)
            masses = [BAG_G] * full + ([lot["g"] - full * BAG_G] if lot["g"] - full * BAG_G > 0 else [])
            n = len(masses); lot["avg"] = lot["g"] / n
        lot["bags"] = n
        lot["cartons"] = math.ceil(n / BAGS_PER_CARTON)
        done = 0
        for c in range(lot["cartons"]):
            nb = min(BAGS_PER_CARTON, n - c * BAGS_PER_CARTON)
            g = round(sum(masses[:c * BAGS_PER_CARTON + nb])) - done; done += g
            cartons.append(dict(lot=lot, first=c * BAGS_PER_CARTON + 1, last=c * BAGS_PER_CARTON + nb, bags=nb, g=g))
    pallets, i = [], 0
    while i < len(cartons):
        rest = len(cartons) - i
        n = L_CARTONS if rest > S_CARTONS else rest
        typ = "G" if n > S_CARTONS else "M"
        chunk = cartons[i:i + n]; i += n
        pid = "%s-P%02d" % (utid, len(pallets) + 1)
        for j, c in enumerate(chunk, 1): c["id"], c["pallet"] = "%s-C%02d" % (pid, j), pid
        pallets.append(dict(id=pid, type=typ, cartons=chunk, bags=sum(c["bags"] for c in chunk), g=sum(c["g"] for c in chunk)))
    nv = math.ceil(len(pallets) / TRAILER_PALLETS)
    sizes = [len(pallets) // nv + (1 if k < len(pallets) % nv else 0) for k in range(nv)]
    k = 0
    for v, sz in enumerate(sizes, 1):
        for p in pallets[k:k + sz]: p["veh"] = "V%d" % v
        k += sz
    return cartons, pallets, nv

def fmt_g(g): return f"{round(g):,}".replace(",", " ")
def fmt_kg(g): return f"{g/1000:,.2f}".replace(",", " ").replace(".", ",") + " kg"
def lotname(l): return (l["p"] + " / " + l["cu"]) if l["p"] else l["cu"]
def veh_ranges(pallets):
    out = []
    for v in sorted(set(p["veh"] for p in pallets), key=lambda x: int(x[1:])):
        ps = [p for p in pallets if p["veh"] == v]
        out.append("%s: %s–%s (%d)" % (v, ps[0]["id"][-3:], ps[-1]["id"][-3:], len(ps)))
    return "; ".join(out)

# ------------------------------------------------------------------ template filling
def tpl(name): return open(os.path.join(TPL, name + ".md"), encoding="utf-8").read()

def head(md, mk_suffix, en_suffix):
    md = re.sub(r"(mk_title: .*)", lambda m: m.group(1) + mk_suffix, md, count=1)
    md = re.sub(r"(en_title: .*)", lambda m: m.group(1) + en_suffix, md, count=1)
    return md.replace("-->\n", "-->\n\n" + EX_NOTE + "\n", 1)

def field(md, label, value, n=1):
    pat = re.compile(r"^(" + re.escape(label) + r" \|\|\| [^\n]*?\|\|\| )[^\n]*$", re.M)
    ms = list(pat.finditer(md))
    if len(ms) < n: raise KeyError(label)
    m = ms[n - 1]
    return md[:m.start()] + m.group(1) + value + md[m.end():]

def table(md, header_prefix, rows):
    i = md.index("\n" + header_prefix) + 1
    j = md.index("\n", i); k = md.index("[[/TABLE]]", j)
    return md[:j + 1] + "\n".join(" ||| ".join(str(c) for c in r) for r in rows) + "\n" + md[k:]

def tick(md, option):
    if ("☐ " + option) not in md: raise KeyError(option)
    return md.replace("☐ " + option, "☒ " + option, 1)

TOTAL = "Вкупно~~Total"

def placeholders(md):
    """Every field still empty becomes an orange [ ] — form values, empty table cells, ___ gaps."""
    out, mode, first = [], None, False
    for ln in md.split("\n"):
        s = ln.strip()
        if s.startswith("[[TABLE"): mode, first = "table", True; out.append(ln); continue
        if s.startswith("[[FORM"): mode = "form"; out.append(ln); continue
        if s.startswith("[[/"): mode = None; out.append(ln); continue
        if mode and "|||" in ln:
            cells = [c.strip() for c in ln.split("|||")]
            if mode == "form":
                v = cells[2] if len(cells) > 2 else ""
                if v in ("", "_") or re.fullmatch(r"(TR-_+-_+.*|L__)", v): v = TBE
                v = re.sub(r"_{3,}", "[ ]", v)
                cells = cells[:2] + [v]
            elif first:
                first = False
            else:
                cells = [c if c else TBE for c in cells]
                cells = [re.sub(r"_{3,}", "[ ]", c) for c in cells]
            ln = " ||| ".join(cells)
        out.append(ln)
    return "\n".join(out)

def write(name, md):
    open(os.path.join(MD, name + ".md"), "w", encoding="utf-8").write(placeholders(md))

MATERIAL = "Сув цвет од канабис, ринфуз~~Dried cannabis flower, bulk"
RANGE = "15–25 °C, RH ≤ 60 %"

def lot_rows(lots):
    rows = [[i, B(lotname(l)), B(l["bags"]), B(l["cartons"]), B(fmt_g(l["g"])), RANGE] for i, l in enumerate(lots, 1)]
    rows.append([TOTAL, B("%d серии~~%d batches" % (len(lots), len(lots))), B(sum(l["bags"] for l in lots)),
                 B(sum(l["cartons"] for l in lots)), B(fmt_g(sum(l["g"] for l in lots))), "—"])
    return rows

# ------------------------------------------------------------------ transport records (WHSOP_003)
def transport_set(tr, lots, cartons, pallets, nv):
    P = T[tr]; nL = sum(p["type"] == "G" for p in pallets); nS = len(pallets) - nL
    vr = veh_ranges(pallets); ns = len(SAMPLES_PER_LOT) * len(lots)
    tot_bags, tot_c, tot_g = sum(l["bags"] for l in lots), len(cartons), sum(l["g"] for l in lots)
    sfx = (" — Т%s (пример)" % tr, " — T%s (example)" % tr)
    date, utid = A(P["date"]), B(P["utid"])
    sample_txt = B("%d мостри (%d серии × купувач + продавач на мало) | %d samples (%d batches × buyer + retailer)" % (ns, len(lots), ns, len(lots)))

    # A01 TRA
    md = head(tpl("WHSOP_003_A01"), *sfx)
    for lab, val in [("UTID", utid), ("Датум на транспорт", date), ("Иницијатор", B("Логистика | Logistics")),
                     ("Рута (код од QASOP_0XX_A06)", B(LANE)),
                     ("Статус на рутата", A("IN QUALIFICATION — PQ-%s; исклучителна мерка преку контрола на промени | exceptional measure via change control" % P["pq"])),
                     ("Важи до", B("— (во квалификација | in qualification)")),
                     ("Место на испраќање", B("Пјурли Плант, Којлија 1043, Петровец | Purely Plant, Kojlija 1043, Petrovec")),
                     ("Примач и адреса", A(CONSIGNEE) + " · " + TBE), ("Превозник", A(CARRIER)),
                     ("Возило (регистарски број)", B("%d возила | %d vehicles" % (nv, nv)) + " · " + TBE),
                     ("Палети G (8 картони)", B(nL)), ("Палети M (4 картони)", B(nS)),
                     ("Логери за еднократна употреба", B("%d (PQ: 2 по палета, Е1 + Е2) | %d (PQ: 2 per pallet, E1 + E2)" % (2 * len(pallets), 2 * len(pallets)))),
                     ("USB логер (сериски број)", B("%d USB (по 3 на возило: жешка, студена точка, амбиент) | %d USB (3 per vehicle: hot, cold spot, ambient)" % (3 * nv, 3 * nv)) + " · " + TBE),
                     ("Распоред на палетите во возилото (скица или опис; позиција на USB логерот)",
                      B("палети на подот, во еден слој, без допир со ѕидовите и вратите; %s; картон со мостри RS во V1 | pallets on the floor, single layer, clear of walls and doors; %s; sample carton RS in V1" % (vr, vr))),
                     ("Место и време на почеток на придружувањето", A("Којлија 1043, Петровец, %s, 07:30 | Kojlija 1043, Petrovec, %s, 07:30" % (P["date"], P["date"])))]:
        md = field(md, lab, val)
    md = tick(md, "Меѓупроизвод | Intermediate")
    md = table(md, "№ ||| Серија~~Batch ||| Кеси~~Bags", lot_rows(lots))
    score = {1: (1, 3), 2: (1, 2), 3: (2, 2), 4: (2, 3), 5: (1, 2), 6: (2, 2), 7: (1, 2), 8: (2, 3), 9: (2, 2), 10: (1, 3)}
    def rsk(m):
        n = int(m.group(1)); L, C = score.get(n, (None, None))
        if L is None: return m.group(0)
        return "%d ||| %s ||| %s ||| %s ||| %s ||| %s ||| %s" % (n, m.group(2), A(L), A(C), A(L * C), m.group(3), A("Низок | Low"))
    md = re.sub(r"^(\d+) \|\|\| ([^\n|]+?) \|\|\|  \|\|\|  \|\|\|  \|\|\| ([^\n]+?) \|\|\| $", rsk, md, flags=re.M)
    md = md.replace("Секој ризик се оценува", "Оценките се предлог; ги потврдува QA. Секој ризик се оценува", 1)
    md = md.replace("Each risk is scored", "The scores are a proposal; QA confirms them. Each risk is scored", 1)
    write("T%s_WHSOP_003_A01" % tr, md)

    # A02 MoIA escort request
    md = head(tpl("WHSOP_003_A02"), *sfx)
    for lab, val in [("Наш број / UTID", utid), ("Датум на поднесување (≥ 24 h пред поаѓање)", A(P["moia"])),
                     ("Датум на поаѓање", date), ("Време на поаѓање", A("08:00")), ("Место на прием", TBE),
                     ("Примач", A(CONSIGNEE)), ("Адреса на примачот", TBE),
                     ("Намена", B("Испорака на меѓупроизвод според договорот за продажба — Транша %s | Delivery of intermediate under the sales contract — Tranche %s" % (tr, tr))),
                     ("Предложено место и време на почеток на придружувањето", A("Којлија 1043, Петровец, %s, 07:30 | Kojlija 1043, Petrovec, %s, 07:30" % (P["date"], P["date"]))),
                     ("Број на палети (G / M)", B("%d (G %d / M %d) во %d возила | %d (L %d / S %d) in %d vehicles" % (len(pallets), nL, nS, nv, len(pallets), nL, nS, nv))),
                     ("Ретенциони мостри (број / вкупна маса, g)", sample_txt + " / " + TBE),
                     ("Превозник (назив, седиште)", A(CARRIER)),
                     ("Возило (марка, тип)", B("%d возила во колона (%s) | %d vehicles in convoy (%s)" % (nv, vr, nv, vr)))]:
        md = field(md, lab, val)
    md = tick(md, "лично | in person")
    md = table(md, "№ ||| Вид на материјал~~Material ||| Серија~~Batch ||| Кеси",
               [[i, MATERIAL, B(lotname(l)), B(l["bags"]), B(l["cartons"]), B(fmt_g(l["g"]))] for i, l in enumerate(lots, 1)] +
               [[TOTAL, "—", B("%d серии~~%d batches" % (len(lots), len(lots))), B(tot_bags), B(tot_c), B(fmt_g(tot_g))]])
    write("T%s_WHSOP_003_A02" % tr, md)

    # A03 labels, packing lists, retention-sample list, allocation of every carton
    md = head(tpl("WHSOP_003_A03"), *sfx)
    p1, c1 = pallets[0], pallets[0]["cartons"][0]
    l1 = lots[0]
    boxes = {
        "Место за пример-етикета на палета (A5)": [
            ("UTID: " + utid + " · ID: " + B(p1["id"]), "Тип | Type: " + B("G / L" if p1["type"] == "G" else "M / S") + " · палета | pallet " + B("1") + " / " + B(len(pallets))),
            ("Картони / кеси | Cartons / bags: " + B("%d / %d" % (len(p1["cartons"]), p1["bags"])), ""),
            ("Испраќач | Consignor: " + B("Пјурли Плант ДООЕЛ Скопје, Којлија 1043, Петровец"), ""),
            ("Примач | Consignee: " + A(CONSIGNEE) + " · " + TBE, ""),
            ("15–25 °C, RH ≤ 60 % · ПРАТКА ПОД КОНТРОЛА — САМО ОВЛАСТЕН ТРАНСПОРТ", "CONTROLLED CONSIGNMENT — AUTHORISED TRANSPORT ONLY"),
            ("Број за итни случаи | Emergency number: " + TBE, "")],
        "Место за пример-етикета на картон (A6)": [
            ("ID: " + B(c1["id"]) + " · картон | carton " + B("1") + " / " + B(len(p1["cartons"])), ""),
            ("Серија | Batch: " + B(lotname(c1["lot"])) + " · кеси | bags " + B("%d–%d (%d)" % (c1["first"], c1["last"], c1["bags"])), ""),
            ("Нето маса | Net mass: " + B(fmt_g(c1["g"]) + " g") + " · лента | tape " + TBE + " · " + TBE, "")],
        "Место за пример-етикета на контејнер со ретенциона мостра": [
            ("РЕТЕНЦИОНА МОСТРА | RETENTION SAMPLE · " + B(lotname(l1)), ""),
            ("За | For: " + B("купувач | buyer") + " · нето маса | net mass " + TBE + " g · датум | date " + date, "")],
        "Место за пример-етикета на картон за мостри (RS)": [
            ("ID: " + B(P["utid"] + "-RS") + " · мостри | samples " + B(ns) + " · лента | tape " + TBE, ""),
            ("Примач | Consignee: " + A(CONSIGNEE) + " · ПРАТКА ПОД КОНТРОЛА | CONTROLLED CONSIGNMENT", "")],
    }
    for cap, lines in boxes.items():
        k = md.index(cap); e = md.index("[[/BOX]]", k); ln_end = md.index("\n", k)
        body = "\n".join((a + (" ||| " + b if b else "")) for a, b in lines)
        md = md[:ln_end + 1] + body + "\n" + md[e:]
    md = re.sub(r"(# 4 Листа на пакување на картон[^\n]*\n\[\[FORM:grid\]\]\nID на картон \|\|\| Carton ID \|\|\| )[^\n]*", lambda m: m.group(1) + B(c1["id"]), md)
    md = re.sub(r"(Датум \|\|\| Date \|\|\| )_", lambda m: m.group(1) + date, md, count=1)
    md = table(md, "№ ||| Серија~~Batch ||| Број на кеса~~Bag No.",
               [[k, B(lotname(c1["lot"])), B(c1["first"] + k - 1), TBE, TBE] for k in range(1, c1["bags"] + 1)] +
               [[TOTAL, "—", B("%d кеси~~%d bags" % (c1["bags"], c1["bags"])), B(fmt_g(c1["g"])), "—"]])
    md = re.sub(r"(# 5 Листа на пакување на палета[^\n]*\n\[\[FORM:grid\]\]\nID на палета \|\|\| Pallet ID \|\|\| )[^\n]*", lambda m: m.group(1) + B(p1["id"]), md)
    md = table(md, "№ ||| ID на картон~~Carton ID ||| Серија~~Batch ||| Кеси~~Bags",
               [[c["id"][-3:], B(c["id"]), B(lotname(c["lot"])), B(c["bags"]), B(fmt_g(c["g"])), TBE] for c in p1["cartons"]] +
               [[TOTAL, "—", "—", B(p1["bags"]), B(fmt_g(p1["g"])), "—"]])
    md = re.sub(r"(# 7 Листа на ретенциони мостри[^\n]*\n\[\[FORM:grid\]\]\nКартон за мостри \(ID\) \|\|\| Sample carton \(ID\) \|\|\| )[^\n]*", lambda m: m.group(1) + B(P["utid"] + "-RS"), md)
    srows, k = [], 0
    for l in lots:
        for mk, en in SAMPLES_PER_LOT:
            k += 1; srows.append([k, B(lotname(l)), B("%s~~%s" % (mk, en)), TBE, TBE, TBE])
    srows.append([TOTAL, B("%d серии~~%d batches" % (len(lots), len(lots))), B("%d мостри~~%d samples" % (ns, ns)), "—", TBE, "—"])
    md = table(md, "№ ||| Серија~~Batch ||| За~~For", srows)
    alloc = ["", "# 8 Распределба на сите картони | Allocation of all cartons",
             "Пресметана распределба: кеси од 401,0 g ± 3 %, една серија по картон, G = 8 картони, остаток ≤ 4 на мала палета, најмногу 33 палети по возило. Секој ред е еден картон со своја етикета и листа на пакување; масата на картонот е пресметана од масата на серијата. ||| Calculated allocation: bags of 401.0 g ± 3 %, one batch per carton, L = 8 cartons, a remainder of ≤ 4 on a small pallet, at most 33 pallets per vehicle. Each row is one carton with its own label and packing list; the carton mass is calculated from the batch mass.",
             "[[TABLE]]", "ID на картон~~Carton ID ||| Возило~~Vehicle ||| Серија~~Batch ||| Кеси бр.~~Bags No. ||| Кеси~~Bags ||| Нето маса (g)~~Net mass (g)"]
    pv = {p["id"]: p["veh"] for p in pallets}
    alloc += [" ||| ".join(map(str, [B(c["id"]), B(pv[c["pallet"]]), B(lotname(c["lot"])), B("%d–%d" % (c["first"], c["last"])), B(c["bags"]), B(fmt_g(c["g"]))])) for c in cartons]
    alloc += [" ||| ".join(map(str, [TOTAL, "—", B("%d картони~~%d cartons" % (tot_c, tot_c)), "—", B(tot_bags), B(fmt_g(tot_g))])), "[[/TABLE]]", ""]
    md = md.rstrip("\n") + "\n" + "\n".join(alloc)
    write("T%s_WHSOP_003_A03" % tr, md)

    # A04 manifest
    md = head(tpl("WHSOP_003_A04"), *sfx)
    for lab, val in [("UTID", utid), ("Датум", date), ("Рута (код)", B(LANE)), ("TRA (референца)", B("WHSOP_003_A01 — " + P["utid"])),
                     ("Примач", A(CONSIGNEE) + " · " + TBE), ("Превозник", A(CARRIER)),
                     ("Возило (регистарски број)", B(vr) + " · " + TBE),
                     ("Картон со ретенциони мостри (ID)", B(P["utid"] + "-RS")),
                     ("Мостри: купувач / продавач на мало", B("%d / %d" % (len(lots), len(lots)))),
                     ("Логери за еднократна употреба (број)", B("%d (PQ-%s: Е1 + Е2 во секоја палета) | %d (PQ-%s: E1 + E2 in every pallet)" % (2 * len(pallets), P["pq"], 2 * len(pallets), P["pq"])))]:
        md = field(md, lab, val)
    md = table(md, "№ ||| ID на палета~~Pallet ID",
               [[k, B("%s (%s)" % (p["id"], p["veh"])), B(p["type"]), B(len(p["cartons"])), B(p["bags"]), B(fmt_g(p["g"])), TBE, TBE, TBE] for k, p in enumerate(pallets, 1)] +
               [[TOTAL, B("%d палети~~%d pallets" % (len(pallets), len(pallets))), B("G %d / M %d" % (nL, nS)), B(tot_c), B(tot_bags), B(fmt_g(tot_g)), "—", "—", TBE]])
    write("T%s_WHSOP_003_A04" % tr, md)

    # A05 checklist — executed on the day
    md = head(tpl("WHSOP_003_A05"), *sfx)
    for lab, val in [("UTID", utid), ("Датум", date), ("Рута (код)", B(LANE)), ("Примач", A(CONSIGNEE))]:
        md = field(md, lab, val)
    write("T%s_WHSOP_003_A05" % tr, md)

    # A06 MoH report
    md = head(tpl("WHSOP_003_A06"), *sfx)
    for lab, val in [("Наш број / UTID", utid), ("Датум на поднесување (≤ 3 работни дена по транспортот)", A(P["moh"])),
                     ("Датум на извршен транспорт", date), ("Примач (назив и адреса)", A(CONSIGNEE) + " · " + TBE),
                     ("Намена", B("Испорака на меѓупроизвод — Транша %s | Delivery of intermediate — Tranche %s" % (tr, tr))),
                     ("Превозник, возило и возач", A(CARRIER) + " · " + TBE),
                     ("Ретенциони мостри вклучени во количината (број / g)", sample_txt + " / " + TBE)]:
        md = field(md, lab, val)
    md = table(md, "№ ||| Вид на материјал~~Material ||| Серија~~Batch ||| Палети",
               [[i, MATERIAL, B(lotname(l)), B("— / %d / %d" % (l["cartons"], l["bags"])), B(fmt_g(l["g"])), TBE] for i, l in enumerate(lots, 1)] +
               [[TOTAL, "—", B("%d серии~~%d batches" % (len(lots), len(lots))), B("%d / %d / %d" % (len(pallets), tot_c, tot_bags)), B(fmt_g(tot_g)), TBE]])
    write("T%s_WHSOP_003_A06" % tr, md)

    # A07 QA review
    md = head(tpl("WHSOP_003_A07"), *sfx)
    for lab, val in [("UTID", utid), ("Датум на транспорт", date), ("Рута (код)", B(LANE))]:
        md = field(md, lab, val)
    write("T%s_WHSOP_003_A07" % tr, md)
    return dict(lots=len(lots), g=tot_g, bags=tot_bags, cartons=tot_c, pallets=len(pallets), L=nL, S=nS, veh=nv, samples=ns,
                maxveh=max(sum(1 for p in pallets if p["veh"] == v) for v in set(p["veh"] for p in pallets)))

# ------------------------------------------------------------------ calculation sheet
def calc_sheet(data, summ):
    s1, s2 = summ["1"], summ["2"]
    oq = 2 * max(s1["maxveh"], s2["maxveh"])
    md = ["<!--HEADERDATA", "mk_title: Калкулација на пратките — Транша 1 и Транша 2 (пример)",
          "en_title: Shipment Calculation — Tranche 1 and Tranche 2 (example)", "code: EX_T1T2_CALC", "version: 01",
          "doctype: FORM", "parent: WHSOP_003", "orient: landscape", "-->", "", EX_NOTE, "",
          "# 1 Легенда | Legend", "[[TABLE]]", "Боја~~Colour ||| Значење~~Meaning",
          "%s ||| податок од нашите записи или пресметан од нив~~data from our records or calculated from them" % B("сино~~blue"),
          "%s ||| пример — да се потврди пред употреба~~example — to be confirmed before use" % A("виолетово~~purple"),
          "[ ]~~[ ] ||| се внесува на денот (мерења, потписи, броеви на пломби и логери, регистарски броеви)~~entered on the day (measurements, signatures, seal and logger numbers, registrations)",
          "[[/TABLE]]", "",
          "# 2 Параметри | Parameters", "[[FORM]]",
          "Извор на сериите ||| Source of the batches ||| " + B("Транши T1 и T2 според одлуката од 18.09.2026; маса по серија од листата на испораки; подсериите се посебни серии | Tranches T1 and T2 per the decision of 18.09.2026; mass per batch from the delivery list; sub-lots are separate batches"),
          "Нето маса на една кеса ||| Net mass of one bag ||| " + B("401,0 g ± 3 % (389,0–413,0 g) — IMB кеса | 401.0 g ± 3 % (389.0–413.0 g) — IMB bag"),
          "Пакување ||| Packaging ||| " + B("10 кеси по картон; голема палета 8 картони, мала 4; една серија по картон | 10 bags per carton; large pallet 8 cartons, small 4; one batch per carton"),
          "Ретенциони мостри ||| Retention samples ||| " + B("по една мостра од секоја серија за купувачот и за продавачот на мало, во картон RS | one sample of each batch for the buyer and for the retailer, in carton RS") + " · " + TBE,
          "Капацитет на возило ||| Vehicle capacity ||| " + B("33 евро-палети во еден слој (приколка 13,6 m) | 33 Euro pallets single-stacked (13.6 m trailer)"),
          "Датуми ||| Dates ||| " + A("OQ %s; Т1 %s; Т2 %s | OQ %s; T1 %s; T2 %s" % (OQ_DATES, T["1"]["date"], T["2"]["date"], OQ_DATES, T["1"]["date"], T["2"]["date"])),
          "Превозник и примач ||| Carrier and consignee ||| " + A(CARRIER) + " · " + A(CONSIGNEE),
          "[[/FORM]]", "", "# 3 Преглед | Overview", "[[TABLE]]",
          "Транша~~Tranche ||| Серии~~Batches ||| Нето маса~~Net mass ||| Кеси~~Bags ||| Картони~~Cartons ||| Палети~~Pallets ||| Возила~~Vehicles ||| Мостри RS~~RS samples ||| Логери рутина~~Loggers routine ||| Логери PQ~~Loggers PQ ||| USB PQ"]
    for tr in ("1", "2"):
        s = summ[tr]
        md.append(" ||| ".join(map(str, ["Т%s~~T%s" % (tr, tr), B(s["lots"]), B(fmt_kg(s["g"])), B(s["bags"]), B(s["cartons"]),
                                          B("%d (G %d / M %d)" % (s["pallets"], s["L"], s["S"])), B(s["veh"]), B(s["samples"]), B(s["pallets"]), B(2 * s["pallets"]), B(3 * s["veh"])])))
    md.append(" ||| ".join(map(str, [TOTAL, B(s1["lots"] + s2["lots"]), B(fmt_kg(s1["g"] + s2["g"])), B(s1["bags"] + s2["bags"]), B(s1["cartons"] + s2["cartons"]),
                                      B(s1["pallets"] + s2["pallets"]), B(s1["veh"] + s2["veh"]), B(s1["samples"] + s2["samples"]), B(s1["pallets"] + s2["pallets"]),
                                      B(2 * (s1["pallets"] + s2["pallets"])), "—"])))
    md += ["[[/TABLE]]", ""]
    for tr in ("1", "2"):
        lots = data[tr]
        md += ["# %d Серии во Т%s | Batches in T%s" % (3 + int(tr), tr, tr), "[[TABLE]]",
               "№ ||| P серија~~P lot ||| Културна серија~~Cultivation batch ||| Сорта~~Strain ||| Нето маса (g)~~Net mass (g) ||| Кеси~~Bags ||| Просек по кеса (g)~~Mean per bag (g) ||| ± 3 % ||| Картони~~Cartons"]
        md += [" ||| ".join(map(str, [i, B(l["p"] or "—"), B(l["cu"]), B(l["strain"]), B(fmt_g(l["g"])), B(l["bags"]),
                                       B(("%.1f" % l["avg"]).replace(".", ",")), B("да~~yes" if l["in_tol"] else "НЕ — делумна кеса~~NO — part bag"), B(l["cartons"])])) for i, l in enumerate(lots, 1)]
        md += [" ||| ".join(map(str, [TOTAL, "—", "—", "—", B(fmt_g(sum(l["g"] for l in lots))), B(sum(l["bags"] for l in lots)), "—", "—", B(sum(l["cartons"] for l in lots))])), "[[/TABLE]]", ""]
    out_tol = [lotname(l) for tr in ("1", "2") for l in data[tr] if not l["in_tol"]]
    md += ["# 6 Што треба да се одлучи | What must be decided", "[[TABLE]]", "№ ||| Прашање~~Question ||| Зошто~~Why",
           "1 ||| %s ||| %s" % (B("Т1 бара %d, Т2 %d палети — %d и %d возила~~T1 needs %d, T2 %d pallets — %d and %d vehicles" % (s1["pallets"], s2["pallets"], s1["veh"], s2["veh"], s1["pallets"], s2["pallets"], s1["veh"], s2["veh"])),
                                "по 8 картони од 10 кеси, палетата носи само околу 32 kg~~at 8 cartons of 10 bags a pallet carries only about 32 kg"),
           "2 ||| %s ||| %s" % (B("Логери за еднократна употреба: рутина %d, PQ %d, OQ %d~~Single-use loggers: routine %d, PQ %d, OQ %d" % (s1["pallets"] + s2["pallets"], 2 * (s1["pallets"] + s2["pallets"]), oq, s1["pallets"] + s2["pallets"], 2 * (s1["pallets"] + s2["pallets"]), oq)),
                                "располагаме со нешто над 100~~we hold a little over 100"),
           "3 ||| %s ||| %s" % (B("USB логери за PQ: %d возила × 3~~USB loggers for PQ: %d vehicles × 3" % (max(s1["veh"], s2["veh"]), max(s1["veh"], s2["veh"]))),
                                "имаме 10; Т2 користи %d~~we hold 10; T2 uses %d" % (3 * s2["veh"], 3 * s2["veh"])),
           "4 ||| %s ||| %s" % (B("%d етикети и листи на пакување за картони~~%d carton labels and packing lists" % (s1["cartons"] + s2["cartons"], s1["cartons"] + s2["cartons"])),
                                "секоја потпишана од две лица~~each signed by two persons"),
           "5 ||| %s ||| %s" % (B("Серии надвор од ± 3 % по кеса: " + (", ".join(out_tol) if out_tol else "нема") + "~~Batches outside ± 3 % per bag: " + (", ".join(out_tol) if out_tol else "none")),
                                "последната кеса е делумна; масата е на етикетата~~the last bag is partial; its mass is on the label"),
           "6 ||| " + B("OQ пред Т1~~OQ before T1") + " ||| PQ не смее да почне без одобрена OQ (QASOP_0XX §6.1)~~PQ must not start without an approved OQ (QASOP_0XX §6.1)",
           "7 ||| " + B("Маса на ретенционите мостри, адреса и рута на примачот~~Retention-sample mass, consignee address and route") + " ||| потребни за барањето до МВР, TRA и известувањето до МЗ~~needed for the MoIA request, the TRA and the MoH report",
           "[[/TABLE]]", ""]
    open(os.path.join(MD, "T0_CALCULATION.md"), "w", encoding="utf-8").write("\n".join(md))

# ------------------------------------------------------------------ validation records (QASOP_0XX)
def validation_set(plans, summ):
    s1, s2 = summ["1"], summ["2"]; mv = max(s1["maxveh"], s2["maxveh"])
    md = head(tpl("QASOP_0XX_A01"), " — L01 (пример)", " — L01 (example)")
    for lab, val in [("Код на рутата", B(LANE)), ("Број на проект за валидација", B(PROTOCOL)), ("Место на прием", A(CONSIGNEE) + " · " + TBE),
                     ("Превозник", A(CARRIER)),
                     ("Максимален товар: палети G / M", B("%d по возило (најполно возило) | %d per vehicle (fullest vehicle)" % (mv, mv))),
                     ("Картони / кеси / маса (kg)", B("Т1: %d / %d / %s; Т2: %d / %d / %s" % (s1["cartons"], s1["bags"], fmt_kg(s1["g"]), s2["cartons"], s2["bags"], fmt_kg(s2["g"])))),
                     ("Симулиран товар (кеси со иста маса и материјал)", B("OQ: %d G-палети, картони со кеси од 401,0 g, завиткани како во рутина | OQ: %d L pallets, cartons of 401.0 g bags, wrapped as in routine" % (mv, mv))),
                     ("Логери: USB (10) / за еднократна употреба (број)", B("10 / OQ %d, PQ-1 %d, PQ-2 %d" % (2 * mv, 2 * s1["pallets"], 2 * s2["pallets"]))),
                     ("Извор на климатските податоци", B("Управа за хидрометеоролошки работи (УХМР), Скопје | National Hydrometeorological Service, Skopje")),
                     ("Образложение за групирање / обем", A("Целосна OQ + PQ. OQ (%s) на возилото на превозникот пред Т1; PQ-1 = Т1 (%s), PQ-2 = Т2 (%s), PQ-3 = следната пратка; Т1 и Т2 по исклучителна мерка одобрена од QA (WHSOP_003 §6.2.2) | Full OQ + PQ. OQ (%s) on the carrier's vehicle before T1; PQ-1 = T1 (%s), PQ-2 = T2 (%s), PQ-3 = the next shipment; T1 and T2 under a QA-approved exceptional measure (WHSOP_003 §6.2.2)" % (OQ_DATES, T["1"]["date"], T["2"]["date"], OQ_DATES, T["1"]["date"], T["2"]["date"]))),
                     ("Планиран почеток и крај", A("%s — PQ-3" % OQ_DATES.split(" – ")[0]))]:
        md = field(md, lab, val)
    md = tick(md, "Готов производ / меѓупроизвод (15–25 °C, RH ≤ 60 %) | Finished product / intermediate (15–25 °C, RH ≤ 60 %)")
    md = tick(md, "Целосна OQ + PQ | Full OQ + PQ")
    write("V1_QASOP_0XX_A01", md)

    md = head(tpl("QASOP_0XX_A03"), " — L01 (пример)", " — L01 (example)")
    for lab, val in [("Код на рутата", B(LANE)), ("Протокол (QASOP_0XX_A02) бр.", B(PROTOCOL)), ("Превозник / возило (регистарски број)", A(CARRIER) + " · " + TBE),
                     ("Палети G / M", B("%d / 0 (симулиран товар) | %d / 0 (simulated load)" % (mv, mv))), ("Сезона", A("есен (октомври) | autumn (October)")),
                     ("Опсег", B(RANGE)), ("Датум на извршување", A(OQ_DATES))]:
        md = field(md, lab, val)
    md = table(md, "ID на палета~~Pallet ID ||| Тип G/M",
               [[B("OQ-P%02d" % k), B("G"), B("ред %d, %s | row %d, %s" % ((k + 1) // 2, "лево" if k % 2 else "десно", (k + 1) // 2, "left" if k % 2 else "right")), TBE, TBE, TBE] for k in range(1, mv + 1)])
    write("V2_QASOP_0XX_A03", md)

    for tr in ("1", "2"):
        P, pallets, s = T[tr], plans[tr][1], summ[tr]
        md = head(tpl("QASOP_0XX_A04"), " — PQ-%s = Т%s (пример)" % (tr, tr), " — PQ-%s = T%s (example)" % (tr, tr))
        for lab, val in [("Код на рутата", B(LANE)), ("Протокол бр.", B(PROTOCOL)), ("UTID (WHSOP_003)", B(P["utid"])), ("Датум", A(P["date"])),
                         ("Сезона", A("есен (октомври) | autumn (October)")), ("Палети G / M", B("%d / %d" % (s["L"], s["S"]))),
                         ("Превозник / возило", A(CARRIER) + " · " + B(veh_ranges(pallets)))]:
            md = field(md, lab, val)
        md = md.replace("☐ 1   ☐ 2   ☐ 3", "☐ 1   ☐ 2   ☐ 3".replace("☐ " + tr, "☒ " + tr), 1)
        md = tick(md, "Реален производ | Real product")
        md = table(md, "ID на палета~~Pallet ID ||| Тип G/M",
                   [[B("%s (%s)" % (p["id"], p["veh"])), B(p["type"]), TBE, TBE, TBE, TBE, TBE, TBE] for p in pallets])
        write("V%d_QASOP_0XX_A04_PQ%s" % (2 + int(tr), tr), md)

    md = head(tpl("QASOP_0XX_A06"), " (пример)", " (example)")
    md = re.sub(r"^L01 \|\|\| [^\n]*$", lambda m: " ||| ".join([
        "L01", A("Versa") + " · " + TBE, B("меѓупроизвод 15–25 °C~~intermediate 15–25 °C"), A("Kuehne + Nagel (предв.) / G-палети~~Kuehne + Nagel (prov.) / L pallets"),
        TBE, TBE, TBE, B("IN QUALIFICATION"), B("—"), B("PQ-1 = Т1, PQ-2 = Т2~~PQ-1 = T1, PQ-2 = T2")]), md, count=1, flags=re.M)
    write("V5_QASOP_0XX_A06", md)

def protocol_docx():
    sys.path.insert(0, os.path.join(HERE, ".."))
    sys.argv = [sys.argv[0], DOCX]
    import build_validation as bv
    bv.OUT = DOCX
    bv.info = lambda label: [
        ("Код на рутата | Lane code", B(LANE)), ("Место на испраќање | Dispatch point", B("Којлија 1043, Петровец | Kojlija 1043, Petrovec")),
        ("Место на прием | Receipt point", A("Versa") + " · " + TBE), ("Превозник / возило | Carrier / vehicle", A(CARRIER) + " · " + TBE),
        ("Контрола на температура | Temperature control", "☐ Активна | Active   ☐ Пасивна | Passive"),
        ("Конфигурација на палети | Pallet configuration", B("G 8 / M 4 картони × 10 кеси од 401,0 g | L 8 / S 4 cartons × 10 bags of 401.0 g")),
        ("Опсег | Range", B(RANGE)), ("План за валидација | Validation plan", B("QASOP_0XX_A01 — " + PROTOCOL)),
        ("Поврзана СОП | Governing SOP", "QASOP_0XX; WHSOP_003"), (label, B(PROTOCOL))]
    bv.protocol()
    os.replace(os.path.join(DOCX, "QASOP_0XX_A02.docx"), os.path.join(DOCX, "V1b_QASOP_0XX_A02.docx"))

# ------------------------------------------------------------------ colouring of the bracketed entries
BLUE, PURPLE, ORANGE = "0B5CAD", "7030A0", "C55A11"
SPAN = re.compile(r"\[[^\[\]]*\]")

def colour_docx(path):
    """Colour every [ ... ] in the document by its kind; brackets are kept, so the entry stays visible
    in black-and-white print as well."""
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    doc = Document(path)
    W_P, W_R, W_T = qn("w:p"), qn("w:r"), qn("w:t")
    for p in doc.element.body.iter(W_P):
        runs = [r for r in p if r.tag == W_R]
        texts = ["".join(t.text or "" for t in r.iter(W_T)) for r in runs]
        full = "".join(texts)
        if "[" not in full: continue
        colour = [None] * len(full)
        for m in SPAN.finditer(full):
            inner = m.group(0)[1:-1].strip()
            if not inner: c = ORANGE
            elif any(len(a) > 1 and (inner == a or a in inner) for a in ASSUME): c = PURPLE
            else: c = BLUE
            for k in range(m.start(), m.end()): colour[k] = c
        pos = 0
        for r, txt in zip(runs, texts):
            n = len(txt)
            if n == 0 or r.find(W_T) is None or len(list(r.iter(W_T))) != 1:
                pos += n; continue
            segs, start = [], 0
            for k in range(1, n + 1):
                if k == n or colour[pos + k] != colour[pos + start]:
                    segs.append((txt[start:k], colour[pos + start])); start = k
            pos += n
            if all(c is None for _, c in segs): continue
            anchor = r
            for s, c in segs:
                nr = copy.deepcopy(r)
                t = nr.find(W_T); t.text = s; t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                if c:
                    rpr = nr.find(qn("w:rPr"))
                    if rpr is None: rpr = OxmlElement("w:rPr"); nr.insert(0, rpr)
                    col = rpr.find(qn("w:color"))
                    if col is None: col = OxmlElement("w:color"); rpr.append(col)
                    col.set(qn("w:val"), c)
                anchor.addnext(nr); anchor = nr
            p.remove(r)
    doc.save(path)

# ------------------------------------------------------------------ build
def main():
    for d in (MD, DOCX, PDF):
        os.makedirs(d, exist_ok=True)
        for f in os.listdir(d): os.remove(os.path.join(d, f))
    data = load(); plans, summ = {}, {}
    for tr in ("1", "2"):
        plans[tr] = plan(data[tr], T[tr]["utid"])
        summ[tr] = transport_set(tr, data[tr], *plans[tr])
    calc_sheet(data, summ)
    validation_set(plans, summ)
    eng = [sys.executable, os.path.join(ENGINE, "build_from_md.py")]
    for f in sorted(os.listdir(MD)):
        subprocess.run(eng + [os.path.join(MD, f), os.path.join(DOCX, f[:-3] + ".docx")], check=True, stdout=subprocess.DEVNULL)
    protocol_docx()
    for f in sorted(os.listdir(DOCX)):
        colour_docx(os.path.join(DOCX, f))
        r = subprocess.run([sys.executable, os.path.join(ENGINE, "pp_verify.py"), os.path.join(DOCX, f)], capture_output=True, text=True)
        print(f, r.stdout.strip().splitlines()[-1])
    for f in sorted(os.listdir(DOCX)):   # main() clears pdf/, so it renders them again (LibreOffice macro updates TOC and fields)
        src, out = os.path.join(DOCX, f), os.path.join(PDF, f[:-5] + ".pdf")
        subprocess.run(["soffice", "--headless", 'macro:///Standard.Module1.ToPdf("%s","%s")' % (src, out)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not os.path.exists(out): sys.exit("PDF not rendered: " + out)
    print({k: {x: v[x] for x in ("lots", "bags", "cartons", "pallets", "veh", "samples")} for k, v in summ.items()})

if __name__ == "__main__":
    main()
