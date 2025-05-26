import os
import re

def select_directory():
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    return filedialog.askdirectory(title="選擇目標資料夾")

def extract_clean_name(name):
    """從【xx、yy】中擷取 yy，並移除空白與全形空白"""
    match = re.match(r"^【[^、]*、([^】]+)】$", name)
    if match:
        new_name = match.group(1)
        return new_name.replace('\u3000', '').replace(' ', '')
    return None

def preview_renames(base_dir):
    """找出符合條件的目錄與預期的新名稱"""
    rename_plan = {}
    for name in os.listdir(base_dir):
        old_path = os.path.join(base_dir, name)
        if os.path.isdir(old_path):
            new_name = extract_clean_name(name)
            if new_name and new_name != name:
                new_path = os.path.join(base_dir, new_name)
                if not os.path.exists(new_path):
                    rename_plan[name] = new_name
    return rename_plan

def execute_rename(base_dir, rename_plan):
    renamed = []
    for old_name, new_name in rename_plan.items():
        old_path = os.path.join(base_dir, old_name)
        new_path = os.path.join(base_dir, new_name)
        try:
            os.rename(old_path, new_path)
            renamed.append((old_name, new_name))
        except Exception as e:
            print(f"❌ 無法重新命名 {old_name} → {new_name}：{e}")
    return renamed

def main():
    base_dir = select_directory()
    if not base_dir:
        print("❌ 未選擇資料夾")
        return

    rename_plan = preview_renames(base_dir)

    if not rename_plan:
        print("⚠️ 沒有符合條件的資料夾需要修改")
        return

    print("📝 預覽以下即將修改的目錄名稱：")
    for old, new in rename_plan.items():
        print(f"  {old} → {new}")

    confirm = input("\n是否執行上述修改？(y/n): ").strip().lower()
    if confirm == 'y':
        renamed = execute_rename(base_dir, rename_plan)
        print("\n✅ 修改完成：")
        for old, new in renamed:
            print(f"  {old} → {new}")
    else:
        print("❎ 已取消修改。")

if __name__ == "__main__":
    main()
