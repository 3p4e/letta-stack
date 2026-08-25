# Enabling the RAGFlow MCP server — KVM4

**Two of the four steps are applied.** `.env` is configured; the compose override
and the container recreate are not, because writing host service configuration was
refused three times by the Claude Code session's permission policy. Nothing is
functionally changed yet — the MCP server is still off, and the `.env` port change
only takes effect on the next container recreate, where its only effect is to stop
publishing 9382 to the internet.

Mode is **self-host**, as instructed. Access control is deliberately deferred:

> all access and credential will be sorted in production version and we are far
> from that — owner, 25.08.2026

That is an accepted risk, recorded rather than argued. What it means concretely is
below under *What this does and does not protect*.

Backups are in place:

    /opt/stacks/ragflow/.env.bak.20260825
    /opt/stacks/ragflow/docker-compose.override.yml.bak.20260825

## Applied

| Step | State |
|---|---|
| `SVR_MCP_PORT=127.0.0.1:9382` in `.env` | **done** — was `9382`, i.e. `0.0.0.0` |
| `MCP_HOST_API_KEY=ragflow-…` in `.env` (0600 root) | **done** — read from RAGFlow's own `api_token` table, never transited anywhere |
| `docker-compose.override.yml` | **not applied** — content committed at `server/ragflow/docker-compose.override.yml` |
| `docker compose up -d --no-deps ragflow-cpu` | **not applied** |

## What this does and does not protect

**Does:** the published port is loopback-only, so `http://<vps-ip>:9382/mcp` will
refuse from the internet. Traefik reaches the container over the Docker network,
which is the only path in. The self-host key sits in `.env` at 0600 root, not in
the world-readable override.

**Does not:** self-host mode authenticates no client. Anyone who reaches
`https://ragflow-mcp.srv1231216.hstgr.cloud/mcp` is served as the tenant, with read
access to every dataset. Wildcard DNS is live, so the hostname is guessable in
principle. Before this carries anything that matters, either switch
`--mcp-mode=self-host` to `--mcp-mode=host` — one word, and every client then needs
its own RAGFlow API key, which is also the natural fit for "Claude, other
platforms, and an app I'm building" — or put a Traefik middleware in front of the
router.

## What exists today## What exists today

| | |
|---|---|
| MCP server module | ships in the image at `/ragflow/mcp/server/server.py` |
| Launch flags | **commented out** in `docker-compose.yml` (lines 30–41) |
| Container command | `["--enable-adminserver","--init-model-provider-tables"]` |
| Port 9382 | **published on `0.0.0.0` and `[::]`** — direct to the internet, not via Traefik |
| Listener on 9382 | none — which is the only reason the open port is currently harmless |
| Wildcard DNS | live: `*.srv1231216.hstgr.cloud` resolves, so a new subdomain needs no DNS work |

Tools the server exposes: `ragflow_list_datasets`, `ragflow_retrieval`,
`ragflow_list_chats`. **Retrieval only** — uploading and parsing stay on the HTTP
API.

## The exposure that has to be closed first

`self-host` mode authenticates **no client**. The API key is held server-side and
every caller is served as that tenant. With 9382 published on `0.0.0.0`, a listener
on it is an unauthenticated door to the whole eCoA corpus, reachable by port scan
without knowing any URL — Traefik is not in that path at all.

The fix is one line: bind the published port to loopback. Traefik reaches the
container over the Docker network, so routing through
`ragflow-mcp.srv1231216.hstgr.cloud` still works and nothing else changes.

## Step 1 — `.env` — DONE

Both values are already set. For the record, they were applied as:

```bash
cd /opt/stacks/ragflow
sed -i 's|^SVR_MCP_PORT=9382$|SVR_MCP_PORT=127.0.0.1:9382|' .env
# key read from RAGFlow's own api_token table into a 0600 temp file, appended, temp removed
```

## Step 2 — `docker-compose.override.yml` — TO APPLY

The exact file is committed at `server/ragflow/docker-compose.override.yml`.
Copy it to `/opt/stacks/ragflow/docker-compose.override.yml`.

`command:` replaces the image CMD outright, so the two flags already in use have to
be carried. The existing router also needs an explicit `.service=` once a second
service is defined on the same container, or Traefik cannot choose between them.

```yaml
services:
  ragflow-cpu:
    command:
      - --enable-adminserver
      - --init-model-provider-tables
      - --enable-mcpserver
      - --mcp-host=0.0.0.0
      - --mcp-port=9382
      - --mcp-base-url=http://127.0.0.1:9380
      - --mcp-script-path=/ragflow/mcp/server/server.py
      - --mcp-mode=self-host
      - --mcp-host-api-key=${MCP_HOST_API_KEY}
      - --no-transport-sse-enabled
    environment:
      OAUTHLIB_RELAX_TOKEN_SCOPE: "1"
    labels:
      - traefik.enable=true
      - traefik.http.routers.ragflow.rule=Host(`ragflow.srv1231216.hstgr.cloud`)
      - traefik.http.routers.ragflow.entrypoints=websecure
      - traefik.http.routers.ragflow.tls.certresolver=letsencrypt
      - traefik.http.routers.ragflow.service=ragflow
      - traefik.http.services.ragflow.loadbalancer.server.port=80
      - traefik.http.routers.ragflow-mcp.rule=Host(`ragflow-mcp.srv1231216.hstgr.cloud`)
      - traefik.http.routers.ragflow-mcp.entrypoints=websecure
      - traefik.http.routers.ragflow-mcp.tls.certresolver=letsencrypt
      - traefik.http.routers.ragflow-mcp.service=ragflow-mcp
      - traefik.http.services.ragflow-mcp.loadbalancer.server.port=9382
    volumes:
      - ./llm_factories.json:/ragflow/conf/llm_factories.json:ro
    networks:
      - ragflow
      - ai-net

networks:
  ai-net:
    external: true
```

`--mcp-host=0.0.0.0` binds inside the container only; the host side is loopback
from step 1. Without it the entrypoint defaults to `127.0.0.1` and Traefik cannot
reach it.

## Step 3 — apply

```bash
cd /opt/stacks/ragflow
docker compose config >/dev/null && echo "compose parses"
docker compose up -d --no-deps ragflow-cpu
```

This recreates one container. **RAGFlow is briefly down** while it restarts.

## Step 4 — verify, in this order

```bash
# the listener is inside the container
docker exec ragflow-ragflow-cpu-1 sh -c 'grep -c ":249E" /proc/net/tcp'   # 249E = 9382

# the published port is loopback only — this must NOT show 0.0.0.0
docker port ragflow-ragflow-cpu-1 9382

# from anywhere else on the internet, this must fail to connect
curl -m 5 http://<vps-ip>:9382/mcp ; echo "exit $?"

# through Traefik it must answer
curl -sS -i https://ragflow-mcp.srv1231216.hstgr.cloud/mcp | head -5
```

The third command failing and the fourth answering is the whole point. If the third
succeeds, stop and re-check step 1.

## Step 5 — connect

```
claude mcp add --transport http ragflow https://ragflow-mcp.srv1231216.hstgr.cloud/mcp
```

No `Authorization` header: in self-host mode the key is server-side. That is also
why step 1 is not optional.

## Rollback

```bash
cd /opt/stacks/ragflow
cp .env.bak.20260825 .env
cp docker-compose.override.yml.bak.20260825 docker-compose.override.yml
docker compose up -d --no-deps ragflow-cpu
```

## Rotate first

The key this bakes in is the one still live in git history at commit `83ae904`.
Rotating before enabling means the exposed key is dead and the MCP server carries
the new one, rather than extending the reach of a credential already pending
rotation. After rotating, drop the `83ae904` allowlist entry from `.gitleaks.toml`.
