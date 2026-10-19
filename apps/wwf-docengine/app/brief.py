# docengine.app.brief — the Document Brief: one saved draft that the single workflow edits page by page (Head of QC,
# 18.10.2026: "only one workflow … step lock in aware, modification lock in aware … in every screen … the option to click
# build").
#
# A brief holds the package (SOP, SOP + annexes, an annex for an SOP, a form, a report), the document's identity (meta),
# its fields — purpose, scope, use, responsibilities, references and every questionnaire answer — the annexes of a
# package and the uploaded sources. Every field has a state:
#   suggested   offered (a default or an agent's proposal), not decided by the requester
#   chosen      set by the requester
#   locked      chosen and fixed: no rule, agent or later change overwrites it until it is unlocked
# and `stale` when a field it depends on changed after it was chosen; a stale field is re-confirmed, never rewritten.
# Every change is one event with its before and after, so the brief's history is complete; `rev` increases by one per
# change and a PATCH that names an older rev is refused (two tabs never overwrite each other).
#
# A brief can be built from any page. What the requester has not decided is filled by the authors and listed as
# `assumed`, which the job keeps and the review report shows. Not a QMS record (CLAUDE.md §10).
from __future__ import annotations

import copy
from datetime import datetime, timezone

from .questionnaires import QUESTIONNAIRES

PACKAGES = ("sop", "sop_annexes", "annex", "form", "report")
STATES = ("suggested", "chosen", "locked")
# The pages that define the document: a change to one of them makes every decided answer below it stale.
# The brief's own pages are "doc.*", so they never collide with a questionnaire answer's key (sop_qc has "purpose").
CORE = ("doc.purpose", "doc.scope_in", "doc.scope_out", "doc.use")
TEXT_FIELDS = CORE + ("doc.responsibilities", "doc.references", "doc.notes")
TEXT_LABEL = {"doc.purpose": "Purpose", "doc.scope_in": "Scope — included", "doc.scope_out": "Scope — excluded",
              "doc.use": "Use and users", "doc.responsibilities": "Responsibilities", "doc.references": "References",
              "doc.notes": "Further instructions"}
META_KEYS = ("title_mk", "title_en", "code", "version", "department", "orient")
DEFAULT_BANK = {"sop": "sop_qc", "sop_annexes": "sop_qc", "annex": "annex_form", "form": "annex_form",
                "report": "annex_form"}
MAX_SOURCE_CHARS, MAX_SOURCES_CHARS = 12_000, 40_000


class BriefError(ValueError):
    status = 400


class BriefConflict(BriefError):
    status = 409


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_brief(package: str, meta: dict | None = None, questionnaire: str = "", parent_sop: str = "") -> dict:
    if package not in PACKAGES:
        raise BriefError(f"package must be one of {', '.join(PACKAGES)}")
    q = questionnaire or DEFAULT_BANK[package]
    if q not in QUESTIONNAIRES:
        raise BriefError("unknown questionnaire")
    return {"rev": 0, "status": "open", "package": package, "questionnaire": q, "parent_sop": parent_sop,
            "meta": {k: v for k, v in (meta or {}).items() if k in META_KEYS and v}, "fields": {}, "annexes": [],
            "job_ids": [], "proposals": {}}


def question_keys(questionnaire: str) -> list[str]:
    return [q["key"] for r in QUESTIONNAIRES[questionnaire]["rounds"] for q in r["questions"]]


def apply_patch(brief: dict, patch: dict, actor: str = "", at: str | None = None) -> tuple[dict, list[dict]]:
    """The brief after `patch`, and one event per change. Raises BriefConflict on an old rev or a locked field.

    patch: {rev, set: {key: value | None}, suggest: {key: value}, lock: [keys], unlock: [keys], meta: {..},
            package, questionnaire, parent_sop, annexes: [{title_en, title_mk, kind}], status,
            proposals: {key: {options: [{value, why, source}], pick}}}  (the advisor's, kept beside the fields)"""
    if brief["status"] != "open" and patch.get("status") != "open":
        raise BriefConflict(f"the brief is {brief['status']}; reopen it to change it")
    if patch.get("rev") != brief["rev"]:
        raise BriefConflict(f"the brief changed since rev {patch.get('rev')}; it is at rev {brief['rev']}")
    b, at = copy.deepcopy(brief), at or now()
    events: list[dict] = []

    def ev(op: str, key: str, before, after) -> None:
        events.append({"op": op, "key": key, "before": before, "after": after, "at": at, "actor": actor})

    for key in patch.get("unlock") or []:
        f = b["fields"].get(key)
        if f and f["state"] == "locked":
            f["state"] = "chosen"
            ev("unlock", key, "locked", "chosen")
    core_changed, changed = False, []
    for key, value in (patch.get("set") or {}).items():
        f = b["fields"].get(key)
        if f and f["state"] == "locked":
            raise BriefConflict(f"{key} is locked; unlock it first")
        before = f["value"] if f else None
        if value in (None, "", []):
            if f:
                del b["fields"][key]
                ev("clear", key, before, None)
                core_changed |= key in CORE
                changed.append(key)
            continue
        if f and f["value"] == value and f["state"] == "chosen" and not f.get("stale"):
            continue
        b["fields"][key] = {"value": value, "state": "chosen", "stale": False, "at": at, "by": actor}
        ev("set", key, before, value)
        core_changed |= key in CORE and before != value
        if before != value:
            changed.append(key)
    for key, value in (patch.get("suggest") or {}).items():
        f = b["fields"].get(key)
        if f and f["state"] != "suggested":
            continue                      # a decided field is never overwritten by a suggestion
        b["fields"][key] = {"value": value, "state": "suggested", "stale": False, "at": at, "by": actor or "agent"}
        ev("suggest", key, f["value"] if f else None, value)
    for key in patch.get("lock") or []:
        f = b["fields"].get(key)
        if not f:
            raise BriefError(f"{key} has no value to lock")
        if f["state"] != "locked":
            ev("lock", key, f["state"], "locked")
            f.update(state="locked", stale=False)
    # A decided answer rests on what was decided before it: a change to purpose, scope or use touches every one, a
    # change to an answer touches the answers that depend on it (question_rules.DEPENDS). Locked ones are never touched.
    from .question_rules import dependents
    just_set = set(patch.get("set") or {})
    touched = {k for k in b["fields"] if k not in CORE} if core_changed else set()
    for k in changed:
        touched |= set(dependents(b["questionnaire"], k))
    for key in sorted(touched - just_set):
        f = b["fields"].get(key)
        if f and f["state"] == "chosen" and not f.get("stale"):
            f["stale"] = True
            ev("stale", key, False, True)
    for k, v in (patch.get("meta") or {}).items():
        if k not in META_KEYS:
            raise BriefError(f"meta.{k} is not a brief field")
        if b["meta"].get(k, "") != (v or ""):
            ev("meta", k, b["meta"].get(k, ""), v or "")
            b["meta"][k] = v or ""
    for k in ("package", "questionnaire", "parent_sop", "status"):
        if k in patch and patch[k] != b.get(k):
            if k == "package" and patch[k] not in PACKAGES:
                raise BriefError(f"package must be one of {', '.join(PACKAGES)}")
            if k == "questionnaire" and patch[k] not in QUESTIONNAIRES:
                raise BriefError("unknown questionnaire")
            ev(k, k, b.get(k), patch[k])
            b[k] = patch[k]
    if "annexes" in patch:
        annexes = [{"title_en": (a.get("title_en") or "").strip(), "title_mk": (a.get("title_mk") or "").strip(),
                    "kind": a.get("kind") or "form"} for a in patch["annexes"] or []]
        if any(not (a["title_en"] or a["title_mk"]) for a in annexes):
            raise BriefError("every annex needs a title")
        if annexes != b["annexes"]:
            ev("annexes", "annexes", b["annexes"], annexes)
            b["annexes"] = annexes
    for key, p in (patch.get("proposals") or {}).items():
        b.setdefault("proposals", {})
        if b["proposals"].get(key) != p:
            ev("propose", key, b["proposals"].get(key), p)
            b["proposals"][key] = p
    if events:
        b["rev"] += 1
    return b, events


def to_workflow(brief: dict, sources: list[dict]) -> dict:
    """The payload POST /workflows takes, from the brief as it stands, with `assumed` naming what was not decided."""
    q, f, meta = brief["questionnaire"], brief["fields"], dict(brief["meta"])
    assumed = []
    if not (meta.get("title_en") or meta.get("title_mk")):
        raise BriefError("give the document a title before building")
    for a, b_ in (("title_mk", "title_en"), ("title_en", "title_mk")):
        if not meta.get(a):
            meta[a] = meta[b_]
            assumed.append(f"{a} (copied from {b_})")
    answers = {k: f[k]["value"] for k in question_keys(q) if k in f}
    assumed += [k for k in question_keys(q) if k not in f] + [k for k in TEXT_FIELDS if k not in f and k != "doc.notes"]
    assumed += [f"{k} (suggested, not confirmed)" for k, v in f.items() if v["state"] == "suggested"]
    assumed += [f"{k} (stale: decided before the scope changed)" for k, v in f.items() if v.get("stale")]
    lines = ["DOCUMENT BRIEF (what the requester decided):"]
    for k in TEXT_FIELDS:
        if k in f:
            v = f[k]["value"]
            lines.append(f"{TEXT_LABEL[k]}: {', '.join(map(str, v)) if isinstance(v, list) else v}")
    if brief["package"] == "sop_annexes" and brief["annexes"]:
        lines.append("Annexes of this package: " + "; ".join(a["title_en"] or a["title_mk"] for a in brief["annexes"]))
    if assumed:
        lines += ["", "Not decided by the requester — fill these from the brief, the sources and house practice, and "
                      "name the assumption in the text: " + ", ".join(assumed)]
    texts, total = [], 0
    for s in sources:
        t = (s.get("text") or "")[:MAX_SOURCE_CHARS]
        if not t or total >= MAX_SOURCES_CHARS:
            continue
        t = t[:MAX_SOURCES_CHARS - total]
        total += len(t)
        texts.append({"name": s["name"], "text": t})
    return {"questionnaire": q, "answers": answers, "meta": {k: v for k, v in meta.items() if k in META_KEYS},
            "instructions": "\n".join(lines)[:12000], "sources": [s["name"] for s in sources][:40],
            "source_texts": texts, "parent_sop": brief.get("parent_sop") or "", "assumed": assumed,
            "brief_id": brief.get("id", ""), "brief_rev": brief["rev"],
            "package_annexes": brief["annexes"] if brief["package"] == "sop_annexes" else []}
