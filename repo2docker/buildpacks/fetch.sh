#!/usr/bin/env bash

# Consider using Appendix config of repo2docker
# This example shows how to use 
# [`appendix`](https://binderhub.readthedocs.io/en/latest/reference/app.html?highlight=c.BinderHub.appendix%20#binderhub.app.BinderHub) 
# feature of BinderHub. 

cd "${REPO_DIR}"

# update oauth token
git remote set-url origin "${BINDER_REPO_URL}"

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
fi


if [ ! -f "garden.yml" ]; then
    cp /home/jovyan/garden.yml .
fi

# so the repo listing in the front-end can be replaced
git add .
git commit -m "auto commit"
git push origin "${branch}"

echo "Post-start script executed successfully" > "${HOME}"/poststart.log


## Autocommit

/bin/bash "${HOME}"/autocommit.sh > autocommit.log &

# contains() {
#     [[ $1 =~ (^| )$2($| ) ]] && echo '1' || echo '0'
# }

# # safer to explicitly whitelist
# whitelist="py ipynb txt json java go"

# # see https://askubuntu.com/questions/819265/bash-script-to-monitor-file-change-and-execute-command
# inotifywait -r -m --event modify --event move --event delete --format "%e %w%f" "${REPO_DIR}" |
# while read event fullpath; do
#     echo "Event: $event on $fullpath"
#     filename=$(basename -- "$fullpath")
#     ext="${filename##*.}"
#     test=$(contains "$whitelist" "$ext")
#     if [ "$test" == '1' ]; then
#         cd "${REPO_DIR}"
#         git add "$fullpath"
#         git commit -m "auto commit"
#         git push origin "$(git rev-parse --abbrev-ref HEAD)"
#         cd -
#     fi
# done
