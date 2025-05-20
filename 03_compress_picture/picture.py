import os
import tinify
from datetime import datetime
import time
import requests
import json

def compress_images_recursive(input_folder, output_folder, api_key):
    """
    递归查找并压缩指定文件夹及其子文件夹中的所有图片

    参数:
        input_folder (str): 包含原始图片的根文件夹路径
        output_folder (str): 压缩后图片的输出根文件夹路径
        api_key (str): TinyPNG API 密钥
    """
    # 初始化 TinyPNG
    tinify.key = api_key

    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 支持的图片格式
    supported_formats = ('.png', '.jpg', '.jpeg', '.webp')

    # 记录处理结果
    processed_files = []
    skipped_files = []
    error_files = []

    # 進度記錄文件
    progress_file = os.path.join(output_folder, "progress.json")

    # 嘗試加載之前的進度
    processed_paths = set()
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
                processed_paths = set(progress_data.get('processed', []))
                print(f"發現之前的進度，已處理 {len(processed_paths)} 個文件，將從中斷處繼續...")
        except:
            pass

    print(f"开始处理文件夹: {input_folder}")
    print(f"输出到: {output_folder}")

    def save_progress():
        """保存當前進度到文件"""
        progress_data = {
            'processed': list(processed_paths),
            'input_folder': input_folder,
            'output_folder': output_folder
        }
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f)

    def check_internet_connection():
        """檢查網路連接"""
        try:
            requests.get('https://api.tinify.com', timeout=5)
            return True
        except:
            return False

    def wait_for_internet():
        """等待網路恢復"""
        print("網路連接中斷，等待恢復...", end=' ', flush=True)
        while not check_internet_connection():
            time.sleep(5)
            print(".", end='', flush=True)
        print("\n網路已恢復，繼續處理...")

    # 获取今天的日期（不包含时间部分）
    today = datetime.now().date()

    # 递归遍历文件夹
    for root, dirs, files in os.walk(input_folder):
        # 计算相对路径
        relative_path = os.path.relpath(root, input_folder)
        # 创建对应的输出子文件夹
        output_subfolder = os.path.join(output_folder, relative_path)
        if not os.path.exists(output_subfolder):
            os.makedirs(output_subfolder)

        for filename in files:
            file_relative_path = os.path.join(relative_path, filename)

            # 如果已經處理過，則跳過
            if file_relative_path in processed_paths:
                continue

            # 检查是否是支持的图片文件
            if not filename.lower().endswith(supported_formats):
                skipped_files.append(file_relative_path)
                continue

            try:
                # 构造完整路径
                file_path = os.path.join(root, filename)

                # 获取文件最后修改时间并转换为日期
                file_mtime = os.path.getmtime(file_path)
                file_date = datetime.fromtimestamp(file_mtime).date()

                # 如果文件是今天修改的，则跳过
                if file_date == today:
                    print(f"跳过今天修改的文件: {file_relative_path}")
                    skipped_files.append(file_relative_path)
                    continue

                output_path = os.path.join(output_subfolder, filename)

                print(f"正在压缩: {file_relative_path}...", end=' ', flush=True)

                # 記錄開始時間
                start_time = datetime.now()

                # 使用 TinyPNG 压缩图片（帶重試機制）
                max_retries = 3
                retry_count = 0
                success = False

                while retry_count < max_retries and not success:
                    try:
                        # 檢查網路連接
                        if not check_internet_connection():
                            wait_for_internet()

                        source = tinify.from_file(file_path)
                        source.to_file(output_path)
                        success = True

                    except tinify.AccountError as e:
                        # 處理API密钥錯誤或API限制
                        raise
                    except Exception as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f"\n重試 {retry_count}/{max_retries}...", end=' ', flush=True)
                            time.sleep(5 * retry_count)  # 指數退避
                        else:
                            raise

                if not success:
                    raise Exception("達到最大重試次數")

                # 計算耗時
                time_taken = (datetime.now() - start_time).total_seconds()

                # 獲取原始和壓縮後文件大小
                original_size = os.path.getsize(file_path) / 1024  # KB
                compressed_size = os.path.getsize(output_path) / 1024  # KB
                reduction = (original_size - compressed_size) / original_size * 100

                print(f"完成! 原始大小: {original_size:.2f}KB → 压缩后: {compressed_size:.2f}KB (减少 {reduction:.1f}%), 耗时: {time_taken:.2f}s")

                processed_files.append({
                    'filename': file_relative_path,
                    'original_size': original_size,
                    'compressed_size': compressed_size,
                    'reduction': reduction,
                    'time_taken': time_taken
                })

                # 記錄已處理的文件
                processed_paths.add(file_relative_path)
                save_progress()

            except tinify.AccountError as e:
                # 處理API密钥錯誤或API限制
                print(f"\n錯誤: {e.message} (API密钥可能无效或超出限额)")
                error_files.append(file_relative_path)
                break
            except Exception as e:
                print(f"\n處理 {file_relative_path} 時出错: {str(e)}")
                error_files.append(file_relative_path)
                continue

    # 處理完成後刪除進度文件
    if os.path.exists(progress_file):
        os.remove(progress_file)

    # 打印摘要
    print("\n处理完成!")
    print(f"成功处理文件数: {len(processed_files)}")
    print(f"跳过文件数: {len(skipped_files)}")
    print(f"错误文件数: {len(error_files)}")

    if processed_files:
        print("\n压缩详情:")
        total_original = sum(f['original_size'] for f in processed_files)
        total_compressed = sum(f['compressed_size'] for f in processed_files)
        total_reduction = (total_original - total_compressed) / total_original * 100

        print(f"总原始大小: {total_original:.2f}KB")
        print(f"总压缩后大小: {total_compressed:.2f}KB")
        print(f"总减少: {total_reduction:.1f}%")

        # 找出压缩效果最好和最差的文件
        best = max(processed_files, key=lambda x: x['reduction'])
        worst = min(processed_files, key=lambda x: x['reduction'])

        print(f"\n最佳压缩: {best['filename']} (减少 {best['reduction']:.1f}%)")
        print(f"最差压缩: {worst['filename']} (减少 {worst['reduction']:.1f}%)")

if __name__ == "__main__":
    # 配置参数
    INPUT_FOLDER = input("请输入要压缩的图片文件夹路径: ").strip()
    OUTPUT_FOLDER = "/Users/oncechen/Downloads/output"  # 压缩后图片输出文件夹
    API_KEY = "BHz2xSbcClQD4RTTMvS2vPt1NKQ4yVhn"  # 替换为你的 TinyPNG API 密钥

    # 执行压缩
    compress_images_recursive(INPUT_FOLDER, OUTPUT_FOLDER, API_KEY)