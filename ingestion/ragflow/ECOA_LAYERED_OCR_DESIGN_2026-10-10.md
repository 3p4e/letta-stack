# eCoA layered extraction — NVIDIA document models + cross-vendor VLM reads (design, 2026-10-10)

Status: **design, not run.** No NVIDIA key is available to this session (the key lives only in
RAGflow's `NVIDIA`/`NVIDIAA` instances and cannot be read back; when tested through RAGflow it
returned "Function … Not found for account"). Every step below needs one live test first.

## What NVIDIA hosts (probed 2026-10-10: 401 = exists and needs a key, 404/410 = not served)

| model | endpoint | what it does | Cyrillic? |
|---|---|---|---|
| `nvidia/nemotron-page-elements-v3` | `ai.api.nvidia.com/v1/cv/nvidia/…` (401) | boxes for table / chart / title / text regions | no text read — language-free |
| `nvidia/nemotron-table-structure-v1` | same (401) | rows, columns and cell boxes inside a table crop | language-free |
| `nvidia/nemotron-graphic-elements-v1` | same (401) | chart parts (axes, legend, labels) | language-free |
| `nvidia/nemotron-ocr-v1` / `-v2` | same (401) | text + box + confidence per region | v2 multilingual: EN, ZH, JA, KO, **RU** — Macedonian Ѓ Ѕ Ј Љ Њ Ќ Џ not confirmed |
| `baidu/paddleocr` | `ai.api.nvidia.com/v1/cv/baidu/paddleocr` (401) | classical-architecture OCR | Cyrillic models exist upstream |
| `nvidia/nemotron-parse`, `nemotron-parse-2.0` | `integrate.api.nvidia.com/v1` chat (listed) | page → markdown, tables as LaTeX, box + class per element | English stated; not Macedonian |
| `moonshotai/kimi-k2.6`, `kimi-k3` | `integrate.api.nvidia.com/v1` (listed) | general VLM | yes (general model) |
| `meta/llama-3.2-90b-vision-instruct` | same (listed) | VLM | weak on Cyrillic |
| old `nemoretriever-*` names | 410 Gone | retired — RAGflow 0.26.4's NVIDIA catalog still uses names like these | — |

Kimi via NVIDIA is the way back to the Kimi models that `OCR_CHAIN` names (Moonshot's own API is
quota-exhausted).

## Why layers fit these certificates

The measured failures (`config/ecoa_extraction_agent.json` `_why`) are structural: a value comes
apart from its parameter and limit, and exponents are lost (10⁴ read as 10³). Detection models fix
the structure (which cell is which) without reading the language; VLMs read the content.

## Pipeline (per page, 300 dpi PNG — the rendered page stays the only source)

1. **Layout** — `nemotron-page-elements-v3`: find the results table(s), header block, signature
   block. Crop each table.
2. **Grid** — `nemotron-table-structure-v1` on each table crop: row/column/cell boxes. Gives the
   row a value belongs to, independent of language — the fix for the "value came apart from the
   parameter" failure.
3. **Read A (cell OCR)** — `nemotron-ocr-v2` multilingual on each cell crop. Strong on digits,
   units and Latin symbols; Macedonian-only letters are not guaranteed, so its text is used for
   **numbers, operators and units only**, never for parameter names.
4. **Read B (VLM, table-aware)** — `nemotron-parse-2.0` on the table crop → LaTeX table. Numeric
   columns only (English model).
5. **Read C (VLM, different vendor, full page)** — Kimi via NVIDIA, or Claude via OpenRouter /
   gpt-4.1 when OpenAI is funded, emitting `ecoa_extraction_schema.json` records with the grid from
   step 2 as row anchors. Parameter names, laboratory, certificate code and dates come from here.
6. **Arbiter (code, no LLM)** — per cell, `value`, `operator`, `limit`: accept when ≥ 2 of A/B/C
   agree exactly (after normalising decimal comma and ×10ⁿ); exponent cells need C plus one other.
   Anything else → `reads_agree=false`, value null, page raised for a person (existing policy).
7. Store the typed record; RAGflow keeps the page text for narrative questions only.

## Decisions needed

- ~~`policy_check.py` rule 1 (no classical OCR)~~ — lifted by the owner on 10.10.2026.
- A working `nvapi-` key from build.nvidia.com (Personal key with API access), placed as
  `NVIDIA_API_KEY` in the environment, then a one-page pilot on the 17 certificates with
  hand-read values (`_why.measured`) before any corpus run.

## Why NVIDIA vision fails inside RAGflow v0.26.4, and the fix (10.10.2026)

`rag/llm/cv_model.py` class `NvidiaCV` (the built-in "NVIDIA" provider's vision class):

- line 1053: when the instance has no base URL it sets `base_url = ("https://ai.api.nvidia.com/v1/vlm",)` —
  a **tuple** (trailing comma) — so `urljoin(base_url, ...)` raises *"Cannot mix str and non-str
  arguments"*. That is the exact error every NVIDIA parse returned.
- Even with a base URL, it POSTs `{"messages": ...}` with **no `model` field** to
  `ai.api.nvidia.com/v1/vlm/<org>/<model>` — a retired route (404 for kimi-k2.6, llama-3.2-90b-vision,
  nemotron-parse, probed 10.10.2026). NVIDIA now serves these on `integrate.api.nvidia.com/v1/chat/completions`.

Fix without patching RAGflow: register NVIDIA under the **OpenAI-API-Compatible** provider. Its vision
class `OpenAI_APICV` uses the OpenAI client (`model` + `messages`, base URL `urljoin(base,"v1")`):

| field | value |
|---|---|
| provider | OpenAI-API-Compatible |
| instance name | `NVIDIA_OAI` |
| base URL | `https://integrate.api.nvidia.com/` |
| API key | the same `nvapi-` key as the NVIDIA instance |

Then add models of type image2text: `moonshotai/kimi-k2.6`, `moonshotai/kimi-k3`,
`nvidia/nemotron-parse-2.0`, `meta/llama-3.2-90b-vision-instruct`, and select one in the pipeline Parser.
The detection/OCR models (page-elements, table-structure, nemotron-ocr) are `ai.api.nvidia.com/v1/cv/...`
endpoints with their own request shape; RAGflow has no client for them — they stay in the runner.
