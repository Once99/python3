import os
import subprocess
from datetime import datetime

# === 项目配置：根据实际情况维护 ===
PROJECTS = {
    "rb88": {
        "path": "/Users/oncechen/IdeaProjects/rb88_web_vue/",
        "web_url": "https://rb88vue.nntitestserver.com/",
        "pipeline_url": "https://git.easydevops.net/frontend/rb88_web_vue/-/pipelines"
    },
    "jxf": {
        "path": "/Users/oncechen/IdeaProjects/jxf_web_static_vue/",
        "web_url": "https://jxfvue.nntitestserver.com/",
        "pipeline_url": "https://git.easydevops.net/frontend/jxf_web_static_vue/-/pipelines"
    },
    "ued": {
        "path": "/Users/oncechen/IdeaProjects/c_ued/WebRoot/",
        "web_url": "https://uedweb01.itomtest.com/mobile/app/fundsManage.jsp",
        "pipeline_url": "https://git.easydevops.net/B2C_DC/ued/web/-/pipelines"
    },
    "tq": {
        "path": "/Users/oncechen/IdeaProjects/c_sportone/web/WebRoot/",
        "web_url": "https://sportoneweb01.itomtest.com/mobile/app/fundsManage.jsp",
        "pipeline_url": "https://git.easydevops.net/B2C_DC/sportone/web/-/pipelines"
    },
    "pt777": {
        "path": "/Users/oncechen/IdeaProjects/c_pt777/web/WebRoot/",
        "web_url": "https://pt777web01.itomtest.com/mobile/app/fundsManage.jsp",
        "pipeline_url": "https://git.easydevops.net/B2C_DC/pt777/web/-/pipelines"
    },
    "qy": {
        "path": "/Users/oncechen/IdeaProjects/c_qy/web/WebRoot/",
        "web_url": "https://qyweb01.itomtest.com/mobile/app/fundsManage.jsp",
        "pipeline_url": "https://git.easydevops.net/B2C_DC/qy/web/-/pipelines"
    },
    "long8": {
        "path": "/Users/oncechen/IdeaProjects/c_long8/web/WebRoot/",
        "web_url": "https://long8web01.itomtest.com/mobile/app/fundsManage.jsp",
        "pipeline_url": "https://git.easydevops.net/B2C_DC/long8/web/-/pipelines"
    }
}

# 使用当前脚本所在目录的 txt 文件缓存上次 commit 信息
LAST_COMMIT_FILE = os.path.join(os.path.dirname(__file__), "last_commit_msg.txt")

def load_last_commit_message():
    if os.path.exists(LAST_COMMIT_FILE):
        with open(LAST_COMMIT_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    else:
        # 文件不存在，自动创建并写入默认内容
        with open(LAST_COMMIT_FILE, 'w', encoding='utf-8') as f:
            f.write("日常维护")
        return "日常维护"

def save_last_commit_message(message):
    with open(LAST_COMMIT_FILE, 'w', encoding='utf-8') as f:
        f.write(message.strip())

def is_git_repo():
    return subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True).returncode == 0


def has_commit():
    return subprocess.run(["git", "rev-parse", "--verify", "HEAD"], capture_output=True).returncode == 0


def has_staged_changes():
    return subprocess.run(["git", "diff", "--staged", "--quiet"]).returncode != 0


def get_unstaged_files():
    result = subprocess.run(["git", "diff", "--name-only"], capture_output=True, text=True)
    files = result.stdout.strip().splitlines()
    return [f for f in files if os.path.basename(f) != ".DS_Store"]


def create_and_push_tag(project_info):
    if not has_commit():
        print("⚠️ 当前仓库没有任何提交，无法打 tag！请先至少提交一次。")
        return

    tag = f"v{datetime.now().strftime('%Y.%m.%d.%H%M')}"
    subprocess.run(["git", "tag", tag], check=True)
    subprocess.run(["git", "push", "origin", tag], check=True)
    print(f"\n🏷️ 已打 tag：{tag} 并推送成功")

    subprocess.run(f"echo '{project_info['web_url']}' | pbcopy", shell=True)
    print(f"📋 已自动复制网址到剪贴板：{project_info['web_url']}")

    subprocess.run(["open", project_info["pipeline_url"]], check=True)
    print(f"🌐 已自动打开 GitLab Pipelines 页面：{project_info['pipeline_url']}\n")


def git_commit_and_tag(project_key):
    if project_key not in PROJECTS:
        print(f"❌ 未知项目代号：{project_key}")
        return

    project_info = PROJECTS[project_key]
    repo_path = project_info["path"]

    os.chdir(repo_path)

    if not is_git_repo():
        print("❌ 当前目录不是 Git 仓库，请确认路径是否正确：", repo_path)
        return

    print("🔄 正在执行 git pull...")
    pull_result = subprocess.run(["git", "pull"])
    if pull_result.returncode != 0:
        print("❌ git pull 失败，请检查网络或远端状态")
        return

    unstaged = get_unstaged_files()
    if unstaged:
        print("\n⚠️ 以下文件尚未加入 Git 暂存区（已排除 .DS_Store）：\n")
        for file in unstaged:
            print(f"  • {file}")
        choice = input("\n➡️ 是否要自动执行 `git add .`？ [y/N]: ").strip().lower()
        if choice == 'y':
            subprocess.run(["git", "add", "."], check=True)
        else:
            print("⚠️ 未加入暂存区，跳过 commit 流程")

    if has_staged_changes():
        last_msg = load_last_commit_message()
        message = input(f"\n💬 请输入 commit 信息（默认：{last_msg}）：").strip() or last_msg
        save_last_commit_message(message)
        try:
            subprocess.run(["git", "commit", "-m", message], check=True)
            subprocess.run(["git", "push"], check=True)
            print(f"\n✅ 已提交并推送成功：{message}")
            create_and_push_tag(project_info)
        except subprocess.CalledProcessError:
            print("❌ commit 或 push 发生错误，流程中止")
    else:
        print("\n📦 没有文件需要 commit")
        choice = input("是否仍要打 Git Tag？ [y/N]: ").strip().lower()
        if choice == 'y':
            create_and_push_tag(project_info)
        else:
            print("✅ 任务结束，未进行 tag 操作")


if __name__ == "__main__":
    print("请输入项目代号：rb88、jxf、ued、tq、pt777、qy、long8")
    key = input("👉 项目代号：").strip().lower()
    git_commit_and_tag(key)