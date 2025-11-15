#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A_script_list_music_with_dialog.py
----------------------------------
步驟一腳本（升級版）：
✔ 會彈出系統「選擇資料夾視窗」
✔ 自動掃描音樂
✔ 直接列印結果到終端機
✔ 你拷貝貼給 ChatGPT 進行第二步分析

使用方式：
    python A_script_list_music_with_dialog.py
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog

SUPPORTED_EXTS = {
    '.mp3', '.m4a', '.aac',
    '.flac', '.ogg', '.wav',
    '.wma', '.alac', '.aiff', '.aif'
}

def scan_music(root_dir):
    results = []
    root_dir = os.path.abspath(root_dir)

    for dirpath, _, filenames in os.walk(root_dir):
        for name in filenames:
            ext = os.path.splitext(name)[1].lower()
            if ext not in SUPPORTED_EXTS:
                continue

            full_path = os.path.join(dirpath, name)
            rel_path = os.path.relpath(full_path, root_dir)
            title = os.path.splitext(name)[0]

            results.append((full_path, rel_path, title))
    return results

def choose_directory():
    root = tk.Tk()
    root.withdraw()  # 隱藏主視窗
    root.attributes("-topmost", True)  # 視窗置頂
    folder = filedialog.askdirectory(title="選擇音樂資料夾")
    root.destroy()
    return folder

def main():
    print("請稍候，正在開啟『選擇資料夾』視窗...\n")
    folder = choose_directory()

    if not folder:
        print("[取消] 你沒有選資料夾。")
        sys.exit(0)

    if not os.path.isdir(folder):
        print(f"[ERROR] 非資料夾：{folder}")
        sys.exit(1)

    print(f"# 已選擇目錄: {os.path.abspath(folder)}")
    print("# 支援副檔名:", ", ".join(sorted(SUPPORTED_EXTS)))
    print("# 掃描結果如下（複製貼給 ChatGPT 分析）：")
    print("# 格式：index\trelative_path\ttrack_title\n")

    files = scan_music(folder)
    if not files:
        print("# 沒找到任何音樂檔案。")
        return

    for idx, (_, rel_path, title) in enumerate(files, start=1):
        print(f"{idx}\t{rel_path}\t{title}")

    print(f"\n# 共 {len(files)} 首音樂")
    print("# 請複製以上內容交給 ChatGPT 做『Hip-Hop / 中文 / 英文』分析。")

if __name__ == "__main__":
    main()