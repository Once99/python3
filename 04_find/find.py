import os
import hashlib
from tqdm import tqdm  # <--- 新增

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

def find_duplicates(folder):
    """尋找重複的檔案，並顯示進度條"""
    hashes = {}
    duplicates = []
    file_list = []

    # 先收集所有檔案路徑（方便計算總數用於 tqdm）
    for root, _, files in os.walk(folder):
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext in ALL_EXTS:
                file_list.append(os.path.join(root, filename))

    # 開始比對檔案
    for full_path in tqdm(file_list, desc="處理進度"):
        file_hash = get_file_hash(full_path)
        if file_hash:
            if file_hash in hashes:
                duplicates.append((hashes[file_hash], full_path))
            else:
                hashes[file_hash] = full_path

    return duplicates

def write_output(duplicates, output_file='output.txt'):
    with open(output_file, 'w', encoding='utf-8') as f:
        for original, duplicate in duplicates:
            f.write(f"原始檔案: {original}\n重複檔案: {duplicate}\n\n")
    print(f"✅ 已寫入 {len(duplicates)} 筆重複資料到 {output_file}")

if __name__ == "__main__":
    folder_to_scan = "/Volumes/My Passport/【　Ａ、在菲照片　】"
    if not os.path.isdir(folder_to_scan):
        print("❌ 指定的路徑不存在或不是資料夾。")
    else:
        dup_files = find_duplicates(folder_to_scan)
        write_output(dup_files)
