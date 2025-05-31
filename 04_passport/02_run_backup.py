import subprocess
from datetime import datetime
from pync import Notifier  # 用來觸發 macOS 通知

# 設定來源與目的地
# 加上斜線，就是目錄拷貝目錄
# 沒加斜線，就是當前目錄下的所有檔案
SRC_DISK = "/Volumes/TOSHIBA EXT/2025-05-22"
DST_DISK = "/Volumes/TOSHIBA EXT 1/"

def run_backup():
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
