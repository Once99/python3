import requests
from bs4 import BeautifulSoup

def get_webpage_title(url):
    try:
        # 发送HTTP请求获取网页内容
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功

        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # 获取网页标题
        title = soup.title.string
        return title
    except requests.exceptions.RequestException as e:
        return f"Error fetching the webpage: {e}"
    except AttributeError:
        return "No title found on the webpage."

if __name__ == "__main__":
    # 输入目标网址
    url = input("请输入目标网址: ")
    title = get_webpage_title(url)
    print(f"网页标题: {title}")