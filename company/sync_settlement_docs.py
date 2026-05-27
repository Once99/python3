#!/usr/bin/env python3
"""
Sync ty_sport_test settlement API docs from the internal Knife4j/OpenAPI page.

Default mode is dry-run:
  python3 sync_settlement_docs.py

Apply generated docs:
  python3 sync_settlement_docs.py --apply
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


REPO = Path("/Users/oncechen/IdeaProjects/ty_sport_test")
DOC_DIR = REPO / "ruoyi-ui" / "docs" / "结算模块（Brad）"
INTERNAL_HOST = "10.10.10.226"
INTERNAL_PORT = 9209
OPENAPI_CANDIDATES = [
    f"http://{INTERNAL_HOST}:{INTERNAL_PORT}/v3/api-docs",
    f"http://{INTERNAL_HOST}:{INTERNAL_PORT}/v3/api-docs/default",
]
TARGET_TAG_KEYWORDS = ("结算",)


def notify(message: str) -> None:
    print(message)
    if sys.platform == "darwin":
        escaped = message.replace("\\", "\\\\").replace('"', '\\"')
        try:
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    f'display notification "{escaped}" with title "赛程结算操盘文档同步"',
                ],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass


def run(cmd: list[str], cwd: Path | None = None) -> str:
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc.stdout.strip()


def check_vpn() -> None:
    try:
        with socket.create_connection((INTERNAL_HOST, INTERNAL_PORT), timeout=5):
            return
    except OSError as exc:
        notify(
            "OpenVPN 可能未开启或未成功连结：无法连接 "
            f"{INTERNAL_HOST}:{INTERNAL_PORT}。请先连接 VPN 后再运行。"
        )
        raise SystemExit(2) from exc


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8")
    return json.loads(body)


def load_openapi() -> tuple[str, dict[str, Any]]:
    last_error: Exception | None = None
    for url in OPENAPI_CANDIDATES:
        try:
            data = fetch_json(url)
            if isinstance(data, dict) and data.get("paths"):
                return url, data
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
    raise RuntimeError(f"Unable to fetch OpenAPI JSON. Last error: {last_error}")


def schema_name(schema: dict[str, Any] | None) -> str:
    if not schema:
        return ""
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]
    if "type" in schema:
        t = schema["type"]
        if t == "array":
            return f"array<{schema_name(schema.get('items')) or 'object'}>"
        return str(t)
    return "object"


def operation_matches(operation: dict[str, Any]) -> bool:
    tags = operation.get("tags") or []
    text = " ".join(str(tag) for tag in tags)
    summary = str(operation.get("summary") or "")
    operation_id = str(operation.get("operationId") or "")
    haystack = f"{text} {summary} {operation_id}"
    return any(keyword in haystack for keyword in TARGET_TAG_KEYWORDS)


def md_filename(index: int, title: str) -> str:
    safe = (
        title.replace("/", "-")
        .replace("\\", "-")
        .replace(":", "-")
        .replace("*", "-")
        .replace("?", "")
        .replace('"', "")
        .replace("<", "")
        .replace(">", "")
        .replace("|", "-")
        .strip()
    )
    return f"{index:02d}-{safe or '未命名接口'}.md"


def render_operation(method: str, path: str, operation: dict[str, Any]) -> tuple[str, str]:
    title = operation.get("summary") or operation.get("operationId") or f"{method.upper()} {path}"
    lines = [
        f"# {title}",
        "",
        f"> 来源：OpenAPI tag：`{', '.join(operation.get('tags') or [])}` / `{operation.get('operationId') or ''}`",
        "",
        "## 基本信息",
        "",
        f"- 方法：`{method.upper()}`",
        f"- 路径：`{path}`",
        f"- operationId：`{operation.get('operationId') or ''}`",
        f"- 说明：{operation.get('description') or operation.get('summary') or ''}",
        "",
    ]

    parameters = operation.get("parameters") or []
    if parameters:
        lines += [
            "## Path / Query 参数",
            "",
            "| 参数 | 位置 | 必填 | 类型 | 说明 |",
            "|---|---|---|---|---|",
        ]
        for p in parameters:
            lines.append(
                "| `{name}` | {where} | {required} | `{typ}` | {desc} |".format(
                    name=p.get("name", ""),
                    where=p.get("in", ""),
                    required="是" if p.get("required") else "否",
                    typ=schema_name(p.get("schema")),
                    desc=p.get("description") or "",
                )
            )
        lines.append("")

    request_body = operation.get("requestBody")
    if request_body:
        content = request_body.get("content") or {}
        schema = None
        for item in content.values():
            schema = item.get("schema")
            if schema:
                break
        lines += [
            "## Request Body",
            "",
            f"- 必填：{'是' if request_body.get('required') else '否'}",
            f"- Schema：`{schema_name(schema) or 'object'}`",
            "",
        ]

    responses = operation.get("responses") or {}
    lines += ["## Response", ""]
    for code, response in responses.items():
        schema = None
        content = response.get("content") or {}
        for item in content.values():
            schema = item.get("schema")
            if schema:
                break
        lines.append(
            f"- {code}：{response.get('description') or ''}"
            + (f"，Schema：`{schema_name(schema)}`" if schema else "")
        )
    lines += [
        "",
        "## 前端对接备注",
        "",
        "- 本文件由 `sync_settlement_docs.py` 根据 OpenAPI 自动生成；如需保留人工备注，请单独追加在 README 或独立补充文档中。",
    ]
    return str(title), "\n".join(lines) + "\n"


def generate_docs(openapi: dict[str, Any], target: Path) -> list[str]:
    target.mkdir(parents=True, exist_ok=True)
    generated: list[str] = []
    index = 1
    for path, methods in sorted((openapi.get("paths") or {}).items()):
        for method, operation in sorted(methods.items()):
            if method.lower() not in {"get", "post", "put", "delete", "patch"}:
                continue
            if not operation_matches(operation):
                continue
            title, content = render_operation(method, path, operation)
            filename = md_filename(index, title)
            (target / filename).write_text(content, encoding="utf-8")
            generated.append(filename)
            index += 1

    readme = [
        "# 结算模块（Brad）API 文档",
        "",
        "> 来源：内部 Knife4j/OpenAPI 自动生成。",
        "",
        "## 文档目录",
        "",
        "| # | 文档 |",
        "|---:|---|",
    ]
    for i, filename in enumerate(generated, 1):
        readme.append(f"| {i} | [{filename}](./{filename}) |")
    readme.append("")
    (target / "README.md").write_text("\n".join(readme), encoding="utf-8")
    generated.append("README.md")
    return sorted(generated)


def compare_dirs(old: Path, new: Path) -> tuple[list[str], list[str], list[str]]:
    old_files = {p.relative_to(old).as_posix(): p for p in old.rglob("*") if p.is_file()}
    new_files = {p.relative_to(new).as_posix(): p for p in new.rglob("*") if p.is_file()}
    added = sorted(set(new_files) - set(old_files))
    removed = sorted(set(old_files) - set(new_files))
    changed = []
    for name in sorted(set(old_files) & set(new_files)):
        if old_files[name].read_bytes() != new_files[name].read_bytes():
            changed.append(name)
    return added, changed, removed


def replace_dir(src: Path, dst: Path) -> None:
    backup = dst.with_name(dst.name + ".bak")
    if backup.exists():
        shutil.rmtree(backup)
    if dst.exists():
        shutil.copytree(dst, backup)
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    shutil.rmtree(backup, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="replace docs when differences exist")
    parser.add_argument("--skip-pull", action="store_true", help="skip git pull")
    args = parser.parse_args()

    check_vpn()

    if not args.skip_pull:
        print("Running git pull...")
        print(run(["git", "pull"], cwd=REPO))

    source_url, openapi = load_openapi()
    print(f"Loaded OpenAPI from {source_url}")

    with tempfile.TemporaryDirectory(prefix="settlement-docs-") as tmp:
        generated_dir = Path(tmp) / "结算模块（Brad）"
        generated = generate_docs(openapi, generated_dir)
        if not generated or generated == ["README.md"]:
            raise RuntimeError("No settlement operations matched OpenAPI tags.")

        added, changed, removed = compare_dirs(DOC_DIR, generated_dir)
        if not added and not changed and not removed:
            notify("此次自动化已完成，没发现接口文档变动。")
            return 0

        print("Detected documentation changes:")
        if added:
            print("Added:")
            print("\n".join(f"  + {item}" for item in added))
        if changed:
            print("Changed:")
            print("\n".join(f"  * {item}" for item in changed))
        if removed:
            print("Removed:")
            print("\n".join(f"  - {item}" for item in removed))

        if args.apply:
            replace_dir(generated_dir, DOC_DIR)
            notify("已更新结算模块（Brad）接口文档，请查看上方 Added/Changed/Removed 清单。")
        else:
            notify("发现接口文档变动；当前为 dry-run，未替换。需要替换请加 --apply。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
