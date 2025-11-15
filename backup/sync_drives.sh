#!/bin/zsh

SRC="/Volumes/My Passport/"
DST="/Volumes/TOSHIBA EXT/"

if [ ! -d "$SRC" ]; then
  echo "❌ 找不到來源硬碟：$SRC"
  exit 1
fi

if [ ! -d "$DST" ]; then
  echo "❌ 找不到目標硬碟：$DST"
  exit 1
fi

echo "⚠️ 注意：這是『完全鏡像』同步"
echo "   $DST 會被同步成跟 $SRC 完全一樣（包含刪除多餘檔案）"
read "ans?確定要執行嗎？(yes/NO) : "

if [ "$ans" != "yes" ]; then
  echo "已取消。"
  exit 0
fi

echo "🔍 執行 dry-run（不會真的動檔案）..."
rsync -avhn --delete --delete-excluded --force --progress \
  --exclude ".DS_Store" \
  "$SRC" "$DST"

echo ""
read "ans2?以上預覽正常嗎？要正式執行？(yes/NO) : "

if [ "$ans2" != "yes" ]; then
  echo "已取消正式同步。"
  exit 0
fi

echo "🚀 開始『完整鏡像』同步..."
rsync -avh --delete --delete-excluded --force --progress \
  --exclude ".DS_Store" \
  "$SRC" "$DST"

echo "✅ 同步完成！"