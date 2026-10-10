#!/usr/bin/env python3
"""ppdocwiz.security — shared-secret gate, in two accepted forms.

The X-API-Key half is an identical contract to apps/wwf-docengine/app/security.py
(constant-time compare, fail-closed 503 when unconfigured), so machine callers
need no special-casing between the two services.

The cookie half exists because ppdocwiz serves its own browser frontend and the
docengine does not. Downloads are plain <a href> links (frontend/index.html), and
a browser following an anchor CANNOT attach a header — so a header-only gate
would silently break both download buttons. The cookie rides same-origin fetch()
AND anchor navigations, which is what makes the existing frontend work unchanged.

The cookie value is HMAC-DERIVED from the key, never the key itself. That matters
specifically here: the same frontend had unescaped innerHTML sinks, and an XSS
that could read a stored key would hand over a credential to the Letta proxy. A
derived value in an HttpOnly cookie is not reachable from JavaScript at all.

CSRF: the cookie is SameSite=Strict, and every gated mutating route requires a
JSON body, which a cross-site HTML form cannot send without a preflight. No CSRF
token is needed. Brute force is not a concern against a 32-byte random key, so
there is deliberately no rate limiting to get wrong.
"""
import hashlib
import hmac

from fastapi import Cookie, Header, HTTPException

from config import settings

COOKIE = "ppdocwiz_session"
_DERIVE_LABEL = b"ppdocwiz-session-v1"


def session_value(key: str) -> str:
    """Deterministic, non-reversible derivation of the cookie value from the key."""
    return hmac.new(key.encode(), _DERIVE_LABEL, hashlib.sha256).hexdigest()


async def require_api_key(x_api_key: str = Header(default=""),
                          ppdocwiz_session: str = Cookie(default="")) -> None:
    if not settings.api_key:
        # Unconfigured service refuses every call rather than running open.
        raise HTTPException(status_code=503, detail="PP Doc Wiz not configured")
    if hmac.compare_digest(x_api_key, settings.api_key):
        return
    if ppdocwiz_session and hmac.compare_digest(
            ppdocwiz_session, session_value(settings.api_key)):
        return
    raise HTTPException(status_code=401, detail="bad api key")
