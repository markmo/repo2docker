#!/usr/bin/env bash

commit_message=${1:-"merge devsheds session"}

jupyterhub_user="${JUPYTERHUB_USER}"

# see https://stackoverflow.com/questions/3162385/how-to-split-a-string-in-shell-and-get-the-last-field
original_branch=${BINDER_REQUEST##*/}

branch="europa-${jupyterhub_user##*-}"

echo "commit_message=${commit_message}"
echo "JUPYTERHUB_USER=${JUPYTERHUB_USER}"
echo "BINDER_REQUEST=${BINDER_REQUEST}"
echo "REPO_DIR=${REPO_DIR}"

cd "${REPO_DIR}"

touch .gitignore
# don't commit the .garden directory
if grep -Fxq ".garden" .gitignore; then
    echo "entry exists"
else
    echo ".garden" >> .gitignore
fi

git add .
git commit -m "catch any changes"

git checkout "${original_branch}"
# Merge the temporary branch
git merge --squash "${branch}"
git commit -m "${commit_message}"

# only delete the working branch if we successfully pushed the merged commits
# TODO keep branches for initial release for safety
git push origin "${original_branch}" #&& git push --delete origin "${branch}" && git branch -D "${branch}"

# TODO redirecting output to a file is not allowed in a restricted shell (rbash)
echo "Pre-stop script executed successfully" #> "/home/jovyan/prestop.log"
