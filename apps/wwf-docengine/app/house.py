# docengine.app.house — the approved, in-use house documents as a source the authors and checkers work from, not only a
# style sample (Head of QC, 19.10.2026: the builder and the agents "should also take into account those already approved
# and in-use SOPs, procedures, annexes … in addition to the regulatory database").
#
#   in_use_list()   every approved document the engine holds (newest version per code): what a new document may cite
#                   as a house document, by code and version, and what it must not contradict.
#   approved_text() an approved SOP's text, for an annex written to it when the engine did not write the SOP itself.
#   NOTE / RULE     how the authors and the checkers use them.
# The approved originals and QALI 001 stay the authority; this is the engine's working copy (CLAUDE.md §10).
from __future__ import annotations

import re

from . import db
from .house_codes import normalize, parts, version_key

NOTE = ("APPROVED, IN-USE HOUSE DOCUMENTS (DB3_PP_CURRENT). Follow their practice: the roles that do each step, the "
        "procedures and forms already in use, the terminology and the cross-references. The new document must not "
        "contradict them; where it must change something one of them says, write it as a change to that code and name "
        "it. Never copy a batch, date, result, person's name or any other value of a record from them.")
RULE = ("HOUSE DOCUMENTS IN USE — cite a house SOP, annex or form only from this list, by its code and version; never "
        "invent a code. A house document you need that is not listed goes under 'To be confirmed'.")
MAX_LIST = 200


async def in_use_list() -> list[dict]:
    """Newest approved version of every code the engine holds, in code order."""
    if not db.ready():
        return []
    best: dict[str, dict] = {}
    for r in await db.reference_list("approved"):
        if r["code"] not in best or version_key(r["version"]) > version_key(best[r["code"]]["version"]):
            best[r["code"]] = r
    return [best[c] for c in sorted(best)]


def list_block(docs: list[dict]) -> str:
    if not docs:
        return ""
    rows = [f"- {d['code']} v{d['version'] or '—'} — {d.get('title_en') or ''} | {d.get('title_mk') or ''}".rstrip(" |")
            for d in docs[:MAX_LIST]]
    return "\n".join([RULE, *rows])


async def approved_text(code: str) -> dict | None:
    """{markdown, version, id} of the newest approved version of `code`, or None."""
    for d in await in_use_list():
        if d["code"] == code:
            full = await db.reference_get(d["id"])
            return {"markdown": full["markdown"], "version": d["version"], "id": d["id"]} if full else None
    return None


# ---------- the documents an SOP works with (Head of QC, 19.10.2026) ----------
# An annex is written beside the forms and annexes its SOP already has. QCSOP001 names QCT002 (Request for analysis),
# QCT003, QCT004, QCT010, QCT012 and QCCoA001 in its text; the engine held all six and drafted a request form beside
# QCT002 without a word. A document is related to an SOP when its code carries the SOP's (…A01), when the register
# names the SOP as its parent, or when the approved SOP's own text names the code.
_CODE_IN_TEXT = re.compile(r"(?<![A-Za-z0-9])([A-Za-z]{2,6})[ _\-]?(\d{2,3})(?:[ _\-]?[AА][ _\-]?(\d{1,2}))?(?![A-Za-z0-9])")
RELATED_NOTE = ("IN-USE DOCUMENTS OF THE PARENT SOP (approved; the SOP names them or they are its annexes). The new "
                "annex is written beside them: it must not duplicate what one of them already records, it refers to "
                "them by code where the SOP does, and it follows their structure and wording. Take no value from them.")
MAX_RELATED, MAX_RELATED_CHARS = 12, 36_000


def listed_codes(markdown: str, known: set[str]) -> list[str]:
    """House codes an approved document's text names, in order of first mention, limited to `known` codes."""
    out: list[str] = []
    for fam, num, ann in _CODE_IN_TEXT.findall(markdown or ""):
        c = normalize(f"{fam}{num}" + (f"A{ann}" if ann else ""))
        if c and c in known and c not in out:
            out.append(c)
    return out


def relations(sop: str, codes: list[str], parents: dict[str, str], listed: list[str]) -> list[tuple[str, str]]:
    """(code, relation) of every code tied to `sop`: 'annex' by code, 'child' by register parent, 'listed' by the
    SOP's text — first match wins, in code order."""
    out: dict[str, str] = {}
    for c in codes:
        if c != sop and c.startswith(sop + "A") and c[len(sop) + 1:].isdigit():
            out[c] = "annex"
    for c, par in parents.items():
        if c != sop and par == sop and c in codes:
            out.setdefault(c, "child")
    for c in listed:
        if c != sop:
            out.setdefault(c, "listed")
    return sorted(out.items())


async def related(code: str) -> dict:
    """The approved copy of `code` and the in-use documents tied to it (GET /house/related/{code})."""
    code = normalize(code) or code
    docs = await in_use_list()
    by_code = {d["code"]: d for d in docs}
    sop = by_code.get(code)
    if not sop:
        return {"code": code, "found": False, "version": "", "title_en": "", "title_mk": "", "related": []}
    full = await db.reference_get(sop["id"])
    listed = listed_codes((full or {}).get("markdown") or "", set(by_code))
    parents = {d["code"]: d.get("parent") or "" for d in docs}
    rel = [{"code": c, "version": by_code[c]["version"], "title_en": by_code[c].get("title_en") or "",
            "title_mk": by_code[c].get("title_mk") or "", "relation": r, "chars": by_code[c].get("chars") or 0}
           for c, r in relations(code, list(by_code), parents, listed)]
    return {"code": code, "found": True, "version": sop["version"], "title_en": sop.get("title_en") or "",
            "title_mk": sop.get("title_mk") or "", "related": rel}


async def related_block(code: str) -> tuple[str, list[str]]:
    """The related documents' text for an annex job's authors, within a budget, and the codes it holds."""
    info = await related(code)
    docs = await in_use_list()
    by_code = {d["code"]: d for d in docs}
    parts, codes, total = [], [], 0
    for r in info["related"][:MAX_RELATED]:
        full = await db.reference_get(by_code[r["code"]]["id"])
        text = ((full or {}).get("markdown") or "").strip()
        if not text or total >= MAX_RELATED_CHARS:
            continue
        text = text[:MAX_RELATED_CHARS - total]
        total += len(text)
        codes.append(r["code"])
        parts.append(f"«{r['code']} v{r['version']} — {r['title_en'] or r['title_mk']}» ({r['relation']}):\n{text}")
    if not parts:
        return "", []
    return RELATED_NOTE + "\n\n" + "\n\n".join(parts), codes


async def listed_map(refs: list[dict] | None = None) -> dict[str, list[str]]:
    """code → the known codes each approved SOP's text names (one read per approved SOP, for the Library)."""
    if not db.ready():
        return {}
    docs = await in_use_list()
    known = {d["code"] for d in docs}
    out: dict[str, list[str]] = {}
    for d in docs:
        try:
            fam, _num, annex = parts(d["code"])
        except ValueError:
            continue
        if annex is not None or not fam.upper().endswith("SOP"):
            continue
        full = await db.reference_get(d["id"])
        out[d["code"]] = listed_codes((full or {}).get("markdown") or "", known)
    return out


# ---------- house consistency: which documents a draft is checked against (Head of QC, 19.10.2026) ----------
# The regulatory checker sees the four passages most like each section, so an approved procedure that contradicts the
# draft in other words could go unseen, and nothing said which documents were looked at. The house check reads the
# full text of a named set, and the job keeps the set.
MAX_CHECK, MAX_CHECK_DOC_CHARS, MAX_CHECK_BATCH_CHARS = 10, 15_000, 48_000
_WORD = re.compile(r"[A-Za-zА-Яа-яЀ-ӿ]{4,}")
_STOP = {"standard", "operating", "procedure", "стандардна", "оперативна", "процедура", "form", "образец", "record",
         "запис", "list", "листа", "document", "документ", "with", "from", "this", "that", "and/or", "или", "за"}


def _words(title: str) -> set[str]:
    return {w.lower() for w in _WORD.findall(title or "") if w.lower() not in _STOP}


def check_set(code: str, parent: str, markdown: str, title_en: str, title_mk: str, docs: list[dict],
              parents: dict[str, str], listed_by: dict[str, list[str]]) -> list[dict]:
    """The approved documents a draft is checked against, in priority order, each with why: the approved version the
    draft revises, its parent SOP and the documents tied to that SOP, the documents the draft itself names, and the
    approved documents whose title shares two or more significant words with the draft's."""
    by_code = {d["code"]: d for d in docs}
    out: dict[str, str] = {}

    def add(c: str, why: str) -> None:
        if c in by_code and c not in out:
            out[c] = why
    add(code, "the approved version this draft revises")
    if parent:
        add(parent, "the parent SOP")
        for c, rel in relations(parent, list(by_code), parents, listed_by.get(parent, [])):
            add(c, f"{rel} of the parent SOP {parent}")
    for c in listed_codes(markdown, set(by_code)):
        add(c, "named in the draft")
    mine = _words(title_en) | _words(title_mk)
    scored = sorted(((len(mine & (_words(d.get("title_en", "")) | _words(d.get("title_mk", "")))), d["code"])
                     for d in docs), reverse=True)
    for n, c in scored:
        if n >= 2:
            add(c, "a title like this draft's")
    return [{"code": c, "version": by_code[c]["version"], "title": by_code[c].get("title_en") or by_code[c].get("title_mk")
             or "", "id": by_code[c]["id"], "why": why} for c, why in list(out.items())[:MAX_CHECK]]


_VERDICT = re.compile(r"^\W*HOUSE\s+([A-Za-z]{2,8}\s?\d{1,3}(?:\s?A\s?\d{1,2})?)\s*:\s*"
                      r"(CONSISTENT|NOT RELEVANT|CHANGES|CONFLICT)\b\s*[—\-:]*\s*(.*)$", re.M | re.I)


def parse_verdicts(reply: str, expected: list[str]) -> dict[str, dict]:
    """code → {verdict, detail} from the checker's lines; a document it did not answer is 'UNCHECKED'."""
    got: dict[str, dict] = {}
    for m in _VERDICT.finditer(reply or ""):
        c = normalize(m.group(1)) or m.group(1)
        if c in expected and c not in got:
            got[c] = {"verdict": m.group(2).upper(), "detail": m.group(3).strip()[:1200]}
    return {c: got.get(c, {"verdict": "UNCHECKED", "detail": "the checker gave no verdict for it"}) for c in expected}


async def checking_docs(code: str, parent: str, markdown: str, title_en: str, title_mk: str) -> list[dict]:
    """check_set over the library, each document with its approved text (cut at MAX_CHECK_DOC_CHARS)."""
    docs = await in_use_list()
    if not docs:
        return []
    by_code = {d["code"]: d for d in docs}
    listed_by: dict[str, list[str]] = {}
    if parent in by_code:
        full = await db.reference_get(by_code[parent]["id"])
        listed_by[parent] = listed_codes((full or {}).get("markdown") or "", set(by_code))
    chosen = check_set(code, parent, markdown, title_en, title_mk, docs,
                       {d["code"]: d.get("parent") or "" for d in docs}, listed_by)
    for d in chosen:
        full = await db.reference_get(d["id"])
        d["text"] = ((full or {}).get("markdown") or "")[:MAX_CHECK_DOC_CHARS]
    return [d for d in chosen if d["text"].strip()]


def batches(docs: list[dict]) -> list[list[dict]]:
    """Documents grouped so one checker exchange stays within MAX_CHECK_BATCH_CHARS."""
    out: list[list[dict]] = [[]]
    size = 0
    for d in docs:
        if out[-1] and size + len(d["text"]) > MAX_CHECK_BATCH_CHARS:
            out.append([])
            size = 0
        out[-1].append(d)
        size += len(d["text"])
    return [b for b in out if b]
