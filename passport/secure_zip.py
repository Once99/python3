import os
import subprocess
from tkinter import Tk, filedialog


def select_folder():
    root = Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="選擇要加密壓縮的資料夾")
    return folder_path

def compress_with_encryption(folder_path):
    parent_dir = os.path.dirname(folder_path)
    folder_name = os.path.basename(folder_path.rstrip("/"))
    zip_path = os.path.join(parent_dir, f"{folder_name}.zip")

    cmd = ['zip', '-er', zip_path, folder_name]
    print(f"🔒 正在壓縮並加密：{folder_path}")
    print(f"📦 壓縮檔案將儲存為：{zip_path}")

    try:
        subprocess.run(cmd, cwd=parent_dir, check=True)
        print(f"✅ 完成：{zip_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ 壓縮失敗：{e}")

def main():
    folder = select_folder()
    if not folder:
        print("⚠️ 未選擇資料夾，已取消。")
        return
    compress_with_encryption(folder)

if __name__ == "__main__":
    main()