#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/Users/oncechen/IdeaProjects/sport}"
BRANCH="${1:-test}"
ORIGIN_REMOTE="${ORIGIN_REMOTE:-origin}"
GITLAB_REMOTE="${GITLAB_REMOTE:-gitlab}"
GITLAB_URL="https://gitlab.com/DavidTsai99/ty_sport.git"

log() {
  printf "\n[%s] %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

fail() {
  printf "\nERROR: %s\n" "$*" >&2
  exit 1
}

command -v git >/dev/null 2>&1 || fail "git command not found"
[ -d "$REPO_DIR/.git" ] || fail "not a git repository: $REPO_DIR"

cd "$REPO_DIR"

log "Repository: $REPO_DIR"
log "Branch: $BRANCH"

git remote get-url "$ORIGIN_REMOTE" >/dev/null 2>&1 || fail "missing remote: $ORIGIN_REMOTE"
git remote get-url "$GITLAB_REMOTE" >/dev/null 2>&1 || fail "missing remote: $GITLAB_REMOTE"

actual_gitlab_url="$(git remote get-url "$GITLAB_REMOTE")"
if [ "$actual_gitlab_url" != "$GITLAB_URL" ]; then
  fail "$GITLAB_REMOTE remote points to '$actual_gitlab_url', expected '$GITLAB_URL'"
fi

current_branch="$(git branch --show-current)"
if [ "$current_branch" != "$BRANCH" ]; then
  fail "current branch is '$current_branch'. Please switch to '$BRANCH' first."
fi

tracked_dirty="$(git status --porcelain=v1 --untracked-files=no)"
if [ -n "$tracked_dirty" ]; then
  printf "%s\n" "$tracked_dirty"
  fail "tracked files have uncommitted changes. Commit or stash them before pull/push."
fi

untracked="$(git ls-files --others --exclude-standard)"
if [ -n "$untracked" ]; then
  log "Untracked files found; they will not be pushed:"
  printf "%s\n" "$untracked"
fi

log "Remotes"
git remote -v

log "Pulling latest from $ORIGIN_REMOTE/$BRANCH"
git pull --ff-only "$ORIGIN_REMOTE" "$BRANCH"

log "Fetching $GITLAB_REMOTE/$BRANCH for safety check"
if git fetch "$GITLAB_REMOTE" "$BRANCH"; then
  remote_ref="$GITLAB_REMOTE/$BRANCH"
  if git show-ref --verify --quiet "refs/remotes/$remote_ref"; then
    if git merge-base --is-ancestor "$remote_ref" "$BRANCH"; then
      log "Pushing $BRANCH to $GITLAB_REMOTE/$BRANCH"
      git push "$GITLAB_REMOTE" "$BRANCH:$BRANCH"
    else
      log "$remote_ref has different history. Syncing by safe overwrite with --force-with-lease."
      git push --force-with-lease="$BRANCH" "$GITLAB_REMOTE" "$BRANCH:$BRANCH"
    fi
  else
    log "$remote_ref not found after fetch. Creating it."
    git push "$GITLAB_REMOTE" "$BRANCH:$BRANCH"
  fi
else
  log "$GITLAB_REMOTE/$BRANCH does not exist or cannot be fetched. Creating it."
  git push "$GITLAB_REMOTE" "$BRANCH:$BRANCH"
fi

log "Done"
