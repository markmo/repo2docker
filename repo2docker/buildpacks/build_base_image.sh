#!/usr/bin/env bash

docker build -t markmo/repo2docker-base -f Dockerfile.base --build-arg NB_USER=jovyan --build-arg NB_UID=1000 .
