#!/usr/bin/env python3
"""
ImB_QC_COAs → Letta ingest worker.

Walks a source location and uploads every CoA (PDF or DOCX, electronic or
scanned) into a Letta source. Two source modes are supported:

  LOCAL    — walk a directory on the local filesystem
             (e.g. the Drive-for-Desktop mount on the user's PC, or a
             bind-mount inside the KVM4 container)
  DRIVE    — walk a Google Drive folder via a service account (mirrors the
             existing PQ1 pipeline pattern)

Env (Letta target — always required):
  LETTA_BASE         e.g. http://localhost:8283
  LETTA_TOKEN        e.g. ${LETTA_SERVER_PASS}
  IMB_SOURCE_ID      Letta source id (created by deploy.sh)

Env (LOCAL mode):
  IMB_LOCAL_PATH     filesystem path to the CoA folder

Env (DRIVE mode):
  SA_JSON            path to Google service-account JSON
  IMB_DRIVE_FOLDER_ID  Drive folder id

Mode is auto-selected: DRIVE if SA_JSON and IMB_DRIVE_FOLDER_ID are set,
otherwise LOCAL.
"""

from __future__ import annotations

import base64
import io
import json
import os
import pathlib
import sys
import time
from typing import Any, Iterable

import requests

LETTA_BASE = os.environ["LETTA_BASE"].rstrip("/")
LETTA_TOKEN = os.environ["LETTA_TOKEN"]
SRC_ID = os.environ["IMB_SOURCE_ID"]

HEADERS_JSON = {"Authorization": f"Bearer {LETTA_TOKEN}", "Content-Type": "application/json"}
HEADERS_BARE = {"Authorization": f"Bearer {LETTA_TOKEN}"}

SUPPORTED_EXT = {".pdf", ".docx"}
MIME_BY_EXT = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

WORKDIR = pathlib.Path("/tmp/imb_qc_coas")
WORKDIR.mkdir(exist_ok=True)


def log(msg: str) -> None:
    print(msg, flush=True)


def existing_filenames() -> set[str]:
    out: set[str] = set()
    try:
        r = requests.get(
            f"{LETTA_BASE}/v1/sources/{SRC_ID}/files",
            headers=HEADERS_BARE,
            timeout=20,
            params={"limit": 2000},
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


def iter_local(root: pathlib.Path) -> Iterable[tuple[str, pathlib.Path]]:
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXT:
            yield p.name, p


def iter_drive(svc, folder_id: str):
    stack = [folder_id]
    while stack:
        fid = stack.pop()
        token = None
        while True:
            resp = (
                svc.files()
                .list(
                    q=f"'{fid}' in parents and trashed=false",
                    spaces="drive",
                    fields="nextPageToken, files(id,name,mimeType,size)",
                    pageSize=200,
                    pageToken=token,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                )
                .execute()
            )
            for f in resp.get("files", []):
                if f["mimeType"] == "application/vnd.google-apps.folder":
                    stack.append(f["id"])
                else:
                    name = f["name"]
                    ext = pathlib.Path(name).suffix.lower()
                    if ext in SUPPORTED_EXT:
                        yield f
            token = resp.get("nextPageToken")
            if not token:
                break


def download_from_drive(svc, file_id: str, dest: pathlib.Path) -> None:
    from googleapiclient.http import MediaIoBaseDownload

    req = svc.files().get_media(fileId=file_id, supportsAllDrives=True)
    buf = io.FileIO(dest, "wb")
    dl = MediaIoBaseDownload(buf, req, chunksize=8 * 1024 * 1024)
    done = False
    while not done:
        _, done = dl.next_chunk()
    buf.close()


def upload_multipart(local: pathlib.Path) -> tuple[bool, str]:
    mime = MIME_BY_EXT[local.suffix.lower()]
    with open(local, "rb") as fh:
        files = {"file": (local.name, fh, mime)}
        r = requests.post(
            f"{LETTA_BASE}/v1/sources/{SRC_ID}/upload",
            headers=HEADERS_BARE,
            files=files,
            timeout=600,
        )
    if r.ok:
        try:
            return True, r.json().get("id", "ok")
        except ValueError:
            return True, "ok"
    return False, r.text[:300]


def upload_b64_fallback(local: pathlib.Path) -> tuple[bool, str]:
    payload = {
        "file_name": local.name,
        "file_data": base64.b64encode(local.read_bytes()).decode(),
        "content_type": MIME_BY_EXT[local.suffix.lower()],
    }
    r = requests.post(
        f"{LETTA_BASE}/v1/sources/{SRC_ID}/upload",
        headers=HEADERS_JSON,
        data=json.dumps(payload),
        timeout=600,
    )
    if r.ok:
        try:
            return True, r.json().get("id", "ok")
        except ValueError:
            return True, "ok"
    return False, r.text[:300]


def wait_for_jobs(active_ids: list[str], timeout_s: int = 900) -> None:
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
                if r.ok and (r.json() or {}).get("status", "") in (
                    "completed",
                    "failed",
                    "cancelled",
                ):
                    pending.discard(jid)
            except requests.RequestException:
                pass
        if pending:
            time.sleep(3)


def run_local() -> int:
    root = pathlib.Path(os.environ["IMB_LOCAL_PATH"]).expanduser()
    if not root.is_dir():
        log(f"ERROR: IMB_LOCAL_PATH not a directory: {root}")
        return 2
    log(f"local: scanning {root}")
    items = list(iter_local(root))
    log(f"local: found {len(items)} CoA files ({sorted({p.suffix.lower() for _, p in items})})")

    already = existing_filenames()
    log(f"letta: {len(already)} files already in source {SRC_ID}")

    ok = skipped = failed = 0
    job_ids: list[str] = []
    for i, (name, path) in enumerate(items, 1):
        if name in already:
            skipped += 1
            log(f"[{i:>3}/{len(items)}] skip (exists): {name}")
            continue
        size_kb = path.stat().st_size // 1024
        good, info = upload_multipart(path)
        if not good:
            good, info = upload_b64_fallback(path)
        if good:
            ok += 1
            log(f"[{i:>3}/{len(items)}] ok ({size_kb} KB): {name} → job={info}")
            if isinstance(info, str) and info.startswith(("job-", "ingest-")):
                job_ids.append(info)
        else:
            failed += 1
            log(f"[{i:>3}/{len(items)}] FAIL upload: {name} :: {info}")

    log("waiting for ingestion jobs to complete…")
    wait_for_jobs(job_ids)
    log(f"\nSummary  ok={ok}  skipped={skipped}  failed={failed}  (total={len(items)})")
    return 0 if failed == 0 else 2


def run_drive() -> int:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    sa_json = os.environ["SA_JSON"]
    folder = os.environ["IMB_DRIVE_FOLDER_ID"]
    creds = service_account.Credentials.from_service_account_file(
        sa_json, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    svc = build("drive", "v3", credentials=creds, cache_discovery=False)

    items = list(iter_drive(svc, folder))
    log(f"drive: found {len(items)} CoA files in folder tree {folder}")

    already = existing_filenames()
    log(f"letta: {len(already)} files already in source {SRC_ID}")

    ok = skipped = failed = 0
    job_ids: list[str] = []
    for i, f in enumerate(items, 1):
        name = f["name"]
        if name in already:
            skipped += 1
            log(f"[{i:>3}/{len(items)}] skip (exists): {name}")
            continue

        local = WORKDIR / name
        try:
            download_from_drive(svc, f["id"], local)
        except Exception as e:
            failed += 1
            log(f"[{i:>3}/{len(items)}] FAIL download: {name} :: {e!s:.200}")
            continue

        size_kb = local.stat().st_size // 1024
        good, info = upload_multipart(local)
        if not good:
            good, info = upload_b64_fallback(local)

        if good:
            ok += 1
            log(f"[{i:>3}/{len(items)}] ok ({size_kb} KB): {name} → job={info}")
            if isinstance(info, str) and info.startswith(("job-", "ingest-")):
                job_ids.append(info)
        else:
            failed += 1
            log(f"[{i:>3}/{len(items)}] FAIL upload: {name} :: {info}")

        try:
            local.unlink()
        except OSError:
            pass

    log("waiting for ingestion jobs to complete…")
    wait_for_jobs(job_ids)
    log(f"\nSummary  ok={ok}  skipped={skipped}  failed={failed}  (drive_total={len(items)})")
    return 0 if failed == 0 else 2


def main() -> int:
    mode = "DRIVE" if (os.environ.get("SA_JSON") and os.environ.get("IMB_DRIVE_FOLDER_ID")) else "LOCAL"
    log(f"mode: {mode}")
    return run_drive() if mode == "DRIVE" else run_local()


if __name__ == "__main__":
    sys.exit(main())
