# -*- coding: utf-8 -*-
import os
import json
import time
import shutil
import requests
import subprocess
from datetime import datetime

# =================== 配置 ===================
REPO_PATH_1 = "/Users/oncechen/IdeaProjects/feiyu-site"
REPO_PATH_2 = "/Applications/XAMPP/xamppfiles/htdocs/feiyu-site"

APK_NAME = "flychat_release.apk"
URLS = [
    "https://feiyu-02.equgou.com/Android/apk/flychat/flychat_release.apk"
]

# 防缓存请求头
HEADERS = {
    "Cache-Control": "no-cache, no-store, max-age=0, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}

# 关闭 insecure warning
try:
    requests.packages.urllib3.disable_warnings()
except:
    pass


# =================== 工具方法 ===================
def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)


def run_cmd(repo_path: str, cmd: list[str]) -> str:
    p = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
    if p.returncode != 0:
        print("[Cmd Error]", repo_path, ">", " ".join(cmd))
        print(p.stdout)
        print(p.stderr)
        raise SystemExit(p.returncode)
    return p.stdout


def ensure_clean_worktree(repo_path: str):
    dirty = subprocess.run(["git", "diff", "--quiet"], cwd=repo_path).returncode != 0
    dirty_cached = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo_path).returncode != 0
    if dirty or dirty_cached:
        print(f"❌ {repo_path} 检测到工作区或暂存区有未提交变更，已中止。")
        print(run_cmd(repo_path, ["git", "status"]))
        raise SystemExit(2)


def git_pull_safe(repo_path: str):
    ensure_clean_worktree(repo_path)

    print(f"🔄 git pull (--ff-only)  @ {repo_path}")
    try:
        print(run_cmd(repo_path, ["git", "pull", "--ff-only"]))
    except SystemExit:
        print(f"⚠️ 分叉分支，改用 git pull --rebase  @ {repo_path}")
        print(run_cmd(repo_path, ["git", "pull", "--rebase"]))


def atomic_write_json(path: str, data: dict):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def atomic_copy(src: str, dst: str):
    ensure_dir(os.path.dirname(dst))
    tmp = dst + ".tmp"
    shutil.copy2(src, tmp)
    os.replace(tmp, dst)


def with_cache_bust(url: str) -> str:
    ts = int(time.time())
    joiner = "&" if "?" in url else "?"
    return f"{url}{joiner}_t={ts}"


# =================== 路径（两个 repo 内一致结构） ===================
def get_paths(repo_path: str):
    apk_dir = os.path.join(repo_path, "apk")
    apk_path = os.path.join(apk_dir, APK_NAME)
    ver_path = os.path.join(repo_path, "version.json")
    return apk_dir, apk_path, ver_path


# =================== 2. 下载 APK（写 repo1，然后同步到 repo2） ===================
def download_apk_to_repo1(repo1_apk_path: str) -> bool:
    ensure_dir(os.path.dirname(repo1_apk_path))
    tmp_path = repo1_apk_path + ".tmp"

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

                # APK/ZIP 头校验（避免拿到 HTML 错误页）
                with open(tmp_path, "rb") as f:
                    if f.read(2) != b"PK":
                        print("❌ 下载内容疑似不是 APK（文件头不是 PK），可能返回错误页/缓存页")
                        try:
                            os.remove(tmp_path)
                        except:
                            pass
                        continue

                os.replace(tmp_path, repo1_apk_path)
                size_mb = os.path.getsize(repo1_apk_path) / 1024 / 1024
                print(f"✅ APK 下载成功：{repo1_apk_path} ({size_mb:.2f} MB)")
                return True

        except Exception as e:
            print("❌ 下载失败:", e)

    try:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    except:
        pass

    return False


# =================== 3. 更新 version.json（两个 repo 都要一致） ===================
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
    return datetime.now().strftime("%Y%m%d%H%M%S")


# =================== 4. 两个 repo commit + push ===================
def git_commit_push(repo_path: str, files_to_add: list[str], version: str) -> bool:
    # add
    run_cmd(repo_path, ["git", "add"] + files_to_add)

    # no change -> skip
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo_path).returncode == 0:
        print(f"⚠️ {repo_path} 无变更，跳过提交")
        return False

    msg = f"{datetime.now():%Y-%m-%d} update apk {version}"
    run_cmd(repo_path, ["git", "commit", "-m", msg])
    run_cmd(repo_path, ["git", "push"])
    print(f"✅ {repo_path} push 完成：{msg}")
    return True


def git_tag_push(repo_path: str, version: str):
    """只在 repo1 打 tag，避免 repo2 重复 tag 报错"""
    tag = f"v{version}"
    # tag 若已存在就跳过（避免脚本中断）
    exists = subprocess.run(["git", "rev-parse", "-q", "--verify", tag],
                            cwd=repo_path, capture_output=True, text=True).returncode == 0
    if not exists:
        run_cmd(repo_path, ["git", "tag", tag])
    run_cmd(repo_path, ["git", "push", "origin", tag])
    print("🏷️ tag 推送成功：", tag)


# =================== 主流程（按你要求顺序） ===================
def main():
    print("🚀 双目录 APK 自动更新开始...")

    # paths
    apk_dir_1, apk_path_1, ver_path_1 = get_paths(REPO_PATH_1)
    apk_dir_2, apk_path_2, ver_path_2 = get_paths(REPO_PATH_2)

    # 1) git pull 更新前同步最新代码（两个目录）
    git_pull_safe(REPO_PATH_1)
    git_pull_safe(REPO_PATH_2)

    # 2) 拉取最新 apk（写 repo1），然后同步到 repo2
    if not download_apk_to_repo1(apk_path_1):
        print("❌ APK 下载失败，退出")
        return

    # 生成版本号
    version = generate_version()
    print("✅ 生成版本号:", version)

    # repo1 更新 version.json
    update_version_json(ver_path_1, version)

    # 同步 apk + version.json 到 repo2（保证一致）
    atomic_copy(apk_path_1, apk_path_2)
    atomic_copy(ver_path_1, ver_path_2)

    print("✅ 已同步到 repo2：")
    print(" -", apk_path_2)
    print(" -", ver_path_2)

    # 3) git commit（两个目录）
    rel_apk_1 = os.path.relpath(apk_path_1, REPO_PATH_1)
    rel_ver_1 = os.path.relpath(ver_path_1, REPO_PATH_1)

    rel_apk_2 = os.path.relpath(apk_path_2, REPO_PATH_2)
    rel_ver_2 = os.path.relpath(ver_path_2, REPO_PATH_2)

    committed1 = git_commit_push(REPO_PATH_1, [rel_apk_1, rel_ver_1], version)
    committed2 = git_commit_push(REPO_PATH_2, [rel_apk_2, rel_ver_2], version)

    # 4) git push 已包含在 git_commit_push 里
    # 额外：tag（只在 repo1）
    if committed1:
        git_tag_push(REPO_PATH_1, version)

    # 5) 最后再 git pull 同步目录（两个目录）
    git_pull_safe(REPO_PATH_1)
    git_pull_safe(REPO_PATH_2)

    print("✅ 全流程完成 ✅")


if __name__ == "__main__":
    main()