import os
import shutil
from tkinter import Tk, filedialog
from tqdm import tqdm

def select_folder(title):
    root = Tk()
    root.withdraw()
    return filedialog.askdirectory(title=title)

def get_unique_filename(dest_dir, filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(dest_dir, new_filename)):
        new_filename = f"{base}_{counter}{ext}"
        counter += 1
    return new_filename

def copy_with_rename(src_dir, dst_dir):
    for root, _, files in os.walk(src_dir):
        rel_path = os.path.relpath(root, src_dir)
        target_path = os.path.join(dst_dir, rel_path)
        os.makedirs(target_path, exist_ok=True)

        for file in tqdm(files, desc=f"Copying files in {rel_path}"):
            src_file = os.path.join(root, file)
            unique_name = get_unique_filename(target_path, file)
            dst_file = os.path.join(target_path, unique_name)
            try:
                shutil.copy2(src_file, dst_file)
            except Exception as e:
                print(f"❌ 無法複製 {src_file}：{e}")

if __name__ == "__main__":
    print("📂 請選擇來源資料夾")
    source = select_folder("選擇來源資料夾")
    print("📁 請選擇目標資料夾")
    destination = select_folder("選擇目標資料夾")

    if source and destination:
        print(f"🚀 開始複製從 {source} 到 {destination}")
        copy_with_rename(source, destination)
        print("✅ 完成！")
    else:
        print("⚠️ 未選擇來源或目標資料夾")
