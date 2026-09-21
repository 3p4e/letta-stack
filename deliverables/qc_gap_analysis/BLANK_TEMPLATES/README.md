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
