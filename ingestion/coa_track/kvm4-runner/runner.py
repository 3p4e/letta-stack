"""
kvm4-runner — minimal HTTPS-exposed command runner for KVM4.

Lets a remote Claude Code session (or any authorized client) execute commands
inside containers on KVM4 and read/write files on the host, authenticated with
a long bearer token.  Traefik provides TLS termination at
runner.srv1231216.hstgr.cloud; everything below that subdomain requires the
token.

Endpoints
---------
GET  /health                public           liveness
GET  /info                  bearer           host + container inventory
POST /exec                  bearer           docker exec in a container
POST /exec/stream           bearer           docker exec, streamed output
POST /shell                 bearer           sh -c on the runner host (sees /opt, docker.sock)
POST /file/read             bearer           read host file (base64)
POST /file/write            bearer           write host file (base64)

Why a runner rather than SSH
----------------------------
Outbound port 22 is blocked from the Claude Code on the web cloud session.
HTTPS through Traefik works in every network policy.  The same surface area
that SSH would give us (run shell, exec in a container, move files) is
exposed here as JSON-over-HTTPS instead.
"""
from __future__ import annotations

import asyncio
import base64
import hmac
import logging
import os
import time
from pathlib import Path
from typing import Optional

import docker
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("kvm4-runner")

TOKEN = os.environ.get("RUNNER_TOKEN", "")
if len(TOKEN) < 24:
    raise SystemExit("RUNNER_TOKEN env var must be >=24 chars")

# Cap returned output so a runaway command can't blow up the response
MAX_OUTPUT = int(os.environ.get("RUNNER_MAX_OUTPUT", "2000000"))  # 2 MB

# /exec/stream had no timeout at all while /exec and /shell both enforce one, so a
# hung stream held a worker open indefinitely. Same default as those two.
STREAM_TIMEOUT = int(os.environ.get("RUNNER_STREAM_TIMEOUT", "600"))

# /file/write accepts an absolute path, creates parents and chmods to a
# caller-supplied mode. With /opt mounted read-write that reached anywhere on the
# host the container can see — including this service's own source, so a token
# holder could silently redefine the runner. Confine writes to one root. The
# default keeps the documented self-update path (/opt/stacks/kvm4-runner/) working
# while putting /etc, /root and /usr out of reach.
WRITE_ROOT = Path(os.environ.get("RUNNER_WRITE_ROOT", "/opt")).resolve()

# docs_url/redoc_url/openapi_url default to enabled, which published a
# machine-readable schema of every privileged endpoint — including request-body
# shapes — to anyone who could reach the host. Nothing consumes them.
app = FastAPI(title="kvm4-runner", version="1.0.0",
              docs_url=None, redoc_url=None, openapi_url=None)
docker_client = docker.from_env()


def authn(authorization: Optional[str] = Header(None)) -> None:
    """Bearer gate.

    Two deliberate properties, both previously absent:
      * constant-time compare — a plain `!=` on str short-circuits at the first
        differing byte, which leaks the token prefix to a timing oracle. Same
        primitive the docengine uses (apps/wwf-docengine/app/security.py:16).
      * one uniform 401 — the old 401-vs-403 split told an attacker when the
        header *shape* was right and only the secret was wrong, which is exactly
        the signal a guesser wants.
    """
    supplied = authorization[7:] if (authorization or "").startswith("Bearer ") else ""
    if not hmac.compare_digest(supplied, TOKEN):
        raise HTTPException(401, "Invalid or missing bearer token")


class ExecReq(BaseModel):
    container: str
    cmd: str
    workdir: Optional[str] = None
    env: dict[str, str] = Field(default_factory=dict)
    timeout: int = 600


class ShellReq(BaseModel):
    cmd: str
    workdir: Optional[str] = None
    timeout: int = 600


class FileReadReq(BaseModel):
    path: str
    max_bytes: int = 1_000_000


class FileWriteReq(BaseModel):
    path: str
    content_b64: str
    mode: int = 0o644
    mkdir: bool = True


@app.get("/health")
def health() -> dict:
    return {"ok": True, "ts": time.time(), "service": "kvm4-runner"}


@app.get("/", response_class=PlainTextResponse)
def root() -> str:
    # Was an unauthenticated inventory of every privileged endpoint — a complete
    # attack-surface map handed to any scanner that resolved the hostname. The
    # endpoint list lives in README.md, which is the right place for it.
    return "kvm4-runner\n"


@app.get("/info", dependencies=[Depends(authn)])
def info() -> dict:
    u = os.uname()
    return {
        "host": {
            "sysname": u.sysname,
            "nodename": u.nodename,
            "release": u.release,
            "version": u.version,
            "machine": u.machine,
        },
        "containers": [
            {
                "name": c.name,
                "status": c.status,
                "image": (c.image.tags[0] if c.image.tags else c.image.id[:12]),
            }
            for c in docker_client.containers.list(all=True)
        ],
        "ts": time.time(),
    }


@app.post("/exec", dependencies=[Depends(authn)])
async def exec_(req: ExecReq) -> dict:
    log.info("exec container=%s cmd=%r", req.container, req.cmd[:200])
    try:
        container = docker_client.containers.get(req.container)
    except docker.errors.NotFound:
        raise HTTPException(404, f"container {req.container!r} not found")

    loop = asyncio.get_running_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: container.exec_run(
                    ["sh", "-c", req.cmd],
                    workdir=req.workdir,
                    environment=req.env or None,
                    demux=False,
                    stream=False,
                ),
            ),
            timeout=req.timeout,
        )
    except asyncio.TimeoutError:
        raise HTTPException(504, f"exec timed out after {req.timeout}s")

    out = result.output.decode("utf-8", errors="replace") if result.output else ""
    return {
        "exit_code": result.exit_code,
        "output": out[-MAX_OUTPUT:],
        "truncated": len(out) > MAX_OUTPUT,
        "bytes": len(out),
    }


@app.post("/exec/stream", dependencies=[Depends(authn)])
async def exec_stream(req: ExecReq) -> StreamingResponse:
    log.info("exec/stream container=%s cmd=%r", req.container, req.cmd[:200])
    try:
        container = docker_client.containers.get(req.container)
    except docker.errors.NotFound:
        raise HTTPException(404, f"container {req.container!r} not found")

    _, stream = container.exec_run(
        ["sh", "-c", req.cmd],
        workdir=req.workdir,
        environment=req.env or None,
        stream=True,
    )

    async def agen():
        loop = asyncio.get_running_loop()
        it = iter(stream)
        # Wall-clock deadline. /exec and /shell both bound their runtime; this
        # endpoint did not, so a command that never finished held the worker and
        # the docker exec open forever. Bounded here rather than per-chunk so a
        # slow-but-progressing stream is not killed mid-flight.
        deadline = loop.time() + max(1, min(req.timeout, STREAM_TIMEOUT))
        while True:
            if loop.time() >= deadline:
                log.warning("exec/stream container=%s hit the %ss deadline — cut",
                            req.container, STREAM_TIMEOUT)
                yield b"\n[kvm4-runner] stream deadline reached, output truncated\n"
                break
            chunk = await loop.run_in_executor(None, lambda: next(it, None))
            if chunk is None:
                break
            yield chunk

    return StreamingResponse(agen(), media_type="text/plain")


@app.post("/shell", dependencies=[Depends(authn)])
async def shell(req: ShellReq) -> dict:
    log.info("shell cmd=%r", req.cmd[:200])
    proc = await asyncio.create_subprocess_shell(
        req.cmd,
        cwd=req.workdir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=req.timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise HTTPException(504, f"shell timed out after {req.timeout}s")
    out = stdout.decode("utf-8", errors="replace") if stdout else ""
    return {
        "exit_code": proc.returncode,
        "output": out[-MAX_OUTPUT:],
        "truncated": len(out) > MAX_OUTPUT,
        "bytes": len(out),
    }


@app.post("/file/read", dependencies=[Depends(authn)])
def file_read(req: FileReadReq) -> dict:
    # These two endpoints logged NOTHING, so arbitrary host file reads and writes
    # left no trace at all — the "persistent audit log" half of the open item in
    # docs/wwf_MASTER-PLAN-2026-08.md:191. Every privileged call is recorded now.
    log.info("file/read path=%r max_bytes=%d", req.path, req.max_bytes)
    p = Path(req.path)
    if not p.is_file():
        raise HTTPException(404, f"{req.path} not found")
    data = p.read_bytes()[: req.max_bytes]
    return {
        "path": str(p),
        "size": p.stat().st_size,
        "returned": len(data),
        "content_b64": base64.b64encode(data).decode("ascii"),
    }


@app.post("/file/write", dependencies=[Depends(authn)])
def file_write(req: FileWriteReq) -> dict:
    log.info("file/write path=%r mode=%o mkdir=%s", req.path, req.mode, req.mkdir)
    p = Path(req.path)
    # Resolve BEFORE writing and confirm containment: resolve() collapses `..`
    # and follows symlinks, so neither a traversal nor a planted link escapes.
    # strict=False because the target legitimately may not exist yet.
    resolved = p.resolve(strict=False)
    if resolved != WRITE_ROOT and WRITE_ROOT not in resolved.parents:
        log.warning("file/write REFUSED path=%r (outside %s)", req.path, WRITE_ROOT)
        raise HTTPException(403, f"writes are confined to {WRITE_ROOT}")
    if req.mkdir:
        resolved.parent.mkdir(parents=True, exist_ok=True)
    data = base64.b64decode(req.content_b64)
    resolved.write_bytes(data)
    resolved.chmod(req.mode)
    return {"path": str(resolved), "bytes": len(data)}
