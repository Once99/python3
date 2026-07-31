# -*- coding: utf-8 -*-
import os
import json
import time
import shutil
import requests
import subprocess
from datetime import datetime

# =================== 配置 ===================
REPO_PATH_1 = "/Users/oncechen/IdeaProjects/site-dolphin"
REPO_PATH_2 = "/Applications/XAMPP/xamppfiles/htdocs/site-dolphin"

APK_NAME = "94chat.apk"

URLS = [
    "https://94chat-3.equgou.com/Android/apk/94chat.apk"
]

# 关闭 insecure warning
try:
    requests.packages.urllib3.disable_warnings()
except:
    pass

# =================== 防缓存请求头 ===================
HEADERS = {
    "Cache-Control": "no-cache, no-store, max-age=0, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}

def with_cache_bust(url: str) -> str:
    ts = int(time.time())
    joiner = "&" if "?" in url else "?"
    return f"{url}{joiner}_t={ts}"

# =================== 工具方法 ===================
def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)

def run_cmd(repo_path: str, cmd: list[str]) -> str:
    """执行命令（cwd=repo_path）"""
    p = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
    if p.returncode != 0:
        print("[Cmd Error]", repo_path, ">", " ".join(cmd))
        print(p.stdout)
        print(p.stderr)
        raise SystemExit(p.returncode)
    return p.stdout

def atomic_write_json(path: str, data: dict):
    """稳定写入 JSON（避免损坏）"""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)

def atomic_copy(src: str, dst: str):
    """原子复制（先 copy 到 tmp，再 replace）"""
    ensure_dir(os.path.dirname(dst))
    tmp = dst + ".tmp"
    shutil.copy2(src, tmp)
    os.replace(tmp, dst)

def get_paths(repo_path: str):
    """返回 (apk_dir, apk_path, version_json_path)"""
    apk_dir = os.path.join(repo_path, "apk")
    apk_path = os.path.join(apk_dir, APK_NAME)
    ver_path = os.path.join(repo_path, "version.json")
    return apk_dir, apk_path, ver_path

# =================== Git：干净检查 & pull ===================
def ensure_clean_worktree(repo_path: str):
    dirty = subprocess.run(["git", "diff", "--quiet"], cwd=repo_path).returncode != 0
    dirty_cached = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo_path).returncode != 0
    if dirty or dirty_cached:
        print(f"❌ {repo_path} 检测到工作区/暂存区有未提交变更，已中止。")
        print(run_cmd(repo_path, ["git", "status"]))
        raise SystemExit(2)

def git_pull_safe(repo_path: str):
    """
    pull 策略：先 ff-only，失败再 rebase
    """
    ensure_clean_worktree(repo_path)

    print(f"🔄 git pull (--ff-only)  @ {repo_path}")
    try:
        print(run_cmd(repo_path, ["git", "pull", "--ff-only"]))
    except SystemExit:
        print(f"⚠️ 分叉分支，改用 git pull --rebase  @ {repo_path}")
        print(run_cmd(repo_path, ["git", "pull", "--rebase"]))

# =================== 2. 下载 APK（写 repo1） ===================
def download_apk_to(repo_apk_path: str) -> bool:
    ensure_dir(os.path.dirname(repo_apk_path))
    tmp_path = repo_apk_path + ".tmp"

    for url in URLS:
        try:
            busted_url = with_cache_bust(url)
            print("🚚 下载(避缓存):", busted_url)

            with requests.get(
                    busted_url,
                    timeout=30,
                    verify=False,
                    stream=True,
                    headers=HEADERS
            ) as r:
                if r.status_code != 200:
                    print("❌ 响应码:", r.status_code)
                    continue

                with open(tmp_path, "wb") as f:
                    for chunk in r.iter_content(1024 * 64):
                        if chunk:
                            f.write(chunk)

                # APK/ZIP 头校验：PK
                with open(tmp_path, "rb") as f:
                    if f.read(2) != b"PK":
                        print("❌ 下载内容疑似不是 APK（文件头不是 PK），可能返回了错误页/缓存页")
                        try:
                            os.remove(tmp_path)
                        except:
                            pass
                        continue

                os.replace(tmp_path, repo_apk_path)
                size_mb = os.path.getsize(repo_apk_path) / 1024 / 1024
                print(f"✅ APK 下载成功并已替换：{repo_apk_path} ({size_mb:.2f} MB)")
                return True

        except Exception as e:
            print("❌ 下载失败:", e)

    try:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    except:
        pass

    return False

# =================== 3. 更新 version.json（保留 assets） ===================
def load_version_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def update_version_json(path: str, version: str):
    data = load_version_json(path)
    assets = data.get("assets", {"css": [], "js": []})
    new_data = {"version": version, "assets": assets}
    atomic_write_json(path, new_data)

def generate_version() -> str:
    version = datetime.now().strftime("%Y%m%d%H%M%S")
    print("✅ 生成版本号:", version)
    return version

# =================== 4. Git commit + push（两个 repo 都做） ===================
def git_commit_push(repo_path: str, file_paths: list[str], version: str):
    run_cmd(repo_path, ["git", "add"] + file_paths)

    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo_path).returncode == 0:
        print(f"⚠️ {repo_path} 无变更，跳过提交")
        return

    msg = f"{datetime.now():%Y-%m-%d} update apk {version}"
    run_cmd(repo_path, ["git", "commit", "-m", msg])
    run_cmd(repo_path, ["git", "push"])
    print(f"✅ {repo_path} 提交并推送完成：{msg}")

# =================== 主流程（按你要求顺序） ===================
def main():
    print("🚀 APK 自动更新流程开始（双目录）...")

    # paths
    _, apk1, ver1 = get_paths(REPO_PATH_1)
    _, apk2, ver2 = get_paths(REPO_PATH_2)

    # 1) 两个目录先 pull
    git_pull_safe(REPO_PATH_1)
    git_pull_safe(REPO_PATH_2)

    # 2) 下载最新 apk（写 repo1），同步到 repo2
    if not download_apk_to(apk1):
        print("❌ APK 下载失败，退出")
        return
    atomic_copy(apk1, apk2)

    # 3) 生成版本号，更新两边 version.json（保持一致）
    version = generate_version()
    update_version_json(ver1, version)
    update_version_json(ver2, version)

    # 4) 两个目录 commit + push
    rel_apk1 = os.path.relpath(apk1, REPO_PATH_1)
    rel_ver1 = os.path.relpath(ver1, REPO_PATH_1)
    git_commit_push(REPO_PATH_1, [rel_apk1, rel_ver1], version)

    rel_apk2 = os.path.relpath(apk2, REPO_PATH_2)
    rel_ver2 = os.path.relpath(ver2, REPO_PATH_2)
    git_commit_push(REPO_PATH_2, [rel_apk2, rel_ver2], version)

    # 5) 最后两个目录再 pull 一次同步
    git_pull_safe(REPO_PATH_1)
    git_pull_safe(REPO_PATH_2)

    print("✅ 全流程完成 ✅")

if __name__ == "__main__":
    main()
