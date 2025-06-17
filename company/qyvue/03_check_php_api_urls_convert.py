import requests
import json  # 添加这行导入
from urllib.parse import urlparse
from datetime import datetime
import time
import os

BASE_URL = "https://qyvue.itomtest.com"

def collect_api_response(url, method='GET', data=None, headers=None, source=None):
    """
    收集单个API接口的响应信息
    :param url: 接口URL
    :param method: 请求方法
    :param data: POST数据
    :param headers: 请求头
    :param source: 来源页面
    :return: 包含响应信息的字典
    """
    try:
        start_time = time.time()

        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, data=data, headers=headers)
        else:
            return {"error": f"Unsupported method: {method}", "url": url, "source": source}

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
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": source
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
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": source
        }


def save_to_txt(results, filename=os.path.join("output", 'merged_api_all.txt')):
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
            f.write(f"【接口 {i}】 => {result.get('status_code', 'N/A')} \n")
            f.write(f"URL: {result.get('url', 'N/A')}\n")
            f.write(f"来源页面: {result.get('source', 'unknown')}\n")

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
        method = api.get('method', 'POST')
        data = api.get('data')
        headers = api.get('headers')
        source = api.get("source", "unknown")

        result = collect_api_response(url, method, data, headers, source=source)
        all_results.append(result)

        if 'error' in result:
            print("失败")
        else:
            print(f"成功 (状态码: {result['status_code']})")

    return all_results


def load_api_list_from_file(filename=os.path.join("output", "merged_api_all.txt")):
    import re
    api_list = []

    if not os.path.exists(filename):
        print(f"❌ 檔案不存在：{filename}")
        return api_list

    with open(filename, "r", encoding="utf-8") as f:
        block = []
        for line in f:
            if line.strip() == "--------------------------------------------------":
                block_text = "\n".join(block)
                match_url = re.search(r"2\.API地址：([^\n]+)", block_text)
                match_page = re.search(r"1\.訪問頁面：([^\n]+)", block_text)
                match_param = re.search(r"4\.接口參數：([^\n]*)", block_text)

                if match_url:
                    raw_url = match_url.group(1).strip()
                    parsed = urlparse(raw_url)
                    url = BASE_URL + parsed.path
                    source = match_page.group(1).strip() if match_page else "unknown"
                    data = match_param.group(1).strip()

                    # 嘗試將 JSON 字串轉成 dict
                    if data and not data.startswith("（"):  # 過濾 Binary 類資料
                        try:
                            data_obj = json.loads(data)
                        except json.JSONDecodeError:
                            data_obj = data  # 非 JSON 格式原樣傳回
                    else:
                        data_obj = None

                    api_list.append({
                        "url": url,
                        "method": "POST",
                        "source": source,
                        "data": data_obj
                    })

                block = []  # 清空以準備下一區塊
            else:
                block.append(line.strip())

    return api_list

if __name__ == "__main__":
    print("开始收集API响应数据...\n")
    api_list = load_api_list_from_file()
    results = batch_collect_api_responses(api_list)

    # 保存到TXT文件
    txt_filename = os.path.join("output", "api_responses_report.txt")
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
