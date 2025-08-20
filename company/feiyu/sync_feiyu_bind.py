#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, shutil, subprocess, sys, argparse, webbrowser
from datetime import datetime

SRC_DIR   = "/Applications/XAMPP/xamppfiles/htdocs/feiyu-bind"
REPO_PATH = "/Users/oncechen/IdeaProjects/feiyu-site"
DEST_DIR  = os.path.join(REPO_PATH, "feiyu-bind")

BRANCH_EXPECT = "master"
COMMIT_PREFIX = "sync feiyu-bind"
EXCLUDES = {".DS_Store"}

GITLAB_PROJECT_URL = "https://git.easydevops.net/it/java-feiyu/feiyu-site"

def run_cmd(cmd, cwd=None, check=True):
    print("➜", " ".join(cmd), f"(cwd={cwd or os.getcwd()})")
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if p.stdout.strip(): print(p.stdout.strip())
    if p.stderr.strip(): print(p.stderr.strip())
    if check and p.returncode != 0: sys.exit(p.returncode)
    return p

def ensure_repo(path):
    p = run_cmd(["git", "rev-parse", "--is-inside-work-tree"], cwd=path, check=False)
    return p.returncode == 0 and "true" in (p.stdout or "").lower()

def current_branch(path):
    p = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=path)
    return (p.stdout or "").strip()

def should_exclude(name: str) -> bool:
    return name in EXCLUDES

def copy_merge(src, dst, dry=False):
    if not os.path.isdir(src):
        print(f"❌ 来源目录不存在：{src}"); sys.exit(1)
    os.makedirs(dst, exist_ok=True)
    for root, _, files in os.walk(src):
        rel = os.path.relpath(root, src)
        target_root = os.path.join(dst, rel) if rel != "." else dst
        os.makedirs(target_root, exist_ok=True)
        for fn in files:
            if should_exclude(fn): continue
            s = os.path.join(root, fn)
            d = os.path.join(target_root, fn)
            os.makedirs(os.path.dirname(d), exist_ok=True)
            print(f"📄 COPY  {os.path.relpath(s, src)}  ->  {os.path.relpath(d, dst)}")
            if not dry:
                shutil.copy2(s, d)

def mirror_cleanup(src, dst, dry=False):
    for root, dirs, files in os.walk(dst, topdown=False):
        rel = os.path.relpath(root, dst)
        src_root = os.path.join(src, rel) if rel != "." else src
        for fn in files:
            if should_exclude(fn): continue
            dfile = os.path.join(root, fn)
            sfile = os.path.join(src_root, fn)
            if not os.path.exists(sfile):
                print(f"🗑 DEL   {os.path.relpath(dfile, dst)}")
                if not dry: os.remove(dfile)
        if root != dst and not os.listdir(root):
            print(f"🗂 RMDIR {os.path.relpath(root, dst)}")
            if not dry: os.rmdir(root)

def create_and_push_tag():
    """输入 tag（或用默认），创建并 push，最后打开项目页"""
    default_tag = "v" + datetime.now().strftime("%Y.%m.%d.%H%M")
    try:
        tag = input(f"🏷️ 请输入 tag 名（回车用默认 {default_tag}）：").strip() or default_tag
    except (EOFError, KeyboardInterrupt):
        tag = default_tag
        print(f"\nℹ️ 非交互/已中断输入，使用默认 tag：{tag}")

    # 检查是否已存在
    exists = subprocess.run(["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"],
                            cwd=REPO_PATH, capture_output=True, text=True)
    if exists.returncode == 0:
        print(f"❌ Tag 已存在：{tag}，请更换名称后重试。")
        sys.exit(1)

    run_cmd(["git", "tag", tag], cwd=REPO_PATH)
    run_cmd(["git", "push", "origin", tag], cwd=REPO_PATH)
    print(f"✅ 已创建并推送 tag：{tag}")

    # 打开项目页面
    try:
        webbrowser.open(GITLAB_PROJECT_URL)
        print(f"🌐 已打开：{GITLAB_PROJECT_URL}")
    except Exception as e:
        print(f"⚠️ 无法自动打开浏览器：{e}")

def main():
    ap = argparse.ArgumentParser(description="Sync feiyu-bind and tag")
    ap.add_argument("--mirror", action="store_true", help="镜像同步（删除目标中多余文件）")
    ap.add_argument("--dry-run", action="store_true", help="预演模式：不实际改动")
    args = ap.parse_args()

    print("🚀 同步 feiyu-bind", "(DRY-RUN)" if args.dry_run else "")
    if not ensure_repo(REPO_PATH):
        print(f"❌ 非 git 仓库：{REPO_PATH}"); sys.exit(1)

    br = current_branch(REPO_PATH)
    if br != BRANCH_EXPECT:
        print(f"⚠️ 当前分支是 {br}，期望 {BRANCH_EXPECT}。可修改 BRANCH_EXPECT 或手动切换。")
        # 如需强制退出，取消注释下一行
        # sys.exit(1)

    # 工作区/暂存区检查（仅提示，不阻断）
    run_cmd(["git", "diff", "--quiet"], cwd=REPO_PATH, check=False)
    run_cmd(["git", "diff", "--cached", "--quiet"], cwd=REPO_PATH, check=False)

    # 同步文件
    print(f"📦 From: {SRC_DIR}\n📦  To: {DEST_DIR}")
    copy_merge(SRC_DIR, DEST_DIR, dry=args.dry_run)
    if args.mirror: mirror_cleanup(SRC_DIR, DEST_DIR, dry=args.dry_run)

    if args.dry_run:
        print("🔎 DRY-RUN 结束（未写入、未提交、未打 tag）")
        return

    # add / status
    rel = os.path.relpath(DEST_DIR, REPO_PATH)
    run_cmd(["git", "add", rel], cwd=REPO_PATH)
    run_cmd(["git", "status", "--porcelain"], cwd=REPO_PATH, check=False)

    # 判断是否有 staged 变更
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=REPO_PATH)

    if staged.returncode != 0:
        # 有变更 → commit & push
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        msg = f"{COMMIT_PREFIX} - {ts}"
        run_cmd(["git", "commit", "-m", msg], cwd=REPO_PATH)
        run_cmd(["git", "push"], cwd=REPO_PATH)
        print("✅ 已提交并推送。")
    else:
        print("ℹ️ 无变更，跳过 commit。")

    # 无论是否有变更，都进入 tag 流程
    create_and_push_tag()

if __name__ == "__main__":
    main()