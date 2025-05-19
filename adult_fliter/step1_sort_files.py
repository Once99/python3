import os
import shutil
import cv2
import numpy as np
import magic
from collections import defaultdict

class FileOrganizer:
    def __init__(self):
        self.stats = defaultdict(int)
        try:
            self.mime = magic.Magic(mime=True)
        except:
            print("警告：未找到 libmagic，将使用文件扩展名判断类型")
            self.mime = None

    def get_file_type(self, filepath):
        """判断文件类型（图片/视频）"""
        if self.mime:
            try:
                file_type = self.mime.from_file(filepath)
                if file_type.startswith("image/"):
                    return "image"
                elif file_type.startswith("video/"):
                    return "video"
            except:
                pass

        ext = os.path.splitext(filepath)[1].lower()
        if ext in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'):
            return "image"
        elif ext in ('.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv'):
            return "video"
        return None

    def classify_resolution(self, filepath):
        """视频分辨率分类"""
        cap = cv2.VideoCapture(filepath)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        if width >= 3840 or height >= 2160:
            return "4K"
        elif width >= 1920 or height >= 1080:
            return "1080p"
        elif width >= 1280 or height >= 720:
            return "720p"
        return "SD"

    def classify_skin_tone(self, img_path):
        """简化肤色分类（仅 Light/Dark）"""
        try:
            img = cv2.imread(img_path)
            if img is None:
                return "Unknown"

            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            lower_skin = np.array([0, 48, 80], dtype=np.uint8)
            upper_skin = np.array([20, 255, 255], dtype=np.uint8)
            skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)

            skin_ratio = cv2.countNonZero(skin_mask) / (img.shape[0] * img.shape[1])
            return "Dark" if skin_ratio > 0.3 else "Light"
        except Exception as e:
            print(f"肤色检测失败 {img_path}: {str(e)}")
            return "Unknown"

    def process_file(self, filepath, output_dir):
        """处理单个文件"""
        file_type = self.get_file_type(filepath)
        if not file_type:
            return False

        if file_type == "image":
            category = self.classify_skin_tone(filepath)
            dest_dir = os.path.join(output_dir, "Images", category)
        else:
            category = self.classify_resolution(filepath)
            dest_dir = os.path.join(output_dir, "Videos", category)

        os.makedirs(dest_dir, exist_ok=True)

        filename = os.path.basename(filepath)
        base, ext = os.path.splitext(filename)
        dest_path = os.path.join(dest_dir, filename)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(dest_dir, f"{base}_{counter}{ext}")
            counter += 1

        shutil.move(filepath, dest_path)
        self.stats[f"{file_type}_{category}"] += 1
        return True

    def move_subdirectories(self, source_dir, output_dir):
        """移动子目录到 output/Main 目录下"""
        others_dir = os.path.join(output_dir, "Main")
        os.makedirs(others_dir, exist_ok=True)

        for item in os.listdir(source_dir):
            item_path = os.path.join(source_dir, item)
            if os.path.isdir(item_path):
                dest_path = os.path.join(others_dir, item)
                counter = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(others_dir, f"{item}_{counter}")
                    counter += 1
                shutil.move(item_path, dest_path)
                print(f"移动子目录: {item} -> {dest_path}")

    def organize_files(self, source_dir, output_dir):
        """主组织函数"""
        print("开始整理文件...")
        total_files = 0

        os.makedirs(output_dir, exist_ok=True)

        # 先处理文件
        for filename in os.listdir(source_dir):
            filepath = os.path.join(source_dir, filename)
            if os.path.isfile(filepath):
                if self.process_file(filepath, output_dir):
                    total_files += 1

        # 再移动子目录
        self.move_subdirectories(source_dir, output_dir)

        # 打印统计结果
        print("\n==== 整理完成 ====")
        print(f"处理文件总数: {total_files}")

        print("\n图片分类统计:")
        for k, v in sorted(self.stats.items()):
            if k.startswith("image_"):
                print(f"{k.replace('image_', ''):<6}: {v}")

        print("\n视频分类统计:")
        for k, v in sorted(self.stats.items()):
            if k.startswith("video_"):
                print(f"{k.replace('video_', ''):<6}: {v}")

if __name__ == "__main__":
    SOURCE_DIR = "/Users/oncechen/Downloads/new/"
    OUTPUT_DIR = "/Users/oncechen/Downloads/output/"

    print("=== 文件整理工具 ===")
    print(f"源目录: {SOURCE_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")

    organizer = FileOrganizer()
    organizer.organize_files(SOURCE_DIR, OUTPUT_DIR)

    if os.name == 'nt':
        input("\n按Enter键退出...")