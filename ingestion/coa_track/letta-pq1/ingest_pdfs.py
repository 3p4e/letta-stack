#!/usr/bin/env python3
"""
Drive → Letta ingest worker.

Called by deploy.sh. Reads env:
  SA_JSON, DRIVE_FOLDER_ID, LETTA_BASE, LETTA_TOKEN, PQ1_SOURCE_ID

For each PDF in the Drive folder:
  1. Download via Google Drive API (service-account auth, supports shared drives).
  2. POST multipart to Letta /v1/sources/{source_id}/upload.
  3. Skip if the file_name already exists in the source.
  4. Poll the returned job to confirm chunking + embedding completion.
"""

from __future__ import annotations

import base64
import io
import json
import os
import pathlib
import sys
import time
from typing import Any

import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SA_JSON       = os.environ["SA_JSON"]
DRIVE_FOLDER  = os.environ["DRIVE_FOLDER_ID"]
LETTA_BASE    = os.environ["LETTA_BASE"].rstrip("/")
LETTA_TOKEN   = os.environ["LETTA_TOKEN"]
SRC_ID        = os.environ["PQ1_SOURCE_ID"]

HEADERS_JSON  = {"Authorization": f"Bearer {LETTA_TOKEN}", "Content-Type": "application/json"}
HEADERS_BARE  = {"Authorization": f"Bearer {LETTA_TOKEN}"}

WORKDIR = pathlib.Path("/tmp/pq1_pdfs")
WORKDIR.mkdir(exist_ok=True)


def log(msg: str) -> None:
    print(msg, flush=True)


def list_drive_pdfs() -> list[dict[str, Any]]:
    creds = service_account.Credentials.from_service_account_file(
        SA_JSON, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    svc = build("drive", "v3", credentials=creds, cache_discovery=False)
    files: list[dict[str, Any]] = []
    token = None
    while True:
        resp = (
            svc.files()
            .list(
                q=f"'{DRIVE_FOLDER}' in parents and trashed=false and mimeType='application/pdf'",
                spaces="drive",
                fields="nextPageToken, files(id,name,size,mimeType,md5Checksum)",
                pageSize=200,
                pageToken=token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        files.extend(resp.get("files", []))
        token = resp.get("nextPageToken")
        if not token:
            break
    return svc, files  # type: ignore[return-value]


def existing_filenames() -> set[str]:
    """Names already ingested into this source (so re-runs skip)."""
    out: set[str] = set()
    try:
        r = requests.get(
            f"{LETTA_BASE}/v1/sources/{SRC_ID}/files",
            headers=HEADERS_BARE,
            timeout=20,
            params={"limit": 1000},
        )
        if r.ok:
            data = r.json()
            items = data if isinstance(data, list) else data.get("data", data.get("files", []))
            for f in items:
                name = f.get("file_name") or f.get("original_file_name") or f.get("name")
                if name:
                    out.add(name)
    except requests.RequestException as e:
        log(f"  warn: could not list existing files ({e})")
    return out


def download(svc, file_id: str, dest: pathlib.Path) -> None:
    req = svc.files().get_media(fileId=file_id, supportsAllDrives=True)
    buf = io.FileIO(dest, "wb")
    dl = MediaIoBaseDownload(buf, req, chunksize=8 * 1024 * 1024)
    done = False
    while not done:
        _, done = dl.next_chunk()
    buf.close()


def upload_multipart(local: pathlib.Path) -> tuple[bool, str]:
    """Letta accepts multipart/form-data on /v1/sources/{id}/upload."""
    with open(local, "rb") as fh:
        files = {"file": (local.name, fh, "application/pdf")}
        r = requests.post(
            f"{LETTA_BASE}/v1/sources/{SRC_ID}/upload",
            headers=HEADERS_BARE,
            files=files,
            timeout=600,
        )
    return r.ok, (r.text[:300] if not r.ok else r.json().get("id", "ok"))


def upload_b64_fallback(local: pathlib.Path) -> tuple[bool, str]:
    """Fallback: some Letta versions expect base64 JSON."""
    payload = {
        "file_name": local.name,
        "file_data": base64.b64encode(local.read_bytes()).decode(),
        "content_type": "application/pdf",
    }
    r = requests.post(
        f"{LETTA_BASE}/v1/sources/{SRC_ID}/upload",
        headers=HEADERS_JSON,
        data=json.dumps(payload),
        timeout=600,
    )
    return r.ok, (r.text[:300] if not r.ok else r.json().get("id", "ok"))


def wait_for_jobs(active_ids: list[str], timeout_s: int = 600) -> None:
    """Best-effort wait for the source-side ingestion jobs to finish."""
    if not active_ids:
        return
    deadline = time.time() + timeout_s
    pending = set(active_ids)
    while pending and time.time() < deadline:
        for jid in list(pending):
            try:
                r = requests.get(
                    f"{LETTA_BASE}/v1/jobs/{jid}", headers=HEADERS_BARE, timeout=15
                )
                if r.ok:
                    status = (r.json() or {}).get("status", "")
                    if status in ("completed", "failed", "cancelled"):
                        pending.discard(jid)
            except requests.RequestException:
                pass
        if pending:
            time.sleep(3)


def main() -> int:
    svc, drive_files = list_drive_pdfs()
    log(f"drive: found {len(drive_files)} PDFs in folder {DRIVE_FOLDER}")

    already = existing_filenames()
    log(f"letta: {len(already)} files already in this source")

    ok = skipped = failed = 0
    job_ids: list[str] = []

    for i, f in enumerate(drive_files, 1):
        name = f["name"]
        if name in already:
            skipped += 1
            log(f"[{i:>3}/{len(drive_files)}] skip (exists): {name}")
            continue

        local = WORKDIR / name
        try:
            download(svc, f["id"], local)
        except Exception as e:
            failed += 1
            log(f"[{i:>3}/{len(drive_files)}] FAIL download: {name} :: {e!s:.200}")
            continue

        size_kb = local.stat().st_size // 1024
        good, info = upload_multipart(local)
        if not good:
            good, info = upload_b64_fallback(local)

        if good:
            ok += 1
            log(f"[{i:>3}/{len(drive_files)}] ok ({size_kb} KB): {name} → job={info}")
            if isinstance(info, str) and info.startswith(("job-", "ingest-")):
                job_ids.append(info)
        else:
            failed += 1
            log(f"[{i:>3}/{len(drive_files)}] FAIL upload: {name} :: {info}")

        try:
            local.unlink()
        except OSError:
            pass

    log("waiting for ingestion jobs to complete…")
    wait_for_jobs(job_ids)

    log(
        f"\nSummary  ok={ok}  skipped={skipped}  failed={failed}"
        f"  (drive_total={len(drive_files)})"
    )
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
