import requests
import json  # 添加这行导入
from urllib.parse import urlparse
from datetime import datetime
import time
import os

BASE_URL = "https://qyvue.itomtest.com"

def collect_api_response(url, method='GET', data=None, headers=None):
    """
    收集单个API接口的响应信息
    :param url: 接口URL
    :param method: 请求方法
    :param data: POST数据
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
            return {"error": f"Unsupported method: {method}", "url": url}

        parsed_url = urlparse(url)

        result = {
            "url": url,
            "method": method.upper(),
            "domain": parsed_url.netloc,
            "path": parsed_url.path,
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds(),
            "total_time": time.time() - start_time,
            "response_size": len(response.content),
            "response_content": response.text,
            "json_response": None,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            result["json_response"] = response.json()
        except ValueError:
            pass

        return result

    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "url": url,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


def save_to_txt(results, filename='api_responses.txt'):
    """
    将结果保存到TXT文件
    :param results: 收集的结果列表
    :param filename: 输出文件名
    """

    # 统计状态码
    status_counts = {}
    for result in results:
        if 'status_code' in result:
            status_code = result['status_code']
            status_counts[status_code] = status_counts.get(status_code, 0) + 1

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=== API响应数据收集报告 ===\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"共收集 {len(results)} 个接口\n\n")

        # 写入状态码统计信息
        f.write("\n【状态码统计】\n")
        for code, count in sorted(status_counts.items()):
            f.write(f"状态码 {code}: {count} 个接口\n")

        # 特别统计200和404的数量
        success_count = status_counts.get(200, 0)
        not_found_count = status_counts.get(404, 0)
        f.write(f"\n成功(200)接口: {success_count} 个\n")
        f.write(f"未找到(404)接口: {not_found_count} 个\n")
        f.write(f"其他状态码接口: {len(results) - success_count - not_found_count} 个\n")

        f.write("\n" + "=" * 50 + "\n\n")

        for i, result in enumerate(results, 1):
            f.write(f"【接口 {i}】 => {result['status_code']} \n")
            f.write(f"URL: {result.get('url', 'N/A')}\n")

            if 'error' in result:
                f.write(f"请求状态: 失败\n")
                f.write(f"错误信息: {result['error']}\n\n")
                continue

            # 写入响应内容
            f.write("\n【响应内容】\n")
            if result.get('json_response'):
                f.write(json.dumps(result['json_response'], indent=2, ensure_ascii=False))
            else:
                f.write(result.get('response_content', '无内容'))

            f.write("\n\n" + "=" * 50 + "\n\n")


def batch_collect_api_responses(api_list):
    """
    批量收集多个API接口的响应信息
    :param api_list: API接口配置列表
    :return: 所有API的响应结果
    """
    all_results = []

    for api in api_list:
        print(f"收集: {api.get('url')}...", end=' ')

        url = api.get('url')
        method = api.get('method', 'GET')
        data = api.get('data')
        headers = api.get('headers')

        result = collect_api_response(url, method, data, headers)
        all_results.append(result)

        if 'error' in result:
            print("失败")
        else:
            print(f"成功 (状态码: {result['status_code']})")

    return all_results


def load_api_list_from_file(filename=os.path.join("output", "php_post_urls_converted.txt")):
    api_list = []
    if not os.path.exists(filename):
        print(f"❌ 檔案不存在：{filename}")
        return api_list

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            path = line.strip()
            if path:
                api_list.append({
                    "url": f"{BASE_URL}{path}",
                    "method": "POST"
                })
    return api_list

if __name__ == "__main__":
    print("开始收集API响应数据...\n")
    api_list = load_api_list_from_file()
    results = batch_collect_api_responses(api_list)

    # 保存到TXT文件
    txt_filename = "api_responses_report.txt"
    save_to_txt(results, txt_filename)

    # 在控制台也显示统计信息
    status_counts = {}
    for result in results:
        if 'status_code' in result:
            status_code = result['status_code']
            status_counts[status_code] = status_counts.get(status_code, 0) + 1

    print("\n【状态码统计】")
    for code, count in sorted(status_counts.items()):
        print(f"状态码 {code}: {count} 个接口")

    success_count = status_counts.get(200, 0)
    not_found_count = status_counts.get(404, 0)
    print(f"\n成功(200)接口: {success_count} 个")
    print(f"未找到(404)接口: {not_found_count} 个")
    print(f"其他状态码接口: {len(results) - success_count - not_found_count} 个")

    print(f"\n收集完成！结果已保存到 {txt_filename}")
