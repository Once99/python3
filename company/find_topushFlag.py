import os
import tkinter as tk
from tkinter import filedialog

# 支持的源码文件扩展名
CODE_EXTENSIONS = ['.js', '.ts', '.vue', '.jsx', '.tsx', '.html', '.php', '.py']

def find_topush_flag(root_dir):
    matches = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if any(file.endswith(ext) for ext in CODE_EXTENSIONS):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f, start=1):
                            if 'topushFlag' in line:
                                matches.append((file_path, i, line.strip()))
                except Exception as e:
                    print(f"❌ 无法读取 {file_path}: {e}")
    return matches

def choose_directory():
    root = tk.Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory(title="请选择要搜索的目录")
    return folder_selected

if __name__ == "__main__":
    print("📁 正在打开目录选择器...")
    directory = choose_directory()

    if not directory:
        print("⚠️ 未选择目录，程序已取消。")
    else:
        print(f"🔍 正在搜索目录：{directory}\n")
        results = find_topush_flag(directory)

        if not results:
            print("✅ 没有找到任何包含 'topushFlag' 的行。")
        else:
            print("📌 找到以下内容：\n")
            for path, lineno, content in results:
                print(f"[{path}:{lineno}] {content}")