"""The official potency specifications (KVM4 potency builder) reach the authors and the advisor as served."""
import asyncio
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import advisor, potency  # noqa: E402
from app.config import settings  # noqa: E402

SPECS = {"specs": [
    {"id": "WED", "name": "Wedding Cake", "status": "finished",
     "ranges": [{"nominal": 22, "tol": 1.4, "lo": 20.6, "hi": 23.39}, {"nominal": 26, "tol": 2.6, "lo": 23.4, "hi": 28.59}]},
    {"id": "NEW", "name": "Draft strain", "status": "draft", "ranges": [{"nominal": 10, "tol": 1, "lo": 9, "hi": 10.99}]}]}


def _transport(calls, status=200):
    def handle(req):
        calls.append(str(req.url))
        return httpx.Response(status, json=SPECS)
    return httpx.MockTransport(handle)


def test_a_potency_document_gets_the_served_grades_and_nothing_else(monkeypatch):
    monkeypatch.setattr(settings, "potency_specs_url", "https://specs.example")
    calls = []
    text = asyncio.run(potency.block("Potency testing of dried flower", transport=_transport(calls)))
    assert calls == ["https://specs.example/api/specs"]
    assert "WED — Wedding Cake: Total THC 22.00 ± 1.40 % (20.60–23.39 %); 26.00 ± 2.60 % (23.40–28.59 %)" in text
    assert "Draft strain" not in text                         # only finished specifications
    assert "never write a grade numeral" in text and "pharmacopoeia" in text
    asyncio.run(potency.block("cannabinoid content", transport=_transport(calls)))
    assert len(calls) == 1                                    # cached
    assert asyncio.run(potency.block("Cleaning of the drying room", transport=_transport(calls))) == ""


def test_an_unreachable_service_means_no_grade_is_stated(monkeypatch):
    monkeypatch.setattr(settings, "potency_specs_url", "https://specs.example")
    text = asyncio.run(potency.block("THC specification", transport=_transport([], status=503)))
    assert "could not be read" in text and "per the strain's current potency specification" in text


def test_off_when_no_url_is_set():
    assert asyncio.run(potency.block("potency")) == ""


def test_the_advisor_reads_the_specifications_before_the_house_documents():
    b = {"meta": {"title_en": "Potency"}, "fields": {}, "package": "sop", "questionnaire": "sop_qc"}
    text = advisor.prompt(b, {"acceptance": {"label": "Acceptance", "multi": True, "options": []}}, "[E1] x", "",
                          [], "OFFICIAL POTENCY SPECIFICATIONS: WED …")
    assert text.index("OFFICIAL POTENCY SPECIFICATIONS") < text.index("APPROVED HOUSE DOCUMENTS")
    assert json.dumps(SPECS)  # fixture is valid JSON
