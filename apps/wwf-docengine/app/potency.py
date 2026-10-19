# docengine.app.potency — the official potency specifications: per strain, each grade's nominal Total THC, tolerance
# and window, as the KVM4 potency builder (potency-spec-service) holds them.
#
# Head of QC, 19.10.2026: "the specification grades and ranges actualy are officialy as in
# https://specs.srv1231216.hstgr.cloud". It is the only source: no author or advisor states a potency grade, window or
# tolerance from a pharmacopoeia, a house document, an older table or its own knowledge. The service names no grade
# numerals (I, II …), so none is written here: a grade is its nominal ± tolerance and window, as served.
from __future__ import annotations

import logging
import re
import time

import httpx

from .config import settings

log = logging.getLogger("docengine.potency")
TTL = 600
_cache: dict = {"at": 0.0, "specs": None}
# Words that put potency in a document's scope (EN / MK).
WORDS = re.compile(r"potency|cannabinoid|thc|cbd|specification|grade|канабиноид|потентност|спецификаци|содржина на",
                   re.I)
RULE = ("Potency grades, nominal values, tolerances and windows come only from the official potency specifications "
        "(KVM4 potency builder) listed here. Never take them from a pharmacopoeia, a house document, an older table or "
        "your own knowledge; never write a grade numeral the list does not give. A strain or a grade not listed is "
        "written \"per the strain's current potency specification\".")
UNAVAILABLE = ("The official potency specifications (KVM4 potency builder) could not be read. State no potency grade, "
               "nominal, tolerance or window: write \"per the strain's current potency specification\".")


def relevant(*texts) -> bool:
    return any(WORDS.search(str(t or "")) for t in texts)


def fmt(n) -> str:
    return f"{float(n):.2f}"


def lines(specs: list[dict]) -> list[str]:
    """One line per finished strain: ABBR — Name: nominal ± tol (lo–hi %); … (in the service's order)."""
    out = []
    for s in specs:
        if s.get("status") != "finished" or not s.get("ranges"):
            continue
        grades = "; ".join(f"{fmt(r['nominal'])} ± {fmt(r['tol'])} % ({fmt(r['lo'])}–{fmt(r['hi'])} %)"
                           for r in s["ranges"])
        out.append(f"{s['id']} — {s.get('name', '')}: Total THC {grades}")
    return out


async def specs(transport: httpx.AsyncBaseTransport | None = None) -> list[dict] | None:
    """The served specifications (cached TTL seconds); None when the service cannot be read."""
    if not settings.potency_specs_url:
        return None
    if _cache["specs"] is not None and time.monotonic() - _cache["at"] < TTL:
        return _cache["specs"]
    try:
        async with httpx.AsyncClient(timeout=20, transport=transport) as c:
            r = await c.get(settings.potency_specs_url + "/api/specs")
            r.raise_for_status()
            data = r.json()["specs"]
    except (httpx.HTTPError, KeyError, ValueError) as e:
        log.warning("potency specifications unavailable: %s", e)
        return None
    _cache.update(at=time.monotonic(), specs=data)
    return data


async def block(*texts, transport: httpx.AsyncBaseTransport | None = None) -> str:
    """The specifications as a prompt block when the document touches potency; '' when it does not."""
    if not settings.potency_specs_url or not relevant(*texts):
        return ""
    data = await specs(transport)
    if data is None:
        return "OFFICIAL POTENCY SPECIFICATIONS: " + UNAVAILABLE
    return "\n".join([f"OFFICIAL POTENCY SPECIFICATIONS ({settings.potency_specs_url}): " + RULE, *lines(data)])
