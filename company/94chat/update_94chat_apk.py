# -*- coding: utf-8 -*-
import os
import json
import time
import requests
import subprocess
from datetime import datetime

# =================== 配置 ===================
REPO_PATH = "/Users/oncechen/IdeaProjects/site-dolphin"
DEST_DIR  = os.path.join(REPO_PATH, "apk")
APK_NAME  = "94chat.apk"
APK_PATH  = os.path.join(DEST_DIR, APK_NAME)

VERSION_JSON_PATH = os.path.join(REPO_PATH, "version.json")

URLS = [
    "https://94chat.equgou.com/Android/apk/94chat.apk"
]

# 关闭 insecure warning
try:
    requests.packages.urllib3.disable_warnings()
except:
    pass


# =================== 工具方法 ===================
def ensure_dir(p):
    os.makedirs(p, exist_ok=True)


def run_cmd(cmd):
    """执行 git 命令"""
    p = subprocess.run(cmd, cwd=REPO_PATH, capture_output=True, text=True)
    if p.returncode != 0:
        print("[Git Error]", p.stdout, p.stderr)
        raise SystemExit(p.returncode)
    return p.stdout


def atomic_write_json(path, data):
    """稳定写入 JSON（避免损坏）"""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


# =================== 1. 下载 APK ===================
def download_apk():
    ensure_dir(DEST_DIR)
    for url in URLS:
        try:
            print("🚚 下载:", url)
            with requests.get(url, timeout=20, verify=False, stream=True) as r:
                if r.status_code == 200:
                    with open(APK_PATH, "wb") as f:
                        for chunk in r.iter_content(1024 * 64):
                            if chunk:
                                f.write(chunk)
                    print("✅ APK 下载成功")
                    return True
                else:
                    print("❌ 响应码:", r.status_code)
        except Exception as e:
            print("❌ 下载失败:", e)
    return False


# =================== 2. 生成版本号 ===================
def generate_version():
    """
    固定格式：YYYYMMDDHHMMSS
    示例：20251111191530
    """
    version = datetime.now().strftime("%Y%m%d%H%M%S")
    print("✅ 生成版本号:", version)
    return version


# =================== 3. 更新 version.json ===================
def load_version_json():
    if not os.path.exists(VERSION_JSON_PATH):
        return {}
    try:
        with open(VERSION_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def update_version_json(version):
    data = load_version_json()

    # 保留 assets，不动结构
    assets = data.get("assets", {"css": [], "js": []})

    new_data = {
        "version": version,
        "assets": assets
    }

    atomic_write_json(VERSION_JSON_PATH, new_data)

    print("✅ version.json 已更新：")
    print(json.dumps(new_data, indent=2, ensure_ascii=False))


# =================== 4. Git 提交 ===================
def git_commit_and_tag(version):
    print("🔄 git pull...")
    print(run_cmd(["git", "pull"]))

    rel_apk = os.path.relpath(APK_PATH, REPO_PATH)
    rel_ver = os.path.relpath(VERSION_JSON_PATH, REPO_PATH)

    run_cmd(["git", "add", rel_apk, rel_ver])

    # 无变更跳过
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=REPO_PATH).returncode == 0:
        print("⚠️ 无变更，跳过提交")
        return

    msg = f"{datetime.now():%Y-%m-%d} update apk {version}"
    run_cmd(["git", "commit", "-m", msg])
    run_cmd(["git", "push"])

    print("✅ Git 提交完成:", msg)

    # tag 使用 vYYYYMMDDHHMMSS
    tag = f"v{version}"
    run_cmd(["git", "tag", tag])
    run_cmd(["git", "push", "origin", tag])
    print("🏷️ tag 推送成功：", tag)


# =================== 主流程 ===================
def main():
    print("🚀 APK 自动更新流程开始...")

    if not download_apk():
        print("❌ APK 下载失败，退出")
        return

    version = generate_version()
    update_version_json(version)
    git_commit_and_tag(version)

    print("✅ 全流程完成 ✅")


if __name__ == "__main__":
    main()