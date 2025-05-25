import os
from datetime import datetime
from PIL import Image, ExifTags
from tkinter import Tk, filedialog

def get_date_taken(path):
    try:
        image = Image.open(path)
        exif_data = image._getexif()
        if not exif_data:
            return None
        # 取得 EXIF 標籤名稱對應的字典
        exif = {
            ExifTags.TAGS.get(tag, tag): value
            for tag, value in exif_data.items()
        }
        date_str = exif.get('DateTimeOriginal') or exif.get('DateTime')
        if date_str:
            return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        print(f"無法處理檔案 {path}：{e}")
    return None

def find_photos_in_jan_2019(folder):
    matched_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg')):
                full_path = os.path.join(root, file)
                date_taken = get_date_taken(full_path)
                if date_taken and date_taken.year == 2019 and date_taken.month == 1:
                    matched_files.append(full_path)
    return matched_files

# 使用範例
if __name__ == "__main__":
    folder_path = filedialog.askdirectory(title="請選擇要掃描的資料夾")
    results = find_photos_in_jan_2019(folder_path)
    print(f"\n找到 {len(results)} 張 2019 年 1 月的照片：")
    for path in results:
        print(path)
