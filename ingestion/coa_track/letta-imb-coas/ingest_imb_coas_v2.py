#!/usr/bin/env python3
"""
ImB_QC_COAs — Complete OCR + RAG ingestion pipeline v2 (run on KVM4).

RUN THIS ON KVM4. It has the OpenAI key + direct Letta access. The cloud
Claude session cannot reach the Letta embedding endpoint or render PDFs at
scale, so OCR-at-volume belongs here.

Two stages:
  STAGE A — Upload pre-extracted native-text CoAs (staged_coas/*.txt) with
            retry + dedup by filename. These are the Farmahem (HPLC
            cannabinoids + Loss on Drying) and UKIM Faculty of Pharmacy
            (DAB cannabinoids + LoD) reports, already cleanly extracted by
            the cloud session.

  STAGE B — OCR the scanned multi-CoA bundles with GPT-4o Vision:
            PyMuPDF render @200 DPI -> GPT-4o vision OCR -> structure ->
            upload. PDFs that already carry a text layer are used directly.

Prereqs:
    pip install PyMuPDF openai
    export OPENAI_API_KEY=sk-...
    # Letta at http://letta:8283 (letta_letta_stack network)

BEFORE RUNNING — confirm the embedding endpoint is alive (all Letta file
processing returns status "Error" when it is down — this is exactly what
blocked the 2026-06-01 cloud-side ingestion):
    curl https://api.openai.com/v1/embeddings \
      -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" \
      -d '{"model":"text-embedding-3-small","input":"ping"}'
    # 200 -> proceed.  401/429 -> fix key/quota/billing first.
"""
import base64
import hashlib
import json
import os
import time
import urllib.request

LETTA_BASE = os.getenv("LETTA_BASE", "http://letta:8283")
LETTA_KEY = os.getenv("LETTA_MASTER_KEY", "${LETTA_SERVER_PASS}")
SOURCE_ID = "source-271bc3be-10d1-4541-8a5b-be3f6fab7c97"  # ImB_QC_COAs
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
HERE = os.path.dirname(os.path.abspath(__file__))
STAGED_DIR = os.path.join(HERE, "staged_coas")
OCR_OUT_DIR = os.path.join(HERE, "ocr_out")
DRIVE_SYNC = "/config/gdrive-sync/1. PP/DATA_B/QC_eCoA/ImB_QC_COAs"
HEADERS = {"Authorization": f"Bearer {LETTA_KEY}"}


def letta_list_files():
    req = urllib.request.Request(
        f"{LETTA_BASE}/v1/sources/{SOURCE_ID}/files?limit=500", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def letta_existing_names():
    return {f["file_name"] for f in letta_list_files()}


def letta_error_files():
    """Return list of {id, file_name} for any files stuck in Error state."""
    return [{"id": f["id"], "file_name": f["file_name"]}
            for f in letta_list_files() if f.get("processing_status") == "Error"]


def letta_delete(file_id):
    req = urllib.request.Request(
        f"{LETTA_BASE}/v1/sources/{SOURCE_ID}/{file_id}",
        method="DELETE", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status == 204 or r.status == 200


def purge_errored():
    """Delete every Error-state file so they can be re-ingested cleanly."""
    errs = letta_error_files()
    if not errs:
        print("  no Error-state files to purge")
        return
    print(f"  purging {len(errs)} Error-state files...")
    for f in errs:
        try:
            letta_delete(f["id"])
            print(f"    deleted {f['file_name']}")
        except Exception as e:
            print(f"    delete failed {f['file_name']}: {e}")


def letta_upload(filename, text, max_retries=4):
    boundary = "----imbcoa" + hashlib.md5(filename.encode()).hexdigest()[:12]
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: text/plain\r\n\r\n"
    ).encode() + text.encode("utf-8") + f"\r\n--{boundary}--\r\n".encode()
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                f"{LETTA_BASE}/v1/sources/{SOURCE_ID}/upload",
                data=body, method="POST",
                headers={**HEADERS,
                         "Content-Type": f"multipart/form-data; boundary={boundary}"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())
        except Exception as e:
            wait = 2 ** (attempt + 1)
            print(f"    upload retry {attempt + 1} in {wait}s ({e})")
            time.sleep(wait)
    raise RuntimeError(f"upload failed: {filename}")


def wait_until_processed(poll=5, timeout=900):
    start = time.time()
    while time.time() - start < timeout:
        files = letta_list_files()
        pend = [f for f in files if f["processing_status"] in
                ("Embedding", "Parsing", "Pending", "Running")]
        err = [f for f in files if f["processing_status"] == "Error"]
        if not pend:
            print(f"  settled: {len(files)} files, {len(err)} Error")
            if err:
                print("  ERRORED -> embedding endpoint likely down. Names:",
                      [f["file_name"] for f in err][:10])
            return len(err) == 0
        print(f"  {len(pend)} still processing...")
        time.sleep(poll)
    print("  timeout")
    return False


def stage_a():
    print("=== STAGE A: native-text CoAs ===")
    purge_errored()
    existing = letta_existing_names()
    files = sorted(f for f in os.listdir(STAGED_DIR) if f.endswith(".txt"))
    up = skip = 0
    for i, name in enumerate(files):
        if name in existing:
            skip += 1
            continue
        with open(os.path.join(STAGED_DIR, name)) as f:
            text = f.read()
        r = letta_upload(name, text)
        up += 1
        print(f"  [{i + 1}/{len(files)}] {name} -> {r.get('id', '?')}")
        time.sleep(2)
    print(f"STAGE A: {up} uploaded, {skip} skipped")
    wait_until_processed()


OCR_PROMPT = (
    "You are reading a scanned pharmaceutical Certificate of Analysis (CoA) for "
    "medical cannabis flower, bilingual Macedonian/English. Transcribe ALL text "
    "verbatim, then append a JSON block with: doc_code, lab_name, batch_number, "
    "issue_date, product_strain, and every parameter {name,result,unit,spec,method} "
    "covering pesticides, heavy metals (Cd/Pb/As/Hg), mycotoxins/aflatoxins, "
    "microbiology (TAMC/TYMC/E.coli/Salmonella/bile-tolerant), cannabinoids, loss "
    "on drying, foreign matter. Never invent values; use null when absent."
)


# OCR fallback chain — see agent_model_policy.OCR_CHAIN
# Order: Moonshot kimi-k2.6 (primary), Moonshot moonshot-v1-128k-vision-preview,
# OpenAI gpt-4o (final fallback).
OCR_PROVIDERS = [
    {"name": "moonshot-kimi",        "base_url": "https://api.moonshot.ai/v1",
     "model": "kimi-k2.6",                            "env": "MOONSHOT_API_KEY"},
    {"name": "moonshot-v1-vision",   "base_url": "https://api.moonshot.ai/v1",
     "model": "moonshot-v1-128k-vision-preview",      "env": "MOONSHOT_API_KEY"},
    {"name": "openai-gpt-4o",        "base_url": "https://api.openai.com/v1",
     "model": "gpt-4o",                               "env": "OPENAI_API_KEY"},
]


def _vision_ocr_call(provider: dict, png_bytes: bytes) -> str:
    """Single attempt against one provider. Raises on failure."""
    import openai
    key = os.environ.get(provider["env"])
    if not key:
        raise RuntimeError(f"{provider['env']} not set")
    client = openai.OpenAI(api_key=key, base_url=provider["base_url"])
    b64 = base64.b64encode(png_bytes).decode()
    resp = client.chat.completions.create(
        model=provider["model"], max_tokens=4096, temperature=0,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": OCR_PROMPT},
            {"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{b64}", "detail": "high"}}]}])
    out = resp.choices[0].message.content or ""
    if len(out.strip()) < 50:
        raise RuntimeError(f"{provider['name']} returned <50 chars — likely refused/unsupported")
    return out


def gpt4o_ocr_page(png_bytes):
    """Route through OCR_PROVIDERS in order, returning the first successful body.
    Name kept for backwards compatibility with callers."""
    last_err = None
    for provider in OCR_PROVIDERS:
        try:
            text = _vision_ocr_call(provider, png_bytes)
            return f"[OCR via {provider['name']}/{provider['model']}]\n{text}"
        except Exception as e:
            print(f"    OCR provider {provider['name']} failed: {e}")
            last_err = e
            continue
    raise RuntimeError(f"all OCR providers failed; last error: {last_err}")


def stage_b():
    import fitz
    print("=== STAGE B: GPT-4o Vision OCR ===")
    os.makedirs(OCR_OUT_DIR, exist_ok=True)
    existing = letta_existing_names()
    pdfs = [f for f in sorted(os.listdir(DRIVE_SYNC)) if f.lower().endswith(".pdf")]
    for pi, pdf_name in enumerate(pdfs):
        out_name = ("OCR_" + os.path.splitext(pdf_name)[0] + ".txt").replace(" ", "_")
        if out_name in existing or os.path.exists(os.path.join(OCR_OUT_DIR, out_name)):
            print(f"  [{pi + 1}/{len(pdfs)}] skip: {pdf_name}")
            continue
        try:
            doc = fitz.open(os.path.join(DRIVE_SYNC, pdf_name))
        except Exception as e:
            print(f"  open fail {pdf_name}: {e}")
            continue
        embedded = "".join(p.get_text() for p in doc)
        if len(embedded.strip()) > 200:
            text = embedded
            print(f"  [{pi + 1}/{len(pdfs)}] {pdf_name}: embedded ({len(text)}c)")
        else:
            parts = []
            for n in range(doc.page_count):
                parts.append(gpt4o_ocr_page(doc[n].get_pixmap(dpi=200).tobytes("png")))
                time.sleep(1)
            text = (f"[SCANNED BUNDLE {pdf_name}, {doc.page_count}p, GPT-4o OCR]\n\n"
                    + "\n\n--- PAGE BREAK ---\n\n".join(parts))
            print(f"  [{pi + 1}/{len(pdfs)}] {pdf_name}: OCR {doc.page_count}p")
        doc.close()
        with open(os.path.join(OCR_OUT_DIR, out_name), "w") as f:
            f.write(text)
        letta_upload(out_name, text)
        time.sleep(2)
    print("STAGE B done")
    wait_until_processed(timeout=1800)


if __name__ == "__main__":
    import sys
    stage = sys.argv[1] if len(sys.argv) > 1 else "all"
    if stage in ("a", "all"):
        stage_a()
    if stage in ("b", "all"):
        stage_b()
