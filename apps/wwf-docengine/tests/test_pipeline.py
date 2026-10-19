# Pipeline unit surface: questionnaire defaulting + Markdown assembly, plus
# run_workflow's error-path coverage (the Letta round-trips are otherwise
# exercised live on the wwf_mass stack, not here).
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import builder, db, fleet  # noqa: E402
from app.config import settings  # noqa: E402
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

    async def fake_job_finish(jid, **fields):       # the terminal write (review 19.10.2026): recorded like any update
        updates.append(fields)
        return True

    async def fake_job_touch(jid):
        return "running"

    async def fake_document_create(job_id, meta):
        return "doc-1"

    async def fake_ensure_fleet(client):
        return {name: f"agent-{name}" for name in _AGENT_NAMES}

    async def fake_spawn_ephemeral(client, agent_name, name_suffix):
        return f"tmp-{agent_name}-{name_suffix}"

    monkeypatch.setattr(db, "job_get", fake_job_get)
    monkeypatch.setattr(db, "job_update", fake_job_update)
    monkeypatch.setattr(db, "job_finish", fake_job_finish)
    monkeypatch.setattr(db, "job_touch", fake_job_touch)
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
    """Hard-gate mode (DOCENGINE_FIX_TO_REVIEW=0)."""
    monkeypatch.setattr(settings, "fix_to_review", False)
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
            return f"{_MK} ||| {_EN}"

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
        "Преглед согласно двoстепениот синџир. ||| Review per the two-tier chain.",
    ])
    issues = _lint_section(body)
    assert any("mixing Cyrillic and Latin" in i and "двoстепениот" in i for i in issues)
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
    assert _lint_section(body, sop=False) == []                         # an annex may hold write-in forms
    assert _lint_section(body.split("[[FORM]]")[0]) == []               # an SOP: the same, without the form


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
    monkeypatch.setattr(settings, "fix_to_review", False)
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


@pytest.mark.asyncio
async def test_fix_after_all_rounds_is_built_and_parked_for_review_not_registered(monkeypatch):
    monkeypatch.setattr(settings, "fix_to_review", True)
    updates = _patch_common(monkeypatch, qkey="sop_qc")
    built, registered = [], []
    monkeypatch.setattr(builder, "build", lambda *a, **k: built.append(1) or _fake_build_result())

    async def no_register(job_id, meta):
        registered.append(meta)
        return "doc-x"
    monkeypatch.setattr(db, "document_create", no_register)

    class AlwaysFix(FakeClient):
        async def send_message(self, agent_id, prompt):
            if "§6A" in prompt:
                return _LIVE_FIX
            if "Check this drafted section" in prompt:
                return "NO-FINDING"
            return "Текст на секцијата ||| Section text"

    await run_workflow("job-1", client=AlwaysFix())
    last = updates[-1]
    assert last["status"] == "awaiting_review" and last["stage"] == "format"
    assert built and not registered, "built and verified, never registered before a person approves"
    res = last["result"]
    assert res["qa_verdict"] == "FIX" and res["qa_rounds"] == settings.qa_repair_rounds
    assert res["artifact"]["path"] == "/tmp/x.docx" and res["verify"] == "RESULT: PASS"
    assert "review_reason" in res and res["markdown"].startswith("<!--HEADERDATA")


def test_reference_rule_reaches_authors_and_repairs():
    from app import pipeline
    assert "За потврда | To be confirmed" in pipeline.REFERENCE_RULE
    src = Path(pipeline.__file__).read_text(encoding="utf-8")
    assert src.count("{REFERENCE_RULE}") >= 3   # SOP draft, annex draft, QA repair


def test_no_length_target_conciseness_is_a_content_rule():
    """Head of QC, 11.10.2026: no page or word limit; redundancy is what gets controlled."""
    import app.pipeline as p
    assert not hasattr(p, "SOP_WORDS") and not hasattr(p, "_length_issue")
    assert "every requirement once" in p.CONCISE and "no filler" in p.CONCISE
    assert p._lint_section("- Записи ||| " + "record " * 2000) == []      # length alone is never a finding


def test_lint_flags_terms_outside_the_house_glossary():
    """Head of QC, 11.10.2026: the house Macedonian glossary (from WHSOP_003 v01 §5) is binding."""
    body = "\n".join([
        "Палетата се завиткува со термално ќебе. ||| The pallet is wrapped in a thermal blanket.",
        "Кесите со интермедијер се бројат. ||| The bags of intermediate are counted.",
        "Секоја девијација се евидентира. ||| Every deviation is recorded.",
    ])
    issues = _lint_section(body)
    hit = next(i for i in issues if "house glossary" in i)
    assert "термално ќебе" in hit and "термо-ќебе" in hit
    assert "интермедијер" in hit and "меѓупроизвод" in hit
    assert "девијација" in hit and "отстапување" in hit


def test_lint_flags_the_older_word_for_sampling():
    """Head of QC, 19.10.2026 (review of QCSOP001A01): one word for sampling in the QC documents — мострирање,
    never узорцирање, which the older QCLB005 and QCSOP014 still carry."""
    issues = _lint_section("Дневник за узорцирање во Сектор Контрола на квалитет ||| Sampling logbook of the QC Department")
    hit = next(i for i in issues if "house glossary" in i)
    assert "узорцирање" in hit and "мострирање" in hit
    assert _lint_section("План за мострирање на мостри во процес ||| Sampling plan for in-process samples") == []


def test_glossary_terms_and_their_legitimate_lookalikes_pass_the_lint():
    body = "\n".join([
        "Палетата се завиткува со стреч-фолија и термо-ќебе. ||| The pallet is wrapped in stretch film and a thermal blanket.",
        "Секое отстапување се евидентира. ||| Every deviation is recorded.",
        "Се пресметува стандардна девијација. ||| The standard deviation is calculated.",
        "Отпадот се собира во вреќи. ||| Waste is collected in sacks.",
        "Методи: метод 1 ||| Methods: method 1",
    ])
    assert _lint_section(body) == []


def test_approved_whsop_003_reads_clean_against_the_glossary():
    """The glossary was taken from WHSOP_003 v01 — its own text must never be flagged."""
    import re
    import zipfile
    from app import glossary
    docs = sorted((Path(__file__).resolve().parents[3] / "deliverables" / "inland_transport_2026-10" / "docx").glob("WHSOP_003*.docx"))
    if not docs:
        pytest.skip("WHSOP_003 deliverables not in this checkout")
    for d in docs:
        text = re.sub(r"<[^>]+>", " ", zipfile.ZipFile(d).read("word/document.xml").decode("utf-8"))
        assert glossary.term_issues(text) == [], d.name


def test_annexes_are_separate_documents_never_forms_inside_the_sop():
    """Head of QC, 13.10.2026: the SOP names its annexes by code and title; each is its own annex job."""
    import app.pipeline as p
    assert "never writes a form's fields into the SOP" in p.ANNEX_RULE and "attached" in p.ANNEX_RULE
    assert p.ANNEX_RULE in p.SECTION_HINT["7.0"] and "7.1" in p.SECTION_HINT["8.0"]
    src = Path(p.__file__).read_text(encoding="utf-8")
    assert "SECTION_HINT.get(num, ANNEX_RULE)" in src                    # every SOP section is told
    assert src.count("{ANNEX_RULE") >= 2                                  # QA repair and the audit
    form = "[[FORM]]\nИзработил~~Prepared by ||| \n[[/FORM]]"
    assert any("[[FORM]]" in i and "separate annexes" in i for i in _lint_section(form))
    assert not any("[[FORM]]" in i for i in _lint_section(form, sop=False))


def test_glossary_terms_added_on_13_10():
    from app import glossary
    text = glossary.memory_text()
    assert "траса" in text and "уред за ладење/греење" in text and "ID на логерот" in text
    assert glossary.term_issues("Се запишува серискиот број на логерот.") == ["„серискиот број на логерот“ → ID на логерот"]


def test_a_reply_that_echoes_the_request_is_never_inserted():
    """13.10.2026, transport run a142b9dd: a lint-repair reply came back as the request + old section + new section."""
    import app.pipeline as p
    echoed = ("Rewrite section 3.0 ОДГОВОРНОСТИ|RESPONSIBILITIES of 'X | Y' (code Z) to fix these problems:\n- …\n\n"
              + p.ENGINE_GRAMMAR + "\n\nKeep every requirement. Return ONLY the corrected section body — your reply is "
              "inserted verbatim.\n\nCURRENT SECTION\n## 3.1 Општо | General\nТекст ||| Text")
    assert p._echoes_prompt(echoed)
    assert any("request text was copied" in i for i in _lint_section(echoed))
    clean = "## 3.1 Општо | General\nВратете го образецот на QA. ||| Return the form to QA.\nТековен дел ||| Current section"
    assert not p._echoes_prompt(clean) and _lint_section(clean) == []
    src = Path(p.__file__).read_text(encoding="utf-8")
    assert "if _echoes_prompt(text) and s.get(\"content\"):" in src and "return s[\"content\"]" in src


def test_transport_controls_reach_authors_repair_and_audit():
    """Head of QC, 13.10.2026: the controls the five transport runs all dropped are declared on the questionnaire
    and reach every SOP section prompt, the QA repair and the §6A audit, which treats a missing one as FIX."""
    import app.pipeline as p
    from app.questionnaires import QUESTIONNAIRES
    ctl = QUESTIONNAIRES["sop_transport"]["controls"]
    joined = " ".join(ctl).lower()
    for must in ("reconciliation", "escort", "never placed inside sealed", "calibrated", "one owner per record",
                 "identifier", "season", "annex 15", "hand-over", "return-leg"):
        assert must in joined, must
    rule = p.controls_rule("sop_transport")
    assert rule.startswith("CONTROLS THIS SOP MUST CONTAIN") and rule.count("\n- ") == len(ctl)
    assert p.controls_rule("sop_qc") == ""                       # declares none → nothing injected
    src = Path(p.__file__).read_text(encoding="utf-8")
    assert src.count("{controls}") >= 3                           # section prompt, QA repair, audit
    assert "a missing control is FIX" in src and "One owner per record" in src


def test_annex_job_reads_its_parent_sop_sections_6_and_7():
    import app.pipeline as p
    md = ("<!--HEADERDATA\ncode: X\n-->\n# 1.0 ЦЕЛ|PURPOSE\nцел ||| purpose\n# 6.0 ПОСТАПКА|PROCEDURE\n## 6.1 A | A\n"
          "серискиот број се запишува во A04 ||| the serial is recorded in A04\n# 7.0 ЗАПИСИ|RECORDS\n[[TABLE]]\n"
          "A04 ||| Манифест~~Manifest ||| Логистика~~Logistics\n[[/TABLE]]\n# 8.0 ПОВРЗАНИ|RELATED\nx ||| y\n")
    part = p._parent_sections(md)
    assert part.startswith("# 6.0") and "recorded in A04" in part and "# 7.0" in part
    assert "# 8.0" not in part and "PURPOSE" not in part
    src = Path(p.__file__).read_text(encoding="utf-8")
    assert "job_latest_markdown_by_code(parent_code)" in src and "PARENT SOP" in src
    from app.main import WorkflowIn
    w = WorkflowIn(questionnaire="annex_form", meta={"title_mk": "а", "title_en": "a", "code": "X_A04"}, parent_sop="WHSOP_003")
    assert w.parent_sop == "WHSOP_003"


def test_form_rules_no_open_questions_on_a_form_and_no_scaffold_heading():
    import app.pipeline as p
    assert "no 'To be confirmed' section" in p.FORM_RULE
    body = "# 1 Идентификација | Identification\n[[FORM:grid]]\nUTID ||| UTID ||| \n[[/FORM]]\n## 1.6 За потврда | To be confirmed\n- x ||| y"
    assert any("To be confirmed" in i for i in _lint_section(body, sop=False))
    clean = body.split("## 1.6")[0]
    assert _lint_section(clean, sop=False) == []
    meta = {"title_mk": "а", "title_en": "a", "code": "X_A04", "doctype": "FORM"}
    out = assemble_markdown(meta, [{"num": "1.0", "mk": "СОДРЖИНА", "en": "CONTENT", "content": clean}])
    assert "СОДРЖИНА" not in out and "\n# 1 Идентификација" in out      # the form's own heading stands alone
    out2 = assemble_markdown(meta, [{"num": "1.0", "mk": "СОДРЖИНА", "en": "CONTENT", "content": "[[FORM:grid]]\nA ||| B ||| \n[[/FORM]]"}])
    assert "# 1.0 СОДРЖИНА|CONTENT" in out2                        # no heading of its own → the wrapper stays
    sop = {"title_mk": "а", "title_en": "a", "code": "X", "doctype": "SOP"}
    assert "# 1.0 ЦЕЛ|PURPOSE" in assemble_markdown(sop, [{"num": "1.0", "mk": "ЦЕЛ", "en": "PURPOSE", "content": "# x"}])


def test_questionnaire_label_uses_metod_not_metoda():
    from app.questionnaires import QUESTIONNAIRES
    import json
    assert "метода" not in json.dumps(QUESTIONNAIRES, ensure_ascii=False)


# ---- review 14.10.2026 ----

def test_sections_named_ignores_clause_numbers_of_regulations_and_annexes():
    """'Chapter 4.1', 'Annex 15 §6.1', 'ICH Q9 4.1', 'A04 2.1 vs 2.2' are clauses of other documents: they used
    to send sections 2 and 4 back for a rewrite the audit never asked for."""
    nums = [f"{n}.0" for n in range(1, 10)]
    audit = ("Section 6 misses the hand-over temperature. EU GMP Chapter 4.1 is cited correctly. Annex 15 §6.1 cited. "
             "ICH Q9 4.1. A04 2.1 vs 2.2. Annex 11 §4.8. EU GMP Part I §4.11. чл. 63 ст. 1.\nVERDICT: FIX")
    assert _sections_named(audit, nums) == ["6.0"]
    assert _sections_named("- 5.2: GDP missing from 5.2\n- 8.0 lists WHSOP_002\nGDP 9.2 says so", nums) == ["5.0", "8.0"]


def test_strip_own_heading_keeps_content_headings_and_misnumbered_subsections():
    # 'ЦЕЛ' is the section title, not a substring to hunt for: "Целосна листа" is content.
    assert _strip_own_heading("1.0", "ЦЕЛ", "PURPOSE", "# Целосна листа | Full list\nа ||| b").startswith("# Целосна")
    body = "# 6.0 ПОСТАПКА|PROCEDURE\n# 6 ПОСТАПКА|PROCEDURE\n# 6.3 Фаза 2 | Stage 2\n# ПОСТАПКА | PROCEDURE\nа ||| b"
    out = _strip_own_heading("6.0", "ПОСТАПКА", "PROCEDURE", body)
    assert out == "# 6.3 Фаза 2 | Stage 2\nа ||| b"          # kept, so the linter sends it back as '## 6.3'
    assert any("single-'#' heading" in i for i in _lint_section(out))


def test_meta_with_a_line_break_cannot_write_its_own_headerdata_line():
    import app.pipeline as p
    with pytest.raises(ValueError, match="line break"):
        p.assemble_markdown({"title_mk": "а\ndoctype: FORM", "title_en": "a", "code": "X", "doctype": "SOP"}, [])


@pytest.mark.asyncio
async def test_annex_job_records_which_parent_job_it_read(monkeypatch):
    updates = _patch_common(monkeypatch)
    monkeypatch.setattr(builder, "build", lambda *a, **k: _fake_build_result())

    async def job_get(jid):
        j = _job("annex_form")
        j["payload"]["parent_sop"] = "WHSOP_003"
        return j

    async def latest(code):
        assert code == "WHSOP_003"
        return {"markdown": "# 6.0 ПОСТАПКА|PROCEDURE\nа ||| b\n# 7.0 ЗАПИСИ|RECORDS\nв ||| c\n",
                "job_id": "abcdef12-0000-0000-0000-000000000000", "status": "awaiting_review"}

    monkeypatch.setattr(db, "job_get", job_get)
    monkeypatch.setattr(db, "job_latest_markdown_by_code", latest)
    seen: list[str] = []

    class Annex(FakeClient):
        async def send_message(self, agent_id, prompt):
            seen.append(prompt)
            if "§6A" in prompt:
                return "VERDICT: PASS"
            if "Check this drafted section" in prompt:
                return "NO-FINDING"
            return "# 1 Идентификација | Identification\n[[FORM:grid]]\nUTID ||| UTID ||| \n[[/FORM]]"

    await run_workflow("job-1", client=Annex())
    res = updates[-1]["result"]
    assert updates[-1]["status"] == "done"
    assert res["knowledge"]["parent_sop"] == {"code": "WHSOP_003", "job_id": "abcdef12-0000-0000-0000-000000000000",
                                               "status": "awaiting_review"}
    assert any("not registered" in n for n in res["knowledge"]["notes"])
    assert any("PARENT SOP WHSOP_003" in s for s in seen)


def test_an_empty_section_is_a_lint_issue():
    """An empty reply passed every check: no lint issue, and the bilingual gate skips short sections."""
    assert _lint_section("") == ["the section is empty — write its content"]
    assert _lint_section("   \n", sop=False) == ["the section is empty — write its content"]


def test_a_pass_is_never_read_out_of_prose():
    """An audit with no verdict line was a PASS when any bullet opened with the word ("- Pass/fail criteria
    are missing"), and a later "the verdict: PASS" overrode a FIX — either registered a FIX document as done."""
    assert _qa_verdict("Findings:\n- Section 6.3 lacks a step owner\n- Pass/fail criteria for the balance are missing") == ""
    assert _qa_verdict("Verdict: FIX\n- missing owner in 7.1\nOnce fixed the verdict: PASS") == "FIX"
    assert _qa_verdict("Earlier verdict: FIX, now resolved.\nVERDICT: PASS") == "PASS"   # the final line rules
    assert _qa_verdict("PASS.") == "PASS" and _qa_verdict("fix the heading in 3.2") == ""


def test_a_fence_only_reply_is_empty():
    import app.pipeline as p
    assert p._clean_section("```markdown\n```") == ""
    assert p._clean_section("```markdown\nа ||| b\n```") == "а ||| b"
    assert _lint_section("```") == ["the section is empty — write its content"]


@pytest.mark.asyncio
async def test_lint_left_after_the_repair_rounds_goes_to_a_person(monkeypatch):
    """A pipe table, an echoed prompt or a monolingual line that survived the repair round was registered as
    done on an auditor's PASS."""
    updates = _patch_common(monkeypatch)
    monkeypatch.setattr(builder, "build", lambda *a, **k: _fake_build_result())

    class Stubborn(FakeClient):
        async def send_message(self, agent_id, prompt):
            if "§6A" in prompt:
                return "VERDICT: PASS"
            if "Check this drafted section" in prompt:
                return "NO-FINDING"
            return "[[FORM:grid]]\nUTID ||| UTID ||| \n[[/FORM]]\n| a | b |\n| c | d |"

    await run_workflow("job-1", client=Stubborn())
    last = updates[-1]
    assert last["status"] == "awaiting_review" and "grammar problems remain in 1.0" in last["result"]["review_reason"]


def test_parent_sections_keep_section_7_whole():
    import app.pipeline as p
    md = "# 6.0 ПОСТАПКА|PROCEDURE\n" + ("а ||| b\n" * 4000) + "# 7.0 ЗАПИСИ|RECORDS\nA04 ||| Манифест\n# 8.0 X|Y\nz ||| z\n"
    part = p._parent_sections(md, limit=5000)
    assert len(part) <= 5000 and part.endswith("A04 ||| Манифест") and "shortened" in part and "# 8.0" not in part


def test_sections_named_reads_lists_and_skips_codes_and_versions():
    nums = [f"{n}.0" for n in range(1, 10)]
    assert _sections_named("Sections 3 and 6 lack EN.", nums) == ["3.0", "6.0"]
    assert _sections_named("Sections 2, 5 and 8.1 repeat each other.", nums) == ["2.0", "5.0", "8.0"]
    assert _sections_named("Section 4: bump to version 1.0; QASOP_011 5.2 and WHSOP_003 6.2 are cited.", nums) == ["4.0"]


def test_headings_the_engine_would_misprint_are_normalised():
    import app.pipeline as p
    assert p._normalise_headings("## 6.1 Подготовка ||| Preparation\nа ||| b") == "## 6.1 Подготовка | Preparation\nа ||| b"
    assert p._normalise_headings("#6.2 Чекор | Step") == "# 6.2 Чекор | Step"


def test_procedure_english_is_not_working_notes():
    assert _lint_section("Записите ||| The records section 7 lists are kept for 5 years.\n"
                         "Краток ||| The brief visual inspection is recorded.") == []
    assert any("working notes" in i for i in _lint_section("Белешка ||| This section covers the scope."))


def test_an_unnumbered_heading_is_dropped_only_when_it_is_the_title():
    assert _strip_own_heading("6.0", "ПОСТАПКА", "PROCEDURE", "# Receipt procedure | Постапка за прием\nА ||| B").startswith("# Receipt")
    assert _strip_own_heading("6.0", "ПОСТАПКА", "PROCEDURE", "# ПОСТАПКА | PROCEDURE\nА ||| B") == "А ||| B"


def test_procedure_text_is_not_an_echo():
    import app.pipeline as p
    assert not p._echoes_prompt("Вратете ја САМО потпишаната копија ||| Return ONLY the signed copy to QA")
    assert p._echoes_prompt("Return ONLY the corrected section body — your reply is inserted verbatim.")


def test_the_brief_never_says_none():
    import app.pipeline as p
    brief = p._brief("sop_qc", {"focus": None, "techniques": [], "records": ["CoA", 5]})
    assert "None" not in brief and "techniques" not in brief and "- records: CoA, 5" in brief


def test_glossary_lookbehinds_hold_across_a_line_break():
    from app import glossary
    assert glossary.term_issues("релативна стандардна\nдевијација") == []


@pytest.mark.asyncio
async def test_a_step_that_failed_transiently_repeats_on_a_fresh_clone(monkeypatch):
    """A timed-out message is not re-sent to the same clone; the step runs again on a new one and the job
    records the repeat (review 14.10.2026)."""
    from app.letta import LettaError
    updates = _patch_common(monkeypatch)
    monkeypatch.setattr(builder, "build", lambda *a, **k: _fake_build_result())
    clones, deleted = [], []

    async def spawn(client, agent_name, suffix):
        clones.append(suffix)
        return f"tmp-{suffix}"

    monkeypatch.setattr(fleet, "spawn_ephemeral", spawn)

    class Flaky(FakeClient):
        failed = False

        async def send_message(self, agent_id, prompt):
            if "Design the" in prompt and not Flaky.failed:
                Flaky.failed = True
                raise LettaError("POST /agents/x/messages -> ReadTimeout: slow", transient=True)
            if "§6A" in prompt:
                return "VERDICT: PASS"
            if "Check this drafted section" in prompt:
                return "NO-FINDING"
            return "# 1 Идентификација | Identification\n[[FORM:grid]]\nUTID ||| UTID ||| \n[[/FORM]]"

        async def delete_agent(self, agent_id):
            deleted.append(agent_id)

    await run_workflow("job-1", client=Flaky())
    last = updates[-1]
    assert last["status"] == "done"
    assert last["result"]["retries"][0]["step"] == "10" and "ReadTimeout" in last["result"]["retries"][0]["error"]
    assert "job-1_10" in clones and "job-1_10_x1" in clones
    assert "tmp-job-1_10" in deleted and "tmp-job-1_10_x1" in deleted


@pytest.mark.asyncio
async def test_a_refusal_is_not_repeated(monkeypatch):
    from app.letta import LettaError
    updates = _patch_common(monkeypatch)

    class Refuses(FakeClient):
        async def send_message(self, agent_id, prompt):
            raise LettaError("POST -> 422: bad", status=422)

    await run_workflow("job-1", client=Refuses())
    assert updates[-1]["status"] == "failed" and "422" in updates[-1]["error"]


# ---- review 19.10.2026 ----

def test_quantities_are_not_section_references():
    nums = [f"{n}.0" for n in range(1, 10)]
    assert _sections_named("Section 6 is fine. The limit is 2.5 kg and 0.5 % per 3.0 mL. VERDICT: FIX", nums) == ["6.0"]
    assert _sections_named("The pH is 7.2 and the hold time 2.5 h; see 6.1 for the 5.0 mm sieve.", nums) == ["6.0"]
    assert _sections_named("§4.2 and section 7.3 are fine; 2.5 kg is a quantity. VERDICT: FIX", nums) == ["4.0", "7.0"]
    assert _sections_named("- 3.1: missing owner\n* 8.2 repeats 6\nSection 1 fine", nums) == ["1.0", "3.0", "8.0"]


@pytest.mark.asyncio
async def test_an_sop_parked_for_review_starts_no_annex_jobs(monkeypatch):
    """Four annexes were written to an SOP the reviewer then returned: the package starts on done or approve only."""
    updates = _patch_common(monkeypatch, qkey="sop_qc")
    monkeypatch.setattr(builder, "build", lambda *a, **k: _fake_build_result())
    created, merged = [], []

    async def job_get(jid):
        j = _job("sop_qc")
        j["payload"]["package_annexes"] = [{"title_en": "Log"}]
        j["payload"]["meta"]["code"] = "QCSOP026"
        return j

    async def job_create(kind, payload, by=""):
        created.append(payload)
        return "annex-1"

    async def merge(jid, extra):
        merged.append(extra)

    async def taken(*a):
        return set()
    monkeypatch.setattr(db, "job_get", job_get)
    monkeypatch.setattr(db, "job_create", job_create)
    monkeypatch.setattr(db, "job_merge_result", merge)
    monkeypatch.setattr(db, "codes_in_use", taken)
    monkeypatch.setattr(db, "codes_of_brief", taken)

    class AlwaysFix(FakeClient):
        async def send_message(self, agent_id, prompt):
            if "§6A" in prompt:
                return _LIVE_FIX
            if "Check this drafted section" in prompt:
                return "NO-FINDING"
            return "Текст на секцијата ||| Section text"

    await run_workflow("job-1", client=AlwaysFix())
    assert updates[-1]["status"] == "awaiting_review" and created == [] and merged == []
    # …and a job that is registered as done starts them
    updates.clear()
    await run_workflow("job-1", client=FakeClient())
    assert updates[-1]["status"] == "done" and [c["meta"]["code"] for c in created] == ["QCSOP026A01"]
    assert merged[-1]["package_jobs"][0]["job_id"] == "annex-1"


@pytest.mark.asyncio
async def test_a_bilingual_gap_after_a_repair_round_is_parked_for_a_person(monkeypatch):
    """A repair reply that dropped one language failed the whole job after the audit had been acted on; the first
    draft's gap still fails it, and so does any gap when review parking is off."""
    updates = _patch_common(monkeypatch, qkey="sop_qc")
    built = []
    monkeypatch.setattr(builder, "build", lambda *a, **k: built.append(1) or _fake_build_result())

    class RepairDropsMK(FakeClient):
        audits = 0

        async def send_message(self, agent_id, prompt):
            if "§6A" in prompt:
                RepairDropsMK.audits += 1
                return "Verdict: FIX\n- Section 4 duplicates its heading" if RepairDropsMK.audits == 1 else "VERDICT: PASS"
            if "Check this drafted section" in prompt:
                return "NO-FINDING"
            if prompt.startswith(("REVISE section", "Rewrite section")):
                return _EN * 3
            return "Текст на секцијата ||| Section text"

    monkeypatch.setattr(settings, "fix_to_review", True)
    await run_workflow("job-1", client=RepairDropsMK())
    last = updates[-1]
    assert last["status"] == "awaiting_review" and built
    assert last["result"]["bilingual_gaps"] == ["4.0 (no MK)"] and "not bilingual" in last["result"]["review_reason"]
    assert "after repair round 1" in last["result"]["review_reason"]
    RepairDropsMK.audits, built[:] = 0, []
    monkeypatch.setattr(settings, "fix_to_review", False)
    await run_workflow("job-1", client=RepairDropsMK())
    assert updates[-1]["status"] == "failed" and "not bilingual" in updates[-1]["error"] and not built


@pytest.mark.asyncio
async def test_an_unconfirmed_parent_without_its_package_job_is_not_looked_up_by_code(monkeypatch):
    """Every unconfirmed QASOPXXX shares the code: a lookup by code read another SOP's procedure into the form."""
    from app import house
    updates = _patch_common(monkeypatch)
    monkeypatch.setattr(builder, "build", lambda *a, **k: _fake_build_result())

    async def job_get(jid):
        j = _job("annex_form")
        j["payload"]["parent_sop"] = "QASOPXXX"
        j["payload"]["meta"]["code"] = "QASOPXXXA01"
        return j

    async def never(*a, **k):
        raise AssertionError("looked the unconfirmed parent up by code")
    monkeypatch.setattr(db, "job_get", job_get)
    monkeypatch.setattr(db, "job_latest_markdown_by_code", never)
    monkeypatch.setattr(house, "approved_text", never)
    seen = []

    class Annex(FakeClient):
        async def send_message(self, agent_id, prompt):
            seen.append(prompt)
            if "§6A" in prompt:
                return "VERDICT: PASS"
            if "Check this drafted section" in prompt:
                return "NO-FINDING"
            return "# 1 Идентификација | Identification\n[[FORM:grid]]\nUTID ||| UTID ||| \n[[/FORM]]"

    await run_workflow("job-1", client=Annex())
    res = updates[-1]["result"]
    assert updates[-1]["status"] == "done" and "parent_sop" not in res["knowledge"]
    assert "parent SOP QASOPXXX is unconfirmed: give the parent job, or confirm the number" in res["knowledge"]["notes"]
    assert not any("PARENT SOP" in p for p in seen)


@pytest.mark.asyncio
async def test_a_job_the_reaper_failed_stops_and_writes_nothing_more(monkeypatch):
    """The pipeline asks the row's status before every exchange; a reaper-failed row ends the run without a terminal
    write (db.job_finish refuses one anyway)."""
    updates = _patch_common(monkeypatch)
    built = []
    monkeypatch.setattr(builder, "build", lambda *a, **k: built.append(1) or _fake_build_result())
    touches = []

    async def touch(jid):
        touches.append(jid)
        return "failed" if len(touches) > 1 else "running"
    monkeypatch.setattr(db, "job_touch", touch)
    await run_workflow("job-1", client=FakeClient())
    assert len(touches) == 2 and not built
    assert [u["status"] for u in updates if "status" in u] == ["running"]


def test_source_files_are_labelled_by_what_they_are_for():
    """Head of QC, 19.10.2026: a formatting example lends its layout, an executed example its structure, never values."""
    from app.pipeline import _brief
    b = _brief("annex_form", {}, source_texts=[{"name": "ref.pdf", "text": "facts", "role": "content"},
                                               {"name": "tpl.docx", "text": "layout", "role": "format"},
                                               {"name": "filled.pdf", "text": "values", "role": "example"},
                                               {"name": "old.md", "text": "x"}])
    assert "«ref.pdf» — reference contents" in b and "«tpl.docx» — an example of document formatting" in b
    assert "«filled.pdf» — an executed (filled-in) example" in b and "«old.md» — reference contents" in b
