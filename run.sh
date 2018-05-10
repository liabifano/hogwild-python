#!/usr/bin/env bash

set -eo pipefail


# build docker images
# TODO: put a check if they already exists and to another to overwrite
for port in 50052 50053;
do
    PORT=$port
    docker build -f `pwd`/Docker/node/Dockerfile `pwd` -t hogwild:node${PORT}
done;

docker build -f `pwd`/Docker/coordinator/Dockerfile `pwd` -t hogwild:coordinator


# TODO: Do it dynamically and also hog-pod.yaml
# Create `pod` in the cluster
kubectl create -f ./Kubernetes/hog-pod.yaml
kubectl get pods
