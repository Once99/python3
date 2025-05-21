import os
import requests
from datetime import datetime
import subprocess
import re

# 配置
DEST_DIR = "/Users/oncechen/IdeaProjects/feiyu-site/apk"
APK_NAME = "flychat_release.apk"
APK_PATH = os.path.join(DEST_DIR, APK_NAME)
URLS = [
    "https://feiyu.jzcla.cn/Android/apk/flychat/flychat_release.apk",
    "https://fujkou.com:12828/Android/apk/flychat/flychat_release.apk",
    "https://fujkou.net:12828/Android/apk/flychat/flychat_release.apk",
]

def download_apk():
    for url in URLS:
        try:
            print(f"尝试下载: {url}")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                with open(APK_PATH, 'wb') as f:
                    f.write(response.content)
                print("✅ 下载成功")
                return True
        except Exception as e:
            print(f"❌ 下载失败: {url} - {e}")
    return False

def extract_version(apk_path):
    try:
        with open(apk_path, 'rb') as f:
            content = f.read()
            match = re.search(rb"\d+\.\d+\.\d+\(\d+\)", content)
            if match:
                return match.group().decode()
    except Exception as e:
        print("❌ 无法解析版本号:", e)
    return "unknown-version"

def git_commit(version):
    os.chdir(DEST_DIR)

    # 提交 APK 文件
    subprocess.run(["git", "add", APK_NAME])
    today = datetime.now().strftime("%Y-%m-%d")
    message = f"{today} update apk {version}"
    subprocess.run(["git", "commit", "-m", message])
    subprocess.run(["git", "push"])
    print("✅ Git 提交完成:", message)

    # === 添加自动打 Tag ===
    tag = f"v{datetime.now().strftime('%Y.%m.%d.%H%M')}"
    subprocess.run(["git", "tag", tag])
    subprocess.run(["git", "push", "origin", tag])
    print(f"🏷️ 已打 tag：{tag} 并推送成功")

def main():
    print("🚀 开始更新 APK...")
    if not download_apk():
        print("❌ 所有下载链接均失败，终止")
        return
    version = extract_version(APK_PATH)
    git_commit(version)

if __name__ == "__main__":
    main()
