import os
import shutil
import rarfile
import zipfile
from tqdm import tqdm
from datetime import datetime
from tkinter import Tk, filedialog

def select_directory():
    root = Tk()
    root.withdraw()
    return filedialog.askdirectory(title="選擇包含 .rar 的資料夾")

def clean_name(name):
    return name.replace("【", "").replace("】", "").replace("　", "").strip()

def copy_to_local(rar_path, local_dir):
    os.makedirs(local_dir, exist_ok=True)
    dest = os.path.join(local_dir, os.path.basename(rar_path))
    shutil.copy2(rar_path, dest)
    return dest

def extract_rar(rar_file, extract_to):
    try:
        with rarfile.RarFile(rar_file) as rf:
            rf.extractall(path=extract_to)
        return True
    except Exception as e:
        print(f"❌ 解壓失敗：{os.path.basename(rar_file)}\n   原因：{e}")
        return False

def compress_to_zip(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                abs_file = os.path.join(root, file)
                rel_path = os.path.relpath(abs_file, folder_path)
                zf.write(abs_file, arcname=rel_path)

def main():
    src_dir = select_directory()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    temp_dir = os.path.expanduser(f"~/Downloads/temp_rar_to_zip_{timestamp}")
    os.makedirs(temp_dir, exist_ok=True)
    log_path = os.path.expanduser(f"~/Downloads/rar_conversion_log_{timestamp}.txt")
    log = []

    rar_files = [
        os.path.join(root, f)
        for root, _, files in os.walk(src_dir)
        for f in files if f.lower().endswith(".rar")
    ]

    if not rar_files:
        print("⚠️ 沒有找到任何 .rar 檔案")
        return

    print(f"🔍 找到 {len(rar_files)} 個 RAR 檔案，是否要開始解壓與壓縮？ (y/n): ", end='')
    if input().lower() != 'y':
        return

    for rar_path in tqdm(rar_files, desc="處理 RAR"):
        try:
            file_name = os.path.basename(rar_path)
            base_name = clean_name(os.path.splitext(file_name)[0])
            extract_dir = os.path.join(temp_dir, base_name)
            local_rar = copy_to_local(rar_path, temp_dir)

            if not extract_rar(local_rar, extract_dir):
                log.append(f"❌ 解壓失敗：{file_name}")
                continue

            zip_local_path = os.path.join(temp_dir, base_name + ".zip")
            compress_to_zip(extract_dir, zip_local_path)

            log.append(f"✅ {file_name} → {base_name}.zip")
        except Exception as e:
            log.append(f"❌ 處理失敗：{file_name} - {e}")

    print(f"\n✅ ZIP 檔案全部保存在：{temp_dir}")

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log))
    print(f"\n📄 處理記錄已儲存：{log_path}")

    print("\n📋 處理結果：")
    for line in log:
        print(line)

if __name__ == "__main__":
    main()
