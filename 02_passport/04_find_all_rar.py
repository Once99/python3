import os
from tkinter import Tk, filedialog

def select_directory():
    """彈出視窗讓使用者選擇資料夾"""
    root = Tk()
    root.withdraw()
    return filedialog.askdirectory(title="選擇要掃描的資料夾")

def find_rar_files(folder):
    """列出資料夾中所有 .rar 檔案"""
    rar_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(".rar"):
                rar_files.append(os.path.join(root, file))
    return rar_files

def main():
    target_dir = select_directory()
    if not target_dir:
        print("❌ 未選擇資料夾")
        return

    print(f"📂 掃描目錄：{target_dir}")
    rar_files = find_rar_files(target_dir)

    if not rar_files:
        print("✅ 沒有找到任何 .rar 檔案")
    else:
        print(f"📦 共找到 {len(rar_files)} 個 .rar 檔案：\n")
        for path in rar_files:
            print(path)

if __name__ == "__main__":
    main()
