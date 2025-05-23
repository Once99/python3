import os
import shutil

def find_google_drive_path():
    cloudstorage_path = os.path.expanduser("~/Library/CloudStorage")
    if not os.path.exists(cloudstorage_path):
        print("⚠️ 找不到 CloudStorage 資料夾")
        return None

    # 找出 GoogleDrive 開頭的資料夾
    for folder in os.listdir(cloudstorage_path):
        if folder.startswith("GoogleDrive"):
            full_path = os.path.join(cloudstorage_path, folder)
            if os.path.isdir(full_path):
                return full_path

    print("⚠️ 找不到 GoogleDrive 掛載資料夾")
    return None

def create_symlink_to_desktop(source_path):
    desktop_path = os.path.expanduser("~/Desktop")
    link_name = os.path.join(desktop_path, "Google雲端硬碟")

    if os.path.exists(link_name):
        print("✅ 桌面上已經有捷徑：Google雲端硬碟")
        return

    try:
        os.symlink(source_path, link_name)
        print(f"✅ 已建立捷徑：{link_name}")
    except Exception as e:
        print(f"❌ 建立捷徑失敗：{e}")

if __name__ == "__main__":
    gd_path = find_google_drive_path()
    if gd_path:
        create_symlink_to_desktop(gd_path)
