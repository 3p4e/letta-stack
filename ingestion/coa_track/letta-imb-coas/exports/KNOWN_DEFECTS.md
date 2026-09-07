# Known defects in these exports

These files are **derived exports** from an earlier parse. Where one disagrees with
a certificate's own page, the page wins (ingestion trap 12). Defects found since the
exports were written are listed here rather than edited into them — an export is a
historical record of what the parse produced.

## `master_coa_table.tsv` — one transposed pair, `197-7-К/26`

The export pairs the values the wrong way round for this certificate only:

| parameter | export says | certificate prints |
|---|---|---|
| Total CBD | `<LOQ %w/w` | **`0.22 %w/w` (U 0.01, k=2)** |
| Total CBN | `0.22 %w/w (U 0.01, k=2)` | **`< LOQ`** |

Established 31.08.2026 by two direct readings — the page read recorded in
`review/farmahem_page_reads_2026-08-31.json` (key `1977K26`) and the certificate's
own results table in `ingestion/ragflow/cache/all_cert_texts_2026-08-30.json`
(`P060352, 197-7-K-26, 07.08.2026, FHM.pdf`) — and confirmed in
`review/FARMAHEM_PAGE_VERIFICATION_2026-08-31.md`.

Measured scope: the export was swept against all 31 Farmahem cannabinoid page reads —
**93 values compared, this pair the only disagreement**. It is one transposed record,
not a systematic ordering difference (the export lists CBN before CBD for the whole
197 series, and pairs label to value correctly everywhere else).

**Consequence.** The release register carried the transposition, the page campaign
corrected it (chain step 7), chain step 16 reinstated it on this export's authority,
and chain step 18's predecessor — step 17, `restore_farmahem_pair.py` — restored the
certificate's values. **Anything re-derived from this export reintroduces the defect.**
Re-derive from the certificates or from the page reads, or apply this correction after
any regeneration.
