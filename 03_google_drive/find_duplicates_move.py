import os
import hashlib
import shutil
from tqdm import tqdm
from datetime import datetime
from tkinter import filedialog

# 支援副檔名
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.mpeg', '.webm'}
ALL_EXTS = IMAGE_EXTS.union(VIDEO_EXTS)

def get_file_hash(file_path, chunk_size=4096):
    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"❌ 無法讀取 {file_path}：{e}")
        return None

def find_duplicates(folder):
    hashes = {}
    duplicates = []
    file_list = []

    print("🔍 掃描檔案中...")
    for root, _, files in os.walk(folder):
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext in ALL_EXTS:
                full_path = os.path.join(root, filename)
                file_list.append(full_path)

    for path in tqdm(file_list, desc="🔑 計算檔案雜湊"):
        file_hash = get_file_hash(path)
        if file_hash:
            if file_hash in hashes:
                print(f"⚠️ 找到重複：\n   原始：{hashes[file_hash]}\n   重複：{path}")
                duplicates.append((hashes[file_hash], path))
            else:
                hashes[file_hash] = path

    return duplicates

def move_duplicates(duplicates, base_folder, timestamp):
    output_base = os.path.join(base_folder, f"{timestamp}_duplicates_output")
    os.makedirs(output_base, exist_ok=True)
    moved_log = os.path.join(base_folder, f"{timestamp}_duplicates.txt")

    with open(moved_log, 'w', encoding='utf-8') as f:
        f.write("📁 搬移的重複檔案清單：\n\n")
        for idx, (original, dup) in enumerate(tqdm(duplicates, desc="📦 搬移重複檔案"), 1):
            rel_path = os.path.relpath(dup, base_folder)
            dest_path = os.path.join(output_base, rel_path)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            try:
                shutil.move(dup, dest_path)
                size = os.path.getsize(dest_path)
                print(f"✅ 已搬移 ({idx}): {dup} → {dest_path} [{size / (1024 * 1024):.2f} MB]")
                f.write(f"🟡 原始檔案: {original}\n")
                f.write(f"    🔁 搬移至: {dest_path}\n")
                f.write(f"       檔案大小: {size / (1024 * 1024):.2f} MB\n")
                f.write("------------------------------------------------------------\n")
            except Exception as e:
                print(f"❌ 搬移失敗: {dup} → {dest_path}，錯誤：{e}")
                f.write(f"❌ 搬移失敗: {dup} -> {dest_path}，錯誤：{e}\n")

    print(f"\n✅ 完成！搬移記錄已寫入：{moved_log}")

if __name__ == "__main__":
    folder = filedialog.askdirectory(title="請選擇要掃描的資料夾")

    if not folder or not os.path.isdir(folder):
        print("❌ 無效路徑")
    else:
        timestamp = datetime.now().strftime('%m%d_%H%M')
        duplicates = find_duplicates(folder)
        if duplicates:
            print(f"\n🧾 共找到 {len(duplicates)} 個重複檔案")
            confirm = input("📦 是否搬移到 output 資料夾？(y/n): ").strip().lower()
            if confirm == 'y':
                move_duplicates(duplicates, folder, timestamp)
            else:
                print("📁 已保留所有檔案")
        else:
            print("🎉 沒有找到重複檔案")
