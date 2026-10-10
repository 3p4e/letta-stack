"""
Letta agent model routing policy — Purely Plant GmbH KVM4.

This module is the single source of truth for which AI provider + model each
agent uses. The rewire script reads from this file, the OCR pipeline reads
from this file, and any future agent provisioning script should also read
from this file. Updating the policy means editing this file only.
"""
from __future__ import annotations

# ── Provider endpoints (OpenAI-compatible chat-completions API everywhere) ──
# IMPORTANT: model_endpoint_type tells Letta which env var to use for auth.
# Setting it to "openai" with a non-OpenAI URL causes Letta to send the
# OPENAI_API_KEY anyway — that's how we got 401s yesterday. Use the real
# provider name so Letta uses DEEPSEEK_API_KEY / MOONSHOT_API_KEY / etc.
PROVIDERS = {
    "moonshot": {
        # NOTE: Letta 0.16.x does NOT have a "moonshot" provider type in its
        # literal whitelist. Vision OCR therefore falls back to gpt-4o for the
        # in-Letta agent; the standalone OCR pipelines call Moonshot directly
        # via the OpenAI SDK with a base_url override.
        "endpoint_type": "openai",
        "endpoint": "https://api.moonshot.ai/v1",
        "env_var": "MOONSHOT_API_KEY",
    },
    "openai": {
        "endpoint_type": "openai",
        "endpoint": "https://api.openai.com/v1",
        "env_var": "OPENAI_API_KEY",
    },
    "deepseek": {
        # Letta has first-class "deepseek" provider type → reads DEEPSEEK_API_KEY
        "endpoint_type": "deepseek",
        "endpoint": "https://api.deepseek.com/v1",
        "env_var": "DEEPSEEK_API_KEY",
    },
}

# ── Model catalogue with provider + context window ──
# Note: kimi-k2.5 is TEXT-ONLY per Moonshot docs.
# For vision tasks use kimi-k2.6 or moonshot-v1-128k-vision-preview.
MODELS = {
    # Vision-capable (Moonshot first, OpenAI fallback)
    "kimi-k2.6":                       {"provider": "moonshot", "ctx": 256_000, "vision": True},
    "moonshot-v1-128k-vision-preview": {"provider": "moonshot", "ctx": 128_000, "vision": True},
    "gpt-4o":                          {"provider": "openai",   "ctx": 128_000, "vision": True},
    # Text-only reasoning (DeepSeek)
    "deepseek-v4-pro":                 {"provider": "deepseek", "ctx":  64_000, "vision": False},
    "deepseek-v4-flash":               {"provider": "deepseek", "ctx":  64_000, "vision": False},
    "kimi-k2.5":                       {"provider": "moonshot", "ctx": 256_000, "vision": False},
}

# ── OCR fallback chain ──
# This is the policy declaration, not an implementation. Its original consumer,
# ingest_imb_coas_v2.py stage b, was retired 29.08.2026 with the Letta source it
# fed. The chain is implemented today in ingestion/ragflow/doc_identity.py; the
# CoA_DATABASE_2026 driver runs a narrower OpenAI-only variant of it, and says
# in its own docstring why (no vision-capable fallback key is confirmed).
OCR_CHAIN = ["kimi-k2.6", "moonshot-v1-128k-vision-preview", "gpt-4o"]

# ── Embedding policy (per-source — managed in source config, not agent) ──
EMBED_PRIMARY = {
    "model": "text-embedding-3-small",
    "endpoint_type": "openai",
    "endpoint": "https://api.openai.com/v1",
    "dim": 1536,
    "chunk_size": 300,
    "batch_size": 32,
}
EMBED_FALLBACK = {
    "model": "voyage-3",
    "endpoint_type": "openai",  # OpenAI-compatible wire format
    "endpoint": "https://api.voyageai.com/v1",
    "dim": 1024,
    "chunk_size": 512,
    "batch_size": 16,
}

# ── Role classification rubric ──
# Each role maps to a model. Adding a new agent: classify into one of these.
#
# NOTE on vision: Letta 0.16.x lacks a "moonshot" provider type, so in-Letta
# vision-capable agents must use gpt-4o for now. The standalone OCR pipeline
# (ingestion/ragflow/doc_identity.py) bypasses Letta and goes directly to
# Moonshot kimi-k2.6 with OpenAI gpt-4o as fallback.
ROLE_TO_MODEL = {
    "vision_ocr":    "gpt-4o",             # in-Letta agent — pipeline uses kimi-k2.6 directly
    "vision_chat":   "gpt-4o",             # image-in-conversation tasks
    "audit":         "deepseek-v4-pro",    # compliance / audit / verification / devils advocate
    "reasoning":     "deepseek-v4-pro",    # multi-step reasoning, planning, complex analysis
    "orchestrator":  "deepseek-v4-pro",    # pipeline orchestrators (delegate to specialists)
    "rag_query":     "deepseek-v4-pro",    # RAG-attached domain experts (CoA, water, GMP, equipment)
    "generation":    "deepseek-v4-pro",    # report assembly, SOP writing, content generation
    "translation":   "deepseek-v4-flash",  # MK↔EN translation
    "format":        "deepseek-v4-flash",  # DOCX / table formatting
    "summarize":     "deepseek-v4-flash",  # summarization, trend detection
    "route":         "deepseek-v4-flash",  # chat routing / fast classification
    "search":        "deepseek-v4-flash",  # search assistant, parameter extraction
    "design":        "deepseek-v4-flash",  # UI/UX / diagrams (creative-light, fast)
}

# ── Agent-name → role classification (the 41 agents in inventory) ──
AGENT_ROLES = {
    # OCR / vision
    "warehouse_quarantine_ocr_agent":     "vision_ocr",
    # Audit / compliance / verification
    "Compliance Analysis Agent":          "audit",
    "qms_gmp_auditor":                    "audit",
    "eu_gmp_compliance_expert":           "audit",
    "ars_devils_advocate":                "audit",
    "ars_integrity_verifier":             "audit",
    "pp_annex_auditor":                   "audit",
    "code_reviewer":                      "audit",
    "security_auditor":                   "audit",
    "web_design_reviewer":                "audit",
    # Reasoning / advisors
    "Specification Advisor Agent":        "reasoning",
    "ars_collaboration_depth":            "reasoning",
    "ars_field_analyst":                  "reasoning",
    # Orchestrators
    "qms_pipeline_orchestrator":          "orchestrator",
    "ars_pipeline_orchestrator":          "orchestrator",
    "pp_annex_orchestrator":              "orchestrator",
    "letta_manager":                      "orchestrator",
    # RAG-attached domain agents
    "imb_qc_coa_agent":                   "rag_query",
    "pq1_water_qc_agent":                 "rag_query",
    "ecoa-qc-agent":                      "rag_query",
    "equipment_manuals_agent":            "rag_query",
    "gmp_rag_agent":                      "rag_query",
    "fastapi_letta_qms_patterns":         "rag_query",
    # Generation / assembly
    "CoQ Assembly Agent":                 "generation",
    "Report Generation Agent":            "generation",
    "qms_sop_expert":                     "generation",
    "pp_annex_table_specialist":          "generation",
    "pp_annex_body_formatter":            "generation",
    # Translation
    "pp_annex_translator":                "translation",
    # Formatting
    "qms_docx_formatter":                 "format",
    "pharma_docx_formatter":              "format",
    # Summarization / trend
    "executive_summarizer":               "summarize",
    "weekly_report_analyst":              "summarize",
    "trend_detector":                     "summarize",
    # Routing / chat
    "letta_chat_interface":               "route",
    # Search / extraction
    "Search Assistant Agent":             "search",
    "Parameter Extraction Agent":         "search",
    "CoA Ingestion Agent":                "search",
    # Design / diagrams
    "penpot_uiux_design":                 "design",
    "excalidraw_diagram_generator":       "design",
    # Miscellaneous (legacy / experiment)
    "stock_trading_advisor":              "summarize",
}


def model_for_agent(name: str) -> str:
    """Return the policy-mandated model name for a given agent.
    Unknown agents default to deepseek-v4-flash (cheap, fast, safe default)."""
    role = AGENT_ROLES.get(name, "search")
    return ROLE_TO_MODEL[role]


def llm_config_for_model(model_name: str) -> dict:
    """Build a Letta llm_config dict for a model in the catalogue."""
    spec = MODELS[model_name]
    prov = PROVIDERS[spec["provider"]]
    return {
        "model": model_name,
        "model_endpoint_type": prov["endpoint_type"],
        "model_endpoint": prov["endpoint"],
        "context_window": spec["ctx"],
        "put_inner_thoughts_in_kwargs": False,
        "temperature": 1.0,
        "enable_reasoner": False,
        "max_reasoning_tokens": 0,
        "parallel_tool_calls": False,
    }
