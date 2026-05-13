#!/bin/zsh
set -u

DEFAULT_SRC="/Volumes/My Passport"
DEFAULT_DST="/Volumes/TOSHIBA EXT"
MODE="check"
PASSES=3
ALLOW_DELETE=0
YES_DELETE=0
SAFETY_GB=10
SRC=""
DST=""

usage() {
  cat <<'USAGE'
Usage:
  3pass.sh [check|dry-run|run|verify] [SRC] [DST] [options]

Modes:
  check     Check mounts, space, and first-level folders. No rsync.
  dry-run   Preview rsync changes. No files are changed.
  run       Sync files. Extra destination files are preserved unless --delete is set.
  verify    Checksum dry-run verification after sync. No files are changed.

Options:
  --delete          Delete destination files that do not exist in source.
  --yes-delete      Required together with --delete in run mode.
  --passes N        Number of sync passes for run/dry-run. Default: 3.
  --safety-gb N     Required free-space safety margin. Default: 10.
  -h, --help        Show this help.

Examples:
  ./3pass.sh check
  ./3pass.sh dry-run "/Volumes/My Passport" "/Volumes/TOSHIBA EXT"
  ./3pass.sh run "/Volumes/My Passport" "/Volumes/TOSHIBA EXT"
  ./3pass.sh run "/Volumes/My Passport" "/Volumes/TOSHIBA EXT" --delete --yes-delete
  ./3pass.sh verify "/Volumes/My Passport" "/Volumes/TOSHIBA EXT"
USAGE
}

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

warn() {
  echo "WARNING: $*" >&2
}

human_bytes() {
  local bytes="$1"
  awk -v b="$bytes" 'BEGIN {
    split("B KB MB GB TB", u, " ");
    i=1;
    while (b >= 1024 && i < 5) { b /= 1024; i++ }
    printf "%.2f %s", b, u[i]
  }'
}

require_positive_int() {
  local label="$1"
  local value="$2"
  [[ "$value" == <-> ]] || fail "$label must be a positive integer"
  [ "$value" -gt 0 ] || fail "$label must be greater than 0"
}

is_mounted_volume() {
  local volume="$1"
  mount | grep -Fq " on $volume ("
}

volume_available_bytes() {
  df -Pk "$1" | awk 'NR==2 { print $4 * 1024 }'
}

volume_used_bytes() {
  df -Pk "$1" | awk 'NR==2 { print $3 * 1024 }'
}

directory_size_bytes() {
  du -sk "$1" | awk '{ print $1 * 1024 }'
}

same_device() {
  local a="$1"
  local b="$2"
  [ "$(df -Pk "$a" | awk 'NR==2 {print $1}')" = "$(df -Pk "$b" | awk 'NR==2 {print $1}')" ]
}

parse_args() {
  local positional=()

  while [ "$#" -gt 0 ]; do
    case "$1" in
      check|dry-run|run|verify)
        MODE="$1"
        shift
        ;;
      --delete)
        ALLOW_DELETE=1
        shift
        ;;
      --yes-delete)
        YES_DELETE=1
        shift
        ;;
      --passes)
        [ "$#" -ge 2 ] || fail "--passes requires a number"
        PASSES="$2"
        shift 2
        ;;
      --safety-gb)
        [ "$#" -ge 2 ] || fail "--safety-gb requires a number"
        SAFETY_GB="$2"
        shift 2
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      --*)
        fail "Unknown option: $1"
        ;;
      *)
        positional+=("$1")
        shift
        ;;
    esac
  done

  [ "${#positional[@]}" -le 2 ] || fail "Too many positional arguments"
  SRC="${positional[1]:-$DEFAULT_SRC}"
  DST="${positional[2]:-$DEFAULT_DST}"
}

collect_dirs() {
  dirs=()
  local dir
  for dir in "$SRC"/*(N/); do
    dirs+=("$dir")
  done
  total_dirs=${#dirs[@]}
  [ "$total_dirs" -gt 0 ] || fail "No first-level folders found in source: $SRC"
}

print_check() {
  echo "Mode: $MODE"
  echo "Source: $SRC"
  echo "Destination: $DST"
  echo "Source data size: $(human_bytes "$src_data_size")"
  echo "Destination existing data: $(human_bytes "$dst_data_size")"
  echo "Destination free: $(human_bytes "$dst_avail")"
  echo "Destination usable for mirror: $(human_bytes "$dst_usable_for_mirror")"
  echo "Safety margin: $(human_bytes "$safety_margin")"
  echo "Space check: $space_status"
  echo "Delete enabled: $ALLOW_DELETE"
  echo "Passes: $PASSES"
  echo "First-level folders: $total_dirs"
  printf '  - %s\n' "${dirs[@]:t}"
}

make_log_file() {
  local script_dir log_dir stamp
  script_dir="${0:A:h}"
  log_dir="$script_dir/logs"
  mkdir -p "$log_dir" || fail "Cannot create log directory: $log_dir"
  stamp=$(date +%Y%m%d-%H%M%S)
  log_file="$log_dir/3pass-$MODE-$stamp.log"
}

run_rsync_passes() {
  local pass index dir name rsync_status failures=0

  {
    echo "========================================"
    echo "Mode: $MODE"
    echo "Source: $SRC"
    echo "Destination: $DST"
    echo "Delete enabled: $ALLOW_DELETE"
    echo "Passes: $PASSES"
    echo "Folders: $total_dirs"
    echo "Space check: $space_status"
    echo "Log: $log_file"
    echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================"
  } | tee -a "$log_file"

  for pass in $(seq 1 "$PASSES"); do
    echo "" | tee -a "$log_file"
    echo "========================================" | tee -a "$log_file"
    echo "Starting pass $pass/$PASSES" | tee -a "$log_file"
    echo "========================================" | tee -a "$log_file"

    index=0
    for dir in "${dirs[@]}"; do
      index=$((index + 1))
      name="${dir:t}"

      echo "" | tee -a "$log_file"
      echo "====== [$pass/$PASSES] [$index/$total_dirs] $name ======" | tee -a "$log_file"

      rsync "${rsync_args[@]}" "$dir/" "$DST/$name/" 2>&1 | tee -a "$log_file"
      rsync_status=${pipestatus[1]}

      if [ "$rsync_status" -ne 0 ]; then
        failures=$((failures + 1))
        echo "ERROR: rsync failed for $name with exit code $rsync_status" | tee -a "$log_file" >&2
        echo "Continuing with remaining folders; review this folder after the run." | tee -a "$log_file" >&2
      else
        echo "Done: [$pass/$PASSES] [$index/$total_dirs] $name" | tee -a "$log_file"
      fi
    done
  done

  {
    echo ""
    echo "========================================"
    echo "Finished: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Failures: $failures"
    echo "Log: $log_file"
    echo "========================================"
  } | tee -a "$log_file"

  [ "$failures" -eq 0 ] || exit 1
}

parse_args "$@"
require_positive_int "--passes" "$PASSES"
require_positive_int "--safety-gb" "$SAFETY_GB"

[ -d "$SRC" ] || fail "Source does not exist: $SRC"
[ -d "$DST" ] || fail "Destination does not exist: $DST"
is_mounted_volume "$SRC" || fail "Source is not a mounted volume: $SRC"
is_mounted_volume "$DST" || fail "Destination is not a mounted volume: $DST"
[ "$SRC" != "$DST" ] || fail "Source and destination cannot be the same"
same_device "$SRC" "$DST" && fail "Source and destination are on the same device"

src_data_size=$(directory_size_bytes "$SRC")
dst_data_size=$(directory_size_bytes "$DST")
dst_avail=$(volume_available_bytes "$DST")
dst_usable_for_mirror=$((dst_data_size + dst_avail))
safety_margin=$((SAFETY_GB * 1024 * 1024 * 1024))
needed_with_margin=$((src_data_size + safety_margin))
space_status="OK"

if [ "$dst_usable_for_mirror" -lt "$needed_with_margin" ]; then
  space_status="NOT ENOUGH SPACE"
  warn "Source data size:              $(human_bytes "$src_data_size")"
  warn "Destination existing data:     $(human_bytes "$dst_data_size")"
  warn "Destination free:              $(human_bytes "$dst_avail")"
  warn "Destination usable for mirror: $(human_bytes "$dst_usable_for_mirror")"
  warn "Safety margin:                 $(human_bytes "$safety_margin")"
  if [ "$MODE" = "run" ]; then
    fail "Destination does not have enough free space. Free up space or use another disk."
  fi
fi

if [ "$MODE" = "run" ] && [ "$ALLOW_DELETE" -eq 1 ] && [ "$YES_DELETE" -ne 1 ]; then
  fail "run --delete requires --yes-delete. Run dry-run --delete first and review the log."
fi

collect_dirs

if [ "$MODE" = "check" ]; then
  print_check
  exit 0
fi

rsync_args=(
  -a
  --protect-args
  --partial
  --partial-dir=.rsync-partial
  --human-readable
  --stats
  --exclude=.Spotlight-V100
  --exclude=.Trashes
  --exclude=.fseventsd
  --exclude=.TemporaryItems
  --exclude=.DocumentRevisions-V100
  --exclude=.DS_Store
  --exclude='._*'
  --exclude=.apdisk
  --exclude=.rsync-partial
)

case "$MODE" in
  dry-run)
    rsync_args+=(--dry-run --itemize-changes)
    [ "$ALLOW_DELETE" -eq 1 ] && rsync_args+=(--delete-delay)
    ;;
  run)
    rsync_args+=(--info=progress2)
    [ "$ALLOW_DELETE" -eq 1 ] && rsync_args+=(--delete-delay)
    ;;
  verify)
    PASSES=1
    rsync_args+=(--dry-run --checksum --itemize-changes)
    ;;
  *)
    fail "Unknown mode: $MODE"
    ;;
esac

make_log_file
run_rsync_passes
