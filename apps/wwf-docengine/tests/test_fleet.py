# Fleet unit surface: model-handle resolution is pure and worth pinning
# (the create/attach/delete round-trips are exercised on the wwf_mass stack,
# same convention as test_pipeline.py).
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.fleet import _resolve_model, load_fleet  # noqa: E402


def test_resolve_model_falls_back_to_yaml_defaults_when_no_agents_exist():
    spec = load_fleet()
    model, embedding = _resolve_model(spec, [])
    assert model == spec["defaults"]["model"]
    assert embedding == spec["defaults"]["embedding"]


def test_resolve_model_adopts_an_existing_agent_handle_over_the_yaml_default():
    spec = {"defaults": {"model": "yaml/default-model", "embedding": "yaml/default-embed"}}
    existing = [
        {"llm_config": {}, "embedding_config": {}},  # no handle — skipped
        {"llm_config": {"handle": "deepseek/deepseek-chat"},
         "embedding_config": {"handle": "letta/letta-free"}},
        {"llm_config": {"handle": "should-never-be-picked"}},
    ]
    model, embedding = _resolve_model(spec, existing)
    assert model == "deepseek/deepseek-chat"
    assert embedding == "letta/letta-free"


def test_reg_checker_is_declared_with_its_regulatory_sources():
    spec = load_fleet()
    ag = next(a for a in spec["agents"] if a["name"] == "gf_reg_checker")
    assert "DB1_REGULATORY" in ag["sources"]


def test_every_agent_clone_carries_the_house_glossary():
    import inspect
    from app import fleet, glossary
    text = glossary.memory_text()
    assert "термо-ќебе" in text and "меѓупроизвод (ринфуз)" in text and "Министерство за здравство (МЗ)" in text
    assert len(text) < fleet.GLOSSARY_LIMIT
    for fn in (fleet.ensure_fleet, fleet.spawn_ephemeral):
        assert '"gf_glossary_mk"' in inspect.getsource(fn)
    for t in glossary.load()["terms"]:          # a listed term is never flagged by its own lint
        assert glossary.term_issues(t["mk"]) == [], t["en"]


# ---- review 14.10.2026: orphaned ephemeral clones are swept ----

def test_stale_clones_are_old_tmp_agents_only():
    from datetime import datetime, timezone
    from app.fleet import _stale_clones
    now = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)
    agents = [
        {"id": "1", "name": "gf_sop_author_tmp_7abd699c_r1_70", "created_at": "2026-10-11T06:04:50.320811Z"},
        {"id": "2", "name": "gf_sop_author_tmp_1234abcd_60", "created_at": "2026-10-14T11:30:00Z"},  # a live job's
        {"id": "3", "name": "gf_sop_author", "created_at": "2026-01-01T00:00:00Z"},                  # the fleet itself
        {"id": "4", "name": "wwf_coordinator_tmp_x", "created_at": "2026-01-01T00:00:00Z"},          # not ours
        {"id": "5", "name": "gf_qa_auditor_tmp_x", "created_at": None},                              # no readable age
    ]
    assert [a["id"] for a in _stale_clones(agents, now)] == ["1"]


def test_ensure_fleet_sweeps_orphans_and_never_the_fleet():
    import asyncio
    from app import fleet

    spec = fleet.load_fleet()
    existing = [{"id": f"id-{a['name']}", "name": a["name"], "created_at": "2026-01-01T00:00:00Z"}
                for a in spec["agents"]]
    existing.append({"id": "orphan", "name": "gf_sop_author_tmp_7abd699c_r1_70", "created_at": "2026-10-11T06:04:50Z"})

    class Client:
        deleted: list = []

        async def list_agents(self):
            return existing

        async def list_sources(self):
            return []

        async def delete_agent(self, aid):
            self.deleted.append(aid)

        async def create_agent(self, spec):  # pragma: no cover — every fleet agent exists
            raise AssertionError("must not create")

    c = Client()
    out = asyncio.run(fleet.ensure_fleet(c))
    assert c.deleted == ["orphan"]
    assert set(out) == {a["name"] for a in spec["agents"]}


def test_list_agents_asks_for_every_agent():
    import asyncio
    from app.letta import LettaClient
    seen = {}

    class C(LettaClient):
        async def _req(self, method, path, **kw):
            seen.update(kw)
            return []

    asyncio.run(C(base="http://x", key="k").list_agents())
    assert seen["params"]["limit"] >= 1000


def test_letta_transport_errors_are_letta_errors():
    """A timeout between create and attach escaped spawn_ephemeral's `except LettaError` and lost the clone."""
    import asyncio
    import httpx
    import pytest
    from app.letta import LettaClient, LettaError

    class C(LettaClient):
        def _client(self):
            return httpx.AsyncClient(base_url="http://x/v1", transport=httpx.MockTransport(self._boom))

        @staticmethod
        def _boom(req):
            raise httpx.ReadTimeout("slow", request=req)

    with pytest.raises(LettaError, match="ReadTimeout"):
        asyncio.run(C(base="http://x", key="k").list_sources())
