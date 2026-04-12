#!/bin/zsh

SRC="/Volumes/My Passport/"
DST="/Volumes/TOSHIBA EXT/"

echo "📦 正在計算總檔案大小..."
TOTAL=$(rsync -a --dry-run --stats "$SRC" "$DST" | grep "Total file size" | awk '{print $4}')

echo "📊 總大小: $TOTAL"
echo "🚀 開始備份..."
echo "===================================="

rsync -a \
  --ignore-errors \
  --partial \
  --info=progress2 \
  --human-readable \
  "$SRC" "$DST"

echo "===================================="
echo "✅ 備份完成"