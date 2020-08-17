#!/usr/bin/env bash

PROFILE=${1}
if [[ ! "${PROFILE}" =~ ^(codeserver|default|garden)$ ]];
then
    echo "Invalid profile"
    exit 1
fi

ENV=${2}
if [[ ! "${ENV}" =~ ^(prod|test)$ ]];
then
    echo "Invalid environment"
    exit 1
fi

COMMIT_MSG=${3}
if [ "${COMMIT_MSG}" == "" ]
then
    echo "Commit message is required"
    exit 1
fi

/bin/bash ./set_base_version.sh "${PROFILE}" "${ENV}"
/bin/sh ./bump_version.sh "${PROFILE}" "${ENV}"
/bin/bash ./set_profile.sh "${PROFILE}" "${ENV}"
git add .
git commit -m "${COMMIT_MSG}"
git push google master
