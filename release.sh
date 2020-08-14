#!/usr/bin/env bash

PROFILE=${1}
if [[ ! "${PROFILE}" =~ ^(codeserver|default|garden)$ ]];
then
    echo "Invalid profile"
    exit 1
fi

COMMIT_MSG=${2}
if [ "${COMMIT_MSG}" == "" ]
then
    echo "Commit message is required"
    exit 1
fi

/bin/sh ./bump_version.sh
/bin/bash ./set_profile.sh "${PROFILE}"
git add .
git commit -m "${COMMIT_MSG}"
git push google master
