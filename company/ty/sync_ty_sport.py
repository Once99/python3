#!/usr/bin/env python3
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_DIR = os.environ.get("REPO_DIR", "/Users/oncechen/IdeaProjects/sport")
BRANCH = sys.argv[1] if len(sys.argv) > 1 else "test"
ORIGIN_REMOTE = os.environ.get("ORIGIN_REMOTE", "origin")
GITLAB_REMOTE = os.environ.get("GITLAB_REMOTE", "gitlab")
GITLAB_URL = "https://gitlab.com/DavidTsai99/ty_sport.git"


def log(message):
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")


def fail(message, code=1):
    print(f"\nERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def run(args, check=True, capture=False):
    kwargs = {
        "cwd": REPO_DIR,
        "text": True,
    }
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    result = subprocess.run(args, **kwargs)
    if check and result.returncode != 0:
        if capture and result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        fail(f"command failed: {' '.join(args)}", result.returncode)
    return result


def git_output(*args):
    result = run(["git", *args], capture=True)
    return result.stdout.strip()


def is_process_running(pattern):
    result = subprocess.run(
        ["pgrep", "-if", pattern],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def open_app(app_name):
    result = subprocess.run(
        ["open", "-a", app_name],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        log(f"⚠️ 启动 {app_name} 失败：{err or 'unknown error'}")
        return False
    return True


def wait_for_process(pattern, seconds=45):
    for _ in range(seconds):
        if is_process_running(pattern):
            return True
        time.sleep(1)
    return is_process_running(pattern)


def latest_openvpn_log_event():
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


def has_openvpn_tunnel():
    # OpenVPN Connect keeps the app/agent alive even after disconnecting, and stale utun
    # interfaces may remain. The app log is the most reliable lightweight status source.
    return latest_openvpn_log_event() == "CONNECTED"


def wait_for_openvpn_tunnel(seconds=90):
    for _ in range(seconds):
        if has_openvpn_tunnel():
            return True
        time.sleep(1)
    return has_openvpn_tunnel()


def require_openvpn():
    profile_hint = "114.119.191.236"
    pattern = r"OpenVPN Connect|OpenVPN|openvpn"
    if not is_process_running(pattern):
        log("ℹ️ 未检测到 OpenVPN，尝试自动启动...")
        for app_name in ["OpenVPN Connect", "OpenVPN"]:
            log(f"🚀 open -a {app_name}")
            if open_app(app_name) and wait_for_process(pattern):
                break

    if not is_process_running(pattern):
        fail("未检测到 OpenVPN 正在运行，且自动启动失败。请手动打开 OpenVPN Connect。")

    if has_openvpn_tunnel():
        log("✅ OpenVPN VPN 已连接")
        return

    log(f"ℹ️ OpenVPN 软件已运行，但 VPN 尚未连接。请在 OpenVPN Connect 点 Connect：{profile_hint}")
    if wait_for_openvpn_tunnel(90):
        log("✅ OpenVPN VPN 已连接")
        return
    fail("OpenVPN 软件已运行，但没有检测到 VPN tunnel。请确认已点击 Connect 并连接成功。")


def ensure_remote(name):
    result = run(["git", "remote", "get-url", name], check=False, capture=True)
    if result.returncode != 0:
        fail(f"missing remote: {name}")
    return result.stdout.strip()


def main():
    require_openvpn()

    if not os.path.isdir(os.path.join(REPO_DIR, ".git")):
        fail(f"not a git repository: {REPO_DIR}")

    log(f"Repository: {REPO_DIR}")
    log(f"Branch: {BRANCH}")

    ensure_remote(ORIGIN_REMOTE)
    actual_gitlab_url = ensure_remote(GITLAB_REMOTE)
    if actual_gitlab_url != GITLAB_URL:
        fail(f"{GITLAB_REMOTE} remote points to '{actual_gitlab_url}', expected '{GITLAB_URL}'")

    current_branch = git_output("branch", "--show-current")
    if current_branch != BRANCH:
        fail(f"current branch is '{current_branch}'. Please switch to '{BRANCH}' first.")

    tracked_dirty = git_output("status", "--porcelain=v1", "--untracked-files=no")
    if tracked_dirty:
        print(tracked_dirty)
        fail("tracked files have uncommitted changes. Commit or stash them before pull/push.")

    untracked = git_output("ls-files", "--others", "--exclude-standard")
    if untracked:
        log("Untracked files found; they will not be pushed:")
        print(untracked)

    log("Remotes")
    run(["git", "remote", "-v"])

    log(f"Pulling latest from {ORIGIN_REMOTE}/{BRANCH}")
    run(["git", "pull", "--ff-only", ORIGIN_REMOTE, BRANCH])

    log(f"Fetching {GITLAB_REMOTE}/{BRANCH} for safety check")
    fetch = run(["git", "fetch", GITLAB_REMOTE, BRANCH], check=False)
    if fetch.returncode != 0:
        log(f"{GITLAB_REMOTE}/{BRANCH} does not exist or cannot be fetched. Creating it.")
        run(["git", "push", GITLAB_REMOTE, f"{BRANCH}:{BRANCH}"])
        log("Done")
        return

    remote_ref = f"{GITLAB_REMOTE}/{BRANCH}"
    has_remote_ref = run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/remotes/{remote_ref}"],
        check=False,
    ).returncode == 0

    if not has_remote_ref:
        log(f"{remote_ref} not found after fetch. Creating it.")
        run(["git", "push", GITLAB_REMOTE, f"{BRANCH}:{BRANCH}"])
    else:
        is_ancestor = run(
            ["git", "merge-base", "--is-ancestor", remote_ref, BRANCH],
            check=False,
        ).returncode == 0
        if is_ancestor:
            log(f"Pushing {BRANCH} to {GITLAB_REMOTE}/{BRANCH}")
            run(["git", "push", GITLAB_REMOTE, f"{BRANCH}:{BRANCH}"])
        else:
            log(f"{remote_ref} has different history. Syncing by safe overwrite with --force-with-lease.")
            run(["git", "push", f"--force-with-lease={BRANCH}", GITLAB_REMOTE, f"{BRANCH}:{BRANCH}"])

    log("Done")


if __name__ == "__main__":
    main()
