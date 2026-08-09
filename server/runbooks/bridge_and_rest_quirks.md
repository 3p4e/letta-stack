# Letta access quirks — bridge (letta-mcp-rust :6507) and REST (verified 2026-08-08)

Three access paths, in order of reliability:
1. **Direct REST** — `curl -H "Authorization: Bearer $LETTA_API_KEY" "${LETTA_UI%/}/v1/…"`.
2. **MCP bridge** (`Letta_KVM4_MCP`, letta-mcp-rust :6507) — agent messaging, `run_from_source`,
   source/memory reads (with the caveats below).
3. **Hostinger VPS API** — infra facts without SSH:
   `GET https://developers.hostinger.com/api/vps/v1/virtual-machines/1231216/docker`.

## Bridge quirks (all reproduced live)

- `letta_tool_manager list` / `list_tools` fail with `missing field 'package'` → tool
  enumeration only via REST.
- `get_block` / `get_block_by_label` truncate values at ~500 chars → full block text via REST
  `GET /v1/blocks/<id>`.
- `letta_source_manager list` reports `attached_agent_count: 0` / `file_count: 0` for every
  source — aggregates are unreliable; use per-source `list_files` / `list_agents_using`.
  `list_folders`/`get_folder_contents` are advertised but not implemented server-side.
- The bridge's MCP prefix flaps between `mcp__Letta_KVM4_MCP__*` and a UUID prefix when the
  connector re-registers — re-discover by keyword, don't hardcode.
- Streaming `send_message` can return empty while `async_message` works.
- `open_file` and `reset_messages` return HTTP 405 on this Letta build.

## `run_from_source` contract (ad-hoc code inside the Letta sandbox)

- `operation: "run_from_source"` on `letta_tool_manager` (bridge) or `POST /v1/tools/run` (REST).
- `tool_args` MUST be a JSON object (even `{}`); the function docstring MUST include an
  `Args:` section describing every parameter (schema is derived from it) or the call 400s.
- Pass `return_char_limit` (bridge) for large returns; the REST endpoint caps returns at
  **50,000 chars** (it appends a truncation NOTE) → slice big payloads at ≤ 40,000 chars.
- Sandbox capabilities: write access to `/root/.letta/*`, `curl`, outbound network
  (github.com reachable, `gotenberg:3000` reachable), **no git, no GitHub token**.
- Transfers into the sandbox: chunk ≤ ~5 KB with per-chunk SHA when payloads are big — a ~32 KB
  arg payload has corrupted in transit before. Always hash-gate before installing anything.

## REST quirks

- Trailing-slash `/v1/sources/<id>/files/` 307-redirects to `http://` and dies at proxies —
  use the no-trailing-slash form.
- Agent-get `memory` can return `[]` even when blocks are attached — cross-check with
  `list_agents_using_block`.
- Embedding fleet: everything new should use `openai/text-embedding-3-small` (1536d, chunk 300).
  Known exceptions that CANNOT cross-search with the rest: the "PQ1 Water Testing Results
Report" source (text-embedding-3-large), `pq1_water_qc_agent` archives (voyage-3-large 1024d),
  `ecoa-qc-agent` archives (letta-free 1024d).
