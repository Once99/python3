import os
import shutil
from datetime import datetime

def flatten_and_move(source_dir, target_dir="new"):
    """
    将来源目录中的所有文件(包括子目录中的文件)全部移动到目标目录，不保持原有结构
    :param source_dir: 来源目录路径
    :param target_dir: 目标目录名称(默认为"new")
    """
    # 创建目标目录
    target_path = os.path.join(os.path.dirname(source_dir), target_dir)
    os.makedirs(target_path, exist_ok=True)

    print(f"开始移动: {source_dir} 所有内容 -> {target_path}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    total_files = 0
    duplicate_count = 0

    # 遍历源目录
    for root, _, files in os.walk(source_dir):
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(target_path, file)

            # 处理文件名冲突
            counter = 1
            while os.path.exists(dest_file):
                base, ext = os.path.splitext(file)
                dest_file = os.path.join(target_path, f"{base}_{counter}{ext}")
                counter += 1
                duplicate_count += 1

            try:
                shutil.move(src_file, dest_file)
                total_files += 1
                print(f"移动文件: {src_file} -> {dest_file}")
            except Exception as e:
                print(f"移动失败 {src_file}: {str(e)}")

    print("\n移动完成!")
    print(f"总移动文件数: {total_files}")
    print(f"重命名文件数(因冲突): {duplicate_count}")
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    # 使用示例
    source_directory = "/Users/oncechen/Downloads/final"

    if not os.path.isdir(source_directory):
        print("错误: 指定的路径不是一个有效目录!")
    else:
        target_name = input("请输入目标目录名称(默认为'new'): ").strip() or "new"
        flatten_and_move(source_directory, target_name)

        # 如果是Windows系统，保持窗口打开
        if os.name == 'nt':
            input("\n按Enter键退出...")