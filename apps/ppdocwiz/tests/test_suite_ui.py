"""The PP Suite frontend: how it is served, and that its composer matches wizard.py."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app as app_mod
import wizard

FIX = Path(__file__).resolve().parents[1] / "web" / "src" / "lib" / "fixtures"


@pytest.fixture
def client():
    return TestClient(app_mod.app)


def test_index_serves_suite_when_built(tmp_path, monkeypatch, client):
    (tmp_path / "index.html").write_text("<title>PP Suite</title>", encoding="utf-8")
    monkeypatch.setattr(app_mod, "SUITE_UI", str(tmp_path))
    assert "PP Suite" in client.get("/").text


def test_index_falls_back_to_legacy_without_a_build(tmp_path, monkeypatch, client):
    monkeypatch.setattr(app_mod, "SUITE_UI", str(tmp_path / "absent"))
    assert client.get("/").text == client.get("/legacy").text


def test_legacy_switch(tmp_path, monkeypatch, client):
    (tmp_path / "index.html").write_text("<title>PP Suite</title>", encoding="utf-8")
    monkeypatch.setattr(app_mod, "SUITE_UI", str(tmp_path))
    monkeypatch.setenv("PPDOCWIZ_UI", "legacy")
    assert "PP Suite" not in client.get("/").text


@pytest.mark.parametrize("status,fixture", [("approved", "payload.md"), ("draft", "payload_draft.md")])
def test_browser_composer_fixtures_match_wizard(status, fixture):
    """web/src/lib/compose.test.ts asserts the TypeScript composer reproduces these
    files; this asserts they are what wizard.compose_markdown produces. Together they
    pin the live page in the browser to the Markdown the server builds."""
    p = json.loads((FIX / "payload.json").read_text(encoding="utf-8"))
    p["status"] = status
    assert wizard.compose_markdown(p) == (FIX / fixture).read_text(encoding="utf-8")


def test_lifecycle_dates_only_when_approved():
    p = {"code": "X", "status": "in_review", "effective_date": "01.01.2027", "sections": []}
    md = wizard.compose_markdown(p)
    assert "status: in_review" in md and "effective_date" not in md
    assert "status:" not in wizard.compose_markdown({"code": "X", "sections": []})
