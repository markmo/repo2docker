#!/usr/bin/env bash

profile=${1}
env=${2}

if [ "${profile}" == "default" ]
then
    name=""
else
    name="-${profile}"
fi

if [ "${env}" == "dev" ]
then
    registry="localhost:5000"
    suffix=""
    version=$(cat repo2docker/buildpacks/profiles/${profile}/DEV-VERSION)
elif [ "${env}" == "test" ]
then
    registry="gcr\.io\/\\\$PROJECT_ID"
    suffix="-test"
    version=$(cat repo2docker/buildpacks/profiles/${profile}/TEST-VERSION)
else
    registry="gcr\.io\/\\\$PROJECT_ID"
    suffix=""
    version=$(cat repo2docker/buildpacks/profiles/${profile}/VERSION)
fi

if [ "$version" == "" ]
then
    echo "Error"
    exit 1
fi

sed -i -E "s/(gcr\.io\/\\\$PROJECT_ID|localhost:5000)(\/repo2docker).*:(latest|[0-9]+\.[0-9]+\.[0-9]+)/${registry}\2${name}${suffix}:${version}/" cloudbuild.yaml
