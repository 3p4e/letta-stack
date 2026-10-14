# docengine.app.letta — thin DIRECT-REST Letta client.
#
# Deliberately not the Rust MCP bridge: the handover-documented decode bug
# ("missing field `package`" on tool get, config writes rejected) reproduced
# in this project — plain REST against /v1 works and is what the live tools
# themselves assume. Only the endpoints the DocEngine needs, nothing more.
from __future__ import annotations

import asyncio
import logging
import random
from typing import Any

import httpx

from .config import settings

log = logging.getLogger("docengine.letta")

# Statuses that say "not now", not "no": the server or a proxy in front of it was overloaded or restarting.
_TRANSIENT_STATUS = {429, 502, 503, 504}
# Of those, the ones that mean the request was refused before it was acted on, so even a POST may be re-sent.
_NOT_PROCESSED_STATUS = {429, 503}
# Transport failures where the request never reached the server: safe to re-send whatever the method.
_NOT_SENT = (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout)


class LettaError(RuntimeError):
    """A failed Letta call. `transient` marks a failure worth trying again (a timeout, a reset, 429/502/503/504),
    as opposed to a refusal that will repeat (400, 401, 404, 422)."""

    def __init__(self, msg: str, status: int | None = None, transient: bool = False):
        super().__init__(msg)
        self.status = status
        self.transient = transient


class LettaClient:
    """Async Letta v1 REST client. All fleet mutations are ADDITIVE and
    namespaced gf_* — existing agents are never modified (handover caution)."""

    def __init__(self, base: str | None = None, key: str | None = None, timeout: httpx.Timeout | None = None):
        self.base = (base if base is not None else settings.letta_base).rstrip("/")
        self.key = key if key is not None else settings.letta_key
        # Short connect (fail fast if the server is down) + long read (one
        # agent generation can take minutes). A single float would force the
        # generous read window onto the connect step too.
        self.timeout = timeout or httpx.Timeout(
            settings.letta_read_timeout,
            connect=settings.letta_connect_timeout,
        )

    @property
    def configured(self) -> bool:
        return bool(self.base and self.key)

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base + "/v1",
            headers={"Authorization": f"Bearer {self.key}"},
            timeout=self.timeout,
        )

    # Overridable in tests (no real waiting).
    _sleep = staticmethod(asyncio.sleep)

    def _delay(self, attempt: int, retry_after: str | None) -> float:
        if retry_after:
            try:
                return min(60.0, max(0.0, float(retry_after)))
            except ValueError:
                pass
        base = settings.letta_retry_base
        return base * (2 ** attempt) + random.uniform(0, base / 2)

    async def _req(self, method: str, path: str, *, idempotent: bool | None = None, **kw) -> Any:
        """One Letta call, retried when a retry cannot do harm (review 14.10.2026: one network blip on any of
        ~30 calls used to fail the whole job after up to half an hour of paid generation).

        Re-sent: a request that never reached the server (connect errors), a 429/503 refusal, and, for an
        idempotent call (GET, DELETE, PATCH by default), any timeout, reset or 5xx gateway error. A POST that
        may have been acted on (a message: the agent may still be writing) is not re-sent here; the error is
        marked transient and the pipeline repeats the whole step on a fresh clone instead."""
        if not self.configured:
            raise LettaError("Letta not configured")
        if idempotent is None:
            idempotent = method.upper() in ("GET", "DELETE", "PATCH", "HEAD")
        attempts = 1 + max(0, settings.letta_retries)
        last: LettaError | None = None
        for attempt in range(attempts):
            retry_after = None
            async with self._client() as c:
                try:
                    r = await c.request(method, path, **kw)
                except httpx.HTTPError as e:
                    # A bare httpx.ReadTimeout reads "": the type name goes into the message.
                    last = LettaError(f"{method} {path} -> {type(e).__name__}: {e}", transient=True)
                    if not (idempotent or isinstance(e, _NOT_SENT)):
                        raise last from e
                else:
                    if r.status_code < 400:
                        return r.json() if r.content else None
                    transient = r.status_code in _TRANSIENT_STATUS
                    last = LettaError(f"{method} {path} -> {r.status_code}: {r.text[:300]}",
                                      status=r.status_code, transient=transient)
                    if not transient or not (idempotent or r.status_code in _NOT_PROCESSED_STATUS):
                        raise last
                    retry_after = r.headers.get("retry-after")
            if attempt + 1 < attempts:
                wait = self._delay(attempt, retry_after)
                log.warning("Letta %s %s failed (%s); retry %d/%d in %.1f s", method, path, last, attempt + 1,
                            attempts - 1, wait)
                await self._sleep(wait)
        raise last  # type: ignore[misc]

    # ---- reads ----
    # Letta pages GET /agents/; a fleet agent past the first page would look missing and be created twice.
    LIST_LIMIT = 1000

    async def list_agents(self, name: str | None = None) -> list[dict]:
        params: dict = {"limit": self.LIST_LIMIT}
        if name:
            params["name"] = name
        out = await self._req("GET", "/agents/", params=params)
        return out or []

    async def list_sources(self) -> list[dict]:
        return await self._req("GET", "/sources/") or []

    # ---- additive fleet ops (gf_* only; guarded) ----
    @staticmethod
    def _guard_gf(name: str) -> None:
        if not name.startswith("gf_"):
            raise LettaError(f"refusing to touch non-gf_ agent: {name!r}")

    async def create_agent(self, spec: dict) -> dict:
        self._guard_gf(spec.get("name", ""))
        try:
            return await self._req("POST", "/agents/", json=spec)
        except LettaError as e:
            if not e.transient:
                raise
            # The create may have happened before the connection broke: look before creating again, so a retry
            # never leaves a second agent of the same name.
            found = [a for a in await self.list_agents(name=spec["name"]) if a.get("name") == spec["name"]]
            if found:
                return found[0]
            return await self._req("POST", "/agents/", json=spec)

    async def attach_source(self, agent_id: str, source_id: str) -> None:
        await self._req(
            "PATCH", f"/agents/{agent_id}/sources/attach/{source_id}"
        )

    async def delete_agent(self, agent_id: str) -> None:
        """Delete an agent by id. Callers must only pass ids of agents they
        themselves created (e.g. spawn_ephemeral's short-lived clones) — this
        has no name guard because the delete path only ever sees an id."""
        try:
            await self._req("DELETE", f"/agents/{agent_id}")
        except LettaError as e:
            if e.status != 404:      # already gone (a retried delete that had succeeded) is success
                raise

    # ---- conversation ----
    async def send_message(self, agent_id: str, text: str) -> str:
        """Send one user message; return the agent's assistant text reply."""
        out = await self._req(
            "POST",
            f"/agents/{agent_id}/messages",
            idempotent=False,
            json={"messages": [{"role": "user", "content": text}]},
        )
        # v1 returns {"messages": [...]} with assistant_message entries
        msgs = (out or {}).get("messages", [])
        parts: list[str] = []
        for m in msgs:
            t = m.get("message_type") or m.get("role")
            if t in ("assistant_message", "assistant"):
                c = m.get("content")
                if isinstance(c, str):
                    parts.append(c)
                elif isinstance(c, list):
                    parts.extend(
                        x.get("text", "") for x in c if isinstance(x, dict)
                    )
        return "\n".join(p for p in parts if p).strip()
