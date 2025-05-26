import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox

# 偵測開頭為年份但沒有底線的資料夾名稱
def is_year_prefix_without_underscore(name):
    return re.match(r'^\d{4}(?!_)\S+', name) is not None

def rename_folders_with_year_prefix(base_path):
    renamed = []
    skipped = []

    for item in os.listdir(base_path):
        old_path = os.path.join(base_path, item)
        if os.path.isdir(old_path) and is_year_prefix_without_underscore(item):
            # 插入底線
            new_name = item[:4] + "_" + item[4:]
            new_path = os.path.join(base_path, new_name)

            if os.path.exists(new_path):
                skipped.append(f"{item}（已存在 {new_name}）")
                continue

            try:
                os.rename(old_path, new_path)
                renamed.append((item, new_name))
            except Exception as e:
                skipped.append(f"{item}（錯誤：{e}）")

    return renamed, skipped

def main():
    root = tk.Tk()
    root.withdraw()

    folder_path = filedialog.askdirectory(title="選擇上層目錄")
    if not folder_path:
        return

    renamed, skipped = rename_folders_with_year_prefix(folder_path)

    msg = ""
    if renamed:
        msg += "✅ 已重新命名以下資料夾：\n" + "\n".join([f"{a} → {b}" for a, b in renamed]) + "\n\n"
    if skipped:
        msg += "⚠️ 以下資料夾略過或失敗：\n" + "\n".join(skipped)

    if not msg:
        msg = "沒有符合條件的資料夾。"

    messagebox.showinfo("執行結果", msg)

if __name__ == "__main__":
    main()
