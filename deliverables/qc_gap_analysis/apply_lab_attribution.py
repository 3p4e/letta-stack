#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every determination cites the laboratory that made it, and one document has one date.

    python3 deliverables/qc_gap_analysis/apply_lab_attribution.py [--dry-run]

The Head of QC, 17.09.2026, reading Section 03 of CoQ-PP_26-004 (GG1024): the internal
certificate of analysis was cited twice under one code with two dates of issue, and credited
with parameters 1 to 11, where the two outside laboratories were credited only with 8 and 12.
The in-house laboratory determines identification A, identification B and foreign matter.
The Institute of Public Health determined that lot's microbiology, mycotoxins, heavy metals
and pesticides (166/0274/25 and 748/2025) and CNP its loss on drying (ППК25008) — the
documents the Head of QC's own pass of 09.09.2026 names for it. The company's in-house CoA
of 23.04.2025 had copied the Institute's figures, and the desk had routed that copy through
the internal certificate, with the copy's date.

Four rules, applied to every row of every certificate:

* **R1 — one document, one date.** A row citing an internal certificate carries that
  certificate's date of issue from the iCoA register, never the date of a record behind it.
* **R2 — the outside laboratory is cited where it exists.** A row outside #1/#2/#7 that cites
  an internal certificate or the in-house laboratory, for a determination the 09.09 pass
  names an outside document for, cites that document — with the release register's date and
  laboratory — provided the document is dated on or before the certificate (v35).
* **R3 — no document, no citation.** Where the pass names no outside document and the
  internal certificate's register row does not list the parameter under `covers_in_house`
  (the ruling of 10.09.2026: one internal certificate covers a determination whose only
  result in that round is an in-house record), the row has nothing to cite: it prints not
  tested, and the figure it carried is kept in `also` with its source, not lost.
* **R4 — an in-house CoA is never cited by its own number** (ruling of 10.09.2026). A #1/#2/#7
  row citing `PP CoA #nnn` cites the round's internal certificate.
* **R5 — one outside certificate, one name.** A row citing `PP CoA #nnn / ППКnnnnn` — the
  in-house CoA number beside the CNP certificate that carries the same figures — cites the
  CNP certificate alone, with its own date of issue from the register, the pass, or the
  certificate's own page in the page-text cache (`ingestion/ragflow/cache`). Section 03 had
  printed that certificate twice, once under the in-house number with the in-house date.

Rows an internal certificate legitimately covers under the 10.09 ruling — HPA1024 and
OPM1024 (microbiology, mycotoxins, metals, pesticides from the company's Report of Analysis)
and P050192 / P050202 (assay and loss on drying from the in-house cross-check) — are left as
they are and named in the output for the Head of QC: they are the remaining certificates on
which the in-house laboratory is credited beyond 1, 2 and 7.
"""
import argparse, csv, datetime as dt, io, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import icoa_register as ICO                                            # noqa: E402
SRC = os.path.join(HERE, "coq_artifact_data.json")
PASS = os.path.join(HERE, "cell_resolution_2026-09-09.tsv")
ICOA = os.path.join(HERE, "icoa_register_2026-09-10.csv")
CACHE = os.path.join(os.path.dirname(os.path.dirname(HERE)), "ingestion", "ragflow", "cache", "all_cert_texts_2026-08-30.json")
ALWAYS = {"1", "2", "7"}
INHOUSE = "Purely Plant GmbH (in-house)"
NT = "not tested — no certificate covers it"
CARRIED = re.compile(r"^(carried from the initial testing \([^)]*\)) — ")


def day(v):
    try:
        return dt.datetime.strptime(str(v).strip(), "%d.%m.%Y").date()
    except Exception:
        return None


def nk(s):
    return re.sub(r"[\s\-/_.＊*]+", "", str(s or "")).upper()


def load_pass():
    """(lot key, determination) -> the pass row, keyed by batch and by P lot."""
    out = {}
    for r in csv.DictReader(io.open(PASS, encoding="utf-8"), delimiter="\t"):
        m = re.match(r"(\d+)", r.get("Determination") or "")
        if not m:
            continue
        for k in (r.get("Batch"), r.get("P lot")):
            if k and k.strip() not in ("", "—"):
                out.setdefault((nk(k), m.group(1)), r)
    return out


def load_icoa():
    return {r["code"]: r for r in csv.DictReader(io.open(ICOA, encoding="utf-8"))}


def register_index(data):
    """document code (folded) -> (date, laboratory) from the release register blocks."""
    idx = {}
    for b in data["reg"]:
        for c in b.get("certs") or []:
            code = str(c.get("code") or "").strip()
            if code and not code.lower().startswith("n/a"):
                idx.setdefault(nk(code), (c.get("date"), c.get("lab")))
    return idx


def cache_dates():
    """document code (folded) -> (date of issue, laboratory) as the certificate's own page
    states them, from the page-text cache of 30.08.2026 — the source for a CNP certificate
    the register holds only under the in-house CoA's number and date."""
    out = {}
    if not os.path.exists(CACHE):
        return out
    for it in json.load(io.open(CACHE, encoding="utf-8")):
        m = (it or {}).get("meta") or {}
        code = str(m.get("cert_code") or "").strip()
        if code and m.get("date_of_issue"):
            out.setdefault(nk(code), (m["date_of_issue"], m.get("lab") or ""))
    return out


def outside_document(prow, reg):
    """The outside document the pass names, as the register spells it — or None."""
    if not prow:
        return None
    doc = (prow.get("Document to cite") or "").strip()
    if not doc or doc == "—" or doc.startswith("iCoA") or doc.upper().startswith("NO-DOC"):
        return None
    hit = reg.get(nk(doc))
    if not hit or ICO.is_in_house(hit[1] or "") or (hit[1] or "").strip() in ("PP", "NGP"):
        return None
    lab = (hit[1] or "").strip()
    return doc if nk(doc) == nk(doc) else doc, hit[0], lab


def apply(data, dry=False):
    pas, ico, reg, cache = load_pass(), load_icoa(), register_index(data), cache_dates()
    # the register's own spelling of every code, so the row prints what the register prints
    spell = {}
    for b in data["reg"]:
        for c in b.get("certs") or []:
            code = str(c.get("code") or "").strip()
            if code:
                spell.setdefault(nk(code), code)
    r1, r2, r3, r4, r5, kept = [], [], [], [], [], []
    for c in data["coqs"]:
        iss = day(c.get("issue")); lotkeys = [nk(c.get("pp")), nk(c.get("cb"))]
        own = str(c.get("icoa_code") or "").strip()
        for r in c["rows"]:
            base = r["no"].split(".")[0]
            doc = str(r.get("doc") or "").strip(); lab = str(r.get("lab") or "").strip()
            m5 = re.match(r"^PP CoA #\d+\s*/\s*(\S+)$", doc)
            if m5:
                code = m5.group(1); hit = reg.get(nk(code))
                prow = next((pas.get((k, base)) for k in lotkeys if pas.get((k, base))), None)
                pdoc = (prow or {}).get("Document to cite", "")
                page = cache.get(nk(code))
                date = (hit[0] if hit else None) or ((prow or {}).get("Issued") if nk(pdoc) == nk(code) else None) \
                    or (page[0] if page else None)
                plab = (hit[1] if hit else None) or ((prow or {}).get("Laboratory") if nk(pdoc) == nk(code) else None) or lab
                if day(date) and iss and day(date) <= iss:
                    r5.append((c["regcode"], r["no"], doc, r.get("dd"), "->", spell.get(nk(code), code), date, plab))
                    if not dry:
                        r["doc"], r["dd"], r["lab"] = spell.get(nk(code), code), date, plab
                else:
                    r5.append((c["regcode"], r["no"], doc, "HELD — no date for", code))
                continue
            cites_icoa = doc.startswith("iCoA")
            inhouse = cites_icoa or ICO.is_in_house(lab) or lab == "PP"
            if base in ALWAYS:
                if doc.startswith("PP CoA") or (lab == "PP" and not cites_icoa):
                    if own and ico.get(own) and day(ico[own]["issued"]) and day(ico[own]["issued"]) <= iss:
                        r4.append((c["regcode"], r["no"], doc, "->", own))
                        if not dry:
                            r["doc"], r["dd"], r["lab"] = own, ico[own]["issued"], INHOUSE
                elif cites_icoa and ico.get(doc) and r.get("dd") != ico[doc]["issued"]:
                    r1.append((c["regcode"], r["no"], doc, r.get("dd"), "->", ico[doc]["issued"]))
                    if not dry:
                        r["dd"] = ico[doc]["issued"]
                continue
            if not inhouse or not doc or doc == "—":
                continue
            prow = next((pas.get((k, base)) for k in lotkeys if pas.get((k, base))), None)
            ext = outside_document(prow, reg)
            if ext and day(ext[1]) and iss and day(ext[1]) <= iss:
                code = spell.get(nk(ext[0]), ext[0])
                m = CARRIED.match(r.get("st") or "")
                r2.append((c["regcode"], r["no"], doc, r.get("dd"), "->", code, ext[1], ext[2]))
                if not dry:
                    r["doc"], r["dd"], r["lab"] = code, ext[1], ext[2]
                    r["st"] = (m.group(1) + " — covered") if m else "covered"
                continue
            covers = set((ico.get(doc, {}).get("covers_in_house") or "").split()) if cites_icoa else set()
            if r["no"] in covers or base in covers:
                kept.append((c["regcode"], r["no"], doc))
                if ico[doc]["issued"] != r.get("dd"):
                    r1.append((c["regcode"], r["no"], doc, r.get("dd"), "->", ico[doc]["issued"]))
                    if not dry:
                        r["dd"] = ico[doc]["issued"]
                continue
            m = CARRIED.match(r.get("st") or "")
            r3.append((c["regcode"], r["no"], r.get("res"), doc, r.get("dd")))
            if not dry:
                note = "%s (in-house record of %s, no certificate)" % (r.get("res"), r.get("dd") or "no date")
                r["also"] = (r.get("also") + "; " + note) if r.get("also") else note
                r["res"], r["doc"], r["dd"], r["lab"] = "—", "—", "", ""
                r["st"] = (m.group(1) + " — " + NT) if m else NT
    return r1, r2, r3, r4, r5, kept


def main(argv):
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv[1:])
    data = json.load(io.open(SRC, encoding="utf-8"))
    r1, r2, r3, r4, r5, kept = apply(data, dry=a.dry_run)
    print("R1 dates set to the internal certificate's issue date: %d" % len(r1))
    for x in r1[:4]: print("   ", x)
    print("R2 rows re-pointed to the outside laboratory's document: %d" % len(r2))
    for x in r2[:6]: print("   ", x)
    print("R3 rows with no document to cite, now not tested: %d" % len(r3))
    for x in r3: print("   ", x)
    print("R4 in-house CoA numbers replaced by the internal certificate: %d" % len(r4))
    for x in r4: print("   ", x)
    print("R5 'PP CoA #nnn / code' citations reduced to the outside certificate: %d" % len(r5))
    for x in r5[:5]: print("   ", x)
    for x in r5:
        if "HELD" in x: print("   ", x)
    certs = sorted({k[0] for k in kept})
    print("kept under the ruling of 10.09.2026 (covers_in_house): %d rows on %d certificates: %s" % (len(kept), len(certs), certs))
    if not a.dry_run:
        with io.open(SRC, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        print("written:", os.path.relpath(SRC))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
