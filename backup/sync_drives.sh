#!/bin/zsh
set -uo pipefail

SRC="/Volumes/My Passport/"
DST="/Volumes/TOSHIBA EXT/"

LOG="$HOME/rsync_mirror_$(date +%Y%m%d_%H%M%S).log"
RETRY=3
SLEEP=2

# 基本檢查
[[ -d "$SRC" ]] || { echo "❌ 找不到來源：$SRC"; exit 1; }
[[ -d "$DST" ]] || { echo "❌ 找不到目標：$DST"; exit 1; }

# rsync 參數：鏡像 + 排除 macOS 垃圾 + log
RSYNC=(
  rsync -rltDh
  --delete --partial --partial-dir=".rsync-partial"
  --info=progress2
  --protect-args
  --no-owner --no-group --no-perms --no-acls --no-xattrs
  --exclude=".TemporaryItems" --exclude=".Trashes" --exclude=".Spotlight-V100" --exclude=".fseventsd"
  --exclude=".DS_Store" --exclude="._*" --exclude=".rsync-partial/"
)

# 補刀：刪掉 rsync 明確說「cannot delete non-empty directory」的目錄
# 注意：只刪 rsync 列出的目錄，不掃整顆硬碟
cleanup_failed_dirs() {
  echo "---- CLEANUP (cannot delete non-empty directory) ----" | tee -a "$LOG"

  # 從 LOG 抓路徑（相對於 DST），組成絕對路徑後 rm -rf
  # sort -u 去重，避免重複刪
  grep "cannot delete non-empty directory:" "$LOG" 2>/dev/null \
    | sed 's/.*directory: //' \
    | sort -u \
    | while IFS= read -r rel; do
        [[ -z "$rel" ]] && continue
        local target="$DST$rel"
        if [[ -d "$target" ]]; then
          echo "🧹 rm -rf: $target" | tee -a "$LOG"
          rm -rf "$target" 2>&1 | tee -a "$LOG" || true
        else
          echo "ℹ️ 不存在或已刪除：$target" | tee -a "$LOG"
        fi
      done
}

echo "SRC: $SRC" | tee -a "$LOG"
echo "DST: $DST" | tee -a "$LOG"
echo "LOG: $LOG" | tee -a "$LOG"

echo "---- DRY RUN ----" | tee -a "$LOG"
("${RSYNC[@]}" -n "$SRC" "$DST" 2>&1) | tee -a "$LOG"

read "ans?要開始正式鏡像同步？(yes/NO): "
[[ "$ans" == "yes" ]] || { echo "已取消"; exit 0; }

# 正式同步 + 重試（不中斷）
i=1
code=1
while (( i <= RETRY )); do
  echo "---- RUN $i/$RETRY ----" | tee -a "$LOG"
  ("${RSYNC[@]}" "$SRC" "$DST" 2>&1) | tee -a "$LOG"
  code=${PIPESTATUS[0]}

  # 成功就不重試
  [[ $code -eq 0 ]] && break

  echo "⚠️ rsync exit=$code，${SLEEP}s 後重試..." | tee -a "$LOG"
  sleep $SLEEP
  ((i++))
done

# ✅ 不管 rsync exit code 是什麼，都先補刀一次（尤其 code=23）
cleanup_failed_dirs

# 驗證（補刀後再驗一次）
echo "---- VERIFY (DRY RUN) ----" | tee -a "$LOG"
("${RSYNC[@]}" -n "$SRC" "$DST" 2>&1) | tee -a "$LOG"

echo "✅ 完成（rsync exit=$code）LOG: $LOG"
exit $code