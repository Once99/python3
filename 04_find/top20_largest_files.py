import os

# 支援的圖片與影片副檔名
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.mpeg', '.webm'}
ALL_EXTS = IMAGE_EXTS.union(VIDEO_EXTS)

def find_largest_files(folder, top_n=20):
    file_list = []

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

    # 按大小排序並取前 N 筆
    top_files = sorted(file_list, key=lambda x: x[1], reverse=True)[:top_n]
    return top_files

def write_largest_files(top_files, output_file='largest_files.txt'):
    with open(output_file, 'w', encoding='utf-8') as f:
        for path, size in top_files:
            f.write(f"{path} ({size / (1024 * 1024):.2f} MB)\n")
    print(f"✅ 已寫入前 {len(top_files)} 大檔案到 {output_file}")

if __name__ == "__main__":
    folder_to_scan = "/Volumes/My Passport/"
    if not os.path.isdir(folder_to_scan):
        print("❌ 指定的路徑不存在或不是資料夾。")
    else:
        largest_files = find_largest_files(folder_to_scan)
        write_largest_files(largest_files)
