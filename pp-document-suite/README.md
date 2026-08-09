# Purely Plant Document Suite — portable package

A self-contained engine that generates bilingual **Macedonian | English** controlled `.docx` in the
Purely Plant house style: **SOPs** (two-column MK|EN with a vertical divider + native TOC),
**Annexes** (inline full-page, navy `#2B547E` section banners, zebra rows), and **reports/records**
(native Word equations, worked calculations, data-entry & execution forms, statistical charts).
Every page carries the mandatory logo header + "Page X of Y" footer from one base template.

Pure Python (`python-docx`) — no API key, no internet, no specific IDE required. Runs anywhere
Python 3.9+ runs.

## Start here

| You want to… | Read |
|---|---|
| Understand the whole spec + routing (SOP vs Annex, content vs format) | **`SKILL.md`** |
| Install it (deps, per-OS render, smoke test) | **`INSTALL.md`** |
| Use it off-Claude — as a library, a tool for any agent/model, or a REST service | **`PORTABILITY.md`** |
| Wire it into stateful **Letta** agents / the QMS API | **`LETTA_INTEGRATION.md`** |
| Runnable integration code (tool fn, Letta register, REST service) | **`integrations/`** (+ `integrations/README.md`) |
| Author content as bilingual Markdown | **`references/GUIDE_bilingual_markdown.md`** |
| Exact typography / colour / table rules | **`references/formatting_specs.md`** |

## 30-second use (bilingual-Markdown path)

```bash
pip install python-docx lxml
python3 scripts/build_from_md.py  source.md  out.docx   # engine applies the house style
python3 scripts/pp_verify.py      out.docx              # gate -> RESULT: PASS
soffice --headless --convert-to pdf out.docx            # optional: render + eyeball
```

## 30-second use (Python-library path)

```python
import sys; sys.path.insert(0, "scripts")
import pp_format as pf
d = pf.new_sop(code="WHSOP_002", version="01", mk_title="…", en_title="…")
pf.sop_titlepage(d, "WHSOP_002 · v01", "…", "…"); pf.sop_toc(d)
# ... build sections via pf.sop_section_row / pf.sop_body_row / pf.sop_block_table ...
pf.save(d, "WHSOP_002.docx")
```

## The one rule

**Content and appearance are separate.** The author (you, or a model/agent) decides *what the
document says* — bilingual, quantified, clause-cited. The **engine** decides *how it looks* — the one
house navy `#2B547E`, Calibri, the 6 pt floor, the intelligent `fixed()` table layout, the template
header/footer. Never hand-roll styling or invent colours; build with the engine, verify with
`pp_verify.py`, render, and eyeball.

**v1.6.2** · engines: `pp_format · pp_report · pp_data · pp_charts · pp_theme · pp_verify`
