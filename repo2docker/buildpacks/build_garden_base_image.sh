#!/usr/bin/env bash

docker build -t markmo/europabase -f Dockerfile-garden-base --build-arg NB_USER=jovyan --build-arg NB_UID=1000 .
