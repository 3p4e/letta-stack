# docengine.app.glossary — the house Macedonian glossary (agents/glossary_mk.yaml), approved by the
# Head of QC on 11.10.2026 from WHSOP_003 v01 §5. Two uses: the text every agent clone carries as its
# gf_glossary_mk memory block, and the linter's check for variants that are wrong in every context.
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

GLOSSARY_FILE = Path(__file__).resolve().parents[1] / "agents" / "glossary_mk.yaml"


@lru_cache(maxsize=1)
def load() -> dict:
    return yaml.safe_load(GLOSSARY_FILE.read_text(encoding="utf-8"))


def memory_text() -> str:
    g = load()
    lines = ["HOUSE MACEDONIAN GLOSSARY (binding; " + g["source"] + "). Use the Macedonian term exactly;",
             "never the 'not' form. English → Macedonian:"]
    for t in g["terms"]:
        avoid = f" — not: {t['avoid']}" if t.get("avoid") else ""
        lines.append(f"- {t['en']} → {t['mk']}{avoid}")
    lines += [f"- {r}" for r in g.get("rules", [])]
    return "\n".join(lines)


@lru_cache(maxsize=1)
def _patterns() -> list[tuple[re.Pattern, str]]:
    out = []
    for t in load()["terms"]:
        for p in t.get("lint", []):
            out.append((re.compile(r"(?<![\w-])(?:" + p + r")\w*", re.IGNORECASE), t["mk"]))  # \w*: report the whole word
    return out


def term_issues(content: str) -> list[str]:
    """Glossary variants found in the text, as 'found → use' pairs (first occurrence of each)."""
    found: dict[str, str] = {}
    for rx, use in _patterns():
        m = rx.search(content or "")
        if m:
            found.setdefault(m.group(0), use)
    return [f"„{w}“ → {u}" for w, u in found.items()]
