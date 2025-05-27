import os
import rarfile
import py7zr
import tarfile
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
            if file.lower().endswith((
                    '.rar', '.7z', '.tar.gz', '.tgz', '.tar.bz2', '.tar.xz', '.tar',
                    '.zip.001', '.z1', '.001'
            )):
                zip_equivalent = os.path.splitext(os.path.join(root, file))[0] + ".zip"
                if not os.path.exists(zip_equivalent):  # 跳過已轉換的 zip
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
    elif filepath.lower().endswith((".tar.gz", ".tgz", ".tar.bz2", ".tar.xz", ".tar")):
        with tarfile.open(filepath, "r:*") as tar:
            tar.extractall(path=extract_to)
    elif filepath.lower().endswith(".zip"):
        with zipfile.ZipFile(filepath, 'r') as zipf:
            zipf.extractall(path=extract_to)
    else:
        raise ValueError("不支援的檔案格式")


def merge_split_zip(zip_part_path):
    base_path = zip_part_path.rsplit('.zip.', 1)[0] + '.zip'
    dir_path = os.path.dirname(zip_part_path)
    part_prefix = os.path.basename(base_path).replace('.zip', '')

    part_files = sorted([
        f for f in os.listdir(dir_path)
        if (f.startswith(part_prefix) and (f.endswith('.z1') or f.endswith('.001') or f.endswith('.zip.001')))
    ])

    with open(base_path, 'wb') as output:
        for part_file in part_files:
            with open(os.path.join(dir_path, part_file), 'rb') as pf:
                shutil.copyfileobj(pf, output)
    return base_path


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


def flatten_nested_same_named_folder(folder_path):
    folder_name = os.path.basename(folder_path)
    current_path = folder_path

    while True:
        inner = os.listdir(current_path)
        if len(inner) == 1:
            inner_path = os.path.join(current_path, inner[0])
            if os.path.isdir(inner_path) and os.path.basename(inner_path) == folder_name:
                current_path = inner_path
            else:
                break
        else:
            break

    if current_path != folder_path:
        for item in os.listdir(current_path):
            shutil.move(os.path.join(current_path, item), folder_path)
        shutil.rmtree(current_path)


def process_compressed_files(compressed_files):
    for file in tqdm(compressed_files, desc="處理壓縮檔 (RAR/7Z/TAR/...)"):
        if file.lower().endswith(('.zip.001', '.z1', '.001')):
            file = merge_split_zip(file)
            if not os.path.exists(file):
                log(f"❌ 拆分檔合併失敗：{file}")
                continue

        base_name = os.path.splitext(os.path.basename(file))[0]
        parent_dir = os.path.dirname(file)
        temp_extract_dir = os.path.join(parent_dir, f"__temp_{base_name}")
        zip_file_path = os.path.join(parent_dir, base_name + ".zip")

        try:
            os.makedirs(temp_extract_dir, exist_ok=True)
            extract_compressed_file(file, temp_extract_dir, RAR_PASSWORD)

            contents = os.listdir(temp_extract_dir)
            subdirs = [d for d in contents if os.path.isdir(os.path.join(temp_extract_dir, d))]

            if len(subdirs) > 1:
                subdirs_sorted = sorted(
                    subdirs,
                    key=lambda x: (x.lower(), os.path.getctime(os.path.join(temp_extract_dir, x)))
                )
                keep = subdirs_sorted[0]
                keep_path = os.path.join(temp_extract_dir, keep)
                for sub in subdirs:
                    sub_path = os.path.join(temp_extract_dir, sub)
                    if sub_path != keep_path:
                        shutil.rmtree(sub_path)
                real_extract_dir = keep_path
            elif len(subdirs) == 1:
                real_extract_dir = os.path.join(temp_extract_dir, subdirs[0])
            else:
                real_extract_dir = temp_extract_dir

            flatten_nested_same_named_folder(real_extract_dir)

            original_size = get_file_size(file)
            extracted_size = get_file_size(real_extract_dir)

            compress_to_zip(real_extract_dir, zip_file_path)

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
            zip_path = folder_path + ".zip"
            if not os.path.exists(zip_path):
                folders_to_zip.append(folder_path)
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

            print(f"\n✅ 完成，請查看日誌：{LOG_FILENAME}")
        else:
            print("❎ 已取消")


if __name__ == "__main__":
    main()
