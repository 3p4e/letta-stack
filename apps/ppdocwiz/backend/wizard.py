#!/usr/bin/env python3
"""
wizard.py — deterministic composer that turns a structured PP Doc Wiz payload into the bilingual
Markdown that pp-document-suite's build_from_md.py consumes. The wizard path is fully deterministic
(no LLM): the user fills guided fields, we compose the exact Markdown, the engine renders the house
style. Chat path (freeform, via a Letta agent) lives in app.py.

Payload shape (from the frontend):
{
  "doctype": "ANNEX" | "SOP" | "FORM",
  "mk_title","en_title","code","version","parent","supersedes","orient",
  "status" (draft | in_review | approved), "effective_date", "review_date",
  "sections": [
    { "num":"1","mk":"Опфат","en":"Scope","level":1,
      "blocks": [
        {"type":"text","paras":[{"mk":"...","en":"..."}]},
        {"type":"form","rows":[{"label_mk":"Поле","label_en":"Field","value":""}]},
        {"type":"table","cols":[{"mk":"№","en":""},{"mk":"Параметар","en":"Parameter"}],
         "rows":[[{"mk":"1","en":""},{"mk":"Карактеристики","en":"Characteristics"}]]}
      ] }
  ]
}
"""
import re

DOCTYPES = [
    {"key": "ANNEX", "mk": "Анекс", "en": "Annex",
     "desc": "Inline full-page bilingual annex (form / log / checklist / register).",
     "default_orient": "portrait"},
    {"key": "SOP", "mk": "СОП", "en": "SOP",
     "desc": "Two-column MK|EN Standard Operating Procedure (9-section).",
     "default_orient": "portrait"},
    {"key": "FORM", "mk": "Образец", "en": "Form",
     "desc": "Single-purpose bilingual data-entry form.",
     "default_orient": "portrait"},
]


# The line grammar (build_from_md.parse) reads a newline as a new line, '|||' as a cell separator, '~~' as the
# MK/EN split inside a cell, and a leading '#', '- ', '* ' or '[[' as a heading, bullet or block marker. A value
# typed into the wizard used to reach it unchanged: "ред 1\nред 2" in a form value became a second, broken row
# (review 19.10.2026). Every value is flattened here; a line that would start a construct is written literal ('\').
_LEAD = re.compile(r"^(#|\[\[|[-*]\s)")


def _one(s):
    """One line of text: newlines (and the whitespace around them) collapse to a space, no cell separator.
    As strict as str.strip(): a None or a number raises, and _compose answers 422."""
    return re.sub(r"\s*[\r\n]+\s*", " ", s).replace("|||", "| | |").strip()


def _lit(line):
    return ("\\" + line) if _LEAD.match(line) else line


def _bil(mk, en):
    mk = _one(mk or ""); en = _one(en or "")
    return mk + ((" ||| " + en) if en else "")


def _cell(mk, en):
    mk = _one(mk or "").replace("~~", "~ ~"); en = _one(en or "").replace("~~", "~ ~")
    return mk + (("~~" + en) if en else "")


def compose_markdown(p: dict) -> str:
    """Turn a wizard payload into pp-document-suite bilingual Markdown. Pure/deterministic."""
    hd = {   # one line each: a newline in a title or code would end its HEADERDATA field and start another
        "mk_title": _one(p.get("mk_title", "")),
        "en_title": _one(p.get("en_title", "")),
        "code": _one(p.get("code", "")),
        "version": _one(p.get("version") or "01"),
        "doctype": _one(p.get("doctype") or "ANNEX").upper(),
        "supersedes": _one(p.get("supersedes", "")),
        "parent": _one(p.get("parent", "")),
        "orient": _one(p.get("orient") or "portrait"),
    }
    # Document-control lifecycle (pp_format.status_band, read by build_from_md from
    # HEADERDATA). A draft is the engine default, so it is not written; a controlled
    # effective / review date exists only once the document is approved.
    status = (p.get("status") or "draft").strip()
    hd["status"] = "" if status == "draft" else status
    hd["effective_date"] = (p.get("effective_date") or "").strip() if status == "approved" else ""
    hd["review_date"] = (p.get("review_date") or "").strip() if status == "approved" else ""
    out = ["<!--HEADERDATA"]
    for k in ("mk_title", "en_title", "code", "version", "doctype", "supersedes", "parent", "orient",
              "status", "effective_date", "review_date"):
        if hd[k]:
            out.append(f"{k}: {hd[k]}")
    out.append("-->")
    out.append("")

    for s in p.get("sections", []):
        lvl = int(s.get("level", 1) or 1)
        hashes = "#" * max(1, min(3, lvl))
        num = _one(s.get("num") or "")
        head_mk = ((num + " ") if num else "") + _one(s.get("mk", ""))
        head_en = _one(s.get("en", ""))
        out.append(f"{hashes} {head_mk}" + ((" | " + head_en) if head_en else ""))
        for b in s.get("blocks", []):
            t = b.get("type")
            if t == "text":
                for para in b.get("paras", []):
                    line = _bil(para.get("mk"), para.get("en"))
                    if line:
                        out.append(_lit(line))
            elif t == "bullets":
                for para in b.get("paras", []):
                    line = _bil(para.get("mk"), para.get("en"))
                    if line:
                        out.append("- " + line)
            elif t == "form":
                out.append("[[FORM]]")
                for r in b.get("rows", []):
                    # form row: label_mk ||| label_en ||| value
                    lm = _one(r.get("label_mk") or ""); le = _one(r.get("label_en") or "")
                    val = _one(r.get("value") or "") or "_"
                    out.append(_lit(f"{lm} ||| {le} ||| {val}"))
                out.append("[[/FORM]]")
            elif t == "table":
                out.append("[[TABLE]]")
                cols = b.get("cols", [])
                out.append(_lit(" ||| ".join(_cell(c.get("mk"), c.get("en")) for c in cols)))
                for row in b.get("rows", []):
                    out.append(_lit(" ||| ".join(_cell(c.get("mk"), c.get("en")) for c in row)))
                out.append("[[/TABLE]]")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# A ready-to-use example so the UI can prefill and the /api/example endpoint can demo end-to-end.
EXAMPLE = {
    "doctype": "ANNEX",
    "mk_title": "Записник за ослободување — пропагационен материјал (клонови)",
    "en_title": "Release Record — Propagation Material (Clones)",
    "code": "WHSOP_002_A02",
    "version": "01",
    "parent": "WHSOP 002",
    "orient": "portrait",
    "sections": [
        {"num": "1", "mk": "Пратка", "en": "Consignment", "level": 1,
         "blocks": [{"type": "form", "rows": [
             {"label_mk": "MRN на царинска декларација", "label_en": "Customs declaration MRN", "value": ""},
             {"label_mk": "Датум/време на пристигнување", "label_en": "Arrival date/time", "value": ""},
             {"label_mk": "Температура при пристигнување", "label_en": "Arrival temperature", "value": ""},
         ]}]},
        {"num": "2", "mk": "Фитосанитарно и ослободување", "en": "Phytosanitary & release", "level": 1,
         "blocks": [{"type": "table",
                     "cols": [{"mk": "№", "en": ""}, {"mk": "Проверка", "en": "Check"},
                              {"mk": "Реф.", "en": "Ref."}, {"mk": "Статус", "en": "Status"}],
                     "rows": [
                         [{"mk": "1", "en": ""}, {"mk": "Фитосанитарна инспекција", "en": "Phytosanitary inspection"},
                          {"mk": "", "en": ""}, {"mk": "", "en": ""}],
                         [{"mk": "2", "en": ""}, {"mk": "SPL земање мостра", "en": "SPL sampling"},
                          {"mk": "", "en": ""}, {"mk": "", "en": ""}],
                         [{"mk": "3", "en": ""}, {"mk": "Сертификат за сообразност (CoC)", "en": "Certificate of Conformity (CoC)"},
                          {"mk": "", "en": ""}, {"mk": "", "en": ""}],
                     ]}]},
    ],
}
