#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from urllib.parse import urlparse

# 默认 clone 根目录
DEFAULT_BASE_DIR = "/Users/oncechen/IdeaProjects"

def run(cmd, check=True):
    print(f"👉 正在执行：{' '.join(cmd)}")
    result = subprocess.run(cmd)
    if check and result.returncode != 0:
        sys.exit(result.returncode)

def guess_repo_name(repo_url: str) -> str:
    """
    从仓库 URL 推断项目名
    例: https://gitlab.com/user/repo.git -> repo
        git@gitlab.com:user/repo.git    -> repo
    """
    name = os.path.basename(urlparse(repo_url).path)
    if name.endswith(".git"):
        name = name[:-4]
    return name

def main():
    repo_url = input("📦 请输入 Git 仓库地址（例如 https:// 或 git@...）: ").strip()
    if not repo_url:
        print("❌ 仓库地址不能为空")
        sys.exit(1)

    # 推断默认目录名
    default_name = guess_repo_name(repo_url)
    target_name = input(f"📂 请输入目标目录名（默认: {default_name}）: ").strip() or default_name

    branch = input("🌿 请输入分支名（留空=默认分支）: ").strip()

    # 拼接完整路径
    target_dir = os.path.join(DEFAULT_BASE_DIR, target_name)
    os.makedirs(DEFAULT_BASE_DIR, exist_ok=True)

    cmd = ["git", "clone"]
    if branch:
        cmd += ["-b", branch]
    cmd += [repo_url, target_dir]

    run(cmd)
    print(f"\n✅ 克隆完成！代码已放在: {target_dir}")

if __name__ == "__main__":
    main()