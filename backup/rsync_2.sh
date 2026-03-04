#!/bin/zsh
set -euo pipefail

SRC="/Volumes/My Passport/"
DST="/Volumes/TOSHIBA EXT/"
LOG="$HOME/rsync_mirror_$(date +%Y%m%d_%H%M%S).log"

[[ -d "$SRC" ]] || { echo "❌ 找不到來源：$SRC"; exit 1; }
[[ -d "$DST" ]] || { echo "❌ 找不到目標：$DST"; exit 1; }

# 1) 清掉目的端殘留的 partial 目錄（避免 non-empty 卡死）
find "$DST" -type d -name ".rsync-partial" -prune -exec rm -rf {} + 2>/dev/null || true
mkdir -p "$DST/.rsync-partial"

# 2) 最短可用的鏡像差異同步（確保 delete 做到底）
rsync -a --delete --delete-delay --no-times \
  --force --ignore-errors \
  --partial --partial-dir="$DST/.rsync-partial" \
  --exclude=".Spotlight-V100/" \
  --exclude=".TemporaryItems/" \
  --exclude=".Trashes/" \
  --exclude=".fseventsd/" \
  --exclude=".DS_Store" \
  --exclude="._*" \
  "$SRC" "$DST" | tee -a "$LOG"

echo "✅ 完成"
echo "📄 LOG: $LOG"