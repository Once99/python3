#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
from datetime import datetime
import sys

# ============ 配置 ============
# 注意：下面两条路径请按你机器实际情况确认；
# 你给的路径看起来像是 "/Applications/XAMPP/xamppfiles/htdocs"，但原文是 "Applcations/htcos"
SRC_DIR  = "/Applications/XAMPP/xamppfiles/htdocs/feiyu-bind"  # ← 拷贝来源目录
REPO_PATH = "/Users/oncechen/IdeaProjects/feiyu-site"          # ← Git 仓库根目录
DEST_DIR  = os.path.join(REPO_PATH, "feiyu-bind")              # ← 拷贝到仓库里的这个目录

# 提交信息前缀（可自定义）
COMMIT_PREFIX = "sync feiyu-bind"

# ============ 工具函数 ============
def run_cmd(cmd, cwd=None, check=True):
    """运行命令的辅助函数，打印并返回 stdout。"""
    print("➜", " ".join(cmd), f"(cwd={cwd or os.getcwd()})")
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if p.stdout.strip():
        print(p.stdout.strip())
    if p.stderr.strip():
        # 一些 git 命令在非致命情况下也会输出 stderr（比如 Pull 时的提示）
        print(p.stderr.strip())
    if check and p.returncode != 0:
        raise SystemExit(p.returncode)
    return p

def ensure_repo(path):
    """检查是否为 Git 仓库"""
    try:
        p = run_cmd(["git", "rev-parse", "--is-inside-work-tree"], cwd=path, check=False)
        return p.returncode == 0 and "true" in (p.stdout or "").lower()
    except Exception:
        return False

def copy_merge(src, dst):
    """
    覆盖式拷贝：将 src 的内容复制到 dst，
    已存在文件会被覆盖，其他文件保留。
    """
    if not os.path.isdir(src):
        print(f"❌ 来源目录不存在：{src}")
        sys.exit(1)
    os.makedirs(dst, exist_ok=True)
    for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        target_root = os.path.join(dst, rel) if rel != "." else dst
        os.makedirs(target_root, exist_ok=True)
        # 复制文件
        for fn in files:
            s = os.path.join(root, fn)
            d = os.path.join(target_root, fn)
            # 确保目标父目录存在
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, d)
            print(f"📄 {os.path.relpath(d, REPO_PATH)}  ←  {os.path.relpath(s, src)}")
        # 创建子目录（文件会在下一轮循环拷）
        for dn in dirs:
            os.makedirs(os.path.join(target_root, dn), exist_ok=True)

# ============ 主流程 ============
def main():
    print("🚀 开始同步 feiyu-bind 并打 Tag")

    # 0) 校验仓库
    if not ensure_repo(REPO_PATH):
        print(f"❌ 不是一个 Git 仓库：{REPO_PATH}")
        sys.exit(1)

    # 1) 拷贝目录（覆盖式）
    print(f"📦 拷贝目录：\n  from: {SRC_DIR}\n  to  : {DEST_DIR}")
    copy_merge(SRC_DIR, DEST_DIR)

    # 2) git pull（避免落后远端）
    print("🔄 git pull ...")
    run_cmd(["git", "pull"], cwd=REPO_PATH)

    # 3) git add
    print("➕ git add feiyu-bind ...")
    rel_path = os.path.relpath(DEST_DIR, REPO_PATH)
    run_cmd(["git", "add", rel_path], cwd=REPO_PATH)

    # 显示即将提交的变更
    print("📋 变更清单：")
    run_cmd(["git", "status", "--porcelain"], cwd=REPO_PATH, check=False)

    # 如果没有 staged 变更，则退出
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=REPO_PATH)
    if staged.returncode == 0:
        print("ℹ️ 没有需要提交的变更，后续流程跳过（无 commit / tag）")
        sys.exit(0)

    # 4) git commit
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_msg = f"{COMMIT_PREFIX} - {ts}"
    print(f"📝 git commit -m \"{commit_msg}\"")
    run_cmd(["git", "commit", "-m", commit_msg], cwd=REPO_PATH)

    print("⬆️ git push ...")
    run_cmd(["git", "push"], cwd=REPO_PATH)

    # 5) git tag（用时间戳，避免重复）
    tag = "v" + datetime.now().strftime("%Y.%m.%d.%H%M")
    print(f"🏷️ 打 tag：{tag}")
    run_cmd(["git", "tag", tag], cwd=REPO_PATH)
    print("⬆️ 推送 tag ...")
    run_cmd(["git", "push", "origin", tag], cwd=REPO_PATH)

    print("✅ 完成！")

if __name__ == "__main__":
    main()