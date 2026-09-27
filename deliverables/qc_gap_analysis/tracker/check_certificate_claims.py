#!/usr/bin/env python3
"""No certificate states a certification the Head of QC has not authorised.

    python3 deliverables/qc_gap_analysis/tracker/check_certificate_claims.py

What happened. On 21.09.2026 the desk wrote "MK GMP Certified Facility" into the empty
bottom-right footer slot of the certificate-of-quality base page and into the internal
certificate's footer, on the authority of a design-system README ("locked business rules:
Header/footer say MK GMP Certified Facility"). A design system governs colour, type and
layout; it has no authority over what a certificate claims. The Head of QC had already had
"MK GMP Certified" taken off the laboratory line on 17.09.2026, and on 27.09.2026, finding
it in the footer: "hell no. from where did MK GMP Certified Facility came from".

What this checks. The printed text (styles, scripts and comments removed) of every page a
build may still change: each certificate of quality outside Tranches 1 and 2 (issued, with
the customer, not touched — Head of QC, 26.09.2026), every page of the Tranche 3 delivery,
and the blank templates new certificates are drawn from. A certification, accreditation or
GMP statement about Purely Plant is refused there unless the Head of QC has ruled it in.
The external laboratories' own accreditation lines (ISO/IEC 17025, LT-005, LT-083) are
statements about them, copied from their certificates, and are not matched.

Exit 1 on any finding.
"""
import csv, glob, html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)

# Phrases that claim a certification for Purely Plant. None is authorised today.
BANNED = re.compile(r"GMP[\s\-]*Certified|MK\s+GMP|EU\s+GMP|GMP\s+facility|"
                    r"ДПП\s+сертифицира|сертифицирана\s+ДПП", re.I)


def printed_text(src):
    s = re.sub(r"<style\b.*?</style>|<script\b.*?</script>|<!--.*?-->", " ", src, flags=re.S | re.I)
    return html.unescape(re.sub(r"<[^>]+>", " ", s))


def frozen_lots():
    """Lots whose pages are issued (T1/T2), read as the page builder reads them."""
    tr18 = {}
    with open(os.path.join(GAP, "intake_tranches_2026-09-18", "drive_folders_2026-09-18.tsv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            f, t = r["folder"], r["tranche"]
            tail = f.rsplit("_", 1)[-1]
            if re.match(r"^[PJ]\d{5,6}$", tail):
                tr18[tail] = t
            tr18[f] = t
            tr18.setdefault(re.sub(r"_P\d{6}$", "", f).rstrip("_").replace("＊", ""), t)
    scope = {}
    for name in ("coq_reissue_scope_2026-09-15.csv", "coq_draft_scope_2026-09-10.csv"):
        p = os.path.join(HERE, name)
        if os.path.exists(p):
            for r in csv.DictReader(open(p, encoding="utf-8")):
                if r.get("p_lot"):
                    scope.setdefault(r["p_lot"], r.get("tranche", ""))

    def frozen(c):
        for k in (c.get("pp"), c.get("cb"), (c.get("cb") or "").replace("＊", "")):
            if k and k in tr18:
                return tr18[k] in ("T1", "T2")
        return any(re.sub(r"\D", "", str(scope.get(k, ""))) in ("1", "2") for k in (c.get("pp"), c.get("cb")) if k)
    return frozen


def main():
    reg = {c["regcode"]: c for c in json.load(open(os.path.join(GAP, "coq_artifact_data.json"), encoding="utf-8"))["coqs"]}
    frozen = frozen_lots()
    pages = []
    for p in glob.glob(os.path.join(GAP, "design_handoff", "out", "**", "CoQ-PP_26-*.html"), recursive=True):
        m = re.search(r"(CoQ-PP_26-\d{3})", os.path.basename(p))
        c = reg.get(m.group(1)) if m else None
        if c is None or not frozen(c):
            pages.append(p)
    pages += glob.glob(os.path.join(GAP, "DELIVER_2026-09-26_T3", "**", "*.html"), recursive=True)
    pages += glob.glob(os.path.join(GAP, "BLANK_TEMPLATES", "*.html"))
    bad = []
    for p in sorted(set(pages)):
        for m in BANNED.finditer(printed_text(open(p, encoding="utf-8").read())):
            bad.append((os.path.relpath(p, GAP), m.group(0)))
    print("certification claims: %d pages read, %d findings" % (len(set(pages)), len(bad)))
    for p, s in bad[:40]:
        print("   CLAIM  %s: %r" % (p, s))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
