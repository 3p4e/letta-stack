# docengine.app.letta — thin DIRECT-REST Letta client.
#
# Deliberately not the Rust MCP bridge: the handover-documented decode bug
# ("missing field `package`" on tool get, config writes rejected) reproduced
# in this project — plain REST against /v1 works and is what the live tools
# themselves assume. Only the endpoints the DocEngine needs, nothing more.
from __future__ import annotations

from typing import Any

import httpx

from .config import settings


class LettaError(RuntimeError):
    pass


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

    async def _req(self, method: str, path: str, **kw) -> Any:
        if not self.configured:
            raise LettaError("Letta not configured")
        async with self._client() as c:
            r = await c.request(method, path, **kw)
            if r.status_code >= 400:
                raise LettaError(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
            if not r.content:
                return None
            return r.json()

    # ---- reads ----
    async def list_agents(self, name: str | None = None) -> list[dict]:
        params = {"name": name} if name else None
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
        return await self._req("POST", "/agents/", json=spec)

    async def attach_source(self, agent_id: str, source_id: str) -> None:
        await self._req(
            "PATCH", f"/agents/{agent_id}/sources/attach/{source_id}"
        )

    async def delete_agent(self, agent_id: str) -> None:
        """Delete an agent by id. Callers must only pass ids of agents they
        themselves created (e.g. spawn_ephemeral's short-lived clones) — this
        has no name guard because the delete path only ever sees an id."""
        await self._req("DELETE", f"/agents/{agent_id}")

    # ---- conversation ----
    async def send_message(self, agent_id: str, text: str) -> str:
        """Send one user message; return the agent's assistant text reply."""
        out = await self._req(
            "POST",
            f"/agents/{agent_id}/messages",
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
