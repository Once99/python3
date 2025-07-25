import os
import subprocess
from datetime import datetime
import webbrowser

# === 配置 ===
SRC = "/Users/oncechen/IdeaProjects/jxf_web_static_vue_main"
DEST = "/Users/oncechen/IdeaProjects/rb88_web_vue"
TAG = "v" + datetime.now().strftime("%Y.%m.%d.%H%M")
ALLOWED_EXT = {'.vue', '.js', '.ts', '.html', '.css', '.scss'}

REPLACE_MAP = {
    "吉祥坊": "走地皇",
    "吉祥": "RB88走地皇",
    "jxfvue.nntitestserver": "rb88vue.nntitestserver",
    "jxfvue.itomtest.com": "rb88vue.itomtest.com",
    "jxvue": "rb88vue"
}

def run(cmd, cwd=None, **kwargs):
    print(f"🔧 執行指令: {' '.join(cmd)}")
    result = subprocess.run(cmd, text=True, cwd=cwd, **kwargs)
    if result.returncode != 0:
        print(f"❌ 指令失敗：{' '.join(cmd)}")
        exit(1)
    return result

def replace_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    original_content = content
    for old, new in REPLACE_MAP.items():
        content = content.replace(old, new)
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 替换完成: {file_path}")

def walk_and_replace(target_dir):
    for root, _, files in os.walk(target_dir):
        for filename in files:
            filepath = os.path.join(root, filename)
            if os.path.splitext(filename)[1] in ALLOWED_EXT:
                try:
                    replace_in_file(filepath)
                except Exception as e:
                    print(f"⚠️ 错误：{filepath} - {e}")

# Step 3.1: 替换 Captcha ID
def ensure_captcha_id(dest_dir):
    target_file = os.path.join(dest_dir, "src", "composables", "useNeCaptcha.ts")
    if not os.path.exists(target_file):
        print(f"⚠️ Captcha 檔案不存在: {target_file}")
        return

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    old_id = "873182f57b6241eb987f3f579f9d6fcb"
    new_id = "d7679d69f38c4a56baffd5ce627b03dc"

    if old_id in content:
        content = content.replace(old_id, new_id)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("🔄 Captcha ID 已更新")
    elif new_id in content:
        print("✅ Captcha ID 已正确设置")
    else:
        print("⚠️ 未找到 Captcha ID，未做替换")


# Step 3.2: 检查 Vite Proxy 配置
def ensure_proxy_target(dest_dir):
    vite_file = os.path.join(dest_dir, "vite.config.ts")
    if not os.path.exists(vite_file):
        print(f"⚠️ vite.config.ts 不存在: {vite_file}")
        return

    with open(vite_file, "r", encoding="utf-8") as f:
        content = f.read()

    expected_target = "https://rb88vue.itomtest.com"
    if expected_target in content:
        print("✅ Proxy target 设置正确")
    else:
        print("⚠️ Proxy target 不是预期值，建议检查 vite.config.ts 中的 /api 配置！")

# === 主流程 ===

# 檢查目錄
if not os.path.isdir(SRC):
    print(f"❌ 源目录不存在：{SRC}")
    exit(1)
if not os.path.isdir(os.path.join(DEST, ".git")):
    print(f"❌ 目标目录不是一个 Git 仓库：{DEST}")
    exit(1)

# Step 1: 拉取最新代码
print("🔄 拉取源项目最新代码...")
run(["git", "pull"], cwd=SRC)
print("🔄 拉取目标项目最新代码...")
run(["git", "pull"], cwd=DEST)

# Step 2: 同步文件
print("📦 同步文件...")
run([
    "rsync", "-av", "--delete",
    "--exclude=.git",
    "--exclude=.gitlab-ci.yml",
    f"{SRC}/", f"{DEST}/"
])

# Step 3: 替换目标项目内容
print("🔧 替换目标项目内容...")
walk_and_replace(DEST)

# Step 3.1: 检查 Captcha ID
ensure_captcha_id(DEST)

# Step 3.2: 检查 Proxy 配置
ensure_proxy_target(DEST)

# Step 4: 提交、推送变更
os.chdir(DEST)
status = run(["git", "status", "--porcelain"], capture_output=True)
has_changes = status.stdout.strip() != ""

if has_changes:
    print("📍 檢測到變更，準備提交...")
    run(["git", "add", "."])
    run(["git", "commit", "-m", "同步 JXF 项目内容并替换为 RB88"])
    run(["git", "pull", "--rebase"])
    run(["git", "push"])
else:
    print("✅ 無需提交，工作目录干净")

# Step 5: 打标签
print(f"🏷️ 打标签: {TAG}")
run(["git", "tag", TAG])
run(["git", "push", "origin", TAG])

# Step 6: 打开 GitLab 页面
print("🌐 打开 GitLab Pipeline 页面")
webbrowser.open("https://git.easydevops.net/frontend/rb88_web_vue/-/pipelines")

print(f"\n🎉 全部流程完成，版本标签 {TAG} 已推送")
print(f"\n记得换接口API地址!")
print(f"\n记得换滑动验证码CaptchID地址!")
