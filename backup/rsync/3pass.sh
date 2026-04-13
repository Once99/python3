#!/bin/zsh
set -u

SRC="/Volumes/My Passport"
DST="/Volumes/TOSHIBA EXT"

# 先收集所有資料夾
dirs=()
for dir in "$SRC"/*; do
  [ -d "$dir" ] || continue
  dirs+=("$dir")
done

total_dirs=${#dirs[@]}

if [ "$total_dirs" -eq 0 ]; then
  echo "❌ 找不到可同步的資料夾"
  exit 1
fi

for pass in 1 2 3; do
  echo "========================================"
  echo "🚀 開始第 $pass 次 rsync"
  echo "📁 共 $total_dirs 個資料夾"
  echo "========================================"

  index=0
  for dir in "${dirs[@]}"; do
    index=$((index + 1))
    name=$(basename "$dir")

    echo
    echo "====== [$pass/3] 同步資料夾 [$index/$total_dirs]：$name ======"

    rsync -a \
      --ignore-errors \
      --partial \
      --delete \
      --partial-dir=".rsync-partial" \
      --info=progress2 \
      --human-readable \
      --stats \
      --no-times \
      --exclude='.Spotlight-V100' \
      --exclude='.Trashes' \
      --exclude='.fseventsd' \
      --exclude='.TemporaryItems' \
      --exclude='.DS_Store' \
      "$dir/" "$DST/$name/"

    echo "✅ [$pass/3] [$index/$total_dirs] 完成：$name"
  done

  echo
  echo "✅ 第 $pass 次 rsync 完成"
done

echo
echo "========================================"
echo "🎉 三次 rsync 全部完成"
echo "========================================"