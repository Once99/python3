import subprocess
import os
from datetime import datetime
from pync import Notifier  # 用來觸發 macOS 通知

# 設定來源與目的地
SRC_DISK = "/Volumes/MyPassportA/"
DST_DISK = "/Volumes/MyPassportB/"

def run_backup():
    if not os.path.exists(SRC_DISK):
        Notifier.notify("來源硬碟未掛載", title="❌ 備份錯誤")
        return
    if not os.path.exists(DST_DISK):
        Notifier.notify("目標硬碟未掛載", title="❌ 備份錯誤")
        return

    # rsync 指令
    cmd = [
        "rsync",
        "-avh", "--progress",
        SRC_DISK,
        DST_DISK
    ]

    try:
        print(f"開始備份：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        subprocess.run(cmd, check=True)
        Notifier.notify("資料備份成功完成", title="✅ 備份完成")
    except subprocess.CalledProcessError as e:
        Notifier.notify("備份時發生錯誤", title="❌ 備份失敗")
        print(f"錯誤細節：{e}")

if __name__ == "__main__":
    run_backup()
