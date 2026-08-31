# eCoA extraction runner

Two independent vision reads of every certificate page, rendered at 300 DPI. Fields the
two reads disagree on are held at `null` and flagged for review — never resolved by
picking a winner. Numbers are never taken from a PDF text layer.

## Why two reads

Measured on the six page-verified certificates from the register audit:

| Certificate | Page | gpt-5 | gemini-3.6-flash | Recorded |
|---|---|---|---|---|
| 1032/1851/25 | 4,9×10⁴ | 4,9×10⁴ | 4,9×10⁴ | 49000 |
| 628/1129/25  | 1,2×10⁴ | 1,2×10⁴ | 1,2×10⁴ | 12000 |
| 320/0587/25  | 4,2×10⁴ | 4,2×10⁴ | 4,2×10⁴ | 42000 |
| 904/1589/25  | 3,3×10⁴ | 3,3×10⁴ | 3,3×10⁴ | 33000 |
| 946/1684/25  | 3,6×10⁴ | 3,6×10⁴ | **3,6×10¹** | held for review |
| 163/0271/25  | 1×10⁴   | 1×10⁴   | 1×10⁴   | 10000 |

The models fail independently and in both directions: gemini misread an exponent on
946/1684/25, gpt-5 misread a *limit* exponent on 320/0587/25 (10⁶ for 10⁵), and gpt-5
returned nothing at all for the NGP certificate that gemini read cleanly. A single-model
runner would have written a wrong value in each of those cases.

The same certificates through RAGFlow's own pipeline read 1032/1851/25 and 628/1129/25
as 10³ — the tenfold understatement the register audit found by hand. That was a
rendering problem, not a model-capability one: at 300 DPI both vendors read them correctly.

## Files

| File | Purpose |
|---|---|
| `extract_ecoa_records.py` | render → two reads → reconcile → typed records |
| `build_table.py` | records → SQLite + the six standing queries |
| `common/pp_batch.py` | canonical batch form, Head of QC grammar §2.1 (23.08.2026) |
| `common/pheur.py` | governing limits: Ph. Eur. 5.1.8 cat. C + specification §02 |
| `quality_guard.py` | post-ingest checks — length, alphabet, mojibake |
| `apply_full.py` / `drop_meta.py` | RAGFlow pipeline-agent configuration |
| `pilot2.py` | pipeline ingest loop with chunk clearing |
| `pilot_records_12docs.json` | 13 certificates, 119 results, 107 confirmed |

## Operating notes

- **`DELETE /chunks` with an empty body returns `code: 0` and deletes nothing.** Send
  `chunk_ids` and verify the count is zero afterwards.
- **RAGFlow reports `run: DONE` on a hallucinated parse.** One NGP certificate produced
  87 characters of Sakha-alphabet Cyrillic and was marked successful. Run `quality_guard`.
- **Gemini free tier gives out after ~20 vision calls per key.** Three keys rotate
  automatically; that is still only ~60 documents/day against 292.
- **Gemini 3 counts reasoning tokens against `maxOutputTokens`** — 8548 thinking tokens
  on a 2-page certificate. Budget is 32768; do not lower it.

## Open rulings

- `pheur.MAX_MULTIPLIER` is unset. The in-house template prints 5× (10⁴ → "max 50 000");
  the general interpretation rule is commonly cited as 2×. At 5× the four TYMC results
  are within specification; at 2×, three are not. Until it is ruled, only
  "exceeds the stated criterion" is reported and no disposition is implied.
- Read B's model for the corpus run — Gemini's quota will not carry 292 documents.
