import os
import shutil
import cv2
import numpy as np
from PIL import Image
import imagehash
import magic
from collections import defaultdict

class FileManager:
    def __init__(self):
        self.stats = defaultdict(int)
        self.seen_hashes = set()
        self.mime = magic.Magic(mime=True)

    def get_file_type(self, filepath):
        """判断文件是图片还是视频"""
        file_type = self.mime.from_file(filepath)
        if file_type.startswith("image/"):
            return "image"
        elif file_type.startswith("video/"):
            return "video"
        return None

    def get_image_hash(self, img_path):
        """计算图片哈希值（去重用）"""
        try:
            with Image.open(img_path) as img:
                return str(imagehash.average_hash(img))
        except:
            return None

    def get_video_hash(self, video_path):
        """计算影片第一帧的哈希值（简易去重）"""
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            return str(imagehash.average_hash(pil_img))
        return None

    def classify_by_resolution(self, filepath, file_type):
        """按分辨率分类（4K/1080p/720p/SD）"""
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

    def detect_skin_tone(self, img_path):
        """使用 OpenCV 检测肤色（Light/Medium/Dark）"""
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

    def move_files(self, source_dir, target_dir, mode='classify', flatten=False, remove_empty=False):
        """
        移动文件的主要函数

        参数:
            source_dir: 源目录路径
            target_dir: 目标目录路径
            mode: 'classify'分类模式或'move'简单移动模式
            flatten: 是否扁平化移动（不保持目录结构）
            remove_empty: 是否删除源目录中的空子目录
        """
        os.makedirs(target_dir, exist_ok=True)

        for root, dirs, files in os.walk(source_dir):
            for file in files:
                filepath = os.path.join(root, file)

                if mode == 'classify':
                    self._process_classify_mode(filepath, target_dir)
                else:
                    self._process_move_mode(filepath, target_dir, flatten)

        if remove_empty:
            self._remove_empty_dirs(source_dir)

        self._print_stats()

    def _process_classify_mode(self, filepath, target_dir):
        """处理分类模式下的文件移动"""
        file_type = self.get_file_type(filepath)
        if not file_type:
            return

        # 计算哈希值去重
        file_hash = (
            self.get_image_hash(filepath)
            if file_type == "image"
            else self.get_video_hash(filepath)
        )
        if file_hash in self.seen_hashes:
            print(f"重复文件: {os.path.basename(filepath)}")
            self.stats["duplicates"] += 1
            return
        self.seen_hashes.add(file_hash)

        # 分类分辨率
        resolution = self.classify_by_resolution(filepath, file_type)

        # 如果是图片，检测肤色
        skin_tone = "Unknown"
        if file_type == "image":
            skin_tone = self.detect_skin_tone(filepath)

        # 目标文件夹结构: Output/[Images|Videos]/[Resolution]/[SkinTone]/filename
        dest_dir = os.path.join(
            target_dir,
            "Images" if file_type == "image" else "Videos",
            resolution,
            skin_tone if file_type == "image" else "NoSkinTone"
        )
        os.makedirs(dest_dir, exist_ok=True)

        # 移动文件
        shutil.move(filepath, os.path.join(dest_dir, os.path.basename(filepath)))

        # 更新统计
        self.stats[f"{file_type}_{resolution}"] += 1
        if file_type == "image":
            self.stats[f"skin_{skin_tone}"] += 1

    def _process_move_mode(self, filepath, target_dir, flatten):
        """处理简单移动模式下的文件移动"""
        if flatten:
            # 扁平化移动模式
            target_path = os.path.join(target_dir, os.path.basename(filepath))

            # 处理文件名冲突
            base, ext = os.path.splitext(os.path.basename(filepath))
            counter = 1
            while os.path.exists(target_path):
                # 检查是否是同一个文件（避免移动到自己）
                if os.path.samefile(filepath, target_path):
                    self.stats["skipped"] += 1
                    print(f"[跳过] 源文件与目标文件相同: {os.path.basename(filepath)}")
                    return

                self.stats["conflicts"] += 1
                new_filename = f"{base}_{counter}{ext}"
                target_path = os.path.join(target_dir, new_filename)
                counter += 1

            try:
                shutil.move(filepath, target_path)
                self.stats["moved"] += 1
                print(f"[{self.stats['moved']}] 已移动: {os.path.relpath(filepath, os.path.dirname(filepath))} → {os.path.basename(target_path)}")
            except Exception as e:
                print(f"错误: 无法移动 {filepath} - {str(e)}")
        else:
            # 保持目录结构模式
            relative_path = os.path.relpath(os.path.dirname(filepath), os.path.dirname(target_dir))
            target_subdir = os.path.join(target_dir, relative_path)
            os.makedirs(target_subdir, exist_ok=True)
            target_path = os.path.join(target_subdir, os.path.basename(filepath))

            try:
                shutil.move(filepath, target_path)
                self.stats["moved"] += 1
                print(f"[{self.stats['moved']}] 已移动: {os.path.relpath(filepath, os.path.dirname(target_dir))} → {os.path.relpath(target_path, target_dir)}")
            except Exception as e:
                print(f"错误: 无法移动 {filepath} - {str(e)}")

    def _remove_empty_dirs(self, path):
        """递归删除空目录"""
        removed_count = 0
        for root, dirs, files in os.walk(path, topdown=False):
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                try:
                    os.rmdir(dir_path)
                    print(f"已删除空目录: {dir_path}")
                    removed_count += 1
                except OSError:
                    pass
        print(f"\n共删除 {removed_count} 个空目录")
        self.stats["removed_dirs"] = removed_count

    def _print_stats(self):
        """打印统计信息"""
        print("\n===== 操作统计 =====")
        if "duplicates" in self.stats:
            print(f"总处理文件数: {len(self.seen_hashes)}")
            print(f"重复文件: {self.stats.get('duplicates', 0)}")
            print("\n分辨率分类:")
            for key, count in self.stats.items():
                if key.startswith("image_") or key.startswith("video_"):
                    print(f"{key}: {count}")
            print("\n肤色分类 (仅图片):")
            for key, count in self.stats.items():
                if key.startswith("skin_"):
                    print(f"{key}: {count}")
        else:
            print(f"移动文件总数: {self.stats.get('moved', 0)}")
            print(f"处理冲突数: {self.stats.get('conflicts', 0)}")
            print(f"跳过文件数: {self.stats.get('skipped', 0)}")
            print(f"删除空目录数: {self.stats.get('removed_dirs', 0)}")

def main():
    print("=== 高级文件管理工具 ===")
    print("1. 智能分类模式（自动按类型/分辨率/肤色分类）")
    print("2. 简单移动模式（可选择是否保持目录结构）")

    choice = input("请选择模式 (1/2): ")

    manager = FileManager()

    if choice == '1':
        print("\n=== 智能分类模式 ===")
        source_dir = "/Users/oncechen/Downloads/new"
        target_dir = "/Users/oncechen/Downloads/output"

        if not os.path.isdir(source_dir):
            print(f"错误: 源目录 '{source_dir}' 不存在")
            return

        manager.move_files(
            source_dir=source_dir,
            target_dir=target_dir,
            mode='classify'
        )
    elif choice == '2':
        print("\n=== 简单移动模式 ===")
        source_dir = input("请输入源目录路径: ").strip()
        target_dir = input("请输入目标目录路径: ").strip()
        flatten = input("是否扁平化移动（不保持目录结构）? (y/n): ").lower() == 'y'
        remove_empty = input("移动完成后是否删除空目录? (y/n): ").lower() == 'y'

        if not os.path.isdir(source_dir):
            print(f"错误: 源目录 '{source_dir}' 不存在")
            return

        manager.move_files(
            source_dir=source_dir,
            target_dir=target_dir,
            mode='move',
            flatten=flatten,
            remove_empty=remove_empty
        )
    else:
        print("无效选择")

if __name__ == "__main__":
    main()