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

app = FastAPI(title="kvm4-runner", version="1.0.0")
docker_client = docker.from_env()


def authn(authorization: Optional[str] = Header(None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    if authorization[7:] != TOKEN:
        raise HTTPException(403, "Invalid token")


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
    return (
        "kvm4-runner\n"
        "  GET  /health\n"
        "  GET  /info             (Bearer)\n"
        "  POST /exec             (Bearer)\n"
        "  POST /exec/stream      (Bearer)\n"
        "  POST /shell            (Bearer)\n"
        "  POST /file/read        (Bearer)\n"
        "  POST /file/write       (Bearer)\n"
    )


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
        while True:
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
    p = Path(req.path)
    if req.mkdir:
        p.parent.mkdir(parents=True, exist_ok=True)
    data = base64.b64decode(req.content_b64)
    p.write_bytes(data)
    p.chmod(req.mode)
    return {"path": str(p), "bytes": len(data)}
