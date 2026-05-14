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
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DEFAULT_REPO = Path("/Users/oncechen/IdeaProjects/sport")
DEFAULT_REPORT_REPO = Path("/Users/oncechen/IdeaProjects/ty_sport_test")
DEFAULT_REPORT_AUTHOR = "Ayea"
DEFAULT_REPORT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "reports"
DEFAULT_JENKINS = "https://jenkins.helpom.com/"
DEFAULT_JOB = "system-ui"
DEFAULT_VPN_APPS = ["OpenVPN Connect", "OpenVPN"]
DEFAULT_VPN_WAIT_HOST = "git.helpom.com"
DEFAULT_VPN_WAIT_PORT = 80
DEFAULT_TY_SPORT_REMOTE = "gitlab"
DEFAULT_SPORT_PUSH_REMOTE = "origin"
DEFAULT_SYNC_AUTHOR_NAME = "loki"
DEFAULT_SYNC_AUTHOR_EMAIL = "webm@dc66.net"
DEFAULT_COMMIT_MESSAGE = ""


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


def staged_ruoyi_files(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", "ruoyi-ui"],
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


def has_ruoyi_diff(repo: Path, base_ref: str, target_ref: str) -> bool:
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
    files = staged_ruoyi_files(repo)
    items = summarize_ty_work(subjects, files)
    lines = [f"{sync_title_date()} 提交内容", ""]
    if not items:
        lines.append("同步 ty_sport 前端更新")
        return "\n".join(lines)

    lines.extend(items)
    return "\n".join(lines)


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
    ensure_remote(repo, ty_remote)
    ensure_remote(repo, sport_remote)

    if not dry_run and current_branch(repo) != active_branch:
        fail(f"current branch is '{current_branch(repo)}'. Please switch to '{active_branch}' first.")

    status = git_output(repo, ["status", "--porcelain"])
    if status:
        print(status)
        fail("sport repo has uncommitted changes. Commit/stash them before syncing ty_sport.")

    log(f"pulling latest sport branch: {sport_remote}/{active_branch}")
    run(["git", "pull", "--ff-only", sport_remote, active_branch], cwd=repo, dry_run=dry_run)
    log(f"fetching ty_sport branch: {ty_remote}/{active_branch}")
    run(["git", "fetch", ty_remote, active_branch], cwd=repo, dry_run=dry_run)
    if not dry_run and not has_ruoyi_diff(repo, "HEAD", f"{ty_remote}/{active_branch}"):
        log("no ruoyi-ui differences from ty_sport; skipping squash merge.")
        push_sport_branch(repo, sport_remote, active_branch, dry_run)
        return
    try:
        run(["git", "merge", "--squash", "--no-commit", f"{ty_remote}/{active_branch}"], cwd=repo, dry_run=dry_run)
    except subprocess.CalledProcessError:
        fail(f"squash merge failed for {ty_remote}/{active_branch}. Resolve conflicts in sport, then commit manually.")

    if not commit_message:
        commit_message = build_sync_commit_message(repo, f"{sport_remote}/{active_branch}", f"{ty_remote}/{active_branch}")
        log("generated sport commit message from actual staged ruoyi-ui changes:")
        print(commit_message)

    commit_squashed_changes(repo, commit_message, author_name, author_email, dry_run)

    push_sport_branch(repo, sport_remote, active_branch, dry_run)


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


def collect_author_commit_files(repo: Path, author: str, since: str, until: str) -> tuple[list[str], list[str]]:
    if not (repo / ".git").exists():
        fail(f"{repo} is not a git repository")

    result = subprocess.run(
        [
            "git",
            "log",
            f"--since={since}",
            f"--until={until}",
            f"--author={report_author_pattern(author)}",
            "--pretty=format:%x1e%s",
            "--name-only",
            "--reverse",
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
            subjects.append(subject)
        files.extend(lines[1:])
    return subjects, files


def collect_author_commit_groups(repo: Path, author: str, since: str, until: str) -> list[tuple[str, list[str], list[str]]]:
    if not (repo / ".git").exists():
        fail(f"{repo} is not a git repository")

    result = subprocess.run(
        [
            "git",
            "log",
            f"--since={since}",
            f"--until={until}",
            f"--author={report_author_pattern(author)}",
            "--date=format:%m/%d",
            "--pretty=format:%x1e%ad%x1f%s",
            "--name-only",
            "--reverse",
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
    if "早盘操盘" in haystack or "tradingboardmock" in file_text:
        append_once(items, "早盘操盘更新")
    elif "earlymarketlist" in file_text and "rollingballlist" in file_text:
        append_once(items, "更新早盘列表、滚球列表")
    elif "earlymarketlist" in file_text:
        append_once(items, "更新早盘列表")
    if "rollingballlist" in file_text:
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
    author: str,
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
    author: str,
    period: str,
    since: str | None,
    until: str | None,
    today_text: str | None,
) -> tuple[str, str, str]:
    report_since, report_until = report_period(since, until, period, today_text)
    groups = collect_author_commit_groups(repo.expanduser(), author, report_since, report_until)
    if not groups:
        return "本周期没有查询到提交内容\n", report_since, report_until

    lines: list[str] = []
    for date_text, subjects, files in groups:
        lines.append(f"{date_text} 提交内容")
        lines.extend(summarize_ty_work(subjects, files) or ["本日没有查询到提交内容"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n", report_since, report_until


def write_summary_report(
    report: str,
    output: Path | None,
    output_dir: Path,
    title_date: str | None = None,
    since: str | None = None,
    until: str | None = None,
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
        output_path = output_dir.expanduser() / f"TY体育_Ayea_{suffix}_提交内容.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return output_path


def generate_summary_report(
    repo: Path,
    author: str,
    period: str,
    since: str | None,
    until: str | None,
    today_text: str | None,
    title_date_text: str | None,
    output: Path | None,
    output_dir: Path,
    stdout: bool,
) -> None:
    report, report_since, report_until = build_chronological_report(repo, author, period, since, until, today_text)
    if stdout:
        print(report, end="")
        return

    output_path = write_summary_report(report, output, output_dir, since=report_since, until=report_until)
    print(output_path)


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
    if dry_run:
        log("would click the Jenkins build button with the default parameters.")
        return

    script = f"""
set targetUrl to "{url}"
set deadline to (current date) + {timeout}
tell application "Google Chrome"
    activate
    set URL of active tab of front window to targetUrl
end tell

repeat while (current date) < deadline
    delay 1
    try
        tell application "Google Chrome"
            set clicked to execute active tab of front window javascript "
(() => {{
  const buttons = Array.from(document.querySelectorAll('button, input[type=submit], a.jenkins-button'));
  const buildButton = buttons.find((el) => {{
    const text = ((el.innerText || el.value || el.getAttribute('aria-label') || '') + '').trim();
    return /^(建置|Build)$/.test(text) || text.includes('建置') || text.includes('Build');
  }});
  if (!buildButton) return 'WAITING';
  buildButton.click();
  return 'CLICKED';
}})();
"
        end tell
        if clicked is "CLICKED" then return
    end try
end repeat
error "Timed out waiting for Jenkins build button"
"""
    result = subprocess.run(["osascript", "-e", script], text=True, capture_output=True, check=False)
    if result.returncode == 0:
        log("submitted the Jenkins build page with the default parameters.")
        return

    message = (result.stderr or result.stdout or "").strip()
    log("could not auto-click the Jenkins build button.")
    if message:
        log(message)
    log("The page is open; click the green 建置 button manually if Chrome blocks automation.")


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
    parser.add_argument("--repo", type=Path, default=Path(os.environ.get("SPORT_REPO", DEFAULT_REPO)))
    parser.add_argument("--remote", default=os.environ.get("SPORT_REMOTE", "origin"))
    parser.add_argument("--branch", default=os.environ.get("SPORT_BRANCH"))
    parser.add_argument(
        "--mode",
        choices=["prompt", "deploy", "sync", "report"],
        default=os.environ.get("SPORT_DEPLOY_MODE", "prompt"),
        help="prompt: ask; deploy: default CI/CD; sync: squash ty_sport into sport, push, then deploy; report: Ayea work summary from ty_sport_test",
    )
    parser.add_argument("--ty-sport-remote", default=os.environ.get("TY_SPORT_REMOTE", DEFAULT_TY_SPORT_REMOTE))
    parser.add_argument("--sport-push-remote", default=os.environ.get("SPORT_PUSH_REMOTE", DEFAULT_SPORT_PUSH_REMOTE))
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
    parser.add_argument("--report-repo", type=Path, default=Path(os.environ.get("TY_SPORT_REPORT_REPO", DEFAULT_REPORT_REPO)))
    parser.add_argument("--report-author", default=os.environ.get("TY_SPORT_REPORT_AUTHOR", DEFAULT_REPORT_AUTHOR))
    parser.add_argument(
        "--report-period",
        choices=["week", "last-week"],
        default=os.environ.get("TY_SPORT_REPORT_PERIOD", "last-week"),
        help="Report period. Default: last-week.",
    )
    parser.add_argument("--report-since", help="Report start date, inclusive. Example: 2026-05-04.")
    parser.add_argument("--report-until", help="Report end date, exclusive. Example: 2026-05-11.")
    parser.add_argument("--report-today", help="Override today for report period calculation. Example: 2026-05-13.")
    parser.add_argument("--report-date", help="Title date, example: 05/12. Default follows DEFAULT_COMMIT_MESSAGE.")
    parser.add_argument("--report-output", type=Path, help="Output txt path for the report.")
    parser.add_argument("--report-output-dir", type=Path, default=Path(os.environ.get("TY_SPORT_REPORT_OUTPUT_DIR", DEFAULT_REPORT_OUTPUT_DIR)))
    parser.add_argument("--report-stdout", action="store_true", help="Print report to stdout instead of writing a file.")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


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
        generate_summary_report(
            args.report_repo,
            args.report_author,
            args.report_period,
            args.report_since,
            args.report_until,
            args.report_today,
            args.report_date,
            args.report_output,
            args.report_output_dir,
            args.report_stdout,
        )
        return

    target_job = job_url(args.jenkins_url, args.job, args.job_url)
    target_build_page = build_page_url(target_job)

    if not args.no_vpn:
        ensure_vpn_ready(
            args.vpn_app or DEFAULT_VPN_APPS,
            args.vpn_wait_host,
            args.vpn_wait_port,
            args.vpn_timeout,
            args.dry_run,
        )

    if mode == "sync":
        pull_ty_sport_worktree(args.report_repo.expanduser(), args.branch, args.dry_run)
        commit_message = resolve_sync_commit_message(args)
        sync_ty_sport_to_sport(
            args.repo.expanduser(),
            args.branch,
            args.ty_sport_remote,
            args.sport_push_remote,
            commit_message,
            args.sync_author_name,
            args.sync_author_email,
            args.dry_run,
        )
    elif not args.no_pull:
        git_pull(args.repo.expanduser(), args.remote, args.branch, args.strict_clean, args.dry_run)

    if args.trigger == "api":
        trigger_jenkins_api(args.jenkins_url, target_job, args.dry_run)
    elif args.trigger == "open":
        submit_jenkins_build_page(target_build_page, args.dry_run)
    else:
        log(f"Jenkins build page URL: {target_build_page}")


if __name__ == "__main__":
    main()
