rsync -a --ignore-errors --partial --info=progress2 --no-times \
  --exclude=".Spotlight-V100/" \
  --exclude=".TemporaryItems/" \
  --exclude=".Trashes/" \
  --exclude=".fseventsd/" \
  --exclude=".DS_Store" \
  --exclude="._*" \
  "/Volumes/My Passport/" "/Volumes/TOSHIBA EXT/"