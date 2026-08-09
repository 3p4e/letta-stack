# docengine.app.security — single shared-secret header gate.
# The service is internal-only (no published ports); the WWF backend proxy is
# the sole caller and injects X-API-Key from its own env. Identical contract
# to the Phase-1 qms-api so the proxy code needs no special-casing.
import hmac

from fastapi import Header, HTTPException

from .config import settings


async def require_api_key(x_api_key: str = Header(default="")) -> None:
    if not settings.api_key:
        # unconfigured service refuses every call rather than running open
        raise HTTPException(status_code=503, detail="DocEngine not configured")
    if not hmac.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="bad api key")
