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
    "e68pc": {
        "path": "/Users/oncechen/IdeaProjects/e68_web_vue/",
        "web_url": "https://e68web01.itomtest.com/",
        "pipeline_url": "https://git.easydevops.net/frontend/e68_web_vue/-/pipelines"
    },
    "e68h5": {
        "path": "/Users/oncechen/IdeaProjects/e68_web_static_vue/",
        "web_url": "https://e68web01.itomtest.com/",
        "pipeline_url": "https://git.easydevops.net/frontend/e68_web_static_vue/-/pipelines"
    },
    "ued": {
        "path": "/Users/oncechen/IdeaProjects/c_ued/WebRoot/",
        "web_url": "https://uedweb01.itomtest.com/mobile/index.jsp",
        "pipeline_url": "https://git.easydevops.net/B2C_DC/ued/web/-/pipelines"
    },
    "tq": {
        "path": "/Users/oncechen/IdeaProjects/c_sportone/web/WebRoot/",
        "web_url": "https://sportoneweb01.itomtest.com/mobile/index.jsp",
        "pipeline_url": "https://git.easydevops.net/B2C_DC/sportone/web/-/pipelines"
    },
    "pt777": {
        "path": "/Users/oncechen/IdeaProjects/c_pt777/WebRoot/",
        "web_url": "https://pt777web01.itomtest.com/mobile/index.jsp",
        "pipeline_url": "https://git.easydevops.net/B2C_DC/pt777/web/-/pipelines"
    },
    "qy": {
        "path": "/Users/oncechen/IdeaProjects/c_qy/web/WebRoot/",
        "web_url": "https://qyweb01.itomtest.com/mobile/index.jsp",
        "pipeline_url": "https://git.easydevops.net/B2C_DC/qy/web/-/pipelines"
    },
    "long8": {
        "path": "/Users/oncechen/IdeaProjects/c_long8/web/WebRoot/",
        "web_url": "https://long8web01.itomtest.com/mobile21/index.jsp",
        "pipeline_url": "https://git.easydevops.net/B2C_DC/long8/web/-/pipelines"
    }
}

EXCLUDES = [
    "dist/",
    "disk/",                 # 如果你是打錯字，可以留著保險
    "build/",                # 可選：常見產出目錄
    "package-lock.json",
    "yarn.lock"
]

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

def ensure_local_ignore(repo_path):
    """把需要忽略的項目寫入 .git/info/exclude（只作用於本機，不會進入版本庫）"""
    exclude_file = os.path.join(repo_path, ".git", "info", "exclude")
    os.makedirs(os.path.dirname(exclude_file), exist_ok=True)
    existing = ""
    if os.path.exists(exclude_file):
        with open(exclude_file, "r", encoding="utf-8") as f:
            existing = f.read()
    to_append = []
    for line in EXCLUDES:
        if line not in existing:
            to_append.append(line)
    if to_append:
        with open(exclude_file, "a", encoding="utf-8") as f:
            f.write("\n# added by commit script\n" + "\n".join(to_append) + "\n")

def get_unstaged_files():
    """維持你的過濾，但補上 disk/ 與 build/"""
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        capture_output=True,
        text=True
    )
    files = result.stdout.strip().splitlines()
    exclude_files = {".DS_Store", "package-lock.json", "yarn.lock"}

    unstaged = []
    for f in files:
        base = os.path.basename(f)
        if base in exclude_files:
            continue
        if f.startswith(("dist/", "disk/", "build/")) or f in ("dist", "disk", "build"):
            continue
        unstaged.append(f)
    return unstaged

def safe_git_add():
    """
    用 pathspec 排除：git add -A ':(exclude)dist' ':(exclude)package-lock.json' ...
    注意：一定要把 . 放在最後，否則排除規則可能無效。
    """
    cmd = [
        "git", "add", "-A",
        ":(exclude)dist", ":(exclude)dist/**",
        ":(exclude)disk", ":(exclude)disk/**",
        ":(exclude)build", ":(exclude)build/**",
        ":(exclude)package-lock.json",
        ":(exclude)yarn.lock",
        ".",
    ]
    subprocess.run(cmd, check=True)


def create_and_push_tag(project_info):
    # 與你原本相同
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

    # ① 先保險：把忽略規則寫進本地 exclude
    ensure_local_ignore(repo_path)

    print("🔄 正在执行 git pull...")
    pull_result = subprocess.run(["git", "pull"])
    if pull_result.returncode != 0:
        print("❌ git pull 失败，请检查网络或远端状态")
        return

    unstaged = get_unstaged_files()
    if unstaged:
        print("\n⚠️ 以下文件尚未加入 Git 暂存区（已排除 dist/disk/build 與 lock 檔）：\n")
        for file in unstaged:
            print(f"  • {file}")
        choice = input("\n➡️ 是否要自动执行安全的 `git add`（會排除 dist/disk/build、package-lock.json、yarn.lock）？ [y/N]: ").strip().lower()
        if choice == 'y':
            # ② 真正 add 的時候使用排除 pathspec
            safe_git_add()
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
    print("请输入项目代号：rb88、jxf、ued、tq、pt777、qy、long8、e68pc、e68h5")
    key = input("👉 项目代号：").strip().lower()
    git_commit_and_tag(key)