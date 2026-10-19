# docengine.app.fleet — ensure-loop for the gf_* agent fleet.
#
# Declarative (agents/fleet.yaml) -> live Letta agents, ADDITIVELY:
#   * create-by-name if missing (never edit an existing agent — the server
#     rejects config writes for the legacy provider enum anyway);
#   * attach the named sources (PQ1 excluded by omission);
#   * seed a `gf_house_rules` core memory block from the canon text.
# Model/embedding handles are taken from what the server actually serves
# (first existing agent's config wins over the YAML default), because the
# handover documented that invented handles are rejected.
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from . import glossary
from .letta import LettaClient, LettaError

log = logging.getLogger("docengine.fleet")
FLEET_FILE = Path(__file__).resolve().parents[1] / "agents" / "fleet.yaml"
# Explicit block limit: the glossary is about 2.5k characters, and a server default could truncate it.
GLOSSARY_LIMIT = 8000
# Ephemeral clones (spawn_ephemeral) are deleted after their one exchange; a failed delete leaves one behind.
# Pipeline comments promised that "the next fleet audit sweeps _tmp_ leftovers" — no such sweep existed, and
# gf_sop_author_tmp_7abd699c_r1_70 was still on the server three days later (review 14.10.2026). ensure_fleet
# now sweeps clones older than this. One exchange is bounded by the Letta read timeout (minutes), so a clone
# this old belongs to no live job.
TMP_AGENT = re.compile(r"^gf_[a-z0-9_]+_tmp_")
TMP_MAX_AGE = timedelta(hours=6)


def _stale_clones(agents: list[dict], now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    out = []
    for a in agents:
        if not TMP_AGENT.match(a.get("name") or ""):
            continue
        try:
            created = datetime.fromisoformat(str(a.get("created_at")).replace("Z", "+00:00"))
        except ValueError:
            continue  # no readable age: leave it alone
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if now - created > TMP_MAX_AGE:
            out.append(a)
    return out


def load_fleet() -> dict:
    return yaml.safe_load(FLEET_FILE.read_text(encoding="utf-8"))


def _resolve_model(spec: dict, existing: list[dict]) -> tuple[str, str]:
    """Adopt a model/embedding handle the server demonstrably accepts: prefer
    any existing agent's llm_config over the YAML default (invented handles
    are rejected by this server, per the handover)."""
    model = spec["defaults"]["model"]
    embedding = spec["defaults"]["embedding"]
    for a in existing:
        lc = a.get("llm_config") or {}
        if lc.get("handle") or lc.get("model"):
            model = lc.get("handle") or lc.get("model")
            ec = a.get("embedding_config") or {}
            cand = ec.get("handle") or ec.get("embedding_model") or ""
            # Adopt only a real provider/model handle. Agents imported or
            # mirrored from another instance carry a bare embedding model name
            # ("text-embedding-3-small"), which POST /agents rejects as an
            # embedding handle — a bare name must not displace the YAML default.
            if "/" in cand:
                embedding = cand
            break
    return model, embedding


async def ensure_fleet(client: LettaClient | None = None) -> dict:
    """Idempotent. Returns {agent_name: agent_id} for the whole gf_ fleet."""
    client = client or LettaClient()
    spec = load_fleet()
    house_rules = spec["house_rules"].strip()
    listed = await client.list_agents()
    stale = _stale_clones(listed)
    for a in stale:
        try:
            await client.delete_agent(a["id"])
            log.info("swept orphaned clone %s", a.get("name"))
        except Exception as e:  # noqa: BLE001 — a leftover clone is harmless; the fleet must still come up
            log.warning("could not sweep orphaned clone %s: %s", a.get("name"), e)
    swept = {a.get("id") for a in stale}
    listed = [a for a in listed if a.get("id") not in swept]
    existing = {a.get("name"): a for a in listed}
    sources = {s.get("name"): s.get("id") for s in await client.list_sources()}
    model, embedding = _resolve_model(spec, list(existing.values()))

    out: dict[str, str] = {}
    glossary_text = glossary.memory_text()
    for ag in spec["agents"]:
        name = ag["name"]
        if name in existing:
            out[name] = existing[name]["id"]
            # The glossary is seeded at creation; a ruling that changes it (мострирање, 19.10.2026) reached no
            # existing agent until this refresh — the clones copy their memory from these base agents.
            try:
                held = (await client.get_block(existing[name]["id"], "gf_glossary_mk")).get("value", "")
                if held != glossary_text:
                    await client.update_block(existing[name]["id"], "gf_glossary_mk", glossary_text)
                    log.info("refreshed gf_glossary_mk on %s", name)
            except Exception as e:  # noqa: BLE001 — the linter still holds the glossary; the fleet must come up
                log.warning("could not refresh the glossary on %s: %s", name, e)
            continue
        body = {
            "name": name,
            "description": ag.get("description", ""),
            "model": model,
            "embedding": embedding,
            "memory_blocks": [
                {"label": "gf_house_rules", "value": house_rules},
                {"label": "persona", "value": ag["persona"].strip()},
                {"label": "gf_glossary_mk", "value": glossary.memory_text(), "limit": GLOSSARY_LIMIT},
            ],
        }
        created = await client.create_agent(body)
        out[name] = created["id"]
        log.info("created agent %s -> %s", name, created["id"])
        for src_name in ag.get("sources", []):
            sid = sources.get(src_name)
            if not sid:
                log.warning("source %s not found for %s", src_name, name)
                continue
            try:
                await client.attach_source(created["id"], sid)
            except LettaError as e:  # non-fatal: agent works, RAG degraded
                log.warning("attach %s -> %s failed: %s", src_name, name, e)
    return out


async def spawn_ephemeral(client: LettaClient, agent_name: str, name_suffix: str) -> str:
    """Create a short-lived clone of a fleet agent (same persona/sources/
    model) for exactly ONE isolated exchange, then the caller deletes it.

    Exists because a persistent Letta agent accumulates every past message
    into the prompt sent on each new turn — fine for a single Q&A agent, but
    fatal for a loop that sends N independent checks against the same agent
    (each turn's system-prompt token estimate keeps growing until it exceeds
    the model's context window; observed live at section 9 of 9 on a fresh
    gf_reg_checker). A fresh clone per exchange keeps that estimate constant
    regardless of how many checks the pipeline runs."""
    spec = load_fleet()
    house_rules = spec["house_rules"].strip()
    ag = next(a for a in spec["agents"] if a["name"] == agent_name)
    existing = await client.list_agents()
    sources = {s.get("name"): s.get("id") for s in await client.list_sources()}
    model, embedding = _resolve_model(spec, existing)
    # The clone must run the SAME model as the agent it clones ("same persona/
    # sources/model") — the global adoption above picks whatever agent happens
    # to list first, which on a mixed instance (fleet + mirrored planners) can
    # be a different provider whose tool-loop behavior differs from the base
    # agent's proven config.
    base = next((a for a in existing if a.get("name") == agent_name), None)
    if base:
        lc = base.get("llm_config") or {}
        if lc.get("handle") or lc.get("model"):
            model = lc.get("handle") or lc.get("model")
        cand = (base.get("embedding_config") or {}).get("handle") or ""
        if "/" in cand:
            embedding = cand

    body = {
        "name": f"{agent_name}_tmp_{name_suffix}",
        "description": f"ephemeral clone of {agent_name} for one isolated exchange",
        "model": model,
        "embedding": embedding,
        "memory_blocks": [
            {"label": "gf_house_rules", "value": house_rules},
            {"label": "persona", "value": ag["persona"].strip()},
            {"label": "gf_glossary_mk", "value": glossary.memory_text(), "limit": GLOSSARY_LIMIT},
        ],
    }
    created = await client.create_agent(body)
    for src_name in ag.get("sources", []):
        sid = sources.get(src_name)
        if not sid:
            log.warning("source %s not found for ephemeral %s", src_name, body["name"])
            continue
        try:
            await client.attach_source(created["id"], sid)
        except LettaError as e:  # non-fatal: this one exchange loses RAG, not the whole job
            log.warning("attach %s -> %s failed: %s", src_name, body["name"], e)
    return created["id"]
