# What the Head of QC has had to correct — and what now stops it happening again

Kept because the Head of QC asked, 27.09.2026: *"commit everything I corrected you for a hundredth
time … You never do this again to me."* Every entry quotes the Head of QC. The standing rules they
produced are in `CLAUDE.md`, which is read at the start of every session; this file is the record
of how each was learned. The same record is in Open Brain (Supabase project `open_brain`, table
`thoughts`, `metadata.source = claude-code-desk`).

## Incident, 27.09.2026 — "MK GMP Certified Facility" in the certificate footer

> *"hell no. from where did MK GMP Certified Facility came from"* — Head of QC, 27.09.2026

**What was printed.** "MK GMP Certified Facility" in the bottom-right footer of the certificates
of quality, and as a line under the address in the internal certificates' footer.

**Who put it there, when, how.** The desk, on **21.09.2026 at 10:16 UTC**. The footer slot of the
CoQ base page the Head of QC supplied (`design_handoff/base/CoQ-PP_26-013…html`) was empty,
`<div class="foot-right"></div>`. The desk was working through the "Purely Plant Design System
(Navy & Gold)" package — the Variation F design-system README from the Claude Design work — whose
"locked business rules" say *"Header/footer say MK GMP Certified Facility — never 'EU GMP' on
flower documents"*. The desk wrote the task as *"Rule 1 is a live gap: neither fleet prints 'MK
GMP Certified Facility' anywhere. Add it to both footers"*, reported *"Now the MK GMP wording — a
locked rule with a real gap"*, wrote the line into the CoQ base page and the iCoA generator
(`icoa_handoff/v3/icoa3_gen.js`) without asking, and rebuilt 172 CoQs and 172 iCoAs.

**What went wrong.**
1. **The wrong authority.** A design system decides colour, type and layout. A GMP statement is a
   regulatory claim; only the Head of QC can make it. A style guide's rule was treated as a ruling.
2. **Against a newer ruling.** On 17.09.2026 the Head of QC had "MK GMP Certified" struck from the
   laboratory line. Four days later the desk put the same claim in the footer without checking it
   against that ruling — the latest ruling governs, and the desk invoked an older, lesser source.
3. **An empty slot was filled.** The template left it empty; the desk called that a gap.
4. **Nothing checked it.** No test tied printed text to a ruling or a cited document.

**What was done (commit `d2e321e`).**
- The line is gone from every certificate not yet issued: the 31 Tranche 3 initials, the 29
  Tranche 3 retests and six lots outside any tranche — that one line and nothing else, 66 pages.
- Tranches 1 and 2 are issued and with the customer (Head of QC, 26.09.2026) and were not touched,
  nor were the six lots built as Tranche 2 before the 18.09 regrouping. Their pages keep the line
  as sent; whether anything is done about the copies already issued is the Head of QC's decision.
- The blank CoQ and iCoA templates no longer carry it; their Word and PDF copies are rebuilt.
- `tracker/check_certificate_claims.py` fails the build and CI on a certification, accreditation or
  GMP claim about Purely Plant in any page a build can still change.
- `CLAUDE.md` §6 records the rule. The Cowork handoff note, which listed the line as an
  "agreement", is corrected.
- The Tranche 3 pages were read again for any other claim: none. What remains is method references
  (Ph. Eur.) and the external laboratories' own ISO/IEC 17025 lines, copied from their certificates.

**Still carrying it, and why.** The design-system README itself (Claude Design package, Variation F
`readme.md` / `VariationF_DESIGN_SYSTEM.md`, and the `business_rules` memory of the Letta agent
`VariationF`) still lists the rule. The desk has not edited it: it is the Head of QC's document.
Until it is struck there, any tool that reads it may bring the line back — the check above is what
catches it here.
