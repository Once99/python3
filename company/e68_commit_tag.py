import os
import subprocess
from datetime import datetime

PROJECTS = {
    "e68_web_vue": {
        "path": "/Users/oncechen/IdeaProjects/e68_web_vue/",
        "web_url": "https://e68vue.nntitestserver.com/",
        "pipeline_url": "https://git.easydevops.net/frontend/e68_web_vue/-/pipelines"
    },
    "e68_web_static_vue": {
        "path": "/Users/oncechen/IdeaProjects/e68_web_static_vue/",
        "web_url": "https://e68staticvue.nntitestserver.com/",
        "pipeline_url": "https://git.easydevops.net/frontend/e68_web_static_vue/-/pipelines"
    }
}


def run_git_cmd(args, **kwargs):
    return subprocess.run(["git"] + args, **kwargs)


def is_git_repo():
    return run_git_cmd(["rev-parse", "--is-inside-work-tree"], capture_output=True).returncode == 0


def has_commit():
    return run_git_cmd(["rev-parse", "--verify", "HEAD"], capture_output=True).returncode == 0


def has_staged_changes():
    return run_git_cmd(["diff", "--staged", "--quiet"]).returncode != 0


def get_unstaged_files():
    result = run_git_cmd(["diff", "--name-only"], capture_output=True, text=True)
    return [f for f in result.stdout.strip().splitlines() if os.path.basename(f) != ".DS_Store"]


def create_and_push_tag(project_info):
    if not has_commit():
        print("⚠️ 当前仓库没有提交，无法打 tag！")
        return

    tag = f"v{datetime.now().strftime('%Y.%m.%d.%H%M')}"
    run_git_cmd(["tag", tag], check=True)
    run_git_cmd(["push", "origin", tag], check=True)

    print(f"🏷️ 已打 tag：{tag}")

    subprocess.run(f"echo '{project_info['web_url']}' | pbcopy", shell=True)
    print(f"📋 已复制网址到剪贴簿：{project_info['web_url']}")

    subprocess.run(["open", project_info["pipeline_url"]], check=True)
    print(f"🌐 打开 Pipelines 页面：{project_info['pipeline_url']}\n")


def handle_project(project_key):
    project_info = PROJECTS[project_key]
    repo_path = project_info["path"]
    print(f"\n📁 处理项目：{project_key}（{repo_path}）")

    os.chdir(repo_path)

    if not is_git_repo():
        print("❌ 不是 Git 仓库，跳过")
        return

    print("🔄 执行 git pull...")
    if run_git_cmd(["pull"]).returncode != 0:
        print("❌ git pull 失败")
        return

    unstaged = get_unstaged_files()
    if unstaged:
        print("⚠️ 检测到未暂存变更：")
        for f in unstaged:
            print(f" • {f}")
        run_git_cmd(["add", "."], check=True)

    if has_staged_changes():
        msg = input(f"\n💬 [{project_key}] 输入 commit 信息（默认：日常维护）：").strip() or "日常维护"
        try:
            run_git_cmd(["commit", "-m", msg], check=True)
            run_git_cmd(["push"], check=True)
            print("✅ 已提交并推送成功")
            create_and_push_tag(project_info)
        except subprocess.CalledProcessError:
            print("❌ commit 或 push 失败")
    else:
        print("✅ 无需提交")
        choice = input("是否仍要打 tag？[y/N]: ").strip().lower()
        if choice == 'y':
            create_and_push_tag(project_info)


if __name__ == "__main__":
    print("🚀 准备同时处理两个项目：e68_web_vue 与 e68_web_static_vue")
    handle_project("e68_web_vue")
    handle_project("e68_web_static_vue")
    print("\n✅ 所有项目处理完毕！")