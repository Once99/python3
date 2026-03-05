#!/bin/zsh
set -u

########################################
# 設定區
########################################
SRC="/Volumes/My Passport"
DST="/Volumes/TOSHIBA EXT"

# 要跑幾次（你要 3 次）
PASSES=3

# 工作目錄：存 logs / failed lists
WORKDIR="${HOME}/rsync_retry_logs"
mkdir -p "$WORKDIR"

# rsync 參數
# 注意：這裡不加 -n（dry-run），就是「實際操作」
RSYNC_OPTS=(
  -a
  --ignore-errors
  --partial
  --info=progress2
  --no-times

  # 排除 macOS 常見系統資料夾，避免 Permission / Spotlight 造成噪音
  --exclude='.Spotlight-V100'
  --exclude='.Trashes'
  --exclude='.fseventsd'
  --exclude='.TemporaryItems'
  --exclude='.DS_Store'
)

########################################
# 函數區
########################################

# 判斷 log 是否含 I/O 類錯誤（只抓硬碟/讀寫相關）
has_io_error() {
  local logfile="$1"
  /usr/bin/grep -Eqi \
    'Input/output error|I/O error|read errors|error in file IO|device error' \
    "$logfile"
}

# 同步一個父資料夾
# 回傳：0=成功，1=失敗（rsync exit code !=0 或 log 偵測到 I/O 類錯誤）
sync_one_dir() {
  local dir="$1"
  local name="$2"
  local pass="$3"

  local log="$WORKDIR/rsync_pass${pass}__${name}.log"

  echo "====== [Pass $pass] 同步: $name ======"
  echo "SRC: $dir/"
  echo "DST: $DST/$name/"
  echo "LOG: $log"
  echo ""

  # 確保目的地資料夾存在
  /bin/mkdir -p "$DST/$name/" 2>/dev/null

  # 跑 rsync 並把 stdout/stderr 都寫入 log
  /usr/bin/rsync "${RSYNC_OPTS[@]}" "$dir/" "$DST/$name/" >"$log" 2>&1
  local code=$?

  # rsync exit code 不為 0 → 直接視為失敗（會進入下一輪重試清單）
  if [[ $code -ne 0 ]]; then
    echo "!! rsync exit code = $code (視為失敗): $name"
    echo "   你可以查看 log：$log"
    return 1
  fi

  # 偵測 I/O 類錯誤字樣 → 視為失敗
  if has_io_error "$log"; then
    echo "!! 偵測到 I/O 類錯誤字樣 (視為失敗): $name"
    echo "   你可以查看 log：$log"
    return 1
  fi

  echo "OK: $name"
  return 0
}

########################################
# 主流程
########################################

# 基本檢查：來源/目的是否存在
if [[ ! -d "$SRC" ]]; then
  echo "SRC 不存在或未掛載：$SRC"
  exit 1
fi

if [[ ! -d "$DST" ]]; then
  echo "DST 不存在或未掛載：$DST"
  exit 1
fi

# 收集 SRC 第一層資料夾
all_dirs=()
for dir in "$SRC"/*; do
  [[ -d "$dir" ]] || continue
  all_dirs+=("$dir")
done

if [[ ${#all_dirs[@]} -eq 0 ]]; then
  echo "SRC 下沒有可同步的資料夾：$SRC"
  exit 1
fi

# Pass 1 先同步全部
targets=("${all_dirs[@]}")

# 跑 PASSES 次
pass=1
while [[ $pass -le $PASSES ]]; do
  local_failed="$WORKDIR/failed_pass${pass}.txt"
  : > "$local_failed"

  echo ""
  echo "=========================================="
  echo "開始 Pass $pass / $PASSES"
  echo "目標資料夾數: ${#targets[@]}"
  echo "=========================================="
  echo ""

  if [[ ${#targets[@]} -eq 0 ]]; then
    echo "沒有需要重試的資料夾了，提早結束。"
    break
  fi

  # 逐個同步
  for dir in "${targets[@]}"; do
    name=$(basename "$dir")

    if ! sync_one_dir "$dir" "$name" "$pass"; then
      echo "$dir" >> "$local_failed"
    fi

    echo ""
  done

  # 準備下一輪：只跑失敗的資料夾
  if [[ -s "$local_failed" ]]; then
    echo "Pass $pass 完成：仍有失敗資料夾"
    echo "失敗清單：$local_failed"
    echo "內容如下："
    cat "$local_failed"
    echo ""

    # 讀成陣列 targets，給下一輪用
    targets=()
    while IFS= read -r line; do
      [[ -n "$line" ]] && targets+=("$line")
    done < "$local_failed"
  else
    echo "Pass $pass 完成：全部成功，沒有需要重試的資料夾。"
    targets=()
  fi

  pass=$((pass + 1))
done

echo ""
echo "=== 完成 ==="
echo "logs / failed lists 都在：$WORKDIR"
echo "最後仍失敗的（如果有）：$WORKDIR/failed_pass${PASSES}.txt"