import os
import shutil
import datetime
from PIL import Image
from PIL.ExifTags import TAGS
from tkinter import filedialog, Tk

def get_taken_year(img_path):
    try:
        img = Image.open(img_path)
        exif_data = img._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'DateTimeOriginal':
                    return value.split(':')[0]
    except Exception:
        pass

    # 如果沒有 EXIF，回傳檔案修改時間的年份
    try:
        timestamp = os.path.getmtime(img_path)
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y')
    except Exception:
        return None

def get_photos(folder):
    supported_exts = ['.jpg', '.jpeg', '.png', '.heic', '.tiff']
    photo_paths = []
    for root, _, files in os.walk(folder):
        for file in files:
            if any(file.lower().endswith(ext) for ext in supported_exts):
                photo_paths.append(os.path.join(root, file))
    return photo_paths

def group_photos_by_year(photo_paths, base_folder):
    move_plan = []

    for path in photo_paths:
        year = get_taken_year(path)
        if year:
            target_folder = os.path.join(base_folder, year)
        else:
            target_folder = os.path.join(base_folder, "Unknown")

        move_plan.append((path, target_folder))

    return move_plan

def display_plan(move_plan):
    print("\n📦 預計搬移以下照片：")
    for src, dst_folder in move_plan:
        dst = os.path.join(dst_folder, os.path.basename(src))
        print(f"→ {src} → {dst}")

    print(f"\n🧮 共 {len(move_plan)} 張照片將被搬移。")

def execute_plan(move_plan):
    for src, dst_folder in move_plan:
        os.makedirs(dst_folder, exist_ok=True)
        dst = os.path.join(dst_folder, os.path.basename(src))
        shutil.move(src, dst)
    print("\n✅ 照片已依照年份分類並搬移完成。")

def main():
    root = Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="選擇照片資料夾")
    if not folder:
        print("⚠️ 未選擇任何資料夾。")
        return

    photos = get_photos(folder)
    move_plan = group_photos_by_year(photos, folder)
    display_plan(move_plan)

    confirm = input("\n是否要執行實際搬移？(y/n): ").strip().lower()
    if confirm == 'y':
        execute_plan(move_plan)
    else:
        print("❌ 操作已取消，未進行任何搬移。")

if __name__ == "__main__":
    main()