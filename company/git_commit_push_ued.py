import os
import subprocess
import time
import socket
from datetime import datetime


def has_staged_changes():
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    return result.returncode != 0


def get_unstaged_files():
    result = subprocess.run(["git", "diff", "--name-only"], capture_output=True, text=True)
    files = result.stdout.strip().splitlines()
    return [f for f in files if os.path.basename(f) != ".DS_Store"]


def vpn_connected(host="HKVPN01.dc66.net", port=443):
    try:
        with socket.create_connection((host, port), timeout=3):
            return True
    except Exception:
        return False


def create_and_push_tag():
    tag = f"v{datetime.now().strftime('%Y.%m.%d.%H%M')}"
    subprocess.run(["git", "tag", tag])
    subprocess.run(["git", "push", "origin", tag])
    print(f"🏷️ 已打 tag：{tag} 並推送成功")

    # 檢查 FortiClientVPN 是否正在執行
    check_vpn = subprocess.run(["pgrep", "-f", "FortiClientVPN"], capture_output=True, text=True)
    if check_vpn.returncode != 0:
        print("🔐 FortiClientVPN 未開啟，正在啟動...")
        subprocess.run(["open", "-a", "FortiClientVPN"])
        print("⏳ 等待 FortiClientVPN 啟動並連線中...")
        time.sleep(10)  # 初步等待時間，可根據實際情況調整
    else:
        print("✅ FortiClientVPN 已在執行中")

    # 等待 VPN 連線成功（偵測指定 IP 可達）
    vpn_hosts = ["HKVPN01.dc66.net", "HKVPN02.dc66.net", "HKVPN03.dc66.net"]
    connected = False
    for host in vpn_hosts:
        if vpn_connected(host):
            print(f"🔗 FortiClientVPN 已成功連線至 {host}")
            connected = True
            break
        else:
            print(f"❌ 無法連線至 VPN 主機 {host}")
    if not connected:
        print("❌ 請手動連線 VPN")
        return

    for _ in range(10):
        if vpn_connected(host):
            subprocess.run("echo 'https://uedweb01.itomtest.com/mobile/app/fundsManage.jsp' | pbcopy", shell=True)
            print("📋 已自動複製網址到剪貼簿：https://uedweb01.itomtest.com/mobile/app/fundsManage.jsp")

            subprocess.run(["open", "https://git.easydevops.net/B2C_DC/ued/web/-/pipelines"])
            print("🌐 已自動開啟 GitLab 頁面：https://git.easydevops.net/B2C_DC/ued/web/")
            break
        print("⏳ 等待 VPN 連線成功...")
        time.sleep(3)
    else:
        print("❌ FortiClientVPN 似乎尚未連線成功")


def git_commit_and_tag():
    repo_path = "/Users/oncechen/IdeaProjects/c_ued"
    os.chdir(repo_path)

    unstaged = get_unstaged_files()
    if unstaged:
        print("\n⚠️ 當前尚未加入 staged 區的檔案（已排除 .DS_Store）：\n")
        for file in unstaged:
            print(f"  • {file}")
        print("\n➡️ 上述檔案尚未加入 git 暫存區")
        choice = input("是否要自動執行 `git add .`？ [y/N]: ").strip().lower()
        if choice == 'y':
            subprocess.run(["git", "add", "."])
        else:
            print("⚠️ 未加入暫存區，跳過 commit 流程")

    if has_staged_changes():
        message = input("💬 請輸入 commit 訊息（預設：日常维护）：").strip() or "日常维护"
        commit_result = subprocess.run(["git", "commit", "-m", message])
        if commit_result.returncode != 0:
            print("❌ commit 發生錯誤，流程中止")
            return
        subprocess.run(["git", "push"])
        print(f"✅ 已提交並推送完成：{message}")
        create_and_push_tag()
    else:
        print("📦 沒有檔案需要 commit")
        choice = input("是否仍要打 Git Tag？ [y/N]: ").strip().lower()
        if choice == 'y':
            create_and_push_tag()
        else:
            print("✅ 任務已結束，未進行 tag")


if __name__ == "__main__":
    git_commit_and_tag()
