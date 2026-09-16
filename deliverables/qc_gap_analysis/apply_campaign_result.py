#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A reissue may cite its own campaign's certificate where the initial round has none.

    python3 deliverables/qc_gap_analysis/apply_campaign_result.py [--dry-run]

The ruling of 15.09.2026 sends a determination the retest did not run back to the
initial testing. For ten lots the initial testing has **no microbiology at all** — the
only microbiology on file is the IJZ-MB campaign's, and the repair of v35 rightly stops
a RELEASE certificate resting on a document issued after it. So the carry reached for an
initial result that does not exist, the cell stayed empty on **both** rounds, and the
certificate sat in the release register the whole time: `CoQ-PP_26-160` printed nothing
for #9.1–#9.5 with `539/1070/26` of 31.08.2026 on file and the reissue dated 21.09.2026.

A reissue is dated after its own campaign, so the objection that stops the release
certificate does not apply to it. Where a row is still empty and the release register
holds a document for that determination **issued on or before the reissue's own date**,
the reissue prints that result and cites that document — code, date and laboratory.

Nothing is invented and no certificate rests on a document that did not yet exist. This
only stops a result the desk holds from appearing on no certificate at all, which is
OI-38. A stability timepoint is never a source: it measures the lot ageing.
"""
import argparse, datetime as dt, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import result_vocabulary as RV          # the desk's one spelling per assertion
SRC = os.path.join(HERE, "coq_artifact_data.json")
# the release register's column letters, in the determination they report
COL_DET = {"E": "4", "G": "5", "H": "6", "I": "8", "J": "9.1", "K": "9.2", "L": "9.3",
           "M": "9.4", "N": "9.5", "O": "10.2", "P": "10.1", "Q": "10.3", "R": "11.1",
           "S": "11.2", "T": "11.3", "U": "11.4", "V": "12"}
BLANK = ("", "—")
# "<10^2 >10" — an upper bound then a lower one with no word between them. The pages
# the desk holds write the pair three ways; this gives the third the connector the
# other two print, so one controlled rule reads all of them.
_BARE_RANGE = re.compile(r"(<\s*10\S*)\s+(>\s*10\S*)")


def day(v):
    """A register date as a date, or None.

    >>> day("31.08.2026").isoformat()
    '2026-08-31'
    >>> day("") is None
    True
    """
    try:
        return dt.datetime.strptime(str(v).strip(), "%d.%m.%Y").date()
    except Exception:
        return None


def register_index(reg):
    """lot key -> determination -> [(date, code, laboratory, value)], stability excluded."""
    out = {}
    for b in reg:
        for cert in (b.get("certs") or []):
            if cert.get("stab"):
                continue
            d = day(cert.get("date"))
            if d is None:
                continue
            for col, val in (cert.get("vals") or {}).items():
                det = COL_DET.get(col)
                if not det:
                    continue
                for k in {str(b.get("cb") or "").strip(), str(b.get("pn") or "").strip()} - {""}:
                    out.setdefault(k, {}).setdefault(det, []).append(
                        (d, cert.get("code"), cert.get("lab"), val))
    return out


def listing_index(path=None):
    """The Head of QC's own eCoA spec listing: lot -> determination -> the citable rows.

    PP_Spec_Parameter_Listing.xlsx carries the determination number in its own № column —
    the desk's numbering exactly, 1 … 9.1 … 11.4 … 12 — so a result is placed by the
    listing's own mapping and never by a pattern read off the parameter's prose name.
    """
    import openpyxl
    path = path or os.path.join(
        os.path.dirname(os.path.dirname(HERE)), "ingestion", "coa_track",
        "letta-imb-coas", "exports", "PP_Spec_Parameter_Listing.xlsx")
    if not os.path.exists(path):
        return {}
    wb = openpyxl.load_workbook(path, read_only=True)
    rows = list(wb["Spec parameter listing"].iter_rows(min_row=3, values_only=True))
    wb.close()
    bad = {"", "\u2014", "-", "n/a", "none", "missing / not tested", "not tested", "missing"}
    out = {}
    for r in rows:
        batch, pn, no = str(r[2] or "").strip(), str(r[3] or "").strip(), str(r[8] or "").strip()
        res, code = str(r[10] or "").strip(), str(r[12] or "").strip()
        iss, lab = str(r[13] or "").strip(), str(r[14] or "").strip()
        if res.lower() in bad or code.lower() in bad:
            continue
        # An in-house result carries no certificate number on its page. The desk already
        # issues an internal certificate of analysis for exactly that, and every #1, #2
        # and #7 on every certificate cites one — so the row is kept and marked, and the
        # citation becomes the batch's own iCoA when it is written.
        inhouse = code.lower().startswith("n/a") or "in-house" in code.lower()
        d = day(iss)
        if d is None:
            continue
        for k in {batch, pn} - {""}:
            out.setdefault(k, {}).setdefault(no, []).append(
                (d, "\u0000iCoA" if inhouse else code, lab, res))
    return out


def apply(data, log=None):
    """Fill every reissue row the register can cite. Returns the rows changed."""
    have = register_index(data["reg"])
    listing = listing_index()
    changed = []
    for c in data["coqs"]:
        if not str(c.get("t") or "").startswith("additional"):
            continue
        iss = day(c.get("issue"))
        if iss is None:
            continue
        pool = (have.get(str(c.get("pp") or "").strip())
                or have.get(str(c.get("cb") or "").strip()) or {})
        for r in c["rows"]:
            if str(r.get("res") or "—").strip() not in BLANK:
                continue
            cands = [x for x in pool.get(r["no"], []) if x[0] <= iss]
            if not cands:
                # the Head of QC's own eCoA listing, where the register has nothing
                lp = (listing.get(str(c.get("pp") or "").strip())
                      or listing.get(str(c.get("cb") or "").strip()) or {})
                cands = [x for x in lp.get(r["no"], []) if x[0] <= iss]
            if not cands:
                continue
            d, code, lab, val = max(cands)          # the latest that may be cited
            if code == "\u0000iCoA":                   # an in-house result cites the iCoA
                code = str(c.get("icoa_code") or "").strip()
                lab = "Purely Plant GmbH (in-house)"
                if not code:
                    continue
            # the register holds the laboratory's own spelling — 5.2×10^2 CFU/g,
            # Одговара, < 10² и > 10 — and a certificate prints the desk's controlled
            # word for it, which is what every other row on the page has been through.
            # A microbiology range is written three ways on the pages the desk holds:
            # "< 10² и > 10", "< 10² and > 10" and, on the in-house sheets, a bare
            # "<10^2 >10" with the connector left out. The first two the controlled
            # vocabulary already reads; the third is given the connector the other two
            # print so it goes down the same path, rather than a fourth spelling.
            raw = str(val or "").strip()
            raw = _BARE_RANGE.sub("\\1 и \\2", raw)
            val = RV.bilingual(RV.canon(raw, r["no"]), r["no"])
            if str(val).strip() in BLANK:
                continue
            r["res"] = val
            r["doc"] = code or "—"
            r["dd"] = d.strftime("%d.%m.%Y")
            r["lab"] = lab or "—"
            r["st"] = "covered"
            changed.append((c.get("regcode"), c.get("pp") or c.get("cb"), r["no"], code,
                            d.strftime("%d.%m.%Y"), c.get("issue")))
    return changed


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--src", default=SRC)
    a = ap.parse_args(argv[1:])
    data = json.load(open(a.src, encoding="utf-8"))
    changed = apply(data)
    print("reissue rows that now cite their campaign's certificate: %d" % len(changed))
    for row in changed[:12]:
        print("   %-16s %-11s #%-5s %-13s of %s   (certificate of %s)" % row)
    if len(changed) > 12:
        print("   … and %d more" % (len(changed) - 12))
    if not a.dry_run and changed:
        with open(a.src, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        print("written:", a.src)
    return 0


if __name__ == "__main__":
    import doctest
    f, t = doctest.testmod()
    print("%d/%d doctests passed" % (t - f, t))
    raise SystemExit(main(sys.argv) if not f else 1)
