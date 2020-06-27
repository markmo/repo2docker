#!/usr/bin/env bash

cd repo2docker/buildpacks
bash build_base_image.sh
docker build -t markmo/repo2docker:latest .
docker push markmo/repo2docker
