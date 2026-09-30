# docengine_studio.app.router - lane routing + model routing helpers.
# The lane router is the enforcement point for the dual-RAG architecture:
# official intents resolve through RAGFlow and FAIL CLOSED; advisory intents may
# use Letta. There is never a silent cross-lane fallback.
from __future__ import annotations

import json

from . import db

OFFICIAL_INTENTS = {"official_evidence", "coa_lookup"}


def resolve_lane(intent: str) -> dict:
    with db.tx() as conn:
        row = conn.execute("SELECT * FROM lane_router WHERE intent=?", (intent,)).fetchone()
    if not row:
        # Unknown intents are treated as advisory but still recorded.
        return {"intent": intent, "lane": "letta", "fail_closed": 0, "known": False}
    return {
        "intent": intent,
        "lane": row["lane"],
        "fail_closed": bool(row["fail_closed"]),
        "rationale": row["rationale"],
        "known": True,
    }


def all_lane_routes() -> list[dict]:
    with db.tx() as conn:
        rows = conn.execute("SELECT * FROM lane_router ORDER BY intent").fetchall()
    out = [dict(r) for r in rows]
    for d in out:
        d["fail_closed"] = bool(d["fail_closed"])
    return out


def set_lane_route(intent: str, lane: str, fail_closed: bool, rationale: str | None, actor: str) -> dict:
    if lane not in ("ragflow", "letta"):
        raise ValueError("lane must be ragflow or letta")
    if intent in OFFICIAL_INTENTS and (lane != "ragflow" or not fail_closed):
        raise ValueError("official intent %s must stay on the ragflow lane with fail_closed" % intent)
    with db.tx() as conn:
        conn.execute(
            "INSERT INTO lane_router(intent,lane,fail_closed,rationale) VALUES (?,?,?,?) "
            "ON CONFLICT(intent) DO UPDATE SET lane=excluded.lane,fail_closed=excluded.fail_closed,rationale=excluded.rationale",
            (intent, lane, 1 if fail_closed else 0, rationale),
        )
    db.audit("lane_router.updated", actor=actor, subject=intent, payload={"lane": lane, "fail_closed": fail_closed})
    return resolve_lane(intent)


def model_route(fn: str) -> dict:
    with db.tx() as conn:
        row = conn.execute("SELECT * FROM model_routing WHERE fn=?", (fn,)).fetchone()
    if not row:
        return {"fn": fn, "known": False, "provider": None, "model": None, "temperature": 0.0}
    d = dict(row)
    d["known"] = True
    return d


def all_model_routes() -> list[dict]:
    with db.tx() as conn:
        rows = conn.execute("SELECT * FROM model_routing ORDER BY fn").fetchall()
    return [dict(r) for r in rows]


def set_model_route(fn: str, provider: str, model: str, temperature: float, rationale: str | None, actor: str) -> dict:
    if provider not in ("moonshot", "deepseek"):
        raise ValueError("provider must be moonshot or deepseek")
    # Producer/checker separation: a checker function may not run a producer model.
    checker_prefixes = ("regulatory", "qa_", "verification", "intent_", "orchestration", "raci_", "record_")
    if fn.startswith(checker_prefixes) and provider == "moonshot":
        raise ValueError("checker functions must run on the checker provider (deepseek)")
    temp = 0.0 if fn.startswith(checker_prefixes) else float(temperature)
    with db.tx() as conn:
        conn.execute(
            "INSERT INTO model_routing(fn,provider,model,temperature,rationale) VALUES (?,?,?,?,?) "
            "ON CONFLICT(fn) DO UPDATE SET provider=excluded.provider,model=excluded.model,"
            "temperature=excluded.temperature,rationale=excluded.rationale",
            (fn, provider, model, temp, rationale),
        )
    db.audit("model_routing.updated", actor=actor, subject=fn, payload={"provider": provider, "model": model, "temperature": temp})
    return model_route(fn)
