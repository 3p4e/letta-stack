#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The sweep of 21.09.2026 reaches the certificates that print a marker for it.

    python3 deliverables/qc_gap_analysis/apply_sweep_2026-09-21.py [--dry-run]

Owner, 21.09.2026: *"There will be no empty space in the certificate of quality nor the
certificate of analysis — all parameter results must be filled in."*

The audit of 20.09.2026 held the owner's `eCoA_DATABASE` against every desk record and
found 24 laboratory scans in none of them. Fifteen stood behind a cell that prints a
marker. Ten of the fifteen passed the two-read gate in `intake_sweep_2026-09-21/`; five
are held because Google's free tier retired a key mid-run and they carry ONE read, which
is not a reading.

WHAT EACH DOCUMENT CERTIFIES — read from the page, not assumed from its family:

  131/0228/26 · 132/0229/26 · 137/0234/26   IJZ-MB microbiology   #9.1-9.5
  362/0692/26 · 407/0790/26 · 75/0118/26    IJZ-MB microbiology   #9.1-9.5
  227-18-М/26 Farmahem mycotoxins           #10.1 aflatoxin B1, #10.3 ochratoxin A
  031-1-К/26 Farmahem cannabinoids          #3 #4 #5 #6
  031-1-ГС/26 Farmahem loss on drying       #8
  328/2026 IJZ contaminant panel            #10.2, #11.1-11.4, #12

`227-18-М/26` is the one certificate of the thirty in its campaign that NEITHER reader
could extract on 16.09.2026. Both read it today, and it fills the reissue's aflatoxin B1
and ochratoxin A — which is the owner's own account of why the initial certificates lack
them: the release round ran one sub-parameter and the re-analysis campaign ran the panel.

Nothing already printed is overwritten. A cell that carries a figure is compared with the
new reading and reported as agreeing or differing; the company's signed record is not
rewritten here.
"""
import argparse
import collections
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import result_vocabulary as RV                                           # noqa: E402
import testing_series as TS                                              # noqa: E402

ART = os.path.join(HERE, "coq_artifact_data.json")
SPEC = os.path.join(HERE, "product_specifications_QCSP001.json")
VALIDATOR = os.path.join(os.path.dirname(os.path.dirname(HERE)), "ingestion", "ragflow",
                         "validate_ecoa_limits.py")


def _validator():
    """The acceptance-criterion rule, imported rather than written a third time.

    build_coq_schedule imports it with a note that it has already been got wrong twice,
    in both directions. A microbial enumeration criterion written as a bare power of ten
    is not that power: Ph. Eur. 5.1.4 reads 10⁴ CFU as a maximum acceptable count of
    20 000, and a result between the power and twice it is UNDETERMINED, not conforming.
    A fourth copy of that arithmetic here would be a fourth chance to get it wrong.
    """
    spec = importlib.util.spec_from_file_location("validate_ecoa_limits", VALIDATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


V = _validator()

# Values the two readers agreed on and the desk still will not print, with the reason.
# 75/0118/26 prints "< 10³ и 10² CFU/g" for the bile-tolerant count — the laboratory
# omitted the ">" and the string asserts nothing a certificate can carry. Both vendors
# read it faithfully; it is the PAGE that is malformed. A laboratory's record is not the
# desk's to repair, so the determination is left uncovered and put to the owner (OI-63).
# A panel determined on ONE sample prints whole or not at all — the owner's ruling behind
# verify_panels.py: "it's not possible that the same batch has only one parameter for
# microbiological purity stated as absent and the others missing". Taking four of the five
# and leaving the malformed one would print exactly that. So the whole panel is held and
# the question goes to the laboratory (OI-63); the four good values are not lost, they are
# waiting on one line being confirmed.
_MALFORMED = ("the page prints '< 10\u00b3 \u0438 10\u00b2 CFU/g' for the bile-tolerant count \u2014 the "
              "laboratory omitted the '>' and the range states nothing; a panel determined on one "
              "sample prints whole or not at all, so the other four are held with it")
_TWO_LOTS = ("the page names a Gorilla Glue sample and a Fat Bastard lot number "
             "(\u0421\u0435\u0440\u0438\u0458\u0430: FB032601) on consecutive lines, and both lots exist \u2014 "
             "FB032601 is CoQ-PP_26-081, GG032601 is CoQ-PP_26-082. Which lot the page "
             "certifies is a question for the laboratory, not a choice for the desk (OI-64)")
WITHHOLD = {("75/0118/26", n): _MALFORMED for n in ("9.1", "9.2", "9.3", "9.4", "9.5")}
WITHHOLD.update({("434/0848/26", n): _TWO_LOTS
                 for n in ("9.1", "9.2", "9.3", "9.4", "9.5")})
GATE = os.path.join(HERE, "intake_sweep_2026-09-21", "two_read_result.json")
IDS = os.path.join(HERE, "intake_sweep_2026-09-21", "drive_ids.json")
IPH = "IPH — Institute of Public Health"
FHM = "Farmahem"
LAB = {"IJZ-MB": (IPH, "IJZ-MB microbiology"), "IJZ": (IPH, "IPH mycotoxins, metals, pesticides"),
       "FHM": (FHM, "Farmahem — cannabinoids"), "FHM-M": (FHM, "Farmahem — mycotoxins")}

# The printed row -> the determination. Matched on the page's own words, lower-cased.
MICRO = [("9.1", "аеробни"), ("9.2", "габи"), ("9.3", "жолчка"),
         ("9.4", "salmonella"), ("9.5", "escherichia")]
METALS = [("11.1", "олово"), ("11.2", "кадмиум"), ("11.3", "арсен"), ("11.4", "жива")]
CANNA = [("5", "cannabidiol"), ("6", "cannabinol"), ("4", "tetrahydrocannabinol")]
MYCO = [("10.1", "aflatoxin b1"), ("10.3", "ochratoxin")]
IDENT_C = "identity by the HPLC cannabinoid profile on this certificate"
AFLA_TOTAL = "вкупни афлатоксини"
# Not taken from 328/2026: бакар (copper), which the specification has no criterion for,
# and the individual aflatoxins B2/G1/G2, which are not determinations of this panel.


def dot(v):
    return re.sub(r"(?<=\d),(?=\d)", ".", str(v or "").strip())


def det_of(printed, fam):
    """Which determination a printed row belongs to, by the page's own wording."""
    n = str(printed or "").strip().lower()
    if fam == "IJZ-MB":
        for no, w in MICRO:
            if w in n:
                return no
        return None
    if fam == "FHM-M":
        for no, w in MYCO:
            if w in n:
                return no
        return None
    if fam == "FHM":
        if "сушење" in n or "lod" in n:
            return "8"
        for no, w in CANNA:
            if w in n:
                return no
        return None
    if fam == "IJZ":                       # the contaminant panel
        for no, w in METALS:
            if n.startswith(w):
                return no
        if AFLA_TOTAL in n:
            return "10.2"
        if n.startswith("бакар") or n.startswith("пестициди вкупно"):
            return None
        return "pest"
    return None


def pesticide_summary(rows):
    """#12 as the panel's own summary: how many residues were run and what they all read."""
    res = [r for r in rows if r[0] == "pest"]
    if not res:
        return None
    spell = collections.Counter(RV.canon(str(r[1] or "").strip(), "12") for r in res)
    (top, n), = spell.most_common(1)
    if n == len(res):
        return "%s mg/kg — all %d residues" % (top, len(res))
    others = ", ".join("%s ×%d" % (k, v) for k, v in spell.most_common() if k != top)
    return "%s mg/kg — %d of %d residues; %s" % (top, n, len(res), others)


CRITERION = {}
for _d in json.load(open(SPEC, encoding="utf-8")).get("determinations", []):
    CRITERION[str(_d.get("no"))] = _d.get("criterion") or ""


def judge(no, value, crit=None):
    """The status a value earns against its own acceptance criterion.

    The same three outcomes build_coq_schedule.status_of gives, from the same helpers:
    a figure above the criterion is OUT OF SPECIFICATION, a counted figure between the
    literal power of ten and twice it is UNDETERMINED under Ph. Eur. 5.1.4, and anything
    else is covered. A value the laboratory itself bounds ("< 10") is not a measurement
    above anything and is never judged against the band.
    """
    text = str(value or "").strip()
    if text.startswith(("<", "\u2264")):
        return "covered"
    lim = V.acceptance_limit(crit or CRITERION.get(no, ""), no)
    got = V.magnitude(text)
    if not lim or got is None or not getattr(lim, "value", None):
        return "covered"
    if got > lim.value:
        return "OUT OF SPECIFICATION"
    if getattr(lim, "power", None) and got > lim.power:
        return "UNDETERMINED (Ph. Eur. 5.1.4)"
    return "covered"


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv[1:])

    gate = json.load(open(GATE, encoding="utf-8"))
    if gate["held"]:
        raise SystemExit("the gate holds %d field(s) — nothing is applied until a person "
                         "rules on them" % len(gate["held"]))
    ids = json.load(open(IDS, encoding="utf-8"))
    meta = {}
    for code, v in ids.items():
        meta[code.replace("/", "-").replace("*", "") + ".pdf"] = (v["p"], v["cu"], v["lab"])
    data = json.load(open(ART, encoding="utf-8"))

    by_lot = collections.defaultdict(list)
    for c in data["coqs"]:
        rnd = "retest" if str(c.get("t") or "").startswith("retest") else "initial"
        for k in (c.get("pp"), c.get("cb")):
            if k:
                by_lot[str(k).strip()].append((rnd, c))
    for v in by_lot.values():
        v.sort(key=lambda t: t[0] != "initial")

    applied, agreed, differ, nolot, nodet = [], [], [], [], []
    covered = []
    skipped_initial, flagged, withheld_vals = [], [], set()
    for scan, doc in sorted(gate["documents"].items()):
        if scan not in meta:
            nolot.append((scan, "no lot recorded in drive_ids.json")); continue
        p, cu, fam = meta[scan]
        lab, family = LAB[fam]
        certs = by_lot.get(p) or by_lot.get(cu) or by_lot.get(cu.rstrip("*")) or []
        if not certs:
            nolot.append((doc["doc_code"], "%s / %s not in the register" % (p, cu))); continue
        rows = [(det_of(x["printed"], fam), x["result"]) for x in doc["parameters"]]
        take = {}
        for no, val in rows:
            if no and no != "pest" and no not in take:
                take[no] = RV.canon(dot(val), no)
        pest = pesticide_summary(rows) if fam == "IJZ" else None
        if pest:
            take["12"] = pest
        if fam == "FHM" and any(n == "4" for n, _ in rows):
            take["3"] = IDENT_C            # the report identifies the profile it quantifies
        if not take:
            nodet.append(doc["doc_code"]); continue
        initial = next((c for r, c in certs if r == "initial"), None)
        # A document of a re-analysis campaign is a RETEST document whatever its code
        # series says (owner, 10.09.2026), and a release certificate may not rest on one:
        # 227-18-М/26 is dated 16.09.2026 and this lot's initial certificate was issued on
        # 06.06.2026, so filling it would put a June document's name on a September
        # reading. That is the defect v35 repaired, and testing_series.is_retest_only()
        # is the rule it was repaired with. The predicate for a re-analysis SERIES is
        # is_reanalysis(); is_retest_only() is the narrower one, for the IJZ-MB delivery
        # of 25/26.08.2026 whose codes carry no series at all.
        retest_only = TS.is_reanalysis(doc["doc_code"]) or TS.is_retest_only(doc["doc_code"])
        for rnd, c in certs:
            if retest_only and rnd == "initial":
                skipped_initial.append((c["regcode"], doc["doc_code"]))
                continue
            for r in c["rows"]:
                no = str(r.get("no"))
                if no not in take:
                    continue
                have = str(r.get("res") or "").strip()
                st = str(r.get("st") or "")
                withheld = (not have or have == "—"
                            or re.search("not tested|to be performed|in-house CoA only", st, re.I))
                if not withheld:
                    same = str(r.get("doc") or "").strip() == str(doc["doc_code"]).strip()
                    if not same:
                        # Another document already covers this determination. Nothing was
                        # compared, so this is not agreement and must not be counted as it.
                        covered.append((c["regcode"], no, r.get("doc"), doc["doc_code"]))
                    elif dot(have) != dot(take[no]):
                        differ.append((c["regcode"], no, have, take[no], doc["doc_code"]))
                    else:
                        agreed.append((c["regcode"], no, have, take[no], doc["doc_code"]))
                    continue
                if (doc["doc_code"], no) in WITHHOLD:
                    withheld_vals.add((doc["doc_code"], no))
                    continue
                r["res"] = take[no]
                r["doc"] = doc["doc_code"]
                r["dd"] = doc["issue_date"]
                r["lab"] = lab
                r["fam"] = family
                r["route"] = ""
                verdict = judge(no, take[no], r.get("crit"))
                r["st"] = (verdict if rnd == "initial" else
                           "carried from the initial testing (%s) — %s"
                           % ((initial or {}).get("regcode") or "the batch's initial CoQ", verdict))
                applied.append((c["regcode"], no, take[no], doc["doc_code"]))
                if verdict != "covered":
                    flagged.append((c["regcode"], no, take[no], verdict))

    print("documents through the two-read gate: %d   held on one read: %d"
          % (len(gate["documents"]), len(gate["read_once"])))
    print("cells filled: %d on %d certificate(s)"
          % (len(applied), len({x[0] for x in applied})))
    got = collections.Counter(x[1] for x in applied)
    for no in sorted(got, key=lambda s: [float(y) for y in s.split(".")]):
        print("   #%-5s %d" % (no, got[no]))
    if skipped_initial:
        print("not put on a release certificate \u2014 a re-analysis document is a retest "
              "document: %d" % len(skipped_initial))
        for k in sorted(set(skipped_initial)):
            print("   %-16s would have cited %s" % k)
    if flagged:
        print("judged against the criterion rather than passed as covered: %d" % len(flagged))
        for k in flagged:
            print("   %-16s #%-5s %-20s %s" % k)
    if withheld_vals:
        print("read by both and still NOT printed \u2014 the page itself is malformed:")
        for k in sorted(withheld_vals):
            print("   %s #%s \u2014 %s" % (k[0], k[1], WITHHOLD[k]))
    if covered:
        print("the cell is already covered by ANOTHER document, so nothing was "
              "compared: %d" % len(covered))
        for k in sorted({(x[0], str(x[2]), x[3]) for x in covered}):
            print("   %-16s carries %-14s the sweep read %s" % k)
    print("already printed, and the new reading agrees: %d" % len(agreed))
    print("already printed, and the new reading DIFFERS: %d" % len(differ))
    for d in differ[:20]:
        print("   %-16s #%-5s printed %-20s read %-20s (%s)" % d)
    for n in nolot + [(x, "no determination this desk carries") for x in nodet]:
        print("   not applied: %s — %s" % n)
    if a.dry_run:
        print("\n--dry-run — nothing written")
        return 0
    json.dump(data, open(ART, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nwritten: coq_artifact_data.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
