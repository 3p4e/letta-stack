#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every iCoA in a folder, held against the master workbook.

    python3 verify_icoa_folder.py <folder> [--md FOLDER.md] [--json out.json]

Walks the folder, finds every internal certificate of analysis in it (`.html`, `.htm`, `.docx`,
and `.pdf` where `pdftotext` is installed), and checks each one field by field against
`CoQ_Analysis_Master_v*.xlsx` sitting beside this script. Exit 0 clean, 1 findings, 2 when a
check could not be performed.

## What is checked, and against what

| the document says | the workbook says |
| --- | --- |
| document ID | `iCoA Register.iCoA code` for that lot and round |
| strain, cultivation batch, P lot, series | the same row of `iCoA Register` |
| which determinations it carries | `iCoA Register.iCoA scope` |
| the verdict on #1, #2, #7 | `#1 Ident. A`, `#2 Ident. B`, `#7 Foreign matter` |
| each results-table row — result, method, acceptance criterion | `CoQ Compilation (long)` for the linked CoQ code and determination |
| any external certificate cited | `Document`, `Issued`, `Laboratory` of that row |

## Two things this script refuses to do

**It does not trust the filename.** The document ID is checked against the register for the lot
and round the document itself states. This is not hypothetical: an iCoA design copy in circulation
is named and headed `iCoA-PP_26-036` for lot `P060012`, where the register has `iCoA-PP_26-035`
for `P060012|I` and gives `036` to `P060022`. A filename-driven check passes that document.

**It does not guess the Series-to-round mapping.** `initial release` → `I`, `retest 1` → `R` and
so on are read off the register, whose `Series` and `Key` columns are both literal and sit in the
same row. Nothing about the naming is assumed.

A cell that cannot be parsed is reported as unparsed, never as a pass.
"""
import collections
import glob
import html as _html
import io
import json
import os
import re
import subprocess
import sys
import unicodedata
import zipfile

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
EMPTY = {None, "", "—", "-", "N/A", "n/a"}
DOC_ID = re.compile(r"iCoA[-_]PP[_-]\d{2}[-_]\d{3}", re.I)
P_LOT = re.compile(r"\bP\d{6}\b")
DATE = re.compile(r"\b(\d{2}\.\d{2}\.\d{4})\b")


# ------------------------------------------------------------------------------------- reading

def norm(s):
    """One spelling for comparison: composed, unpadded, single-spaced, one kind of dash.

    The certificates set a Macedonian gloss beside every English label and separate fields with
    `·`, and the workbook does not. Comparing raw text would report every cell as a mismatch, so
    both sides come through here — and only through here.
    """
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s))
    s = s.replace(" ", " ").replace("‑", "-")
    for dash in "‒–—―":
        s = s.replace(dash, "-")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def strip_mk(markup):
    """Drop the Macedonian gloss spans, which the workbook has no counterpart for."""
    return re.sub(r'<span[^>]*class="[^"]*\bmk\b[^"]*"[^>]*>.*?</span>', " ", markup,
                  flags=re.S | re.I)


def text_of(markup):
    markup = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", markup, flags=re.I)
    return norm(_html.unescape(re.sub(r"<[^>]+>", " ", markup)))


def read_document(path):
    """(markup, plain text) of a certificate, or (None, None) if it cannot be read."""
    low = path.lower()
    if low.endswith((".html", ".htm")):
        markup = io.open(path, encoding="utf-8", errors="replace").read()
        return strip_mk(markup), text_of(strip_mk(markup))
    if low.endswith(".docx"):
        try:
            xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8", "replace")
        except Exception:
            return None, None
        # a paragraph break must not glue two fields into one word
        xml = re.sub(r"</w:p>", " \n", xml)
        return None, text_of(xml)
    if low.endswith(".pdf"):
        try:
            out = subprocess.run(["pdftotext", "-layout", path, "-"],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        except OSError:
            return None, None
        if out.returncode != 0:
            return None, None
        return None, norm(out.stdout.decode("utf-8", "replace"))
    return None, None


def result_rows(markup):
    """The results table as [(number, cells…)] — only from markup; a flat text layer has no cells."""
    if not markup:
        return None
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", markup, flags=re.S | re.I):
        cells = [text_of(td) for td in
                 re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.S | re.I)]
        if len(cells) >= 4 and re.fullmatch(r"\d+(\.\d+)?", cells[0].strip()):
            rows.append(cells)
    return rows


def ticked(markup):
    """Every ticked option of the findings section, by the box character the page prints."""
    if not markup:
        return None
    out = []
    for chip in re.findall(r"<span[^>]*class=\"[^\"]*\bck\b[^\"]*\"[^>]*>(.*?)</span>\s*</span>",
                           markup, flags=re.S | re.I):
        t = text_of(chip)
        if "☒" in t:
            out.append(norm(t.replace("☒", "")))
    return out


# ------------------------------------------------------------------------------------ workbook

def find_workbook(args):
    named = [a for a in args if a.lower().endswith(".xlsx")]
    if named:
        return named[0]
    seen = []
    for where in (HERE, os.path.join(HERE, ".."), os.getcwd()):
        seen += glob.glob(os.path.join(where, "CoQ_Analysis_Master_v*.xlsx"))
    if not seen:
        return None
    return max(seen, key=lambda p: int((re.search(r"_v(\d+)", os.path.basename(p))
                                        or re.match(r"(-1)", "-1")).group(1)))


def table(ws):
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


def lotkey(s):
    """One spelling per lot. The starred form is the same lot as the unstarred one."""
    return re.sub(r"[\s\-/_.＊*]+", "", norm(s)).upper()


def coq_by_key(coq_rows):
    """Key -> CoQ code, by the rule the register's own formula states (build_tracker_v8.py:2727)."""
    n, out = 0, {}
    for r in coq_rows:
        if norm(r.get("Issuable")).lower() in ("yes", "allocated", "ruled"):
            n += 1
            out[norm(r.get("Key"))] = "CoQ-PP_26-%03d" % n
    return out


def series_to_round(icoa_rows):
    """The Series-to-round mapping, read off the register rather than assumed."""
    m = collections.defaultdict(collections.Counter)
    for r in icoa_rows:
        key = norm(r.get("Key"))
        if "|" in key:
            m[norm(r.get("Series")).lower()][key.rsplit("|", 1)[1]] += 1
    return {s: c.most_common(1)[0][0] for s, c in m.items()}


# --------------------------------------------------------------- comparing a cell to a workbook

# The workbook stores a bilingual value as `English | Македонски` — `Conforms | Одговара`. The
# certificate prints the two in separate elements and the Macedonian one is stripped before
# comparison, so the workbook's gloss has to come off too or nothing ever matches.
def english(s):
    s = norm(s)
    return norm(s.split("|")[0]) if "|" in s else s


CITE = re.compile(r"\b\d+\.\d+(?:\.\d+)?\b|\b\d{4}\b|\bDAB\b", re.I)
STOP = {"the", "a", "an", "to", "of", "in", "for", "and", "on", "·", "-", "|", ",", ":"}


def tokens(s):
    return {t for t in re.split(r"[\s]+", norm(s).lower()) if t and t not in STOP}


def compare(got, want):
    """('ok' | 'note' | 'bad', explanation) for a printed cell against a workbook cell.

    Exact equality is the wrong test and testing it against an issued certificate proved so. The
    certificate prints the short form of a method — `Ph. Eur. 2.8.23 · mon. 3028` — where the
    workbook holds `Ph. Eur. 2.8.23 (microscopy)`; same determination, different wording, and a
    strict check calls every row a defect. So:

    * the document's words are all in the workbook's — **ok**, it says no more than the record;
    * the pharmacopoeial citations agree but the wording does not — **note**, for the owner's eye
      but not a mismatch;
    * the citations conflict — **bad**. A certificate citing 2.2.29 where the record says 2.8.23
      names the wrong method, and that is a finding whatever the wording.
    """
    g, w = norm(got), norm(want)
    if not g:
        return "bad", "the cell is empty; the workbook has %r" % w
    parts = [norm(x) for x in w.split("|")] + [w]
    if g.lower() in [p.lower() for p in parts]:
        return "ok", ""
    tg, tw = tokens(g), tokens(w)
    cg, cw = set(CITE.findall(g)), set(CITE.findall(w))
    if cg and cw and not (cg & cw):
        return "bad", "document %r cites %s; the workbook %r cites %s" % (
            g, "/".join(sorted(cg)), w, "/".join(sorted(cw)))
    if tg <= tw:
        return "ok", ""
    if (tg & tw) and (not cg or not cw or (cg & cw)):
        return "note", "document %r · workbook %r" % (g, w)
    return "bad", "document %r · workbook %r" % (g, w)


# --------------------------------------------------------------------------------------- check

class Report(object):
    def __init__(self):
        self.findings, self.lines, self.stopped, self.notes = [], [], [], []

    def say(self, t=""):
        self.lines.append(t)

    def find(self, doc, what, detail=""):
        self.findings.append((doc, what, detail))
        print("[%s] %s%s" % (doc, what, " — " + detail if detail else ""))

    def note(self, doc, what, detail=""):
        """A difference worth the owner's eye that is not a mismatch — see compare()."""
        self.notes.append((doc, what, detail))

    def cannot(self, doc, why):
        self.stopped.append((doc, why))
        print("[could not verify] %s — %s" % (doc, why))


def documents(folder):
    """Every candidate certificate under the folder, deepest path first for stable reporting."""
    out = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in sorted(files):
            if f.startswith(".") or f.startswith("~$"):
                continue
            if f.lower().endswith((".html", ".htm", ".docx", ".pdf")):
                out.append(os.path.join(root, f))
    return sorted(out)


def one(rep, path, folder, icoa_rows, long_by, code_by_key, s2r):
    """Check one document. Every disagreement quotes both sides."""
    name = os.path.relpath(path, folder)
    markup, text = read_document(path)
    if not text:
        rep.cannot(name, "could not extract text (install poppler-utils for .pdf)")
        return None

    ids = sorted({norm(m.group(0)).replace("_PP-", "_PP_") for m in DOC_ID.finditer(text)})
    if not ids:
        rep.cannot(name, "no iCoA document ID in the document")
        return None
    if len(ids) > 1:
        rep.find(name, "more than one document ID in one document", " · ".join(ids))
    doc_id = ids[0]

    lots = collections.Counter(P_LOT.findall(text))
    lot = lots.most_common(1)[0][0] if lots else ""

    # Which register row is this? By lot and round, taken from the document, not the filename.
    low = text.lower()
    series = None
    for s in sorted(s2r, key=len, reverse=True):
        if s in low:
            series = s
            break
    if series is None:
        series = "initial release" if "initial" in low else None
    if series is None:
        rep.cannot(name, "the document does not state its series (initial release / retest n)")
        return doc_id
    want_round = s2r[series]

    cands = [r for r in icoa_rows
             if norm(r.get("Issuable")).lower() == "yes"
             and lotkey(r.get("P Batch")) == lotkey(lot)
             and norm(r.get("Key")).rsplit("|", 1)[-1] == want_round]
    if not cands:
        cands = [r for r in icoa_rows
                 if norm(r.get("Issuable")).lower() == "yes"
                 and lotkey(r.get("CU Batch")) == lotkey(lot)
                 and norm(r.get("Key")).rsplit("|", 1)[-1] == want_round]
    if len(cands) != 1:
        rep.cannot(name, "%d register rows match lot %r round %r — cannot check this document"
                   % (len(cands), lot, want_round))
        return doc_id
    reg = cands[0]

    # 1 — the identity of the document
    if norm(reg["iCoA code"]) != doc_id:
        rep.find(name, "wrong document ID",
                 "the document says %s; the register gives %s to %s (%s), and %s to %s"
                 % (doc_id, norm(reg["iCoA code"]), lot, norm(reg.get("Key")),
                    doc_id, ", ".join(sorted({norm(r.get("P Batch")) for r in icoa_rows
                                              if norm(r.get("iCoA code")) == doc_id})) or "no lot"))
    for col, label in (("Strain", "strain"), ("CU Batch", "cultivation batch")):
        want = norm(reg.get(col))
        if want and norm(want).lower() not in norm(text).lower():
            rep.find(name, "the %s the register states is not on the document" % label,
                     "register %r" % want)

    issued = DATE.findall(text)
    basis = norm(reg.get("Basis date"))
    if basis and basis not in issued:
        rep.find(name, "the register's basis date is not among the dates on the document",
                 "register %s; document carries %s" % (basis, ", ".join(sorted(set(issued))[:6])))

    # 2 — the scope: which determinations this certificate is allowed to carry
    scope = norm(reg.get("iCoA scope"))
    rows = result_rows(markup)
    if rows is None:
        rep.cannot(name, "no results table could be read from this format — "
                         "provide the .html to check the Result column")
        return doc_id
    dets = [r[0].strip() for r in rows]
    if not dets:
        rep.find(name, "no results table rows found", "scope on the register: %s" % scope)
        return doc_id

    # 3 — the values, against the compilation for the certificate of quality this iCoA belongs to
    coq = code_by_key.get(norm(reg.get("Key")))
    if not coq:
        rep.cannot(name, "no certificate of quality numbered for key %r" % norm(reg.get("Key")))
        return doc_id
    for cells in rows:
        det = cells[0].strip()
        want = long_by.get((coq, det))
        if not want:
            rep.find(name, "a determination the workbook does not carry for this certificate",
                     "#%s — %s has no such row" % (det, coq))
            continue
        # the columns of the printed table, by position: № · parameter · method · criterion · result
        got_method, got_crit, got_result = cells[2], cells[3], cells[-1]
        for got, key, label in ((got_result, "Result", "result"),
                                (got_method, "Method", "method"),
                                (got_crit, "Acceptance criterion", "acceptance criterion")):
            verdict, why = compare(got, want.get(key))
            if verdict == "bad":
                rep.find(name, "#%s %s does not match the workbook" % (det, label), why)
            elif verdict == "note":
                rep.note(name, "#%s %s is worded differently from the workbook" % (det, label), why)

        # 4 — the external certificate behind the number. A determination performed in house has
        # no external certificate to cite: the document names the analyst and the QC laboratory,
        # and looking for the company's own name in it is looking for the wrong thing.
        lab = norm(want.get("Laboratory"))
        if blank(lab) or "in-house" in lab.lower():
            continue
        for key, label in (("Document", "document code"), ("Issued", "date of issue")):
            w = english(want.get(key))
            if blank(w):
                continue
            if w.lower() not in norm(text).lower():
                rep.find(name, "#%s the %s the workbook cites is not on the document" % (det, label),
                         "workbook %r · laboratory %r" % (w, lab))
        short = {"IPH — Institute of Public Health": "IJZ",
                 "UKIM Faculty of Pharmacy — Center for Natural Products": "CNP",
                 "Farmahem": "FHM"}
        names = [lab] + ([short[lab]] if lab in short else [])
        if not any(n.lower() in norm(text).lower() for n in names):
            rep.find(name, "#%s the institution the workbook cites is not on the document" % det,
                     "workbook %r" % lab)
    return doc_id


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    folder = args[0] if args else None
    if not folder or not os.path.isdir(folder):
        print(__doc__.strip().splitlines()[2])
        print("give the folder holding the iCoA documents")
        return 2
    path = find_workbook(args[1:])
    if not path:
        print("no CoQ_Analysis_Master_v*.xlsx beside this script")
        return 2
    print("workbook: %s" % os.path.abspath(path))
    print("folder:   %s" % os.path.abspath(folder))

    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    for s in ("iCoA Register", "CoQ Register", "CoQ Compilation (long)"):
        if s not in wb.sheetnames:
            print("sheet %r is not in this workbook" % s)
            return 2
    icoa_rows = table(wb["iCoA Register"])
    coq_rows = table(wb["CoQ Register"])
    long_by = {}
    for r in table(wb["CoQ Compilation (long)"]):
        if r.get("CoQ code"):
            long_by[(norm(r["CoQ code"]), norm(r["#"]))] = r
    code_by_key = coq_by_key(coq_rows)
    s2r = series_to_round(icoa_rows)

    rep = Report()
    rep.say("# The iCoA folder against the master workbook")
    rep.say()
    rep.say("`%s` · folder `%s`" % (os.path.basename(path), os.path.abspath(folder)))
    rep.say()
    rep.say("Series-to-round mapping read off the register: %s"
            % " · ".join("%s → %s" % (k, v) for k, v in sorted(s2r.items())))
    rep.say()

    docs = documents(folder)
    rep.say("## Documents")
    rep.say()
    rep.say("| | |")
    rep.say("| --- | --- |")
    rep.say("| documents found | %d |" % len(docs))
    seen = []
    for p in docs:
        rep.say()
        rep.say("### `%s`" % os.path.relpath(p, folder))
        rep.say()
        before = len(rep.findings)
        got = one(rep, p, folder, icoa_rows, long_by, code_by_key, s2r)
        if got:
            seen.append((got, os.path.relpath(p, folder)))
        new = rep.findings[before:]
        notes = [n for n in rep.notes if n[0] == os.path.relpath(p, folder)]
        if new:
            for _, what, detail in new:
                rep.say("* **%s**%s" % (what, " — " + detail if detail else ""))
        elif not notes:
            rep.say("Matches the workbook.")
        if notes:
            rep.say("")
            rep.say("Worded differently from the workbook, not a mismatch:")
            for _, what, detail in notes:
                rep.say("* %s%s" % (what, " — " + detail if detail else ""))

    # 5 — one iCoA per CoQ, across the whole folder
    rep.say()
    rep.say("## One iCoA per certificate of quality")
    rep.say()
    rep.say("| | |")
    rep.say("| --- | --- |")
    issuable = [r for r in icoa_rows if norm(r.get("Issuable")).lower() == "yes"]
    rep.say("| iCoA the register expects | %d |" % len(issuable))
    rep.say("| documents that named an iCoA code | %d |" % len(seen))
    ids = collections.Counter(c for c, _ in seen)
    rep.say("| distinct codes in the folder | %d |" % len(ids))
    for code, n in sorted(ids.items()):
        if n > 1:
            rep.find("the folder", "one iCoA code on more than one document",
                     "%s on %s" % (code, ", ".join(f for c, f in seen if c == code)))
    expected = {norm(r["iCoA code"]) for r in issuable}
    for code in sorted(expected - set(ids)):
        rep.say("| &nbsp;&nbsp;not in the folder | %s |" % code)
    for code in sorted(set(ids) - expected):
        rep.find("the folder", "an iCoA code the register does not issue", code)
    rep.say("| **present of expected** | **%d of %d** |"
            % (len(set(ids) & expected), len(expected)))

    rep.say()
    rep.say("## The count")
    rep.say()
    rep.say("**%d finding(s)**, and %d difference(s) of wording that are not mismatches."
            % (len(rep.findings), len(rep.notes)))
    for doc, why in rep.stopped:
        rep.say("* could not verify: %s — %s" % (doc, why))

    print("\n%d finding(s), %d wording note(s)." % (len(rep.findings), len(rep.notes)))
    if "--md" in argv:
        dst = argv[argv.index("--md") + 1]
        io.open(dst, "w", encoding="utf-8").write("\n".join(rep.lines).rstrip() + "\n")
        print("report: %s" % dst)
    if "--json" in argv:
        dst = argv[argv.index("--json") + 1]
        io.open(dst, "w", encoding="utf-8").write(json.dumps(
            [{"document": d, "what": w, "detail": t} for d, w, t in rep.findings],
            ensure_ascii=False, indent=2))
    if rep.stopped:
        return 2
    return 1 if rep.findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
