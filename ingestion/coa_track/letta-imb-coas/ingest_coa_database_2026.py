#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CoA_DATABASE_2026 — full ingestion driver: Drive eCoA folder -> RAGFlow.

Dataset: CoA_DATABASE_2026 (id f29f8f58a13c11f1858cf58865604f65), created and
configured this session — chunk_method naive, embedding voyage-3-large
(matching eCOA_INGEST/eCOA_INGEST_SUMMA/STABILITY_PROGRAMME), RAPTOR and
GraphRAG OFF (matching the two non-fragile datasets; eCOA_INGEST has both ON
and was flagged fragile — not repeated here), vision model
gpt-4.1@openai-vlm@OpenAI for layout_recognize.

That vision model id is verified, not assumed: gpt-4o@OpenAI@OpenAI (the
plain "OpenAI" factory registration made via /v1/llm/add_llm this session)
FAILS at parse time with "Instance OpenAI not found for model
gpt-4o@OpenAI@OpenAI" — the plain OpenAI factory's catalog only actually
lists embedding/tts/speech2text/chat, not image2text, regardless of what
/v1/llm/my_llms shows after add_llm. gpt-4.1@openai-vlm@OpenAI (the id
already live on STABILITY_PROGRAMME) was tested end-to-end this session —
real upload, parse, 3 chunks generated, embedded, indexed, and retrieved by
a real semantic query — and is the one this script uses.

The dataset's own llm_id (used only if/when a chat assistant is later built
on top of this dataset — RAPTOR is off, so nothing calls it during
ingestion) could not be set via the public /api/v1/datasets REST API; every
field name tried was rejected with "Extra inputs are not permitted". It
sits at the RAGFlow-assigned default, deepseek-v4-flash — harmless for
ingestion, and settable later through the RAGFlow UI if a chat assistant is
built on this dataset.

Pipeline per file:
  1. fetch bytes (Drive)
  2. extract text: native PDF text layer if present and non-trivial;
     otherwise full-page verbatim vision-OCR transcription, multi-provider
     fallback (OpenAI -> Moonshot Kimi -> DeepSeek is not vision-capable,
     so the fallback chain here is OpenAI providers only, matching what
     this session actually has working keys for)
  3. classify_ecoa.classify() -> full metadata dict, including the
     content-based test_type tag this was built for
  4. skip if this file's dedup_key already exists in the running index
  5. upload to RAGFlow, set meta_fields, trigger parse

A note on the OCR prompt: a narrow prompt asking the model to extract only
the sample-description field was tested this session and is NOT reliable —
against two of this run's own real pilot files it silently dropped the
field it was asked for, and once triggered an outright refusal. A full
verbatim "transcribe everything" prompt (the shape proven by the retired
ingest_imb_coas_v2.py's OCR_PROMPT) is the robust pattern: classify_ecoa's
regexes then find the sample-description line themselves inside the full
transcript, which is exactly what they are built to do and is proven
against real certificate text in classify_ecoa.py's own self-test.
"""
import base64
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import classify_ecoa as ce  # noqa: E402

RAGFLOW_SERVER = os.environ["RAGFLOW_API_SERVER"].rstrip("/")
RAGFLOW_KEY = os.environ["RAGFLOW_API_KEY"]
DATASET_ID = "f29f8f58a13c11f1858cf58865604f65"  # CoA_DATABASE_2026

INDEX_PATH = os.path.join(HERE, "coa_database_2026_index.json")

FULL_TEXT_OCR_PROMPT = (
    "You are transcribing a scanned pharmaceutical Certificate of Analysis "
    "(CoA) for medical cannabis flower, bilingual Macedonian/English, for a "
    "routine QC records system. Transcribe ALL text verbatim, in its "
    "original script exactly as printed (Cyrillic stays Cyrillic — do not "
    "transliterate to Latin letters). Include every field, table row, and "
    "footer exactly as it appears. Do not summarize, do not omit anything, "
    "do not add commentary."
)

# OpenAI-only vision fallback chain — this session confirmed DeepSeek's
# registered model here is chat-only (deepseek-chat), not vision-capable,
# and the Moonshot/Kimi keys tested this session were validated for chat
# completions, not confirmed for vision; kept out of this chain rather than
# assumed in. Extend once a vision-capable fallback key is confirmed.
OCR_PROVIDERS = [
    {"name": "openai-gpt4o", "base_url": "https://api.openai.com/v1",
     "model": "gpt-4o", "env": "OPENAI_API_KEY"},
]


def ragflow_api(path, method="GET", body=None, timeout=180):
    cmd = ["curl", "-sS", "--max-time", str(timeout), "-X", method,
           f"{RAGFLOW_SERVER}{path}",
           "-H", f"Authorization: Bearer {RAGFLOW_KEY}",
           "-H", "Content-Type: application/json"]
    if body is not None:
        cmd += ["-d", json.dumps(body)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"_raw": r.stdout[:800], "_err": r.stderr[:300]}


def ragflow_upload(path, filename):
    """Every real eCoA filename has a comma in it — both the current Drive
    convention (BATCH_CODE, DATE_LAB.pdf) and the Head-of-QC one
    (BatchNo, code, date, LAB.pdf). curl's -F parser treats ANY comma
    anywhere in the -F value (in the @path, or in an explicit filename=)
    as a field/attachment separator, so a real eCoA name breaks it —
    confirmed this session by bisecting: a Cyrillic-only name uploaded
    fine, a comma-only name (even with a plain ASCII @path and the comma
    confined to filename=) failed with "Failed to open/read local data
    from file/...". Backslash-escaping the comma per curl's documented
    -F escape syntax did NOT fix it either (tested directly).

    The reliable fix: always stage a copy under a guaranteed comma-free
    ASCII temp name for the actual curl @path upload — proven to work —
    then rename the document to the true filename with a plain JSON PUT,
    which has no comma problem since it never goes through curl's form
    parser."""
    import shutil
    import tempfile
    import uuid
    tmp_dir = tempfile.mkdtemp(prefix="ragflow_up_")
    safe_path = os.path.join(tmp_dir, f"{uuid.uuid4().hex}.pdf")
    shutil.copy(path, safe_path)
    try:
        cmd = ["curl", "-sS", "-X", "POST",
               f"{RAGFLOW_SERVER}/api/v1/datasets/{DATASET_ID}/documents",
               "-H", f"Authorization: Bearer {RAGFLOW_KEY}",
               "-F", f"file=@{safe_path};type=application/pdf"]
        r = subprocess.run(cmd, capture_output=True, text=True)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    try:
        up = json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"_curl_stdout": r.stdout[:500], "_curl_stderr": r.stderr[:500]}
    if up.get("code") != 0:
        return up
    doc_id = up["data"][0]["id"]
    ren = ragflow_api(f"/api/v1/datasets/{DATASET_ID}/documents/{doc_id}",
                       "PUT", {"name": filename})
    if ren.get("code") != 0:
        return {"code": ren.get("code"), "message": f"upload OK, rename failed: {ren}"}
    return up


def load_index():
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"by_dedup_key": {}, "by_drive_id": {}}


def save_index(idx):
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(idx, f, indent=1, ensure_ascii=False)


def extract_native_text(pdf_path):
    r = subprocess.run(["pdftotext", "-layout", pdf_path, "-"],
                        capture_output=True, text=True)
    return r.stdout


def vision_ocr(png_bytes, page_num, total_pages):
    b64 = base64.b64encode(png_bytes).decode()
    last_err = None
    for provider in OCR_PROVIDERS:
        key = os.environ.get(provider["env"])
        if not key:
            continue
        payload = {
            "model": provider["model"], "max_tokens": 4096, "temperature": 0,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": FULL_TEXT_OCR_PROMPT},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{b64}", "detail": "high"}}]}],
        }
        # base64 image data is far too large for a command-line argument
        # (E2BIG) — the payload has to go through a temp file and -d @file.
        tmp_path = None
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False, encoding="utf-8") as tf:
                json.dump(payload, tf)
                tmp_path = tf.name
            r = subprocess.run(
                ["curl", "-sS", f"{provider['base_url']}/chat/completions",
                 "-H", f"Authorization: Bearer {key}",
                 "-H", "Content-Type: application/json",
                 "-d", f"@{tmp_path}"],
                capture_output=True, text=True, timeout=90)
            d = json.loads(r.stdout)
            text = d.get("choices", [{}])[0].get("message", {}).get("content", "")
            if len(text.strip()) < 30:
                raise RuntimeError(f"{provider['name']} returned <30 chars "
                                    f"(refusal or empty) on page {page_num}/{total_pages}")
            return text
        except Exception as e:
            last_err = e
            continue
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
    raise RuntimeError(f"all vision providers failed on page {page_num}/{total_pages}: {last_err}")


def extract_text_for_pdf(pdf_path, scratch_dir):
    native = extract_native_text(pdf_path)
    if len(native.strip()) > 200:
        return native, "native"
    # scanned — render pages and OCR each
    prefix = os.path.join(scratch_dir, "ocr_page")
    subprocess.run(["pdftoppm", "-png", "-r", "200", pdf_path, prefix],
                    capture_output=True)
    pages = sorted(f for f in os.listdir(scratch_dir) if f.startswith("ocr_page"))
    parts = []
    for i, pg in enumerate(pages, 1):
        png = open(os.path.join(scratch_dir, pg), "rb").read()
        parts.append(vision_ocr(png, i, len(pages)))
        os.remove(os.path.join(scratch_dir, pg))
    return "\n\n--- PAGE BREAK ---\n\n".join(parts), "vision"


def parse_drive_filename(title):
    """Old convention (as currently on Drive, confirmed this session):
    BATCH_CERTCODE, DATE_LAB.pdf — e.g.
    P050192_NGP-QCG-SOP-024 F3, 28.11.2025_NGP.pdf. Also accepts the new
    Head-of-QC comma convention (BatchNo, code, date, LAB.pdf) so this
    script keeps working if the physical re-filing project (out of scope
    here — see classify_ecoa.py's closing note) is ever done first."""
    assert title.lower().endswith(".pdf")
    base = title[:-4]
    parts = [p.strip() for p in base.split(",")]
    if len(parts) == 4:
        batch, code, date, lab = parts
        return {"batch_raw": batch, "cert_code": code, "date": date, "lab": lab}
    if len(parts) == 2:
        left, right = parts
        if "_" not in right:
            return None
        date, lab = right.rsplit("_", 1)
        if lab == "DFL":
            batch, cert = (left.split("_", 1) + [""])[:2] if "_" in left else (left, "")
        else:
            batch, cert = (left.rsplit("_", 1)) if "_" in left else (left, "")
        return {"batch_raw": batch.replace("＊", "*").strip(), "cert_code": cert.strip(),
                "date": date.strip(), "lab": lab.strip()}
    return None


def process_one(pdf_path, filename, idx, dry_run=True):
    parsed = parse_drive_filename(filename)
    if parsed is None:
        return {"filename": filename, "status": "SKIP_UNPARSEABLE_FILENAME"}

    scratch_dir = os.path.dirname(pdf_path)
    text, source = extract_text_for_pdf(pdf_path, scratch_dir)
    data = open(pdf_path, "rb").read()
    meta = ce.classify(filename, text, data, parsed["batch_raw"],
                        parsed["cert_code"], parsed["date"], parsed["lab"])
    meta["text_source"] = source

    key = "|".join(str(x) for x in meta["dedup_key"])
    if key in idx["by_dedup_key"]:
        return {"filename": filename, "status": "SKIP_DUPLICATE",
                "duplicate_of": idx["by_dedup_key"][key], "meta": meta}

    if dry_run:
        return {"filename": filename, "status": "WOULD_UPLOAD", "meta": meta}

    up = ragflow_upload(pdf_path, filename)
    if up.get("code") != 0:
        return {"filename": filename, "status": "UPLOAD_FAILED", "error": up}
    doc_id = up["data"][0]["id"]

    flat_meta = {k: v for k, v in meta.items() if v is not None and not isinstance(v, (tuple, list))}
    flat_meta["dedup_key"] = key
    ragflow_api(f"/api/v1/datasets/{DATASET_ID}/documents/{doc_id}", "PUT",
                {"parser_config": {"layout_recognize": "gpt-4.1@openai-vlm@OpenAI"}})
    ragflow_api(f"/api/v1/datasets/{DATASET_ID}/documents/{doc_id}", "PUT",
                {"meta_fields": flat_meta})
    ragflow_api(f"/api/v1/datasets/{DATASET_ID}/chunks", "POST", {"document_ids": [doc_id]})

    idx["by_dedup_key"][key] = filename
    return {"filename": filename, "status": "UPLOADED", "doc_id": doc_id, "meta": meta}


if __name__ == "__main__":
    print("This module is meant to be driven by a caller that supplies the "
          "actual Drive file list (id -> local path after download) — it has "
          "no Drive credentials of its own. See process_one() / parse_drive_filename() "
          "/ extract_text_for_pdf() for the pieces; classify_ecoa.py has its own "
          "self-test. Run classify_ecoa.py directly to verify the classification "
          "logic before wiring this driver to a real file list.")
