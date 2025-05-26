import os
import rarfile
import zipfile
import shutil
from tqdm import tqdm
from tkinter import Tk, filedialog

RAR_PASSWORD = "https://t.me/ZpostP"

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

def show_preview_in_terminal(rar_files):
    print("🔍 將轉換以下 .rar 檔案為 .zip：\n")
    for path in rar_files:
        print(f"  - {os.path.relpath(path)}")
    print("\n⚠️ 是否要繼續？ (y/n): ", end="")
    return input().strip().lower() == "y"

def process_rar_files(rar_files):
    for rar_file in tqdm(rar_files, desc="處理 .rar 檔案"):
        base_name = os.path.splitext(os.path.basename(rar_file))[0]
        parent_dir = os.path.dirname(rar_file)
        extract_dir = os.path.join(parent_dir, base_name + "_extracted")
        zip_file_path = os.path.join(parent_dir, base_name + ".zip")

        try:
            extract_rar(rar_file, extract_dir, RAR_PASSWORD)
            compress_to_zip(extract_dir, zip_file_path)
            os.remove(rar_file)            # 註解這行可保留原始 rar
            shutil.rmtree(extract_dir)    # 註解這行可保留解壓資料夾
        except rarfile.BadRarFile:
            print(f"❌ 無法開啟 RAR 檔案：{rar_file}")
        except rarfile.RarWrongPassword:
            print(f"🔑 密碼錯誤：{rar_file}")
        except Exception as e:
            print(f"❌ 其他錯誤：{rar_file} -> {e}")

if __name__ == "__main__":
    target_dir = select_directory()
    if target_dir:
        rar_files = find_rar_files(target_dir)
        if not rar_files:
            print("⚠️ 未找到任何 .rar 檔案")
        elif show_preview_in_terminal(rar_files):
            process_rar_files(rar_files)
            print("\n✅ 所有可處理檔案已完成。")
        else:
            print("❎ 已取消執行")
