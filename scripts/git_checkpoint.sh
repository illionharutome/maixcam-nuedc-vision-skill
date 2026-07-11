#!/usr/bin/env sh
set -eu
message=${1:?usage: git_checkpoint.sh "commit message"}
git add -A
git diff --cached --quiet && { echo "No staged changes to checkpoint." >&2; exit 1; }
git commit -m "$message"
if git remote | grep -qx origin; then git push; else echo "No origin remote; update docs/git_remote_todo.md." >&2; fi

