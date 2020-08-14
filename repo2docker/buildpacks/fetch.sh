#!/usr/bin/env bash

# Consider using Appendix config of repo2docker
# This example shows how to use 
# [`appendix`](https://binderhub.readthedocs.io/en/latest/reference/app.html?highlight=c.BinderHub.appendix%20#binderhub.app.BinderHub) 
# feature of BinderHub. 

repo_dir=${1:-$REPO_DIR}
binder_repo_url=${2:-$BINDER_REPO_URL}
jupyterhub_user=${3:-$JUPYTERHUB_USER}
original_branch=${BINDER_REQUEST##*/}
git_branch=${4:-$original_branch}

echo "Args:"
echo "repo_dir=${repo_dir}"
echo "binder_repo_url=${binder_repo_url}"
echo "jupyterhub_user=${jupyterhub_user}"
echo "original_branch=${original_branch}"
echo "git_branch=${git_branch}"

cd "${repo_dir}"

# update oauth token
git remote set-url origin "${binder_repo_url}"

jupyterhub_user="${jupyterhub_user}"

# see https://stackoverflow.com/questions/3162385/how-to-split-a-string-in-shell-and-get-the-last-field
branch="europa-${jupyterhub_user##*-}"

git checkout -b "${branch}"

remote_branch_exists=$(git ls-remote --refs -q "${binder_repo_url}" "${branch}" | wc -l)
if [ "${remote_branch_exists}" == "1" ]; then
    git pull origin "${branch}"
else
    # `GIT_BRANCH` is the original branch
    git pull origin "${git_branch}"
    git merge "${git_branch}"
fi


if [ ! -f "garden.yml" ]; then
    cp /home/jovyan/garden.yml .
fi

# so the repo listing in the front-end can be replaced
git add .
git commit -m "auto commit"
git push origin "${branch}"


# systemd not available in a docker container
## Autocommit

# systemctl --user enable autocommit.service
# systemctl --user start autocommit.service


## Europa API

# systemctl --user enable europa.service
# systemctl --user start europa.service


# Set Kubeflow runtime settings for Elyra
# TODO:
# - replace password with user-specific password and 
#   policy on bucket
# - need to create bucket programmatically before spawning notebook server
# - alternatively, given multi-user support in kfp is not quite there yet,
#   set details from UI for a user-hosted kfp instance
# elyra-metadata install runtimes --replace=true \
#     --schema_name=kfp \
#     --name=devsheds-kfp \
#     --display_name="Kubeflow Pipeline" \
#     --api_endpoint=https://kubeflow.europanb.online/pipeline \
#     --cos_endpoint=https://minio.europanb.online \
#     --cos_username=minio \
#     --cos_password=minio123 \
#     --cos_bucket=${jupyterhub_user}


echo "Post-start script executed successfully" > "${HOME}"/poststart.log

exit 0

# or exec ...
# nohup /bin/bash "${HOME}"/autocommit.sh > autocommit.log &
# disown

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
