# Revise a generated draft by instruction (Head of QC, 20.10.2026). Offline: the author clone is faked.
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import fleet, revise  # noqa: E402

MD = ("<!--HEADERDATA\nmk_title: Барање\nen_title: Request\ncode: QCT002\nversion: 03\ndoctype: FORM\norient: portrait\n-->\n"
      "# 1. ЦЕЛ | PURPOSE\nЦелта е барање за анализа на мостра од производство. ||| The purpose is a request for analysis.\n\n"
      "# 2. ПОДАТОЦИ | DATA\nПодатоци за мострата и серијата што се бара. ||| Data on the sample and the batch requested.\n")


class FakeLetta:
    def __init__(self, answer):
        self.answer, self.sent, self.deleted = answer, [], []

    async def send_message(self, agent_id, text):
        self.sent.append((agent_id, text))
        return self.answer

    async def delete_agent(self, agent_id):
        self.deleted.append(agent_id)


@pytest.fixture
def spawned(monkeypatch):
    names = []

    async def fake_spawn(client, agent_name, suffix):
        names.append(agent_name)
        return "tmp-" + suffix
    monkeypatch.setattr(fleet, "spawn_ephemeral", fake_spawn)
    return names


def test_a_form_splits_at_its_level_2_sections_with_the_title_first():
    form = ("<!--HEADERDATA\ncode: QCT002\ndoctype: FORM\n-->\n# БАРАЊЕ | REQUEST\nУвод. ||| Intro.\n\n"
            "## 1. Мостра | Sample\nа ||| b\n\n## 2. Анализа | Analysis\nв ||| c\n")
    head, secs = revise.split(form)
    assert [s.split("\n")[0] for s in secs] == ["# БАРАЊЕ | REQUEST", "## 1. Мостра | Sample", "## 2. Анализа | Analysis"]
    assert revise.join(head, secs) == form
    assert revise.titles(form)[1] == "1. Мостра | Sample"


def test_split_and_join_keep_the_header_and_every_section():
    head, secs = revise.split(MD)
    assert head.startswith("<!--HEADERDATA") and head.rstrip().endswith("-->")
    assert [s.split("\n")[0] for s in secs] == ["# 1. ЦЕЛ | PURPOSE", "# 2. ПОДАТОЦИ | DATA"]
    assert revise.join(head, secs) == MD
    assert revise.titles(MD) == ["1. ЦЕЛ | PURPOSE", "2. ПОДАТОЦИ | DATA"]


@pytest.mark.asyncio
async def test_one_section_is_revised_and_the_rest_left_word_for_word(spawned):
    new = ("Податоци за мострата, серијата и количината што се бара. ||| Data on the sample, the batch and the quantity "
           "requested.")
    fake = FakeLetta("Here is the revised section:\n```\n" + new + "\n```")
    out = await revise.revise(MD, "add the quantity", 1, "FORM", client=fake)
    assert spawned == ["gf_annex_author"] and fake.deleted == ["tmp-rev"]
    assert "add the quantity" in fake.sent[0][1] and "HEADERDATA" not in fake.sent[0][1]
    head, secs = revise.split(out["markdown"])
    assert head == revise.split(MD)[0]                       # the header never changes
    assert secs[0] == revise.split(MD)[1][0]                 # the other section is untouched
    assert secs[1] == "# 2. ПОДАТОЦИ | DATA\n" + new         # the heading is kept though the author dropped it
    assert out["gaps"] == [] and out["title"] == "2. ПОДАТОЦИ | DATA"


@pytest.mark.asyncio
async def test_a_one_language_answer_is_reported(spawned):
    fake = FakeLetta("# 2. ПОДАТОЦИ | DATA\nData on the sample, the batch, the quantity and the requester of the test "
                     "and the reason for the request in English only, with the storage condition, the laboratory and the "
                     "date by which the result is needed.")
    out = await revise.revise(MD, "rewrite", 1, "FORM", client=fake)
    assert out["gaps"] == ["2 (no MK)"]


@pytest.mark.asyncio
async def test_the_whole_body_goes_to_the_sop_author(spawned):
    body = "\n\n".join(revise.split(MD)[1]).replace("анализа", "испитување")
    out = await revise.revise(MD, "use испитување", None, "SOP", client=FakeLetta(body))
    assert spawned == ["gf_sop_author"] and "испитување" in out["markdown"]
    assert out["markdown"].startswith("<!--HEADERDATA") and len(revise.split(out["markdown"])[1]) == 2


@pytest.mark.asyncio
async def test_bad_requests_are_refused(spawned):
    with pytest.raises(ValueError):
        await revise.revise(MD, "  ", 0, "FORM", client=FakeLetta("x"))
    with pytest.raises(ValueError):
        await revise.revise(MD, "do it", 5, "FORM", client=FakeLetta("x"))
