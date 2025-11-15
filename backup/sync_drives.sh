#!/bin/zsh

# 設定來源與目標硬碟路徑（換成你的名稱）
SRC="/Volumes/My Passport/"
DST="/Volumes/TOSHIBA EXT/"

# 檢查硬碟是否有掛載
if [ ! -d "$SRC" ]; then
  echo "❌ 找不到來源硬碟：$SRC"
  exit 1
fi

if [ ! -d "$DST" ]; then
  echo "❌ 找不到目標硬碟：$DST"
  exit 1
fi

echo "⚠️ 注意：這是『完全鏡像』，$DST 會變成跟 $SRC 一模一樣"
echo "    目標碟上多出來的檔案會被刪除！"
read "ans?確定要執行嗎？(yes/NO) : "

if [ "$ans" != "yes" ]; then
  echo "已取消。"
  exit 0
fi

# 建議先做一次乾跑列出即將變動的項目
echo "🔍 先做一次 dry-run (不會真的改動檔案)…"
rsync -avhn --delete --progress \
  --exclude ".DS_Store" \
  "$SRC" "$DST"

read "ans2?上面看起來沒問題嗎？確定要正式執行？(yes/NO) : "

if [ "$ans2" != "yes" ]; then
  echo "已取消正式同步。"
  exit 0
fi

echo "🚀 開始正式同步…"
rsync -avh --delete --progress \
  --exclude ".DS_Store" \
  "$SRC" "$DST"

echo "✅ 同步完成！"