#!/usr/bin/env bash

jupyterhub_user="${JUPYTERHUB_USER}"

# see https://stackoverflow.com/questions/3162385/how-to-split-a-string-in-shell-and-get-the-last-field
branch="europa-${jupyterhub_user##*-}"

cd "${REPO_DIR}"
# `GIT_BRANCH` is the original branch
git checkout "${GIT_BRANCH}"
# Merge the temporary branch
git merge "${branch}"
git push origin "${GIT_BRANCH}"
echo "Pre-stop script executed successfully" > prestop.log