import os
import requests
from datetime import datetime
import subprocess
import re
import tkinter.messagebox as msgbox  # 頂部新增

# 配置
DEST_DIR = "/Users/oncechen/IdeaProjects/feiyu-site/apk"
APK_NAME = "flychat_release.apk"
APK_PATH = os.path.join(DEST_DIR, APK_NAME)
INDEX_JS_PATH = "/Users/oncechen/IdeaProjects/feiyu-site/js/index.js"
URLS = [
    "https://feiyu.jzcla.cn/Android/apk/flychat/flychat_release.apk",
    "https://fujkou.com:12828/Android/apk/flychat/flychat_release.apk",
    "https://fujkou.net:12828/Android/apk/flychat/flychat_release.apk",
]

def download_apk():
    for url in URLS:
        try:
            print(f"尝试下载: {url}")
            response = requests.get(url, timeout=10, verify=False)
            if response.status_code == 200:
                with open(APK_PATH, 'wb') as f:
                    f.write(response.content)
                print("✅ 下载成功")
                return True
        except requests.exceptions.SSLError as e:
            print(f"❌ SSL 驗證錯誤: {url} - {e}")
        except Exception as e:
            print(f"❌ 下載失敗: {url} - {e}")
    return False

def extract_version(apk_path, fallback_version=None):
    try:
        with open(apk_path, 'rb') as f:
            content = f.read()
            match = re.search(rb"\d+\.\d+\.\d+\(\d+\)", content)
            if match:
                return match.group().decode()
    except Exception as e:
        print("❌ 无法解析版本号:", e)

    if fallback_version:
        return fallback_version
    else:
        return input("🔢 請手動輸入版本號（格式如 1.0.0(100)）：").strip()

def update_index_js(version):
    today = datetime.now().strftime("%Y/%m/%d")
    with open(INDEX_JS_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_first_line = f'var _ANDROID_URL = "/apk/flychat_release.apk"; // {today} apk版本: {version}\n'
    lines[0] = new_first_line

    with open(INDEX_JS_PATH, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print("🛠️ index.js 已更新第一行為：")
    print(new_first_line.strip())

def git_commit(version):
    os.chdir(DEST_DIR)

    subprocess.run(["git", "add", APK_NAME])
    subprocess.run(["git", "add", INDEX_JS_PATH])

    # 檢查是否有變化
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode == 0:
        msgbox.showinfo("無更新", "沒有可需要的更新")
        print("⚠️ 沒有可需要的更新，已跳過提交")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    message = f"{today} update apk {version}"
    subprocess.run(["git", "commit", "-m", message])
    subprocess.run(["git", "push"])
    print("✅ Git 提交完成:", message)

    tag = f"v{datetime.now().strftime('%Y.%m.%d.%H%M')}"
    subprocess.run(["git", "tag", tag])
    subprocess.run(["git", "push", "origin", tag])
    print(f"🏷️ 已打 tag：{tag} 並推送成功")


def main():
    print("🚀 开始更新 APK...")
    if not download_apk():
        print("❌ 所有下载链接均失败，终止")
        return
    version = extract_version(APK_PATH)
    update_index_js(version)
    git_commit(version)

if __name__ == "__main__":
    main()
