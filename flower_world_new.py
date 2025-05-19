import os
import shutil
from pathlib import Path
import cv2

class MediaOrganizer:
    def __init__(self, source_root):
        self.source = Path(source_root)
        self.dest = self.source.parent / "媒体资料库"
        self._create_structure()

        # 按照新结构定义的特殊人物映射表
        self.special_mappings = {
            # 亚洲区/台湾
            "雅美蝶": "人物收藏/亚洲区/台湾/雅美蝶",
            "Clair": "人物收藏/亚洲区/台湾/Clair",
            "嘟嘟": "人物收藏/亚洲区/台湾/嘟嘟",
            "Cristine": "人物收藏/亚洲区/台湾/Cristine",
            "＊Nang": "人物收藏/亚洲区/台湾/Nang",

            # 亚洲区/日本
            "安佐江": "人物收藏/亚洲区/日本/安佐江",

            # 亚洲区/其他
            "捷運站美魔女": "人物收藏/亚洲区/其他/捷運站美魔女",
            "水波奶": "人物收藏/亚洲区/其他/水波奶",
            "小籠包": "人物收藏/亚洲区/其他/小籠包",
            "Somnus_Wu": "人物收藏/亚洲区/其他/Somnus_Wu",
            "Allen_Huang": "人物收藏/亚洲区/其他/Allen_Huang",

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

            # 特殊分类
            "NTR": "人物收藏/特殊类型/NTR",
            "好獵奇": "人物收藏/特殊类型/猎奇",
            "ED MOSAIC": "人物收藏/特殊类型/ED_MOSAIC",
            "iBra's store": "人物收藏/特殊类型/iBra_store",
            "PINAY SCANDALS": "人物收藏/特殊类型/PINAY_SCANDALS",
            "PINAY & KIDS": "人物收藏/特殊类型/PINAY_KIDS"
        }

    def _create_structure(self):
        """创建新结构的目录"""
        base_structure = [
            # 人物收藏
            "人物收藏/亚洲区/台湾",
            "人物收藏/亚洲区/日本",
            "人物收藏/亚洲区/其他",
            "人物收藏/菲律宾区/微信联系人",
            "人物收藏/菲律宾区/脸书联系人",
            "人物收藏/特殊类型",

            # 媒体格式
            "媒体格式/图像/高画质",
            "媒体格式/图像/低光环境",
            "媒体格式/视频/分辨率/1080p",
            "媒体格式/视频/分辨率/720p",
            "媒体格式/视频/分辨率/SD",

            # 系统
            "系统元数据/文件哈希库",
            "系统元数据/缩略图缓存"
        ]

        for folder in base_structure:
            (self.dest / folder).mkdir(parents=True, exist_ok=True)

    def organize_all(self):
        """执行完整整理流程"""
        print("="*50)
        print("开始移动特殊人物完整目录...")
        self._move_entire_special_folders()

        print("\n" + "="*50)
        print("整理其他媒体文件...")
        self._process_media_files()

        print("\n" + "="*50)
        print("检查未处理文件...")
        self._check_remaining_files()

    def _move_entire_special_folders(self):
        """移动整个特殊人物目录到新位置"""
        # 检查所有可能的来源路径
        possible_source_locations = [
            self.source,  # 根目录
            self.source / "02_廢北" / "Main",
            self.source / "01_癡情" / "Others",
            self.source / "03_小菲" / "小菲網路相關" / "微信",
            self.source / "03_小菲" / "小菲網路相關" / "臉書",
            self.source / "03_小菲" / "小菲影片相關"
        ]

        moved_folders = set()

        for location in possible_source_locations:
            if not location.exists():
                continue

            print(f"\n检查位置: {location}")
            for item in location.iterdir():
                if item.is_dir() and item.name in self.special_mappings and item.name not in moved_folders:
                    dest_path = self.dest / self.special_mappings[item.name]

                    print(f"准备移动整个目录: {item} -> {dest_path}")

                    if item.exists():
                        # 确保目标目录不存在
                        if dest_path.exists():
                            print(f"目标目录已存在，先删除: {dest_path}")
                            shutil.rmtree(dest_path)

                        # 移动整个目录
                        try:
                            shutil.move(str(item), str(dest_path))
                            moved_folders.add(item.name)
                            print(f"成功移动: {item.name} => {dest_path}")
                        except Exception as e:
                            print(f"移动失败 {item} -> {dest_path}: {e}")
                    else:
                        print(f"来源目录不存在: {item}")

        # 处理菲律宾影片分级目录
        self._process_pinay_level_folders()

    def _process_pinay_level_folders(self):
        """处理菲律宾影片分级目录"""
        pinay_source = self.source / "03_小菲" / "小菲影片相關"
        if not pinay_source.exists():
            return

        print("\n处理菲律宾影片分级目录...")
        level_mapping = {
            "L1": "人物收藏/菲律宾区/L1-精品",
            "L2": "人物收藏/菲律宾区/L2-自拍",
            "L3": "人物收藏/菲律宾区/L3-特殊",
            "L4": "人物收藏/菲律宾区/L4-普通",
            "L5": "人物收藏/菲律宾区/L5-普通"
        }

        for item in pinay_source.iterdir():
            if item.is_dir() and item.name in level_mapping:
                dest_path = self.dest / level_mapping[item.name]
                print(f"移动影片分级目录: {item} -> {dest_path}")

                if dest_path.exists():
                    print(f"合并目录: {item} 到现有 {dest_path}")
                    self._merge_folders(item, dest_path)
                else:
                    shutil.move(str(item), str(dest_path))
                    print(f"成功移动: {item.name} => {dest_path}")

    def _merge_folders(self, src, dest):
        """合并两个目录的内容"""
        for item in src.glob('*'):
            try:
                dest_item = dest / item.name
                if dest_item.exists():
                    # 如果目标已存在，添加后缀
                    counter = 1
                    while dest_item.exists():
                        dest_item = dest / f"{item.stem}_{counter}{item.suffix}"
                        counter += 1
                shutil.move(str(item), str(dest_item))
            except Exception as e:
                print(f"合并失败 {item} -> {dest}: {e}")

        # 删除空目录
        try:
            src.rmdir()
            print(f"移除空目录: {src}")
        except:
            pass

    def _process_media_files(self):
        """处理剩余媒体文件"""
        media_count = 0
        for item in self.source.rglob('*'):
            # 跳过已处理目录和目标目录
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
                    print(f"处理 {item} 时出错: {e}")

        print(f"\n已处理 {media_count} 个媒体文件")

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
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()

            res_folder = "1080p" if width >= 1920 else "720p" if width >= 1280 else "SD"
            self._move_file(video_path, self.dest / "媒体格式" / "视频" / "分辨率" / res_folder)
        except:
            print(f"视频解析失败 {video_path}, 移动到默认目录")
            self._move_file(video_path, self.dest / "媒体格式" / "视频")

    def _move_file(self, src_path, dest_dir):
        """安全移动文件并处理名称冲突"""
        dest_dir.mkdir(parents=True, exist_ok=True)

        new_path = dest_dir / src_path.name

        # 处理文件名冲突
        counter = 1
        while new_path.exists():
            new_path = dest_dir / f"{src_path.stem}_{counter}{src_path.suffix}"
            counter += 1

        try:
            shutil.move(str(src_path), str(new_path))
            print(f"移动文件: {src_path.name} -> {new_path}")
        except Exception as e:
            print(f"移动失败 {src_path} -> {new_path}: {e}")

    def _check_remaining_files(self):
        """检查未处理的文件和空目录"""
        print("\n正在检查剩余文件...")
        remaining_files = []
        remaining_dirs = []

        for item in self.source.rglob('*'):
            if item.is_file() and not str(item).startswith(str(self.dest)):
                remaining_files.append(item)
            elif item.is_dir() and item != self.dest and not any(item.iterdir()):
                remaining_dirs.append(item)

        if remaining_files:
            print("\n以下文件未被处理:")
            for file in remaining_files[:10]:  # 只显示前10个
                print(f"- {file}")
            if len(remaining_files) > 10:
                print(f"... 以及另外 {len(remaining_files)-10} 个文件")

        if remaining_dirs:
            print("\n以下空目录未被移除:")
            for dir in remaining_dirs[:5]:  # 只显示前5个
                print(f"- {dir}")
            if len(remaining_dirs) > 5:
                print(f"... 以及另外 {len(remaining_dirs)-5} 个空目录")

        if not remaining_files and not remaining_dirs:
            print("\n所有文件已成功处理！")
        else:
            print("\n请手动检查上述未处理项目")

if __name__ == "__main__":
    source_path = "/Users/oncechen/Documents/新花花世界"

    if not Path(source_path).exists():
        print(f"错误: 源路径不存在 {source_path}")
    else:
        print(f"开始整理: {source_path}")
        organizer = MediaOrganizer(source_path)
        organizer.organize_all()
        print("\n" + "="*50)
        print("整理完成！结果保存在: ", organizer.dest)
        print("="*50)