import os
import hashlib
from collections import defaultdict
from tkinter import Tk, filedialog

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
LOG_FILENAME = "duplicates_log.txt"

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

def find_duplicate_photos(folder):
    hash_map = defaultdict(list)
    for root, _, files in os.walk(folder):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in IMAGE_EXTS:
                path = os.path.join(root, file)
                file_hash = get_file_hash(path)
                if file_hash:
                    hash_map[file_hash].append(path)

    return [group for group in hash_map.values() if len(group) > 1]

def write_log(duplicates, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        for group in duplicates:
            for path in group:
                f.write(path + '\n')
            f.write('---\n')  # 每組重複檔案之間用分隔線

def main():
    folder = select_directory()
    if not folder:
        print("❌ 沒有選擇資料夾，已中止")
        return

    duplicates = find_duplicate_photos(folder)
    if duplicates:
        write_log(duplicates, LOG_FILENAME)
        print(f"✅ 已將 {len(duplicates)} 組重複照片寫入 {LOG_FILENAME}")
    else:
        print("✅ 沒有找到任何重複照片")

if __name__ == "__main__":
    main()
