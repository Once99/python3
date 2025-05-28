import os
import shutil
from PIL import Image, ExifTags
from datetime import datetime
from tqdm import tqdm
from tkinter import Tk, filedialog, simpledialog, messagebox

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.mpeg', '.webm'}
ALL_EXTS = IMAGE_EXTS.union(VIDEO_EXTS)

def select_directory():
    root = Tk()
    root.withdraw()
    return filedialog.askdirectory(title="選擇來源目錄")

def ask_interval_mode():
    root = Tk()
    root.withdraw()
    result = messagebox.askquestion("選擇時間間隔方式", "是否要以『一天』為分組間隔？\n\n選『是』 ➜ 每一天一組\n選『否』 ➜ 自訂分鐘間隔")
    if result == 'yes':
        return 'day', None
    else:
        try:
            minutes = simpledialog.askinteger("輸入間隔", "請輸入時間間隔（單位：分鐘）", initialvalue=10, minvalue=1, maxvalue=180)
            return 'minute', minutes or 10
        except Exception:
            return 'minute', 10

def get_taken_time(file_path):
    try:
        if file_path.lower().endswith(tuple(IMAGE_EXTS)):
            image = Image.open(file_path)
            exif_data = image._getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = ExifTags.TAGS.get(tag_id)
                    if tag == 'DateTimeOriginal':
                        return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
        timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp)
    except Exception:
        return None

def group_by_scene(file_paths, interval_mode='minute', interval_value=10):
    grouped = []
    file_paths_with_time = []

    for path in file_paths:
        taken_time = get_taken_time(path)
        if taken_time:
            file_paths_with_time.append((path, taken_time))

    file_paths_with_time.sort(key=lambda x: x[1])

    current_group = []
    last_time = None
    interval_seconds = 86400 if interval_mode == 'day' else interval_value * 60

    for path, taken_time in file_paths_with_time:
        if last_time is None or (taken_time - last_time).total_seconds() > interval_seconds:
            if current_group:
                grouped.append(current_group)
            current_group = [path]
        else:
            current_group.append(path)
        last_time = taken_time

    if current_group:
        grouped.append(current_group)

    return grouped

def preview_groups(groups):
    print("\n📋 預覽分類結果：")
    for idx, group in enumerate(groups, 1):
        print(f"\n📂 場景 {idx:03d}：共 {len(group)} 檔案")
        for path in group:
            print(f" - {os.path.basename(path)}")
    print(f"\n✅ 共分出 {len(groups)} 組場景")

def copy_to_output(groups, output_base):
    os.makedirs(output_base, exist_ok=True)
    for idx, group in enumerate(tqdm(groups, desc="🚀 拷貝中"), 1):
        group_folder = os.path.join(output_base, f"scene_{idx:03d}")
        os.makedirs(group_folder, exist_ok=True)
        for path in group:
            try:
                filename = os.path.basename(path)
                shutil.copy2(path, os.path.join(group_folder, filename))
            except Exception as e:
                print(f"❌ 無法複製 {path}：{e}")

def main():
    src_folder = select_directory()
    if not src_folder:
        print("❌ 未選擇來源資料夾")
        return

    interval_mode, interval_value = ask_interval_mode()

    all_files = []
    for root, _, files in os.walk(src_folder):
        for file in files:
            if os.path.splitext(file)[1].lower() in ALL_EXTS:
                all_files.append(os.path.join(root, file))

    print(f"\n🔍 共找到 {len(all_files)} 個媒體檔案，正在分析時間…")
    groups = group_by_scene(all_files, interval_mode=interval_mode, interval_value=interval_value)

    preview_groups(groups)

    answer = input("\n是否要拷貝分類結果到 output 資料夾？ (Y/N)：").strip().lower()
    if answer == 'y':
        output_folder = os.path.join(os.path.dirname(src_folder), "output")
        copy_to_output(groups, output_folder)
        print(f"\n✅ 已成功拷貝到 {output_folder}")
    else:
        print("\n❌ 已取消拷貝動作。")

if __name__ == "__main__":
    main()
