#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
import subprocess
import platform

IGNORE_FILES = {'.DS_Store', '.gitkeep'}

def select_directory() -> str:
    root = tk.Tk()
    root.withdraw()
    return filedialog.askdirectory(title="請選擇要掃描的資料夾")

def find_empty_dirs(base_path: str) -> list:
    empty_dirs = []
    for root, dirs, files in os.walk(base_path, topdown=False):
        valid_files = [f for f in files if f not in IGNORE_FILES]
        if not valid_files and not dirs:
            empty_dirs.append(os.path.relpath(root, base_path))
    return empty_dirs

def count_files_and_size(base_path: str) -> tuple:
    total_files = 0
    total_size = 0
    for root, _, files in os.walk(base_path):
        for f in files:
            if f in IGNORE_FILES:
                continue
            file_path = os.path.join(root, f)
            try:
                total_files += 1
                total_size += os.path.getsize(file_path)
            except Exception:
                continue
    return total_files, total_size

def write_result_to_file(base_path: str, empty_dirs: list) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{timestamp}_empty_dirs.txt"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, output_filename)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"共找到 {len(empty_dirs)} 個空目錄：\n\n")
        for path in empty_dirs:
            f.write(f"{path}\n")

    open_text_file(output_path)
    return output_path

def open_text_file(filepath: str):
    """根據作業系統自動打開文字檔"""
    try:
        if platform.system() == "Darwin":  # macOS
            subprocess.run(["open", filepath])
        elif platform.system() == "Windows":
            os.startfile(filepath)
        elif platform.system() == "Linux":
            subprocess.run(["xdg-open", filepath])
    except Exception as e:
        print(f"⚠️ 無法自動開啟結果檔案：{e}")

def confirm(prompt: str) -> bool:
    while True:
        ans = input(f"{prompt} (y/N): ").strip().lower()
        if ans in ('y', 'yes'):
            return True
        elif ans in ('n', 'no', ''):
            return False
        else:
            print("請輸入 y 或 n")

def delete_empty_dirs(base_path: str, rel_paths: list):
    deleted = []
    failed = []

    for rel_path in rel_paths:
        full_path = os.path.join(base_path, rel_path)
        try:
            os.rmdir(full_path)
            deleted.append(rel_path)
        except Exception as e:
            failed.append((rel_path, str(e)))

    # 顯示結果
    print(f"\n🗑️ 已成功刪除 {len(deleted)} 個目錄：")
    for d in deleted:
        print(f"  ✅ {d}")

    if failed:
        print(f"\n⚠️ 無法刪除 {len(failed)} 個目錄：")
        for d, err in failed:
            print(f"  ❌ {d} - {err}")

def main():
    target_dir = select_directory()
    if not target_dir:
        print("❌ 未選擇任何目錄，結束程序")
        return

    print(f"\n📁 掃描目錄：{target_dir}\n" + "=" * 50)

    total_files, total_size = count_files_and_size(target_dir)
    size_mb = round(total_size / (1024 * 1024), 2)
    print(f"\n📊 檔案統計：{total_files} 個檔案，{size_mb} MB")

    empty_dirs = find_empty_dirs(target_dir)
    if empty_dirs:
        print(f"\n🗂️ 共找到 {len(empty_dirs)} 個空目錄：")
        for path in empty_dirs:
            print(f"📂 {path}")

        output_file = write_result_to_file(target_dir, empty_dirs)
        print(f"\n📝 結果已寫入並自動開啟：{output_file}")

        if confirm("\n是否要刪除這些空目錄？"):
            delete_empty_dirs(target_dir, empty_dirs)
    else:
        print("\n🎉 沒有發現空目錄")

if __name__ == "__main__":
    main()
