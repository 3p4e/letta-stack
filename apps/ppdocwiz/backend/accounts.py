#!/usr/bin/env python3
"""ppdocwiz.accounts — named accounts (Head of QC, 19.10.2026: phase 5, one login per person).

Each person signs in with a username and a password; the password is kept only as a scrypt hash
(security.hash_password). An administrator adds people with a temporary password, which they must change
at their first sign-in, and can reset a password or disable an account. Nobody is deleted: a disabled
account keeps its name on everything it did. The signed-in person is passed to the DocEngine with every
request (X-Actor), so each brief change, build, suggestion and review records who made it.

Stored on the data volume beside the revoked-sessions file:
  .ppdocwiz_users.json   {username: {hash, role, must_change, disabled, created, by}}
  ppdocwiz_auth.log      one JSON line per sign-in, failure, password change and account change (append only)

The first start after this change turns the shared password (if one is set) into the account "admin",
so the owner's sign-in keeps working; he then adds named accounts, his own included.
"""
import datetime as dt
import json
import os
import re
import threading

import security

USERS_FILE = os.path.join(os.path.dirname(security.REVOKED_FILE), ".ppdocwiz_users.json")
AUTH_LOG = os.path.join(os.path.dirname(security.REVOKED_FILE), "ppdocwiz_auth.log")
NAME = re.compile(r"^[a-z0-9][a-z0-9._-]{1,39}$")
ROLES = ("admin", "user")
_LOCK = threading.Lock()


class AccountError(ValueError):
    status = 400


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def load() -> dict:
    try:
        with open(USERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save(users: dict) -> None:
    tmp = USERS_FILE + ".part"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=1)
    os.replace(tmp, USERS_FILE)


def log(event: str, username: str, client: str = "", **detail) -> None:
    line = json.dumps({"at": _now(), "event": event, "user": username, "client": client, **detail}, ensure_ascii=False)
    with _LOCK, open(AUTH_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def enabled() -> bool:
    """Named accounts are in use once at least one exists."""
    return bool(load())


def bootstrap() -> None:
    """The shared password, when one is set and no account exists yet, becomes the account 'admin'."""
    with _LOCK:
        if os.path.exists(USERS_FILE):
            return
        h = security.current_hash()
        if not h:
            return
        _save({"admin": {"hash": h, "role": "admin", "must_change": security.must_change(), "disabled": False,
                         "created": _now(), "by": "migration from the shared password"}})
    log("migrated", "admin")


def active(username: str) -> dict | None:
    u = load().get(username)
    return u if u and not u.get("disabled") else None


def authenticate(username: str, password: str) -> dict | None:
    u = active((username or "").strip().lower())
    return u if u and security.check_password(password, u["hash"]) else None


def _check_password(pw: str) -> None:
    if len(pw) < security.MIN_PASSWORD:
        raise AccountError(f"a password needs at least {security.MIN_PASSWORD} characters")


def create(username: str, role: str, temporary: str, by: str) -> dict:
    username = (username or "").strip().lower()
    if not NAME.match(username):
        raise AccountError("a username is 2-40 characters: lower-case letters, digits, '.', '_' or '-'")
    if role not in ROLES:
        raise AccountError(f"role must be one of {', '.join(ROLES)}")
    _check_password(temporary)
    with _LOCK:
        users = load()
        if username in users:
            raise AccountError(f"{username} already exists")
        users[username] = {"hash": security.hash_password(temporary), "role": role, "must_change": True,
                           "disabled": False, "created": _now(), "by": by}
        _save(users)
    log("account_created", username, by=by, role=role)
    return public(username, users[username])


def update(username: str, by: str, disabled: bool | None = None, role: str | None = None,
           reset_password: str | None = None) -> dict:
    with _LOCK:
        users = load()
        u = users.get(username)
        if not u:
            raise AccountError(f"no account {username}")
        if role is not None:
            if role not in ROLES:
                raise AccountError(f"role must be one of {', '.join(ROLES)}")
            u["role"] = role
        if disabled is not None:
            u["disabled"] = bool(disabled)
        if reset_password is not None:
            _check_password(reset_password)
            u["hash"], u["must_change"] = security.hash_password(reset_password), True
        admins = [n for n, x in users.items() if x["role"] == "admin" and not x.get("disabled")]
        if not admins:
            raise AccountError("at least one administrator must stay enabled")
        _save(users)
    log("account_changed", username, by=by, role=role, disabled=disabled, password_reset=reset_password is not None)
    return public(username, u)


def change_own_password(username: str, current: str, new: str) -> None:
    _check_password(new)
    if new == current:
        raise AccountError("choose a password different from the current one")
    with _LOCK:
        users = load()
        u = users.get(username)
        if not u or u.get("disabled") or not security.check_password(current, u["hash"]):
            e = AccountError("the current password is wrong")
            e.status = 401
            raise e
        u["hash"], u["must_change"] = security.hash_password(new), False
        _save(users)
    log("password_changed", username)


def public(username: str, u: dict) -> dict:
    return {"username": username, "role": u["role"], "must_change": u.get("must_change", False),
            "disabled": u.get("disabled", False), "created": u.get("created", ""), "by": u.get("by", "")}


def listing() -> list[dict]:
    return [public(n, u) for n, u in sorted(load().items())]


def recent_log(limit: int = 200) -> list[dict]:
    try:
        with open(AUTH_LOG, encoding="utf-8") as f:
            lines = f.readlines()[-limit:]
    except OSError:
        return []
    out = []
    for ln in reversed(lines):
        try:
            out.append(json.loads(ln))
        except ValueError:
            pass
    return out
