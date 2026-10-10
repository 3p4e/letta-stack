#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The date each external certificate says the laboratory received the sample.

    python3 deliverables/qc_gap_analysis/receipt_dates.py      # self-test + census, writes the CSV

Owner, 15.09.2026: the references table is to carry, beside every certificate a
CoQ cites, the date the sample was admitted to the external laboratory. The
certificates print it, each laboratory in its own words, and four sources on file
hold those words:

  1. the certificate text the corpus holds (ingestion/ragflow/cache/
     all_cert_texts_2026-08-30.json) — IJZ and Farmahem "Датум на прием", IJZ-MB
     "Дата на прием", CNP "Доставил/Доставувач на испитување … на <date>", DFL
     "Дата и час на прием за анализа" / "Date of sample receiving", NGP "Received
     at Lab";
  2. the Tranche 2 page reads (intake_220M_2026-09-14/reads_claude.json,
     date_received);
  3. the Tranche 3 page reads (intake_227K_2026-09-15/reads_227K.json, date_received);
  4. the IJZ-MB campaign manifest (tracker/split_manifest_IJZ-MB_2026-09-01.csv,
     receipt_date, pixel-verified);
  5. the Tranche 2 cannabinoid page reads (intake_220K_2026-09-15/reads_220K.json,
     date_received).

A page read outranks the corpus (trap 12: where chunk text and page disagree, the
page wins); a corpus date is written with its source named so a reader knows which
evidence it rests on. A certificate none of the four holds has no receipt date,
and the table says so rather than guessing one.

Output: receipt_dates_2026-09-15.csv — code (as the record spells it), lab,
received, source, phrase.
"""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CACHE = os.path.join(ROOT, "ingestion", "ragflow", "cache", "all_cert_texts_2026-08-30.json")
OUT = os.path.join(HERE, "receipt_dates_2026-09-15.csv")
DATE = r"(\d{1,2}[./]\d{1,2}[./]\d{4})"
PHRASES = [
    ("Датум на прием", r"Датум на прием[^\d]{0,40}" + DATE),
    ("Дата на прием", r"Дата на прием[^\d]{0,40}" + DATE),
    ("Дата и час на прием за анализа", r"прием за анализа[^\d]{0,40}" + DATE),
    ("Date of sample receiving", r"Date of sample receiving[^\d]{0,40}" + DATE),
    ("Доставил на испитување … на", r"Достав(?:ил|увач) на испитување[^\n]{0,160}?\bна\s*" + DATE),
    ("Received at Lab", r"Received at Lab[^\d]{0,40}" + DATE),
]


def norm(code):
    """One spelling for matching: Latin K/M, hyphens, no spaces.

    >>> norm("197-13-М/26"), norm("197-13-M-26"), norm("752/2025"), norm("ППК25052")
    ('197-13-M-26', '197-13-M-26', '752-2025', 'ППK25052')
    """
    return (str(code or "").strip().translate({ord("М"): "M", ord("К"): "K"})
            .replace("/", "-").replace(" ", ""))


def from_text(text):
    """(date, phrase) off a certificate's text, or (None, None).

    >>> from_text("сув цвет Датум на прием: 13.02.2025 Со писмо")
    ('13.02.2025', 'Датум на прием')
    >>> from_text("Доставил на испитување: ПУРЕЈЛИ ПЛАНТ ДООЕЛ, с. Којлија, Петровец, на 21.04.2026 год.")
    ('21.04.2026', 'Доставил на испитување … на')
    >>> from_text("no receipt here")
    (None, None)
    """
    t = re.sub(r"\s+", " ", text or "")
    for name, rx in PHRASES:
        m = re.search(rx, t)
        if m:
            d = m.group(1).replace("/", ".")
            dd, mm, yy = d.split(".")
            return "%02d.%02d.%s" % (int(dd), int(mm), yy), name
    return None, None


def build():
    rows = {}

    def put(code, lab, received, source, phrase, rank):
        k = norm(code)
        if not k or not received:
            return
        if k not in rows or rows[k]["rank"] > rank:
            rows[k] = {"code": str(code).strip(), "lab": lab, "received": received,
                       "source": source, "phrase": phrase, "rank": rank}

    if os.path.exists(CACHE):
        for e in json.load(open(CACHE, encoding="utf-8")):
            m = e.get("meta") or {}
            d, phrase = from_text(e.get("text") or "")
            put(m.get("cert_code"), m.get("lab", ""), d, "certificate text (corpus)", phrase, 3)
    p = os.path.join(HERE, "intake_220M_2026-09-14", "reads_claude.json")
    if os.path.exists(p):
        for m in json.load(open(p, encoding="utf-8")).values():
            put(m["cert_code"], "FHM-M", m.get("date_received"), "page read 14.09.2026", "Датум на прием", 1)
    p = os.path.join(HERE, "intake_227K_2026-09-15", "reads_227K.json")
    if os.path.exists(p):
        for m in json.load(open(p, encoding="utf-8")).values():
            put(m["cert_code"], "FHM-K", m.get("date_received"), "page read 12.09.2026", "Датум на прием", 1)
    p = os.path.join(HERE, "intake_220K_2026-09-15", "reads_220K.json")
    if os.path.exists(p):
        for m in json.load(open(p, encoding="utf-8")).values():
            put(m["cert_code"], "FHM-K", m.get("date_received"), "page read 15.09.2026", "Датум на прием", 1)
    p = os.path.join(HERE, "tracker", "split_manifest_IJZ-MB_2026-09-01.csv")
    if os.path.exists(p):
        with open(p, encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                put(r["lab_no"], "IJZ-MB", r.get("receipt_date"), "IJZ-MB manifest (pixel-verified)", "Дата на прием", 2)
    return sorted(rows.values(), key=lambda r: (r["lab"], r["code"]))


_MAP = None


def received(code):
    """The receipt date on file for a certificate code, or ''.

    >>> received("752/2025"), received("no such code")
    ('13.02.2025', '')
    """
    global _MAP
    if _MAP is None:
        _MAP = {}
        if os.path.exists(OUT):
            with open(OUT, encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    _MAP[norm(r["code"])] = r["received"]
    return _MAP.get(norm(code), "")


def main(argv):
    rows = build()
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=["code", "lab", "received", "source", "phrase"], extrasaction="ignore")
        wr.writeheader()
        wr.writerows(rows)
    global _MAP
    _MAP = None
    import doctest
    fail, ran = doctest.testmod()
    print("%d doctests, %d failed" % (ran, fail))
    from collections import Counter
    print("%s: %d certificate(s) with a receipt date" % (os.path.basename(OUT), len(rows)))
    for (lab, src), n in sorted(Counter((r["lab"], r["source"]) for r in rows).items()):
        print("   %-7s %-36s %3d" % (lab, src, n))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
