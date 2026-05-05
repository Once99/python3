#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import json
import os
import shutil
import ssl
import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import requests
    from requests.adapters import HTTPAdapter
except Exception:
    requests = None
    HTTPAdapter = None

try:
    from urllib3.util.retry import Retry
except Exception:
    Retry = None


REPO_PATH_1 = Path("/Users/oncechen/IdeaProjects/feiyu-site")
REPO_PATH_2 = Path("/Applications/XAMPP/xamppfiles/htdocs/feiyu-site")

APK_NAME = "flychat_release.apk"
URLS = [
    "https://feiyu-02.equgou.com/Android/apk/flychat/flychat_release.apk",
]

HEADERS = {
    "Cache-Control": "no-cache, no-store, max-age=0, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}

CONNECT_TIMEOUT = 10
READ_TIMEOUT = 60
CHUNK_SIZE = 1024 * 64


if requests is not None:
    try:
        requests.packages.urllib3.disable_warnings()
    except Exception:
        pass


@dataclass(frozen=True)
class RepoPaths:
    root: Path
    apk_dir: Path
    apk_path: Path
    version_path: Path


def log(message: str) -> None:
    print(message, flush=True)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def get_repo_paths(repo_path: Path) -> RepoPaths:
    apk_dir = repo_path / "apk"
    return RepoPaths(
        root=repo_path,
        apk_dir=apk_dir,
        apk_path=apk_dir / APK_NAME,
        version_path=repo_path / "version.json",
    )


def run_cmd(repo_path: Path, cmd: list[str], check: bool = True) -> str:
    proc = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
    if check and proc.returncode != 0:
        joined = " ".join(cmd)
        raise RuntimeError(
            f"命令执行失败: {repo_path} > {joined}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )
    return proc.stdout.strip()


def is_worktree_clean(repo_path: Path) -> bool:
    unstaged_clean = subprocess.run(
        ["git", "diff", "--quiet"],
        cwd=repo_path,
    ).returncode == 0
    staged_clean = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=repo_path,
    ).returncode == 0
    return unstaged_clean and staged_clean


def ensure_clean_worktree(repo_path: Path) -> None:
    if is_worktree_clean(repo_path):
        return
    status = run_cmd(repo_path, ["git", "status", "--short"], check=False)
    raise RuntimeError(
        f"{repo_path} 检测到已跟踪文件存在未提交变更，已中止。\n{status}"
    )


def git_pull_safe(repo_path: Path) -> None:
    ensure_clean_worktree(repo_path)
    log(f"🔄 git pull (--ff-only) @ {repo_path}")
    proc = subprocess.run(
        ["git", "pull", "--ff-only"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        output = proc.stdout.strip()
        if output:
            log(output)
        return

    stderr = (proc.stderr or "") + (proc.stdout or "")
    if "Not possible to fast-forward" not in stderr and "divergent" not in stderr.lower():
        raise RuntimeError(
            f"git pull --ff-only 失败: {repo_path}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )

    log(f"⚠️ 检测到分叉分支，改用 git pull --rebase @ {repo_path}")
    output = run_cmd(repo_path, ["git", "pull", "--rebase"])
    if output:
        log(output)


def get_remote_url(repo_path: Path, remote_name: str = "origin") -> str:
    return run_cmd(repo_path, ["git", "remote", "get-url", remote_name], check=False).strip()


def atomic_write_json(path: Path, data: dict) -> None:
    ensure_dir(path.parent)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def atomic_copy(src: Path, dst: Path) -> None:
    ensure_dir(dst.parent)
    fd, tmp_name = tempfile.mkstemp(dir=dst.parent, prefix=dst.name, suffix=".tmp")
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        shutil.copy2(src, tmp_path)
        os.replace(tmp_path, dst)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def with_cache_bust(url: str) -> str:
    ts = int(time.time())
    joiner = "&" if "?" in url else "?"
    return f"{url}{joiner}_t={ts}"


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def files_are_same(file1: Path, file2: Path) -> bool:
    if not file1.exists() or not file2.exists():
        return False
    if file1.stat().st_size != file2.stat().st_size:
        return False
    return sha256sum(file1) == sha256sum(file2)


def build_session():
    if requests is None:
        return None

    session = requests.Session()
    if Retry is not None and HTTPAdapter is not None:
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=1,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
    return session


def is_valid_apk_file(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            return fh.read(2) == b"PK"
    except OSError:
        return False


def download_with_urllib(url: str, output_path: Path) -> None:
    request = Request(url, headers=HEADERS)
    ssl_context = ssl._create_unverified_context()
    with urlopen(request, timeout=CONNECT_TIMEOUT + READ_TIMEOUT, context=ssl_context) as response:
        status = getattr(response, "status", 200)
        if status != 200:
            raise RuntimeError(f"响应码: {status}")
        with output_path.open("wb") as fh:
            while True:
                chunk = response.read(CHUNK_SIZE)
                if not chunk:
                    break
                fh.write(chunk)


def download_apk_to_repo1(repo1_apk_path: Path) -> str:
    ensure_dir(repo1_apk_path.parent)
    session = build_session()
    download_failed = False

    for url in URLS:
        busted_url = with_cache_bust(url)
        log(f"🚚 下载(避缓存): {busted_url}")

        fd, tmp_name = tempfile.mkstemp(dir=repo1_apk_path.parent, prefix=repo1_apk_path.name, suffix=".tmp")
        os.close(fd)
        tmp_path = Path(tmp_name)
        try:
            if session is not None:
                with session.get(
                    busted_url,
                    timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                    verify=False,
                    stream=True,
                    headers=HEADERS,
                ) as response:
                    if response.status_code != 200:
                        log(f"❌ 响应码: {response.status_code}")
                        download_failed = True
                        continue

                    with tmp_path.open("wb") as fh:
                        for chunk in response.iter_content(CHUNK_SIZE):
                            if chunk:
                                fh.write(chunk)
            else:
                download_with_urllib(busted_url, tmp_path)

            if not is_valid_apk_file(tmp_path):
                log("❌ 下载内容疑似不是 APK（文件头不是 PK），可能返回错误页或缓存页")
                download_failed = True
                continue

            if files_are_same(tmp_path, repo1_apk_path):
                log("ℹ️ 下载完成，但 APK 内容与当前 repo1 文件一致，跳过覆盖")
                return "unchanged"

            os.replace(tmp_path, repo1_apk_path)
            size_mb = repo1_apk_path.stat().st_size / 1024 / 1024
            log(f"✅ APK 下载成功：{repo1_apk_path} ({size_mb:.2f} MB)")
            return "updated"
        except Exception as exc:
            download_failed = True
            if requests is not None and isinstance(exc, requests.RequestException):
                log(f"❌ 下载失败: {exc}")
            elif isinstance(exc, (HTTPError, URLError)):
                log(f"❌ 下载失败: {exc}")
            else:
                log(f"❌ 下载失败: {exc}")
        finally:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    return "failed" if download_failed else "unchanged"


def load_version_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def build_updated_version_json(path: Path, version: str) -> dict:
    current = load_version_json(path)
    assets = current.get("assets")
    if not isinstance(assets, dict):
        assets = {"css": [], "js": []}
    assets.setdefault("css", [])
    assets.setdefault("js", [])
    return {
        "version": version,
        "assets": assets,
    }


def update_version_json(path: Path, version: str) -> None:
    atomic_write_json(path, build_updated_version_json(path, version))


def generate_version() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


def repo_has_staged_changes(repo_path: Path) -> bool:
    return subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=repo_path,
    ).returncode != 0


def git_commit_push(repo_path: Path, files_to_add: list[str], version: str) -> bool:
    run_cmd(repo_path, ["git", "add", *files_to_add])

    if not repo_has_staged_changes(repo_path):
        log(f"⚠️ {repo_path} 无变更，跳过提交")
        return False

    message = f"{datetime.now():%Y-%m-%d} update apk {version}"
    run_cmd(repo_path, ["git", "commit", "-m", message])
    run_cmd(repo_path, ["git", "push"])
    log(f"✅ {repo_path} push 完成：{message}")
    return True


def git_tag_push(repo_path: Path, version: str) -> None:
    tag = f"v{version}"
    exists = subprocess.run(
        ["git", "rev-parse", "-q", "--verify", tag],
        cwd=repo_path,
        capture_output=True,
        text=True,
    ).returncode == 0

    if not exists:
        run_cmd(repo_path, ["git", "tag", tag])
    run_cmd(repo_path, ["git", "push", "origin", tag])
    log(f"🏷️ tag 推送成功：{tag}")


def main() -> None:
    log("🚀 双目录 APK 自动更新开始...")

    repo1 = get_repo_paths(REPO_PATH_1)
    repo2 = get_repo_paths(REPO_PATH_2)
    repo1_remote = get_remote_url(repo1.root)
    repo2_remote = get_remote_url(repo2.root)
    same_remote = bool(repo1_remote and repo1_remote == repo2_remote)

    git_pull_safe(repo1.root)
    git_pull_safe(repo2.root)

    download_status = download_apk_to_repo1(repo1.apk_path)
    if download_status == "failed":
        log("❌ APK 下载失败，退出")
        return
    if download_status == "unchanged":
        log("ℹ️ APK 无变化，跳过 version.json 更新、提交和打 tag")
        return

    version = generate_version()
    log(f"✅ 生成版本号: {version}")

    update_version_json(repo1.version_path, version)
    if not same_remote:
        atomic_copy(repo1.apk_path, repo2.apk_path)
        atomic_copy(repo1.version_path, repo2.version_path)
        log("✅ 已同步到 repo2：")
        log(f" - {repo2.apk_path}")
        log(f" - {repo2.version_path}")
    else:
        log("ℹ️ 检测到两个目录使用同一个远端仓库，repo2 将在 repo1 push 后通过 git pull 同步")

    committed1 = git_commit_push(
        repo1.root,
        [
            os.path.relpath(repo1.apk_path, repo1.root),
            os.path.relpath(repo1.version_path, repo1.root),
        ],
        version,
    )
    committed2 = False

    if not same_remote:
        committed2 = git_commit_push(
            repo2.root,
            [
                os.path.relpath(repo2.apk_path, repo2.root),
                os.path.relpath(repo2.version_path, repo2.root),
            ],
            version,
        )

    if committed1:
        git_tag_push(repo1.root, version)

    if same_remote:
        if committed1:
            git_pull_safe(repo2.root)
    elif committed1 or committed2:
        git_pull_safe(repo1.root)
        git_pull_safe(repo2.root)

    log("✅ 全流程完成 ✅")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log(f"❌ 执行失败: {exc}")
        raise SystemExit(1)
