#!/usr/bin/env bash

cd repo2docker/buildpacks
bash build_base_image.sh
docker build -t markmo/europabase -f Dockerfile.base --build-arg NB_USER=jovyan --build-arg NB_UID=1000 .
docker push markmo/repo2docker
