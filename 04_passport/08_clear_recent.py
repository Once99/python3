import os
import subprocess
from pathlib import Path

def clear_sfl2_recent_items():
    """清除 Finder 最近開啟的 Apps/Documents/Servers"""
    sharedfilelist_dir = Path.home() / "Library/Application Support/com.apple.sharedfilelist"
    sfl2_files = [
        "com.apple.LSSharedFileList.RecentApplications.sfl2",
        "com.apple.LSSharedFileList.RecentDocuments.sfl2",
        "com.apple.LSSharedFileList.RecentServers.sfl2"
    ]
    print("🧹 清除 Finder 最近項目...")
    for sfl2 in sfl2_files:
        file_path = sharedfilelist_dir / sfl2
        if file_path.exists():
            try:
                os.remove(file_path)
                print(f"✅ 已刪除：{file_path}")
            except Exception as e:
                print(f"❌ 無法刪除 {file_path}：{e}")
        else:
            print(f"⚠️ 檔案不存在：{file_path}")

def clear_app_recent_plists():
    """清除 Preview、QuickTime、TextEdit 等 App 的最近項目"""
    plist_files = {
        "Preview": "~/Library/Containers/com.apple.Preview/Data/Library/Preferences/com.apple.Preview.LSSharedFileList.plist",
        "QuickTime": "~/Library/Containers/com.apple.QuickTimePlayerX/Data/Library/Preferences/com.apple.QuickTimePlayerX.LSSharedFileList.plist",
        "TextEdit": "~/Library/Containers/com.apple.TextEdit/Data/Library/Preferences/com.apple.TextEdit.LSSharedFileList.plist"
    }
    print("🧼 清除 App 最近紀錄...")
    for app, plist_path in plist_files.items():
        path = Path(os.path.expanduser(plist_path))
        if path.exists():
            try:
                os.remove(path)
                print(f"✅ 已刪除 {app} 的最近紀錄：{path}")
            except Exception as e:
                print(f"❌ 無法刪除 {app} 的 plist：{e}")
        else:
            print(f"⚠️ 找不到 {app} 的 plist：{path}")

def restart_finder():
    """重啟 Finder"""
    try:
        subprocess.run(["killall", "Finder"], check=True)
        print("🔄 Finder 已重新啟動")
    except Exception as e:
        print(f"❌ Finder 重啟失敗：{e}")

def main():
    print("🚀 開始清除 macOS 最近項目")
    clear_sfl2_recent_items()
    clear_app_recent_plists()
    restart_finder()
    print("✅ 全部完成")

if __name__ == "__main__":
    main()
