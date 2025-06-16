import subprocess
import time
import socket

def vpn_connected(host="HKVPN01.dc66.net", port=443):
    try:
        with socket.create_connection((host, port), timeout=3):
            return True
    except Exception:
        return False

def connect_forticlient():
    # 檢查是否已啟動 FortiClientVPN
    check_vpn = subprocess.run(["pgrep", "-f", "FortiClientVPN"], capture_output=True, text=True)
    if check_vpn.returncode != 0:
        print("🔐 FortiClientVPN 未開啟，正在啟動...")
        subprocess.run(["open", "-a", "FortiClientVPN"])
        time.sleep(5)  # 等待 UI 載入
    else:
        print("✅ FortiClientVPN 已在執行中")

    print("📡 嘗試自動點擊 Connect 按鈕...")
    subprocess.run([
        "osascript", "-e",
        'tell application "System Events" to tell process "FortiClientVPN" to click button "Connect" of window 1'
    ])

    print("⏳ 檢查 VPN 連線狀態...")
    for i in range(10):
        if vpn_connected():
            print("🔗 VPN 已成功連線")
            return
        print(f"等待連線中... ({i+1}/10)")
        time.sleep(3)

    print("❌ 無法自動完成 VPN 連線，請手動檢查")

if __name__ == "__main__":
    connect_forticlient()