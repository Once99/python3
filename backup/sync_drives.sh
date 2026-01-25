#!/bin/zsh
set -uo pipefail

# =========================
# 基本設定
# =========================
SRC="/Volumes/My Passport"
DST="/Volumes/TOSHIBA EXT"

SRC_DIR="$SRC/"
DST_DIR="$DST/"

MAX_RETRY=3
SLEEP_BETWEEN_RETRY=3

# =========================
# 基礎檢查
# =========================
if [ ! -d "$SRC" ]; then
  echo "❌ 找不到來源硬碟：$SRC"
  exit 1
fi

if [ ! -d "$DST" ]; then
  echo "❌ 找不到目標硬碟：$DST"
  exit 1
fi

if [ "$(cd "$SRC" && pwd)" = "$(cd "$DST" && pwd)" ]; then
  echo "❌ 來源與目標路徑相同，已中止"
  exit 1
fi

# =========================
# Log 設定
# =========================
LOG_DIR="$HOME/rsync_logs"
mkdir -p "$LOG_DIR"
TS="$(date '+%Y%m%d_%H%M%S')"
LOG_FILE="$LOG_DIR/rsync_mirror_${TS}.log"

echo "========================================"
echo "⚠️  完全鏡像同步（含刪除）"
echo "SRC: $SRC_DIR"
echo "DST: $DST_DIR"
echo "LOG: $LOG_FILE"
echo "========================================"

read "ans?確定要執行 dry-run 嗎？(yes/NO) : "
if [ "$ans" != "yes" ]; then
  echo "已取消"
  exit 0
fi

# =========================
# rsync 基本參數
# =========================
RSYNC_BASE=(
  rsync
  -rltDh
  --delete
  --ignore-errors
  --ignore-missing-args
  --partial
  --partial-dir=".rsync-partial"
  --info=progress2
  --itemize-changes
  --protect-args
  --no-owner --no-group --no-perms
  --no-acls --no-xattrs
  --omit-dir-times

  --exclude=".TemporaryItems"
  --exclude=".Trashes"
  --exclude=".DS_Store"
  --exclude="._*"
  --exclude=".Spotlight-V100"
  --exclude=".fseventsd"
  --exclude=".Trashes"
  --exclude=".rsync-partial/"
)

# =========================
# 1️⃣ Dry-run
# =========================
echo "🔍 Dry-run 預覽（不動檔案）..."
("${RSYNC_BASE[@]}" -n "$SRC_DIR" "$DST_DIR" 2>&1) | tee -a "$LOG_FILE"

read "ans2?Dry-run 正常，執行正式同步？(yes/NO) : "
if [ "$ans2" != "yes" ]; then
  echo "已取消正式同步"
  exit 0
fi

# =========================
# 2️⃣ 正式同步（重試機制）
# =========================
TRY=1
RSYNC_EXIT=0

while [ $TRY -le $MAX_RETRY ]; do
  echo "" | tee -a "$LOG_FILE"
  echo "🚀 rsync 正式同步（第 $TRY 次）..." | tee -a "$LOG_FILE"

  ("${RSYNC_BASE[@]}" "$SRC_DIR" "$DST_DIR" 2>&1) | tee -a "$LOG_FILE"
  RSYNC_EXIT=${PIPESTATUS[0]}

  if [ $RSYNC_EXIT -eq 0 ]; then
    echo "✅ rsync 成功完成（第 $TRY 次）" | tee -a "$LOG_FILE"
    break
  else
    echo "⚠️ rsync exit code = $RSYNC_EXIT（第 $TRY 次）" | tee -a "$LOG_FILE"
    TRY=$((TRY + 1))
    sleep $SLEEP_BETWEEN_RETRY
  fi
done

if [ $RSYNC_EXIT -ne 0 ]; then
  echo "❌ rsync 在 $MAX_RETRY 次後仍有錯誤" | tee -a "$LOG_FILE"
  echo "👉 請檢查 log 中的 failed / permission / vanished 檔案" | tee -a "$LOG_FILE"
  exit 1
fi

# =========================
# 3️⃣ 同步後檢查
# =========================
echo "" | tee -a "$LOG_FILE"
echo "🔎 同步後驗證（再次 dry-run，理想狀態無任何輸出）" | tee -a "$LOG_FILE"
("${RSYNC_BASE[@]}" -n "$SRC_DIR" "$DST_DIR" 2>&1) | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "🎉 全部完成！Log 位於：" | tee -a "$LOG_FILE"
echo "👉 $LOG_FILE"