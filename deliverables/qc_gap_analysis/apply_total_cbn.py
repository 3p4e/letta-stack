#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#6 Total CBN, from the certificate the lot's cannabinoids already come from.

    python3 deliverables/qc_gap_analysis/apply_total_cbn.py [--dry-run]

Owner, 21.09.2026: *"There will be no empty space in the certificate of quality nor the
certificate of analysis — all parameter results must be filled in."*

#6 Total CBN was the largest single gap on the face of the certificates: 34 of 172 printed
a marker for it while the very same document already filled #4 Total Δ⁹-THC and #5 Total
CBD on the same lot.

THE CAUSE. The Center for Natural Products has two forms. The newer one prints
*Вкупно CBN\** — a total — and the desk takes it. The older one prints *Содржина на CBN*,
the free form, and no CBNA line at all. Forty-three certificates on the older form already
carry #6 on their certificate of quality; twenty-two identical ones did not, because those
records never went through the derivation. Not a difference in the evidence — a difference
in whether the evidence was read.

THE DERIVATION is the one `ingestion/ecoa_runner/build_coq.derive_totals()` already
applies, with its own vocabulary for what was done, and this script does not invent a
second one:

    computed              CBN and CBNA both reported → CBN + CBNA × 0.876
    free-form-only        CBN reported, CBNA not printed by the laboratory at all
    acid-not-quantified   CBNA printed but not quantified — never assumed zero

Every cell this fills is `free-form-only`: the older form has no CBNA row, so the content
the laboratory reports is the whole of what it measured. A printed total always wins over a
derivation, and a derived value close to its criterion is a LOWER BOUND and is held rather
than passed — `derive_totals` flags that, and none of these come near it: the criterion is
1.0 % w/w and the highest value here is 0.02 %.

The row cites the SAME document that already carries #4 and #5, because it is the same
determination on the same page. Nothing already printed is overwritten.
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import result_vocabulary as RV                                           # noqa: E402

ART = os.path.join(HERE, "coq_artifact_data.json")
CORPUS = os.path.join(ROOT, "ingestion", "ecoa_runner", "records_corpus.json")
K_CBNA = 0.876                    # CBNA -> CBN, the decarboxylation factor build_coq uses
CRITERION = 1.0                   # % w/w, QCSP 001
LOWER_BOUND_MARGIN = 0.8          # build_coq.LOWER_BOUND_MARGIN — hold near the criterion
WITHHELD = re.compile(r"not tested|to be performed|in-house CoA only", re.I)


def num(v):
    m = re.search(r"-?\d+(?:[.,]\d+)?", str(v or ""))
    return float(m.group(0).replace(",", ".")) if m else None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv[1:])

    corp = json.load(open(CORPUS, encoding="utf-8"))
    recs = corp if isinstance(corp, list) else (corp.get("records") or list(corp.values())[0])
    by = {}
    for r in recs:
        by[str(r.get("cert_code"))] = (r, {str(p.get("parameter")): p for p in (r.get("parameters") or [])})

    data = json.load(open(ART, encoding="utf-8"))
    filled, held, nodoc = [], [], []
    for c in data["coqs"]:
        rows = {x["no"]: x for x in c["rows"]}
        r6 = rows.get("6")
        if r6 is None:
            continue
        res6 = str(r6.get("res") or "").strip()
        if not (not res6 or res6 == "—" or WITHHELD.search(str(r6.get("st") or ""))):
            continue
        doc = next((str(rows[n].get("doc") or "").strip() for n in ("4", "5", "3")
                    if str(rows.get(n, {}).get("doc") or "").strip() not in ("", "—")), "")
        ent = by.get(doc)
        if not ent:
            nodoc.append((c["regcode"], c.get("pp") or c.get("cb"), doc or "no cannabinoid document"))
            continue
        rec, ps = ent
        if "total_cbn" in ps:                       # a printed total always wins
            printed, kind = ps["total_cbn"].get("result_printed"), "printed total"
        else:
            fr, ac = ps.get("cbn_free"), ps.get("cbna")
            if not fr:
                nodoc.append((c["regcode"], c.get("pp") or c.get("cb"), doc + " — no CBN line"))
                continue
            f, av = num(fr.get("result_printed")), num((ac or {}).get("result_printed"))
            if ac is not None and f is not None and av is not None:
                printed, kind = "%.2f" % round(f + av * K_CBNA, 2), "computed"
            elif ac is None:
                printed, kind = fr.get("result_printed"), "free-form-only"
            else:
                printed, kind = fr.get("result_printed"), "acid-not-quantified"
            # A derivation without the acid form is a LOWER bound: near the criterion it
            # cannot be concluded, so it is held rather than printed (build_coq's rule).
            if kind != "computed":
                v = num(printed)
                if v is not None and v >= LOWER_BOUND_MARGIN * CRITERION:
                    held.append((c["regcode"], doc, printed, "lower bound at %.2f vs %.2f" % (v, CRITERION)))
                    continue
        val = RV.canon(printed, "6")
        r6["res"] = val
        r6["doc"] = doc
        r6["dd"] = rows.get("4", {}).get("dd") or rows.get("5", {}).get("dd") or rec.get("date_of_issue") or ""
        r6["lab"] = rows.get("4", {}).get("lab") or rows.get("5", {}).get("lab") or ""
        r6["fam"] = rows.get("4", {}).get("fam") or ""
        r6["route"] = ""
        r6["st"] = "covered"
        r6["drv"] = kind
        filled.append((c["regcode"], c.get("pp") or c.get("cb"), doc, kind, val))

    print("#6 Total CBN — derived from the certificate that already carries #4 and #5")
    print("   filled: %d cell(s) on %d certificate(s)" % (len(filled), len({f[0] for f in filled})))
    for k, n in collections.Counter(f[3] for f in filled).most_common():
        print("      %-22s %d" % (k, n))
    print("   values: %s" % ", ".join("%s ×%d" % (v, n)
          for v, n in collections.Counter(f[4] for f in filled).most_common()))
    if held:
        print("   held — a lower bound too close to the %.1f %% criterion to conclude: %d" % (CRITERION, len(held)))
        for h in held:
            print("      %-15s %-12s %-8s %s" % h)
    if nodoc:
        print("   no cannabinoid certificate on file for the lot: %d" % len(nodoc))
        for n in nodoc[:12]:
            print("      %-15s %-12s %s" % n)
    if a.dry_run:
        print("\n--dry-run — nothing written")
        return 0
    json.dump(data, open(ART, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nwritten: coq_artifact_data.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
