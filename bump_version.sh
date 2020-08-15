#!/bin/sh

profile=${1}

bin/versionbump patch repo2docker/buildpacks/profiles/${profile}/VERSION
git add repo2docker/buildpacks/profiles/${profile}/VERSION
