#!/bin/sh

profile=${1}
env=${2}

# `sh` uses a single eq
if [ "$env" = "dev" ]
then
    bin/versionbump patch repo2docker/buildpacks/profiles/${profile}/DEV-VERSION
elif [ "$env" = "test" ]
then
    bin/versionbump patch repo2docker/buildpacks/profiles/${profile}/TEST-VERSION
    git add repo2docker/buildpacks/profiles/${profile}/TEST-VERSION
elif [ "$env" = "prod" ]
then
    bin/versionbump patch repo2docker/buildpacks/profiles/${profile}/VERSION
    git add repo2docker/buildpacks/profiles/${profile}/VERSION
else
    echo "Invalid environment"
    exit 1
fi
