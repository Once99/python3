import os
import hashlib
from collections import defaultdict
from tkinter import Tk, filedialog
from datetime import datetime
from tqdm import tqdm
import subprocess

# 支援的圖片副檔名
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}

def select_directory():
    root = Tk()
    root.withdraw()
    return filedialog.askdirectory(title="選擇要掃描的目錄")

def get_file_hash(file_path, chunk_size=4096):
    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None

def collect_all_files(folder):
    all_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            all_files.append(os.path.join(root, file))
    return all_files

def find_duplicates_optimized(all_files, filter_exts=None):
    size_map = defaultdict(list)
    # 先依檔案大小分組
    for path in all_files:
        if filter_exts:
            ext = os.path.splitext(path)[1].lower()
            if ext not in filter_exts:
                continue
        try:
            size = os.path.getsize(path)
            size_map[size].append(path)
        except Exception:
            continue

    hash_map = defaultdict(list)
    total_candidates = sum(len(group) for group in size_map.values() if len(group) > 1)

    with tqdm(total=total_candidates, desc="🔍 計算雜湊中") as pbar:
        for group in size_map.values():
            if len(group) < 2:
                continue
            for path in group:
                file_hash = get_file_hash(path)
                if file_hash:
                    hash_map[file_hash].append(path)
                pbar.update(1)

    return [group for group in hash_map.values() if len(group) > 1]

def write_log(duplicates, output_path, mode_name):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_groups = len(duplicates)
    total_files = sum(len(group) for group in duplicates)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# 重複檔案掃描報告\n")
        f.write(f"# 時間：{now_str}\n")
        f.write(f"# 模式：{mode_name}\n")
        f.write(f"# 重複組數：{total_groups}\n")
        f.write(f"# 重複檔案總數：{total_files}\n")
        f.write(f"# 格式：每組間以 '---' 分隔\n\n")

        for group in duplicates:
            for path in group:
                f.write(path + '\n')
            f.write('---\n')

def main():
    folder = select_directory()
    if not folder:
        print("❌ 沒有選擇資料夾，已中止")
        return

    print("\n請選擇搜尋模式：")
    print("1. 只尋找照片重複")
    print("2. 尋找任何檔案重複")
    mode = input("請輸入 1 或 2：").strip()

    print("📦 正在統計檔案總數...")
    all_files = collect_all_files(folder)

    if mode == '1':
        duplicates = find_duplicates_optimized(all_files, filter_exts=IMAGE_EXTS)
        mode_name = "只尋找照片重複"
    elif mode == '2':
        duplicates = find_duplicates_optimized(all_files, filter_exts=None)
        mode_name = "尋找任何檔案重複"
    else:
        print("❌ 無效的選擇，請輸入 1 或 2")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"duplicates_log_{timestamp}.txt"

    if duplicates:
        write_log(duplicates, log_filename, mode_name)
        print(f"\n✅ 共找到 {len(duplicates)} 組重複檔案，已寫入 {log_filename}")
        # subprocess.run(["open", log_filename])  # 🔥 自動開啟結果檔
    else:
        print("\n✅ 沒有找到任何重複檔案")


if __name__ == "__main__":
    main()
