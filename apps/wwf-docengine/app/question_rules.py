# docengine.app.question_rules — the questions react to the answers before them, without an agent (Head of QC,
# 18.10.2026: "reactive questionare (updates after every user input …) with pregiven suitably chosen … topic specific,
# scope specific, goal appropriate pre given choices").
#
#   DEPENDS     which answers each answer rests on. When one of them changes, a decided dependent is marked stale
#               (re-confirmed by the requester, never rewritten). A change to purpose, scope or use (brief.CORE) still
#               marks every decided answer stale.
#   RECOMMEND   given an answer, the options of a later question that fit it — shown as recommended, never chosen
#               for the requester.
#   TOPICS      words in the title, purpose or scope that point to a question bank made for that topic.
# Deterministic and instant; the advisor agent (app/advisor.py) adds proposals with sources on top.
from __future__ import annotations

DEPENDS: dict[str, dict[str, list[str]]] = {
    "sop_qc": {
        "techniques": ["focus", "sample_types"],
        "acceptance": ["focus", "techniques"],
        "reference_standards": ["techniques"],
        "records": ["techniques", "purpose"],
        "review_chain": ["performer"],
    },
    "sop_transport": {
        "packaging": ["movements"],
        "conditions": ["movements", "packaging"],
        "roles": ["movements"],
        "records": ["movements", "authorities"],
    },
    "annex_form": {
        "id_fields": ["purpose"],
        "main_content": ["purpose", "initiator"],
    },
}

# (questionnaire, answered key, answer prefix) -> {later key: [option prefixes]}. Prefixes, so a reworded option
# still matches its start.
RECOMMEND: dict[str, dict[str, dict[str, dict[str, list[str]]]]] = {
    "sop_qc": {
        "focus": {
            "Identity": {"techniques": ["Microscopy", "HPLC-DAD"], "acceptance": ["Foreign matter"],
                         "reference_standards": ["CRS"]},
            "Potency": {"techniques": ["HPLC-DAD"], "acceptance": ["Cannabinoid"], "reference_standards": ["CRS", "SST"]},
            "Purity": {"techniques": ["Microscopy", "LOD", "Karl Fischer"], "acceptance": ["LOD", "Foreign matter"]},
            "Contaminants": {"techniques": ["GC-MS", "ICP-MS", "LC-MS/MS"],
                             "acceptance": ["Heavy metals", "Pesticides", "Mycotoxins"], "reference_standards": ["CRS"]},
            "Microbiology": {"techniques": ["Microbiological"], "acceptance": ["Microbial limits"]},
            "Water": {"techniques": ["Microbiological"], "acceptance": ["Microbial limits"]},
            "Sample management": {"records": ["Sample-prep records"]},
        },
        "techniques": {
            "HPLC-DAD": {"reference_standards": ["CRS", "SST"], "records": ["Instrument printouts", "SST records"]},
            "GC-MS": {"reference_standards": ["CRS", "SST"], "records": ["Instrument printouts"]},
            "ICP-MS": {"records": ["Instrument printouts"]},
            "LC-MS/MS": {"reference_standards": ["CRS"], "records": ["Instrument printouts"]},
            "Microbiological": {"records": ["Worksheets"]},
        },
        "purpose": {
            "Internal QC": {"records": ["Worksheets", "OOS records"]},
        },
        "performer": {
            "QC Analyst": {"review_chain": ["Two-tier"]},
            "External lab": {"review_chain": ["Two-tier"], "records": ["CoA"]},
        },
    },
    "sop_transport": {
        "movements": {
            "Intermediate": {"packaging": ["10 bags/carton"], "conditions": ["15–25 °C", "Data loggers"],
                             "roles": ["QC", "QA", "Security", "Logistics", "Carrier", "Consignee"]},
            "Propagation": {"packaging": ["Qualified cool box"], "conditions": ["Data loggers"]},
            "Final leg": {"packaging": ["10 bags/carton"], "conditions": ["15–25 °C", "Data loggers"]},
            "Cannabis waste": {"packaging": ["Sealed sacks"], "roles": ["QA", "Security"]},
        },
        "authorities": {
            "Police escort": {"records": ["Request for police escort"]},
            "Post-transport": {"records": ["Post-transport notification"]},
        },
    },
    "annex_form": {
        "purpose": {
            "Request": {"main_content": ["Item list", "Priority", "Sign-off rows"]},
            "Recording": {"main_content": ["Item list", "Quantities"], "id_fields": ["Batch", "Date"]},
            "Verification": {"main_content": ["Item list", "Sign-off rows"]},
            "Approval": {"main_content": ["Description", "Sign-off rows"]},
        },
    },
}

TOPICS: list[tuple[str, tuple[str, ...]]] = [
    ("sop_transport", ("transport", "превоз", "транспорт", "dispatch", "отпрема", "shipment", "courier")),
]


def _values(v) -> list[str]:
    return [str(x) for x in v] if isinstance(v, list) else ([str(v)] if v not in (None, "") else [])


def dependents(questionnaire: str, key: str) -> list[str]:
    return [q for q, deps in DEPENDS.get(questionnaire, {}).items() if key in deps]


def guide(brief: dict, questions: dict[str, list[str]]) -> dict:
    """What the questions show for the brief as it stands: per question the options recommended by the answers
    before it (and which answers led there), what it depends on, and a question bank the topic points to.
    `questions` maps each question key to its options."""
    q, fields = brief["questionnaire"], brief["fields"]
    out: dict = {"questions": {}, "questionnaire_hint": ""}
    for key, opts in questions.items():
        rec: dict[str, list[str]] = {}
        for src_key, by_answer in RECOMMEND.get(q, {}).items():
            f = fields.get(src_key)
            if not f:
                continue
            for answer in _values(f["value"]):
                for prefix, targets in by_answer.items():
                    if answer.startswith(prefix):
                        for pfx in targets.get(key, []):
                            for o in opts:
                                if o.startswith(pfx):
                                    rec.setdefault(o, []).append(f"{src_key}: {answer}")
        out["questions"][key] = {"recommended": [{"value": o, "because": sorted(set(b))} for o, b in rec.items()],
                                 "depends_on": DEPENDS.get(q, {}).get(key, [])}
    text = " ".join(str(x) for x in (brief["meta"].get("title_en", ""), brief["meta"].get("title_mk", ""),
                                     *(_values(fields.get(k, {}).get("value")) for k in ("doc.purpose", "doc.scope_in")))).lower()
    for bank, words in TOPICS:
        if bank != q and brief["package"] in ("sop", "sop_annexes") and any(w in text for w in words):
            out["questionnaire_hint"] = bank
            break
    return out
