import os
import hashlib
from tqdm import tqdm

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
    """尋找重複的檔案，並同時找出檔案最大的20個"""
    hashes = {}
    duplicates = []
    file_list = []

    # 收集所有檔案資訊
    for root, _, files in os.walk(folder):
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext in ALL_EXTS:
                full_path = os.path.join(root, filename)
                try:
                    size = os.path.getsize(full_path)
                    file_list.append((full_path, size))
                except Exception as e:
                    print(f"❌ 無法取得大小 {full_path}: {e}")

    # 根據雜湊比對找重複
    for full_path, _ in tqdm(file_list, desc="處理進度"):
        file_hash = get_file_hash(full_path)
        if file_hash:
            if file_hash in hashes:
                duplicates.append((hashes[file_hash], full_path))
            else:
                hashes[file_hash] = full_path

    # 按大小排序，取出前 20 名
    top_20_largest = sorted(file_list, key=lambda x: x[1], reverse=True)[:20]

    return duplicates, top_20_largest

def write_output(duplicates, largest_files, dup_file='duplicates_files.txt', size_file='largest_files.txt'):
    with open(dup_file, 'w', encoding='utf-8') as f:
        for original, duplicate in duplicates:
            f.write(f"原始檔案: {original}\n重複檔案: {duplicate}\n\n")
    print(f"✅ 已寫入 {len(duplicates)} 筆重複資料到 {dup_file}")

    with open(size_file, 'w', encoding='utf-8') as f:
        for path, size in largest_files:
            f.write(f"{path} ({size / (1024 * 1024):.2f} MB)\n")
    print(f"✅ 已寫入前 20 大檔案資訊到 {size_file}")

if __name__ == "__main__":
    folder_to_scan = "/Volumes/My Passport/【　Ａ、在菲照片　】"
    if not os.path.isdir(folder_to_scan):
        print("❌ 指定的路徑不存在或不是資料夾。")
    else:
        dup_files, largest_files = find_duplicates_and_largest(folder_to_scan)
        write_output(dup_files, largest_files)
