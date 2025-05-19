import os
import shutil
import hashlib
from datetime import datetime
from collections import defaultdict
from PIL import Image
import imagehash

# 支持的媒体文件扩展名
SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.heic',
                        '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv')

def hash_file(filepath, block_size=65536):
    """计算文件的精确哈希值(SHA256)"""
    print(f"🔍 正在计算文件哈希: {filepath}")
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(block_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"❌ 无法读取 {filepath}: {e}")
        return None

def calculate_image_hash(file_path):
    """计算图片的感知哈希值(phash)"""
    try:
        with Image.open(file_path) as img:
            return imagehash.phash(img)
    except Exception as e:
        print(f"❌ 无法处理图片 {file_path}: {str(e)}")
        return None

def find_duplicate_files(root_dir):
    """查找完全相同的文件(精确哈希)"""
    hash_dict = defaultdict(list)
    total = 0
    for foldername, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(SUPPORTED_EXTENSIONS):
                total += 1
                print(f"🔍 已扫描 {total} 个媒体文件...", end='\r')
                full_path = os.path.join(foldername, filename)
                file_hash = hash_file(full_path)
                if file_hash:
                    hash_dict[file_hash].append(full_path)
    print("\n✅ 扫描完成!")
    return {h: paths for h, paths in hash_dict.items() if len(paths) > 1}

def find_similar_images(root_dir, similarity_threshold=5):
    """查找相似图片(感知哈希)"""
    hashes = {}
    total = 0
    for root, _, files in os.walk(root_dir):
        for filename in files:
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.heic')):
                total += 1
                print(f"🔍 已扫描 {total} 张图片...", end='\r')
                file_path = os.path.join(root, filename)
                img_hash = calculate_image_hash(file_path)
                if img_hash:
                    # 查找相似哈希值
                    found = False
                    for existing_hash in hashes.keys():
                        if img_hash - existing_hash <= similarity_threshold:
                            hashes[existing_hash].append(file_path)
                            found = True
                            break
                    if not found:
                        hashes[img_hash] = [file_path]
    print("\n✅ 扫描完成!")
    return {k: v for k, v in hashes.items() if len(v) > 1}

def get_file_date(file_path):
    """获取文件创建日期"""
    try:
        timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp)
    except:
        return datetime.now()

def organize_media_by_month(source_dir, target_dir):
    """按月份整理媒体文件"""
    print("\n📂 开始按月份整理媒体文件...")

    # 创建目标目录
    os.makedirs(target_dir, exist_ok=True)

    for foldername, _, filenames in os.walk(source_dir):
        for filename in filenames:
            if filename.lower().endswith(SUPPORTED_EXTENSIONS):
                file_path = os.path.join(foldername, filename)
                file_date = get_file_date(file_path)

                # 创建目标文件夹结构: 年-月
                month_dir = os.path.join(target_dir, f"{file_date.year}-{file_date.month:02d}")
                os.makedirs(month_dir, exist_ok=True)

                # 移动文件
                dest_path = os.path.join(month_dir, filename)
                if not os.path.exists(dest_path):
                    shutil.move(file_path, dest_path)
                    print(f"📄 整理文件: {filename} -> {month_dir}")
                else:
                    # 处理文件名冲突
                    base, ext = os.path.splitext(filename)
                    new_name = f"{base}_{file_date.hour}{file_date.minute}{ext}"
                    new_path = os.path.join(month_dir, new_name)
                    shutil.move(file_path, new_path)
                    print(f"🔄 重命名文件: {filename} -> {new_name}")

def handle_duplicates(target_dir, duplicates, method='move'):
    """处理重复文件"""
    dup_dir = os.path.join(target_dir, "_duplicates")
    os.makedirs(dup_dir, exist_ok=True)

    for i, (hash_value, files) in enumerate(duplicates.items(), 1):
        print(f"\n🔁 重复组 #{i} (哈希: {hash_value}):")
        # 保留第一个文件
        print(f"✅ 保留: {files[0]}")

        # 处理其他重复文件
        for file_path in files[1:]:
            if method == 'move':
                dest_path = os.path.join(dup_dir, os.path.basename(file_path))
                if not os.path.exists(dest_path):
                    shutil.move(file_path, dest_path)
                    print(f"♻️ 移动重复文件: {file_path} -> {dest_path}")
                else:
                    base, ext = os.path.splitext(os.path.basename(file_path))
                    new_name = f"{base}_dup{ext}"
                    shutil.move(file_path, os.path.join(dup_dir, new_name))
                    print(f"🔄 重命名并移动: {file_path} -> {new_name}")
            elif method == 'delete':
                os.remove(file_path)
                print(f"🗑️ 删除重复文件: {file_path}")

def main():
    # 配置路径
    source_dir = "/Users/oncechen/Downloads/new"
    target_dir = "/Users/oncechen/Downloads/output"

    # 1. 先按月份整理媒体文件
    organize_media_by_month(source_dir, target_dir)

    # 2. 查找完全相同的文件
    print("\n🔍 开始查找完全相同的文件...")
    exact_duplicates = find_duplicate_files(target_dir)

    # 3. 查找相似的图片
    print("\n🔍 开始查找相似的图片...")
    similar_images = find_similar_images(target_dir)

    # 4. 处理重复文件
    if exact_duplicates:
        print("\n⚠️ 发现完全相同的文件:")
        handle_duplicates(target_dir, exact_duplicates, method='move')

    if similar_images:
        print("\n⚠️ 发现相似的图片:")
        handle_duplicates(target_dir, similar_images, method='move')

    if not exact_duplicates and not similar_images:
        print("\n✅ 没有发现重复或相似的文件!")
    else:
        print("\n🎉 重复文件处理完成!")

if __name__ == "__main__":
    main()