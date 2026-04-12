#!/bin/zsh
set -euo pipefail

SRC="/Volumes/My Passport/"
DST="/Volumes/TOSHIBA EXT/"

LOG="$HOME/rsync_mirror_$(date +%Y%m%d_%H%M%S).log"

# ===== 基本檢查 =====
[[ -d "$SRC" ]] || { echo "❌ 找不到來源：$SRC"; exit 1; }
[[ -d "$DST" ]] || { echo "❌ 找不到目標：$DST"; exit 1; }

echo "SRC: $SRC" | tee "$LOG"
echo "DST: $DST" | tee -a "$LOG"
echo "LOG: $LOG" | tee -a "$LOG"
echo "🚀 開始備份..." | tee -a "$LOG"
echo "========================================" | tee -a "$LOG"

rsync \
-a \
--delete \
--human-readable \
--info=progress2 \
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
"$SRC" "$DST" | tee -a "$LOG"

echo "========================================" | tee -a "$LOG"
echo "✅ Mirror Backup 完成" | tee -a "$LOG"