#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Is the master workbook full enough to compile the CoQ and the iCoA?

    python3 verify_fullness.py                      # newest CoQ_Analysis_Master_v*.xlsx beside it
    python3 verify_fullness.py WORKBOOK.xlsx        # a named one
    python3 verify_fullness.py --md FULLNESS.md     # also write the report
    python3 verify_fullness.py --baseline b.json    # the measured counts, as JSON

Eight checks, A to H. Each prints its findings as

    [sheet] what — detail

and the run ends with a count. Exit 0 clean, 1 with findings, 2 when a check could not be
performed at all — a false clean is worse than no answer.

## Self-contained on purpose

This file has no imports from the repository: stdlib and openpyxl, nothing else. Drop it in a
folder with `CoQ_Analysis_Master_v56.xlsx` and it runs. The repository has richer machinery for
all of this — `reference_sections.latest_master`, `verify_workbook.table`, `batch_id.batch_key`,
`tracker_data.nkey` — and a checker that lives *in* the tree should use it. This one is meant to
travel.

## The one thing that will otherwise waste a day

Several register columns are live Excel formulas, and openpyxl stores no cached value for them:
read with data_only=True and `CoQ code`, `iCoA (register)` and `CoQ (register)` all come back
None. A checker that takes that at face value reports gaps that are not there. Two of those
columns carry the iCoA-to-CoQ link, which is check H — the whole point of the exercise.

So H does not read them. Both registers also carry a **literal** `Key` of the form `CJ1024|I`,
`P050202|R3` — lot and testing round — and that is what the join runs on. The CoQ code itself is
reconstructed from the rule its own formula states (build_tracker_v8.py:2727): walk the register
top to bottom and number the issuable rows. No LibreOffice, no recalculation, nothing assumed.
"""
import collections
import datetime
import glob
import json
import os
import re
import sys

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))

# A cell that says nothing. The em-dash is the workbook's own "not applicable" and must not be
# mistaken for a value — eleven results hang on that distinction.
EMPTY = {None, "", "—", "-", "N/A", "n/a"}

# A result may be absent, but only in one of three controlled ways. Anything else in the Result
# column that is not a measurement is a vocabulary breach, not an absence.
ABSENCE = (
    "not tested",
    "upon request",
    "carried from the initial testing",
)

# One laboratory, one name. The short forms are the same institutions under an abbreviation; a
# certificate that names the laboratory differently from its neighbour names it wrongly on one
# of the two.
CANON = {
    "IJZ": "IPH — Institute of Public Health",
    "CNP": "UKIM Faculty of Pharmacy — Center for Natural Products",
    "FHM": "Farmahem",
}

ISSUABLE = {"yes", "allocated", "ruled"}     # the states the CoQ numbering counts


def find_workbook(argv):
    """The workbook to audit: named on the command line, or the newest one lying about."""
    named = [a for a in argv if a.lower().endswith(".xlsx")]
    if named:
        return named[0]
    seen = []
    for where in (HERE, os.path.join(HERE, ".."), os.path.join(HERE, "tracker"), os.getcwd()):
        seen += glob.glob(os.path.join(where, "CoQ_Analysis_Master_v*.xlsx"))
    if not seen:
        return None

    def ver(p):
        m = re.search(r"_v(\d+)", os.path.basename(p))
        return int(m.group(1)) if m else -1

    return max(seen, key=ver)


def table(ws):
    """Rows of a sheet as dicts, header from row 1.

    The workbook ends several sheets with a merged footnote — one long string in the first
    column and nothing beside it. It is prose, not a row, and counting it as one has bitten
    scripts here before, so it is dropped.
    """
    it = ws.iter_rows(values_only=True)
    head = [str(h) if h is not None else "" for h in next(it)]
    out = []
    for r in it:
        if all(c in EMPTY for c in r):
            continue
        if len(r) > 1 and isinstance(r[0], str) and len(r[0]) > 120 and all(c in EMPTY for c in r[1:]):
            continue
        out.append(dict(zip(head, r)))
    return out


def blank(v):
    return (v.strip() if isinstance(v, str) else v) in EMPTY


def is_absence(result):
    low = str(result).strip().lower()
    return any(low.startswith(a) for a in ABSENCE)


def as_date(s):
    if isinstance(s, datetime.datetime):
        return s.date()
    if isinstance(s, datetime.date):
        return s
    try:
        return datetime.datetime.strptime(str(s).strip(), "%d.%m.%Y").date()
    except ValueError:
        return None


class Report(object):
    """Findings, and the prose that goes around them."""

    def __init__(self):
        self.findings = []
        self.lines = []
        self.stopped = []

    def say(self, text=""):
        self.lines.append(text)

    def find(self, sheet, what, detail=""):
        self.findings.append((sheet, what, detail))
        print("[%s] %s%s" % (sheet, what, " — " + detail if detail else ""))

    def cannot(self, what, why):
        self.stopped.append((what, why))
        print("[could not verify] %s — %s" % (what, why))


# ----------------------------------------------------------------------------- the eight checks

def check_grid(rep, long_rows):
    """A — the grid is whole, and no result cell is blank."""
    per = collections.Counter(r["CoQ code"] for r in long_rows)
    sizes = collections.Counter(per.values())
    rep.say("| rows | %d |" % len(long_rows))
    rep.say("| certificates | %d |" % len(per))
    rep.say("| determinations per certificate | %s |"
            % " · ".join("%d on %d" % (k, v) for k, v in sorted(sizes.items())))
    if len(sizes) > 1:
        for code, n in sorted(per.items()):
            if n != sizes.most_common(1)[0][0]:
                rep.find("CoQ Compilation (long)", "short panel",
                         "%s carries %d determinations" % (code, n))
    empty = [r for r in long_rows if blank(r["Result"])]
    rep.say("| blank result cells | %d |" % len(empty))
    for r in empty[:20]:
        rep.find("CoQ Compilation (long)", "blank result",
                 "%s #%s %s" % (r["CoQ code"], r["#"], r["Parameter"]))
    return per


def check_absence(rep, long_rows):
    """B — every absence is one of the three controlled forms."""
    absent = [r for r in long_rows if is_absence(r["Result"])]
    forms = collections.Counter(str(r["Result"]).strip() for r in absent)
    rep.say("| results stated | %d |" % (len(long_rows) - len(absent)))
    rep.say("| absence markers | %d |" % len(absent))
    for form, n in forms.most_common():
        rep.say("| &nbsp;&nbsp;`%s` | %d |" % (form, n))
    if len(forms) > len(ABSENCE):
        for form, n in forms.most_common():
            if not any(form.lower().startswith(a) for a in ABSENCE):
                rep.find("CoQ Compilation (long)", "uncontrolled absence wording",
                         "%r on %d row(s)" % (form, n))
    return [r for r in long_rows if not is_absence(r["Result"])]


def check_provenance(rep, stated):
    """C — every stated result names its laboratory, its document, its date and its method."""
    need = ("Method", "Acceptance criterion", "Laboratory", "Document", "Issued")
    counts = {k: sum(1 for r in stated if not blank(r[k])) for k in need}
    for k in need:
        rep.say("| %s | %d / %d |" % (k, counts[k], len(stated)))
    bad = [r for r in stated
           if blank(r["Laboratory"]) or blank(r["Document"]) or blank(r["Issued"])]
    for r in bad:
        rep.find("CoQ Compilation (long)", "result stated without provenance",
                 "%s #%s %s · status %r" % (r["CoQ code"], r["#"],
                                            str(r["Parameter"])[:34], str(r["Status"])[:48]))
    missing_method = [r for r in stated if blank(r["Method"]) or blank(r["Acceptance criterion"])]
    for r in missing_method:
        rep.find("CoQ Compilation (long)", "result stated without a method or criterion",
                 "%s #%s" % (r["CoQ code"], r["#"]))
    return bad


def check_institutions(rep, stated):
    """D — one laboratory, one name."""
    labs = collections.Counter(str(r["Laboratory"]).strip() for r in stated)
    for name, n in labs.most_common():
        rep.say("| %s | %d |" % (name, n))
    short = 0
    for alias, full in CANON.items():
        if labs.get(alias):
            short += labs[alias]
            where = sorted({r["CoQ code"] for r in stated
                            if str(r["Laboratory"]).strip() == alias})
            rep.find("CoQ Compilation (long)", "laboratory under two names",
                     "%r on %d row(s) is %r, which %d row(s) spell in full · %s"
                     % (alias, labs[alias], full, labs.get(full, 0),
                        ", ".join(where[:6]) + ("…" if len(where) > 6 else "")))
    rep.say("| rows carrying a short form | %d |" % short)
    return short


def check_methods(rep, stated):
    """E — the analysis reference: one method per document and determination, and the story the
    method string tells about itself."""
    by_det = collections.defaultdict(lambda: collections.Counter())
    for r in stated:
        by_det[str(r["#"])][str(r["Method"])] += 1
    multi = {k: v for k, v in by_det.items() if len(v) > 1}
    rep.say("| determinations carrying more than one method | %d of %d |"
            % (len(multi), len(by_det)))
    for det in sorted(multi, key=lambda d: (len(d), d)):
        rep.say("| &nbsp;&nbsp;#%s | %s |"
                % (det, " · ".join("%d × %s" % (n, m[:58]) for m, n in multi[det].most_common())))

    # Within one document a determination must have been run one way. This is the check that
    # says whether the split is a real difference between documents or a data fault.
    clash = collections.defaultdict(set)
    for r in stated:
        if not blank(r["Document"]):
            clash[(str(r["Document"]).strip(), str(r["#"]))].add(str(r["Method"]))
    clashes = {k: v for k, v in clash.items() if len(v) > 1}
    rep.say("| document + determination pairs citing two methods | %d |" % len(clashes))
    for (doc, det), methods in sorted(clashes.items())[:20]:
        rep.find("CoQ Compilation (long)", "one document, two methods for one determination",
                 "%s #%s · %s" % (doc, det, " | ".join(sorted(m[:40] for m in methods))))

    # The DAB rows say in their own text that they predate an accreditation. Test that claim.
    dab = [r for r in stated if "DAB 2018" in str(r["Method"])]
    if dab:
        labs = sorted({str(r["Laboratory"]).strip() for r in dab})
        same_lab = [r for r in stated
                    if str(r["Laboratory"]).strip() in labs and "DAB 2018" not in str(r["Method"])]
        dd = sorted(d for d in (as_date(r["Issued"]) for r in dab) if d)
        od = sorted(d for d in (as_date(r["Issued"]) for r in same_lab) if d)
        rep.say("| DAB 2018 rows | %d, %s .. %s, laboratories: %s |"
                % (len(dab), dd[0] if dd else "?", dd[-1] if dd else "?", ", ".join(labs)))
        if dd and od:
            rep.say("| the same laboratories' Ph. Eur. rows | %d, %s .. %s |"
                    % (len(od), od[0], od[-1]))
            before = [d for d in od if d < dd[-1]]
            if before and "before its Ph. Eur" in " ".join(str(r["Method"]) for r in dab[:50]):
                rep.find("CoQ Compilation (long)",
                         "the method text claims a date boundary the dates do not have",
                         "the DAB string reads \"before its Ph. Eur. 3028 accreditation\", but %d "
                         "row(s) of the same laboratories carry the Ph. Eur. method with an issue "
                         "date earlier than the last DAB row (%s)" % (len(before), dd[-1]))
    return multi


def check_receipt(rep, stated):
    """F — the date the laboratory received the sample, where it is missing.

    Two kinds of row are not findings here and are excluded from the count rather than
    explained away in a footnote. A determination performed **in house** is not sent anywhere,
    so there is no institution to receive it and no receipt date to give — the absence is the
    fact, not a gap. And a row with no laboratory at all is already reported by check C; saying
    it twice buries the eleven rows that matter under a second copy of themselves.
    """
    external = [r for r in stated
                if not blank(r["Laboratory"]) and "in-house" not in str(r["Laboratory"]).lower()]
    rep.say("| stated results | %d |" % len(stated))
    rep.say("| &nbsp;&nbsp;performed in house — no receipt date applies | %d |"
            % sum(1 for r in stated if "in-house" in str(r["Laboratory"]).lower()))
    rep.say("| &nbsp;&nbsp;no laboratory named — reported by check C | %d |"
            % sum(1 for r in stated if blank(r["Laboratory"])))
    miss = [r for r in external if blank(r["Received by the laboratory"])]
    rep.say("| **sent out, with no receipt date** | **%d of %d** |" % (len(miss), len(external)))
    by = collections.Counter((str(r["Laboratory"]).strip(), str(r["#"])) for r in miss)
    for (lab, det), n in by.most_common(12):
        rep.say("| &nbsp;&nbsp;%s · #%s | %d |" % (lab, det, n))
    whole = collections.Counter(str(r["Laboratory"]).strip() for r in miss)
    tot = collections.Counter(str(r["Laboratory"]).strip() for r in external)
    for lab, n in whole.most_common():
        if n == tot[lab]:
            rep.find("CoQ Compilation (long)",
                     "an external laboratory with no sample-receipt date on any result",
                     "%s — all %d stated results" % (lab, n))
    return len(miss)


def check_icoa_inputs(rep, icoa_rows, formula_cols):
    """G — what an iCoA needs in order to be compiled, for each issuable one."""
    issuable = [r for r in icoa_rows if str(r.get("Issuable", "")).strip() == "yes"]
    rep.say("| iCoA rows | %d |" % len(icoa_rows))
    rep.say("| issuable | %d |" % len(issuable))
    if not issuable:
        rep.cannot("iCoA compilation inputs", "no issuable rows found on iCoA Register")
        return issuable
    needed = ["iCoA scope", "Basis date", "Harvest", "Packaging",
              "#1 Ident. A", "#2 Ident. B", "#7 Foreign matter",
              "Ident C — covered by (eCoA)", "Strain", "CU Batch", "Series"]
    for col in needed:
        if col in formula_cols:                       # never counted: openpyxl sees no value
            rep.say("| %s | formula column, not audited here |" % col)
            continue
        if col not in issuable[0]:
            rep.find("iCoA Register", "column the iCoA needs is absent", col)
            continue
        gaps = [r for r in issuable if blank(r[col])]
        rep.say("| %s | %d / %d |" % (col, len(issuable) - len(gaps), len(issuable)))
        if col in ("iCoA scope", "#1 Ident. A", "#2 Ident. B", "#7 Foreign matter", "Basis date"):
            for r in gaps[:10]:
                rep.find("iCoA Register", "an iCoA cannot be compiled without %s" % col,
                         str(r.get("iCoA code") or r.get("Key")))
    # The scope is what the iCoA's Result column is allowed to carry, so it decides what a
    # folder of iCoA documents must be checked against. It is NOT the same on all 172.
    scopes = collections.Counter(str(r["iCoA scope"]).strip() for r in issuable
                                 if not blank(r.get("iCoA scope")))
    for s, n in scopes.most_common():
        rep.say("| &nbsp;&nbsp;scope `%s` | %d |" % (s, n))
    if len(scopes) > 1:
        usual = scopes.most_common(1)[0][0]
        for r in issuable:
            if str(r.get("iCoA scope", "")).strip() not in ("", usual):
                rep.find("iCoA Register", "an iCoA whose scope is wider than the other %d"
                                          % scopes[usual],
                         "%s (%s) · %s" % (r.get("iCoA code"), r.get("Key"),
                                           str(r["iCoA scope"])))
    return issuable


def coq_codes(coq_rows):
    """The CoQ code of every register row, by the rule the register's own formula states.

    build_tracker_v8.py:2727 writes
        No.  = IF(OR(Issuable="yes","allocated","ruled"), COUNT(A$1:A_prev)+1, "")
        code = IF(No.<>"", "CoQ-PP_26-" & TEXT(No.,"000"), "— at issue —")
    so the code is nothing more than the position of a row among the issuable ones. Reconstructing
    it beats recalculating the workbook: same answer, no LibreOffice, and it fails loudly if the
    rule ever changes, because the count stops matching the register's own row total.
    """
    n = 0
    out = []
    for r in coq_rows:
        if str(r.get("Issuable", "")).strip().lower() in ISSUABLE:
            n += 1
            out.append("CoQ-PP_26-%03d" % n)
        else:
            out.append(None)
    return out


def check_linkage(rep, coq_rows, icoa_rows, long_codes):
    """H — one iCoA for every certificate of quality, initial release and every retest."""
    codes = coq_codes(coq_rows)
    live = [(c, r) for c, r in zip(codes, coq_rows) if c]
    rep.say("| CoQ register rows | %d |" % len(coq_rows))
    rep.say("| numbered (issuable) | %d |" % len(live))
    rep.say("| distinct CoQ codes in CoQ Compilation (long) | %d |" % len(long_codes))

    if len(live) != len(long_codes):
        rep.find("CoQ Register", "the register and the compilation disagree on how many "
                                 "certificates there are",
                 "register numbers %d, compilation carries %d" % (len(live), len(long_codes)))
    unnumbered = {c for c in long_codes} - {c for c, _ in live}
    for c in sorted(unnumbered)[:10]:
        rep.find("CoQ Compilation (long)", "certificate compiled but not numbered in the register", c)

    # The join. Both registers carry a literal Key — lot and testing round, `CJ1024|I`,
    # `P050202|R3` — so the link needs neither of the formula columns.
    if "Key" not in coq_rows[0] or "Key" not in icoa_rows[0]:
        rep.cannot("one iCoA per CoQ", "no literal Key column on both registers")
        return
    ckeys = collections.Counter(str(r["Key"]).strip() for c, r in live)
    ikeys = collections.Counter(str(r["Key"]).strip() for r in icoa_rows
                                if str(r.get("Issuable", "")).strip() == "yes")
    rep.say("| issuable CoQ keys | %d (%d distinct) |" % (sum(ckeys.values()), len(ckeys)))
    rep.say("| issuable iCoA keys | %d (%d distinct) |" % (sum(ikeys.values()), len(ikeys)))

    for key, n in sorted(ckeys.items()):
        if n > 1:
            rep.find("CoQ Register", "one key numbered more than once", "%s × %d" % (key, n))
    for key, n in sorted(ikeys.items()):
        if n > 1:
            rep.find("iCoA Register", "one key issued more than once", "%s × %d" % (key, n))
    for key in sorted(set(ckeys) - set(ikeys)):
        rep.find("iCoA Register", "a certificate of quality with no internal certificate", key)
    for key in sorted(set(ikeys) - set(ckeys)):
        rep.find("iCoA Register", "an internal certificate with no certificate of quality", key)

    rounds = collections.Counter(k.split("|")[-1] for k in ckeys)
    rep.say("| by testing round | %s |"
            % " · ".join("%s %d" % (r, n) for r, n in sorted(rounds.items())))

    # A lot that carries round R4 but no R2 or R3 is either a campaign label — the rounds are
    # named after the testing campaign, and a lot simply was not in the earlier ones — or a
    # sequence with holes in it. The workbook does not say which, so this is reported as a
    # question and not as a defect.
    by_lot = collections.defaultdict(set)
    for k in ckeys:
        lot, _, rd = k.rpartition("|")
        by_lot[lot].add(rd)
    holes = {}
    for lot, rds in by_lot.items():
        nums = sorted(int(x[1:]) for x in rds if re.fullmatch(r"R\d+", x))
        if nums and min(nums) > 2:
            holes[lot] = sorted(rds)
    if holes:
        rep.find("CoQ Register", "a retest round with no lower round on file",
                 "%s — if the round is a campaign label this is expected; if it counts this "
                 "lot's retests, the earlier ones are missing"
                 % " · ".join("%s %s" % (l, "/".join(v)) for l, v in sorted(holes.items())))
    matched = len(set(ckeys) & set(ikeys))
    rep.say("| **matched one to one** | **%d ↔ %d** |" % (matched, matched))


# ------------------------------------------------------------------------------------- the run

SECTIONS = [
    ("A", "The grid is whole"),
    ("B", "Absence is stated in a controlled way"),
    ("C", "Every stated result carries its provenance"),
    ("D", "One laboratory, one name"),
    ("E", "The analysis reference"),
    ("F", "The sample-receipt date"),
    ("G", "What an iCoA needs in order to be compiled"),
    ("H", "One iCoA for every certificate of quality"),
]


def formula_columns(path, sheet):
    """Columns whose first data row holds a formula — openpyxl caches no value for these."""
    wb = openpyxl.load_workbook(path, data_only=False, read_only=True)
    if sheet not in wb.sheetnames:
        return set()
    ws = wb[sheet]
    it = ws.iter_rows(values_only=True)
    head = [str(h) if h is not None else "" for h in next(it)]
    try:
        first = next(it)
    except StopIteration:
        return set()
    out = {head[i] for i, c in enumerate(first)
           if isinstance(c, str) and c.startswith("=") and i < len(head)}
    wb.close()
    return out


def baseline(path, long_rows, icoa_rows, coq_rows):
    """The measured counts, so a later run can prove it read the same workbook.

    Every number here is computed from the workbook on the spot. Nothing is carried in the file
    as a constant, because a baseline that was typed rather than measured is a way of being wrong
    twice.
    """
    stated = [r for r in long_rows if not is_absence(r["Result"])]
    codes = coq_codes(coq_rows)
    ckeys = {str(r["Key"]).strip() for c, r in zip(codes, coq_rows) if c}
    ikeys = {str(r["Key"]).strip() for r in icoa_rows
             if str(r.get("Issuable", "")).strip() == "yes"}
    return {
        "workbook": os.path.basename(path),
        "measured": datetime.date.today().isoformat(),
        "compilation_long_rows": len(long_rows),
        "certificates": len({r["CoQ code"] for r in long_rows}),
        "determinations_per_certificate":
            sorted(collections.Counter(collections.Counter(
                r["CoQ code"] for r in long_rows).values()).items()),
        "blank_result_cells": sum(1 for r in long_rows if blank(r["Result"])),
        "results_stated": len(stated),
        "absence_markers": dict(collections.Counter(
            str(r["Result"]).strip() for r in long_rows if is_absence(r["Result"]))),
        "provenance_complete": sum(1 for r in stated if not (
            blank(r["Laboratory"]) or blank(r["Document"]) or blank(r["Issued"]))),
        "method_stated": sum(1 for r in stated if not blank(r["Method"])),
        "criterion_stated": sum(1 for r in stated if not blank(r["Acceptance criterion"])),
        "receipt_date_missing": sum(1 for r in stated
                                    if blank(r["Received by the laboratory"])),
        "laboratories": dict(collections.Counter(
            str(r["Laboratory"]).strip() for r in stated)),
        "icoa_rows": len(icoa_rows),
        "icoa_issuable": len(ikeys),
        "coq_numbered": sum(1 for c in codes if c),
        "icoa_to_coq_matched": len(ckeys & ikeys),
        "rounds": dict(collections.Counter(k.rsplit("|", 1)[-1] for k in ckeys)),
        "icoa_scopes": dict(collections.Counter(
            str(r["iCoA scope"]).strip() for r in icoa_rows
            if str(r.get("Issuable", "")).strip() == "yes" and not blank(r.get("iCoA scope")))),
    }


def main(argv):
    path = find_workbook(argv[1:])
    if not path:
        print("no CoQ_Analysis_Master_v*.xlsx found beside this script or in the current folder")
        return 2
    print("workbook: %s" % os.path.abspath(path))

    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    rep = Report()
    rep.say("# Fullness of the master workbook")
    rep.say()
    rep.say("`%s` — audited %s by `verify_fullness.py`."
            % (os.path.basename(path), datetime.date.today().strftime("%d.%m.%Y")))
    rep.say()
    rep.say("The question is the owner's: *is every analysis result there, and is there enough "
            "in the workbook to compile both the certificate of quality and the internal "
            "certificate of analysis?* Eight checks answer it. A finding names its rows.")

    need = ["CoQ Compilation (long)", "iCoA Register", "CoQ Register"]
    absent = [s for s in need if s not in wb.sheetnames]
    if absent:
        for s in absent:
            rep.cannot("the audit", "sheet %r is not in this workbook" % s)
        return 2

    long_rows = [r for r in table(wb["CoQ Compilation (long)"]) if r.get("CoQ code")]
    icoa_rows = table(wb["iCoA Register"])
    coq_rows = table(wb["CoQ Register"])
    icoa_formula = formula_columns(path, "iCoA Register")

    results = {}
    for letter, title in SECTIONS:
        rep.say()
        rep.say("## %s · %s" % (letter, title))
        rep.say()
        rep.say("| | |")
        rep.say("| --- | --- |")
        before = len(rep.findings)
        if letter == "A":
            results["per"] = check_grid(rep, long_rows)
        elif letter == "B":
            results["stated"] = check_absence(rep, long_rows)
        elif letter == "C":
            check_provenance(rep, results["stated"])
        elif letter == "D":
            check_institutions(rep, results["stated"])
        elif letter == "E":
            check_methods(rep, results["stated"])
        elif letter == "F":
            check_receipt(rep, results["stated"])
        elif letter == "G":
            check_icoa_inputs(rep, icoa_rows, icoa_formula)
        elif letter == "H":
            check_linkage(rep, coq_rows, icoa_rows, set(results["per"]))
        new = rep.findings[before:]
        rep.say()
        if new:
            for sheet, what, detail in new:
                rep.say("* **[%s]** %s%s" % (sheet, what, " — " + detail if detail else ""))
        else:
            rep.say("Nothing to report.")

    rep.say()
    rep.say("## The count")
    rep.say()
    rep.say("**%d finding(s).**" % len(rep.findings))
    for what, why in rep.stopped:
        rep.say("* could not verify: %s — %s" % (what, why))

    print("\n%d finding(s)." % len(rep.findings))
    if "--md" in argv:
        dst = argv[argv.index("--md") + 1]
        with open(dst, "w", encoding="utf-8") as fh:
            fh.write("\n".join(rep.lines).rstrip() + "\n")
        print("report: %s" % dst)
    if "--json" in argv:
        dst = argv[argv.index("--json") + 1]
        with open(dst, "w", encoding="utf-8") as fh:
            json.dump([{"sheet": s, "what": w, "detail": d} for s, w, d in rep.findings],
                      fh, ensure_ascii=False, indent=2)
    if "--baseline" in argv:
        dst = argv[argv.index("--baseline") + 1]
        with open(dst, "w", encoding="utf-8") as fh:
            json.dump(baseline(path, long_rows, icoa_rows, coq_rows), fh,
                      ensure_ascii=False, indent=2)
        print("baseline: %s" % dst)
    if rep.stopped:
        return 2
    return 1 if rep.findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
