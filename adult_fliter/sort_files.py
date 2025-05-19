import os
import shutil
import cv2
import numpy as np
from PIL import Image
import imagehash
import magic
from collections import defaultdict

# 設定來源資料夾和輸出目錄
SOURCE_DIR = "/Users/oncechen/Library/CloudStorage/GoogleDrive-howard123702002@gmail.com/我的雲端硬碟/new"  # 替換成你的圖片/影片資料夾
OUTPUT_DIR = "/Users/oncechen/Downloads/output"          # 整理後的輸出目錄

# 確保輸出目錄存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 初始化統計和去重
stats = defaultdict(int)
seen_hashes = set()

def get_file_type(filepath):
    """判斷檔案是圖片還是影片"""
    mime = magic.Magic(mime=True)
    file_type = mime.from_file(filepath)
    if file_type.startswith("image/"):
        return "image"
    elif file_type.startswith("video/"):
        return "video"
    return None

def get_image_hash(img_path):
    """計算圖片哈希值（去重用）"""
    try:
        with Image.open(img_path) as img:
            return str(imagehash.average_hash(img))
    except:
        return None

def get_video_hash(video_path):
    """計算影片第一幀的哈希值（簡易去重）"""
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    if ret:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(frame_rgb)
        return str(imagehash.average_hash(pil_img))
    return None

def classify_by_resolution(filepath, file_type):
    """按解析度分類（4K/1080p/720p/SD）"""
    if file_type == "image":
        try:
            with Image.open(filepath) as img:
                width, height = img.size
        except:
            return "Unknown"
    elif file_type == "video":
        cap = cv2.VideoCapture(filepath)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
    else:
        return "Unknown"

    if width >= 3840 or height >= 2160:
        return "4K"
    elif width >= 1920 or height >= 1080:
        return "1080p"
    elif width >= 1280 or height >= 720:
        return "720p"
    else:
        return "SD"

def detect_skin_tone(img_path):
    """使用 OpenCV 檢測膚色（Light/Medium/Dark）"""
    try:
        img = cv2.imread(img_path)
        if img is None:
            return "Unknown"

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_skin = np.array([0, 48, 80], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)

        skin_pixels = cv2.countNonZero(skin_mask)
        total_pixels = img.shape[0] * img.shape[1]
        skin_ratio = (skin_pixels / total_pixels) * 100

        if skin_ratio < 5:
            return "Unknown"
        elif skin_ratio < 30:
            return "Light"
        elif skin_ratio < 60:
            return "Medium"
        else:
            return "Dark"
    except:
        return "Unknown"

def main():
    for filename in os.listdir(SOURCE_DIR):
        filepath = os.path.join(SOURCE_DIR, filename)
        if not os.path.isfile(filepath):
            continue

        file_type = get_file_type(filepath)
        if not file_type:
            continue  # 跳過非圖片/影片檔案

        # 計算哈希值去重
        file_hash = (
            get_image_hash(filepath)
            if file_type == "image"
            else get_video_hash(filepath)
        )
        if file_hash in seen_hashes:
            print(f"重複檔案: {filename}")
            stats["duplicates"] += 1
            continue
        seen_hashes.add(file_hash)

        # 分類解析度
        resolution = classify_by_resolution(filepath, file_type)

        # 如果是圖片，檢測膚色
        skin_tone = "Unknown"
        if file_type == "image":
            skin_tone = detect_skin_tone(filepath)

        # 目標資料夾結構: Output/[Images|Videos]/[Resolution]/[SkinTone]/filename
        dest_dir = os.path.join(
            OUTPUT_DIR,
            "Images" if file_type == "image" else "Videos",
            resolution,
            skin_tone if file_type == "image" else "NoSkinTone"
        )
        os.makedirs(dest_dir, exist_ok=True)

        # 移動檔案
        shutil.move(filepath, os.path.join(dest_dir, filename))

        # 更新統計
        stats[f"{file_type}_{resolution}"] += 1
        if file_type == "image":
            stats[f"skin_{skin_tone}"] += 1

    # 輸出統計
    print("\n===== 分類完成 =====")
    print(f"總檔案數: {len(seen_hashes)}")
    print(f"重複檔案: {stats.get('duplicates', 0)}")
    print("\n解析度分類:")
    for key, count in stats.items():
        if key.startswith("image_") or key.startswith("video_"):
            print(f"{key}: {count}")
    print("\n膚色分類 (僅圖片):")
    for key, count in stats.items():
        if key.startswith("skin_"):
            print(f"{key}: {count}")

if __name__ == "__main__":
    main()