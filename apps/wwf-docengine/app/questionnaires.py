# docengine.app.questionnaires — the canonical Mode-A question banks,
# encoded verbatim-in-substance from engine/references/questionnaire_library.md
# (the binding source per DOCENGINE-CANON §5). Principles preserved:
#   * every answer PRE-POPULATED (user selects, never types free regulation text);
#   * options verified against the regulatory hierarchy — no invented options;
#   * unanswered -> most-compliant default (marked with default=True).
# The UI renders these; the pipeline stores the selections as the content brief.

QUESTIONNAIRES: dict[str, dict] = {
    "sop_qc": {
        "title": {"en": "QC SOP questionnaire", "mk": "Прашалник за СОП — Контрола на квалитет"},
        "doctype": "SOP",
        "rounds": [
            {
                "key": "r1_scope",
                "title": {"en": "R1 — Scope", "mk": "Р1 — Опсег"},
                "questions": [
                    {"key": "focus", "multi": False, "label": {"en": "Primary testing focus", "mk": "Примарен фокус на тестирање"},
                     "options": ["Identity (Annex 8 §2 — ALL containers)", "Potency", "Purity", "Contaminants", "Microbiology", "Water", "Sample management"]},
                    {"key": "sample_types", "multi": True, "label": {"en": "Sample types", "mk": "Типови мостри"},
                     "options": ["Raw material", "In-process", "Bulk", "Finished product", "Water", "Environmental", "Stability"]},
                    {"key": "purpose", "multi": False, "label": {"en": "Batch-release vs monitoring", "mk": "Пуштање на серија или мониторинг"},
                     "options": [{"v": "Internal QC / IPQC / trending (release stays with accredited lab)", "default": True}, "Monitoring only"]},
                    {"key": "method_source", "multi": False, "label": {"en": "Method source", "mk": "Извор на метода"},
                     "options": [{"v": "Ph. Eur. (preferred)", "default": True}, "USP", "In-house", "ISO", "Contract lab"]},
                ],
            },
            {
                "key": "r2_technical",
                "title": {"en": "R2 — Technical", "mk": "Р2 — Технички"},
                "questions": [
                    {"key": "techniques", "multi": True, "label": {"en": "Techniques", "mk": "Техники"},
                     "options": ["HPLC-DAD", "GC-MS", "ICP-MS", "LC-MS/MS", "Microscopy", "LOD", "Karl Fischer", "Microbiological"]},
                    {"key": "acceptance", "multi": True, "label": {"en": "Acceptance criteria", "mk": "Критериуми за прифатливост"},
                     "options": ["Cannabinoid ±10 % (Ph. Eur. 3028)", "LOD NMT 12 %", "Foreign matter NMT 2 %", "Heavy metals", "Pesticides (Ph. Eur. 2.8.13)", "Mycotoxins", "Microbial limits"]},
                    {"key": "reference_standards", "multi": True, "label": {"en": "Reference standards", "mk": "Референтни стандарди"},
                     "options": ["CRS", "Secondary standard", "SST", "Internal"]},
                ],
            },
            {
                "key": "r3_responsibilities",
                "title": {"en": "R3 — Responsibilities", "mk": "Р3 — Одговорности"},
                "questions": [
                    {"key": "performer", "multi": False, "label": {"en": "Primary performer", "mk": "Примарен извршител"},
                     "options": [{"v": "QC Analyst", "default": True}, "QC Department Manager", "External lab"]},
                    {"key": "review_chain", "multi": False, "label": {"en": "Review chain", "mk": "Синџир на преглед"},
                     "options": ["Single", {"v": "Two-tier (Analyst + QC Manager)", "default": True}, "Three-tier + QP", "Cross-functional"]},
                ],
            },
            {
                "key": "r4_records",
                "title": {"en": "R4 — Records", "mk": "Р4 — Записи"},
                "questions": [
                    {"key": "records", "multi": True, "label": {"en": "Records generated", "mk": "Генерирани записи"},
                     "options": ["Worksheets (EU GMP 6.17)", "Instrument printouts", "Sample-prep records", "SST records", "CoA", "OOS records"]},
                    {"key": "retention", "multi": False, "label": {"en": "Retention", "mk": "Чување"},
                     "options": [{"v": "Batch docs: 1 y after expiry / min 5 y (EU GMP 4.11)", "default": True}, "Other (state in §7)"]},
                ],
            },
        ],
    },
    "annex_form": {
        "title": {"en": "Annex / Form questionnaire", "mk": "Прашалник за анекс / образец"},
        "doctype": "FORM",
        "rounds": [
            {
                "key": "r1_purpose",
                "title": {"en": "R1 — Purpose", "mk": "Р1 — Намена"},
                "questions": [
                    {"key": "purpose", "multi": False, "label": {"en": "Form purpose", "mk": "Намена на образецот"},
                     "options": ["Request", "Recording", "Verification", "Approval"]},
                    {"key": "initiator", "multi": False, "label": {"en": "Who initiates", "mk": "Кој иницира"},
                     "options": ["Operator", "Analyst", "Department manager", "QA", "QP"]},
                ],
            },
            {
                "key": "r2_content",
                "title": {"en": "R2 — Content", "mk": "Р2 — Содржина"},
                "questions": [
                    {"key": "id_fields", "multi": True, "label": {"en": "Identification fields", "mk": "Полиња за идентификација"},
                     "options": [{"v": "Doc ID (EU GMP 4.2)", "default": True}, {"v": "Version (4.3)", "default": True}, {"v": "Date (4.8)", "default": True}, "Batch"]},
                    {"key": "main_content", "multi": True, "label": {"en": "Main content", "mk": "Главна содржина"},
                     "options": ["Item list", "Quantities", "Description", "Priority", "Sign-off rows"]},
                ],
            },
        ],
    },
}


def questionnaire_index() -> list[dict]:
    return [
        {"key": k, "title": q["title"], "doctype": q["doctype"], "rounds": len(q["rounds"])}
        for k, q in QUESTIONNAIRES.items()
    ]


def apply_defaults(key: str, answers: dict) -> dict:
    """Auto-completion principle: unanswered -> most-compliant (default) option."""
    q = QUESTIONNAIRES[key]
    out = dict(answers or {})
    for rnd in q["rounds"]:
        for qq in rnd["questions"]:
            if qq["key"] in out and out[qq["key"]] not in (None, "", []):
                continue
            defaults = [
                (o["v"] if isinstance(o, dict) else o)
                for o in qq["options"]
                if isinstance(o, dict) and o.get("default")
            ]
            if defaults:
                out[qq["key"]] = defaults if qq["multi"] else defaults[0]
    return out
