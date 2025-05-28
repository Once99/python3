import os
import shutil
import zipfile
import rarfile
from tkinter import Tk, filedialog
from tqdm import tqdm

RAR_PASSWORD = "https://t.me/ZpostP"
TARGET_DELETE_FILES = {"看更多.jpg", "看更多.txt"}

def select_directory():
    root = Tk()
    root.withdraw()
    return filedialog.askdirectory(title="選擇包含 .rar 的資料夾")

def find_rar_files(base_dir):
    rar_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith(".rar"):
                rar_files.append(os.path.join(root, file))
    return rar_files

def extract_rar(rar_path, output_dir):
    try:
        with rarfile.RarFile(rar_path) as rf:
            print(f"📦 解壓：{os.path.basename(rar_path)}")
            if rf.needs_password():
                rf.extractall(path=output_dir, pwd=RAR_PASSWORD)
            else:
                rf.extractall(path=output_dir)
            # 刪除指定的檔案
            for target in TARGET_DELETE_FILES:
                target_path = os.path.join(output_dir, target)
                if os.path.isfile(target_path):
                    os.remove(target_path)
            return True
    except rarfile.RarCannotExec as e:
        print(f"❌ 無法執行 unrar：{e}")
    except rarfile.PasswordRequired:
        print(f"❌ 檔案需要密碼但未提供：{rar_path}")
    except Exception as e:
        print(f"❌ 解壓失敗 {rar_path}：{e}")
    return False

def compress_to_zip(source_dir, zip_path):
    print(f"🗜️  壓縮為 ZIP：{os.path.basename(zip_path)}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, source_dir)
                zipf.write(full_path, arcname)

def main():
    base_dir = select_directory()
    if not base_dir:
        print("⚠️ 未選擇目錄")
        return

    rar_files = find_rar_files(base_dir)
    if not rar_files:
        print("📭 找不到任何 .rar 檔案")
        return

    for rar_path in tqdm(rar_files, desc="處理 .rar 檔案"):
        extract_dir = os.path.splitext(rar_path)[0] + "_unpacked"
        zip_path = os.path.splitext(rar_path)[0] + ".zip"
        os.makedirs(extract_dir, exist_ok=True)

        if extract_rar(rar_path, extract_dir):
            compress_to_zip(extract_dir, zip_path)
            shutil.rmtree(extract_dir)  # 清除中繼資料夾
            try:
                os.remove(rar_path)  # 刪除原始 .rar 檔
                print(f"🗑️ 已刪除原始檔：{os.path.basename(rar_path)}")
            except Exception as e:
                print(f"❌ 刪除 .rar 檔案失敗：{e}")
        else:
            print(f"⚠️ 跳過壓縮，因為解壓失敗：{rar_path}")

    print("\n✅ 所有處理完成")

if __name__ == "__main__":
    main()
