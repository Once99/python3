import os
import requests
from datetime import datetime
import subprocess
import re
import tkinter.messagebox as msgbox  # 提示視窗（macOS/Windows 可用）

# === 配置區 ===
DEST_DIR = "/Users/oncechen/IdeaProjects/feiyu-site/apk"
APK_NAME = "flychat_release.apk"
APK_PATH = os.path.join(DEST_DIR, APK_NAME)
INDEX_JS_PATH = "/Users/oncechen/IdeaProjects/feiyu-site/js/index.js"
URLS = [
    "https://feiyu.jzcla.cn/Android/apk/flychat/flychat_release.apk",
    "https://fujkou.com:12828/Android/apk/flychat/flychat_release.apk",
    "https://fujkou.net:12828/Android/apk/flychat/flychat_release.apk",
]

# === APK 下载 ===
def download_apk():
    for url in URLS:
        try:
            print(f"🚚 嘗試下載: {url}")
            response = requests.get(url, timeout=10, verify=False)
            if response.status_code == 200:
                with open(APK_PATH, 'wb') as f:
                    f.write(response.content)
                print("✅ APK 下載成功")
                return True
        except requests.exceptions.SSLError as e:
            print(f"❌ SSL 驗證錯誤: {url} - {e}")
        except Exception as e:
            print(f"❌ 下載失敗: {url} - {e}")
    return False

# === 版本解析 ===
def extract_version(apk_path, fallback_prefix="1.0.0"):
    try:
        with open(apk_path, 'rb') as f:
            content = f.read()
            match = re.search(rb"\d+\.\d+\.\d+\(\d+\)", content)
            if match:
                version = match.group().decode()
                print(f"✅ 從 APK 中擷取版本號：{version}")
                return version
    except Exception as e:
        print("❌ 無法解析版本號:", e)

    # 若無法解析版本，則從檔案時間推算版本
    try:
        mtime = os.path.getmtime(apk_path)
        timestamp_str = datetime.fromtimestamp(mtime).strftime("%Y%m%d%H%M")
        fallback_version = f"{fallback_prefix}({timestamp_str})"
    except Exception:
        fallback_version = f"{fallback_prefix}(100)"

    version = input(f"🔢 請手動輸入版本號（預設為 {fallback_version}）：").strip()
    if not version:
        version = fallback_version
        print(f"✅ 已使用預設版本號：{version}")
    return version

# === 更新 index.js 第一行版本註解 ===
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

# === Git 提交與打 tag ===
def git_commit(version):
    os.chdir(DEST_DIR)

    subprocess.run(["git", "add", APK_NAME])
    subprocess.run(["git", "add", INDEX_JS_PATH])

    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode == 0:
        msgbox.showinfo("無更新", "沒有可需要的更新")
        print("⚠️ 沒有變更，已跳過提交")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    commit_msg = f"{today} update apk {version}"
    subprocess.run(["git", "commit", "-m", commit_msg])
    subprocess.run(["git", "push"])
    print("✅ Git 提交完成:", commit_msg)

    tag = f"v{datetime.now().strftime('%Y.%m.%d.%H%M')}"
    subprocess.run(["git", "tag", tag])
    subprocess.run(["git", "push", "origin", tag])
    print(f"🏷️ 已打 tag：{tag} 並推送成功")

    subprocess.run(["open", "https://git.easydevops.net/it/java-feiyu/feiyu-site/-/pipelines"])
    print("🌐 已自動開啟 GitLab Pipelines 頁面")

# === 主流程 ===
def main():
    print("🚀 開始執行 APK 自動更新流程")
    if not download_apk():
        print("❌ 所有下載連結失敗，流程中止")
        return
    version = extract_version(APK_PATH)
    update_index_js(version)
    git_commit(version)

if __name__ == "__main__":
    main()