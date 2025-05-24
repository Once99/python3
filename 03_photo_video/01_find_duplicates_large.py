import os
import hashlib
from tqdm import tqdm
from datetime import datetime
from tkinter import Tk, filedialog

# 支援的圖片與影片副檔名
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.mpeg', '.webm'}
ALL_EXTS = IMAGE_EXTS.union(VIDEO_EXTS)

def get_file_hash(file_path, chunk_size=4096):
    """計算檔案 SHA256 雜湊"""
    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"無法讀取 {file_path}：{e}")
        return None

def find_duplicates_and_largest(folder):
    hashes = {}
    size_groups = {}  # ➜ 先依大小分組
    file_list = []
    total_size = 0
    duplicate_size = 0
    duplicates = []

    # 收集所有檔案
    for root, _, files in os.walk(folder):
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext in ALL_EXTS:
                full_path = os.path.join(root, filename)
                try:
                    size = os.path.getsize(full_path)
                    total_size += size
                    file_list.append((full_path, size))
                    size_groups.setdefault(size, []).append(full_path)  # 分組
                except Exception as e:
                    print(f"❌ 無法取得大小 {full_path}: {e}")

    # 對同大小的檔案群組進行雜湊比對
    for size, paths in tqdm(size_groups.items(), desc="處理進度"):
        if len(paths) < 2:
            continue  # 不可能重複
        for path in paths:
            file_hash = get_file_hash(path)
            if file_hash in hashes:
                existing_path = hashes[file_hash]

                # 比較修改時間
                try:
                    existing_mtime = os.path.getmtime(existing_path)
                    current_mtime = os.path.getmtime(path)
                except Exception as e:
                    print(f"⚠️ 無法取得 mtime：{e}")
                    continue

                if current_mtime > existing_mtime:
                    print(f"⚠️ 找到重複：\n   原始：{existing_path}\n   重複：{path}")
                    duplicates.append((existing_path, path, size))
                else:
                    print(f"⚠️ 找到重複：\n   原始：{path}\n   重複：{existing_path}")
                    duplicates.append((path, existing_path, size))
                    hashes[file_hash] = path  # 更新為新的原始基準
                duplicate_size += size
            else:
                hashes[file_hash] = path



# 找出前 20 大檔案
    top_20_largest = sorted(file_list, key=lambda x: x[1], reverse=True)[:20]

    stats = {
        "total_files": len(file_list),
        "total_size": total_size,
        "duplicate_count": len(duplicates),
        "duplicate_size": duplicate_size
    }

    return duplicates, top_20_largest, stats


def write_output(duplicates, largest_files, stats, timestamp):
    dup_file = f'{timestamp}_duplicates_files.txt'
    size_file = f'{timestamp}_largest_files.txt'

    # 將重複檔案依照 hash 分組
    grouped = {}
    for original, duplicate, size in duplicates:
        key = original  # 用原始檔案當作分組 key
        if key not in grouped:
            grouped[key] = []
        grouped[key].append((duplicate, size))

    with open(dup_file, 'w', encoding='utf-8') as f:
        f.write("📁 重複檔案清單：\n\n")
        for original, dup_list in grouped.items():
            f.write(f"🟡 原始檔案: {original}\n")
            for duplicate, size in dup_list:
                f.write(f"    🔁 重複檔案: {duplicate}\n")
                f.write(f"       檔案大小: {size / (1024 * 1024):.2f} MB\n")
            f.write("------------------------------------------------------------\n")
    print(f"✅ 已寫入 {len(duplicates)} 筆重複資料到 {dup_file}")

    with open(size_file, 'w', encoding='utf-8') as f:
        f.write("📊 統計資訊\n")
        f.write(f"掃描檔案總數: {stats['total_files']}\n")
        f.write(f"掃描總大小: {stats['total_size'] / (1024 * 1024):.2f} MB\n")
        f.write(f"重複檔案數量: {stats['duplicate_count']}\n")
        f.write(f"可釋放空間總計: {stats['duplicate_size'] / (1024 * 1024):.2f} MB\n")
        f.write("\n📁 前 20 大檔案：\n")
        for path, size in largest_files:
            f.write(f"{path} ({size / (1024 * 1024):.2f} MB)\n")
    print(f"✅ 已寫入前 20 大檔案與統計資訊到 {size_file}")

if __name__ == "__main__":
    folder_to_scan = filedialog.askdirectory(title="請選擇要掃描的資料夾")

    if not os.path.isdir(folder_to_scan):
        print("❌ 指定的路徑不存在或不是資料夾。")
    else:
        timestamp = datetime.now().strftime('%m%d_%H%M')
        dup_files, largest_files, stats = find_duplicates_and_largest(folder_to_scan)
        write_output(dup_files, largest_files, stats, timestamp)
