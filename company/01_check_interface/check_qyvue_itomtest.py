import requests
import json  # 添加这行导入
from urllib.parse import urlparse
from datetime import datetime
import time


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


# 示例API列表配置
api_list = [
    {
        "url": "https://qyvue.itomtest.com/api/getBanner",
        "method": "POST",
    },
    {
        "url": "https://qyvue.itomtest.com/api/getAllNews",
        "method": "POST",
        "data": {
            "key1": "value1",
            "key2": "value2"
        }
    },
    {
        "url": "https://qyvue.itomtest.com/api/newMessageCenter",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/querySystemConfig",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getPcRedRainIsOpenConfig",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getSmsCodeSwitch",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/mobilefindCouponNum",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/queryPoints",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/fetchPopData",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getCsUrl",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/queryAgentDownLoadAddress",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/querySystemConfig",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getNewUserRedCoupon",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/transferInforRedCoupon",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/mobileSendSmsCodeForUser",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/sendSmsCodeForUserByCashout",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getUsdtRedCoupon",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/enterGameHall",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/appPayOnline",
        "method": "POST"
    },

    {
        "url": "https://qyvue.itomtest.com/api/newLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/logout",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/newMobileLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getLoginWrongTime",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/newRegistration",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/validateSmsCodebyPwd",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getbackAcc",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/unlockAccountByInfo",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/change_pws",
        "method": "POST"
    }

    ,
    {
        "url": "https://qyvue.itomtest.com/api/getMessageByUser",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getGuestbookUnReadNum",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/readMsg",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/mobileBatchReadTopic",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/deleteMsg",
        "method": "POST"
    },

    {
        "url": "https://qyvue.itomtest.com/api/getGameMoney",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/queryList",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/queryChessList",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/queryGameCollect",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/selectLastPlayGame",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getTokenPc",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameNewIMLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameNewSBLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameFBLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameOBLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameNEWAGLiveLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gamePMLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/bbinLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameFBLIVELogin",
        "method": "POST"
    },

    {
        "url": "https://qyvue.itomtest.com/api/gameNewPgLoginHtml",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameDTLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameDBSLOTLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gamePPLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameNewCq9Login",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameNEWMGLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gamePtBDH5Login",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameLoginPtSky",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameNEWAGLogin",
        "method": "POST"
    },

    {
        "url": "https://qyvue.itomtest.com/api/gameIMDJLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameDBDJLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameTFLogin",
        "method": "POST"
    },

    {
        "url": "https://qyvue.itomtest.com/api/gameKSLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameDBCPLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameNKYQPLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameHLQPLogin",
        "method": "POST"
    },

    {
        "url": "https://qyvue.itomtest.com/api/gameIGLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameDBCPLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameSYLogin",
        "method": "POST"
    },

    {
        "url": "https://qyvue.itomtest.com/api/gameKSLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameNEWAGLiveLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gameLoginPtSky",
        "method": "POST"
    },

    {
        "url": "https://qyvue.itomtest.com/api/gamePtBDAPPLogin",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/gamePGAPPLogin",
        "method": "POST"
    },

    {
        "url": "https://qyvue.itomtest.com/api/queryLatestPreferentialList",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/queryLatestPreferential",
        "method": "POST"
    },

    {
        "url": "https://qyvue.itomtest.com/api/getAllPointsPresents",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/pointsRecord",
        "method": "POST"
    },

    {
        "url": "https://qyvue.itomtest.com/api/getRecordType",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/optLosePromo",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/doXima",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/handleAddress",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getBetListRecordV2",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getRecords",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/checkUpgrade",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/queryPTLosePromo",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/queryPTLosePromoReccords",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/mobileCouponPageList",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getAutoXimaSlotObject",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/mobileNewEditUserInfoV2",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/validateEmailisActivation",
        "method": "POST"
    },

    {
        "url": "https://qyvue.itomtest.com/api/showList",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/showListV4",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getChannel",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/submitThirdV4",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/switchChannel",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/bankList",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getNewDeposit",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/invalidDeposit",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/queryDepositBank",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getCurrencyPayUrl",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getCurrencyExchangeRateV2",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getC2CDeposit",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getEbc2cDeposit",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/cancelEbc2c",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/uploadProofEbc2c",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getYbC2cmethods",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getPayWayTutorial",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/confirmPayWayTutorial",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/checkBrushOrderLimit",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/checkUserWhiteList",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getBindedBankinfos",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getPayWayStatus",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/createPostscriptDepositOrder",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getPayAdvert",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/ebPay",
        "method": "POST"
    },



    {
        "url": "https://qyvue.itomtest.com/api/getBindedBankinfos",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getUserAllWthdrawAmount",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/withdrawfee",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/withdrawNew",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/currencyWithdraw",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/currencyWithdrawV2",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getUserCreditCurrencyBussiness",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getWithdSmsCodeSwitch",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getEbC2CProposal",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/confirmEbc2c",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getC2CProposal",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/bindUserBank",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/unBindBankinfo",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/getBankInfo",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/checkWithdrawNew",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/change_pwsPayAjax",
        "method": "POST"
    },
    {
        "url": "https://qyvue.itomtest.com/api/unDigitalWallet",
        "method": "POST"
    },


    {
        "url": "https://qyvue.itomtest.com/api/gameTransfer",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/getTotalGameBalance",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/updateSwitchStatus",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/getGameBalance",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/updateGameMoney",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/getAllGameBalance",
        "method": "POST"
    },



    {
        "url": "https://qyvue.itomtest.com/api/newRegisterAgent",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/newMobileAgentLogin",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/getAgentsOfflineNew",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/createSubAgentNew",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/searchAgentCreditLog",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/queryPtCommissions",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/queryAgentFinancialReport",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/queryAgentWithdrawReccords",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/queryAgentSubUserInfoNew",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/getUsersRecordsByLoginname",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/getAgentComparisonInfo",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/searchPtCommissionsReport",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/searchAgentMultiReport",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/getAgentLevelNew",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/searchPtCommissionsMultiDetail",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/getAgentAddressById",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/addAgentAddress",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/addAgentAddressCollection",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/queryAgentAddressList",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/getAgentAddressConfig",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/updateAgentFyAccount",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/getAgentPromotionalMaterial",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/getAgentContactUsConfig",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/agentModifyPassword",
        "method": "POST"
    },{
        "url": "https://qyvue.itomtest.com/api/modifyAgentPayPwd",
        "method": "POST"
    }
]

if __name__ == "__main__":
    print("开始收集API响应数据...\n")
    results = batch_collect_api_responses(api_list)

    # 保存到TXT文件
    txt_filename = "qyvue_itomtest_api_responses_report.txt"
    save_to_txt(results, txt_filename)

    # 在控制台也显示统计信息
    status_counts = {}
    for result in results:
        if 'status_code' in result:
            status_code = result['status_code']
            status_counts[status_code] = status_counts.get(status_code, 0) + 1

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
