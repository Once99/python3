import os
import shutil
from tkinter import Tk, filedialog

def select_folder(title):
    root = Tk()
    root.withdraw()
    return filedialog.askdirectory(title=title)

def get_unique_filename(dest_dir, filename):
    name, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(dest_dir, new_filename)):
        new_filename = f"{name}_{counter}{ext}"
        counter += 1
    return new_filename

def preview_move_plan(src_dir, dest_dir):
    plan = []
    for root, _, files in os.walk(src_dir):
        for file in files:
            src_path = os.path.join(root, file)
            unique_name = get_unique_filename(dest_dir, file)
            dest_path = os.path.join(dest_dir, unique_name)
            plan.append((src_path, dest_path, file, unique_name))
    return plan

def move_files(plan):
    total_moved = 0
    for src_path, dest_path, orig_name, new_name in plan:
        try:
            shutil.move(src_path, dest_path)
            print(f"✅ 搬移：{orig_name} → {new_name}")
            total_moved += 1
        except Exception as e:
            print(f"❌ 搬移失敗：{orig_name} → {e}")
    print(f"\n✅ 完成搬移，共處理 {total_moved} 個檔案")

def main():
    print("📁 選擇來源與目標目錄")
    src = select_folder("選擇來源目錄")
    dest = select_folder("選擇目標目錄")
    if not src or not dest:
        print("⚠️ 未選擇目錄，已取消")
        return

    plan = preview_move_plan(src, dest)
    if not plan:
        print("📭 沒有檔案可搬移")
        return

    print("\n📋 預覽搬移計畫：")
    for _, _, orig, new in plan:
        print(f"  - {orig} → {new}")

    confirm = input("\n是否執行搬移？輸入 Y 確認：")
    if confirm.strip().upper() == 'Y':
        move_files(plan)
    else:
        print("🚫 已取消搬移")

if __name__ == "__main__":
    main()
