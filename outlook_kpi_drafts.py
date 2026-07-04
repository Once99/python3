#!/usr/bin/env python3
"""
Draft Outlook KPI rating replies without sending.

Default behavior:
- open Outlook web mail
- find visible KPI emails
- skip excluded employees
- use reply-all
- write "评级：A"
- ensure CTO and HR HRPHIT are recipients
- leave replies as drafts

Requirements:
  python3 -m pip install playwright
  python3 -m playwright install chromium

For best results, run while already signed in to Outlook in Chrome.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path


DEFAULT_OUTLOOK_URL = "https://outlook.cloud.microsoft/mail/"
DEFAULT_RATING = "评级：A"
DEFAULT_SKIP = ("Angemi", "Oswin", "Roger", "Lelisu", "Musk")
DEFAULT_REQUIRED_RECIPIENTS = ("CTO@dc66.net", "HRPHIT@dc66.net")


@dataclass
class DraftResult:
    name: str
    subject: str
    status: str
    detail: str = ""


def load_playwright():
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    except ModuleNotFoundError:
        print(
            "Missing dependency: playwright\n"
            "Install with:\n"
            "  python3 -m pip install playwright\n"
            "  python3 -m playwright install chromium",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return sync_playwright, PlaywrightTimeoutError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create Outlook KPI rating reply-all drafts.")
    parser.add_argument("--rating", default=DEFAULT_RATING, help="Rating text to put in the reply body.")
    parser.add_argument("--skip", nargs="*", default=list(DEFAULT_SKIP), help="Employee names to skip.")
    parser.add_argument(
        "--required-recipient",
        action="append",
        default=list(DEFAULT_REQUIRED_RECIPIENTS),
        help="Recipient email to ensure is included. Can be repeated.",
    )
    parser.add_argument("--url", default=DEFAULT_OUTLOOK_URL, help="Outlook URL to open.")
    parser.add_argument("--max", type=int, default=20, help="Maximum visible KPI emails to inspect.")
    parser.add_argument("--dry-run", action="store_true", help="List matching emails without creating drafts.")
    parser.add_argument("--headless", action="store_true", help="Run browser headless.")
    parser.add_argument(
        "--user-data-dir",
        default=str(Path.home() / "Library/Application Support/Google/Chrome"),
        help="Chrome user data directory for persistent login state.",
    )
    parser.add_argument("--profile-directory", default="Default", help="Chrome profile directory name.")
    return parser.parse_args()


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def employee_from_label(label: str) -> str:
    label = normalize_text(label)
    patterns = [
        r"\bDEV?\s+([A-Za-z][A-Za-z0-9_.-]+)\b",
        r"\bDev\s+([A-Za-z][A-Za-z0-9_.-]+)\b",
        r"KPI[^A-Za-z0-9]+([A-Za-z][A-Za-z0-9_.-]+)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, label, re.IGNORECASE)
        if match:
            return match.group(1)
    return "unknown"


def is_kpi_mail(label: str) -> bool:
    text = normalize_text(label).lower()
    return "kpi" in text and ("hr hrphit" not in text or "工作流" in text or "6月" in text)


def should_skip(label: str, skip_names: list[str]) -> bool:
    folded = label.casefold()
    return any(name.casefold() in folded for name in skip_names)


def wait_for_outlook(page, timeout_ms: int = 45_000) -> None:
    page.goto(DEFAULT_OUTLOOK_URL, wait_until="domcontentloaded", timeout=timeout_ms)
    page.wait_for_timeout(5_000)
    page.get_by_role("button", name=re.compile("新郵件|新邮件|New mail")).first.wait_for(timeout=timeout_ms)


def get_visible_kpi_options(page, max_items: int, skip_names: list[str]):
    options = page.locator('[role="option"]')
    count = min(options.count(), max_items)
    items = []
    for index in range(count):
        option = options.nth(index)
        label = option.get_attribute("aria-label") or option.inner_text(timeout=2_000)
        if not is_kpi_mail(label):
            continue
        employee = employee_from_label(label)
        skipped = should_skip(label, skip_names)
        items.append((index, employee, label, skipped))
    return items


def click_reply_all(page) -> None:
    candidates = page.locator('[aria-label="全部回覆"], [aria-label="Reply all"]')
    if candidates.count() == 0:
        raise RuntimeError("Could not find Reply all / 全部回覆")
    candidates.last.click()
    page.wait_for_timeout(1_500)


def ensure_recipients(page, required_recipients: list[str]) -> str:
    recipient = page.locator('[aria-label="收件者"][contenteditable="true"], [aria-label="To"][contenteditable="true"]').last
    current = recipient.inner_text(timeout=5_000)
    missing = []
    current_folded = current.casefold()
    for email in required_recipients:
        local_name = email.split("@", 1)[0]
        if email.casefold() not in current_folded and local_name.casefold() not in current_folded:
            missing.append(email)
    if missing:
        recipient.click()
        recipient.type(" " + "; ".join(missing) + ";")
        page.wait_for_timeout(2_000)
    return recipient.inner_text(timeout=5_000)


def write_rating(page, rating: str) -> str:
    body = page.locator('[aria-label="郵件內文"][contenteditable="true"][role="textbox"], [aria-label="Message body"][contenteditable="true"][role="textbox"]').last
    body.wait_for(timeout=10_000)
    text = body.inner_text(timeout=5_000)
    if not text.strip().startswith(rating):
        body.fill(f"{rating}\n\n{text}")
        page.wait_for_timeout(2_000)
    return body.inner_text(timeout=5_000)


def process_kpi_mail(page, option_index: int, employee: str, label: str, args: argparse.Namespace) -> DraftResult:
    subject = normalize_text(label)[:120]
    options = page.locator('[role="option"]')
    options.nth(option_index).click()
    page.wait_for_timeout(1_800)
    click_reply_all(page)
    recipients = ensure_recipients(page, args.required_recipient)
    body = write_rating(page, args.rating)
    ok = body.strip().startswith(args.rating)
    return DraftResult(
        name=employee,
        subject=subject,
        status="drafted" if ok else "needs-review",
        detail=f"recipients={normalize_text(recipients)}",
    )


def main() -> int:
    args = parse_args()
    sync_playwright, PlaywrightTimeoutError = load_playwright()

    results: list[DraftResult] = []
    with sync_playwright() as p:
        user_data_dir = str(Path(args.user_data_dir).expanduser())
        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=args.headless,
            args=[f"--profile-directory={args.profile_directory}"],
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        try:
            page.goto(args.url, wait_until="domcontentloaded", timeout=45_000)
            page.wait_for_timeout(7_000)
            items = get_visible_kpi_options(page, args.max, args.skip)
            if args.dry_run:
                for _, employee, label, skipped in items:
                    marker = "SKIP" if skipped else "TODO"
                    print(f"{marker}\t{employee}\t{normalize_text(label)}")
                return 0

            for option_index, employee, label, skipped in items:
                if skipped:
                    results.append(DraftResult(employee, normalize_text(label)[:120], "skipped"))
                    continue
                try:
                    results.append(process_kpi_mail(page, option_index, employee, label, args))
                    time.sleep(0.5)
                except Exception as exc:
                    results.append(DraftResult(employee, normalize_text(label)[:120], "error", str(exc)))
        except PlaywrightTimeoutError as exc:
            print(f"Timed out waiting for Outlook: {exc}", file=sys.stderr)
            return 1
        finally:
            browser.close()

    for result in results:
        suffix = f"\t{result.detail}" if result.detail else ""
        print(f"{result.status}\t{result.name}\t{result.subject}{suffix}")
    print("Done. No send action is performed by this script.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
