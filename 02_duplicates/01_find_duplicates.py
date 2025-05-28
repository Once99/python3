import os
import hashlib
from collections import defaultdict
from tkinter import Tk, filedialog
from tqdm import tqdm

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
    except Exception as e:
        print(f"❌ 無法讀取 {file_path}：{e}")
        return None

def find_duplicate_photos(folder):
    hash_map = defaultdict(list)
    print("🔍 開始掃描圖片檔案...")
    for root, _, files in os.walk(folder):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in IMAGE_EXTS:
                file_path = os.path.join(root, file)
                file_hash = get_file_hash(file_path)
                if file_hash:
                    hash_map[file_hash].append(file_path)

    duplicates = [paths for paths in hash_map.values() if len(paths) > 1]
    return duplicates

def main():
    folder = select_directory()
    if not folder:
        print("❌ 沒有選擇資料夾，已中止")
        return

    duplicates = find_duplicate_photos(folder)

    if not duplicates:
        print("✅ 沒有發現重複的照片")
    else:
        print(f"\n📸 找到 {len(duplicates)} 組重複的照片：\n")
        for i, group in enumerate(duplicates, 1):
            print(f"🧩 重複組 {i}:")
            for path in group:
                print(f"   - {path}")
            print()

if __name__ == "__main__":
    main()
