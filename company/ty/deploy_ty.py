#!/usr/bin/env python3
"""Pull the sport repo, start VPN, and open or trigger the system-ui Jenkins deploy."""

from __future__ import annotations

import argparse
import base64
import getpass
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DEFAULT_REPO = Path("/Users/oncechen/IdeaProjects/sport")
DEFAULT_JENKINS = "https://jenkins.helpom.com/"
DEFAULT_JOB = "system-ui"
DEFAULT_VPN_APPS = ["OpenVPN Connect", "OpenVPN"]
DEFAULT_VPN_WAIT_HOST = "git.helpom.com"
DEFAULT_VPN_WAIT_PORT = 80
DEFAULT_TY_SPORT_REMOTE = "gitlab"
DEFAULT_SPORT_PUSH_REMOTE = "origin"
DEFAULT_COMMIT_MESSAGE = "deploy: sync sport changes"


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


def has_worktree_changes(repo: Path) -> bool:
    return bool(git_output(repo, ["status", "--porcelain"]))


def commit_worktree_changes(repo: Path, message: str, dry_run: bool) -> None:
    status = git_output(repo, ["status", "--porcelain"])
    if not status:
        log("sport worktree has no local changes to commit.")
        return

    log("sport worktree has local changes; committing them before push.")
    print(status)
    run(["git", "add", "-A"], cwd=repo, dry_run=dry_run)
    run(["git", "commit", "-m", message], cwd=repo, dry_run=dry_run)


def ensure_remote(repo: Path, remote: str) -> str:
    try:
        return git_output(repo, ["remote", "get-url", remote])
    except subprocess.CalledProcessError:
        fail(f"missing git remote: {remote}")


def sync_ty_sport_to_sport(
    repo: Path,
    branch: str | None,
    ty_remote: str,
    sport_remote: str,
    commit_message: str,
    dry_run: bool,
) -> None:
    if not (repo / ".git").exists():
        fail(f"{repo} is not a git repository")

    active_branch = branch or current_branch(repo)
    ensure_remote(repo, ty_remote)
    ensure_remote(repo, sport_remote)

    if not dry_run and current_branch(repo) != active_branch:
        fail(f"current branch is '{current_branch(repo)}'. Please switch to '{active_branch}' first.")

    commit_worktree_changes(repo, commit_message, dry_run)
    log(f"syncing {ty_remote}/{active_branch} into local sport branch {active_branch}")
    run(["git", "fetch", ty_remote, active_branch], cwd=repo, dry_run=dry_run)
    try:
        run(["git", "merge", "--ff-only", f"{ty_remote}/{active_branch}"], cwd=repo, dry_run=dry_run)
    except subprocess.CalledProcessError:
        log(f"{ty_remote}/{active_branch} is not a fast-forward; creating a merge commit in sport.")
        try:
            run(["git", "merge", "--no-edit", f"{ty_remote}/{active_branch}"], cwd=repo, dry_run=dry_run)
        except subprocess.CalledProcessError:
            fail("merge failed. Resolve conflicts in sport, then rerun ayea mode.")

    if has_worktree_changes(repo) and not dry_run:
        fail("sync left uncommitted changes in sport; resolve them before pushing.")

    log(f"running git push inside sport: {sport_remote} {active_branch}:{active_branch}")
    run(["git", "push", sport_remote, f"{active_branch}:{active_branch}"], cwd=repo, dry_run=dry_run)


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
        choices=["prompt", "deploy", "ayea"],
        default=os.environ.get("SPORT_DEPLOY_MODE", "prompt"),
        help="prompt: ask; deploy: default CI/CD; ayea: sync ty_sport to sport, push, then deploy",
    )
    parser.add_argument("--ty-sport-remote", default=os.environ.get("TY_SPORT_REMOTE", DEFAULT_TY_SPORT_REMOTE))
    parser.add_argument("--sport-push-remote", default=os.environ.get("SPORT_PUSH_REMOTE", DEFAULT_SPORT_PUSH_REMOTE))
    parser.add_argument("--commit-message", default=os.environ.get("SPORT_COMMIT_MESSAGE", DEFAULT_COMMIT_MESSAGE))
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
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def choose_mode(mode: str) -> str:
    if mode != "prompt":
        return mode
    try:
        value = input("部署模式：直接按 Enter=开启 CI/CD 部署；输入 ayea=同步 ty_sport 到 sport、push 后部署：").strip()
    except EOFError:
        value = ""
    if not value:
        return "deploy"
    if value.lower() == "ayea":
        return "ayea"
    fail(f"unknown mode: {value}. Use Enter or ayea.")


def main() -> None:
    args = parse_args()
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

    mode = choose_mode(args.mode)

    if mode == "ayea":
        sync_ty_sport_to_sport(
            args.repo.expanduser(),
            args.branch,
            args.ty_sport_remote,
            args.sport_push_remote,
            args.commit_message,
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
