#!/usr/bin/env bash

# Consider using Appendix config of repo2docker
# This example shows how to use 
# [`appendix`](https://binderhub.readthedocs.io/en/latest/reference/app.html?highlight=c.BinderHub.appendix%20#binderhub.app.BinderHub) 
# feature of BinderHub. 

jupyterhub_user="${JUPYTERHUB_USER}"

# see https://stackoverflow.com/questions/3162385/how-to-split-a-string-in-shell-and-get-the-last-field
branch="europa-${jupyterhub_user##*-}"

git checkout -b "${branch}"

remote_branch_exists=$(git ls-remote --refs -q "${BINDER_REPO_URL}" "${branch}" | wc -l)
if [ "${remote_branch_exists}" == "1" ]; then
    git pull origin "${branch}"
else
    # `GIT_BRANCH` is the original branch
    git pull origin "${GIT_BRANCH}"
    git merge "${GIT_BRANCH}"
    # so the repo listing in the front-end can be replaced
    git push origin "${branch}"
fi
echo "Post-start script executed successfully" > poststart.log