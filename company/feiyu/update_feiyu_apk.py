import os
import requests
from datetime import datetime
import subprocess
import re
import sys
import webbrowser
import tkinter.messagebox as msgbox  # 提示窗口（macOS/Windows 可用）

# 关闭 InsecureRequestWarning（仍保留 verify=False 的行为）
try:
    requests.packages.urllib3.disable_warnings()  # type: ignore
except Exception:
    pass

# === 配置区 ===
REPO_PATH = "/Users/oncechen/IdeaProjects/feiyu-site"              # ← 项目根目录（git 在这）
DEST_DIR  = os.path.join(REPO_PATH, "apk")                          # APK 放在 repo 里的 apk/
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

# === APK 下载（流式写入） ===
def download_apk():
    ensure_dirs()
    for url in URLS:
        try:
            print(f"🚚 尝试下载: {url}")
            with requests.get(url, timeout=20, verify=False, stream=True) as r:
                if r.status_code == 200:
                    with open(APK_PATH, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1024 * 64):
                            if chunk:
                                f.write(chunk)
                    print("✅ APK 下载成功")
                    return True
                else:
                    print(f"❌ 非 200 响应码：{r.status_code}")
        except requests.exceptions.SSLError as e:
            print(f"❌ SSL 验证错误: {url} - {e}")
        except Exception as e:
            print(f"❌ 下载失败: {url} - {e}")
    return False

# === 版本解析（APK 二进制中找类似 1.2.3(456) 的字样；失败则 fallback） ===
def extract_version(apk_path, fallback_prefix="1.0.0"):
    try:
        with open(apk_path, 'rb') as f:
            content = f.read()
            match = re.search(rb"\d+\.\d+\.\d+\(\d+\)", content)
            if match:
                version = match.group().decode()
                print(f"✅ 从 APK 中提取版本号：{version}")
                return version
    except Exception as e:
        print("❌ 无法解析版本号:", e)

    # 如果无法解析版本，则从文件时间推算版本
    try:
        mtime = os.path.getmtime(apk_path)
        timestamp_str = datetime.fromtimestamp(mtime).strftime("%Y%m%d%H%M")
        fallback_version = f"{fallback_prefix}({timestamp_str})"
    except Exception:
        fallback_version = f"{fallback_prefix}(100)"

    # 如果是交互环境，允许手动输入；否则用 fallback
    if sys.stdin.isatty():
        version = input(f"🔢 请手动输入版本号（默认 {fallback_version}）：").strip()
        if not version:
            version = fallback_version
            print(f"✅ 已使用默认版本号：{version}")
    else:
        version = fallback_version
        print(f"ℹ️ 非交互环境，使用默认版本号：{version}")
    return version

# === 更新 index.js 第一行版本注释 ===
def update_index_js(version):
    today = datetime.now().strftime("%Y/%m/%d")
    new_first_line = f'var _ANDROID_URL = "/apk/{APK_NAME}"; // {today} apk版本: {version}\n'

    # 安全读写（如果文件不存在或为空，直接写入第一行）
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

    print("🛠️ index.js 已更新第一行为：")
    print(new_first_line.strip())

# === Git 提交与打 tag ===
def git_commit(version):
    def run_cmd(cmd):
        result = subprocess.run(cmd, cwd=REPO_PATH, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ 命令失败: {' '.join(cmd)}")
            print(result.stdout)
            print(result.stderr)
            raise SystemExit(result.returncode)
        return result.stdout

    print("🔄 更新远端分支...")
    print(run_cmd(["git", "pull"]))
    print("✅ git pull 成功")

    # add 两个文件
    run_cmd(["git", "add", os.path.relpath(APK_PATH, REPO_PATH)])
    run_cmd(["git", "add", os.path.relpath(INDEX_JS_PATH, REPO_PATH)])

    # 显示将要提交的变更（方便排查）
    print("📋 即将提交的变更：")
    print(run_cmd(["git", "status", "--porcelain"]))

    # 判断是否有 staged 变更
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=REPO_PATH)
    if result.returncode == 0:
        msgbox.showinfo("无更新", "没有需要提交的变更")
        print("⚠️ 没有变更，已跳过提交")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    commit_msg = f"{today} update apk {version}"
    run_cmd(["git", "commit", "-m", commit_msg])
    run_cmd(["git", "push"])
    print("✅ Git 提交完成:", commit_msg)

    # tag：采用 版本号 + 时间戳，避免重复
    tag = f"v{version}-{datetime.now():%Y%m%d%H%M}"
    run_cmd(["git", "tag", tag])
    run_cmd(["git", "push", "origin", tag])
    print(f"🏷️ 已打 tag 并推送成功：{tag}")

    # 跨平台打开 pipelines 页面
    try:
        webbrowser.open("https://git.easydevops.net/it/java-feiyu/feiyu-site/-/pipelines")
        print("🌐 已自动打开 GitLab Pipelines 页面")
    except Exception as e:
        print(f"⚠️ 无法自动打开浏览器：{e}")

# === 主流程 ===
def main():
    print("🚀 开始执行 APK 自动更新流程")
    if not download_apk():
        print("❌ 所有下载链接失败，流程中止")
        return
    version = extract_version(APK_PATH)
    update_index_js(version)
    git_commit(version)

if __name__ == "__main__":
    main()