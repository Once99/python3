#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import filedialog

IGNORE_FILES = {'.DS_Store', '.gitkeep'}

def select_directory() -> str:
    """使用 GUI 選擇目錄"""
    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="請選擇要掃描的資料夾")
    return folder

def find_empty_dirs(base_path: str):
    """列出所有真正的空目錄（無檔案且無子目錄）"""
    print(f"\n📁 掃描目錄：{base_path}\n" + "=" * 50)

    for root, dirs, files in os.walk(base_path, topdown=False):
        # 過濾掉特殊檔案
        valid_files = [f for f in files if f not in IGNORE_FILES]
        if not valid_files and not dirs:
            print(f"📂 空目錄：{os.path.relpath(root, base_path)}")

def main():
    target_dir = select_directory()
    if not target_dir:
        print("❌ 未選擇任何目錄，結束程序")
        return

    find_empty_dirs(target_dir)

if __name__ == "__main__":
    main()
