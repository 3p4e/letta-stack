# network-shared — persist the cross-stack Docker network on KVM4

## What this is

On KVM4 (Hostinger VPS 1231216), each compose stack runs on its own bridge
network by default, so containers in `letta` can't resolve containers in
`coa_tracker_app` or `qdrant` by name. To fix that, a single external
bridge network called `shared` was created and every running container was
attached to it via a one-shot bootstrap stack:

```yaml
# claude-net-fix-v2 — one-shot stack, docker.sock mounted
services:
  net-fix:
    image: docker:cli
    volumes: ["/var/run/docker.sock:/var/run/docker.sock"]
    command:
      - sh
      - -c
      - |
        docker network create --driver bridge shared || true
        for cid in $$(docker ps -q); do
          mode=$$(docker inspect -f '{{.HostConfig.NetworkMode}}' "$$cid")
          [ "$$mode" = "host" ] && continue
          docker network connect shared "$$cid" 2>/dev/null || true
        done
```

Result (verified 2026-05-22): 17 containers on `172.16.23.0/24`, 2 skipped
(`qms-api`, `traefik-traefik-1` — they use `network_mode: host`).

**The shared network is non-persistent.** When `docker compose down` runs
against any stack, that stack's containers lose their `shared` attachment.
The patches in this directory make the membership permanent.

## What's in here

- `before/` — original docker-compose.yml content pulled via
  `GET https://developers.hostinger.com/api/vps/v1/virtual-machines/1231216/docker/<stack>`
  on 2026-05-22 at 19:31 UTC. Treat as the source of truth at that moment.
- `after/` — same files with two changes:
  1. `shared` appended to every service's `networks:` list (skipping
     services declared with `network_mode: host`)
  2. top-level `networks: { shared: { external: true } }` added so compose
     references — instead of creating — the network
- `patch_compose_for_shared_network.py` — the script that produced
  `after/` from `before/`. Re-runnable.

## How to apply on KVM4

The Hostinger API exposes `GET /docker/<stack>` (read-only) but no write
endpoint for compose content. You have to apply via SSH or the hPanel
file editor. For each stack:

```bash
# on KVM4 as the user that owns /opt/stacks (root for the managed ones)
STACK=letta
PATH_=/opt/stacks/$STACK/docker-compose.yml      # see GET /docker for the real path
cp $PATH_ $PATH_.bak
# upload after/$STACK.yml to $PATH_
docker compose -f $PATH_ up -d
```

Repeat for each `after/*.yml` whose original lives at the path returned by
`GET /docker/<stack>`. Stacks with paths under `/docker/` (e.g.
`/docker/agent-zero-t4sx/docker-compose.yml`) are Hostinger's hPanel
stacks; for those the hPanel UI's compose editor is usually easier.

## Caveats

- `visual-studio-code-server-7gqe` is **not patched** — its existing
  compose file has malformed YAML upstream (a `devices`/`cap_add` block
  landed under `networks:` instead of the service). Fix the indentation
  first, then re-run the patcher.
- `qms-api` is declared in `letta/docker-compose.yml` with
  `networks: [letta_stack]`, but the running container shows
  `network_mode: host`. The patch adds `shared` to its declared
  `networks:`. After recreate, `qms-api` will run on `letta_stack +
  shared` instead of `host`. That's almost certainly fine — `qms-api`
  reaches `letta-daemon` and `gotenberg` by DNS — but verify before
  rolling out.
- The `traefik` stack uses `network_mode: host` for the running
  container; it isn't in this patch set. Cross-container DNS doesn't
  matter for traefik (it routes to host ports), so no action needed.

## Why not just re-run the bootstrap stack after each compose-down?

That works as a recovery mechanism but it's a side-channel that drifts
from the declared state. The compose-file change makes the intent
explicit and survives node reboots without manual intervention.
