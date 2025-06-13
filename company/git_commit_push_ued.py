import os
import subprocess
from datetime import datetime

def has_staged_changes():
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    return result.returncode != 0

def get_unstaged_files():
    result = subprocess.run(["git", "diff", "--name-only"], capture_output=True, text=True)
    files = result.stdout.strip().splitlines()
    return [f for f in files if os.path.basename(f) != ".DS_Store"]

def git_commit_and_tag():
    repo_path = "/Users/oncechen/IdeaProjects/c_ued"
    os.chdir(repo_path)

    # 檢查是否有 staged 變更
    if not has_staged_changes():
        unstaged = get_unstaged_files()
        if unstaged:
            print("⚠️ 偵測到以下未 staged 的變更（已略過 .DS_Store）：\n")
            for file in unstaged:
                print(f" - {file}")
            choice = input("\n是否要自動執行 git add . ? [y/N]: ").strip().lower()
            if choice == 'y':
                subprocess.run(["git", "add", "."])
            else:
                print("❌ 未加入 staged 區，結束")
                return

        if not has_staged_changes():
            print("⚠️ 即使 add 之後也沒有可提交的內容，跳過")
            return

    message = input("💬 請輸入 commit 訊息（預設：日常维护）：").strip()
    if not message:
        message = "日常维护"

    subprocess.run(["git", "commit", "-m", message])
    subprocess.run(["git", "push"])
    print(f"✅ 已提交並推送完成：{message}")

    tag = f"v{datetime.now().strftime('%Y.%m.%d.%H%M')}"
    subprocess.run(["git", "tag", tag])
    subprocess.run(["git", "push", "origin", tag])
    print(f"🏷️ 已打 tag：{tag} 並推送成功")

    # ✅ 自動複製網址到剪貼簿
    subprocess.run("echo 'https://uedweb01.itomtest.com/mobile/app/fundsManage.jsp' | pbcopy", shell=True)
    print("📋 已自動複製網址到剪貼簿：https://uedweb01.itomtest.com/mobile/app/fundsManage.jsp")

    # ✅ 自動打開 GitLab Pipelines 頁面
    subprocess.run(["open", "https://git.easydevops.net/B2C_DC/ued/web/-/pipelines"])
    print("🌐 已自動開啟 GitLab 頁面：https://git.easydevops.net/B2C_DC/ued/web/")

if __name__ == "__main__":
    git_commit_and_tag()