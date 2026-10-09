# RAGFlow link: the client's request and parsing, the /knowledge routes, and the pipeline's
# regulatory check citing retrieved DB01 passages (with a fallback when RAGFlow is down).
import json
import sys
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import builder, ragflow  # noqa: E402
from app.config import settings  # noqa: E402
from app.pipeline import run_workflow  # noqa: E402
from app.ragflow import RagflowClient, RagflowError, citations, format_passages  # noqa: E402

# Shape of a real DB01_REG chunk (retrieved from the KVM4 instance, 09.10.2026), trimmed.
CHUNK = {
    "content": "9.2. Transportation\nThe required storage conditions for medicinal products should be maintained during transportation.",
    "dataset_id": "a33b0812a3d411f1858cf58865604f65", "dataset_name": "DB01_REG",
    "document_id": "0a02543ca3db11f1858cf58865604f65",
    "document_keyword": "DB1_REGULATORY/EudraLex/Annexes/CELEX_52013XC1123(01)_EN_TXT.pdf",
    "document_name": "DB1_REGULATORY/EudraLex/Annexes/CELEX_52013XC1123(01)_EN_TXT.pdf",
    "id": "69f492590cc8d5b3", "positions": [[10, 125, 208, 737, 750]], "similarity": 0.3605679,
}


def _transport(seen, payload=None, status=200):
    def handler(request: httpx.Request):
        seen.append(request)
        return httpx.Response(status, json=payload if payload is not None else {"code": 0, "data": {"chunks": [CHUNK]}})
    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_retrieve_request_and_parsing():
    seen = []
    rag = RagflowClient("http://ragflow:9380", "k-test", transport=_transport(seen))
    out = await rag.retrieve("transport temperature", ["ds1"], top_n=4)
    req = seen[0]
    assert req.url.path == "/api/v1/retrieval" and req.headers["authorization"] == "Bearer k-test"
    body = json.loads(req.content)
    assert body["dataset_ids"] == ["ds1"] and body["page_size"] == 4 and body["question"] == "transport temperature"
    assert out == [{"text": CHUNK["content"], "document": CHUNK["document_name"], "dataset": "DB01_REG",
                    "page": 10, "similarity": 0.361, "chunk_id": "69f492590cc8d5b3"}]


@pytest.mark.asyncio
@pytest.mark.parametrize("payload,status", [({"code": 102, "message": "bad key"}, 200), ({"x": 1}, 500)])
async def test_retrieve_errors_raise(payload, status):
    rag = RagflowClient("http://ragflow:9380", "k", transport=_transport([], payload, status))
    with pytest.raises(RagflowError):
        await rag.retrieve("q", ["ds1"])


@pytest.mark.asyncio
async def test_unconfigured_raises():
    with pytest.raises(RagflowError):
        await RagflowClient("", "").retrieve("q", ["ds1"])


def test_format_and_citations():
    p = [{"text": "abc", "document": "Annex 15", "page": 9, "similarity": 0.5, "chunk_id": "c1"}]
    assert format_passages(p) == "[R1] Annex 15, p. 9\nabc"
    assert citations(p) == [{"ref": "R1", "document": "Annex 15", "page": 9, "chunk_id": "c1", "similarity": 0.5}]


# ---- /knowledge routes -------------------------------------------------------------------
@pytest.fixture
def api(monkeypatch):
    from app import main
    monkeypatch.setattr(settings, "api_key", "t")
    return TestClient(main.app), {"X-API-Key": "t"}


def test_knowledge_search(api, monkeypatch):
    client, h = api
    async def fake(self, q, ids, top_n=None, keyword=False, threshold=0.2):
        assert ids == settings.ragflow_ecoa_datasets and keyword
        return [{"text": "t", "document": "IJZ 1065/2026", "dataset": "eCOA_DB", "page": 1, "similarity": 0.9, "chunk_id": "x"}]
    monkeypatch.setattr(RagflowClient, "retrieve", fake)
    r = client.post("/knowledge/search", json={"corpus": "ecoa", "question": "SJ102501", "keyword": True}, headers=h)
    assert r.status_code == 200 and r.json()["passages"][0]["document"] == "IJZ 1065/2026"
    assert "not a source of values" in r.json()["note"]


def test_knowledge_search_rejects(api, monkeypatch):
    client, h = api
    assert client.post("/knowledge/search", json={"corpus": "x", "question": "qq"}, headers=h).status_code == 404
    monkeypatch.setattr(settings, "ragflow_example_datasets", ())
    assert client.post("/knowledge/search", json={"corpus": "examples", "question": "qq"}, headers=h).status_code == 409
    assert client.post("/knowledge/search", json={"corpus": "regulatory", "question": "qq"}).status_code == 401


def test_knowledge_search_ragflow_down_is_503(api, monkeypatch):
    client, h = api
    async def down(self, *a, **k):
        raise RagflowError("RAGFlow unreachable")
    monkeypatch.setattr(RagflowClient, "retrieve", down)
    assert client.post("/knowledge/search", json={"corpus": "regulatory", "question": "qq"}, headers=h).status_code == 503


# ---- pipeline: the regulatory check cites retrieved passages ---------------------------------
from tests.test_pipeline import _fake_build_result, _patch_common  # noqa: E402


class RecordingClient:
    def __init__(self):
        self.prompts = []

    async def send_message(self, agent_id, prompt):
        self.prompts.append(prompt)
        if "§6A" in prompt:
            return "PASS"
        if prompt.startswith("Check this drafted section"):
            return "NO-FINDING"
        return "# 1 Пратка | Consignment\n[[FORM:grid]]\nДатум ||| Date ||| _\n[[/FORM]]"

    async def delete_agent(self, agent_id):
        pass


class FakeRag:
    configured = True

    def __init__(self, fail=False):
        self.fail, self.calls = fail, []

    async def retrieve(self, q, ids, top_n=None, keyword=False, threshold=0.2):
        self.calls.append((q, tuple(ids)))
        if self.fail:
            raise RagflowError("RAGFlow unreachable")
        return [{"text": "Storage conditions maintained during transport.", "document": "EU GDP 2013/C 343/01",
                 "page": 10, "similarity": 0.36, "chunk_id": "69f4"}]


@pytest.mark.asyncio
async def test_reg_check_uses_ragflow_passages(monkeypatch):
    updates = _patch_common(monkeypatch)
    monkeypatch.setattr(builder, "build", lambda *a, **k: _fake_build_result())
    c, rag = RecordingClient(), FakeRag()
    await run_workflow("job-1", client=c, rag=rag)
    check = [p for p in c.prompts if p.startswith("Check this drafted section")][0]
    assert "RAGFlow DB01" in check and "[R1] EU GDP 2013/C 343/01, p. 10" in check
    assert rag.calls[0][1] == settings.ragflow_reg_datasets
    done = updates[-1]
    assert done["status"] == "done"
    assert done["result"]["regulatory_sources"]["1.0"][0]["chunk_id"] == "69f4"
    assert done["result"]["knowledge"]["ragflow"] is True


@pytest.mark.asyncio
async def test_reg_check_falls_back_to_letta_sources_and_says_so(monkeypatch):
    updates = _patch_common(monkeypatch)
    monkeypatch.setattr(builder, "build", lambda *a, **k: _fake_build_result())
    c = RecordingClient()
    await run_workflow("job-1", client=c, rag=FakeRag(fail=True))
    check = [p for p in c.prompts if p.startswith("Check this drafted section")][0]
    assert "regulatory corpus (" in check and "[R1]" not in check
    notes = updates[-1]["result"]["knowledge"]["notes"]
    assert notes and "Letta sources used" in notes[0]


@pytest.mark.asyncio
async def test_examples_reach_the_author_only_when_configured(monkeypatch):
    _patch_common(monkeypatch)
    monkeypatch.setattr(builder, "build", lambda *a, **k: _fake_build_result())
    monkeypatch.setattr(settings, "ragflow_example_datasets", ("ex1",))
    c = RecordingClient()
    await run_workflow("job-1", client=c, rag=FakeRag())
    author = [p for p in c.prompts if p.startswith("Design the")][0]
    assert "Never copy a value" in author and "[E1]" in author
