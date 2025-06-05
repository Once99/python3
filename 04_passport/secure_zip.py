import os
import subprocess
from tkinter import Tk, filedialog, simpledialog

def select_folder():
    root = Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="選擇要加密壓縮的資料夾")
    return folder_path

def get_password():
    root = Tk()
    root.withdraw()
    password = simpledialog.askstring("輸入密碼", "請輸入壓縮檔密碼：", show='*')
    return password

def compress_with_encryption(folder_path, password):
    parent_dir = os.path.dirname(folder_path)
    folder_name = os.path.basename(folder_path.rstrip("/"))
    zip_path = os.path.join(parent_dir, f"{folder_name}.zip")

    cmd = ['zip', '-er', zip_path, folder_name]
    print(f"🔒 正在壓縮並加密：{folder_path}")
    print(f"📦 壓縮檔案將儲存為：{zip_path}")

    try:
        # 切換到父層資料夾，避免 zip 把完整路徑打包
        subprocess.run(cmd, cwd=parent_dir, input=(password + '\n') * 2, text=True, check=True)
        print(f"✅ 完成：{zip_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ 壓縮失敗：{e}")

def main():
    folder = select_folder()
    if not folder:
        print("⚠️ 未選擇資料夾，已取消。")
        return
    password = get_password()
    if not password:
        print("⚠️ 未輸入密碼，已取消。")
        return
    compress_with_encryption(folder, password)

if __name__ == "__main__":
    main()
