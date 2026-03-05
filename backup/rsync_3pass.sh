#!/bin/zsh

SRC="/Volumes/My Passport"
DST="/Volumes/TOSHIBA EXT"

for pass in 1 2 3; do
  echo "=============================="
  echo "開始第 $pass 次 rsync"
  echo "=============================="

  for dir in "$SRC"/*; do
    [ -d "$dir" ] || continue

    name=$(basename "$dir")

    echo "====== 同步: $name ======"

    rsync -a \
      --ignore-errors \
      --partial --partial-dir=".rsync-partial" \
      --progress \
      --no-times \
      --human-readable \
      --stats \
      --exclude='.Spotlight-V100' \
      --exclude='.Trashes' \
      --exclude='.fseventsd' \
      --exclude='.TemporaryItems' \
      --exclude='.DS_Store' \
      "$dir/" "$DST/$name/"
  done

done

echo "=== 三次 rsync 完成 ==="