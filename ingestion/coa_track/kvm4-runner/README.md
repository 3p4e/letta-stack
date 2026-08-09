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
