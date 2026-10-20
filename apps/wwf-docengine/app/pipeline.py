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

from . import builder, db, glossary, house, potency
from .config import settings
from .house_codes import XXX
from .letta import LettaClient, LettaError
from .ragflow import RagflowClient, RagflowError, citations, format_passages
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

# No length target. Head of QC, 11.10.2026: a page or word limit "will probably sometimes cut on very
# important content", or pad a short procedure — length is a result of the content. What is controlled is
# redundancy: the authors state each requirement once, and the §6A audit flags repetition and padding.
CONCISE = ("Write only what the procedure needs: every requirement once, no repetition of another section, "
           "no explanation of why a rule exists unless the brief asks for it, no filler.")
# Annexes are separate documents. Head of QC, 13.10.2026, after run 6fb3e246: one run wrote the annex forms into 7.0,
# the next listed them and claimed they were "attached at the end" — they were not. The SOP names its annexes; each
# annex is its own controlled document made by its own annex job (EU GMP Ch. 4 §4.1: instructions and records apart).
ANNEX_RULE = ("Annexes (forms, logs, checklists, labels) are separate controlled documents, each made by its own "
              "annex job: the SOP names each one by code and title, says in section 6 when it is completed, and "
              "never writes a form's fields into the SOP nor says that annexes are attached or appended.")
# Rules for an executable form (annex). 13.10.2026 review of the DEMO annexes: every generated form printed
# its open questions and a reference list on the page that will be filled in, and duplicated the header data
# as write-ins.
FORM_RULE = ("An executable form carries only what is filled in or ticked: no 'To be confirmed' section, no "
             "reference list, no explanation; the document code, version and date are in the header and are not "
             "repeated as write-in fields; every value cell is blank; where the parent SOP uses a transport or "
             "record identifier, the form has a field for it in the SOP's format.")


def controls_rule(questionnaire_key: str) -> str:
    """The controls a questionnaire declares for its SOP, as prompt text; empty when it declares none."""
    ctl = QUESTIONNAIRES.get(questionnaire_key, {}).get("controls") or []
    if not ctl:
        return ""
    return ("CONTROLS THIS SOP MUST CONTAIN — each in the section it belongs to, none omitted; where a value is "
            "unknown write a blank and mark it to be confirmed:\n" + "\n".join(f"- {c}" for c in ctl))


def _parent_sections(markdown: str, first: int = 6, last: int = 7, limit: int = 30000) -> str:
    """Sections `first`..`last` of an assembled SOP (the procedure and its records), for an annex job.

    Over `limit`, the earlier sections are shortened and the last (section 7, the records register the form
    must match) is kept whole. A plain cut at 14 000 characters dropped all of section 7 from WHSOP_003, whose
    sections 6 and 7 run to 27 000, while the prompt told the author to use "the completers section 7 names"
    (review 14.10.2026)."""
    parts: dict[int, list[str]] = {}
    cur = None
    for ln in markdown.splitlines():
        m = re.match(r"^# (\d)\.0", ln)
        if m:
            cur = int(m.group(1)) if first <= int(m.group(1)) <= last else None
        if cur is not None:
            parts.setdefault(cur, []).append(ln)
    blocks = ["\n".join(parts[k]) for k in sorted(parts)]
    if not blocks:
        return ""
    whole = "\n".join(blocks)
    if len(whole) <= limit:
        return whole
    tail = blocks[-1][:limit]
    room = max(0, limit - len(tail) - 80)
    head = "\n".join(blocks[:-1])[:room]
    return (head + "\n[… shortened for length …]\n" if head else "") + tail


SECTION_HINT = {
    "7.0": "List the records in 7.1 by code and title, with who completes and who keeps each. " + ANNEX_RULE,
    "8.0": "List the related documents by code and title; do not repeat the annex list of 7.1.",
    "9.0": "Give the revision history.",
}


# Fence lines anywhere in a reply. The old pattern (^```lang\n|\n```$) consumed the newline the closing fence
# needed, so a fence-only reply ("```markdown\n```") came out as the literal "```" and replaced a section.
_MD_FENCE = re.compile(r"^[ \t]*```[\w-]*[ \t]*$\n?", re.M)

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


class JobAborted(Exception):
    """The row was failed by the stale-job reaper while this worker was still running it: nothing more is written."""


class LintUnresolved(Exception):
    """Proven grammar problems survived every repair round and review parking is off."""

    def __init__(self, sections: str):
        super().__init__(f"grammar problems remain in {sections}")


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
# The line the prompt asks for: "VERDICT: PASS" / "VERDICT: FIX" on its own, markup allowed.
_FINAL_VERDICT = re.compile(r"^[\s*#_`>-]*verdict[\s:*_`-]*(PASS|FIX)[\s*_`.!]*$", re.I)
# A bare verdict word only when it stands alone or opens "FIX: …" — never "Pass/fail criteria are missing".
_BARE_VERDICT = re.compile(r"^[\s*#_`>-]*(PASS|FIX)(?:[\s*_`.!]*$|\s*:)", re.I)


def _qa_verdict(text: str) -> str:
    """PASS, FIX or "" from the auditor's free text.

    1. The reply's last non-empty line, when it is the "VERDICT: X" line the prompt asks for.
    2. Otherwise every "Verdict: X" in the text: FIX if any of them is FIX, else PASS.
    3. Otherwise lines that are only PASS/FIX (or open with "FIX:"): FIX if any is FIX, else PASS.
    The first word is not the verdict: a live auditor opens with "I'll review the assembled document…"
    (found 10.10.2026). And a PASS must never be read out of prose: the old fallback took any line opening
    with the word, so "- Pass/fail criteria are missing" was a PASS, and "Verdict: FIX … once fixed, the
    verdict: PASS" was a PASS — either registered a FIX document as done with no person (review 14.10.2026)."""
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    if lines and (m := _FINAL_VERDICT.match(lines[-1])):
        return m.group(1).upper()
    for found in ([v.upper() for v in _VERDICT_LINE.findall(text or "")],
                  [m.group(1).upper() for ln in lines if (m := _BARE_VERDICT.match(ln))]):
        if found:
            return "FIX" if "FIX" in found else "PASS"
    return ""


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
- Forms (write-in fields): [[FORM]] … [[/FORM]], one field per line, three cells:
  Label MK ||| Label EN ||| value  (the value stays blank for a human; no ~~ in a form row).
- Only document content: no notes to yourself, no restating of the brief, no explanation of what the
  section does or what you are about to do."""

# Where a reference may come from. Authors kept naming plausible regulations no passage or brief
# supported (GLP, ICH Q7 — an API guideline — in a finished-product SOP, Annex 11 technical claims);
# found by the auditor in live runs 10.10.2026.
REFERENCE_RULE = """REFERENCES: name a regulation, guideline, standard or pharmacopoeia text ONLY if it is in the
content brief or in a regulatory finding supplied to you; name a house SOP, annex or form ONLY from the list of house
documents in use in the content brief, by code and version. Any other reference you believe applies goes in the
section's LAST numbered subsection, '## N.M За потврда | To be confirmed', as 'MK ||| EN' bullets — never
presented as a normative basis. Never cite a document
whose scope excludes this procedure (e.g. ICH Q7 covers active substances, not finished product)."""

_PIPE_TABLE = re.compile(r"^\s*\|.*\|\s*$")
_H1 = re.compile(r"^#\s")
_HNUM = re.compile(r"^#+\s*([0-9]+)(?:\.[0-9]+)*\.?\s")
# Working notes, not procedure. "The brief visual inspection" and "the records section 7 lists" are procedure:
# the bare "the brief" and mid-sentence "section N lists" flagged them and sent real text back for deletion
# (review 14.10.2026). Section phrases count only where the line, or its English half, opens with them.
_META = re.compile(
    r"\b(the content brief|i must|i will|i'll|i have|i've|let me)\b|"
    r"(?:^|\|\|\|\s*)(?:this section|section \d+(?:\.\d+)?) (?:covers|is|must|should|lists|names|contains)\b",
    re.I)
_LETTERS = re.compile(r"[A-Za-zЀ-ӿ]")
# Lines only our own prompts contain. Observed 13.10.2026 (transport run a142b9dd): a lint-repair reply came back as
# the whole request, then the old section, then the new one, and all of it was inserted "verbatim" into 3.0.
# Anchored to our own sentences: "Return ONLY the signed copy to QA" is procedure (review 14.10.2026).
_ECHO = re.compile(r"Return ONLY the (?:corrected|bilingual)|^CURRENT SECTION\s*$|ENGINE MARKDOWN \(the only grammar|"
                   r"^(?:Rewrite|REVISE|Draft ONLY) section \d", re.M)


def _echoes_prompt(text: str) -> bool:
    return bool(_ECHO.search(text or ""))
# A word with Cyrillic AND Latin letters is a typo the eye cannot see ("двoстепен" with a Latin o) — found live.
_MIXED = re.compile(r"\b(?=\w*[Ѐ-ӿ])(?=\w*[A-Za-z])\w+\b")


def _strip_own_heading(num: str, mk: str, en: str, content: str) -> str:
    """Drop single-# heading lines that repeat this section's own heading (the pipeline writes it).
    Observed live: "# 2.0 ПОДРАЧЈЕ…|SCOPE", notes, then "# 2 ПОДРАЧЈЕ…|SCOPE" again inside section 2.

    Only the section's OWN heading: numbered "N" or "N.0", or unnumbered and naming the section's title as a
    whole word. A subsection an author wrote with one '#' ("# 6.3 Stage 2") is kept, so the linter can send it
    back as '## 6.3'; it used to be deleted here, before the linter could see it. A title is matched as a word,
    not a substring: "ЦЕЛ" is not "Целосна листа", and a heading is dropped only when it is nothing but the
    title — "# Receipt procedure | Постапка за прием" in section 6 is content (review 14.10.2026)."""
    major = num.split(".")[0]
    own_num = re.compile(rf"^#\s*{re.escape(major)}(?:\.0)?\.?(?:\s|$)")
    any_num = re.compile(r"^#\s*[0-9]")
    titles = {t.strip().lower() for t in (mk, en) if t.strip()}
    keep = []
    for ln in content.splitlines():
        s = ln.strip()
        if _H1.match(s):
            if own_num.match(s):
                continue
            parts = {x.strip().lower() for x in s.lstrip("#").split("|") if x.strip()}
            if not any_num.match(s) and parts and parts <= titles:
                continue          # "# ПОСТАПКА | PROCEDURE" — not "# Receipt procedure | Постапка за прием"
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
    if not _LETTERS.search(content):
        # An empty reply passed every other check (the bilingual gate skips anything under 120 letters).
        return ["the section is empty — write its content"]
    if not sop and re.search(r"(?im)^#{1,3}.*(За потврда|To be confirmed)", content):
        issues.append("a 'To be confirmed' section on an executable form — delete it; open points go to the requester, "
                      "not onto the form that will be filled in")
    if _echoes_prompt(content):
        issues.append("the request text was copied into the section — delete everything that is not document content")
    if sop and "[[FORM" in content:
        issues.append("a write-in form ([[FORM]]) inside the SOP — forms are separate annexes: name the annex by "
                      "code and title instead (keep tables as [[TABLE]])")
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
    terms = glossary.term_issues(content)
    if terms:
        issues.append("Macedonian terms outside the house glossary (replace them everywhere): " + ", ".join(terms[:8]))
    return issues


_SEC_REF = re.compile(r"(?:§\s*|\b[Ss]ections?\s+|\b[Сс]екци(?:ја|и|ите)\s+)([1-9](?:\.[0-9]+)*"
                      r"(?:\s*(?:,|and|&|и|/)\s*[1-9](?:\.[0-9]+)*)*)")
# A bare "N.M" is a section only where the text points at one: opening a line or a bullet ("- 5.2: …", the auditor's
# per-section list) or after see / in / at / under. A decimal followed by a unit is a quantity. "The limit is 2.5 kg
# and 0.5 % per 3.0 mL" sent sections 2 and 3 back for a rewrite (review 19.10.2026).
_UNIT = r"(?!\s*(?:%|kg|g|mg|µg|mL|ml|L|°C|mm|cm|m|h|hours?|hrs?|min|minutes?|s|sec|seconds?|days?)\b)"
_BARE_REF = re.compile(r"(?:^|[-*•]\s+|\b(?:see|in|at|under|види|во)\s+)\s*([1-9])\.[0-9]+(?!\.?\d)" + _UNIT, re.I | re.M)
# A clause of a regulation or of another document is not a section of this one. An auditor citing
# "EU GMP Chapter 4.1", "Annex 15 §6", "ICH Q9 4.1" or "A04 2.1" used to send sections 4, 6 and 2 back
# for a rewrite nobody asked for (found in review 14.10.2026). Those citations are removed first.
_CLAUSE_CITE = re.compile(
    r"(?i)(?:\b(?:annex|anhang|chapter|ch\.|part\s+[ivx]+|article|art\.|чл\.?|член|анекс|поглавје|"
    r"gdp|gmp|ich\s+q\d+(?:\(r\d\))?|q\d+(?:\(r\d\))?|usp|ph\.\s*eur\.?|who\s+trs|trs|iso|version|ver\.|v\.|rev\.?)"
    r"|\bA\d{2}\b|\b[a-z]{2,}[a-z0-9]*_[0-9a-z_]*[0-9])(?:\s+(?:of\s+)?(?:the\s+)?(?:eu\s+)?(?:gmp|gdp|guidelines?))?\s*(?:no\.?\s*)?(?:§\s*)?"
    r"\d+(?:\.\d+)*"
    r"(?:\s*§\s*\d+(?:\.\d+)*)?"                                         # "Annex 11 §4.8"
    r"(?:\s*(?:and|or|vs\.?|to|–|-|и|или)\s*(?:§\s*)?\d+(?:\.\d+)*)*")    # "A04 2.1 vs 2.2"


def _sections_named(audit: str, nums: list[str]) -> list[str]:
    """The sections a FIX verdict talks about; all of them when it names none."""
    text = _CLAUSE_CITE.sub(" ", audit or "")
    majors: set[str] = set()
    for listed in _SEC_REF.findall(text):
        majors.update(re.findall(r"(?<![.\d])([1-9])(?:\.[0-9]+)*", listed))
    majors.update(m.group(1) for m in _BARE_REF.finditer(text))
    named = [n for n in nums if n.split(".")[0] in majors]
    return named or list(nums)


def _strip_fences(text: str) -> str:
    return _MD_FENCE.sub("", text or "").strip()


_HEAD_NOSPACE = re.compile(r"^(#{1,6})(?=[0-9A-Za-zЀ-ӿ])", re.M)
_HEAD_TRIPLE = re.compile(r"^(#{1,6}\s.*?)\s*\|\|\|\s*", re.M)


def _normalise_headings(text: str) -> str:
    """Headings the engine would misprint. build_from_md splits a heading on its FIRST '|', so an author who
    writes the prose form "## 6.1 Подготовка ||| Preparation" got "6.1 Подготовка | || Preparation"; and
    "#6.2 …" without a space is not a heading to the parser but printed its '#' as text (review 14.10.2026)."""
    text = _HEAD_NOSPACE.sub(r"\1 ", text)
    return _HEAD_TRIPLE.sub(r"\1 | ", text)


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


# What an uploaded source is for (Head of QC, 19.10.2026): the authors are told, so a formatting example lends its
# layout and never its facts, and an executed example lends its structure and never its values.
SOURCE_ROLE = {
    "content": "reference contents: facts may be taken from it; cite it by this file name.",
    "format": "an example of document formatting: follow its structure, section order and layout; take no fact or "
              "value from it and do not cite it.",
    "example": "an executed (filled-in) example of this kind of document: it shows which fields are completed and "
               "how; take its structure, never its values, names, dates or results, and do not cite it.",
}


async def _house_check(ask, meta: dict, markdown: str, parent_code: str, brief: str) -> dict:
    """gf_house_checker over the documents house.checking_docs names: {checked: [{code, version, title, why}],
    verdicts: {code: {verdict, detail}}, error?}. No approved document to check against is said, not skipped."""
    try:
        docs = await house.checking_docs(meta["code"], parent_code, markdown, meta.get("title_en", ""),
                                         meta.get("title_mk", ""))
    except Exception as e:  # noqa: BLE001 — the library being unreadable is recorded and goes to a person
        return {"checked": [], "verdicts": {}, "error": f"library unavailable: {e}"[:200]}
    out = {"checked": [{k: d[k] for k in ("code", "version", "title", "why")} for d in docs], "verdicts": {}}
    if not docs:
        out["note"] = "no approved, in-use document in the library relates to this draft"
        return out
    for i, group in enumerate(house.batches(docs)):
        approved = "\n\n".join(f"=== {d['code']} v{d['version']} — {d['title']} ({d['why']}) ===\n{d['text']}" for d in group)
        try:
            reply = await ask("gf_house_checker", f"house{i}",
                f"Check the DRAFT {meta['code']} '{meta.get('title_mk', '')} | {meta.get('title_en', '')}' against each "
                f"approved, in-use document below. Answer one line per document, for exactly these codes: "
                f"{', '.join(d['code'] for d in group)}.\n\nWhat the requester decided for this draft (a change the "
                f"brief asks for is CHANGES, not CONFLICT):\n{brief[:6000]}\n\nAPPROVED DOCUMENTS\n{approved}\n\n"
                f"DRAFT\n{markdown}")
        except LettaError as e:
            out["error"] = str(e)[:200]
            reply = ""
        out["verdicts"].update(house.parse_verdicts(reply, [d["code"] for d in group]))
    return out


def _brief(questionnaire_key: str, answers: dict, instructions: str = "", sources: list | None = None,
           source_texts: list | None = None) -> str:
    lines = [f"Questionnaire: {questionnaire_key}"]
    for k, v in answers.items():
        if v in (None, "", []):
            continue              # an unanswered question with no default: printing "None" invites the author to
        lines.append(f"- {k}: {', '.join(map(str, v)) if isinstance(v, list) else v}")
    if (instructions or "").strip():
        lines += ["", "Requester's instructions:", instructions.strip()]
    srcs = [str(x).strip() for x in (sources or []) if str(x).strip()]
    if srcs:
        lines += ["", "Sources named by the requester (may be cited):"] + [f"- {x}" for x in srcs]
    # Files uploaded to the Document Brief: their text, cited by file name. Facts come from here or from the brief;
    # nothing is copied that the requester did not provide.
    for st in source_texts or []:
        if (st.get("text") or "").strip():
            lines += ["", f"SOURCE FILE «{st['name']}» — {SOURCE_ROLE.get(st.get('role') or 'content', SOURCE_ROLE['content'])}",
                      st["text"].strip()]
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
        # One HEADERDATA line per field: a line break in a value writes a field of its own ("doctype: FORM"),
        # which builder.build reads first and build_from_md reads last — the two disagree on the document.
        if _v and ("\n" in str(_v) or "\r" in str(_v)):
            raise ValueError(f"meta.{_k} may not contain a line break (it would write its own HEADERDATA line)")
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
        content = s["content"].strip()
        # A form that opens with its own '# ' heading needs no synthetic "1.0 СОДРЖИНА|CONTENT" above it
        # (13.10.2026 review: a scaffolding heading on every generated form).
        if not (meta.get("doctype") != "SOP" and content.startswith("# ")):
            body.append(f"# {s['num']} {s['mk']}|{s['en']}")
        body.append(content)
        body.append("")
    return hd + "\n".join(body)


_annex_tasks: set = set()


async def _start_package_annexes(sop_job: str, p: dict, meta: dict) -> list[dict]:
    """SOP + annexes from one workflow (Head of QC, 18.10.2026): once the SOP is written, one annex job per annex of the
    package, numbered from the register under the SOP's code, each reading the SOP's sections 6 and 7 (ANNEX_RULE)."""
    from .house_codes import next_code
    # A rebuild of the same brief reuses its own annex numbers (A01 … again, not A03 …), and an SOP whose number is
    # not confirmed (…XXX) numbers its annexes by position: no other package shares its sequence.
    unconfirmed = meta["code"].endswith(XXX)
    taken = set() if unconfirmed else set(await db.codes_in_use()) - await db.codes_of_brief(p.get("brief_id", ""))
    out = []
    for i, a in enumerate(p.get("package_annexes") or [], 1):
        code = f"{meta['code']}A{i:02d}" if unconfirmed else next_code(parent=meta["code"], taken=taken)
        taken.add(code)
        title_en, title_mk = a.get("title_en") or a.get("title_mk"), a.get("title_mk") or a.get("title_en")
        payload = {"questionnaire": "annex_form", "answers": {}, "parent_sop": meta["code"],
                   "meta": {"title_mk": title_mk, "title_en": title_en, "code": code, "version": meta.get("version", "1.0")},
                   "instructions": (p.get("instructions") or "")[:6000] + f"\n\nThis annex ({a.get('kind', 'form')}) is part of "
                                   f"the {meta['code']} package.", "sources": p.get("sources") or [],
                   "source_texts": p.get("source_texts") or [], "assumed": ["annex content (from the SOP)"],
                   "brief_id": p.get("brief_id", ""), "package_of": sop_job, "requested_by": p.get("requested_by", "")}
        jid = await db.job_create("workflow", payload, p.get("requested_by", ""))
        t = asyncio.get_running_loop().create_task(run_workflow(jid))
        _annex_tasks.add(t)                      # a task with no reference can be collected mid-run
        t.add_done_callback(_annex_tasks.discard)
        out.append({"code": code, "job_id": jid, "title_en": title_en})
    return out


async def start_package(job_id: str, p: dict, meta: dict, sop: bool) -> None:
    """Once an SOP of a package stands — registered as done here, or approved by a person in review_workflow — start
    its annexes (they read its Markdown) and record them on it. Not on awaiting_review: four annexes were written to
    an SOP the reviewer then returned (review 19.10.2026)."""
    if not (sop and p.get("package_annexes")):
        return
    try:
        extra = {"package_jobs": await _start_package_annexes(job_id, p, meta)}
    except Exception as e:  # noqa: BLE001 — the SOP stands; the annexes that did not start are reported on it
        log.exception("job %s: package annexes did not start", job_id)
        extra = {"package_error": f"{type(e).__name__}: {e}"[:300]}
    await db.job_merge_result(job_id, extra)


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
        return ("\n\n" + house.NOTE + "\n" + format_passages(ex, tag="E", max_chars=1500)) if ex else ""

    async def finish(**fields) -> bool:
        """The job's terminal write; False (and a log line) when the reaper failed the row meanwhile (review 19.10.2026)."""
        ok = await db.job_finish(job_id, **fields)
        if not ok:
            log.warning("job %s was failed by the stale-job reaper meanwhile; its late %s is not written",
                        job_id, fields.get("status"))
        return ok

    async def ask(agent_name: str, tag: str, prompt: str) -> str:
        """One exchange on a fresh clone of a fleet agent, deleted afterwards.

        A clone is built from agents/fleet.yaml (house rules + persona) on the base agent's model,
        so an instruction change in fleet.yaml reaches every exchange — ensure_fleet never edits an
        agent that already exists — and no exchange inherits another's conversation."""
        from .fleet import spawn_ephemeral  # late import: fleet needs live Letta (and is patched in tests)

        # Progress is told by updated_at alone: a long exchange (one section can take minutes) must bump it, or the
        # reaper reads a working job as abandoned; and a row the reaper did fail is left alone (review 19.10.2026).
        if await db.job_touch(job_id) == "failed":
            raise JobAborted(job_id)
        # A message that failed transiently (a timeout: the agent may still be writing; a gateway error) is not
        # re-sent to the same clone. The clone is deleted and the step repeats on a fresh one, which is safe
        # because a clone carries nothing from any other exchange. Each repeat is recorded in the job's result.
        for attempt in range(1 + max(0, settings.ask_retries)):
            suffix = f"{job_id[:8]}_{tag}" + (f"_x{attempt}" if attempt else "")
            tmp_id = await spawn_ephemeral(client, agent_name, suffix)
            try:
                return await client.send_message(tmp_id, prompt)
            except LettaError as e:
                if not e.transient or attempt >= settings.ask_retries:
                    raise
                ctx.setdefault("retries", []).append({"step": tag, "agent": agent_name, "attempt": attempt + 1,
                                                      "error": str(e)[:200]})
                log.warning("job %s: %s step %s failed transiently (%s); repeating on a fresh clone",
                            job_id, agent_name, tag, e)
            finally:
                # Broad catch on purpose: cleanup of a throwaway clone must never abort the job — an orphaned
                # tmp agent is harmless (ensure_fleet sweeps clones older than fleet.TMP_MAX_AGE).
                try:
                    await client.delete_agent(tmp_id)
                except Exception as e:  # noqa: BLE001
                    log.warning("failed to delete ephemeral %s: %s", tmp_id, e)
        raise LettaError(f"{agent_name} step {tag}: no attempt left")  # unreachable: the loop returns or raises

    try:
        job = await db.job_get(job_id)
        p = job["payload"]
        qkey = p["questionnaire"]
        meta = p["meta"]
        answers = apply_defaults(qkey, p.get("answers", {}))
        doctype = QUESTIONNAIRES[qkey]["doctype"]
        meta["doctype"] = doctype
        sop = doctype == "SOP"
        brief = _brief(qkey, answers, p.get("instructions", ""), p.get("sources") or [], p.get("source_texts") or [])
        # The approved, in-use house documents the new one may cite and must not contradict (19.10.2026).
        try:
            in_use = await house.in_use_list()
        except Exception as e:  # noqa: BLE001 — the list helps the authors; its absence is noted, not fatal
            in_use = []
            knowledge["notes"].append(f"house document list unavailable: {e}"[:200])
        if in_use:
            brief += "\n\n" + house.list_block(in_use)
            knowledge["house_documents"] = len(in_use)
        # The official potency specifications, when the document touches potency (Head of QC, 19.10.2026).
        specs = await potency.block(meta.get("title_en", ""), meta.get("title_mk", ""), brief)
        if specs:
            brief += "\n\n" + specs
            knowledge["notes"].append("potency specifications: " + ("read from the KVM4 potency builder"
                                                                    if "could not be read" not in specs else "unavailable"))
        if p.get("assumed"):
            ctx["assumed"] = p["assumed"]          # what the requester did not decide: the review report lists it
        controls = controls_rule(qkey)
        # An annex job reads the SOP it serves (sections 6 and 7) so the form captures what that SOP records in it.
        parent_code = (p.get("parent_sop") or "").strip()
        parent_md, related_md = "", ""
        if parent_code and doctype != "SOP":
            parent = None
            if p.get("package_of"):
                # An annex of a package reads the very SOP job that started it, never another job with the same code
                # (a revision being written, or another unconfirmed …XXX SOP).
                own = await db.job_get(p["package_of"])
                md = ((own or {}).get("result") or {}).get("markdown") or ""
                if md:
                    parent = {"markdown": md, "job_id": p["package_of"], "status": own["status"]}
            unconfirmed = parent is None and parent_code.endswith(XXX)
            if unconfirmed:
                # Every unconfirmed QASOPXXX shares the code: a lookup by code would read another SOP's procedure
                # into this form (review 19.10.2026). The package job is the only safe source; without it, the brief.
                knowledge["notes"].append(f"parent SOP {parent_code} is unconfirmed: give the parent job, or confirm "
                                          "the number")
            elif parent is None:
                parent = await db.job_latest_markdown_by_code(parent_code)
            if parent:
                parent_md = _parent_sections(parent["markdown"])
                knowledge["parent_sop"] = {"code": parent_code, "job_id": parent["job_id"], "status": parent["status"]}
                if parent["status"] != "done":
                    knowledge["notes"].append(f"parent SOP {parent_code} is not registered: read from job "
                                              f"{parent['job_id'][:8]} ({parent['status']})")
            elif not unconfirmed:
                try:
                    approved = await house.approved_text(parent_code)
                except Exception as e:  # noqa: BLE001
                    approved = None
                    knowledge["notes"].append(f"approved parent SOP unavailable: {e}"[:200])
                if approved:
                    # The approved copies are the Word files' text, not engine Markdown: no "# 6.0" headings to cut
                    # at, so the SOP goes whole (12 000 characters once dropped the records section of a 14 000 SOP).
                    parent_md = _parent_sections(approved["markdown"]) or approved["markdown"][:30000]
                    knowledge["parent_sop"] = {"code": parent_code, "approved_version": approved["version"],
                                               "reference_id": approved["id"]}
                    try:          # the SOP's own forms and annexes (Head of QC, 19.10.2026): written beside, not over
                        related_md, related_codes = await house.related_block(parent_code)
                    except Exception as e:  # noqa: BLE001
                        related_md, related_codes = "", []
                        knowledge["notes"].append(f"related documents of {parent_code} unavailable: {e}"[:200])
                    if related_codes:
                        knowledge["parent_sop"]["related"] = related_codes
                else:
                    knowledge["notes"].append(f"parent SOP {parent_code} not found; the form was drafted from the brief only")
        parent_note = (f"PARENT SOP {parent_code}, sections 6 and 7 — the form must hold a field for every item these "
                       f"sections write into this record, with the completers section 7 names:\n{parent_md}\n" if parent_md else "")
        if related_md:
            parent_note += "\n" + related_md + "\n"
        await db.job_update(job_id, status="running", stage="generate")

        from .fleet import ensure_fleet  # late import: fleet needs live Letta

        await ensure_fleet(client)   # the base agents the clones copy their model from

        def author_of(s: dict) -> str:
            if not sop:
                return "gf_annex_author"
            return "gf_raci_specialist" if s["num"] == "3.0" else "gf_sop_author"

        def tidy(s: dict, text: str) -> str:
            if not _LETTERS.search(_strip_fences(text)) and s.get("content"):
                # An empty reply (seen from some models) is not a revision either: keep what the section had.
                log.warning("job %s: empty reply for %s; kept the previous text", job_id, s["num"])
                ctx.setdefault("empty_rejected", []).append(s["num"])
                return s["content"]
            if _echoes_prompt(text) and s.get("content"):
                # A reply that repeats the request is not a revision: keep what the section had.
                log.warning("job %s: reply for %s echoed the prompt; kept the previous text", job_id, s["num"])
                ctx.setdefault("echo_rejected", []).append(s["num"])
                return s["content"]
            body = _normalise_headings(_clean_section(text, structured=not sop))
            return _strip_own_heading(s["num"], s["mk"], s["en"], body) if sop else body

        def section_issues(s: dict) -> list[str]:
            return _lint_section(s["content"], sop)

        async def lint_and_repair(s: dict) -> None:
            """Proven grammar problems go back to the author before anyone audits the document."""
            issues = section_issues(s)
            for r in range(settings.lint_repair_rounds):
                if not issues:
                    break
                text = await ask(author_of(s), f"l{r + 1}_{s['num'].replace('.', '')}",
                    f"Rewrite section {s['num']} {s['mk']}|{s['en']} of '{meta['title_mk']} | {meta['title_en']}' "
                    f"(code {meta['code']}) to fix these problems:\n- "
                    + "\n- ".join(issues) + f"\n\n{ENGINE_GRAMMAR}\n\nKeep every requirement; change only what "
                    "the problems name. "
                    "Return ONLY the corrected section body — your reply is inserted verbatim.\n\n"
                    f"CURRENT SECTION\n{s['content']}")
                s["content"] = tidy(s, text)
                issues = section_issues(s)
            if issues:
                ctx["lint"][s["num"]] = issues
            else:
                ctx["lint"].pop(s["num"], None)        # a later repair fixed what an earlier round recorded

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
                    f"{CONCISE} {SECTION_HINT.get(num, ANNEX_RULE)}\n\n{controls}\n\n"
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
                f"write-in values. {FORM_RULE}\n{parent_note}"
                "Return ONLY the bilingual Markdown body — NO commentary, preamble, "
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
        house_sources: dict[str, list] = {}
        sem = asyncio.Semaphore(settings.reg_concurrency)
        done = 0

        async def check(s: dict) -> str:
            nonlocal done
            async with sem:
                # RAGFlow DB01 first: the checker gets the actual passages and cites them by [R#]; the job
                # keeps which passage each [R#] was. Without RAGFlow (or if it fails) the checker searches
                # its attached Letta sources, and the job says so.
                passages: list[dict] = []
                own: list[dict] = []
                if rag.configured and settings.ragflow_example_datasets:
                    try:
                        own = await rag.retrieve(f"{meta['title_en']} — {s['en']}: {s['content'][:800]}",
                                                 settings.ragflow_example_datasets, top_n=4)
                    except RagflowError as e:
                        knowledge["notes"].append(f"[{s['num']}] house documents unavailable to the check: {e}")
                house_part = ("\n\nAPPROVED, IN-USE HOUSE DOCUMENTS (cite as [H#]): also report, as CONFLICT [H#], "
                              "anything in the section that contradicts them — a different role, step, limit, form or "
                              "record for the same activity — unless the section says it changes that document.\n"
                              + format_passages(own, tag="H", max_chars=900)) if own else ""
                if own:
                    house_sources.setdefault(s["num"], citations(own))
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
                              f"if none applies.\n\nPASSAGES\n{format_passages(passages)}{house_part}\n\nSECTION\n{s['content']}")
                    reg_sources[s["num"]] = citations(passages)
                else:
                    prompt = (f"Check this drafted section {s['num']} of {meta['code']} against the "
                              f"regulatory corpus ({', '.join(settings.reg_sources)}). Cite only "
                              f"retrieved passages; say NO-FINDING if nothing applies.{house_part}\n\n{s['content']}")
                finding = await ask("gf_reg_checker", s["num"].replace(".", ""), prompt)
            done += 1
            await db.job_update(job_id, stage=f"regulatory-check {sections[done - 1]['num']}")
            return f"[{s['num']}] {finding.strip()}"

        outcomes = await asyncio.gather(*(check(s) for s in sections), return_exceptions=True)
        for o in outcomes:
            if isinstance(o, BaseException):
                raise o
        reg_findings: list[str] = list(outcomes)
        ctx.update(regulatory=reg_findings, regulatory_sources=reg_sources, house_sources=house_sources)

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
                if rnd == 0 or not settings.fix_to_review:
                    raise BilingualGap(gaps)
                # A repair reply that dropped one language, after an audit that was otherwise acted on: the draft
                # and the audit are kept and a person decides, as with a remaining FIX (review 19.10.2026).
                ctx["bilingual_gaps"] = gaps
                ctx["review_reason"] = ((ctx.get("review_reason", "") + "; ") if ctx.get("review_reason") else "") + \
                    f"after repair round {rnd} sections are not bilingual: {', '.join(gaps)}; a person decides"
                break
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
                "CONTENT BRIEF (the questionnaire answers, pre-verified by the questionnaire, and any "
                "instructions and sources the requester named; references in it count as supported):\n"
                f"{brief}\n\n"
                "REGULATORY CHECK FINDINGS, per section ([R#] = a passage retrieved from RAGFlow DB01):\n"
                f"{findings_txt}\n\n"
                "Also flag repetition (a requirement stated twice, or restating another section), padding "
                "and explanation the procedure does not need — never ask for more text to fill space.\n\n"
                + (f"Annexes: {ANNEX_RULE} Flag a form written into the SOP and any claim that annexes are "
                   "attached; never ask for the annexes to be added to this document.\n\n" if sop else
                   f"Form rules: {FORM_RULE} Flag each breach.\n\n")
                + (f"{controls}\nFlag every control that is missing or incomplete — a missing control is FIX. "
                   "One owner per record: for every record in 7.1 name its owner and check that the role text in 3, "
                   "the RACI and the steps in 6 agree; a disagreement is FIX.\n\n" if controls else "")
                + (f"PARENT SOP — sections 6 and 7 of {parent_code}. The form under audit must hold a field for every "
                   "item these sections write into this record, and its completers must be those section 7 names; a "
                   f"missing field is FIX.\n{parent_md}\n\n" if parent_md else "")
                + "List concrete, actionable issues per section. End your reply with one final line, "
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
                    + f"{CONCISE}\n{ANNEX_RULE if sop else FORM_RULE}\n{controls}\n"
                    + "Return ONLY the corrected section body — your reply is inserted verbatim.")
                s["content"] = tidy(s, text)
                await lint_and_repair(s)

        # Grammar problems the linter proved and the repair rounds did not fix (an echoed prompt, a pipe table,
        # an empty or monolingual section) used to be recorded and then registered as done on an auditor's PASS
        # (review 14.10.2026). A person sees them first, or the job fails when review parking is off.
        if ctx["lint"]:
            left = ", ".join(sorted(ctx["lint"]))
            if not settings.fix_to_review:
                raise LintUnresolved(left)
            ctx["review_reason"] = ((ctx.get("review_reason", "") + "; ") if ctx.get("review_reason") else "") + \
                f"grammar problems remain in {left} after the repair rounds (see lint); a person decides"

        # ---- house consistency (Head of QC, 19.10.2026) ----
        # The finished draft against the full text of a named set of approved, in-use documents. A conflict is never
        # registered silently: the job waits for a person, who must give the reason to register it anyway.
        await db.job_update(job_id, stage="house-check")
        ctx["house_check"] = await _house_check(ask, meta, ctx["markdown"], parent_code, brief)
        conflicts = [c for c, v in ctx["house_check"]["verdicts"].items() if v["verdict"] == "CONFLICT"]
        unchecked = [c for c, v in ctx["house_check"]["verdicts"].items() if v["verdict"] == "UNCHECKED"]
        if conflicts or unchecked or ctx["house_check"].get("error"):
            why = []
            if conflicts:
                why.append(f"conflicts with approved {', '.join(conflicts)}")
            if unchecked:
                why.append(f"no verdict for {', '.join(unchecked)}")
            if ctx["house_check"].get("error"):
                why.append(f"house check unavailable: {ctx['house_check']['error']}")
            ctx["review_reason"] = ((ctx.get("review_reason", "") + "; ") if ctx.get("review_reason") else "") + \
                "; ".join(why) + " — a person decides, and registering it needs a reason"

        # ---- format + verify (hard gate — a review never skips it) ----
        await db.job_update(job_id, stage="format")
        # H14 — builder.build is fully synchronous (docx render + verify, tens of seconds); called bare
        # it blocked the event loop, stalling every request this worker serves, including the polls.
        result = await asyncio.to_thread(
            builder.build, ctx["markdown"], settings.out_dir, meta["code"]
        )
        if ctx.get("review_reason"):
            # Built and verified, NOT registered: POST /workflows/{id}/review approves (registers) or returns it.
            await finish(status="awaiting_review", stage="format",
                         result={**ctx, "verify": result.verify_report, "bytes": result.bytes,
                                 "artifact": {"path": str(result.path), "bytes": result.bytes}})
            return
        # Stopped while formatting (POST /workflows/{id}/stop): nothing is registered (20.10.2026).
        if await db.job_touch(job_id) == "failed":
            raise JobAborted(job_id)
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
        if await finish(status="done", stage="done",
                        result={**ctx, "document_id": did, "verify": result.verify_report, "bytes": result.bytes}):
            await start_package(job_id, p, meta, sop)
    except JobAborted:
        log.warning("job %s: stopped (by a user or the stale-job reaper) while running; nothing written", job_id)
    except builder.VerifyFailed as e:
        log.error("job %s verify FAILED", job_id)
        await finish(status="failed", error="verify FAILED", result={**ctx, "verify": e.report})
    except QaAuditFailed as e:
        log.error("job %s §6A audit did not pass", job_id)
        await finish(status="failed", error="§6A audit did not pass",
                     result={**ctx, "qa_audit": e.verdict, "qa_verdict": _qa_verdict(e.verdict) or "FIX"})
    except LintUnresolved as e:
        log.error("job %s: %s", job_id, e)
        await finish(status="failed", error=str(e), result=ctx)
    except BilingualGap as e:
        log.error("job %s bilingual gap: %s", job_id, e.gaps)
        await finish(status="failed", error="sections are not bilingual: " + ", ".join(e.gaps),
                     result={**ctx, "bilingual_gaps": e.gaps})
    except LettaError as e:
        log.error("job %s letta error: %s", job_id, e)
        await finish(status="failed", error=f"letta: {e}", result=ctx)
    except Exception as e:  # noqa: BLE001 — job must record any failure
        log.exception("job %s failed", job_id)
        # Some exceptions (notably httpx.ReadTimeout) stringify to "" — always
        # record the type name so the job row never shows a blank error.
        detail = str(e).strip() or repr(e)
        await finish(status="failed", error=f"{type(e).__name__}: {detail}"[:500], result=ctx)
