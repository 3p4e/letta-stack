# The Word set, made from the printed page — 21.09.2026

## What the owner ruled

> *"Your conversion from HTML to Word is a totally different file, different design,
> different structure, different everything — that will not do in a GMP environment. But
> as you can actually convert the certificate into PDF, then from PDF you can convert it
> into Word — like iLovePDF converts from PDF into Word without any visual differences.
> Can you do that?"*

He is right, and the reason is worth stating plainly. An HTML-to-Word writer re-flows the
document: it decides for itself where a line breaks and how tall a row is. The page that
comes out is a page nobody approved, and a certificate whose layout is not the approved
layout is not that certificate. The Word files are now made the way he asked — from the
printed PDF, not from the source.

## What was tried first, and why it was not enough

| route | what happened |
| --- | --- |
| `html_to_docx.py` | re-flow from source. On the specification it dropped the whole Section 01 banner and overlapped the Section 02 rows. This is the route the owner rejected. |
| `pdf2docx` 0.5.13 | re-flow from the PDF — better, but still a reconstruction. On `CoQ-PP_26-013` it clipped the RESULT column off the right edge, overlapped the section bars with their labels, and spilled one A4 page onto two. Tuning it (`page_margin_factor_*`, `max_line_spacing_ratio`, `min_section_height`) got it back to one page and no further: the overlaps stayed. |

Both fail for the same reason: they ask what the document *means* and rebuild it. Neither
is told what it should look like.

## What was built instead

`design_handoff/toolchain/pdf_to_docx_exact.py`. It reconstructs nothing. It takes the
printed page as given:

* **The page stays the page.** Every rule, bar, panel, logo and signature the PDF draws is
  kept untouched — vector art and images are never redacted — and becomes the Word page's
  background at 300 dpi, behind the text.
* **The text becomes text, where it already is.** Each text span is lifted out of that
  background and re-emitted as a real Word run inside a positioned frame (`w:framePr`,
  anchored to the page, in twips) at the coordinates the PDF gives it. Nothing re-flows,
  because nothing flows: there is no paragraph stream to break.
* **The faces travel with the file.** `embed_fonts.py` embeds Montserrat, Roboto Mono and
  Orbitron — eighteen faces per certificate — so a run is as wide in Word on a reviewer's
  laptop as it is in the PDF.

The result opens in Word as an ordinary document: selectable, searchable, editable text on
a page that is the certificate's own.

### The four things that had to be got right

1. **`w:xAlign` beats `w:x`.** A frame carrying both is aligned, not positioned, so the
   first build pinned every run to the left edge of the page. The alignment attributes are
   gone.
2. **Word measures type in half-points and nothing finer.** The certificate sets its table
   at 15.975 pt; python-docx truncated that to 15.5, and every run came out three per cent
   narrow — the right-hand column ended 9 pt short of its own edge. Sizes are rounded to
   the nearest half-point and the widths are then corrected to *that* size.
3. **Tracking is spread over the gaps, not the characters.** `w:spacing` after the last
   character moves nothing visible, so dividing by the character count left the letter-
   spaced title 1.6 pt short. Each run is split in two, the first *r* characters carrying
   one twip more than the rest, so the correction lands to within a twentieth of a point.
4. **PyMuPDF invents spaces.** Left to itself it returns the letter-spaced subtitle as
   `С Е Р Т И Ф И К А Т З А К В А Л И Т Е Т` — forty-one characters where the page draws
   twenty-one. That is the wrong text to copy out of a controlled document, and it is also
   too wide, so the width correction squeezed it until the real word spaces closed up.
   `TEXT_INHIBIT_SPACES` returns what the page actually holds.

### Where the frame sits

Word seats a line inside a box it sizes from the face's own ascent, not from the baseline
the PDF gives, so the frame origin needs an offset. It is not guessed. `--calibrate`
converts the output back to PDF, matches the runs by their text and measures the
displacement; the offset turned out to be proportional to the type size and different for
each family, and the constants in the file are what that measurement returned.

    FRAME_DX   = -0.100
    FRAME_DY_A =  0.014
    FRAME_DY_B = {Montserrat 0.3058, Orbitron 0.2083, Roboto Mono 0.2439}  × size

## Verification

Not an opinion — every run is converted back to PDF and compared with the approved page,
by `--verify`. A point is a third of a millimetre.

| | left edge | top edge | right edge |
| --- | ---: | ---: | ---: |
| `CoQ-PP_26-013` · 199 runs matched | median 0.011 · **max 0.025 pt** | median 0.012 · **max 0.047 pt** | median 0.037 · **max 0.718 pt** |
| `iCoA-PP_26-001` · 290 runs matched | median 0.012 · **max 0.025 pt** | median 0.011 · **max 0.047 pt** | median 0.031 · **max 0.663 pt** |

Every run begins within a fortieth of a point of where the certificate puts it, sits
within a twentieth of a point of its own line, and ends within three quarters of a point
— a quarter of a millimetre — in the worst case on the page.

**And the file is checked for validity before it is written.** An earlier Word export was
lost to *"unreadable content"*, which is all Word says when a document's property children
are out of the order its schema fixes. `check_order()` asserts both sequences — `w:pPr`
and `w:rPr` — on every paragraph and run of every file produced, and the conversion fails
rather than writing a document Word would refuse. It caught a real one: `w:jc` was being
written before `w:contextualSpacing`.

## What stays in the page layer

Thirty-nine spans on a certificate of quality and sixty-five on an internal certificate
are glyph-level fallbacks the browser reached for — `☒ ☐ ≤ ∑ Δ` and the superscripts,
carried by DejaVu and Liberation rather than a house face. Those are left in the page
image: they print exactly as the PDF prints them, and they are not text anybody edits.
Everything else — all of the Latin and Cyrillic content, 342 runs on a certificate of
quality and 419 on an internal certificate — is a Word run.

## Where the files are

The Word documents sit where they always have, one per certificate, beside the PDF and the
HTML they belong to:

    SIGNED_2026-09-21/CoQ/Initial/DOCX/    89
    SIGNED_2026-09-21/CoQ/Retest/DOCX/     83
    SIGNED_2026-09-21/iCoA/Initial/DOCX/   89
    SIGNED_2026-09-21/iCoA/Retest/DOCX/    83
    specs/QCSP_001_ImB/DOCX/               57

The HTML and the PDF are unchanged. Only the Word files are rebuilt, and they are rebuilt
from the PDF sitting next to them — so a Word file and its PDF are the same page by
construction, not by care.

## One box per field, for the templates

> *"is it possible that the individual text boxes follow some logical wholeness? not just
> with 3 or 5 words"* — the owner, 21.09.2026

A box per PDF span is right for a certificate and wrong for a template, for the reason
above: a span is what the renderer drew, not what the field is.

**Merging by position was measured and rejected.** Taking same-baseline neighbours cut the
certificate of quality's 378 spans to 256 boxes and joined two separate tick pills into
`HYBRIDINDICA`. Tightening it — never across a symbol, only within one of PyMuPDF's own
lines — stopped that and left the median box at two words, which is the complaint again.
PyMuPDF's `blocks` are no help either: one of them spans 21 unrelated rows of the
heavy-metals table.

**The HTML knows.** The field map is read off the laid-out document in the pass that
prints it — `render(..., probe=)` in `print_coq_pdfs.py` — and the PDF still places every
run. Three faults had to be found on the way:

* **The probe saw 4 of 49 placeholders.** It looked at a leaf's direct children only, so
  every nested `<span class="ph">` was invisible to it.
* **46 of the 51 placeholder spans are `Type3`.** The blue italic is a weight Montserrat
  has no true italic for, so the renderer synthesises the slant and embeds it as a font
  with no family name. `face_of` rejects them, so the very fields the owner types into
  were being left in the page image. The DOM's computed face rescues them.
* **A frame the width of its DOM element wraps what the page prints flat.** A design lets
  text overflow its box; `02` broke into `0` and `2`, and every cell of the RESULT column
  wrapped into the row beneath. A frame is now never narrower than its own text — except
  where the page itself wraps the cell, since widening those pushed `[PRODUCTION BATCH]`
  across the manufacture date beside it.

Two smaller ones: a gap between runs was being bridged by letter-spacing the preceding
word, which distorted it and still fell 6 pt short — it is a measured space now; and a
correction of more than a quarter of the type size per character is refused rather than
applied, which is what made `02` illegible.

| | boxes | placeholders whole | left edge | top edge |
| --- | ---: | ---: | ---: | ---: |
| CoQ | 291 | **48/48** | median 0.015 pt | median 0.016 pt |
| ImB specification | 279 | **13/13** | median 0.010 pt | median 0.013 pt |
| iCoA | 445 | 45/60 | median 0.013 pt | median 0.013 pt |

The fifteen are placeholders the page itself truncates to `[OBS...`, because the
descriptors are longer than the observation chips that hold them. The Word file carries
what the page prints.

**The 344 certificates are untouched.** Field grouping runs only when a field map is
given; without one the converter behaves exactly as it did, and re-measuring
`CoQ-PP_26-013` after the change returned the same 0.025 / 0.047 / 0.718 pt.

## The shadow twin

Building the templates turned up something that is not about templates. Every tick-chip
and section number on a certificate of quality exists **twice** in the PDF's text layer,
0.75 pt apart. Selecting `Hybrid` gives it doubled; editing one Word box leaves the other
behind; searching the PDF finds two hits.

The HTML says `Hybrid` once. The cause is `text-shadow: 0 1px 1px` on `.chip-sel`,
`.chip-un`, `.sec-label`, `.sec-no`, `.mk`, `.pb-grade` and `.stmt .badge` — design system
§6.4 — because **Chromium draws a text shadow in a PDF by printing the glyphs a second
time.**

| | spans | drawn twice |
| --- | ---: | ---: |
| CoQ certificate | 383 | **19** |
| Specification sheet | 345 | **22** |
| internal certificate | 484 | **0** — it sets no text shadow |

**The converter no longer makes a box out of a shadow.** `shadow_twins()` identifies the
pair exactly rather than by tolerance — same text, same face, the same left edge to a
tenth of a point, three quarters of a point lower, and a different colour — and the lower
one is left in the page image, never redacted and never boxed. The emboss still prints;
it is simply not also a second text box. The internal certificate is untouched, which is
the check that the rule is precise and not a heuristic.

Dropping a shadow may never drop a word, so the conversion asserts it: every twin removed
must leave its own text still on the page in the span it was shadowing, or the run fails.
On the three fleets, **19, 0 and 22 twins removed and no text lost**.

    CoQ template     291 boxes -> 276      specification  279 -> 255
    internal cert    445 boxes -> 445      (nothing to remove)

**A defect of the desk's own print layer, found on the way.** `printOpaqueLayer` in
`build_v40.js` re-emits every rule whose background is an alpha gradient with each
`rgba(C,a)` replaced by that colour over white. It was doing that to *every* rgba in the
declaration, including `text-shadow` — which is not a background fill. `.chip-sel`'s
shadow, authored as `rgba(9,22,38,.45)`, a soft dark shade, printed as `rgb(144,150,157)`,
an opaque grey haze on a dark blue chip. Shadows, text colour and border colour now carry
through as the design wrote them; only what paints the page behind them is converted.

**Still open, and the owner's to decide.** None of this removes the doubling from the
*issued PDFs* — any text shadow doubles the glyphs, and only dropping `text-shadow` in
print would stop it. That would take the 1 px emboss off the tick-chips and section bands
of 172 certificates of quality and 57 specification sheets and mean reprinting them, so it
is a change to an approved look rather than a repair. The owner has asked for it to be
planned; it is not done.

The 344 certificates and 57 specification sheets already committed keep their doubled
boxes until they are re-converted, which needs more disk than this session holds.
