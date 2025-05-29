import os
import rarfile
import zipfile
import shutil
from tqdm import tqdm
from tkinter import Tk, filedialog

def select_directory():
    root = Tk()
    root.withdraw()
    return filedialog.askdirectory(title="選擇包含 .rar 檔案的資料夾")

def find_rar_files(folder):
    rar_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(".rar"):
                rar_files.append(os.path.join(root, file))
    return rar_files

def clean_folder_name(name):
    return name.replace("【", "").replace("】", "").replace("　", "").strip()

def extract_rar(rar_path, output_dir):
    with rarfile.RarFile(rar_path) as rf:
        rf.extractall(path=output_dir)

def compress_to_zip(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, start=folder_path)
                zipf.write(full_path, arcname)

def confirm(prompt):
    return input(f"{prompt} (y/n): ").strip().lower() == "y"

def main():
    base_dir = select_directory()
    rar_files = find_rar_files(base_dir)

    if not rar_files:
        print("❗ 沒有找到 .rar 檔案")
        return

    print("\n📦 將要處理以下 .rar 檔案：\n")
    for rar in rar_files:
        print("  -", os.path.basename(rar))

    if not confirm("\n是否要開始解壓與壓縮？"):
        print("❌ 已取消執行")
        return

    for rar_path in tqdm(rar_files, desc="處理 RAR 檔案"):
        try:
            rar_name = os.path.splitext(os.path.basename(rar_path))[0]
            extract_folder = os.path.join(os.path.dirname(rar_path), rar_name)

            extract_rar(rar_path, extract_folder)

            # 尋找並重新命名含有特殊符號的子資料夾
            for item in os.listdir(extract_folder):
                item_path = os.path.join(extract_folder, item)
                if os.path.isdir(item_path):
                    new_name = clean_folder_name(item)
                    new_path = os.path.join(extract_folder, new_name)
                    if new_path != item_path:
                        os.rename(item_path, new_path)
                        item_path = new_path

                    # 壓縮為 zip
                    zip_output_path = new_path + ".zip"
                    compress_to_zip(item_path, zip_output_path)
                    print(f"✅ 壓縮完成：{zip_output_path}")

            os.remove(rar_path)
            print(f"🗑️ 已刪除原始 RAR：{rar_path}")

        except Exception as e:
            print(f"❌ 發生錯誤：{rar_path} → {e}")

if __name__ == "__main__":
    main()
