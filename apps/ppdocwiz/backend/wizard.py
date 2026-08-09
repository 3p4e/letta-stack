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


def _bil(mk, en):
    mk = (mk or "").strip(); en = (en or "").strip()
    return mk + ((" ||| " + en) if en else "")


def _cell(mk, en):
    mk = (mk or "").strip(); en = (en or "").strip()
    return mk + (("~~" + en) if en else "")


def compose_markdown(p: dict) -> str:
    """Turn a wizard payload into pp-document-suite bilingual Markdown. Pure/deterministic."""
    hd = {
        "mk_title": p.get("mk_title", "").strip(),
        "en_title": p.get("en_title", "").strip(),
        "code": p.get("code", "").strip(),
        "version": (p.get("version") or "01").strip(),
        "doctype": (p.get("doctype") or "ANNEX").strip().upper(),
        "supersedes": p.get("supersedes", "").strip(),
        "parent": p.get("parent", "").strip(),
        "orient": (p.get("orient") or "portrait").strip(),
    }
    out = ["<!--HEADERDATA"]
    for k in ("mk_title", "en_title", "code", "version", "doctype", "supersedes", "parent", "orient"):
        if hd[k]:
            out.append(f"{k}: {hd[k]}")
    out.append("-->")
    out.append("")

    for s in p.get("sections", []):
        lvl = int(s.get("level", 1) or 1)
        hashes = "#" * max(1, min(3, lvl))
        num = (s.get("num") or "").strip()
        head_mk = ((num + " ") if num else "") + (s.get("mk", "").strip())
        head_en = s.get("en", "").strip()
        out.append(f"{hashes} {head_mk}" + ((" | " + head_en) if head_en else ""))
        for b in s.get("blocks", []):
            t = b.get("type")
            if t == "text":
                for para in b.get("paras", []):
                    line = _bil(para.get("mk"), para.get("en"))
                    if line:
                        out.append(line)
            elif t == "bullets":
                for para in b.get("paras", []):
                    line = _bil(para.get("mk"), para.get("en"))
                    if line:
                        out.append("- " + line)
            elif t == "form":
                out.append("[[FORM]]")
                for r in b.get("rows", []):
                    lbl = _cell(r.get("label_mk"), r.get("label_en")).replace("~~", "~~")
                    # form row: label_mk ||| label_en ||| value
                    lm = (r.get("label_mk") or "").strip(); le = (r.get("label_en") or "").strip()
                    val = (r.get("value") or "").strip() or "_"
                    out.append(f"{lm} ||| {le} ||| {val}")
                out.append("[[/FORM]]")
            elif t == "table":
                out.append("[[TABLE]]")
                cols = b.get("cols", [])
                out.append(" ||| ".join(_cell(c.get("mk"), c.get("en")) for c in cols))
                for row in b.get("rows", []):
                    out.append(" ||| ".join(_cell(c.get("mk"), c.get("en")) for c in row))
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
