"""LettaClient retries (review 14.10.2026): one network blip on any of ~30 agent calls failed the whole job."""
import asyncio
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402
from app.letta import LettaClient, LettaError  # noqa: E402


def client(handler, monkeypatch):
    monkeypatch.setattr(settings, "letta_retries", 2)
    monkeypatch.setattr(settings, "letta_retry_base", 0.0)

    class C(LettaClient):
        async def _sleep(self, s):  # noqa: D401 - no real waiting
            return None

        def _client(self):
            return httpx.AsyncClient(base_url="http://x/v1", transport=httpx.MockTransport(handler))

    return C(base="http://x", key="k")


def test_a_gateway_error_on_a_read_is_retried(monkeypatch):
    calls = []

    def h(req):
        calls.append(req)
        return httpx.Response(503 if len(calls) < 3 else 200, json=[{"id": "s1"}])

    assert asyncio.run(client(h, monkeypatch).list_sources()) == [{"id": "s1"}]
    assert len(calls) == 3


def test_a_message_that_timed_out_is_not_resent_but_marked_transient(monkeypatch):
    calls = []

    def h(req):
        calls.append(req)
        raise httpx.ReadTimeout("slow", request=req)

    with pytest.raises(LettaError) as e:
        asyncio.run(client(h, monkeypatch).send_message("a1", "hi"))
    assert e.value.transient and len(calls) == 1          # the agent may still be writing: never sent twice


def test_a_refused_message_is_resent(monkeypatch):
    calls = []

    def h(req):
        calls.append(req)
        if len(calls) == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, json={"detail": "slow down"})
        return httpx.Response(200, json={"messages": [{"message_type": "assistant_message", "content": "ok"}]})

    assert asyncio.run(client(h, monkeypatch).send_message("a1", "hi")) == "ok"
    assert len(calls) == 2


def test_a_client_error_is_not_retried(monkeypatch):
    calls = []

    def h(req):
        calls.append(req)
        return httpx.Response(422, json={"detail": "bad"})

    with pytest.raises(LettaError) as e:
        asyncio.run(client(h, monkeypatch).list_sources())
    assert not e.value.transient and len(calls) == 1


def test_deleting_an_agent_that_is_already_gone_is_success(monkeypatch):
    asyncio.run(client(lambda req: httpx.Response(404, json={}), monkeypatch).delete_agent("gone"))


def test_a_create_that_broke_midway_is_found_not_duplicated(monkeypatch):
    posts = []

    def h(req):
        if req.method == "POST":
            posts.append(req)
            raise httpx.ReadTimeout("slow", request=req)
        return httpx.Response(200, json=[{"id": "made", "name": "gf_x_tmp_1"}])

    got = asyncio.run(client(h, monkeypatch).create_agent({"name": "gf_x_tmp_1"}))
    assert got["id"] == "made" and len(posts) == 1
