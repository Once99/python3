import requests
from urllib.parse import urlparse

def collect_api_response(url):
    try:
        # 发送GET请求
        response = requests.post(url)

        # 解析URL获取域名信息
        parsed_url = urlparse(url)

        # 收集响应信息
        result = {
            "url": url,
            "domain": parsed_url.netloc,
            "path": parsed_url.path,
            "status_code": response.status_code,

            "response_content": response.text,
            "json_response": None
        }

        # 尝试解析JSON响应
        try:
            result["json_response"] = response.json()
        except ValueError:
            pass

        return result

    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "url": url
        }

# 目标API URL
api_url = "https://qyvue.nntitestserver.com/api/getSmsCodeSwitch"

# 收集响应数据
api_data = collect_api_response(api_url)

# 打印结果
print(f"请求URL: {api_data['url']}")
print(f"域名: {api_data['domain']}")
print(f"路径: {api_data['path']}")
print(f"HTTP状态码: {api_data['status_code']}")

print("\n响应内容:")
print(api_data['response_content'])

if api_data['json_response']:
    print("\nJSON格式响应:")
    print(api_data['json_response'])