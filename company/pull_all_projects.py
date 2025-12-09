import subprocess
import os

# === 项目配置：根据实际情况维护 ===
PROJECTS = {
    "rb88": {
        "path": "/Users/oncechen/IdeaProjects/rb88_web_vue/"
    },
    "jxf": {
        "path": "/Users/oncechen/IdeaProjects/jxf_web_static_vue_main/"
    },
    "ued": {
        "path": "/Users/oncechen/IdeaProjects/c_ued/WebRoot/"
    },
    "tq": {
        "path": "/Users/oncechen/IdeaProjects/c_sportone/web/WebRoot/"
    },
    "pt777": {
        "path": "/Users/oncechen/IdeaProjects/c_pt777/WebRoot/"
    },
    "qy": {
        "path": "/Users/oncechen/IdeaProjects/c_qy/web/WebRoot/"
    },
    "long8": {
        "path": "/Users/oncechen/IdeaProjects/c_long8/web/WebRoot/"
    },
    "uedpc": {
        "path": "/Users/oncechen/IdeaProjects/ued_web_vue/"
    },
    "uedh5": {
        "path": "/Users/oncechen/IdeaProjects/ued_web_static_vue/"
    },
    "lwpc": {
        "path": "/Users/oncechen/IdeaProjects/e68_web_vue/"
    },
    "lwh5": {
        "path": "/Users/oncechen/IdeaProjects/e68_web_static_vue/"
    },
    "feiyu": {
        "path": "/Users/oncechen/IdeaProjects/feiyu-site/"
    },
    "94Chat": {
        "path": "/Users/oncechen/IdeaProjects/site-dolphin/"
    },
    "weiquandanbao": {
        "path": "/Users/oncechen/IdeaProjects/site-weiquandanbao/"
    }
}


def pull_project(name, info):
    path = info["path"]
    print(f"\n🔄 正在处理项目：{name}")
    print(f"📁 路径：{path}")

    if not os.path.isdir(path):
        print("❌ 路径不存在，跳过")
        return

    try:
        result = subprocess.run(["git", "pull"], cwd=path, capture_output=True, text=True, check=True)
        print("✅ git pull 成功")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("❌ git pull 失败")
        print(e.stderr)


def main():
    print("🚀 开始批量 git pull 所有项目...\n")
    for name, info in PROJECTS.items():
        pull_project(name, info)
    print("\n✅ 所有项目已完成 pull")


if __name__ == "__main__":
    main()
