import requests
import json
from urllib.parse import urlparse
from datetime import datetime
import time

def collect_api_response(url, method='GET', data=None, headers=None):
    """
    收集单个API接口的响应信息
    :param url: 接口URL
    :param method: 请求方法，默认GET
    :param data: POST请求的数据
    :param headers: 请求头
    :return: 包含响应信息的字典
    """
    try:
        start_time = time.time()

        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, data=data, headers=headers)
        else:
            return {"error": f"不支持的请求方法: {method}", "url": url}

        # 解析URL获取域名信息
        parsed_url = urlparse(url)

        # 收集响应信息
        result = {
            "url": url,
            "method": method.upper(),
            "domain": parsed_url.netloc,
            "path": parsed_url.path,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "response_time": response.elapsed.total_seconds(),
            "total_time": time.time() - start_time,
            "response_size": len(response.content),
            "response_content": response.text,
            "json_response": None,
            "timestamp": datetime.now().isoformat()
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
            "url": url,
            "timestamp": datetime.now().isoformat()
        }

def batch_collect_api_responses(api_list, output_file='api_responses.json'):
    """
    批量收集多个API接口的响应信息
    :param api_list: API接口配置列表
    :param output_file: 输出文件名
    :return: 所有API的响应结果
    """
    all_results = []

    for api in api_list:
        print(f"\n正在收集: {api.get('url')}")

        # 获取配置参数
        url = api.get('url')
        method = api.get('method', 'GET')
        data = api.get('data')
        headers = api.get('headers')

        # 收集响应数据
        result = collect_api_response(url, method, data, headers)
        all_results.append(result)

        # 打印简要结果
        if 'error' in result:
            print(f"  × 错误: {result['error']}")
        else:
            print(f"  √ 成功 - 状态码: {result['status_code']}, 响应时间: {result['response_time']:.3f}s, 响应内容: {result['response_content']:}")

    # 保存结果到JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n所有API响应数据已保存到: {output_file}")
    return all_results

# 示例API列表配置
api_list = [
    {
        "url": "https://qyvue.nntitestserver.com/api/getPcRedRainIsOpenConfig",
        "method": "POST",
    },
    {
        "url": "https://qyvue.nntitestserver.com/api/getSmsCodeSwitch",
        "method": "POST",
        "data": {
            "key1": "value1",
            "key2": "value2"
        }
    },
    {
        "url": "https://qyvue.nntitestserver.com/api/mobilefindCouponNum",
        "method": "POST"
    }
    # 可以继续添加更多API配置
]

# 执行批量收集
if __name__ == "__main__":
    results = batch_collect_api_responses(api_list)

    # 打印汇总信息
    print("\n=== 汇总结果 ===")
    for idx, result in enumerate(results, 1):
        status = "失败" if 'error' in result else "成功"
        print(f"{idx}. {result['url']} - {status} - 状态码: {result.get('status_code', 'N/A')}")