import os
import shutil
import re
from PIL import Image, ExifTags, ImageFile
from tkinter import Tk, filedialog
from tqdm import tqdm

ImageFile.LOAD_TRUNCATED_IMAGES = True

# 分類標籤
CATEGORY_CAMERA = "分類_手機拍攝"
CATEGORY_SCREENSHOT = "分類_手機截圖"
CATEGORY_DOWNLOADED = "分類_網路下載"
CATEGORY_OTHER = "分類_其他"

SUPPORTED_EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')

SCREENSHOT_PATTERNS = [
    r"^Screenshot_\d{8}-\d{6}",
    r"^IMG_\d{8}_\d{6}",
    r"^IMG-\d{8}-WA\d+",
    r"^Capture\+\d{8}_\d{6}",
    r"^スクリーンショット",
    r"^屏幕截图",
]

COMMON_SCREEN_RESOLUTIONS = [
    (1080, 1920), (1920, 1080),
    (1170, 2532), (2532, 1170),
    (1242, 2688), (2688, 1242),
    (828, 1792), (1792, 828),
    (1080, 2340), (2340, 1080),
]

def is_camera_photo(image_path):
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        if not exif_data:
            return False
        for tag_id, value in exif_data.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            if tag == 'Make' and isinstance(value, str):
                if any(brand in value for brand in ["Apple", "iPhone", "Samsung", "Huawei", "Xiaomi", "OPPO", "Vivo"]):
                    return True
    except:
        return False
    return False

def is_screenshot(file_name, width, height):
    for pattern in SCREENSHOT_PATTERNS:
        if re.match(pattern, file_name, re.IGNORECASE):
            if (width, height) in COMMON_SCREEN_RESOLUTIONS or (height, width) in COMMON_SCREEN_RESOLUTIONS:
                return True
    return False

def safe_move_or_copy(src_path, dst_dir, do_move):
    """避免同名檔案覆蓋，必要時自動加上編號，並根據選項移動或複製"""
    base_name = os.path.basename(src_path)
    name, ext = os.path.splitext(base_name)
    counter = 1
    target_path = os.path.join(dst_dir, base_name)

    while os.path.exists(target_path):
        target_path = os.path.join(dst_dir, f"{name}_{counter}{ext}")
        counter += 1

    if do_move:
        shutil.move(src_path, target_path)
    else:
        shutil.copy2(src_path, target_path)

    return target_path

def scan_images(source_folder):
    result_data = []
    summary = {
        CATEGORY_CAMERA: 0,
        CATEGORY_SCREENSHOT: 0,
        CATEGORY_DOWNLOADED: 0,
        CATEGORY_OTHER: 0,
        "總處理數": 0
    }

    for root, _, files in os.walk(source_folder):
        for file in files:
            if not file.lower().endswith(SUPPORTED_EXTS):
                continue
            full_path = os.path.join(root, file)
            try:
                with Image.open(full_path) as img:
                    width, height = img.size
                    file_name = os.path.splitext(file)[0]

                    if width < 200 or height < 200:
                        category = CATEGORY_OTHER
                    elif is_camera_photo(full_path):
                        category = CATEGORY_CAMERA
                    elif is_screenshot(file_name, width, height):
                        category = CATEGORY_SCREENSHOT
                    else:
                        category = CATEGORY_DOWNLOADED

                    result_data.append((category, width, height, file, full_path))
                    summary[category] += 1
                    summary["總處理數"] += 1

            except Exception as e:
                result_data.append((CATEGORY_OTHER, 0, 0, file, full_path, str(e)))

    return result_data, summary

def export_results(results, summary, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    txt_path = os.path.join(output_folder, "處理結果.txt")
    error_log_path = os.path.join(output_folder, "錯誤記錄.log")

    with open(txt_path, "w", encoding="utf-8") as f_txt, open(error_log_path, "w", encoding="utf-8") as f_err:
        for entry in results:
            if len(entry) == 5:
                category, width, height, file, path = entry
                f_txt.write(f"{category} | {width}x{height} | {file} | {path}\n")
            else:
                category, _, _, file, path, err = entry
                f_err.write(f"❌ {file} ({path}) - {err}\n")
        f_txt.write("\n===== 統計報告 =====\n")
        for key, val in summary.items():
            f_txt.write(f"{key}: {val}\n")

def move_or_copy_images(results, source_folder, do_move):
    output_base = os.path.join(source_folder, "output")
    output_dirs = {
        CATEGORY_CAMERA: os.path.join(output_base, CATEGORY_CAMERA),
        CATEGORY_SCREENSHOT: os.path.join(output_base, CATEGORY_SCREENSHOT),
        CATEGORY_DOWNLOADED: os.path.join(output_base, CATEGORY_DOWNLOADED),
        CATEGORY_OTHER: os.path.join(output_base, CATEGORY_OTHER),
    }

    for path in output_dirs.values():
        os.makedirs(path, exist_ok=True)

    for entry in tqdm(results, desc="🔄 移動/複製檔案中..."):
        if len(entry) == 5:
            category, _, _, _, full_path = entry
            safe_move_or_copy(full_path, output_dirs[category], do_move)

def main():
    root = Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="請選擇要處理的圖片資料夾")
    if not folder:
        print("❌ 未選擇資料夾。")
        return

    print("\n🔍 掃描與分類中...")
    results, summary = scan_images(folder)

    print("\n📊 分類統計結果：")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    export_results(results, summary, os.path.join(folder, "output"))

    while True:
        choice = input("\n要複製還是移動圖片？(copy/move/exit): ").strip().lower()
        if choice == "copy":
            move_or_copy_images(results, folder, do_move=False)
            print("✅ 檔案已複製完成。")
            break
        elif choice == "move":
            move_or_copy_images(results, folder, do_move=True)
            print("✅ 檔案已移動完成。")
            break
        elif choice == "exit":
            print("🚫 動作取消，未處理檔案。")
            break
        else:
            print("請輸入 'copy' 或 'move' 或 'exit'")

if __name__ == "__main__":
    main()
