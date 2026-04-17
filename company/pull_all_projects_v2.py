import subprocess
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECTS = {
    "tyadmin": {"path": "/Users/oncechen/IdeaProjects/ty_admin/"},
    "ezpay": {"path": "/Users/oncechen/IdeaProjects/ezpay-site/"},
    "qypc": {"path": "/Users/oncechen/IdeaProjects/qy_web_vue/"},
    "qyh5": {"path": "/Users/oncechen/IdeaProjects/qy_web_static_vue/"},
    "qy": {"path": "/Users/oncechen/IdeaProjects/c_qy/web/WebRoot/"},
    "rb88_main": {"path": "/Users/oncechen/IdeaProjects/rb88_web_vue_main/"},
    "jxf_main": {"path": "/Users/oncechen/IdeaProjects/jxf_web_static_vue_main/"},
    "uedpc": {"path": "/Users/oncechen/IdeaProjects/ued_web_vue/"},
    "uedh5": {"path": "/Users/oncechen/IdeaProjects/ued_web_static_vue/"},
    "ued": {"path": "/Users/oncechen/IdeaProjects/c_ued/WebRoot/"},
    "tq": {"path": "/Users/oncechen/IdeaProjects/c_sportone/web/WebRoot/"},
    "pt777": {"path": "/Users/oncechen/IdeaProjects/c_pt777/WebRoot/"},
    "long8": {"path": "/Users/oncechen/IdeaProjects/c_long8/web/WebRoot/"},
    "lwpc": {"path": "/Users/oncechen/IdeaProjects/e68_web_vue/"},
    "lwh5": {"path": "/Users/oncechen/IdeaProjects/e68_web_static_vue/"},
    "feiyu": {"path": "/Users/oncechen/IdeaProjects/feiyu-site/"},
    "94Chat": {"path": "/Users/oncechen/IdeaProjects/site-dolphin/"},
    "weiquandanbao": {"path": "/Users/oncechen/IdeaProjects/site-weiquandanbao/"},
    "haitun": {"path": "/Users/oncechen/IdeaProjects/site-haitun-web/"},
    "dolphin_im": {"path": "/Users/oncechen/IdeaProjects/dolphin_im_pc/"},
}

MAX_WORKERS = 6
GIT_TIMEOUT = 90


def run_cmd(cmd, cwd, timeout=GIT_TIMEOUT):
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout
    )


def is_git_repo(path: str) -> bool:
    git_dir = os.path.join(path, ".git")
    if os.path.isdir(git_dir):
        return True

    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=path,
        capture_output=True,
        text=True,
        check=False
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def get_branch(path: str) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=path,
        capture_output=True,
        text=True,
        check=False
    )
    return result.stdout.strip() or "(unknown)"


def has_upstream(path: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "@{upstream}"],
        cwd=path,
        capture_output=True,
        text=True,
        check=False
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def classify_pull_result(stdout: str, stderr: str) -> str:
    text = f"{stdout}\n{stderr}".lower()
    if "already up to date" in text or "already up-to-date" in text:
        return "UP_TO_DATE"
    return "UPDATED"


def pull_project(name: str, info: dict) -> tuple[str, str, str]:
    path = info["path"]

    if not os.path.isdir(path):
        return name, "FAILED", f"❌ 路径不存在：{path}"

    if not is_git_repo(path):
        return name, "FAILED", f"❌ 不是 Git 仓库：{path}"

    branch = get_branch(path)

    if not has_upstream(path):
        return name, "FAILED", f"❌ branch={branch}，未配置上游分支，无法执行 git pull"

    try:
        result = run_cmd(["git", "pull", "--ff-only"], cwd=path)

        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()

        if result.returncode != 0:
            return name, "FAILED", (
                f"❌ branch={branch}，pull 失败：\n"
                f"{stderr or stdout or '未知错误'}"
            )

        status = classify_pull_result(stdout, stderr)
        if status == "UP_TO_DATE":
            return name, "UP_TO_DATE", f"ℹ️ branch={branch}，已是最新"

        return name, "UPDATED", f"✅ branch={branch}，已更新：\n{stdout or stderr or 'Fast-forward'}"

    except subprocess.TimeoutExpired:
        return name, "FAILED", f"❌ branch={branch}，执行超时（>{GIT_TIMEOUT}s）"
    except Exception as e:
        return name, "FAILED", f"❌ branch={branch}，运行异常：{e!r}"


def main():
    selected = sys.argv[1:]

    if selected:
        unknown = [name for name in selected if name not in PROJECTS]
        if unknown:
            print(f"❌ 未知项目：{', '.join(unknown)}")
            print(f"可选项目：{', '.join(PROJECTS.keys())}")
            sys.exit(1)

        projects_to_run = {name: PROJECTS[name] for name in selected}
    else:
        projects_to_run = PROJECTS

    workers = min(MAX_WORKERS, len(projects_to_run))
    print(f"🚀 开始并行 git pull，共 {len(projects_to_run)} 个项目，并发数：{workers}\n")

    results = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_name = {
            executor.submit(pull_project, name, info): name
            for name, info in projects_to_run.items()
        }

        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                proj_name, status, msg = future.result()
                icon = {
                    "UPDATED": "✅",
                    "UP_TO_DATE": "ℹ️",
                    "SKIPPED": "⚠️",
                    "FAILED": "❌",
                }.get(status, "•")

                print(f"[{icon}] 项目：{proj_name}")
                print(msg)
                print("-" * 60)
                results.append((proj_name, status))
            except Exception as e:
                print(f"[❌] 项目：{name}")
                print(f"未捕获异常：{e!r}")
                print("-" * 60)
                results.append((name, "FAILED"))

    status_map = {name: status for name, status in results}

    updated = [name for name in projects_to_run if status_map.get(name) == "UPDATED"]
    up_to_date = [name for name in projects_to_run if status_map.get(name) == "UP_TO_DATE"]
    skipped = [name for name in projects_to_run if status_map.get(name) == "SKIPPED"]
    failed = [name for name in projects_to_run if status_map.get(name) == "FAILED"]

    print("\n========== 总结 ==========")
    print(f"✅ 已更新：{len(updated)} 个 -> {', '.join(updated) if updated else '无'}")
    print(f"ℹ️ 已是最新：{len(up_to_date)} 个 -> {', '.join(up_to_date) if up_to_date else '无'}")
    print(f"⚠️ 已跳过：{len(skipped)} 个 -> {', '.join(skipped) if skipped else '无'}")
    print(f"❌ 失败：{len(failed)} 个 -> {', '.join(failed) if failed else '无'}")


if __name__ == "__main__":
    main()
