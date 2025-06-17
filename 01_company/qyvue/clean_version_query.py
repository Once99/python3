import os
import re
from tkinter import Tk, filedialog

# 🔍 顯示選擇資料夾對話框
def select_directory():
    root = Tk()
    root.withdraw()
    return filedialog.askdirectory(title="📂 請選擇要掃描的資料夾")

# 遞迴找出所有 .jsp 檔案
def find_jsp_files(base_dir):
    jsp_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith('.jsp'):
                jsp_files.append(os.path.join(root, file))
    return jsp_files

# 搜尋並回傳修改清單，不處理 <%@...%> 行
def preview_modifications(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    modified_lines = []
    changes = []

    for line in lines:
        if line.strip().startswith("<%@"):
            modified_lines.append(line)  # 跳過 JSP 指令
            continue

        modified_line = re.sub(r'\?v=\d+', '', line)
        modified_lines.append(modified_line)

        if modified_line != line:
            changes.append((line.strip(), modified_line.strip()))

    return modified_lines, changes

# 寫回修改後內容
def apply_changes(file_path, modified_lines):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(modified_lines)

# 主流程
def process_directory(base_dir):
    jsp_files = find_jsp_files(base_dir)
    total_changes = 0
    changes_preview = []

    for file in jsp_files:
        modified_lines, changes = preview_modifications(file)
        if changes:
            changes_preview.append((file, changes, modified_lines))
            total_changes += len(changes)

    if not changes_preview:
        print("✅ 沒有找到需要修改的 .jsp 檔案。")
        return

    print(f"\n🧩 共找到 {total_changes} 處包含 `?v=數字` 的連結：\n")

    for file_path, changes, _ in changes_preview:
        print(f"📄 檔案：{file_path}")
        for original, updated in changes:
            print(f"  🔸 原始：{original}")
            print(f"  👉 修改：{updated}")
        print("")

    choice = input("❓ 是否要套用這些修改？(y/n): ").strip().lower()
    if choice == 'y':
        for file_path, _, modified_lines in changes_preview:
            apply_changes(file_path, modified_lines)
        print("✅ 所有檔案已套用變更。")
    else:
        print("❌ 未修改任何檔案。")

# 執行主程式
if __name__ == "__main__":
    folder = select_directory()
    if folder and os.path.isdir(folder):
        process_directory(folder)
    else:
        print("⚠️ 無效的資料夾路徑。")