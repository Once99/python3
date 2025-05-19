import os
import hashlib
from collections import defaultdict

# 支援的照片與影片格式副檔名
SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp',
                        '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv')

def hash_file(filepath, block_size=65536):
    print(f"🔍 正在讀取檔案：{filepath}")
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(block_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"❌ 無法讀取 {filepath}: {e}")
        return None

def find_duplicates(root_dir):
    hash_dict = defaultdict(list)
    total = 0
    for foldername, subfolders, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(SUPPORTED_EXTENSIONS):
                total += 1
                print(f"🔍 發現 {total} 個照片/影片檔案，開始比對中...\n")
                full_path = os.path.join(foldername, filename)
                file_hash = hash_file(full_path)
                if file_hash:
                    hash_dict[file_hash].append(full_path)
    return {h: paths for h, paths in hash_dict.items() if len(paths) > 1}

if __name__ == "__main__":
    # folder_to_scan = input("請輸入資料夾路徑：").strip()
    folder_to_scan = "/Users/oncechen/Library/CloudStorage/GoogleDrive-howard123702002@gmail.com/我的雲端硬碟/新增包含項目的檔案夾"
    if not os.path.isdir(folder_to_scan):
        print("❌ 找不到資料夾，請確認路徑正確。")
    else:
        print("✅ 開始掃描資料夾...\n")
        duplicates = find_duplicates(folder_to_scan)
        if not duplicates:
            print("✅ 沒有發現重複的照片或影片。")
        else:
            print("⚠️ 發現以下重複檔案：\n")
            for i, paths in enumerate(duplicates.values(), 1):
                print(f"🔁 重複組 #{i}:")
                for p in paths:
                    print(f"  - {p}")
                print()


