# INSTALL — Purely Plant Document Suite

Self-contained document engine (python-docx). Generates bilingual **Macedonian | English**
controlled `.docx` — SOPs (two-column), Annexes (inline), and reports/records (native equations,
worked calculations, data-entry forms, charts) — all in the Purely Plant house style, off a single
base template that carries the mandatory logo header + "Page X of Y" footer.

Nothing in this package needs the internet, an API key, or a specific IDE. It is plain Python plus
one `.docx` template. It runs anywhere Python 3.9+ runs.

---

## 1. What's in the box

```
pp-document-suite/
├── SKILL.md                         # master spec / router (read this first)
├── README.md                        # index of everything here
├── INSTALL.md                       # this file
├── PORTABILITY.md                   # run it off-Claude: library, any agent, REST, other models
├── LETTA_INTEGRATION.md             # wire the engine into stateful Letta agents
├── requirements.txt                 # pip deps (core + optional groups)
├── assets/
│   └── PP_BASE_TEMPLATE.docx        # logo header + footer + A4 geometry (loaded by the engine)
├── references/
│   ├── formatting_specs.md          # exact typography / colour / table rules
│   ├── questionnaire_library.md     # Mode-A content question banks
│   ├── regulatory_and_context.md    # company + regulatory backbone
│   └── GUIDE_bilingual_markdown.md  # the Markdown -> docx authoring convention
└── scripts/
    ├── pp_theme.py                  # design tokens (the one house navy #2B547E) — no deps
    ├── pp_format.py                 # SOP / Annex shells
    ├── pp_report.py                 # reports/records: equations, calcs, forms, status grids
    ├── pp_data.py                   # dataset binding + statistics (single source of truth)
    ├── pp_charts.py                 # matplotlib figures (optional)
    ├── pp_verify.py                 # pre-delivery QC gate (font floor, bilingual, fidelity)
    ├── build_from_md.py             # bilingual-Markdown -> controlled .docx adapter
    └── render_pdf.ps1               # Windows Word-COM PDF render
```

## 2. Core install (required)

```bash
python3 -m venv .venv && . .venv/bin/activate      # optional but recommended
pip install -r pp-document-suite/requirements.txt   # or: pip install python-docx lxml
```

That is enough to build **every** SOP, annex, form and report. Equations fall back to text and
charts are skipped until you add the optional groups below.

## 3. Optional capabilities

| Capability | Install | Notes |
|---|---|---|
| **Native Word equations** (editable OMML, not text) | `pip install latex2mathml` **+** the Office stylesheet `MML2OMML.XSL` | The stylesheet ships with Microsoft Office (Windows). On Linux/macOS it is absent, so `eqn()/calc_step()` fall back to monospace text — the build still passes. |
| **Statistical charts** (`pp_charts.py`) | `pip install matplotlib numpy` | Only needed for data/validation reports that embed figures. |

## 4. PDF render (system packages, not pip) — for the eyeball QC step only

The `.docx` is produced with pure Python. Rendering to PDF to *look at it* needs a renderer:

- **Linux / macOS**
  ```bash
  # Debian/Ubuntu
  sudo apt-get install -y libreoffice-writer poppler-utils
  soffice --headless --convert-to pdf mydoc.docx        # -> mydoc.pdf
  pdftoppm -png -r 120 mydoc.pdf page                    # -> page-1.png ... eyeball it
  ```
- **Windows** — Microsoft Word present:
  ```powershell
  pwsh pp-document-suite/scripts/render_pdf.ps1 mydoc.docx
  ```
  Word COM also updates the native TOC and "Page X of Y" fields and enables OMML equations.

> Native TOC (SOPs) and "Page X of Y" show blank until fields are updated: in Word press
> `Ctrl+A → F9`; `soffice --convert-to pdf` and the PowerShell renderer update them automatically.

## 5. Smoke test (verify the install)

```bash
cd pp-document-suite/scripts
python3 - <<'PY'
import sys; sys.path.insert(0,'.')
import pp_theme, pp_format, pp_report, pp_verify, pp_data
print("engine OK — house navy #%s" % pp_theme.NAVY_HEX)
d = pp_format.new_sop(code="TEST 001", version="1.0",
                      mk_title="Тест", en_title="Smoke Test")
pp_format.sop_titlepage(d, "TEST 001 · v1.0", "Тест", "Smoke Test")
pp_format.save(d, "/tmp/pp_smoke.docx")
print("built /tmp/pp_smoke.docx")
PY
python3 pp_verify.py /tmp/pp_smoke.docx        # expect: RESULT: PASS
```

If `pp_verify.py` prints **RESULT: PASS**, the core install is good. `matplotlib`/`latex2mathml`
being absent is fine unless you need charts/equations.

## 6. Version

Purely Plant Document Suite **v1.6.2** — engines `pp_format · pp_report · pp_data · pp_charts ·
pp_theme · pp_verify` (python-docx). Output: bilingual MK|EN controlled `.docx` + PDF.
