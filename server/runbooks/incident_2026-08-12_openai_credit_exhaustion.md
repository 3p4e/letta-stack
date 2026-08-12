# Archival-memory outage & recovery — 2026-08-12

**Symptom:** `search_archival` and archival-memory inserts began returning
`500 {"detail":"An unknown error occurred"}` for every agent tested, regardless of embedding
provider — reproduced via both direct REST and the MCP bridge. Plain reads (`GET /v1/agents/{id}`,
`list_passages`) kept working throughout, isolating the failure to the embedding-call path
specifically.

**Root cause:** `OPENAI_API_KEY` had run out of billing credits (`insufficient_quota` /
`credit_balance_exhausted`, confirmed via a direct `POST https://api.openai.com/v1/embeddings`
call returning HTTP 429). Every agent actually observed during triage — including
`pq1_water_qc_agent`, whose `embedding_config` points at `https://api.voyageai.com/v1` — uses
`embedding_endpoint_type: "openai"`; whether Letta's embedding client keys auth off the endpoint
hostname or always falls back to `OPENAI_API_KEY` for that type wasn't confirmed from outside (no
server-log access), so the Voyage-endpoint agent's failure may or may not be fully explained by
this same cause — flag for whoever has log access next. Resolved the moment OpenAI billing
credits were topped up: `search_archival` and inserts both recovered immediately, no Letta
restart needed.

**Secondary findings while triaging:**
- Voyage AI is **not** usable via the `/v1/providers` BYOK registry on this Letta build (0.16.8):
  `POST /v1/providers` accepts a `provider_type: "openai"` + custom `base_url` entry (mirrors how
  `moonshot` is registered), but the connectivity `check`/`refresh` step 404s, because Voyage's
  API has no OpenAI-style `/v1/models` endpoint — no embedding models get auto-discovered this
  way. The working pattern instead is a **direct `embedding_config`** set on the agent, no
  provider row involved: `embedding_endpoint_type: "openai"`,
  `embedding_endpoint: "https://api.voyageai.com/v1"`, a real Voyage model name + matching dim
  (e.g. `voyage-3-large`, 1024d, chunk 512). This is how `pq1_water_qc_agent`'s archives are
  already configured — use it as the template for any future Voyage-backed agent.
- The whole VPS (every container across every stack, not just Letta) showed uniform ~2h uptime
  during triage, consistent with a host reboot shortly before the incident — a red herring here,
  but worth recording that `letta-postgres`'s healthcheck is just `pg_isready`
  (`server/compose/letta-compose.sanitized.yml:25`), which would not catch a broken `vector`
  extension/index after a restart. Worth a real check next time archival search misbehaves after
  a host restart.

**Recovery action taken:** re-created the Tranche 1 Batch Reconciliation cohort passage
(`passage-fb47a99b-539b-4ca0-b505-9b29b30e4e37`) on the Specification Advisor Agent
(`agent-58fdfb99-f59c-4d1a-856f-00818994c544`), which had been stripped by a prior stale-version
cleanup and was waiting on this outage to clear. Verified retrievable via `search_archival`
immediately after creation.
