# docengine_studio.app.security - identity, roles, capabilities and machine clients.
#
# Two principal kinds:
#   * human  - identified by proxy headers (WWF pattern) or the shared studio key;
#              carries exactly one role, which maps to capabilities.
#   * machine- OAuth2 client-credentials; carries *capability scopes only*, never a
#              role, and can never approve or sign (confused-deputy protection).
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets as _secrets
import time
from dataclasses import dataclass, field

from fastapi import Header, HTTPException, Request, status

from . import db
from .config import settings

# ---------------------------------------------------------------- capabilities

CAPABILITIES: dict[str, set[str]] = {
    "viewer":      {"qms.read"},
    "author":      {"qms.read", "qms.author", "qms.build", "certs.render", "assistant.ask"},
    "qc_reviewer": {"qms.read", "qms.author", "qms.build", "qms.review", "certs.render", "assistant.ask"},
    "qa_approver": {"qms.read", "qms.review", "qms.approve", "qms.sign", "certs.render", "audit.read", "assistant.ask"},
    "admin":       {"qms.read", "qms.author", "qms.build", "qms.review", "qms.approve", "qms.sign",
                    "certs.render", "audit.read", "admin.clients", "assistant.ask"},
}

KNOWN_ROLES = tuple(CAPABILITIES)

# Scopes a machine client may be granted. Approve/sign are intentionally absent.
MACHINE_SCOPES = (
    "qms.read", "qms.author", "qms.build", "qms.review",
    "certs.render", "audit.read", "assistant.ask",
)


def capabilities_for_role(role: str) -> set[str]:
    return set(CAPABILITIES.get(role, set()))


# --------------------------------------------------------------------- principal

@dataclass
class Principal:
    kind: str                      # "human" | "machine" | "anonymous"
    name: str
    sub: str
    role: str | None = None
    scopes: set[str] = field(default_factory=set)
    client_id: str | None = None

    @property
    def capabilities(self) -> set[str]:
        if self.kind == "human":
            return capabilities_for_role(self.role or "viewer")
        return set(self.scopes)

    def can(self, capability: str) -> bool:
        return capability in self.capabilities

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "name": self.name,
            "sub": self.sub,
            "role": self.role,
            "client_id": self.client_id,
            "capabilities": sorted(self.capabilities),
        }


def _header_get(headers: dict, *names: str) -> str | None:
    for n in names:
        v = headers.get(n) or headers.get(n.lower())
        if v:
            return v
    return None


ANONYMOUS = Principal(kind="anonymous", name="anonymous", sub="anonymous")


def _session_secret() -> bytes | None:
    """Sessions exist only when a studio key is configured to derive the secret."""
    if not settings.studio_key:
        return None
    return hashlib.sha256(("studio-session|" + settings.studio_key).encode()).digest()


def verify_studio_key(provided: str | None) -> bool:
    """Constant-time check of the shared studio key; False when unset."""
    if not settings.studio_key or not provided:
        return False
    return hmac.compare_digest(provided, settings.studio_key)


def create_session(sub: str, role: str, name: str) -> str | None:
    """Return a signed session token, or None when sessions are not configured."""
    secret = _session_secret()
    if not secret:
        return None
    payload = {"sub": sub, "role": role, "name": name, "exp": int(time.time()) + settings.session_ttl}
    raw = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    sig = hmac.new(secret, raw.encode(), hashlib.sha256).hexdigest()
    return raw + "." + sig


def read_session(token: str | None) -> Principal | None:
    if not token or "." not in token:
        return None
    secret = _session_secret()
    if not secret:
        return None
    raw, sig = token.rsplit(".", 1)
    expect = hmac.new(secret, raw.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expect):
        return None
    try:
        pad = "=" * (-len(raw) % 4)
        payload = json.loads(base64.urlsafe_b64decode(raw + pad))
    except Exception:  # noqa: BLE001
        return None
    if int(payload.get("exp", 0)) < time.time():
        return None
    role = payload.get("role", "viewer")
    return Principal(
        kind="human",
        name=payload.get("name") or payload.get("sub") or "user",
        sub=payload.get("sub") or "user",
        role=role if role in CAPABILITIES else "viewer",
    )


def _identify(request: Request) -> Principal:
    h = {k.lower(): v for k, v in request.headers.items()}

    # 0) browser session cookie
    cookie = request.cookies.get(settings.session_cookie)
    if cookie:
        p = read_session(cookie)
        if p:
            return p

    # 1) machine bearer token (client credentials)
    auth = h.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
        p = resolve_machine_token(token)
        if p:
            return p

    # 2) human via proxy headers
    if settings.trust_headers:
        sub = _header_get(h, "x-auth-request-user", "x-user-id", "x-forwarded-user", "remote-user")
        if sub:
            role = (_header_get(h, "x-auth-request-groups", "x-user-role", "x-auth-request-role") or "viewer")
            role = role.split(",")[0].strip().lower()
            if role not in CAPABILITIES:
                role = "viewer"
            name = _header_get(h, "x-auth-request-email", "x-user-name", "x-auth-request-name") or sub
            return Principal(kind="human", name=name, sub=sub, role=role)

    # 3) shared studio key marks an operator/dev session
    if settings.studio_key:
        provided = h.get("x-studio-key") or request.query_params.get("studio_key")
        if verify_studio_key(provided):
            role = (h.get("x-user-role") or "admin").lower()
            return Principal(kind="human", name=h.get("x-user-name", "operator"), sub="studio-key", role=role if role in CAPABILITIES else "admin")

    return ANONYMOUS


async def current_principal(request: Request) -> Principal:
    p = _identify(request)
    if p.kind == "anonymous":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "authentication required")
    return p


def require(capability: str):
    async def _dep(request: Request) -> Principal:
        p = await current_principal(request)
        if not p.can(capability):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "missing capability: " + capability)
        return p
    return _dep


# ------------------------------------------------------------- machine clients

_HASH_ITER = 120_000


def hash_client_secret(secret: str) -> str:
    salt = _secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", secret.encode(), salt.encode(), _HASH_ITER).hex()
    return "pbkdf2$%d$%s$%s" % (_HASH_ITER, salt, dk)


def verify_client_secret(secret: str, stored: str) -> bool:
    try:
        _, iters, salt, dk = stored.split("$")
        calc = hashlib.pbkdf2_hmac("sha256", secret.encode(), salt.encode(), int(iters)).hex()
        return hmac.compare_digest(calc, dk)
    except Exception:  # noqa: BLE001
        return False


def create_api_client(name: str, scopes: list[str], actor: str) -> dict:
    bad = [s for s in scopes if s not in MACHINE_SCOPES]
    if bad:
        raise ValueError("unknown or forbidden scope: " + ", ".join(bad))
    client_id = "dcs_" + _secrets.token_hex(8)
    secret = _secrets.token_urlsafe(32)
    row_id = db.new_id("cli")
    with db.tx() as conn:
        conn.execute(
            "INSERT INTO api_clients(id,name,client_id,secret_hash,scopes,active,created_at) VALUES (?,?,?,?,?,1,?)",
            (row_id, name, client_id, hash_client_secret(secret), json.dumps(scopes), time.time()),
        )
    db.audit("api_client.created", actor=actor, subject=client_id, payload={"name": name, "scopes": scopes})
    return {"id": row_id, "client_id": client_id, "client_secret": secret, "scopes": scopes}


def resolve_machine_token(token: str) -> Principal | None:
    """Token format: <client_id>.<secret> (opaque, no JWT dependency)."""
    if "." not in token:
        return None
    client_id, secret = token.split(".", 1)
    with db.tx() as conn:
        row = conn.execute(
            "SELECT * FROM api_clients WHERE client_id=? AND active=1", (client_id,)
        ).fetchone()
    if not row or not verify_client_secret(secret, row["secret_hash"]):
        return None
    return Principal(
        kind="machine",
        name=row["name"],
        sub=client_id,
        scopes=set(json.loads(row["scopes"])),
        client_id=client_id,
    )
