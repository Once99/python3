#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter

try:
    from urllib3.util.retry import Retry
except Exception:  # pragma: no cover
    Retry = None


# =================== 配置 ===================
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


try:
    requests.packages.urllib3.disable_warnings()
except Exception:
    pass


# =================== 数据结构 ===================
@dataclass(frozen=True)
class RepoPaths:
    root: Path
    apk_dir: Path
    apk_path: Path
    version_path: Path


# =================== 基础工具 ===================
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
    untracked = run_cmd(repo_path, ["git", "ls-files", "--others", "--exclude-standard"])
    return unstaged_clean and staged_clean and not untracked