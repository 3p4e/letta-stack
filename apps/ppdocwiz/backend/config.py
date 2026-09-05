#!/usr/bin/env python3
"""ppdocwiz.config — environment-driven settings.

Same shape as apps/wwf-docengine/app/config.py, and the key follows the house
naming convention <SERVICE>_API_KEY (QMS_API_KEY, SUMA_API_KEY, DOCENGINE_API_KEY).
Values come from the per-stack /opt/stacks/ppdocwiz/.env (0600 root) — this repo
carries env-var NAMES only, never values.

NOTE on import style: backend/ is deliberately NOT a package. app.py does a flat
`import wizard` and the Dockerfile runs `uvicorn app:app` with backend/ as the
working directory, so these modules use flat imports rather than the relative
form the docengine uses. That is the one place ppdocwiz departs from the
docengine layout, and it is forced by the existing run contract.
"""
import os


class Settings:
    # Unset is not "open" — security.require_api_key returns 503 for every
    # request when this is empty, so a misconfigured deploy refuses rather than
    # serving the Letta proxy to anyone who can reach the port.
    api_key: str = os.environ.get("PPDOCWIZ_API_KEY", "")

    # Which Letta agent(s) the chat proxy may talk to. This is an ALLOWLIST, not
    # a default: the agent name used to be taken from the request body, so a
    # caller could name any agent on the server and converse with it.
    letta_agents: str = os.environ.get("LETTA_AGENT", "qms_docx_formatter")

    # The session cookie is Secure by default. Set to "0" only for plain-HTTP
    # loopback development, where a Secure cookie would never be sent back.
    cookie_secure: bool = os.environ.get("PPDOCWIZ_COOKIE_SECURE", "1") != "0"

    @property
    def agent_allowlist(self) -> list[str]:
        return [a.strip() for a in self.letta_agents.split(",") if a.strip()]


settings = Settings()
