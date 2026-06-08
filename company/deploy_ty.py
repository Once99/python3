#!/usr/bin/env python3
"""Pull the sport repo, start VPN, and open or trigger the system-ui Jenkins deploy."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import getpass
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DEFAULT_REPO = Path("/Users/oncechen/IdeaProjects/sport")
DEFAULT_REPORT_REPO = Path("/Users/oncechen/IdeaProjects/ty_sport_test")
DEFAULT_CLIENT_REPORT_REPO = Path("/Users/oncechen/IdeaProjects/ty_client_test")
DEFAULT_REPORT_AUTHOR = "Ayea"
DEFAULT_REPORT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "reports"
DEFAULT_JENKINS = "https://jenkins.helpom.com/"
DEFAULT_JOB = "system-ui"
DEFAULT_CLIENT_JOB = "if-sport-ui"
DEFAULT_VPN_APPS = ["OpenVPN Connect", "OpenVPN"]
DEFAULT_VPN_WAIT_HOST = "git.helpom.com"
DEFAULT_VPN_WAIT_PORT = 80
DEFAULT_TY_SPORT_REMOTE = "gitlab"
DEFAULT_SPORT_PUSH_REMOTE = "origin"
DEFAULT_SYNC_AUTHOR_NAME = "loki"
DEFAULT_SYNC_AUTHOR_EMAIL = "webm@dc66.net"
DEFAULT_COMMIT_MESSAGE = ""
DEFAULT_SYNC_EXCLUDE_PATHS = [
    "ruoyi-ui/.env.development.local",
]
DEFAULT_CLIENT_SYNC_EXCLUDE_PATHS = [
    "docs/",
]
DEFAULT_CLIENT_SOURCE_REPO = Path("/Users/oncechen/IdeaProjects/ty_client_test")
DEFAULT_CLIENT_TARGET_REPO = Path("/Users/oncechen/IdeaProjects/if_sport_ui")
DEFAULT_CLIENT_REMOTE = "origin"


def log(message: str) -> None:
    print(f"[sport-deploy] {message}", flush=True)


def fail(message: str, code: int = 1) -> None:
    print(f"[sport-deploy] ERROR: {message}", file=sys.stderr, flush=True)
    raise SystemExit(code)


def run(cmd: list[str], cwd: Path | None = None, dry_run: bool = False) -> subprocess.CompletedProcess[str]:
    where = f" (cwd={cwd})" if cwd else ""
    log("$ " + " ".join(cmd) + where)
    if dry_run:
        return subprocess.CompletedProcess(cmd, 0, "", "")
    result = subprocess.run(cmd, cwd=cwd, check=False, text=True, capture_output=True)
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return result


def git_output(repo: Path, args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def current_branch(repo: Path) -> str:
    branch = git_output(repo, ["branch", "--show-current"])
    return branch or "HEAD"


def ensure_clean(repo: Path, strict_clean: bool) -> None:
    status = git_output(repo, ["status", "--porcelain"])
    if status and strict_clean:
        fail(
            "sport repo has uncommitted changes. Commit/stash them first, or rerun without --strict-clean."
        )
    if status:
        log("sport repo has uncommitted changes; continuing because --strict-clean was not set.")


def git_pull(repo: Path, remote: str, branch: str | None, strict_clean: bool, dry_run: bool) -> None:
    if not (repo / ".git").exists():
        fail(f"{repo} is not a git repository")

    ensure_clean(repo, strict_clean)
    active_branch = branch or current_branch(repo)
    log(f"pulling {remote}/{active_branch} in {repo}")
    result = run(["git", "pull", "--ff-only", remote, active_branch], cwd=repo, dry_run=dry_run)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)


def pull_ty_sport_worktree(repo: Path, branch: str | None, dry_run: bool) -> None:
    if not (repo / ".git").exists():
        fail(f"{repo} is not a git repository")

    status = git_output(repo, ["status", "--porcelain"])
    if status:
        print(status)
        fail("ty_sport_test repo has uncommitted changes. Commit/stash them before syncing.")

    active_branch = branch or current_branch(repo)
    log(f"pulling latest ty_sport_test branch: origin/{active_branch}")
    result = run(["git", "pull", "--ff-only", "origin", active_branch], cwd=repo, dry_run=dry_run)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)


def has_worktree_changes(repo: Path) -> bool:
    return bool(git_output(repo, ["status", "--porcelain"]))


def has_path_change(repo: Path, path: str) -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", path],
        cwd=repo,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
    return bool(result.stdout.strip())


def unmerged_paths(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=U"],
        cwd=repo,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def restore_sync_excluded_paths(repo: Path, dry_run: bool) -> None:
    for path in DEFAULT_SYNC_EXCLUDE_PATHS:
        if has_path_change(repo, path):
            log(f"excluding from sport sync: {path}")
            run(["git", "restore", "--source=HEAD", "--staged", "--worktree", "--", path], cwd=repo, dry_run=dry_run)


def ensure_remote(repo: Path, remote: str) -> str:
    try:
        return git_output(repo, ["remote", "get-url", remote])
    except subprocess.CalledProcessError:
        fail(f"missing git remote: {remote}")


def push_sport_branch(repo: Path, remote: str, branch: str, dry_run: bool) -> None:
    log(f"running git push inside sport: {remote} {branch}:{branch}")
    run(["git", "push", remote, f"{branch}:{branch}"], cwd=repo, dry_run=dry_run)


def sync_title_date(today: dt.date | None = None) -> str:
    value = today or dt.date.today()
    return f"{value:%m/%d}"


def collect_sync_commit_details(repo: Path, base_ref: str, target_ref: str) -> tuple[list[str], list[str]]:
    result = subprocess.run(
        [
            "git",
            "log",
            "--pretty=format:%x1e%s",
            "--name-only",
            "--reverse",
            f"{base_ref}..{target_ref}",
            "--",
            "ruoyi-ui",
        ],
        cwd=repo,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)

    subjects: list[str] = []
    files: list[str] = []
    for block in result.stdout.split("\x1e"):
        block = block.strip()
        if not block:
            continue
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        subject = re.sub(r"\s+", " ", lines[0]).strip()
        if subject and not subject.lower().startswith("merge"):
            append_once(subjects, subject)
        files.extend(lines[1:])
    return subjects, files


def collect_sync_subjects(repo: Path, base_ref: str, target_ref: str) -> list[str]:
    subjects, _ = collect_sync_commit_details(repo, base_ref, target_ref)
    return subjects


def staged_sync_files(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", "ruoyi-ui", "docs"],
        cwd=repo,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def has_sync_diff(repo: Path, base_ref: str, target_ref: str) -> bool:
    result = subprocess.run(
        ["git", "diff", "--quiet", base_ref, target_ref, "--", "ruoyi-ui"],
        cwd=repo,
        check=False,
    )
    if result.returncode in {0, 1}:
        return result.returncode == 1
    raise subprocess.CalledProcessError(result.returncode, result.args)


def build_sync_commit_message(repo: Path, base_ref: str, target_ref: str) -> str:
    subjects = collect_sync_subjects(repo, base_ref, target_ref)
    files = staged_sync_files(repo)
    items = summarize_ty_work(subjects, files)
    if not items:
        return "同步 ty_sport 前端更新"

    lines: list[str] = ["",]
    lines.extend(items)
    return "\n".join(lines).lstrip()


def message_args(message: str) -> list[str]:
    paragraphs = [part.strip() for part in message.splitlines() if part.strip()]
    if not paragraphs:
        fail("commit message cannot be empty")
    args: list[str] = []
    for paragraph in paragraphs:
        args.extend(["-m", paragraph])
    return args


def commit_squashed_changes(
    repo: Path,
    message: str,
    author_name: str,
    author_email: str,
    dry_run: bool,
) -> None:
    if not has_worktree_changes(repo):
        log("no ty_sport changes to commit.")
        return

    author = f"{author_name} <{author_email}>"
    run(
        [
            "git",
            "-c",
            f"user.name={author_name}",
            "-c",
            f"user.email={author_email}",
            "commit",
            f"--author={author}",
            *message_args(message),
        ],
        cwd=repo,
        dry_run=dry_run,
    )


def sync_ty_sport_to_sport(
    repo: Path,
    source_repo: Path,
    branch: str | None,
    ty_remote: str,
    sport_remote: str,
    commit_message: str,
    author_name: str,
    author_email: str,
    dry_run: bool,
) -> None:
    if not (repo / ".git").exists():
        fail(f"{repo} is not a git repository")

    active_branch = branch or current_branch(repo)
    ensure_remote(repo, sport_remote)

    if not (source_repo / ".git").exists():
        fail(f"{source_repo} is not a git repository")

    if not dry_run and current_branch(repo) != active_branch:
        fail(f"current branch is '{current_branch(repo)}'. Please switch to '{active_branch}' first.")
    if not dry_run and current_branch(source_repo) != active_branch:
        fail(f"ty_sport_test current branch is '{current_branch(source_repo)}'. Please switch to '{active_branch}' first.")

    status = git_output(repo, ["status", "--porcelain"])
    if status:
        print(status)
        fail("sport repo has uncommitted changes. Commit/stash them before syncing ty_sport.")
    source_status = git_output(source_repo, ["status", "--porcelain"])
    if source_status:
        print(source_status)
        fail("ty_sport_test repo has uncommitted changes. Commit/stash them before syncing.")

    log(f"pulling latest sport branch: {sport_remote}/{active_branch}")
    run(["git", "pull", "--ff-only", sport_remote, active_branch], cwd=repo, dry_run=dry_run)

    log(f"syncing local ty_sport_test ruoyi-ui -> sport/ruoyi-ui without docs: {source_repo} -> {repo / 'ruoyi-ui'}")
    if not dry_run:
        with tempfile.TemporaryDirectory(prefix="ty-sport-sync-") as temp_name:
            temp_dir = Path(temp_name)
            archive = subprocess.run(
                ["git", "archive", "--format=tar", "HEAD", "ruoyi-ui"],
                cwd=source_repo,
                check=False,
                stdout=subprocess.PIPE,
            )
            if archive.returncode != 0:
                fail("failed to archive ty_sport_test ruoyi-ui")
            tar = subprocess.run(
                ["tar", "-xf", "-", "-C", str(temp_dir)],
                input=archive.stdout,
                check=False,
            )
            if tar.returncode != 0:
                fail("failed to extract ty_sport_test ruoyi-ui archive")
            target_ruoyi = repo / "ruoyi-ui"
            if target_ruoyi.exists():
                shutil.rmtree(target_ruoyi)
            shutil.copytree(temp_dir / "ruoyi-ui", target_ruoyi)
            target_ruoyi_docs = target_ruoyi / "docs"
            if target_ruoyi_docs.exists():
                shutil.rmtree(target_ruoyi_docs)
            target_root_docs = repo / "docs"
            if target_root_docs.exists():
                shutil.rmtree(target_root_docs)

    run(["git", "add", "-A", "ruoyi-ui"], cwd=repo, dry_run=dry_run)
    if (repo / "docs").exists() or git_output(repo, ["ls-files", "docs"]):
        run(["git", "add", "-A", "docs"], cwd=repo, dry_run=dry_run)
    restore_sync_excluded_paths(repo, dry_run)

    if not has_path_change(repo, "ruoyi-ui") and not has_path_change(repo, "docs"):
        log("no ruoyi-ui differences from local ty_sport_test; skipping commit.")
        push_sport_branch(repo, sport_remote, active_branch, dry_run)
        return

    if not commit_message:
        commit_message = build_sync_commit_message(repo, f"{sport_remote}/{active_branch}", "HEAD")
        log("generated sport commit message from actual staged ruoyi-ui changes:")
        print(commit_message)

    commit_squashed_changes(repo, commit_message, author_name, author_email, dry_run)

    push_sport_branch(repo, sport_remote, active_branch, dry_run)


def ensure_branch(repo: Path, branch: str, label: str) -> None:
    active = current_branch(repo)
    if active != branch:
        fail(f"{label} current branch is '{active}'. Please switch to '{branch}' first.")


def changed_target_files(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=repo,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
    files: list[str] = []
    for line in result.stdout.splitlines():
        value = line[3:].strip()
        if " -> " in value:
            value = value.split(" -> ", 1)[1].strip()
        if value:
            files.append(value)
    return files


def latest_commit_date(repo: Path) -> str:
    return git_output(repo, ["log", "-1", "--format=%cI"])


def client_source_subjects(repo: Path, limit: int = 20, since: str | None = None) -> list[str]:
    cmd = ["git", "log", f"-{limit}", "--pretty=format:%s"]
    if since:
        cmd.insert(2, f"--since={since}")
    result = subprocess.run(
        cmd,
        cwd=repo,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def client_target_recent_message_text(repo: Path, limit: int = 20) -> str:
    result = subprocess.run(
        ["git", "log", f"-{limit}", "--pretty=format:%s%n%b"],
        cwd=repo,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
    return result.stdout.lower()


def clean_client_subject(subject: str) -> str:
    cleaned = re.sub(r"^(feat|feature|fix|bug|chore|refactor|style|docs)[:：]\s*", "", subject, flags=re.I)
    return cleaned.strip(" -：:")


def unsynced_client_source_subjects(source_repo: Path, target_repo: Path) -> list[str]:
    target_latest_date = latest_commit_date(target_repo)
    synced_text = client_target_recent_message_text(target_repo)
    subjects: list[str] = []
    for subject in client_source_subjects(source_repo, since=target_latest_date):
        cleaned = clean_client_subject(subject)
        if not cleaned or cleaned.lower().startswith("merge"):
            continue
        if cleaned.lower() in synced_text:
            continue
        append_once(subjects, cleaned)
    return subjects


def summarize_client_work(subjects: list[str], files: list[str]) -> list[str]:
    file_text = "\n".join(files).lower()
    subject_text = "\n".join(subjects).lower()
    haystack = f"{subject_text}\n{file_text}"
    items: list[str] = []

    if "余额" in haystack or "balance" in haystack or "src/api/user" in file_text or "src/api/order" in file_text:
        append_once(items, "接入余额接口并明确 token 来源")
    if (
        "sportsview" in haystack
        or "matchdetailpanel" in file_text
        or "usematchlistpolling" in file_text
        or "useoddsflash" in file_text
        or "oddsadapter" in file_text
        or "后端协议" in haystack
    ):
        append_once(items, "重构 SportsView 并对齐后端协议")
    if ".env.production" in file_text or ".env.development" in file_text:
        append_once(items, "调整客户端环境配置")
    if "src/utils/request" in file_text:
        append_once(items, "调整客户端请求拦截处理")

    if not items:
        for subject in subjects:
            cleaned = clean_client_subject(subject)
            if cleaned and not cleaned.lower().startswith("merge"):
                append_once(items, cleaned)

    return items


def build_client_sync_commit_message(source_repo: Path, target_repo: Path) -> str:
    subjects = unsynced_client_source_subjects(source_repo, target_repo)
    files = changed_target_files(target_repo)
    items = subjects or summarize_client_work([], files)
    if not items:
        return "同步 ty_client_test 客户端更新"
    title_items = "、".join(items[:2])
    lines = [title_items, ""]
    lines.extend(items)
    return "\n".join(lines)


def sync_ty_client_to_if_sport_ui(
    source_repo: Path,
    target_repo: Path,
    branch: str | None,
    remote: str,
    commit_message: str,
    author_name: str,
    author_email: str,
    dry_run: bool,
) -> None:
    if not (source_repo / ".git").exists():
        fail(f"{source_repo} is not a git repository")
    if not (target_repo / ".git").exists():
        fail(f"{target_repo} is not a git repository")
    if shutil.which("rsync") is None:
        fail("rsync is required for client sync")

    active_branch = branch or "test"
    ensure_remote(source_repo, remote)
    ensure_remote(target_repo, remote)

    if not dry_run:
        ensure_branch(source_repo, active_branch, "ty_client_test")
        ensure_branch(target_repo, active_branch, "if_sport_ui")

    if git_output(source_repo, ["status", "--porcelain"]):
        fail("ty_client_test repo has uncommitted changes. Commit/stash them before syncing client.")
    if git_output(target_repo, ["status", "--porcelain"]):
        fail("if_sport_ui repo has uncommitted changes. Commit/stash them before syncing client.")

    log(f"pulling latest ty_client_test branch: {remote}/{active_branch}")
    run(["git", "pull", "--ff-only", remote, active_branch], cwd=source_repo, dry_run=dry_run)

    log(f"pulling latest if_sport_ui branch: {remote}/{active_branch}")
    run(["git", "pull", "--ff-only", remote, active_branch], cwd=target_repo, dry_run=dry_run)

    log(f"syncing ty_client_test -> if_sport_ui: {source_repo} -> {target_repo}")
    rsync_cmd = [
        "rsync",
        "-a",
        "--delete",
        "--exclude",
        ".git",
    ]
    for path in DEFAULT_CLIENT_SYNC_EXCLUDE_PATHS:
        rsync_cmd.extend(["--exclude", path])
    rsync_cmd.extend([f"{source_repo}/", f"{target_repo}/"])
    run(
        rsync_cmd,
        dry_run=dry_run,
    )
    target_docs = target_repo / "docs"
    if target_docs.exists():
        log(f"removing if_sport_ui docs directory: {target_docs}")
        if not dry_run:
            shutil.rmtree(target_docs)

    if not has_worktree_changes(target_repo):
        log("no ty_client changes to commit.")
        return

    if not commit_message:
        commit_message = build_client_sync_commit_message(source_repo, target_repo)
        log("generated client commit message from synced changes:")
        print(commit_message)

    run(["git", "add", "-A"], cwd=target_repo, dry_run=dry_run)
    commit_squashed_changes(target_repo, commit_message, author_name, author_email, dry_run)
    push_sport_branch(target_repo, remote, active_branch, dry_run)


def report_period_dates(period: str, today: dt.date) -> tuple[str, str]:
    if period == "week":
        start = today - dt.timedelta(days=today.weekday())
        return start.isoformat(), (today + dt.timedelta(days=1)).isoformat()
    if period == "last-week":
        this_week = today - dt.timedelta(days=today.weekday())
        start = this_week - dt.timedelta(days=7)
        return start.isoformat(), this_week.isoformat()
    raise ValueError(f"Unsupported report period: {period}")


def report_author_pattern(author: str) -> str:
    if author.strip().lower() == "ayea":
        return "Aye"
    return author


def report_title_date(value: str | None, today_text: str | None) -> str:
    if value:
        return value
    today = dt.date.fromisoformat(today_text) if today_text else dt.date.today()
    return f"{today:%m/%d}"


def report_period(since: str | None, until: str | None, period: str, today_text: str | None) -> tuple[str, str]:
    today = dt.date.fromisoformat(today_text) if today_text else dt.date.today()
    report_since, report_until = (since, until) if since and until else report_period_dates(period, today)
    if not report_since or not report_until:
        fail("--report-since and --report-until must be used together.")
    return report_since, report_until


def collect_author_commit_files(repo: Path, author: str | None, since: str, until: str) -> tuple[list[str], list[str]]:
    if not (repo / ".git").exists():
        fail(f"{repo} is not a git repository")

    cmd = [
        "git",
        "log",
        f"--since={since}",
        f"--until={until}",
        "--pretty=format:%x1e%s",
        "--name-only",
        "--reverse",
    ]
    if author:
        cmd.insert(4, f"--author={report_author_pattern(author)}")

    result = subprocess.run(
        cmd,
        cwd=repo,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)

    subjects: list[str] = []
    files: list[str] = []
    for block in result.stdout.split("\x1e"):
        block = block.strip()
        if not block:
            continue
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        subject = re.sub(r"\s+", " ", lines[0]).strip()
        if subject and not subject.lower().startswith("merge"):
            subjects.append(subject)
        files.extend(lines[1:])
    return subjects, files


def collect_author_commit_groups(repo: Path, author: str | None, since: str, until: str) -> list[tuple[str, list[str], list[str]]]:
    if not (repo / ".git").exists():
        fail(f"{repo} is not a git repository")

    cmd = [
        "git",
        "log",
        f"--since={since}",
        f"--until={until}",
        "--date=format:%m/%d",
        "--pretty=format:%x1e%ad%x1f%s",
        "--name-only",
        "--reverse",
    ]
    if author:
        cmd.insert(4, f"--author={report_author_pattern(author)}")

    result = subprocess.run(
        cmd,
        cwd=repo,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)

    grouped: dict[str, tuple[list[str], list[str]]] = {}
    ordered_dates: list[str] = []
    for block in result.stdout.split("\x1e"):
        block = block.strip()
        if not block:
            continue
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines or "\x1f" not in lines[0]:
            continue
        date_text, subject = lines[0].split("\x1f", 1)
        subject = re.sub(r"\s+", " ", subject).strip()
        if date_text not in grouped:
            grouped[date_text] = ([], [])
            ordered_dates.append(date_text)
        subjects, files = grouped[date_text]
        if subject and not subject.lower().startswith("merge"):
            subjects.append(subject)
        files.extend(lines[1:])

    return [(date_text, *grouped[date_text]) for date_text in ordered_dates]


def unique_ordered(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        append_once(result, item)
    return result


def append_once(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def summarize_ty_work(subjects: list[str], files: list[str]) -> list[str]:
    file_text = "\n".join(files).lower()
    subject_text = "\n".join(subjects).lower()
    haystack = f"{subject_text}\n{file_text}"
    items: list[str] = []

    if "src/api/sports/settlementmatch" in file_text:
        append_once(items, "新增赛果结算 API")
    has_result_entry = "manualsettlement" in file_text or "settlementresultentry/" in file_text
    has_result_entry_log = "settlementlog" in file_text or "settlementresultentrylog" in file_text
    if has_result_entry and has_result_entry_log:
        append_once(items, "新增录入赛果入口页与日志页")
    elif has_result_entry:
        append_once(items, "新增录入赛果入口页")
    elif has_result_entry_log:
        append_once(items, "更新录入赛果日志页")
    if "settlementmatch" in file_text or "结算管理" in haystack or "完善结算管理" in haystack:
        append_once(items, "更新赛果结算页面")
    has_early_and_rolling_lists = "earlymarketlist" in file_text and "rollingballlist" in file_text
    if "早盘操盘" in haystack or "tradingboardmock" in file_text:
        append_once(items, "早盘操盘更新")
    if "盘口赔率" in haystack:
        append_once(items, "更新盘口赔率")
    if "操盘列表路由" in haystack:
        append_once(items, "调整操盘列表路由")
    elif has_early_and_rolling_lists:
        append_once(items, "更新早盘列表、滚球列表")
    elif "earlymarketlist" in file_text:
        append_once(items, "更新早盘列表")
    if "rollingballlist" in file_text and not has_early_and_rolling_lists:
        append_once(items, "更新滚球列表")
    if "src/router/" in file_text or "store/modules/permission" in file_text:
        append_once(items, "调整路由与权限菜单")
    if "storagetradermatchboard" in file_text:
        append_once(items, "同步交易盘本地缓存处理")
    if "vue.config.js" in file_text:
        append_once(items, "更新前端构建配置")

    if not items:
        for subject in subjects:
            cleaned = re.sub(r"^(feat|feature|fix|bug|chore|refactor|style|docs)[:：]\s*", "", subject, flags=re.I)
            cleaned = cleaned.strip(" -：:")
            if cleaned:
                append_once(items, cleaned)

    return items


def render_summary_report(title_date: str, items: list[str]) -> str:
    lines = [f"{title_date} 提交内容"]
    lines.extend(items or ["本周期没有查询到提交内容"])
    return "\n".join(lines) + "\n"


def build_summary_message(
    repo: Path,
    author: str | None,
    period: str,
    since: str | None,
    until: str | None,
    today_text: str | None,
    title_date_text: str | None,
) -> str:
    report_since, report_until = report_period(since, until, period, today_text)
    subjects, files = collect_author_commit_files(repo.expanduser(), author, report_since, report_until)
    return render_summary_report(report_title_date(title_date_text, today_text), summarize_ty_work(subjects, files))


def build_chronological_report(
    repo: Path,
    author: str | None,
    period: str,
    since: str | None,
    until: str | None,
    today_text: str | None,
) -> tuple[str, str, str]:
    report_since, report_until = report_period(since, until, period, today_text)
    groups = collect_author_commit_groups(repo.expanduser(), author, report_since, report_until)
    if not groups:
        return "本周期没有查询到提交内容\n", report_since, report_until

    start = dt.date.fromisoformat(report_since)
    end = dt.date.fromisoformat(report_until) - dt.timedelta(days=1)
    all_subjects = [subject for _, subjects, _ in groups for subject in subjects]
    all_files = [file for _, _, files in groups for file in files]
    summary_items = summarize_ty_work(all_subjects, all_files)

    lines: list[str] = []
    lines.append(f"前端工作周报（{start:%m/%d}-{end:%m/%d}）")
    lines.append("")
    lines.append("一、本周工作汇总")
    lines.extend(f"- {item}" for item in (summary_items or ["本周没有归纳到明确工作项"]))
    lines.append("")
    lines.append("二、每日提交与实际修改文件")
    for date_text, subjects, files in groups:
        lines.append(f"{date_text} 提交内容")
        lines.append("提交记录：")
        lines.extend(f"- {subject}" for subject in unique_ordered(subjects))
        lines.append("归纳工作：")
        lines.extend(f"- {item}" for item in (summarize_ty_work(subjects, files) or ["本日没有归纳到明确工作项"]))
        lines.append("实际修改文件：")
        lines.extend(f"- {file}" for file in unique_ordered(files))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n", report_since, report_until


def write_summary_report(
    report: str,
    output: Path | None,
    output_dir: Path,
    title_date: str | None = None,
    since: str | None = None,
    until: str | None = None,
    output_prefix: str = "TY体育_Ayea",
) -> Path:
    if output:
        output_path = output.expanduser()
    else:
        if title_date:
            suffix = title_date.replace("/", "")
        elif since and until:
            start = dt.date.fromisoformat(since)
            end = dt.date.fromisoformat(until) - dt.timedelta(days=1)
            suffix = f"{start:%m%d}_{end:%m%d}"
        else:
            suffix = "提交内容"
        output_path = output_dir.expanduser() / f"{output_prefix}_{suffix}_提交内容.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return output_path


def generate_summary_report(
    repo: Path,
    author: str | None,
    period: str,
    since: str | None,
    until: str | None,
    today_text: str | None,
    title_date_text: str | None,
    output: Path | None,
    output_dir: Path,
    stdout: bool,
    output_prefix: str = "TY体育_Ayea",
) -> None:
    report, report_since, report_until = build_chronological_report(repo, author, period, since, until, today_text)
    if stdout:
        print(report, end="")
        return

    output_path = write_summary_report(
        report,
        output,
        output_dir,
        since=report_since,
        until=report_until,
        output_prefix=output_prefix,
    )
    print(output_path)
    print()
    print(report, end="")


def report_week_windows(today_text: str | None) -> tuple[tuple[dt.date, dt.date], tuple[dt.date, dt.date]]:
    today = dt.date.fromisoformat(today_text) if today_text else dt.date.today()
    this_week_start = today - dt.timedelta(days=today.weekday())
    last_week_start = this_week_start - dt.timedelta(days=7)
    return (last_week_start, this_week_start - dt.timedelta(days=1)), (this_week_start, today)


def count_markdown_table_api_rows(readme: Path, heading: str) -> int:
    if not readme.exists():
        return 0
    lines = readme.read_text(encoding="utf-8").splitlines()
    in_section = False
    count = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = stripped == heading
            continue
        if in_section and stripped.startswith("| `"):
            count += 1
    return count


def count_completed_settlement_docs(repo: Path, current_week_numbers: set[str]) -> tuple[int, int]:
    settlement_dir = repo / "ruoyi-ui/docs/结算模块（Brad）"
    if not settlement_dir.exists():
        return 0, 0
    completed = [path for path in settlement_dir.glob("*.md") if "【调试通过】" in path.name]
    current_week = 0
    for path in completed:
        match = re.match(r"(\d+)-", path.name)
        if match and match.group(1) in current_week_numbers:
            current_week += 1
    return max(0, len(completed) - current_week), current_week


def file_contains_all(path: Path, keywords: list[str]) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    return all(keyword in text for keyword in keywords)


def implemented_marker_count(markers: list[list[tuple[Path, list[str]]]]) -> int:
    return sum(1 for marker in markers if all(file_contains_all(path, keywords) for path, keywords in marker))


def directory_contains_all(root: Path, keywords: list[str]) -> bool:
    if not root.exists():
        return False
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in {".js", ".vue", ".ts"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if all(keyword in text for keyword in keywords):
                return True
    return False


def build_sport_interface_counts(repo: Path) -> list[tuple[str, int, int, str | None]]:
    return [
        ("操盘模块", 4, 6, None),
        ("结算模块", 5, 12, None),
        ("赛事 / 赛程模块", 0, 13, None),
    ]


def build_client_interface_counts(repo: Path) -> list[tuple[str, int, int, str | None]]:
    return [("客户端", 5, 23, "7 个 PC/H5 页面")]


def render_interface_progress_report(
    targets: list[str],
    sport_repo: Path,
    client_repo: Path,
    today_text: str | None,
) -> str:
    (last_start, last_end), (week_start, week_end) = report_week_windows(today_text)
    sport_sections: list[tuple[str, int, int, str | None]] = build_sport_interface_counts(sport_repo) if "sport" in targets else []
    client_sections: list[tuple[str, int, int, str | None]] = build_client_interface_counts(client_repo) if "client" in targets else []
    completion_details: dict[str, tuple[str, str]] = {
        "操盘模块": (
            "我的操盘赛事、开关封锁上报、盘口 A/M 操盘模式上报、M 模式赔率水位调整上报。",
            "联赛参数设置列表、联赛属性修改、联赛模板绑定、操盘参数模板列表、操盘参数模板详情、操盘参数模板保存。",
        ),
        "结算模块": (
            "赛事赛果重推、冻结/解冻赛事、盘口冻结/解冻、赛事列表、赛事公告列表获取。",
            "赛事维度发送公告、看板统计数据、结算日志列表、赛事维度公告删除、待结算盘口列表、已结算盘口列表、已取消盘口列表、盘口结算详情、盘口结算、盘口回滚、盘口赛果重推、盘口取消。",
        ),
        "赛事 / 赛程模块": (
            "无。",
            "三方赛事分页列表、预开售赛事分页列表、历史赛事分页列表、玩法集列表、玩法列表、可选玩法列表、标准赛事生成、对阵管理、比赛时间调整、移入预开售、玩法集管理、玩法绑定、玩法状态 / 排序调整。",
        ),
    }

    lines = [
        f"前端本周报告（{week_start:%Y-%m-%d} ~ {week_end:%Y-%m-%d}）",
        "",
    ]

    for name, last_week, this_week, _note in sport_sections:
        detail = completion_details[name]
        lines.append(f"**{name}**")
        lines.append("")
        lines.append(f"上周完成 {last_week} 个接口：{detail[0]}")
        if last_week == 0:
            lines[-1] = "上周完成 0 个接口。"
        lines.append(f"本周完成 / 推进 {this_week} 个接口：{detail[1]}")
        lines.append("")

    if client_sections:
        name, last_week, this_week, page_note = client_sections[0]
        lines.append(f"**{name}**")
        lines.append("")
        lines.append("上周完成 5 个接口：登录两步走、余额读取、赛事列表、赛事详情、试玩相关数据接入。")
        lines.append("")
        lines.append(f"本周完成 / 推进 {this_week} 个接口 + {page_note}：")
        lines.append("")
        lines.append("- FB / NFB 体育接口，前端自行封装：赛事列表、赛事详情、右侧玩法展示、开售联赛列表、单关投注、串关投注接口入口、订单状态详情、投注单赔率轮询、注单列表、提前结算报价、提前结算提交。")
        lines.append("- 开发提供接口，按后端要求接入 / 修改：登录、试玩用户登录、获取 IF 令牌、用户余额读取、顶部公告列表、充值方式查询、充值通道列表、充值订单校验、充值订单提交、场馆余额读取、场馆余额刷新、额度转换、一键回收。")
        lines.append("- 页面补充：PC/H5 充值页、PC/H5 转账页、PC/H5 注单页、H5 移动端路由入口。")
        lines.append("")

    if "sport" in targets or "client" in targets:
        lines.append("**本周架构优化备注**")
        lines.append("")
    if "sport" in targets:
        lines.append("后台系统：按操盘、结算、赛程等业务模块统一前端目录，拆分 API、页面、路由入口，方便五大模块维护和多人协作。")
        lines.append("")
    if "client" in targets:
        lines.append("客户端：统一 `api`、`components`、`layout`、`router/modules`、`store/modules`、`views` 等目录；完成 PC/H5 路由与页面拆分，并补充充值、转账、注单、提前结算业务链路。样式沿用各客户端自身风格，未套用 UED 样式。")
        lines.append("")
        lines.append("客户端计划：当前优先补足页面、路由、API 等 Vue 架构可见部分；第二阶段优先接入后端提供接口；收到设计图后再同步美化页面。")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def generate_interface_progress_report(
    targets: list[str],
    sport_repo: Path,
    client_repo: Path,
    today_text: str | None,
    output: Path | None,
    output_dir: Path,
    stdout: bool,
) -> None:
    report = render_interface_progress_report(targets, sport_repo, client_repo, today_text)
    if stdout:
        print(report, end="")
        return

    (last_start, _), (_, week_end) = report_week_windows(today_text)
    output_path = write_summary_report(
        report,
        output,
        output_dir,
        since=last_start.isoformat(),
        until=(week_end + dt.timedelta(days=1)).isoformat(),
        output_prefix="ty_report",
    )
    print(output_path)
    print()
    print(report, end="")


def resolve_sync_commit_message(args: argparse.Namespace) -> str:
    custom_message = os.environ.get("SPORT_COMMIT_MESSAGE") is not None or args.commit_message != DEFAULT_COMMIT_MESSAGE
    if custom_message:
        return args.commit_message
    return ""


def open_vpn(app_names: list[str], dry_run: bool) -> None:
    for app in app_names:
        try:
            run(["open", "-a", app], dry_run=dry_run)
            log(f"requested VPN app: {app}")
            return
        except subprocess.CalledProcessError:
            continue
    fail(f"could not open any VPN app: {', '.join(app_names)}")


def wait_for_host(host: str, port: int, timeout: int) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=5):
                return True
        except OSError:
            time.sleep(3)
    return False


def ensure_vpn_ready(
    app_names: list[str],
    host: str,
    port: int,
    timeout: int,
    dry_run: bool,
) -> None:
    if dry_run:
        log(f"would check VPN/network reachability: {host}:{port}")
        open_vpn(app_names, dry_run)
        log(f"would wait for {host}:{port}")
        return

    log(f"checking VPN/network reachability: {host}:{port}")
    if wait_for_host(host, port, 5):
        log(f"VPN/network already reachable: {host}:{port}")
        return

    log("VPN/network is not reachable yet; opening OpenVPN.")
    open_vpn(app_names, dry_run)
    if wait_for_host(host, port, timeout):
        log(f"VPN/network reachable: {host}:{port}")
        return

    fail(
        f"timed out waiting for {host}:{port}; "
        "confirm OpenVPN is connected, then run again."
    )


def normalize_jenkins_url(url: str) -> str:
    return url.rstrip("/") + "/"


def job_url(base_url: str, job: str, explicit_job_url: str | None) -> str:
    if explicit_job_url:
        return explicit_job_url.rstrip("/") + "/"

    base = normalize_jenkins_url(base_url)
    parts = [part for part in job.strip("/").split("/") if part]
    encoded = "/".join("job/" + urllib.parse.quote(part) for part in parts)
    return urllib.parse.urljoin(base, encoded + "/")


def build_page_url(target_job_url: str) -> str:
    return urllib.parse.urljoin(target_job_url, "build?delay=0sec")


def open_jenkins(url: str, dry_run: bool) -> None:
    run(["open", url], dry_run=dry_run)
    log(f"opened Jenkins: {url}")


def submit_jenkins_build_page(url: str, dry_run: bool, timeout: int = 30) -> None:
    open_jenkins(url, dry_run)
    log("Jenkins build page is open; click the green 建置 button manually.")


def jenkins_request(
    url: str,
    method: str = "GET",
    user: str | None = None,
    token: str | None = None,
    data: bytes | None = None,
) -> tuple[int, bytes, dict[str, str]]:
    headers = {}
    if user and token:
        auth = base64.b64encode(f"{user}:{token}".encode()).decode()
        headers["Authorization"] = f"Basic {auth}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status, response.read(), dict(response.headers)


def get_crumb(base_url: str, user: str, token: str) -> tuple[str, str] | None:
    crumb_url = urllib.parse.urljoin(normalize_jenkins_url(base_url), "crumbIssuer/api/json")
    try:
        _, body, _ = jenkins_request(crumb_url, user=user, token=token)
        payload = json.loads(body.decode())
        return payload["crumbRequestField"], payload["crumb"]
    except (urllib.error.URLError, KeyError, json.JSONDecodeError):
        return None


def trigger_jenkins_api(base_url: str, target_job_url: str, dry_run: bool) -> None:
    user = os.environ.get("JENKINS_USER")
    token = os.environ.get("JENKINS_TOKEN")
    if not user:
        user = input("Jenkins user: ").strip()
    if not token:
        token = getpass.getpass("Jenkins API token/password: ").strip()
    if not user or not token:
        fail("Jenkins credentials are required for --trigger api")

    crumb = get_crumb(base_url, user, token)
    headers = {}
    if crumb:
        headers[crumb[0]] = crumb[1]

    auth = base64.b64encode(f"{user}:{token}".encode()).decode()
    headers["Authorization"] = f"Basic {auth}"
    build_url = urllib.parse.urljoin(target_job_url, "build")
    log(f"triggering Jenkins build: {build_url}")
    if dry_run:
        return

    request = urllib.request.Request(build_url, data=b"", headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            log(f"Jenkins accepted build request: HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        fail(f"Jenkins API returned HTTP {exc.code}: {exc.reason}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pull sport, start OpenVPN, open Jenkins, and deploy system-ui."
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["deploy", "sync", "report"],
        help="Optional positional mode. Example: deploy_ty.py sync client",
    )
    parser.add_argument(
        "target",
        nargs="?",
        choices=["sport", "client", "all"],
        help="Optional sync target. Example: deploy_ty.py sync client",
    )
    parser.add_argument("--repo", type=Path, default=Path(os.environ.get("SPORT_REPO", DEFAULT_REPO)))
    parser.add_argument("--remote", default=os.environ.get("SPORT_REMOTE", "origin"))
    parser.add_argument("--branch", default=os.environ.get("SPORT_BRANCH"))
    parser.add_argument(
        "--mode",
        choices=["prompt", "deploy", "sync", "report"],
        default=os.environ.get("SPORT_DEPLOY_MODE", "prompt"),
        help="prompt: ask; deploy: default CI/CD; sync: squash ty_sport into sport, push, then deploy; report: Ayea work summary from the selected report target",
    )
    parser.add_argument("--ty-sport-remote", default=os.environ.get("TY_SPORT_REMOTE", DEFAULT_TY_SPORT_REMOTE))
    parser.add_argument("--sport-push-remote", default=os.environ.get("SPORT_PUSH_REMOTE", DEFAULT_SPORT_PUSH_REMOTE))
    parser.add_argument(
        "--sync-target",
        choices=["sport", "client", "all"],
        default=os.environ.get("SPORT_SYNC_TARGET", "sport"),
        help="sync target: sport = ty_sport -> sport/system-ui; client = ty_client_test -> if_sport_ui; all = sport then client",
    )
    parser.add_argument(
        "--client-source-repo",
        type=Path,
        default=Path(os.environ.get("TY_CLIENT_SOURCE_REPO", DEFAULT_CLIENT_SOURCE_REPO)),
        help="Source repo for sync client. Default: ty_client_test.",
    )
    parser.add_argument(
        "--client-target-repo",
        type=Path,
        default=Path(os.environ.get("TY_CLIENT_TARGET_REPO", DEFAULT_CLIENT_TARGET_REPO)),
        help="Target repo for sync client. Default: if_sport_ui.",
    )
    parser.add_argument("--client-remote", default=os.environ.get("TY_CLIENT_REMOTE", DEFAULT_CLIENT_REMOTE))
    parser.add_argument(
        "--commit-message",
        default=os.environ.get("SPORT_COMMIT_MESSAGE", DEFAULT_COMMIT_MESSAGE),
        help="Override the sync commit message. Default: collect git log from ty_sport remote changes under ruoyi-ui.",
    )
    parser.add_argument("--sync-author-name", default=os.environ.get("SPORT_SYNC_AUTHOR_NAME", DEFAULT_SYNC_AUTHOR_NAME))
    parser.add_argument("--sync-author-email", default=os.environ.get("SPORT_SYNC_AUTHOR_EMAIL", DEFAULT_SYNC_AUTHOR_EMAIL))
    parser.add_argument("--strict-clean", action="store_true")
    parser.add_argument("--no-pull", action="store_true")
    parser.add_argument("--no-vpn", action="store_true")
    parser.add_argument("--vpn-app", action="append", help="VPN app name. Can be passed more than once.")
    parser.add_argument("--vpn-wait-host", default=os.environ.get("VPN_WAIT_HOST", DEFAULT_VPN_WAIT_HOST))
    parser.add_argument("--vpn-wait-port", type=int, default=int(os.environ.get("VPN_WAIT_PORT", str(DEFAULT_VPN_WAIT_PORT))))
    parser.add_argument("--vpn-timeout", type=int, default=int(os.environ.get("VPN_TIMEOUT", "120")))
    parser.add_argument("--jenkins-url", default=os.environ.get("JENKINS_URL", DEFAULT_JENKINS))
    parser.add_argument("--job", default=os.environ.get("JENKINS_JOB", DEFAULT_JOB))
    parser.add_argument("--job-url", default=os.environ.get("JENKINS_JOB_URL"))
    parser.add_argument(
        "--trigger",
        choices=["open", "api", "none"],
        default=os.environ.get("JENKINS_TRIGGER", "open"),
        help="open: open job page; api: POST build; none: only print URL",
    )
    parser.add_argument("--report-repo", type=Path, default=Path(os.environ["TY_SPORT_REPORT_REPO"]) if os.environ.get("TY_SPORT_REPORT_REPO") else None)
    parser.add_argument("--report-author", default=os.environ.get("TY_SPORT_REPORT_AUTHOR"))
    parser.add_argument(
        "--report-period",
        choices=["week", "last-week"],
        default=os.environ.get("TY_SPORT_REPORT_PERIOD", "week"),
        help="Report period. Default: week.",
    )
    parser.add_argument("--report-since", help="Report start date, inclusive. Example: 2026-05-04.")
    parser.add_argument("--report-until", help="Report end date, exclusive. Example: 2026-05-11.")
    parser.add_argument("--report-today", help="Override today for report period calculation. Example: 2026-05-13.")
    parser.add_argument("--report-date", help="Title date, example: 05/12. Default follows DEFAULT_COMMIT_MESSAGE.")
    parser.add_argument("--report-output", type=Path, help="Output txt path for the report.")
    parser.add_argument("--report-output-dir", type=Path, default=Path(os.environ.get("TY_SPORT_REPORT_OUTPUT_DIR", DEFAULT_REPORT_OUTPUT_DIR)))
    parser.add_argument("--report-stdout", action="store_true", help="Print report to stdout instead of writing a file.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.command:
        args.mode = args.command
    if args.target:
        args.sync_target = args.target
    return args


def choose_mode(mode: str) -> str:
    if mode != "prompt":
        return mode
    try:
        value = input("部署模式：直接按 Enter=开启 CI/CD 部署；输入 sync=同步 ty_sport 到 sport、push 后部署；输入 report=生成 Ayea 工作内容总结：").strip()
    except EOFError:
        value = ""
    if not value:
        return "deploy"
    normalized = value.lower()
    if normalized in {"sync", "report"}:
        return normalized
    fail(f"unknown mode: {value}. Use Enter, sync, or report.")


def main() -> None:
    args = parse_args()
    mode = choose_mode(args.mode)

    if mode == "report":
        report_targets = ["sport", "client"] if args.sync_target == "all" else [args.sync_target]
        sport_report_repo = args.report_repo or DEFAULT_REPORT_REPO
        generate_interface_progress_report(
            report_targets,
            sport_report_repo,
            args.client_source_repo,
            args.report_today,
            args.report_output,
            args.report_output_dir,
            args.report_stdout,
        )
        return

    sync_targets = ["sport", "client"] if args.sync_target == "all" else [args.sync_target]
    effective_job = DEFAULT_CLIENT_JOB if mode == "sync" and sync_targets == ["client"] and not args.job_url else args.job
    target_job = job_url(args.jenkins_url, effective_job, args.job_url)
    target_build_page = build_page_url(target_job)

    if not args.no_vpn:
        ensure_vpn_ready(
            args.vpn_app or DEFAULT_VPN_APPS,
            args.vpn_wait_host,
            args.vpn_wait_port,
            args.vpn_timeout,
            args.dry_run,
        )

    if mode == "sync" and "sport" in sync_targets:
        pull_ty_sport_worktree((args.report_repo or DEFAULT_REPORT_REPO).expanduser(), args.branch, args.dry_run)
        commit_message = resolve_sync_commit_message(args)
        sync_ty_sport_to_sport(
            args.repo.expanduser(),
            (args.report_repo or DEFAULT_REPORT_REPO).expanduser(),
            args.branch,
            args.ty_sport_remote,
            args.sport_push_remote,
            commit_message,
            args.sync_author_name,
            args.sync_author_email,
            args.dry_run,
        )

    if mode == "sync" and "client" in sync_targets:
        sync_ty_client_to_if_sport_ui(
            args.client_source_repo.expanduser(),
            args.client_target_repo.expanduser(),
            args.branch,
            args.client_remote,
            args.commit_message,
            args.sync_author_name,
            args.sync_author_email,
            args.dry_run,
        )

    if mode != "sync" and not args.no_pull:
        git_pull(args.repo.expanduser(), args.remote, args.branch, args.strict_clean, args.dry_run)

    if args.trigger == "api":
        trigger_jenkins_api(args.jenkins_url, target_job, args.dry_run)
    elif args.trigger == "open":
        submit_jenkins_build_page(target_build_page, args.dry_run)
    else:
        log(f"Jenkins build page URL: {target_build_page}")


if __name__ == "__main__":
    main()
