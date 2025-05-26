import os
import shutil
import re
from tqdm import tqdm
from tkinter import Tk, filedialog

def select_directory():
    root = Tk()
    root.withdraw()
    return filedialog.askdirectory(title="選擇要整理的主資料夾")

def ensure_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)

def move_files(src_folder, dst_folder):
    for item in os.listdir(src_folder):
        src_path = os.path.join(src_folder, item)
        dst_path = os.path.join(dst_folder, item)
        if os.path.isfile(src_path):
            # 若目標有同名檔案，避免覆蓋自動加後綴
            if os.path.exists(dst_path):
                base, ext = os.path.splitext(item)
                counter = 1
                while os.path.exists(dst_path):
                    new_name = f"{base}_{counter}{ext}"
                    dst_path = os.path.join(dst_folder, new_name)
                    counter += 1
            shutil.move(src_path, dst_path)

def delete_folder_if_empty(folder_path):
    # 僅當資料夾為空才移除
    if not os.listdir(folder_path):
        os.rmdir(folder_path)
        print(f"🗑️ 已刪除空資料夾：{folder_path}")
    else:
        print(f"⚠️ 未刪除（非空）：{folder_path}")

def main():
    base_dir = select_directory()
    if not base_dir:
        print("❎ 未選擇資料夾")
        return

    all_dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

    prefix_map = {}
    pattern = re.compile(r"^(\d{2})_")

    for folder in all_dirs:
        match = pattern.match(folder)
        if match:
            prefix = match.group(1)
            prefix_map.setdefault(prefix, []).append(folder)

    if not prefix_map:
        print("⚠️ 未找到符合 nn_ 格式的資料夾")
        return

    for prefix, folders in prefix_map.items():
        target_folder = os.path.join(base_dir, prefix)
        ensure_folder(target_folder)

        for folder in tqdm(folders, desc=f"整理 {prefix}_* 資料夾"):
            src_path = os.path.join(base_dir, folder)
            move_files(src_path, target_folder)
            delete_folder_if_empty(src_path)

    print("✅ 所有資料已整理並清除空目錄")

if __name__ == "__main__":
    main()
