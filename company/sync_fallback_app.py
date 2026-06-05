#!/usr/bin/env python3
"""Sync fallback APP APKs from live download-address APIs.

This script updates the local fallback APK files used by the appBuild pages,
then commits and pushes the APK changes in each repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


@dataclass(frozen=True)
class AppTarget:
    name: str
    api_url: str
    repo: Path
    apk_path: Path
    referer: str
    post_data: Mapping[str, str]
    download_prefix: str


TARGETS = [
    AppTarget(
        name="QM",
        api_url="https://qm7088.com/app/queryAgentDownLoadAddress.php",
        repo=Path("/Users/oncechen/IdeaProjects/c_pt777"),
        apk_path=Path("WebRoot/appBuild/apk/pt777_fallback.apk"),
        referer="https://qm7088.com/app/",
        post_data={"isLogin": "0", "agent": "", "type": "android", "appProduct": "at"},
        download_prefix="ae",
    ),
    AppTarget(
        name="TH",
        api_url="https://tty187.vip/asp/queryAgentDownLoadAddress.php",
        repo=Path("/Users/oncechen/IdeaProjects/c_long8/web"),
        apk_path=Path("WebRoot/appBuild/apk/th_fallback.apk"),
        referer="https://tty187.vip/asp/",
        post_data={"isLogin": "0", "agent": "", "type": "android"},
        download_prefix="th",
    ),
]


class SyncError(RuntimeError):
    pass


def run(cmd: Iterable[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    cmd_list = list(cmd)
    print("+", " ".join(cmd_list))
    completed = subprocess.run(
        cmd_list,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.stdout:
        print(completed.stdout.rstrip())
    if check and completed.returncode != 0:
        raise SyncError(f"command failed ({completed.returncode}): {' '.join(cmd_list)}")
    return completed


def ssl_context(insecure: bool) -> ssl.SSLContext | None:
    if insecure:
        return ssl._create_unverified_context()
    return None


BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Mobile Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
}


def fetch_json(target: AppTarget, timeout: int, insecure: bool) -> dict:
    headers = dict(BROWSER_HEADERS)
    headers["Referer"] = target.referer
    headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
    headers["X-Requested-With"] = "XMLHttpRequest"
    body = urllib.parse.urlencode(target.post_data).encode()
    request = urllib.request.Request(target.api_url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=ssl_context(insecure)) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            body = response.read().decode(charset)
    except urllib.error.URLError as exc:
        raise SyncError(f"failed to call API {target.api_url}: {exc}") from exc

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise SyncError(f"API returned invalid JSON: {target.api_url}") from exc

    if payload.get("code") != "10000":
        raise SyncError(f"API returned non-success code for {target.api_url}: {payload!r}")
    return payload


def android_url_from_api(target: AppTarget, timeout: int, insecure: bool) -> str:
    payload = fetch_json(target, timeout, insecure)
    android_url = payload.get("data", {}).get("android")
    if not isinstance(android_url, str) or not android_url.startswith(("http://", "https://")):
        raise SyncError(f"{target.name} API did not provide a valid android URL: {payload!r}")
    return android_url


def page_download_url(target: AppTarget, android_url: str) -> str:
    parsed = urllib.parse.urlparse(android_url)
    if not parsed.scheme or not parsed.netloc:
        raise SyncError(f"{target.name} API returned malformed android URL: {android_url}")
    timestamp = time.strftime("%Y%m%d%H%M%S")
    return f"{parsed.scheme}://{parsed.netloc}/download/{target.download_prefix}_{timestamp}.apk"


def download_file(url: str, destination: Path, timeout: int, insecure: bool, referer: str) -> None:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": BROWSER_HEADERS["User-Agent"],
            "Accept": "*/*",
            "Referer": referer,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=ssl_context(insecure)) as response, destination.open("wb") as out:
            shutil.copyfileobj(response, out)
    except urllib.error.URLError as exc:
        raise SyncError(f"failed to download {url}: {exc}") from exc


def validate_apk(path: Path, min_size: int) -> None:
    size = path.stat().st_size
    if size < min_size:
        raise SyncError(f"downloaded APK is too small: {path} ({size} bytes)")
    with path.open("rb") as fh:
        magic = fh.read(4)
    if magic != b"PK\x03\x04":
        raise SyncError(f"downloaded file is not a ZIP/APK: {path}")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_clean_repo(repo: Path) -> None:
    status = run(["git", "status", "--porcelain"], cwd=repo).stdout.strip()
    if status:
        raise SyncError(f"repository has local changes; refusing to overwrite: {repo}\n{status}")


def sync_target(target: AppTarget, timeout: int, min_size: int, dry_run: bool, insecure: bool) -> bool:
    print(f"\n== {target.name} ==")
    ensure_clean_repo(target.repo)
    full_apk_path = target.repo / target.apk_path
    full_apk_path.parent.mkdir(parents=True, exist_ok=True)

    android_url = android_url_from_api(target, timeout, insecure)
    print(f"android: {android_url}")
    download_url = page_download_url(target, android_url)
    print(f"download: {download_url}")

    with tempfile.NamedTemporaryFile(prefix=f"{target.name.lower()}_fallback_", suffix=".apk", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        download_file(download_url, tmp_path, timeout, insecure, target.referer)
        validate_apk(tmp_path, min_size)
        old_size = full_apk_path.stat().st_size if full_apk_path.exists() else 0
        new_size = tmp_path.stat().st_size
        old_hash = sha256_file(full_apk_path)
        new_hash = sha256_file(tmp_path)
        print(f"compare: {full_apk_path} ({old_size} -> {new_size} bytes)")
        print(f"sha256: {old_hash or 'missing'} -> {new_hash}")
        if old_hash == new_hash:
            print(f"{target.name}: APK unchanged; skip replace/commit/push")
            return False
        if dry_run:
            print(f"{target.name}: APK changed; dry-run skips replace/commit/push")
            return True
        print(f"replace: {full_apk_path}")
        os.replace(tmp_path, full_apk_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    changed = bool(run(["git", "status", "--porcelain", "--", str(target.apk_path)], cwd=target.repo).stdout.strip())
    if not changed:
        print(f"{target.name}: APK unchanged; skip commit/push")
        return False

    run(["git", "add", str(target.apk_path)], cwd=target.repo)
    run(["git", "commit", "-m", f"同步 {target.name} 兜底 APK"], cwd=target.repo)
    run(["git", "push"], cwd=target.repo)
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync QM/TH fallback APK files and push commits.")
    parser.add_argument("--dry-run", action="store_true", help="download and validate, but do not replace/commit/push")
    parser.add_argument("--timeout", type=int, default=120, help="HTTP timeout in seconds")
    parser.add_argument("--min-size", type=int, default=5 * 1024 * 1024, help="minimum acceptable APK size in bytes")
    parser.add_argument("--insecure", action="store_true", help="skip TLS certificate verification for endpoints with incomplete chains")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    changed_any = False
    for target in TARGETS:
        changed_any = sync_target(target, args.timeout, args.min_size, args.dry_run, args.insecure) or changed_any
    print("\nDONE:", "changed" if changed_any else "no changes")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SyncError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
