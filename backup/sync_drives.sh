#!/bin/zsh
set -uo pipefail

SRC="/Volumes/My Passport/"
DST="/Volumes/TOSHIBA EXT/"

LOG="$HOME/rsync_mirror_$(date +%Y%m%d_%H%M%S).log"
RETRY=3
SLEEP=2

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="$DST/.rsync-backup/$STAMP"

# ===== 基本檢查 =====
[[ -d "$SRC" ]] || { echo "❌ 找不到來源：$SRC"; exit 1; }
[[ -d "$DST" ]] || { echo "❌ 找不到目標：$DST"; exit 1; }

# 確保備份目錄可建立
mkdir -p "$BACKUP_DIR" || { echo "❌ 無法建立備份目錄：$BACKUP_DIR"; exit 1; }

# ===== rsync 參數（可回滾・保留歷史版本）=====
RSYNC=(
  rsync
  -aH
  --numeric-ids

  # 鏡像刪除，但「被刪/被覆蓋」的舊檔會移到 backup-dir
  --delete-delay
  --backup
  --backup-dir="$BACKUP_DIR"

  --partial
  --partial-dir=".rsync-partial"
  --protect-args
  --info=progress2,stats2
  --human-readable

  # 外接碟常見格式友善
  --no-owner --no-group --no-perms --no-acls --no-xattrs

  # 排除 macOS 垃圾
  --exclude=".TemporaryItems"
  --exclude=".Trashes"
  --exclude=".Spotlight-V100"
  --exclude=".fseventsd"
  --exclude=".DS_Store"
  --exclude="._*"
  --exclude=".rsync-partial/"
  --exclude=".rsync-backup/"
)

echo "==============================" | tee -a "$LOG"
echo "SRC: $SRC" | tee -a "$LOG"
echo "DST: $DST" | tee -a "$LOG"
echo "BACKUP_DIR: $BACKUP_DIR" | tee -a "$LOG"
echo "LOG: $LOG" | tee -a "$LOG"
echo "==============================" | tee -a "$LOG"

# ===== DRY RUN =====
echo "---- DRY RUN (preview) ----" | tee -a "$LOG"
("${RSYNC[@]}" -n "$SRC" "$DST" 2>&1) | tee -a "$LOG"

read "ans?要開始正式同步（含可回滾備份）？(yes/NO): "
[[ "$ans" == "yes" ]] || { echo "已取消"; exit 0; }

# ===== 正式同步（自動重試）=====
i=1
code=1
while (( i <= RETRY )); do
  echo "---- RUN $i/$RETRY ----" | tee -a "$LOG"

  ("${RSYNC[@]}" "$SRC" "$DST" 2>&1) | tee -a "$LOG"
  code=${PIPESTATUS[0]}

  [[ $code -eq 0 ]] && break

  echo "⚠️ rsync exit=$code，${SLEEP}s 後重試..." | tee -a "$LOG"
  sleep $SLEEP
  ((i++))
done

# ===== 最終驗證（dry-run）=====
echo "---- VERIFY (final dry-run) ----" | tee -a "$LOG"
("${RSYNC[@]}" -n "$SRC" "$DST" 2>&1) | tee -a "$LOG"

echo "✅ 完成（rsync exit=$code）"
echo "📦 可回滾備份位於：$BACKUP_DIR"
echo "📄 LOG: $LOG"
exit $code