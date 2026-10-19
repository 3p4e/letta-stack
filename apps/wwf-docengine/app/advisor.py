# docengine.app.advisor — proposals for the questions of a Document Brief page, each with a reason and a source
# (Head of QC, 18.10.2026: "pregiven suitably chosen and appropriate logical, topic specific, scope specific, goal
# appropriate pre given choices").
#
# One exchange with a fresh clone of gf_brief_advisor. It reads the brief (identity and what is decided), the questions
# asked about with their current options, the approved house documents (DB3_PP_CURRENT, [E#]), the regulatory corpus
# (DB01_REG, [R#]) and the uploaded sources, and answers JSON. A proposal is never a decision: the brief keeps it as
# `proposals` (and a value for an open question as `suggested`), and a chosen or locked answer is never overwritten.
from __future__ import annotations

import json
import logging
import re

from .config import settings
from .letta import LettaClient, LettaError
from .ragflow import RagflowClient, RagflowError, format_passages

log = logging.getLogger("docengine.advisor")
MAX_OPTIONS = 6
SHAPE = ('{"proposals": [{"key": "<question key>", "options": [{"value": "<short option>", "why": "<one sentence>", '
         '"source": "<E1 | R2 | file name | house practice>"}], "pick": "<value, or list of values for a multi question>"}]}')


def _first_json(text: str) -> dict:
    """The first JSON object in an agent's answer (it may wrap it in prose or a code fence)."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError("no JSON object in the answer")
    return json.loads(m.group(0))


def clean(raw: dict, asked: dict[str, dict]) -> dict[str, dict]:
    """Keep only proposals for the questions asked, as {key: {options: [...], pick}}; at most MAX_OPTIONS each."""
    out: dict[str, dict] = {}
    for p in (raw or {}).get("proposals") or []:
        key = p.get("key")
        if key not in asked or not isinstance(p.get("options"), list):
            continue
        opts = []
        for o in p["options"][:MAX_OPTIONS]:
            if isinstance(o, dict) and str(o.get("value", "")).strip():
                opts.append({"value": str(o["value"]).strip()[:300], "why": str(o.get("why", "")).strip()[:300],
                             "source": str(o.get("source", "")).strip()[:120] or "house practice"})
        if not opts:
            continue
        values = [o["value"] for o in opts] + list(asked[key].get("options") or [])
        pick = p.get("pick")
        if asked[key].get("multi"):
            pick = [v for v in (pick if isinstance(pick, list) else [pick]) if v in values]
        else:
            pick = pick if isinstance(pick, str) and pick in values else ""
        out[key] = {"options": opts, "pick": pick}
    return out


def prompt(brief: dict, asked: dict[str, dict], examples: str, regulatory: str, sources: list[dict]) -> str:
    decided = {k: f["value"] for k, f in brief["fields"].items() if f["state"] in ("chosen", "locked")}
    lines = [f"DOCUMENT: {brief['meta'].get('code') or '(code at build)'} — {brief['meta'].get('title_en', '')} | "
             f"{brief['meta'].get('title_mk', '')}; package {brief['package']}; question bank {brief['questionnaire']}.",
             "DECIDED BY THE PERSON (never contradict):", json.dumps(decided, ensure_ascii=False, indent=1),
             "", "QUESTIONS TO PROPOSE OPTIONS FOR:"]
    for key, q in asked.items():
        lines.append(f"- {key}: {q.get('label', key)}" + (" (several may be chosen)" if q.get("multi") else "")
                     + (f"; options already offered: {'; '.join(q['options'])}" if q.get("options") else "; free text"))
    if examples:
        lines += ["", "APPROVED HOUSE DOCUMENTS (structure and practice only):", examples]
    if regulatory:
        lines += ["", "REGULATORY PASSAGES:", regulatory]
    for s in sources[:3]:
        lines += ["", f"SOURCE FILE «{s['name']}»:", (s.get("text") or "")[:3000]]
    lines += ["", "Propose for every question above: up to 4 options that fit this document (new ones, or the offered "
              "ones that fit best), each with why and source, and the one you would pick. JSON only, in this shape:",
              SHAPE]
    return "\n".join(lines)


async def propose(brief: dict, asked: dict[str, dict], sources: list[dict], client: LettaClient | None = None,
                  rag: RagflowClient | None = None) -> dict:
    """{proposals: {key: {options, pick}}, notes: [...]} for the questions in `asked` ({key: {label, multi, options}})."""
    from .fleet import spawn_ephemeral
    client, rag, notes = client or LettaClient(), rag or RagflowClient(), []
    query = " ".join(str(x) for x in (brief["meta"].get("title_en", ""), brief["meta"].get("title_mk", ""),
                                      *[brief["fields"][k]["value"] for k in ("doc.purpose", "doc.scope_in")
                                        if k in brief["fields"]]))[:1500]
    examples = regulatory = ""
    if rag.configured and query.strip():
        try:
            if settings.ragflow_example_datasets:
                examples = format_passages(await rag.retrieve(query, settings.ragflow_example_datasets, top_n=4),
                                           tag="E", max_chars=900)
            regulatory = format_passages(await rag.retrieve(query, settings.ragflow_reg_datasets, top_n=4),
                                         tag="R", max_chars=700)
        except RagflowError as e:
            notes.append(f"knowledge bases unavailable: {e}")
    text = prompt(brief, asked, examples, regulatory, sources)
    tmp = await spawn_ephemeral(client, "gf_brief_advisor", f"brief_{brief['id'][:8]}")
    try:
        answer = await client.send_message(tmp, text)
    finally:
        try:
            await client.delete_agent(tmp)
        except Exception as e:  # noqa: BLE001 — an orphaned clone is swept by ensure_fleet
            log.warning("failed to delete advisor clone %s: %s", tmp, e)
    try:
        return {"proposals": clean(_first_json(answer), asked), "notes": notes}
    except (ValueError, json.JSONDecodeError) as e:
        raise LettaError(f"the advisor did not answer in the agreed shape: {e}") from e
