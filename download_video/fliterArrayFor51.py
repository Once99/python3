import requests
from bs4 import BeautifulSoup
import json

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
    else:
        print("未找到video数组中的url字段")

if __name__ == "__main__":
    main()