# Blank templates — one per document type

Three HTML files, each the document with every value replaced by a **blue bracketed
descriptor** and every piece of fixed wording left alone.

    CoQ_BLANK_TEMPLATE.html                 the certificate of quality       50 placeholders
    iCoA_BLANK_TEMPLATE.html                the internal certificate         61 placeholders
    ImB_Specification_BLANK_TEMPLATE.html   the product specification        12 placeholders

Open any of them in a browser. Anything in blue italics inside square brackets is a value
to replace; everything in black is the document's own wording and stays.

## Which fields are placeholders was not decided by hand

Every document of a fleet is parsed and each text node addressed by its position in the
tree. A node whose text is **the same on all 172** is fixed wording and is left exactly as
it is; a node whose text **differs between any two** is a value somebody fills, and only
those become descriptors.

    certificate of quality        172 compared — 254 nodes fixed, 50 variable
    internal certificate          172 compared — 325 nodes fixed, 61 variable
    product specification          57 compared — the owner's own blank, 12 named by hand

So the templates cannot quietly blank a caption, and cannot leave a batch number behind.

The descriptor takes its name from the caption the design already prints beside the field
— *Product Code*, *Packaging Date*, *Parameters Covered* — so the template reads in the
document's own language rather than in the stylesheet's. A result cell is named by the
determination it carries: `[RESULT #4]`, `[RESULT #9.3]`.

## The blue

One `<style id="__placeholders">` block **appended** to each document. Delete that block
and the file is the design exactly as delivered — the same rule the certificates follow: a
settled visual layer is added to, never edited.

## What is not blanked

The tick pills keep their selected state, because in these documents a tick is carried by
a class rather than by text and there is nothing in the text to replace. Change the ticked
option in the markup when filling.

## Rebuilding

    python3 deliverables/qc_gap_analysis/build_blank_templates.py

## As PDF

`PDF/` holds each template printed to one A4 page, fonts embedded — the form to convert to
Word from, or to hand to anyone who only needs to see what a filled document will look
like. The same printer the certificates use prints them, so a template prints as the
document it is a template for.

    PDF/CoQ_BLANK_TEMPLATE.pdf                  1 page    49 placeholders
    PDF/iCoA_BLANK_TEMPLATE.pdf                 1 page    60 placeholders
    PDF/ImB_Specification_BLANK_TEMPLATE.pdf    1 page    12 placeholders

**The HTML is self-contained.** The internal certificate carried its three stylesheets and
its logo by relative path, which resolve beside the fleet and nowhere else; moved into this
folder the page lost every rule it had and printed over three A4 pages with a broken image
where the mark belongs. Stylesheets and images are now folded into the file, so a template
is one file that opens anywhere.

## As Word

`DOCX/` holds each template as a Word document, built the way the certificates are —
HTML to PDF, PDF to Word — so the page is the approved page and not a re-drawing of it.
`build_template_docx.py` makes them.

**One text box per whole field.** A certificate is a record nobody edits, so the converter
gives it one box per PDF text span, and a span is whatever the renderer happened to draw.
A template is a document somebody types into, and there `[MANUFACTURE DATE]` arriving as
`[MANUFACTUR` and `E DATE]` is useless. The owner asked for boxes with "some logical
wholeness, not just with 3 or 5 words", and the boundaries now come from the template's
own HTML — every `<span class="ph">` and every leaf element is one box — while the PDF
still says where the ink goes. Merging by position was tried first and is not safe: it
joined two separate tick pills into `HYBRIDINDICA`.

| | boxes | placeholders in one whole box |
| --- | ---: | ---: |
| `CoQ_BLANK_TEMPLATE.docx` | 276 | **48 of 48** |
| `ImB_Specification_BLANK_TEMPLATE.docx` | 255 | **13 of 13** |
| `iCoA_BLANK_TEMPLATE.docx` | 445 | 45 of 60 |

**Typing into one.** A box is as wide as its field, and never narrower than the text the
page already prints, so a longer value wraps inside the field instead of running across
the page. Where the page itself wraps a cell, the box keeps that width and wraps there
too.

**One thing for the owner on the internal certificate.** Fifteen of its placeholders are
too long for the observation chips that hold them, so the page truncates them —
`[OBSERVATION 12]` prints as `[OBS...`. The Word file carries what the page prints,
because a converter may not invent text. Shortening those descriptors in
`build_blank_templates.py` would fix it at source.

**No label is boxed twice.** The design gives its tick-chips and section bands a CSS text
shadow, and Chromium draws a text shadow in a PDF by printing the glyphs a second time —
so `Hybrid` used to arrive as two Word boxes on top of each other. The shadow copy is now
left in the page image where it belongs: the emboss still prints, and the text layer
carries each label once.
