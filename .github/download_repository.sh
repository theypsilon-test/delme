#!/usr/bin/env bash

set -euo pipefail

REPO_PATH="${1}"
REPO_URL="${2}"
BRANCH="${3:-}"

rm -rf "${REPO_PATH}" || true
mkdir -p "${REPO_PATH}"
pushd "${REPO_PATH}" > /dev/null 2>&1
git init -q
git remote add origin "${REPO_URL}"
git -c protocol.version=2 fetch --depth=1 -q --no-tags --prune --no-recurse-submodules origin "${BRANCH}"
git checkout -qf FETCH_HEAD
popd > /dev/null 2>&1
