import os
import rarfile
import py7zr
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
    return filedialog.askdirectory(title="選擇包含壓縮檔的資料夾")

def find_compressed_files(base_dir):
    compressed_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith(('.rar', '.7z')):
                compressed_files.append(os.path.join(root, file))
    return compressed_files

def extract_compressed_file(filepath, extract_to, password):
    if filepath.lower().endswith(".rar"):
        with rarfile.RarFile(filepath) as rf:
            if rf.needs_password():
                rf.extractall(path=extract_to, pwd=password)
            else:
                rf.extractall(path=extract_to)
    elif filepath.lower().endswith(".7z"):
        with py7zr.SevenZipFile(filepath, mode='r', password=password) as archive:
            archive.extractall(path=extract_to)
    else:
        raise ValueError("不支援的檔案格式")

def compress_to_zip(source_folder, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_folder):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, source_folder)
                zipf.write(full_path, arcname=rel_path)

def show_preview_in_terminal(compressed_files, folders_to_zip, base_dir):
    print("🔍 將轉換以下壓縮檔案為 .zip：")
    for path in compressed_files:
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

def process_compressed_files(compressed_files):
    for file in tqdm(compressed_files, desc="處理壓縮檔（RAR/7Z）"):
        base_name = os.path.splitext(os.path.basename(file))[0]
        parent_dir = os.path.dirname(file)
        temp_extract_dir = os.path.join(parent_dir, f"__temp_{base_name}")
        zip_file_path = os.path.join(parent_dir, base_name + ".zip")

        try:
            os.makedirs(temp_extract_dir, exist_ok=True)
            extract_compressed_file(file, temp_extract_dir, RAR_PASSWORD)

            # 判斷是否只有一層資料夾
            contents = os.listdir(temp_extract_dir)
            if len(contents) == 1 and os.path.isdir(os.path.join(temp_extract_dir, contents[0])):
                real_extract_dir = os.path.join(temp_extract_dir, contents[0])
            else:
                real_extract_dir = temp_extract_dir

            original_size = get_file_size(file)
            extracted_size = get_file_size(real_extract_dir)

            compress_to_zip(real_extract_dir, zip_file_path)

            # ✅ 確認壓縮成功才刪除原始資料
            if os.path.exists(zip_file_path) and os.path.getsize(zip_file_path) > 0:
                os.remove(file)
                shutil.rmtree(temp_extract_dir)
                zip_size = get_file_size(zip_file_path)

                log(f"✅ 轉ZIP：{file}")
                log(f"    原始大小: {original_size} bytes")
                log(f"    解壓後大小: {extracted_size} bytes")
                log(f"    ZIP大小  : {zip_size} bytes\n")
            else:
                raise Exception("ZIP 檔案不存在或大小為 0")

        except Exception as e:
            log(f"❌ 錯誤處理：{file} -> {e}")
            if os.path.exists(temp_extract_dir):
                shutil.rmtree(temp_extract_dir)

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

def process_folders_to_zip(folders_to_zip, delete_original=False):
    for folder in tqdm(folders_to_zip, desc="壓縮資料夾"):
        zip_path = folder + ".zip"
        try:
            original_size = get_file_size(folder)
            compress_to_zip(folder, zip_path)

            if os.path.exists(zip_path) and os.path.getsize(zip_path) > 0:
                if delete_original:
                    shutil.rmtree(folder)
                zip_size = get_file_size(zip_path)

                log(f"✅ 資料夾壓縮：{folder}")
                log(f"    原始大小: {original_size} bytes")
                log(f"    ZIP大小  : {zip_size} bytes\n")
            else:
                raise Exception("ZIP 壓縮失敗或檔案為空")

        except Exception as e:
            log(f"❌ 壓縮失敗：{folder} -> {e}")

def main():
    target_dir = select_directory()
    if target_dir:
        compressed_files = find_compressed_files(target_dir)
        folders_to_zip = find_folders_to_zip(target_dir)

        if not compressed_files and not folders_to_zip:
            print("⚠️ 沒有壓縮檔或未壓縮資料夾可處理")
        elif show_preview_in_terminal(compressed_files, folders_to_zip, target_dir):
            delete_after_zip = ask_user_delete_after_zip()

            if compressed_files:
                process_compressed_files(compressed_files)
            if folders_to_zip:
                process_folders_to_zip(folders_to_zip, delete_after_zip)

            print(f"\n✅ 完成，詳見日誌：{LOG_FILENAME}")
        else:
            print("❎ 已取消")

if __name__ == "__main__":
    main()
