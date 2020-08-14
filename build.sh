#!/usr/bin/env bash

PROFILE=${1:-codeserver}
PROJECT="apt-phenomenon-243802"
VERSION=$(cat ../repo2docker-base/profiles/${PROFILE}/VERSION)
sed -i "s/(FROM gcr\.io\/${PROJECT}\/repo2docker-)\w+(-base:)(\d+\.\d+\.\d+)/\1${PROFILE}\2${VERSION}/" repo2docker/buildpacks/base.py
