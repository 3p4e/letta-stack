# LiteLLM proxy on KVM4

One OpenAI-compatible endpoint in front of every provider this project uses,
with the two safeguards the direct-call setup cannot give RAGFlow:

1. **A hard spend ceiling.** The prepaid OpenAI balance is small; the proxy
   refuses OpenAI calls past `max_budget` instead of failing mid-corpus with an
   overdrawn account. Top up, raise the value, restart.
2. **Quota rotation + fallback.** Four free-tier Gemini keys behind one model
   name with automatic cooldown on 429, and a fallback chain onto the Moonshot
   subscription (flat rate) when a paid provider is down or exhausted.

## Deploy (requires shell on KVM4 - cannot be done from a remote session)

    cd ingestion/litellm
    cp env.example .env    # fill in real keys; .env is git-ignored
    docker compose up -d
    curl -s http://localhost:4000/v1/models -H "Authorization: Bearer $LITELLM_MASTER_KEY"

Check the docker network name first (`docker network ls`) and adjust
`docker-compose.yml` if RAGFlow's network is not `docker_ragflow`.

## Wiring RAGFlow to it

Add a provider instance of type OpenAI-compatible with
`base_url = http://litellm:4000/v1` and `api_key = LITELLM_MASTER_KEY`, then
models `gpt-4.1`, `gpt-4.1-mini`, `gemini-flash`, `moonshot-v1-128k` become
available to pipeline nodes with the safeguards applied.

## What stays OUT of the proxy

The two-pass runner (`ingestion/ecoa_runner/extract_ecoa_records.py`) keeps
calling OpenAI and Google directly. Its guarantee is two INDEPENDENT vendors
reading the same page; a proxy that silently falls back would let one vendor
answer both reads. The runner has its own safeguards instead: a metered
OpenAI ceiling (`OPENAI_BUDGET_USD`, default $5.50) that stops the run cleanly
before the document that would cross it, key rotation with a clean stop when
every Gemini key is exhausted, and per-document incremental saves so a stopped
run resumes where it left off.
