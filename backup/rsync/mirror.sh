#!/bin/zsh
set -euo pipefail

SRC="/Volumes/My Passport/"
DST="/Volumes/TOSHIBA EXT/"

# ===== 基本檢查 =====
[[ -d "$SRC" ]] || { echo "❌ 找不到來源：$SRC"; exit 1; }
[[ -d "$DST" ]] || { echo "❌ 找不到目標：$DST"; exit 1; }

echo "SRC: $SRC"
echo "DST: $DST"
echo "🧹 清理目標端垃圾檔..."
echo "========================================"

# ===== 清理 macOS 垃圾 =====
find "$DST" -name ".DS_Store" -type f -delete 2>/dev/null || true
find "$DST" -name "._*" -type f -delete 2>/dev/null || true
find "$DST" -name ".Spotlight-V100" -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$DST" -name ".Trashes" -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$DST" -name ".fseventsd" -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$DST" -name ".TemporaryItems" -type d -prune -exec rm -rf {} + 2>/dev/null || true

echo "🚀 開始備份（顯示總進度）..."
echo "========================================"

rsync \
  -a \
  --delete \
  --delete-excluded \
  --force \
  --human-readable \
  --info=progress2,stats2 \
  --no-inc-recursive \
  --partial \
  --protect-args \
  --no-owner --no-group --no-perms \
  --exclude=".DS_Store" \
  --exclude=".Spotlight-V100" \
  --exclude=".Trashes" \
  --exclude=".fseventsd" \
  --exclude=".TemporaryItems" \
  --exclude="._*" \
  "$SRC" "$DST"

echo
echo "========================================"
echo "✅ 完成（上面 stats 有總傳輸統計）"