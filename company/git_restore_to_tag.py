#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
from datetime import datetime

def run(cmd, cwd=None, check=False, text=True):
    # 统一打印 + 捕获输出，失败时也把 stdout/stderr 打出来
    print("👉", " ".join(cmd))
    p = subprocess.run(cmd, cwd=cwd, text=text, capture_output=True)
    if p.stdout:
        print(p.stdout, end="")
    if p.returncode != 0 and p.stderr:
        print(p.stderr, end="")
    if check and p.returncode != 0:
        raise subprocess.CalledProcessError(p.returncode, cmd, output=p.stdout, stderr=p.stderr)
    return p

def hard_reset_to_tag(path, tag, push_force=False):
    b = current_branch(path)
    info(f"当前分支：{b}")
    info(f"将把分支 {b} 强制重置到 tag {tag} 对应提交")
    run(["git", "reset", "--hard", tag], cwd=path, check=True)
    ok("本地已重置到 tag。")

    if not push_force:
        return

    remote = input("远端名（默认 origin）: ").strip() or "origin"
    if confirm("需要强制推送到远端（会改写远端历史）吗？", default=False):
        try:
            # 先尝试更安全的 --force-with-lease
            run(["git", "push", remote, b, "--force-with-lease"], cwd=path, check=True)
            ok("已强制推送到远端（--force-with-lease）。")
        except subprocess.CalledProcessError as e:
            print("\n❌ 推送失败。常见原因：")
            print("   1) 目标分支是受保护分支（Protected branch），禁止 force push；")
            print("   2) 你没有足够权限（需 Maintainer 才能改保护/强推）；")
            print("   3) 远端名/分支名不对；")
            print("   4) 服务器的 pre-receive hook 拒绝。")

            err = ((e.stderr or "") + (e.output or "")).lower()
            if "protected branch" in err or "not allowed to force push" in err:
                print("👉 侦测到可能是受保护分支导致。")

            # 提供降级方案：建立并推送回退分支 rollback/<tag>
            rb = f"rollback/{tag}"
            if confirm(f"\n是否创建并推送备选分支 {rb}（用于发 MR 合回 {b}）？", default=True):
                # 在当前提交上创建/重置该分支并推送
                run(["git", "checkout", "-B", rb], cwd=path, check=True)
                run(["git", "push", "-u", remote, rb], cwd=path, check=True)
                ok(f"已推送 {rb}。请到 GitLab 发起 MR：{rb} → {b}")
            else:
                print("ℹ️ 你也可以在 GitLab 解除分支保护后，再重试强推。")

def die(msg):
    print(f"❌ {msg}")
    sys.exit(1)

def ok(msg):
    print(f"✅ {msg}")

def info(msg):
    print(f"ℹ️  {msg}")

def confirm(prompt, default=False):
    ans = input(f"{prompt} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
    if ans == "" and default:
        return True
    return ans in ("y", "yes")

def git_available():
    try:
        run(["git", "--version"])
        return True
    except Exception:
        return False

def is_git_repo(path):
    p = run(["git", "rev-parse", "--is-inside-work-tree"], cwd=path)
    return p.returncode == 0 and p.stdout.strip() == "true"

def current_branch(path):
    p = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=path)
    return p.stdout.strip()

def has_uncommitted_changes(path):
    # 包含 staged/unstaged/未追踪文件
    p = run(["git", "status", "--porcelain"], cwd=path)
    return p.stdout.strip() != ""

def tag_exists(path, tag):
    p = run(["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"], cwd=path)
    return p.returncode == 0

def get_tag_commit(path, tag):
    p = run(["git", "rev-list", "-n", "1", tag], cwd=path)
    if p.returncode != 0:
        return None
    return p.stdout.strip()

def stash_changes(path):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    p = run(["git", "stash", "push", "-u", "-m", f"auto-stash {stamp}"], cwd=path)
    print(p.stdout or p.stderr)

def checkout_tag(path, tag):
    info(f"切换到 tag：{tag}（detached HEAD）")
    run(["git", "checkout", f"tags/{tag}"], cwd=path, check=True)
    ok("已切换到 tag（detached HEAD）。")

def create_branch_from_tag(path, tag, branch_name=None):
    if not branch_name:
        branch_name = f"restore/{tag}-{datetime.now().strftime('%Y%m%d-%H%M')}"
    info(f"在 tag {tag} 上创建分支：{branch_name}")
    run(["git", "checkout", "-b", branch_name, f"tags/{tag}"], cwd=path, check=True)
    ok(f"已创建并切换到分支：{branch_name}")

def hard_reset_to_tag(path, tag, push_force=False):
    b = current_branch(path)
    info(f"当前分支：{b}")
    info(f"将把分支 {b} 强制重置到 tag {tag} 对应提交")
    run(["git", "reset", "--hard", tag], cwd=path, check=True)
    ok("本地已重置到 tag。")
    if push_force:
        if confirm("需要强制推送到远端（会改写远端历史）吗？", default=False):
            run(["git", "push", "origin", b, "--force"], cwd=path, check=True)
            ok("已强制推送到远端。")
        else:
            info("已跳过强制推送。")

def main():
    if not git_available():
        die("未检测到 git，请先安装。")

    repo_path = input("📁 请输入本地仓库路径（留空=当前目录）: ").strip() or os.getcwd()
    repo_path = os.path.abspath(repo_path)
    if not os.path.isdir(repo_path):
        die(f"路径不存在：{repo_path}")
    if not is_git_repo(repo_path):
        die(f"不是 Git 仓库：{repo_path}")

    # 可选：先拉一下
    if confirm("是否先执行 `git fetch --all --tags` 同步远端标签？", default=True):
        run(["git", "fetch", "--all", "--tags"], cwd=repo_path, check=True)
        ok("已同步远端标签。")

    tag = input("🏷 请输入目标 tag 名称（例如 v2025.08.01.1530）: ").strip()
    if not tag:
        die("未输入 tag。")
    if not tag_exists(repo_path, tag):
        die(f"本地未找到该 tag：{tag}（可先执行 fetch --tags 或检查拼写）")
    commit = get_tag_commit(repo_path, tag)
    info(f"tag {tag} 对应提交：{commit}")

    # 未提交改动处理
    if has_uncommitted_changes(repo_path):
        info("检测到未提交的改动（包含未跟踪文件）。")
        if confirm("是否自动执行 `git stash -u` 暂存当前改动？", default=True):
            stash_changes(repo_path)
        else:
            die("为避免数据丢失，已中止。请提交或清理工作区后重试。")

    print("\n请选择模式：")
    print("  1) checkout 仅切到 tag（detached HEAD，适合查看/打包）")
    print("  2) branch   在 tag 上创建新分支（继续开发）")
    print("  3) reset    将当前分支重置到 tag（可选强推远端）")
    choice = (input("👉 请输入 1/2/3（默认=2）: ").strip() or "2")

    if choice == "1":
        checkout_tag(repo_path, tag)
    elif choice == "2":
        default_branch_name = f"restore/{tag}-{datetime.now().strftime('%Y%m%d-%H%M')}"
        bn = input(f"请输入新分支名（默认：{default_branch_name}）: ").strip() or default_branch_name
        create_branch_from_tag(repo_path, tag, bn)
    elif choice == "3":
        pf = confirm("重置后是否准备强制推送远端？（会改写远端历史）", default=False)
        hard_reset_to_tag(repo_path, tag, push_force=pf)
    else:
        die("无效选项。")

    ok("完成。")

if __name__ == "__main__":
    main()