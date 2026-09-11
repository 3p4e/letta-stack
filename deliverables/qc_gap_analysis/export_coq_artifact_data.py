#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One JSON for the QC issuance artifact: CoQ schedule, iCoA plan, eCoA receipt.

    python3 deliverables/qc_gap_analysis/export_coq_artifact_data.py OUT.json

Everything is derived from the same computations the workbooks use —
build_coq_schedule.schedule() / icoa_plan() and build_document_registers
load_register() / verified_map() — so the artifact cannot drift from the
deliverables. No value is retyped here.
"""
import json
import os
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.chdir(ROOT)
sys.path.insert(0, HERE)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "ingestion", "ragflow"))

import build_coq_schedule as CQ            # noqa: E402
import validate_ecoa_limits as VEL         # noqa: E402
import build_document_registers as DR      # noqa: E402


# Which fields of each page-reads record are analytical values, and the
# register-facing label each renders under. Everything else on a record
# (batch identity, uncertainties, spec strings, notes) stays in the file.
PR_LABELS = {
    "cnp": [("thc", "Total Δ9-THC %"), ("d9", "Δ9-THC %"), ("thca", "Δ9-THCA %"),
            ("cbd", "Total CBD %"), ("cbd_raw", "CBD %"), ("cbda", "CBDA %"),
            ("cbn", "CBN %"), ("lod", "Loss on drying %"),
            ("foreign_matter", "Foreign matter"), ("verdict", "Verdict")],
    "farmahem": [("thc", "Total Δ9-THC %"), ("cbd", "Total CBD %"),
                 ("cbn", "Total CBN %"), ("afla", "Aflatoxins Σ µg/kg"),
                 ("aflab1", "Aflatoxin B1 µg/kg"), ("afla_b2", "Aflatoxin B2 µg/kg"),
                 ("afla_g1", "Aflatoxin G1 µg/kg"), ("afla_g2", "Aflatoxin G2 µg/kg"),
                 ("ota", "Ochratoxin A µg/kg"), ("lod", "Loss on drying %")],
    "iph_physchem": [("pb", "Pb mg/kg"), ("cd", "Cd mg/kg"), ("as", "As mg/kg"),
                     ("hg", "Hg mg/kg"), ("cu", "Cu mg/kg"),
                     ("afla", "Aflatoxins µg/kg"), ("pest", "Pesticides")],
    "microbiology": [("tamc", "TAMC CFU/g"), ("tymc", "TYMC CFU/g"),
                     ("gnb", "Bile-tolerant GNB CFU/g"), ("ecoli", "E. coli /1 g"),
                     ("salm", "Salmonella /25 g"), ("verdict", "Verdict")],
    "residual": [("tamc", "TAMC CFU/g"), ("tymc", "TYMC CFU/g"),
                 ("gnb", "Bile-tolerant GNB CFU/g"), ("ecoli", "E. coli /1 g"),
                 ("salmonella", "Salmonella /25 g"), ("pesticides", "Pesticides"),
                 ("verdict", "Verdict")],
}


# One analyte, one identity — whatever a source calls it. Tier suppression and
# contradiction detection both key on this, because a page value and a corpus
# value for the same analyte arrived under different labels and rendered side by
# side (ППК26037: page CBN 1.09 beside corpus "Total CBN" 0.19).
def analyte(label):
    l = label.lower()
    for a, b in (("δ9-thc", "thc"), ("δ9", ""), ("total ", ""), ("σ", ""),
                 ("(partial read)", ""), ("%", ""), ("µg/kg", ""), ("mg/kg", ""),
                 ("cfu/g", ""), ("/1 g", ""), ("/25 g", ""), (" ", ""), ("-", "")):
        l = l.replace(a, b)
    return l.strip(" .·")


def disagree(a, b):
    """True when two printed values are different measurements, not different
    spellings of the same one."""
    import re as _re
    ma, mb = VEL.magnitude(a), VEL.magnitude(b)
    if ma is not None and mb is not None:
        return abs(ma - mb) > max(abs(ma), abs(mb)) * 1e-9
    def canon(v):
        u = str(v).upper().replace(",", ".")
        u = _re.sub(r"\s*\([^)]*\)", "", u)
        u = u.replace("\u0425", "X").replace("\u0445", "X").replace("\u00d7", "X")
        u = _re.sub(r"CFU/G|\u0418|AND|\u041D\.\u0414\.|N\.D\.|ND", "", u)
        return _re.sub(r"[^A-Z0-9<>.^]", "", u)
    return canon(a) != canon(b)


def page_rect_map():
    """fold(code) -> the certificate's values as read off its own page (tier T1)."""
    import glob
    import verification_coverage as VC
    out = {}
    for path in sorted(glob.glob("review/*_page_reads_*.json")):
        blk = path.split("/")[-1].split("_page_reads")[0]
        for code, rec in json.load(open(path, encoding="utf-8")).items():
            vals = []
            for f, lbl in PR_LABELS[blk]:
                if rec.get(f) in (None, "", {}):
                    continue
                src = "page-read 31.08.2026 (" + blk + ")"
                # a partially read panel is not a panel result: three IPH
                # pesticide reads cover only part of the page and say so in
                # their own record, so the qualifier travels with the value
                if f == "pest" and rec.get("pest_pages") and \
                        "full" not in str(rec["pest_pages"]).lower():
                    lbl += " (partial read)"
                    src += " · coverage: " + str(rec["pest_pages"])
                vals.append({"k": lbl, "v": str(rec[f]), "src": src, "t": "T1"})
            if vals:
                out[VC.fold(code)] = vals
    return out


def corpus_rect_map():
    """code (exactly as printed) -> corpus-derived values (tiers T2/T3), from
    the rectification sweep's output when it exists. Corpus values never mark
    a certificate page-verified — the remediation desk is the promotion path."""
    path = os.path.join(HERE, "ecoa_rectification_2026-08-31.json")
    if not os.path.exists(path):
        return {}
    data = json.load(open(path, encoding="utf-8"))
    return {code: rec["params"] for code, rec in data.get("certs", {}).items()
            if rec.get("params")}


# Every flagged receipt, with its documented cause — assembled from the
# correction chain's own comments and the page-verification campaigns.
# Four baseline ambers carried no recorded reason anywhere; their causes are
# documented here from the page reads, marked as such.
_TYMC_STANDS = ("TYMC %s CFU/g against the cat. C criterion 10\u2074 — over even the "
                "Ph. Eur. 5.1.4 maximum acceptable count 2\u00d710\u2074 (%s\u00d7); the certificate "
                "still concludes ОДГОВАРА. Flag stands; deviation record open.")
_TYMC_UNDET = ("TYMC %s CFU/g — conforms against the Ph. Eur. 5.1.4 maximum acceptable "
               "count 2\u00d710\u2074, over QCSP 001's literal 10\u2074. UNDETERMINED until QC rules "
               "how QCSP 001 reads its maximum.")
FLAG_DOSSIER = {
    "320/0587/25": _TYMC_STANDS % ("4.2\u00d710\u2074", "2.10"),
    "904/1589/25": _TYMC_STANDS % ("3.3\u00d710\u2074", "1.65"),
    "946/1684/25": _TYMC_STANDS % ("3.6\u00d710\u2074", "1.80") +
        " Value read 10\u00b3 in the first transcription; corrected to 10\u2074 on the page read.",
    "948/1686/25": _TYMC_STANDS % ("2.6\u00d710\u2074", "1.30"),
    "1032/1851/25": _TYMC_STANDS % ("4.9\u00d710\u2074", "2.45") +
        " The largest TYMC on the register (320/0587/25 carries a larger count "
        "overall \u2014 TAMC 5.1\u00d710\u2074 \u2014 but against a criterion ten times higher).",
    "472/0863/25": _TYMC_UNDET % "1.9\u00d710\u2074" +
        " The closest call on the register: 19 000 against a maximum acceptable "
        "count of 20 000.",
    "587/1066/25": _TYMC_UNDET % "1.5\u00d710\u2074",
    "628/1129/25": _TYMC_UNDET % "1.2\u00d710\u2074",
    "949/1687/25": _TYMC_UNDET % "1.7\u00d710\u2074",
    "1220/2171/25": "TYMC 200 CFU/g against the certificate's own printed limit 10\u00b2 — "
        "2\u00d7 over on its own paper, conforming against the register column's 10\u2074. "
        "A per-certificate manufacturer spec, outside the pharmacopoeial rule.",
    "ППК25154": "Data-integrity flag on the source corpus, not on the batch: the RAGflow "
        "corpus holds a corrupted total 1.87; the register's 18.27 is page-confirmed correct.",
    "ППК25155": "Baseline amber on CBD 0.1 % with no recorded reason anywhere in the "
        "chain. Page read confirms CBD 0.10 %, conforming (< 1.00). Documented on "
        "rectification, 31.08.2026 — reads as a transcription-check mark, not a finding.",
    "ППК26033": "CBN above the \u2264 1.00 % criterion on a 40\u00b0C/75%RH accelerated-stability "
        "arm — a stability finding, not a release failure (R5).",
    "ППК26035": "CBN above the \u2264 1.00 % criterion on a 40\u00b0C/75%RH accelerated-stability "
        "arm — a stability finding, not a release failure (R5).",
    "ППК26037": "CBN 1.09 % above the \u2264 1.00 % criterion on a stability arm — a stability "
        "finding, not a release failure (R5).",
    "ППК26058": "CBN 2.05 % above the \u2264 1.00 % criterion on an accelerated-stability "
        "timepoint — a stability finding, not a release failure (R5).",
    "ППК26127": "The certificate itself concludes НЕ ОДГОВАРА — foreign matter: cannabis "
        "seed present. Every numeric value on the page is in specification; the failure "
        "lives only in the conclusion line.",
    "197-7-К/26": "The register's CBD/CBN pair has a history: transposed in the "
        "first transcription, corrected by the page campaign (chain step 7), swapped "
        "back by a misreading in chain step 16, and restored to the certificate's "
        "values — CBD 0.22, CBN < LOQ — by chain step 17 after the rectification "
        "cross-check caught the regression against two primary sources. Both values "
        "conform either way; the amber records the history.",
    "197-14-М/26": "Ochratoxin A 2.06 \u00b5g/kg — DETECTED above LOQ, conforming against "
        "the 20 \u00b5g/kg criterion. Baseline amber; cause documented on rectification, "
        "31.08.2026.",
    "100-2-ГС/26": "Loss on drying 10.3 % \u2014 <b>conforming</b>: the certificate "
        "prints its own specification as &lt; 12, the register column criterion is "
        "\u2264 12.00 and QCSP 001 \u00a78 reads \u2264 12.0 %. (The 10.00 % limit belongs to the "
        "older CNP certificate form and to the stability programme; it does not govern "
        "a Farmahem release loss-on-drying certificate.) The amber records a document "
        "defect, not a result: the page prints twin-batch label J31112501 where its "
        "cannabinoid sibling 100-2-К/26 and the register print J31122501 \u2014 see "
        "FARMAHEM_PAGE_VERIFICATION_2026-08-31. Cause documented on rectification, "
        "31.08.2026.",
    "100-3-ГС/26": "Loss on drying 10.3 % \u2014 <b>conforming</b> against the "
        "certificate\u2019s own &lt; 12, the register\u2019s \u2264 12.00 and QCSP 001 \u00a78\u2019s "
        "\u2264 12.0 %. The amber records two document defects: the same twin-batch label "
        "as 100-2-ГС/26, and a scan bound backwards (results on page 1, cover on "
        "page 2). Cause documented on rectification, 31.08.2026.",
    "197-6-К/26": "The batch cell is flagged, not a value: cultivation batch "
        "CC012601/1 appears in no register and no issue plan \u2014 identity unresolved "
        "(P060332) \u2014 and the record holds nothing else for the lot: no identity, "
        "foreign matter, loss on drying, heavy metals, pesticides or microbiology. The "
        "register comment asks QC to confirm the batch and open the block properly; "
        "that no certificate of quality can issue meanwhile follows from this folder\u2019s "
        "own rule \u2014 a CoQ never carries a result or a conformity assertion that has "
        "not been certified.",
}


def main(out):
    rows, per_coq, dets = CQ.schedule()
    plan = CQ.icoa_plan(per_coq)
    specj = json.load(open(os.path.join(HERE, "product_specifications_QCSP001.json"),
                           encoding="utf-8"))["specifications"]

    coqs, by_n = [], {}
    for r in rows:
        k = (r["CoQ number"], r["Cultivation batch"], r["CoQ type"])
        if k not in by_n:
            p = per_coq[len(coqs)]
            assert p["number"] == r["CoQ number"] and p["cb"] == r["Cultivation batch"]
            by_n[k] = {
                "n": p["number"], "t": p["type"], "basis": p["basis"],
                "issue": p["date"], "pp": p["pp"], "cb": p["cb"],
                "strain": p["strain"], "grade": p["grade"], "cls": p["cls"],
                "ic": p["icoa_ref"], "thc": p["banner_thc"],
                "spec": p["spec_doc"], "conflict": p["spec_conflict"],
                "reg": p["in_register"], "issued": p["issued"],
                "md": p.get("md", ""), "pk": p.get("pk", ""),
                "pcode": (specj.get(p["pp"]) or {}).get("product_code", ""),
                "rows": [],
            }
            coqs.append(by_n[k])
        by_n[k]["rows"].append({
            "no": r["№"], "crit": r["Acceptance criterion"],
            "res": r["Result"], "doc": r["Source document"],
            "dd": r["Document date"], "lab": r["Issuing institution"],
            "fam": r["Report series"], "st": r["Status"],
            "route": r["Performed by"], "also": r["Also on file"],
        })

    # The CoQ Register states, per lot, the code the certificate carries and the
    # date it is issued (owner, 10.09.2026: the certificate prints THAT date).
    # Lifted from the workbook by tracker/extract_coq_register.py, so the desk,
    # the page and the compiled certificates all read one source. A lot the
    # register cannot issue yet has no date, and keeps the schedule's floor.
    reg_csv = os.path.join(HERE, "coq_register_2026-09-10.csv")
    if os.path.exists(reg_csv):
        import csv as _csv
        _reg = {}
        with open(reg_csv, encoding="utf-8") as _fh:
            for _r in _csv.DictReader(_fh):
                if _r["key"]:
                    _reg[_r["key"]] = _r
        # The register keys itself on the P lot where the lot has one and on the
        # cultivation batch where it does not, so both are indexed — and through
        # the single batch-identity definition, never by string: the register
        # writes GG012601＊ where the schedule writes GG012601.
        _byk = {}
        for _kk, _rr in _reg.items():
            _pre, _sfx = _kk.rsplit("|", 1)
            for _name in (_pre, _rr.get("cu_batch", ""), _rr.get("p_batch", "")):
                _name = (_name or "").strip()
                if _name and not _name.startswith(("N/A", "\u2014")):
                    _byk.setdefault((CQ.BI.batch_key(_name), _sfx), _rr)
        _hit = 0
        for _c in coqs:
            _sfx = "R" if _c["t"].startswith("additional") else "I"
            _row = (_byk.get((CQ.BI.batch_key(_c["pp"]), _sfx)) if _c["pp"] else None) \
                or _byk.get((CQ.BI.batch_key(_c["cb"]), _sfx))
            if not _row:
                continue
            _c["regcode"] = _row["coq_code"]
            _d = (_row["issue_date"] or "").strip()
            if _d and _d != "\u2014":
                _c["issue"] = _d
                _hit += 1
        print("CoQ register: %d of %d CoQs take their issue date from the workbook"
              % (_hit, len(coqs)))

    # Owner, 10.09.2026: the phenotype and processing pills are selected
    # according to the specification for the product strain. Those pills — and
    # the chemotype pill beside them, and the primary-packaging line under them —
    # are product attributes, not laboratory results, and the document that
    # states them is the issued QCSP 001 specification the certificate already
    # names in Spec. Ref. spec_attributes.py reads them off that document; this
    # only joins them to the lot, on the specification code, which is the same
    # string the certificate prints. A lot whose specification is not on file
    # gets nothing, and the certificate marks the band rather than guessing it.
    _spec_csv = os.path.join(HERE, "spec_attributes_2026-09-10.csv")
    if os.path.exists(_spec_csv):
        import csv as _csv2
        _spec = {}
        with open(_spec_csv, encoding="utf-8") as _fh:
            for _r in _csv2.DictReader(_fh):
                _spec[_r["code"].strip()] = _r
        _sh, _sm = 0, set()
        for _c in coqs:
            _code = (_c.get("spec") or "").strip()
            _r = _spec.get(_code)
            if not _r:
                if _code and _code != "\u2014":
                    _sm.add(_code)
                continue
            _c["spc"] = {"code": _r["code"], "pheno": _r["phenotype"],
                         "chemo": _r["chemotype"], "proc": _r["processing"],
                         "dominance": _r["dominance"], "dom": _r["dom"],
                         "pack": _r["packaging"]}
            _sh += 1
        print("Specification attributes: %d of %d CoQs; %d specification code(s) "
              "not on file%s" % (_sh, len(coqs), len(_sm),
                                 (" — " + ", ".join(sorted(_sm))) if _sm else ""))

    # Owner's rulings of 10.09.2026 on when a document is issued —
    # issuance_schedule.py, which reads them off the undivided register through
    # testing_series.py. This supersedes the CoQ Register's planned dates: the
    # register held one date per lot, and the ruling gives a date per lot per
    # testing round, floored so that nothing controlled by the specification SOP
    # predates it and nothing is dated before the evidence it cites.
    try:
        import issuance_schedule as ISS
        _rows = ISS.build()
        _packto = {}
        _bd = os.path.join(HERE, "batch_dates_2026-09-10.csv")
        if os.path.exists(_bd):
            import csv as _csv3
            with open(_bd, encoding="utf-8") as _fh:
                for _r in _csv3.DictReader(_fh):
                    _to = (_r.get("packaging_to") or "").strip()
                    if not _to:
                        continue
                    for _n in (_r.get("batch"), _r.get("p_batch")):
                        _n = (_n or "").strip()
                        if _n:
                            _packto.setdefault(CQ.BI.batch_key(_n), _to)
        _tested = {}
        for _r in _rows:
            _kind = "initial release" if _r["kind"] == "initial release" else "additional"
            _tested.setdefault((CQ.BI.batch_key(_r["batch"]), _kind), _r["tested"])
        _n = 0
        for _c in coqs:
            _kind = "additional" if _c["t"].startswith("additional") else "initial release"
            # The date is computed from the documents THIS certificate cites, not
            # from everything the batch has on file. The two are not the same since
            # a release certificate stopped citing the post-release re-analysis:
            # nine certificates were waiting on a 10.08.2026 document they no
            # longer print. A certificate is issued after its own evidence and
            # after nothing else.
            _dates = [(_r.get("dd") or "").strip() for _r in _c["rows"]
                      if (_r.get("doc") or "").strip() not in ("", "\u2014")]
            _dates = [_d for _d in _dates if ISS.parse(_d)]
            if not _dates:
                continue
            _last = max(_dates, key=lambda _d: ISS.parse(_d))
            # For the release round the internal CoA is tested on the batch's own
            # packaging date, and the certificate carries it — that is the
            # authority, not the schedule's per-batch lookup, which keys on the
            # register's spelling of the batch and misses where the two differ. It
            # missed on three lots and dated their certificates in August on the
            # strength of an August testing date they do not have.
            if _kind == "initial release":
                _t = _c.get("pk") or _tested.get((CQ.BI.batch_key(_c["cb"]), _kind)) or _last
            else:
                _t = _tested.get((CQ.BI.batch_key(_c["cb"]), _kind)) or _last
            _ic = ISS.icoa_issue(_t)
            # never before the batch finished being packed: JD022601's last
            # external certificate is dated 30.06.2026 and the lot was still being
            # packed on 05.08.2026
            _pkto = _packto.get(CQ.BI.batch_key(_c["cb"]), "") if _kind == "initial release" else ""
            _issue = ISS.coq_issue(_last, _ic, _pkto)
            if not _issue:
                continue
            _c["issue"] = _issue
            _c["icoa_issue"] = _ic or ""
            _c["icoa_tested"] = _t
            _c["last_external"] = _last
            _n += 1
        print("Issuance schedule: %d of %d CoQs take their date from the 10.09 rulings"
              % (_n, len(coqs)))
    except Exception as _e:                       # the schedule is additive, never fatal
        print("Issuance schedule not applied: %s" % _e)

    # Owner's rulings of 10.09.2026 on the internal certificate of analysis:
    # identity A, identity B and foreign matter go on ONE internal certificate per
    # testing round, its code and issue date are referenced on the certificate of
    # quality against those parameters, and an in-house result is never referenced
    # on a certificate of quality — it is carried on the internal certificate,
    # which the certificate of quality then cites.
    #
    # `cell_resolution` rule 1 refused these determinations because the internal
    # certificate carrying them had not been issued. The owner has now issued it,
    # dated it and coded it, so the premise of that refusal is gone for exactly
    # the determinations the certificate covers — and for no others.
    try:
        import icoa_register as ICO
        import cell_resolution as _CR
        _icoa = ICO.by_batch_round()
        _pass = {}
        for _r in _CR.load():
            _no = _CR.det_no(_r.get("Determination", ""))
            _v = _CR.pieces(_r.get("What the document prints", ""))
            if _no and len(_v) == 1:
                _pass[(CQ.BI.batch_key(_r["Batch"]), _no)] = _v[0]
        _cited, _filled = 0, 0
        for _c in coqs:
            _kind = "additional" if _c["t"].startswith("additional") else "initial release"
            _row = _icoa.get((CQ.BI.batch_key(_c["cb"]), _kind))
            if not _row:
                continue
            _c["icoa_code"] = _row["code"]
            _c["icoa_issue"] = _row["issued"]
            _c["icoa_tested"] = _row["tested_from"]
            _covers = set(_row["parameters"].split())
            for _rr in _c["rows"]:
                if _rr["no"] not in _covers:
                    continue
                _doc = (_rr.get("doc") or "").strip()
                _lab = (_rr.get("lab") or "").strip()
                if _doc and _doc != "\u2014" and not ICO.is_in_house(_lab):
                    continue          # an outsourced certificate already covers it
                _rr["doc"] = _row["code"]
                _rr["dd"] = _row["issued"]
                _rr["lab"] = "Purely Plant GmbH (in-house)"
                _cited += 1
                if (_rr.get("res") or "\u2014") == "\u2014":
                    _val = _pass.get((CQ.BI.batch_key(_c["cb"]), _rr["no"]))
                    if _val:
                        _rr["res"] = _val
                        _filled += 1
        print("Internal CoA: %d determination(s) now cite one, %d result(s) unblocked"
              % (_cited, _filled))
    except Exception as _e:
        print("Internal CoA register not applied: %s" % _e)

    # Owner's ruling, 10.09.2026: one notation for a not-detected result, and it
    # is ND. The desk carried eight spellings of the same assertion on the
    # certificates alone. The audit of 11.09.2026 found five more families of the
    # same disease — below quantitation, the conformity verdict, absence, a
    # counted colony and a mass fraction — so result_vocabulary.canon() is now the
    # single definition and result_notation.nd() is the family inside it. It
    # rewrites the notation and nothing else: unit, footnote marker, re-test and
    # derived markers and residue glosses all survive, and a laboratory's own
    # non-conformity is preserved as a verdict rather than folded away. Applied
    # here, so the certificates, the desk and the PDFs inherit one spelling from
    # one place.
    #
    # The Macedonian half is added here and not in canon(), because the two
    # serve different readers. The workbook is the desk's own record and keeps
    # one word per assertion; the certificate is a bilingual controlled document
    # and prints both, in the ENG | MK convention the master already uses in its
    # sub-row labels. Owner's ruling of 11.09.2026: "Conforms | Одговара, and use
    # the formatting convention that is set for the rest of the CoQ text."
    try:
        import result_vocabulary as RV
        _nd = _bi = 0
        for _c in coqs:
            for _r in _c["rows"]:
                _v = _r.get("res")
                if not _v:
                    continue
                _no = str(_r.get("no") or "").strip()
                _w = RV.canon(_v, _no)
                if _w != _v:
                    _nd += 1
                _b = RV.bilingual(_w, _no)
                if _b != _w:
                    _bi += 1
                _r["res"] = _b
        print("Notation: %d printed result(s) in the controlled vocabulary; "
              "%d conformity result(s) paired with their Macedonian" % (_nd, _bi))
    except Exception as _e:
        print("Notation not normalised: %s" % _e)

    docs = [r for r in DR.load_register()
            if not r["code"].lower().startswith(("n/a", "(not numbered)"))]
    docs.sort(key=lambda r: (DR.key(r["date"]), r["row"]))
    seen = set()
    docs = [r for r in docs
            if not (r["code"].strip() in seen or seen.add(r["code"].strip()))]
    ver = DR.verified_map()
    rectmap = page_rect_map()
    corpus = corpus_rect_map()
    import verification_coverage as VC

    contradictions = []

    def rect_for(code):
        vals = next((rectmap[c] for c in VC.candidates(code) if c in rectmap), [])
        extra = corpus.get(code.strip(), [])
        have = {}
        for x in vals:
            have.setdefault(analyte(x["k"]), x)
        out = list(vals)
        for x in extra:
            a = analyte(x["k"])
            if a not in have:
                out.append(x)
                continue
            # the page always wins (trap 12): a corpus value that disagrees with
            # the page read of the same analyte is a corpus corruption. It is
            # recorded as a finding, never rendered beside the page value.
            # Compared by magnitude, not by string — the two sources write the
            # same number differently (Cyrillic х for ×, ^4 for a superscript,
            # decimal comma for point), and a notation difference is not a
            # disagreement.
            if disagree(have[a]["v"], x["v"]):
                contradictions.append({"code": code.strip(), "analyte": a,
                                       "page": have[a]["v"], "corpus": x["v"],
                                       "src": x["src"]})
        return out

    ecoa = [{
        "date": r["date"], "lab": r["lab"], "code": r["code"], "batch": r["batch"],
        "ref": r["ref"], "strain": r["strain"], "pn": r["pn"],
        "reported": r["reported"], "flag": ("red" if "red" in r["flags"] else
                                            ("amber" if r["flags"] else "")),
        "verified": bool(DR.page_verified(r["code"], ver)),
        "rect": rect_for(r["code"]),
        "why": FLAG_DOSSIER.get(r["code"].strip(), ""),
        "pdf": r["pdf"],
    } for r in docs]

    # The release-register view: every certificate row of every batch block,
    # with the column criteria, so the page can show the register the way the
    # published register artifact does — and judge values with the same
    # acceptance-limit rule.
    from openpyxl import load_workbook
    from openpyxl.utils import get_column_letter
    wb = load_workbook(CQ.REG_X)
    ws = wb[CQ.SHEET]
    columns = {}
    for cidx in range(5, 23):
        L = get_column_letter(cidx)
        columns[L] = {"name": str(ws.cell(row=4, column=cidx).value or ""),
                      "crit": str(ws.cell(row=5, column=cidx).value or "")}
    order, batches, _limits = CQ.read_register()
    reg = []
    for cb in order:
        b = batches[cb]
        by_code = OrderedDict()
        for L, lst in b["cells"].items():
            for c in lst:
                r = by_code.setdefault(c["code"], {
                    "code": c["code"], "date": c["date"], "lab": c["lab"],
                    "fam": c["family"], "stab": c["stability"], "vals": {},
                    "flags": {}})
                r["vals"][L] = c["value"]
                if c["flag"]:
                    r["flags"][L] = c["flag"]
        reg.append({"cb": cb, "pn": b["pnumber"], "strain": b["strain"],
                    "certs": list(by_code.values())})

    data = {
        "generated": "31.08.2026",
        "sop_effective": CQ.SOP_EFFECTIVE,
        "reg_columns": columns,
        "reg": reg,
        "dets": [{"no": d["no"], "group": d["group"], "en": d["en"],
                  "mk": d["mk"], "method": d["method"], "crit": d["criterion"],
                  "src": d["source"], "col": d["column"]} for d in dets],
        "coqs": coqs,
        "icoa_plan": plan,
        "ecoa": ecoa,
        "corpus_contradictions": contradictions,
    }
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{out}: {len(coqs)} CoQs, {sum(len(c['rows']) for c in coqs)} rows, "
          f"{len(plan)} iCoAs, {len(ecoa)} eCoA documents, "
          f"{os.path.getsize(out)//1024} KiB")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else
                  os.path.join(HERE, "coq_artifact_data.json")))
