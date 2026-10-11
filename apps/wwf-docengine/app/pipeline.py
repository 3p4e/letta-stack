# docengine.app.pipeline — the merged content workflow (DOCENGINE-CANON §5):
# questionnaire answers -> section generation by the gf_ fleet -> per-section
# regulatory RAG check -> §6A audit -> bilingual Markdown assembly -> the
# formatting core (builder.py, hard PASS gate) -> registry row.
#
# Runs as an asyncio background task; ALL state transitions go through
# Postgres (db.jobs) so any worker can serve the poll.
from __future__ import annotations

import asyncio
import logging
import re

from . import builder, db
from .config import settings
from .letta import LettaClient, LettaError
from .ragflow import EXAMPLES_NOTE, RagflowClient, RagflowError, citations, format_passages
from .questionnaires import QUESTIONNAIRES, apply_defaults

log = logging.getLogger("docengine.pipeline")

SOP_SECTIONS = [
    ("1.0", "ЦЕЛ", "PURPOSE"),
    ("2.0", "ПОДРАЧЈЕ НА ПРИМЕНА", "SCOPE"),
    ("3.0", "ОДГОВОРНОСТИ", "RESPONSIBILITIES"),
    ("4.0", "РЕФЕРЕНТНИ ДОКУМЕНТИ", "REFERENCE DOCUMENTS"),
    ("5.0", "ДЕФИНИЦИИ", "DEFINITIONS"),
    ("6.0", "ПОСТАПКА", "PROCEDURE"),
    ("7.0", "ЗАПИСИ", "RECORDS"),
    ("8.0", "ПОВРЗАНИ ДОКУМЕНТИ", "RELATED DOCUMENTS"),
    ("9.0", "РЕВИЗИЈА", "REVISION"),
]

_MD_FENCE = re.compile(r"^```[a-zA-Z]*\n|\n```$", re.M)

# Conversational lead-ins a stateful agent sometimes emits BEFORE the document
# body despite being told "body only" (observed live: "Looking at the persona
# description more carefully... Let me align..."). These must never reach the
# .docx. Matched case-insensitively at the very start of a line.
# Narrowed deliberately. These five alternatives were removed because they
# open legitimate SOP prose at least as often as agent chatter, and the strip
# is silent: "note:", "based on( the)?", "the following", "this is (my|the)",
# "below is". "Note: samples are stored at 2-8 C." and "The following
# equipment is required:" are ordinary procedure text, and losing either is a
# content-integrity defect in a controlled document. What is left is
# first-person / meta phrasing that has no place in an SOP body at all.
_PREAMBLE = re.compile(
    r"^(looking at|let me|here('s| is)|here are|i'll|i will|i have|i've|"
    r"as (requested|instructed|per)|sure[,!]|certainly|okay|alright|"
    r"understood|of course|great[,!]|let's|now,? (let|i))\b",
    re.I,
)
# A conversational lead-in is SHORT — a sentence or two. Anything bigger is
# the agent's actual output, so the stripper must not be what decides to drop
# it. Absolute cap only, deliberately: a proportional cap misfires on short
# sections, where a single legitimate lead-in line is a large share of the
# body and would be wrongly kept.
_MAX_PREAMBLE_CHARS = 400
# The first structural token of a real document body: a Markdown heading or a
# form/table marker. Everything an annex author says before this is commentary.
_STRUCT = re.compile(r"^\s*(#{1,6}\s|\[\[(FORM|TABLE))", re.M)


class QaAuditFailed(Exception):
    """The §6A auditor returned a FIX verdict (or something other than a
    clear PASS) — the document must not proceed to formatting/registration
    until the issues are addressed. Consistent with pp_verify's own hard
    PASS/FAIL gate elsewhere in this pipeline: never fabricate, fail loud."""

    def __init__(self, verdict: str):
        super().__init__("§6A audit did not PASS")
        self.verdict = verdict


class BilingualGap(Exception):
    """One or more sections carry only ONE language.

    pp_verify's `--require-bilingual` asks whether the WHOLE .docx contains
    Cyrillic and Latin anywhere, which a single Macedonian word in a
    forty-page English document satisfies. Every real bilingual failure this
    pipeline can produce is per-SECTION — an agent drafts section 5 in English
    only while sections 1-4 carry both — and the document-wide check passes it
    without comment. Checked here, where sections are still separate.
    """

    def __init__(self, gaps: list[str]):
        super().__init__("sections are not bilingual: " + ", ".join(gaps))
        self.gaps = gaps


# Letters only. Digits, punctuation and the [[FORM]]/[[TABLE]] markers say
# nothing about language.
_CYR = re.compile(r"[Ѐ-ӿ]")
_LAT = re.compile(r"[A-Za-z]")
# TWO thresholds, deliberately, because they answer different questions. A
# single one is wrong in a way that is easy to miss: Macedonian renders longer
# than its English equivalent, so an ordinary short bilingual section sits at
# something like 52 Cyrillic / 31 Latin letters. Judged against one shared
# floor, that section is "missing English" and FAILS a perfectly good job —
# worse than the gap the check exists to close.
#
# _MIN_TOTAL_TO_JUDGE: below this much text there is nothing to be confident
# about, and a bare [[FORM:grid]], a formula or a code reference is
# legitimately language-neutral. Skip the section entirely.
_MIN_TOTAL_TO_JUDGE = 120
# _MIN_PRESENCE: above the total floor, this much of a language counts as
# present. Low on purpose — a real heading or clause clears it easily, while a
# stray acronym or unit symbol ("pH", "HPLC", "mg") does not.
_MIN_PRESENCE = 15


def _bilingual_gaps(sections: list[dict]) -> list[str]:
    """Return the numbers of sections that carry substantial text in only one
    of the two languages. Sections too short to judge are skipped — see
    _MIN_TOTAL_TO_JUDGE."""
    gaps = []
    for s in sections:
        body = s.get("content") or ""
        cyr, lat = len(_CYR.findall(body)), len(_LAT.findall(body))
        if cyr + lat < _MIN_TOTAL_TO_JUDGE:
            continue
        if cyr < _MIN_PRESENCE:
            gaps.append(f"{s.get('num', '?')} (no MK)")
        elif lat < _MIN_PRESENCE:
            gaps.append(f"{s.get('num', '?')} (no EN)")
    return gaps


_VERDICT_LINE = re.compile(r"\bverdict\b[\s:*_`-]*\**\s*(PASS|FIX)\b", re.I)
_BARE_VERDICT = re.compile(r"^[\s*#_`>-]*(PASS|FIX)\b", re.I)


def _qa_verdict(text: str) -> str:
    """PASS, FIX or "" from the auditor's free text.

    The verdict is the LAST "Verdict: X" in the reply, else the last line that opens with PASS or FIX.
    The first word is not the verdict: a live auditor opens with "I'll review the assembled document…"
    and states "Verdict: FIX" further down. Judged on the first word, every reply — a clean PASS
    included — read as not-PASS, so no document could ever reach the build (found 10.10.2026)."""
    t = text or ""
    found = _VERDICT_LINE.findall(t)
    if found:
        return found[-1].upper()
    bare = [m.group(1) for ln in t.splitlines() if (m := _BARE_VERDICT.match(ln))]
    return bare[-1].upper() if bare else ""


def _qa_audit_passed(verdict: str) -> bool:
    return _qa_verdict(verdict) == "PASS"


# The engine's Markdown, stated once for authors, repairers and the auditor alike. It is what
# pp-document-suite/scripts/build_from_md.py parse() reads — nothing more. Authors and the auditor
# previously worked from a looser description, and the auditor demanded constructs the parser does
# not have while authors wrote Markdown pipe tables the parser prints as text.
ENGINE_GRAMMAR = """ENGINE MARKDOWN (the only grammar the formatter reads):
- Every prose line and every bullet is ONE line: Macedonian ||| English (three pipes). Bullets start with "- ".
- Subsections: "## N.M Македонски наслов | English title", numbered inside this section (e.g. ## 6.1 …).
  Never write this section's own heading, and never a single "#" heading — the pipeline adds it.
- Tables: a line [[TABLE]], then one row per line with cells separated by |||; the first row is the
  header; inside a cell write Macedonian~~English; close with [[/TABLE]]. Never Markdown pipe tables
  (| a | b |) and never separator rows (|---|).
- Forms (write-in fields): [[FORM]] … [[/FORM]], one field per line: Label MK~~Label EN ||| value
  (the value stays blank for a human).
- Only document content: no notes to yourself, no restating of the brief, no explanation of what the
  section does or what you are about to do."""

# Where a reference may come from. Authors kept naming plausible regulations no passage or brief
# supported (GLP, ICH Q7 — an API guideline — in a finished-product SOP, Annex 11 technical claims);
# found by the auditor in live runs 10.10.2026.
REFERENCE_RULE = """REFERENCES: name a regulation, guideline, standard or pharmacopoeia text ONLY if it is in the
content brief or in a regulatory finding supplied to you. Any other reference you believe applies goes in the
section's LAST numbered subsection, '## N.M За потврда | To be confirmed', as 'MK ||| EN' bullets — never
presented as a normative basis. Never cite a document
whose scope excludes this procedure (e.g. ICH Q7 covers active substances, not finished product)."""

_PIPE_TABLE = re.compile(r"^\s*\|.*\|\s*$")
_H1 = re.compile(r"^#\s")
_HNUM = re.compile(r"^#+\s*([0-9]+)(?:\.[0-9]+)*\.?\s")
_META = re.compile(
    r"\b(the (content )?brief|i must|i will|i'll|i have|i've|let me|"
    r"this section (covers|is|must|should|lists|names|contains)|"
    r"section \d+(\.\d+)? (covers|is|must|should|lists|names|contains))\b", re.I)
_LETTERS = re.compile(r"[A-Za-zЀ-ӿ]")
# A word with Cyrillic AND Latin letters is a typo the eye cannot see ("двoстепен" with a Latin o) — found live.
_MIXED = re.compile(r"\b(?=\w*[Ѐ-ӿ])(?=\w*[A-Za-z])\w+\b")


def _strip_own_heading(num: str, mk: str, en: str, content: str) -> str:
    """Drop single-# heading lines that repeat this section's own heading (the pipeline writes it).
    Observed live: "# 2.0 ПОДРАЧЈЕ…|SCOPE", notes, then "# 2 ПОДРАЧЈЕ…|SCOPE" again inside section 2."""
    major = num.split(".")[0]
    keep = []
    for ln in content.splitlines():
        s = ln.strip()
        if _H1.match(s):
            m = _HNUM.match(s)
            if (m and m.group(1) == major) or mk.lower() in s.lower() or en.lower() in s.lower():
                continue
        keep.append(ln)
    return "\n".join(keep).strip()


def _lint_section(content: str, sop: bool = True) -> list[str]:
    """Grammar problems a parser-level reading can prove, as instructions an author can act on."""
    pipe = h1 = 0
    mixed = sorted(set(_MIXED.findall(content)))
    mono: list[str] = []
    meta: list[str] = []
    in_block = False
    for ln in content.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith(("[[TABLE", "[[FORM", "[[BOX")):
            in_block = True
            continue
        if s.startswith("[[/"):
            in_block = False
            continue
        if s.startswith(("[[PAGEBREAK", "[[NEWPAGE")):
            continue
        if _PIPE_TABLE.match(s) and "|||" not in s:
            pipe += 1
            continue
        if s.startswith("#"):
            in_block = False
            if sop and _H1.match(s):
                h1 += 1
            if _META.search(s):
                meta.append(s[:90])
            continue
        if _META.search(s):
            meta.append(s[:90])
        if not in_block and "|||" not in s and len(_LETTERS.findall(s)) >= 15:
            mono.append(s[:90])
    issues = []
    if pipe:
        issues.append(f"{pipe} line(s) are Markdown pipe tables (| a | b |) — rewrite them as "
                      "[[TABLE]] … [[/TABLE]] (or [[FORM]] for write-in fields) with ||| between cells")
    if h1:
        issues.append(f"{h1} single-'#' heading(s) — do not write the section heading; subsections use '## N.M MK | EN'")
    if mono:
        issues.append(f"{len(mono)} prose line(s) are not 'Macedonian ||| English', e.g. "
                      + " / ".join(f'"{x}"' for x in mono[:3]))
    if mixed:
        issues.append("words mixing Cyrillic and Latin letters (retype them in one alphabet): "
                      + ", ".join(mixed[:8]))
    if meta:
        issues.append("working notes or commentary in the body (delete them), e.g. "
                      + " / ".join(f'"{x}"' for x in meta[:3]))
    return issues


_SEC_REF = re.compile(r"(?:§\s*|\b[Ss]ections?\s+|\b[Сс]екциј[аи]\s+)([1-9])(?:\.[0-9]+)*|\b([1-9])\.[0-9]+\b")


def _sections_named(audit: str, nums: list[str]) -> list[str]:
    """The sections a FIX verdict talks about; all of them when it names none."""
    majors = {a or b for a, b in _SEC_REF.findall(audit or "")}
    named = [n for n in nums if n.split(".")[0] in majors]
    return named or list(nums)


def _strip_fences(text: str) -> str:
    return _MD_FENCE.sub("", text or "").strip()


def _clean_section(text: str, structured: bool = False) -> str:
    """Strip code fences AND any leading agent commentary from a section body.

    structured=True (annex/form bodies, which always contain a heading or a
    [[FORM]]/[[TABLE]] marker): drop everything before the first structural
    token — anything prior is preamble. structured=False (SOP prose sections,
    legitimately plain text with no heading): only peel conversational lead-in
    lines off the top, so real prose is never lost."""
    t = _strip_fences(text)
    if not t:
        return t
    if structured:
        m = _STRUCT.search(t)
        if m:
            return t[m.start():].strip()
    # peel leading conversational lines (and the blank lines between them)
    lines = t.split("\n")
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if s == "" or _PREAMBLE.match(s):
            i += 1
            continue
        break
    cleaned = "\n".join(lines[i:]).strip() or t
    # Bound the strip, and SAY when it fires. The §5A fidelity check compares
    # the built .docx against this already-cleaned text, so anything removed
    # here is invisible to the one safeguard meant to catch content
    # impoverishment. A removal past the absolute cap is not a lead-in, so the
    # original is kept and the section goes through with the (harmless) chatter
    # rather than silently losing procedure text.
    #
    # Absolute cap ONLY — a proportional one was tried and dropped, because on
    # a short section a single legitimate lead-in line is a large share of the
    # body and would be wrongly kept. Note this path is not reached in
    # structured mode when a heading/[[FORM]] marker was found: there the
    # boundary is unambiguous and the strip returns above, uncapped.
    removed = len(t) - len(cleaned)
    if removed > 0:
        too_big = removed > _MAX_PREAMBLE_CHARS
        log.info("preamble strip removed %d/%d chars%s", removed, len(t),
                 " — REFUSED (too large to be a lead-in), keeping original" if too_big else "")
        if too_big:
            return t
    return cleaned


def _brief(questionnaire_key: str, answers: dict) -> str:
    lines = [f"Questionnaire: {questionnaire_key}"]
    for k, v in answers.items():
        lines.append(f"- {k}: {', '.join(v) if isinstance(v, list) else v}")
    return "\n".join(lines)


def assemble_markdown(meta: dict, sections: list[dict]) -> str:
    """Assemble the HEADERDATA block + section bodies into engine Markdown."""
    # A literal "-->" in a meta value would be mistaken for the HEADERDATA
    # block's own terminator by build_from_md.py's parser, truncating the
    # header and leaking the remaining fields into the document body. Reject
    # rather than silently strip/sanitize — fail loud, never ship a
    # corrupted controlled document.
    for _k in ("title_mk", "title_en", "code", "version", "doctype", "orient"):
        _v = meta.get(_k)
        if _v and "-->" in str(_v):
            raise ValueError(f"meta.{_k} may not contain '-->' (breaks the HEADERDATA block terminator)")
    hd = (
        "<!--HEADERDATA\n"
        f"mk_title: {meta['title_mk']}\n"
        f"en_title: {meta['title_en']}\n"
        f"code: {meta['code']}\n"
        f"version: {meta.get('version', '1.0')}\n"
        f"doctype: {meta['doctype']}\n"
        f"orient: {meta.get('orient', 'portrait')}\n"
        "-->\n"
    )
    body = []
    for s in sections:
        body.append(f"# {s['num']} {s['mk']}|{s['en']}")
        body.append(s["content"].strip())
        body.append("")
    return hd + "\n".join(body)


async def run_workflow(job_id: str, client: LettaClient | None = None, rag: RagflowClient | None = None) -> None:
    """The full Mode-A + Mode-B pipeline for one job. Never raises: every
    failure lands in the job row as status=failed — with the draft, the
    regulatory findings and the audit kept, so a failed run can be reviewed."""
    client = client or LettaClient()
    rag = rag or RagflowClient()
    knowledge = {"ragflow": rag.configured, "examples_used": 0, "notes": []}
    # Everything a reviewer needs from a run, kept whether it ends done or failed.
    ctx: dict = {"knowledge": knowledge, "lint": {}, "qa_rounds": 0}

    async def examples_for(query: str) -> str:
        # Approved house documents, when that dataset exists: structure and style only.
        if not (rag.configured and settings.ragflow_example_datasets):
            return ""
        try:
            ex = await rag.retrieve(query, settings.ragflow_example_datasets, top_n=3)
        except RagflowError as e:
            knowledge["notes"].append(f"examples unavailable: {e}")
            return ""
        knowledge["examples_used"] += len(ex)
        return ("\n\n" + EXAMPLES_NOTE + "\n" + format_passages(ex, tag="E", max_chars=1500)) if ex else ""

    async def ask(agent_name: str, tag: str, prompt: str) -> str:
        """One exchange on a fresh clone of a fleet agent, deleted afterwards.

        A clone is built from agents/fleet.yaml (house rules + persona) on the base agent's model,
        so an instruction change in fleet.yaml reaches every exchange — ensure_fleet never edits an
        agent that already exists — and no exchange inherits another's conversation."""
        from .fleet import spawn_ephemeral  # late import: fleet needs live Letta (and is patched in tests)

        tmp_id = await spawn_ephemeral(client, agent_name, f"{job_id[:8]}_{tag}")
        try:
            return await client.send_message(tmp_id, prompt)
        finally:
            # Broad catch on purpose: cleanup of a throwaway clone must never abort the job —
            # delete_agent can also raise plain httpx transport errors, and an orphaned tmp agent
            # is harmless (the next fleet audit sweeps _tmp_ leftovers) while a failed job isn't.
            try:
                await client.delete_agent(tmp_id)
            except Exception as e:  # noqa: BLE001
                log.warning("failed to delete ephemeral %s: %s", tmp_id, e)

    try:
        job = await db.job_get(job_id)
        p = job["payload"]
        qkey = p["questionnaire"]
        meta = p["meta"]
        answers = apply_defaults(qkey, p.get("answers", {}))
        doctype = QUESTIONNAIRES[qkey]["doctype"]
        meta["doctype"] = doctype
        sop = doctype == "SOP"
        brief = _brief(qkey, answers)
        await db.job_update(job_id, status="running", stage="generate")

        from .fleet import ensure_fleet  # late import: fleet needs live Letta

        await ensure_fleet(client)   # the base agents the clones copy their model from

        def author_of(s: dict) -> str:
            if not sop:
                return "gf_annex_author"
            return "gf_raci_specialist" if s["num"] == "3.0" else "gf_sop_author"

        def tidy(s: dict, text: str) -> str:
            body = _clean_section(text, structured=not sop)
            return _strip_own_heading(s["num"], s["mk"], s["en"], body) if sop else body

        async def lint_and_repair(s: dict) -> None:
            """Proven grammar problems go back to the author before anyone audits the document."""
            issues = _lint_section(s["content"], sop)
            for r in range(settings.lint_repair_rounds):
                if not issues:
                    break
                text = await ask(author_of(s), f"l{r + 1}_{s['num'].replace('.', '')}",
                    f"Rewrite section {s['num']} {s['mk']}|{s['en']} of '{meta['title_mk']} | {meta['title_en']}' "
                    f"(code {meta['code']}) so that it follows the engine grammar. Problems found:\n- "
                    + "\n- ".join(issues) + f"\n\n{ENGINE_GRAMMAR}\n\nKeep the content; change only the form. "
                    "Return ONLY the corrected section body — your reply is inserted verbatim.\n\n"
                    f"CURRENT SECTION\n{s['content']}")
                s["content"] = tidy(s, text)
                issues = _lint_section(s["content"], sop)
            if issues:
                ctx["lint"][s["num"]] = issues

        # ---- section generation ----
        sections: list[dict] = []
        if sop:
            for num, mk, en in SOP_SECTIONS:
                s = {"num": num, "mk": mk, "en": en}
                ex = await examples_for(f"SOP section {num} {en}: {meta['title_en']}")
                text = await ask(author_of(s), num.replace(".", ""),
                    f"Draft ONLY section {num} {mk}|{en} of the SOP "
                    f"'{meta['title_mk']} | {meta['title_en']}' (code {meta['code']}). "
                    f"Content brief:\n{brief}\n\n{ENGINE_GRAMMAR}\n\n{REFERENCE_RULE}\n\n"
                    "Return ONLY the bilingual Markdown body — no code fences, and NO commentary, "
                    "preamble, or explanation of what you are doing. Your entire reply is inserted "
                    "verbatim into the document. Unknown facility specifics stay as blank fields." + ex)
                s["content"] = tidy(s, text)
                await db.job_update(job_id, stage=f"generate {num}")
                await lint_and_repair(s)
                sections.append(s)
        else:
            s = {"num": "1.0", "mk": "СОДРЖИНА", "en": "CONTENT"}
            ex = await examples_for(f"{doctype} {meta['title_en']}")
            text = await ask("gf_annex_author", "10",
                f"Design the {doctype} '{meta['title_mk']} | {meta['title_en']}' "
                f"(code {meta['code']}). Content brief:\n{brief}\n\n{ENGINE_GRAMMAR}\n\n{REFERENCE_RULE}\n\n"
                "Use [[FORM:grid]] for the metadata block and [[TABLE]] for data grids. Blank "
                "write-in values. Return ONLY the bilingual Markdown body — NO commentary, preamble, "
                "or explanation; your entire reply is inserted verbatim into the document." + ex)
            s["content"] = tidy(s, text)
            await lint_and_repair(s)
            sections.append(s)

        # ---- per-section regulatory check, concurrent ----
        # Each section gets its OWN short-lived agent: a single persistent checker accumulates every
        # prior section + passage into its prompt and blew the context window by section 8-9 (observed
        # live, twice). The checks are independent, so they run side by side — sequentially they were
        # 13 of a 16-minute run (10.10.2026). The stage counts completed checks, so it only moves forward.
        await db.job_update(job_id, stage="regulatory-check")
        reg_sources: dict[str, list] = {}
        sem = asyncio.Semaphore(settings.reg_concurrency)
        done = 0

        async def check(s: dict) -> str:
            nonlocal done
            async with sem:
                # RAGFlow DB01 first: the checker gets the actual passages and cites them by [R#]; the job
                # keeps which passage each [R#] was. Without RAGFlow (or if it fails) the checker searches
                # its attached Letta sources, and the job says so.
                passages: list[dict] = []
                if rag.configured:
                    try:
                        passages = await rag.retrieve(
                            f"{meta['title_en']} — {s['en']}: {s['content'][:800]}", settings.ragflow_reg_datasets)
                    except RagflowError as e:
                        knowledge["notes"].append(f"[{s['num']}] regulatory corpus unavailable, Letta sources used: {e}")
                if passages:
                    prompt = (f"Check this drafted section {s['num']} of {meta['code']} against the "
                              "regulatory passages below, retrieved from the RAGFlow DB01 library. Cite "
                              "only these passages, as [R#] with the document and clause; say NO-FINDING "
                              f"if none applies.\n\nPASSAGES\n{format_passages(passages)}\n\nSECTION\n{s['content']}")
                    reg_sources[s["num"]] = citations(passages)
                else:
                    prompt = (f"Check this drafted section {s['num']} of {meta['code']} against the "
                              f"regulatory corpus ({', '.join(settings.reg_sources)}). Cite only "
                              f"retrieved passages; say NO-FINDING if nothing applies.\n\n{s['content']}")
                finding = await ask("gf_reg_checker", s["num"].replace(".", ""), prompt)
            done += 1
            await db.job_update(job_id, stage=f"regulatory-check {sections[done - 1]['num']}")
            return f"[{s['num']}] {finding.strip()}"

        outcomes = await asyncio.gather(*(check(s) for s in sections), return_exceptions=True)
        for o in outcomes:
            if isinstance(o, BaseException):
                raise o
        reg_findings: list[str] = list(outcomes)
        ctx.update(regulatory=reg_findings, regulatory_sources=reg_sources)

        # ---- bilingual gate + §6A audit, with repair rounds ----
        # The gate is per section and comes BEFORE the audit and the build: both of those see the
        # assembled document, where pp_verify's document-wide --require-bilingual is satisfied by any
        # Cyrillic anywhere.
        findings_txt = "\n".join(f[:1200] for f in reg_findings)
        audit = ""
        for rnd in range(settings.qa_repair_rounds + 1):
            await db.job_update(job_id, stage="bilingual-check")
            gaps = _bilingual_gaps(sections)
            if gaps:
                ctx["markdown"] = assemble_markdown(meta, sections)
                raise BilingualGap(gaps)
            await db.job_update(job_id, stage="qa-audit" if rnd == 0 else f"qa-audit repair-{rnd}")
            markdown = assemble_markdown(meta, sections)
            ctx["markdown"] = markdown
            audit = await ask("gf_qa_auditor", f"qa{rnd}",
                f"Run the §6A review of this assembled document ({meta['code']}).\n\n"
                f"Judge its Markdown only against this grammar — do not require constructs it does not define:\n{ENGINE_GRAMMAR}\n"
                "The '# N.0 MK|EN' section headings and the <!--HEADERDATA--> block in the DOCUMENT are "
                "written by the pipeline and are correct — do not flag them; judge the authored content "
                "under each heading. A reference listed under 'За потврда | To be confirmed' is not a "
                "finding; a reference presented as a normative basis must be in the brief or the findings.\n\n"
                "CONTENT BRIEF (the questionnaire answers; regulatory references in it are pre-verified "
                f"by the questionnaire and count as supported):\n{brief}\n\n"
                "REGULATORY CHECK FINDINGS, per section ([R#] = a passage retrieved from RAGFlow DB01):\n"
                f"{findings_txt}\n\n"
                "List concrete, actionable issues per section. End your reply with one final line, "
                "exactly 'VERDICT: PASS' or 'VERDICT: FIX'.\n\nDOCUMENT\n" + markdown)
            ctx.update(qa_audit=audit, qa_verdict=_qa_verdict(audit), qa_rounds=rnd)
            if _qa_audit_passed(audit):
                break
            if rnd == settings.qa_repair_rounds:
                if not settings.fix_to_review:
                    raise QaAuditFailed(audit)
                ctx["review_reason"] = (f"§6A FIX after {rnd} repair round(s): the auditor's remaining "
                                        "issues are in qa_audit; a person decides")
                break
            # Send the named sections back to their authors with the auditor's text.
            named = set(_sections_named(audit, [x["num"] for x in sections]))
            for s in sections:
                if s["num"] not in named:
                    continue
                await db.job_update(job_id, stage=f"qa-audit repair-{rnd + 1}")
                text = await ask(author_of(s), f"r{rnd + 1}_{s['num'].replace('.', '')}",
                    f"REVISE section {s['num']} {s['mk']}|{s['en']} of '{meta['title_mk']} | {meta['title_en']}' "
                    f"(code {meta['code']}). A reviewer returned FIX for the assembled document. Fix every "
                    f"issue the review raises about section {s['num']}, and anything in it a document-wide "
                    "issue affects; ignore issues that belong only to other sections; keep what was not "
                    "criticised. Facts you do not have stay as blank fields — never invent data or citations.\n\n"
                    f"Content brief:\n{brief}\n\n{ENGINE_GRAMMAR}\n\n{REFERENCE_RULE}\n\n"
                    f"REGULATORY FINDINGS (retrieved passages, citable):\n{findings_txt}\n\nREVIEW\n{audit}\n\n"
                    f"CURRENT SECTION {s['num']}\n{s['content']}\n\n"
                    "Return ONLY the corrected section body — your reply is inserted verbatim.")
                s["content"] = tidy(s, text)
                await lint_and_repair(s)

        # ---- format + verify (hard gate — a review never skips it) ----
        await db.job_update(job_id, stage="format")
        # H14 — builder.build is fully synchronous (docx render + verify, tens of seconds); called bare
        # it blocked the event loop, stalling every request this worker serves, including the polls.
        result = await asyncio.to_thread(
            builder.build, ctx["markdown"], settings.out_dir, meta["code"]
        )
        if ctx.get("review_reason"):
            # Built and verified, NOT registered: POST /workflows/{id}/review approves (registers) or returns it.
            await db.job_update(
                job_id, status="awaiting_review", stage="format",
                result={**ctx, "verify": result.verify_report, "bytes": result.bytes,
                        "artifact": {"path": str(result.path), "bytes": result.bytes}},
            )
            return
        did = await db.document_create(
            job_id,
            {
                "code": meta["code"], "doctype": doctype,
                "title_mk": meta["title_mk"], "title_en": meta["title_en"],
                "version": meta.get("version", "1.0"),
                "path": str(result.path), "bytes": result.bytes,
                "verify": result.verify_report,
            },
        )
        await db.job_update(
            job_id, status="done", stage="done",
            result={**ctx, "document_id": did, "verify": result.verify_report, "bytes": result.bytes},
        )
    except builder.VerifyFailed as e:
        log.error("job %s verify FAILED", job_id)
        await db.job_update(job_id, status="failed", error="verify FAILED",
                            result={**ctx, "verify": e.report})
    except QaAuditFailed as e:
        log.error("job %s §6A audit did not pass", job_id)
        await db.job_update(job_id, status="failed", error="§6A audit did not pass",
                            result={**ctx, "qa_audit": e.verdict, "qa_verdict": _qa_verdict(e.verdict) or "FIX"})
    except BilingualGap as e:
        log.error("job %s bilingual gap: %s", job_id, e.gaps)
        await db.job_update(job_id, status="failed",
                            error="sections are not bilingual: " + ", ".join(e.gaps),
                            result={**ctx, "bilingual_gaps": e.gaps})
    except LettaError as e:
        log.error("job %s letta error: %s", job_id, e)
        await db.job_update(job_id, status="failed", error=f"letta: {e}", result=ctx)
    except Exception as e:  # noqa: BLE001 — job must record any failure
        log.exception("job %s failed", job_id)
        # Some exceptions (notably httpx.ReadTimeout) stringify to "" — always
        # record the type name so the job row never shows a blank error.
        detail = str(e).strip() or repr(e)
        await db.job_update(job_id, status="failed", error=f"{type(e).__name__}: {detail}"[:500], result=ctx)
