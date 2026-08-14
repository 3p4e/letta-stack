# Final_Docs — PDF renders (A4)

PDF conversions of every `.html` document in the `SP-COA-COQ_FINAL_DOCS.zip`
archive's `Final_Docs/` tree (Drive file 1SXHNe_7QoYflp55qHFDPEVreD7cSgFEy),
mirroring its folder structure. Rendered 14.08.2026 with Chromium (A4,
zero margin, Google fonts embedded at render time so Orbitron/Montserrat/
Roboto Mono survive offline), then ghostscript-compressed; visual parity
with the browser render verified on samples (mean pixel diff <0.5%).

- 351 PDFs. The ImB/ImG specification family (BASE_SPCs, NEWs, RENs,
  T1/T2/T3, T1_rename, ImG_SPEC) renders exactly one A4 page per file,
  as designed. Seven screen-format root documents (iCoA series, CoQ pair)
  flow to two A4 pages; the QC activity log fits one.
- Source HTML is NOT in this repo — the Drive archive remains the source
  of truth (see its HANDOFF.md files). Regenerate by re-running the
  conversion against a fresh copy of the archive.

Download everything at once: use GitHub's "Code → Download ZIP" on this
branch, or fetch files individually from this folder.
