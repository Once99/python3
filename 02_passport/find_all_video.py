import os
import shutil
import datetime
from tkinter import filedialog, Tk

def get_file_year(path):
    try:
        timestamp = os.path.getmtime(path)
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y')
    except Exception:
        return None

def get_videos(folder):
    supported_exts = ['.mp4', '.mov', '.avi', '.mkv', '.flv']
    video_paths = []
    for root, _, files in os.walk(folder):
        for file in files:
            if any(file.lower().endswith(ext) for ext in supported_exts):
                video_paths.append(os.path.join(root, file))
    return video_paths

def group_videos_by_year(video_paths, base_folder):
    move_plan = []
    no_date_videos = []

    for path in video_paths:
        year = get_file_year(path)
        if year:
            target_folder = os.path.join(base_folder, year)
        else:
            target_folder = os.path.join(base_folder, "Unknown")
            no_date_videos.append(path)

        move_plan.append((path, target_folder))

    return move_plan, no_date_videos

def display_plan(move_plan, no_date_videos):
    print("\n📦 預計搬移以下影片：")
    for src, dst_folder in move_plan:
        dst = os.path.join(dst_folder, os.path.basename(src))
        print(f"→ {src} → {dst}")

    print(f"\n🧮 共 {len(move_plan)} 部影片將被搬移：")
    print(f"   ✔ 有檔案修改日期：{len(move_plan) - len(no_date_videos)}")
    print(f"   ⚠ 無日期資訊：{len(no_date_videos)}（將歸入 Unknown 資料夾）")

def execute_plan(move_plan):
    for src, dst_folder in move_plan:
        os.makedirs(dst_folder, exist_ok=True)
        dst = os.path.join(dst_folder, os.path.basename(src))
        shutil.move(src, dst)
    print("\n✅ 影片已依照年份分類並搬移完成。")

def main():
    root = Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="選擇影片資料夾")
    if not folder:
        print("⚠️ 未選擇任何資料夾。")
        return

    videos = get_videos(folder)
    move_plan, no_date_videos = group_videos_by_year(videos, folder)
    display_plan(move_plan, no_date_videos)

    confirm = input("\n是否要執行實際搬移？(y/n): ").strip().lower()
    if confirm == 'y':
        execute_plan(move_plan)
    else:
        print("❌ 操作已取消，未進行任何搬移。")

if __name__ == "__main__":
    main()