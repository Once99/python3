import os
import tkinter as tk
from tkinter import messagebox

def show_message(title, msg):
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(title, msg)

def show_error(title, msg):
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(title, msg)

def find_mounted_passport(vol_name="My Passport"):
    volumes_path = "/Volumes"
    try:
        for item in os.listdir(volumes_path):
            if vol_name.lower() in item.lower():
                full_path = os.path.join(volumes_path, item)
                if os.path.ismount(full_path):
                    return full_path
    except Exception as e:
        return None
    return None

def create_desktop_shortcut(target_path, alias_name="My Passport"):
    desktop_path = os.path.expanduser("~/Desktop")
    shortcut_path = os.path.join(desktop_path, alias_name)

    # 若捷徑已存在就先刪除
    if os.path.islink(shortcut_path) or os.path.exists(shortcut_path):
        os.remove(shortcut_path)

    try:
        os.symlink(target_path, shortcut_path)
        return True
    except Exception as e:
        print(f"建立捷徑失敗：{e}")
        return False

def main():
    disk_path = find_mounted_passport("My Passport")
    if disk_path:
        success = create_desktop_shortcut(disk_path, "My Passport")
        if success:
            show_message("My Passport 狀態", f"✅ 『My Passport』已掛載，捷徑已建立在桌面。\n路徑：{disk_path}")
        else:
            show_error("捷徑建立失敗", f"⚠️ 『My Passport』已掛載，但無法建立桌面捷徑。\n請手動確認權限或磁碟狀態。")
    else:
        show_error("未偵測到 My Passport", "❌ 沒有找到已掛載的『My Passport』磁碟，請確認是否已插入並掛載。")

if __name__ == "__main__":
    main()
