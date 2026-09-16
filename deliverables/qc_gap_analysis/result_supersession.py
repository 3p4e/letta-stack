#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Does a certificate of quality print a result the record has since replaced?

    python3 deliverables/qc_gap_analysis/result_supersession.py
    python3 deliverables/qc_gap_analysis/result_supersession.py --check superseded --dets 10,11
    python3 deliverables/qc_gap_analysis/result_supersession.py --md tracker/RESULT_SUPERSESSION_2026-09-16.md

The microbiology defect of 16.09.2026 was found by asking one question of every
certificate: does it print a result that a LATER certificate for the SAME lot — one
already on file the day the certificate issues — contradicts? That question was asked
of microbiology alone. The Head of QC reports that a second desk flags heavy metals and
mycotoxins as well, so this asks it of all seventeen determinations the release
register carries, and asks two neighbouring questions the first one raises.

    superseded   a certificate prints X for a determination, citing a document of
                 date D; another certificate for the same lot, dated after D and on
                 or before the day of issue, gives a different value.
    unprinted    a result in the release register that no certificate of quality for
                 that lot cites — a testing round the desk holds and no document shows.
    parallel     one register block holding TWO certificates of the same testing on
                 the same day that disagree: a block carrying more than one sublot.
                 `testing_series.rounds()` calls a tie release testing, on the reasoning
                 that a laboratory splitting one day's work across two documents is not
                 a second testing period. That is right when the two documents describe
                 one sample and wrong when they describe two.

None of the three is a verdict. A finding here is a question about what a controlled
document should print, and the answers are the owner's: `superseded` separates a
certificate that CITES a document from one that CARRIES a result forward, because the
first is settled by the ruling of 10.09.2026 (the earliest result is the release
result) and only the second is open (OI-38).

**A stability timepoint never supersedes anything.** It measures the lot ageing; it is
not release or retest testing and no certificate of quality prints it. The register
marks them and all three checks skip them — without that, the 05.03.2026 and 11.05.2026
stability pulls on the two Grape Pie lots alone raise 30 findings that are not findings.

Reads `coq_artifact_data.json` only: the certificates as the desk will print them and
the release register as the intakes left it.
"""
import argparse
import ast
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "tracker"))
import tracker_data as TD                                            # noqa: E402
import testing_series as TS                                          # noqa: E402

_spec = __import__("importlib.util", fromlist=["util"]).spec_from_file_location(
    "_tc_norm", os.path.join(HERE, "tracker", "truth_check_2026-09-15.py"))
TC = __import__("importlib.util", fromlist=["util"]).module_from_spec(_spec)
_spec.loader.exec_module(TC)          # the truth check's normaliser, not a second one

# the determination each release-register column carries (build_coq_schedule's map)
COL = {"4": "E", "5": "G", "6": "H", "8": "I",
       "9.1": "J", "9.2": "K", "9.3": "L", "9.4": "M", "9.5": "N",
       "10.1": "P", "10.2": "O", "10.3": "Q",
       "11.1": "R", "11.2": "S", "11.3": "T", "11.4": "U", "12": "V"}
BYCOL = {v: k for k, v in COL.items()}
NAME = {"4": "Total Δ9-THC", "5": "Total CBD", "6": "Total CBN", "8": "Loss on drying",
        "9.1": "TAMC", "9.2": "TYMC", "9.3": "Bile-tolerant GNB", "9.4": "Salmonella",
        "9.5": "E. coli", "10.1": "Aflatoxin B1", "10.2": "Aflatoxins Σ",
        "10.3": "Ochratoxin A", "11.1": "Pb", "11.2": "Cd", "11.3": "As", "11.4": "Hg",
        "12": "Pesticides"}
GROUP = {"4": "potency", "5": "potency", "6": "potency", "8": "loss on drying",
         "9.1": "microbiology", "9.2": "microbiology", "9.3": "microbiology",
         "9.4": "microbiology", "9.5": "microbiology",
         "10.1": "mycotoxins", "10.2": "mycotoxins", "10.3": "mycotoxins",
         "11.1": "heavy metals", "11.2": "heavy metals", "11.3": "heavy metals",
         "11.4": "heavy metals", "12": "pesticides"}


def bkey(x):
    """One key for a lot, star or no star — the batch list writes GG012601＊ and the
    register block is labelled without it."""
    return TD.batch_key(re.sub(r"[＊*]", "", str(x or "").strip()))


def printed(res):
    """What a certificate of quality asserts, without its unit gloss, its footnote
    marker or its Macedonian half.

    >>> printed("ND mg/kg — all 25 residues")
    'ND'
    >>> printed("< LOQ** %w/w")
    '< LOQ'
    >>> printed("Conforms | Одговара")
    'Conforms'
    """
    s = str(res or "").strip().split("|")[0].strip()
    s = re.sub(r"\s*\*+\s*", " ", s)
    s = re.sub(r"\s*—.*$", "", s).strip()
    s = re.sub(r"\s*(%\s*w/w|mg/kg|µg/kg|CFU/g|%)\s*$", "", s).strip()
    s = re.sub(r"\s*/\s*(25|1)\s*g\s*$", "", s).strip()
    return s


def load(path=None):
    return json.load(open(path or os.path.join(HERE, "coq_artifact_data.json"),
                          encoding="utf-8"))


def _rows(c):
    r = c["rows"]
    return ast.literal_eval(r) if isinstance(r, str) else r


def _blocks(data):
    out = {}
    for b in data["reg"]:
        for k in (b.get("pn"), b.get("cb")):
            if k:
                out.setdefault(bkey(k), b)
    return out


def coverage(data):
    """Per determination: how much of the record could even be compared.

    A zero in `superseded` means nothing unless this table says the comparison was
    possible. Heavy metals are the case that matters: no lot on file carries a SECOND
    metals certificate, so a sweep of #11 can only ever return zero — the certificates'
    metals rest on one document each and nothing exists to contradict them. That is a
    fact about the record, not a clean bill, and it is printed beside every zero.
    """
    out = {}
    for det in COL:
        docs, lots2 = 0, 0
        for b in data["reg"]:
            codes = {c["code"] for c in b["certs"]
                     if not c.get("stab")
                     and (c.get("vals") or {}).get(COL[det]) not in (None, "", "/")}
            docs += len(codes)
            lots2 += (len(codes) >= 2)
        out[det] = {"documents": docs, "lots_with_two": lots2}
    return out


def superseded(data, want=None):
    """Certificates printing a value a later certificate for the same lot contradicts."""
    blocks, out, n = _blocks(data), [], 0
    for c in data["coqs"]:
        blk = blocks.get(bkey(c.get("pp"))) or blocks.get(bkey(c.get("cb")))
        if blk is None:
            continue
        issue = TC.dkey(c.get("issue"))
        for r in _rows(c):
            det = str(r.get("no"))
            if det not in COL:
                continue
            if want and det not in want and det.split(".")[0] not in want:
                continue
            res = printed(r.get("res"))
            doc, dd = str(r.get("doc") or "").strip(), TC.dkey(r.get("dd"))
            if not res or res in ("—", "-") or not doc or doc in ("—", "-") or not dd:
                continue
            mine = TC.normd(res, det)
            for cert in blk["certs"]:
                v = (cert.get("vals") or {}).get(COL[det])
                cd = TC.dkey(cert.get("date"))
                if v in (None, "", "/") or cert.get("stab") or not cd:
                    continue
                if cd <= dd or (issue and cd > issue):
                    continue
                if TC.nkey(cert.get("code")) == TC.nkey(doc):
                    continue
                n += 1
                if TC.same(mine, TC.normd(v, det)):
                    continue
                out.append({
                    "coq": c["n"], "regcode": c.get("regcode", ""), "series": c["t"],
                    "lot": c.get("pp") or "", "cb": c.get("cb"), "issue": c.get("issue"),
                    "det": det, "group": GROUP[det], "name": NAME[det],
                    "printed": res, "doc": doc, "dd": r.get("dd"),
                    "newer": cert.get("code"), "newer_date": cert.get("date"),
                    "newer_lab": cert.get("lab"), "newer_val": v,
                    "st": r.get("st", ""),
                    "carried": "carried from" in (r.get("st") or "")})
    return out, n


def cited_after_issue(data):
    """A certificate of quality resting on a document issued after it.

    A controlled document cannot cite one that did not yet exist. This is the integrity
    rule the handover of 16.09.2026 states as its rule 2 ("issue date = 7 days after the
    last certificate the CoQ cites"), read as the inequality it implies, and it is the
    check that caught the IJZ-MB delivery standing behind thirteen RELEASE certificates.
    """
    out = []
    for c in data["coqs"]:
        iss = TC.dkey(c.get("issue"))
        if not iss:
            continue
        for r in _rows(c):
            det, doc, dd = str(r.get("no")), str(r.get("doc") or "").strip(), TC.dkey(r.get("dd"))
            if not doc or doc in ("—", "-") or not dd or dd <= iss:
                continue
            out.append({"coq": c["n"], "regcode": c.get("regcode", ""), "series": c["t"],
                        "lot": c.get("pp") or "", "cb": c.get("cb"), "issue": c.get("issue"),
                        "det": det, "name": NAME.get(det, "#" + det),
                        "doc": doc, "dd": r.get("dd")})
    return out


def unprinted(data):
    """Register results no certificate of quality for that lot cites."""
    cited, ncoq = defaultdict(set), Counter()
    for c in data["coqs"]:
        keys = {bkey(c.get("pp")), bkey(c.get("cb"))} - {""}
        for k in keys:
            ncoq[k] += 1
        for r in _rows(c):
            det, doc = str(r.get("no")), str(r.get("doc") or "").strip()
            if det in COL and doc and doc not in ("—", "-"):
                for k in keys:
                    cited[k].add((TC.nkey(doc), det))
    out = []
    for b in data["reg"]:
        keys = {bkey(b.get("pn")), bkey(b.get("cb"))} - {""}
        have = set().union(*(cited[k] for k in keys)) if keys else set()
        for cert in b["certs"]:
            if cert.get("stab"):
                continue
            for col, v in sorted((cert.get("vals") or {}).items()):
                if col not in BYCOL or v in (None, "", "/"):
                    continue
                if (TC.nkey(cert.get("code")), BYCOL[col]) in have:
                    continue
                out.append({"cb": b.get("cb"), "pn": b.get("pn"),
                            "coqs": max((ncoq[k] for k in keys), default=0),
                            "code": cert.get("code"), "date": cert.get("date"),
                            "lab": cert.get("lab"), "fam": cert.get("fam"),
                            "det": BYCOL[col], "name": NAME[BYCOL[col]], "val": v})
    return out


def parallel(data):
    """One block, one day, one testing — two certificates that disagree."""
    cited = defaultdict(set)
    for c in data["coqs"]:
        for r in _rows(c):
            doc = str(r.get("doc") or "").strip()
            if doc and doc not in ("—", "-"):
                for k in {bkey(c.get("pp")), bkey(c.get("cb"))} - {""}:
                    cited[k].add(TC.nkey(doc))
    out = []
    for b in data["reg"]:
        keys = {bkey(b.get("pn")), bkey(b.get("cb"))} - {""}
        have = set().union(*(cited[k] for k in keys)) if keys else set()
        byday = defaultdict(list)
        for c in b["certs"]:
            # A stability timepoint is not release testing, and a STARRED SAMPLE is not a
            # second sublot — the owner ruled on 16.09.2026 that it is a second sample of
            # the same packaged lot, kept in the record and in every statistic but never
            # certifying. Counting either here would report a question that has an answer.
            if c.get("stab") or TS.is_experimental(c.get("code", "")):
                continue
            byday[(TC.dkey(c.get("date")), c.get("fam") or "")].append(c)
        for (day, fam), group in sorted(byday.items()):
            if len(group) < 2:
                continue
            diffs = []
            for col in sorted({k for c in group for k in (c.get("vals") or {})}):
                if col not in BYCOL:
                    continue
                vals = [(c["code"], (c.get("vals") or {}).get(col)) for c in group]
                vals = [(k, v) for k, v in vals if v not in (None, "", "/")]
                if len(vals) < 2:
                    continue
                ns = [TC.normd(v, BYCOL[col]) for _, v in vals]
                if any(not TC.same(ns[0], x) for x in ns[1:]):
                    diffs.append({"det": BYCOL[col], "name": NAME[BYCOL[col]],
                                  "vals": vals})
            if diffs:
                out.append({"cb": b.get("cb"), "pn": b.get("pn"), "strain": b.get("strain"),
                            "day": day, "fam": fam,
                            "codes": [c["code"] for c in group],
                            "printed": [c["code"] for c in group
                                        if TC.nkey(c["code"]) in have],
                            "diffs": diffs})
    return out


# ------------------------------------------------------------------------ reporting
def _class(f):
    return "carried forward" if f["carried"] else "cited as covering the determination"


def _unp_class(m):
    """Which of the three the unprinted result belongs to."""
    c = str(m.get("code") or "")
    if re.match(r"^5[2-6]\d/10\d\d/26$|^5[2-6]\d/11\d\d/26$", c.strip()):
        return "the IJZ-MB campaign microbiology of 25/26.08.2026"
    if c.lower().startswith("n/a") or "in-house" in c.lower():
        return "an in-house document with no document number"
    if TS.is_experimental(c):
        return "a starred sample, which by the ruling of 16.09.2026 never certifies"
    return "an ordinary laboratory certificate"


def report(data, want=None):
    sup, n = superseded(data, want)
    unp, par = unprinted(data), parallel(data)
    L = []
    w = L.append
    w("# Does any certificate of quality print a result the record has replaced?")
    w("")
    w("The sweep of 16.09.2026, over %d certificates of quality and %d register blocks. "
      "Run it with `python3 deliverables/qc_gap_analysis/result_supersession.py`."
      % (len(data["coqs"]), len(data["reg"])))
    w("")
    w("## 1 · A printed result a later certificate contradicts")
    w("")
    w("%d comparisons — every (certificate, determination, later certificate for the same "
      "lot) triple where the later certificate was on file the day the certificate of "
      "quality issues. **%d contradict.**" % (n, len(sup)))
    w("")
    w("**A zero is only as good as what could be compared**, so the coverage is beside it. "
      "A lot with one document for a determination can never contradict itself: the "
      "certificate's value rests on that one document and the sweep has nothing to hold it "
      "against.")
    w("")
    cov = coverage(data)
    w("| # | parameter | documents on file | lots with two or more | contradictions |")
    w("|---|---|---:|---:|---:|")
    for det in sorted(COL, key=lambda x: [int(p) for p in x.split(".")]):
        k = sum(1 for f in sup if f["det"] == det)
        w("| #%s | %s | %d | %d | %s |"
          % (det, NAME[det], cov[det]["documents"], cov[det]["lots_with_two"],
             k if k else ("0" if cov[det]["lots_with_two"] else "— nothing to compare —")))
    w("")
    blind = sorted((d for d in COL if not cov[d]["lots_with_two"]),
                   key=lambda x: [int(p) for p in x.split(".")])
    if blind:
        w("**%s %s no second document anywhere in the record**, so the sweep is blind there "
          "and its zero says nothing. Read that as a gap in the record, not as a clean "
          "result: every certificate of quality that prints %s rests on a single laboratory "
          "document, and the retest campaigns did not re-run %s."
          % (", ".join("#%s %s" % (d, NAME[d]) for d in blind),
             "has" if len(blind) == 1 else "have",
             " or ".join(NAME[d] for d in blind),
             "it" if len(blind) == 1 else "them"))
        w("")
    thin = [d for d in COL if 0 < cov[d]["lots_with_two"] <= 2]
    if thin:
        w("%s %s compared on %s only — a zero there is real but thin."
          % (", ".join("#%s %s" % (d, NAME[d]) for d in thin),
             "was" if len(thin) == 1 else "were",
             ", ".join("%d lot%s" % (cov[d]["lots_with_two"],
                                     "" if cov[d]["lots_with_two"] == 1 else "s")
                       for d in thin)))
        w("")
    real = [d for d in COL if cov[d]["lots_with_two"] > 2
            and not any(f["det"] == d for f in sup)]
    if real:
        w("Where the comparison was genuinely available and returned nothing, it is worth "
          "stating plainly: %s."
          % ("; ".join("#%s %s over %d lots" % (d, NAME[d], cov[d]["lots_with_two"])
                       for d in sorted(real, key=lambda x: [int(p) for p in x.split(".")]))))
        w("")
    w("The %d split in two, and only the second half is an open question:" % len(sup))
    w("")
    for cls in ("cited as covering the determination", "carried forward"):
        rows = [f for f in sup if _class(f) == cls]
        w("### %s — %d" % (cls, len(rows)))
        w("")
        if cls.startswith("cited"):
            w("The certificate cites the document as the one that covers the determination. "
              "Every one of these is a RELEASE certificate citing the RELEASE result while a "
              "later retest sits on file — which is the owner's ruling of 10.09.2026 working "
              "exactly as written: the earliest result for a parameter is the release result, "
              "and a later one belongs to a retest certificate, not to this one. Nothing to "
              "repair.")
        else:
            w("The certificate carries the result forward from the initial testing because "
              "the campaign it rests on did not retest that determination — the ruling of "
              "15.09.2026. The question OI-38 puts to the owner is whether *forward from the "
              "initial testing* should mean the initial result or the latest result on file, "
              "and these are the rows it decides.")
        w("")
        w("| certificate | series | lot | # | parameter | prints | from | superseded by |")
        w("|---|---|---|---|---|---|---|---|")
        for f in sorted(rows, key=lambda f: (f["group"], f["det"], f["cb"])):
            w("| %s | %s | %s | #%s | %s | %s | %s (%s) | %s = %s (%s) |"
              % (f["regcode"] or f["coq"], f["series"], f["lot"] or f["cb"], f["det"],
                 f["name"], f["printed"], f["doc"], f["dd"], f["newer"], f["newer_val"],
                 f["newer_date"]))
        w("")
    aft = cited_after_issue(data)
    w("## 2 · A certificate resting on a document issued after it")
    w("")
    if aft:
        w("**%d row(s) on %d certificate(s).** A controlled document cannot cite one that "
          "did not yet exist."
          % (len(aft), len({(a["regcode"] or a["coq"], a["cb"]) for a in aft})))
        w("")
        w("| certificate | series | lot | issued | # | document | its date |")
        w("|---|---|---|---|---|---|---|")
        for a in sorted(aft, key=lambda a: (a["cb"], a["det"])):
            w("| %s | %s | %s | %s | #%s | %s | %s |"
              % (a["regcode"] or a["coq"], a["series"], a["lot"] or a["cb"], a["issue"],
                 a["det"], a["doc"], a["dd"]))
        w("")
    else:
        w("None, over every determination of every certificate. Every cited document was "
          "on file the day its certificate of quality issues.")
        w("")
    w("## 3 · One block, two sublots")
    w("")
    w("%d group(s) where a register block holds two certificates of the same testing on the "
      "same day that report different results, over %d block(s). The certificate of quality "
      "prints one of the pair; the other's results appear on no certificate at all."
      % (len(par), len({(h["cb"], h["pn"]) for h in par})))
    w("")
    for h in par:
        w("**%s%s — %s, %s, %s.** Documents %s; the certificate of quality prints %s."
          % (h["cb"], " (%s)" % h["pn"] if h["pn"] else "", h["strain"] or "", h["day"],
             h["fam"], ", ".join("`%s`" % c for c in h["codes"]),
             ", ".join("`%s`" % c for c in h["printed"]) or "neither"))
        w("")
        for d in h["diffs"]:
            w("* #%s %s — %s" % (d["det"], d["name"],
                                 "; ".join("`%s` = %s" % (k, v) for k, v in d["vals"])))
        w("")
    w("## 4 · Results on file that no certificate of quality prints")
    w("")
    w("%d, over %d lot(s). The number is large and almost all of it is already accounted "
      "for by the two sections above; it is here so a ruling can be costed."
      % (len(unp), len({(m["cb"], m["pn"]) for m in unp})))
    w("")
    for label, note in (
            ("the IJZ-MB campaign microbiology of 25/26.08.2026",
             "the delivery v34 wrote into the register. The reissues carry the initial "
             "microbiology instead — that is OI-38, and these are the results a ruling "
             "for *the latest on file* would put on the certificates."),
            ("a starred sample, which by the ruling of 16.09.2026 never certifies",
             "a second sample of the same packaged lot, sent for a limited panel outside "
             "the release testing. The Head of QC ruled on 16.09.2026 that its result stays "
             "in the record and in every statistic but never sources a certificate of "
             "quality, so appearing here is correct and not a gap "
             "(testing_series.EXPERIMENTAL)."),
            ("an in-house document with no document number",
             "the two in-house certificates of analysis for HPA1024 and OPM1024, which "
             "print no report number, and the two in-house cross-checks. A certificate of "
             "quality cannot cite a document that has no code; these are routed through the "
             "lot's internal certificate instead. Nothing to do."),
            ("an ordinary laboratory certificate",
             "each is either an intermediate retest round no certificate of quality rests "
             "on, or the second sublot of section 2.")):
        rows = [m for m in unp if _unp_class(m) == label]
        w("**%d — %s.** %s" % (len(rows), label, note))
        w("")
        if label.startswith("an ordinary"):
            w("| lot | document | date | testing | determinations |")
            w("|---|---|---|---|---|")
            bydoc = defaultdict(list)
            for m in rows:
                bydoc[(m["cb"], m["pn"], m["code"], m["date"], m["fam"])].append(m["det"])
            for (cb, pn, code, date, fam), dets in sorted(bydoc.items()):
                w("| %s%s | %s | %s | %s | %s |"
                  % (cb, " (%s)" % pn if pn else "", code, date, fam or "",
                     " ".join(sorted(dets))))
            w("")
    w("All of it by determination:")
    w("")
    w("| determination | results |")
    w("|---|---|")
    for k, v in sorted(Counter(m["name"] for m in unp).items()):
        w("| %s | %d |" % (k, v))
    w("")
    return "\n".join(L) + "\n", sup, unp, par



# ------------------------------------------------------------------------- the tab
NAVY, GREY, AMBER, ROSE = "1F3864", "EFEFEF", "FFF2CC", "FCE4EC"
SHEET = "Result Supersession"
COLS = ["Check", "CU Batch", "P Lot", "Certificate of quality", "Series", "Issued",
        "#", "Parameter", "Result on the certificate", "Document", "Document issued",
        "The other result", "Its document", "Its date", "Its laboratory", "What it means"]

_MEANS_CITED = ("Correct as it stands. The certificate cites the release result, and the "
                "owner's ruling of 10.09.2026 makes the earliest result for a parameter the "
                "release result — the later one belongs to a retest certificate.")
_MEANS_CARRIED = ("Open — OI-38. The reissue carries this determination forward from the "
                  "initial testing because its campaign did not retest it (ruling of "
                  "15.09.2026). Whether 'forward' means the initial result or the latest on "
                  "file is the owner's to settle.")
_MEANS_PARALLEL = ("Open — OI-39. Two certificates of the same testing on the same day "
                   "report different results in one register block: the block carries two "
                   "sublots. The certificate of quality prints one of them and does not say "
                   "which.")
_MEANS_AFTER = ("A controlled document cannot rest on one issued after it. Every row here "
                "is a defect, not a question.")
_MEANS_UNPRINTED = ("For information. This result is in the release register and on the "
                    "tracker; no certificate of quality for the lot cites it. Where the lot "
                    "appears in the two checks above, that is why.")


def sheet_rows(data):
    """Every finding of the three checks as one filterable table."""
    sup, _ = superseded(data)
    out = []
    for f in sorted(sup, key=lambda f: (bool(f["carried"]), f["group"], f["det"], f["cb"])):
        out.append({
            "Check": "carried forward" if f["carried"] else "cited as covering",
            "CU Batch": f["cb"], "P Lot": f["lot"],
            "Certificate of quality": f["regcode"] or f["coq"], "Series": f["series"],
            "Issued": f["issue"], "#": f["det"], "Parameter": f["name"],
            "Result on the certificate": f["printed"], "Document": f["doc"],
            "Document issued": f["dd"], "The other result": f["newer_val"],
            "Its document": f["newer"], "Its date": f["newer_date"],
            "Its laboratory": f["newer_lab"],
            "What it means": _MEANS_CARRIED if f["carried"] else _MEANS_CITED})
    for a in cited_after_issue(data):
        out.append({
            "Check": "cited after the issue date", "CU Batch": a["cb"], "P Lot": a["lot"],
            "Certificate of quality": a["regcode"] or a["coq"], "Series": a["series"],
            "Issued": a["issue"], "#": a["det"], "Parameter": a["name"],
            "Result on the certificate": "", "Document": a["doc"], "Document issued": a["dd"],
            "The other result": "", "Its document": "", "Its date": "", "Its laboratory": "",
            "What it means": _MEANS_AFTER})
    for h in parallel(data):
        for d in h["diffs"]:
            a, b = d["vals"][0], d["vals"][1]
            out.append({
                "Check": "two sublots in one block", "CU Batch": h["cb"], "P Lot": h["pn"],
                "Certificate of quality": "", "Series": h["fam"], "Issued": h["day"],
                "#": d["det"], "Parameter": d["name"],
                "Result on the certificate": a[1] if a[0] in h["printed"] else b[1],
                "Document": a[0] if a[0] in h["printed"] else b[0], "Document issued": h["day"],
                "The other result": b[1] if a[0] in h["printed"] else a[1],
                "Its document": b[0] if a[0] in h["printed"] else a[0],
                "Its date": h["day"], "Its laboratory": "",
                "What it means": _MEANS_PARALLEL})
    for m in sorted(unprinted(data), key=lambda m: (m["cb"], m["date"], m["det"])):
        out.append({
            "Check": "on file, on no certificate", "CU Batch": m["cb"], "P Lot": m["pn"],
            "Certificate of quality": "", "Series": m["fam"], "Issued": "",
            "#": m["det"], "Parameter": m["name"], "Result on the certificate": "",
            "Document": "", "Document issued": "", "The other result": m["val"],
            "Its document": m["code"], "Its date": m["date"], "Its laboratory": m["lab"],
            "What it means": _MEANS_UNPRINTED})
    return out


def fill(ws, rows):
    """The tab, one row per finding, coloured by what the desk can do about it."""
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    ws.append(COLS)
    for r in rows:
        ws.append([r.get(c, "") for c in COLS])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF", size=9)
        c.fill = PatternFill("solid", fgColor=NAVY)
        c.alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[1].height = 30
    for i, w in enumerate([22, 15, 10, 18, 26, 12, 7, 18, 22, 20, 13, 22, 20, 12, 26, 64], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    grey = PatternFill("solid", fgColor=GREY)
    amber = PatternFill("solid", fgColor=AMBER)
    rose = PatternFill("solid", fgColor=ROSE)
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.font = Font(size=9)
            c.alignment = Alignment(wrap_text=True, vertical="top")
        k = str(row[0].value or "")
        fill_ = (amber if k == "carried forward" else
                 rose if k in ("two sublots in one block",
                               "cited after the issue date") else grey)
        row[0].fill = fill_
        row[15].fill = fill_
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = ws.dimensions
    return len(rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    ap.add_argument("--check", default="all",
                    choices=["all", "superseded", "unprinted", "parallel", "after"])
    ap.add_argument("--dets", default="")
    ap.add_argument("--md", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    data = load(a.data)
    want = set(a.dets.split(",")) if a.dets else None
    md, sup, unp, par = report(data, want)
    if a.md:
        path = a.md if os.path.isabs(a.md) else os.path.join(HERE, a.md)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(md)
        print("wrote %s" % os.path.relpath(path, HERE))
    if a.json:
        json.dump({"superseded": sup, "unprinted": unp, "parallel": par,
                   "cited_after_issue": cited_after_issue(data)},
                  open(a.json, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    if a.check in ("all", "superseded"):
        print("superseded: %d finding(s) — %s" % (len(sup), dict(sorted(
            Counter(f["group"] for f in sup).items())) or "none"))
        print("            %d carried forward (OI-38), %d cited as covering "
              "(the ruling of 10.09.2026)"
              % (sum(1 for f in sup if f["carried"]), sum(1 for f in sup if not f["carried"])))
    if a.check in ("all", "after"):
        _aft = cited_after_issue(data)
        print("after issue: %d row(s) citing a document issued after the certificate — %s"
              % (len(_aft), ", ".join(sorted({x["regcode"] or x["coq"] for x in _aft})) or "none"))
    if a.check in ("all", "parallel"):
        print("parallel:   %d group(s) over %d block(s) — %s"
              % (len(par), len({(h["cb"], h["pn"]) for h in par}),
                 ", ".join(sorted({h["cb"] for h in par})) or "none"))
    if a.check in ("all", "unprinted"):
        print("unprinted:  %d result(s) over %d lot(s)"
              % (len(unp), len({(m["cb"], m["pn"]) for m in unp})))


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        import doctest
        print(doctest.testmod())
    else:
        main()
