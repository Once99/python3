import os
import subprocess
from datetime import datetime

SRC = "/Users/oncechen/IdeaProjects/jxf_web_static_vue_dev"
DEST = "/Users/oncechen/IdeaProjects/jxf_web_static_vue_main"

# 生成 tag：vYYYY.MM.DD.HHmm
TAG = "v" + datetime.now().strftime("%Y.%m.%d.%H%M")

def run(cmd, **kwargs):
  """執行指令，出錯時中止腳本"""
  print(f"🔧 執行指令: {' '.join(cmd)}")
  result = subprocess.run(cmd, text=True, **kwargs)
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

# 同步文件（排除 .git 及 .gitlab-ci.yml）
print("📦 正在同步文件...")
run([
  "rsync", "-av", "--delete",
  "--exclude=.git",
  "--exclude=.gitlab-ci.yml",
  f"{SRC}/", f"{DEST}/"
])

# 切換目錄
os.chdir(DEST)

# 檢查是否有變更
status = run(["git", "status", "--porcelain"], capture_output=True)
has_changes = status.stdout.strip() != ""

if has_changes:
  print("📍 檢測到變更，準備提交...")

  run(["git", "add", "."])
  run(["git", "commit", "-m", "同步 dev 项目内容"])

  print("⬇️ 拉取远端变更并尝试 rebase...")
  try:
    run(["git", "pull", "--rebase"])
  except Exception as e:
    print("❌ git pull --rebase 失败，請手動解決衝突後再重新執行")
    exit(1)

  run(["git", "push"])
else:
  print("✅ 無需提交，工作目录干净")

# 打标签并推送
print(f"🏷️ 打标签: {TAG}")
run(["git", "tag", TAG])
run(["git", "push", "origin", TAG])

print(f"✅ 同步與版本標記 {TAG} 完成")