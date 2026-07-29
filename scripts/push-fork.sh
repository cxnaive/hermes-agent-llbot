#!/usr/bin/env bash
# Push local `main` to the fork (cxnaive/hermes-agent-llbot) using the PAT in
# .env.fork-push (gitignored). Rewritten SHAs after a rebase → force-with-lease
# against the fork's CURRENT main so we never clobber an unexpected state.
#
#   scripts/push-fork.sh            # push main → fork
#   scripts/push-fork.sh <branch>   # push <branch> → fork/<branch>
set -euo pipefail
cd "$(dirname "$0")/.."

BRANCH="${1:-main}"
ENV_FILE=".env.fork-push"
[[ -f "$ENV_FILE" ]] || { echo "missing $ENV_FILE (FORK_PUSH_TOKEN / FORK_PUSH_USER)"; exit 1; }
# shellcheck disable=SC1090
source "$ENV_FILE"
: "${FORK_PUSH_TOKEN:?FORK_PUSH_TOKEN not set in $ENV_FILE}"
USER="${FORK_PUSH_USER:-cxnaive}"
REPO="github.com/cxnaive/hermes-agent-llbot.git"

REMOTE_SHA="$(git ls-remote "https://${USER}:${FORK_PUSH_TOKEN}@${REPO}" "refs/heads/${BRANCH}" | cut -f1)"
if [[ -z "$REMOTE_SHA" ]]; then
  echo "fork has no ${BRANCH} yet — creating it"
  git push "https://${USER}:${FORK_PUSH_TOKEN}@${REPO}" "${BRANCH}:${BRANCH}"
else
  git push --force-with-lease="${BRANCH}:${REMOTE_SHA}" \
    "https://${USER}:${FORK_PUSH_TOKEN}@${REPO}" "${BRANCH}:${BRANCH}"
fi
