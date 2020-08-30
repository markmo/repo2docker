#!/usr/bin/env bash

profile=${1}
env=${2}

project="apt-phenomenon-243802"

if [ "${profile}" == "default" ]
then
    name=""
else
    name="${profile}-"
fi

if [ "$env" == "dev" ]
then
    registry="localhost:5000"
    suffix=""
    version=$(cat ../repo2docker-base/profiles/${profile}/DEV-VERSION)
elif [ "${env}" == "test" ]
then
    registry="gcr\.io\/${project}"
    suffix="-test"
    version=$(cat ../repo2docker-base/profiles/${profile}/TEST-VERSION)
else
    registry="gcr\.io\/${project}"
    suffix=""
    version=$(cat ../repo2docker-base/profiles/${profile}/VERSION)
fi

if [ "$version" == "" ]
then
    echo "Error"
    exit 1
fi

cp repo2docker/buildpacks/profiles/${profile}/base.py repo2docker/buildpacks/base.py

sed -i -E "s/(FROM )(gcr\.io\/${project}|localhost:5000)(\/repo2docker-).*:(latest|[0-9]+\.[0-9]+\.[0-9]+)/\1${registry}\3${name}base${suffix}:${version}/" repo2docker/buildpacks/base.py
