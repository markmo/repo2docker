#!/usr/bin/env bash

PROFILE=${1}
ENV=${2}
PROJECT="apt-phenomenon-243802"
if [ "${PROFILE}" == "" ] || [ "${PROFILE}" == "default" ]
then
    path="default"
    name=""
else
    path="${PROFILE}"
    name="${PROFILE}-"
fi
if [ "${ENV}" == "test" ]
then
    SUFFIX="-test"
    VERSION=$(cat ../repo2docker-base/profiles/${path}/TEST-VERSION)
else
    SUFFIX=""
    VERSION=$(cat ../repo2docker-base/profiles/${path}/VERSION)
fi
if [ "$VERSION" == "" ]
then
    echo "Error"
    exit 1
fi
cp repo2docker/buildpacks/profiles/${PROFILE}/base.py repo2docker/buildpacks/base.py
sed -i -E "s/(FROM gcr\.io\/${PROJECT}\/repo2docker-).*:(latest|[0-9]+\.[0-9]+\.[0-9]+)/\1${name}base${SUFFIX}:${VERSION}/" repo2docker/buildpacks/base.py
