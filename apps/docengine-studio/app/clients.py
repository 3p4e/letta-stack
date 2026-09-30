# docengine_studio.app.clients - thin upstream clients (DocEngine Line B + Letta).
# Direct REST only: the Rust MCP bridge is unreliable per server/runbooks.
from __future__ import annotations

from typing import Any

import httpx

from .config import settings


class UpstreamError(RuntimeError):
    """Upstream transport/status failure; callers map this to HTTP 502."""


class DocEngineClient:
    """Async client for the Line B GrowFlow DocEngine (apps/wwf-docengine)."""

    def __init__(self) -> None:
        self.endpoint = settings.docengine_endpoint
        self.key = settings.docengine_key

    def _headers(self) -> dict[str, str]:
        return {"X-API-Key": self.key} if self.key else {}

    @staticmethod
    def _handle(r: httpx.Response) -> Any:
        if r.status_code >= 500:
            raise UpstreamError("upstream %s: %s" % (r.status_code, r.text[:200]))
        if r.status_code == 422:
            # Preserve the verify report: the UI renders it as QC feedback.
            try:
                detail = r.json().get("detail", r.text)
            except Exception:  # noqa: BLE001
                detail = r.text
            return {"__status__": 422, "detail": detail}
        if r.status_code == 404:
            return {"__status__": 404, "detail": "not found upstream"}
        r.raise_for_status()
        return r.json()

    async def _get(self, path: str) -> Any:
        async with httpx.AsyncClient(timeout=60.0) as c:
            r = await c.get(self.endpoint + path, headers=self._headers())
            return self._handle(r)

    async def _post(self, path: str, payload: dict) -> Any:
        async with httpx.AsyncClient(timeout=90.0) as c:
            r = await c.post(self.endpoint + path, json=payload, headers=self._headers())
            return self._handle(r)

    async def health(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10.0) as c:
                r = await c.get(self.endpoint + "/health")
                return r.json() if r.status_code == 200 else {"ok": False, "code": r.status_code}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": str(e)[:160]}

    # --- pass-through surface ---
    async def list_questionnaires(self) -> dict:
        return await self._get("/questionnaires")

    async def get_questionnaire(self, key: str) -> dict:
        return await self._get("/questionnaires/" + key)

    async def start_workflow(self, body: dict) -> dict:
        return await self._post("/workflows", body)

    async def get_workflow(self, jid: str) -> dict:
        return await self._get("/workflows/" + jid)

    async def build(self, body: dict) -> dict:
        return await self._post("/build", body)

    async def list_documents(self) -> dict:
        return await self._get("/documents")

    async def get_document(self, did: str) -> dict:
        return await self._get("/documents/" + did)

    async def _binary(self, path: str, timeout: float) -> tuple[int, str, bytes]:
        async with httpx.AsyncClient(timeout=timeout) as c:
            r = await c.get(self.endpoint + path, headers=self._headers())
            return r.status_code, r.headers.get("content-type", ""), r.content

    async def download(self, did: str) -> tuple[int, str, bytes]:
        return await self._binary("/documents/%s/download" % did, 120.0)

    async def pdf(self, did: str) -> tuple[int, str, bytes]:
        return await self._binary("/documents/%s/pdf" % did, 180.0)


class LettaClient:
    """Minimal Letta REST client for the advisory lane (optional)."""

    @property
    def configured(self) -> bool:
        return bool(settings.letta_endpoint and settings.letta_key)

    async def _agent_id(self, name: str) -> str:
        async with httpx.AsyncClient(
            headers={"Authorization": "Bearer " + settings.letta_key},
            timeout=httpx.Timeout(30.0, connect=10.0),
        ) as c:
            r = await c.get(settings.letta_endpoint + "/v1/agents/", params={"name": name})
            r.raise_for_status()
            agents = r.json() or []
            if not agents:
                raise UpstreamError("advisory agent not found: " + name)
            return agents[0]["id"]

    async def send_message(self, text: str, agent: str | None = None) -> str:
        if not self.configured:
            raise UpstreamError("Letta not configured")
        name = agent or settings.letta_advisory_agent
        agent_id = await self._agent_id(name)
        async with httpx.AsyncClient(
            headers={"Authorization": "Bearer " + settings.letta_key},
            timeout=httpx.Timeout(180.0, connect=15.0),
        ) as c:
            r = await c.post(
                settings.letta_endpoint + "/v1/agents/" + agent_id + "/messages",
                json={"messages": [{"role": "user", "content": text}]},
            )
            r.raise_for_status()
            msgs = (r.json() or {}).get("messages", [])
        parts: list[str] = []
        for m in msgs:
            t = m.get("message_type") or m.get("role")
            if t in ("assistant_message", "assistant"):
                content = m.get("content")
                if isinstance(content, str):
                    parts.append(content)
                elif isinstance(content, list):
                    parts.extend(x.get("text", "") for x in content if isinstance(x, dict))
        return "\n".join(p for p in parts if p).strip()
