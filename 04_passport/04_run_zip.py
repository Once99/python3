import os
import zipfile
from tkinter import Tk, filedialog
from tqdm import tqdm
import shutil
import subprocess

def empty_trash():
    """清空 macOS 垃圾桶"""
    try:
        subprocess.run(['osascript', '-e', 'tell app "Finder" to empty the trash'], check=True)
        print("🗑️ 已清空垃圾桶")
    except subprocess.CalledProcessError as e:
        print(f"❌ 清空垃圾桶時發生錯誤：{e}")

def select_directory():
    """開啟視窗讓使用者選擇目標目錄"""
    root = Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="選擇要壓縮子目錄的資料夾")
    return folder_path

def get_unique_zip_name(base_dir, base_name):
    """產生不重複的 zip 檔案名稱"""
    zip_path = os.path.join(base_dir, f"{base_name}.zip")
    counter = 1
    while os.path.exists(zip_path):
        zip_path = os.path.join(base_dir, f"{base_name}_{counter}.zip")
        counter += 1
    return zip_path

def preview_zip_plan(base_dir):
    """產生壓縮檔名預覽清單"""
    plan = {}
    for subdir in os.listdir(base_dir):
        full_path = os.path.join(base_dir, subdir)
        if os.path.isdir(full_path):
            zip_name = get_unique_zip_name(base_dir, subdir)
            plan[subdir] = zip_name
    return plan

def zip_and_delete_subdirectories(base_dir, plan):
    """依照計畫壓縮並刪除原始子目錄"""
    print("\n📦 開始壓縮並刪除原始子目錄...\n")
    for subdir, zip_path in tqdm(plan.items(), desc="處理中"):
        subdir_path = os.path.join(base_dir, subdir)

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(subdir_path):
                    for file in files:
                        abs_file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(abs_file_path, subdir_path)
                        zipf.write(abs_file_path, os.path.join(subdir, rel_path))

            shutil.rmtree(subdir_path)
            print(f"✅ 已壓縮並刪除：{subdir}")
        except Exception as e:
            print(f"❌ 錯誤處理 {subdir}：{e}")
    print("\n✅ 所有子目錄處理完成！")

def main():
    empty_trash()

    target_folder = select_directory()
    if not target_folder:
        print("❌ 未選擇目錄。")
        return

    zip_plan = preview_zip_plan(target_folder)

    if not zip_plan:
        print("⚠️ 沒有可壓縮的子目錄。")
        return

    print("📝 即將處理以下目錄：")
    for subdir, zip_path in zip_plan.items():
        print(f"  {subdir} → {os.path.basename(zip_path)}")

    confirm = input("\n是否開始壓縮並刪除原始目錄？(y/n): ").strip().lower()
    if confirm == 'y':
        zip_and_delete_subdirectories(target_folder, zip_plan)
    else:
        print("❎ 已取消操作。")

if __name__ == "__main__":
    main()
