import os
from tkinter import Tk, filedialog

def select_directory():
    """彈出視窗選擇資料夾"""
    root = Tk()
    root.withdraw()
    return filedialog.askdirectory(title="選擇要掃描的資料夾")

def delete_ds_store_files(base_dir):
    deleted_count = 0
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file == ".DS_Store":
                full_path = os.path.join(root, file)
                try:
                    os.remove(full_path)
                    print(f"🗑️ 刪除：{full_path}")
                    deleted_count += 1
                except Exception as e:
                    print(f"⚠️ 無法刪除 {full_path}：{e}")
    print(f"\n✅ 完成，共刪除 {deleted_count} 個 .DS_Store 檔案")

if __name__ == "__main__":
    target_dir = select_directory()
    if target_dir:
        delete_ds_store_files(target_dir)
    else:
        print("❌ 未選擇任何資料夾")
