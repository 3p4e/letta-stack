# docengine.app.ragflow — the DocEngine's link to the RAGFlow knowledge bases on KVM4.
#
#   regulatory  DB01_REG   EudraLex Vol. 4, EU GDP, ICH, WHO, MK law, Ph. Eur. — the corpus a
#                          drafted section is checked against; findings cite these passages.
#   ecoa        eCOA_INGEST certificates of analysis (482; eCOA_DB is retired) — LOOKUP ONLY: which certificate
#                          exists for a batch. The dataset's own rule: never read a measured
#                          value out of chunk text (it drops superscripts and truncates ranges);
#                          values come from the typed, double-read extraction.
#   examples    DB3_PP_CURRENT  the approved, in-use house documents (text of the Word file, one entry per code +
#                          version) the authors consult for structure and style. PUT /reference indexes them here.
#
# One HTTP call: POST {RAGFLOW_BASE_URL}/api/v1/retrieval with the tenant API key.
from __future__ import annotations

import re

import httpx

from .config import settings

ECOA_NOTE = ("eCOA_INGEST passages identify certificates; they are not a source of values. Take any "
             "measured value from the typed extraction (two independent reads), never from chunk text.")
EXAMPLES_NOTE = ("House examples for structure, wording style and layout only. Never copy a value, "
                 "batch, name, date or result from them into the new document.")


class RagflowError(RuntimeError):
    pass


_NOT_FOUND = re.compile(r"HTTP 404|not found|not exist|doesn't exist|no such", re.I)


def corpus_datasets(corpus: str) -> tuple:
    return {"regulatory": settings.ragflow_reg_datasets,
            "ecoa": settings.ragflow_ecoa_datasets,
            "examples": settings.ragflow_example_datasets}.get(corpus, ())


class RagflowClient:
    def __init__(self, base: str | None = None, key: str | None = None, transport: httpx.AsyncBaseTransport | None = None):
        self.base = (base if base is not None else settings.ragflow_base).rstrip("/")
        self.key = key if key is not None else settings.ragflow_key
        self._transport = transport

    @property
    def configured(self) -> bool:
        return bool(self.base and self.key)

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.base, transport=self._transport,
                                 headers={"Authorization": f"Bearer {self.key}"},
                                 timeout=httpx.Timeout(60.0, connect=10.0))

    async def retrieve(self, question: str, dataset_ids, top_n: int | None = None,
                       keyword: bool = False, threshold: float = 0.2) -> list[dict]:
        """Passages for `question` from the given datasets, best first:
        [{text, document, dataset, page, similarity, chunk_id}]."""
        ids = [d for d in (dataset_ids or ()) if d]
        if not self.configured:
            raise RagflowError("RAGFlow not configured: set RAGFLOW_BASE_URL and RAGFLOW_API_KEY")
        if not ids or not question.strip():
            return []
        body = {"question": question[:2000], "dataset_ids": ids, "page": 1,
                "page_size": top_n or settings.ragflow_top_n, "similarity_threshold": threshold,
                "vector_similarity_weight": 0.3, "top_k": 1024, "keyword": keyword}
        try:
            async with self._client() as c:
                r = await c.post("/api/v1/retrieval", json=body)
        except httpx.HTTPError as e:
            raise RagflowError(f"RAGFlow unreachable: {e}") from e
        if r.status_code != 200:
            raise RagflowError(f"RAGFlow HTTP {r.status_code}: {r.text[:200]}")
        try:
            j = r.json()
        except ValueError as e:
            raise RagflowError(f"RAGFlow returned non-JSON: {r.text[:120]!r}") from e
        if not isinstance(j, dict):
            raise RagflowError("RAGFlow returned an unexpected body")
        if j.get("code", 0) != 0:
            raise RagflowError(f"RAGFlow error {j.get('code')}: {str(j.get('message') or '')[:200]}")
        out = []
        for ch in (j.get("data") or {}).get("chunks", []):
            pos = ch.get("positions") or []
            out.append({
                "text": (ch.get("content") or "").strip(),
                "document": ch.get("document_name") or ch.get("document_keyword") or ch.get("document_id", ""),
                "dataset": ch.get("dataset_name") or ch.get("dataset_id") or ch.get("kb_id", ""),
                "page": pos[0][0] if pos and isinstance(pos[0], (list, tuple)) and pos[0] else None,
                "similarity": round(float(ch.get("similarity") or 0), 3),
                "chunk_id": ch.get("id", ""),
            })
        return out

    async def _json(self, r: httpx.Response) -> dict:
        if r.status_code != 200:
            raise RagflowError(f"RAGFlow HTTP {r.status_code}: {r.text[:200]}")
        j = r.json()
        if j.get("code", 0) != 0:
            raise RagflowError(f"RAGFlow error {j.get('code')}: {str(j.get('message') or '')[:200]}")
        return j

    async def index_text(self, dataset_id: str, filename: str, text: str, replace_id: str = "") -> str:
        """Upload `text` as one document of `dataset_id`, start its parsing, and return the new document id.
        `replace_id`, the document an earlier version of the same text was, is deleted first."""
        if not self.configured:
            raise RagflowError("RAGFlow not configured: set RAGFLOW_BASE_URL and RAGFLOW_API_KEY")
        async with self._client() as c:
            if replace_id:
                try:
                    await self._json(await c.request("DELETE", f"/api/v1/datasets/{dataset_id}/documents",
                                                     json={"ids": [replace_id]}))
                except RagflowError as e:
                    # The earlier entry is already gone (deleted in RAGFlow, or a failed upload left a stale id): the
                    # point of the delete is met. Anything else (RAGFlow down) still fails (review 19.10.2026).
                    if not _NOT_FOUND.search(str(e)):
                        raise
            j = await self._json(await c.post(f"/api/v1/datasets/{dataset_id}/documents",
                                              files={"file": (filename, text.encode("utf-8"), "text/markdown")}))
            data = j.get("data") or []
            doc_id = (data[0] if isinstance(data, list) and data else data or {}).get("id", "")
            if not doc_id:
                raise RagflowError("RAGFlow upload returned no document id")
            await self._json(await c.post(f"/api/v1/datasets/{dataset_id}/chunks", json={"document_ids": [doc_id]}))
        return doc_id

    async def reachable(self) -> bool:
        if not self.configured:
            return False
        try:
            async with self._client() as c:
                r = await c.get("/api/v1/datasets", params={"page": 1, "page_size": 1})
            return r.status_code == 200 and r.json().get("code", 0) == 0
        except Exception:  # noqa: BLE001 — a health probe never raises
            return False


def format_passages(passages: list[dict], tag: str = "R", max_chars: int = 1200) -> str:
    """Numbered passages for a prompt: '[R1] <document>, p. <n>' then the text."""
    blocks = []
    for i, p in enumerate(passages, 1):
        where = p["document"] + (f", p. {p['page']}" if p.get("page") else "")
        text = p["text"] if len(p["text"]) <= max_chars else p["text"][:max_chars] + " …"
        blocks.append(f"[{tag}{i}] {where}\n{text}")
    return "\n\n".join(blocks)


def citations(passages: list[dict], tag: str = "R") -> list[dict]:
    """What the job result keeps for traceability: which passage each [R#] was."""
    return [{"ref": f"{tag}{i}", "document": p["document"], "page": p.get("page"),
             "chunk_id": p["chunk_id"], "similarity": p["similarity"]} for i, p in enumerate(passages, 1)]
