#!/usr/bin/env bash

cd "${REPO_DIR}"
git checkout master
git merge "${GIT_BRANCH}"
git push origin master
echo "Pre-stop script executed successfully" > prestop.log