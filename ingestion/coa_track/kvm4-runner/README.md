# kvm4-runner

Tiny FastAPI service deployed on KVM4 that gives an authorized HTTPS client
shell-equivalent access to the box: `docker exec` into any container, run
host shell commands, read/write files.  It exists because Claude Code on the
web cloud sessions cannot reach KVM4 over SSH (outbound :22 is blocked by the
cloud-session egress policy), and we want a stable way to drive KVM4 from any
future session without hand-piloting through Hostinger's compose UI.

## Endpoints

All non-`/health` endpoints require `Authorization: Bearer $RUNNER_TOKEN`.

| Method | Path             | Body                                                | Returns                          |
|--------|------------------|-----------------------------------------------------|----------------------------------|
| GET    | `/health`        | —                                                   | `{"ok": true, ...}`              |
| GET    | `/info`          | —                                                   | host + container inventory       |
| POST   | `/exec`          | `{"container":"letta","cmd":"...","timeout":600}`   | `{"exit_code","output",...}`     |
| POST   | `/exec/stream`   | same as `/exec`                                     | `text/plain` chunked output      |
| POST   | `/shell`         | `{"cmd":"...","workdir":null,"timeout":600}`        | `{"exit_code","output",...}`     |
| POST   | `/file/read`     | `{"path":"...","max_bytes":1000000}`                | `{"content_b64",...}`            |
| POST   | `/file/write`    | `{"path":"...","content_b64":"...","mode":420}`     | `{"path","bytes"}`               |

## First deployment

The runner is its own bootstrap problem: we need a runner to push files, but
we have no runner yet.  `deploy.py` resolves it by inlining `runner.py` as a
heredoc inside the compose `command:` and pushing the whole stack via the
Hostinger VPS API.  After the first deploy succeeds, every subsequent change
to `runner.py` can be applied through the runner itself.

```bash
export HOSTINGER_API_KEY=...
python3 scripts/kvm4-runner/deploy.py
# token printed to stdout — copy it
```

## Using the runner from a new cloud session

```bash
export RUNNER_URL=https://runner.srv1231216.hstgr.cloud
export RUNNER_TOKEN=...     # from deploy output

# Run a command in the letta container
curl -sS -X POST -H "Authorization: Bearer $RUNNER_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"container":"letta","cmd":"ls /root/.letta | head"}' \
     "$RUNNER_URL/exec" | jq .

# Run a command on the host
curl -sS -X POST -H "Authorization: Bearer $RUNNER_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"cmd":"docker ps --format \"{{.Names}}\\t{{.Status}}\""}' \
     "$RUNNER_URL/shell" | jq -r .output

# Pull repo updates
curl -sS -X POST -H "Authorization: Bearer $RUNNER_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"cmd":"cd /opt/CoA_TRACK && git pull"}' \
     "$RUNNER_URL/shell" | jq -r .output
```

## Security notes

- The runner has `/var/run/docker.sock` and `/opt` mounted.  Anyone holding
  the token has root-on-host equivalent.  Store the token like an SSH key.
- TLS is provided by Traefik via Let's Encrypt — no plain HTTP.
- The token is required to be ≥24 chars (`deploy.py` defaults to 48).
- Rotate the token by re-running `deploy.py` with a new `RUNNER_TOKEN` env
  var; the running stack will be updated in place.
- To revoke access entirely, `POST /docker/kvm4-runner/stop` via Hostinger
  API or delete the stack.

### Hardening applied 2026-08-29

- **Constant-time token compare.**  The check was a plain `!=` on `str`, which
  short-circuits at the first differing byte and leaks the prefix to a timing
  oracle; it now uses `hmac.compare_digest`.  The 401/403 split was collapsed
  into one 401 — the old split confirmed to a guesser when the header *shape*
  was right and only the secret was wrong.
- **Writes are confined to a root.**  `/file/write` took any absolute path,
  created parents and chmod'd to a caller-supplied mode, so it could rewrite the
  runner's own source under `/opt` and silently redefine the service.  The
  target is now `resolve()`d (collapsing `..` and following symlinks) and must
  sit under `RUNNER_WRITE_ROOT`, default `/opt`.  The documented self-update path
  still works; `/etc`, `/root` and `/usr` no longer do.
- **Privileged calls are logged.**  `/file/read` and `/file/write` previously
  logged nothing at all, so arbitrary host file access left no trace.  Both now
  emit a log line, and a refused write is logged as a warning.
- **`/exec/stream` has a deadline** (`RUNNER_STREAM_TIMEOUT`, default 600s).
  `/exec` and `/shell` both bounded their runtime; this one did not, so a hung
  command held the worker and the docker exec open indefinitely.
- **No endpoint inventory is served anonymously.**  `GET /` returned the full
  list of privileged endpoints, and FastAPI's `/docs`, `/redoc` and
  `/openapi.json` were left enabled — a machine-readable map of every route and
  request body, free to any scanner.  All four are off; the endpoint table above
  is the reference.
- **The token is printed at most once**, and only when `deploy.py` generated it.
  It was previously echoed twice per deploy.

**Still open — these need a host action, not a code change:**

- The token is interpolated in plaintext into the compose YAML that is POSTed to
  and stored by the Hostinger API.  A repo change cannot fix that.
- There is no IP allowlist, rate limit or lockout, and no token expiry.  A
  Traefik IP-allowlist middleware on this router is the cheapest real
  improvement; see `docs/wwf_MASTER-PLAN-2026-08.md:191`.
- **Editing this file changes nothing on the running service.**  `deploy.py`
  inlines `runner.py` as a heredoc, so the deployed code can drift from this
  copy and nothing verifies it.  Diff before and after, and redeploy for any of
  the above to take effect.
