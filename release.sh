#!/usr/bin/env bash

profile=${1}
env=${2}
commit_msg=${3}

if [[ ! "${profile}" =~ ^(codeserver|default|garden)$ ]];
then
    echo "Invalid profile"
    exit 1
fi

if [[ ! "${env}" =~ ^(prod|test|dev)$ ]];
then
    echo "Invalid environment"
    exit 1
fi

if [[ "${env}" != "dev" && "${commit_msg}" == "" ]];
then
    echo "Commit message is required"
    exit 1
fi

/bin/bash ./set_base_version.sh "${profile}" "${env}"
/bin/sh ./bump_version.sh "${profile}" "${env}"
/bin/bash ./set_profile.sh "${profile}" "${env}"

if [ "${env}" == "dev" ]
then
    cloud-build-local --config=cloudbuild.yaml --dryrun=false --push .
else
    git add .
    git commit -m "${commit_msg}"
    git push google master
fi
