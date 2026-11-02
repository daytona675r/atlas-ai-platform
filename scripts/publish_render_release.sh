#!/usr/bin/env bash
set -euo pipefail

RENDER_RELEASE_BRANCH="${1:?release branch required}"
SOURCE_SHA="${2:?source SHA required}"
GIT_REMOTE="${GIT_REMOTE:-origin}"

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git fetch "$GIT_REMOTE" "$RENDER_RELEASE_BRANCH" || true
git checkout -B "$RENDER_RELEASE_BRANCH" "$SOURCE_SHA"

# The model is intentionally ignored in developer worktrees.  At this point
# both files have already passed candidate provenance and SHA-256 validation.
test -s model.pkl
test -s candidate-metadata.json
git add -f -- model.pkl
git add -- candidate-metadata.json
git commit -m "Render release $SOURCE_SHA" || echo "Release artifacts already present"
git push --force-with-lease "$GIT_REMOTE" "HEAD:refs/heads/$RENDER_RELEASE_BRANCH"
