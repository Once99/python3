#!/bin/bash

SRC="/Users/oncechen/IdeaProjects/jxf_web_static_vue_dev"
DEST="/Users/oncechen/IdeaProjects/jxf_web_static_vue_main"

# 时间戳 tag 格式 vYYYY.MM.DD.HHmm
TAG="v$(date +'%Y.%m.%d.%H%M')"

# 检查源目录和目标目录
if [ ! -d "$SRC" ]; then
  echo "❌ 源目录不存在：$SRC"
  exit 1
fi

if [ ! -d "$DEST/.git" ]; then
  echo "❌ 目标目录不是一个 Git 仓库：$DEST"
  exit 1
fi

# 同步文件
echo "📦 正在同步文件..."
rsync -av --delete --exclude=".git" "$SRC/" "$DEST/"

cd "$DEST" || exit 1

# Git 提交并推送
echo "🔧 正在提交更新..."
git add .
git commit -m "同步 dev 项目内容"
git push

# 打标签并推送
echo "🏷️ 打标签: $TAG"
git tag "$TAG"
git push origin "$TAG"

echo "✅ 同步与版本标记 $TAG 完成"