import os
import subprocess
from datetime import datetime

SRC = "/Users/oncechen/IdeaProjects/jxf_web_static_vue_main"
DEST = "/Users/oncechen/IdeaProjects/rb88_web_vue"
TAG = "v" + datetime.now().strftime("%Y.%m.%d.%H%M")

def run(cmd, cwd=None, **kwargs):
  print(f"🔧 執行指令: {' '.join(cmd)}")
  result = subprocess.run(cmd, text=True, cwd=cwd, **kwargs)
  if result.returncode != 0:
    print(f"❌ 指令失敗：{' '.join(cmd)}")
    exit(1)
  return result

# 檢查目錄
if not os.path.isdir(SRC):
  print(f"❌ 源目录不存在：{SRC}")
  exit(1)
if not os.path.isdir(os.path.join(DEST, ".git")):
  print(f"❌ 目标目录不是一个 Git 仓库：{DEST}")
  exit(1)

# 步驟 1：兩邊 git pull 保持最新
print("🔄 先拉取 DEV 最新代码...")
run(["git", "pull"], cwd=SRC)

print("🔄 再拉取 MAIN 最新代码...")
run(["git", "pull"], cwd=DEST)

# 步驟 2 & 3：同步文件
print("📦 正在同步文件...")
run([
  "rsync", "-av", "--delete",
  "--exclude=.git",
  "--exclude=.gitlab-ci.yml",
  f"{SRC}/", f"{DEST}/"
])

# 步驟 4：提交變更（如有）
os.chdir(DEST)
status = run(["git", "status", "--porcelain"], capture_output=True)
has_changes = status.stdout.strip() != ""

if has_changes:
  print("📍 檢測到變更，準備提交...")
  run(["git", "add", "."])
  run(["git", "commit", "-m", "同步 jxf 项目内容"])

  print("⬇️ 拉取远端变更并尝试 rebase...")
  run(["git", "pull", "--rebase"])
  run(["git", "push"])
else:
  print("✅ 無需提交，工作目录干净")

# 步驟 6：打标签并推送
print(f"🏷️ 打标签: {TAG}")
run(["git", "tag", TAG])
run(["git", "push", "origin", TAG])

print(f"✅ 同步與版本標記 {TAG} 完成")

# 步驟 7：開啟 Git 項目頁面
import webbrowser
webbrowser.open("https://git.easydevops.net/frontend/rb88_web_vue/-/pipelines")