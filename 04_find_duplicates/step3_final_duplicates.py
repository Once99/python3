import os
import shutil
import hashlib
from datetime import datetime

def get_file_hash(filepath):
    """计算文件的MD5哈希值"""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def find_and_move_duplicates(source_dir, output_dir, compare_mtime=True):
    """
    查找并移动重复文件（保留修改日期较新的文件）
    :param source_dir: 要搜索的目录
    :param output_dir: 存放重复文件的目录
    :param compare_mtime: 是否比较修改时间（True=保留新的，False=保留旧的）
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    print(f"开始搜索重复文件: {source_dir}")
    print(f"重复文件将移动到: {output_dir}")
    print(f"比较策略: {'保留较新文件' if compare_mtime else '保留较旧文件'}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    file_dict = {}  # 存储文件哈希值和信息
    duplicates = []  # 存储重复文件
    total_files = 0

    # 遍历目录并计算文件哈希
    for root, _, files in os.walk(source_dir):
        for file in files:
            filepath = os.path.join(root, file)
            total_files += 1

            try:
                # 获取文件信息
                file_size = os.path.getsize(filepath)
                file_mtime = os.path.getmtime(filepath)
                file_hash = get_file_hash(filepath)

                # 检查是否已存在相同哈希的文件
                if file_hash in file_dict:
                    existing_file = file_dict[file_hash]

                    # 比较修改时间
                    if compare_mtime:
                        # 保留较新的文件
                        if file_mtime > existing_file['mtime']:
                            duplicates.append(existing_file['path'])
                            file_dict[file_hash] = {
                                'path': filepath,
                                'mtime': file_mtime,
                                'size': file_size
                            }
                        else:
                            duplicates.append(filepath)
                    else:
                        # 保留较旧的文件
                        if file_mtime < existing_file['mtime']:
                            duplicates.append(existing_file['path'])
                            file_dict[file_hash] = {
                                'path': filepath,
                                'mtime': file_mtime,
                                'size': file_size
                            }
                        else:
                            duplicates.append(filepath)
                else:
                    file_dict[file_hash] = {
                        'path': filepath,
                        'mtime': file_mtime,
                        'size': file_size
                    }

                if total_files % 100 == 0:
                    print(f"已处理 {total_files} 个文件...", end='\r')
            except Exception as e:
                print(f"处理文件 {filepath} 时出错: {str(e)}")

    # 移动重复文件
    moved_count = 0
    for dup_file in duplicates:
        try:
            filename = os.path.basename(dup_file)
            dest_path = os.path.join(output_dir, filename)

            # 处理文件名冲突
            counter = 1
            while os.path.exists(dest_path):
                base, ext = os.path.splitext(filename)
                dest_path = os.path.join(output_dir, f"{base}_{counter}{ext}")
                counter += 1

            shutil.move(dup_file, dest_path)
            moved_count += 1
            print(f"移动重复文件: {dup_file} -> {dest_path}")
        except Exception as e:
            print(f"移动文件 {dup_file} 失败: {str(e)}")

    # 打印统计信息
    print("\n==== 操作完成 ====")
    print(f"扫描文件总数: {total_files}")
    print(f"发现重复文件数: {len(duplicates)}")
    print(f"成功移动文件数: {moved_count}")
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    print("=== 重复文件清理工具 ===")
    source = input("请输入要搜索的目录路径: ").strip()
    output = "/Users/oncechen/Downloads/duplicates"

    strategy = input("保留策略 (1=保留较新的, 2=保留较旧的, 默认为1): ").strip()
    compare_mtime = True if strategy != "2" else False

    if not os.path.isdir(source):
        print("错误: 指定的源目录不存在!")
    else:
        find_and_move_duplicates(source, output, compare_mtime)

        # 如果是Windows系统，保持窗口打开
        if os.name == 'nt':
            input("\n按Enter键退出...")