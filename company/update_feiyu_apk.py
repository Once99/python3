import os
import requests
from datetime import datetime
import subprocess
import re
import sys
import webbrowser
import tkinter.messagebox as msgbox  # 提示視窗（macOS/Windows 可用）

# 關閉 InsecureRequestWarning（仍保留 verify=False 的行為）
try:
    requests.packages.urllib3.disable_warnings()  # type: ignore
except Exception:
    pass

# === 配置區 ===
REPO_PATH = "/Users/oncechen/IdeaProjects/feiyu-site"              # ← 專案根目錄（git 在這）
DEST_DIR  = os.path.join(REPO_PATH, "apk")                          # APK 放在 repo 裡的 apk/
APK_NAME  = "flychat_release.apk"
APK_PATH  = os.path.join(DEST_DIR, APK_NAME)
INDEX_JS_PATH = os.path.join(REPO_PATH, "js/index.js")

URLS = [
    "https://feiyu.equgou.com/Android/apk/flychat/flychat_release.apk",
    "https://fujkou.com:12828/Android/apk/flychat/flychat_release.apk",
    "https://fujkou.net:12828/Android/apk/flychat/flychat_release.apk",
]

def ensure_dirs():
    os.makedirs(DEST_DIR, exist_ok=True)

# === APK 下載（串流寫入） ===
def download_apk():
    ensure_dirs()
    for url in URLS:
        try:
            print(f"🚚 嘗試下載: {url}")
            with requests.get(url, timeout=20, verify=False, stream=True) as r:
                if r.status_code == 200:
                    with open(APK_PATH, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1024 * 64):
                            if chunk:
                                f.write(chunk)
                    print("✅ APK 下載成功")
                    return True
                else:
                    print(f"❌ 非 200 回應碼：{r.status_code}")
        except requests.exceptions.SSLError as e:
            print(f"❌ SSL 驗證錯誤: {url} - {e}")
        except Exception as e:
            print(f"❌ 下載失敗: {url} - {e}")
    return False

# === 版本解析（APK 二進位內找類似 1.2.3(456) 的字樣；失敗則 fallback） ===
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

    # 若是非互動環境，直接用 fallback；否則允許手動輸入
    if sys.stdin.isatty():
        version = input(f"🔢 請手動輸入版本號（預設為 {fallback_version}）：").strip()
        if not version:
            version = fallback_version
            print(f"✅ 已使用預設版本號：{version}")
    else:
        version = fallback_version
        print(f"ℹ️ 非互動環境，使用預設版本號：{version}")
    return version

# === 更新 index.js 第一行版本註解 ===
def update_index_js(version):
    today = datetime.now().strftime("%Y/%m/%d")
    new_first_line = f'var _ANDROID_URL = "/apk/{APK_NAME}"; // {today} apk版本: {version}\n'

    # 安全讀寫（若檔案不存在或為空，直接寫入第一行）
    lines = []
    if os.path.exists(INDEX_JS_PATH):
        with open(INDEX_JS_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

    if lines:
        lines[0] = new_first_line
    else:
        lines = [new_first_line]

    with open(INDEX_JS_PATH, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print("🛠️ index.js 已更新第一行為：")
    print(new_first_line.strip())

# === Git 提交與打 tag ===
def git_commit(version):
    def run_cmd(cmd):
        result = subprocess.run(cmd, cwd=REPO_PATH, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ 命令失敗: {' '.join(cmd)}")
            print(result.stdout)
            print(result.stderr)
            raise SystemExit(result.returncode)
        return result.stdout

    print("🔄 更新遠端分支...")
    print(run_cmd(["git", "pull"]))
    print("✅ git pull 成功")

    # add 兩個檔
    run_cmd(["git", "add", os.path.relpath(APK_PATH, REPO_PATH)])
    run_cmd(["git", "add", os.path.relpath(INDEX_JS_PATH, REPO_PATH)])

    # 顯示將要提交的變更（方便排查）
    print("📋 即將提交的變更：")
    print(run_cmd(["git", "status", "--porcelain"]))

    # 判斷是否有 staged 變更
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=REPO_PATH)
    if result.returncode == 0:
        msgbox.showinfo("無更新", "沒有需要提交的變更")
        print("⚠️ 沒有變更，已跳過提交")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    commit_msg = f"{today} update apk {version}"
    run_cmd(["git", "commit", "-m", commit_msg])
    run_cmd(["git", "push"])
    print("✅ Git 提交完成:", commit_msg)

    # tag：採用 版本號 + 時間戳，避免重複
    tag = f"v{version}-{datetime.now():%Y%m%d%H%M}"
    run_cmd(["git", "tag", tag])
    run_cmd(["git", "push", "origin", tag])
    print(f"🏷️ 已打 tag 並推送成功：{tag}")

    # 跨平台開啟 pipelines 頁面
    try:
        webbrowser.open("https://git.easydevops.net/it/java-feiyu/feiyu-site/-/pipelines")
        print("🌐 已自動開啟 GitLab Pipelines 頁面")
    except Exception as e:
        print(f"⚠️ 無法自動開啟瀏覽器：{e}")

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