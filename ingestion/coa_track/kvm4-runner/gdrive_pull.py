#!/usr/bin/env python3
"""
gdrive_pull.py — download Drive folders/files via a service-account.

Designed to run inside kvm4-runner.  Service account JSON at
/opt/data/.gcp/sa.json must be Editor (or Viewer) on the target items.

Usage
-----
    python3 gdrive_pull.py folder <FOLDER_ID> <OUT_DIR>
    python3 gdrive_pull.py file   <FILE_ID>   <OUT_PATH>

Resumability: existing files of the same byte size are skipped so a re-run
fills in only what gdown missed without redownloading what we already have.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SA_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "/opt/data/.gcp/sa.json")
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
svc = build("drive", "v3", credentials=creds, cache_discovery=False)


def _download(file_id: str, out_path: Path, expected_size: int | None = None) -> None:
    if expected_size is not None and out_path.exists() and out_path.stat().st_size == expected_size:
        print(f"  skip (cached): {out_path.name}")
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    req = svc.files().get_media(fileId=file_id, supportsAllDrives=True)
    tmp = out_path.with_suffix(out_path.suffix + ".part")
    with tmp.open("wb") as fh:
        dl = MediaIoBaseDownload(fh, req, chunksize=2 * 1024 * 1024)
        done = False
        while not done:
            _, done = dl.next_chunk()
    tmp.rename(out_path)
    sz = out_path.stat().st_size
    print(f"  got: {out_path.name} ({sz} bytes)")


def pull_folder(folder_id: str, out_dir: Path) -> tuple[int, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    page_token = None
    n_files = n_skipped = 0
    while True:
        resp = svc.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            pageSize=200,
            pageToken=page_token,
            fields="nextPageToken, files(id, name, mimeType, size)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()
        for f in resp.get("files", []):
            name = f["name"]
            mime = f["mimeType"]
            if mime == "application/vnd.google-apps.folder":
                print(f"== folder: {name} ==")
                sub_n, sub_s = pull_folder(f["id"], out_dir / name)
                n_files += sub_n
                n_skipped += sub_s
                continue
            # Google-native docs (Docs/Sheets/Slides) can't be get_media'd directly;
            # we don't expect any in the QC folders but flag if we hit one.
            if mime.startswith("application/vnd.google-apps"):
                print(f"  WARN native gdoc, skipping: {name} ({mime})")
                n_skipped += 1
                continue
            target = out_dir / name
            try:
                size = int(f["size"]) if f.get("size") else None
            except (TypeError, ValueError):
                size = None
            if size is not None and target.exists() and target.stat().st_size == size:
                n_skipped += 1
                continue
            try:
                _download(f["id"], target, size)
                n_files += 1
            except Exception as e:
                print(f"  ERROR {name}: {e}")
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return n_files, n_skipped


def pull_file(file_id: str, out_path: Path) -> None:
    meta = svc.files().get(
        fileId=file_id, fields="id,name,mimeType,size", supportsAllDrives=True
    ).execute()
    name = meta["name"]
    if out_path.is_dir() or str(out_path).endswith("/"):
        out_path = out_path / name
    size = int(meta["size"]) if meta.get("size") else None
    print(f"== file: {name} ({meta.get('mimeType')}, {size} bytes) ==")
    _download(file_id, out_path, size)


def main() -> int:
    if len(sys.argv) < 4 or sys.argv[1] not in ("folder", "file"):
        print(__doc__)
        return 1
    target_id = sys.argv[2]
    out = Path(sys.argv[3])
    if sys.argv[1] == "folder":
        n, s = pull_folder(target_id, out)
        print(f"DONE: {n} fetched, {s} skipped, dir={out}")
    else:
        pull_file(target_id, out)
        print(f"DONE: file -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
