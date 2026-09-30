# docengine_studio.app.main - DocEngine Studio gateway.
#
# One authed entry point in front of the Line B DocEngine. The Studio adds:
#   * registry lifecycle + approvals + signatures (additive, upstream untouched)
#   * a hash-chained audit log
#   * lane routing (RAGFlow official / Letta advisory) with fail-closed official lane
#   * model routing with producer/checker separation
#   * machine clients via scopes, and an MCP JSON-RPC surface
#   * a static PWA front-end
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import db, mcp, router, services
from .clients import UpstreamError
from .config import settings
from .security import (
    MACHINE_SCOPES,
    Principal,
    create_api_client,
    create_session,
    current_principal,
    require,
    verify_studio_key,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("studio")

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    db.audit("studio.started", actor="system", payload={"version": "0.1.0"})
    yield
    db.audit("studio.stopped", actor="system")


app = FastAPI(title="DocEngine Studio", version="0.1.0", lifespan=lifespan)


@app.exception_handler(UpstreamError)
async def _upstream_error(request: Request, exc: UpstreamError):
    return JSONResponse(status_code=502, content={"error": "upstream", "detail": str(exc)})


@app.exception_handler(services.LaneUnavailable)
async def _lane_error(request: Request, exc: services.LaneUnavailable):
    return JSONResponse(status_code=503, content={"error": "lane_unavailable", "detail": str(exc)})


# ------------------------------------------------------------------- meta/health

@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "studio": "0.1.0",
        "docengine": await services.upstream_health(),
        "audit": db.audit_verify(),
        "official_lane": bool(settings.ragflow_endpoint and settings.ragflow_key),
        "advisory_lane": bool(settings.letta_endpoint and settings.letta_key),
        "model_provider_ready": settings.model_provider_ready,
    }


@app.get("/api/me")
async def me(principal: Principal = Depends(current_principal)):
    return principal.to_dict()



class SessionIn(BaseModel):
    key: str = Field(min_length=1)


@app.post("/api/session")
async def api_login(body: SessionIn, request: Request, response: Response):
    """Exchange the studio key for a signed HttpOnly cookie session."""
    if not verify_studio_key(body.key):
        db.audit("session.refused", actor="anonymous", subject="login", payload={"reason": "bad key"})
        raise HTTPException(401, "invalid key")
    role = (request.headers.get("x-user-role") or "admin").lower()
    token = create_session(sub="studio-key", role=role, name=request.headers.get("x-user-name", "operator"))
    if token is None:
        raise HTTPException(400, "sessions are not configured on this deployment")
    response.set_cookie(
        settings.session_cookie,
        token,
        max_age=settings.session_ttl,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    db.audit("session.created", actor="studio-key", subject="login")
    return {"ok": True, "role": role, "expires_in": settings.session_ttl}


@app.delete("/api/session")
async def api_logout(response: Response, principal: Principal = Depends(current_principal)):
    response.delete_cookie(settings.session_cookie, path="/")
    db.audit("session.ended", actor=principal.sub, subject="logout")
    return {"ok": True}


# ------------------------------------------------------------------- catalog

@app.get("/api/questionnaires")
async def api_questionnaires(principal: Principal = Depends(require("qms.read"))):
    return {"questionnaires": await services.list_questionnaires(), "_capabilities": principal.to_dict()}


@app.get("/api/questionnaires/{key}")
async def api_questionnaire(key: str, principal: Principal = Depends(require("qms.read"))):
    return await services.get_questionnaire(key)


# ------------------------------------------------------------------- workflows

class WorkflowIn(BaseModel):
    questionnaire: str
    answers: dict = Field(default_factory=dict)
    meta: dict
    document_id: str | None = None


@app.post("/api/workflows")
async def api_start_workflow(body: WorkflowIn, principal: Principal = Depends(require("qms.author"))):
    for k in ("title_mk", "title_en", "code"):
        if not body.meta.get(k):
            raise HTTPException(400, "meta.%s is required" % k)
    return await services.start_workflow(body.model_dump(), principal.sub)


@app.get("/api/workflows/{jid}")
async def api_get_workflow(jid: str, principal: Principal = Depends(require("qms.read"))):
    return await services.get_workflow(jid)


# ------------------------------------------------------------------- build

class BuildIn(BaseModel):
    markdown: str = Field(min_length=20, max_length=400_000)
    out_name: str = Field(default="document", min_length=1, max_length=80)
    meta: dict = Field(default_factory=dict)
    document_id: str | None = None


@app.post("/api/build")
async def api_build(body: BuildIn, principal: Principal = Depends(require("qms.build"))):
    return await services.build_document(body.model_dump(), principal.sub)


# ------------------------------------------------------------------- certificates

@app.get("/api/certificates")
async def api_certificates(principal: Principal = Depends(require("certs.render"))):
    return {"documents": await services.list_certificates()}


@app.get("/api/certificates/{did}")
async def api_certificate(did: str, principal: Principal = Depends(require("certs.render"))):
    return await services.get_certificate(did)


@app.get("/api/certificates/{did}/download")
async def api_certificate_download(did: str, principal: Principal = Depends(require("certs.render"))):
    status, ctype, body = await services.fetch_artifact(did, "docx")
    if status >= 400:
        raise HTTPException(status, "artifact unavailable upstream")
    return Response(
        content=body,
        media_type=ctype or "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=\"%s.docx\"" % did},
    )


@app.get("/api/certificates/{did}/pdf")
async def api_certificate_pdf(did: str, principal: Principal = Depends(require("certs.render"))):
    status, ctype, body = await services.fetch_artifact(did, "pdf")
    if status >= 400:
        raise HTTPException(status, "PDF renderer unavailable for this document")
    return Response(content=body, media_type=ctype or "application/pdf")


# ------------------------------------------------------------------- registry

class RegistryIn(BaseModel):
    title: str
    doc_type: str | None = None
    questionnaire_key: str | None = None
    language: str = "MK"
    revision: str | None = None


@app.get("/api/registry")
async def api_registry(status: str | None = None, limit: int = 200, principal: Principal = Depends(require("qms.read"))):
    return {"documents": services.list_registry(status, limit)}


@app.post("/api/registry")
async def api_registry_create(body: RegistryIn, principal: Principal = Depends(require("qms.author"))):
    try:
        return services.create_registry_entry(body.model_dump(), principal.sub)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/registry/{doc_id}")
async def api_registry_get(doc_id: str, principal: Principal = Depends(require("qms.read"))):
    entry = services.get_registry_entry(doc_id)
    if not entry:
        raise HTTPException(404, "no such document")
    return entry


class StatusIn(BaseModel):
    status: str
    comment: str | None = None


@app.post("/api/registry/{doc_id}/status")
async def api_registry_status(doc_id: str, body: StatusIn, principal: Principal = Depends(require("qms.author"))):
    try:
        return services.update_registry_status(doc_id, body.status, principal.sub, body.comment)
    except KeyError:
        raise HTTPException(404, "no such document")
    except ValueError as e:
        raise HTTPException(409, str(e))


# ------------------------------------------------------------------- approval

class ApprovalIn(BaseModel):
    decision: str
    comment: str | None = None
    version: int | None = None


@app.get("/api/registry/{doc_id}/approvals")
async def api_approvals(doc_id: str, principal: Principal = Depends(require("qms.read"))):
    return services.list_approvals(doc_id)


@app.post("/api/registry/{doc_id}/approvals")
async def api_approval(doc_id: str, body: ApprovalIn, principal: Principal = Depends(require("qms.approve"))):
    if principal.kind != "human":
        raise HTTPException(403, "machine clients may not approve documents")
    try:
        result = services.add_approval(doc_id, body.decision, principal.sub, principal.role or "qa_approver", body.comment, body.version)
    except KeyError:
        raise HTTPException(404, "no such document")
    except ValueError as e:
        raise HTTPException(400, str(e))
    # approval implies lifecycle movement
    if body.decision == "approved":
        try:
            services.update_registry_status(doc_id, "approved", principal.sub, body.comment)
        except ValueError:
            pass
    return result


class SignatureIn(BaseModel):
    meaning: str
    sha256: str | None = None
    version: int | None = None


@app.post("/api/registry/{doc_id}/signatures")
async def api_signature(doc_id: str, body: SignatureIn, principal: Principal = Depends(require("qms.sign"))):
    if principal.kind != "human":
        raise HTTPException(403, "only a named human may sign")
    try:
        return services.add_signature(doc_id, body.meaning, principal.sub, body.sha256, body.version)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ------------------------------------------------------------------- audit

@app.get("/api/audit")
async def api_audit(limit: int = 100, principal: Principal = Depends(require("audit.read"))):
    return {"events": services.audit_tail(limit), "chain": db.audit_verify()}


# ------------------------------------------------------------------- routing

@app.get("/api/routing/lanes")
async def api_lanes(principal: Principal = Depends(require("qms.read"))):
    return {"routes": router.all_lane_routes()}


@app.get("/api/routing/models")
async def api_models(principal: Principal = Depends(require("qms.read"))):
    return {"routes": router.all_model_routes(), "provider_ready": settings.model_provider_ready}


# ------------------------------------------------------------------- assistant

class AskIn(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    intent: str = "qa_query"
    agent: str | None = None


@app.post("/api/ask")
async def api_ask(body: AskIn, principal: Principal = Depends(require("assistant.ask"))):
    # Humans always keep the assistant capability; machine clients need the scope.
    if principal.kind == "human" and not principal.can("assistant.ask"):
        pass
    return await services.ask(body.question, body.intent, principal.sub, body.agent)


# ------------------------------------------------------------------- machine clients

class ClientIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    scopes: list[str] = Field(default_factory=lambda: ["qms.read"])


@app.get("/api/machine-scopes")
async def api_machine_scopes(principal: Principal = Depends(require("admin.clients"))):
    return {"scopes": list(MACHINE_SCOPES)}


@app.post("/api/clients")
async def api_create_client(body: ClientIn, principal: Principal = Depends(require("admin.clients"))):
    try:
        return create_api_client(body.name, body.scopes, principal.sub)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ------------------------------------------------------------------- MCP

@app.post("/mcp")
async def mcp_endpoint(request: Request, principal: Principal = Depends(current_principal)):
    body = await request.json()
    result = await mcp.dispatch(body, principal)
    if result is None:
        return Response(status_code=204)
    return JSONResponse(result)


@app.get("/mcp")
async def mcp_info():
    return {
        "protocol": mcp.PROTOCOL_VERSION,
        "server": mcp.SERVER_INFO,
        "transport": "http-post-jsonrpc",
        "note": "POST JSON-RPC 2.0 with a bearer token; tool list is scope-filtered.",
    }


# ------------------------------------------------------------------- frontend

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
