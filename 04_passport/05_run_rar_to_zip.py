import os
import rarfile
import zipfile
import shutil
from tqdm import tqdm
from datetime import datetime
from tkinter import Tk, filedialog

RAR_PASSWORD = "https://t.me/ZpostP"
LOG_FILENAME = f"conversion_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

def select_directory():
    root = Tk()
    root.withdraw()
    return filedialog.askdirectory(title="選擇包含 .rar 檔案的資料夾")

def find_rar_files(base_dir):
    rar_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith(".rar"):
                rar_files.append(os.path.join(root, file))
    return rar_files

def find_folders_to_zip(base_dir):
    folders_to_zip = []
    for root, dirs, _ in os.walk(base_dir):
        for dir_name in dirs:
            folder_path = os.path.join(root, dir_name)
            zip_path = os.path.join(root, dir_name + ".zip")
            if not os.path.exists(zip_path):
                folders_to_zip.append(folder_path)
        break  # 只處理第一層資料夾
    return folders_to_zip

def extract_rar(rar_path, extract_to, password):
    with rarfile.RarFile(rar_path) as rf:
        if rf.needs_password():
            rf.extractall(path=extract_to, pwd=password)
        else:
            rf.extractall(path=extract_to)

def compress_to_zip(source_folder, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_folder):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, source_folder)
                zipf.write(full_path, arcname=rel_path)

def show_preview_in_terminal(rar_files, folders_to_zip, base_dir):
    print("🔍 將轉換以下 .rar 檔案為 .zip：")
    for path in rar_files:
        print(f"  - {os.path.relpath(path, base_dir)}")

    print("\n🗂️ 將壓縮以下未壓縮的資料夾為 .zip：")
    for folder in folders_to_zip:
        print(f"  - {os.path.relpath(folder, base_dir)}")

    print("\n⚠️ 是否要繼續？ (y/n): ", end="")
    return input().strip().lower() == "y"

def ask_user_delete_after_zip():
    print("\n🧹 壓縮後是否要刪除原始資料夾？ (y/n): ", end="")
    return input().strip().lower() == "y"

def log(message):
    with open(LOG_FILENAME, 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def get_file_size(path):
    total_size = 0
    if os.path.isfile(path):
        return os.path.getsize(path)
    for root, _, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

def process_rar_files(rar_files):
    for rar_file in tqdm(rar_files, desc="處理 .rar 檔案"):
        base_name = os.path.splitext(os.path.basename(rar_file))[0]
        parent_dir = os.path.dirname(rar_file)
        extract_dir = os.path.join(parent_dir, base_name + "_extracted")
        zip_file_path = os.path.join(parent_dir, base_name + ".zip")

        try:
            extract_rar(rar_file, extract_dir, RAR_PASSWORD)
            original_size = get_file_size(rar_file)
            extracted_size = get_file_size(extract_dir)
            compress_to_zip(extract_dir, zip_file_path)
            zip_size = get_file_size(zip_file_path)

            os.remove(rar_file)            # 註解這行可保留 .rar
            shutil.rmtree(extract_dir)     # 註解這行可保留解壓資料夾

            log(f"✅ RAR轉ZIP：{rar_file}")
            log(f"    原始RAR大小: {original_size} bytes")
            log(f"    解壓後大小 : {extracted_size} bytes")
            log(f"    ZIP壓縮後 : {zip_size} bytes\n")

        except rarfile.BadRarFile:
            log(f"❌ 無法開啟 RAR 檔案：{rar_file}")
        except rarfile.RarWrongPassword:
            log(f"🔑 密碼錯誤：{rar_file}")
        except Exception as e:
            log(f"❌ 其他錯誤：{rar_file} -> {e}")

def process_folders_to_zip(folders_to_zip, delete_original=False):
    for folder in tqdm(folders_to_zip, desc="壓縮未壓縮的資料夾"):
        zip_path = folder + ".zip"
        try:
            original_size = get_file_size(folder)
            compress_to_zip(folder, zip_path)
            zip_size = get_file_size(zip_path)
            if delete_original:
                shutil.rmtree(folder)

            log(f"✅ 資料夾壓縮：{folder}")
            log(f"    原始資料夾大小: {original_size} bytes")
            log(f"    ZIP壓縮後      : {zip_size} bytes\n")

        except Exception as e:
            log(f"❌ 壓縮失敗：{folder} -> {e}")

def main():
    target_dir = select_directory()
    if target_dir:
        rar_files = find_rar_files(target_dir)
        folders_to_zip = find_folders_to_zip(target_dir)

        if not rar_files and not folders_to_zip:
            print("⚠️ 沒有 .rar 或未壓縮資料夾可處理")
        elif show_preview_in_terminal(rar_files, folders_to_zip, target_dir):
            delete_after_zip = ask_user_delete_after_zip()

            if rar_files:
                process_rar_files(rar_files)
            if folders_to_zip:
                process_folders_to_zip(folders_to_zip, delete_after_zip)

            print(f"\n✅ 所有可處理項目已完成，詳情請見日誌檔案：{LOG_FILENAME}")
        else:
            print("❎ 已取消執行")

if __name__ == "__main__":
    main()
