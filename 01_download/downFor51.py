import requests
from bs4 import BeautifulSoup
import json
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


def fetch_website_content(url):
    """
    获取网站内容。
    :param url: 目标网站的URL
    :return: 网页内容（HTML文本）
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"无法访问网站: {e}")
        return None

def extract_dplayer_video_urls(html):
    """
    从HTML内容中提取dplayer的video数组中的url字段。
    :param html: 网页的HTML内容
    :return: 包含url字段的列表
    """
    soup = BeautifulSoup(html, 'html.parser')

    # 查找所有包含dplayer参数的div标签
    dplayer_divs = soup.find_all('div', class_='dplayer')

    # 提取dplayer参数中的video数组，并进一步提取url字段
    video_urls = []
    for div in dplayer_divs:
        # 假设参数存储在data-config属性中（JSON格式）
        if 'data-config' in div.attrs:
            try:
                config = json.loads(div['data-config'])
                if 'video' in config and 'url' in config['video']:
                    video_urls.append(config['video']['url'])
            except json.JSONDecodeError:
                print(f"解析JSON失败，跳过当前div: {div}")

    return video_urls

def get_webpage_title(url):
    try:
        # 发送HTTP请求获取网页内容
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功

        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # 获取网页标题
        title = soup.title.string.split("-")[1].strip()
        return title
    except requests.exceptions.RequestException as e:
        return f"Error fetching the webpage: {e}"
    except AttributeError:
        return "No title found on the webpage."

def main():
    # 输入目标网站的URL
    website_url = input("请输入目标网站的URL: ")

    # 获取网站内容
    html_content = fetch_website_content(website_url)
    if not html_content:
        return

    # 提取video数组中的url字段
    video_urls = extract_dplayer_video_urls(html_content)

    if video_urls:
        print("找到的video数组中的url字段:")
        for i, url in enumerate(video_urls, 1):
            print(f"url {i}: {url}")
            # 提示用户输入输出文件名
            output_filename = get_webpage_title(website_url).strip()
            output_filename = f"{output_filename}-{i}.ts"
            # 启动 VLC 并保存流输出到本地下载目录
            start_vlc_with_local_stream_output(f"{url}", output_filename)
    else:
        print("未找到video数组中的url字段")


    # 提示用户输入输出文件名
    # output_filename = input("请输入保存的文件名（例如 output.ts）：").strip()
    # output_filename = get_webpage_title(website_url).strip()

    # 启动 VLC 并保存流输出到本地下载目录
    # start_vlc_with_local_stream_output(video_urls, output_filename)

if __name__ == "__main__":
    main()


