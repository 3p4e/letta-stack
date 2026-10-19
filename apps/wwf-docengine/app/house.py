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

from . import db

NOTE = ("APPROVED, IN-USE HOUSE DOCUMENTS (DB3_PP_CURRENT). Follow their practice: the roles that do each step, the "
        "procedures and forms already in use, the terminology and the cross-references. The new document must not "
        "contradict them; where it must change something one of them says, write it as a change to that code and name "
        "it. Never copy a batch, date, result, person's name or any other value of a record from them.")
RULE = ("HOUSE DOCUMENTS IN USE — cite a house SOP, annex or form only from this list, by its code and version; never "
        "invent a code. A house document you need that is not listed goes under 'To be confirmed'.")
MAX_LIST = 200


def _key(v: str) -> tuple:
    try:
        return (0, float(v))
    except (TypeError, ValueError):
        return (1, str(v))


async def in_use_list() -> list[dict]:
    """Newest approved version of every code the engine holds, in code order."""
    if not db.ready():
        return []
    best: dict[str, dict] = {}
    for r in await db.reference_list("approved"):
        if r["code"] not in best or _key(r["version"]) > _key(best[r["code"]]["version"]):
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
