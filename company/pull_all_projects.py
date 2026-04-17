import subprocess
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# === 项目配置：根据实际情况维护 ===
PROJECTS = {

    "tyadmin": {"path": "/Users/oncechen/IdeaProjects/ty_admin/"},
    "ezpay": {"path": "/Users/oncechen/IdeaProjects/ezpay-site/"},

    "qypc": {"path": "/Users/oncechen/IdeaProjects/qy_web_vue/"},
    "qyh5": {"path": "/Users/oncechen/IdeaProjects/qy_web_static_vue/"},
    "qy": {"path": "/Users/oncechen/IdeaProjects/c_qy/web/WebRoot/"},

    "rb88_main": {"path": "/Users/oncechen/IdeaProjects/rb88_web_vue_main/"},
    "jxf_main": {"path": "/Users/oncechen/IdeaProjects/jxf_web_static_vue_main/"},
    "uedpc": {"path": "/Users/oncechen/IdeaProjects/ued_web_vue/"},
    "uedh5": {"path": "/Users/oncechen/IdeaProjects/ued_web_static_vue/"},
    "ued": {"path": "/Users/oncechen/IdeaProjects/c_ued/WebRoot/"},
    "tq": {"path": "/Users/oncechen/IdeaProjects/c_sportone/web/WebRoot/"},

    "pt777": {"path": "/Users/oncechen/IdeaProjects/c_pt777/WebRoot/"},
    "long8": {"path": "/Users/oncechen/IdeaProjects/c_long8/web/WebRoot/"},
    "lwpc": {"path": "/Users/oncechen/IdeaProjects/e68_web_vue/"},
    "lwh5": {"path": "/Users/oncechen/IdeaProjects/e68_web_static_vue/"},

    "feiyu": {"path": "/Users/oncechen/IdeaProjects/feiyu-site/"},
    "94Chat": {"path": "/Users/oncechen/IdeaProjects/site-dolphin/"},
    "weiquandanbao": {"path": "/Users/oncechen/IdeaProjects/site-weiquandanbao/"},
    "haitun": {"path": "/Users/oncechen/IdeaProjects/site-haitun-web/"},
    "dolphin_im": {"path": "/Users/oncechen/IdeaProjects/dolphin_im_pc/"}
}

# 最大并发数量：可以根据网络情况调，比如 4、6、8
MAX_WORKERS = 6

def pull_project(name: str, info: dict) -> tuple[str, bool, str]:
    path = info["path"]

    if not os.path.isdir(path):
        return name, False, f"❌ 路径不存在：{path}"

    # 这里可以换成你喜欢的 pull 策略，比如 --ff-only 避免产生 merge
    cmd = ["git", "pull", "--ff-only"]

    try:
        result = subprocess.run(
            cmd,
            cwd=path,
            capture_output=True,
            text=True,
            check=False    # 不抛异常，自己判断 returncode
        )

        if result.returncode == 0:
            msg = result.stdout.strip() or "up to date"
            return name, True, f"✅ 成功：{msg}"
        else:
            return name, False, f"❌ 失败（code={result.returncode}）：\n{result.stderr}"
    except Exception as e:
        return name, False, f"❌ 运行异常：{e!r}"


def main():
    print("🚀 开始并行 git pull 所有项目...\n")

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_name = {
            executor.submit(pull_project, name, info): name
            for name, info in PROJECTS.items()
        }

        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                proj_name, ok, msg = future.result()
                prefix = "✅" if ok else "⚠️"
                print(f"\n[{prefix}] 项目：{proj_name}")
                print(msg)
                results.append((proj_name, ok))
            except Exception as e:
                print(f"\n❌ 项目 {name} 发生未捕获异常：{e!r}")
                results.append((name, False))

    # 汇总结果
    success = [n for n, ok in results if ok]
    failed = [n for n, ok in results if not ok]

    print("\n========== 总结 ==========")
    print(f"✅ 成功：{len(success)} 个 -> {', '.join(success) if success else '无'}")
    print(f"❌ 失败：{len(failed)} 个 -> {', '.join(failed) if failed else '无'}")


if __name__ == "__main__":
    main()