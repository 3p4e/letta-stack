# docengine.app.library — the Library's shelves (Head of QC, 18.10.2026: "rethink the organisation … of the doc library,
# the approved and in use, the open drafts").
#
# One entry per document code, from four sources:
#   register        register/*.yaml — the code, its titles and its status in QALI 001 (or the department's known list)
#   reference docs  the approved, in-use documents (text of the Word file) and the ACME_SOP work in progress
#   engine builds   docengine.documents — what the engine itself built and registered
#   open jobs       workflow jobs not failed — drafts the engine is writing or holding for review
#
# Shelves, first match wins:
#   retired         superseded or withdrawn
#   revision        in use, and a new version is being written (QALI "под ревизија", or a draft exists for it)
#   approved        approved and in use
#   drafts          being written: a work-in-progress document, an engine draft, or a register draft
#   numbers         only a number so far: reserved, unconfirmed or known from a file
# Not a QMS record (CLAUDE.md §10): QALI 001 and the paper system stay the authority.
from __future__ import annotations

from .house import relations
from .house_codes import parts, version_key

SHELVES = ("approved", "revision", "drafts", "numbers", "retired")
_IN_USE = ("effective", "effective_revising")


def shelve(register: list[dict], references: list[dict], builds: list[dict], jobs: dict[str, list[dict]],
           listed: dict[str, list[str]] | None = None) -> dict:
    entries: dict[str, dict] = {}

    def entry(code: str) -> dict:
        return entries.setdefault(code, {"code": code, "parent": "", "department": "", "title_mk": "", "title_en": "",
                                         "status": "", "version": "", "effective_date": "", "approved": None,
                                         "wip": [], "builds": [], "jobs": [], "notes": []})

    for r in register:
        e = entry(r["code"])
        e.update(parent=r.get("parent", ""), department=r.get("department", ""), status=r.get("status", ""),
                 title_mk=r.get("title_mk", ""), title_en=r.get("title_en", ""),
                 version=str(r.get("version", "") or ""), effective_date=r.get("effective_date", "") or "")
    for ref in references:
        e = entry(ref["code"])
        brief = {k: ref.get(k) for k in ("id", "version", "title_en", "effective_date", "chars", "ragflow_doc_id", "package")}
        if ref["kind"] == "approved":
            if e["approved"] is None or version_key(ref.get("version", "")) > version_key(e["approved"].get("version", "")):
                e["approved"] = brief
        else:
            e["wip"].append(brief)
        for k in ("title_mk", "title_en", "parent", "department"):
            if not e[k] and ref.get(k):
                e[k] = ref[k]
    for b in builds:
        entry(b["code"])["builds"].append({k: b.get(k) for k in ("id", "version", "doctype", "created_at", "job_id")})
    for code, js in jobs.items():
        entry(code)["jobs"] = js

    for e in entries.values():
        st, has_draft = e["status"], bool(e["wip"] or e["jobs"])
        if e["approved"] and e["status"] and e["status"] not in _IN_USE:
            e["notes"].append(f"an approved copy is held, but the register says {e['status']}")
        if e["approved"] and e["version"] and e["approved"]["version"] and e["approved"]["version"] != e["version"]:
            e["notes"].append(f"approved copy is v{e['approved']['version']}, the register says v{e['version']}")
        if st in ("superseded", "withdrawn"):
            e["shelf"] = "retired"
        elif st == "effective_revising" or ((st == "effective" or e["approved"]) and has_draft):
            e["shelf"] = "revision"
        elif st == "effective" or e["approved"]:
            e["shelf"] = "approved"
        elif has_draft or e["builds"] or st in ("draft", "awaiting_signature"):
            e["shelf"] = "drafts"
        else:
            e["shelf"] = "numbers"

    shelves = {s: [] for s in SHELVES}
    for code in sorted(entries):
        shelves[entries[code]["shelf"]].append(entries[code])
    pk = packages(entries, listed or {})
    return {"shelves": shelves, "counts": {s: len(v) for s, v in shelves.items()}, **pk}


def _is_sop(code: str) -> bool:
    try:
        fam, num, annex = parts(code)
    except ValueError:
        return False
    return annex is None and fam.upper().endswith("SOP")


def packages(entries: dict[str, dict], listed: dict[str, list[str]]) -> dict:
    """The Library by document package (Head of QC, 19.10.2026): every SOP with its annexes and the documents tied
    to it — by code (…A01), by the register's parent, or named in the approved SOP's text — in two groups, the
    packages whose SOP is in use and the packages still being written; the documents under no SOP are listed loose."""
    codes = sorted(entries)
    parents = {c: entries[c].get("parent") or "" for c in codes}
    in_pkg: set[str] = set()
    pk = {"in_use": [], "drafts": []}
    for c in codes:
        if not _is_sop(c):
            continue
        members = []
        for m, rel in relations(c, codes, parents, listed.get(c, [])):
            members.append({**entries[m], "relation": rel})
            in_pkg.add(m)
        in_pkg.add(c)
        group = "in_use" if entries[c]["shelf"] in ("approved", "revision") else "drafts"
        pk[group].append({"sop": entries[c], "members": members})
    loose = {"in_use": [], "drafts": []}
    for c in codes:
        if c in in_pkg:
            continue
        loose["in_use" if entries[c]["shelf"] in ("approved", "revision") else "drafts"].append(entries[c])
    return {"packages": pk, "loose": loose}
