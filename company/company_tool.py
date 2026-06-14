#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Company automation tool.

Usage:
  company_tool.py              # ask what to run
  company_tool.py pull         # pull all projects
  company_tool.py all git pull # pull all projects
  company_tool.py feiyu        # update Feiyu APK
  company_tool.py 94chat       # update 94Chat APK
  company_tool.py sync-ty      # sync sport/test to GitLab ty_sport/test
  company_tool.py check        # check local config and script itself
"""

import hashlib
import json
import os
import plistlib
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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

if requests is not None:
    try:
        requests.packages.urllib3.disable_warnings()
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 60
CHUNK_SIZE = 1024 * 64
GIT_TIMEOUT = 90
MAX_WORKERS = 6

HEADERS = {
    "Cache-Control": "no-cache, no-store, max-age=0, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}

PROJECTS = {
    "ezpay": {"path": "/Users/oncechen/IdeaProjects/ezpay-site/"},
    "qypc": {"path": "/Users/oncechen/IdeaProjects/qy_web_vue/"},
    "qyh5": {"path": "/Users/oncechen/IdeaProjects/qy_web_static_vue/"},
    "qy": {"path": "/Users/oncechen/IdeaProjects/c_qy/web/WebRoot/"},
    "rb88": {"path": "/Users/oncechen/IdeaProjects/rb88_web_vue/"},
    "jxf": {"path": "/Users/oncechen/IdeaProjects/jxf_web_vue/"},
    "uedpc": {"path": "/Users/oncechen/IdeaProjects/ued_web_vue/"},
    "uedh5": {"path": "/Users/oncechen/IdeaProjects/ued_web_static_vue/"},
    "ued": {"path": "/Users/oncechen/IdeaProjects/c_ued/WebRoot/"},
    "tq": {"path": "/Users/oncechen/IdeaProjects/c_sportone/web/WebRoot/"},
    "pt777": {"path": "/Users/oncechen/IdeaProjects/c_pt777/WebRoot/"},
    "pt777pc": {"path": "/Users/oncechen/IdeaProjects/pt777_web_vue/"},
    "pt777h5": {"path": "/Users/oncechen/IdeaProjects/pt777_web_static_vue/"},
    "long8": {"path": "/Users/oncechen/IdeaProjects/c_long8/web/WebRoot/"},
    "lwpc": {"path": "/Users/oncechen/IdeaProjects/e68_web_vue/"},
    "lwh5": {"path": "/Users/oncechen/IdeaProjects/e68_web_static_vue/"},
    "feiyu": {"path": "/Users/oncechen/IdeaProjects/feiyu-site-clean/"},
    "94Chat": {"path": "/Users/oncechen/IdeaProjects/site-dolphin/"},
    "weiquandanbao": {"path": "/Users/oncechen/IdeaProjects/site-weiquandanbao/"},
    "haitun": {"path": "/Users/oncechen/IdeaProjects/site-haitun-web/"},
    "dolphin_im": {"path": "/Users/oncechen/IdeaProjects/dolphin_im_pc/"},

}

ALIASES = {
    "all": "pull",
    "pull-all": "pull",
    "pull_all": "pull",
    "update-feiyu": "feiyu",
    "update_feiyu": "feiyu",
    "flychat": "feiyu",
    "update-94chat": "94chat",
    "update_94chat": "94chat",
    "94": "94chat",
    "sync_ty": "sync-ty",
    "sync-ty-sport": "sync-ty",
    "sync_ty_sport": "sync-ty",
    "ty": "sync-ty",
}


@dataclass(frozen=True)
class RepoPaths:
    root: Path
    apk_dir: Path
    apk_path: Path
    version_path: Path


@dataclass(frozen=True)
class ApkTarget:
    name: str
    repo1: Path
    repo2: Path
    apk_name: str
    urls: tuple[str, ...]
    push_tag: bool = False
    update_when_unchanged: bool = False
    asset_version_files: tuple[str, ...] = ()
    download_info_date_files: tuple[str, ...] = ()


APK_TARGETS = {
    "feiyu": ApkTarget(
        name="feiyu",
        repo1=Path("/Users/oncechen/IdeaProjects/feiyu-site-clean"),
        repo2=Path("/Users/oncechen/IdeaProjects/feiyu-site-clean"),
        apk_name="flychat_release.apk",
        urls=("https://fujkou.com:12828/Android/apk/flychat/flychat_release.apk", "https://feiyu-02.equgou.com/Android/apk/flychat/flychat_release.apk",),
        push_tag=True,
        update_when_unchanged=True,
        asset_version_files=("index.html",),
        download_info_date_files=("index.html",),
    ),
    "94chat": ApkTarget(
        name="94chat",
        repo1=Path("/Users/oncechen/IdeaProjects/site-dolphin"),
        repo2=Path("/Users/oncechen/IdeaProjects/site-dolphin"),
        apk_name="94chat.apk",
        urls=("https://94chat-2.equgou.com/Android/apk/94chat.apk",),
        push_tag=False,
        update_when_unchanged=True,
        asset_version_files=("index.html", "agreement.html", "support.html"),
    ),
}


class ToolError(RuntimeError):
    pass


def log(message: str) -> None:
    print(message, flush=True)


def print_usage() -> None:
    print("用法:")
    print("  company_tool.py              # 互动询问要执行什么")
    print("  company_tool.py pull         # pull all projects")
    print("  company_tool.py all git pull # pull all projects")
    print("  company_tool.py git pull     # pull all projects")
    print("  company_tool.py pull feiyu   # 只 pull 指定项目，可指定多个")
    print("  company_tool.py feiyu        # update feiyu apk")
    print("  company_tool.py 94chat       # update 94chat apk")
    print("  company_tool.py sync-ty      # sync sport/test to GitLab ty_sport/test")
    print("  company_tool.py check        # 检查配置")


def normalize_command(raw: str) -> str:
    key = raw.strip().lower()
    return ALIASES.get(key, key)


def normalize_argv(argv: list[str]) -> list[str]:
    """Accept shell-style commands like `all git pull` as aliases for `pull`."""
    normalized = [arg.strip() for arg in argv if arg.strip()]
    lowered = [arg.lower() for arg in normalized]

    if lowered in (["git", "pull"], ["all", "git", "pull"], ["all", "pull"]):
        return ["pull"]
    if lowered[:2] == ["all", "git"] and lowered[2:3] == ["pull"]:
        return ["pull", *normalized[3:]]
    if lowered[:1] == ["all"] and lowered[1:2] == ["pull"]:
        return ["pull", *normalized[2:]]
    if lowered[:2] == ["git", "pull"]:
        return ["pull", *normalized[2:]]

    return normalized


def run_cmd(repo_path: Path | str, cmd: list[str], check: bool = True, timeout: int | None = None) -> str:
    cwd = Path(repo_path)
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )
    if check and proc.returncode != 0:
        joined = " ".join(cmd)
        raise ToolError(
            f"命令执行失败: {cwd} > {joined}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )
    return (proc.stdout or "").strip()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def is_git_repo(path: Path | str) -> bool:
    repo = Path(path)
    if (repo / ".git").is_dir():
        return True
    proc = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def get_branch(path: Path | str) -> str:
    return run_cmd(path, ["git", "branch", "--show-current"], check=False).strip() or "(unknown)"


def has_upstream(path: Path | str) -> bool:
    proc = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "@{upstream}"],
        cwd=Path(path),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0 and bool(proc.stdout.strip())


def get_remote_url(repo_path: Path, remote_name: str = "origin") -> str:
    return run_cmd(repo_path, ["git", "remote", "get-url", remote_name], check=False).strip()


def is_worktree_clean(repo_path: Path) -> bool:
    unstaged = subprocess.run(["git", "diff", "--quiet"], cwd=repo_path).returncode == 0
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo_path).returncode == 0
    return unstaged and staged


def ensure_clean_worktree(repo_path: Path) -> None:
    if is_worktree_clean(repo_path):
        return
    status = run_cmd(repo_path, ["git", "status", "--short"], check=False)
    raise ToolError(f"{repo_path} 检测到已跟踪文件存在未提交变更，已中止。\n{status}")


def has_tracked_changes(repo_path: Path) -> bool:
    return not is_worktree_clean(repo_path)


def has_unpushed_commits(repo_path: Path) -> bool:
    if not has_upstream(repo_path):
        return False
    count = run_cmd(repo_path, ["git", "rev-list", "--count", "@{upstream}..HEAD"], check=False)
    try:
        return int(count or "0") > 0
    except ValueError:
        return False


def commit_tracked_changes(repo_path: Path, target_name: str) -> bool:
    if not has_tracked_changes(repo_path):
        return False

    status = run_cmd(repo_path, ["git", "status", "--short"], check=False)
    log(f"⚠️ {repo_path} 检测到已跟踪修改，先提交再 push：\n{status}")
    run_cmd(repo_path, ["git", "add", "-u"])

    if not repo_has_staged_changes(repo_path):
        log(f"ℹ️ {repo_path} 没有可提交的已跟踪修改")
        return False

    message = f"{datetime.now():%Y-%m-%d} update {target_name} site"
    run_cmd(repo_path, ["git", "commit", "-m", message])
    log(f"✅ {repo_path} 已提交：{message}")
    return True


def push_if_needed(repo_path: Path) -> None:
    if has_unpushed_commits(repo_path):
        log(f"⬆️ {repo_path} 有本地提交，先 git push")
        run_cmd(repo_path, ["git", "push"])
        log(f"✅ {repo_path} push 完成")


def git_push_or_pull_before_update(repo_path: Path, target_name: str) -> None:
    committed = commit_tracked_changes(repo_path, target_name)
    if committed or has_unpushed_commits(repo_path):
        push_if_needed(repo_path)
        return

    git_pull_safe(repo_path)


def git_pull_secondary_clone(repo_path: Path, target_name: str) -> None:
    if has_tracked_changes(repo_path):
        status = run_cmd(repo_path, ["git", "status", "--short"], check=False)
        log(f"⚠️ {repo_path} 是同远端预览目录，检测到本地修改，先 stash 再 pull：\n{status}")
        message = f"auto backup before {target_name} pull {datetime.now():%Y%m%d%H%M%S}"
        run_cmd(repo_path, ["git", "stash", "push", "-m", message])

    git_pull_safe(repo_path)


def git_pull_safe(repo_path: Path) -> None:
    ensure_clean_worktree(repo_path)
    log(f"🔄 git pull (--ff-only) @ {repo_path}")
    proc = subprocess.run(
        ["git", "pull", "--ff-only"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        output = (proc.stdout or "").strip()
        if output:
            log(output)
        return

    combined = f"{proc.stderr or ''}\n{proc.stdout or ''}"
    if "Not possible to fast-forward" not in combined and "divergent" not in combined.lower():
        raise ToolError(
            f"git pull --ff-only 失败: {repo_path}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )

    log(f"⚠️ 检测到分叉分支，改用 git pull --rebase @ {repo_path}")
    output = run_cmd(repo_path, ["git", "pull", "--rebase"])
    if output:
        log(output)


def classify_pull_result(stdout: str, stderr: str) -> str:
    text = f"{stdout}\n{stderr}".lower()
    if "already up to date" in text or "already up-to-date" in text:
        return "UP_TO_DATE"
    return "UPDATED"


def pull_project(name: str, info: dict) -> tuple[str, str, str]:
    path = Path(info["path"])
    if not path.is_dir():
        return name, "FAILED", f"❌ 路径不存在：{path}"
    if not is_git_repo(path):
        return name, "FAILED", f"❌ 不是 Git 仓库：{path}"

    branch = get_branch(path)
    if not has_upstream(path):
        return name, "FAILED", f"❌ branch={branch}，未配置上游分支，无法执行 git pull"

    try:
        proc = subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            timeout=GIT_TIMEOUT,
        )
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        if proc.returncode != 0:
            return name, "FAILED", f"❌ branch={branch}，pull 失败：\n{stderr or stdout or '未知错误'}"

        status = classify_pull_result(stdout, stderr)
        if status == "UP_TO_DATE":
            return name, "UP_TO_DATE", f"ℹ️ branch={branch}，已是最新"
        return name, "UPDATED", f"✅ branch={branch}，已更新：\n{stdout or stderr or 'Fast-forward'}"
    except subprocess.TimeoutExpired:
        return name, "FAILED", f"❌ branch={branch}，执行超时（>{GIT_TIMEOUT}s）"
    except Exception as exc:
        return name, "FAILED", f"❌ branch={branch}，运行异常：{exc!r}"


def pull_all_projects(selected: list[str] | None = None) -> int:
    selected = selected or []
    if selected:
        unknown = [name for name in selected if name not in PROJECTS]
        if unknown:
            log(f"❌ 未知项目：{', '.join(unknown)}")
            log(f"可选项目：{', '.join(PROJECTS.keys())}")
            return 1
        projects_to_run = {name: PROJECTS[name] for name in selected}
    else:
        projects_to_run = PROJECTS

    workers = min(MAX_WORKERS, len(projects_to_run)) or 1
    log(f"🚀 开始并行 git pull，共 {len(projects_to_run)} 个项目，并发数：{workers}\n")

    results: list[tuple[str, str]] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_name = {
            executor.submit(pull_project, name, info): name
            for name, info in projects_to_run.items()
        }
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                proj_name, status, msg = future.result()
            except Exception as exc:
                proj_name, status, msg = name, "FAILED", f"未捕获异常：{exc!r}"

            icon = {"UPDATED": "✅", "UP_TO_DATE": "ℹ️", "SKIPPED": "⚠️", "FAILED": "❌"}.get(status, "•")
            print(f"[{icon}] 项目：{proj_name}")
            print(msg)
            print("-" * 60)
            results.append((proj_name, status))

    status_map = {name: status for name, status in results}
    updated = [name for name in projects_to_run if status_map.get(name) == "UPDATED"]
    up_to_date = [name for name in projects_to_run if status_map.get(name) == "UP_TO_DATE"]
    skipped = [name for name in projects_to_run if status_map.get(name) == "SKIPPED"]
    failed = [name for name in projects_to_run if status_map.get(name) == "FAILED"]

    print("\n========== 总结 ==========")
    print(f"✅ 已更新：{len(updated)} 个 -> {', '.join(updated) if updated else '无'}")
    print(f"ℹ️ 已是最新：{len(up_to_date)} 个 -> {', '.join(up_to_date) if up_to_date else '无'}")
    print(f"⚠️ 已跳过：{len(skipped)} 个 -> {', '.join(skipped) if skipped else '无'}")
    print(f"❌ 失败：{len(failed)} 个 -> {', '.join(failed) if failed else '无'}")
    # 保持旧 pull_all_projects_v2.py 行为：失败项目会列在总结里，但不阻断整个工具退出码。
    return 0


def get_repo_paths(repo_path: Path, apk_name: str) -> RepoPaths:
    apk_dir = repo_path / "apk"
    return RepoPaths(
        root=repo_path,
        apk_dir=apk_dir,
        apk_path=apk_dir / apk_name,
        version_path=repo_path / "version.json",
    )


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
        tmp_path.unlink(missing_ok=True)


def with_cache_bust(url: str) -> str:
    joiner = "&" if "?" in url else "?"
    return f"{url}{joiner}_t={int(time.time())}"


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


def download_apk_to_repo1(target: ApkTarget, repo1_apk_path: Path) -> str:
    ensure_dir(repo1_apk_path.parent)
    session = build_session()
    download_failed = False

    for url in target.urls:
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


def update_version_json(path: Path, version: str) -> None:
    current = load_version_json(path)
    assets = current.get("assets")
    if not isinstance(assets, dict):
        assets = {"css": [], "js": []}
    assets.setdefault("css", [])
    assets.setdefault("js", [])
    atomic_write_json(path, {"version": version, "assets": assets})


def update_asset_query_versions(repo_path: Path, files: tuple[str, ...], version: str) -> list[str]:
    changed: list[str] = []
    if not files:
        return changed
    pattern = re.compile(r"(\.(?:js|css)(?:\?v=))\d{8,14}")
    for rel_path in files:
        path = repo_path / rel_path
        if not path.exists():
            log(f"⚠️ 静态资源版本文件不存在，跳过：{path}")
            continue
        old = path.read_text(encoding="utf-8")
        new = pattern.sub(rf"\g<1>{version}", old)
        if new != old:
            path.write_text(new, encoding="utf-8")
            changed.append(rel_path)
            log(f"✅ 静态资源版本号已更新：{rel_path} -> {version}")
    return changed


def format_version_date(version_date: str) -> str:
    if len(version_date) == 8 and version_date.isdigit():
        return f"{version_date[:4]}-{version_date[4:6]}-{version_date[6:8]}"
    return version_date


def update_download_info_dates(repo_path: Path, files: tuple[str, ...], version_date: str) -> list[str]:
    changed: list[str] = []
    if not files:
        return changed

    display_date = format_version_date(version_date)
    pattern = re.compile(
        r'(<span class="download-info-label" lang="downloadInfoUpdate">.*?</span>\s*'
        r'<span class="download-info-value">)([^<]*)(</span>)',
        re.DOTALL,
    )

    for rel_path in files:
        path = repo_path / rel_path
        if not path.exists():
            log(f"⚠️ 下载信息日期文件不存在，跳过：{path}")
            continue

        old = path.read_text(encoding="utf-8")
        new, count = pattern.subn(rf"\g<1>{display_date}\g<3>", old, count=1)
        if count == 0:
            log(f"⚠️ 未找到下载信息更新时间节点，跳过：{path}")
            continue
        if new != old:
            path.write_text(new, encoding="utf-8")
            changed.append(rel_path)
            log(f"✅ 下载信息更新时间已更新：{rel_path} -> {display_date}")
    return changed


def generate_version() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


def generate_tag() -> str:
    return datetime.now().strftime("v%y.%m.%d.%H%M")


def repo_has_staged_changes(repo_path: Path) -> bool:
    return subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo_path).returncode != 0


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
    tag = generate_tag()
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


def update_apk(target: ApkTarget) -> int:
    log(f"🚀 {target.name} 双目录 APK 自动更新开始...")
    repo1 = get_repo_paths(target.repo1, target.apk_name)
    repo2 = get_repo_paths(target.repo2, target.apk_name)

    repo1_remote = get_remote_url(repo1.root)
    repo2_remote = get_remote_url(repo2.root)
    same_remote = bool(repo1_remote and repo1_remote == repo2_remote)

    git_push_or_pull_before_update(repo1.root, target.name)
    if same_remote:
        git_pull_secondary_clone(repo2.root, target.name)
    else:
        git_push_or_pull_before_update(repo2.root, target.name)

    download_status = download_apk_to_repo1(target, repo1.apk_path)
    if download_status == "failed":
        log("❌ APK 下载失败，退出")
        return 1
    if download_status == "unchanged" and not target.update_when_unchanged:
        log("ℹ️ APK 无变化，跳过 version.json 更新和提交")
        return 0
    if download_status == "unchanged" and target.update_when_unchanged:
        log("ℹ️ APK 内容无变化，仍继续更新 version.json 并提交新版本号")

    version = generate_version()
    version_date = version[:8]
    log(f"✅ 生成版本号: {version}")
    update_version_json(repo1.version_path, version)
    asset_version_files = update_asset_query_versions(repo1.root, target.asset_version_files, version)
    download_info_date_files = update_download_info_dates(repo1.root, target.download_info_date_files, version_date)

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
            *asset_version_files,
            *download_info_date_files,
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

    if target.push_tag and committed1:
        git_tag_push(repo1.root, version)

    if same_remote:
        if committed1:
            git_pull_safe(repo2.root)
    elif committed1 or committed2:
        git_pull_safe(repo1.root)
        git_pull_safe(repo2.root)

    log("✅ 全流程完成 ✅")
    return 0


def sync_ty_sport(branch: str = "test") -> int:
    require_openvpn()

    repo_dir = Path(os.environ.get("REPO_DIR", "/Users/oncechen/IdeaProjects/sport"))
    origin_remote = os.environ.get("ORIGIN_REMOTE", "origin")
    gitlab_remote = os.environ.get("GITLAB_REMOTE", "gitlab")
    gitlab_url = "https://gitlab.com/DavidTsai99/ty_sport.git"

    if not (repo_dir / ".git").is_dir():
        raise ToolError(f"not a git repository: {repo_dir}")

    log(f"Repository: {repo_dir}")
    log(f"Branch: {branch}")

    run_cmd(repo_dir, ["git", "remote", "get-url", origin_remote])
    actual_gitlab_url = run_cmd(repo_dir, ["git", "remote", "get-url", gitlab_remote])
    if actual_gitlab_url != gitlab_url:
        raise ToolError(f"{gitlab_remote} remote points to '{actual_gitlab_url}', expected '{gitlab_url}'")

    current_branch = run_cmd(repo_dir, ["git", "branch", "--show-current"])
    if current_branch != branch:
        raise ToolError(f"current branch is '{current_branch}'. Please switch to '{branch}' first.")

    tracked_dirty = run_cmd(repo_dir, ["git", "status", "--porcelain=v1", "--untracked-files=no"])
    if tracked_dirty:
        print(tracked_dirty)
        raise ToolError("tracked files have uncommitted changes. Commit or stash them before pull/push.")

    untracked = run_cmd(repo_dir, ["git", "ls-files", "--others", "--exclude-standard"])
    if untracked:
        log("Untracked files found; they will not be pushed:")
        print(untracked)

    log("Remotes")
    print(run_cmd(repo_dir, ["git", "remote", "-v"], check=False))

    log(f"Pulling latest from {origin_remote}/{branch}")
    run_cmd(repo_dir, ["git", "pull", "--ff-only", origin_remote, branch])

    log(f"Fetching {gitlab_remote}/{branch} for safety check")
    fetch = subprocess.run(["git", "fetch", gitlab_remote, branch], cwd=repo_dir, check=False)
    if fetch.returncode != 0:
        log(f"{gitlab_remote}/{branch} does not exist or cannot be fetched. Creating it.")
        run_cmd(repo_dir, ["git", "push", gitlab_remote, f"{branch}:{branch}"])
        return 0

    remote_ref = f"{gitlab_remote}/{branch}"
    has_remote_ref = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/remotes/{remote_ref}"],
        cwd=repo_dir,
        check=False,
    ).returncode == 0

    if not has_remote_ref:
        log(f"{remote_ref} not found after fetch. Creating it.")
        run_cmd(repo_dir, ["git", "push", gitlab_remote, f"{branch}:{branch}"])
        return 0

    is_ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", remote_ref, branch],
        cwd=repo_dir,
        check=False,
    ).returncode == 0

    if is_ancestor:
        log(f"Pushing {branch} to {gitlab_remote}/{branch}")
        run_cmd(repo_dir, ["git", "push", gitlab_remote, f"{branch}:{branch}"])
    else:
        log(f"{remote_ref} has different history. Syncing by safe overwrite with --force-with-lease.")
        run_cmd(repo_dir, ["git", "push", f"--force-with-lease={branch}", gitlab_remote, f"{branch}:{branch}"])
    return 0


def is_process_running(pattern: str) -> bool:
    proc = subprocess.run(
        ["pgrep", "-if", pattern],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def open_app(app_name: str) -> bool:
    proc = subprocess.run(
        ["open", "-a", app_name],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        log(f"⚠️ 启动 {app_name} 失败：{err or 'unknown error'}")
        return False
    return True


def wait_for_process(pattern: str, seconds: int = 45) -> bool:
    for _ in range(seconds):
        if is_process_running(pattern):
            return True
        time.sleep(1)
    return is_process_running(pattern)


def ensure_app_running(label: str, pattern: str, app_names: list[str], wait_seconds: int = 45) -> None:
    if is_process_running(pattern):
        log(f"✅ {label} 已运行")
        return

    log(f"ℹ️ 未检测到 {label}，尝试自动启动...")
    for app_name in app_names:
        log(f"🚀 open -a {app_name}")
        if open_app(app_name) and wait_for_process(pattern, wait_seconds):
            log(f"✅ {label} 已启动")
            return

    raise ToolError(f"未检测到 {label} 正在运行，且自动启动失败。请手动打开/连接后再执行。")


def read_forticlient_vpn_state() -> dict:
    plist_path = (
        Path.home()
        / "Library/Group Containers/group.com.fortinet.forticlient.vpn/Library/Preferences/group.com.fortinet.forticlient.vpn.plist"
    )
    if not plist_path.exists():
        return {}
    try:
        with plist_path.open("rb") as fp:
            data = plistlib.load(fp)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def is_forticlient_vpn_connected() -> bool:
    state = read_forticlient_vpn_state()
    if state.get("IS_VPN_CONNECTED") not in (1, True, "1", "true", "TRUE"):
        return False
    return bool(state.get("SSLVPN_IP_ADDRESS") or state.get("kAppCurrentConnectedVPNName"))


def wait_for_forticlient_vpn(seconds: int = 90) -> bool:
    for _ in range(seconds):
        if is_forticlient_vpn_connected():
            return True
        time.sleep(1)
    return is_forticlient_vpn_connected()


def describe_forticlient_vpn_state() -> str:
    state = read_forticlient_vpn_state()
    name = state.get("kAppCurrentConnectedVPNName") or "unknown profile"
    ip = state.get("SSLVPN_IP_ADDRESS") or "no vpn ip"
    connected = state.get("IS_VPN_CONNECTED")
    return f"profile={name}, ip={ip}, connected={connected}"


def require_forticlient_vpn() -> None:
    ensure_app_running(
        "FortiClientVPN/FortiClient 软件",
        r"forticlientVPN|FortiClientVPN|FortiClient|FortiClientAgent|FortiTray",
        ["FortiClientVPN", "FortiClient", "forticlientVPN"],
    )

    if is_forticlient_vpn_connected():
        log(f"✅ FortiClientVPN 已连接：{describe_forticlient_vpn_state()}")
        return

    log("ℹ️ FortiClientVPN 软件已运行，但 VPN 尚未连接。请在 FortiClientVPN 点 Connect。")
    if wait_for_forticlient_vpn(90):
        log(f"✅ FortiClientVPN 已连接：{describe_forticlient_vpn_state()}")
        return

    raise ToolError(f"FortiClientVPN 软件已运行，但没有检测到 VPN 已连接：{describe_forticlient_vpn_state()}")


def latest_openvpn_log_event() -> str:
    log_file = Path.home() / "Library/Application Support/OpenVPN Connect/log/ovpn.log"
    if not log_file.exists():
        return ""

    try:
        lines = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return ""

    latest = ""
    for line in lines[-400:]:
        if "EVENT: CONNECTED" in line:
            latest = "CONNECTED"
        elif "EVENT: DISCONNECTED" in line or "EVENT: CONNECTION_TIMEOUT" in line or "EVENT: EXITING" in line:
            latest = "DISCONNECTED"
    return latest


def has_openvpn_tunnel() -> bool:
    # OpenVPN Connect keeps the app/agent alive even after disconnecting, and stale utun
    # interfaces may remain. The app log is the most reliable lightweight status source.
    return latest_openvpn_log_event() == "CONNECTED"


def wait_for_openvpn_tunnel(seconds: int = 90) -> bool:
    for _ in range(seconds):
        if has_openvpn_tunnel():
            return True
        time.sleep(1)
    return has_openvpn_tunnel()


def require_openvpn() -> None:
    profile_hint = "114.119.191.236"
    ensure_app_running(
        "OpenVPN Connect 软件",
        r"OpenVPN Connect|OpenVPN|openvpn",
        ["OpenVPN Connect", "OpenVPN"],
    )
    if has_openvpn_tunnel():
        log("✅ OpenVPN VPN 已连接")
        return

    log(f"ℹ️ OpenVPN 软件已运行，但 VPN 尚未连接。请在 OpenVPN Connect 点 Connect：{profile_hint}")
    if wait_for_openvpn_tunnel(90):
        log("✅ OpenVPN VPN 已连接")
        return
    raise ToolError("OpenVPN 软件已运行，但没有检测到 VPN tunnel。请确认已点击 Connect 并连接成功。")


def check_config() -> int:
    print(f"BASE_DIR: {BASE_DIR}")
    print("\nAPK targets:")
    ok = True
    for name, target in APK_TARGETS.items():
        print(f"- {name}: {target.apk_name}")
        print(f"  repo1: {target.repo1} {'OK' if target.repo1.exists() else 'MISSING'}")
        print(f"  repo2: {target.repo2} {'OK' if target.repo2.exists() else 'MISSING'}")
        for url in target.urls:
            print(f"  url: {url}")
        ok = ok and target.repo1.exists() and target.repo2.exists()

    print("\nPull projects:")
    for name, info in PROJECTS.items():
        path = Path(info["path"])
        print(f"- {name:16s} {'OK' if path.exists() else 'MISSING'} {path}")
        ok = ok and path.exists()
    return 0 if ok else 1


def prompt_for_command() -> list[str]:
    print("请选择要执行的功能：")
    print("  1. pull all projects")
    print("  2. update feiyu apk")
    print("  3. update 94chat apk")
    print("  4. sync sport -> ty_sport")
    print("  0. exit")
    print("也可以输入：pull / feiyu / 94chat / sync-ty")
    choice = input("请输入：").strip()
    mapping = {
        "": "pull",
        "1": "pull",
        "2": "feiyu",
        "3": "94chat",
        "4": "sync-ty",
        "0": "exit",
        "q": "exit",
        "quit": "exit",
        "exit": "exit",
    }
    command = mapping.get(choice.lower(), choice)
    if command == "exit":
        return ["exit"]
    return command.split()


def main(argv: list[str]) -> int:
    if not argv:
        argv = prompt_for_command()
    argv = normalize_argv(argv)

    command = normalize_command(argv[0])
    args = argv[1:]

    if command in ("-h", "--help", "help"):
        print_usage()
        return 0
    if command == "exit":
        log("已取消")
        return 0
    if command == "check":
        return check_config()

    require_forticlient_vpn()

    if command == "pull":
        return pull_all_projects(args)
    if command in APK_TARGETS:
        if args:
            log(f"⚠️ {command} 不需要额外参数，已忽略：{' '.join(args)}")
        return update_apk(APK_TARGETS[command])
    if command == "sync-ty":
        return sync_ty_sport(args[0] if args else "test")

    print(f"未知指令: {argv[0]}", file=sys.stderr)
    print_usage()
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except ToolError as exc:
        log(f"❌ 执行失败: {exc}")
        raise SystemExit(1)
    except KeyboardInterrupt:
        log("已中止")
        raise SystemExit(130)
