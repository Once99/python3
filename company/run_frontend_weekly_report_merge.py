#!/usr/bin/env python3
"""One-command frontend weekly report merger.

Default usage:
  python3 run_frontend_weekly_report_merge.py

Expected files:
  ./0518_0522_前端工作周报.xlsx
  ./outlook_weekly_reports.txt

Output:
  ./0518_0522_前端工作周报_合并版.xlsx

You can also pass a different xlsx/text file:
  python3 run_frontend_weekly_report_merge.py \
    --xlsx /path/to/0518_0522_前端工作周报.xlsx \
    --outlook-text /path/to/outlook_weekly_reports.txt
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MERGE_SCRIPT = ROOT / "merge_outlook_next_plan.py"
DEFAULT_OUTLOOK_TEXT = ROOT / "outlook_weekly_reports.txt"


def find_default_xlsx() -> Path | None:
    candidates = sorted(
        ROOT.glob("*_前端工作周报.xlsx"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        if "合并版" not in path.stem and "测试版" not in path.stem:
            return path
    return None


def output_path_for(xlsx: Path, output: Path | None) -> Path:
    if output:
        return output
    stem = re.sub(r"(_合并版|_下周计划测试版)$", "", xlsx.stem)
    return xlsx.with_name(f"{stem}_合并版.xlsx")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Quickly merge Outlook next plans into frontend weekly report.")
    parser.add_argument("--xlsx", type=Path, help="Frontend weekly report xlsx. Defaults to latest *_前端工作周报.xlsx in this folder.")
    parser.add_argument("--outlook-text", type=Path, default=DEFAULT_OUTLOOK_TEXT, help="Pasted Outlook weekly reports text file.")
    parser.add_argument("--output", type=Path, help="Output xlsx. Defaults to *_合并版.xlsx next to input.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    xlsx = args.xlsx or find_default_xlsx()
    if xlsx is None:
        print("找不到 *_前端工作周报.xlsx，请用 --xlsx 指定文件。", file=sys.stderr)
        return 2
    if not xlsx.exists():
        print(f"找不到 xlsx：{xlsx}", file=sys.stderr)
        return 2
    if not args.outlook_text.exists():
        print(f"找不到 Outlook 文本：{args.outlook_text}", file=sys.stderr)
        print("请把 Outlook 周报内容贴到 outlook_weekly_reports.txt，或用 --outlook-text 指定。", file=sys.stderr)
        return 2
    if not MERGE_SCRIPT.exists():
        print(f"找不到合并脚本：{MERGE_SCRIPT}", file=sys.stderr)
        return 2

    output = output_path_for(xlsx, args.output)
    cmd = [
        sys.executable,
        str(MERGE_SCRIPT),
        "--xlsx",
        str(xlsx),
        "--outlook-text",
        str(args.outlook_text),
        "--output",
        str(output),
    ]
    print("运行：", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"已生成：{output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
