# HTML → Word: the exact mechanism

**How the three blank HTML templates — Certificate of Quality (CoQ), Product Specification
(ImB / QCSP 001) and Internal Certificate of Analysis (iCoA) — become `.docx` files that
are editable Word documents *and* a visual replica of the HTML on one A4 page.**

Written 23.09.2026 from the code and the built artifacts on disk. Every mechanism below is
traced to a file and a line. Where the existing record
(`tracker/PDF_TO_WORD_2026-09-21.md`) and the code disagree, the code is taken as
authoritative and the disagreement is stated in §11. Figures are separated into *recorded
in the repo* (§9.1) and *measured from the files on disk while writing this* (§9.2) —
the second kind will change the next time anything is rebuilt.

---

## 1 · The pipeline, end to end

```
 .html  (self-contained: CSS + logo folded in, blue .ph placeholders inserted)
   │
   │  build_blank_templates.py            — makes the templates from the fleets
   │      · per-node diff across every document of the fleet → which nodes are values
   │      · nearest_label() names each one, shorten()/clip_words() cuts it to 22 chars
   │      · ticks become a literal ☐ instead of a descriptor
   │      · fit_placeholders() measures the real print layout and walks the ladder
   ▼
 fonts: house_fonts.font_face_css()       — Montserrat / Roboto Mono / Orbitron
   │      · fetched from Google once, cached as woff2
   │      · variable axes PINNED → static instance (else Chromium emits Type 3)
   │      · subset to the characters these documents print, BOTH cases
   │      · inlined as data: URIs, each carrying its own unicode-range
   ▼
 headless Chromium (Playwright)           — print_coq_pdfs.render()
   │      · fonts.googleapis.com and fonts.gstatic.com ABORTED at the route layer
   │      · @page{size:A4;margin:0} + .page fixed 210×297 mm
   │      · page.pdf(prefer_css_page_size=True, print_background=True)
   │      · probe= callback reads the DOM's own field geometry in the SAME pass
   ▼
 .pdf   (one A4 page, 594.96 × 841.92 pt, fonts embedded as TrueType)
   │
   │  pdf_to_docx_exact.py                — the converter; reconstructs NOTHING
   │      · house-font text spans REDACTED out of the page
   │      · what is left rendered at 300 dpi → one PNG, the page layer
   │      · each span (certificate) or each DOM field (template) re-emitted as a
   │        w:framePr paragraph at the PDF's own coordinates, in twips
   │      · widths corrected with w:spacing so Word sets them as wide as the page
   ▼
 embed_fonts.py                           — house faces embedded as word/fonts/*.odttf
   │
   ▼
 check_order()                            — w:pPr / w:rPr child order asserted
   ▼
 .docx
```

Nothing in this chain re-flows the document. There is no HTML→Word writer and no
`pdf2docx`-style reconstruction anywhere in it; both were tried and rejected
(`tracker/PDF_TO_WORD_2026-09-21.md:19-26`).

### 1.1 The files

| role | path |
| --- | --- |
| template generator (HTML) | `deliverables/qc_gap_analysis/build_blank_templates.py` |
| printer (HTML → PDF) | `deliverables/qc_gap_analysis/live_instrument/print_coq_pdfs.py` |
| web-font subsetter / inliner | `ingestion/coa_track/letta-imb-coas/house_fonts.py` |
| converter (PDF → DOCX) | `deliverables/qc_gap_analysis/design_handoff/toolchain/pdf_to_docx_exact.py` |
| Word font embedder | `deliverables/qc_gap_analysis/design_handoff/toolchain/embed_fonts.py` |
| template driver (one box per field) | `deliverables/qc_gap_analysis/BLANK_TEMPLATES/build_template_docx.py` |
| outputs | `BLANK_TEMPLATES/{,PDF/,DOCX/}` — 3 HTML, 3 PDF, 3 DOCX |

---

## 2 · Stage 1 — the blank templates (`build_blank_templates.py`)

### 2.1 Which fields are placeholders is diffed, not chosen

`build()` (`build_blank_templates.py:259-325`) parses every document of a fleet, addresses
every text node by its position in the tree (`addr()`, `:135-142`; `texts()`, `:145-154`)
and collects the set of values each address takes. A node whose text differs between any
two documents is a value; everything else is fixed wording and is left untouched
(`:267` — `variable = {k for k, v in vals.items() if len(v) > 1}`).

Fleets compared (`main()`, `:454-461`):

* CoQ — `design_handoff/out/ISSUE_COQ/*.html` + `design_handoff/out/REISSUE/*/*.html`,
  specimen `CoQ-PP_26-013_P050072_GP_Grape_Pie_Grade_II.html`
* iCoA — `icoa_handoff/v3/ISSUE_iCOA/*/*.html`, specimen
  `iCoA-PP_26-001_CJ1024_CJ_Cap_Junky_Initial.html`
* ImB specification — **not derived.** The owner supplied a blank; `specs/TEMPLATE/
  QCSP_001_ImB_TEMPLATE.html` is copied verbatim (`:462-471`) so there is one source for
  the specification rather than two that can drift.

### 2.2 The blue is appended, never edited

`STYLE` (`:40-47`) is one `<style id="__placeholders">` block appended before `</body>`
(`:318`):

```css
.ph { color:#1565C0 !important; font-style:italic !important; font-weight:600 !important;
      -webkit-print-color-adjust:exact; print-color-adjust:exact; }
```

Delete that block and the file is the delivered design. The placeholder itself is a
`<span class="ph">[LABEL]</span>` inserted as the element's first child, with the original
text removed (`:309-315`).

That `font-weight:600` + `font-style:italic` combination is the direct cause of the Type 3
problem in §4.3 — Montserrat has no true italic at 600 in the linked face set, so Chromium
synthesises the slant.

### 2.3 Naming a field — `nearest_label()`, `NAMES`, `STRUCTURAL`

`nearest_label()` (`:169-200`) takes the caption the design already prints beside the value:
it walks *preceding siblings* looking for a class matching
`(^|[\s-])(lbl|label|attr)($|[\s-])` and **not** containing `sec` (`:180`), then strips the
Macedonian half by splitting on the first Cyrillic character (`:183`). It climbs **three**
levels — the field, its panel, and the panel's group — because the observation chip sits in
`.ck` inside `.fc-opts` whose group caption `<div class="fc-attr">Colour</div>` is the
sibling of the third ancestor (`:190-193`). A two-level climb named all twenty-three of them
`OBSERVATION` after their CSS class.

`NAMES` (`:52-67`) is the per-class fallback. `STRUCTURAL = {"bx", "ck", "title"}` (`:71`)
are named by what they *are*, never by their caption — letting the caption reach a tick box
made every box in the observation record read `[COLOUR]` (`:292-297`). `fc` and `ck-t` are
deliberately absent from `NAMES` (`:61-64`) so the group caption names them.

A cell inside a results row is suffixed with its determination number
(`row_number()`, `:203-214`, → `[RESULT #4]`, `[RESULT #9.3]`); otherwise a repeat of the
same label is numbered `LABEL 2`, `LABEL 3` (`:303-306`).

### 2.4 Ticks — `TICKS`, `UNTICKED`

```python
TICKS = {"bx"}          # build_blank_templates.py:74
UNTICKED = "☐"     # build_blank_templates.py:75  →  ☐
```

A tick is a state, not a value, so the box is drawn empty instead of receiving a descriptor
(`:283-290`). The certificate's own wording is the authority: the menus are *"printed
unticked and marked and initialled by hand at the time of analysis"*. This alone took the
internal certificate from 60 placeholders to 35 — and it was those wide `[TICK n]` boxes,
not the descriptors, that were pushing the chips over
(`tracker/PDF_TO_WORD_2026-09-21.md:237-241`).

### 2.5 Fitting the descriptor to its box — `clip_words`, `shorten`, `ladder`, `fit_placeholders`

| function | line | what it does |
| --- | --- | --- |
| `clip_words(label, n)` | `:89-111` | cuts to ≤ `n` chars **on a word boundary**, then strips the trailing separators given under this table. Cutting at the character left `[CYSTOLITHS · HCL R TES]` and `[COVERING TRICHOMES — D]` reading as mistakes. |
| `shorten(label)` | `:114-132` | looks the label up in `SHORT` (`:80-86`) twice — as given, and with a trailing `[\s№.:·—-]+` stripped, so `FINAL QC TESTING FOR BATCH №` matches `FINAL QC TESTING FOR BATCH` → `BATCH`. Otherwise `clip_words(label, 22)`. **22 characters** is the cap in both branches. |
| `ladder(text)` | `:332-367` | yields progressively shorter forms, **always keeping the number**, because the number is the field's identity. Splits on `LADDER_SPLIT = [\s·—/&-]+` (`:328`), parsed by `PH_TEXT = ^\[(.*?)(?:\s+(#?\d+))?\]$` (`:329`). Forms: full label → first 3 chars of each word → first letter of each word → number alone → `[·]`. `[COLOUR 3]` → `[COL 3]` → `[C 3]` → `[3]`. |
| `fit_placeholders(paths, css, chromium)` | `:370-451` | measures the **printed** layout and walks the ladder only as far as each box demands. |

The trailing separators `clip_words` strips, verbatim — quoted in a block because a table
cell may not hold a bare vertical bar:

```
 ·|—-
```

`fit_placeholders` is where the measurement is actually made correctly. A `.ph` is an inline
`<span>`, and `scrollWidth` on an inline element measures nothing — the first attempt
reported all three templates clean while the chips were visibly cut off. The `OVERFLOW`
probe (`:389-396`) therefore climbs to the **nearest ancestor that hides horizontal
overflow** and asks *that* element whether it is over-full:

```js
for (let n = e; n && n !== document.body; n = n.parentElement) {
  const o = getComputedStyle(n).overflowX;
  if ((o === 'hidden' || o === 'clip') && n.scrollWidth > n.clientWidth + 0.5)
    return {i: +e.dataset.phi, t: e.textContent};
}
```

Mechanics: each `.ph` is tagged `data-phi=<index>` in a temporary `src + ".fit.html"`
(`:405-409`), the page is loaded, the inlined font CSS added, `document.fonts.ready`
awaited and `page.emulate_media(media="print")` applied (`:411-414`); then at most **six**
rounds (`:418`) of "who is still over-full → give it the next rung". The chosen rungs are
written back into the real HTML file and `data-phi` removed (`:439-444`). If anything is
still clipped the build **fails** rather than shipping an unreadable descriptor
(`:448-450`).

### 2.6 `self_contained()` — why a template is one file

`self_contained()` (`:217-245`) folds every *relative* `<link rel="stylesheet">` into a
`<style data-from="...">` and every relative `<img src>` into a `data:` URI (`MEDIA`,
`:248-249`; `read_asset`, `:252-256`). `//`-prefixed and `data:` URLs are left alone, which
is why the Google Fonts `<link>` survives in all three files — harmless, because the printer
blocks it (§3.3) and injects the inlined faces instead.

This existed because the iCoA carried `../_icoa.css` and `../_logo.svg` by relative path:
moved into `BLANK_TEMPLATES/` the page lost every rule and printed over three A4 pages with
a broken image where the mark belongs (`:217-226`).

---

## 3 · Stage 2 — HTML → PDF (`print_coq_pdfs.py`)

### 3.1 `render()` — the whole printing pass

`print_coq_pdfs.py:114-142`:

```python
def render(paths, outdir, chromium=None, css="", probe=None):
    from playwright.sync_api import sync_playwright
    made = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=chromium) if chromium \
            else pw.chromium.launch()
        page = browser.new_page()
        for pat in BLOCK:
            page.route(pat, lambda route: route.abort())
        for src in paths:
            page.goto("file://" + os.path.abspath(src))
            if css:
                page.add_style_tag(content=css)
            page.evaluate("() => document.fonts.ready")
            if probe is not None:
                probe(src, page)
            dst = os.path.join(outdir, os.path.basename(src)[:-5] + ".pdf")
            page.pdf(path=dst, prefer_css_page_size=True, print_background=True)
            made.append(dst)
        browser.close()
    return made
```

The **exact** `page.pdf` arguments are `path=dst`, `prefer_css_page_size=True`,
`print_background=True` (`:139`) — nothing else. `prefer_css_page_size` hands the page size
to the document's own `@page{size:A4;margin:0}` (present in all three templates, verified
in the files) so there is no printer margin; `print_background=True` because the DRAFT
watermark, section rules, selection pills and the red of a marked field **are** the
document, not decoration (`:31-37`).

### 3.2 `probe=` — the DOM and the PDF measured in one pass

`probe`, when given, is called as `probe(src, page)` on the laid-out page **immediately
before** it is printed, and its return value is ignored (`:114-122`, `:136-137`). This is
the whole reason field boundaries can be trusted: it is the only moment the DOM's geometry
and the PDF's ink are guaranteed to describe the same layout. Passing no `probe` leaves the
printer behaving exactly as it did — which matters, because both certificate fleets print
through this same function.

### 3.3 `FAMILIES`, `SUBSETS`, `BLOCK`

```python
FAMILIES = (                                                   # print_coq_pdfs.py:63-67
    ("Montserrat",  "Montserrat:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400;1,500;1,600;1,700"),
    ("Roboto Mono", "Roboto+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500"),
    ("Orbitron",    "Orbitron:wght@500;600;700;800;900"),
)
SUBSETS = ("latin", "latin-ext", "cyrillic", "greek")          # :70
BLOCK   = ("**fonts.googleapis.com/**", "**fonts.gstatic.com/**")   # :71
```

* **Every italic weight the stylesheet sets must be listed.** `.ap-cred` sets
  `font-weight:600; font-style:italic` and italic 600 was missing: the browser emboldened
  the nearest real italic (500), and a synthesised face has no outlines to embed, so Skia
  rasterised it into Type 3 glyph procedures — **39 faces in the Tranche 1 PDF and 27 in
  Tranche 2** came out Type 3 while the same family embedded as TrueType elsewhere in the
  same document (`:54-62`). Pinning the variable axes fixes the faces the page *asks for*;
  it cannot fix one the page never asked for.
* `greek` carries the **Δ** of "Total Δ⁹-THC"; `latin-ext` the accented letters a strain
  name can hold; `cyrillic` the Macedonian (`:68-70`).
* `BLOCK` is applied with `page.route(pat, lambda route: route.abort())` (`:129-130`) so
  the PDF is byte-identical whether or not the container has a route to Google. A controlled
  document that changes appearance depending on a third party's reachability is not one to
  hand a regulator (`:13-23`).

### 3.4 `page_text()` — both cases of every character

`page_text(paths)` (`:91-111`) is the character set handed to the subsetter. It strips
`<script>`/`<style>` bodies *first* so a base64 blob never reaches the set (`:99`), then
strips all remaining tags (`:100`). Then the line that matters:

```python
chars |= {c.upper() for c in chars} | {c.lower() for c in chars}   # :109
```

Almost every label on these documents is set with `text-transform:uppercase`, so the source
carries `Код на документ` and the renderer asks for `Н` — never in the subset, and it fell
to Liberation Sans, one substituted letter inside an otherwise-Montserrat word on nearly
every Macedonian label of the fleet. The same took `V` out of Orbitron in `CULTIVAR`
(`:101-108`).

---

## 4 · Stage 3 — the fonts (`house_fonts.py`, `embed_fonts.py`)

Two different subsetters, two different jobs.

### 4.1 `house_fonts.py` — into the **HTML**, as data URIs

`ingestion/coa_track/letta-imb-coas/house_fonts.py`.

`font_face_css(text, families, subsets)` (`:162-185`) returns
`(css, upstream_bytes, embedded_bytes)`.

| step | line | detail |
| --- | --- | --- |
| fetch | `:61-93` | `GET https://fonts.googleapis.com/css2?family=<spec>&display=swap` with a desktop-Chrome UA (`:32-33`, `:64-66`), then each `.woff2` slice, cached in `.fontcache/<Family>-<weight>-<style>-<subset>.woff2` (`:85-91`). **The CSS index request is not cached** — a build needs network reachability to `fonts.googleapis.com` even with a warm woff2 cache. |
| keep the unicode-range | `:74-80` | Google's per-slice `unicode-range` must travel with the face: several slices share one family/weight/style, and `@font-face` rules agreeing on those three with no range **do not combine — the last one parsed wins outright**. Without it the Latin slice (served last) silenced Cyrillic and Greek and every `Н Њ № Δ` fell to a system font. |
| pin the variable axes | `:124-133` | `instancer.instantiateVariableFont(...)`. A variable font **cannot** be embedded in a PDF; Skia rasterises each instance into Type 3 glyph procedures. Pinning `wght` first makes it an ordinary static font that embeds as TrueType. |
| rename | `:100-110` | Google's slices all carry the *Thin* name table whatever their weight; name IDs 1, 2, 4, 6, 16, 17 are rewritten. |
| subset | `:142-150` | `flavor="woff2"`, `desubroutinize=True`, `layout_features=["kern","liga","locl"]`, `notdef_outline=False`, `drop_tables += ["GSUB","GPOS"]`. |
| always-include set | `:58` | the always-include set, given under this table — CSS `::after` content and badge glyphs that never appear in the HTML source as text. |
| emit | `:180-184` | `@font-face{font-family:'X';font-style:…;font-weight:…;font-display:block;src:url(data:font/woff2;base64,…) format('woff2');unicode-range:…;}` |

The always-include set, verbatim:

```
ALWAYS = "TARGETNEW0123456789.,:;()[]/|-–—·%°±×≤≥<>&#@№µΔ⁹⁴⁵₁₂ "
```

The module's own defaults (`SUBSETS` = latin + cyrillic at `:36`; two families at `:51-54`)
are the QCSP 001 specification's. **The certificate pipeline overrides both** by passing
`print_coq_pdfs.FAMILIES` / `SUBSETS` — three families including Orbitron, four subsets
including Greek (`build_template_docx.py:163`, `build_blank_templates.py:481`,
`print_coq_pdfs.py:172`).

Recorded size for the CoQ fleet run: `fonts: 59 faces, 1908 KB upstream -> 252 KB subset`
(`design_handoff/pdf_run.log:1`, also `design_handoff/t12.log:3`).

### 4.2 `embed_fonts.py` — into the **DOCX**, as obfuscated `.odttf`

`design_handoff/toolchain/embed_fonts.py`. Run as a subprocess by the converter
(`pdf_to_docx_exact.py:710-711`).

| step | line | detail |
| --- | --- | --- |
| source | `:38` | `SRC = os.environ.get("PP_FONT_SRC", "/tmp/claude-0/fonts")` — five **variable** TTFs listed in `VARIABLE` (`:44-46`): `Montserrat[wght].ttf`, `Montserrat-Italic[wght].ttf`, `RobotoMono[wght].ttf`, `RobotoMono-Italic[wght].ttf`, `Orbitron[wght].ttf`. Note the default path is a session scratch directory. |
| one family per weight | `:51-59` | Word matches an embedded face by **name** and knows only four styles per name, so each weight gets its own family: `face_name()` returns `("Montserrat", …)` for 400/700 and `"Montserrat SemiBold"`, `"Montserrat Medium"`, `"Orbitron Black"` … for the rest. `WEIGHTS` (`:47-48`) snaps a requested weight to the nearest the family actually carries. |
| static instance | `:62-96` | `instancer.instantiateVariableFont(f, {"wght": weight})`, then name IDs 1/2/3/4/6/16/17 rewritten, `OS/2.usWeightClass`, `fsSelection` and `head.macStyle` set to match the slot. Cached in `.fontcache_ttf/`. A family with no variable source (Orbitron has no italic) falls back to the upright (`:74-77`). |
| glyph set | `:107-113` | `KEEP` = ASCII 0x20–0x7E, Latin-1/Extended-A 0xA0–0x17F, Cyrillic 0x400–0x45F, superscripts/subscripts 0x2070–0x208F, plus `– — ‘ ’ “ ” • … ‰ € ™ ← → − ≠ ≤ ≥ ● ✓ ✗ Δ № ∑ ☐ ☑ ☒ ＊`. **Plus every character the document itself sets** (`:174-176`), so editing in either alphabet stays possible. |
| obfuscation | `:144-150` | OOXML font obfuscation: the first 32 bytes XORed with the GUID's bytes reversed. |
| wiring | `:200-241` | `word/fonts/fontN.odttf`, `word/fontTable.xml` entries with `embedRegular`/`embedBold`/`embedItalic`/`embedBoldItalic`, `word/_rels/fontTable.xml.rels`, the `odttf` default in `[Content_Types].xml`, and `<w:embedTrueTypeFonts/><w:embedSystemFonts/>` in `settings.xml`. |

Verified in `BLANK_TEMPLATES/DOCX/iCoA_BLANK_TEMPLATE.docx` as built: 12 `word/fonts/*.odttf`
under 8 family names — `Montserrat` (regular, italic, bold), `Montserrat SemiBold`
(regular, italic), `Orbitron` (bold), `Orbitron Black`, `Orbitron ExtraBold`,
`Orbitron SemiBold` (italic), `Roboto Mono` (bold), `Roboto Mono SemiBold` (regular,
italic); `embedTrueTypeFonts` and `embedSystemFonts` both present.

### 4.3 Why the fonts have to be embedded **twice**

They are two separate requirements and neither substitutes for the other:

* the **web** faces (house_fonts) decide what the *PDF* looks like and how wide each run is;
* the **Word** faces (embed_fonts) decide whether a reviewer's machine, which has never
  heard of Montserrat, lays the text out at those same widths. Without them Word
  substitutes something wider or narrower, the lines re-wrap, and the page stops being the
  page (`embed_fonts.py:7-11`).

`embed_fonts.instance()` is also what the converter **measures** against
(`pdf_to_docx_exact.py:225-235` — `metric_font()` opens the very TTF that will be
embedded), so the width correction in §6.2 is computed from the exact outlines Word will
use.

---

## 5 · Stage 4 — PDF → DOCX (`pdf_to_docx_exact.py`)

`convert_page(page, doc, dpi, first, fields=None, drop_shadows=True)` (`:547-605`) is the
whole of it, in order:

1. **Read the page once** (`:552-554`). Every `get_text` call builds fresh dictionaries, so a
   second read returns different objects and the shadow twins found in the first could never
   be matched against them.
2. **Find shadow twins** (`:555`) and assert that dropping them loses no text (`:559-564`;
   §6.4).
3. **Split the spans** (`:566-574`) into `spans` (will become Word runs) and `keep` (stay in
   the page image). A span is ours if the PDF names a house face for it — or if the DOM
   field covering it names one (`covering_face`, `:662-667`), which is what rescues the
   synthesised-oblique placeholders.
4. **Redact only the spans that come back as runs** (`:579-585`). The rectangle is pulled in
   by 0.3 pt horizontally and 0.2 pt vertically, because a redaction removes any glyph whose
   box *meets* the rectangle and the symbol fallbacks sit flush against their neighbours in
   the same line. `apply_redactions(images=PDF_REDACT_IMAGE_NONE,
   graphics=PDF_REDACT_LINE_ART_NONE, text=PDF_REDACT_TEXT_REMOVE)` — **vector art and
   images are never touched.**
5. **Render what is left** at `dpi` (default 300) to a PNG (`:587-589`).
6. **Set up the section** from the PDF's own `page.rect` (`:591-592` → `page_setup`,
   `:161-167`): page size in EMU, **all** of `left/right/top/bottom_margin`,
   `header_distance`, `footer_distance`, `gutter` set to `Emu(0)`. The frames carry every
   position.
7. **Lay the PNG in as the page's background** (`:594-599`) — see §6.1.
8. **Emit the text** — `emit_fields()` when a field map was given, else one `add_span()` per
   span (`:601-604`).

`convert()` (`:695-719`) loops the pages, then: `pdf.close()` **without saving**, so the
controlled PDF on disk is never written to — the redactions live only in memory
(`:705-707`); `doc.save(out)`; `embed_fonts.py` as a subprocess; `check_order(out)`, which
raises `SystemExit` rather than writing a file Word would refuse.

---

## 6 · Why the page is not re-flowed

### 6.1 The page layer: one floating `wp:anchor`, `behindDoc`

`float_behind(run_picture, width_pt, height_pt, z)` (`:170-208`). python-docx only writes
`wp:inline`, which sits **in the text flow** and pushes the first line down a page's worth.
The background has to be out of the flow and behind the text, so the `wp:inline` is replaced
by a `wp:anchor` carrying:

```
distT=0 distB=0 distL=0 distR=0 simplePos=0 relativeHeight=<1 + page.number>
behindDoc=1 locked=0 layoutInCell=1 allowOverlap=1
  <wp:simplePos x=0 y=0/>
  <wp:positionH relativeFrom="page"><wp:posOffset>0</wp:posOffset></wp:positionH>
  <wp:positionV relativeFrom="page"><wp:posOffset>0</wp:posOffset></wp:positionV>
  <wp:extent cx=width_pt*12700 cy=height_pt*12700/>
  <wp:effectExtent l=0 t=0 r=0 b=0/>
  <wp:wrapNone/>
```

The original `wp:extent`/`wp:effectExtent` children are skipped when copying (`:203-205`) so
they are not duplicated. The carrying paragraph gets
`<w:spacing w:before="0" w:after="0" w:line="20" w:lineRule="exact"/>` (`:596`) — a
one-point line, so the background paragraph itself occupies nothing.

Verified in the built `iCoA_BLANK_TEMPLATE.docx`: exactly one `behindDoc="1"` anchor, one
`wrapNone`, `wp:extent` = `7555992 × 10692384` EMU = 594.96 × 841.92 pt, and
`word/media/image1.png` at 2479 × 3508 px — 300.0 dpi across 594.96 pt.

### 6.2 The text layer: one `w:framePr` paragraph per span/field

`frame(doc, x0, y0, family, size, width_pt, page_w_pt, line_pt=None)` (`:358-379`) writes:

```xml
<w:framePr w:w="…" w:hRule="auto" w:wrap="none"
           w:vAnchor="page" w:hAnchor="page" w:x="…" w:y="…"/>
<w:spacing w:before="0" w:after="0" w:line="…" w:lineRule="exact"/>
<w:ind w:left="0" w:right="0" w:firstLine="0"/>
<w:jc w:val="left"/>
```

`x` and `y` are in **twips** (`TWIP_PER_PT = 20`, `:72`), absolute, anchored to the *page*.
There is no paragraph stream to break, so nothing can re-flow. `w:wrap="none"` keeps
surrounding text from flowing round it. The frame width is clamped to
`min(max(width_pt, 4.0), max(page_w_pt - x0 - 0.5, 4.0))` (`:365`) so Word can never pull a
frame back inside the page and drag the right-hand column with it. `line`/`lineRule="exact"`
fixes the leading — for a wrapped cell, to the leading measured off the page
(`add_field`, `:492`), otherwise to the type size.

Verified: a real frame from the built iCoA file is
`<w:framePr w:w="504" w:hRule="auto" w:wrap="none" w:vAnchor="page" w:hAnchor="page" w:x="4445" w:y="7515"/>`,
and the section is `<w:pgSz w:w="11899" w:h="16838"/>` with every `w:pgMar` value `0` — i.e.
the page size comes from the PDF (594.95 × 841.9 pt), not from a hardcoded A4.

**Why the text is still editable and selectable.** Every run is an ordinary `w:r` inside an
ordinary `w:p`. The frame only says *where the paragraph sits*; it is not a shape, not a
text box object, not an image. Click into it in Word and you are in a paragraph: type,
select, search, spell-check, change the text. Only the background — rules, bars, panels,
logo, signature block — is a picture, and it is behind everything and out of the flow.

### 6.3 The frame origin: `FRAME_DX`, `FRAME_DY_A`, `FRAME_DY_B`

Word seats a line inside a box it sizes from the **face's own ascent**, not from the baseline
the PDF gives, so the frame origin needs an offset. It is measured, not guessed:

```python
FRAME_DX   = -0.100                                              # :84
FRAME_DY_A =  0.014                                              # :85
FRAME_DY_B = {"Montserrat": 0.3058, "Orbitron": 0.2083,
              "Roboto Mono": 0.2439}                             # :88
FRAME_DY_B_DEFAULT = 0.2165                                      # :89
```

applied as (`:368-371`):

```
x = (x0 + FRAME_DX) * 20
y = (y0 + FRAME_DY_A + FRAME_DY_B[family] * size) * 20
```

`FRAME_DY_B` is **per family and multiplied by the type size** because the same size drops
Orbitron and Roboto Mono differently from Montserrat (`:86-87`). `FRAME_DY_B_DEFAULT`
covers a family not in the table.

`calibrate(src, dpi)` (`:723-773`) is what produced them: convert → render the `.docx` back
to PDF through **LibreOffice** (`soffice --headless --convert-to pdf`, `:729`) → match spans
by their text, keeping only texts that occur exactly once (`:739-740`) → median `dx`, and a
least-squares fit of `dy = a + b·size` (`:752-759`) so the size-proportional part is taken
*out of the frame origin* rather than averaged away. It prints the replacement constants
directly (`:764-771`).

### 6.4 The four things that must be right

#### (1) OOXML child ordering

`w:rPr` and `w:pPr` have **ordered** content models. A child in the wrong place does not get
repaired — Word declines to open the file and says only *"unreadable content"*, which is how
an earlier Word export was lost (`:788-792`).

* `_RPR_ORDER` (`:138-142`) — the full CT_RPr sequence, 40 names, `rStyle, rFonts, b, bCs,
  i, iCs, caps, smallCaps, strike, dstrike, outline, shadow, emboss, imprint, noProof,
  snapToGrid, vanish, webHidden, color, spacing, w, kern, position, sz, szCs, highlight, u,
  effect, bdr, shd, fitText, vertAlign, rtl, cs, em, lang, eastAsianLayout, specVanish,
  oMath`. Note where `spacing` belongs: **between `color` and `w`** — a file that appends it
  after `sz` is one Word calls unreadable (`:135-137`). python-docx has no accessor for it.
* `rpr_set(rPr, tag, **attrs)` (`:146-158`) removes any existing instance, then inserts
  before the first child whose rank is greater — i.e. at the position the schema requires,
  never by appending.
* `_PPR_ORDER` (`:776-783`) — the CT_PPr sequence. `framePr` comes **before** `spacing`,
  `ind`, `jc`; `frame()` writes them in exactly that order (`:366-378`).
* `check_order(path)` (`:786-811`) re-opens the finished `.docx`, walks every `w:pPr` and
  `w:rPr` in `word/document.xml`, and reports any unknown child or any out-of-order
  sequence. `convert()` raises rather than writing the file (`:712-715`). It caught a real
  one: `w:jc` written before `w:contextualSpacing`
  (`tracker/PDF_TO_WORD_2026-09-21.md:91-96`).

  *Checked while writing this:* `check_order()` returns clean for all three built templates.

#### (2) Half-point `w:sz`

Word measures type in half-points and nothing finer. The certificate's table is set at
**15.975 pt**, which Word cannot hold; python-docx truncated it to 15.5 and every run came
out three per cent narrow — the right-hand column ended 9 pt short of its own edge
(`:318-322`).

```python
size = max(0.5, round(span["size"] * 2) / 2.0)   # style_of, :323
```

and written as an explicit integer half-point count (`emit_run`, `:349-350`):

```python
rpr_set(rPr, "sz",   val=int(round(size * 2)))   # 15.975 → 16.0 → w:sz 32
rpr_set(rPr, "szCs", val=int(round(size * 2)))
```

The rounding happens **before** the width correction, so `tracking()` corrects to the width
Word will actually set, not to the width the PDF nominally used.

#### (3) Letter-spacing spread over the gaps (n − 1), with the two-run split

`tracking(text, size, want_pt, family, weight, italic)` (`:238-268`) measures how much wider
the run must be made: `delta = want_pt - font.text_length(text, fontsize=size)`, in twips.
Two causes, one measurement — CSS `letter-spacing` on the titles and section bars (set
plainly, `СЕРТИФИКАТ ЗА КВАЛИТЕТ` is two thirds of the width the page gives it), and the
half-point size rounding above.

A guard at `:266`: a correction that would squeeze or stretch by more than **a quarter of
the type size per character** is refused and the run is left at its natural width — the
section number `02` was asked to give back four and a half points a character and came out
illegible.

`split_tracking(total_twips, n)` (`:271-297`) turns that into per-character spacing:

```python
gaps = n - 1
if gaps <= 0:
    return 0, 0
k = total_twips // gaps          # floors towards minus infinity, as wanted
r = total_twips - k * gaps
return k + (1 if r else 0), r
```

Two distinct points:

* **n − 1, not n.** `w:spacing` after the *last* character moves nothing visible — the
  glyphs still end where they ended — so the correction is spread over the gaps *between*
  characters. That single point was worth **1.6 pt** on the title (`:277-279`).
* **the two-run split.** `w:spacing` is one whole twip per character, so a sixty-character
  line could only be corrected in steps of three points. Giving the first `r` characters one
  twip *more* than the rest brings the granularity down to a twentieth of a point
  (`:273-276`). `emit_run` (`:330-332`) does the split:

```python
hi, r = split_tracking(track, len(text)) if abs(track) >= 3 else (0, 0)
lo = hi - 1 if r else hi
parts = [(text[:r], hi), (text[r:], lo)] if 0 < r < len(text) else [(text, hi)]
```

  — so a run whose correction is under 3 twips (0.15 pt) is left alone, and otherwise the
  text is emitted as **two runs** with `w:spacing` differing by one twip.

Also in `emit_run`: `rpr_set(rPr, "kern", val=0)` (`:355`). Kerning is switched **off**
because the width was measured from the face's plain advances and Word's kerning would pull
the run back in under the correction just applied. Verified in the built iCoA file: 826
`<w:kern w:val="0"/>` elements.

And a single character has no gaps at all, so a lone spacer cannot be spaced through
`split_tracking`. `emit_gap(p, style, gap_pt, face)` (`:531-544`) sets its `w:spacing`
outright:

```python
space = font.text_length(" ", fontsize=style[3])
emit_run(p, " ", style, 0)
rpr_set(rPr, "spacing", val=int(round((gap_pt - space) * TWIP_PER_PT)))
```

This is what carries the next run to where the page starts it. The earlier attempt bridged
the gap by letter-spacing the *preceding word*, which distorted the word and still fell
6 pt short of the column (`:519-527`).

#### (4) Shadow-twin suppression

A CSS `text-shadow` is drawn, in a PDF, by printing the glyphs a **second time**. Every rule
in this design offsets downwards by one CSS pixel — 0.75 pt — so the twin is always the
lower of the pair and always in the shadow's own colour (`:608-611`).

```python
SHADOW_DY = (0.5, 1.1)          # :611
```

`shadow_twins(spans)` (`:614-651`) groups by `(stripped text, round(bbox[0], 1))` and pairs
two spans when **all** of:

| test | line |
| --- | --- |
| same stripped text | `:641` (the grouping key) |
| same left edge to a tenth of a point | `:641` (the grouping key) |
| `0.5 < abs(dy) < 1.1` pt | `:647` |
| type sizes within 0.05 pt | `:648` |
| **different** colour | `:649` |

and the **lower** of the pair is the shadow (`:650`). The **font face is deliberately not
part of the identity** (`:623-629`): a synthesised oblique is embedded as a Type 3 font and
*each draw gets its own object*, so the blue placeholders came back as `Type3 (109 0 R)` and
`Type3 (110 0 R)` and a rule that compared faces let every one of them through.

The twin is **not redacted** — it stays in the page image, so the emboss still prints. It
simply does not also become a Word box (`:568-570`).

Dropping a shadow may never drop a word, so it is asserted (`:559-564`): every twin removed
must leave its own text still on the page in the span it was shadowing, or the conversion
raises `SystemExit`.

The internal certificate sets no text shadow and none is found — which is the check that
this is a precise rule and not a heuristic. *Verified on the template PDFs while writing
this:* CoQ 15 twins, iCoA **0**, specification 26.

> `convert_page`'s `drop_shadows` parameter (`:547`) has no CLI switch; `convert()` never
> passes it, so shadow suppression is always on in practice.

---

## 7 · Certificate (one box per span) vs template (one box per whole field)

### 7.1 The difference

| | certificate | template |
| --- | --- | --- |
| what it is | a record nobody edits | a document somebody types into |
| box granularity | one per **PDF text span** — `add_span()`, `pdf_to_docx_exact.py:382-393` | one per **DOM field** — `add_field()`, `:428-528`, driven by `emit_fields()`, `:670-692` |
| where the boundary comes from | the renderer's own spans | the laid-out DOM, read by the `PROBE` in the printing pass |
| invoked by | `pdf_to_docx_exact.py IN.pdf OUT.docx` (no `--fields`) | `build_template_docx.py`, which passes `fields=` |

A span is whatever the renderer happened to draw, so `[MANUFACTURE DATE]` arrives as
`[MANUFACTUR` + `E DATE]` and nobody can type a date into two boxes
(`build_template_docx.py:8-11`). The owner's words: *"is it possible that the individual
text boxes follow some logical wholeness? not just with 3 or 5 words"*.

**The 344 certificates are untouched by the field work.** Field grouping runs only when a
field map is given; without one the converter behaves exactly as it did, and re-measuring
`CoQ-PP_26-013` after the change returned the same 0.025 / 0.047 / 0.718 pt
(`tracker/PDF_TO_WORD_2026-09-21.md:167-169`).

### 7.2 Why position-based merging was rejected — the recorded evidence

From `tracker/PDF_TO_WORD_2026-09-21.md:130-136` and `build_template_docx.py:16-20`:

* taking same-baseline neighbours cut the certificate of quality's **378 spans to 256
  boxes** and joined two separate tick pills into **`HYBRIDINDICA`**;
* tightening the rule — never across a symbol, only within one of PyMuPDF's own lines —
  stopped that and left the **median box at two words**, which is the original complaint
  again;
* PyMuPDF's `blocks` are no help either: **one of them spans 21 unrelated rows of the
  heavy-metals table**.

Conclusion, in the code's own words: *"Ink position does not say what belongs together."*
The HTML does — every field of these templates is already an element.

### 7.3 The `PROBE`

`build_template_docx.py:50-87`. Run via `measure()` (`:90-99`), which is a `probe=` callback
into `render()`; it calls `page.emulate_media(media="print")` first so the layout measured is
the layout that will be **printed**, then `page.evaluate(PROBE)`.

```js
() => {
  const page = document.querySelector('.page') || document.body;
  const pr = page.getBoundingClientRect();
  const INLINE = new Set(['SPAN','A','B','I','EM','STRONG','SUP','SUB','SMALL','BR','U',
                          'CODE','TT','LABEL','ABBR','WBR','S','MARK','FONT','BDI','Q']);
  const out = [];
  const take = (el, ph) => {
    const r = el.getBoundingClientRect();
    const t = (el.innerText || el.textContent || '').trim();
    if (!t || r.width <= 0 || r.height <= 0) return;
    const cs = getComputedStyle(el);
    out.push({x: r.x - pr.x, y: r.y - pr.y, w: r.width, h: r.height, text: t, ph: ph,
              ff: cs.fontFamily, fw: cs.fontWeight, fs: cs.fontStyle});
  };
  const walk = (el) => {
    if (el.classList && el.classList.contains('ph')) { take(el, true); return; }
    const kids = Array.from(el.children);
    const leaf = kids.every(k => INLINE.has(k.tagName));
    if (leaf) {
      take(el, false);
      el.querySelectorAll('.ph').forEach(k => take(k, true));
      return;
    }
    kids.forEach(walk);
  };
  walk(page);
  return {pw: pr.width, ph: pr.height, fields: out};
}
```

Three things it does deliberately:

* **a leaf is an element whose children are all inline** — the smallest thing that is still
  a whole field;
* **`el.querySelectorAll('.ph')`, not `el.children`** (`:80`). Looking one level down found
  **4 of the certificate's 49** placeholders; the other 45 were left to whatever geometry
  happened to cover them, which is how `[PRODUCTION BATCH]` stayed in two pieces
  (`:76-79`);
* **it returns the computed face** (`ff`, `fw`, `fs`) as well as the box (`:64-68`). See
  §7.5.

Coordinates come back relative to the `.page` box in CSS pixels, together with `pw`/`ph`.

### 7.4 `house_face()` and `fields_for()`

`house_face(family, weight, style)` (`:105-115`) maps a computed CSS font to
`[family, weight, italic]` via `HOUSE = {"montserrat": "Montserrat", "roboto mono":
"Roboto Mono", "orbitron": "Orbitron"}` (`:102`), walking the comma-separated stack and
stripping quotes; `"bold"` → 700, anything unparsable → 400. Returns `None` if the font is
not ours.

`fields_for(raw, pdf_path)` (`:118-134`) converts pixels to points by the **one measurement
that ties the browser to the PDF without either being assumed**:

```python
scale = w_pt / raw["pw"] if raw["pw"] else 0.75      # :124
```

— the printed page's own width in points divided by the probe's page width in pixels. Then
the ordering that matters (`:133`):

```python
out.sort(key=lambda f: (0 if f["ph"] else 1, f["w"] * f["h"]))
```

**A placeholder first, then the smallest box**, so a field is claimed by the element that
*is* it and not by an ancestor that happens to contain it. Returns `{0: out}` — the
templates are one page each. (The CLI form of the same thing is `--fields FILE.json`,
loaded by `load_fields()`, `pdf_to_docx_exact.py:859-865`, keyed by page number.)

### 7.5 The Type 3 rescue

46 of the 51 placeholder spans are Type 3. The blue italic is
`font-style:italic; font-weight:600` and Montserrat has no true italic at that weight in the
linked face set, so the renderer synthesises the slant and embeds it as a font **with no
family name at all**. `face_of()` (`:101-119`) rejects them, so the very fields the owner
types into would have been left in the page image
(`pdf_to_docx_exact.py:300-311`, `build_template_docx.py:60-65`).

The DOM's computed face rescues them. `covering_face(span, fields)` (`:662-667`) returns the
face of the first field whose box contains the span's centre; `convert_page` uses
`face_of(s["font"]) or covering_face(s, fields)` to decide whether a span becomes a run
(`:574`). In `emit_fields` (`:681-683`) the precedence is explicit: **the DOM's face is used
only where the PDF names none; where the PDF names one, the PDF is the page and wins.**

*Measured while writing this:* with no field map the iCoA template gives 409 boxes and
leaves 77 spans in the page image; with the field map it gives **444** boxes — exactly
409 + 35, and 35 is exactly the number of `.ph` placeholders in that template. The rescue is
visible in the arithmetic.

### 7.6 `add_field()` — the three cases and the widths

`pdf_to_docx_exact.py:428-528`. Spans of one element, grouped into lines by
`round(origin[1], 1)` and sorted left-to-right (`:456-462`).

| case | condition | treatment |
| --- | --- | --- |
| one line, one style | `len(styles) == 1 and same_text(...)` | one run carrying the **element's own text**, tracked to the ink width (`:501-511`) |
| one line, several styles | e.g. `Assay — Total Δ⁹-THC*`, where a superscript starts a new span | one box, a run per span, with the inter-span gap carried by `emit_gap` (`:513-528`) |
| several lines, one style, text agrees | uniform styling | the element's whole text goes in and **Word re-wraps it inside the box** — this is what makes the field typable and repairs a break made mid-word |
| several lines, mixed styling | — | `return 0` (`:496-497`): handed back to the caller, which falls back to span-by-span. *"joining those safely would mean guessing where a word ended, and a template is not a place to guess."* |

`same_text(spans, dom_text)` (`:405-425`) is the safety catch: the element's text may be
preferred only while it agrees with the page. The two may differ in **whitespace alone** —
that difference *is* the line break being repaired — and in nothing else. *"A converter may
put a broken word back together and may not put a word there that the page does not
print."*

The frame width (`:470-489`) is the **maximum** of four quantities, and each is there
because of a specific failure:

```python
width = max(ink_w + 2.0, widest + 2.0, natural + 4.0, box_w_pt or 0.0)
```

* `box_w_pt` — the DOM element's own width, so a longer typed value wraps inside the field;
* `ink_w + 2.0` / `widest + 2.0` — never narrower than the page already uses. Taking the
  element's width alone looked right and was not: a design lets text overflow its box, so
  Word wrapped lines the page prints flat — `02` broke into `0` and `2`, the headline fell
  onto the phenotype row, and every cell of the RESULT column wrapped into the row beneath
  (`:471-477`);
* `natural + 4.0` — never narrower than the text needs at its natural width, **but only
  where the page itself sets the field on one line** (`:484-488`). A cell the page wraps is
  wrapped because its column is that wide, and widening it pushed `[PRODUCTION BATCH]`
  straight across the manufacture date beside it.

`in_field(span, f)` (`:654-659`) is centre-in-box with a 0.6 pt tolerance on each side.

### 7.7 `words()` — the before/after instrument

`build_template_docx.py:137-152` counts, in a built `.docx`, the paragraphs that carry a
`w:framePr` and hold non-blank text, and returns `(count, median words per box)`. `main()`
(`:176-183`) builds each template **twice** — once with `fields=None` into a temporary
`.<name>.span.docx` which is then deleted, once with the field map — and prints the two side
by side under the headings `one box/span` and `one box/field`.

---

## 8 · How to run it

All commands are as they appear in the code and the repo's own notes. Run from the
repository root, `/home/user/letta-stack`.

### 8.1 Rebuild the three blank HTML templates

```sh
python3 deliverables/qc_gap_analysis/build_blank_templates.py
```

(`build_blank_templates.py:5`.) Diffs the fleets, inserts the `.ph` descriptors, copies the
owner's specification blank, then runs `fit_placeholders` on all three and **fails** if any
descriptor is still clipped.

### 8.2 Build the three templates as PDF **and** Word

```sh
python3 deliverables/qc_gap_analysis/BLANK_TEMPLATES/build_template_docx.py
```

(`build_template_docx.py:5`.) Takes every `*.html` in `BLANK_TEMPLATES/`, subsets and inlines
the fonts, prints each to `BLANK_TEMPLATES/PDF/`, probes the DOM in the same pass, and writes
`BLANK_TEMPLATES/DOCX/<name>.docx` with one box per field. Needs no arguments; it finds
Chromium itself with `glob.glob("/opt/pw-browsers/chromium*/chrome-linux/chrome")`
(`:167`).

### 8.3 Convert any single PDF to Word (certificate mode, one box per span)

```sh
python3 deliverables/qc_gap_analysis/design_handoff/toolchain/pdf_to_docx_exact.py \
    IN.pdf OUT.docx [--dpi 300] [--no-fonts]
```

(`pdf_to_docx_exact.py:5`.) `--dpi` defaults to 300 (`:880`); `--no-fonts` skips the
`embed_fonts.py` step.

### 8.4 Convert a whole folder

```sh
python3 deliverables/qc_gap_analysis/design_handoff/toolchain/pdf_to_docx_exact.py \
    --batch IN_DIR OUT_DIR [--dpi 300] [--jobs 4]
```

(`pdf_to_docx_exact.py:6`.) The real recorded invocation, from
`design_handoff/docx/_SUPERSEDED.md:26-27`:

```sh
python3 design_handoff/toolchain/pdf_to_docx_exact.py --batch --force \
    design_handoff/pdf/ISSUE_COQ design_handoff/docx/ISSUE_COQ
```

> The docstring advertises `--jobs 4`, but `main()` defines no `--jobs` argument
> (`:876-889`) — passing it would be rejected by argparse. The batch loop is serial
> (`:894-903`). `--force` rewrites existing outputs.

### 8.5 Convert with an explicit field map (template mode, from the CLI)

```sh
python3 .../pdf_to_docx_exact.py IN.pdf OUT.docx --fields FIELDS.json
```

(`:888`.) `FIELDS.json` is `{"<page number>": [{"x","y","w","h","text","ph","face"}, …]}`
in **points**, as produced by `fields_for()`.

### 8.6 Measure and re-calibrate

```sh
python3 .../pdf_to_docx_exact.py SRC.pdf --verify      # where every run landed
python3 .../pdf_to_docx_exact.py SRC.pdf --calibrate   # prints replacement constants
```

(`:883-885`, `verify()` `:814-856`, `calibrate()` `:723-773`.) Both convert, then render the
`.docx` **back** to PDF through LibreOffice and compare span positions with the source.
`--verify` reports median / p95 / max for the left, top and right edge plus the six furthest
off; `--calibrate` prints the `FRAME_DX` / `FRAME_DY_A` / `FRAME_DY_B[...]` values to paste
back into the file. Note `verify()` converts at **`dpi=150`** by default (`:814`), where
production is 300.

### 8.7 Print the certificate fleets (context)

```sh
python3 deliverables/qc_gap_analysis/live_instrument/print_coq_pdfs.py \
    --scope deliverables/qc_gap_analysis/tracker/coq_draft_scope_2026-09-10.csv \
    --chromium /opt/pw-browsers/chromium-1194/chrome-linux/chrome
```

(`print_coq_pdfs.py:5-7`.) Also takes `--drafts`, `--out`, and
`--series {initial,reissue}` (`:152-159`).

### 8.8 What the environment has to provide

| requirement | where it is read | present on this machine (23.09.2026) |
| --- | --- | --- |
| `pymupdf` | `pdf_to_docx_exact.py:62` | 1.28.2 |
| `python-docx` | `:63-66` | 1.1.2 |
| `fontTools` (incl. `varLib.instancer`) | `embed_fonts.py:33-35`, `house_fonts.py:114-133` | 4.55.3 |
| `lxml` | `build_blank_templates.py:30`, `check_order`, `words` | 5.3.0 |
| `playwright` + Chromium | `print_coq_pdfs.py:123-127` | `/opt/pw-browsers/chromium-1187`, `chromium-1194` |
| `soffice` (LibreOffice) — **only** for `--verify` / `--calibrate` | `:729`, `:825` | `/usr/bin/soffice` |
| `pdfunite` — only for `merge()` | `print_coq_pdfs.py:146` | `/usr/bin/pdfunite` |
| variable TTFs at `$PP_FONT_SRC` | `embed_fonts.py:38` | `/tmp/claude-0/fonts` — 5 files: `Montserrat[wght].ttf`, `Montserrat-Italic[wght].ttf`, `RobotoMono[wght].ttf`, `RobotoMono-Italic[wght].ttf`, `Orbitron[wght].ttf` |
| network reachability to `fonts.googleapis.com` for the CSS index | `house_fonts.py:64-66` | required at build time; only the `.woff2` payloads are cached |

---

## 9 · Verified accuracy

### 9.1 Recorded in the repo

**Certificates, one box per span** — `tracker/PDF_TO_WORD_2026-09-21.md:82-85`. Produced by
`--verify`: convert, render back to PDF through LibreOffice, match runs by text. A point is
a third of a millimetre.

| | left edge | top edge | right edge |
| --- | ---: | ---: | ---: |
| `CoQ-PP_26-013` · 199 runs matched | median 0.011 · **max 0.025 pt** | median 0.012 · **max 0.047 pt** | median 0.037 · **max 0.718 pt** |
| `iCoA-PP_26-001` · 290 runs matched | median 0.012 · **max 0.025 pt** | median 0.011 · **max 0.047 pt** | median 0.031 · **max 0.663 pt** |

**Templates, one box per field** — `tracker/PDF_TO_WORD_2026-09-21.md:158-162` (before the
shadow-twin fix):

| | boxes | placeholders whole | left edge | top edge |
| --- | ---: | ---: | ---: | ---: |
| CoQ | 291 | 48/48 | median 0.015 pt | median 0.016 pt |
| ImB specification | 279 | 13/13 | median 0.010 pt | median 0.013 pt |
| iCoA | 445 | 45/60 | median 0.013 pt | median 0.013 pt |

**After the shadow-twin fix and the descriptor work** —
`tracker/PDF_TO_WORD_2026-09-21.md:266-276`:

| | boxes | placeholders, all whole | cut off |
| --- | ---: | ---: | ---: |
| CoQ | 276 | 48 | **0** |
| internal certificate | 444 | 35 | **0** |
| specification | 253 | 11 | **0** |

with *"Placement is unchanged: left edge median 0.010–0.015 pt, top 0.012–0.016 pt"*
(`:275-276`). `tracker/iCOA_AUDIT_KIT/HANDOFF_FOR_COWORK.md:122-125` states the same
envelope as *"verified to placement medians of 0.015–0.02 pt"*.

**Shadow twins in the certificate fleets** — `tracker/PDF_TO_WORD_2026-09-21.md:184-201`:
CoQ certificate 383 spans / **19** drawn twice; specification sheet 345 / **22**; internal
certificate 484 / **0** (it sets no text shadow). *"19, 0 and 22 twins removed and no text
lost."* Box counts `291 → 276`, `279 → 255`, `445 → 445`.

**What stays in the page layer** — `tracker/PDF_TO_WORD_2026-09-21.md:98-105`: 39 spans on a
certificate of quality and 65 on an internal certificate are glyph-level fallbacks
(`☒ ☐ ≤ ∑ Δ` and the superscripts, carried by DejaVu and Liberation). 342 runs on a
certificate of quality and 419 on an internal certificate are Word runs.

**Font subsetting, CoQ fleet run** — `design_handoff/pdf_run.log:1`:
`fonts: 59 faces, 1908 KB upstream -> 252 KB subset`.

### 9.2 Measured from the files on disk, 23.09.2026

These are **not** repo records; they are what the artifacts currently in
`BLANK_TEMPLATES/` say. They will change on the next rebuild.

Built artifacts:

| file | size |
| --- | ---: |
| `BLANK_TEMPLATES/DOCX/CoQ_BLANK_TEMPLATE.docx` | 549,509 B |
| `BLANK_TEMPLATES/DOCX/iCoA_BLANK_TEMPLATE.docx` | 538,604 B |
| `BLANK_TEMPLATES/DOCX/ImB_Specification_BLANK_TEMPLATE.docx` | 662,763 B |

Template PDFs, all one page, all 594.96 × 841.92 pt:

| PDF | spans | shadow twins found | PDF names a house face | PDF names none |
| --- | ---: | ---: | ---: | ---: |
| `CoQ_BLANK_TEMPLATE.pdf` | 378 | 15 | 300 | 78 |
| `iCoA_BLANK_TEMPLATE.pdf` | 486 | **0** | 409 | 77 |
| `ImB_Specification_BLANK_TEMPLATE.pdf` | 356 | 26 | 301 | 55 |

Built DOCX, field mode vs span mode (span mode rebuilt into the scratchpad for the
comparison; nothing in the project was changed):

| | one box / field (shipped) | one box / span | `.ph` in the HTML | whole-placeholder boxes |
| --- | ---: | ---: | ---: | ---: |
| CoQ | **276** boxes, median 2 words | 288 boxes, 75 spans left in the image | 49 | 48 |
| iCoA | **444** boxes, median 2 words | 409 boxes, 77 spans left in the image | 35 | 35 |
| ImB specification | **253** boxes, median 2 words | 284 boxes, 46 spans left in the image | 12 | 11 |

Two things worth reading off that table:

* the field map both **merges** (CoQ: 288 span-boxes → 276) and **rescues** (iCoA: 409 → 444,
  the difference being exactly the 35 Type 3 placeholders);
* the **median box is 2 words in both modes.** The virtue of the DOM boundaries is not a
  higher word count — most fields on these documents genuinely are one or two words — it is
  that each box is a *whole field*: `[MANUFACTURE DATE]` is one box you can type a date
  into, rather than `[MANUFACTUR` plus `E DATE]`.

Structural checks run on the shipped files: `check_order()` clean on all three; no `w:xAlign`
or `w:yAlign` anywhere; exactly one `behindDoc="1"` anchor per page; background PNG at
300.0 dpi; `<w:pgMar>` all zero. Doctests: `pdf_to_docx_exact.py` 16/16 pass,
`build_blank_templates.py` 11/11 pass.

---

## 10 · Known limitations and what is still open

1. **The doubling is still in the issued PDFs.** Suppressing the shadow twin fixes the Word
   file only. Any CSS `text-shadow` doubles the glyphs in the PDF text layer, and only
   dropping `text-shadow` in print would stop it — which takes the 1 px emboss off the
   tick-chips and section bands of 172 certificates of quality and 57 specification sheets
   and means reprinting them. That is a change to an approved look, not a repair. *"The
   owner has asked for it to be planned; it is not done."*
   (`tracker/PDF_TO_WORD_2026-09-21.md:211-216`.)
2. **The already-committed fleets keep their doubled boxes** until re-converted, which needs
   more disk than the 21.09 session held (`:218-219`).
3. **Symbol spans stay in the page image.** `☒ ☐ ≤ ∑ Δ` and the superscripts are carried by
   DejaVu and Liberation, not a house face, so they are not redacted and not boxed. They
   print exactly as the PDF prints them and are **not editable**
   (`pdf_to_docx_exact.py:38-43`). Measured above: 55–78 such spans per template — a larger
   share on the templates than on a certificate, because `UNTICKED = ☐` adds one per tick
   box.
4. **Mixed-style wrapped cells fall back to span-by-span.** `add_field` returns 0 for them
   (`:496-497`), so those cells are still one box per span in the template.
5. **Two adjacent placeholders with no separating character become one box.** Verified on
   the shipped CoQ template: the HTML has
   `<span style="font-weight:800;…"><span class="ph">[BATCH 2]</span></span><span><span class="ph">[THC %]</span></span>`
   with no whitespace between them, the renderer draws them as a **single** PDF span
   (`OrbitronSemiBold` 17.25 pt, bbox `120.71 … 310.10`), and the DOCX carries one box whose
   text is `[BATCH 2][THC %]`. This is the converter behaving correctly — it must never
   introduce a character the page does not print — but it means the headline's batch and THC
   fields cannot be typed into separately. That is why the count is 49 `.ph` in the HTML and
   48 bracket-boxes in the DOCX. **Open**; the fix belongs in the template markup (a
   separator between the two spans), not in the converter.
6. **`--verify` and `--calibrate` measure through LibreOffice, not Word**
   (`:729`, `:825`). The placement figures in §9.1 are therefore LibreOffice's rendering of
   the `.docx`. No Microsoft-Word measurement is recorded anywhere in the repo.
7. **A missing font source degrades silently.** `metric_font()` swallows any exception and
   caches `None` (`:225-235`); `tracking()` and `natural_width()` then return 0 and every
   width correction is quietly skipped. `embed_fonts.embed()` returns 0 rather than failing
   when no face matches. So if `$PP_FONT_SRC` (default `/tmp/claude-0/fonts`, a session
   scratch path) is empty, the build still succeeds and produces a `.docx` with **no
   letter-spacing correction and no embedded faces**. There is no assertion against this.
8. **`house_fonts._fetch` always hits the network** for the Google CSS index (`:64-66`); only
   the `.woff2` payloads are cached in `.fontcache/`. An offline rebuild fails.
9. **`fit_placeholders` does not block Google's font hosts.** It launches its own browser
   (`build_blank_templates.py:398-401`) with no `page.route` abort, unlike `render()`
   (`print_coq_pdfs.py:129-130`). The inlined `@font-face` blocks use `font-display:block`,
   so in practice the measurement uses the inlined faces — but the asymmetry is real and the
   fit measurement is not network-isolated the way the print pass is.
10. **`--jobs` is documented but not implemented** (§8.4).
11. **`drop_shadows` has no CLI switch** (`:547`; `convert()` never passes it).
12. **`fit_placeholders` gives up after six rounds** (`:418`) and imports `render` without
    using it (`:382`).

---

## 11 · Where the existing record and the code disagree

The code is authoritative. Each row below was checked against the code and, where possible,
against the built files.

| claim in the record | what the code does |
| --- | --- |
| `tracker/PDF_TO_WORD_2026-09-21.md:48-50` lists *"`w:xAlign` beats `w:x`"* as the first of the four things to get right | **Historical.** `frame()` (`:366-371`) writes only `w`, `hRule`, `wrap`, `vAnchor`, `hAnchor`, `x`, `y` — the alignment attributes are gone, as that note itself says. Verified: no `w:xAlign` or `w:yAlign` in any built template. The four things that matter **now** are the ones in §6.4. |
| `tracker/PDF_TO_WORD_2026-09-21.md:190-192` says the shadow pair is identified by *"same text, **same face**, the same left edge…"* | **Wrong, and the same file corrects itself at `:261-264`.** `shadow_twins()` (`:614-651`) deliberately excludes the face: *"The FACE is deliberately not part of it."* The identity is text + left edge + `0.5 < abs(dy) < 1.1` + size within 0.05 + different colour. |
| `BLANK_TEMPLATES/README.md:79-83` gives CoQ 276 / spec 255 / iCoA 445 boxes, with 48/48, 13/13, 45/60 placeholders | **Stale — a mix of the before and after states.** The shipped files measure 276 / 253 / 444 boxes with 48 / 11 / 35 placeholders, all whole, none cut off, which matches the tracker's later table at `:266-270`. |
| `BLANK_TEMPLATES/README.md:6-8` gives 50 / 61 / 12 placeholders per template, and `:54-56` gives 49 / 60 / 12 in the PDFs | **Stale for the iCoA.** The shipped HTML carries 49 / **35** / 12 `.ph` spans; 35 is the post-tick-fix number the tracker records at `:240`. The CoQ difference (50 recorded vs 49 on disk) is not explained by anything in the code — treat the on-disk count as the figure and re-derive it after any rebuild. |
| `tracker/PDF_TO_WORD_2026-09-21.md:184-188` gives the CoQ 383 spans with 19 twins and the specification 345 / 22 | Those are the **certificate** documents. The **template** PDFs on disk measure 378 / 15 and 356 / 26. Both are right; they are different documents. Do not quote one for the other. |
| `tracker/PDF_TO_WORD_2026-09-21.md:39-41` says *"eighteen faces per certificate"* | Face count is per document and is derived from the runs actually present (`embed_fonts.faces_used`, `:153-164`). The shipped iCoA template carries **12**. |
