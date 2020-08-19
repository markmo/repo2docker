#!/bin/sh

profile=${1}
ENV=${2:-test}

# `sh` uses a single eq
if [ "$ENV" = "test" ]
then
    bin/versionbump patch repo2docker/buildpacks/profiles/${profile}/TEST-VERSION
    git add repo2docker/buildpacks/profiles/${profile}/TEST-VERSION
else
    bin/versionbump patch repo2docker/buildpacks/profiles/${profile}/VERSION
    git add repo2docker/buildpacks/profiles/${profile}/VERSION
fi