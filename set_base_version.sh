#!/usr/bin/env bash

PROFILE=${1}
if [ "${PROFILE}" == "" ] || [ "${PROFILE}" == "default" ]
then
    path="default"
    name=""
else
    path="${PROFILE}"
    name="${PROFILE}-"
fi
PROJECT="apt-phenomenon-243802"
VERSION=$(cat ../repo2docker-base/profiles/${path}/VERSION)
if [ "$VERSION" == "" ]
then
    echo "Error"
    exit 1
fi
sed -i -E "s/(FROM gcr\.io\/${PROJECT}\/repo2docker-)\w+-(base:)([0-9]+\.[0-9]+\.[0-9]+)/\1${name}\2${VERSION}/" repo2docker/buildpacks/base.py
