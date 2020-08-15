#!/usr/bin/env bash

PROFILE=${1}
if [ "${PROFILE}" == "" ] || [ "${PROFILE}" == "default" ]
then
    name=""
else
    name="-${PROFILE}"
fi
VERSION=$(cat repo2docker/buildpacks/profiles/${PROFILE}/VERSION)
if [ "$VERSION" == "" ]
then
    echo "Error"
    exit 1
fi

sed -i -E "s/(gcr\.io\/\\\$PROJECT_ID\/repo2docker).*:(latest|[0-9]+\.[0-9]+\.[0-9]+)/\1${name}:${VERSION}/g" cloudbuild.yaml
