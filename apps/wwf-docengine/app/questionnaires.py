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
    # Inland transport of narcotic drugs. Every option and default is taken from the approved
    # WHSOP_003 v01 (deliverables/inland_transport_2026-10/md/WHSOP_003.md; section noted per question),
    # so the questionnaire offers nothing the facility's own SOP and its references do not support.
    "sop_transport": {
        "title": {"en": "Transport SOP questionnaire", "mk": "Прашалник за СОП — Транспорт"},
        "doctype": "SOP",
        "rounds": [
            {
                "key": "r1_scope",
                "title": {"en": "R1 — Scope", "mk": "Р1 — Опсег"},
                "questions": [
                    # WHSOP_003 §2.1 (1)-(4)
                    {"key": "movements", "multi": True, "label": {"en": "Movements covered", "mk": "Опфатени движења"},
                     "options": [{"v": "Intermediate (bulk in bags) and finished product to licensed domestic consignees", "default": True},
                                 {"v": "Propagation material (clones, seeds) between sites", "default": True},
                                 {"v": "Final leg after customs clearance to the site", "default": True},
                                 {"v": "Cannabis waste to an authorised destruction site", "default": True}]},
                    # §2.1, §6.1 (c)
                    {"key": "carrier", "multi": False, "label": {"en": "Who transports", "mk": "Кој превезува"},
                     "options": [{"v": "Contracted, qualified and licensed carrier under a Quality Agreement", "default": True}]},
                    # §1.0 (d), §2.3
                    {"key": "records_system", "multi": False, "label": {"en": "Record system", "mk": "Систем на записи"},
                     "options": [{"v": "Paper-based", "default": True}, "Electronic tracking system (after change control, §2.3)"]},
                ],
            },
            {
                "key": "r2_security",
                "title": {"en": "R2 — Security and authorities", "mk": "Р2 — Безбедност и органи"},
                "questions": [
                    # §6.3, §6.8, §4.1
                    {"key": "authorities", "multi": True, "label": {"en": "Authority steps", "mk": "Чекори кон органите"},
                     "options": [{"v": "Police escort requested from the MoIA at least 24 h before dispatch (Law on Control of Narcotic Drugs, Off. Gazette 37/16)", "default": True},
                                 {"v": "Written MoIA confirmation mandatory before dispatch", "default": True},
                                 {"v": "Post-transport notification to the Ministry of Health", "default": True}]},
                    # §6.1 (a), §6.2.2
                    {"key": "lane", "multi": False, "label": {"en": "Lane status before dispatch", "mk": "Статус на рутата пред отпрема"},
                     "options": [{"v": "Lane QUALIFIED per QASOP_0XX, same vehicle and pallet configuration", "default": True}]},
                    # §4.2
                    {"key": "references", "multi": True, "label": {"en": "GMP / GDP references", "mk": "GMP / GDP референци"},
                     "options": [{"v": "EU GDP 2013/C 343/01 Ch. 7 and Ch. 9", "default": True},
                                 {"v": "EudraLex Vol. 4 Part I Ch. 4, Ch. 5 §5.10, Ch. 7", "default": True},
                                 {"v": "WHO TRS 961 Annex 9", "default": True},
                                 {"v": "ICH Q9(R1)", "default": True}]},
                ],
            },
            {
                "key": "r3_conditions",
                "title": {"en": "R3 — Packaging and conditions", "mk": "Р3 — Пакување и услови"},
                "questions": [
                    # §6.1 condition matrix
                    {"key": "packaging", "multi": True, "label": {"en": "Packaging", "mk": "Пакување"},
                     "options": [{"v": "10 bags/carton; pallet L 8 or S 4 cartons; stretch film and thermal blanket", "default": True},
                                 {"v": "Qualified cool box (propagation material)", "default": True},
                                 {"v": "Airtight container", "default": True},
                                 {"v": "Sealed sacks with a record (waste)", "default": True}]},
                    # §6.4 (pallet label conditions), §6.6
                    {"key": "conditions", "multi": True, "label": {"en": "Conditions and monitoring", "mk": "Услови и следење"},
                     "options": [{"v": "15–25 °C, RH ≤ 60 %, protect from moisture", "default": True},
                                 {"v": "Data loggers placed per the QA-approved plan", "default": True}]},
                ],
            },
            {
                "key": "r4_records",
                "title": {"en": "R4 — Responsibilities and records", "mk": "Р4 — Одговорности и записи"},
                "questions": [
                    # §3.0 RACI columns
                    {"key": "roles", "multi": True, "label": {"en": "Roles in the RACI", "mk": "Улоги во RACI"},
                     "options": [{"v": "QC", "default": True}, {"v": "QA", "default": True}, {"v": "Security", "default": True},
                                 {"v": "Logistics", "default": True}, {"v": "Carrier (driver)", "default": True},
                                 {"v": "Consignee", "default": True}, {"v": "QP", "default": True}]},
                    # §7.0 annex register
                    {"key": "records", "multi": True, "label": {"en": "Records (annexes)", "mk": "Записи (анекси)"},
                     "options": [{"v": "Transport Risk Assessment (TRA)", "default": True},
                                 {"v": "Request for police escort and notification to the MoIA", "default": True},
                                 {"v": "Pallet and carton labels and packing lists", "default": True},
                                 {"v": "Transport manifest and chain of custody", "default": True},
                                 {"v": "Pre-dispatch and receipt checklist", "default": True},
                                 {"v": "Post-transport notification to the Ministry of Health", "default": True},
                                 {"v": "Transport file review and disposition", "default": True}]},
                    # §6.8 / EU GMP 4.11
                    {"key": "retention", "multi": False, "label": {"en": "Retention", "mk": "Чување"},
                     "options": [{"v": "At least 5 y or 1 y after batch expiry, whichever is longer (EU GMP 4.11)", "default": True}]},
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
