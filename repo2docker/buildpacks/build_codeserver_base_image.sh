#!/usr/bin/env bash

docker build -t markmo/repo2docker-codeserver-base -f Dockerfile-codeserver-base --build-arg NB_USER=jovyan --build-arg NB_UID=1000 .
