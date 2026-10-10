# Pipeline unit surface: questionnaire defaulting + Markdown assembly, plus
# run_workflow's error-path coverage (the Letta round-trips are otherwise
# exercised live on the wwf_mass stack, not here).
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import builder, db, fleet  # noqa: E402
from app.letta import LettaError  # noqa: E402
from app.pipeline import (  # noqa: E402
    assemble_markdown, run_workflow, _strip_fences, _clean_section, _bilingual_gaps,
    _qa_verdict, _lint_section, _strip_own_heading, _sections_named,
)
from app.questionnaires import apply_defaults  # noqa: E402


def test_apply_defaults_fills_compliant_options():
    out = apply_defaults("sop_qc", {"focus": "Potency"})
    assert out["focus"] == "Potency"                       # explicit answer kept
    assert out["method_source"] == "Ph. Eur. (preferred)"  # default filled
    assert out["review_chain"].startswith("Two-tier")
    # multi-select default
    assert "Doc ID (EU GMP 4.2)" in apply_defaults("annex_form", {})["id_fields"]


def test_assemble_markdown_headerdata_and_sections():
    md = assemble_markdown(
        {"title_mk": "МК", "title_en": "EN", "code": "C-1", "doctype": "SOP"},
        [{"num": "1.0", "mk": "ЦЕЛ", "en": "PURPOSE", "content": "Текст.|Text."}],
    )
    assert md.startswith("<!--HEADERDATA")
    assert "doctype: SOP" in md and "code: C-1" in md
    assert "# 1.0 ЦЕЛ|PURPOSE" in md and "Текст.|Text." in md


def test_assemble_markdown_rejects_embedded_comment_terminator():
    # B2: a meta field value containing '-->' would corrupt the HEADERDATA
    # block boundary downstream — reject at assembly time, don't ship it.
    with pytest.raises(ValueError):
        assemble_markdown(
            {"title_mk": "Опис --> на процедура", "title_en": "EN", "code": "C-1", "doctype": "SOP"},
            [{"num": "1.0", "mk": "ЦЕЛ", "en": "PURPOSE", "content": "Текст.|Text."}],
        )


def test_strip_fences():
    assert _strip_fences("```markdown\nhello\n```") == "hello"
    assert _strip_fences("plain") == "plain"


def test_clean_section_structured_drops_preamble_before_marker():
    # the exact failure observed on the live wwf_mass smoke
    raw = (
        "Looking at the persona description more carefully — it explicitly "
        "describes the structure of QCT-SMOKE-01 (my earlier work). Let me align "
        "to that specification precisely.\n\n"
        "# Барање | Material Transfer Request\n\n"
        "[[FORM:grid]]\nИме ~~ Name ||| _____\n[[FORM:grid]]"
    )
    out = _clean_section(raw, structured=True)
    assert out.startswith("# Барање | Material Transfer Request")
    assert "Looking at the persona" not in out
    assert "[[FORM:grid]]" in out


def test_clean_section_prose_peels_leading_commentary_only():
    raw = "Here is the section body:\n\nThe purpose of this SOP is to define X."
    out = _clean_section(raw, structured=False)
    assert out == "The purpose of this SOP is to define X."


def test_clean_section_keeps_legitimate_prose():
    # a real SOP prose body must never be eaten, even with no heading
    raw = "The purpose of this procedure is to describe the sampling of water."
    assert _clean_section(raw, structured=False) == raw
    # a body that is ALL commentary falls back to the original (never empty)
    only = "Let me think about this."
    assert _clean_section(only, structured=False) == only


# ── run_workflow error-path coverage ────────────────────────────────────────
# Every branch below drives run_workflow end-to-end with fakes for db/fleet/
# the Letta client, asserting on the job row run_workflow itself writes —
# run_workflow "never raises: every failure lands in the job row as
# status=failed" (its own docstring), and this is what pins that promise.
_AGENT_NAMES = ("gf_sop_author", "gf_raci_specialist", "gf_annex_author",
                "gf_reg_checker", "gf_qa_auditor")


def _job(qkey="annex_form"):
    return {
        "id": "job-1",
        "payload": {
            "questionnaire": qkey, "answers": {},
            "meta": {"title_mk": "МК наслов", "title_en": "EN title", "code": "C-1"},
        },
    }


class FakeClient:
    """Replies NO-FINDING to regulatory checks and PASS to the §6A audit by
    default; subclasses override send_message/delete_agent for specific
    failure modes."""

    async def send_message(self, agent_id, prompt):
        if "§6A" in prompt:
            return "PASS"
        return "NO-FINDING"

    async def delete_agent(self, agent_id):
        pass


def _patch_common(monkeypatch, qkey="annex_form"):
    updates = []

    async def fake_job_get(jid):
        return _job(qkey)

    async def fake_job_update(jid, **fields):
        updates.append(fields)

    async def fake_document_create(job_id, meta):
        return "doc-1"

    async def fake_ensure_fleet(client):
        return {name: f"agent-{name}" for name in _AGENT_NAMES}

    async def fake_spawn_ephemeral(client, agent_name, name_suffix):
        return f"tmp-{agent_name}-{name_suffix}"

    monkeypatch.setattr(db, "job_get", fake_job_get)
    monkeypatch.setattr(db, "job_update", fake_job_update)
    monkeypatch.setattr(db, "document_create", fake_document_create)
    monkeypatch.setattr(fleet, "ensure_fleet", fake_ensure_fleet)
    monkeypatch.setattr(fleet, "spawn_ephemeral", fake_spawn_ephemeral)
    return updates


def _fake_build_result():
    return builder.BuildResult(path=Path("/tmp/x.docx"), bytes=10,
                               verify_report="RESULT: PASS", doctype="SOP")


@pytest.mark.asyncio
async def test_verify_failed_records_failed_status(monkeypatch):
    updates = _patch_common(monkeypatch)
    monkeypatch.setattr(builder, "build",
                        lambda *a, **k: (_ for _ in ()).throw(builder.VerifyFailed("bad report")))
    await run_workflow("job-1", client=FakeClient())
    assert updates[-1]["status"] == "failed"
    assert updates[-1]["error"] == "verify FAILED"
    assert updates[-1]["result"]["verify"] == "bad report"


@pytest.mark.asyncio
async def test_letta_error_records_failed_status(monkeypatch):
    updates = _patch_common(monkeypatch)

    class FailingClient(FakeClient):
        async def send_message(self, agent_id, prompt):
            raise LettaError("letta down")

    await run_workflow("job-1", client=FailingClient())
    assert updates[-1]["status"] == "failed"
    assert updates[-1]["error"] == "letta: letta down"


@pytest.mark.asyncio
async def test_generic_exception_with_blank_str_still_records_a_useful_error(monkeypatch):
    # httpx.ReadTimeout and friends stringify to "" — the job's error must
    # never end up blank; it falls back to the exception's type name.
    updates = _patch_common(monkeypatch)

    class _Blank(Exception):
        def __str__(self):
            return ""

    class FailingClient(FakeClient):
        async def send_message(self, agent_id, prompt):
            raise _Blank()

    await run_workflow("job-1", client=FailingClient())
    assert updates[-1]["status"] == "failed"
    assert updates[-1]["error"].startswith("_Blank:")


@pytest.mark.asyncio
async def test_qa_audit_fix_verdict_blocks_the_build(monkeypatch):
    updates = _patch_common(monkeypatch)
    built = []
    monkeypatch.setattr(builder, "build", lambda *a, **k: built.append(1) or _fake_build_result())

    class FixClient(FakeClient):
        async def send_message(self, agent_id, prompt):
            if "§6A" in prompt:
                return "FIX: section 2.0 references the wrong regulation"
            return "NO-FINDING"

    await run_workflow("job-1", client=FixClient())
    assert not built, "builder.build must never run past a §6A FIX verdict"
    assert updates[-1]["status"] == "failed"
    assert updates[-1]["error"] == "§6A audit did not pass"
    assert updates[-1]["result"]["qa_audit"].startswith("FIX")


@pytest.mark.asyncio
async def test_qa_audit_pass_verdict_proceeds_to_build(monkeypatch):
    updates = _patch_common(monkeypatch)
    monkeypatch.setattr(builder, "build", lambda *a, **k: _fake_build_result())
    await run_workflow("job-1", client=FakeClient())
    assert updates[-1]["status"] == "done"


@pytest.mark.asyncio
async def test_ephemeral_regchecker_cleanup_failure_does_not_abort_the_job(monkeypatch):
    """The SOP path spawns + deletes a throwaway reg-checker per section; a
    failure deleting it (observed live: httpx transport errors) must not
    abort the whole job — it's logged and the job still completes."""
    updates = _patch_common(monkeypatch, qkey="sop_qc")
    monkeypatch.setattr(builder, "build", lambda *a, **k: _fake_build_result())

    class FlakyDeleteClient(FakeClient):
        async def delete_agent(self, agent_id):
            raise RuntimeError("delete failed")

    await run_workflow("job-1", client=FlakyDeleteClient())
    assert updates[-1]["status"] == "done"


def test_clean_section_keeps_sop_prose_openers():
    """M — the stripper used to match "note:", "based on", "the following",
    "this is the" and "below is" at the start of a line. Those open ordinary
    procedure text at least as often as agent chatter, and the strip is silent:
    the §5A fidelity check compares the built .docx against this ALREADY-CLEANED
    text, so anything lost here is invisible to the one safeguard meant to catch
    content impoverishment."""
    for raw in (
        "Note: samples must be stored at 2-8 °C until tested.",
        "Based on the risk assessment, sampling is performed per QCSOP-011.",
        "The following equipment is required for this procedure.",
        "This is the reference method for water conductivity.",
        "Below is the acceptance criteria table.",
    ):
        assert _clean_section(raw, structured=False) == raw, raw


def test_clean_section_refuses_an_oversized_strip():
    """M — a conversational lead-in is short. A large removal is the agent's
    real output, so the stripper keeps the original rather than being the thing
    that silently drops procedure text."""
    big = ("Let me explain. " + "This sentence is real procedure content. " * 40).strip()
    out = _clean_section(big, structured=False)
    assert out == big                      # refused, nothing lost
    # …while a genuinely short lead-in is still peeled
    small = "Let me explain.\n\nThe purpose of this SOP is to define X."
    assert _clean_section(small, structured=False) == "The purpose of this SOP is to define X."


# --- per-section bilingual gate -------------------------------------------
# M — pp_verify's --require-bilingual asks whether the WHOLE .docx contains
# Cyrillic and Latin ANYWHERE, so one Macedonian word in a forty-page English
# document passes it. Every realistic failure is per-section, which is where
# _bilingual_gaps looks.

_MK = ("Оваа постапка ја опишува постапката за земање, обележување и чување на "
       "примероци од секоја произведена серија до крајот на рокот на употреба.")
_EN = ("This procedure describes the sampling, labelling and retention of samples "
       "from every manufactured batch until the end of its shelf life.")


def test_bilingual_gaps_flags_a_monolingual_section():
    gaps = _bilingual_gaps([
        {"num": "1.0", "content": f"{_MK}|{_EN}"},
        {"num": "2.0", "content": _EN * 2},      # English only
        {"num": "3.0", "content": _MK * 2},      # Macedonian only
    ])
    assert gaps == ["2.0 (no MK)", "3.0 (no EN)"]


def test_bilingual_gaps_passes_a_document_that_is_bilingual_throughout():
    assert _bilingual_gaps([
        {"num": "1.0", "content": f"{_MK}|{_EN}"},
        {"num": "2.0", "content": f"{_MK}|{_EN}"},
    ]) == []


def test_bilingual_gaps_ignores_sections_with_too_little_text_to_judge():
    """A bare form marker, a formula or a short code reference is legitimately
    language-neutral. Failing those would make the gate unusable."""
    assert _bilingual_gaps([
        {"num": "4.0", "content": "[[FORM:grid]]"},
        {"num": "5.0", "content": "QCSOP-011 v2.0"},
        {"num": "6.0", "content": "C = (A - B) / V * 100"},
        {"num": "7.0", "content": ""},
    ]) == []


def test_bilingual_gaps_is_what_the_whole_document_check_would_miss():
    """The regression this exists for, stated directly: a document whose
    sections are overwhelmingly English but that carries Macedonian in ONE
    section satisfies pp_verify's document-wide check, and must not satisfy
    this one."""
    sections = [{"num": "1.0", "content": f"{_MK}|{_EN}"}] + [
        {"num": f"{n}.0", "content": _EN * 3} for n in range(2, 8)
    ]
    whole_doc = " ".join(s["content"] for s in sections)
    import re as _re
    assert _re.search(r"[Ѐ-ӿ]", whole_doc) and _re.search(r"[A-Za-z]", whole_doc)
    assert _bilingual_gaps(sections) == [f"{n}.0 (no MK)" for n in range(2, 8)]


@pytest.mark.asyncio
async def test_monolingual_section_fails_the_job_before_the_build(monkeypatch):
    """The gate wired end-to-end: an English-only section must fail the job,
    and must do so BEFORE builder.build runs — the whole point is catching it
    while the sections are still separable, not after pp_verify's
    document-wide check has waved it through."""
    updates = _patch_common(monkeypatch)
    built = []
    monkeypatch.setattr(builder, "build", lambda *a, **k: built.append(1) or _fake_build_result())

    class EnglishOnlyClient(FakeClient):
        async def send_message(self, agent_id, prompt):
            if "§6A" in prompt:
                return "PASS"
            if "Check this drafted section" in prompt:
                return "NO-FINDING"
            return _EN * 3          # the drafted section body — no Macedonian

    await run_workflow("job-1", client=EnglishOnlyClient())
    assert updates[-1]["status"] == "failed"
    assert "not bilingual" in updates[-1]["error"]
    assert updates[-1]["result"]["bilingual_gaps"] == ["1.0 (no MK)"]
    assert not built, "the build must not run once a section is known monolingual"


@pytest.mark.asyncio
async def test_bilingual_sections_still_reach_the_build(monkeypatch):
    """The other direction — the gate must not block a legitimate document."""
    updates = _patch_common(monkeypatch)
    built = []
    monkeypatch.setattr(builder, "build", lambda *a, **k: built.append(1) or _fake_build_result())

    class BilingualClient(FakeClient):
        async def send_message(self, agent_id, prompt):
            if "§6A" in prompt:
                return "PASS"
            if "Check this drafted section" in prompt:
                return "NO-FINDING"
            return f"{_MK}|{_EN}"

    await run_workflow("job-1", client=BilingualClient())
    assert updates[-1]["status"] == "done"
    assert built


def test_bilingual_gaps_does_not_fail_a_short_bilingual_section():
    """The regression that the code check caught before this shipped.

    Macedonian renders longer than its English equivalent, so an ordinary short
    bilingual section sits around 52 Cyrillic / 31 Latin letters. Judged against
    a single shared floor that reads as "missing English" and FAILS a perfectly
    good job — worse than the gap the check exists to close. Hence the split
    into _MIN_TOTAL_TO_JUDGE (is there enough text to have an opinion?) and
    _MIN_PRESENCE (is this language present at all?)."""
    mk = "Опсегот на оваа постапка ги опфаќа сите серии од производство"
    en = "Scope covers all production batches"
    assert _bilingual_gaps([{"num": "2.0", "content": f"{mk}|{en}"}]) == []
    # ...and a longer section with the same lopsided ratio is still fine
    assert _bilingual_gaps([{"num": "3.0", "content": f"{mk * 3}|{en * 3}"}]) == []


# ---- §6A verdict, grammar lint and repair rounds (10.10.2026) ----

_LIVE_FIX = ("I'll review the assembled document against the house rules.\n\n---\n\n"
             "Verdict: FIX\n\n**Issues**\n- Section 4 heading duplicated")


def test_qa_verdict_reads_the_verdict_line_not_the_first_word():
    """The live auditor opens with "I'll review…"; reading the first word made every reply not-PASS."""
    assert _qa_verdict(_LIVE_FIX) == "FIX"
    assert _qa_verdict("I'll review the document.\nNo issues.\nVERDICT: PASS") == "PASS"
    assert _qa_verdict("PASS") == "PASS"
    assert _qa_verdict("FIX: section 2.0 references the wrong regulation") == "FIX"
    assert _qa_verdict("Return verdict PASS or FIX.\n…\n**Verdict: FIX**") == "FIX"
    assert _qa_verdict("The bypass valve is fine.") == ""


def test_lint_flags_what_the_engine_cannot_read():
    body = "\n".join([
        "| Параметар | Parameter |",
        "|---|---|",
        "Аналитичарот ги проверува референтните стандарди пред анализата.",
        "Section 8 is a controlled cross-reference list.",
        "# 2 ПОДРАЧЈЕ|SCOPE",
    ])
    issues = _lint_section(body)
    assert any("pipe tables" in i for i in issues)
    assert any("not 'Macedonian ||| English'" in i for i in issues)
    assert any("working notes" in i for i in issues)
    assert any("single-'#'" in i for i in issues)


def test_lint_passes_the_engine_grammar():
    body = "\n".join([
        "## 6.1 Подготовка | Preparation",
        "Аналитичарот ги подготвува примероците. ||| The analyst prepares the samples.",
        "- Проверка на вагата ||| Balance check",
        "[[TABLE]]",
        "Параметар~~Parameter ||| Вредност~~Value",
        "Маса на примерок~~Sample weight ||| ",
        "[[/TABLE]]",
        "[[FORM]]",
        "Изработил~~Prepared by ||| ",
        "[[/FORM]]",
    ])
    assert _lint_section(body) == []


def test_strip_own_heading_drops_the_repeated_section_heading_only():
    body = "# 2.0 ПОДРАЧЈЕ НА ПРИМЕНА|SCOPE\nТекст ||| Text\n# 2 ПОДРАЧЈЕ НА ПРИМЕНА|SCOPE\n## 2.1 Опсег | Range\nА ||| B"
    out = _strip_own_heading("2.0", "ПОДРАЧЈЕ НА ПРИМЕНА", "SCOPE", body)
    assert "# 2.0" not in out and "\n# 2 " not in out
    assert "## 2.1 Опсег | Range" in out and "Текст ||| Text" in out


def test_sections_named_by_an_audit():
    nums = [f"{n}.0" for n in range(1, 10)]
    assert _sections_named("Section 4 duplicates its heading; §6.3 steps lack EN; see 7.1.", nums) == ["4.0", "6.0", "7.0"]
    assert _sections_named("The document is unclear.", nums) == nums


@pytest.mark.asyncio
async def test_live_shaped_pass_reaches_the_build(monkeypatch):
    """Regression: a PASS stated on the verdict line, after a preamble, must not fail the job."""
    updates = _patch_common(monkeypatch)
    monkeypatch.setattr(builder, "build", lambda *a, **k: _fake_build_result())

    class Live(FakeClient):
        async def send_message(self, agent_id, prompt):
            if "§6A" in prompt:
                return "I'll review the document.\nNo issues found.\nVERDICT: PASS"
            return "NO-FINDING"

    await run_workflow("job-1", client=Live())
    assert updates[-1]["status"] == "done"
    assert updates[-1]["result"]["qa_verdict"] == "PASS"


@pytest.mark.asyncio
async def test_fix_verdict_sends_named_sections_back_then_passes(monkeypatch):
    updates = _patch_common(monkeypatch, qkey="sop_qc")
    monkeypatch.setattr(builder, "build", lambda *a, **k: _fake_build_result())
    seen: list[str] = []

    class FixThenPass(FakeClient):
        audits = 0

        async def send_message(self, agent_id, prompt):
            seen.append(prompt)
            if "§6A" in prompt:
                FixThenPass.audits += 1
                return "Verdict: FIX\n- Section 4 duplicates its heading" if FixThenPass.audits == 1 else "VERDICT: PASS"
            if "Check this drafted section" in prompt:
                return "NO-FINDING"
            return "Текст на секцијата ||| Section text"

    await run_workflow("job-1", client=FixThenPass())
    assert updates[-1]["status"] == "done"
    assert updates[-1]["result"]["qa_rounds"] == 1
    repairs = [p for p in seen if p.startswith("REVISE section")]
    assert len(repairs) == 1 and repairs[0].startswith("REVISE section 4.0")
    assert any(u.get("stage") == "qa-audit repair-1" for u in updates)


@pytest.mark.asyncio
async def test_failed_audit_keeps_the_draft_and_findings(monkeypatch):
    """A failed job used to keep only the verdict; the draft and sources were lost."""
    updates = _patch_common(monkeypatch, qkey="sop_qc")

    class AlwaysFix(FakeClient):
        async def send_message(self, agent_id, prompt):
            if "§6A" in prompt:
                return _LIVE_FIX
            if "Check this drafted section" in prompt:
                return "OK [R1] EU GMP Ch. 4"
            return "Текст на секцијата ||| Section text"

    await run_workflow("job-1", client=AlwaysFix())
    res = updates[-1]["result"]
    assert updates[-1]["status"] == "failed" and updates[-1]["error"] == "§6A audit did not pass"
    assert res["qa_verdict"] == "FIX" and res["qa_audit"] == _LIVE_FIX
    assert res["markdown"].startswith("<!--HEADERDATA") and "# 9.0" in res["markdown"]
    assert len(res["regulatory"]) == 9 and res["regulatory"][0].startswith("[1.0]")


@pytest.mark.asyncio
async def test_regulatory_checks_run_concurrently_and_keep_section_order(monkeypatch):
    import asyncio
    updates = _patch_common(monkeypatch, qkey="sop_qc")
    monkeypatch.setattr(builder, "build", lambda *a, **k: _fake_build_result())
    live = {"now": 0, "peak": 0}

    class Slow(FakeClient):
        async def send_message(self, agent_id, prompt):
            if "Check this drafted section" in prompt:
                live["now"] += 1
                live["peak"] = max(live["peak"], live["now"])
                await asyncio.sleep(0.02)
                live["now"] -= 1
                return "NO-FINDING " + prompt.split("section ", 1)[1].split(" ", 1)[0]
            return "PASS" if "§6A" in prompt else "Текст ||| Text"

    await run_workflow("job-1", client=Slow())
    res = updates[-1]["result"]
    assert updates[-1]["status"] == "done"
    assert 1 < live["peak"] <= 4
    assert [r.split("]")[0] for r in res["regulatory"]] == [f"[{n}.0" for n in range(1, 10)]
    stages = [u["stage"] for u in updates if str(u.get("stage", "")).startswith("regulatory-check ")]
    assert stages == [f"regulatory-check {n}.0" for n in range(1, 10)]
