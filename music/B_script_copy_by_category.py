#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B_script_copy_by_category_with_dialog.py
----------------------------------------
步驟三腳本：彈出視窗讓你選擇音樂根目錄，再依
「中文 / 英文」+「hip-hop / 其他」四大類自動分類並拷貝。

分類：
  - 中文-hiphop
  - 中文-其他
  - 英文-hiphop
  - 英文-其他
"""

import os
import sys
import shutil
import tkinter as tk
from tkinter import filedialog

# 支援的音樂副檔名
SUPPORTED_EXTS = {
    '.mp3', '.m4a', '.aac',
    '.flac', '.ogg', '.wav',
    '.wma', '.alac', '.aiff', '.aif'
}

# === 英文 hip-hop 關鍵字 ===
EN_HIPHOP_KEYWORDS = [
    'eminem', 'snoop dogg', 'snoop',
    'dr. dre', 'dr dre',
    '50 cent', '50cent',
    'dmx', 'ice cube', 'xzibit',
    'post malone', 'jay-z', 'jay z',
    'kendrick lamar', 'kanye west',
    'still d.r.e', 'still dre',
    'drop it like it\'s hot',
    'numb _ encore', 'numb/encore',
    'sunflower (spider-man'
]

# === 中文 hip-hop 關鍵字 ===
ZH_HIPHOP_KEYWORDS = [
    '高爾宣', 'OSN',
    '頑童', 'MJ116',
    '瘦子', 'E.SO',
    '兄弟本色', 'G.U.T.S',
    '玖壹壹', '蜜汁沼澤', 'G22',
    'J.Sheon', 'Karencici'
]


# ---------------- 工具區 ----------------

def is_chinese(text: str) -> bool:
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff':
            return True
    return False


def is_hiphop(title: str, rel_path: str) -> bool:
    combo = f"{title} {rel_path}"
    combo_lower = combo.lower()

    for kw in EN_HIPHOP_KEYWORDS:
        if kw in combo_lower:
            return True

    for kw in ZH_HIPHOP_KEYWORDS:
        if kw in combo:
            return True

    if 'hip-hop' in combo_lower or 'hip hop' in combo_lower or 'rap ' in combo_lower:
        return True

    return False


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


def classify_tracks(root_dir):
    files = scan_music(root_dir)
    categories = {
        "中文-hiphop": [],
        "中文-其他": [],
        "英文-hiphop": [],
        "英文-其他": []
    }

    for full_path, rel_path, title in files:
        text = f"{title} {rel_path}"
        is_zh = is_chinese(text)
        is_hh = is_hiphop(title, rel_path)

        if is_zh and is_hh:
            categories["中文-hiphop"].append((full_path, rel_path, title))
        elif is_zh:
            categories["中文-其他"].append((full_path, rel_path, title))
        elif is_hh:
            categories["英文-hiphop"].append((full_path, rel_path, title))
        else:
            categories["英文-其他"].append((full_path, rel_path, title))

    return categories


def print_classification(categories):
    print("\n========== 分類結果預覽 ==========")
    total = 0

    for cat, items in categories.items():
        print(f"\n【{cat}】共 {len(items)} 首：")
        for _, rel_path, title in items[:20]:
            print(f"  - {rel_path}  |  {title}")
        if len(items) > 20:
            print(f"  ... (還有 {len(items) - 20} 首)")
        total += len(items)

    print(f"\n========== 總計：{total} 首 ==========\n")


def copy_by_category(categories, root_dir, dest_root):
    for cat, items in categories.items():
        for full_path, rel_path, title in items:
            dest_dir = os.path.join(dest_root, cat, os.path.dirname(rel_path))
            os.makedirs(dest_dir, exist_ok=True)

            dest_path = os.path.join(dest_dir, os.path.basename(full_path))

            try:
                shutil.copy2(full_path, dest_path)
                print(f"[COPY] {full_path} -> {dest_path}")
            except Exception as e:
                print(f"[ERROR] 無法拷貝：{full_path} -> {dest_path} ({e})")


# ---------------- 主流程 ----------------

def main():
    print("請選擇音樂根目錄...")

    root = tk.Tk()
    root.withdraw()

    music_root = filedialog.askdirectory(title="選擇音樂根目錄")
    if not music_root:
        print("[取消] 未選取資料夾，腳本結束。")
        return

    music_root = os.path.abspath(music_root)
    print(f"\n[*] 音樂根目錄：{music_root}")

    categories = classify_tracks(music_root)
    print_classification(categories)

    do_copy = input("是否要開始拷貝到新目錄？(y/N)：").strip().lower()
    if do_copy != 'y':
        print("[INFO] 已取消拷貝。")
        return

    print("\n請選擇『分類後要輸出的目錄』...")
    dest_root = filedialog.askdirectory(title="選擇結果輸出目錄")
    if not dest_root:
        print("[取消] 未選取輸出資料夾。")
        return

    dest_root = os.path.abspath(dest_root)
    print(f"[*] 開始拷貝到：{dest_root}")

    copy_by_category(categories, music_root, dest_root)

    print("\n[DONE] 已完成！所有檔案已成功分類並拷貝。")


if __name__ == "__main__":
    main()