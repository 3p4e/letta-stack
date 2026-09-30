# docengine_studio.app.config - 12-factor settings for the DocEngine Studio gateway.
# The gateway fronts the Line B GrowFlow DocEngine (apps/wwf-docengine) REST API and
# adds document lifecycle, approvals, provenance, audit, model routing and an MCP surface.
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("STUDIO_DATA_DIR", str(ROOT / "data")))


class Settings:
    # --- upstream DocEngine (Line B) ---
    docengine_endpoint: str = os.environ.get("DOCENGINE_ENDPOINT", "http://docengine:8000").rstrip("/")
    docengine_key: str = os.environ.get("DOCENGINE_API_KEY", "")

    # --- Letta (advisory lane; optional) ---
    letta_endpoint: str = os.environ.get("LETTA_ENDPOINT", "").rstrip("/")
    letta_key: str = os.environ.get("LETTA_API_KEY", "")
    letta_advisory_agent: str = os.environ.get("LETTA_ADVISORY_AGENT", "gf_app_assistant")

    # --- studio auth gate (optional shared secret for direct use) ---
    studio_key: str = os.environ.get("STUDIO_API_KEY", "")

    # Identity headers are injected by the upstream proxy (WWF pattern).
    trust_headers: bool = os.environ.get("STUDIO_TRUST_HEADERS", "1") == "1"

    # Browser sessions: an HttpOnly cookie signed with a server-side secret.
    # The cookie is only accepted when a studio key exists to derive that secret.
    session_cookie: str = os.environ.get("STUDIO_SESSION_COOKIE", "studio_session")
    session_ttl: int = int(os.environ.get("STUDIO_SESSION_TTL", "43200"))
    cookie_secure: bool = os.environ.get("STUDIO_COOKIE_SECURE", "1") == "1"

    db_path: Path = Path(os.environ.get("STUDIO_DB_PATH", str(DATA_DIR / "studio.db")))

    # RAGFlow (official evidence lane). Empty = lane explicitly unavailable.
    ragflow_endpoint: str = os.environ.get("RAGFLOW_ENDPOINT", "").rstrip("/")
    ragflow_key: str = os.environ.get("RAGFLOW_API_KEY", "")

    page_size: int = int(os.environ.get("STUDIO_PAGE_SIZE", "50"))
    model_provider_ready: bool = os.environ.get("STUDIO_MODEL_PROVIDER_READY", "0") == "1"

    def ensure_dirs(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
