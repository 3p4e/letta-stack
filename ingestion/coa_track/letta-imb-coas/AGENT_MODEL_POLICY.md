# Letta Agent Model Routing Policy

_Authoritative source: [`agent_model_policy.py`](agent_model_policy.py). This document is a human-readable summary._

## Policy rules

| Function class | Primary | Fallback 1 | Fallback 2 |
|---|---|---|---|
| **OCR / document vision** | Moonshot `kimi-k2.6` | Moonshot `moonshot-v1-128k-vision-preview` | OpenAI `gpt-4o` |
| **In-chat vision** (image attached to user message) | Moonshot `kimi-k2.6` | OpenAI `gpt-4o` | — |
| **Audit / compliance / verification** | DeepSeek `deepseek-v4-pro` | OpenAI `gpt-4o` | — |
| **Reasoning / advisory** | DeepSeek `deepseek-v4-pro` | OpenAI `gpt-4o` | — |
| **Orchestrators** (delegate to specialists) | DeepSeek `deepseek-v4-pro` | OpenAI `gpt-4o` | — |
| **RAG domain experts** (CoA / water / GMP / equipment) | DeepSeek `deepseek-v4-pro` | OpenAI `gpt-4o` | — |
| **Generation / SOP writing / CoQ assembly** | DeepSeek `deepseek-v4-pro` | OpenAI `gpt-4o` | — |
| **Translation MK↔EN** | DeepSeek `deepseek-v4-flash` | OpenAI `gpt-4o` | — |
| **Formatting / DOCX** | DeepSeek `deepseek-v4-flash` | OpenAI `gpt-4o` | — |
| **Summarization / trends** | DeepSeek `deepseek-v4-flash` | OpenAI `gpt-4o` | — |
| **Routing / chat router** | DeepSeek `deepseek-v4-flash` | OpenAI `gpt-4o` | — |
| **Fast search / extraction** | DeepSeek `deepseek-v4-flash` | OpenAI `gpt-4o` | — |
| **Design / diagrams** | DeepSeek `deepseek-v4-flash` | OpenAI `gpt-4o` | — |
| **Embeddings** (per RAG source) | OpenAI `text-embedding-3-small` (1536d) | Voyage `voyage-3` (1024d) | — |

### Why these models

- **`kimi-k2.6`** is Moonshot's first vision-capable flagship; `kimi-k2.5` is text-only and is therefore NOT used for vision tasks despite the family-name shorthand.
- **`moonshot-v1-128k-vision-preview`** kept as a secondary Moonshot vision fallback in case `kimi-k2.6` rate-limits or returns refusals on a specific image.
- **`gpt-4o`** is the final OCR fallback — well-documented strong Cyrillic + Macedonian + table-layout extraction.
- **`deepseek-v4-pro`** is used wherever multi-step reasoning, evidence-grounded analysis, or audit-style verification matters — the role you would otherwise hand to a senior analyst.
- **`deepseek-v4-flash`** is used for fast, structurally-simple tasks where latency and per-token cost matter more than nuance.

### Cost & context implications

| Model | Provider | Context | Vision | Approx. relative cost (vs gpt-4o = 1.0) |
|---|---|---|---|---|
| `kimi-k2.6` | Moonshot | 256k | ✅ | ~0.6 |
| `moonshot-v1-128k-vision-preview` | Moonshot | 128k | ✅ | ~0.6 |
| `gpt-4o` | OpenAI | 128k | ✅ | 1.0 |
| `deepseek-v4-pro` | DeepSeek | 64k | ❌ | ~0.15 |
| `deepseek-v4-flash` | DeepSeek | 64k | ❌ | ~0.05 |

A typical multi-page CoA OCR job that used to cost ~$0.05 on `gpt-4o` will cost ~$0.03 on `kimi-k2.6` when it succeeds — assuming Cyrillic quality is acceptable (to be verified per the test plan).

## Agent → role assignment (41 agents)

Defined in `agent_model_policy.AGENT_ROLES`. Any agent not in the dict defaults to `deepseek-v4-flash` (cheap & safe).

| Role | Model | Agents |
|---|---|---|
| `vision_ocr` | `kimi-k2.6` | `warehouse_quarantine_ocr_agent` |
| `audit` | `deepseek-v4-pro` | `Compliance Analysis Agent`, `qms_gmp_auditor`, `eu_gmp_compliance_expert`, `ars_devils_advocate`, `ars_integrity_verifier`, `pp_annex_auditor`, `code_reviewer`, `security_auditor`, `web_design_reviewer` |
| `reasoning` | `deepseek-v4-pro` | `Specification Advisor Agent`, `ars_collaboration_depth`, `ars_field_analyst` |
| `orchestrator` | `deepseek-v4-pro` | `qms_pipeline_orchestrator`, `ars_pipeline_orchestrator`, `pp_annex_orchestrator`, `letta_manager` |
| `rag_query` | `deepseek-v4-pro` | `imb_qc_coa_agent`, `pq1_water_qc_agent`, `ecoa-qc-agent`, `equipment_manuals_agent`, `gmp_rag_agent`, `fastapi_letta_qms_patterns` |
| `generation` | `deepseek-v4-pro` | `CoQ Assembly Agent`, `Report Generation Agent`, `qms_sop_expert`, `pp_annex_table_specialist`, `pp_annex_body_formatter` |
| `translation` | `deepseek-v4-flash` | `pp_annex_translator` |
| `format` | `deepseek-v4-flash` | `qms_docx_formatter`, `pharma_docx_formatter` |
| `summarize` | `deepseek-v4-flash` | `executive_summarizer`, `weekly_report_analyst`, `trend_detector`, `stock_trading_advisor` |
| `route` | `deepseek-v4-flash` | `letta_chat_interface` |
| `search` | `deepseek-v4-flash` | `Search Assistant Agent`, `Parameter Extraction Agent`, `CoA Ingestion Agent` |
| `design` | `deepseek-v4-flash` | `penpot_uiux_design`, `excalidraw_diagram_generator` |

Distribution after rewire: **27 agents on `deepseek-v4-pro`, 13 on `deepseek-v4-flash`, 1 on `kimi-k2.6`** (41 total) — net effect is that virtually every text-only agent moves off OpenAI to DeepSeek, cutting per-message cost ~6-20× while keeping reasoning quality high.

## Applying the policy

### 1. Container env (you, on Hostinger deployment-manager UI)

Confirm all of these are present and named exactly as below:

| Name | Source |
|---|---|
| `OPENAI_API_KEY` | already set |
| `DEEPSEEK_API_KEY` | already set |
| `MOONSHOT_API_KEY` | renamed from `MOONSHOTAI_API_KEY` |
| `VOYAGE_API_KEY` | already set (rotate first — was leaked in chat) |
| `HF_TOKEN` | renamed from `HUGGINGFACE_API_KEY` |

### 2. Compose file (one-time, on KVM4)

```bash
cd /opt/stacks/letta
# verify the letta service depends_on has ONLY postgres (no letta-daemon)
grep -A5 "^  letta:" docker-compose.yml | grep -A3 depends_on
docker compose up -d
docker exec letta env | grep -E "MOONSHOT|DEEPSEEK|OPENAI|VOYAGE|HF_TOKEN"  # confirm all 5
```

### 3. Apply the policy to all existing agents (one-time, from KVM4)

```bash
cd /opt/CoA_TRACK   # or wherever you cloned the repo
git pull
python3 scripts/letta-imb-coas/rewire_agents.py --dry-run   # preview the diff
python3 scripts/letta-imb-coas/rewire_agents.py             # apply
```

The script prints a per-agent diff (`old_model → new_model`) and a final distribution table.

### 4. OCR pipeline

The chain was first wired into `ingest_imb_coas_v2.py`, which was retired
29.08.2026 along with the Letta source it fed. It is implemented today in
`ingestion/ragflow/doc_identity.py`, which routes every page through the chain: Moonshot kimi-k2.6 → moonshot-v1-128k-vision-preview → gpt-4o. First success wins. The first line of every produced `.txt` is annotated with which provider+model did the OCR, so we can audit Cyrillic quality after the run:

```
[OCR via moonshot-kimi/kimi-k2.6]
... transcribed text ...
```

## Maintaining the policy

To rename a model, change a role's primary, or add a new agent, edit `agent_model_policy.py` only — the rewire script and the OCR pipeline both re-read it. Re-running `rewire_agents.py` is idempotent.
