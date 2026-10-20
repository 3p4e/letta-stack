# docengine.app.revise — change a generated draft by instruction (Head of QC, 20.10.2026: after the first generation the
# canvas must be editable and take commands).
#
# The draft is split at its level-1 headings. One section, or the whole body, goes to a fresh clone of the author that
# wrote it (gf_sop_author for an SOP, gf_annex_author for a form) with the instruction; the answer is cleaned as a
# generated section is, checked for both languages, and spliced back. The HEADERDATA block never leaves the engine, so
# code, version and titles cannot be changed by a command. Nothing is stored: the caller rebuilds with POST /build.
from __future__ import annotations

import logging
import re

from .letta import LettaClient, LettaError
from .pipeline import _bilingual_gaps, _clean_section

log = logging.getLogger("docengine")

MAX_INSTRUCTION = 4000
_HEAD_END = "-->"
_H1 = re.compile(r"^# (?!#)", re.M)
_H2 = re.compile(r"^## (?!#)", re.M)


def _level(body: str) -> re.Pattern:
    """The headings a draft is split at: level 1 where it has two or more (an SOP's '# 1.0 …'), else level 2 (a form:
    one '# ' title over '## ' sections)."""
    return _H1 if len(_H1.findall(body)) >= 2 or not _H2.search(body) else _H2


def split(markdown: str) -> tuple[str, list[str]]:
    """(HEADERDATA block, [each section with its heading line]). Text before the first section heading (a form's title)
    is a section of its own."""
    head, body = "", markdown
    if markdown.lstrip().startswith("<!--HEADERDATA"):
        end = markdown.find(_HEAD_END)
        if end >= 0:
            head, body = markdown[:end + len(_HEAD_END)] + "\n", markdown[end + len(_HEAD_END):]
    starts = [m.start() for m in _level(body).finditer(body)]
    if not starts:
        return head, ([body.strip("\n")] if body.strip() else [])
    pre = body[:starts[0]].strip("\n")
    return head, ([pre] if pre else []) + [body[a:b].strip("\n") for a, b in zip(starts, starts[1:] + [len(body)])]


def join(head: str, sections: list[str]) -> str:
    return head.rstrip("\n") + "\n" + "\n\n".join(s.strip("\n") for s in sections) + "\n"


def titles(markdown: str) -> list[str]:
    """The heading line of each section, without its '#' marks."""
    return [s.split("\n", 1)[0].lstrip("#").strip() for s in split(markdown)[1]]


def prompt(instruction: str, target: str, whole: bool, doctype: str) -> str:
    what = "the whole document body" if whole else "one section of the document"
    form = ("a form/annex body: keep its [[FORM]] and [[TABLE]] blocks, their columns and markers"
            if doctype != "SOP" else "an SOP section: keep the '## N.M MK | EN' sub-headings and the 'MK ||| EN' line pairs")
    return (
        f"Revise {what} below, which you drafted earlier, by this instruction from the Head of QC:\n\n"
        f"INSTRUCTION:\n{instruction}\n\n"
        "Rules:\n"
        f"- It is {form}. Keep the engine Markdown exactly as the house rules define it, Macedonian first, every prose "
        "line bilingual 'MK ||| EN'.\n"
        "- Change only what the instruction asks for; leave every other line as it is, word for word.\n"
        "- Keep the level-1 heading line(s) ('# …') unchanged unless the instruction is about the heading.\n"
        "- Write no batch, date, result or name that the text or the instruction does not give.\n"
        "- Answer with the revised Markdown only: no commentary, no code fences.\n\n"
        f"TEXT TO REVISE:\n{target}\n"
    )


async def revise(markdown: str, instruction: str, section: int | None, doctype: str,
                 client: LettaClient | None = None, tag: str = "rev") -> dict:
    """{markdown, section, title, gaps, agent}: the draft with the section (or the whole body) revised."""
    from .fleet import spawn_ephemeral
    instruction = instruction.strip()
    if not instruction:
        raise ValueError("an instruction is required")
    head, secs = split(markdown)
    if not secs:
        raise ValueError("the draft has no sections to revise")
    if section is not None and not 0 <= section < len(secs):
        raise ValueError(f"section {section} does not exist (the draft has {len(secs)})")
    whole = section is None
    target = "\n\n".join(secs) if whole else secs[section]
    agent = "gf_sop_author" if doctype == "SOP" else "gf_annex_author"
    client = client or LettaClient()
    tmp = await spawn_ephemeral(client, agent, tag)
    try:
        answer = await client.send_message(tmp, prompt(instruction, target, whole, doctype))
    finally:
        try:
            await client.delete_agent(tmp)
        except Exception as e:  # noqa: BLE001 — an orphaned clone is swept by ensure_fleet
            log.warning("failed to delete revise clone %s: %s", tmp, e)
    text = _clean_section(answer, structured=True).strip("\n")
    if not text:
        raise LettaError(f"{agent} returned no text")
    if whole:
        new = split("\n" + text)[1] or [text]
        out = join(head, new)
        gaps = _bilingual_gaps([{"num": str(i + 1), "content": s} for i, s in enumerate(new)])
        title = ""
    else:
        if secs[section].startswith("#") and not text.startswith("#"):
            text = secs[section].split("\n", 1)[0] + "\n" + text  # the heading is the section's anchor: kept if dropped
        secs = secs[:section] + [text] + secs[section + 1:]
        out = join(head, secs)
        gaps = _bilingual_gaps([{"num": str(section + 1), "content": text}])
        title = text.split("\n", 1)[0].lstrip("#").strip()
    return {"markdown": out, "section": section, "title": title, "gaps": gaps, "agent": agent}
