#!/usr/bin/env bash

PROFILE=${1}
ENV=${2}
if [ "${PROFILE}" == "" ] || [ "${PROFILE}" == "default" ]
then
    NAME=""
else
    NAME="-${PROFILE}"
fi
if [ "${ENV}" == "test" ]
then
    SUFFIX="-test"
    VERSION=$(cat repo2docker/buildpacks/profiles/${PROFILE}/TEST-VERSION)
else
    SUFFIX=""
    VERSION=$(cat repo2docker/buildpacks/profiles/${PROFILE}/VERSION)
fi
if [ "$VERSION" == "" ]
then
    echo "Error"
    exit 1
fi

sed -i -E "s/(gcr\.io\/\\\$PROJECT_ID\/repo2docker).*:(latest|[0-9]+\.[0-9]+\.[0-9]+)/\1${NAME}${SUFFIX}:${VERSION}/g" cloudbuild.yaml
