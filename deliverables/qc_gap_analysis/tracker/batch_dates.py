#!/usr/bin/env python3
"""Harvest and packaging dates per batch, from the Head of QC's list of 04.09.2026.

batch_dates_raw_2026-09-04.tsv is the list as sent (verbatim). This module normalises it
into batch_dates.csv — one row per batch, every date as dd.mm.yyyy, ranges as from/to —
and offers load_dates() to the tracker builder. Rules, each recorded in the `note` column:

  17/18.03.2025 and 11-13.08.2025  -> two days / a range inside one month
  27.06-04.07.2025                 -> a range across months
  31.07-05.08, 05-07.08, 30.09     -> no year printed: the harvest year of the same row,
                                      else the year of the row above (the list is chronological)
  11-13-11.2025                    -> read as 11-13.11.2025 (a dash where the dot belongs)
  0, ]                             -> no date given

The iCoA for identification A, B and foreign matter is dated on the LAST day of packaging
(the batch is complete only then); the whole range stays on the row.
"""
import csv, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "batch_dates_raw_2026-09-04.tsv")
OUT = os.path.join(HERE, "batch_dates.csv")

_D = r"(\d{1,2})"


def _fmt(d, m, y):
    return "%02d.%02d.%04d" % (int(d), int(m), int(y))


def parse(text, year_hint):
    """-> (from, to, note) with dates as dd.mm.yyyy, or (None, None, note)."""
    t = (text or "").strip()
    note = ""
    if t in ("", "0", "]", "-", "—"):
        return None, None, "no date given"
    m = re.fullmatch(r"(\d{1,2})-(\d{1,2})-(\d{1,2})\.(\d{4})", t)      # 11-13-11.2025
    if m:
        note = "printed %s, read as %s-%s.%s.%s" % (t, m.group(1), m.group(2), m.group(3), m.group(4))
        t = "%s-%s.%s.%s" % (m.group(1), m.group(2), m.group(3), m.group(4))
    m = re.fullmatch(_D + r"\." + _D + r"\." + r"(\d{4})", t)              # 20.01.2025
    if m:
        return _fmt(m.group(1), m.group(2), m.group(3)), _fmt(m.group(1), m.group(2), m.group(3)), note
    m = re.fullmatch(_D + r"[/-]" + _D + r"\." + _D + r"\.(\d{4})", t)      # 17/18.03.2025, 11-13.08.2025
    if m:
        return _fmt(m.group(1), m.group(3), m.group(4)), _fmt(m.group(2), m.group(3), m.group(4)), note
    m = re.fullmatch(_D + r"\." + _D + r"-" + _D + r"\." + _D + r"\.(\d{4})", t)   # 27.06-04.07.2025
    if m:
        return _fmt(m.group(1), m.group(2), m.group(5)), _fmt(m.group(3), m.group(4), m.group(5)), note
    if year_hint is None:
        return None, None, "no year printed and none to infer (%s)" % t
    y = year_hint
    inferred = "year %d inferred (not printed)" % y
    m = re.fullmatch(_D + r"\." + _D, t)                                     # 30.09
    if m:
        return _fmt(m.group(1), m.group(2), y), _fmt(m.group(1), m.group(2), y), inferred
    m = re.fullmatch(_D + r"[/-]" + _D + r"\." + _D, t)                      # 05-07.08
    if m:
        return _fmt(m.group(1), m.group(3), y), _fmt(m.group(2), m.group(3), y), inferred
    m = re.fullmatch(_D + r"\." + _D + r"-" + _D + r"\." + _D, t)            # 31.07-05.08
    if m:
        return _fmt(m.group(1), m.group(2), y), _fmt(m.group(3), m.group(4), y), inferred
    return None, None, "unreadable: %s" % t


def normalise(raw=RAW, out=OUT):
    rows = []
    prev_year = None
    for r in csv.DictReader(open(raw, encoding="utf-8"), delimiter="\t"):
        cu = re.sub(r"\s*-\s*R&D$", "", r["Batch"].strip())
        pk_batch = r["Packaging batch"].strip()
        h_from, h_to, h_note = parse(r["Date of harvest"], prev_year)
        year_hint = int(h_to[-4:]) if h_to else prev_year
        p_from, p_to, p_note = parse(r["Packaging date"], year_hint)
        if p_to:
            prev_year = int(p_to[-4:])
        notes = [x for x in ("harvest: " + h_note if h_note else "", "packaging: " + p_note if p_note else "") if x]
        if cu != r["Batch"].strip():
            notes.append("listed as '%s'" % r["Batch"].strip())
        rows.append({"seq": r["#"], "cu_batch": cu, "p_batch": pk_batch if pk_batch.startswith("P") else "",
                     "harvest_printed": r["Date of harvest"].strip(), "packaging_printed": r["Packaging date"].strip(),
                     "harvest_from": h_from or "", "harvest_to": h_to or "",
                     "packaging_from": p_from or "", "packaging_to": p_to or "",
                     "note": "; ".join(notes)})
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return rows


def span(a, b):
    """'17.03.2025' / '17.03.2025 – 18.03.2025' for display."""
    if not a:
        return ""
    return a if a == b else "%s – %s" % (a, b)


def load_dates(path=OUT):
    """{'P050122': row, 'CU:<batch_key>': row} — the builder looks a lot up by P-number first,
    then by the cultivation batch (needs tracker_data.batch_key for the CU form)."""
    if not os.path.exists(path):
        return {}
    out = {}
    for r in csv.DictReader(open(path, encoding="utf-8")):
        if r["p_batch"]:
            out[r["p_batch"]] = r
        out["CU:" + r["cu_batch"].upper()] = r
    return out


if __name__ == "__main__":
    rows = normalise()
    bad = [r for r in rows if not r["packaging_to"]]
    inf = [r for r in rows if "inferred" in r["note"]]
    print("%d rows -> %s | without a packaging date: %d | year inferred: %d" % (len(rows), OUT, len(bad), len(inf)))
    for r in rows:
        if r["note"]:
            print("  %-3s %-14s %-8s harvest=%-24s packaging=%-24s %s" % (
                r["seq"], r["cu_batch"], r["p_batch"], span(r["harvest_from"], r["harvest_to"]) or "—",
                span(r["packaging_from"], r["packaging_to"]) or "—", r["note"]))
