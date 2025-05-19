import os
import shutil
from pathlib import Path
import cv2

class MediaOrganizer:
    def __init__(self, source_root):
        self.source = Path(source_root)
        self.dest = self.source.parent / "媒体资料库"
        self._create_structure()

        # 特殊人物映射表
        self.special_mappings = {
            # 亚洲区/台湾
            "雅美蝶": "人物收藏/台湾区/雅美蝶",
            "Clair": "人物收藏/台湾区/Clair",
            "嘟嘟": "人物收藏/台湾区/嘟嘟",
            "Cristine": "人物收藏/台湾区/Cristine",
            "＊Nang": "人物收藏/台湾区/Nang",
            "安佐江": "人物收藏/台湾区/安佐江",
            "捷運站美魔女": "人物收藏/台湾区/捷運站美魔女",
            "水波奶": "人物收藏/台湾区/水波奶",
            "小籠包": "人物收藏/台湾区/小籠包",
            "Somnus_Wu": "人物收藏/台湾区/Somnus_Wu",
            "Allen_Huang": "人物收藏/台湾区/Allen_Huang",

            # 菲律宾区/微信联系人
            "哈尼": "人物收藏/菲律宾区/微信联系人/哈尼",
            "akosichiiklet": "人物收藏/菲律宾区/微信联系人/akosichiiklet",
            "Bbychloe_888": "人物收藏/菲律宾区/微信联系人/Bbychloe_888",
            "yeyefei667788": "人物收藏/菲律宾区/微信联系人/yeyefei667788",
            "meimei_sb": "人物收藏/菲律宾区/微信联系人/meimei_sb",
            "PamAnderson": "人物收藏/菲律宾区/微信联系人/PamAnderson",
            "天秤座": "人物收藏/菲律宾区/微信联系人/天秤座",
            "狮子座": "人物收藏/菲律宾区/微信联系人/狮子座",

            # 菲律宾区/脸书联系人
            "Cy Cy": "人物收藏/菲律宾区/脸书联系人/Cy Cy",
            "Cutebabytey": "人物收藏/菲律宾区/脸书联系人/Cutebabytey",
            "Charmel Kim": "人物收藏/菲律宾区/脸书联系人/Charmel Kim",
            "Lovely Angela Ong": "人物收藏/菲律宾区/脸书联系人/Lovely Angela Ong",
            "Mitch Cer": "人物收藏/菲律宾区/脸书联系人/Mitch Cer",
            "Piyanut Lidala": "人物收藏/菲律宾区/脸书联系人/Piyanut Lidala",
            "Venus Aino": "人物收藏/菲律宾区/脸书联系人/Venus Aino",
            "SHAINE": "人物收藏/菲律宾区/脸书联系人/SHAINE",
            "PINAY SCANDALS": "人物收藏/菲律宾区/分級內容/PINAY_SCANDALS",
            "PINAY & KIDS": "人物收藏/菲律宾区/分級內容/PINAY_KIDS",

            # 特殊分类
            "NTR": "人物收藏/特殊类型/NTR",
            "好獵奇": "人物收藏/特殊类型/猎奇",
            "ED MOSAIC": "人物收藏/特殊类型/ED_MOSAIC",
            "iBra's store": "人物收藏/特殊类型/iBra_store"
        }

    def _create_structure(self):
        """创建完整的目录结构"""
        base_structure = [
            # 人物收藏
            "人物收藏/台湾区",
            "人物收藏/菲律宾区/微信联系人",
            "人物收藏/菲律宾区/脸书联系人",
            "人物收藏/特殊类型",

            # 媒体格式
            "媒体格式/图像/高画质",
            "媒体格式/图像/低光环境",
            "媒体格式/视频/分辨率/1080p",
            "媒体格式/视频/分辨率/720p",
            "媒体格式/视频/分辨率/SD"
        ]

        for folder in base_structure:
            (self.dest / folder).mkdir(parents=True, exist_ok=True)

    def organize_all(self):
        """执行完整整理流程"""
        print("="*50)
        print("开始整理媒体库...")

        print("\n[阶段1] 移动特殊人物目录...")
        self._move_special_folders()

        print("\n[阶段2] 处理菲律宾影片相关目录...")
        self._process_pinay_video_folders()

        print("\n[阶段3] 整理其他媒体文件...")
        self._process_media_files()

        print("\n[阶段4] 检查未处理文件...")
        self._check_remaining_files()

        print("\n" + "="*50)
        print("整理完成！结果保存在:", self.dest)
        print("="*50)

    def _move_special_folders(self):
        """移动特殊人物目录"""
        possible_sources = [
            self.source,
            self.source / "02_廢北" / "Main",
            self.source / "01_癡情" / "Others",
            self.source / "03_小菲" / "小菲網路相關" / "微信",
            self.source / "03_小菲" / "小菲網路相關" / "臉書"
        ]

        moved_count = 0
        for location in possible_sources:
            if not location.exists():
                continue

            print(f"\n检查位置: {location}")
            for item in location.iterdir():
                if item.is_dir() and item.name in self.special_mappings:
                    dest_path = self.dest / self.special_mappings[item.name]
                    print(f"移动: {item.name} -> {dest_path}")

                    try:
                        if dest_path.exists():
                            shutil.rmtree(dest_path)
                        shutil.move(str(item), str(dest_path))
                        moved_count += 1
                        print(f"  成功移动 {item.name}")
                    except Exception as e:
                        print(f"  移动失败: {e}")

        print(f"\n总共移动了 {moved_count} 个特殊人物目录")

    def _process_pinay_video_folders(self):
        """专门处理菲律宾影片相关目录结构"""
        pinay_source = self.source / "03_小菲" / "小菲影片相關"
        if not pinay_source.exists():
            print(f"未找到菲律宾影片目录: {pinay_source}")
            return

        # 分级映射
        level_mapping = {
            "PINAY SCANDALS": "人物收藏/菲律宾区/分級內容/PINAY_SCANDALS",
            "PINAY & KIDS": "人物收藏/菲律宾区/分級內容/PINAY_KIDS"
        }

        total_moved = 0

        # print("\n处理分级目录:")
        # for subdir in pinay_source.iterdir():
        #     if subdir.is_dir() and subdir.name in level_mapping:
        #         dest_path = self.dest / level_mapping[subdir.name]
        #         print(f"\n处理目录: {subdir.name} -> {dest_path}")
        #
        #         # 移动整个目录及其内容
        #         moved = self._move_entire_folder(subdir, dest_path)
        #         total_moved += moved

        # 处理其他未映射的子目录(默认放到L4普通目录)
        print("\n处理未分类目录:")
        for subdir in pinay_source.iterdir():
            if subdir.is_dir() and subdir.name not in level_mapping:
                dest_parent = self.dest / "人物收藏/菲律宾区/分級內容/"
                dest_path = dest_parent / subdir.name
                print(f"\n处理未分类目录: {subdir.name} -> {dest_path}")

                moved = self._move_entire_folder(subdir, dest_path)
                total_moved += moved

        print(f"\n总共移动了 {total_moved} 个菲律宾影片项目")

    def _move_entire_folder(self, src, dest):
        """移动整个文件夹及其内容"""
        if not src.exists():
            return 0

        # 确保目标目录存在
        dest.mkdir(parents=True, exist_ok=True)

        moved_count = 0

        # 先移动所有文件
        for item in src.glob('*'):
            if item.is_file():
                try:
                    dest_file = dest / item.name
                    if dest_file.exists():
                        # 处理文件名冲突
                        base, ext = os.path.splitext(item.name)
                        counter = 1
                        while dest_file.exists():
                            dest_file = dest / f"{base}_{counter}{ext}"
                            counter += 1

                    shutil.move(str(item), str(dest_file))
                    moved_count += 1
                    print(f"  已移动文件: {item.name} -> {dest_file.name}")
                except Exception as e:
                    print(f"  文件移动失败 {item.name}: {e}")

        # 然后处理子目录
        for subdir in src.glob('*/'):
            if subdir.is_dir():
                dest_subdir = dest / subdir.name
                print(f"  处理子目录: {subdir.name}")
                moved_count += self._move_entire_folder(subdir, dest_subdir)

        # 尝试删除空目录
        try:
            src.rmdir()
            print(f"已移除空目录: {src}")
        except:
            print(f"目录非空，保留: {src}")

        return moved_count

    def _process_media_files(self):
        """处理其他媒体文件"""
        media_count = 0
        for item in self.source.rglob('*'):
            if item.is_file() and not str(item).startswith(str(self.dest)):
                try:
                    if item.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                        self._process_image(item)
                        media_count += 1
                    elif item.suffix.lower() in ['.mp4', '.mov', '.avi']:
                        self._process_video(item)
                        media_count += 1
                    else:
                        self._move_file(item, self.dest / "系统元数据")
                        media_count += 1
                except Exception as e:
                    print(f"处理失败 {item}: {e}")

        print(f"\n总共处理了 {media_count} 个媒体文件")

    def _process_image(self, img_path):
        """处理图片文件"""
        try:
            img = cv2.imread(str(img_path))
            if img is not None:
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                brightness = hsv[...,2].mean()
                dest_folder = "高画质" if brightness > 100 else "低光环境"
                self._move_file(img_path, self.dest / "媒体格式" / "图像" / dest_folder)
        except Exception as e:
            print(f"图片处理失败 {img_path}: {e}")
            self._move_file(img_path, self.dest / "媒体格式" / "图像")

    def _process_video(self, video_path):
        """处理视频文件"""
        try:
            cap = cv2.VideoCapture(str(video_path))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            cap.release()

            res_folder = "1080p" if width >= 1920 else "720p" if width >= 1280 else "SD"
            self._move_file(video_path, self.dest / "媒体格式" / "视频" / "分辨率" / res_folder)
        except:
            print(f"视频解析失败 {video_path}")
            self._move_file(video_path, self.dest / "媒体格式" / "视频")

    def _move_file(self, src_path, dest_dir):
        """安全移动单个文件"""
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / src_path.name

        if dest_path.exists():
            base, ext = os.path.splitext(src_path.name)
            counter = 1
            while dest_path.exists():
                dest_path = dest_dir / f"{base}_{counter}{ext}"
                counter += 1

        try:
            shutil.move(str(src_path), str(dest_path))
            print(f"移动文件: {src_path.name} -> {dest_path.name}")
        except Exception as e:
            print(f"文件移动失败 {src_path.name}: {e}")

    def _check_remaining_files(self):
        """检查未处理文件"""
        remaining_files = []
        remaining_dirs = []

        for item in self.source.rglob('*'):
            if item.is_file() and not str(item).startswith(str(self.dest)):
                remaining_files.append(item)
            elif item.is_dir() and item != self.dest and not any(item.iterdir()):
                remaining_dirs.append(item)

        if remaining_files:
            print("\n以下文件未被处理:")
            for file in remaining_files[:10]:
                print(f"- {file}")
            if len(remaining_files) > 10:
                print(f"...(共 {len(remaining_files)} 个未处理文件)")

        if remaining_dirs:
            print("\n以下空目录未被移除:")
            for dir in remaining_dirs[:5]:
                print(f"- {dir}")
            if len(remaining_dirs) > 5:
                print(f"...(共 {len(remaining_dirs)} 个空目录)")

        if not remaining_files and not remaining_dirs:
            print("\n所有文件已处理完毕")
        else:
            print("\n请手动检查上述未处理项目")

if __name__ == "__main__":
    source_path = "/Users/oncechen/Documents/新花花世界"
    if not Path(source_path).exists():
        print(f"错误: 源路径不存在 {source_path}")
    else:
        print(f"开始整理媒体库: {source_path}")
        organizer = MediaOrganizer(source_path)
        organizer.organize_all()