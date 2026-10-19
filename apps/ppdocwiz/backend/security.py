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
import json
import os
import secrets
import tempfile
import threading
import time

from fastapi import Cookie, Header, HTTPException

from config import settings

COOKIE = "ppdocwiz_session"
_DERIVE_LABEL = b"ppdocwiz-session-v1"
# A session lasts this long on the SERVER, not only in the browser. The cookie used to be a fixed derivation of
# the key, accepted forever: a value captured once worked until the key itself was rotated, and "Sign out" could
# not end it (review 14.10.2026). It now carries its issue time and a random session id, signed with the key.
SESSION_TTL = 8 * 3600
_SKEW = 60
# Signed-out sessions, kept until they would have expired anyway. A file in the app's data directory, so a
# restart does not reopen them (single worker: see the Dockerfile CMD).
REVOKED_FILE = os.path.join(os.environ.get("PP_OUT_DIR") or ("/data" if os.path.isdir("/data") else tempfile.gettempdir()),
                            ".ppdocwiz_revoked_sessions.json")
_REVOKED_LOCK = threading.Lock()


def _b(s: str) -> bytes:
    return (s or "").encode("utf-8", "surrogateescape")


def session_value(key: str) -> str:
    """The old fixed cookie value. Kept only so a test can prove it is no longer accepted."""
    return hmac.new(key.encode(), _DERIVE_LABEL, hashlib.sha256).hexdigest()


def _mac(key: str, body: str) -> str:
    return hmac.new(key.encode(), _DERIVE_LABEL + b"|" + body.encode(), hashlib.sha256).hexdigest()


def issue_session(key: str, now: float | None = None) -> str:
    """v2.<issued-at>.<session id>.<signature>: nothing secret in it, and nothing usable without the key."""
    body = f"v2.{int(now if now is not None else time.time())}.{secrets.token_hex(12)}"
    return f"{body}.{_mac(key, body)}"


def _revoked() -> dict:
    try:
        with open(REVOKED_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def session_id(value: str, key: str, now: float | None = None) -> str | None:
    """The session id of a valid, unexpired, not signed-out cookie; None otherwise."""
    parts = (value or "").split(".")
    if len(parts) != 4 or parts[0] != "v2":
        return None
    body, mac = ".".join(parts[:3]), parts[3]
    if not hmac.compare_digest(_b(mac), _b(_mac(key, body))):
        return None
    try:
        issued = int(parts[1])
    except ValueError:
        return None
    t = now if now is not None else time.time()
    if not (issued - _SKEW <= t <= issued + SESSION_TTL):
        return None
    sid = parts[2]
    return None if sid in _revoked() else sid


def revoke(value: str, key: str) -> bool:
    """Sign a session out until it would have expired. False when the cookie was not a live session."""
    sid = session_id(value, key)
    if not sid:
        return False
    issued = int(value.split(".")[1])
    with _REVOKED_LOCK:
        live = {s: exp for s, exp in _revoked().items() if exp > time.time()}   # forget the expired ones
        live[sid] = issued + SESSION_TTL
        tmp = REVOKED_FILE + ".part"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(live, f)
        os.replace(tmp, REVOKED_FILE)
    return True


# ---- shared password (Head of QC, 19.10.2026) ----
# Unlike a 32-byte random key, a password can be guessed, so failed sign-ins are limited: per client address and in
# total, over a sliding window. Kept in memory (single worker); a restart forgets them, which only resets the window.
_SCRYPT = {"n": 2 ** 15, "r": 8, "p": 1}
FAIL_WINDOW, FAIL_PER_CLIENT, FAIL_TOTAL = 900, 10, 100
_fails: dict[str, list[float]] = {}
_FAIL_LOCK = threading.Lock()


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    d = hashlib.scrypt(password.encode("utf-8"), salt=salt, dklen=32, maxmem=64 * 1024 * 1024, **_SCRYPT)
    return f"scrypt${_SCRYPT['n']}${_SCRYPT['r']}${_SCRYPT['p']}${salt.hex()}${d.hex()}"


def check_password(password: str, stored: str) -> bool:
    try:
        kind, n, r, p, salt, digest = (stored or "").split("$")
        if kind != "scrypt":
            return False
        d = hashlib.scrypt(password.encode("utf-8", "surrogateescape"), salt=bytes.fromhex(salt), n=int(n), r=int(r),
                           p=int(p), dklen=32, maxmem=64 * 1024 * 1024)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(d.hex(), digest)


def _recent(times: list[float], now: float) -> list[float]:
    return [t for t in times if now - t < FAIL_WINDOW]


def too_many_failures(client: str, now: float | None = None) -> bool:
    now = now if now is not None else time.time()
    with _FAIL_LOCK:
        mine = _fails[client] = _recent(_fails.get(client, []), now)
        total = sum(len(_recent(v, now)) for v in _fails.values())
    return len(mine) >= FAIL_PER_CLIENT or total >= FAIL_TOTAL


def note_failure(client: str, now: float | None = None) -> None:
    with _FAIL_LOCK:
        _fails.setdefault(client, []).append(now if now is not None else time.time())


async def require_api_key(x_api_key: str = Header(default=""),
                          ppdocwiz_session: str = Cookie(default="")) -> None:
    if settings.auth_off:
        return                       # PPDOCWIZ_AUTH=off: open access by the owner's choice (config.py)
    if not settings.api_key:
        # Unconfigured service refuses every call rather than running open.
        raise HTTPException(status_code=503, detail="PP Doc Wiz not configured")
    # Bytes, not str: compare_digest raises TypeError on a non-ASCII str, so a crafted header was a 500.
    if hmac.compare_digest(_b(x_api_key), _b(settings.api_key)):
        return
    if ppdocwiz_session and session_id(ppdocwiz_session, settings.api_key):
        return
    raise HTTPException(status_code=401, detail="bad api key")


if __name__ == "__main__":
    # python3 backend/security.py hash   — reads the password (not echoed) and prints its PPDOCWIZ_PASSWORD_HASH value
    import getpass
    import sys
    if sys.argv[1:] == ["hash"]:
        pw = sys.stdin.readline().rstrip("\n") if not sys.stdin.isatty() else getpass.getpass("password: ")
        if len(pw) < 12:
            sys.exit("a password of at least 12 characters, please")
        print(hash_password(pw))
