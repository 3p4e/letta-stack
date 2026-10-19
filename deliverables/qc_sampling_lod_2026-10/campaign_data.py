#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Campaign data for PP-QC-SP-002/26 — in-house loss on drying before shipment, Tranches 1 and 2.

Single source of truth for every number printed on the sampling plan and the two daily execution
records. Reads only committed records; computes N, n, k, the systematic bag selection and the day
split; writes SAMPLING_PLAN_T1_T2_2026-10.tsv and bag_selection.tsv next to this file.

Sources (all in this repository):
  tranche_assignment_2026-09-18.csv          which lots are Tranche 1 and 2 (Head of QC, 18.09.2026)
  CoQ_Analysis_Master_v57.xlsx / Reference    kg per lot, block "DELIVERY T1-T3" column E (the basis
                                              chosen by the Head of QC on 05.10.2026)
  quantities_table.tsv                        the owner's stock table, 10-11.08.2026 (cross-check +
                                              warehouse)
  coq_artifact_data.json                      strain, grade, packaging date, last loss-on-drying result

Rules as executed (Head of QC, 06.10.2026, amending the draft of 05.10.2026):
  N = ceil(kg / 0.400)             400 g bags, 10 per carton; informative (bags in the batch)
  n = 1                            one bag per batch, chosen at sampling and written as K{carton}B{bag}
  k = 1                            one test portion per batch
  day = 1                          all 46 batches sampled on one day and dried in one oven run
The draft's r-plan helpers (n = ceil(1.5 * sqrt(N)), k = 1/2/3 by N, systematic selection) are kept below
with their doctests; build() no longer uses them.

>>> n_from_N(560), n_from_N(103), n_from_N(55), n_from_N(49), n_from_N(23)   # the July values
(36, 16, 12, 11, 8)
>>> N_from_kg(223.73), N_from_kg(43.87), N_from_kg(0.87)
(560, 110, 3)
>>> k_from_N(23), k_from_N(100), k_from_N(101), k_from_N(400), k_from_N(401)
(1, 1, 2, 2, 3)
>>> bag_id(1), bag_id(10), bag_id(11), bag_id(99)
('K1B1', 'K1B10', 'K2B1', 'K10B9')
>>> sel = select_bags(100, 15, start=1); sel[:3], sel[-1], len(sel)
(['K1B1', 'K1B8', 'K2B5'], 'K10B9', 15)
>>> len(select_bags(110, 16, start=5)), len(select_bags(23, 8, start=2))
(16, 8)
"""
import csv
import json
import math
import os
import random
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
GAP = os.path.join(REPO, "deliverables", "qc_gap_analysis")
sys.path.insert(0, os.path.join(REPO, "ingestion", "common"))
from batch_id import batch_key  # noqa: E402

TRANCHE_CSV = os.path.join(GAP, "tranche_assignment_2026-09-18.csv")
MASTER_XLSX = os.path.join(GAP, "tracker", "CoQ_Analysis_Master_v57.xlsx")
STOCK_TSV = os.path.join(REPO, "ingestion", "coa_track", "letta-imb-coas", "sources_of_truth",
                         "quantities_table.tsv")
REGISTER_JSON = os.path.join(GAP, "coq_artifact_data.json")
BATCH_DATES_CSV = os.path.join(GAP, "batch_dates_2026-09-10.csv")   # owner's workbook: packaging_from

BAG_KG = 0.400          # net per primary bag (QCSP-RMI-P0005 Triplex Alu bag, 400.0 g +/- 3 %)
BAGS_PER_CARTON = 10
N_BAGS_EXECUTED = 1           # Head of QC, 06.10.2026: one bag per batch
K_PORTIONS_EXECUTED = 1       # one test portion per batch
BAG_WRITE_IN = "K___B___"     # the bag is chosen at sampling and written on the forms
SEED = 20261005         # fixed and printed on the plan, so the selection is reproducible
# Where a master kg is implausible against the owner's stock table (below one tenth of it), the
# stock value is used and the master cell is reported for correction. One lot: GG1024_01, 0.87 kg
# in Reference E216 against 223.734 kg on stock and the July plan's 560 bags.
IMPLAUSIBLE_RATIO = 0.10
WAREHOUSE_ORDER = ["E66", "E46/47", "F131", "Sec.Pack"]
TEST_PORTION_G = 1.000
FLOWER_G_LOW, FLOWER_G_HIGH = 1.0, 3.0


def N_from_kg(kg):
    return int(math.ceil(round(float(kg) / BAG_KG, 6)))


def n_from_N(N):
    return int(math.ceil(1.5 * math.sqrt(N) - 1e-9))


def k_from_N(N):
    return 1 if N <= 100 else (2 if N <= 400 else 3)


def bag_id(b):
    c = (b - 1) // BAGS_PER_CARTON + 1
    return "K%dB%d" % (c, (b - 1) % BAGS_PER_CARTON + 1)


def interval(N, n):
    """Sampling interval: ceil(N/n) as in PP-QC-SP-001/26; where that cannot place n bags inside N
    (e.g. N 126, n 17: 1 + 8*16 = 129 > 126) the floor is used, which always fits.

    >>> interval(100, 15), interval(126, 17), interval(23, 8)
    (7, 7, 3)
    """
    i = int(math.ceil(N / n))
    if N - i * (n - 1) < 1:
        i = max(1, N // n)
    return i


def max_start(N, n):
    """Largest random start that still fits n bags at the interval ceil(N/n)."""
    return max(1, N - interval(N, n) * (n - 1))


def select_bags(N, n, start):
    i = interval(N, n)
    bags = [start + j * i for j in range(n)]
    assert bags[-1] <= N, (N, n, start)
    return [bag_id(b) for b in bags]


def _f(x):
    try:
        return float(str(x).replace(",", "."))
    except (TypeError, ValueError):
        return None


def load_tranches():
    lots = []
    with open(TRANCHE_CSV, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["tranche"] in ("1", "2"):
                lots.append({"tranche": int(row["tranche"]), "p_lot": row["p_lot"].strip() or None,
                             "batch_csv": row["batch"].strip(), "bkey": batch_key(row["batch"])})
    return lots


def load_master():
    import openpyxl
    ws = openpyxl.load_workbook(MASTER_XLSX, read_only=True, data_only=True)["Reference"]
    rows = []
    for r in ws.iter_rows(min_row=208, max_row=285, values_only=True):
        if r[2] is None or _f(r[4]) is None:
            continue
        rows.append({"delivery_tranche": str(r[0]).strip(), "batch": str(r[2]).strip(),
                     "strain": str(r[3] or "").strip(), "kg": _f(r[4]),
                     "p_lot": None if str(r[7] or "").strip() in ("", "—", "-") else str(r[7]).strip(),
                     "desk_lot": str(r[8] or "").strip(), "row": None})
    # row numbers for the correction note
    for idx, rw in enumerate(rows):
        rw["row"] = 208 + idx
    return rows


def load_stock():
    out = []
    with open(STOCK_TSV, encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            out.append({"label": row["batch_label"].strip(), "key": row["p_number"].strip(),
                        "kg": _f(row["quantity_kg"]), "warehouse": row["warehouse"].strip()})
    return out


def load_register():
    return json.load(open(REGISTER_JSON, encoding="utf-8"))["coqs"]


def load_batch_dates():
    by_p, by_b = {}, {}
    with open(BATCH_DATES_CSV, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            pk = (row.get("packaging_from") or "").strip()
            if row.get("p_batch", "").strip():
                by_p[row["p_batch"].strip()] = pk
            by_b[batch_key(row["batch"])] = pk
    return by_p, by_b


def _lab_short(lab):
    lab = lab or ""
    if "Farmahem" in lab:
        return "Farmahem"
    if "Natural Products" in lab or "UKIM" in lab:
        return "UKIM CNP"
    if "Public Health" in lab or "IPH" in lab or "ИЈЗ" in lab:
        return "IPH"
    if "Purely" in lab or "In-house" in lab or "in-house" in lab:
        return "in-house"
    return lab[:24]


def _date_key(d):
    try:
        dd, mm, yy = d.split(".")
        return (int(yy), int(mm), int(dd))
    except Exception:
        return (0, 0, 0)


def last_lod(records):
    best = None
    for rec in records:
        for row in rec.get("rows", []):
            if row.get("no") != "8":
                continue
            res = (row.get("res") or "").strip()
            if not res or res.startswith("["):
                continue
            cand = (_date_key(row.get("dd") or ""), res, _lab_short(row.get("lab")), row.get("dd") or "",
                    row.get("doc") or "")
            if best is None or cand[0] > best[0]:
                best = cand
    if best is None:
        return None
    return {"res": best[1], "lab": best[2], "date": best[3], "doc": best[4]}


def build(seed=SEED, verbose=True):
    lots = load_tranches()
    master = load_master()
    stock = load_stock()
    reg = load_register()
    dates_p, dates_b = load_batch_dates()
    notes = []

    by_p_master = {m["p_lot"]: m for m in master if m["p_lot"]}
    by_b_master = {batch_key(m["batch"]): m for m in master}
    by_p_stock = {s["key"]: s for s in stock}
    by_b_stock = {batch_key(s["key"]): s for s in stock}
    reg_by_p = {}
    reg_by_b = {}
    for rec in reg:
        if rec.get("pp"):
            reg_by_p.setdefault(rec["pp"], []).append(rec)
        if rec.get("cb"):
            reg_by_b.setdefault(batch_key(rec["cb"]), []).append(rec)

    out = []
    for lot in lots:
        m = by_p_master.get(lot["p_lot"]) if lot["p_lot"] else None
        if m is None:
            m = by_b_master.get(lot["bkey"])
        s = by_p_stock.get(lot["p_lot"]) if lot["p_lot"] else None
        if s is None:
            s = by_b_stock.get(lot["bkey"])
        recs = (reg_by_p.get(lot["p_lot"]) if lot["p_lot"] else None) or reg_by_b.get(lot["bkey"]) or []
        if m is None:
            raise SystemExit("no master kg for %s / %s" % (lot["batch_csv"], lot["p_lot"]))
        kg_master = m["kg"]
        kg_stock = s["kg"] if s else None
        kg_used, kg_source = kg_master, "master v57 Reference E%d" % m["row"]
        if kg_stock and kg_master < IMPLAUSIBLE_RATIO * kg_stock:
            kg_used, kg_source = kg_stock, "stock table (master E%d = %.2f kg implausible)" % (m["row"], kg_master)
            notes.append("%s: master v57 Reference E%d reads %.2f kg against %.3f kg on the stock table; "
                         "the plan uses the stock figure (N %d) and the master cell needs correction."
                         % (m["batch"], m["row"], kg_master, kg_stock, N_from_kg(kg_stock)))
        N = N_from_kg(kg_used)
        n = N_BAGS_EXECUTED
        k = K_PORTIONS_EXECUTED
        rec0 = sorted(recs, key=lambda r: _date_key(r.get("issue") or ""))[-1] if recs else {}
        strain = (rec0.get("strain") or m["strain"] or "").strip()
        pk = (rec0.get("pk") or "").strip() or (dates_p.get(lot["p_lot"]) if lot["p_lot"] else None) \
            or dates_b.get(lot["bkey"]) or ""
        if not (rec0.get("pk") or "").strip() and pk:
            notes.append("%s: packaging date %s taken from batch_dates_2026-09-10.csv (register pk empty)."
                         % (m["batch"], pk))
        out.append(OrderedDict([
            ("tranche", lot["tranche"]), ("batch", m["batch"]), ("p_lot", lot["p_lot"] or "—"),
            ("strain", strain), ("grade", (rec0.get("grade") or "").strip()),
            ("packaging_date", pk),
            ("warehouse", s["warehouse"] if s else "—"),
            ("kg_master", kg_master), ("kg_stock", kg_stock), ("kg_used", kg_used), ("kg_source", kg_source),
            ("N", N), ("n", n), ("k", k), ("interval", ""),
            ("composite_g_low", ""), ("composite_g_high", ""),
            ("test_portions_g", round(k * TEST_PORTION_G, 3)),
            ("last_lod", last_lod(recs)),
        ]))
    assert len(out) == 46, len(out)

    # as executed (Head of QC, 06.10.2026): one bag per batch, chosen at sampling (a write-in), one day
    for lot in out:
        lot["start"] = ""
        lot["bags"] = [BAG_WRITE_IN]
        lot["cartons"] = []
        lot["day"] = 1
    days = {1: list(out)}
    worder = {w: i for i, w in enumerate(WAREHOUSE_ORDER)}
    days[1].sort(key=lambda x: (worder.get(x["warehouse"], 9), x["tranche"], x["batch"]))
    for i, lot in enumerate(days[1], start=1):
        lot["seq"] = i
    out.sort(key=lambda x: (x["day"], x["seq"]))

    if verbose:
        print("Day 1: %d lots, bags opened %d, test portions %d (one bag and one portion per batch)"
              % (len(days[1]), sum(l["n"] for l in days[1]), sum(l["k"] for l in days[1])))
        for note in notes:
            print("NOTE:", note)
    return out, notes


def write_tsv(lots, notes):
    plan = os.path.join(HERE, "SAMPLING_PLAN_T1_T2_2026-10.tsv")
    cols = ["day", "seq", "tranche", "batch", "p_lot", "strain", "grade", "packaging_date", "warehouse",
            "kg_master", "kg_stock", "kg_used", "kg_source", "N", "n", "k", "interval", "start",
            "composite_g_low", "composite_g_high", "test_portions_g", "last_lod_res", "last_lod_lab",
            "last_lod_date", "last_lod_doc", "cartons", "bags"]
    with open(plan, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(cols)
        for l in lots:
            ll = l["last_lod"] or {}
            w.writerow([l["day"], l["seq"], l["tranche"], l["batch"], l["p_lot"], l["strain"], l["grade"],
                        l["packaging_date"], l["warehouse"], l["kg_master"], l["kg_stock"] if l["kg_stock"] is not None else "",
                        l["kg_used"], l["kg_source"], l["N"], l["n"], l["k"], l["interval"], l["start"],
                        l["composite_g_low"], l["composite_g_high"], l["test_portions_g"],
                        ll.get("res", ""), ll.get("lab", ""), ll.get("date", ""), ll.get("doc", ""),
                        " ".join(str(c) for c in l["cartons"]), " ".join(l["bags"])])
    sel = os.path.join(HERE, "bag_selection.tsv")
    with open(sel, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["day", "batch", "p_lot", "N", "n", "interval", "start", "pick", "bag_no", "bag_id", "carton", "bag_in_carton"])
        for l in lots:
            for j, bid in enumerate(l["bags"], start=1):
                w.writerow([l["day"], l["batch"], l["p_lot"], l["N"], l["n"], "", "", j, "", bid, "", ""])
    with open(os.path.join(HERE, "DATA_NOTES.md"), "w", encoding="utf-8") as fh:
        fh.write("# Data notes — PP-QC-SP-002/26\n\nAs executed (Head of QC, 06.10.2026): one bag per batch, chosen at "
                 "sampling and written on the forms; one test portion per batch; all 46 batches on one day, one oven run. "
                 "Bag mass %.3f kg, %d bags per carton.\n\n" % (BAG_KG, BAGS_PER_CARTON))
        for note in notes:
            fh.write("- %s\n" % note)
    return plan, sel


if __name__ == "__main__":
    if "--test" in sys.argv:
        import doctest
        fails, ran = doctest.testmod()
        print("%d/%d doctests passed" % (ran - fails, ran))
        raise SystemExit(1 if fails else 0)
    lots, notes = build()
    p, s = write_tsv(lots, notes)
    print("written:", os.path.relpath(p, REPO), os.path.relpath(s, REPO))
