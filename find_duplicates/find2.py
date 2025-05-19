import os
import shutil
from PIL import Image
from datetime import datetime
import imagehash

def calculate_image_hash(file_path):
    """计算图片的感知哈希值"""
    try:
        with Image.open(file_path) as img:
            return imagehash.phash(img)
    except Exception as e:
        print(f"无法处理图片 {file_path}: {str(e)}")
        return None

def find_duplicates(source_dir, similarity_threshold=5):
    """
    查找重复图片
    返回格式：{哈希值: [文件路径列表]}
    """
    hashes = {}
    for root, _, files in os.walk(source_dir):
        for filename in files:
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.heic')):
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
    return {k: v for k, v in hashes.items() if len(v) > 1}

def organize_with_deduplication(source_dir, target_dir):
    """整理照片并处理重复"""
    # 先整理照片
    organize_photos_by_date(source_dir, target_dir)

    # 在整理后的目录中查找重复
    print("\n开始重复图片检测...")
    duplicates = find_duplicates(target_dir)

    # 处理重复文件
    dup_dir = os.path.join(target_dir, "_duplicates")
    os.makedirs(dup_dir, exist_ok=True)

    for hash_value, files in duplicates.items():
        print(f"\n发现重复组（哈希相似度 {hash_value}）:")
        # 保留第一个文件，移动其他重复项
        for file_path in files[1:]:
            dest_path = os.path.join(dup_dir, os.path.basename(file_path))
            if not os.path.exists(dest_path):
                shutil.move(file_path, dest_path)
                print(f"移动重复文件: {file_path} -> {dest_path}")
            else:
                # 处理文件名冲突
                base, ext = os.path.splitext(os.path.basename(file_path))
                new_name = f"{base}_dup{ext}"
                shutil.move(file_path, os.path.join(dup_dir, new_name))
                print(f"重命名并移动: {file_path} -> {new_name}")

# 在原整理函数中添加哈希计算支持
def organize_photos_by_date(source_dir, target_dir):
    """（原整理函数，增加哈希计算存储）"""
    # ... 保持原有代码不变 ...

if __name__ == "__main__":
    organize_with_deduplication(
        source_dir="/path/to/your/photos",
        target_dir="/path/to/organized/photos"
    )