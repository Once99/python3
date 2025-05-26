import os
import zipfile
from tkinter import Tk, filedialog, messagebox
from tqdm import tqdm

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

def confirm_with_user(plan):
    """讓使用者確認是否要執行壓縮"""
    message = "以下是即將建立的壓縮檔案：\n\n"
    for subdir, zip_path in plan.items():
        message += f"{subdir} → {os.path.basename(zip_path)}\n"
    message += "\n是否要執行壓縮？"

    root = Tk()
    root.withdraw()
    return messagebox.askyesno("確認壓縮", message)

def zip_subdirectories(plan):
    """依照確認好的計畫執行壓縮"""
    print("📦 開始壓縮...\n")
    for subdir, zip_path in tqdm(plan.items(), desc="壓縮中"):
        subdir_path = os.path.join(os.path.dirname(zip_path), subdir)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(subdir_path):
                for file in files:
                    abs_file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_file_path, subdir_path)
                    zipf.write(abs_file_path, os.path.join(subdir, rel_path))
    print("\n✅ 所有壓縮完成！")

if __name__ == "__main__":
    target_folder = select_directory()
    if target_folder:
        zip_plan = preview_zip_plan(target_folder)
        if not zip_plan:
            print("❌ 找不到任何子目錄可壓縮。")
        elif confirm_with_user(zip_plan):
            zip_subdirectories(zip_plan)
        else:
            print("❎ 使用者取消壓縮。")
    else:
        print("❌ 未選擇目錄。")
