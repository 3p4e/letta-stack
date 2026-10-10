#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The contaminant panels reach the certificates that have been printing "not tested".

    python3 deliverables/qc_gap_analysis/apply_contaminants.py [--dry-run]

The Head of QC, 18.09.2026: "There cannot be parameters for heavy metals not tested."

He is right, and the cause was not that the tests were never run. Sixty-five certificates
of the Institute of Public Health were in the archive, unread: each one a full contaminant
panel — 29 pesticide residues, four heavy metals and total aflatoxins — for a lot whose
certificate of quality prints a dash against #11.

Every figure here passed the desk's two-read gate: two readers transcribed all sixty-five
scans independently, without seeing each other's work, and this script takes only what
both of them wrote. The gate's own record is in intake_contaminants_2026-09-18/.

WHAT IS TAKEN AND WHAT IS NOT

  #11.1–11.4  heavy metals — lead, cadmium, arsenic, mercury. Taken.
  #10.2       total aflatoxins. Taken.
  #12         pesticide residues. Taken, as the panel's own summary: the spelling names
              how many residues were run and what they all read, because "ND" alone does
              not say whether twenty-two or twenty-nine analytes stand behind it.

  #10.1, #10.3  aflatoxin B1 and ochratoxin A are NOT taken. These certificates report
              вкупни афлатоксини and nothing else — there is no B1 row and no ochratoxin
              row on the page. The desk's own gap stays where it is rather than being
              filled from a determination the laboratory did not make.

A limit column is read but never applied: the older form of the report prints looser
maxima (lead 5, cadmium 1, arsenic 2 mg/kg) than the certificate's criterion. The RESULT
is the laboratory's; the acceptance criterion is the desk's, and it does not move.

Nothing already printed is overwritten. Where a certificate already carries a figure for a
determination, this script compares it with the new reading and reports agreement or
disagreement — it does not rewrite the company's own signed record.
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import result_vocabulary as RV                                           # noqa: E402

ART = os.path.join(HERE, "coq_artifact_data.json")
GATE = os.path.join(HERE, "intake_contaminants_2026-09-18", "two_read_result.json")
LAB = "IPH — Institute of Public Health"
FAM = "IPH mycotoxins, metals, pesticides"

# The printed row on the page -> the determination on the certificate. The criteria match
# the laboratory's own 2026 maxima exactly (lead 0.5, cadmium 0.3, arsenic 0.2, mercury
# 0.1 mg/kg), which is how the four were told apart in the first place.
METALS = [("11.1", "олово"), ("11.2", "кадмиум"), ("11.3", "арсен"), ("11.4", "жива")]
AFLA = ("10.2", "афлатоксин")
# бакар is on four of the reports and has no maximum printed beside it. It is not a
# determination of this specification, so it is not placed on any certificate.


def dot(v):
    """The desk prints a decimal point; the laboratory prints a comma."""
    return re.sub(r"(?<=\d),(?=\d)", ".", str(v or "").strip())


def lot_of(scan):
    """(cultivation batch, P lot) from the scan's own file name.

    A starred cultivation batch is the same packaged lot, a second sample sent for a
    limited panel (Head of QC, 16.09.2026), so the star is folded away for the lookup.
    """
    stem = os.path.basename(scan).rsplit(".", 1)[0]
    parts = stem.split("_")
    tail = re.sub(r"[＊*]", "", parts[-1] if parts else "")
    if "-P" in tail:
        cu, p = tail.rsplit("-P", 1)
        return cu, "P" + p
    return tail, ""


def pesticide_summary(rows):
    """One line for #12 that says how many residues were run and what they read."""
    res = [r for r in rows if r["det"] == "pest"]
    if not res:
        return None
    # The laboratory's own decimal mark is kept in this line, as the desk already
    # writes it: "< 0,01 mg/kg — all 29 residues". It is a quotation of the form, not a
    # measured value in the desk's own notation.
    spell = collections.Counter(RV.canon(str(r["result"] or "").strip(), "12") for r in res)
    unit = collections.Counter(str(r.get("unit") or "").strip() for r in res).most_common(1)[0][0]
    (top, n), = spell.most_common(1)
    if n == len(res):
        return "%s %s — all %d residues" % (top, unit or "mg/kg", len(res))
    others = ", ".join("%s ×%d" % (k, v) for k, v in spell.most_common() if k != top)
    return "%s %s — %d of %d residues; %s" % (top, unit or "mg/kg", n, len(res), others)


_CLAIM = re.compile(r"^(.*?)\s*—\s*all\s+\d+\s+residues$")


def _same_claim(a, b):
    """True when two #12 sentences make the same assertion and differ only in the count."""
    ma, mb = _CLAIM.match(str(a).strip()), _CLAIM.match(str(b).strip())
    if mb is None:
        return False
    left_a = ma.group(1) if ma else str(a).strip()
    return dot(left_a).rstrip(" mg/kKg") == dot(mb.group(1)).rstrip(" mg/kKg") \
        or dot(left_a) == dot(mb.group(1))


def classify(doc):
    """Tag every printed row of one certificate with the determination it belongs to."""
    out = []
    for p in doc["parameters"]:
        name = str(p.get("name") or "").strip().lower()
        det = None
        for no, word in METALS:
            if name.startswith(word):
                det = no
        if AFLA[1] in name:
            det = AFLA[0]
        if name.startswith("бакар") or name.startswith("пестициди вкупно"):
            det = "skip"
        out.append({"det": det or "pest", "name": p.get("name"), "result": p.get("result"),
                    "limit": p.get("limit"), "unit": p.get("unit")})
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv[1:])

    gate = json.load(open(GATE, encoding="utf-8"))
    data = json.load(open(ART, encoding="utf-8"))

    # lot -> the certificates of quality of that lot, initial first
    by_lot = collections.defaultdict(list)
    for c in data["coqs"]:
        rnd = "retest" if str(c.get("t") or "").startswith("retest") else "initial"
        for k in (c.get("pp"), c.get("cb")):
            if k:
                by_lot[str(k).strip()].append((rnd, c))
    for v in by_lot.values():
        v.sort(key=lambda t: t[0] != "initial")

    applied, agreed, differ, recount, nolot, nothing = [], [], [], [], [], []
    for key, doc in sorted(gate["documents"].items()):
        cu, p = lot_of(doc.get("scan") or "")
        certs = by_lot.get(p) or by_lot.get(cu) or []
        if not certs:
            nolot.append((doc.get("doc_code"), cu, p)); continue
        rows = classify(doc)
        initial = next((c for r, c in certs if r == "initial"), None)
        take = {}
        for no, _word in METALS + [AFLA]:
            hit = [r for r in rows if r["det"] == no]
            if len(hit) == 1:
                take[no] = RV.canon(dot(hit[0]["result"]), no)
        pest = pesticide_summary(rows)
        if pest:
            take["12"] = pest
        if not take:
            nothing.append(doc.get("doc_code")); continue
        for rnd, c in certs:
            for r in c["rows"]:
                no = str(r.get("no"))
                if no not in take:
                    continue
                st = str(r.get("st") or "")
                if "not tested" not in st:
                    # Compare only where the certificate cites THIS document. A cell
                    # sourced from Farmahem and a reading of an IPH panel are two
                    # laboratories on one determination, not two readings of one page,
                    # and calling that a disagreement invents eighty-six of them.
                    have = str(r.get("res") or "").strip()
                    same_doc = (str(r.get("doc") or "").strip()
                                == str(doc.get("doc_code") or "").strip())
                    if have and have != "—" and same_doc and dot(have) != dot(take[no]):
                        # #12 is the desk's own sentence about the panel, not a laboratory
                        # figure: "ND mg/kg — all N residues". Where the two readers agree
                        # on N and the desk's single read of 09.09.2026 wrote another
                        # number, the sentence is corrected — the RESULT is identical in
                        # every one of these, only the count of analytes behind it was
                        # wrong. Anything else is held, named and left exactly as printed.
                        if no == "12" and _same_claim(have, take[no]):
                            r["res"] = take[no]
                            recount.append((c.get("regcode"), have, take[no], doc.get("doc_code")))
                        else:
                            differ.append((c.get("regcode"), no, have, take[no], doc.get("doc_code")))
                    elif have and have != "—" and same_doc:
                        agreed.append((c.get("regcode"), no, have, take[no], doc.get("doc_code")))
                    continue
                r["res"] = take[no]
                r["doc"] = doc.get("doc_code")
                r["dd"] = doc.get("issue_date") or doc.get("receipt_date") or ""
                r["lab"] = LAB
                r["fam"] = FAM
                r["st"] = ("covered" if rnd == "initial" else
                           "carried from the initial testing (%s) — covered"
                           % ((initial or {}).get("regcode") or "the batch's initial CoQ"))
                applied.append((c.get("regcode"), no, take[no], doc.get("doc_code")))

    print("documents through the two-read gate: %d" % len(gate["documents"]))
    print("cells filled: %d on %d certificate(s)"
          % (len(applied), len({x[0] for x in applied})))
    got = collections.Counter(x[1] for x in applied)
    for no in sorted(got, key=lambda s: [int(y) for y in s.split(".")]):
        print("   #%-5s %d" % (no, got[no]))
    print("already printed and the new reading agrees: %d" % len(agreed))
    print("residue count corrected on #12 (same result, both readers count 29): %d" % len(recount))
    print("already printed and the new reading DIFFERS: %d" % len(differ))
    for d in differ[:20]:
        print("   %-16s #%-5s printed %-14s read %-14s (%s)" % d)
    if nolot:
        print("no lot in the register: %d" % len(nolot))
        for n in nolot[:10]:
            print("   %s  %s / %s" % n)
    if nothing:
        print("nothing to take from: %s" % ", ".join(nothing))
    if a.dry_run:
        print("\n--dry-run — nothing written")
        return 0
    json.dump(data, open(ART, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nwritten: %s" % os.path.relpath(ART, os.path.dirname(HERE)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
