#!/bin/zsh
set -u

SRC="/Volumes/My Passport"
DST="/Volumes/TOSHIBA EXT"

# 你要跑幾次
PASSES=3

# 工作目錄（存 logs / failed lists）
WORKDIR="${HOME}/rsync_retry_logs"
mkdir -p "$WORKDIR"

# rsync 參數集中管理
RSYNC_OPTS=(
  -a
  --ignore-errors
  --partial
  --info=progress2
  --no-times
)

# 判斷 log 是否含 I/O 類錯誤（可依你的實際狀況再增修關鍵字）
has_io_error() {
  local logfile="$1"
  /usr/bin/grep -Eqi \
    'Input/output error|I/O error|read errors|error in file IO|device error' \
    "$logfile"
}

# 同步一個父資料夾，並回傳 0=成功 1=失敗(含I/O類錯誤或rsync exit code非0)
sync_one_dir() {
  local dir="$1"
  local name="$2"
  local pass="$3"

  local log="$WORKDIR/rsync_pass${pass}__${name}.log"

  echo "====== [Pass $pass] 同步: $name ======"
  echo "SRC: $dir/"
  echo "DST: $DST/$name/"
  echo "LOG: $log"

  # 跑 rsync 並把 stdout/stderr 都記到 log
  /usr/bin/rsync "${RSYNC_OPTS[@]}" "$dir/" "$DST/$name/" >"$log" 2>&1
  local code=$?

  # rsync exit code 不為 0 也算失敗（即使不是 I/O）
  if [[ $code -ne 0 ]]; then
    echo "!! rsync exit code = $code (視為失敗): $name"
    return 1
  fi

  # 看 log 有沒有 I/O 類錯誤字樣
  if has_io_error "$log"; then
    echo "!! 偵測到 I/O 類錯誤字樣 (視為失敗): $name"
    return 1
  fi

  echo "OK: $name"
  return 0
}

# 取得 SRC 下第一層父資料夾清單
all_dirs=()
for dir in "$SRC"/*; do
  [[ -d "$dir" ]] || continue
  all_dirs+=("$dir")
done

if [[ ${#all_dirs[@]} -eq 0 ]]; then
  echo "SRC 下沒有可同步的資料夾：$SRC"
  exit 1
fi

# 第一次同步：全部
targets=("${all_dirs[@]}")

for pass in {1..3}; do
  [[ $pass -le $PASSES ]] || break

  local_failed="$WORKDIR/failed_pass${pass}.txt"
  : > "$local_failed"

  echo ""
  echo "==============================="
  echo "開始 Pass $pass / $PASSES"
  echo "目標資料夾數: ${#targets[@]}"
  echo "==============================="

  if [[ ${#targets[@]} -eq 0 ]]; then
    echo "沒有需要重試的資料夾了，提早結束。"
    break
  fi

  # 逐個同步
  for dir in "${targets[@]}"; do
    name=$(basename "$dir")

    if ! sync_one_dir "$dir" "$name" "$pass"; then
      # 記錄失敗的父資料夾「完整路徑」
      echo "$dir" >> "$local_failed"
    fi

    echo ""
  done

  # 整理下一輪 targets：只針對失敗者
  if [[ -s "$local_failed" ]]; then
    echo "Pass $pass 完成：有失敗資料夾，清單：$local_failed"
    echo "內容如下："
    cat "$local_failed"

    # 讀成陣列供下一 pass 使用
    targets=()
    while IFS= read -r line; do
      [[ -n "$line" ]] && targets+=("$line")
    done < "$local_failed"
  else
    echo "Pass $pass 完成：全部成功，沒有需要重試的資料夾。"
    targets=()
  fi
done

echo ""
echo "=== 完成 ==="
echo "logs / failed lists 都在：$WORKDIR"