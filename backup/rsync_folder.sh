#!/bin/zsh

SRC="/Volumes/My Passport"
DST="/Volumes/TOSHIBA EXT"

for dir in "$SRC"/*; do
  [ -d "$dir" ] || continue

  name=$(basename "$dir")

  echo "====== 同步: $name ======"

  rsync -a --ignore-errors --partial --info=progress2 --no-times \
    "$dir/" "$DST/$name/"
done