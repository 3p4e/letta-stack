# ImB_QC_COAs — Ingestion & Ph.Eur. 3028 Coverage Status

_Last updated: 2026-06-01 19:25 UTC by cloud Claude session._

## Source of truth
- **Drive folder:** `1. PP/DATA_B/QC_eCoA/ImB_QC_COAs` (Drive ID `16oMK_j0FUusjveV61B5rxWi6Sl5kQsn5`) — **125 PDFs**
- **Letta source:** `source-271bc3be-10d1-4541-8a5b-be3f6fab7c97` (ImB_QC_COAs)
- **Agent attached:** `imb_qc_coa_agent` (`agent-edf27c5c-1f88-495b-b6fb-506105bd717c`)

## BLOCKER — Letta embedding endpoint still down (confirmed 2026-06-01 19:20 UTC)
Re-tested today with two fresh uploads (a 25-byte ASCII ping and a 617-byte
Farmahem CoA). Both moved through `Embedding -> Error` within ~30s of upload.
21 UKIM_PPK files uploaded earlier on 06-01 are likewise stuck in `Error`.

**Diagnosis:** Letta's OpenAI `text-embedding-3-small` endpoint is failing —
expired/over-quota API key, suspended billing, or upstream outage. Letta
itself accepts the file and writes the row; it's the embedding call that
flips the row to Error.

Fix on KVM4 (no other path — cloud cannot reach the embedding endpoint):
```bash
docker exec letta env | grep -i openai
curl https://api.openai.com/v1/embeddings \
  -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"text-embedding-3-small","input":"ping"}'   # must be 200
docker compose -f /opt/letta/docker-compose.yml restart letta
```

After the key is good, run on KVM4:
```bash
cd /path/to/CoA_TRACK/scripts/letta-imb-coas
python3 ingest_imb_coas_v2.py a   # purges 21+ Error files, uploads 47 staged
python3 ingest_imb_coas_v2.py b   # GPT-4o Vision OCR for CamScanner thumbnails
```
The updated `stage_a()` purges every Error-state file before uploading, so the
21 UKIM_PPK rows currently in Error get a clean re-ingest.

## Letta source state right now (68 -> 66 after cleanup of two test uploads)
| Bucket | Count | Status |
|--------|-------|--------|
| `P05xxx2.txt` + `P06xxx2_CoA.txt` (Drive-OCR bundles) | 21 | Completed |
| CamScanner thumbnails (BG/BSS/CJ/HPA/GG/OPM 1024, GP0824_02_bulk) | 7 | Completed |
| `P060012_CoA..P060092_CoA` + `List_of_COAs` | 10 | Completed |
| `J31122501_*` + `OPM122501_eCoA` (full-panel batches) | 3 | Completed |
| `P050162/182/192/202` (stability bundle CoAs) | 4 | Completed |
| `UKIM_PPK260xx` | 21 | **Error** (awaiting endpoint fix → re-upload) |
| **Total Completed** | **45** | |
| **Total Errored** | **21** | |

## Staged & ready (`staged_coas/`, 56 files)
- **17 Farmahem** native-text CoAs (cannabinoids HPLC/DAD + Loss on Drying):
  J31102501, J31112501, J31122501, SJ102501, SJ112501, KC102501, GRC102501/2,
  OPM122501 (reports `051-1..6` and `100-1..4` series)
- **21 UKIM ППК** native-text CoAs (DAB cannabinoids + LoD incl. stability):
  PM112501, OPM112501, GG112501, GG012601, JD112501, JD012601, FB112501,
  FB012601, CC112501, SCR112501, plus Grape Pie stability at months 3/6/9
  for batches P050022 / P050072 / P050202 at 25°C/60% RH and 40°C/75% RH
- **18 Bundle full-panel** summaries (Ph.Eur. 3028 panel per production batch,
  each citing lab + doc-code + date per parameter — drives the CoQ Builder):
  - Strain thumbnails: BG1024, BSS1024, CJ1024
  - Batched bundles: AB092501 (P060052), BSS052501 (P050192),
    BSS10240_01 (P050122), CJ052501-1 (P050162), CJ072501 (P050252),
    CJ082501-1 (P060022), CJ082501-2 (P060032), CJ092501 (P060072),
    GP052501 (P050152), GP062501 (P050202), GP092501 (P060092),
    OPM092501 (P060042), PM092501 (P060062), SJ092501 (P060082),
    WC082501 (P060012)

Once the endpoint is fixed: `stage_a()` runs in seconds. The script's new
`purge_errored()` step will delete the 21 UKIM Error rows first, then upload
all 56 staged files cleanly.

## Still needs OCR — STAGE B
The remaining ~30 scanner-bundle PDFs (the rest of the scans, plain `P0xxxx`
files in subfolders, and `MB0824_*`, `OPM092501`, etc.) carry the
**pesticide / heavy-metal / mycotoxin / microbiology** panels. STAGE B uses
GPT-4o Vision at 200 DPI for any PDF whose embedded-text layer is empty.

## Ph.Eur. 11.5 Cannabis Flower Monograph (3028) — parameter coverage
| Ph.Eur. parameter | Method | Lab | Coverage when STAGE A re-runs |
|-------------------|--------|-----|-------------------------------|
| Identification (cannabinoids) | HPLC/DAD 2.2.29 | Farmahem / UKIM | ✅ broad |
| Assay Total THC / CBD / CBN | HPLC/DAD | Farmahem / UKIM | ✅ broad |
| Loss on drying | 2.2.32 | Farmahem / UKIM | ✅ broad |
| Foreign matter | 2.8.2 | UKIM (DAB Beobachtung) | ⚠ in raw OCR — needs CoQ assembly |
| Pesticides | 2.8.13 | IPH + State Phytosanitary | ⚠ raw OCR + Bundle summaries |
| Heavy metals Cd/Pb/As/Hg | 2.4.27 | IPH | ⚠ raw OCR + Bundle summaries |
| Mycotoxins (aflatoxins) | 2.8.18 | Farmahem / IPH | ⚠ raw OCR + Bundle summaries |
| Microbial enumeration | 2.6.12 / 5.1.8 | IPH | ⚠ raw OCR + Bundle summaries |

## CoQ assembly (after endpoint fix)
Per production batch the CoQ gathers one result per Ph.Eur. 3028 parameter,
each cited as **issuing lab + report doc-code + issue date**:
- Cannabinoids/LoD → Farmahem `051-*-K/GS-26`, `100-*-K/GS-26`, or UKIM `ППК260xx`
- Pesticides → State Phytosanitary `DFL` report or IPH report
- Heavy metals → IPH report
- Mycotoxins → Farmahem `*-M/25` or IPH report
- Microbiology → IPH Microbiology `xxxx/xxxx/25`
- Foreign matter → UKIM `ППК260xx` (DAB "Beobachtung" line)

The Bundle_*.txt files in `staged_coas/` already carry a structured header
that names lab + doc-code + date for each parameter — ready for a CoQ
Builder agent to extract.

## Run order (KVM4)
```bash
cd scripts/letta-imb-coas
python3 ingest_imb_coas_v2.py a    # purge Errors + upload 47 staged (~2 min)
python3 ingest_imb_coas_v2.py b    # GPT-4o Vision OCR for scans (~30-60 min)
# verify: every file processing_status == Completed
```
