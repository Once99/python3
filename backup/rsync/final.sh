#!/bin/zsh
set -u

SRC="/Volumes/My Passport"
DST="/Volumes/TOSHIBA EXT"
LOG="$HOME/rsync_backup_$(date +%Y%m%d_%H%M%S).log"

MODE="${1:-}"

# ===== 共用排除項目 =====
EXCLUDES=(
  --exclude=".DS_Store"
  --exclude=".Spotlight-V100"
  --exclude=".Trashes"
  --exclude=".fseventsd"
  --exclude=".TemporaryItems"
  --exclude="._*"
)

# ===== 基本檢查 =====
check_paths() {
  [[ -d "$SRC" ]] || { echo "❌ 找不到來源：$SRC"; exit 1; }
  [[ -d "$DST" ]] || { echo "❌ 找不到目標：$DST"; exit 1; }
}

show_info() {
  echo "=============================="
  echo "模式: $MODE"
  echo "SRC : $SRC"
  echo "DST : $DST"
  echo "LOG : $LOG"
  echo "時間: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "=============================="
}

usage() {
  cat <<EOF
用法：
  ./backup.sh mirror   # 完整鏡像同步（會刪除目標多餘檔案）
  ./backup.sh triple   # 分資料夾同步，跑 3 次補強
  ./backup.sh single   # 分資料夾同步，跑 1 次快速版

說明：
  mirror  = 危險模式，DST 會被同步成和 SRC 完全一致
  triple  = 適合壞碟 / 搶救 / 補漏檔
  single  = 適合一般快速搬資料
EOF
  exit 1
}

# ===== 模式 1：鏡像同步 =====
run_mirror() {
  echo "⚠️ 進入 mirror 模式：目標端多餘檔案將被刪除" | tee -a "$LOG"

  rsync \
    -a \
    --delete \
    --human-readable \
    --info=progress2 \
    --partial \
    --protect-args \
    --no-owner --no-group --no-perms \
    "${EXCLUDES[@]}" \
    "$SRC/" "$DST/" | tee -a "$LOG"

  echo "✅ Mirror Backup 完成" | tee -a "$LOG"
}

# ===== 模式 2 / 3：逐資料夾同步 =====
sync_dirs_once() {
  local pass_label="$1"

  echo "==============================" | tee -a "$LOG"
  echo "開始同步：$pass_label" | tee -a "$LOG"
  echo "==============================" | tee -a "$LOG"

  for dir in "$SRC"/*; do
    [[ -d "$dir" ]] || continue

    local name
    name=$(basename "$dir")

    echo "====== 同步: $name ======" | tee -a "$LOG"

    if [[ "$MODE" == "triple" ]]; then
      rsync -a \
        --ignore-errors \
        --partial --partial-dir=".rsync-partial" \
        --progress \
        --no-times \
        --human-readable \
        --stats \
        "${EXCLUDES[@]}" \
        "$dir/" "$DST/$name/" | tee -a "$LOG"
    else
      rsync -a \
        --ignore-errors \
        --partial \
        --info=progress2 \
        --no-times \
        "${EXCLUDES[@]}" \
        "$dir/" "$DST/$name/" | tee -a "$LOG"
    fi
  done
}

run_triple() {
  for pass in 1 2 3; do
    sync_dirs_once "第 $pass 次 rsync"
  done
  echo "✅ 三次 rsync 完成" | tee -a "$LOG"
}

run_single() {
  sync_dirs_once "單次 rsync"
  echo "✅ 單次 rsync 完成" | tee -a "$LOG"
}

# ===== 主程式 =====
[[ -n "$MODE" ]] || usage
check_paths
show_info | tee "$LOG"

case "$MODE" in
  mirror)
    run_mirror
    ;;
  triple)
    run_triple
    ;;
  single)
    run_single
    ;;
  *)
    usage
    ;;
esac