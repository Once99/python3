import subprocess
import os

def start_vlc_with_local_stream_output(input_url, output_filename):
    """
    启动 VLC 播放器，播放网络视频资源，并将流输出保存到本地下载目录。

    :param input_url: 输入的网络视频资源 URL。
    :param output_filename: 输出的文件名（保存到 ~/Downloads 目录）。
    """
    # VLC 在 macOS 上的默认路径
    vlc_path = "/Applications/VLC.app/Contents/MacOS/VLC"

    # 获取下载目录路径
    download_dir = os.path.expanduser("~/Downloads")
    output_path = os.path.join(download_dir, output_filename)

    # 流输出选项：将流保存为本地文件
    sout_options = f"#standard{{access=file,mux=ts,dst='{output_path}'}}"

    try:
        # 构建 VLC 命令行参数
        command = [
            vlc_path,
            input_url,
            "--sout",
            sout_options,
        ]

        # 启动 VLC
        subprocess.Popen(command)
        print(f"正在使用 VLC 播放并保存流输出: {input_url} -> {output_path}")
    except FileNotFoundError:
        print("未找到 VLC 播放器，请确保 VLC 已安装并路径正确。")
    except Exception as e:
        print(f"启动 VLC 时出错: {e}")

if __name__ == "__main__":
    # 提示用户输入网络视频资源 URL
    input_url = input("请输入网络视频资源的 URL（例如 http://example.com/stream.mp4）：").strip()

    # 提示用户输入输出文件名
    output_filename = input("请输入保存的文件名（例如 output.ts）：").strip()

    # 启动 VLC 并保存流输出到本地下载目录
    start_vlc_with_local_stream_output(input_url, output_filename)