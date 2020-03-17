#!/usr/bin/env bash

cd "${REPO_DIR}"
git checkout master
git merge "${GIT_BRANCH}"