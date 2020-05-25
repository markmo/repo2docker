#!/usr/bin/env bash

remote_branch_exists=$(git ls-remote --refs -q "${BINDER_REPO_URL}" "${GIT_BRANCH}" | wc -l)
if [ "${remote_branch_exists}" == "1" ]; then
    git pull origin "${GIT_BRANCH}"
else
    git pull origin master
    git merge master
fi
echo "Post-start script executed successfully" > poststart.log