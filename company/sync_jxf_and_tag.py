import os
import subprocess
from datetime import datetime

SRC = "/Users/oncechen/IdeaProjects/jxf_web_static_vue_dev"
DEST = "/Users/oncechen/IdeaProjects/jxf_web_static_vue_main"

# 生成 tag：vYYYY.MM.DD.HHmm
TAG = "v" + datetime.now().strftime("%Y.%m.%d.%H%M")

# 檢查目錄
if not os.path.isdir(SRC):
  print(f"❌ 源目录不存在：{SRC}")
  exit(1)

if not os.path.isdir(os.path.join(DEST, ".git")):
  print(f"❌ 目标目录不是一个 Git 仓库：{DEST}")
  exit(1)

# 同步文件（排除 .git 及 .gitlab-ci.yml）
print("📦 正在同步文件...")
rsync_cmd = [
  "rsync", "-av", "--delete",
  "--exclude=.git",
  "--exclude=.gitlab-ci.yml",
  f"{SRC}/", f"{DEST}/"
]
subprocess.run(rsync_cmd, check=True)

# 切换目录
os.chdir(DEST)

# 檢查是否有變更
status_result = subprocess.run(
  ["git", "status", "--porcelain"],
  capture_output=True,
  text=True
)

if status_result.stdout.strip():
  print("🔧 检测到变更，正在提交...")
  subprocess.run(["git", "add", "."], check=True)
  subprocess.run(["git", "commit", "-m", "同步 dev 项目内容"], check=True)
  subprocess.run(["git", "push"], check=True)
else:
  print("✅ 无需提交，工作目录干净")

# 打标签并推送
print(f"🏷️ 打标签: {TAG}")
subprocess.run(["git", "tag", TAG], check=True)
subprocess.run(["git", "push", "origin", TAG], check=True)

print(f"✅ 同步与版本标记 {TAG} 完成")